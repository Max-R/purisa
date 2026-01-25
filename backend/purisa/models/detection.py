"""Detection models for flags and scores."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict


class Flag(BaseModel):
    """Individual flag for suspicious behavior."""

    account_id: str = Field(..., description="Account being flagged")
    flag_type: str = Field(..., description="Type of flag (new_account, high_frequency, etc.)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    reason: str = Field(..., description="Human-readable explanation")
    timestamp: datetime = Field(default_factory=datetime.now, description="When flag was created")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "did:plc:abc123",
                "flag_type": "high_frequency_posting",
                "confidence_score": 0.85,
                "reason": "Account posted 50 times in 1 hour",
                "timestamp": "2024-01-15T14:30:00Z"
            }
        }


class Score(BaseModel):
    """Aggregated bot detection score for an account."""

    account_id: str = Field(..., description="Account being scored")
    total_score: float = Field(..., ge=0.0, le=13.5, description="Total bot score (0-13.5)")
    signals: Dict[str, float] = Field(default_factory=dict, description="Individual signal scores")
    flagged: bool = Field(False, description="Whether account is flagged as suspicious")
    threshold: float = Field(7.0, description="Threshold used for flagging")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "did:plc:abc123",
                "total_score": 8.5,
                "signals": {
                    "new_account": 2.0,
                    "high_frequency": 3.0,
                    "repetitive_content": 2.5,
                    "low_engagement": 1.0
                },
                "flagged": True,
                "threshold": 7.0
            }
        }
