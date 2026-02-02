"""
SQLAlchemy database models for coordination detection (Purisa 2.0).

These models support network-based coordination detection:
- AccountEdgeDB: Pairwise account similarity/connection edges
- CoordinationClusterDB: Detected coordination clusters
- ClusterMemberDB: Many-to-many link between accounts and clusters
- CoordinationMetricDB: Hourly/daily coordination intensity metrics
- EventDB: User-contributed or auto-detected events for correlation
- EventCorrelationDB: Links coordination spikes to events
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime

from .models import Base


class AccountEdgeDB(Base):
    """
    Stores pairwise account similarity/connection edges.

    Edges represent detected coordination signals between two accounts,
    such as synchronized posting, shared URLs, or text similarity.
    """

    __tablename__ = 'account_edges'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id_1 = Column(String, ForeignKey('accounts.id'), nullable=False)
    account_id_2 = Column(String, ForeignKey('accounts.id'), nullable=False)
    platform = Column(String, nullable=False)
    edge_type = Column(String, nullable=False)  # 'synchronized_posting', 'url_sharing', 'text_similarity', 'reply_pattern'
    similarity_score = Column(Float, default=0.0)  # 0.0 to 1.0
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    evidence = Column(JSON, default=dict)  # Supporting data: shared URLs, similar text snippets, etc.
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index('idx_edges_account1', 'account_id_1'),
        Index('idx_edges_account2', 'account_id_2'),
        Index('idx_edges_platform', 'platform'),
        Index('idx_edges_type', 'edge_type'),
        Index('idx_edges_time_window', 'time_window_start', 'time_window_end'),
    )


class CoordinationClusterDB(Base):
    """
    Stores detected coordination clusters.

    A cluster is a group of accounts exhibiting coordinated behavior
    during a specific time window.
    """

    __tablename__ = 'coordination_clusters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(String, unique=True, nullable=False)  # e.g., "2024-01-15_12:00_cluster_0"
    platform = Column(String, nullable=False)
    detected_at = Column(DateTime, default=datetime.now)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    member_count = Column(Integer, default=0)
    density_score = Column(Float, default=0.0)  # Graph density (0.0 to 1.0)
    primary_topic = Column(String, nullable=True)  # Extracted topic/keyword
    cluster_type = Column(String, nullable=True)  # 'synchronized', 'amplification', 'url_sharing', etc.
    coordination_score = Column(Float, default=0.0)  # Cluster-level coordination intensity
    active = Column(Integer, default=1)  # SQLite boolean: 1=active, 0=inactive
    cluster_metadata = Column(JSON, default=dict)  # Additional cluster properties

    __table_args__ = (
        Index('idx_clusters_platform', 'platform'),
        Index('idx_clusters_detected', 'detected_at'),
        Index('idx_clusters_time_window', 'time_window_start', 'time_window_end'),
        Index('idx_clusters_active', 'active'),
    )


class ClusterMemberDB(Base):
    """
    Links accounts to clusters (many-to-many relationship).

    An account can belong to multiple clusters over time,
    and each cluster contains multiple accounts.
    """

    __tablename__ = 'cluster_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(String, ForeignKey('coordination_clusters.cluster_id'), nullable=False)
    account_id = Column(String, ForeignKey('accounts.id'), nullable=False)
    centrality_score = Column(Float, default=0.0)  # How central to the cluster (0.0 to 1.0)
    joined_at = Column(DateTime, default=datetime.now)
    edge_count = Column(Integer, default=0)  # Number of edges to other cluster members

    __table_args__ = (
        Index('idx_members_cluster', 'cluster_id'),
        Index('idx_members_account', 'account_id'),
        Index('idx_members_centrality', 'centrality_score'),
    )


class CoordinationMetricDB(Base):
    """
    Hourly/daily coordination metrics for time-series analysis.

    Aggregated metrics for visualizing coordination intensity over time
    and detecting spikes.
    """

    __tablename__ = 'coordination_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String, nullable=False)
    time_bucket = Column(DateTime, nullable=False)  # Hour or day start
    bucket_type = Column(String, nullable=False)  # 'hourly' or 'daily'
    coordination_score = Column(Float, default=0.0)  # 0-100 aggregate score
    total_posts_analyzed = Column(Integer, default=0)
    coordinated_posts_count = Column(Integer, default=0)
    organic_posts_count = Column(Integer, default=0)
    active_cluster_count = Column(Integer, default=0)
    avg_cluster_size = Column(Float, default=0.0)
    synchronized_posting_rate = Column(Float, default=0.0)  # % of posts within sync window
    url_sharing_rate = Column(Float, default=0.0)  # % of posts sharing same URLs
    text_similarity_rate = Column(Float, default=0.0)  # % of posts with high text similarity
    top_topics = Column(JSON, default=list)  # [{topic, coordinated_count}, ...]
    metric_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index('idx_metrics_platform', 'platform'),
        Index('idx_metrics_time_bucket', 'time_bucket'),
        Index('idx_metrics_bucket_type', 'bucket_type'),
        Index('idx_metrics_score', 'coordination_score'),
        # Unique constraint: one metric per platform/time_bucket/bucket_type
        Index('idx_metrics_unique', 'platform', 'time_bucket', 'bucket_type', unique=True),
    )


class EventDB(Base):
    """
    User-contributed or auto-detected events for correlation.

    Events are external occurrences (news, announcements, etc.) that
    can be correlated with coordination spikes.
    """

    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    platform = Column(String, nullable=True)  # NULL = cross-platform event
    event_time = Column(DateTime, nullable=False)
    event_type = Column(String, nullable=True)  # 'political', 'news', 'product_launch', etc.
    source = Column(String, nullable=True)  # 'user', 'auto_detected', 'news_api'
    created_by = Column(String, nullable=True)  # User who added the event
    event_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index('idx_events_platform', 'platform'),
        Index('idx_events_time', 'event_time'),
        Index('idx_events_type', 'event_type'),
    )


class EventCorrelationDB(Base):
    """
    Links coordination spikes to events.

    Tracks the correlation between detected coordination spikes
    and external events for analysis.
    """

    __tablename__ = 'event_correlations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    metric_id = Column(Integer, ForeignKey('coordination_metrics.id'), nullable=False)
    correlation_strength = Column(Float, default=0.0)  # How closely spike matched event timing
    lag_seconds = Column(Integer, default=0)  # Time between event and spike (can be negative)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index('idx_correlations_event', 'event_id'),
        Index('idx_correlations_metric', 'metric_id'),
    )
