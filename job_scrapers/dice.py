import re
from datetime import datetime
from urllib.parse import urlencode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from job_scrapers.base_scraper import BaseJobScraper

class DiceScraper(BaseJobScraper):
    """Scraper for Dice.com"""
    
    def __init__(self, db_instance=None):
        super().__init__(source_name="Dice", requires_login=True, db_instance=db_instance)
    
    def get_base_url(self, remote_only=True):
        """Get the starting URL for job search"""
        params = {
            'q': 'frontend developer',
            'radius': '30',
            'radiusUnit': 'mi',
            'page': '1',
            'pageSize': '20',
            'filters.postedDate': 'ONE',  # Last 24 hours
            'language': 'en'
        }
        
        # Add remote filter if requested
        if remote_only:
            params['filters.workFromHomeAvailability'] = 'TRUE'
        
        base_url = "https://www.dice.com/jobs?"
        return base_url + urlencode(params)
    
    def login(self, username, password):
        """Login to Dice"""
        try:
            print(f"Attempting to log in to Dice with username: {username}")
            
            # Go to login page
            self.driver.get("https://www.dice.com/dashboard/login")
            self.human_like_delay(2, 3)
            
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
            
            # Verify login success
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".logged-in-container"))
                )
                print("Successfully logged in to Dice")
                return True
            except TimeoutException:
                print("Login failed - could not verify success")
                return False
                
        except Exception as e:
            print(f"Error during Dice login: {str(e)}")
            return False
    
    def parse_date_posted(self, date_text):
        """Convert Dice's date format to days"""
        if not date_text:
            return '30d'
            
        date_text = date_text.lower()
        
        if 'today' in date_text or 'just now' in date_text:
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
                job_id = f"dice_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Get title
            try:
                title_element = job_element.find_element(By.CSS_SELECTOR, "a.card-title-link")
                title = title_element.text.strip()
                
                # Get job URL from title link
                job_url = title_element.get_attribute('href')
            except NoSuchElementException:
                title = "Not specified"
                job_url = f"https://www.dice.com/jobs/{job_id}"
            
            # Get company
            try:
                company_element = job_element.find_element(By.CSS_SELECTOR, "div.company-name-rating a")
                company = company_element.text.strip()
            except NoSuchElementException:
                try:
                    company_element = job_element.find_element(By.CSS_SELECTOR, "div.company-name-rating span")
                    company = company_element.text.strip()
                except:
                    company = "Not specified"
            
            # Get location
            try:
                location_element = job_element.find_element(By.CSS_SELECTOR, "span.location")
                location = location_element.text.strip()
                
                # Check if it's remote
                try:
                    remote_element = job_element.find_element(By.CSS_SELECTOR, "span.remote-label")
                    if remote_element.text.strip():
                        location = f"{location} (Remote)"
                except:
                    pass
            except:
                location = "Not specified"
            
            # Get posted date
            try:
                date_element = job_element.find_element(By.CSS_SELECTOR, "span.posted-date")
                posted_text = date_element.text.strip()
                posted = self.parse_date_posted(posted_text)
            except:
                posted = "30d"  # Default to 30 days
            
            # Get salary if available
            try:
                salary_element = job_element.find_element(By.CSS_SELECTOR, "span.compensation")
                salary = salary_element.text.strip()
            except:
                salary = "Not specified"
            
            # Get skills/tags
            tags = []
            try:
                tag_elements = job_element.find_elements(By.CSS_SELECTOR, "a.skill-button")
                for tag in tag_elements:
                    tags.append(tag.text.strip())
            except:
                pass
            
            return {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'posted': posted,
                'tags': ', '.join(tags) if tags else 'dice',
                'url': job_url,
                'date_found': datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            print(f"Error extracting Dice job details: {str(e)}")
            return None
    
    def _extract_jobs(self):
        """Extract all jobs from current page"""
        try:
            print("Waiting for Dice job listings to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "dhi-search-card"))
            )
            
            self.human_like_delay(2, 3)
            
            # Get all job cards
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, "dhi-search-card")
            print(f"Found {len(job_elements)} potential job listings on Dice page")
            
            new_jobs = []
            for job_element in job_elements:
                job_details = self.extract_job_details(job_element)
                if job_details:
                    new_jobs.append(job_details)
            
            self.jobs_data.extend(new_jobs)
            print(f"Successfully extracted {len(new_jobs)} jobs from Dice")
            return new_jobs
            
        except Exception as e:
            print(f"Error extracting jobs from Dice page: {str(e)}")
            return []
    
    def has_next_page(self):
        """Check if there's a next page of results"""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-cy='pager-next']")
            if 'disabled' in next_button.get_attribute('class'):
                return None
            return True  # Return True since Dice uses JS navigation
        except:
            return None
    
    def go_to_next_page(self, next_url):
        """Navigate to the next page of results"""
        try:
            # Click the next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-cy='pager-next']")
            next_button.click()
            
            # Wait for new results to load
            self.human_like_delay(3, 5)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "dhi-search-card"))
            )
            
            return True
        except Exception as e:
            print(f"Error navigating to next Dice page: {str(e)}")
            return False