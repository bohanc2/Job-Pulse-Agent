"""
Scheduled task scheduler
Automatically refreshes data every hour
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)

class SchedulerManager:
    """Scheduled task manager"""
    
    def __init__(self, collector_manager):
        self.collector_manager = collector_manager
        self.scheduler = BackgroundScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup scheduled tasks"""
        # Execute data collection every hour
        self.scheduler.add_job(
            func=self._refresh_jobs,
            trigger=IntervalTrigger(hours=1),
            id='refresh_jobs',
            name='Hourly job data refresh',
            replace_existing=True
        )
        logger.info("Scheduled task set: refresh every hour")
    
    def _refresh_jobs(self):
        """Execute data refresh"""
        try:
            logger.info("Starting scheduled data refresh...")
            self.collector_manager.collect_all()
            logger.info("Scheduled data refresh completed")
        except Exception as e:
            logger.error(f"Scheduled data refresh failed: {e}")
    
    def start(self):
        """Start scheduler"""
        self.scheduler.start()
        logger.info("Scheduled task scheduler started")
    
    def stop(self):
        """Stop scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduled task scheduler stopped")
