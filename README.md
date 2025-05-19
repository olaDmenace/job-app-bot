# Job Application Bot

An automated job application system for streamlining your job search across multiple platforms.

## Features

- **Multi-Platform Job Scraping**: Search jobs across Indeed, LinkedIn, Web3.career, and more
- **Contact Finding**: Discover potential contacts at companies with job openings
- **Email Outreach**: Manage personalized email campaigns to hiring managers
- **Application Tracking**: Track status of all your job applications

## Supported Job Platforms

The system currently supports or is planned to support the following job platforms:

- [x] Web3.career (no login required)
- [x] Indeed (no login required)
- [x] LinkedIn (login required)
- [ ] Dice (login required)
- [ ] Monster (login required)
- [ ] Glassdoor (login required)
- [ ] Adzuna (no login required)
- [ ] Jobsite (no login required)
- [ ] CVLibrary (no login required)

## Setup

### Prerequisites

- Python 3.8+
- Chrome browser
- ChromeDriver matching your Chrome version

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/job-app-bot.git
   cd job-app-bot
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
   - Windows:
     ```bash
     venv\Scripts\activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file with your personal information and credentials.

6. Set up the database:
   ```bash
   python setup.py
   ```

## Usage

### Job Scraping

Use the job scraper command-line interface:

```bash
# List available job platforms
python job_scraper_cli.py --list-platforms

# Run all job scrapers (skipping those requiring login if credentials aren't provided)
python job_scraper_cli.py --all

# Run a specific job platform
python job_scraper_cli.py --platform indeed

# Run with custom parameters
python job_scraper_cli.py --platform linkedin --pages 10 --include-onsite
```

### Contact Finding

Find contacts at companies with job openings:

```bash
python contact_finder.py
```

### Email Outreach

Send personalized emails to potential contacts:

```bash
python email_manager.py
```

## Adding New Job Platforms

To add a new job platform:

1. Create a new scraper class by copying `job_scrapers/scraper_template.py` to a new file named after your platform (e.g., `job_scrapers/glassdoor.py`).
2. Implement the required methods for the platform.
3. Update the configuration in `config/job_scrapers.json` to include your new platform.

## Database Structure

The application uses SQLite for data storage with the following main tables:

- `jobs`: Job listings scraped from sources
- `applications`: Tracks application status for jobs
- `companies`: Information about companies with jobs
- `outreach_contacts`: Potential hiring contacts at companies
- `email_templates`: Templates for different outreach scenarios
- `outreach_messages`: Tracks all sent emails and responses

See `schema.sql` for the full database schema.

## Testing

Run the tests to verify the system is working correctly:

```bash
python test_setup.py
python test_email_system.py
```

## License

[MIT License](LICENSE)