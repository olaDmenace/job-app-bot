import re
from datetime import datetime
from urllib.parse import urlencode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from job_scrapers.base_scraper import BaseJobScraper

class JobsiteScraper(BaseJobScraper):
    """Scraper for Jobsite.co.uk"""
    
    def __init__(self, db_instance=None):
        super().__init__(source_name="Jobsite", requires_login=False, db_instance=db_instance)
    
    def get_base_url(self, remote_only=True):
        """Get the starting URL for job search"""
        params = {
            'q': 'frontend developer',
            'postedwithin': '30',  # Last 30 days
            'sort': 'date'  # Sort by date
        }
        
        # Add remote filter if requested
        if remote_only:
            params['remote'] = '1'  # Remote work filter
        
        base_url = "https://www.jobsite.co.uk/jobs?"
        return base_url + urlencode(params)
    
    def login(self, username, password):
        """Not required for basic Jobsite search"""
        return True
    
    def parse_date_posted(self, date_text):
        """Convert Jobsite's date format to days"""
        if not date_text:
            return '30d'
            
        date_text = date_text.lower()
        
        if 'today' in date_text or 'just now' in date_text or 'hour' in date_text:
            return '0d'
            
        if 'yesterday' in date_text:
            return '1d'
            
        days_match = re.search(r'(\d+)\s+day', date_text)
        if days_match:
            return f"{days_match.group(1)}d"
            
        weeks_match = re.search(r'(\d+)\s+week', date_text)
        if weeks_match:
            days = int(weeks_match.group(1)) * 7
            return f"{days}d"
            
        months_match = re.search(r'(\d+)\s+month', date_text)
        if months_match:
            days = int(months_match.group(1)) * 30
            return f"{days}d"
            
        return '30d'  # Default
    
    def extract_job_details(self, job_element):
        """Extract job details from a single listing"""
        try:
            # Get job ID 
            job_id = job_element.get_attribute('id')
            if not job_id:
                job_id = f"jobsite_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Get title and URL
            try:
                title_element = job_element.find_element(By.CSS_SELECTOR, "h2.job-title")
                title = title_element.text.strip()
                
                link_element = job_element.find_element(By.CSS_SELECTOR, "a.job-title-link")
                job_url = link_element.get_attribute('href')
            except:
                try:
                    # Alternative structure
                    title_element = job_element.find_element(By.CSS_SELECTOR, "a[data-at='job-item-title']")
                    title = title_element.text.strip()
                    job_url = title_element.get_attribute('href')
                except:
                    title = "Not specified"
                    job_url = f"https://www.jobsite.co.uk/job/{job_id}"
            
            # Get company
            try:
                company_element = job_element.find_element(By.CSS_SELECTOR, "div.company")
                company = company_element.text.strip()
            except:
                try:
                    company_element = job_element.find_element(By.CSS_SELECTOR, "div[data-at='job-item-company-name']")
                    company = company_element.text.strip()
                except:
                    company = "Not specified"
            
            # Get location
            try:
                location_element = job_element.find_element(By.CSS_SELECTOR, "div.location")
                location = location_element.text.strip()
            except:
                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, "div[data-at='job-item-location']")
                    location = location_element.text.strip()
                except:
                    location = "Not specified"
            
            # Check for remote indicator
            if "remote" in location.lower() or job_element.find_elements(By.CSS_SELECTOR, ".remote-tag, .remote-marker"):
                location = f"{location} (Remote)"
            
            # Get posted date
            try:
                date_element = job_element.find_element(By.CSS_SELECTOR, "div.date")
                posted_text = date_element.text.strip()
                posted = self.parse_date_posted(posted_text)
            except:
                try:
                    date_element = job_element.find_element(By.CSS_SELECTOR, "div[data-at='job-item-posted-date']")
                    posted_text = date_element.text.strip()
                    posted = self.parse_date_posted(posted_text)
                except:
                    posted = "30d"  # Default
            
            # Get salary if available
            try:
                salary_element = job_element.find_element(By.CSS_SELECTOR, "div.salary")
                salary = salary_element.text.strip()
            except:
                try:
                    salary_element = job_element.find_element(By.CSS_SELECTOR, "div[data-at='job-item-salary']")
                    salary = salary_element.text.strip()
                except:
                    salary = "Not specified"
            
            return {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'posted': posted,
                'tags': 'jobsite',
                'url': job_url,
                'date_found': datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            print(f"Error extracting Jobsite job details: {str(e)}")
            return None
    
    def _extract_jobs(self):
        """Extract all jobs from current page"""
        try:
            print("Waiting for Jobsite job listings to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card, .results-item"))
            )
            
            self.human_like_delay(2, 3)
            
            # Handle cookie consent if it appears
            try:
                cookie_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "ccmgt_explicit_accept"))
                )
                cookie_button.click()
                print("Accepted cookies")
                self.human_like_delay(1, 2)
            except:
                pass  # No cookie popup or already handled
            
            # Get all job cards
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-card, .results-item")
            print(f"Found {len(job_elements)} potential job listings on Jobsite page")
            
            new_jobs = []
            for job_element in job_elements:
                job_details = self.extract_job_details(job_element)
                if job_details:
                    new_jobs.append(job_details)
            
            self.jobs_data.extend(new_jobs)
            print(f"Successfully extracted {len(new_jobs)} jobs from Jobsite")
            return new_jobs
            
        except Exception as e:
            print(f"Error extracting jobs from Jobsite page: {str(e)}")
            return []
    
    def has_next_page(self):
        """Check if there's a next page of results"""
        try:
            # Find next link
            next_link = self.driver.find_element(By.CSS_SELECTOR, "a.next, a[data-at='pagination-next']")
            
            # Check if disabled
            if 'disabled' in next_link.get_attribute('class') or not next_link.is_enabled():
                return None
                
            next_url = next_link.get_attribute('href')
            return next_url
        except:
            return None
    
    def go_to_next_page(self, next_url):
        """Navigate to the next page of results"""
        try:
            print(f"Navigating to next Jobsite page: {next_url}")
            self.driver.get(next_url)
            self.human_like_delay(3, 5)
            
            # Wait for new results to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card, .results-item"))
            )
            
            return True
        except Exception as e:
            print(f"Error navigating to next Jobsite page: {str(e)}")
            return False