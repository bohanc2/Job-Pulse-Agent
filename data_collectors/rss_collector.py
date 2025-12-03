"""
RSS Feed collector
Collects job information from company RSS pages
"""

import feedparser
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import html

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
                    
                    # Extract company name from RSS custom fields (e.g., <company> tag)
                    # feedparser stores custom fields in entry attributes
                    company = self._extract_custom_field(entry, 'company')
                    
                    # Extract location from RSS custom fields (e.g., <location> tag)
                    location = self._extract_custom_field(entry, 'location')
                    
                    # Extract job type from RSS custom fields (e.g., <type> tag)
                    job_type = self._extract_custom_field(entry, 'type')
                    
                    # If not found in custom fields, try to extract from title or description
                    if not company or not location:
                        extracted_company, extracted_location = self._extract_company_location(title, description)
                        company = company or extracted_company
                        location = location or extracted_location
                    
                    # Clean HTML from description
                    description = self._clean_html(description)
                    
                    # Parse publication date
                    posted_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        posted_date = datetime(*entry.published_parsed[:6])
                    
                    # Detect job level (use job_type if available, otherwise detect from content)
                    level = self._detect_level_from_type(job_type) or self._detect_level(title, description)
                    
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
    
    def _extract_custom_field(self, entry, field_name):
        """Extract custom field from RSS entry (e.g., <company>, <location>, <type>)"""
        # feedparser stores custom fields directly as entry attributes
        # Try to get the field value
        try:
            # Method 1: Direct attribute access
            if hasattr(entry, field_name):
                field_value = getattr(entry, field_name)
                if field_value:
                    # If it's a list, get the first element
                    if isinstance(field_value, list) and len(field_value) > 0:
                        return str(field_value[0]).strip()
                    return str(field_value).strip()
            
            # Method 2: Check if it's in the entry's dictionary-like structure
            if hasattr(entry, 'keys') and field_name in entry:
                field_value = entry[field_name]
                if field_value:
                    if isinstance(field_value, list) and len(field_value) > 0:
                        return str(field_value[0]).strip()
                    return str(field_value).strip()
            
            # Method 3: Check entry's internal structure (feedparser may store in different formats)
            # Some RSS feeds use tags like <jobId>, <company>, etc. which feedparser stores as-is
            if hasattr(entry, '__dict__'):
                for key, value in entry.__dict__.items():
                    if key.lower() == field_name.lower():
                        if value:
                            if isinstance(value, list) and len(value) > 0:
                                return str(value[0]).strip()
                            return str(value).strip()
        except Exception as e:
            logger.debug(f"Error extracting custom field {field_name}: {e}")
        
        return ''
    
    def _clean_html(self, html_content):
        """Remove HTML tags from description and decode HTML entities"""
        if not html_content:
            return ''
        
        try:
            # First, unescape HTML entities (e.g., &#160; -> space)
            text = html.unescape(html_content)
            
            # Use BeautifulSoup to remove HTML tags
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up extra whitespace
            import re
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        except Exception as e:
            logger.warning(f"Failed to clean HTML: {e}")
            # Fallback: try simple regex to remove tags
            import re
            text = re.sub(r'<[^>]+>', '', html_content)
            text = html.unescape(text)
            return text.strip()
    
    def _detect_level_from_type(self, job_type):
        """Detect job level from RSS type field"""
        if not job_type:
            return None
        
        job_type_lower = job_type.lower()
        
        # Map common job types to levels
        if job_type_lower in ['intern', 'internship', 'entry', 'entry-level', 'entry level']:
            return 'entry'
        elif job_type_lower in ['senior', 'sr', 'lead', 'principal']:
            return 'senior'
        elif job_type_lower in ['executive', 'director', 'vp', 'vice president', 'c-level', 'c-suite']:
            return 'executive'
        elif job_type_lower in ['mid', 'mid-level', 'mid level', 'individual contributor']:
            return 'mid'
        
        return None
    
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
        """Detect job level from title and description content"""
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
