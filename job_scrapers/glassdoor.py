import re
from datetime import datetime
from urllib.parse import urlencode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException

from job_scrapers.base_scraper import BaseJobScraper

class GlassdoorScraper(BaseJobScraper):
    """Scraper for Glassdoor"""
    
    def __init__(self):
        super().__init__(source_name="Glassdoor", requires_login=True)
    
    def get_base_url(self, remote_only=True):
        """Get the starting URL for job search"""
        params = {
            'keyword': 'frontend developer',
            'sortBy': 'date',
            'fromAge': '30'  # Last 30 days
        }
        
        # Add remote filter if requested
        if remote_only:
            params['remoteWorkType'] = 'REMOTE'
        
        base_url = "https://www.glassdoor.com/Job/jobs.htm?"
        return base_url + urlencode(params)
    
    def login(self, username, password):
        """Login to Glassdoor"""
        try:
            print(f"Attempting to log in to Glassdoor with username: {username}")
            
            # Go to login page
            self.driver.get("https://www.glassdoor.com/profile/login_input.htm")
            self.human_like_delay(2, 3)
            
            # Handle potential redirects or overlays
            try:
                # Close any modals that might appear
                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.modal_closeIcon, .close")
                for button in close_buttons:
                    try:
                        button.click()
                        print("Closed a modal dialog")
                        self.human_like_delay(1, 2)
                    except:
                        pass
            except:
                pass  # No modals to close
            
            # Enter email - Glassdoor has multiple possible login form structures
            try:
                # Try to find the email field
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "modalUserEmail")) or
                    EC.element_to_be_clickable((By.ID, "userEmail")) or
                    EC.element_to_be_clickable((By.NAME, "username"))
                )
                email_field.clear()
                email_field.send_keys(username)
                
                # Click continue button if present
                try:
                    continue_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    continue_button.click()
                    self.human_like_delay(2, 3)
                except:
                    pass  # No continue button
                
                # Now try to find the password field
                password_field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "modalUserPassword")) or
                    EC.element_to_be_clickable((By.ID, "userPassword")) or
                    EC.element_to_be_clickable((By.NAME, "password"))
                )
                password_field.clear()
                password_field.send_keys(password)
                
                # Click sign in button
                sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                sign_in_button.click()
                
                # Wait for successful login
                self.human_like_delay(5, 7)
                
                # Verify login success
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".member-home-content, .user-menu"))
                    )
                    print("Successfully logged in to Glassdoor")
                    return True
                except TimeoutException:
                    print("Login to Glassdoor failed - could not verify success")
                    return False
                    
            except Exception as e:
                print(f"Error with login form: {str(e)}")
                return False
                
        except Exception as e:
            print(f"Error during Glassdoor login: {str(e)}")
            return False
    
    def parse_date_posted(self, date_text):
        """Convert Glassdoor's date format to days"""
        if not date_text:
            return '30d'
            
        date_text = date_text.lower()
        
        if 'today' in date_text or 'just posted' in date_text or 'hour' in date_text:
            return '0d'
            
        if 'yesterday' in date_text or '1 day' in date_text:
            return '1d'
            
        days_match = re.search(r'(\d+)\s*d', date_text)
        if days_match:
            return f"{days_match.group(1)}d"
            
        weeks_match = re.search(r'(\d+)\s*w', date_text)
        if weeks_match:
            days = int(weeks_match.group(1)) * 7
            return f"{days}d"
            
        months_match = re.search(r'(\d+)\s*mo', date_text)
        if months_match:
            days = int(months_match.group(1)) * 30
            return f"{days}d"
            
        return '30d'  # Default
    
    def extract_job_details(self, job_element):
        """Extract job details from a single listing"""
        try:
            # Click on the job to load details in the sidebar
            try:
                job_element.click()
                self.human_like_delay(1, 2)
            except ElementClickInterceptedException:
                # Handle overlays
                self.driver.execute_script("arguments[0].click();", job_element)
                self.human_like_delay(1, 2)
                
            # Get job ID from various attributes
            job_id = job_element.get_attribute('data-id') or job_element.get_attribute('id')
            if not job_id:
                # Extract from URL if possible
                try:
                    current_url = self.driver.current_url
                    job_id_match = re.search(r'jobListingId=(\d+)', current_url)
                    if job_id_match:
                        job_id = job_id_match.group(1)
                    else:
                        job_id = f"glassdoor_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                except:
                    job_id = f"glassdoor_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Get title
            try:
                title_element = job_element.find_element(By.CSS_SELECTOR, "a.jobTitle")
                title = title_element.text.strip()
                
                # Get job URL
                job_url = title_element.get_attribute('href')
            except NoSuchElementException:
                try:
                    # Alternative structure
                    title_element = job_element.find_element(By.CSS_SELECTOR, "div.jobTitle")
                    title = title_element.text.strip()
                    job_url = f"https://www.glassdoor.com/job-listing/{job_id}"
                except:
                    title = "Not specified"
                    job_url = f"https://www.glassdoor.com/job-listing/{job_id}"
            
            # Get company
            try:
                company_element = job_element.find_element(By.CSS_SELECTOR, "div.companyName")
                company = company_element.text.strip()
            except:
                try:
                    company_element = job_element.find_element(By.CSS_SELECTOR, "div.jobCompany")
                    company = company_element.text.strip().split('\n')[0]
                except:
                    company = "Not specified"
            
            # Get location
            try:
                location_element = job_element.find_element(By.CSS_SELECTOR, "div.location")
                location = location_element.text.strip()
                
                # Check if remote
                if "remote" in location.lower():
                    location = f"{location} (Remote)"
            except:
                try:
                    # Alternative location format
                    location_element = job_element.find_element(By.CSS_SELECTOR, "div.companyLocation")
                    location = location_element.text.strip()
                    
                    if "remote" in location.lower():
                        location = f"{location} (Remote)"
                except:
                    location = "Not specified"
            
            # Get posted date
            try:
                date_element = job_element.find_element(By.CSS_SELECTOR, "div.listing-age")
                posted_text = date_element.text.strip()
                posted = self.parse_date_posted(posted_text)
            except:
                try:
                    # Alternative date format
                    date_element = job_element.find_element(By.CSS_SELECTOR, "div.jobAge")
                    posted_text = date_element.text.strip()
                    posted = self.parse_date_posted(posted_text)
                except:
                    posted = "30d"  # Default
            
            # Get salary if available
            try:
                salary_element = job_element.find_element(By.CSS_SELECTOR, "div.salary-estimate")
                salary = salary_element.text.strip()
            except:
                try:
                    # Alternative salary format
                    salary_element = job_element.find_element(By.CSS_SELECTOR, "span[data-test='detailSalary']")
                    salary = salary_element.text.strip()
                except:
                    salary = "Not specified"
            
            # Build and return job object
            return {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'posted': posted,
                'tags': 'glassdoor',
                'url': job_url,
                'date_found': datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            print(f"Error extracting Glassdoor job details: {str(e)}")
            return None
    
    def _extract_jobs(self):
        """Extract all jobs from current page"""
        try:
            print("Waiting for Glassdoor job listings to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.react-job-listing"))
            )
            
            self.human_like_delay(2, 3)
            
            # Close any popups that might appear
            try:
                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.modal_closeIcon, .close")
                for button in close_buttons:
                    try:
                        button.click()
                        print("Closed a modal dialog")
                        self.human_like_delay(1, 2)
                    except:
                        pass
            except:
                pass  # No popups
            
            # Get all job cards
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, "li.react-job-listing")
            print(f"Found {len(job_elements)} potential job listings on Glassdoor page")
            
            new_jobs = []
            for index, job_element in enumerate(job_elements):
                print(f"Processing Glassdoor job {index+1}/{len(job_elements)}")
                job_details = self.extract_job_details(job_element)
                if job_details:
                    new_jobs.append(job_details)
            
            self.jobs_data.extend(new_jobs)
            print(f"Successfully extracted {len(new_jobs)} jobs from Glassdoor")
            return new_jobs
            
        except Exception as e:
            print(f"Error extracting jobs from Glassdoor page: {str(e)}")
            return []
    
    def has_next_page(self):
        """Check if there's a next page of results"""
        try:
            # Find next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button.nextButton, li.next a")
            if 'disabled' in next_button.get_attribute('class'):
                return None
            return True  # Glassdoor uses JS navigation
        except:
            return None
    
    def go_to_next_page(self, next_url):
        """Navigate to the next page of results"""
        try:
            # Click the next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button.nextButton, li.next a")
            next_button.click()
            
            # Wait for new results to load
            self.human_like_delay(3, 5)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.react-job-listing"))
            )
            
            return True
        except Exception as e:
            print(f"Error navigating to next Glassdoor page: {str(e)}")
            return False