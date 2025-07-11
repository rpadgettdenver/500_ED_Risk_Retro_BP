"""
Suggested File Name: comprehensive_energy_loader.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/data_processing/
Use: Load all energy data from Energize Denver Report with proper handling of multiple years

This script:
1. Uses 'Building ID' as the unique key
2. Loads ALL years of data to track energy trends
3. Identifies most recent reporting year for current status
4. Preserves all energy columns including Weather Normalized data
5. Includes GHG emissions data
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

def examine_excel_structure(excel_path):
    """First, let's understand the Excel file structure"""
    
    print("📊 Examining Excel file structure...")
    
    # Load a sample to understand columns
    df_sample = pd.read_excel(excel_path, nrows=100)
    
    print(f"\n📋 File contains {len(df_sample.columns)} columns")
    
    # Identify key columns
    key_columns = {
        'id': None,
        'year': None,
        'name': None,
        'address': None,
        'type': None,
        'sqft': None,
        'energy_columns': [],
        'ghg_columns': []
    }
    
    print("\n🔍 Identifying key columns:")
    
    for col in df_sample.columns:
        col_lower = col.lower()
        
        # Building ID
        if 'building id' in col_lower:
            key_columns['id'] = col
            print(f"   Building ID: {col}")
        
        # Reporting Year
        elif 'reporting year' in col_lower:
            key_columns['year'] = col
            print(f"   Reporting Year: {col}")
        
        # Building Name
        elif 'building name' in col_lower or 'property name' in col_lower:
            key_columns['name'] = col
            print(f"   Building Name: {col}")
        
        # Address
        elif 'address' in col_lower:
            key_columns['address'] = col
            print(f"   Address: {col}")
        
        # Property Type
        elif 'property type' in col_lower:
            key_columns['type'] = col
            print(f"   Property Type: {col}")
        
        # Square Footage
        elif 'gross floor area' in col_lower or 'sqft' in col_lower:
            key_columns['sqft'] = col
            print(f"   Square Footage: {col}")
        
        # Energy columns
        elif any(term in col_lower for term in ['energy use', 'eui', 'weather normalized', 'electricity', 'natural gas']):
            key_columns['energy_columns'].append(col)
        
        # GHG columns
        elif 'ghg' in col_lower or 'emissions' in col_lower:
            key_columns['ghg_columns'].append(col)
    
    print(f"\n⚡ Found {len(key_columns['energy_columns'])} energy-related columns")
    print(f"🌍 Found {len(key_columns['ghg_columns'])} GHG-related columns")
    
    return key_columns, df_sample

def load_all_years_data(excel_path, key_columns):
    """Load all years of data to preserve historical trends"""
    
    print("\n📂 Loading complete dataset...")
    
    # Load full dataset
    df_all = pd.read_excel(excel_path)
    print(f"   Loaded {len(df_all)} total rows")
    
    # Check years available
    if key_columns['year']:
        years = df_all[key_columns['year']].unique()
        print(f"\n📅 Years available: {sorted(years)}")
        
        # Count buildings per year
        for year in sorted(years):
            year_data = df_all[df_all[key_columns['year']] == year]
            unique_buildings = year_data[key_columns['id']].nunique()
            print(f"   {year}: {len(year_data)} rows, {unique_buildings} unique buildings")
    
    # Check total unique buildings
    total_unique = df_all[key_columns['id']].nunique()
    print(f"\n🏢 Total unique buildings across all years: {total_unique}")
    
    return df_all

def create_comprehensive_dataset(df_all, key_columns):
    """Create dataset with all energy data and most recent status"""
    
    print("\n🔧 Creating comprehensive dataset...")
    
    # Ensure Building ID is string
    df_all['Building ID'] = df_all[key_columns['id']].astype(str)
    
    # Get most recent year
    most_recent_year = df_all[key_columns['year']].max()
    print(f"   Most recent reporting year: {most_recent_year}")
    
    # Check if most recent year has fewer buildings (partial year)
    year_counts = df_all.groupby(key_columns['year'])[key_columns['id']].nunique()
    avg_buildings = year_counts[:-1].mean()  # Average of all years except the last
    
    # Determine which year to use as base
    if year_counts.iloc[-1] < avg_buildings * 0.5:  # If last year has less than 50% of average
        print(f"   ⚠️  Warning: {most_recent_year} appears to be partial year data ({year_counts.iloc[-1]} buildings vs {avg_buildings:.0f} average)")
        # Use previous year instead
        base_year = sorted(df_all[key_columns['year']].unique())[-2]  # Second to last year
        print(f"   📊 Using {base_year} as base year for complete data analysis")
    else:
        base_year = most_recent_year
        print(f"   ✓ Using {base_year} as base year")
    
    # Create base dataset from selected year
    df_current = df_all[df_all[key_columns['year']] == base_year].copy()
    print(f"   Base year has {len(df_current)} buildings")
    
    # Essential columns to keep
    essential_cols = ['Building ID']
    
    # Add key identification columns
    if key_columns['name']:
        essential_cols.append(key_columns['name'])
    if key_columns['address']:
        essential_cols.append(key_columns['address'])
    if key_columns['type']:
        essential_cols.append(key_columns['type'])
    if key_columns['sqft']:
        essential_cols.append(key_columns['sqft'])
    
    # Add all energy columns
    print("\n⚡ Including energy columns:")
    for col in key_columns['energy_columns']:
        if col in df_current.columns:
            essential_cols.append(col)
            print(f"   ✓ {col}")
    
    # Add GHG columns
    print("\n🌍 Including GHG columns:")
    for col in key_columns['ghg_columns']:
        if col in df_current.columns:
            essential_cols.append(col)
            print(f"   ✓ {col}")
    
    # Create the comprehensive dataset
    df_comprehensive = df_current[essential_cols].copy()
    
    # Add reporting year
    df_comprehensive['Base_Year'] = base_year
    df_comprehensive['Most_Recent_Year'] = most_recent_year
    
    # Calculate energy trends if multiple years available
    if len(df_all[key_columns['year']].unique()) > 1:
        print("\n📈 Calculating energy trends...")
        
        # Find Weather Normalized Site EUI column
        eui_col = None
        for col in key_columns['energy_columns']:
            if 'weather normalized site eui' in col.lower():
                eui_col = col
                break
        
        if eui_col:
            # Calculate 3-year average EUI if available
            recent_years = sorted(df_all[key_columns['year']].unique())[-3:]
            df_recent = df_all[df_all[key_columns['year']].isin(recent_years)].copy()  # Use copy to avoid warning
            
            # Convert EUI column to numeric, handling any non-numeric values
            df_recent.loc[:, eui_col] = pd.to_numeric(df_recent[eui_col], errors='coerce')
            
            # Remove any rows with null EUI values before averaging
            df_recent_clean = df_recent[df_recent[eui_col].notna()]
            
            if len(df_recent_clean) > 0:
                avg_eui = df_recent_clean.groupby('Building ID')[eui_col].mean()
                df_comprehensive['Average_EUI_3yr'] = df_comprehensive['Building ID'].map(avg_eui)
                
                # Calculate trend (increasing/decreasing)
                first_year = min(recent_years)
                last_year = max(recent_years)
                
                # Get data for first and last years
                df_first = df_all[df_all[key_columns['year']] == first_year].copy()
                df_first.loc[:, eui_col] = pd.to_numeric(df_first[eui_col], errors='coerce')
                
                df_last = df_all[df_all[key_columns['year']] == last_year].copy()
                df_last.loc[:, eui_col] = pd.to_numeric(df_last[eui_col], errors='coerce')
                
                # Create a mapping of Building ID to EUI for each year
                first_year_eui = df_first.set_index('Building ID')[eui_col].to_dict()
                last_year_eui = df_last.set_index('Building ID')[eui_col].to_dict()
                
                # Calculate percentage change for buildings that exist in both years
                eui_changes = {}
                for building_id in df_comprehensive['Building ID']:
                    if (building_id in first_year_eui and 
                        building_id in last_year_eui and 
                        pd.notna(first_year_eui[building_id]) and 
                        pd.notna(last_year_eui[building_id]) and 
                        first_year_eui[building_id] != 0):
                        change = ((last_year_eui[building_id] - first_year_eui[building_id]) / 
                                 first_year_eui[building_id] * 100)
                        eui_changes[building_id] = change
                
                # Map the changes to the comprehensive dataframe
                df_comprehensive['EUI_Change_Pct'] = df_comprehensive['Building ID'].map(eui_changes).fillna(0)
                
                print(f"   ✓ Added 3-year average EUI")
                print(f"   ✓ Added EUI trend ({first_year} to {last_year})")
                print(f"   ✓ Calculated trends for {len(eui_changes)} buildings")
            else:
                print("   ⚠️  No valid EUI data for trend calculation")
    
    return df_comprehensive, df_all

def merge_with_other_sources(df_comprehensive, data_dir):
    """Merge with geocoding, EPB, and other data sources"""
    
    print("\n🔄 Merging with other data sources...")
    
    # 1. Geocoded data
    geocoded_path = os.path.join(data_dir, 'geocoded_buildings_final.csv')
    if os.path.exists(geocoded_path):
        df_geo = pd.read_csv(geocoded_path)
        
        # Check what columns are in the geocoded file
        print(f"\n   Geocoded columns: {df_geo.columns.tolist()[:5]}...")
        
        # Find the building ID column
        geo_id_col = None
        for col in df_geo.columns:
            if 'building' in col.lower() and 'id' in col.lower():
                geo_id_col = col
                break
        
        if geo_id_col:
            df_geo['building_id_clean'] = df_geo[geo_id_col].astype(str)
            
            # Check if lat/lon columns exist
            lat_col = next((col for col in df_geo.columns if 'lat' in col.lower()), None)
            lon_col = next((col for col in df_geo.columns if 'lon' in col.lower()), None)
            
            if lat_col and lon_col:
                merge_cols = ['building_id_clean', lat_col, lon_col]
                df_geo_subset = df_geo[merge_cols].copy()
                df_geo_subset.columns = ['building_id_clean', 'latitude', 'longitude']
                
                df_comprehensive = df_comprehensive.merge(
                    df_geo_subset,
                    left_on='Building ID',
                    right_on='building_id_clean',
                    how='left'
                )
                df_comprehensive.drop('building_id_clean', axis=1, inplace=True)
                print(f"   ✓ Added coordinates: {df_comprehensive['latitude'].notna().sum()} buildings geocoded")
            else:
                print(f"   ⚠️  Could not find latitude/longitude columns in geocoded data")
        else:
            print(f"   ⚠️  Could not find building ID column in geocoded data")
    
    # 2. EPB data
    epb_path = os.path.join(data_dir, 'CopyofWeeklyEPBStatsReport Report.csv')
    if os.path.exists(epb_path):
        df_epb = pd.read_csv(epb_path)
        df_epb['Building ID'] = df_epb['Building ID'].astype(str)
        df_epb['is_epb'] = df_epb['EPB Application Status'].isin(['Approved', 'Pending'])
        
        df_comprehensive = df_comprehensive.merge(
            df_epb[['Building ID', 'is_epb', 'EPB Application Status']],
            on='Building ID',
            how='left'
        )
        df_comprehensive['is_epb'] = df_comprehensive['is_epb'].fillna(False)
        print(f"   ✓ Added EPB status: {df_comprehensive['is_epb'].sum()} EPB buildings")
    
    # 3. Zip codes
    zip_path = os.path.join(data_dir, 'building_zipcode_lookup.csv')
    if os.path.exists(zip_path):
        df_zip = pd.read_csv(zip_path)
        
        # Find building ID column
        zip_id_col = None
        for col in df_zip.columns:
            if 'building' in col.lower() and 'id' in col.lower():
                zip_id_col = col
                break
        
        if zip_id_col:
            df_zip['building_id_clean'] = df_zip[zip_id_col].astype(str)
            zip_col = next((col for col in df_zip.columns if 'zip' in col.lower()), None)
            
            if zip_col:
                df_comprehensive = df_comprehensive.merge(
                    df_zip[['building_id_clean', zip_col]],
                    left_on='Building ID',
                    right_on='building_id_clean',
                    how='left'
                )
                df_comprehensive.drop('building_id_clean', axis=1, inplace=True)
                df_comprehensive.rename(columns={zip_col: 'zip_code'}, inplace=True)
                print(f"   ✓ Added zip codes")
        else:
            print(f"   ⚠️  Could not find building ID column in zip code data")
    
    return df_comprehensive

def save_comprehensive_data(df_comprehensive, df_all, output_dir):
    """Save the comprehensive datasets"""
    
    print(f"\n💾 Saving comprehensive energy data...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save base year comprehensive data
    base_year = int(df_comprehensive['Base_Year'].iloc[0])
    current_path = os.path.join(output_dir, f'energize_denver_{base_year}_comprehensive.csv')
    df_comprehensive.to_csv(current_path, index=False)
    print(f"   ✓ Saved {base_year} comprehensive data: {current_path}")
    
    # Also save a copy as the main comprehensive file
    main_path = os.path.join(output_dir, 'energize_denver_comprehensive.csv')
    df_comprehensive.to_csv(main_path, index=False)
    print(f"   ✓ Saved main comprehensive data: {main_path}")
    
    # Save all years data
    all_years_path = os.path.join(output_dir, 'energize_denver_all_years.csv')
    df_all.to_csv(all_years_path, index=False)
    print(f"   ✓ Saved historical data: {all_years_path}")
    
    # Save summary
    summary = {
        'data_generated': datetime.now().isoformat(),
        'total_unique_buildings': int(df_comprehensive['Building ID'].nunique()),
        'buildings_with_coordinates': int(df_comprehensive['latitude'].notna().sum()) if 'latitude' in df_comprehensive.columns else 0,
        'epb_buildings': int(df_comprehensive['is_epb'].sum()) if 'is_epb' in df_comprehensive.columns else 0,
        'base_year': int(df_comprehensive['Base_Year'].iloc[0]),
        'most_recent_year': int(df_comprehensive['Most_Recent_Year'].iloc[0]),
        'years_available': sorted([int(y) for y in df_all['Reporting Year'].unique()]),
        'energy_columns': [col for col in df_comprehensive.columns if any(term in col.lower() for term in ['energy', 'eui', 'normalized'])],
        'ghg_columns': [col for col in df_comprehensive.columns if 'ghg' in col.lower() or 'emissions' in col.lower()]
    }
    
    summary_path = os.path.join(output_dir, 'comprehensive_data_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"   ✓ Saved summary: {summary_path}")
    
    return current_path, all_years_path, summary_path

def main():
    """Main function to create comprehensive energy dataset"""
    
    # Paths
    excel_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/Energize Denver Report Request 060225.xlsx'
    data_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw'
    output_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed'
    
    print("🚀 Starting Comprehensive Energy Data Load\n")
    
    # Step 1: Examine Excel structure
    key_columns, df_sample = examine_excel_structure(excel_path)
    
    # Step 2: Load all years
    df_all = load_all_years_data(excel_path, key_columns)
    
    # Step 3: Create comprehensive dataset
    df_comprehensive, df_all_processed = create_comprehensive_dataset(df_all, key_columns)
    
    # Step 4: Merge with other sources
    df_comprehensive = merge_with_other_sources(df_comprehensive, data_dir)
    
    # Step 5: Save results
    current_path, all_path, summary_path = save_comprehensive_data(
        df_comprehensive, 
        df_all_processed,
        output_dir
    )
    
    print("\n✅ Comprehensive energy data load complete!")
    print(f"\n📊 Results:")
    print(f"   Buildings: {len(df_comprehensive)}")
    print(f"   Columns: {len(df_comprehensive.columns)}")
    print(f"\n📁 Output files:")
    print(f"   Current year: {current_path}")
    print(f"   All years: {all_path}")
    print(f"   Summary: {summary_path}")
    
    return df_comprehensive

if __name__ == "__main__":
    df = main()
