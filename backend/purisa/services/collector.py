"""Universal data collector service for all platforms."""
import logging
import yaml
import os
from typing import Dict, List, Optional, Set
from datetime import datetime
from purisa.platforms.base import SocialPlatform
from purisa.platforms.bluesky import BlueskyPlatform
from purisa.platforms.hackernews import HackerNewsPlatform
from purisa.models.account import Account
from purisa.models.post import Post
from purisa.database.connection import get_database
from purisa.database.models import AccountDB, PostDB, InflammatoryFlagDB
from purisa.config.settings import get_settings
from purisa.services.inflammatory import get_inflammatory_detector, InflammatoryMatch

logger = logging.getLogger(__name__)


class UniversalCollector:
    """Collects data from multiple social media platforms."""

    def __init__(self):
        """Initialize collector with configured platforms."""
        self.platforms: Dict[str, SocialPlatform] = {}
        self.config = self._load_platform_config()
        self.settings = get_settings()
        self._initialize_platforms()
        self.comment_config = self._load_comment_config()
        self._inflammatory_detector = None  # Lazy loaded

    def _load_comment_config(self) -> dict:
        """Load comment collection configuration."""
        return self.config.get('comment_collection', {
            'enabled': True,
            'min_engagement_score': 0.3,
            'max_comments_per_post': 100,
            'max_posts_for_comment_harvest': 20,
            'fetch_commenter_profiles': True
        })

    @property
    def inflammatory_detector(self):
        """Lazy load the inflammatory detector."""
        if self._inflammatory_detector is None:
            self._inflammatory_detector = get_inflammatory_detector(
                model_name=getattr(self.settings, 'inflammatory_model', 'original-small'),
                threshold=getattr(self.settings, 'inflammatory_threshold', 0.5),
                device=getattr(self.settings, 'inflammatory_device', 'cpu')
            )
        return self._inflammatory_detector

    def _load_platform_config(self) -> dict:
        """
        Load platform configuration from YAML file.

        Returns:
            Platform configuration dict
        """
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'platforms.yaml'
        )

        try:
            with open(config_path, 'r') as f:
                content = f.read()

            # Replace environment variables in YAML
            for key, value in os.environ.items():
                content = content.replace(f'${{{key}}}', value)

            config = yaml.safe_load(content)
            logger.info("Platform configuration loaded successfully")
            return config

        except Exception as e:
            logger.error(f"Failed to load platform config: {e}")
            return {}

    def _initialize_platforms(self):
        """Initialize enabled platform adapters."""
        # Initialize Bluesky
        if self.config.get('bluesky', {}).get('enabled'):
            try:
                bluesky_config = {
                    'handle': self.settings.bluesky_handle,
                    'password': self.settings.bluesky_password
                }
                if bluesky_config['handle'] and bluesky_config['password']:
                    self.platforms['bluesky'] = BlueskyPlatform(bluesky_config)
                    logger.info("Bluesky platform initialized")
                else:
                    logger.warning("Bluesky credentials not found in environment")
            except Exception as e:
                logger.error(f"Failed to initialize Bluesky: {e}")

        # Initialize Hacker News
        if self.config.get('hackernews', {}).get('enabled'):
            try:
                self.platforms['hackernews'] = HackerNewsPlatform({})
                logger.info("Hacker News platform initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Hacker News: {e}")

    async def collect_from_platform(
        self,
        platform_name: str,
        query: str,
        limit: int
    ) -> List[Post]:
        """
        Collect posts from a specific platform.

        Args:
            platform_name: Platform to collect from (bluesky, hackernews, etc.)
            query: Search query or hashtag
            limit: Maximum number of posts to collect

        Returns:
            List of collected posts
        """
        platform = self.platforms.get(platform_name)
        if not platform:
            raise ValueError(f"Platform not available: {platform_name}")

        posts = await platform.collect_posts(query, limit)
        logger.info(f"Collected {len(posts)} posts from {platform_name}")

        return posts

    async def collect_account_history(
        self,
        platform_name: str,
        username: str,
        limit: int
    ) -> List[Post]:
        """
        Collect posting history for a specific account.

        Args:
            platform_name: Platform name
            username: Username to collect history for
            limit: Maximum number of posts

        Returns:
            List of posts from account history
        """
        platform = self.platforms.get(platform_name)
        if not platform:
            raise ValueError(f"Platform not available: {platform_name}")

        posts = await platform.get_account_history(username, limit)
        logger.info(f"Collected {len(posts)} posts from {username} on {platform_name}")

        return posts

    async def store_posts(self, posts: List[Post]):
        """
        Store collected posts in database.

        Args:
            posts: List of posts to store
        """
        db = get_database()

        with db.get_session() as session:
            # Track accounts and posts we've processed in this batch to avoid duplicates
            processed_accounts = set()
            processed_posts = set()

            for post in posts:
                # Skip if we've already processed this post in this batch
                if post.id in processed_posts:
                    continue

                # Store account if not exists (check both DB and current batch)
                if post.account_id not in processed_accounts:
                    account_exists = session.query(AccountDB).filter_by(
                        id=post.account_id
                    ).first()

                    if not account_exists:
                        # Fetch account info
                        try:
                            platform = self.platforms.get(post.platform)
                            if platform:
                                # For Bluesky, account_id is DID; for HN, it's username
                                username = post.metadata.get('author_handle', post.account_id)
                                account_info = await platform.get_account_info(username)
                                self._store_account(session, account_info)
                                processed_accounts.add(post.account_id)
                        except Exception as e:
                            logger.warning(f"Failed to fetch account info: {e}")
                            # Create minimal account entry
                            account_db = AccountDB(
                                id=post.account_id,
                                username=post.account_id,
                                platform=post.platform,
                                created_at=datetime.now(),
                                first_seen=datetime.now()
                            )
                            session.merge(account_db)  # Use merge instead of add for safety
                            processed_accounts.add(post.account_id)
                    else:
                        processed_accounts.add(post.account_id)

                # Store post (use merge to handle duplicates from overlapping queries)
                post_db = PostDB(
                    id=post.id,
                    account_id=post.account_id,
                    platform=post.platform,
                    content=post.content,
                    created_at=post.created_at,
                    engagement=post.engagement,
                    platform_metadata=post.metadata,  # Map Pydantic model metadata to database platform_metadata
                    collected_at=datetime.now()
                )
                session.merge(post_db)
                processed_posts.add(post.id)

        logger.info(f"Stored {len(processed_posts)} posts in database (from {len(posts)} collected)")

    def _store_account(self, session, account: Account):
        """
        Store account in database.

        Args:
            session: Database session
            account: Account object to store
        """
        account_db = AccountDB(
            id=account.id,
            username=account.username,
            display_name=account.display_name,
            platform=account.platform,
            created_at=account.created_at,
            follower_count=account.follower_count,
            following_count=account.following_count,
            post_count=account.post_count,
            platform_metadata=account.metadata,  # Map Pydantic model metadata to database platform_metadata
            first_seen=datetime.now()
        )
        session.merge(account_db)  # Use merge to update if exists

    async def run_collection_cycle(self):
        """Run a full collection cycle for all configured platforms."""
        logger.info("Starting collection cycle")

        all_collected_posts: List[Post] = []

        # Collect from Bluesky
        if 'bluesky' in self.platforms:
            bluesky_config = self.config.get('bluesky', {})
            targets = bluesky_config.get('targets', {})

            # Collect hashtags
            for hashtag in targets.get('hashtags', []):
                try:
                    posts = await self.collect_from_platform(
                        'bluesky',
                        f'#{hashtag}',
                        bluesky_config['collection']['posts_per_cycle']
                    )
                    await self.store_posts(posts)
                    all_collected_posts.extend(posts)
                except Exception as e:
                    logger.error(f"Error collecting Bluesky hashtag {hashtag}: {e}")

        # Collect from Hacker News
        if 'hackernews' in self.platforms:
            hn_config = self.config.get('hackernews', {})
            targets = hn_config.get('targets', {})

            # Collect story types
            for story_type in targets.get('types', ['top']):
                try:
                    posts = await self.collect_from_platform(
                        'hackernews',
                        story_type,
                        hn_config['collection']['posts_per_cycle']
                    )
                    await self.store_posts(posts)
                    all_collected_posts.extend(posts)
                except Exception as e:
                    logger.error(f"Error collecting HN {story_type} stories: {e}")

        # Phase 2: Identify top-performing posts and harvest comments
        if self.comment_config.get('enabled', True) and all_collected_posts:
            top_posts = self._identify_top_performers(all_collected_posts)
            if top_posts:
                await self._harvest_comments_phase(top_posts)

        logger.info("Collection cycle completed")

    def _identify_top_performers(self, posts: List[Post]) -> List[Post]:
        """
        Identify top-performing posts based on engagement metrics.

        Args:
            posts: List of posts to evaluate

        Returns:
            List of top-performing posts for comment harvesting
        """
        if not posts:
            return []

        min_score = self.comment_config.get('min_engagement_score', 0.3)
        max_posts = self.comment_config.get('max_posts_for_comment_harvest', 20)

        # Calculate engagement scores per platform
        scored_posts = []
        for post in posts:
            platform = self.platforms.get(post.platform)
            if platform:
                try:
                    engagement_score = platform.get_engagement_score(post)
                    if engagement_score >= min_score:
                        scored_posts.append((post, engagement_score))
                except Exception as e:
                    logger.warning(f"Error calculating engagement score for post {post.id}: {e}")

        # Sort by engagement score (descending)
        scored_posts.sort(key=lambda x: x[1], reverse=True)

        # Take top N posts
        top_posts = [post for post, score in scored_posts[:max_posts]]

        # Mark as top performers in database
        if top_posts:
            self._mark_top_performers(top_posts, min_score)

        logger.info(f"Identified {len(top_posts)} top-performing posts for comment harvest")
        return top_posts

    def _mark_top_performers(self, posts: List[Post], threshold: float):
        """Mark posts as top performers in database."""
        db = get_database()

        with db.get_session() as session:
            for post in posts:
                post_db = session.query(PostDB).filter_by(id=post.id).first()
                if post_db:
                    post_db.is_top_performer = 1
            session.commit()
        logger.debug(f"Marked {len(posts)} posts as top performers (threshold={threshold})")

    async def _harvest_comments_phase(self, top_posts: List[Post]):
        """
        Harvest comments from top-performing posts.

        For each top post:
        1. Fetch comments via platform adapter
        2. Store comments (as Posts with parent_id)
        3. Fetch full profiles for new commenter accounts (batched)
        4. Analyze for inflammatory content
        5. Flag accounts for analysis if inflammatory detected
        """
        max_comments = self.comment_config.get('max_comments_per_post', 100)
        fetch_profiles = self.comment_config.get('fetch_commenter_profiles', True)
        accounts_to_analyze: Set[str] = set()
        all_new_accounts: List[dict] = []  # Collect new accounts for batch profile fetch

        for post in top_posts:
            try:
                platform = self.platforms.get(post.platform)
                if not platform:
                    continue

                # Fetch comments
                comments = await platform.get_post_comments(post.id, max_comments)

                if not comments:
                    continue

                # Store comments and collect new account IDs
                new_accounts = await self._store_comments(comments, parent_id=post.id)
                all_new_accounts.extend(new_accounts)

                # Mark post as having comments collected
                self._mark_comments_collected(post.id)

                # Analyze comments for inflammatory content
                flagged_accounts = await self._analyze_comments_for_inflammatory(
                    comments, parent_post=post
                )
                accounts_to_analyze.update(flagged_accounts)

                logger.info(f"Harvested {len(comments)} comments from post {post.id}")

            except Exception as e:
                logger.error(f"Error harvesting comments for post {post.id}: {e}")

        # Batch fetch profiles for new commenter accounts
        if fetch_profiles and all_new_accounts:
            await self._fetch_commenter_profiles_batch(all_new_accounts)

        if accounts_to_analyze:
            logger.info(f"Flagged {len(accounts_to_analyze)} accounts with inflammatory comments for analysis")

    async def _store_comments(self, comments: List[Post], parent_id: str) -> List[dict]:
        """
        Store comments in database.

        Returns:
            List of new account info dicts for batch profile fetching:
            [{'id': account_id, 'username': handle, 'platform': platform}, ...]
        """
        db = get_database()
        new_accounts: List[dict] = []

        with db.get_session() as session:
            # Track accounts processed in this batch to avoid duplicate inserts
            processed_accounts_in_batch: Set[str] = set()

            for comment in comments:
                # Ensure account exists (check both DB and current batch)
                if comment.account_id not in processed_accounts_in_batch:
                    account_exists = session.query(AccountDB).filter_by(
                        id=comment.account_id
                    ).first()

                    if not account_exists:
                        # Create minimal account entry (will be updated with full profile later)
                        username = comment.metadata.get('author_handle', comment.account_id)
                        account_db = AccountDB(
                            id=comment.account_id,
                            username=username,
                            platform=comment.platform,
                            created_at=datetime.now(),
                            first_seen=datetime.now()
                        )
                        session.merge(account_db)
                        session.flush()  # Ensure account is committed before dependent comment

                        # Track for batch profile fetch
                        new_accounts.append({
                            'id': comment.account_id,
                            'username': username,
                            'platform': comment.platform
                        })

                    processed_accounts_in_batch.add(comment.account_id)

                # Store comment as post with parent_id and post_type
                comment_db = PostDB(
                    id=comment.id,
                    account_id=comment.account_id,
                    platform=comment.platform,
                    content=comment.content,
                    created_at=comment.created_at,
                    engagement=comment.engagement,
                    platform_metadata=comment.metadata,
                    collected_at=datetime.now(),
                    parent_id=comment.metadata.get('parent_id', parent_id),
                    post_type='comment'
                )
                session.merge(comment_db)

            session.commit()

        return new_accounts

    async def _fetch_commenter_profiles_batch(self, new_accounts: List[dict]):
        """
        Batch fetch full profiles for new commenter accounts.

        This enables full 13-signal bot detection for commenters by fetching
        follower counts, profile metadata, verification status, etc.

        Args:
            new_accounts: List of dicts with 'id', 'username', 'platform' keys
        """
        if not new_accounts:
            return

        # Deduplicate accounts (same account may appear in multiple comment batches)
        unique_accounts = {acc['id']: acc for acc in new_accounts}
        accounts_list = list(unique_accounts.values())
        total = len(accounts_list)

        logger.info(f"Fetching full profiles for {total} new commenter accounts...")

        db = get_database()
        fetched = 0
        failed = 0

        for i, acc in enumerate(accounts_list):
            try:
                platform = self.platforms.get(acc['platform'])
                if not platform:
                    continue

                # Fetch full profile from platform
                account_info = await platform.get_account_info(acc['username'])

                if account_info:
                    # Update account in database with full profile
                    with db.get_session() as session:
                        self._store_account(session, account_info)
                        session.commit()
                    fetched += 1
                else:
                    failed += 1

            except Exception as e:
                logger.debug(f"Failed to fetch profile for {acc['username']}: {e}")
                failed += 1

            # Progress logging every 10 accounts or at completion
            if (i + 1) % 10 == 0 or (i + 1) == total:
                logger.info(f"Profile fetch progress: {i + 1}/{total} ({fetched} fetched, {failed} failed)")

        logger.info(f"Completed profile fetch: {fetched} profiles updated, {failed} failed out of {total}")

    def _mark_comments_collected(self, post_id: str):
        """Mark a post as having its comments collected."""
        db = get_database()

        with db.get_session() as session:
            post_db = session.query(PostDB).filter_by(id=post_id).first()
            if post_db:
                post_db.comments_collected = 1
                post_db.comments_collected_at = datetime.now()
            session.commit()

    async def _analyze_comments_for_inflammatory(
        self,
        comments: List[Post],
        parent_post: Post
    ) -> Set[str]:
        """
        Analyze comments for inflammatory content using Detoxify.

        Args:
            comments: List of comments to analyze
            parent_post: The parent post these comments are on

        Returns:
            Set of account IDs flagged for inflammatory content
        """
        if not comments:
            return set()

        accounts_flagged: Set[str] = set()
        db = get_database()

        # Use batch analysis for efficiency
        texts = [c.content or '' for c in comments]
        results = self.inflammatory_detector.analyze_batch(texts)

        with db.get_session() as session:
            for comment, result in zip(comments, results):
                if result.is_inflammatory:
                    # Create inflammatory flag record
                    flag_db = InflammatoryFlagDB(
                        post_id=comment.id,
                        account_id=comment.account_id,
                        parent_post_id=parent_post.id,
                        platform=comment.platform,
                        toxicity_scores=result.toxicity_scores,
                        triggered_categories=result.triggered_categories,
                        severity_score=result.severity_score,
                        content_snippet=comment.content[:200] if comment.content else '',
                        detected_at=datetime.now(),
                        analysis_triggered=1
                    )
                    session.add(flag_db)
                    accounts_flagged.add(comment.account_id)

                    logger.debug(
                        f"Inflammatory content detected in comment {comment.id} "
                        f"by account {comment.account_id} (severity: {result.severity_score:.2f}, "
                        f"categories: {result.triggered_categories})"
                    )

            session.commit()

        return accounts_flagged

    def get_available_platforms(self) -> List[str]:
        """
        Get list of available/initialized platforms.

        Returns:
            List of platform names
        """
        return list(self.platforms.keys())
