"""
Scheduled task scheduler
Automatically refreshes data every hour with smart keyword rotation
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import os

logger = logging.getLogger(__name__)

class SchedulerManager:
    """Scheduled task manager"""
    
    def __init__(self, collector_manager):
        self.collector_manager = collector_manager
        self.scheduler = BackgroundScheduler()
        self.current_keyword_index = 0
        self._setup_jobs()
    
    def _get_keywords(self):
        """Get list of search keywords to rotate through"""
        # Get keywords from environment variable or use defaults
        keywords_str = os.getenv('ADZUNA_KEYWORDS', '')
        if keywords_str:
            # Comma-separated list from environment
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        else:
            # Default keywords covering different job categories
            keywords = [
                'software engineer',
                'data scientist',
                'product manager',
                'marketing',
                'sales',
                'designer',
                'developer',
                'analyst',
                'consultant',
                'manager'
            ]
        return keywords
    
    def _setup_jobs(self):
        """Setup scheduled tasks"""
        # Execute data collection every hour with keyword rotation
        self.scheduler.add_job(
            func=self._refresh_jobs_with_rotation,
            trigger=IntervalTrigger(hours=1),
            id='refresh_jobs',
            name='Hourly job data refresh with keyword rotation',
            replace_existing=True
        )
        logger.info("Scheduled task set: refresh every hour with keyword rotation")
    
    def trigger_immediate_refresh(self):
        """Trigger an immediate data refresh (non-blocking)"""
        import threading
        def run_refresh():
            self._refresh_jobs()
        thread = threading.Thread(target=run_refresh, daemon=True)
        thread.start()
        logger.info("Immediate refresh triggered in background thread")
    
    def _refresh_jobs_with_rotation(self):
        """Execute data refresh with keyword rotation to collect more diverse jobs"""
        try:
            from models.database import get_job_sources, get_refresh_status
            
            # Check if API limit was reached today
            refresh_status = get_refresh_status()
            if refresh_status.get('api_limit_reached', False):
                logger.info("⏸️ API limit reached today. Skipping scheduled collection. Will resume tomorrow.")
                return
            
            # Get all configured sources
            sources = get_job_sources()
            
            # If no sources configured, collect from default "all" source
            if len(sources) == 0:
                logger.info("No data sources configured, skipping scheduled refresh")
                return
            
            # Check if we should use keyword rotation
            use_keyword_rotation = os.getenv('ADZUNA_USE_KEYWORD_ROTATION', 'true').lower() == 'true'
            
            if use_keyword_rotation:
                keywords = self._get_keywords()
                if keywords:
                    # Rotate through keywords
                    keyword = keywords[self.current_keyword_index % len(keywords)]
                    self.current_keyword_index += 1
                    
                    logger.info(f"Starting scheduled data refresh with keyword: '{keyword}'")
                    # Collect from specific keyword
                    self.collector_manager.collect_from_source('api', keyword, f'Adzuna - {keyword.title()}')
                    logger.info(f"Scheduled data refresh completed for keyword: '{keyword}'")
                else:
                    # Fallback to collecting all sources
                    logger.info("Starting scheduled data refresh (all sources)...")
                    self.collector_manager.collect_all()
                    logger.info("Scheduled data refresh completed")
            else:
                # Collect from all configured sources
                logger.info("Starting scheduled data refresh (all sources)...")
                self.collector_manager.collect_all()
                logger.info("Scheduled data refresh completed")
        except Exception as e:
            logger.error(f"Scheduled data refresh failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _refresh_jobs(self):
        """Execute data refresh (legacy method, kept for compatibility)"""
        self._refresh_jobs_with_rotation()
    
    def start(self):
        """Start scheduler"""
        self.scheduler.start()
        logger.info("Scheduled task scheduler started")
    
    def stop(self):
        """Stop scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduled task scheduler stopped")
