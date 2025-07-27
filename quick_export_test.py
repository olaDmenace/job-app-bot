#!/usr/bin/env python3
"""
Quick test to verify export works with correct schema
"""

try:
    from data_exporter import JobDataExporter
    
    print("Testing export with corrected schema...")
    
    exporter = JobDataExporter()
    
    # Test summary
    summary = exporter.get_export_summary()
    print(f"Total jobs: {summary['total_jobs']}")
    
    if summary['total_jobs'] > 0:
        # Test CSV export with small limit
        print("Testing CSV export...")
        csv_file = exporter.export_to_csv("test_schema_fix.csv", limit=3)
        print(f"CSV export result: {csv_file}")
        
        # Test getting recent data (last 1 day)
        print("Testing recent data query...")
        recent_jobs = exporter.get_jobs_data(limit=5, days_back=1)
        print(f"Recent jobs found: {len(recent_jobs)}")
        
        if recent_jobs:
            print("Sample job data:")
            sample = recent_jobs[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
    
    print("Export test complete!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()