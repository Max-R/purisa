"""
SQLAlchemy database models for scheduled jobs.

Supports cron-based recurring collection and coordination analysis jobs
with full execution history tracking.

Note on naming: 'job_metadata' and 'execution_metadata' avoid the reserved
SQLAlchemy 'metadata' attribute name.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Index
from datetime import datetime

from .models import Base


class ScheduledJobDB(Base):
    """
    Stores user-defined scheduled coordination detection jobs.

    Each job defines a recurring collect-then-analyze pipeline
    targeting a specific platform and query set.
    """

    __tablename__ = 'scheduled_jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    platform = Column(String, nullable=False)  # 'bluesky', 'hackernews'
    queries = Column(JSON, nullable=False, default=list)  # ["#politics", "#election"]
    cron_expression = Column(String, nullable=False)  # "0 */6 * * *"
    collect_limit = Column(Integer, default=100)  # Posts per query per run
    analysis_hours = Column(Integer, default=6)  # Hours of data to analyze
    harvest_comments = Column(Integer, default=1)  # SQLite boolean
    enabled = Column(Integer, default=1)  # SQLite boolean
    job_metadata = Column(JSON, default=dict)  # Extensible properties
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_jobs_platform', 'platform'),
        Index('idx_jobs_enabled', 'enabled'),
    )


class JobExecutionDB(Base):
    """
    Stores execution history for scheduled jobs.

    Each row represents a single run of a scheduled job,
    tracking status, timing, and results.

    Note: job_id intentionally has no ForeignKey constraint so that
    execution history survives job deletion.
    """

    __tablename__ = 'job_executions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default='pending')  # 'pending', 'running', 'success', 'failed'
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    posts_collected = Column(Integer, default=0)
    accounts_discovered = Column(Integer, default=0)
    comments_collected = Column(Integer, default=0)
    coordination_score = Column(Float, nullable=True)  # Peak score from analysis
    clusters_detected = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index('idx_executions_job', 'job_id'),
        Index('idx_executions_status', 'status'),
        Index('idx_executions_started', 'started_at'),
    )
