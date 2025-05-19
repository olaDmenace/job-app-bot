# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a job application automation bot that helps with job hunting in the web3/crypto space. The system has three main components:

1. **Job Scraping**: Automatically scrapes job postings from websites like web3.career
2. **Contact Finding**: Discovers potential contacts at companies with job openings
3. **Email Outreach**: Manages personalized email campaigns to hiring managers

## Core Commands

### Setup and Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate virtual environment (Linux/Mac)
source venv/bin/activate
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables in .env file
# Required variables:
# - YOUR_NAME
# - EMAIL_ADDRESS
# - EMAIL_PASSWORD
# - GITHUB_URL
# - LINKEDIN_URL
```

### Running Core Components

```bash
# Run job scraper
python web3_bot.py

# Run contact finder
python contact_finder.py

# Run tests
python test_email_system.py
python test_setup.py
```

## Database Structure

The application uses SQLite for data storage with the following main tables:

- `jobs`: Job listings scraped from sources
- `applications`: Tracks application status for jobs
- `companies`: Information about companies with jobs
- `outreach_contacts`: Potential hiring contacts at companies
- `email_templates`: Templates for different outreach scenarios
- `outreach_messages`: Tracks all sent emails and responses

The full schema is defined in `schema.sql`.

## Key Components

### database_manager.py

Database connector that handles all database operations including:
- Adding jobs, contacts, and companies
- Tracking application status
- Managing email templates and outreach

### email_manager.py

Handles all email-related functionality:
- Creating personalized emails from templates
- Sending emails with rate limiting
- Processing follow-ups
- Analyzing response content for success metrics

### web3_bot.py

Web scraper for job listings:
- Uses Selenium to scrape job boards
- Focuses on web3.career for frontend jobs
- Saves jobs to both database and CSV

### contact_finder.py

Automates finding potential contacts:
- Scrapes LinkedIn and WellFound for contacts
- Identifies hiring managers and technical leads
- Adds company and contact data to database

### config.py

Central configuration:
- Loads environment variables
- Stores personal information for job applications
- Contains email template definitions
- Defines success/failure metrics for responses

## Testing

The project has two main test files:

- `test_setup.py`: Verifies environment setup (Selenium, Chrome, database)
- `test_email_system.py`: Tests email functionality

To run tests:
```bash
python test_setup.py
python test_email_system.py
```