#!/usr/bin/env python3
"""
Quick test to verify the typing issue is fixed
"""

print("Testing import fix...")

try:
    from job_scrapers.scraper_factory import JobScraperFactory
    print("✓ JobScraperFactory imported successfully")
    
    scrapers = JobScraperFactory.get_available_scrapers()
    print(f"✓ Found {len(scrapers)} scrapers")
    
    coverage = JobScraperFactory.get_platforms_covered()
    print(f"✓ Platform coverage working: {len(coverage)} platforms")
    
    print("\nImport fix successful! You can now run:")
    print("python job_scraper_cli.py --apis-only --query \"react developer\"")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()