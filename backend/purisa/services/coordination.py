"""
Coordination detection service for Purisa 2.0.

Analyzes posts for coordinated inauthentic behavior by:
1. Building similarity networks between accounts
2. Detecting clusters using Louvain community detection
3. Calculating hourly/daily coordination scores
4. Identifying coordination spikes
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import uuid

import networkx as nx
import numpy as np
from sqlalchemy.orm import Session

from ..database.connection import get_database
from ..database.models import PostDB, AccountDB
from ..database.coordination_models import (
    AccountEdgeDB,
    CoordinationClusterDB,
    ClusterMemberDB,
    CoordinationMetricDB,
)
from .similarity import (
    TextSimilarityCalculator,
    find_url_sharing_pairs,
    find_hashtag_overlap_pairs,
    SimilarityResult,
)

logger = logging.getLogger(__name__)


@dataclass
class CoordinationConfig:
    """Configuration for coordination detection."""
    # Time windows
    sync_window_seconds: int = 90  # Posts within this window are "synchronized"
    analysis_window_hours: int = 1  # Default analysis window

    # Similarity thresholds
    text_similarity_threshold: float = 0.8
    min_hashtag_overlap: int = 2

    # Cluster detection
    min_cluster_size: int = 3
    min_cluster_density: float = 0.3
    louvain_resolution: float = 1.0

    # Edge weights
    sync_weight: float = 1.0
    url_weight: float = 1.5
    text_weight: float = 1.0
    hashtag_weight: float = 0.5
    reply_pattern_weight: float = 0.8

    # Scoring weights
    cluster_coverage_weight: float = 0.4
    density_weight: float = 0.3
    sync_rate_weight: float = 0.3


@dataclass
class Cluster:
    """Detected coordination cluster."""
    cluster_id: str
    members: List[str]  # Account IDs
    density: float
    size: int
    edge_count: int
    primary_type: str  # Most common edge type
    centrality_scores: Dict[str, float]  # Account ID -> centrality


@dataclass
class CoordinationResult:
    """Result of coordination analysis for a time window."""
    platform: str
    time_window_start: datetime
    time_window_end: datetime
    coordination_score: float  # 0-100
    total_posts: int
    coordinated_posts: int
    organic_posts: int
    clusters: List[Cluster]
    edge_count: int
    sync_rate: float
    url_sharing_rate: float
    text_similarity_rate: float
    is_spike: bool
    spike_magnitude: float  # How many std devs above baseline


class CoordinationAnalyzer:
    """
    Analyzes social media posts for coordinated inauthentic behavior.

    Uses network analysis to detect clusters of accounts exhibiting
    coordinated posting patterns.
    """

    def __init__(self, config: Optional[CoordinationConfig] = None):
        """
        Initialize the analyzer.

        Args:
            config: Configuration for coordination detection
        """
        self.config = config or CoordinationConfig()
        self.text_calculator = TextSimilarityCalculator(
            similarity_threshold=self.config.text_similarity_threshold
        )

    def analyze_hour(
        self,
        platform: str,
        hour_start: datetime,
        session: Optional[Session] = None
    ) -> CoordinationResult:
        """
        Analyze coordination for a single hour.

        Args:
            platform: Platform to analyze
            hour_start: Start of the hour to analyze
            session: Optional database session

        Returns:
            CoordinationResult with analysis results
        """
        hour_end = hour_start + timedelta(hours=1)

        logger.info(f"Analyzing coordination for {platform} from {hour_start} to {hour_end}")

        # Get database session
        close_session = False
        if session is None:
            db = get_database()
            session = db.get_session_direct()
            close_session = True

        try:
            # Get posts in time window
            posts = self._get_posts_in_window(session, platform, hour_start, hour_end)

            if len(posts) < self.config.min_cluster_size:
                logger.info(f"Not enough posts ({len(posts)}) for analysis")
                return self._empty_result(platform, hour_start, hour_end)

            # Build similarity network
            graph = self._build_network(posts)

            if graph.number_of_edges() == 0:
                logger.info("No edges detected in network")
                return self._empty_result(platform, hour_start, hour_end)

            # Detect clusters
            clusters = self._detect_clusters(graph)

            # Calculate coordination metrics
            result = self._calculate_metrics(
                platform, hour_start, hour_end, posts, graph, clusters
            )

            # Store results in database
            self._store_results(session, result)

            return result

        finally:
            if close_session:
                session.close()

    def analyze_range(
        self,
        platform: str,
        start: datetime,
        end: datetime
    ) -> List[CoordinationResult]:
        """
        Analyze coordination for a date range, hour by hour.

        Args:
            platform: Platform to analyze
            start: Start of range
            end: End of range

        Returns:
            List of CoordinationResult for each hour
        """
        results = []

        # Round to hour boundaries
        current = start.replace(minute=0, second=0, microsecond=0)
        end = end.replace(minute=0, second=0, microsecond=0)

        db = get_database()
        with db.get_session() as session:
            while current < end:
                result = self.analyze_hour(platform, current, session)
                results.append(result)
                current += timedelta(hours=1)

        return results

    def get_recent_metrics(
        self,
        platform: str,
        hours: int = 24
    ) -> List[Dict]:
        """
        Get recent coordination metrics.

        Args:
            platform: Platform to query
            hours: Number of hours to look back

        Returns:
            List of metric dictionaries
        """
        db = get_database()
        cutoff = datetime.now() - timedelta(hours=hours)

        with db.get_session() as session:
            metrics = session.query(CoordinationMetricDB).filter(
                CoordinationMetricDB.platform == platform,
                CoordinationMetricDB.time_bucket >= cutoff,
                CoordinationMetricDB.bucket_type == 'hourly'
            ).order_by(CoordinationMetricDB.time_bucket.desc()).all()

            return [
                {
                    'time_bucket': m.time_bucket.isoformat(),
                    'coordination_score': m.coordination_score,
                    'total_posts': m.total_posts_analyzed,
                    'coordinated_posts': m.coordinated_posts_count,
                    'cluster_count': m.active_cluster_count,
                    'avg_cluster_size': m.avg_cluster_size,
                    'sync_rate': m.synchronized_posting_rate,
                }
                for m in metrics
            ]

    def get_spikes(
        self,
        platform: str,
        hours: int = 168,  # 7 days
        threshold_std: float = 2.0
    ) -> List[Dict]:
        """
        Get coordination spikes above baseline.

        Args:
            platform: Platform to query
            hours: Hours to look back
            threshold_std: Standard deviations above mean to consider a spike

        Returns:
            List of spike dictionaries
        """
        db = get_database()
        cutoff = datetime.now() - timedelta(hours=hours)

        with db.get_session() as session:
            metrics = session.query(CoordinationMetricDB).filter(
                CoordinationMetricDB.platform == platform,
                CoordinationMetricDB.time_bucket >= cutoff,
                CoordinationMetricDB.bucket_type == 'hourly'
            ).order_by(CoordinationMetricDB.time_bucket).all()

            if len(metrics) < 10:
                return []

            scores = [m.coordination_score for m in metrics]
            mean_score = np.mean(scores)
            std_score = np.std(scores)

            if std_score == 0:
                return []

            spikes = []
            for m in metrics:
                z_score = (m.coordination_score - mean_score) / std_score
                if z_score >= threshold_std:
                    spikes.append({
                        'time_bucket': m.time_bucket.isoformat(),
                        'coordination_score': m.coordination_score,
                        'z_score': float(z_score),
                        'total_posts': m.total_posts_analyzed,
                        'cluster_count': m.active_cluster_count,
                        'baseline_mean': float(mean_score),
                        'baseline_std': float(std_score),
                    })

            return sorted(spikes, key=lambda x: x['z_score'], reverse=True)

    def _get_posts_in_window(
        self,
        session: Session,
        platform: str,
        start: datetime,
        end: datetime
    ) -> List[PostDB]:
        """Get posts within a time window."""
        return session.query(PostDB).filter(
            PostDB.platform == platform,
            PostDB.created_at >= start,
            PostDB.created_at < end,
            PostDB.post_type == 'post'  # Only original posts, not comments
        ).all()

    def _build_network(self, posts: List[PostDB]) -> nx.Graph:
        """
        Build a network graph of accounts based on coordination signals.

        Edges represent detected coordination between accounts.
        """
        G = nx.Graph()

        # Add all accounts as nodes
        account_ids = set(p.account_id for p in posts)
        for account_id in account_ids:
            G.add_node(account_id)

        # Prepare posts for similarity analysis
        post_data = [(p.id, p.account_id, p.content or '') for p in posts]

        # 1. Synchronized posting detection
        sync_edges = self._find_synchronized_pairs(posts)
        for edge in sync_edges:
            self._add_edge(G, edge, 'synchronized_posting', self.config.sync_weight)

        # 2. URL sharing detection
        url_results = find_url_sharing_pairs(post_data)
        for result in url_results:
            self._add_edge_from_result(G, result, self.config.url_weight)

        # 3. Text similarity detection
        text_results = self.text_calculator.find_similar_pairs(post_data)
        for result in text_results:
            self._add_edge_from_result(G, result, self.config.text_weight)

        # 4. Hashtag overlap detection
        hashtag_results = find_hashtag_overlap_pairs(
            post_data,
            min_overlap=self.config.min_hashtag_overlap
        )
        for result in hashtag_results:
            self._add_edge_from_result(G, result, self.config.hashtag_weight)

        # 5. Reply pattern detection (commenting on same posts)
        reply_edges = self._find_reply_pattern_pairs(posts)
        for edge in reply_edges:
            self._add_edge(G, edge, 'reply_pattern', self.config.reply_pattern_weight)

        logger.info(f"Built network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G

    def _find_synchronized_pairs(
        self,
        posts: List[PostDB]
    ) -> List[Tuple[str, str, Dict]]:
        """Find pairs of accounts posting within sync window."""
        edges = []

        # Sort posts by time
        sorted_posts = sorted(posts, key=lambda p: p.created_at)

        # Sliding window comparison
        for i, post1 in enumerate(sorted_posts):
            for post2 in sorted_posts[i + 1:]:
                time_diff = (post2.created_at - post1.created_at).total_seconds()

                if time_diff > self.config.sync_window_seconds:
                    break  # No more posts within window

                if post1.account_id != post2.account_id:
                    edges.append((
                        post1.account_id,
                        post2.account_id,
                        {
                            'time_diff_seconds': time_diff,
                            'post1_id': post1.id,
                            'post2_id': post2.id,
                        }
                    ))

        return edges

    def _find_reply_pattern_pairs(
        self,
        posts: List[PostDB]
    ) -> List[Tuple[str, str, Dict]]:
        """Find pairs of accounts commenting on the same posts."""
        # Group posts by parent_id
        posts_by_parent: Dict[str, List[PostDB]] = {}
        for post in posts:
            if post.parent_id:
                if post.parent_id not in posts_by_parent:
                    posts_by_parent[post.parent_id] = []
                posts_by_parent[post.parent_id].append(post)

        edges = []
        for parent_id, comments in posts_by_parent.items():
            if len(comments) < 2:
                continue

            # Create edges between accounts commenting on same post
            accounts = list(set(c.account_id for c in comments))
            for i, acc1 in enumerate(accounts):
                for acc2 in accounts[i + 1:]:
                    edges.append((
                        acc1,
                        acc2,
                        {
                            'parent_id': parent_id,
                            'comment_count': len(comments),
                        }
                    ))

        return edges

    def _add_edge(
        self,
        G: nx.Graph,
        edge: Tuple[str, str, Dict],
        edge_type: str,
        weight: float
    ):
        """Add or update an edge in the graph."""
        a1, a2, evidence = edge

        if G.has_edge(a1, a2):
            G[a1][a2]['weight'] += weight
            G[a1][a2]['types'].add(edge_type)
            G[a1][a2]['evidence'][edge_type] = evidence
        else:
            G.add_edge(
                a1, a2,
                weight=weight,
                types={edge_type},
                evidence={edge_type: evidence}
            )

    def _add_edge_from_result(
        self,
        G: nx.Graph,
        result: SimilarityResult,
        weight: float
    ):
        """Add edge from a SimilarityResult."""
        a1 = result.evidence.get('account1')
        a2 = result.evidence.get('account2')

        if not a1 or not a2 or a1 == a2:
            return

        adjusted_weight = weight * result.similarity_score

        if G.has_edge(a1, a2):
            G[a1][a2]['weight'] += adjusted_weight
            G[a1][a2]['types'].add(result.similarity_type)
            G[a1][a2]['evidence'][result.similarity_type] = result.evidence
        else:
            G.add_edge(
                a1, a2,
                weight=adjusted_weight,
                types={result.similarity_type},
                evidence={result.similarity_type: result.evidence}
            )

    def _detect_clusters(self, G: nx.Graph) -> List[Cluster]:
        """Detect coordination clusters using Louvain community detection."""
        if G.number_of_nodes() < self.config.min_cluster_size:
            return []

        try:
            from networkx.algorithms.community import louvain_communities

            communities = louvain_communities(
                G,
                resolution=self.config.louvain_resolution,
                weight='weight'
            )

            clusters = []
            for i, community in enumerate(communities):
                if len(community) < self.config.min_cluster_size:
                    continue

                subgraph = G.subgraph(community)
                density = nx.density(subgraph)

                if density < self.config.min_cluster_density:
                    continue

                # Calculate centrality
                centrality = nx.degree_centrality(subgraph)

                # Determine primary edge type
                edge_types: Dict[str, int] = {}
                for _, _, data in subgraph.edges(data=True):
                    for t in data.get('types', set()):
                        edge_types[t] = edge_types.get(t, 0) + 1

                primary_type = max(edge_types, key=edge_types.get) if edge_types else 'unknown'

                cluster = Cluster(
                    cluster_id=f"{datetime.now().strftime('%Y%m%d_%H%M')}_cluster_{i}",
                    members=list(community),
                    density=density,
                    size=len(community),
                    edge_count=subgraph.number_of_edges(),
                    primary_type=primary_type,
                    centrality_scores=centrality,
                )
                clusters.append(cluster)

            logger.info(f"Detected {len(clusters)} coordination clusters")
            return clusters

        except Exception as e:
            logger.error(f"Error detecting clusters: {e}")
            return []

    def _calculate_metrics(
        self,
        platform: str,
        start: datetime,
        end: datetime,
        posts: List[PostDB],
        graph: nx.Graph,
        clusters: List[Cluster]
    ) -> CoordinationResult:
        """Calculate coordination metrics from analysis results."""
        total_posts = len(posts)

        # Get accounts in clusters
        clustered_accounts: Set[str] = set()
        for cluster in clusters:
            clustered_accounts.update(cluster.members)

        # Count coordinated vs organic posts
        coordinated_posts = sum(
            1 for p in posts if p.account_id in clustered_accounts
        )
        organic_posts = total_posts - coordinated_posts

        # Calculate rates
        cluster_coverage = coordinated_posts / total_posts if total_posts > 0 else 0
        avg_density = np.mean([c.density for c in clusters]) if clusters else 0

        # Calculate sync rate (posts with synchronized edges / total)
        sync_edges = sum(
            1 for _, _, data in graph.edges(data=True)
            if 'synchronized_posting' in data.get('types', set())
        )
        sync_rate = (sync_edges * 2) / total_posts if total_posts > 0 else 0  # *2 because each edge involves 2 posts

        # URL sharing rate
        url_edges = sum(
            1 for _, _, data in graph.edges(data=True)
            if 'url' in data.get('types', set())
        )
        url_rate = (url_edges * 2) / total_posts if total_posts > 0 else 0

        # Text similarity rate
        text_edges = sum(
            1 for _, _, data in graph.edges(data=True)
            if 'text' in data.get('types', set())
        )
        text_rate = (text_edges * 2) / total_posts if total_posts > 0 else 0

        # Calculate coordination score (0-100)
        coordination_score = (
            cluster_coverage * self.config.cluster_coverage_weight +
            avg_density * self.config.density_weight +
            sync_rate * self.config.sync_rate_weight
        ) * 100

        coordination_score = min(coordination_score, 100)

        return CoordinationResult(
            platform=platform,
            time_window_start=start,
            time_window_end=end,
            coordination_score=coordination_score,
            total_posts=total_posts,
            coordinated_posts=coordinated_posts,
            organic_posts=organic_posts,
            clusters=clusters,
            edge_count=graph.number_of_edges(),
            sync_rate=sync_rate,
            url_sharing_rate=url_rate,
            text_similarity_rate=text_rate,
            is_spike=False,  # Will be determined by spike detection
            spike_magnitude=0.0,
        )

    def _store_results(self, session: Session, result: CoordinationResult):
        """Store analysis results in database."""
        try:
            # Store or update metric
            metric = session.query(CoordinationMetricDB).filter(
                CoordinationMetricDB.platform == result.platform,
                CoordinationMetricDB.time_bucket == result.time_window_start,
                CoordinationMetricDB.bucket_type == 'hourly'
            ).first()

            if metric:
                # Update existing
                metric.coordination_score = result.coordination_score
                metric.total_posts_analyzed = result.total_posts
                metric.coordinated_posts_count = result.coordinated_posts
                metric.organic_posts_count = result.organic_posts
                metric.active_cluster_count = len(result.clusters)
                metric.avg_cluster_size = np.mean([c.size for c in result.clusters]) if result.clusters else 0
                metric.synchronized_posting_rate = result.sync_rate
                metric.url_sharing_rate = result.url_sharing_rate
                metric.text_similarity_rate = result.text_similarity_rate
            else:
                # Create new
                metric = CoordinationMetricDB(
                    platform=result.platform,
                    time_bucket=result.time_window_start,
                    bucket_type='hourly',
                    coordination_score=result.coordination_score,
                    total_posts_analyzed=result.total_posts,
                    coordinated_posts_count=result.coordinated_posts,
                    organic_posts_count=result.organic_posts,
                    active_cluster_count=len(result.clusters),
                    avg_cluster_size=np.mean([c.size for c in result.clusters]) if result.clusters else 0,
                    synchronized_posting_rate=result.sync_rate,
                    url_sharing_rate=result.url_sharing_rate,
                    text_similarity_rate=result.text_similarity_rate,
                )
                session.add(metric)

            # Store clusters
            for cluster in result.clusters:
                cluster_db = CoordinationClusterDB(
                    cluster_id=cluster.cluster_id,
                    platform=result.platform,
                    time_window_start=result.time_window_start,
                    time_window_end=result.time_window_end,
                    member_count=cluster.size,
                    density_score=cluster.density,
                    cluster_type=cluster.primary_type,
                    coordination_score=result.coordination_score,
                )
                session.add(cluster_db)

                # Store cluster members
                for account_id, centrality in cluster.centrality_scores.items():
                    member = ClusterMemberDB(
                        cluster_id=cluster.cluster_id,
                        account_id=account_id,
                        centrality_score=centrality,
                        edge_count=cluster.edge_count,
                    )
                    session.add(member)

            session.commit()
            logger.info(f"Stored coordination results for {result.platform} at {result.time_window_start}")

        except Exception as e:
            logger.error(f"Error storing results: {e}")
            session.rollback()

    def _empty_result(
        self,
        platform: str,
        start: datetime,
        end: datetime
    ) -> CoordinationResult:
        """Return an empty result for when there's insufficient data."""
        return CoordinationResult(
            platform=platform,
            time_window_start=start,
            time_window_end=end,
            coordination_score=0.0,
            total_posts=0,
            coordinated_posts=0,
            organic_posts=0,
            clusters=[],
            edge_count=0,
            sync_rate=0.0,
            url_sharing_rate=0.0,
            text_similarity_rate=0.0,
            is_spike=False,
            spike_magnitude=0.0,
        )
