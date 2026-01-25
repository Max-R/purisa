"""Background job scheduler using APScheduler."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from purisa.services.collector import UniversalCollector
from purisa.services.analyzer import BotDetector
from purisa.config.settings import get_settings

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Manages background jobs for data collection and analysis."""

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.collector = UniversalCollector()
        self.analyzer = BotDetector()
        self.settings = get_settings()

    async def collection_job(self):
        """Background job for data collection."""
        try:
            logger.info("Running scheduled collection job")
            await self.collector.run_collection_cycle()
            logger.info("Collection job completed successfully")
        except Exception as e:
            logger.error(f"Collection job failed: {e}")

    async def analysis_job(self):
        """Background job for bot detection analysis."""
        try:
            logger.info("Running scheduled analysis job")
            self.analyzer.analyze_all_accounts()
            logger.info("Analysis job completed successfully")
        except Exception as e:
            logger.error(f"Analysis job failed: {e}")

    def start(self):
        """Start the background scheduler."""
        # Add collection job (runs every 10 minutes by default)
        self.scheduler.add_job(
            self.collection_job,
            trigger=IntervalTrigger(seconds=self.settings.collection_interval),
            id='collection_job',
            name='Data collection job',
            replace_existing=True
        )

        # Add analysis job (runs every 30 minutes)
        self.scheduler.add_job(
            self.analysis_job,
            trigger=IntervalTrigger(seconds=1800),  # 30 minutes
            id='analysis_job',
            name='Bot detection analysis job',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Background scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Background scheduler shutdown")

    def get_jobs(self):
        """Get list of scheduled jobs."""
        return self.scheduler.get_jobs()
