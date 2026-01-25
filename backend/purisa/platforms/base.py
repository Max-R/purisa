"""Base platform abstraction for all social media platforms."""
from abc import ABC, abstractmethod
from typing import List, Optional
from purisa.models.account import Account
from purisa.models.post import Post


class SocialPlatform(ABC):
    """Abstract base class for social media platform adapters."""

    @abstractmethod
    async def collect_posts(self, query: str, limit: int) -> List[Post]:
        """
        Collect posts based on query (hashtag, keyword, etc.).

        Args:
            query: Search query (hashtag, keyword, or other platform-specific query)
            limit: Maximum number of posts to collect

        Returns:
            List of Post objects
        """
        pass

    @abstractmethod
    async def get_account_info(self, username: str) -> Account:
        """
        Get account metadata for a specific user.

        Args:
            username: Username/handle to look up

        Returns:
            Account object with user information
        """
        pass

    @abstractmethod
    async def get_account_history(self, username: str, limit: int) -> List[Post]:
        """
        Get posting history for an account.

        Args:
            username: Username/handle to look up
            limit: Maximum number of posts to retrieve

        Returns:
            List of Post objects from user's history
        """
        pass

    @abstractmethod
    async def search_posts(self, query: str, limit: int) -> List[Post]:
        """
        Search for posts matching query.

        Args:
            query: Search query string
            limit: Maximum number of posts to return

        Returns:
            List of Post objects matching query
        """
        pass

    @abstractmethod
    async def get_post_comments(self, post_id: str, limit: int) -> List[Post]:
        """
        Get comments/replies for a specific post.

        Args:
            post_id: Platform-specific post identifier
            limit: Maximum number of comments to retrieve

        Returns:
            List of Post objects representing comments (with parent_id in metadata)
        """
        pass

    @abstractmethod
    def get_engagement_score(self, post: Post) -> float:
        """
        Calculate normalized engagement score for a post (0.0-1.0).

        Platform-specific implementation to handle different engagement metrics.
        Used to identify top-performing posts for comment harvesting.

        Args:
            post: Post object with engagement metrics

        Returns:
            Normalized engagement score between 0.0 and 1.0
        """
        pass
