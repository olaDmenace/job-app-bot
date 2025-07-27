import os
import json
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional

from job_scrapers.scraper_factory import JobScraperFactory
from job_scrapers.api_scrapers import create_api_scraper
from job_scrapers.api_usage_manager import APIUsageManager
from database_manager import JobApplicationDB

class JobScraperCoordinator:
    """Coordinates multiple job scrapers"""
    
    def __init__(self, config_file=None):
        """
        Initialize the coordinator.
        
        Args:
            config_file (str, optional): Path to configuration file.
        """
        # Load environment variables for credentials
        load_dotenv()
        
        # Create shared database instance
        self.db = JobApplicationDB()
        
        # Initialize API usage manager
        self.usage_manager = APIUsageManager()
        
        self.login_credentials = {}
        self.config = {}
        
        # Load configuration if provided
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                    
                # Extract platform-specific configs
                self.platform_configs = self.config.get('platforms', {})
            except Exception as e:
                print(f"Error loading config file: {str(e)}")
                self.platform_configs = {}
        else:
            self.platform_configs = {}
        
        # Set up default credentials from environment variables
        self.setup_default_credentials()
        
        # Set up API credentials
        self.setup_api_credentials()
    
    def setup_default_credentials(self):
        """Set up default credentials from environment variables"""
        
        # LinkedIn credentials
        if os.getenv('LINKEDIN_EMAIL') and os.getenv('LINKEDIN_PASSWORD'):
            self.login_credentials['LinkedIn'] = {
                'username': os.getenv('LINKEDIN_EMAIL'),
                'password': os.getenv('LINKEDIN_PASSWORD')
            }
        
        # Dice credentials
        if os.getenv('DICE_EMAIL') and os.getenv('DICE_PASSWORD'):
            self.login_credentials['Dice'] = {
                'username': os.getenv('DICE_EMAIL'),
                'password': os.getenv('DICE_PASSWORD')
            }
        
        # Monster credentials
        if os.getenv('MONSTER_EMAIL') and os.getenv('MONSTER_PASSWORD'):
            self.login_credentials['Monster'] = {
                'username': os.getenv('MONSTER_EMAIL'),
                'password': os.getenv('MONSTER_PASSWORD')
            }
        
        # Glassdoor credentials
        if os.getenv('GLASSDOOR_EMAIL') and os.getenv('GLASSDOOR_PASSWORD'):
            self.login_credentials['Glassdoor'] = {
                'username': os.getenv('GLASSDOOR_EMAIL'),
                'password': os.getenv('GLASSDOOR_PASSWORD')
            }
    
    def setup_api_credentials(self):
        """Set up API credentials and check availability"""
        self.api_credentials = {}
        
        # Adzuna API
        if os.getenv('ADZUNA_APP_ID') and os.getenv('ADZUNA_APP_KEY'):
            self.api_credentials['adzuna'] = {
                'app_id': os.getenv('ADZUNA_APP_ID'),
                'app_key': os.getenv('ADZUNA_APP_KEY')
            }
        
        # JSearch/RapidAPI
        if os.getenv('RAPIDAPI_KEY'):
            self.api_credentials['jsearch'] = {
                'api_key': os.getenv('RAPIDAPI_KEY')
            }
    
    def get_platform_config(self, platform_name):
        """
        Get platform-specific configuration.
        
        Args:
            platform_name (str): Name of the platform
            
        Returns:
            dict: Platform configuration or empty dict if not found
        """
        return self.platform_configs.get(platform_name, {})
    
    def run_scraper(self, scraper_name, max_pages=5, remote_only=True, query="frontend developer", **kwargs):
        """
        Run a specific job scraper with smart API selection.
        
        Args:
            scraper_name (str): Name of the scraper to run
            max_pages (int, optional): Maximum number of pages to scrape
            remote_only (bool, optional): Whether to filter for remote jobs
            query (str): Search query for job matching
            
        Returns:
            list: The extracted job data
        """
        try:
            # First, try API scrapers if applicable
            api_jobs = self._try_api_scrapers(scraper_name, query, remote_only, **kwargs)
            if api_jobs:
                return api_jobs
            
            # Fallback to web scraper
            return self._run_web_scraper(scraper_name, max_pages, remote_only)
            
        except Exception as e:
            print(f"Error running {scraper_name} scraper: {str(e)}")
            return []
    
    def _try_api_scrapers(self, platform_name: str, query: str, remote_only: bool, **kwargs) -> List[Dict]:
        """Try to get jobs using API scrapers first"""
        platform_lower = platform_name.lower()
        
        # Get optimal API strategy
        strategy = self.usage_manager.get_optimal_api_strategy(query, [platform_name])
        
        for api_name, target_platform, estimated_calls in strategy:
            if target_platform.lower() != platform_lower:
                continue
                
            try:
                if api_name == 'adzuna' and 'adzuna' in self.api_credentials:
                    print(f"Using Adzuna API for {platform_name}")
                    scraper = create_api_scraper('adzuna', self.db)
                    # Share the same usage manager instance
                    scraper.usage_manager = self.usage_manager
                    jobs = scraper.search_jobs(
                        query=query,
                        remote_only=remote_only,
                        max_results=kwargs.get('max_results', 50)
                    )
                    if jobs:
                        scraper.jobs_data = jobs
                        scraper.save_jobs()
                        return jobs
                
                elif api_name == 'jsearch' and 'jsearch' in self.api_credentials:
                    print(f"Using JSearch API for {platform_name}")
                    scraper = create_api_scraper('jsearch', self.db)
                    # Share the same usage manager instance
                    scraper.usage_manager = self.usage_manager
                    jobs = scraper.search_jobs(
                        query=query,
                        remote_only=remote_only,
                        max_results=kwargs.get('max_results', 10)  # Lower limit for JSearch
                    )
                    if jobs:
                        scraper.jobs_data = jobs
                        scraper.save_jobs()
                        return jobs
                
            except Exception as e:
                print(f"API scraper {api_name} failed for {platform_name}: {e}")
                continue
        
        return []
    
    def _run_web_scraper(self, scraper_name: str, max_pages: int, remote_only: bool) -> List[Dict]:
        """Run traditional web scraper as fallback"""
        try:
            # Create scraper with shared database instance
            scraper = JobScraperFactory.create_scraper(scraper_name, self.db)
            
            # Get platform-specific configuration
            platform_config = self.get_platform_config(scraper.source_name)
            
            # Override default parameters with platform-specific ones
            platform_max_pages = platform_config.get('max_pages', max_pages)
            platform_remote_only = platform_config.get('remote_only', remote_only)
            
            # Get login credentials if needed
            login_credentials = None
            if scraper.requires_login:
                if scraper.source_name in self.login_credentials:
                    login_credentials = self.login_credentials[scraper.source_name]
                else:
                    print(f"Warning: {scraper.source_name} requires login but no credentials provided")
                    print(f"Skipping {scraper.source_name} web scraper")
                    return []
            
            # Run the scraper
            print(f"\nRunning {scraper.source_name} web scraper:")
            print(f"  Max pages: {platform_max_pages}")
            print(f"  Remote only: {platform_remote_only}")
            
            jobs = scraper.run_job_search(
                remote_only=platform_remote_only,
                max_pages=platform_max_pages,
                login_credentials=login_credentials
            )
            
            return jobs
            
        except Exception as e:
            print(f"Error running {scraper_name} web scraper: {str(e)}")
            return []
    
    def run_available_scrapers(self, max_pages=5, remote_only=True, skip_login_required=False):
        """
        Run all available scrapers.
        
        Args:
            max_pages (int, optional): Maximum number of pages to scrape per platform
            remote_only (bool, optional): Whether to filter for remote jobs
            skip_login_required (bool, optional): Whether to skip platforms requiring login
            
        Returns:
            dict: Dictionary with platform names as keys and their job data as values
        """
        available_scrapers = JobScraperFactory.get_available_scrapers()
        results = {}
        
        print(f"\nRunning job search across {len(available_scrapers)} platforms:")
        for name, info in available_scrapers.items():
            # Skip if requires login and we're set to skip those
            if skip_login_required and info['requires_login']:
                print(f"Skipping {name} (requires login)")
                continue
                
            # Skip if requires login but no credentials provided
            if info['requires_login'] and name not in self.login_credentials:
                print(f"Skipping {name} (no login credentials provided)")
                continue
            
            print(f"\n--- Starting {name} scraper ---")
            results[name] = self.run_scraper(name, max_pages, remote_only)
            print(f"--- Completed {name} scraper ({len(results[name])} jobs found) ---")
        
        # Print summary
        print("\nJob search complete!")
        print("Summary of results:")
        total_jobs = 0
        for platform, jobs in results.items():
            job_count = len(jobs)
            total_jobs += job_count
            print(f"  {platform}: {job_count} jobs")
        print(f"Total jobs found: {total_jobs}")
        
        return results
    
    def run_api_search(self, query: str, platforms: List[str] = None, max_results: int = 50, 
                      remote_only: bool = True, location: str = "") -> Dict[str, List[Dict]]:
        """
        Run API-first job search across specified platforms.
        
        Args:
            query (str): Search query
            platforms (List[str]): List of platforms to search (None for all)
            max_results (int): Maximum results per platform
            remote_only (bool): Filter for remote jobs
            location (str): Location filter
            
        Returns:
            Dict[str, List[Dict]]: Results by platform
        """
        if platforms is None:
            platforms = ['indeed', 'linkedin', 'glassdoor', 'monster', 'dice']
        
        # Show quota status
        self.usage_manager.print_quota_status()
        
        # Get recommendations
        recommendations = self.usage_manager.get_usage_recommendations(query, platforms)
        if recommendations:
            print("\nAPI Usage Recommendations:")
            for rec in recommendations:
                print(f"  {rec}")
            print()
        
        # Get optimal strategy
        strategy = self.usage_manager.get_optimal_api_strategy(query, platforms, max_results)
        
        results = {}
        
        for api_name, platform, estimated_calls in strategy:
            try:
                if api_name == 'adzuna' and 'adzuna' in self.api_credentials:
                    scraper = create_api_scraper('adzuna', self.db)
                    scraper.usage_manager = self.usage_manager
                    jobs = scraper.search_jobs(
                        query=query,
                        location=location,
                        remote_only=remote_only,
                        max_results=max_results
                    )
                    
                elif api_name == 'jsearch' and 'jsearch' in self.api_credentials:
                    scraper = create_api_scraper('jsearch', self.db)
                    scraper.usage_manager = self.usage_manager
                    jobs = scraper.search_jobs(
                        query=query,
                        location=location,
                        remote_only=remote_only,
                        max_results=min(max_results, 10)  # Conservative limit
                    )
                    
                elif api_name == 'scraper':
                    # Fall back to web scraper
                    jobs = self._run_web_scraper(platform, 3, remote_only)
                    
                else:
                    continue
                
                if jobs:
                    scraper.jobs_data = jobs
                    scraper.save_jobs()
                    results[platform] = jobs
                    print(f"{platform}: {len(jobs)} jobs found")
                else:
                    results[platform] = []
                    print(f"{platform}: No jobs found")
                    
            except Exception as e:
                print(f"Error with {platform} via {api_name}: {e}")
                results[platform] = []
        
        # Show updated quota status
        print("\nUpdated API Usage:")
        self.usage_manager.print_quota_status()
        
        return results
    
    def get_quota_status(self) -> Dict:
        """Get current API quota status"""
        return self.usage_manager.get_quota_status()
    
    def run_with_smart_fallback(self, query: str, platforms: List[str], 
                               api_first: bool = True, **kwargs) -> Dict[str, List[Dict]]:
        """
        Run job search with smart API-first strategy and web scraper fallback.
        
        Args:
            query (str): Search query
            platforms (List[str]): Platforms to search
            api_first (bool): Whether to try APIs first
            
        Returns:
            Dict[str, List[Dict]]: Results by platform
        """
        results = {}
        
        if api_first:
            # Try API search first
            api_results = self.run_api_search(query, platforms, **kwargs)
            results.update(api_results)
            
            # Find platforms that didn't return results
            failed_platforms = [p for p, jobs in api_results.items() if not jobs]
            
            if failed_platforms and len(failed_platforms) < len(platforms):
                print(f"\nFalling back to web scrapers for: {', '.join(failed_platforms)}")
                
                # Try web scrapers for failed platforms
                for platform in failed_platforms:
                    try:
                        web_jobs = self._run_web_scraper(platform, 3, kwargs.get('remote_only', True))
                        if web_jobs:
                            results[platform] = web_jobs
                            print(f"{platform} (web): {len(web_jobs)} jobs found")
                    except Exception as e:
                        print(f"ERROR {platform} (web): {e}")
        else:
            # Traditional web scraper approach
            for platform in platforms:
                results[platform] = self.run_scraper(platform, **kwargs)
        
        return results