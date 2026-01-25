"""Bot detection analyzer with multiple signals."""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter
import re
from purisa.database.connection import get_database
from purisa.database.models import AccountDB, PostDB, FlagDB, ScoreDB, InflammatoryFlagDB, CommentStatsDB
from purisa.models.detection import Flag, Score
from purisa.config.settings import get_settings

logger = logging.getLogger(__name__)


class BotDetector:
    """Detects bot-like behavior using multiple signals."""

    def __init__(self):
        """Initialize bot detector with settings."""
        self.settings = get_settings()
        self.threshold = self.settings.bot_detection_threshold

    def analyze_account(self, account_id: str) -> Optional[Score]:
        """
        Analyze an account for bot-like behavior.

        Includes 8 original signals plus 5 comment-based signals.

        Args:
            account_id: Account ID to analyze

        Returns:
            Score object with analysis results, or None if account not found
        """
        db = get_database()

        with db.get_session() as session:
            account = session.query(AccountDB).filter_by(id=account_id).first()
            if not account:
                logger.warning(f"Account not found: {account_id}")
                return None

            posts = session.query(PostDB).filter_by(account_id=account_id).all()

            # Separate original posts from comments
            original_posts = [p for p in posts if p.post_type != 'comment']
            comments = [p for p in posts if p.post_type == 'comment']

            # Calculate original 8 signals
            signals = {
                'new_account': self._check_new_account(account),
                'high_frequency': self._check_high_frequency(posts),
                'repetitive_content': self._check_repetitive_content(posts),
                'low_engagement': self._check_low_engagement(account, posts),
                'generic_username': self._check_generic_username(account),
                'incomplete_profile': self._check_incomplete_profile(account),
                'temporal_pattern': self._check_temporal_pattern(posts),
                'unverified_account': self._check_unverified_account(account)
            }

            # Calculate 5 new comment-based signals
            comment_signals = self._calculate_comment_signals(
                session, account_id, comments, original_posts
            )
            signals.update(comment_signals)

            # Update comment stats for this account
            self._update_comment_stats(session, account_id, account.platform, comments, original_posts)

            # Calculate total score (max is now 22.0)
            total_score = sum(signals.values())
            flagged = total_score >= self.threshold

            # Create score object
            score = Score(
                account_id=account_id,
                total_score=total_score,
                signals=signals,
                flagged=flagged,
                threshold=self.threshold
            )

            # Store score in database
            self._store_score(session, score)

            # Create flags for significant signals
            self._create_flags(session, account_id, signals)

            # Update last_analyzed timestamp
            account.last_analyzed = datetime.now()
            session.commit()

            logger.info(f"Analyzed account {account_id}: score={total_score:.2f}, flagged={flagged}")
            return score

    def _calculate_comment_signals(
        self,
        session,
        account_id: str,
        comments: List[PostDB],
        original_posts: List[PostDB]
    ) -> Dict[str, float]:
        """
        Calculate all 5 comment-based signals.

        Args:
            session: Database session
            account_id: Account ID
            comments: List of comment posts
            original_posts: List of original posts

        Returns:
            Dictionary of comment signal scores
        """
        return {
            'comment_repetitiveness': self._check_comment_repetitiveness(comments),
            'comment_timing': self._check_comment_timing(comments),
            'inflammatory_frequency': self._check_inflammatory_frequency(session, account_id, comments),
            'comment_to_post_ratio': self._check_comment_to_post_ratio(comments, original_posts),
            'comment_engagement_ratio': self._check_comment_engagement_ratio(comments)
        }

    def _check_comment_repetitiveness(self, comments: List[PostDB]) -> float:
        """
        Signal 9: Check for repetitive comments across multiple posts.

        Bots often post the same/similar comments on multiple posts.

        Args:
            comments: List of comment posts

        Returns:
            Signal score (0-2.0)
        """
        if len(comments) < 5:
            return 0.0

        # Get comment contents
        contents = [c.content.lower().strip() for c in comments if c.content]

        if not contents:
            return 0.0

        # Check for exact duplicates
        unique_contents = set(contents)
        duplicate_ratio = 1 - (len(unique_contents) / len(contents))

        # Check for similar content using word overlap (Jaccard similarity)
        word_sets = [set(re.findall(r'\w+', content)) for content in contents]

        # Compare each comment to others
        high_similarity_count = 0
        comparisons = 0

        for i in range(len(word_sets)):
            for j in range(i + 1, min(i + 10, len(word_sets))):  # Compare with next 10
                if word_sets[i] and word_sets[j]:
                    intersection = len(word_sets[i] & word_sets[j])
                    union = len(word_sets[i] | word_sets[j])
                    if union > 0 and intersection / union > 0.7:
                        high_similarity_count += 1
                    comparisons += 1

        similarity_ratio = high_similarity_count / comparisons if comparisons > 0 else 0

        # Score based on ratios
        if duplicate_ratio > 0.5 or similarity_ratio > 0.4:
            return 2.0
        elif duplicate_ratio > 0.3 or similarity_ratio > 0.25:
            return 1.5
        elif duplicate_ratio > 0.15 or similarity_ratio > 0.15:
            return 1.0
        elif duplicate_ratio > 0.05:
            return 0.5

        return 0.0

    def _check_comment_timing(self, comments: List[PostDB]) -> float:
        """
        Signal 10: Check for rapid-fire commenting patterns.

        Bots often post multiple comments in quick succession.

        Args:
            comments: List of comment posts

        Returns:
            Signal score (0-2.5)
        """
        if len(comments) < 3:
            return 0.0

        # Sort by creation time
        sorted_comments = sorted(comments, key=lambda c: c.created_at)

        # Calculate time gaps between consecutive comments
        gaps = []
        rapid_fire_count = 0  # Comments within 30 seconds

        for i in range(1, len(sorted_comments)):
            gap = (sorted_comments[i].created_at - sorted_comments[i-1].created_at).total_seconds()
            gaps.append(gap)

            if gap < 30:  # Less than 30 seconds
                rapid_fire_count += 1

        if not gaps:
            return 0.0

        avg_gap = sum(gaps) / len(gaps)
        rapid_fire_ratio = rapid_fire_count / len(gaps)

        # Very suspicious: many comments in rapid succession
        if rapid_fire_ratio > 0.5 or avg_gap < 60:
            return 2.5
        elif rapid_fire_ratio > 0.3 or avg_gap < 120:
            return 2.0
        elif rapid_fire_ratio > 0.15 or avg_gap < 300:
            return 1.0
        elif rapid_fire_ratio > 0.05:
            return 0.5

        return 0.0

    def _check_inflammatory_frequency(self, session, account_id: str, comments: List[PostDB]) -> float:
        """
        Signal 11: Check what percentage of comments are flagged as inflammatory.

        Args:
            session: Database session
            account_id: Account ID
            comments: List of comment posts

        Returns:
            Signal score (0-2.0)
        """
        total_comments = len(comments)
        if total_comments < 5:
            return 0.0

        # Get inflammatory flag count for this account
        inflammatory_count = session.query(InflammatoryFlagDB).filter_by(
            account_id=account_id
        ).count()

        inflammatory_ratio = inflammatory_count / total_comments

        # High percentage of inflammatory comments is very suspicious
        if inflammatory_ratio > 0.5:
            return 2.0
        elif inflammatory_ratio > 0.3:
            return 1.5
        elif inflammatory_ratio > 0.15:
            return 1.0
        elif inflammatory_ratio > 0.05:
            return 0.5

        return 0.0

    def _check_comment_to_post_ratio(
        self,
        comments: List[PostDB],
        original_posts: List[PostDB]
    ) -> float:
        """
        Signal 12: Check if account only comments (never posts original content).

        "Amplification parasites" typically have very high comment-to-post ratios.

        Args:
            comments: List of comment posts
            original_posts: List of original posts

        Returns:
            Signal score (0-1.5)
        """
        total_content = len(comments) + len(original_posts)

        if total_content < 10:
            return 0.0

        if len(original_posts) == 0:
            # Only comments, never posts - very suspicious
            return 1.5

        ratio = len(comments) / len(original_posts)

        if ratio > 20:  # More than 20 comments per original post
            return 1.5
        elif ratio > 10:
            return 1.0
        elif ratio > 5:
            return 0.5

        return 0.0

    def _check_comment_engagement_ratio(self, comments: List[PostDB]) -> float:
        """
        Signal 13: Check if account's comments receive any engagement.

        Bot comments typically receive very low or no engagement (likes, replies).

        Args:
            comments: List of comment posts

        Returns:
            Signal score (0-1.5)
        """
        if len(comments) < 5:
            return 0.0

        # Calculate total engagement on comments
        total_engagement = 0
        comments_with_engagement = 0

        for comment in comments:
            eng = comment.engagement or {}
            comment_eng = eng.get('likes', 0) + eng.get('replies', 0) + eng.get('score', 0)
            total_engagement += comment_eng
            if comment_eng > 0:
                comments_with_engagement += 1

        avg_engagement = total_engagement / len(comments)
        engagement_ratio = comments_with_engagement / len(comments)

        # Comments that receive zero engagement are suspicious
        if avg_engagement < 0.1 and engagement_ratio < 0.1:
            return 1.5
        elif avg_engagement < 0.5 and engagement_ratio < 0.2:
            return 1.0
        elif avg_engagement < 1.0 and engagement_ratio < 0.3:
            return 0.5

        return 0.0

    def _update_comment_stats(
        self,
        session,
        account_id: str,
        platform: str,
        comments: List[PostDB],
        original_posts: List[PostDB]
    ):
        """
        Update CommentStatsDB with calculated metrics.

        Args:
            session: Database session
            account_id: Account ID
            platform: Platform name
            comments: List of comment posts
            original_posts: List of original posts
        """
        stats = session.query(CommentStatsDB).filter_by(account_id=account_id).first()

        if not stats:
            stats = CommentStatsDB(account_id=account_id, platform=platform)
            session.add(stats)

        # Update counts
        stats.total_comments = len(comments)
        stats.total_original_posts = len(original_posts)

        if len(original_posts) > 0:
            stats.comment_to_post_ratio = len(comments) / len(original_posts)
        else:
            stats.comment_to_post_ratio = float(len(comments)) if comments else 0.0

        # Update repetitiveness metrics
        if comments:
            contents = [c.content.lower().strip() for c in comments if c.content]
            unique_contents = set(contents)
            stats.unique_comment_hashes = len(unique_contents)
            stats.repetitive_comment_count = len(contents) - len(unique_contents)
            stats.repetitiveness_ratio = stats.repetitive_comment_count / len(contents) if contents else 0.0

        # Update timing metrics
        if len(comments) >= 2:
            sorted_comments = sorted(comments, key=lambda c: c.created_at)
            gaps = []
            rapid_fire = 0

            for i in range(1, len(sorted_comments)):
                gap = (sorted_comments[i].created_at - sorted_comments[i-1].created_at).total_seconds()
                gaps.append(gap)
                if gap < 30:
                    rapid_fire += 1

            if gaps:
                stats.avg_seconds_between_comments = sum(gaps) / len(gaps)
                stats.min_seconds_between_comments = min(gaps)
                stats.rapid_fire_instances = rapid_fire

        # Update inflammatory metrics
        inflammatory_count = session.query(InflammatoryFlagDB).filter_by(
            account_id=account_id
        ).count()
        stats.inflammatory_comment_count = inflammatory_count
        stats.inflammatory_ratio = inflammatory_count / len(comments) if comments else 0.0

        # Update engagement metrics
        total_engagement = 0
        comments_with_replies = 0
        for comment in comments:
            eng = comment.engagement or {}
            total_engagement += eng.get('likes', 0) + eng.get('replies', 0) + eng.get('score', 0)
            if eng.get('replies', 0) > 0 or eng.get('comments', 0) > 0:
                comments_with_replies += 1

        stats.total_comment_engagement = total_engagement
        stats.avg_comment_engagement = total_engagement / len(comments) if comments else 0.0
        stats.comments_with_replies = comments_with_replies

        stats.last_updated = datetime.now()

    def _check_new_account(self, account: AccountDB) -> float:
        """
        Check if account is suspiciously new.

        Args:
            account: Account database object

        Returns:
            Signal score (0-2)
        """
        if not account.created_at:
            return 0.0

        account_age = datetime.now() - account.created_at
        new_account_days = self.settings.new_account_days

        if account_age.days < 7:
            return 2.0
        elif account_age.days < new_account_days:
            return 1.0
        return 0.0

    def _check_high_frequency(self, posts: List[PostDB]) -> float:
        """
        Check for suspiciously high posting frequency.

        Args:
            posts: List of post database objects

        Returns:
            Signal score (0-3)
        """
        if not posts:
            return 0.0

        # Analyze last 24 hours of posts
        now = datetime.now()
        recent_posts = [
            p for p in posts
            if (now - p.created_at).total_seconds() < 86400  # 24 hours
        ]

        posts_per_hour = len(recent_posts) / 24.0

        if posts_per_hour > 10:  # More than 10 posts/hour
            return 3.0
        elif posts_per_hour > 5:  # More than 5 posts/hour
            return 2.0
        elif posts_per_hour > 2:  # More than 2 posts/hour
            return 1.0
        return 0.0

    def _check_repetitive_content(self, posts: List[PostDB]) -> float:
        """
        Check for repetitive or duplicate content.

        Args:
            posts: List of post database objects

        Returns:
            Signal score (0-2.5)
        """
        if len(posts) < 5:
            return 0.0

        # Get recent posts (last 100)
        recent_posts = sorted(posts, key=lambda p: p.created_at, reverse=True)[:100]
        contents = [p.content.lower().strip() for p in recent_posts]

        # Check for exact duplicates
        duplicate_count = len(contents) - len(set(contents))
        duplicate_ratio = duplicate_count / len(contents) if contents else 0

        # Check for very similar content (same words)
        word_sets = [set(re.findall(r'\w+', content)) for content in contents]
        similarity_scores = []

        for i in range(len(word_sets)):
            for j in range(i + 1, min(i + 10, len(word_sets))):  # Compare with next 10
                intersection = len(word_sets[i] & word_sets[j])
                union = len(word_sets[i] | word_sets[j])
                if union > 0:
                    similarity_scores.append(intersection / union)

        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0

        if duplicate_ratio > 0.3 or avg_similarity > 0.7:
            return 2.5
        elif duplicate_ratio > 0.1 or avg_similarity > 0.5:
            return 1.5
        elif duplicate_ratio > 0.05 or avg_similarity > 0.3:
            return 0.5
        return 0.0

    def _check_low_engagement(self, account: AccountDB, posts: List[PostDB]) -> float:
        """
        Check for suspiciously low engagement relative to post volume.

        Args:
            account: Account database object
            posts: List of post database objects

        Returns:
            Signal score (0-1.5)
        """
        if not posts or len(posts) < 10:
            return 0.0

        # Calculate average engagement per post
        total_engagement = 0
        for post in posts:
            eng = post.engagement or {}
            total_engagement += eng.get('likes', 0)
            total_engagement += eng.get('reposts', 0)
            total_engagement += eng.get('replies', 0)
            total_engagement += eng.get('score', 0)
            total_engagement += eng.get('comments', 0)

        avg_engagement = total_engagement / len(posts)

        # High post count but low engagement is suspicious
        if account.post_count > 100 and avg_engagement < 1:
            return 1.5
        elif account.post_count > 50 and avg_engagement < 2:
            return 1.0
        elif account.post_count > 20 and avg_engagement < 3:
            return 0.5
        return 0.0

    def _check_generic_username(self, account: AccountDB) -> float:
        """
        Check for generic or bot-like username patterns.

        Args:
            account: Account database object

        Returns:
            Signal score (0-1)
        """
        username = account.username.lower()

        # Common bot patterns
        bot_patterns = [
            r'^[a-z]+\d{4,}$',  # wordNNNN
            r'^[a-z]+_[a-z]+\d+$',  # word_wordNN
            r'^\w+bot\w*$',  # contains 'bot'
            r'^user\d+$',  # userNNN
            r'^[a-z]{1,3}\d{6,}$',  # short letters + many numbers
        ]

        for pattern in bot_patterns:
            if re.match(pattern, username):
                return 1.0

        # Very short or very long usernames
        if len(username) < 3 or len(username) > 30:
            return 0.5

        return 0.0

    def _check_incomplete_profile(self, account: AccountDB) -> float:
        """
        Check for incomplete profile (missing bio, avatar, etc.).

        Args:
            account: Account database object

        Returns:
            Signal score (0-1)
        """
        # Extract platform-specific metadata for profile completeness check
        # Bluesky: checks description, avatar
        # Hacker News: checks about, karma
        metadata = account.platform_metadata or {}

        # Platform-specific checks
        if account.platform == 'bluesky':
            has_description = bool(metadata.get('description'))
            has_avatar = bool(metadata.get('avatar'))

            if not has_description and not has_avatar:
                return 1.0
            elif not has_description or not has_avatar:
                return 0.5

        elif account.platform == 'hackernews':
            has_about = bool(metadata.get('about'))
            karma = metadata.get('karma', 0)

            if not has_about and karma < 10:
                return 1.0
            elif not has_about or karma < 5:
                return 0.5

        return 0.0

    def _check_temporal_pattern(self, posts: List[PostDB]) -> float:
        """
        Check for suspicious temporal posting patterns (24/7 posting, exact intervals).

        Args:
            posts: List of post database objects

        Returns:
            Signal score (0-1)
        """
        if len(posts) < 20:
            return 0.0

        # Get posting hours
        hours = [p.created_at.hour for p in posts]
        hour_distribution = Counter(hours)

        # Check if posting is too evenly distributed (bots post 24/7)
        unique_hours = len(hour_distribution)
        if unique_hours > 20:  # Posting in more than 20 different hours
            return 1.0
        elif unique_hours > 16:
            return 0.5

        return 0.0

    def _check_unverified_account(self, account: AccountDB) -> float:
        """
        Check if account lacks verification (platform-specific).

        Args:
            account: Account database object

        Returns:
            Signal score (0-1.5)
        """
        metadata = account.platform_metadata or {}

        # Platform-specific verification checks
        if account.platform == 'bluesky':
            # Bluesky has a 'verified' field in metadata
            is_verified = metadata.get('verified', False)

            if is_verified:
                # Verified accounts are less likely to be bots
                return 0.0
            else:
                # Unverified accounts get moderate suspicion
                # Higher weight if account is also new
                if account.created_at:
                    account_age_days = (datetime.now() - account.created_at).days
                    if account_age_days < 7:
                        return 1.5  # Very new + unverified = more suspicious
                    elif account_age_days < 30:
                        return 1.0  # Somewhat new + unverified
                return 0.5  # Older but still unverified

        elif account.platform == 'hackernews':
            # HN doesn't have formal verification, but high karma is a trust signal
            karma = metadata.get('karma', 0)

            if karma >= 1000:  # High karma = established user
                return 0.0
            elif karma >= 100:
                return 0.3
            elif karma >= 10:
                return 0.7
            else:
                return 1.5  # Very low/no karma

        return 0.0

    def _store_score(self, session, score: Score):
        """
        Store score in database.

        Args:
            session: Database session
            score: Score object to store
        """
        score_db = session.query(ScoreDB).filter_by(account_id=score.account_id).first()

        if score_db:
            # Update existing score
            score_db.total_score = score.total_score
            score_db.signals = score.signals
            score_db.flagged = 1 if score.flagged else 0
            score_db.threshold = score.threshold
            score_db.last_updated = datetime.now()
        else:
            # Create new score
            score_db = ScoreDB(
                account_id=score.account_id,
                total_score=score.total_score,
                signals=score.signals,
                flagged=1 if score.flagged else 0,
                threshold=score.threshold,
                last_updated=datetime.now()
            )
            session.add(score_db)

    def _create_flags(self, session, account_id: str, signals: Dict[str, float]):
        """
        Create flags for significant signals.

        Args:
            session: Database session
            account_id: Account ID
            signals: Signal scores dictionary
        """
        # Only flag signals with score >= 1.0
        significant_signals = {k: v for k, v in signals.items() if v >= 1.0}

        for signal_name, signal_score in significant_signals.items():
            # Create flag
            flag_db = FlagDB(
                account_id=account_id,
                flag_type=signal_name,
                confidence_score=signal_score / 3.0,  # Normalize to 0-1
                reason=self._get_flag_reason(signal_name, signal_score),
                timestamp=datetime.now()
            )
            session.add(flag_db)

    def _get_flag_reason(self, signal_name: str, score: float) -> str:
        """
        Get human-readable reason for a flag.

        Args:
            signal_name: Name of the signal
            score: Signal score

        Returns:
            Human-readable reason string
        """
        reasons = {
            # Original 8 signals
            'new_account': f'Account is very new (score: {score:.1f}/2.0)',
            'high_frequency': f'Posting frequency is unusually high (score: {score:.1f}/3.0)',
            'repetitive_content': f'Content is highly repetitive (score: {score:.1f}/2.5)',
            'low_engagement': f'Low engagement relative to post volume (score: {score:.1f}/1.5)',
            'generic_username': f'Username follows generic bot pattern (score: {score:.1f}/1.0)',
            'incomplete_profile': f'Profile is incomplete or minimal (score: {score:.1f}/1.0)',
            'temporal_pattern': f'Posting pattern suggests automation (score: {score:.1f}/1.0)',
            'unverified_account': f'Account lacks verification or trust signals (score: {score:.1f}/1.5)',
            # New 5 comment-based signals
            'comment_repetitiveness': f'Comments are highly repetitive across posts (score: {score:.1f}/2.0)',
            'comment_timing': f'Rapid-fire commenting pattern detected (score: {score:.1f}/2.5)',
            'inflammatory_frequency': f'High percentage of inflammatory comments (score: {score:.1f}/2.0)',
            'comment_to_post_ratio': f'Account primarily comments, rarely posts original content (score: {score:.1f}/1.5)',
            'comment_engagement_ratio': f'Comments receive very little engagement (score: {score:.1f}/1.5)'
        }
        return reasons.get(signal_name, f'{signal_name}: {score:.1f}')

    def analyze_all_accounts(self, platform: Optional[str] = None) -> List[Score]:
        """
        Analyze all accounts in database.

        Args:
            platform: Optional platform filter

        Returns:
            List of Score objects
        """
        db = get_database()
        scores = []

        with db.get_session() as session:
            query = session.query(AccountDB)
            if platform:
                query = query.filter_by(platform=platform)

            accounts = query.all()

            for account in accounts:
                try:
                    score = self.analyze_account(account.id)
                    if score:
                        scores.append(score)
                except Exception as e:
                    logger.error(f"Error analyzing account {account.id}: {e}")

        logger.info(f"Analyzed {len(scores)} accounts")
        return scores
