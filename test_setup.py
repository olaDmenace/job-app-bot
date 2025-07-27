from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
# import pandas as pd  # Removed to avoid Windows compatibility issues
import os
from dotenv import load_dotenv
import socket
import warnings
import urllib3

# Suppress the SSL warning
warnings.filterwarnings('ignore', category=urllib3.exceptions.NotOpenSSLWarning)

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def test_setup():
    print("Testing installations...")
    
    # Check internet connection first
    internet_available = check_internet()
    if not internet_available:
        print("⚠️  Warning: No internet connection detected. Selenium test will be skipped.")
    
    # Test selenium and chrome driver only if internet is available
    if internet_available:
        try:
            chrome_options = Options()
            chrome_options.binary_location = "/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev"
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # Removed timeout parameter
            service = Service(
                ChromeDriverManager(chrome_type="chrome-dev").install(),
                service_args=['--verbose']
            )
            
            driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            print("✓ Selenium and ChromeDriver setup successful")
            driver.quit()
        except Exception as e:
            print("✗ Selenium setup failed:", str(e))
            print("\nTroubleshooting tips:")
            print("1. Check your internet connection")
            print("2. Try running the script again when connection is better")
            print("3. If problem persists, you might need to manually download ChromeDriver")
    
    # Test CSV functionality (built-in Python module)
    try:
        import csv
        print("[OK] CSV setup successful")
    except Exception as e:
        print("[ERROR] CSV setup failed:", str(e))
    
    # Test dotenv (works offline)
    try:
        load_dotenv()
        print("✓ python-dotenv setup successful")
    except Exception as e:
        print("✗ python-dotenv setup failed:", str(e))
    
    if not internet_available:
        print("\nNote: Run this script again when you have a better internet connection to test Selenium setup.")

if __name__ == "__main__":
    test_setup()