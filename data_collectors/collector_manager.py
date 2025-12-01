"""
Data collection manager
Unified management of all data source collection work
"""

from data_collectors.rss_collector import RSSCollector
from data_collectors.url_collector import URLCollector
from data_collectors.api_collector import APICollector
from models.database import get_job_sources, add_job, update_refresh_status
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CollectorManager:
    """Data collection manager"""
    
    def __init__(self):
        self.collectors = {
            'rss': RSSCollector(),
            'url': URLCollector(),
            'api': APICollector()
        }
    
    def collect_from_source(self, source_type, source_url, source_name=''):
        """Collect data from a single source"""
        collector = self.collectors.get(source_type)
        if not collector:
            logger.warning(f"Unknown source type: {source_type}")
            return []
        
        try:
            logger.info(f"Collecting data from {source_type}: {source_url}")
            jobs = collector.collect(source_url)
            
            # Save to database
            saved_count = 0
            updated_count = 0
            created_count = 0
            
            for job in jobs:
                try:
                    result = add_job(
                        title=job.get('title', ''),
                        company=job.get('company', ''),
                        location=job.get('location', ''),
                        description=job.get('description', ''),
                        url=job.get('url', ''),
                        source=source_type,
                        source_name=source_name or source_url,
                        level=job.get('level'),
                        posted_date=job.get('posted_date')
                    )
                    saved_count += 1
                    if result == 'updated':
                        updated_count += 1
                    elif result == 'created':
                        created_count += 1
                except Exception as e:
                    logger.error(f"Failed to save job: {e}")
            
            logger.info(f"Successfully processed {saved_count} jobs from {source_type} (Created: {created_count}, Updated: {updated_count})")
            return jobs
        except Exception as e:
            logger.error(f"Data collection failed ({source_type}): {e}")
            return []
    
    def collect_all(self):
        """Collect data from all sources"""
        logger.info("Starting collection from all sources...")
        sources = get_job_sources()
        
        total_collected = 0
        for source in sources:
            jobs = self.collect_from_source(
                source['type'],
                source['url'],
                source.get('name', '')
            )
            total_collected += len(jobs)
        
        # Update refresh status
        update_refresh_status()
        logger.info(f"Data collection completed, collected {total_collected} jobs in total")
        return total_collected
