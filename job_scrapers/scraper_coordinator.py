import os
import json
from dotenv import load_dotenv
from datetime import datetime

from job_scrapers.scraper_factory import JobScraperFactory

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
    
    def get_platform_config(self, platform_name):
        """
        Get platform-specific configuration.
        
        Args:
            platform_name (str): Name of the platform
            
        Returns:
            dict: Platform configuration or empty dict if not found
        """
        return self.platform_configs.get(platform_name, {})
    
    def run_scraper(self, scraper_name, max_pages=5, remote_only=True):
        """
        Run a specific job scraper.
        
        Args:
            scraper_name (str): Name of the scraper to run
            max_pages (int, optional): Maximum number of pages to scrape
            remote_only (bool, optional): Whether to filter for remote jobs
            
        Returns:
            list: The extracted job data
        """
        try:
            # Create scraper
            scraper = JobScraperFactory.create_scraper(scraper_name)
            
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
                    print(f"Skipping {scraper.source_name}")
                    return []
            
            # Run the scraper
            print(f"\nRunning {scraper.source_name} scraper:")
            print(f"  Max pages: {platform_max_pages}")
            print(f"  Remote only: {platform_remote_only}")
            
            jobs = scraper.run_job_search(
                remote_only=platform_remote_only,
                max_pages=platform_max_pages,
                login_credentials=login_credentials
            )
            
            return jobs
            
        except Exception as e:
            print(f"Error running {scraper_name} scraper: {str(e)}")
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