import re
import time
from datetime import datetime
from urllib.parse import quote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException

from job_scrapers.base_scraper import BaseJobScraper

class LinkedInScraper(BaseJobScraper):
    """Scraper for LinkedIn Jobs"""
    
    def __init__(self, db_instance=None):
        super().__init__(source_name="LinkedIn", requires_login=True, db_instance=db_instance)
    
    def get_base_url(self, remote_only=True):
        """Get the starting URL based on search parameters"""
        job_search_url = "https://www.linkedin.com/jobs/search/?"
        
        # Base search for frontend developer roles
        params = {
            'keywords': 'frontend developer',
            'f_TPR': 'r2592000',  # Last 30 days
            'sortBy': 'DD',  # Sort by most recent
        }
        
        # Add remote filter if requested
        if remote_only:
            params['f_WT'] = '2'  # Remote filter
        
        # Construct query string manually
        query_parts = []
        for key, value in params.items():
            query_parts.append(f"{key}={quote(str(value))}")
        
        return job_search_url + "&".join(query_parts)
    
    def login(self, username, password):
        """Login to LinkedIn"""
        try:
            print(f"Attempting to log in to LinkedIn with username: {username}")
            
            # Navigate to login page
            self.driver.get("https://www.linkedin.com/login")
            self.human_like_delay(2, 3)
            
            # Enter username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(username)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click sign in button
            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            sign_in_button.click()
            
            # Wait for login to complete
            self.human_like_delay(5, 7)
            
            # Check if login was successful by looking for the LinkedIn logo
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".global-nav__logo"))
                )
                print("Successfully logged in to LinkedIn")
                return True
            except TimeoutException:
                print("Login to LinkedIn failed - could not verify success")
                return False
                
        except Exception as e:
            print(f"Error during LinkedIn login: {str(e)}")
            return False
    
    def parse_date_posted(self, date_text):
        """Convert LinkedIn's relative date to days"""
        if not date_text:
            return '30d'
            
        date_text = date_text.lower()
        
        if 'just now' in date_text or 'less than a' in date_text or 'an hour ago' in date_text:
            return '0d'
            
        if 'hour' in date_text:
            return '0d'
            
        if 'day' in date_text:
            days_match = re.search(r'(\d+)\s+day', date_text)
            if days_match:
                return f"{days_match.group(1)}d"
            return '1d'
            
        if 'week' in date_text:
            weeks_match = re.search(r'(\d+)\s+week', date_text)
            if weeks_match:
                days = int(weeks_match.group(1)) * 7
                return f"{days}d"
            return '7d'
            
        if 'month' in date_text:
            months_match = re.search(r'(\d+)\s+month', date_text)
            if months_match:
                days = int(months_match.group(1)) * 30
                return f"{days}d"
            return '30d'
            
        return '30d'  # Default
    
    def extract_job_details(self, job_element):
        """Extract all details from a single job listing"""
        try:
            # Click on the job to load details
            try:
                job_element.click()
                self.human_like_delay(1, 2)
            except ElementClickInterceptedException:
                # Sometimes LinkedIn has overlays that prevent clicking
                self.driver.execute_script("arguments[0].click();", job_element)
                self.human_like_delay(1, 2)
            
            # Get job ID
            try:
                current_url = self.driver.current_url
                job_id_match = re.search(r'currentJobId=(\d+)', current_url)
                if job_id_match:
                    job_id = job_id_match.group(1)
                else:
                    # Alternative method
                    job_id = job_element.get_attribute('data-job-id') or job_element.get_attribute('id')
            except:
                job_id = f"linkedin_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Wait for job details to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title"))
            )
            
            # Get title
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title")
                title = title_element.text.strip()
            except:
                try:
                    title_element = job_element.find_element(By.CSS_SELECTOR, "h3.base-search-card__title")
                    title = title_element.text.strip()
                except:
                    title = "Not specified"
            
            # Get company
            try:
                company_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name")
                company = company_element.text.strip()
            except:
                try:
                    company_element = job_element.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle")
                    company = company_element.text.strip()
                except:
                    company = "Not specified"
            
            # Get location
            try:
                location_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__bullet")
                location = location_element.text.strip()
            except:
                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                    location = location_element.text.strip()
                except:
                    location = "Not specified"
            
            # Add remote indicator if present
            try:
                workplace_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__workplace-type")
                workplace_type = workplace_element.text.strip()
                if 'remote' in workplace_type.lower():
                    location = f"{location} (Remote)"
            except:
                pass
            
            # Get posted date
            try:
                date_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__posted-date")
                posted_text = date_element.text.strip()
            except:
                try:
                    date_element = job_element.find_element(By.CSS_SELECTOR, ".job-search-card__listdate")
                    posted_text = date_element.text.strip()
                except:
                    posted_text = "30+ days ago"
            
            posted = self.parse_date_posted(posted_text)
            
            # Get salary if available
            try:
                salary_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-insight:contains('$')")
                salary = salary_element.text.strip()
            except:
                salary = "Not specified"
            
            # Get skills/tags if available
            tags = []
            try:
                skill_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-details-skill-match-card__skills-item")
                for skill in skill_elements:
                    tags.append(skill.text.strip())
            except:
                pass
            
            # Get job URL
            job_url = self.driver.current_url
            
            return {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'posted': posted,
                'tags': ', '.join(tags) if tags else 'linkedin',
                'url': job_url,
                'date_found': datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            print(f"Error extracting LinkedIn job details: {str(e)}")
            return None
    
    def _extract_jobs(self):
        """Extract all jobs from current page"""
        try:
            print("Waiting for LinkedIn job listings to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.jobs-search-results__list-item"))
            )
            
            self.human_like_delay(2, 3)
            
            # Get all job cards
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, "li.jobs-search-results__list-item")
            print(f"Found {len(job_elements)} potential job listings on current LinkedIn page")
            
            new_jobs = []
            for index, job_element in enumerate(job_elements):
                print(f"Processing LinkedIn job {index+1}/{len(job_elements)}")
                job_details = self.extract_job_details(job_element)
                if job_details:
                    new_jobs.append(job_details)
                self.human_like_delay(1, 2)  # Small delay between processing each job
            
            self.jobs_data.extend(new_jobs)
            print(f"Successfully extracted {len(new_jobs)} jobs from LinkedIn")
            return new_jobs
            
        except Exception as e:
            print(f"Error extracting jobs from LinkedIn page: {str(e)}")
            return []
    
    def has_next_page(self):
        """Check if there's a next page and get its URL"""
        try:
            # Find the next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button.artdeco-pagination__button--next:not(.artdeco-button--disabled)")
            return True  # LinkedIn uses JS navigation, so we just return True if next button exists
        except:
            return None
    
    def go_to_next_page(self, next_url):
        """Navigate to the next page"""
        try:
            # Since LinkedIn uses JS navigation, we need to click the next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button.artdeco-pagination__button--next")
            next_button.click()
            self.human_like_delay(3, 5)
            
            # Wait for job listings to reload
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.jobs-search-results__list-item"))
            )
            
            return True
        except Exception as e:
            print(f"Error navigating to next LinkedIn page: {str(e)}")
            return False