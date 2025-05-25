import os
import time
import random
from datetime import datetime
from abc import ABC, abstractmethod
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from database_manager import JobApplicationDB

class BaseJobScraper(ABC):
    """Abstract base class for all job scrapers."""
    
    def __init__(self, source_name, requires_login=False, db_instance=None):
        """
        Initialize a job scraper.
        
        Args:
            source_name (str): Name of the job source (e.g., "Indeed", "LinkedIn")
            requires_login (bool): Whether this source requires user login
            db_instance (JobApplicationDB): Shared database instance
        """
        self.driver = None
        self.jobs_data = []
        self.db = db_instance if db_instance else JobApplicationDB()
        self.source_name = source_name
        self.requires_login = requires_login
        
    def setup_driver(self):
        """Initialize and configure the Chrome driver with anti-detection measures."""
        try:
            options = webdriver.ChromeOptions()
            
            # Browser settings for stealth
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-extensions-file-access-check')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins-discovery')
            
            # Handle Windows Chrome executable paths
            import platform
            if platform.system() == "Windows":
                chrome_paths = [
                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                    os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
                ]
                for path in chrome_paths:
                    if os.path.exists(path):
                        options.binary_location = path
                        break
            
            # Set user agent
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            options.add_argument(f'--user-agent={user_agent}')
            
            # Disable automation flags
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Additional anti-detection preferences
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.geolocation": 2
            }
            options.add_experimental_option("prefs", prefs)
            
            # Setup ChromeDriver - try fallback first since it's working
            try:
                # Try fallback method first (it's working)
                self.driver = webdriver.Chrome(options=options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                print(f"Browser setup successful for {self.source_name}")
                return True
            except Exception as fallback_error:
                print(f"Direct Chrome method failed: {str(fallback_error)}")
                # Try webdriver-manager as backup
                try:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    
                    print(f"Browser setup successful for {self.source_name} (webdriver-manager)")
                    return True
                except Exception as manager_error:
                    print(f"Both methods failed. Fallback: {str(fallback_error)}, Manager: {str(manager_error)}")
                    raise fallback_error
            
        except Exception as e:
            print(f"Error setting up browser: {str(e)}")
            return False
    
    def check_for_bot_detection(self):
        """Check if page has bot detection and handle gracefully"""
        try:
            # Common bot detection indicators
            bot_indicators = [
                "verify you are human",
                "captcha",
                "cloudflare",
                "access denied",
                "blocked",
                "robot",
                "bot detected"
            ]
            
            page_text = self.driver.page_source.lower()
            for indicator in bot_indicators:
                if indicator in page_text:
                    print(f"Bot detection found: {indicator}")
                    return True
            return False
        except:
            return False
            
    def human_like_delay(self, min_seconds=2, max_seconds=5):
        """Add random delay to mimic human behavior."""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def save_jobs(self):
        """Save jobs to both database and CSV."""
        if not self.jobs_data:
            print("No jobs to save")
            return
            
        try:
            # Save to CSV for backup
            filename = f"{self.source_name.lower()}_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            df = pd.DataFrame(self.jobs_data)
            
            # Save to CSV
            df.to_csv(filename, index=False)
            print(f"\nSaved {len(self.jobs_data)} jobs to {filename}")
            
            # Save to database
            db_saved_count = 0
            for job in self.jobs_data:
                # Add source information
                job['source'] = self.source_name.lower()
                
                # Save to database
                self.db.add_job(job)
                db_saved_count += 1
            
            print(f"Saved {db_saved_count} jobs to database")
            
        except Exception as e:
            print(f"Error saving jobs: {str(e)}")
            
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                print(f"Browser closed successfully for {self.source_name}")
            except Exception as e:
                print(f"Error closing browser: {str(e)}")
        
        if hasattr(self, 'db'):
            self.db.close()
    
    @abstractmethod
    def get_base_url(self, remote_only=True):
        """
        Get the starting URL for job search.
        
        Args:
            remote_only (bool): Whether to filter for remote jobs only
            
        Returns:
            str: The URL to start job search from
        """
        pass
    
    @abstractmethod
    def login(self, username, password):
        """
        Log in to the job site if required.
        
        Args:
            username (str): Username or email
            password (str): Password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_job_details(self, job_element):
        """
        Extract job details from a job listing element.
        
        Args:
            job_element: The element containing job information
            
        Returns:
            dict: Job details or None if extraction failed
        """
        pass
    
    @abstractmethod
    def _extract_jobs(self):
        """
        Extract all jobs from current page.
        
        Returns:
            list: List of job dictionaries
        """
        pass
        
    @abstractmethod
    def has_next_page(self):
        """
        Check if there's a next page of job listings.
        
        Returns:
            str or None: URL of next page or None
        """
        pass
    
    @abstractmethod
    def go_to_next_page(self, next_url):
        """
        Navigate to the next page of job listings.
        
        Args:
            next_url (str): URL of next page
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        pass
    
    def run_job_search(self, remote_only=True, max_pages=5, login_credentials=None):
        """
        Main method to run the job search process.
        
        Args:
            remote_only (bool): Whether to filter for remote jobs
            max_pages (int): Maximum number of pages to process
            login_credentials (dict): Dictionary with 'username' and 'password' keys
            
        Returns:
            list: The extracted job data
        """
        try:
            if not self.setup_driver():
                print("Failed to set up browser. Aborting search.")
                return []
            
            url = self.get_base_url(remote_only)
            print(f"Navigating to: {url}")
            self.driver.get(url)
            
            self.human_like_delay(4, 6)
            
            # Handle login if required
            if self.requires_login:
                if not login_credentials:
                    print(f"Login required for {self.source_name} but no credentials provided")
                    self.cleanup()
                    return []
                
                login_success = self.login(
                    login_credentials.get('username'), 
                    login_credentials.get('password')
                )
                
                if not login_success:
                    print(f"Login failed for {self.source_name}")
                    self.cleanup()
                    return []
            
            page = 1
            total_jobs = 0
            
            while page <= max_pages:
                print(f"\nProcessing page {page}...")
                
                try:
                    new_jobs = self._extract_jobs()
                    total_jobs += len(new_jobs)
                except Exception as extract_error:
                    print(f"Error extracting jobs from {self.source_name} page: {str(extract_error)}")
                    new_jobs = []
                
                if not new_jobs:
                    print("No jobs found on this page")
                    break
                
                next_url = self.has_next_page()
                if next_url and page < max_pages:
                    if not self.go_to_next_page(next_url):
                        print("Failed to navigate to next page")
                        break
                    page += 1
                else:
                    print("No more pages available")
                    break
            
            print(f"\nTotal pages processed: {page}")
            print(f"Total jobs found: {total_jobs}")
            
            # Save to both CSV and database
            self.save_jobs()
            
            return self.jobs_data
            
        except Exception as e:
            print(f"Error during {self.source_name} job search process: {str(e)}")
            return []
            
        finally:
            self.cleanup()