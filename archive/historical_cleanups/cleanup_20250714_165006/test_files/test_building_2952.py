#!/usr/bin/env python3
"""
Test script to check Building 2952 data
"""

import pandas as pd
from pathlib import Path

# Load the targets CSV
csv_path = Path("/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/Building_EUI_Targets.csv")
df = pd.read_csv(csv_path)

# Find Building 2952
building_2952 = df[df['Building ID'] == 2952]

if not building_2952.empty:
    print("Building 2952 data:")
    print("-" * 50)
    row = building_2952.iloc[0]
    
    # Print all values
    for col in building_2952.columns:
        print(f"{col}: {row[col]}")
    
    print("\n" + "="*50 + "\n")
    
    # Compare with nearby buildings
    print("For comparison, nearby buildings:")
    print("-" * 50)
    
    for bid in [2951, 2953, 2954]:
        b = df[df['Building ID'] == bid]
        if not b.empty:
            r = b.iloc[0]
            print(f"\nBuilding {bid} ({r['Master Property Type']}):")
            print(f"  Baseline EUI: {r['Baseline EUI']}")
            print(f"  First Interim: {r['First Interim Target EUI']}")
            print(f"  Second Interim: {r['Second Interim Target EUI']}")
            print(f"  Final Target: {r['Adjusted Final Target EUI']}")
else:
    print("Building 2952 not found!")
