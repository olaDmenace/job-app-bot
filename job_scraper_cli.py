#!/usr/bin/env python3
import argparse
import json
import os
from dotenv import load_dotenv
from job_scrapers.scraper_coordinator import JobScraperCoordinator
from job_scrapers.scraper_factory import JobScraperFactory

def main():
    """Main CLI entry point for job scraper"""
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Job Application Bot - Job Scraper')
    
    # Platform selection arguments
    platform_group = parser.add_argument_group('Platform Selection')
    platform_group.add_argument('--all', action='store_true', 
                             help='Run all available scrapers')
    platform_group.add_argument('--platform', type=str, 
                             help='Specific platform to scrape (e.g., "indeed", "linkedin")')
    platform_group.add_argument('--list-platforms', action='store_true',
                             help='List available job platforms')
    platform_group.add_argument('--skip-login', action='store_true',
                             help='Skip platforms that require login')
    
    # Job search parameters
    search_group = parser.add_argument_group('Search Parameters')
    search_group.add_argument('--pages', type=int, default=5,
                           help='Maximum number of pages to scrape (default: 5)')
    search_group.add_argument('--include-onsite', action='store_true',
                           help='Include onsite jobs (default: remote only)')
    search_group.add_argument('--config', type=str,
                           help='Path to configuration file')
    
    # Debug options
    debug_group = parser.add_argument_group('Debug Options')
    debug_group.add_argument('--debug', action='store_true',
                          help='Enable debug output')
    
    args = parser.parse_args()
    
    # List available platforms if requested
    if args.list_platforms:
        available_scrapers = JobScraperFactory.get_available_scrapers()
        print("\nAvailable job platforms:")
        for name, info in available_scrapers.items():
            login_status = "Requires login" if info['requires_login'] else "No login required"
            print(f"  - {name} ({login_status})")
        return
    
    # Create the scraper coordinator
    coordinator = JobScraperCoordinator(config_file=args.config)
    
    # Set search parameters
    remote_only = not args.include_onsite
    max_pages = args.pages
    
    # Run the appropriate scraper(s)
    if args.platform:
        # Run specific platform
        try:
            jobs = coordinator.run_scraper(
                args.platform, 
                max_pages=max_pages, 
                remote_only=remote_only
            )
            print(f"\nFound {len(jobs)} jobs from {args.platform}")
        except ValueError as e:
            print(f"Error: {str(e)}")
            print("Use --list-platforms to see available platforms")
    else:
        # Run all platforms
        coordinator.run_available_scrapers(
            max_pages=max_pages,
            remote_only=remote_only,
            skip_login_required=args.skip_login
        )

if __name__ == "__main__":
    main()