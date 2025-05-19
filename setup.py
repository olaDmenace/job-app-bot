#!/usr/bin/env python3
"""
Setup script for Job Application Bot

This script:
1. Checks Python version
2. Checks ChromeDriver installation
3. Tests Selenium
4. Initializes the database
5. Creates necessary directories
"""

import os
import sys
import subprocess
import platform
from datetime import datetime

def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 80)
    print(" Job Application Bot - Setup Script ".center(80, "="))
    print("=" * 80)
    print("\nThis script will set up your environment for the Job Application Bot.")
    print("\nChecking system requirements...\n")

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    
    major, minor, _ = sys.version_info
    version_str = f"{major}.{minor}.{_}"
    
    if major < 3 or (major == 3 and minor < 8):
        print(f"❌ Python {version_str} detected. This project requires Python 3.8 or higher.")
        return False
    
    print(f"✓ Python {version_str} detected. Compatible!")
    return True

def check_pip_packages():
    """Check if required pip packages are installed"""
    print("\nChecking required packages...")
    
    try:
        # Check if requirements.txt exists
        if not os.path.exists("requirements.txt"):
            print("❌ requirements.txt not found in current directory.")
            return False
        
        # Run pip check to see if packages are installed
        process = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True, 
            text=True
        )
        
        # If pip check succeeded, packages are properly installed
        if process.returncode == 0:
            print("✓ Required packages are properly installed.")
            return True
        
        print("❌ Some packages are missing or have dependency conflicts.")
        print("   Please run 'pip install -r requirements.txt' to resolve.")
        return False
        
    except Exception as e:
        print(f"❌ Error checking pip packages: {str(e)}")
        return False

def check_chromedriver():
    """Check ChromeDriver installation"""
    print("\nChecking ChromeDriver...")
    
    # Create the drivers directory if it doesn't exist
    os.makedirs("drivers", exist_ok=True)
    
    # Determine expected ChromeDriver path
    system = platform.system()
    if system == "Windows":
        chromedriver_path = os.path.join("drivers", "chromedriver.exe")
    else:
        chromedriver_path = os.path.join("drivers", "chromedriver")
    
    # Check if ChromeDriver exists
    if not os.path.exists(chromedriver_path):
        print(f"❌ ChromeDriver not found at {chromedriver_path}")
        print("   Please download the appropriate ChromeDriver for your Chrome version")
        print("   from https://chromedriver.chromium.org/downloads")
        print("   and place it in the 'drivers' directory.")
        return False
    
    # On Unix-like systems, ensure ChromeDriver is executable
    if system != "Windows":
        try:
            subprocess.run(["chmod", "+x", chromedriver_path], check=True)
        except subprocess.CalledProcessError:
            print(f"❌ Failed to set execute permission on {chromedriver_path}")
            print("   Please run 'chmod +x drivers/chromedriver' manually.")
            return False
    
    print(f"✓ ChromeDriver found at {chromedriver_path}")
    return True

def test_selenium():
    """Test Selenium with ChromeDriver"""
    print("\nTesting Selenium with ChromeDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        
        # Determine ChromeDriver path
        system = platform.system()
        if system == "Windows":
            chromedriver_path = os.path.join("drivers", "chromedriver.exe")
        else:
            chromedriver_path = os.path.join("drivers", "chromedriver")
        
        # Configure ChromeDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode for testing
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Initialize Chrome
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        # Test with a simple navigation
        driver.get("https://www.python.org")
        title = driver.title
        
        # Clean up
        driver.quit()
        
        print(f"✓ Selenium test successful! Connected to: {title}")
        return True
        
    except Exception as e:
        print(f"❌ Selenium test failed: {str(e)}")
        print("   Please check your ChromeDriver installation and Chrome version compatibility.")
        return False

def initialize_database():
    """Initialize the SQLite database"""
    print("\nInitializing database...")
    
    try:
        from database_manager import JobApplicationDB
        
        # Initialize the database
        db = JobApplicationDB()
        db.close()
        
        if os.path.exists("job_applications.db"):
            print("✓ Database initialized successfully!")
            return True
        else:
            print("❌ Database not created. Check permissions or disk space.")
            return False
        
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\nCreating necessary directories...")
    
    directories = [
        "output",  # For any output files
        "drivers", # For WebDriver executables
        "logs",    # For log files
        "data",    # For data exports/imports
        "backups"  # For database backups
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {str(e)}")

def check_env_file():
    """Check if .env file exists and create from example if not"""
    print("\nChecking environment configuration...")
    
    if os.path.exists(".env"):
        print("✓ .env file already exists.")
        return True
    
    if os.path.exists(".env.example"):
        try:
            # Copy the example file
            with open(".env.example", "r") as example_file:
                with open(".env", "w") as env_file:
                    env_file.write(example_file.read())
            
            print("✓ Created .env file from .env.example.")
            print("   Please edit .env file to add your credentials and settings.")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {str(e)}")
            return False
    else:
        print("❌ .env.example file not found. Cannot create .env file.")
        return False

def main():
    """Main function"""
    print_banner()
    
    # Perform checks
    python_ok = check_python_version()
    packages_ok = check_pip_packages()
    chromedriver_ok = check_chromedriver()
    selenium_ok = test_selenium()
    database_ok = initialize_database()
    
    # Create directories and config
    create_directories()
    env_ok = check_env_file()
    
    # Report results
    print("\n" + "=" * 80)
    print(" Setup Results ".center(80, "="))
    print("=" * 80)
    print(f"Python version check: {'✓' if python_ok else '❌'}")
    print(f"Required packages: {'✓' if packages_ok else '❌'}")
    print(f"ChromeDriver: {'✓' if chromedriver_ok else '❌'}")
    print(f"Selenium test: {'✓' if selenium_ok else '❌'}")
    print(f"Database: {'✓' if database_ok else '❌'}")
    print(f"Environment config: {'✓' if env_ok else '❌'}")
    print("=" * 80)
    
    # Overall result
    if all([python_ok, packages_ok, chromedriver_ok, selenium_ok, database_ok, env_ok]):
        print("\n✅ Setup completed successfully!")
        print("\nYou can now run the job scraper with:")
        print("  python job_scraper_cli.py --list-platforms")
        print("  python job_scraper_cli.py --all")
        print("  python job_scraper_cli.py --platform indeed")
    else:
        print("\n⚠️ Setup completed with some issues.")
        print("Please fix the errors above before running the job scraper.")
        print("Refer to INSTALLATION.md for detailed troubleshooting.")

if __name__ == "__main__":
    main()