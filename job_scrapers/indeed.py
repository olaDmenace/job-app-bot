import re
from datetime import datetime, timedelta
from urllib.parse import quote, urlencode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from job_scrapers.base_scraper import BaseJobScraper

class IndeedScraper(BaseJobScraper):
    """Scraper for Indeed"""
    
    def __init__(self, db_instance=None):
        super().__init__(source_name="Indeed", requires_login=False, db_instance=db_instance)
        
    def get_base_url(self, remote_only=True):
        """Get the starting URL based on search parameters"""
        params = {
            'q': 'frontend developer',  # Search term
            'l': '',  # Location left blank for remote
            'sc': '0kf:attr(DSQF7);;',  # This is the parameter for remote jobs
            'vjk': '1',  # Show only jobs that can be applied to
        }
        
        # If remote only, add remote filter
        base = "https://www.indeed.com/jobs?"
        if remote_only:
            params['remotejob'] = '032b3046-06a3-4876-8dfd-474eb5e7ed11'
            
        query_string = urlencode(params)
        return base + query_string
    
    def login(self, username, password):
        """Login to Indeed - Not required for basic search"""
        return True  # Basic search doesn't require login
    
    def parse_date_posted(self, date_text):
        """Convert Indeed's relative date to days"""
        today = datetime.now()
        
        if not date_text or date_text.lower() == 'just posted':
            return '0d'
            
        if 'today' in date_text.lower():
            return '0d'
            
        if 'hour' in date_text.lower():
            return '0d'
            
        days_match = re.search(r'(\d+)\s+day', date_text.lower())
        if days_match:
            return f"{days_match.group(1)}d"
            
        weeks_match = re.search(r'(\d+)\s+week', date_text.lower())
        if weeks_match:
            days = int(weeks_match.group(1)) * 7
            return f"{days}d"
            
        months_match = re.search(r'(\d+)\s+month', date_text.lower())
        if months_match:
            days = int(months_match.group(1)) * 30
            return f"{days}d"
            
        return '30d'  # Default to 30 days if can't parse
    
    def extract_job_details(self, job_element):
        """Extract all details from a single job listing"""
        try:
            # Get job ID from data attribute
            job_id = job_element.get_attribute('data-jk') or job_element.get_attribute('id').replace('job_', '')
            
            # Get title
            try:
                title_element = job_element.find_element(By.CSS_SELECTOR, "h2.jobTitle span")
                title = title_element.text.strip()
            except NoSuchElementException:
                title_element = job_element.find_element(By.CSS_SELECTOR, "h2.jobTitle")
                title = title_element.text.strip()
                
            # Get company
            try:
                company_element = job_element.find_element(By.CSS_SELECTOR, "span.companyName")
                company = company_element.text.strip()
            except NoSuchElementException:
                company = "Not specified"
                
            # Get location
            try:
                location_element = job_element.find_element(By.CSS_SELECTOR, "div.companyLocation")
                location = location_element.text.strip()
                
                if 'remote' in location.lower():
                    location = f"{location} (Remote)"
            except NoSuchElementException:
                location = "Not specified"
                
            # Get salary if available
            try:
                salary_element = job_element.find_element(By.CSS_SELECTOR, "div.salary-snippet-container")
                salary = salary_element.text.strip()
            except NoSuchElementException:
                try:
                    salary_element = job_element.find_element(By.CSS_SELECTOR, "div.metadata.salary-snippet-container")
                    salary = salary_element.text.strip()
                except NoSuchElementException:
                    salary = "Not specified"
                    
            # Get posted date
            try:
                date_element = job_element.find_element(By.CSS_SELECTOR, "span.date")
                posted_text = date_element.text.replace('Posted', '').strip()
                posted = self.parse_date_posted(posted_text)
            except NoSuchElementException:
                posted = "Not specified"
                
            # Get job URL
            job_url = f"https://www.indeed.com/viewjob?jk={job_id}"
            
            # Build job object
            return {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'posted': posted,
                'tags': 'indeed',  # Indeed doesn't have tags in the listing
                'url': job_url,
                'date_found': datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            print(f"Error extracting Indeed job details: {str(e)}")
            return None
    
    def _extract_jobs(self):
        """Extract all jobs from current page"""
        try:
            print("Waiting for Indeed job listings to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_seen_beacon"))
            )
            
            self.human_like_delay(2, 4)
            
            # Indeed uses different job card classes
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon, div.tapItem")
            print(f"Found {len(job_elements)} potential job listings on current Indeed page")
            
            new_jobs = []
            for job_element in job_elements:
                job_details = self.extract_job_details(job_element)
                if job_details:
                    new_jobs.append(job_details)
            
            self.jobs_data.extend(new_jobs)
            print(f"Successfully extracted {len(new_jobs)} jobs from Indeed")
            return new_jobs
            
        except Exception as e:
            print(f"Error extracting jobs from Indeed page: {str(e)}")
            return []
    
    def has_next_page(self):
        """Check if there's a next page and get its URL"""
        try:
            next_link = self.driver.find_element(By.CSS_SELECTOR, "a[data-testid='pagination-page-next']")
            next_url = next_link.get_attribute('href')
            return next_url
        except NoSuchElementException:
            try:
                # Alternative pagination format
                navigation = self.driver.find_element(By.CSS_SELECTOR, "nav[role='navigation']")
                next_link = navigation.find_element(By.XPATH, "//a[contains(., 'Next')]")
                next_url = next_link.get_attribute('href')
                return next_url
            except:
                return None
        except:
            return None
    
    def go_to_next_page(self, next_url):
        """Navigate to the next page"""
        try:
            print(f"Navigating to next Indeed page: {next_url}")
            self.driver.get(next_url)
            self.human_like_delay(3, 5)
            
            # Handle potential popup
            try:
                popup_close = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.icl-CloseButton"))
                )
                popup_close.click()
                print("Closed popup")
            except:
                pass  # No popup found
                
            return True
        except Exception as e:
            print(f"Error navigating to next Indeed page: {str(e)}")
            return False