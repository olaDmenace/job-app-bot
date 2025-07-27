import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import time
import hashlib

from job_scrapers.api_usage_manager import APIUsageManager
from database_manager import JobApplicationDB

class BaseAPIScraper(ABC):
    """Base class for API-based job scrapers"""
    
    def __init__(self, source_name: str, db_instance: Optional[JobApplicationDB] = None):
        """
        Initialize API scraper.
        
        Args:
            source_name (str): Name of the job source
            db_instance (JobApplicationDB): Shared database instance
        """
        self.source_name = source_name
        self.db = db_instance if db_instance else JobApplicationDB()
        self.usage_manager = APIUsageManager()
        self.jobs_data = []
        self.cache_dir = "api_cache"
        self.cache_duration_hours = 24
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, query: str, location: str = "", **kwargs) -> str:
        """Generate cache key for API requests"""
        cache_data = f"{self.source_name}_{query}_{location}_{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get cache file path"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache is still valid"""
        if not os.path.exists(cache_path):
            return False
        
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - cache_time < timedelta(hours=self.cache_duration_hours)
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Load data from cache if valid"""
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                    print(f"Using cached results ({len(cached_data)} jobs)")
                    # Ensure cached data is properly normalized
                    normalized_data = []
                    for job in cached_data:
                        normalized_job = {}
                        for key, value in job.items():
                            normalized_job[key] = value if value is not None else ''
                        normalized_data.append(normalized_job)
                    return normalized_data
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: List[Dict]):
        """Save data to cache"""
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not cache results: {e}")
    
    def normalize_job_data(self, raw_job: Dict) -> Dict:
        """Normalize job data to consistent format"""
        return {
            'id': raw_job.get('id', ''),
            'title': raw_job.get('title', ''),
            'company': raw_job.get('company', ''),
            'location': raw_job.get('location', ''),
            'salary': raw_job.get('salary', 'Not specified'),
            'posted': raw_job.get('posted', ''),
            'tags': raw_job.get('tags', ''),
            'url': raw_job.get('url', ''),
            'date_found': datetime.now().strftime('%Y-%m-%d'),
            'source': self.source_name.lower(),
            'description': raw_job.get('description', '')
        }
    
    def save_jobs(self):
        """Save jobs to database"""
        if not self.jobs_data:
            print("No jobs to save")
            return
        
        try:
            db_saved_count = 0
            for job in self.jobs_data:
                self.db.add_job(job)
                db_saved_count += 1
            
            print(f"Saved {db_saved_count} jobs to database")
            
        except Exception as e:
            print(f"Error saving jobs: {e}")
    
    @abstractmethod
    def search_jobs(self, query: str, location: str = "", **kwargs) -> List[Dict]:
        """Search for jobs using the API"""
        pass

class AdzunaAPIScraper(BaseAPIScraper):
    """Adzuna API job scraper - covers Indeed, Monster, Dice, Jobsite, CVLibrary"""
    
    def __init__(self, db_instance: Optional[JobApplicationDB] = None):
        super().__init__("adzuna", db_instance)
        
        # Adzuna API credentials
        self.app_id = os.getenv('ADZUNA_APP_ID')
        self.app_key = os.getenv('ADZUNA_APP_KEY')
        
        if not self.app_id or not self.app_key:
            raise ValueError("Adzuna API credentials not found. Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env")
        
        # API endpoints by country
        self.endpoints = {
            'us': 'https://api.adzuna.com/v1/api/jobs/us/search',
            'uk': 'https://api.adzuna.com/v1/api/jobs/gb/search',
            'ca': 'https://api.adzuna.com/v1/api/jobs/ca/search'
        }
        
        self.default_country = 'us'
    
    def search_jobs(self, query: str, location: str = "", country: str = "us", 
                   max_results: int = 50, remote_only: bool = True, **kwargs) -> List[Dict]:
        """
        Search for jobs using Adzuna API.
        
        Args:
            query (str): Job search query
            location (str): Location filter
            country (str): Country code ('us', 'uk', 'ca')
            max_results (int): Maximum number of results
            remote_only (bool): Filter for remote jobs only
            
        Returns:
            List[Dict]: List of normalized job data
        """
        # Check quota
        if not self.usage_manager.can_use_api('adzuna', 1):
            print("⚠️  Adzuna API quota exceeded for this month")
            return []
        
        # Check cache first
        cache_key = self._get_cache_key(query, location, country=country, remote_only=remote_only)
        cached_jobs = self._load_from_cache(cache_key)
        if cached_jobs:
            return cached_jobs
        
        endpoint = self.endpoints.get(country, self.endpoints[self.default_country])
        
        # Build search parameters
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'results_per_page': min(max_results, 50),  # API limit is 50 per page
            'what': query,
            'content-type': 'application/json'
        }
        
        if location:
            params['where'] = location
        
        # Add remote job filter
        if remote_only:
            params['what'] += ' remote'
        
        # Add salary data if available
        params['salary_include_unknown'] = '0'
        
        try:
            print(f"Searching Adzuna API: {query} {f'in {location}' if location else ''}")
            
            response = requests.get(endpoint + '/1', params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            if 'results' in data:
                for job_data in data['results']:
                    try:
                        normalized_job = self._normalize_adzuna_job(job_data)
                        jobs.append(normalized_job)
                    except Exception as e:
                        print(f"Error processing job: {e}")
                        continue
            
            # Log API usage
            self.usage_manager.log_api_usage('adzuna', 1)
            
            # Cache results
            if self.usage_manager.should_cache_results('adzuna', query):
                self._save_to_cache(cache_key, jobs)
            
            print(f"Found {len(jobs)} jobs from Adzuna API")
            return jobs
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Adzuna API request failed: {e}")
            return []
        except Exception as e:
            print(f"ERROR: Error processing Adzuna API response: {e}")
            return []
    
    def _normalize_adzuna_job(self, job_data: Dict) -> Dict:
        """Normalize Adzuna job data to standard format"""
        # Extract salary information
        salary = "Not specified"
        if job_data.get('salary_min') and job_data.get('salary_max'):
            salary = f"${job_data['salary_min']:,.0f} - ${job_data['salary_max']:,.0f}"
        elif job_data.get('salary_min'):
            salary = f"${job_data['salary_min']:,.0f}+"
        
        # Calculate days since posted
        posted = "Recently"
        if job_data.get('created'):
            try:
                created_date = datetime.strptime(job_data['created'][:10], '%Y-%m-%d')
                days_ago = (datetime.now() - created_date).days
                posted = f"{days_ago}d" if days_ago > 0 else "Today"
            except:
                pass
        
        # Extract tags/skills
        tags = ""
        if job_data.get('category', {}).get('tag'):
            tags = job_data['category']['tag']
        
        # Normalize location
        location = job_data.get('location', {}).get('display_name', '')
        if not location and job_data.get('location', {}).get('area'):
            location = ', '.join(job_data['location']['area'])
        
        return self.normalize_job_data({
            'id': job_data.get('id') or '',
            'title': job_data.get('title') or '',
            'company': job_data.get('company', {}).get('display_name') or '',
            'location': location or '',
            'salary': salary or 'Not specified',
            'posted': posted or 'Recently',
            'tags': tags or '',
            'url': job_data.get('redirect_url') or '',
            'description': job_data.get('description') or ''
        })

class JSearchAPIScraper(BaseAPIScraper):
    """JSearch API scraper - aggregates LinkedIn, Indeed, Glassdoor data"""
    
    def __init__(self, db_instance: Optional[JobApplicationDB] = None):
        super().__init__("jsearch", db_instance)
        
        # RapidAPI key for JSearch
        self.api_key = os.getenv('RAPIDAPI_KEY')
        
        if not self.api_key:
            raise ValueError("RapidAPI key not found. Set RAPIDAPI_KEY in .env")
        
        self.base_url = "https://jsearch.p.rapidapi.com"
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        }
    
    def search_jobs(self, query: str, location: str = "", max_results: int = 10, 
                   remote_only: bool = True, employment_types: str = "FULLTIME", **kwargs) -> List[Dict]:
        """
        Search for jobs using JSearch API - USE SPARINGLY (200 calls/month limit).
        
        Args:
            query (str): Job search query
            location (str): Location filter
            max_results (int): Maximum number of results (keep low!)
            remote_only (bool): Filter for remote jobs only
            employment_types (str): Employment types filter
            
        Returns:
            List[Dict]: List of normalized job data
        """
        # CRITICAL: Check quota before any JSearch usage
        if not self.usage_manager.can_use_api('jsearch', 1):
            print("🚨 JSearch API quota exceeded for this month!")
            return []
        
        # Check if this is a high-priority query
        query_priority = self.usage_manager.classify_query_priority(query)
        remaining_quota = self.usage_manager.get_remaining_quota('jsearch')
        
        if query_priority == 'low' and remaining_quota <= 50:
            print(f"💡 Preserving JSearch quota ({remaining_quota} left) - use Adzuna for broad searches")
            return []
        
        # Check cache first (always cache JSearch results)
        cache_key = self._get_cache_key(query, location, remote_only=remote_only, employment_types=employment_types)
        cached_jobs = self._load_from_cache(cache_key)
        if cached_jobs:
            return cached_jobs
        
        # Build search parameters
        params = {
            'query': query,
            'page': '1',
            'num_pages': '1',
            'date_posted': 'all',
            'employment_types': employment_types
        }
        
        if location:
            params['location'] = location
        
        if remote_only:
            params['remote_only'] = 'true'
        
        try:
            print(f"Searching JSearch API: {query} (Priority: {query_priority}, Quota: {remaining_quota})")
            
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            if data.get('status') == 'OK' and 'data' in data:
                for job_data in data['data'][:max_results]:
                    try:
                        normalized_job = self._normalize_jsearch_job(job_data)
                        jobs.append(normalized_job)
                    except Exception as e:
                        print(f"Error processing job: {e}")
                        continue
            
            # CRITICAL: Log API usage
            self.usage_manager.log_api_usage('jsearch', 1)
            
            # Always cache JSearch results
            self._save_to_cache(cache_key, jobs)
            
            print(f"Found {len(jobs)} jobs from JSearch API")
            return jobs
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: JSearch API request failed: {e}")
            return []
        except Exception as e:
            print(f"ERROR: Error processing JSearch API response: {e}")
            return []
    
    def _normalize_jsearch_job(self, job_data: Dict) -> Dict:
        """Normalize JSearch job data to standard format"""
        # Extract salary information
        salary = "Not specified"
        if job_data.get('job_salary_currency') and job_data.get('job_min_salary'):
            min_sal = job_data.get('job_min_salary', 0)
            max_sal = job_data.get('job_max_salary', 0)
            currency = job_data.get('job_salary_currency', 'USD')
            
            if max_sal and max_sal > min_sal:
                salary = f"{currency}{min_sal:,.0f} - {currency}{max_sal:,.0f}"
            elif min_sal:
                salary = f"{currency}{min_sal:,.0f}+"
        
        # Calculate days since posted
        posted = "Recently"
        if job_data.get('job_posted_at_datetime_utc'):
            try:
                posted_date = datetime.fromisoformat(job_data['job_posted_at_datetime_utc'].replace('Z', '+00:00'))
                days_ago = (datetime.now() - posted_date.replace(tzinfo=None)).days
                posted = f"{days_ago}d" if days_ago > 0 else "Today"
            except:
                pass
        
        # Extract required skills/tags
        tags = ""
        if job_data.get('job_required_skills'):
            tags = ', '.join(job_data['job_required_skills'])
        
        # Determine if remote
        location = job_data.get('job_city', '')
        if job_data.get('job_is_remote'):
            location = f"Remote" + (f" ({location})" if location else "")
        elif job_data.get('job_state'):
            location = f"{location}, {job_data['job_state']}" if location else job_data['job_state']
        
        return self.normalize_job_data({
            'id': job_data.get('job_id') or '',
            'title': job_data.get('job_title') or '',
            'company': job_data.get('employer_name') or '',
            'location': location or '',
            'salary': salary or 'Not specified',
            'posted': posted or 'Recently',
            'tags': tags or '',
            'url': job_data.get('job_apply_link') or '',
            'description': job_data.get('job_description') or ''
        })

class ArbeitsNowAPIScraper(BaseAPIScraper):
    """ArbeitsNow API scraper - free public API for international jobs"""
    
    def __init__(self, db_instance: Optional[JobApplicationDB] = None):
        super().__init__("arbeitsnow", db_instance)
        self.base_url = "https://www.arbeitnow.com/api/job-board-api"
    
    def search_jobs(self, query: str = "", location: str = "", max_results: int = 50, **kwargs) -> List[Dict]:
        """
        Search for jobs using ArbeitsNow API (free, no auth required).
        
        Args:
            query (str): Job search query
            location (str): Location filter
            max_results (int): Maximum number of results
            
        Returns:
            List[Dict]: List of normalized job data
        """
        # Check cache first
        cache_key = self._get_cache_key(query, location)
        cached_jobs = self._load_from_cache(cache_key)
        if cached_jobs:
            return cached_jobs
        
        try:
            print(f"Searching ArbeitsNow API: {query}")
            
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            if 'data' in data:
                for job_data in data['data'][:max_results]:
                    try:
                        # Filter by query if provided
                        if query and query.lower() not in job_data.get('title', '').lower():
                            continue
                        
                        # Filter by location if provided
                        if location and location.lower() not in job_data.get('location', '').lower():
                            continue
                        
                        normalized_job = self._normalize_arbeitsnow_job(job_data)
                        jobs.append(normalized_job)
                    except Exception as e:
                        print(f"Error processing job: {e}")
                        continue
            
            # Cache results
            self._save_to_cache(cache_key, jobs)
            
            print(f"Found {len(jobs)} jobs from ArbeitsNow API")
            return jobs
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: ArbeitsNow API request failed: {e}")
            return []
        except Exception as e:
            print(f"ERROR: Error processing ArbeitsNow API response: {e}")
            return []
    
    def _normalize_arbeitsnow_job(self, job_data: Dict) -> Dict:
        """Normalize ArbeitsNow job data to standard format"""
        # Calculate days since posted
        posted = "Recently"
        if job_data.get('created_at'):
            try:
                created_date = datetime.fromisoformat(job_data['created_at'][:10])
                days_ago = (datetime.now() - created_date).days
                posted = f"{days_ago}d" if days_ago > 0 else "Today"
            except:
                pass
        
        # Extract tags
        tags = ', '.join(job_data.get('tags', []))
        
        return self.normalize_job_data({
            'id': job_data.get('slug', ''),
            'title': job_data.get('title', ''),
            'company': job_data.get('company_name', ''),
            'location': job_data.get('location', ''),
            'salary': 'Not specified',  # ArbeitsNow doesn't provide salary data
            'posted': posted,
            'tags': tags,
            'url': job_data.get('url', ''),
            'description': job_data.get('description', '')
        })

# Factory function for easy API scraper creation
def create_api_scraper(api_name: str, db_instance: Optional[JobApplicationDB] = None) -> BaseAPIScraper:
    """
    Create an API scraper instance.
    
    Args:
        api_name (str): Name of the API ('adzuna', 'jsearch', 'arbeitsnow')
        db_instance (JobApplicationDB): Shared database instance
        
    Returns:
        BaseAPIScraper: The requested API scraper
    """
    scrapers = {
        'adzuna': AdzunaAPIScraper,
        'jsearch': JSearchAPIScraper,
        'arbeitsnow': ArbeitsNowAPIScraper
    }
    
    if api_name.lower() not in scrapers:
        raise ValueError(f"Unknown API scraper: {api_name}. Available: {', '.join(scrapers.keys())}")
    
    return scrapers[api_name.lower()](db_instance)