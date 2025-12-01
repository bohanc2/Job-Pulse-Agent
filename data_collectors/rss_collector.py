"""
RSS Feed collector
Collects job information from company RSS pages
"""

import feedparser
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RSSCollector:
    """RSS Feed collector"""
    
    def collect(self, rss_url):
        """Collect jobs from RSS Feed"""
        jobs = []
        
        try:
            feed = feedparser.parse(rss_url)
            
            if feed.bozo:
                logger.warning(f"RSS Feed parsing error: {feed.bozo_exception}")
                return jobs
            
            for entry in feed.entries:
                try:
                    title = entry.get('title', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    link = entry.get('link', '')
                    
                    # Try to extract company name and location from title or description
                    company, location = self._extract_company_location(title, description)
                    
                    # Parse publication date
                    posted_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        posted_date = datetime(*entry.published_parsed[:6])
                    
                    # Detect job level
                    level = self._detect_level(title, description)
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'url': link,
                        'level': level,
                        'posted_date': posted_date
                    })
                except Exception as e:
                    logger.error(f"Failed to parse RSS entry: {e}")
                    continue
            
            logger.info(f"Collected {len(jobs)} jobs from RSS Feed")
        except Exception as e:
            logger.error(f"RSS collection failed: {e}")
        
        return jobs
    
    def _extract_company_location(self, title, description):
        """Extract company name and location from title and description"""
        # Simple extraction logic, can be improved based on actual format
        company = ''
        location = ''
        
        # Try to extract from description
        text = description.lower()
        
        # Common location keywords
        location_keywords = ['location:', 'city:', 'state:', 'remote', 'hybrid']
        for keyword in location_keywords:
            if keyword in text:
                # Simple extraction, can use more complex NLP in actual applications
                parts = text.split(keyword)
                if len(parts) > 1:
                    location = parts[1].split('\n')[0].strip()[:100]
                    break
        
        return company, location
    
    def _detect_level(self, title, description):
        """Detect job level"""
        text = (title + ' ' + description).lower()
        
        # Check for entry level first (intern, new graduate)
        if any(word in text for word in ['intern', 'internship', 'new graduate', 'entry level', 'entry-level']):
            return 'entry'
        # Check for senior level
        elif any(word in text for word in ['senior', 'sr.', 'lead', 'principal', 'director', 'vp', 'vice president']):
            return 'senior'
        # Check for executive level
        elif any(word in text for word in ['executive', 'chief', 'ceo', 'cto', 'cfo']):
            return 'executive'
        else:
            # Default to mid-level for all other jobs
            return 'mid'
