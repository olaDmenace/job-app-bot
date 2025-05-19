#!/usr/bin/env python3
"""
Web3 Job Scraper - Main script for scraping web3.career

This script is maintained for backward compatibility.
For newer multi-platform functionality, use job_scraper_cli.py
"""

import sys
from job_scrapers.web3_career import Web3CareerScraper

def main():
    """Main entry point for web3.career scraper"""
    print("Starting Web3 career job search...")
    print("Note: For multi-platform support, consider using job_scraper_cli.py instead")
    
    # Parse command-line arguments
    remote_only = True
    max_pages = 5
    
    if len(sys.argv) > 1:
        if '--include-onsite' in sys.argv:
            remote_only = False
            print("Including onsite jobs")
            
        for i, arg in enumerate(sys.argv):
            if arg == '--pages' and i+1 < len(sys.argv):
                try:
                    max_pages = int(sys.argv[i+1])
                    print(f"Setting max pages to {max_pages}")
                except ValueError:
                    pass
    
    # Run the web3.career scraper
    scraper = Web3CareerScraper()
    jobs = scraper.run_job_search(remote_only=remote_only, max_pages=max_pages)
    
    print(f"\nFound {len(jobs)} jobs from web3.career")

if __name__ == "__main__":
    main()