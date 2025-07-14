"""
Suggested File Name: verify_data_freshness.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Verify if the energize_denver_comprehensive_latest.csv is up to date with source Excel file

This script:
1. Compares modification dates of source Excel and processed CSV
2. Checks if data content matches between files
3. Reports any discrepancies
4. Provides option to regenerate if needed
"""

import pandas as pd
import os
from datetime import datetime
import json

def check_file_dates():
    """Compare modification dates of source and processed files"""
    
    excel_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/Energize Denver Report Request 060225.xlsx'
    csv_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed/energize_denver_comprehensive_latest.csv'
    
    print("📅 Checking file modification dates...\n")
    
    # Get modification times
    excel_mtime = os.path.getmtime(excel_path)
    csv_mtime = os.path.getmtime(csv_path)
    
    excel_date = datetime.fromtimestamp(excel_mtime)
    csv_date = datetime.fromtimestamp(csv_mtime)
    
    print(f"Source Excel file: {excel_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Processed CSV file: {csv_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if excel_mtime > csv_mtime:
        print("\n⚠️  WARNING: Excel file is newer than CSV file!")
        print("    The processed data may be out of date.")
        return False
    else:
        print("\n✅ CSV file is up to date (newer than or same as Excel file)")
        return True

def compare_data_content():
    """Compare actual data content between files"""
    
    excel_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/Energize Denver Report Request 060225.xlsx'
    csv_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed/energize_denver_comprehensive_latest.csv'
    
    print("\n📊 Comparing data content...\n")
    
    # Load Excel data
    print("Loading Excel file...")
    df_excel = pd.read_excel(excel_path)
    
    # Get unique buildings in Excel (post-2021)
    excel_post_2021 = df_excel[df_excel['Reporting Year'] > 2021]
    excel_buildings = set(excel_post_2021['Building ID'].astype(str).unique())
    
    # Load CSV data
    print("Loading CSV file...")
    df_csv = pd.read_csv(csv_path)
    csv_buildings = set(df_csv['Building ID'].astype(str).unique())
    
    # Compare counts
    print(f"\nExcel file (post-2021): {len(excel_buildings)} unique buildings")
    print(f"CSV file: {len(csv_buildings)} unique buildings")
    
    # Check for missing buildings
    missing_in_csv = excel_buildings - csv_buildings
    extra_in_csv = csv_buildings - excel_buildings
    
    if missing_in_csv:
        print(f"\n⚠️  Buildings in Excel but not in CSV: {len(missing_in_csv)}")
        if len(missing_in_csv) <= 10:
            print(f"   Missing IDs: {sorted(list(missing_in_csv))}")
    
    if extra_in_csv:
        print(f"\n📌 Buildings in CSV but not in Excel (post-2021): {len(extra_in_csv)}")
        print("   Note: This is expected if CSV includes pre-2021 buildings with recent data")
    
    # Check most recent data year
    excel_max_year = df_excel['Reporting Year'].max()
    if 'Most_Recent_Report_Year' in df_csv.columns:
        csv_max_year = df_csv['Most_Recent_Report_Year'].max()
    elif 'Reporting Year' in df_csv.columns:
        csv_max_year = df_csv['Reporting Year'].max()
    else:
        csv_max_year = None
    
    print(f"\nMost recent year in Excel: {excel_max_year}")
    print(f"Most recent year in CSV: {csv_max_year}")
    
    return len(missing_in_csv) == 0

def check_processing_summary():
    """Check the processing summary for additional details"""
    
    summary_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed/comprehensive_data_summary_latest.json'
    
    if os.path.exists(summary_path):
        print("\n📋 Checking processing summary...\n")
        
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        if 'data_generated' in summary:
            generated_date = datetime.fromisoformat(summary['data_generated'])
            print(f"Data generated: {generated_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if 'total_unique_buildings' in summary:
            print(f"Total buildings: {summary['total_unique_buildings']}")
        
        if 'buildings_with_coordinates' in summary:
            print(f"Buildings with coordinates: {summary['buildings_with_coordinates']}")
        
        if 'epb_buildings' in summary:
            print(f"EPB buildings: {summary['epb_buildings']}")
        
        if 'most_recent_years' in summary:
            print("\nBuildings by most recent report year:")
            for year, count in sorted(summary['most_recent_years'].items()):
                print(f"  {year}: {count} buildings")

def regenerate_data():
    """Option to regenerate the data"""
    
    print("\n🔄 Would you like to regenerate the comprehensive data? (y/n): ", end='')
    response = input().strip().lower()
    
    if response == 'y':
        print("\nRegenerating data...")
        print("Run: python src/data_processing/enhanced_comprehensive_loader.py")
        print("\nOr import and run:")
        print("from src.data_processing.enhanced_comprehensive_loader import main")
        print("df = main()")
    else:
        print("\n✅ Data verification complete.")

def main():
    """Main verification function"""
    
    print("=" * 60)
    print("🔍 ENERGIZE DENVER DATA FRESHNESS VERIFICATION")
    print("=" * 60)
    
    # Check file dates
    dates_ok = check_file_dates()
    
    # Compare content
    content_ok = compare_data_content()
    
    # Check summary
    check_processing_summary()
    
    # Overall status
    print("\n" + "=" * 60)
    if dates_ok and content_ok:
        print("✅ VERIFICATION PASSED: Data appears to be up to date")
    else:
        print("⚠️  VERIFICATION FAILED: Data may need to be regenerated")
        regenerate_data()
    print("=" * 60)

if __name__ == "__main__":
    main()
