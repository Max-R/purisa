"""Configuration settings using Pydantic."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///./purisa.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins_str: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(',')]

    # Bluesky
    bluesky_handle: Optional[str] = None
    bluesky_password: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    # Detection thresholds
    bot_detection_threshold: float = 7.0
    new_account_days: int = 30
    high_frequency_threshold: int = 50  # posts per hour

    # Collection settings
    collection_interval: int = 600  # seconds (10 minutes)
    default_post_limit: int = 100

    # Comment collection settings
    comment_collection_enabled: bool = True
    comment_min_engagement_score: float = 0.3
    comment_max_per_post: int = 100
    comment_max_posts_per_cycle: int = 20

    # Inflammatory detection settings (Detoxify)
    inflammatory_model: str = "original-small"  # 'original-small', 'original', or 'unbiased'
    inflammatory_threshold: float = 0.5  # Flag if any toxicity category >= 0.5
    inflammatory_device: str = "cpu"  # 'cpu' or 'cuda' for GPU

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance (lazy initialization).

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.

    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
