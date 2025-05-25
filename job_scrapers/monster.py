import re
from datetime import datetime
from urllib.parse import urlencode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from job_scrapers.base_scraper import BaseJobScraper

class MonsterScraper(BaseJobScraper):
    """Scraper for Monster.com"""
    
    def __init__(self, db_instance=None):
        super().__init__(source_name="Monster", requires_login=True, db_instance=db_instance)
    
    def get_base_url(self, remote_only=True):
        """Get the starting URL for job search"""
        params = {
            'q': 'frontend developer',
            'where': '',  # Location left blank for remote
            'page': '1',
            'so': 'date.desc',  # Sort by date
        }
        
        # Add remote filter if requested
        if remote_only:
            params['intcid'] = 'swoop_HeroSearch_remote'
            params['remotetype'] = '0'  # Remote work filter
        
        base_url = "https://www.monster.com/jobs/search?"
        return base_url + urlencode(params)
    
    def login(self, username, password):
        """Login to Monster"""
        try:
            print(f"Attempting to log in to Monster with username: {username}")
            
            # Go to login page
            self.driver.get("https://www.monster.com/profile/signin")
            self.human_like_delay(2, 3)
            
            # Accept cookies if popup appears
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_button.click()
                self.human_like_delay(1, 2)
            except:
                pass  # No cookie popup
            
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(username)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for successful login
            self.human_like_delay(5, 7)
            
            # Verify login success by checking for profile elements
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".user-menu-toggle"))
                )
                print("Successfully logged in to Monster")
                return True
            except TimeoutException:
                print("Login to Monster failed - could not verify success")
                return False
                
        except Exception as e:
            print(f"Error during Monster login: {str(e)}")
            return False
    
    def parse_date_posted(self, date_text):
        """Convert Monster's date format to days"""
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
            # Get job ID from data attribute or element ID
            job_id = job_element.get_attribute('data-job-id') or job_element.get_attribute('id')
            if not job_id:
                job_id = f"monster_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Get title
            try:
                title_element = job_element.find_element(By.CSS_SELECTOR, "h3.job-title")
                title = title_element.text.strip()
                
                # Get job URL
                try:
                    title_link = job_element.find_element(By.CSS_SELECTOR, "a[data-test-id='job-card-title']")
                    job_url = title_link.get_attribute('href')
                except:
                    job_url = f"https://www.monster.com/jobs/detail/{job_id}"
            except:
                title = "Not specified"
                job_url = f"https://www.monster.com/jobs/detail/{job_id}"
            
            # Get company
            try:
                company_element = job_element.find_element(By.CSS_SELECTOR, ".job-card-company")
                company = company_element.text.strip()
            except:
                company = "Not specified"
            
            # Get location
            try:
                location_element = job_element.find_element(By.CSS_SELECTOR, ".job-card-location")
                location = location_element.text.strip()
                
                # Check if remote
                if "remote" in location.lower():
                    location = f"{location} (Remote)"
            except:
                location = "Not specified"
            
            # Get posted date
            try:
                date_element = job_element.find_element(By.CSS_SELECTOR, ".job-card-posted")
                posted_text = date_element.text.strip()
                posted = self.parse_date_posted(posted_text)
            except:
                posted = "30d"  # Default
            
            # Get salary if available (sometimes shown as a range)
            try:
                salary_element = job_element.find_element(By.CSS_SELECTOR, ".job-card-salary")
                salary = salary_element.text.strip()
            except:
                salary = "Not specified"
            
            # Get skills/tags - Monster usually doesn't show these in the card
            tags = "monster"
            
            return {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'posted': posted,
                'tags': tags,
                'url': job_url,
                'date_found': datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            print(f"Error extracting Monster job details: {str(e)}")
            return None
    
    def _extract_jobs(self):
        """Extract all jobs from current page"""
        try:
            print("Waiting for Monster job listings to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card"))
            )
            
            self.human_like_delay(2, 3)
            
            # Get all job cards
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-card")
            print(f"Found {len(job_elements)} potential job listings on Monster page")
            
            new_jobs = []
            for job_element in job_elements:
                job_details = self.extract_job_details(job_element)
                if job_details:
                    new_jobs.append(job_details)
            
            self.jobs_data.extend(new_jobs)
            print(f"Successfully extracted {len(new_jobs)} jobs from Monster")
            return new_jobs
            
        except Exception as e:
            print(f"Error extracting jobs from Monster page: {str(e)}")
            return []
    
    def has_next_page(self):
        """Check if there's a next page of results"""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='search-next-page']")
            if 'disabled' in next_button.get_attribute('class') or not next_button.is_enabled():
                return None
            return True  # Monster uses JS navigation
        except:
            try:
                # Alternative pagination
                pagination = self.driver.find_element(By.CSS_SELECTOR, ".pagination")
                active_page = pagination.find_element(By.CSS_SELECTOR, ".active")
                next_page = active_page.find_element(By.XPATH, "following-sibling::li[1]/a")
                return next_page.get_attribute('href')
            except:
                return None
    
    def go_to_next_page(self, next_url):
        """Navigate to the next page of results"""
        try:
            if isinstance(next_url, bool):
                # Javascript based navigation
                next_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='search-next-page']")
                next_button.click()
            else:
                # Standard link navigation
                self.driver.get(next_url)
                
            # Wait for new results to load
            self.human_like_delay(3, 5)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card"))
            )
            
            return True
        except Exception as e:
            print(f"Error navigating to next Monster page: {str(e)}")
            return False