"""Hacker News platform adapter using Firebase API."""
import httpx
from typing import List, Optional
from datetime import datetime
import logging
from .base import SocialPlatform
from purisa.models.account import Account
from purisa.models.post import Post

logger = logging.getLogger(__name__)


class HackerNewsPlatform(SocialPlatform):
    """Hacker News platform adapter using the Firebase API."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, config: dict):
        """
        Initialize Hacker News client.

        Args:
            config: Configuration dict (not used for HN, no auth required)
        """
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("Initialized Hacker News platform adapter")

    async def collect_posts(self, query: str, limit: int) -> List[Post]:
        """
        Collect top/new stories from HN.

        Args:
            query: Collection type ('top', 'new', 'best', 'ask', 'show', 'job')
            limit: Maximum number of posts to collect

        Returns:
            List of Post objects
        """
        try:
            # Determine which endpoint to use based on query
            endpoint_map = {
                'top': 'topstories',
                'new': 'newstories',
                'best': 'beststories',
                'ask': 'askstories',
                'show': 'showstories',
                'job': 'jobstories'
            }

            endpoint = endpoint_map.get(query.lower(), 'topstories')

            # Get story IDs
            response = await self.client.get(f"{self.BASE_URL}/{endpoint}.json")
            response.raise_for_status()
            story_ids = response.json()[:limit]

            # Fetch individual stories
            posts = []
            for story_id in story_ids:
                story = await self._get_item(story_id)
                if story and story.get('type') in ('story', 'poll'):
                    posts.append(self._transform_post(story))

            logger.info(f"Collected {len(posts)} posts from Hacker News ({endpoint})")
            return posts

        except Exception as e:
            logger.error(f"Error collecting posts from Hacker News: {e}")
            raise

    async def get_account_info(self, username: str) -> Account:
        """
        Get HN user info.

        Args:
            username: Hacker News username

        Returns:
            Account object with user information
        """
        try:
            response = await self.client.get(f"{self.BASE_URL}/user/{username}.json")
            response.raise_for_status()
            user_data = response.json()

            if not user_data:
                raise ValueError(f"User not found: {username}")

            account = self._transform_account(user_data)
            logger.info(f"Retrieved account info for HN user: {username}")
            return account

        except Exception as e:
            logger.error(f"Error getting account info from Hacker News: {e}")
            raise

    async def get_account_history(self, username: str, limit: int) -> List[Post]:
        """
        Get user's submission history.

        Args:
            username: Hacker News username
            limit: Maximum number of posts to retrieve

        Returns:
            List of Post objects from user's history
        """
        try:
            user_response = await self.client.get(f"{self.BASE_URL}/user/{username}.json")
            user_response.raise_for_status()
            user_data = user_response.json()

            if not user_data:
                raise ValueError(f"User not found: {username}")

            # Get submitted item IDs
            submitted_ids = user_data.get('submitted', [])[:limit]

            # Fetch individual items
            posts = []
            for item_id in submitted_ids:
                item = await self._get_item(item_id)
                if item and item.get('type') in ('story', 'comment', 'poll'):
                    posts.append(self._transform_post(item))

            logger.info(f"Retrieved {len(posts)} posts from HN user: {username}")
            return posts

        except Exception as e:
            logger.error(f"Error getting account history from Hacker News: {e}")
            raise

    async def search_posts(self, query: str, limit: int) -> List[Post]:
        """
        Search posts by keyword.

        Note: HN Firebase API doesn't support keyword search.
        This implementation returns top stories as a fallback.
        For real search, integrate with Algolia HN Search API.

        Args:
            query: Search query string
            limit: Maximum number of posts to return

        Returns:
            List of Post objects (top stories as fallback)
        """
        logger.warning("HN Firebase API doesn't support search. Returning top stories.")
        return await self.collect_posts('top', limit)

    async def get_post_comments(self, story_id: str, limit: int) -> List[Post]:
        """
        Get comments for a Hacker News story.

        HN uses 'kids' array containing comment IDs for each item.

        Args:
            story_id: HN story ID as string
            limit: Maximum number of comments to retrieve

        Returns:
            List of Post objects representing comments
        """
        try:
            # Get story to find comment IDs
            story = await self._get_item(int(story_id))
            if not story or 'kids' not in story:
                logger.info(f"No comments found for HN story: {story_id}")
                return []

            comments = []
            await self._fetch_comments_recursive(
                comment_ids=story.get('kids', []),
                parent_id=story_id,
                limit=limit,
                comments=comments,
                depth=0
            )

            logger.info(f"Collected {len(comments)} comments from HN story: {story_id}")
            return comments[:limit]

        except Exception as e:
            logger.error(f"Error getting comments from HN story {story_id}: {e}")
            raise

    async def _fetch_comments_recursive(
        self,
        comment_ids: List[int],
        parent_id: str,
        limit: int,
        comments: List[Post],
        depth: int = 0
    ) -> None:
        """
        Recursively fetch HN comments.

        Args:
            comment_ids: List of comment IDs to fetch
            parent_id: ID of the parent item
            limit: Maximum total comments to collect
            comments: List to append collected comments to
            depth: Current recursion depth
        """
        if depth > 5 or len(comments) >= limit:
            return

        for comment_id in comment_ids:
            if len(comments) >= limit:
                break

            item = await self._get_item(comment_id)
            if not item or item.get('type') != 'comment' or item.get('deleted'):
                continue

            post = self._transform_comment(item, parent_id)
            comments.append(post)

            # Recursively get nested comments
            if 'kids' in item:
                await self._fetch_comments_recursive(
                    comment_ids=item['kids'],
                    parent_id=str(comment_id),
                    limit=limit,
                    comments=comments,
                    depth=depth + 1
                )

    def _transform_comment(self, item: dict, parent_id: str) -> Post:
        """
        Transform HN comment to Post model.

        Args:
            item: HN comment item dict from API
            parent_id: ID of the parent item

        Returns:
            Post object representing the comment
        """
        created_at = datetime.fromtimestamp(item['time'])

        return Post(
            id=str(item['id']),
            account_id=item.get('by', 'unknown'),
            platform='hackernews',
            content=item.get('text', '[deleted]'),
            created_at=created_at,
            engagement={
                'score': 0,  # HN comments don't have visible scores
                'comments': len(item.get('kids', []))  # Count of child comments
            },
            metadata={
                'type': 'comment',
                'parent_id': parent_id,
                'post_type': 'comment',
                'dead': item.get('dead', False),
                'deleted': item.get('deleted', False)
            }
        )

    def get_engagement_score(self, post: Post) -> float:
        """
        Calculate normalized engagement score for a HN post.

        Uses score and descendant count.

        Args:
            post: Post object with engagement metrics

        Returns:
            Normalized score between 0.0 and 1.0
        """
        eng = post.engagement or {}
        raw_score = eng.get('score', 0) + eng.get('comments', 0) * 0.5
        # Normalize: assume 500 is "very high" for HN
        return min(raw_score / 500.0, 1.0)

    async def _get_item(self, item_id: int) -> Optional[dict]:
        """
        Get individual item from HN.

        Args:
            item_id: Item ID to fetch

        Returns:
            Item data as dict, or None if not found
        """
        try:
            response = await self.client.get(f"{self.BASE_URL}/item/{item_id}.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch HN item {item_id}: {e}")
            return None

    def _transform_post(self, item: dict) -> Post:
        """
        Transform HN item to generic Post model.

        Args:
            item: HN item dict from API

        Returns:
            Generic Post object
        """
        # Combine title and text for content
        content_parts = []
        if item.get('title'):
            content_parts.append(item['title'])
        if item.get('text'):
            content_parts.append(item['text'])

        content = '\n'.join(content_parts) if content_parts else '[No content]'

        # Parse timestamp
        created_at = datetime.fromtimestamp(item['time'])

        return Post(
            id=str(item['id']),
            account_id=item.get('by', 'unknown'),
            platform='hackernews',
            content=content,
            created_at=created_at,
            engagement={
                'score': item.get('score', 0),
                'comments': item.get('descendants', 0)
            },
            metadata={
                'url': item.get('url', ''),
                'type': item.get('type', 'unknown'),
                'descendants': item.get('descendants', 0),
                'dead': item.get('dead', False),
                'deleted': item.get('deleted', False)
            }
        )

    def _transform_account(self, user: dict) -> Account:
        """
        Transform HN user to generic Account model.

        Args:
            user: HN user dict from API

        Returns:
            Generic Account object
        """
        # Parse timestamp
        created_at = datetime.fromtimestamp(user['created'])

        return Account(
            id=user['id'],
            username=user['id'],
            display_name=user['id'],  # HN doesn't have separate display names
            platform='hackernews',
            created_at=created_at,
            follower_count=0,  # HN doesn't have followers
            following_count=0,  # HN doesn't have following
            post_count=len(user.get('submitted', [])),
            metadata={
                'karma': user.get('karma', 0),
                'about': user.get('about', '')
            }
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
