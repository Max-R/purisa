"""
SQLAlchemy database models for Purisa.

Note on naming: The column 'platform_metadata' stores platform-specific
attributes. It cannot be named 'metadata' as that is a reserved attribute
in SQLAlchemy's declarative base. The API continues to expose this field
as 'metadata' for consistency with the Pydantic models.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class AccountDB(Base):
    """
    Database model for accounts/users.

    Stores user account information collected from various social media platforms.
    The platform_metadata field contains platform-specific attributes that don't
    fit into the standard schema.

    Platform-specific metadata examples:

    Bluesky accounts include:
      - did: Decentralized identifier
      - description: User bio/description
      - avatar: Avatar image URL
      - banner: Banner image URL (optional)
      - verified: Verification status

    Hacker News accounts include:
      - karma: User's karma score
      - about: User's about/bio section
    """

    __tablename__ = 'accounts'

    id = Column(String, primary_key=True)                       # Platform-specific unique identifier (DID for Bluesky, username for HN)
    username = Column(String, nullable=False)                   # Username or handle
    display_name = Column(String)                               # Display name (if different from username)
    platform = Column(String, nullable=False)                   # Platform name: 'bluesky', 'hackernews', etc.
    created_at = Column(DateTime)                               # Account creation timestamp (from platform)
    follower_count = Column(Integer, default=0)                 # Number of followers
    following_count = Column(Integer, default=0)                # Number of accounts following
    post_count = Column(Integer, default=0)                     # Total number of posts/submissions
    platform_metadata = Column(JSON, default=dict)              # Platform-specific attributes (see class docstring)
    first_seen = Column(DateTime, default=datetime.now)         # When account was first collected by Purisa
    last_analyzed = Column(DateTime)                            # Last bot detection analysis timestamp

    # Indexes
    __table_args__ = (
        Index('idx_accounts_platform', 'platform'),
        Index('idx_accounts_username_platform', 'username', 'platform'),
    )


class PostDB(Base):
    """
    Database model for posts/submissions and comments.

    Stores posts/submissions collected from various social media platforms.
    Also stores comments with parent_id set to the parent post/comment.
    The platform_metadata field contains platform-specific attributes unique
    to each platform's post structure.

    Platform-specific metadata examples:

    Bluesky posts include:
      - uri: AT Protocol URI
      - cid: Content identifier
      - author_handle: Author's handle
      - author_display_name: Author's display name
      - langs: Array of language codes

    Hacker News posts include:
      - url: External URL (for link submissions)
      - type: Item type (story, comment, poll, etc.)
      - descendants: Number of descendants/comments
      - dead: Whether item is dead/flagged
      - deleted: Whether item is deleted
    """

    __tablename__ = 'posts'

    id = Column(String, primary_key=True)                                       # Platform-specific unique identifier
    account_id = Column(String, ForeignKey('accounts.id'), nullable=False)      # Foreign key to accounts table
    platform = Column(String, nullable=False)                                   # Platform name: 'bluesky', 'hackernews', etc.
    content = Column(Text)                                                      # Post content/text
    created_at = Column(DateTime, nullable=False)                               # Post creation timestamp (from platform)
    engagement = Column(JSON, default=dict)                                     # Engagement metrics: likes, reposts, comments, score
    platform_metadata = Column(JSON, default=dict)                              # Platform-specific attributes (see class docstring)
    collected_at = Column(DateTime, default=datetime.now)                       # When post was collected by Purisa

    # Comment-related columns
    parent_id = Column(String, ForeignKey('posts.id'), nullable=True)           # Parent post ID (NULL for top-level posts)
    post_type = Column(String, default='post')                                  # 'post' or 'comment'
    is_top_performer = Column(Integer, default=0)                               # 1 if identified as high-engagement post
    comments_collected = Column(Integer, default=0)                             # 1 if comments have been harvested
    comments_collected_at = Column(DateTime, nullable=True)                     # When comments were last collected

    # Indexes
    __table_args__ = (
        Index('idx_posts_account', 'account_id'),
        Index('idx_posts_platform', 'platform'),
        Index('idx_posts_created', 'created_at'),
        Index('idx_posts_parent', 'parent_id'),
        Index('idx_posts_type', 'post_type'),
        Index('idx_posts_top_performer', 'is_top_performer'),
    )


class FlagDB(Base):
    """Database model for detection flags."""

    __tablename__ = 'flags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey('accounts.id'), nullable=False)
    flag_type = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    reason = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

    # Indexes
    __table_args__ = (
        Index('idx_flags_account', 'account_id'),
        Index('idx_flags_timestamp', 'timestamp'),
    )


class ScoreDB(Base):
    """Database model for bot detection scores."""

    __tablename__ = 'scores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey('accounts.id'), nullable=False, unique=True)
    total_score = Column(Float, nullable=False)
    signals = Column(JSON, default=dict)
    flagged = Column(Integer, default=0)  # SQLite uses 0/1 for boolean
    threshold = Column(Float, default=7.0)
    last_updated = Column(DateTime, default=datetime.now)

    # Indexes
    __table_args__ = (
        Index('idx_scores_account', 'account_id'),
        Index('idx_scores_flagged', 'flagged'),
    )


class InflammatoryFlagDB(Base):
    """
    Database model for inflammatory content detections.

    Tracks comments flagged as inflammatory by the Detoxify ML model,
    linking them to the account and parent post for analysis.
    """

    __tablename__ = 'inflammatory_flags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String, ForeignKey('posts.id'), nullable=False)            # The comment that was flagged
    account_id = Column(String, ForeignKey('accounts.id'), nullable=False)      # Author of the comment
    parent_post_id = Column(String, ForeignKey('posts.id'), nullable=True)      # Top-level post being commented on
    platform = Column(String, nullable=False)
    toxicity_scores = Column(JSON, default=dict)                                # Full Detoxify output scores
    triggered_categories = Column(JSON, default=list)                           # Categories above threshold
    severity_score = Column(Float, nullable=False)                              # Max toxicity score (0.0-1.0)
    content_snippet = Column(Text)                                              # First 200 chars of flagged content
    detected_at = Column(DateTime, default=datetime.now)
    analysis_triggered = Column(Integer, default=0)                             # 1 if account analysis was queued

    # Indexes
    __table_args__ = (
        Index('idx_inflammatory_account', 'account_id'),
        Index('idx_inflammatory_post', 'post_id'),
        Index('idx_inflammatory_parent', 'parent_post_id'),
        Index('idx_inflammatory_detected', 'detected_at'),
        Index('idx_inflammatory_severity', 'severity_score'),
    )


class CommentStatsDB(Base):
    """
    Database model for aggregated comment statistics per account.

    Pre-computed metrics for efficient scoring during bot detection.
    Updated each time an account is analyzed.
    """

    __tablename__ = 'comment_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey('accounts.id'), nullable=False, unique=True)
    platform = Column(String, nullable=False)

    # Comment behavior metrics
    total_comments = Column(Integer, default=0)
    total_original_posts = Column(Integer, default=0)
    comment_to_post_ratio = Column(Float, default=0.0)

    # Repetitiveness metrics
    unique_comment_hashes = Column(Integer, default=0)                          # Count of unique comments
    repetitive_comment_count = Column(Integer, default=0)                       # Count of duplicate/similar comments
    repetitiveness_ratio = Column(Float, default=0.0)

    # Timing metrics
    avg_seconds_between_comments = Column(Float, nullable=True)
    min_seconds_between_comments = Column(Float, nullable=True)
    rapid_fire_instances = Column(Integer, default=0)                           # Comments within 30 seconds of each other

    # Inflammatory metrics
    inflammatory_comment_count = Column(Integer, default=0)
    inflammatory_ratio = Column(Float, default=0.0)

    # Engagement received on comments
    total_comment_engagement = Column(Integer, default=0)                       # Likes/upvotes received on comments
    avg_comment_engagement = Column(Float, default=0.0)
    comments_with_replies = Column(Integer, default=0)

    last_updated = Column(DateTime, default=datetime.now)

    # Indexes
    __table_args__ = (
        Index('idx_comment_stats_account', 'account_id'),
        Index('idx_comment_stats_platform', 'platform'),
    )
