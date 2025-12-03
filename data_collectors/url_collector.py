"""
URL scraping collector
Collects job information from specified company recruitment pages using LLM
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
import os
import json

logger = logging.getLogger(__name__)

# Try to import OpenAI and Gemini, but make them optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not available")

class URLCollector:
    """URL scraping collector using LLM for extraction"""
    
    def __init__(self):
        """Initialize URL collector with optional LLM client (Gemini or OpenAI)"""
        self.llm_client = None
        self.llm_type = None
        
        # Try Gemini first (free tier available, faster and cheaper)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if GEMINI_AVAILABLE and gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                # Try gemini-2.0-flash-exp first, fallback to gemini-1.5-flash if not available
                try:
                    self.llm_client = genai.GenerativeModel('gemini-2.0-flash-exp')
                    self.llm_type = 'gemini'
                    logger.info("Gemini 2.0 Flash client initialized for URL collection")
                except Exception:
                    # Fallback to gemini-1.5-flash if 2.0 is not available
                    self.llm_client = genai.GenerativeModel('gemini-1.5-flash')
                    self.llm_type = 'gemini'
                    logger.info("Gemini 1.5 Flash client initialized for URL collection")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
        
        # Fallback to OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if OPENAI_AVAILABLE and api_key:
            try:
                self.llm_client = openai.OpenAI(api_key=api_key)
                self.llm_type = 'openai'
                logger.info("OpenAI client initialized for URL collection")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        if not self.llm_client:
            logger.warning("No LLM API key set (GEMINI_API_KEY or OPENAI_API_KEY), URL collection will not work")
    
    def collect(self, url):
        """Collect jobs from specified URL using LLM extraction"""
        jobs = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.warning(f"URL request failed: {response.status_code}")
                return jobs
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract clean text from webpage
            page_text = self._extract_page_text(soup)
            
            if not page_text or len(page_text.strip()) < 100:
                logger.warning("Page text too short or empty, skipping LLM extraction")
                return jobs
            
            # Use LLM to extract job information
            if self.llm_client:
                jobs = self._extract_jobs_with_llm(page_text, url)
            else:
                logger.warning("LLM client not available, cannot use LLM extraction")
                return jobs
            
            logger.info(f"Collected {len(jobs)} jobs from URL using LLM")
        except Exception as e:
            logger.error(f"URL collection failed: {e}")
        
        return jobs
    
    def _extract_page_text(self, soup):
        """Extract clean text content from webpage"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        # Limit text length to avoid exceeding token limits (keep first 15000 characters)
        # This should be enough for most job listing pages
        if len(text) > 15000:
            text = text[:15000] + "..."
            logger.info(f"Text truncated to 15000 characters for LLM processing")
        
        return text
    
    def _extract_jobs_with_llm(self, page_text, base_url):
        """Use LLM to extract job information from page text"""
        jobs = []
        
        if not self.llm_client:
            return jobs
        
        try:
            prompt = f"""You are a job data extraction expert. Analyze the following webpage text and extract all job listings.

Webpage URL: {base_url}

Webpage Text:
{page_text}

Please extract all job listings from this webpage and return them as a JSON object with a "jobs" array. Each job should have the following structure:
{{
    "title": "Job title",
    "company": "Company name (if mentioned, otherwise use domain from URL)",
    "location": "Job location (e.g., 'Remote', 'New York, NY', 'San Francisco, CA', 'Worldwide')",
    "description": "Job description or summary (first 500 characters)",
    "url": "Full job URL (if available, otherwise use base URL: {base_url})",
    "salary": "Salary range if mentioned (e.g., '$80,000 - $120,000', 'Competitive', or empty string if not mentioned)",
    "level": "Job level: 'entry', 'mid', 'senior', or 'executive' (based on title and description)"
}}

Important rules:
1. Extract ALL job listings found on the page
2. If company name is not mentioned, extract it from the URL domain
3. If location is not mentioned, use "Not specified"
4. If salary is not mentioned, use empty string ""
5. Determine job level based on keywords: 'intern/internship/entry' -> 'entry', 'senior/lead/principal' -> 'senior', 'executive/director/ceo' -> 'executive', otherwise -> 'mid'
6. If no job listings are found, return {{"jobs": []}}
7. Return ONLY valid JSON object with "jobs" key containing an array, no additional text or explanation

Return format: {{"jobs": [...]}}"""

            if self.llm_type == 'gemini':
                # Use Gemini API
                try:
                    # Try with JSON mode first (Gemini 2.0 supports this)
                    try:
                        response = self.llm_client.generate_content(
                            prompt,
                            generation_config=genai.types.GenerationConfig(
                                temperature=0.1,
                                max_output_tokens=2000,
                                response_mime_type="application/json"
                            )
                        )
                        content = response.text.strip()
                    except (AttributeError, TypeError) as json_error:
                        # If response_mime_type is not supported, try without it
                        logger.debug(f"JSON mode not supported, trying without: {json_error}")
                        response = self.llm_client.generate_content(
                            prompt,
                            generation_config=genai.types.GenerationConfig(
                                temperature=0.1,
                                max_output_tokens=2000
                            )
                        )
                        content = response.text.strip()
                        # Try to extract JSON from markdown code blocks if present
                        import re
                        # Look for JSON in code blocks or plain JSON
                        json_match = re.search(r'```(?:json)?\s*(\{.*"jobs".*\})', content, re.DOTALL)
                        if json_match:
                            content = json_match.group(1)
                        else:
                            # Try to find JSON object directly
                            json_match = re.search(r'\{.*"jobs".*\}', content, re.DOTALL)
                            if json_match:
                                content = json_match.group(0)
                except Exception as e:
                    logger.error(f"Gemini API call failed: {e}")
                    return jobs
            else:
                # Use OpenAI API
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o-mini",  # Using cheaper model for cost efficiency
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional job data extraction system. Extract job listings from webpage text and return structured JSON data. Always return valid JSON arrays only."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_tokens=2000,  # Enough for multiple job listings
                    response_format={"type": "json_object"}  # Force JSON response
                )
                content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                result = json.loads(content)
                
                # Extract jobs array from response
                if isinstance(result, dict):
                    # Check for common keys
                    if 'jobs' in result:
                        jobs_data = result['jobs']
                    elif 'job_listings' in result:
                        jobs_data = result['job_listings']
                    elif 'data' in result:
                        jobs_data = result['data']
                    else:
                        # If it's a single job object, wrap it in a list
                        if 'title' in result:
                            jobs_data = [result]
                        else:
                            logger.warning(f"Unexpected JSON structure: {list(result.keys())}")
                            jobs_data = []
                elif isinstance(result, list):
                    # Direct array (fallback)
                    jobs_data = result
                else:
                    jobs_data = []
                
                # Process each job
                for job_data in jobs_data:
                    if not isinstance(job_data, dict):
                        continue
                    
                    # Extract and validate job information
                    title = job_data.get('title', '').strip()
                    if not title or len(title) < 3:
                        continue
                    
                    company = job_data.get('company', '').strip()
                    if not company:
                        company = self._extract_company_from_url(base_url)
                    
                    location = job_data.get('location', '').strip()
                    if not location:
                        location = 'Not specified'
                    
                    description = job_data.get('description', '').strip()
                    job_url = job_data.get('url', base_url).strip()
                    
                    # Ensure URL is absolute
                    if job_url and not job_url.startswith('http'):
                        from urllib.parse import urljoin
                        job_url = urljoin(base_url, job_url)
                    
                    # Determine level
                    level = job_data.get('level', '').strip().lower()
                    if level not in ['entry', 'mid', 'senior', 'executive']:
                        # Fallback to detection based on title and description
                        level = self._detect_level(title, description)
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'url': job_url,
                        'level': level,
                        'posted_date': None
                    })
                
                logger.info(f"LLM extracted {len(jobs)} jobs from webpage")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"LLM response content: {content[:500]}")
                # Try to extract JSON from the response if it's wrapped in text
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    try:
                        jobs_data = json.loads(json_match.group())
                        # Process jobs_data as above
                        for job_data in jobs_data:
                            if isinstance(job_data, dict) and job_data.get('title'):
                                jobs.append({
                                    'title': job_data.get('title', ''),
                                    'company': job_data.get('company', self._extract_company_from_url(base_url)),
                                    'location': job_data.get('location', 'Not specified'),
                                    'description': job_data.get('description', ''),
                                    'url': job_data.get('url', base_url),
                                    'level': job_data.get('level', 'mid'),
                                    'posted_date': None
                                })
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
        
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
