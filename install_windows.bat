@echo off
echo Job Scraper Windows Installation
echo ================================

echo Step 1: Cleaning up old installations...
pip uninstall numpy pandas -y >NUL 2>&1

echo Step 2: Upgrading pip...
python -m pip install --upgrade pip

echo Step 3: Installing core dependencies...
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install beautifulsoup4==4.12.2
pip install lxml==4.9.3
pip install email-validator==2.0.0
pip install selenium==4.13.0
pip install webdriver-manager==4.0.0
pip install tqdm==4.65.0
pip install python-dateutil==2.8.2
pip install fake-useragent==1.2.1
pip install openpyxl==3.1.2

echo Step 4: Testing installation...
python -c "print('Testing imports...'); import requests; import json; import csv; from datetime import datetime; print('All imports successful!')"

echo Step 5: Testing API system...
python -c "from job_scrapers.api_usage_manager import APIUsageManager; print('API system working!')"

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Edit .env file with your API credentials
echo 2. Test with: python job_scraper_cli.py --quota-status
echo 3. Start scraping: python job_scraper_cli.py --list-sources
echo.
pause