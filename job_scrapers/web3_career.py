import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from job_scrapers.base_scraper import BaseJobScraper

class Web3CareerScraper(BaseJobScraper):
    """Scraper for web3.career"""
    
    def __init__(self):
        super().__init__(source_name="web3.career", requires_login=False)
    
    def get_base_url(self, remote_only=True):
        """Get the starting URL based on remote filter"""
        return "https://web3.career/front-end+remote-jobs" if remote_only else "https://web3.career/front-end-jobs"
    
    def login(self, username, password):
        """Not required for web3.career"""
        return True  # No login needed
    
    def is_bootcamp_or_ad(self, job_element):
        """Check if the job listing is actually a bootcamp ad or sponsored content"""
        try:
            bootcamp_indicators = ['bootcamp', 'course', 'guaranteed', 'learn', 'training']
            job_text = job_element.text.lower()
            
            is_sponsored = 'sponsor' in job_element.get_attribute('id').lower() if job_element.get_attribute('id') else False
            has_bootcamp_keywords = any(indicator in job_text for indicator in bootcamp_indicators)
            
            return is_sponsored or has_bootcamp_keywords
        except Exception:
            return False
    
    def extract_job_details(self, job_element):
        """Extract all details from a single job listing"""
        try:
            if self.is_bootcamp_or_ad(job_element):
                return None

            job_id = job_element.get_attribute('data-jobid')
            if not job_id:
                return None

            # Get title
            title_element = job_element.find_element(By.CSS_SELECTOR, "h2.fs-6.fs-md-5.fw-bold.my-primary")
            title = title_element.text.strip()

            # Get company
            company_element = job_element.find_element(By.CSS_SELECTOR, "h3[style*='font-size: 12px']")
            company = company_element.text.strip()

            # Get location
            try:
                # Find the fourth td element which contains the location
                location_td = job_element.find_elements(By.TAG_NAME, "td")[3]
                location_element = location_td.find_element(By.CSS_SELECTOR, "span[style*='color: #d5d3d3'], a[style*='color: #d5d3d3']")
                location = location_element.text.strip()
            except:
                location = "Not specified"

            # Get salary
            try:
                salary_element = job_element.find_element(By.CSS_SELECTOR, "p[class*='text-salary']")
                salary = salary_element.text.split('\n')[0].strip()
            except:
                salary = "Not specified"

            # Get posted time
            try:
                time_element = job_element.find_element(By.TAG_NAME, "time")
                posted = time_element.text.strip()
            except:
                posted = "Not specified"

            # Get tags
            try:
                tag_elements = job_element.find_elements(By.CSS_SELECTOR, "span.my-badge.my-badge-secondary a")
                tags = [tag.text.strip() for tag in tag_elements if tag.text.strip()]
            except:
                tags = []

            # Get job URL
            try:
                job_link = title_element.find_element(By.XPATH, "..").get_attribute('href')
                full_url = f"https://web3.career{job_link}" if job_link.startswith('/') else job_link
            except:
                full_url = f"https://web3.career/front-end-jobs/{job_id}"

            return {
                'id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'posted': posted,
                'tags': ', '.join(tags),
                'url': full_url,
                'date_found': datetime.now().strftime("%Y-%m-%d")
            }

        except Exception as e:
            print(f"Error extracting job details: {str(e)}")
            return None
    
    def is_within_time_range(self, posted):
        """Check if job was posted within the last 30 days"""
        try:
            days = int(posted.replace('d', ''))
            return days <= 30
        except:
            return False
    
    def _extract_jobs(self):
        """Extract all jobs from current page"""
        try:
            print("Waiting for job listings to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tr[data-jobid]"))
            )
            
            self.human_like_delay(2, 3)
            
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, "tr[data-jobid]")
            print(f"Found {len(job_elements)} potential job listings on current page")
            
            new_jobs = []
            for job_element in job_elements:
                job_details = self.extract_job_details(job_element)
                if job_details and self.is_within_time_range(job_details['posted']):
                    new_jobs.append(job_details)
            
            self.jobs_data.extend(new_jobs)
            print(f"Successfully extracted {len(new_jobs)} jobs within time range")
            return new_jobs
            
        except Exception as e:
            print(f"Error extracting jobs from page: {str(e)}")
            return []
    
    def has_next_page(self):
        """Check if there's a next page and get its URL"""
        try:
            next_link = self.driver.find_element(By.CSS_SELECTOR, "li.page-item.next:not(.disabled) a")
            next_url = next_link.get_attribute('href')
            return next_url
        except:
            return None
    
    def go_to_next_page(self, next_url):
        """Navigate to the next page"""
        try:
            print(f"Navigating to next page: {next_url}")
            self.driver.get(next_url)
            self.human_like_delay(3, 5)
            return True
        except:
            return False