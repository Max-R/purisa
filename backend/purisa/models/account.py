"""Account data model for all platforms."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class Account(BaseModel):
    """Generic account/user model that works across all platforms."""

    id: str = Field(..., description="Platform-specific unique identifier")
    username: str = Field(..., description="Username or handle")
    platform: str = Field(..., description="Platform name (bluesky, hackernews, etc.)")
    display_name: Optional[str] = Field(None, description="Display name if different from username")
    created_at: datetime = Field(..., description="Account creation timestamp")
    follower_count: int = Field(0, description="Number of followers")
    following_count: int = Field(0, description="Number of accounts following")
    post_count: int = Field(0, description="Total number of posts/submissions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific extra data")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "did:plc:abc123",
                "username": "user.bsky.social",
                "platform": "bluesky",
                "display_name": "John Doe",
                "created_at": "2024-01-01T00:00:00Z",
                "follower_count": 150,
                "following_count": 200,
                "post_count": 500,
                "metadata": {
                    "did": "did:plc:abc123",
                    "description": "Software engineer",
                    "verified": False
                }
            }
        }
