# Installation Guide for Job Application Bot

This guide will walk you through the process of setting up and running the Job Application Bot on your machine.

## Prerequisites

1. **Python 3.8+**: Make sure you have Python 3.8 or newer installed.
   
   Check your Python version:
   ```bash
   python --version
   # or
   python3 --version
   ```

   If needed, download Python from [python.org](https://www.python.org/downloads/).

2. **Chrome Browser**: The bot uses Chrome for web automation.
   
   Download from [google.com/chrome](https://www.google.com/chrome/).

3. **ChromeDriver**: You need the ChromeDriver that matches your Chrome browser version.
   
   Determine your Chrome version:
   ```bash
   # On Windows:
   reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version
   
   # On macOS:
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
   
   # On Linux:
   google-chrome --version
   ```

   Download the matching ChromeDriver from [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads).

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/job-app-bot.git
cd job-app-bot
```

## Step 2: Set Up Virtual Environment

Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` appear at the beginning of your command prompt, indicating the virtual environment is active.

## Step 3: Install Required Packages

Install all dependencies:

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- Selenium for web automation
- Pandas for data handling
- Python-dotenv for environment variables
- BeautifulSoup4 for HTML parsing
- And other utilities

## Step 4: Set Up ChromeDriver

1. Create a `drivers` directory in your project folder:
   
   ```bash
   mkdir -p drivers
   ```

2. Place the downloaded ChromeDriver executable in the `drivers` directory.

3. Make the ChromeDriver executable:
   
   ```bash
   # On macOS/Linux:
   chmod +x drivers/chromedriver
   ```

## Step 5: Configure Environment Variables

Create a `.env` file with your credentials and settings:

```bash
cp .env.example .env
```

Edit the `.env` file to add your personal information:
- Email and password for job platforms
- Personal details for applications
- Email configuration for outreach

## Step 6: Set Up the Database

Initialize the SQLite database:

```bash
python -c "from database_manager import JobApplicationDB; JobApplicationDB()"
```

This creates a new SQLite database file using the schema defined in `schema.sql`.

## Step 7: Test the Installation

Run the test setup script to ensure everything is working correctly:

```bash
python test_setup.py
```

This will check:
- Python environment
- Selenium installation
- ChromeDriver accessibility
- Database connection

## Running the Job Scraper

Now you're ready to run the job scraper:

### List Available Job Platforms

```bash
python job_scraper_cli.py --list-platforms
```

### Run All Job Scrapers

```bash
python job_scraper_cli.py --all
```

### Run Specific Job Platform

```bash
python job_scraper_cli.py --platform indeed
```

### Run With Custom Parameters

```bash
python job_scraper_cli.py --platform linkedin --pages 10 --include-onsite
```

## Troubleshooting

### ChromeDriver Issues

If you encounter ChromeDriver errors:

1. **Version mismatch**: Make sure the ChromeDriver version matches your Chrome browser version.
   
2. **Path issues**: Update the path in `base_scraper.py` if needed:
   
   ```python
   driver_path = os.path.join(os.getcwd(), "drivers", "chromedriver")
   ```
   
   If using Windows, change to:
   ```python
   driver_path = os.path.join(os.getcwd(), "drivers", "chromedriver.exe")
   ```

3. **Permission issues** (Linux/Mac):
   
   ```bash
   chmod +x drivers/chromedriver
   ```

### Login Problems

If platforms requiring login fail:

1. Double-check your credentials in the `.env` file.
2. Some platforms may have additional security measures like CAPTCHA or 2FA that might interfere with automation.
3. Try logging in manually first, then run the scraper.

## Additional Resources

- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [ChromeDriver Documentation](https://chromedriver.chromium.org/getting-started)
- [Python Virtual Environments Guide](https://docs.python.org/3/tutorial/venv.html)