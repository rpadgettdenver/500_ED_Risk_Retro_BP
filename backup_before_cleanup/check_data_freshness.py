"""
Quick verification of data freshness
"""

import os
from datetime import datetime
import pandas as pd
import json

# File paths
excel_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/Energize Denver Report Request 060225.xlsx'
csv_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed/energize_denver_comprehensive_latest.csv'
summary_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed/comprehensive_data_summary_latest.json'

print("=" * 60)
print("DATA FRESHNESS CHECK")
print("=" * 60)

# 1. Check modification dates
excel_mtime = os.path.getmtime(excel_path)
csv_mtime = os.path.getmtime(csv_path)

excel_date = datetime.fromtimestamp(excel_mtime)
csv_date = datetime.fromtimestamp(csv_mtime)

print("\nFile Modification Dates:")
print(f"Excel source: {excel_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"CSV output:   {csv_date.strftime('%Y-%m-%d %H:%M:%S')}")

if excel_mtime > csv_mtime:
    print("\nSTATUS: ⚠️  Excel is NEWER - CSV needs regeneration!")
else:
    print("\nSTATUS: ✅ CSV is up to date")

# 2. Check summary file
if os.path.exists(summary_path):
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    if 'data_generated' in summary:
        gen_date = summary['data_generated'][:19]  # Just date/time part
        print(f"\nProcessing timestamp: {gen_date}")
    
    if 'total_unique_buildings' in summary:
        print(f"Total buildings in CSV: {summary['total_unique_buildings']}")

# 3. Quick data check
print("\nQuick data verification:")
df_csv = pd.read_csv(csv_path, nrows=5)
print(f"CSV columns: {len(df_csv.columns)}")
print(f"Sample Building IDs: {df_csv['Building ID'].tolist()}")

print("\n" + "=" * 60)
