import os
import time
import random
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from database_manager import JobApplicationDB

class Web3CareerBot:
    def __init__(self):
        self.driver = None
        self.jobs_data = []
        self.db = JobApplicationDB()  # Initialize database connection

    def get_base_url(self, remote_only=True):
        """Get the starting URL based on remote filter"""
        return "https://web3.career/front-end+remote-jobs" if remote_only else "https://web3.career/front-end-jobs"

    def setup_driver(self):
        """Initialize and configure the Chrome driver"""
        try:
            options = webdriver.ChromeOptions()
            options.binary_location = "/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev"
            
            # Browser settings
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Set user agent
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            options.add_argument(f'--user-agent={user_agent}')
            
            # Disable automation flags
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Setup ChromeDriver
            driver_path = os.path.join(os.getcwd(), "drivers", "chromedriver")
            service = Service(driver_path)
            
            # Initialize driver
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("Browser setup successful")
            return True
            
        except Exception as e:
            print(f"Error setting up browser: {str(e)}")
            return False

    def human_like_delay(self, min_seconds=2, max_seconds=5):
        """Add random delay to mimic human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds))

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

    def is_within_time_range(self, posted):
        """Check if job was posted within the last 30 days"""
        try:
            days = int(posted.replace('d', ''))
            return days <= 30
        except:
            return False

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

    def save_jobs(self):
        """Save jobs to both database and CSV"""
        if not self.jobs_data:
            print("No jobs to save")
            return
            
        try:
            # Save to CSV for backup
            filename = f"web3_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            df = pd.DataFrame(self.jobs_data)
            
            # Sort by posted date
            df['days_ago'] = df['posted'].str.extract('(\d+)').astype(float)
            df = df.sort_values('days_ago')
            df = df.drop('days_ago', axis=1)
            
            # Save to CSV
            df.to_csv(filename, index=False)
            print(f"\nSaved {len(self.jobs_data)} jobs to {filename}")
            
            # Save to database
            db_saved_count = 0
            for job in self.jobs_data:
                # Add source information
                job['source'] = 'web3.career'
                
                # Save to database
                self.db.add_job(job)
                db_saved_count += 1
            
            print(f"Saved {db_saved_count} jobs to database")
            
            # Display jobs from database
            all_applications = self.db.get_all_applications()
            if all_applications:
                print("\nRecent Jobs in Database:")
                for app in all_applications[:15]:  # Show last 15 jobs
                    print(
                        f"Title: {app['title']}\n"
                        f"Company: {app['company']}\n"
                        f"Location: {app['location']}\n"
                        f"Status: {app['status']}\n"
                        f"Posted: {app['posted']}\n"
                        f"Salary: {app['salary']}\n"
                        f"---"
                    )
            
        except Exception as e:
            print(f"Error saving jobs: {str(e)}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {str(e)}")
        
        if hasattr(self, 'db'):
            self.db.close()

    def run_job_search(self, remote_only=True, max_pages=5):
        """Main method to run the job search process"""
        try:
            if not self.setup_driver():
                print("Failed to set up browser. Aborting search.")
                return
            
            url = self.get_base_url(remote_only)
            print(f"Navigating to: {url}")
            self.driver.get(url)
            
            self.human_like_delay(4, 6)
            
            page = 1
            total_jobs = 0
            
            while page <= max_pages:
                print(f"\nProcessing page {page}...")
                
                new_jobs = self._extract_jobs()
                total_jobs += len(new_jobs)
                
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
            
        except Exception as e:
            print(f"Error during job search process: {str(e)}")
            
        finally:
            self.cleanup()

if __name__ == "__main__":
    bot = Web3CareerBot()
    bot.run_job_search(remote_only=True, max_pages=5)