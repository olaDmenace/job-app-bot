import os
import time
import random
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from database_manager import JobApplicationDB

class ContactFinder:
    def __init__(self, db_instance=None):
        self.driver = None
        self.contacts_data = []
        # Use existing DB instance if provided, otherwise create new
        self.db = db_instance if db_instance else JobApplicationDB()

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

    def find_linkedin_contacts(self, company_name, positions=None):
        """Find contacts on LinkedIn for a given company"""
        if positions is None:
            positions = ['CTO', 'Engineering Manager', 'Tech Lead', 'VP of Engineering', 'Hiring Manager']
        
        try:
            # First, search for the company
            search_url = f"https://www.linkedin.com/company/{company_name}/people/"
            self.driver.get(search_url)
            self.human_like_delay(3, 5)
            
            # Extract employees with matching positions
            contacts = []
            for position in positions:
                try:
                    elements = self.driver.find_elements(By.XPATH, 
                        f"//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{position.lower()}')]//ancestor::li")
                    
                    for element in elements:
                        contact = self._extract_linkedin_contact(element, company_name)
                        if contact:
                            contacts.append(contact)
                            
                except Exception as e:
                    print(f"Error finding contacts with position {position}: {str(e)}")
                    continue
                
            return contacts
            
        except Exception as e:
            print(f"Error searching LinkedIn for {company_name}: {str(e)}")
            return []

    def find_wellfound_contacts(self, company_name):
        """Find contacts on WellFound (AngelList Talent) for a given company"""
        try:
            search_url = f"https://wellfound.com/company/{company_name}"
            self.driver.get(search_url)
            self.human_like_delay(3, 5)
            
            # Find team section
            team_elements = self.driver.find_elements(By.CSS_SELECTOR, ".team-member-card")
            
            contacts = []
            for element in team_elements:
                contact = self._extract_wellfound_contact(element, company_name)
                if contact:
                    contacts.append(contact)
                    
            return contacts
            
        except Exception as e:
            print(f"Error searching WellFound for {company_name}: {str(e)}")
            return []

    def _extract_linkedin_contact(self, element, company_name):
        """Extract contact details from LinkedIn element"""
        try:
            name = element.find_element(By.CSS_SELECTOR, ".name").text.strip()
            title = element.find_element(By.CSS_SELECTOR, ".title").text.strip()
            profile_url = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            
            return {
                'name': name,
                'title': title,
                'company': company_name,
                'linkedin_url': profile_url,
                'source': 'LinkedIn',
                'is_hiring_manager': any(role.lower() in title.lower() 
                    for role in ['manager', 'lead', 'head', 'director', 'vp', 'chief']),
                'is_technical': any(tech.lower() in title.lower() 
                    for tech in ['engineer', 'developer', 'technical', 'technology', 'cto'])
            }
            
        except Exception:
            return None

    def _extract_wellfound_contact(self, element, company_name):
        """Extract contact details from WellFound element"""
        try:
            name = element.find_element(By.CSS_SELECTOR, ".name").text.strip()
            title = element.find_element(By.CSS_SELECTOR, ".role").text.strip()
            profile_url = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            
            return {
                'name': name,
                'title': title,
                'company': company_name,
                'wellfound_url': profile_url,
                'source': 'WellFound',
                'is_hiring_manager': any(role.lower() in title.lower() 
                    for role in ['manager', 'lead', 'head', 'director', 'vp', 'chief']),
                'is_technical': any(tech.lower() in title.lower() 
                    for tech in ['engineer', 'developer', 'technical', 'technology', 'cto'])
            }
            
        except Exception:
            return None

    def save_contacts(self):
        """Save contacts to both database and CSV"""
        if not self.contacts_data:
            print("No contacts to save")
            return
            
        try:
            # Save to CSV for backup
            filename = f"contacts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            
            # Save to CSV using built-in csv module
            if self.contacts_data:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = self.contacts_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.contacts_data)
                print(f"\nSaved {len(self.contacts_data)} contacts to {filename}")
            
            # Save to database
            saved_count = 0
            for contact in self.contacts_data:
                # Save to database (you'll need to add this method to your DB manager)
                self.db.add_contact(contact)
                saved_count += 1
            
            print(f"Saved {saved_count} contacts to database")
            
        except Exception as e:
            print(f"Error saving contacts: {str(e)}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {str(e)}")

    def find_contacts_for_companies(self, companies):
        """Main method to find contacts for a list of companies"""
        try:
            if not self.setup_driver():
                print("Failed to set up browser. Aborting search.")
                return
            
            total_contacts = 0
            
            for company in companies:
                print(f"\nSearching contacts for {company}...")
                
                # Find LinkedIn contacts
                linkedin_contacts = self.find_linkedin_contacts(company)
                self.contacts_data.extend(linkedin_contacts)
                
                # Add delay between searches
                self.human_like_delay(5, 8)
                
                # Find WellFound contacts
                wellfound_contacts = self.find_wellfound_contacts(company)
                self.contacts_data.extend(wellfound_contacts)
                
                total_contacts += len(linkedin_contacts) + len(wellfound_contacts)
                print(f"Found {len(linkedin_contacts)} LinkedIn and {len(wellfound_contacts)} WellFound contacts for {company}")
                
                # Add longer delay between companies
                self.human_like_delay(8, 12)
            
            print(f"\nTotal contacts found: {total_contacts}")
            self.save_contacts()
            
        except Exception as e:
            print(f"Error during contact search process: {str(e)}")
            
        finally:
            self.cleanup()

# Example usage
if __name__ == "__main__":
    # Get companies from your jobs database or provide a list
    companies = ["example-company-1", "example-company-2"]
    finder = ContactFinder()
    finder.find_contacts_for_companies(companies)