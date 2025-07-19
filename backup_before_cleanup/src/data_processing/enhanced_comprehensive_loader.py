"""
Suggested File Name: enhanced_comprehensive_loader.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/data_processing/
Use: Enhanced loader that creates comprehensive dataset with all buildings reporting after 2021

This script:
1. Timestamps all output files
2. Includes ALL buildings that reported after 2021 (post-COVID)
3. Uses most recent data for each building
4. Tracks when each building last reported
5. Maximizes building coverage while using best available data
6. Calculates trends from baseline years using Building_EUI_Targets.csv
7. Formats numeric columns as float for Excel compatibility
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

def get_timestamp():
    """Generate timestamp for file naming"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

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

def create_post_covid_comprehensive_dataset(df_all, key_columns):
    """Create dataset with all buildings reporting after 2021"""
    
    print("\n🔧 Creating post-COVID comprehensive dataset...")
    
    # Ensure Building ID is string
    df_all['Building ID'] = df_all[key_columns['id']].astype(str)
    df_all['Reporting Year'] = df_all[key_columns['year']]
    
    # Filter to post-2021 data (avoiding COVID impacts)
    print("   📅 Filtering to buildings reporting after 2021...")
    df_post_covid = df_all[df_all[key_columns['year']] > 2021].copy()
    
    # Get unique buildings that reported after 2021
    post_covid_buildings = df_post_covid['Building ID'].unique()
    print(f"   Found {len(post_covid_buildings)} unique buildings reporting after 2021")
    
    # For each building, get the most recent year's data
    print("\n   🔄 Getting most recent data for each building...")
    
    # Create list to store most recent data for each building
    building_data = []
    
    for building_id in post_covid_buildings:
        # Get all records for this building
        building_records = df_all[df_all['Building ID'] == building_id]
        
        # Get the most recent year
        most_recent_year = building_records[key_columns['year']].max()
        
        # Get the data for the most recent year
        most_recent_data = building_records[building_records[key_columns['year']] == most_recent_year].iloc[0].to_dict()
        
        # Add tracking of when they last reported
        most_recent_data['Most_Recent_Report_Year'] = most_recent_year
        most_recent_data['Years_Reported'] = building_records[key_columns['year']].unique().tolist()
        most_recent_data['Number_Years_Reported'] = len(building_records[key_columns['year']].unique())
        
        building_data.append(most_recent_data)
    
    # Create comprehensive dataframe
    df_comprehensive = pd.DataFrame(building_data)
    
    # Sort by most recent report year and building ID
    df_comprehensive = df_comprehensive.sort_values(['Most_Recent_Report_Year', 'Building ID'], 
                                                  ascending=[False, True])
    
    print(f"\n   📊 Comprehensive dataset statistics:")
    print(f"      Total buildings: {len(df_comprehensive)}")
    
    # Count by most recent year
    year_counts = df_comprehensive['Most_Recent_Report_Year'].value_counts().sort_index()
    print("\n   📅 Buildings by most recent report year:")
    for year, count in year_counts.items():
        print(f"      {year}: {count} buildings")
    
    # Add energy trends if multiple years available
    print("\n   📈 Calculating energy trends...")
    
    # Find Weather Normalized Site EUI column
    eui_col = None
    for col in key_columns['energy_columns']:
        if 'weather normalized site eui' in col.lower():
            eui_col = col
            break
    
    if eui_col:
        # Calculate 3-year trends where possible
        trend_count = 0
        for idx, row in df_comprehensive.iterrows():
            building_id = row['Building ID']
            
            # Get historical data for this building
            building_history = df_all[df_all['Building ID'] == building_id]
            
            # Get last 3 years of data if available
            recent_years = sorted(building_history[key_columns['year']].unique())[-3:]
            
            if len(recent_years) >= 2:  # Need at least 2 years for trend
                df_recent = building_history[building_history[key_columns['year']].isin(recent_years)].copy()
                df_recent[eui_col] = pd.to_numeric(df_recent[eui_col], errors='coerce')
                
                # Calculate average and trend
                if df_recent[eui_col].notna().sum() >= 2:
                    avg_eui = df_recent[eui_col].mean()
                    df_comprehensive.at[idx, 'Average_EUI_Recent'] = float(avg_eui)
                    
                    # Calculate year-over-year change
                    first_year_eui = df_recent[df_recent[key_columns['year']] == min(recent_years)][eui_col].iloc[0]
                    last_year_eui = df_recent[df_recent[key_columns['year']] == max(recent_years)][eui_col].iloc[0]
                    
                    if pd.notna(first_year_eui) and pd.notna(last_year_eui) and first_year_eui != 0:
                        pct_change = ((last_year_eui - first_year_eui) / first_year_eui) * 100
                        df_comprehensive.at[idx, 'EUI_Trend_Pct'] = float(pct_change)
                        trend_count += 1
        
        print(f"   ✓ Calculated trends for {trend_count} buildings")
    
    # Convert numeric columns to float
    numeric_columns = ['Average_EUI_Recent', 'EUI_Trend_Pct']
    for col in numeric_columns:
        if col in df_comprehensive.columns:
            df_comprehensive[col] = pd.to_numeric(df_comprehensive[col], errors='coerce').astype('float64')
    
    return df_comprehensive, df_all

def calculate_baseline_trends(df_comprehensive, df_all, key_columns):
    """Calculate energy trends from each building's baseline year"""
    
    print("\n📈 Calculating trends from baseline years...")
    
    # Find baseline year column
    baseline_col = None
    for col in df_comprehensive.columns:
        if 'baseline' in col.lower() and 'year' in col.lower():
            baseline_col = col
            break
    
    if not baseline_col:
        print("   ⚠️  No baseline year column found, skipping baseline trend calculation")
        return df_comprehensive
    
    # Find Weather Normalized Site EUI column
    eui_col = None
    for col in key_columns['energy_columns']:
        if 'weather normalized site eui' in col.lower():
            eui_col = col
            break
    
    if not eui_col:
        print("   ⚠️  No Weather Normalized Site EUI column found")
        return df_comprehensive
    
    # Calculate trends from baseline
    baseline_trend_count = 0
    
    for idx, row in df_comprehensive.iterrows():
        building_id = row['Building ID']
        baseline_year = row.get(baseline_col)
        current_year = row['Most_Recent_Report_Year']
        
        if pd.notna(baseline_year) and baseline_year != current_year:
            # Get historical data for this building
            building_history = df_all[df_all['Building ID'] == building_id].copy()
            
            # Convert EUI to numeric
            building_history[eui_col] = pd.to_numeric(building_history[eui_col], errors='coerce')
            
            # Get baseline year data
            baseline_data = building_history[building_history[key_columns['year']] == baseline_year]
            current_data = building_history[building_history[key_columns['year']] == current_year]
            
            if len(baseline_data) > 0 and len(current_data) > 0:
                baseline_eui = baseline_data[eui_col].iloc[0]
                current_eui = current_data[eui_col].iloc[0]
                
                if pd.notna(baseline_eui) and pd.notna(current_eui) and baseline_eui > 0:
                    # Calculate percentage change from baseline
                    pct_change = ((current_eui - baseline_eui) / baseline_eui) * 100
                    df_comprehensive.at[idx, 'EUI_Change_From_Baseline_Pct'] = float(pct_change)
                    df_comprehensive.at[idx, 'Baseline_EUI'] = float(baseline_eui)
                    df_comprehensive.at[idx, 'Current_EUI'] = float(current_eui)
                    baseline_trend_count += 1
    
    print(f"   ✓ Calculated baseline trends for {baseline_trend_count} buildings")
    
    # Show baseline year distribution
    if baseline_col in df_comprehensive.columns:
        baseline_counts = df_comprehensive[baseline_col].value_counts().sort_index()
        print("\n   📅 Baseline years showing improvement from baseline:")
        
        # For buildings with baseline trends, show which baseline years are improving
        df_with_trends = df_comprehensive[df_comprehensive['EUI_Change_From_Baseline_Pct'].notna()]
        improving = df_with_trends[df_with_trends['EUI_Change_From_Baseline_Pct'] < 0]
        
        for year in sorted(baseline_counts.index):
            if pd.notna(year):
                year_buildings = df_comprehensive[df_comprehensive[baseline_col] == year]
                year_improving = improving[improving[baseline_col] == year]
                print(f"      {int(year)}: {len(year_buildings)} buildings ({len(year_improving)} improving)")
    
    # Ensure all numeric columns are float type
    float_columns = ['Average_EUI_Recent', 'EUI_Trend_Pct', 'EUI_Change_From_Baseline_Pct', 
                    'latitude', 'longitude', 'Baseline_EUI', 'Current_EUI']
    
    for col in float_columns:
        if col in df_comprehensive.columns:
            df_comprehensive[col] = pd.to_numeric(df_comprehensive[col], errors='coerce').astype('float64')
    
    return df_comprehensive

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
                
                # Convert lat/lon to float
                df_geo_subset['latitude'] = pd.to_numeric(df_geo_subset['latitude'], errors='coerce').astype('float64')
                df_geo_subset['longitude'] = pd.to_numeric(df_geo_subset['longitude'], errors='coerce').astype('float64')
                
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
    
    # 4. EUI Targets and Baseline Years
    targets_path = os.path.join(data_dir, 'Building_EUI_Targets.csv')
    if os.path.exists(targets_path):
        df_targets = pd.read_csv(targets_path)
        
        # Find building ID column
        target_id_col = None
        for col in df_targets.columns:
            if 'building' in col.lower() and 'id' in col.lower():
                target_id_col = col
                break
        
        if target_id_col:
            df_targets['building_id_clean'] = df_targets[target_id_col].astype(str)
            
            # Find baseline year column
            baseline_col = None
            for col in df_targets.columns:
                if 'baseline' in col.lower() and 'year' in col.lower():
                    baseline_col = col
                    break
            
            # Find target columns
            target_cols = ['building_id_clean']
            if baseline_col:
                target_cols.append(baseline_col)
                
            # Add other useful target columns
            for col in df_targets.columns:
                if any(term in col.lower() for term in ['target', 'baseline eui']):
                    if col not in target_cols:
                        target_cols.append(col)
            
            # Merge targets
            df_comprehensive = df_comprehensive.merge(
                df_targets[target_cols],
                left_on='Building ID',
                right_on='building_id_clean',
                how='left'
            )
            df_comprehensive.drop('building_id_clean', axis=1, inplace=True)
            
            if baseline_col in df_comprehensive.columns:
                print(f"   ✓ Added baseline years and targets")
                # Convert baseline year to numeric
                df_comprehensive[baseline_col] = pd.to_numeric(df_comprehensive[baseline_col], errors='coerce')
                
                # Show baseline year distribution
                baseline_counts = df_comprehensive[baseline_col].value_counts().sort_index()
                print("\n   📅 Baseline year distribution:")
                for year, count in baseline_counts.items():
                    if pd.notna(year):
                        print(f"      {int(year)}: {count} buildings")
            else:
                print(f"   ✓ Added EUI targets (no baseline year column found)")
        else:
            print(f"   ⚠️  Could not find building ID column in targets data")
    
    return df_comprehensive

def format_eui_columns(df):
    """Format EUI columns to 2 decimal places"""
    eui_columns = ['Average_EUI_Recent', 'EUI_Trend_Pct', 'EUI_Change_From_Baseline_Pct', 
                   'Current_EUI', 'Baseline_EUI']
    
    for col in eui_columns:
        if col in df.columns:
            # Round to 2 decimal places
            df[col] = df[col].round(2)
    
    return df

def save_comprehensive_data(df_comprehensive, df_all, output_dir, timestamp):
    """Save the comprehensive datasets with timestamps"""
    
    print(f"\n💾 Saving comprehensive energy data with timestamp {timestamp}...")
    
    # Format EUI columns to 2 decimal places
    df_comprehensive = format_eui_columns(df_comprehensive)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save comprehensive post-COVID data with timestamp
    comprehensive_path = os.path.join(output_dir, f'energize_denver_comprehensive_{timestamp}.csv')
    df_comprehensive.to_csv(comprehensive_path, index=False)
    print(f"   ✓ Saved comprehensive data: {comprehensive_path}")
    
    # Also save without timestamp for easy reference
    latest_path = os.path.join(output_dir, 'energize_denver_comprehensive_latest.csv')
    df_comprehensive.to_csv(latest_path, index=False)
    print(f"   ✓ Saved latest reference: {latest_path}")
    
    # Save all years data with timestamp
    all_years_path = os.path.join(output_dir, f'energize_denver_all_years_{timestamp}.csv')
    df_all.to_csv(all_years_path, index=False)
    print(f"   ✓ Saved historical data: {all_years_path}")
    
    # Save summary with timestamp
    summary = {
        'data_generated': datetime.now().isoformat(),
        'timestamp': timestamp,
        'total_unique_buildings': int(df_comprehensive['Building ID'].nunique()),
        'buildings_with_coordinates': int(df_comprehensive['latitude'].notna().sum()) if 'latitude' in df_comprehensive.columns else 0,
        'epb_buildings': int(df_comprehensive['is_epb'].sum()) if 'is_epb' in df_comprehensive.columns else 0,
        'post_covid_filter': 'Buildings reporting after 2021',
        'most_recent_years': df_comprehensive['Most_Recent_Report_Year'].value_counts().sort_index().to_dict(),
        'energy_columns': [col for col in df_comprehensive.columns if any(term in col.lower() for term in ['energy', 'eui', 'normalized'])],
        'ghg_columns': [col for col in df_comprehensive.columns if 'ghg' in col.lower() or 'emissions' in col.lower()]
    }
    
    # Add baseline trend summary if available
    if 'EUI_Change_From_Baseline_Pct' in df_comprehensive.columns:
        buildings_with_trends = df_comprehensive['EUI_Change_From_Baseline_Pct'].notna().sum()
        improving_buildings = (df_comprehensive['EUI_Change_From_Baseline_Pct'] < 0).sum()
        avg_improvement = df_comprehensive[df_comprehensive['EUI_Change_From_Baseline_Pct'] < 0]['EUI_Change_From_Baseline_Pct'].mean()
        
        summary['baseline_trends'] = {
            'buildings_with_baseline_trends': int(buildings_with_trends),
            'buildings_improving_from_baseline': int(improving_buildings),
            'average_improvement_percent': float(avg_improvement) if pd.notna(avg_improvement) else None
        }
    
    summary_path = os.path.join(output_dir, f'comprehensive_data_summary_{timestamp}.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"   ✓ Saved summary: {summary_path}")
    
    # Also save latest summary
    latest_summary_path = os.path.join(output_dir, 'comprehensive_data_summary_latest.json')
    with open(latest_summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return comprehensive_path, all_years_path, summary_path

def main():
    """Main function to create enhanced comprehensive energy dataset"""
    
    # Paths
    excel_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/Energize Denver Report Request 060225.xlsx'
    data_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw'
    output_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed'
    
    # Generate timestamp
    timestamp = get_timestamp()
    
    print(f"🚀 Starting Enhanced Comprehensive Energy Data Load (Timestamp: {timestamp})\n")
    
    # Step 1: Examine Excel structure
    key_columns, df_sample = examine_excel_structure(excel_path)
    
    # Step 2: Load all years
    df_all = load_all_years_data(excel_path, key_columns)
    
    # Step 3: Create post-COVID comprehensive dataset
    df_comprehensive, df_all_processed = create_post_covid_comprehensive_dataset(df_all, key_columns)
    
    # Step 4: Merge with other sources
    df_comprehensive = merge_with_other_sources(df_comprehensive, data_dir)
    
    # Step 5: Calculate baseline trends if targets were merged
    df_comprehensive = calculate_baseline_trends(df_comprehensive, df_all_processed, key_columns)
    
    # Step 6: Save results with timestamp
    current_path, all_path, summary_path = save_comprehensive_data(
        df_comprehensive, 
        df_all_processed,
        output_dir,
        timestamp
    )
    
    print("\n✅ Enhanced comprehensive energy data load complete!")
    print(f"\n📊 Results:")
    print(f"   Total buildings (post-2021 reporters): {len(df_comprehensive)}")
    print(f"   Columns: {len(df_comprehensive.columns)}")
    print(f"   Timestamp: {timestamp}")
    
    if 'EUI_Change_From_Baseline_Pct' in df_comprehensive.columns:
        buildings_with_trends = df_comprehensive['EUI_Change_From_Baseline_Pct'].notna().sum()
        improving = (df_comprehensive['EUI_Change_From_Baseline_Pct'] < 0).sum()
        print(f"\n📊 Baseline Trend Analysis:")
        print(f"   Buildings with baseline trends: {buildings_with_trends}")
        print(f"   Buildings improving from baseline: {improving}")
    
    print(f"\n📁 Output files:")
    print(f"   Comprehensive: {current_path}")
    print(f"   Latest reference: energize_denver_comprehensive_latest.csv")
    print(f"   All years: {all_path}")
    print(f"   Summary: {summary_path}")
    
    return df_comprehensive

if __name__ == "__main__":
    df = main()
