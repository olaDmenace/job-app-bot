"""
Template for creating new job scrapers.

To implement a new job platform scraper:
1. Copy this template to a new file named after your platform (e.g., 'glassdoor.py')
2. Fill in the implementation details for each required method
3. Update the class name to match your platform
4. Test your implementation
"""

from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from job_scrapers.base_scraper import BaseJobScraper

class TemplateJobScraper(BaseJobScraper):
    """Template for creating new job scrapers"""
    
    def __init__(self):
        # Initialize with your platform name and whether login is required
        super().__init__(source_name="Template", requires_login=False)
    
    def get_base_url(self, remote_only=True):
        """
        Get the starting URL for job search.
        
        Args:
            remote_only (bool): Whether to filter for remote jobs only
            
        Returns:
            str: The URL to start job search from
        """
        # Implement URL construction with appropriate filters
        return "https://example.com/jobs"
    
    def login(self, username, password):
        """
        Log in to the job site if required.
        
        Args:
            username (str): Username or email
            password (str): Password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        # Implement login logic if the platform requires it
        # If login not required, just return True
        return True
    
    def extract_job_details(self, job_element):
        """
        Extract job details from a job listing element.
        
        Args:
            job_element: The element containing job information
            
        Returns:
            dict: Job details or None if extraction failed
        """
        try:
            # Extract job ID, title, company, location, etc.
            job_id = "example_id"
            title = "Example Title"
            company = "Example Company"
            location = "Example Location"
            salary = "Example Salary"
            posted = "0d"  # Format as "Xd" where X is number of days
            tags = "example, tags"
            url = "https://example.com/job/123"
            
            # Return standardized job object
            return {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'posted': posted,
                'tags': tags,
                'url': url,
                'date_found': datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            print(f"Error extracting job details: {str(e)}")
            return None
    
    def _extract_jobs(self):
        """
        Extract all jobs from current page.
        
        Returns:
            list: List of job dictionaries
        """
        try:
            # Wait for job listings to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-listing"))
            )
            
            # Get all job elements
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-listing")
            
            # Process each job
            new_jobs = []
            for job_element in job_elements:
                job_details = self.extract_job_details(job_element)
                if job_details:
                    new_jobs.append(job_details)
            
            # Add to overall jobs data
            self.jobs_data.extend(new_jobs)
            return new_jobs
            
        except Exception as e:
            print(f"Error extracting jobs from page: {str(e)}")
            return []
    
    def has_next_page(self):
        """
        Check if there's a next page of job listings.
        
        Returns:
            str or None: URL of next page or None
        """
        try:
            # Find next page link/button
            next_link = self.driver.find_element(By.CSS_SELECTOR, ".next-page")
            next_url = next_link.get_attribute('href')
            return next_url
        except:
            return None
    
    def go_to_next_page(self, next_url):
        """
        Navigate to the next page of job listings.
        
        Args:
            next_url (str): URL of next page
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            # Navigate to next page
            self.driver.get(next_url)
            self.human_like_delay(3, 5)
            return True
        except:
            return False