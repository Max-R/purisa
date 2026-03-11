"""
Job executor for scheduled coordination detection jobs.

Orchestrates the collect → analyze pipeline and publishes
real-time events via an SSE event bus.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List

from ..database.connection import get_database
from ..database.job_models import ScheduledJobDB, JobExecutionDB
from .collector import UniversalCollector
from .coordination import CoordinationAnalyzer

logger = logging.getLogger(__name__)


class SSEEventBus:
    """Simple asyncio.Queue-based pub/sub for Server-Sent Events."""

    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to events. Returns a queue that receives messages."""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from events."""
        try:
            self._subscribers.remove(queue)
        except ValueError:
            pass

    async def publish(self, event_type: str, data: dict):
        """Broadcast an event to all subscribers."""
        import json
        message = {"event": event_type, "data": data}
        for queue in self._subscribers:
            try:
                await queue.put(message)
            except Exception:
                pass  # Don't let one bad subscriber block others


# Global event bus singleton
event_bus = SSEEventBus()


class JobExecutor:
    """
    Runs the collect → analyze pipeline for a scheduled job.

    Pipeline:
    1. Load job config from DB
    2. Create execution record (status='running')
    3. Emit SSE: job_started
    4. For each query: collect posts + store
    5. Run coordination analysis
    6. Update execution record
    7. Emit SSE: job_completed or job_failed
    """

    def __init__(self):
        self.collector = UniversalCollector()
        self.analyzer = CoordinationAnalyzer()

    async def execute_job(self, job_id: int) -> JobExecutionDB:
        """
        Execute a scheduled job by ID.

        Args:
            job_id: ID of the ScheduledJobDB record

        Returns:
            The JobExecutionDB record
        """
        db = get_database()
        started_at = datetime.now()

        # Load job config (snapshot it so session can close)
        with db.get_session() as session:
            job = session.query(ScheduledJobDB).filter_by(id=job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")

            job_name = job.name
            platform = job.platform
            queries = list(job.queries or [])
            collect_limit = job.collect_limit
            analysis_hours = job.analysis_hours
            harvest_comments = bool(job.harvest_comments)

        # Create execution record
        with db.get_session() as session:
            execution = JobExecutionDB(
                job_id=job_id,
                status='running',
                started_at=started_at,
            )
            session.add(execution)
            session.flush()
            execution_id = execution.id

        # Emit start event
        await event_bus.publish('job_started', {
            'job_id': job_id,
            'execution_id': execution_id,
            'job_name': job_name,
            'platform': platform,
            'started_at': started_at.isoformat(),
        })

        total_posts = 0
        total_accounts = 0
        total_comments = 0
        coordination_score = None
        clusters_detected = 0
        error_message = None
        status = 'success'

        try:
            # Phase 1: Collection
            for query in queries:
                try:
                    posts = await self.collector.collect_from_platform(
                        platform, query, collect_limit
                    )
                    await self.collector.store_posts(posts)
                    total_posts += len(posts)
                    account_ids = set(p.account_id for p in posts)
                    total_accounts += len(account_ids)

                    await event_bus.publish('job_progress', {
                        'job_id': job_id,
                        'execution_id': execution_id,
                        'phase': 'collection',
                        'query': query,
                        'posts_collected': len(posts),
                    })
                except Exception as e:
                    logger.error(f"Collection failed for query '{query}': {e}")

            # Phase 2: Coordination analysis (synchronous, run in thread)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=analysis_hours)
            results = await asyncio.to_thread(
                self.analyzer.analyze_range, platform, start_time, end_time
            )

            if results:
                scores = [r.coordination_score for r in results]
                coordination_score = max(scores) if scores else 0.0
                clusters_detected = sum(len(r.clusters) for r in results)

            await event_bus.publish('job_progress', {
                'job_id': job_id,
                'execution_id': execution_id,
                'phase': 'analysis',
                'hours_analyzed': analysis_hours,
                'coordination_score': coordination_score,
                'clusters_detected': clusters_detected,
            })

        except Exception as e:
            status = 'failed'
            error_message = str(e)
            logger.error(f"Job {job_id} execution failed: {e}")

        # Update execution record
        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()

        with db.get_session() as session:
            execution = session.query(JobExecutionDB).filter_by(id=execution_id).first()
            if execution:
                execution.status = status
                execution.completed_at = completed_at
                execution.duration_seconds = duration
                execution.posts_collected = total_posts
                execution.accounts_discovered = total_accounts
                execution.comments_collected = total_comments
                execution.coordination_score = coordination_score
                execution.clusters_detected = clusters_detected
                execution.error_message = error_message

        # Emit completion event
        event_name = 'job_completed' if status == 'success' else 'job_failed'
        await event_bus.publish(event_name, {
            'job_id': job_id,
            'execution_id': execution_id,
            'job_name': job_name,
            'status': status,
            'duration_seconds': duration,
            'posts_collected': total_posts,
            'coordination_score': coordination_score,
            'clusters_detected': clusters_detected,
            'error_message': error_message,
            'completed_at': completed_at.isoformat(),
        })

        logger.info(f"Job {job_id} ({job_name}) completed: status={status}, posts={total_posts}, score={coordination_score}")
        return execution
