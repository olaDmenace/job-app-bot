#!/usr/bin/env python3
"""
Quick test for export functionality
"""

print("Testing Export System...")
print("=" * 40)

try:
    from data_exporter import JobDataExporter
    
    # Initialize exporter
    exporter = JobDataExporter()
    
    # Test database connection and summary
    print("1. Testing database connection and summary...")
    summary = exporter.get_export_summary()
    print(f"   Total jobs in database: {summary['total_jobs']}")
    
    if summary['total_jobs'] > 0:
        print("   Jobs by source:")
        for source, count in summary['jobs_by_source'].items():
            print(f"     {source}: {count} jobs")
        
        print("\n2. Testing CSV export...")
        try:
            csv_file = exporter.export_to_csv("test_export.csv", limit=5)
            if csv_file:
                print(f"   CSV export successful: {csv_file}")
            else:
                print("   CSV export failed")
        except Exception as e:
            print(f"   CSV export error: {e}")
        
        print("\n3. Testing Excel export...")
        try:
            excel_file = exporter.export_to_excel("test_export.xlsx", limit=5)
            if excel_file:
                print(f"   Excel export successful: {excel_file}")
            else:
                print("   Excel export failed (openpyxl may not be installed)")
        except Exception as e:
            print(f"   Excel export error: {e}")
            print("   Install openpyxl with: pip install openpyxl")
    
    else:
        print("   No jobs in database yet. Run a search first:")
        print("   python job_scraper_cli.py --apis-only --query \"react developer\"")
    
    print("\nExport system test complete!")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed")
except Exception as e:
    print(f"Test error: {e}")

print("\nAvailable export commands:")
print("- Export current data to CSV: python job_scraper_cli.py --export-only --export-csv")
print("- Export current data to Excel: python job_scraper_cli.py --export-only --export-excel") 
print("- Search and export: python job_scraper_cli.py --apis-only --query \"react developer\" --export-csv")
print("- Standalone exporter: python data_exporter.py --csv")