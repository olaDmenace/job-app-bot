import re
from datetime import datetime
from urllib.parse import urlencode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from job_scrapers.base_scraper import BaseJobScraper

class AdzunaScraper(BaseJobScraper):
    """Scraper for Adzuna"""
    
    def __init__(self):
        super().__init__(source_name="Adzuna", requires_login=False)
    
    def get_base_url(self, remote_only=True):
        """Get the starting URL for job search"""
        # Base URL for US site (can be adjusted for other countries)
        base_url = "https://www.adzuna.com/search?"
        
        params = {
            'q': 'frontend developer',
            'w': '',  # Location left blank for remote
            'sort': 'date',  # Sort by date
            'days': '30'  # Last 30 days
        }
        
        # Add remote filter if requested
        if remote_only:
            params['remote_work'] = '1'  # Remote work filter
        
        return base_url + urlencode(params)
    
    def login(self, username, password):
        """Not required for Adzuna"""
        return True  # No login needed for basic search
    
    def parse_date_posted(self, date_text):
        """Convert Adzuna's date format to days"""
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
                job_id = f"adzuna_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Get title and URL
            try:
                title_element = job_element.find_element(By.CSS_SELECTOR, "h2.Jobentry__title")
                title = title_element.text.strip()
                
                link_element = job_element.find_element(By.CSS_SELECTOR, "a.Jobentry__title-link")
                job_url = link_element.get_attribute('href')
            except:
                try:
                    # Alternative structure
                    title_element = job_element.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle")
                    title = title_element.text.strip()
                    job_url = title_element.get_attribute('href')
                except:
                    title = "Not specified"
                    job_url = f"https://www.adzuna.com/details/{job_id}"
            
            # Get company
            try:
                company_element = job_element.find_element(By.CSS_SELECTOR, "div.Jobentry__company")
                company = company_element.text.strip()
            except:
                try:
                    company_element = job_element.find_element(By.CSS_SELECTOR, "div.jcs-JobemployerName")
                    company = company_element.text.strip()
                except:
                    company = "Not specified"
            
            # Get location
            try:
                location_element = job_element.find_element(By.CSS_SELECTOR, "div.Jobentry__location")
                location = location_element.text.strip()
            except:
                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, "span.jcs-Joblocation")
                    location = location_element.text.strip()
                except:
                    location = "Not specified"
            
            # Add remote indicator if present
            if job_element.find_elements(By.CSS_SELECTOR, ".remote-tag, span.jcs-JobRemote"):
                location = f"{location} (Remote)"
            
            # Get posted date
            try:
                date_element = job_element.find_element(By.CSS_SELECTOR, "div.Jobentry__details--block-posting")
                posted_text = date_element.text.strip()
                posted = self.parse_date_posted(posted_text)
            except:
                try:
                    # Alternative date format
                    date_element = job_element.find_element(By.CSS_SELECTOR, "span.jcs-JobDate")
                    posted_text = date_element.text.strip()
                    posted = self.parse_date_posted(posted_text)
                except:
                    posted = "30d"  # Default
            
            # Get salary if available
            try:
                salary_element = job_element.find_element(By.CSS_SELECTOR, "div.Jobentry__details--block-salary")
                salary = salary_element.text.strip()
            except:
                try:
                    salary_element = job_element.find_element(By.CSS_SELECTOR, "span.jcs-JobSalary")
                    salary = salary_element.text.strip()
                except:
                    salary = "Not specified"
            
            # Get tags if available
            tags = []
            try:
                tag_elements = job_element.find_elements(By.CSS_SELECTOR, ".tag-chip")
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
                'tags': ', '.join(tags) if tags else 'adzuna',
                'url': job_url,
                'date_found': datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            print(f"Error extracting Adzuna job details: {str(e)}")
            return None
    
    def _extract_jobs(self):
        """Extract all jobs from current page"""
        try:
            print("Waiting for Adzuna job listings to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".Jobentry, .jcs-JobContainer"))
            )
            
            self.human_like_delay(2, 3)
            
            # Get all job cards (handle different possible structures)
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".Jobentry, .jcs-JobContainer")
            print(f"Found {len(job_elements)} potential job listings on Adzuna page")
            
            new_jobs = []
            for job_element in job_elements:
                job_details = self.extract_job_details(job_element)
                if job_details:
                    new_jobs.append(job_details)
            
            self.jobs_data.extend(new_jobs)
            print(f"Successfully extracted {len(new_jobs)} jobs from Adzuna")
            return new_jobs
            
        except Exception as e:
            print(f"Error extracting jobs from Adzuna page: {str(e)}")
            return []
    
    def has_next_page(self):
        """Check if there's a next page of results"""
        try:
            # Try to find the next page link
            next_link = self.driver.find_element(By.CSS_SELECTOR, "a[rel='next'], .pagination--next")
            next_url = next_link.get_attribute('href')
            return next_url
        except NoSuchElementException:
            return None
    
    def go_to_next_page(self, next_url):
        """Navigate to the next page of results"""
        try:
            print(f"Navigating to next Adzuna page: {next_url}")
            self.driver.get(next_url)
            self.human_like_delay(3, 5)
            
            # Wait for new results to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".Jobentry, .jcs-JobContainer"))
            )
            
            return True
        except Exception as e:
            print(f"Error navigating to next Adzuna page: {str(e)}")
            return False