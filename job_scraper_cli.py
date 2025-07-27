#!/usr/bin/env python3
import argparse
import json
import os
from dotenv import load_dotenv
from job_scrapers.scraper_coordinator import JobScraperCoordinator
from job_scrapers.scraper_factory import JobScraperFactory
from job_scrapers.api_usage_manager import APIUsageManager
from data_exporter import JobDataExporter

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
    platform_group.add_argument('--platforms', type=str, 
                             help='Comma-separated list of platforms to scrape')
    platform_group.add_argument('--list-platforms', action='store_true',
                             help='List available job platforms')
    platform_group.add_argument('--list-sources', action='store_true',
                             help='List all available sources (APIs and web scrapers)')
    platform_group.add_argument('--skip-login', action='store_true',
                             help='Skip platforms that require login')
    
    # API-specific arguments
    api_group = parser.add_argument_group('API Options')
    api_group.add_argument('--apis-only', action='store_true',
                          help='Use only API scrapers, skip web scrapers')
    api_group.add_argument('--api-first', action='store_true', default=True,
                          help='Try APIs first, fallback to web scrapers (default: True)')
    api_group.add_argument('--web-only', action='store_true',
                          help='Use only web scrapers, skip APIs')
    api_group.add_argument('--quota-status', action='store_true',
                          help='Show API quota status and exit')
    api_group.add_argument('--show-quotas', action='store_true',
                          help='Show quota usage during execution')
    api_group.add_argument('--max-api-calls', type=int,
                          help='Maximum API calls to make (for quota management)')
    api_group.add_argument('--smart-usage', action='store_true', default=True,
                          help='Use smart API usage optimization (default: True)')
    
    # Job search parameters
    search_group = parser.add_argument_group('Search Parameters')
    search_group.add_argument('--query', type=str, default='frontend developer',
                           help='Job search query (default: "frontend developer")')
    search_group.add_argument('--location', type=str, default='',
                           help='Location filter (leave empty for remote)')
    search_group.add_argument('--pages', type=int, default=5,
                           help='Maximum number of pages to scrape (default: 5)')
    search_group.add_argument('--max-results', type=int, default=50,
                           help='Maximum results per platform (default: 50)')
    search_group.add_argument('--include-onsite', action='store_true',
                           help='Include onsite jobs (default: remote only)')
    search_group.add_argument('--config', type=str,
                           help='Path to configuration file')
    
    # Export options
    export_group = parser.add_argument_group('Export Options')
    export_group.add_argument('--export-csv', action='store_true',
                           help='Export results to CSV after search')
    export_group.add_argument('--export-excel', action='store_true',
                           help='Export results to Excel after search')
    export_group.add_argument('--export-filename', type=str,
                           help='Custom filename for export')
    export_group.add_argument('--export-only', action='store_true',
                           help='Only export existing data, do not run new search')
    
    # Debug options
    debug_group = parser.add_argument_group('Debug Options')
    debug_group.add_argument('--debug', action='store_true',
                          help='Enable debug output')
    
    args = parser.parse_args()
    
    # Handle information requests
    if args.quota_status:
        usage_manager = APIUsageManager()
        usage_manager.print_quota_status()
        return
    
    # Handle export-only requests
    if args.export_only:
        exporter = JobDataExporter()
        exporter.print_export_summary()
        
        if args.export_csv:
            filename = exporter.export_to_csv(args.export_filename)
            if filename:
                print(f"CSV export complete: {filename}")
        
        if args.export_excel:
            filename = exporter.export_to_excel(args.export_filename)
            if filename:
                print(f"Excel export complete: {filename}")
        
        if not args.export_csv and not args.export_excel:
            print("\nTo export data, use --export-csv or --export-excel")
        
        return
    
    if args.list_sources or args.list_platforms:
        available_scrapers = JobScraperFactory.get_available_scrapers()
        print("\nAvailable Job Sources:")
        print("=" * 60)
        
        # Group by type
        api_scrapers = {k: v for k, v in available_scrapers.items() if v.get('type') == 'api'}
        web_scrapers = {k: v for k, v in available_scrapers.items() if v.get('type') == 'web'}
        
        if api_scrapers:
            print("\nAPI Scrapers (Recommended):")
            for name, info in api_scrapers.items():
                quota_info = f"({info['quota_limit']} calls/month)" if info['quota_limit'] else "(unlimited)"
                platforms = ", ".join(info.get('platforms_covered', [name]))
                creds_needed = "[CREDS REQUIRED]" if info.get('requires_credentials') else "[NO CREDS NEEDED]"
                print(f"  [API] {name.upper()} {quota_info} - covers: {platforms}")
                print(f"     {info.get('description', '')} - {creds_needed}")
        
        if web_scrapers:
            print("\nWeb Scrapers (Fallback):")
            for name, info in web_scrapers.items():
                login_status = "[LOGIN REQUIRED]" if info.get('requires_login') else "[NO LOGIN REQUIRED]"
                print(f"  [WEB] {name.upper()} - {info.get('description', '')} - {login_status}")
        
        # Show platform coverage
        coverage = JobScraperFactory.get_platforms_covered()
        print("\nPlatform Coverage:")
        for platform, scrapers in sorted(coverage.items()):
            scraper_list = []
            for s in scrapers:
                icon = "[API]" if s['type'] == 'api' else "[WEB]"
                scraper_list.append(f"{icon}{s['scraper']}")
            print(f"  {platform}: {', '.join(scraper_list)}")
        return
    
    # Create the scraper coordinator
    coordinator = JobScraperCoordinator(config_file=args.config)
    
    # Show initial quota status if requested
    if args.show_quotas:
        usage_manager = APIUsageManager()
        usage_manager.print_quota_status()
        print()
    
    # Set search parameters
    remote_only = not args.include_onsite
    max_pages = args.pages
    query = args.query
    location = args.location
    max_results = args.max_results
    
    # Determine execution mode
    api_first = args.api_first and not args.web_only
    apis_only = args.apis_only
    
    if apis_only:
        api_first = True
        print("Running in API-only mode")
    elif args.web_only:
        api_first = False
        print("Running in web-only mode")
    elif api_first:
        print("Running in API-first mode with web scraper fallback")
    
    # Prepare platform list
    platforms_to_search = []
    if args.platform:
        platforms_to_search = [args.platform]
    elif args.platforms:
        platforms_to_search = [p.strip() for p in args.platforms.split(',')]
    else:
        # Default platform list
        platforms_to_search = ['indeed', 'linkedin', 'glassdoor', 'monster', 'dice']
    
    print(f"Searching for: '{query}' {f'in {location}' if location else '(remote)'}")
    print(f"Platforms: {', '.join(platforms_to_search)}")
    
    try:
        if apis_only:
            # API-only search
            results = coordinator.run_api_search(
                query=query,
                platforms=platforms_to_search,
                max_results=max_results,
                remote_only=remote_only,
                location=location
            )
        elif api_first:
            # Smart fallback search
            results = coordinator.run_with_smart_fallback(
                query=query,
                platforms=platforms_to_search,
                api_first=True,
                max_results=max_results,
                remote_only=remote_only,
                location=location,
                max_pages=max_pages
            )
        else:
            # Traditional web scraper approach
            results = {}
            for platform in platforms_to_search:
                jobs = coordinator.run_scraper(
                    platform,
                    max_pages=max_pages,
                    remote_only=remote_only,
                    query=query
                )
                results[platform] = jobs
        
        # Print summary
        total_jobs = sum(len(jobs) for jobs in results.values())
        print(f"\nSearch Complete! Total jobs found: {total_jobs}")
        print("\nResults by platform:")
        for platform, jobs in results.items():
            print(f"  {platform}: {len(jobs)} jobs")
        
        # Show final quota status if requested
        if args.show_quotas:
            print()
            usage_manager = APIUsageManager()
            usage_manager.print_quota_status()
        
        # Handle post-search exports
        if args.export_csv or args.export_excel:
            print("\nExporting search results...")
            exporter = JobDataExporter()
            
            # Export recent results (last 1 day to get current search)
            export_params = {'days_back': 1}
            
            if args.export_csv:
                filename = exporter.export_to_csv(args.export_filename, **export_params)
                if filename:
                    print(f"CSV export complete: {filename}")
            
            if args.export_excel:
                filename = exporter.export_to_excel(args.export_filename, **export_params)
                if filename:
                    print(f"Excel export complete: {filename}")
            
    except Exception as e:
        print(f"ERROR: Error during job search: {e}")
        print("Use --list-sources to see available platforms")

if __name__ == "__main__":
    main()