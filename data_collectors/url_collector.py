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
            
            # Strategy 1: Direct search for job-title elements (most reliable)
            # Look for elements with job-title related classes (e.g., "job-title", "text-primary job-title mb-0")
            job_titles = self._find_job_title_elements(soup)
            if job_titles:
                logger.info(f"Found {len(job_titles)} job titles using direct title search")
                jobs = self._extract_jobs_from_titles(job_titles, url, soup)
            
            # Strategy 2: Container-based approach (fallback)
            if not jobs:
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
                        # Extract title with improved logic
                        title_elem = elem.find(['h2', 'h3', 'h4', 'a', 'span'], class_=re.compile('title|heading', re.I))
                        if not title_elem:
                            title_elem = elem.find('a') or elem
                        
                        title = self._clean_text(title_elem.get_text(strip=True))
                        if not title or not self._is_valid_job_title(title):
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
                        location = self._clean_text(location_elem.get_text(strip=True)) if location_elem else ''
                        
                        # Extract description
                        desc_elem = elem.find(['p', 'div'], class_=re.compile('description|summary', re.I))
                        description = self._clean_text(desc_elem.get_text(strip=True)[:1000]) if desc_elem else ''
                        
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
    
    def _find_job_title_elements(self, soup):
        """Find elements that likely contain job titles (e.g., elements with job-title classes)"""
        title_elements = []
        
        # Look for elements with job-title related classes (most common patterns)
        title_class_patterns = [
            re.compile(r'job[-_]title', re.I),  # job-title, job_title
            re.compile(r'position[-_]title', re.I),
            re.compile(r'career[-_]title', re.I),
            re.compile(r'role[-_]title', re.I),
            re.compile(r'opening[-_]title', re.I),
        ]
        
        # Try different tags with job-title classes
        for pattern in title_class_patterns:
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'a', 'span', 'div', 'p']:
                elements = soup.find_all(tag, class_=pattern)
                for elem in elements:
                    title = self._clean_text(elem.get_text(strip=True))
                    if self._is_valid_job_title(title):
                        link = self._extract_link_from_element(elem)
                        title_elements.append({
                            'element': elem,
                            'title': title,
                            'link': link
                        })
        
        # Also look for headings that might be job titles
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            title = self._clean_text(heading.get_text(strip=True))
            if self._is_valid_job_title(title) and len(title) > 5:
                link = heading.find('a', href=True)
                if link:
                    title_elements.append({
                        'element': heading,
                        'title': title,
                        'link': link.get('href', '')
                    })
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_titles = []
        for item in title_elements:
            title_lower = item['title'].lower().strip()
            if title_lower not in seen_titles and len(title_lower) > 5:
                seen_titles.add(title_lower)
                unique_titles.append(item)
        
        return unique_titles[:50]  # Limit to 50
    
    def _extract_jobs_from_titles(self, title_elements, base_url, soup):
        """Extract job information from title elements"""
        jobs = []
        company = self._extract_company_from_url(base_url)
        
        for item in title_elements:
            try:
                title = item['title']
                link = item['link']
                
                # Make link absolute if relative
                if link and not link.startswith('http'):
                    from urllib.parse import urljoin
                    link = urljoin(base_url, link)
                
                # Try to find related information (location, description) near the title
                elem = item['element']
                parent = elem.find_parent()
                
                location = self._extract_location_near_element(elem, parent)
                description = self._extract_description_near_element(elem, parent)
                
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
                logger.debug(f"Failed to extract job from title element: {e}")
                continue
        
        return jobs
    
    def _extract_link_from_element(self, elem):
        """Extract link from element or its parent"""
        # Check if element itself is a link
        if elem.name == 'a' and elem.get('href'):
            return elem.get('href')
        
        # Check parent for link
        parent = elem.find_parent('a', href=True)
        if parent:
            return parent.get('href')
        
        # Check for nearby link
        link = elem.find('a', href=True)
        if link:
            return link.get('href')
        
        return ''
    
    def _extract_location_near_element(self, elem, container):
        """Extract location information near an element"""
        if not container:
            return ''
        
        # Look for location-related elements
        location_patterns = [
            re.compile(r'location|city|place|address|area', re.I),
            re.compile(r'remote|hybrid|onsite', re.I),
        ]
        
        for pattern in location_patterns:
            location_elem = container.find(['span', 'div', 'p'], class_=pattern)
            if location_elem:
                location = self._clean_text(location_elem.get_text(strip=True))
                if location and len(location) < 100:
                    return location
        
        return ''
    
    def _extract_description_near_element(self, elem, container):
        """Extract description information near an element"""
        if not container:
            return ''
        
        # Look for description-related elements
        desc_elem = container.find(['p', 'div'], class_=re.compile(r'description|summary|detail', re.I))
        if desc_elem:
            description = self._clean_text(desc_elem.get_text(strip=True))
            return description[:1000] if description else ''
        
        # Fallback: get first paragraph
        para = container.find('p')
        if para:
            description = self._clean_text(para.get_text(strip=True))
            return description[:500] if description else ''
        
        return ''
    
    def _is_valid_job_title(self, title):
        """Validate if text looks like a job title"""
        if not title or len(title) < 5:
            return False
        
        if len(title) > 200:  # Too long to be a title
            return False
        
        # Check if it's garbage text
        if self._is_garbage_text(title):
            return False
        
        # Check for common job title keywords
        job_keywords = [
            'engineer', 'developer', 'manager', 'analyst', 'specialist',
            'coordinator', 'director', 'assistant', 'associate', 'intern',
            'designer', 'consultant', 'executive', 'officer', 'lead',
            'architect', 'scientist', 'administrator', 'representative',
            'technician', 'supervisor', 'officer', 'agent', 'representative'
        ]
        
        title_lower = title.lower()
        has_job_keyword = any(keyword in title_lower for keyword in job_keywords)
        
        # Check special character ratio
        special_char_ratio = sum(1 for c in title if not c.isalnum() and c not in ' -') / len(title) if title else 1
        
        # Valid if has job keywords OR reasonable special char ratio
        if has_job_keyword or special_char_ratio < 0.3:
            return True
        
        return False
    
    def _is_garbage_text(self, text):
        """Check if text appears to be garbage/meaningless"""
        if not text:
            return True
        
        # Too many special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and c not in ' -.,!?') / len(text) if text else 1
        if special_char_ratio > 0.5:
            return True
        
        # Too many repeated characters (likely encoding issues)
        if len(text) > 10 and len(set(text)) < len(text) * 0.3:
            return True
        
        # Check for common garbage patterns
        garbage_patterns = [
            r'^[0-9\s\-]+$',  # Only numbers and dashes
            r'^[^\w\s]+$',     # Only special characters
        ]
        
        for pattern in garbage_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ''
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
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
