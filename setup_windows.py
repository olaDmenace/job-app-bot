#!/usr/bin/env python3
"""
Windows-compatible setup script for the job scraper system.
This script helps set up the environment and dependencies.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"ERROR: Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_virtual_env():
    """Check if running in virtual environment"""
    print("Checking virtual environment...")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("[OK] Running in virtual environment")
        return True
    else:
        print("WARNING: Not running in virtual environment")
        print("Consider creating one with: python -m venv venv")
        print("Then activate with: venv\\Scripts\\activate")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        # Try to upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install compatible versions
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                              "numpy==1.24.3", 
                              "pandas==2.0.3",
                              "--no-cache-dir"])
        
        # Install other requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[OK] Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False

def check_imports():
    """Test importing key modules"""
    print("Testing module imports...")
    modules_to_test = [
        'pandas',
        'numpy', 
        'requests',
        'json',
        'datetime',
        'os'
    ]
    
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"[OK] {module}")
        except ImportError as e:
            print(f"ERROR: Cannot import {module}: {e}")
            return False
    
    return True

def create_env_template():
    """Create .env template file"""
    print("Creating .env template...")
    env_template = """# API Credentials for job scraping
# Get Adzuna credentials from: https://developer.adzuna.com/
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here

# Get RapidAPI key from: https://rapidapi.com/
# Subscribe to JSearch API for LinkedIn/Glassdoor access
RAPIDAPI_KEY=your_rapidapi_key_here

# Web scraper credentials (fallback)
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
DICE_EMAIL=your_dice_email
DICE_PASSWORD=your_dice_password
MONSTER_EMAIL=your_monster_email
MONSTER_PASSWORD=your_monster_password
GLASSDOOR_EMAIL=your_glassdoor_email
GLASSDOOR_PASSWORD=your_glassdoor_password

# Your personal information for job applications
YOUR_NAME=Your Full Name
EMAIL_ADDRESS=your.email@example.com
EMAIL_PASSWORD=your_email_password
GITHUB_URL=https://github.com/yourusername
LINKEDIN_URL=https://linkedin.com/in/yourusername
"""
    
    env_file = Path('.env')
    if not env_file.exists():
        with open('.env', 'w') as f:
            f.write(env_template)
        print("[OK] Created .env template - please edit with your credentials")
    else:
        print("[INFO] .env file already exists")
    
    return True

def test_api_system():
    """Test the API system components"""
    print("Testing API system components...")
    try:
        # Test APIUsageManager
        from job_scrapers.api_usage_manager import APIUsageManager
        usage_manager = APIUsageManager("test_usage.json")
        
        # Test basic functionality
        can_use_jsearch = usage_manager.can_use_api('jsearch', 1)
        can_use_adzuna = usage_manager.can_use_api('adzuna', 1)
        
        print(f"[OK] JSearch API available: {can_use_jsearch}")
        print(f"[OK] Adzuna API available: {can_use_adzuna}")
        
        # Test query classification
        priority = usage_manager.classify_query_priority("senior developer")
        print(f"[OK] Query classification working: senior developer -> {priority}")
        
        # Cleanup test file
        if os.path.exists("test_usage.json"):
            os.remove("test_usage.json")
        
        print("[OK] API system components working")
        return True
    except Exception as e:
        print(f"ERROR: API system test failed: {e}")
        return False

def test_cli():
    """Test CLI functionality"""
    print("Testing CLI functionality...")
    try:
        import argparse
        from job_scrapers.scraper_factory import JobScraperFactory
        
        # Test scraper factory
        scrapers = JobScraperFactory.get_available_scrapers()
        api_scrapers = [k for k, v in scrapers.items() if v.get('type') == 'api']
        web_scrapers = [k for k, v in scrapers.items() if v.get('type') == 'web']
        
        print(f"[OK] Found {len(api_scrapers)} API scrapers: {', '.join(api_scrapers)}")
        print(f"[OK] Found {len(web_scrapers)} web scrapers: {', '.join(web_scrapers)}")
        
        print("[OK] CLI components working")
        return True
    except Exception as e:
        print(f"ERROR: CLI test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("Job Scraper Windows Setup")
    print("=" * 40)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Check virtual environment
    check_virtual_env()  # Warning only
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Test imports
    if not check_imports():
        success = False
    
    # Create .env template
    if not create_env_template():
        success = False
    
    # Test API system
    if not test_api_system():
        success = False
    
    # Test CLI
    if not test_cli():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("SETUP COMPLETE!")
        print("\nNext steps:")
        print("1. Edit .env file with your API credentials")
        print("2. Test quota status: python job_scraper_cli.py --quota-status")
        print("3. List available sources: python job_scraper_cli.py --list-sources")
        print("4. Start scraping: python job_scraper_cli.py --apis-only --query \"react developer\"")
    else:
        print("SETUP FAILED!")
        print("Please fix the errors above and run setup again.")
    
    return success

if __name__ == "__main__":
    main()