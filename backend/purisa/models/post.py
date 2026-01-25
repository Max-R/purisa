"""Post data model for all platforms."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any


class Post(BaseModel):
    """Generic post/submission model that works across all platforms."""

    id: str = Field(..., description="Platform-specific unique identifier")
    account_id: str = Field(..., description="ID of account that created this post")
    platform: str = Field(..., description="Platform name (bluesky, hackernews, etc.)")
    content: str = Field(..., description="Post content/text")
    created_at: datetime = Field(..., description="Post creation timestamp")
    engagement: Dict[str, int] = Field(default_factory=dict, description="Engagement metrics (likes, reposts, etc.)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific extra data")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "at://did:plc:abc123/app.bsky.feed.post/xyz789",
                "account_id": "did:plc:abc123",
                "platform": "bluesky",
                "content": "This is an example post about politics",
                "created_at": "2024-01-15T12:30:00Z",
                "engagement": {
                    "likes": 10,
                    "reposts": 2,
                    "replies": 5
                },
                "metadata": {
                    "uri": "at://did:plc:abc123/app.bsky.feed.post/xyz789",
                    "cid": "bafyrei...",
                    "langs": ["en"]
                }
            }
        }
