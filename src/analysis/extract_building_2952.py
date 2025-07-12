"""
Extract Building 2952 data from comprehensive dataset
"""

import pandas as pd
import json

# Load the comprehensive data
df = pd.read_csv('/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed/energize_denver_comprehensive_latest.csv')

# Convert Building ID to string to ensure proper matching
df['Building ID'] = df['Building ID'].astype(str)

# Find Building 2952
building_2952 = df[df['Building ID'] == '2952']

if not building_2952.empty:
    print("Building 2952 found!")
    
    # Extract key data
    row = building_2952.iloc[0]
    
    building_data = {
        'building_id': '2952',
        'building_name': row['Building Name'],
        'property_type': row['Master Property Type'],
        'sqft': row['Master Sq Ft'],
        'site_eui': row['Site EUI'],
        'weather_norm_eui': row['Weather Normalized Site EUI'],
        'electricity_kwh': row['Electricity Use Grid Purchase (kWh)'],
        'gas_kbtu': row['Natural Gas Use (kBtu)'],
        'total_ghg': row['Total GHG Emissions (mtCO2e)'],
        'is_epb': row.get('is_epb', False),
        'baseline_year': row.get('Baseline Year', None),
        'baseline_eui': row.get('Baseline EUI', None),
        'first_interim_target': row.get('First Interim Target EUI', None),
        'second_interim_target': row.get('Second Interim Target EUI', None),
        'final_target': row.get('Adjusted Final Target EUI', None),
    }
    
    # Save to JSON
    with open('/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/analysis/building_2952_data.json', 'w') as f:
        json.dump(building_data, f, indent=2)
    
    print("\nBuilding 2952 Data:")
    for key, value in building_data.items():
        print(f"{key}: {value}")
        
else:
    print("Building 2952 not found in dataset")
    print(f"Total buildings: {len(df)}")
    print(f"Sample Building IDs: {df['Building ID'].head(20).tolist()}")
