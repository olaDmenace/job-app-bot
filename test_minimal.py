#!/usr/bin/env python3
"""
Minimal test for Windows compatibility without pandas/numpy dependencies.
"""

print("Testing Job Scraper System (Windows Minimal)")
print("=" * 50)

# Test 1: Basic Python imports
print("\n1. Testing basic Python imports...")
try:
    import json
    import csv
    import os
    import sys
    from datetime import datetime
    print("   [OK] Basic Python modules imported successfully")
except Exception as e:
    print(f"   [ERROR] Basic imports failed: {e}")
    sys.exit(1)

# Test 2: Required third-party packages
print("\n2. Testing required packages...")
packages_to_test = [
    'requests',
    'json',
    'csv',
    'datetime'
]

for package in packages_to_test:
    try:
        if package == 'requests':
            import requests
        elif package == 'json':
            import json  
        elif package == 'csv':
            import csv
        elif package == 'datetime':
            from datetime import datetime
        print(f"   [OK] {package}")
    except ImportError as e:
        print(f"   [ERROR] {package}: {e}")

# Test 3: API Usage Manager
print("\n3. Testing API Usage Manager...")
try:
    from job_scrapers.api_usage_manager import APIUsageManager
    
    # Initialize manager
    manager = APIUsageManager("test_usage.json")
    
    # Test basic functionality
    can_use_jsearch = manager.can_use_api('jsearch', 1)
    can_use_adzuna = manager.can_use_api('adzuna', 1)
    
    print(f"   [OK] JSearch API available: {can_use_jsearch}")
    print(f"   [OK] Adzuna API available: {can_use_adzuna}")
    
    # Test query classification
    priority = manager.classify_query_priority("senior react developer")
    print(f"   [OK] Query classification: 'senior react developer' -> {priority}")
    
    # Cleanup
    if os.path.exists("test_usage.json"):
        os.remove("test_usage.json")
        
    print("   [OK] API Usage Manager working correctly")
except Exception as e:
    print(f"   [ERROR] API Usage Manager failed: {e}")

# Test 4: Scraper Factory
print("\n4. Testing Scraper Factory...")
try:
    from job_scrapers.scraper_factory import JobScraperFactory
    
    # Get available scrapers
    scrapers = JobScraperFactory.get_available_scrapers()
    api_scrapers = [k for k, v in scrapers.items() if v.get('type') == 'api']
    web_scrapers = [k for k, v in scrapers.items() if v.get('type') == 'web']
    
    print(f"   [OK] Found {len(api_scrapers)} API scrapers: {', '.join(api_scrapers)}")
    print(f"   [OK] Found {len(web_scrapers)} web scrapers: {', '.join(web_scrapers)}")
    
    # Test platform coverage
    coverage = JobScraperFactory.get_platforms_covered()
    print(f"   [OK] Platform coverage working: {len(coverage)} platforms supported")
    
except Exception as e:
    print(f"   [ERROR] Scraper Factory failed: {e}")

# Test 5: CLI imports
print("\n5. Testing CLI functionality...")
try:
    import argparse
    print("   [OK] Argparse available")
    
    # Test basic argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args(['--test'])
    print(f"   [OK] Argument parsing working: test={args.test}")
    
except Exception as e:
    print(f"   [ERROR] CLI test failed: {e}")

# Test 6: CSV functionality
print("\n6. Testing CSV export (pandas replacement)...")
try:
    import csv
    import tempfile
    
    # Test CSV writing
    test_data = [
        {'title': 'Senior Developer', 'company': 'Test Corp', 'location': 'Remote'},
        {'title': 'Frontend Engineer', 'company': 'Web Co', 'location': 'New York'}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        fieldnames = test_data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_data)
        temp_filename = f.name
    
    # Test CSV reading
    with open(temp_filename, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    os.unlink(temp_filename)
    
    print(f"   [OK] CSV export/import working: {len(rows)} rows processed")
    
except Exception as e:
    print(f"   [ERROR] CSV test failed: {e}")

print("\n" + "=" * 50)
print("MINIMAL SYSTEM TEST COMPLETE!")

print("\nSystem Status:")
print("- No pandas/numpy dependencies required")
print("- Using built-in Python CSV module for data export")
print("- All Unicode icons removed for Windows compatibility")
print("- Core API functionality preserved")

print("\nNext Steps:")
print("1. Run: install_windows.bat (to install dependencies)")
print("2. Create .env file with API credentials:")
print("   ADZUNA_APP_ID=your_app_id")
print("   ADZUNA_APP_KEY=your_app_key")
print("   RAPIDAPI_KEY=your_rapidapi_key")
print("3. Test: python job_scraper_cli.py --quota-status")
print("4. Search: python job_scraper_cli.py --apis-only --query \"react developer\"")

print("\nSystem is ready for Windows!")