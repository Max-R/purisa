"""Bluesky platform adapter using atproto."""
from atproto import Client
from typing import List
from datetime import datetime
import logging
from .base import SocialPlatform
from purisa.models.account import Account
from purisa.models.post import Post

logger = logging.getLogger(__name__)


def _parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO timestamp with support for nanosecond precision.

    Python's fromisoformat only supports up to microseconds (6 digits),
    but atproto may return nanoseconds (9 digits). This truncates to 6.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        datetime object
    """
    # Replace Z with +00:00 for proper timezone handling
    timestamp_str = timestamp_str.replace('Z', '+00:00')

    # Check if we have fractional seconds with more than 6 digits
    if '.' in timestamp_str:
        parts = timestamp_str.split('.')
        if len(parts) == 2:
            # Get fractional part and timezone
            fractional_and_tz = parts[1]

            # Find where timezone starts (+ or -)
            tz_start = max(fractional_and_tz.find('+'), fractional_and_tz.find('-'))
            if tz_start > 0:
                fractional = fractional_and_tz[:tz_start]
                timezone = fractional_and_tz[tz_start:]

                # Truncate fractional to 6 digits
                if len(fractional) > 6:
                    fractional = fractional[:6]
                    timestamp_str = f"{parts[0]}.{fractional}{timezone}"

    return datetime.fromisoformat(timestamp_str)


class BlueskyPlatform(SocialPlatform):
    """Bluesky platform adapter using the AT Protocol library."""

    def __init__(self, config: dict):
        """
        Initialize Bluesky client with credentials.

        Args:
            config: Configuration dict with 'handle' and 'password' keys
        """
        self.client = Client()
        try:
            self.client.login(config['handle'], config['password'])
            logger.info(f"Successfully logged into Bluesky as {config['handle']}")
        except Exception as e:
            logger.error(f"Failed to login to Bluesky: {e}")
            raise

    async def collect_posts(self, query: str, limit: int) -> List[Post]:
        """
        Collect posts from Bluesky timeline or search.

        Uses pagination to handle limits greater than 100 (API maximum per request).

        Args:
            query: Search query (hashtag or keyword)
            limit: Maximum number of posts to collect

        Returns:
            List of Post objects
        """
        try:
            posts = []
            cursor = None
            max_per_request = 100

            while len(posts) < limit:
                # Calculate how many to fetch this request
                remaining = limit - len(posts)
                fetch_limit = min(remaining, max_per_request)

                params = {'q': query, 'limit': fetch_limit}
                if cursor:
                    params['cursor'] = cursor

                results = self.client.app.bsky.feed.search_posts(params=params)

                if not results.posts:
                    break

                for post in results.posts:
                    posts.append(self._transform_post(post))

                # Check if there are more results
                cursor = getattr(results, 'cursor', None)
                if not cursor:
                    break

                logger.debug(f"Fetched {len(posts)}/{limit} posts from Bluesky")

            logger.info(f"Collected {len(posts)} posts from Bluesky for query: {query}")
            return posts

        except Exception as e:
            logger.error(f"Error collecting posts from Bluesky: {e}")
            raise

    async def get_account_info(self, username: str) -> Account:
        """
        Get Bluesky account/profile info.

        Args:
            username: Bluesky handle (e.g., 'user.bsky.social')

        Returns:
            Account object with profile information
        """
        try:
            profile = self.client.app.bsky.actor.get_profile(params={'actor': username})
            account = self._transform_account(profile)
            logger.info(f"Retrieved account info for Bluesky user: {username}")
            return account

        except Exception as e:
            logger.error(f"Error getting account info from Bluesky: {e}")
            raise

    async def get_account_history(self, username: str, limit: int) -> List[Post]:
        """
        Get user's post history.

        Uses pagination to handle limits greater than 100 (API maximum per request).

        Args:
            username: Bluesky handle
            limit: Maximum number of posts to retrieve

        Returns:
            List of Post objects from user's history
        """
        try:
            posts = []
            cursor = None
            max_per_request = 100

            while len(posts) < limit:
                # Calculate how many to fetch this request
                remaining = limit - len(posts)
                fetch_limit = min(remaining, max_per_request)

                params = {'actor': username, 'limit': fetch_limit}
                if cursor:
                    params['cursor'] = cursor

                feed = self.client.app.bsky.feed.get_author_feed(params=params)

                if not feed.feed:
                    break

                for item in feed.feed:
                    posts.append(self._transform_post(item.post))

                # Check if there are more results
                cursor = getattr(feed, 'cursor', None)
                if not cursor:
                    break

                logger.debug(f"Fetched {len(posts)}/{limit} posts from Bluesky user: {username}")

            logger.info(f"Retrieved {len(posts)} posts from Bluesky user: {username}")
            return posts

        except Exception as e:
            logger.error(f"Error getting account history from Bluesky: {e}")
            raise

    async def search_posts(self, query: str, limit: int) -> List[Post]:
        """
        Search posts by keyword.

        Args:
            query: Search query string
            limit: Maximum number of posts to return

        Returns:
            List of Post objects matching query
        """
        return await self.collect_posts(query, limit)

    async def get_post_comments(self, post_uri: str, limit: int) -> List[Post]:
        """
        Get replies/comments for a Bluesky post.

        Uses app.bsky.feed.getPostThread to retrieve the thread with replies.

        Args:
            post_uri: AT Protocol URI of the post
            limit: Maximum number of comments to retrieve

        Returns:
            List of Post objects representing comments
        """
        try:
            comments = []

            # Get thread with replies (depth controls how deep to traverse)
            thread = self.client.app.bsky.feed.get_post_thread(
                params={'uri': post_uri, 'depth': 10}
            )

            # Extract replies from thread
            if hasattr(thread.thread, 'replies') and thread.thread.replies:
                self._extract_replies_recursive(
                    thread.thread.replies,
                    parent_uri=post_uri,
                    limit=limit,
                    collected=comments
                )

            logger.info(f"Collected {len(comments)} comments from Bluesky post: {post_uri}")
            return comments[:limit]

        except Exception as e:
            logger.error(f"Error getting comments from Bluesky post {post_uri}: {e}")
            raise

    def _extract_replies_recursive(
        self,
        replies: list,
        parent_uri: str,
        limit: int,
        collected: List[Post]
    ) -> None:
        """
        Recursively extract replies from a thread.

        Args:
            replies: List of reply objects from the thread
            parent_uri: URI of the parent post
            limit: Maximum total comments to collect
            collected: List to append collected comments to
        """
        for reply in replies:
            if len(collected) >= limit:
                break

            if hasattr(reply, 'post'):
                post = self._transform_post(reply.post)
                # Add parent info to metadata
                post.metadata['parent_uri'] = parent_uri
                post.metadata['post_type'] = 'comment'
                collected.append(post)

                # Recursively get nested replies
                if hasattr(reply, 'replies') and reply.replies:
                    self._extract_replies_recursive(
                        reply.replies,
                        parent_uri=post.id,  # This reply becomes the parent
                        limit=limit,
                        collected=collected
                    )

    def get_engagement_score(self, post: Post) -> float:
        """
        Calculate normalized engagement score for a Bluesky post.

        Formula: (likes + reposts*2 + replies*1.5) / normalization_factor

        Args:
            post: Post object with engagement metrics

        Returns:
            Normalized score between 0.0 and 1.0
        """
        eng = post.engagement or {}
        raw_score = (
            eng.get('likes', 0) +
            eng.get('reposts', 0) * 2 +
            eng.get('replies', 0) * 1.5
        )
        # Normalize: assume 1000 is "very high" engagement for Bluesky
        return min(raw_score / 1000.0, 1.0)

    def _transform_post(self, post) -> Post:
        """
        Transform Bluesky post to generic Post model.

        Args:
            post: Bluesky post object from atproto

        Returns:
            Generic Post object
        """
        # Parse timestamp (handles nanosecond precision from newer atproto)
        created_at = _parse_timestamp(post.record.created_at)

        return Post(
            id=post.uri,
            account_id=post.author.did,
            platform='bluesky',
            content=post.record.text,
            created_at=created_at,
            engagement={
                'likes': post.like_count or 0,
                'reposts': post.repost_count or 0,
                'replies': post.reply_count or 0
            },
            metadata={
                'uri': post.uri,
                'cid': post.cid,
                'author_handle': post.author.handle,
                'author_display_name': post.author.display_name or '',
                'langs': getattr(post.record, 'langs', [])
            }
        )

    def _transform_account(self, profile) -> Account:
        """
        Transform Bluesky profile to generic Account model.

        Args:
            profile: Bluesky profile object from atproto

        Returns:
            Generic Account object
        """
        # Note: Bluesky doesn't directly expose account creation date via API
        # Using current time as placeholder - this should be improved
        return Account(
            id=profile.did,
            username=profile.handle,
            display_name=profile.display_name or '',
            platform='bluesky',
            created_at=datetime.now(),  # Limitation: creation date not available
            follower_count=profile.followers_count or 0,
            following_count=profile.follows_count or 0,
            post_count=profile.posts_count or 0,
            metadata={
                'did': profile.did,
                'description': profile.description or '',
                'avatar': profile.avatar or '',
                'banner': getattr(profile, 'banner', ''),
                'verified': getattr(profile, 'verified', False)
            }
        )
