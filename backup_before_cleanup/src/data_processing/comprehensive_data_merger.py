"""
Suggested File Name: comprehensive_data_merger.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/data_processing/
Use: Merge all raw data sources to create comprehensive building dataset for DER analysis

This script:
1. Uses Energize Denver Report as the base (source of truth)
2. Joins geocoded data for lat/lon
3. Joins EPB status data
4. Joins zip codes
5. Joins EUI targets
6. Creates a master dataset with all building information
"""

import pandas as pd
import numpy as np
import os
import json

def load_and_examine_data(data_dir):
    """Load all raw data files and examine their structure"""
    
    print("📂 Loading raw data files...")
    
    # 1. Load main Energize Denver report (Excel)
    excel_path = os.path.join(data_dir, 'Energize Denver Report Request 060225.xlsx')
    print(f"\n1️⃣ Loading main Energize Denver report...")
    
    # First check what sheets are available
    xl_file = pd.ExcelFile(excel_path)
    print(f"   Available sheets: {xl_file.sheet_names}")
    
    # Load the main data
    df_main = pd.read_excel(excel_path, sheet_name=0)
    print(f"   Loaded {len(df_main)} total rows")
    print(f"   Columns: {df_main.columns.tolist()[:10]}...")  # First 10 columns
    
    # Check for year column to handle multiple years
    year_cols = [col for col in df_main.columns if 'year' in col.lower() or 'reporting' in col.lower() and 'year' in col.lower()]
    if year_cols:
        print(f"\n   ⚠️  MULTIPLE YEARS DETECTED: {year_cols[0]}")
        years = df_main[year_cols[0]].unique()
        print(f"   Years available: {sorted(years)}")
        print(f"   Rows per year:")
        for year in sorted(years):
            count = len(df_main[df_main[year_cols[0]] == year])
            print(f"      {year}: {count} rows")
        
        # Filter to most recent year
        most_recent_year = max(years)
        print(f"\n   📅 Filtering to most recent year: {most_recent_year}")
        df_main = df_main[df_main[year_cols[0]] == most_recent_year].copy()
        print(f"   Filtered to {len(df_main)} buildings for year {most_recent_year}")
    
    # Check unique building count
    building_id_cols = [col for col in df_main.columns if 'building' in col.lower() and 'id' in col.lower()]
    if building_id_cols:
        unique_buildings = df_main[building_id_cols[0]].nunique()
        print(f"\n   📊 Unique buildings: {unique_buildings}")
        if unique_buildings < len(df_main):
            print(f"   ⚠️  Warning: {len(df_main) - unique_buildings} duplicate building entries found")
    
    # Check for key columns
    print("\n   Key columns found:")
    key_patterns = ['building', 'property', 'address', 'eui', 'sqft', 'square', 'name']
    for pattern in key_patterns:
        cols = [col for col in df_main.columns if pattern.lower() in col.lower()]
        if cols:
            print(f"      {pattern}: {cols}")
    
    # 2. Load geocoded buildings
    geocoded_path = os.path.join(data_dir, 'geocoded_buildings_final.csv')
    print(f"\n2️⃣ Loading geocoded buildings...")
    df_geocoded = pd.read_csv(geocoded_path)
    print(f"   Loaded {len(df_geocoded)} geocoded buildings")
    print(f"   Columns: {df_geocoded.columns.tolist()}")
    
    # 3. Load EPB data
    epb_path = os.path.join(data_dir, 'CopyofWeeklyEPBStatsReport Report.csv')
    print(f"\n3️⃣ Loading EPB data...")
    df_epb = pd.read_csv(epb_path)
    print(f"   Loaded {len(df_epb)} EPB buildings")
    print(f"   Columns: {df_epb.columns.tolist()[:5]}...")
    
    # 4. Load zip codes
    zip_path = os.path.join(data_dir, 'building_zipcode_lookup.csv')
    print(f"\n4️⃣ Loading zip code data...")
    df_zip = pd.read_csv(zip_path)
    print(f"   Loaded {len(df_zip)} building zip codes")
    print(f"   Columns: {df_zip.columns.tolist()}")
    
    # 5. Load EUI targets
    targets_path = os.path.join(data_dir, 'Building_EUI_Targets.csv')
    print(f"\n5️⃣ Loading EUI targets...")
    df_targets = pd.read_csv(targets_path)
    print(f"   Loaded {len(df_targets)} building targets")
    print(f"   Columns: {df_targets.columns.tolist()[:5]}...")
    
    return {
        'main': df_main,
        'geocoded': df_geocoded,
        'epb': df_epb,
        'zip': df_zip,
        'targets': df_targets
    }

def deduplicate_main_data(df_main):
    """Remove duplicate buildings if they exist after year filtering"""
    
    # Find building ID column
    building_id_cols = [col for col in df_main.columns if 'building' in col.lower() and 'id' in col.lower()]
    if building_id_cols:
        id_col = building_id_cols[0]
        
        # Check for duplicates
        duplicates = df_main[id_col].duplicated().sum()
        if duplicates > 0:
            print(f"\n⚠️  Found {duplicates} duplicate building entries")
            print("   Keeping first occurrence of each building")
            df_main = df_main.drop_duplicates(subset=[id_col], keep='first')
            print(f"   Reduced to {len(df_main)} unique buildings")
    
    return df_main

def standardize_building_ids(dfs):
    """Ensure all building IDs are strings and consistent"""
    
    print("\n🔧 Standardizing building IDs...")
    
    # First deduplicate main data if needed
    if 'main' in dfs:
        dfs['main'] = deduplicate_main_data(dfs['main'])
    
    for name, df in dfs.items():
        # Find the building ID column
        id_cols = [col for col in df.columns if 'building' in col.lower() and 'id' in col.lower()]
        if not id_cols and name == 'epb':
            id_cols = ['Building ID']
        
        if id_cols:
            id_col = id_cols[0]
            print(f"   {name}: Using column '{id_col}'")
            # Standardize to 'building_id' and ensure string type
            df['building_id'] = df[id_col].astype(str)
            # Remove any .0 from the end (Excel float conversion)
            df['building_id'] = df['building_id'].str.replace('.0$', '', regex=True)
        else:
            print(f"   ⚠️  {name}: No building ID column found!")
    
    return dfs

def merge_all_data(dfs):
    """Merge all data sources into comprehensive dataset"""
    
    print("\n🔄 Merging all data sources...")
    
    # Start with main data as base
    df_merged = dfs['main'].copy()
    print(f"   Starting with {len(df_merged)} buildings from main dataset")
    
    # 1. Add geocoded data (lat/lon)
    if 'building_id' in dfs['geocoded'].columns:
        geocoded_cols = ['building_id', 'latitude', 'longitude', 'geocoded']
        geocoded_cols = [col for col in geocoded_cols if col in dfs['geocoded'].columns]
        
        df_merged = df_merged.merge(
            dfs['geocoded'][geocoded_cols],
            on='building_id',
            how='left',
            suffixes=('', '_geo')
        )
        print(f"   ✓ Added geocoded data: {df_merged['latitude'].notna().sum()} buildings with coordinates")
    
    # 2. Add EPB status
    if 'building_id' in dfs['epb'].columns:
        # Create EPB flags
        dfs['epb']['is_epb'] = dfs['epb']['EPB Application Status'].isin(['Approved', 'Pending'])
        dfs['epb']['epb_status'] = dfs['epb']['EPB Application Status']
        dfs['epb']['epb_building_name'] = dfs['epb']['Building Name']
        dfs['epb']['epb_building_address'] = dfs['epb']['Building Address']
        
        epb_cols = ['building_id', 'is_epb', 'epb_status', 'epb_building_name', 'epb_building_address']
        
        df_merged = df_merged.merge(
            dfs['epb'][epb_cols],
            on='building_id',
            how='left',
            suffixes=('', '_epb')
        )
        df_merged['is_epb'] = df_merged['is_epb'].fillna(False)
        print(f"   ✓ Added EPB data: {df_merged['is_epb'].sum()} EPB buildings")
    
    # 3. Add zip codes
    if 'building_id' in dfs['zip'].columns:
        zip_cols = ['building_id'] + [col for col in dfs['zip'].columns if 'zip' in col.lower()]
        
        df_merged = df_merged.merge(
            dfs['zip'][zip_cols],
            on='building_id',
            how='left',
            suffixes=('', '_zip')
        )
        print(f"   ✓ Added zip codes")
    
    # 4. Add EUI targets
    if 'building_id' in dfs['targets'].columns:
        target_cols = ['building_id'] + [col for col in dfs['targets'].columns if 'target' in col.lower() or 'eui' in col.lower()]
        
        df_merged = df_merged.merge(
            dfs['targets'][target_cols],
            on='building_id',
            how='left',
            suffixes=('', '_target')
        )
        print(f"   ✓ Added EUI targets")
    
    # Clean up column names
    print(f"\n   Final dataset: {len(df_merged)} buildings with {len(df_merged.columns)} columns")
    
    return df_merged

def create_der_ready_dataset(df_merged):
    """Create dataset specifically formatted for DER clustering analysis"""
    
    print("\n🎯 Creating DER-ready dataset...")
    
    # Essential columns for DER analysis
    der_columns = {
        'building_id': 'building_id',
        'building_name': None,  # Will find best column
        'property_address': None,  # Will find best column
        'property_type': None,
        'gross_floor_area': None,
        'latitude': 'latitude',
        'longitude': 'longitude',
        'zip_code': None,
        'is_epb': 'is_epb',
        'epb_status': 'epb_status'
    }
    
    # Find best columns for each field
    for target, current in der_columns.items():
        if current is None:
            # Search for matching columns
            if target == 'building_name':
                candidates = [col for col in df_merged.columns if 'name' in col.lower() and 'building' in col.lower()]
                if not candidates:
                    candidates = [col for col in df_merged.columns if 'name' in col.lower()]
                if candidates:
                    # Prefer EPB name if available
                    if 'epb_building_name' in candidates:
                        der_columns[target] = 'epb_building_name'
                    else:
                        der_columns[target] = candidates[0]
            
            elif target == 'property_address':
                candidates = [col for col in df_merged.columns if 'address' in col.lower()]
                if candidates:
                    # Prefer EPB address if available
                    if 'epb_building_address' in candidates:
                        der_columns[target] = 'epb_building_address'
                    else:
                        der_columns[target] = candidates[0]
            
            elif target == 'property_type':
                candidates = [col for col in df_merged.columns if 'type' in col.lower() and 'property' in col.lower()]
                if candidates:
                    der_columns[target] = candidates[0]
            
            elif target == 'gross_floor_area':
                candidates = [col for col in df_merged.columns if 'sqft' in col.lower() or 'square' in col.lower() or 'floor' in col.lower()]
                if candidates:
                    der_columns[target] = candidates[0]
            
            elif target == 'zip_code':
                candidates = [col for col in df_merged.columns if 'zip' in col.lower()]
                if candidates:
                    der_columns[target] = candidates[0]
    
    # Create DER dataset with found columns
    df_der = pd.DataFrame()
    
    for target, source in der_columns.items():
        if source and source in df_merged.columns:
            df_der[target] = df_merged[source]
            print(f"   ✓ {target} <- {source}")
        else:
            print(f"   ⚠️  {target} <- NOT FOUND")
            df_der[target] = None
    
    # Add energy use columns
    print("\n   Adding energy use columns...")
    
    # Find electricity columns
    elec_cols = [col for col in df_merged.columns if 'electric' in col.lower() and 'use' in col.lower()]
    if elec_cols:
        df_der['electricity_use'] = df_merged[elec_cols[0]]
        print(f"   ✓ electricity_use <- {elec_cols[0]}")
    
    # Find gas columns
    gas_cols = [col for col in df_merged.columns if 'gas' in col.lower() and 'use' in col.lower()]
    if gas_cols:
        df_der['natural_gas_use'] = df_merged[gas_cols[0]]
        print(f"   ✓ natural_gas_use <- {gas_cols[0]}")
    
    # Find EUI columns
    eui_cols = [col for col in df_merged.columns if 'eui' in col.lower() and 'site' in col.lower()]
    if eui_cols:
        df_der['site_eui'] = df_merged[eui_cols[0]]
        print(f"   ✓ site_eui <- {eui_cols[0]}")
    
    # Add all other potentially useful columns
    print("\n   Adding additional columns...")
    for col in df_merged.columns:
        if col not in df_der.columns and any(keyword in col.lower() for keyword in ['penalty', 'target', 'compliance', 'opt']):
            df_der[col] = df_merged[col]
            print(f"   ✓ {col}")
    
    # Filter to only buildings with coordinates
    df_der_geo = df_der[df_der['latitude'].notna() & df_der['longitude'].notna()].copy()
    print(f"\n📍 Final DER dataset: {len(df_der_geo)} buildings with coordinates")
    
    return df_der, df_der_geo

def save_datasets(df_merged, df_der, df_der_geo, output_dir):
    """Save the merged datasets"""
    
    print(f"\n💾 Saving datasets to {output_dir}...")
    
    # Create processed data directory
    processed_dir = os.path.join(output_dir, 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    # Save comprehensive merged dataset
    merged_path = os.path.join(processed_dir, 'comprehensive_building_data.csv')
    df_merged.to_csv(merged_path, index=False)
    print(f"   ✓ Saved comprehensive data: {merged_path}")
    
    # Save DER-ready dataset (all buildings)
    der_path = os.path.join(processed_dir, 'der_ready_all_buildings.csv')
    df_der.to_csv(der_path, index=False)
    print(f"   ✓ Saved DER-ready data (all): {der_path}")
    
    # Save DER-ready dataset (with coordinates only)
    der_geo_path = os.path.join(processed_dir, 'der_ready_with_coordinates.csv')
    df_der_geo.to_csv(der_geo_path, index=False)
    print(f"   ✓ Saved DER-ready data (geo): {der_geo_path}")
    
    # Save summary statistics
    summary = {
        'total_buildings_raw': len(df_merged),
        'buildings_with_coordinates': len(df_der_geo),
        'epb_buildings': int(df_der_geo['is_epb'].sum()),
        'data_sources': {
            'main_report': 'Energize Denver Report Request 060225.xlsx',
            'geocoded': 'geocoded_buildings_final.csv',
            'epb': 'CopyofWeeklyEPBStatsReport Report.csv',
            'zip_codes': 'building_zipcode_lookup.csv',
            'eui_targets': 'Building_EUI_Targets.csv'
        },
        'columns_available': df_der_geo.columns.tolist()
    }
    
    summary_path = os.path.join(processed_dir, 'data_merge_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"   ✓ Saved summary: {summary_path}")
    
    return {
        'merged_path': merged_path,
        'der_path': der_path,
        'der_geo_path': der_geo_path,
        'summary_path': summary_path
    }

def main():
    """Main function to merge all data sources"""
    
    # Paths
    data_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw'
    output_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data'
    
    print("🚀 Starting Comprehensive Data Merge for DER Analysis\n")
    
    # Load all data
    dfs = load_and_examine_data(data_dir)
    
    # Standardize building IDs
    dfs = standardize_building_ids(dfs)
    
    # Merge all data
    df_merged = merge_all_data(dfs)
    
    # Create DER-ready dataset
    df_der, df_der_geo = create_der_ready_dataset(df_merged)
    
    # Save datasets
    paths = save_datasets(df_merged, df_der, df_der_geo, output_dir)
    
    print("\n✅ Data merge complete!")
    print("\n🎯 Next steps:")
    print("   1. Use 'der_ready_with_coordinates.csv' for clustering analysis")
    print("   2. This file has building names, addresses, and all energy data")
    print("   3. Run the enhanced DER clustering with this comprehensive dataset")
    
    return df_der_geo, paths

if __name__ == "__main__":
    df_final, output_paths = main()
