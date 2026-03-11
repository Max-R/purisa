"""
Cron-based job scheduler with database persistence.

Replaces the legacy interval-based BackgroundScheduler with a
cron-driven system that loads jobs from the database on startup
and supports dynamic job management via the API.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Optional

from ..database.connection import get_database
from ..database.job_models import ScheduledJobDB
from .job_executor import JobExecutor

logger = logging.getLogger(__name__)


class JobScheduler:
    """
    Manages cron-based scheduled jobs with database persistence.

    Jobs survive server restarts by loading from the database
    on startup and re-registering with APScheduler.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.executor = JobExecutor()

    def start(self):
        """Start the scheduler and load persisted jobs from database."""
        self.scheduler.start()
        self._load_jobs_from_db()
        logger.info("Job scheduler started")

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        self.scheduler.shutdown(wait=False)
        logger.info("Job scheduler shutdown")

    def _load_jobs_from_db(self):
        """Load all enabled jobs from database and register with APScheduler."""
        db = get_database()

        with db.get_session() as session:
            jobs = session.query(ScheduledJobDB).filter(
                ScheduledJobDB.enabled == 1
            ).all()

            for job in jobs:
                self._register_job(job.id, job.cron_expression)

            logger.info(f"Loaded {len(jobs)} scheduled jobs from database")

    def _register_job(self, job_id: int, cron_expression: str):
        """Register a single job with APScheduler using CronTrigger."""
        apscheduler_id = f"purisa_job_{job_id}"

        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            self.scheduler.add_job(
                self._run_job,
                trigger=trigger,
                id=apscheduler_id,
                name=f"Purisa scheduled job {job_id}",
                args=[job_id],
                replace_existing=True,
            )
            logger.info(f"Registered job {job_id} with cron: {cron_expression}")
        except Exception as e:
            logger.error(f"Failed to register job {job_id}: {e}")

    def _unregister_job(self, job_id: int):
        """Remove a job from APScheduler."""
        apscheduler_id = f"purisa_job_{job_id}"
        try:
            self.scheduler.remove_job(apscheduler_id)
            logger.info(f"Unregistered job {job_id}")
        except Exception:
            pass  # Job may not exist in scheduler

    async def _run_job(self, job_id: int):
        """APScheduler callback — execute the job."""
        logger.info(f"Scheduler triggered job {job_id}")
        try:
            await self.executor.execute_job(job_id)
        except Exception as e:
            logger.error(f"Scheduled execution of job {job_id} failed: {e}")

    def add_job(self, job_id: int, cron_expression: str):
        """Add a new job to the scheduler (called after DB insert)."""
        self._register_job(job_id, cron_expression)

    def update_job(self, job_id: int, cron_expression: str, enabled: bool):
        """Update or toggle a job in the scheduler."""
        if enabled:
            self._register_job(job_id, cron_expression)
        else:
            self._unregister_job(job_id)

    def remove_job(self, job_id: int):
        """Remove a job from the scheduler (called after DB delete)."""
        self._unregister_job(job_id)

    def get_next_run(self, job_id: int) -> Optional[datetime]:
        """Get the next scheduled run time for a job."""
        apscheduler_id = f"purisa_job_{job_id}"
        job = self.scheduler.get_job(apscheduler_id)
        if job and job.next_run_time:
            return job.next_run_time
        return None
