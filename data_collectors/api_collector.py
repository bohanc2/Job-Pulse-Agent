"""
API collector
Collects data from job sites with free APIs
Supports: Adzuna, Reed, Indeed API, etc.
"""

import requests
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class APICollector:
    """API collector"""
    
    def collect(self, api_config):
        """
        Collect jobs from API
        api_config can be:
        - For Adzuna: "adzuna:field service" or search query string (if Adzuna credentials are set)
        - For other APIs: API URL string
        - JSON configuration string containing url, params, headers, etc.
        """
        jobs = []
        
        try:
            # Check if Adzuna credentials are available
            app_id = os.getenv('ADZUNA_APP_ID')
            app_key = os.getenv('ADZUNA_APP_KEY')
            has_adzuna_creds = app_id and app_key
            
            # Check if it's an Adzuna search query or URL
            if api_config.startswith('adzuna:'):
                # Format: "adzuna:field service"
                search_query = api_config[7:].strip()
                jobs = self._collect_from_adzuna(search_query)
            elif 'adzuna' in api_config.lower() and api_config.startswith('http'):
                # It's an Adzuna API URL
                jobs = self._collect_from_adzuna(api_config)
            elif has_adzuna_creds and not api_config.startswith('http'):
                # If Adzuna credentials exist and it's not a URL, treat as Adzuna search query
                jobs = self._collect_from_adzuna(api_config)
            elif 'reed' in api_config.lower():
                jobs = self._collect_from_reed(api_config)
            else:
                # Generic API call
                jobs = self._collect_generic(api_config)
            
            logger.info(f"Collected {len(jobs)} jobs from API")
        except Exception as e:
            logger.error(f"API collection failed: {e}")
        
        return jobs
    
    def _collect_from_adzuna(self, search_query_or_url):
        """
        Collect from Adzuna API - fetches ALL pages of results
        search_query_or_url can be:
        - A search query string (e.g., "field service")
        - A full Adzuna API URL
        """
        jobs = []
        
        # Get API credentials from environment
        app_id = os.getenv('ADZUNA_APP_ID')
        app_key = os.getenv('ADZUNA_APP_KEY')
        
        if not app_id or not app_key:
            logger.error("Adzuna API credentials not found in environment variables")
            return jobs
        
        try:
            # Determine base URL and search parameters
            if search_query_or_url.startswith('http'):
                # It's already a full URL, extract parameters
                import re
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(search_query_or_url)
                params = parse_qs(parsed.query)
                
                # Extract country from path (e.g., /jobs/us/search/1)
                path_parts = parsed.path.split('/')
                country = 'us'  # default
                if 'jobs' in path_parts:
                    idx = path_parts.index('jobs')
                    if idx + 1 < len(path_parts):
                        country = path_parts[idx + 1]
                
                # Extract search query
                search_query = params.get('what', [''])[0] if params.get('what') else ''
                base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search"
            else:
                # It's a search query, build the URL
                country = 'us'  # Options: us, gb, au, ca, de, etc.
                search_query = search_query_or_url.strip() if search_query_or_url else ''
                base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search"
            
            # Fetch all pages
            page = 1
            max_pages = 1000  # Safety limit to prevent infinite loops
            results_per_page = 50
            
            logger.info(f"Starting to collect all jobs from Adzuna API (country: {country}, query: '{search_query}')...")
            
            while page <= max_pages:
                # Build API URL for current page
                if not search_query or search_query.lower() in ['all', '*', 'all jobs']:
                    api_url = f"{base_url}/{page}?app_id={app_id}&app_key={app_key}&results_per_page={results_per_page}"
                else:
                    api_url = f"{base_url}/{page}?app_id={app_id}&app_key={app_key}&results_per_page={results_per_page}&what={search_query.replace(' ', '%20')}"
                
                logger.info(f"Fetching page {page} from Adzuna API...")
                response = requests.get(api_url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"Adzuna API request failed for page {page} with status {response.status_code}: {response.text[:200]}")
                    break
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    logger.info(f"No more results on page {page}, stopping pagination")
                    break
                
                logger.info(f"Page {page}: Adzuna API returned {len(results)} results")
                
                for item in results:
                    try:
                        # Parse date
                        posted_date = None
                        if item.get('created'):
                            try:
                                # Adzuna date format: "2024-01-15T10:30:00Z"
                                date_str = item['created'].replace('Z', '+00:00')
                                posted_date = datetime.fromisoformat(date_str)
                            except:
                                pass
                        
                        jobs.append({
                            'title': item.get('title', ''),
                            'company': item.get('company', {}).get('display_name', '') if isinstance(item.get('company'), dict) else item.get('company', ''),
                            'location': item.get('location', {}).get('display_name', '') if isinstance(item.get('location'), dict) else item.get('location', ''),
                            'description': item.get('description', ''),
                            'url': item.get('redirect_url', '') or item.get('url', ''),
                            'level': self._detect_level(item.get('title', ''), item.get('description', '')),
                            'posted_date': posted_date
                        })
                    except Exception as e:
                        logger.error(f"Failed to parse Adzuna job item: {e}")
                        continue
                
                # Check if we got fewer results than requested (last page)
                if len(results) < results_per_page:
                    logger.info(f"Received {len(results)} results (less than {results_per_page}), this is the last page")
                    break
                
                page += 1
                
                # Add a small delay to avoid rate limiting
                import time
                time.sleep(0.5)
            
            logger.info(f"Completed collecting from Adzuna API. Total jobs collected: {len(jobs)}")
                
        except Exception as e:
            logger.error(f"Adzuna API collection failed: {e}")
        
        return jobs
    
    def _collect_from_reed(self, api_url):
        """Collect from Reed API"""
        jobs = []
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                for item in results:
                    jobs.append({
                        'title': item.get('jobTitle', ''),
                        'company': item.get('employerName', ''),
                        'location': item.get('locationName', ''),
                        'description': item.get('jobDescription', ''),
                        'url': item.get('jobUrl', ''),
                        'level': self._detect_level(item.get('jobTitle', ''), item.get('jobDescription', '')),
                        'posted_date': datetime.fromisoformat(item['date']) if item.get('date') else None
                    })
        except Exception as e:
            logger.error(f"Reed API collection failed: {e}")
        
        return jobs
    
    def _collect_generic(self, api_url):
        """Generic API collection"""
        jobs = []
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Try different data structures
                results = data.get('results') or data.get('jobs') or data.get('data') or []
                
                for item in results:
                    if isinstance(item, dict):
                        jobs.append({
                            'title': item.get('title') or item.get('jobTitle') or item.get('name', ''),
                            'company': item.get('company') or item.get('employer') or item.get('companyName', ''),
                            'location': item.get('location') or item.get('city') or item.get('locationName', ''),
                            'description': item.get('description') or item.get('jobDescription') or item.get('summary', ''),
                            'url': item.get('url') or item.get('link') or item.get('jobUrl', ''),
                            'level': self._detect_level(
                                item.get('title') or item.get('jobTitle', ''),
                                item.get('description') or item.get('jobDescription', '')
                            ),
                            'posted_date': None
                        })
        except Exception as e:
            logger.error(f"Generic API collection failed: {e}")
        
        return jobs
    
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
