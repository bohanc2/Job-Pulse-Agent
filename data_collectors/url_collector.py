"""
URL scraping collector
Collects job information from specified company recruitment pages
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

class URLCollector:
    """URL scraping collector"""
    
    def collect(self, url):
        """Collect jobs from specified URL"""
        jobs = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"URL request failed: {response.status_code}")
                return jobs
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple common job list selectors
            job_selectors = [
                {'tag': 'div', 'class': re.compile('job|position|opening|career')},
                {'tag': 'li', 'class': re.compile('job|position|opening')},
                {'tag': 'article', 'class': re.compile('job|position')},
            ]
            
            job_elements = []
            for selector in job_selectors:
                elements = soup.find_all(selector['tag'], class_=selector['class'])
                if elements:
                    job_elements = elements
                    break
            
            # If not found, try to find links containing "job" or "position"
            if not job_elements:
                job_elements = soup.find_all('a', href=re.compile('job|position|career|opening', re.I))
            
            for elem in job_elements[:50]:  # Limit quantity
                try:
                    # Extract title
                    title_elem = elem.find(['h2', 'h3', 'h4', 'a', 'span'], class_=re.compile('title|heading', re.I))
                    if not title_elem:
                        title_elem = elem.find('a') or elem
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Extract link
                    link_elem = elem.find('a', href=True) if elem.name != 'a' else elem
                    link = link_elem.get('href', '') if link_elem else ''
                    
                    if link and not link.startswith('http'):
                        # Convert relative link to absolute link
                        from urllib.parse import urljoin
                        link = urljoin(url, link)
                    
                    # Extract company name (from URL or page title)
                    company = self._extract_company_from_url(url)
                    
                    # Extract location
                    location_elem = elem.find(['span', 'div'], class_=re.compile('location|city|place', re.I))
                    location = location_elem.get_text(strip=True) if location_elem else ''
                    
                    # Extract description
                    desc_elem = elem.find(['p', 'div'], class_=re.compile('description|summary', re.I))
                    description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ''
                    
                    # Detect job level
                    level = self._detect_level(title, description)
                    
                    if title and link:
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'description': description,
                            'url': link,
                            'level': level,
                            'posted_date': None
                        })
                except Exception as e:
                    logger.error(f"Failed to parse job element: {e}")
                    continue
            
            logger.info(f"Collected {len(jobs)} jobs from URL")
        except Exception as e:
            logger.error(f"URL collection failed: {e}")
        
        return jobs
    
    def _extract_company_from_url(self, url):
        """Extract company name from URL"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        # Remove www. and .com etc.
        company = domain.replace('www.', '').split('.')[0]
        return company.capitalize()
    
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
