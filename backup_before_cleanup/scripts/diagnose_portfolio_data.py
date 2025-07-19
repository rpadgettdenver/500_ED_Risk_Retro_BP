"""
Suggested File Name: diagnose_portfolio_data.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/scripts/
Use: Diagnose data issues and understand portfolio structure

This script examines the data to understand:
- What buildings are included
- Data quality issues
- Proper column names and types
"""

import pandas as pd
import numpy as np
import os

def diagnose_portfolio_data():
    """Diagnose issues with portfolio data"""
    
    print("🔍 PORTFOLIO DATA DIAGNOSTIC")
    print("=" * 60)
    
    # Define paths
    base_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data'
    comprehensive_path = os.path.join(base_path, 'processed', 'energize_denver_comprehensive_latest.csv')
    targets_path = os.path.join(base_path, 'raw', 'Building_EUI_Targets.csv')
    
    # Load comprehensive data
    print("\n1. Loading comprehensive data...")
    df_comprehensive = pd.read_csv(comprehensive_path)
    print(f"   Loaded {len(df_comprehensive)} rows")
    print(f"   Columns: {len(df_comprehensive.columns)}")
    
    # Check Building ID
    print("\n2. Checking Building ID column...")
    building_id_cols = [col for col in df_comprehensive.columns if 'building' in col.lower() and 'id' in col.lower()]
    print(f"   Building ID columns found: {building_id_cols}")
    
    if 'Building ID' in df_comprehensive.columns:
        unique_buildings = df_comprehensive['Building ID'].nunique()
        print(f"   Unique Building IDs: {unique_buildings}")
        print(f"   Duplicates: {len(df_comprehensive) - unique_buildings}")
    
    # Check EUI columns
    print("\n3. Checking EUI columns...")
    eui_cols = [col for col in df_comprehensive.columns if 'eui' in col.lower()]
    print(f"   EUI columns found: {len(eui_cols)}")
    for col in eui_cols[:5]:  # Show first 5
        print(f"     - {col}")
    
    # Check Weather Normalized Site EUI
    print("\n4. Checking Weather Normalized Site EUI...")
    if 'Weather Normalized Site EUI' in df_comprehensive.columns:
        eui_col = df_comprehensive['Weather Normalized Site EUI']
        print(f"   Data type: {eui_col.dtype}")
        print(f"   Non-numeric values: {(~pd.to_numeric(eui_col, errors='coerce').notna()).sum()}")
        print(f"   Missing values: {eui_col.isna().sum()}")
        
        # Show sample of non-numeric values
        non_numeric_mask = ~pd.to_numeric(eui_col, errors='coerce').notna() & eui_col.notna()
        if non_numeric_mask.any():
            print(f"   Sample non-numeric values:")
            print(f"     {eui_col[non_numeric_mask].head().tolist()}")
    
    # Check Square Footage
    print("\n5. Checking Square Footage columns...")
    sqft_cols = [col for col in df_comprehensive.columns if any(term in col.lower() for term in ['sqft', 'square', 'floor', 'area'])]
    print(f"   Square footage columns found: {len(sqft_cols)}")
    for col in sqft_cols[:5]:  # Show first 5
        print(f"     - {col}")
    
    if 'Master Sq Ft' in df_comprehensive.columns:
        sqft_col = df_comprehensive['Master Sq Ft']
        print(f"\n   Master Sq Ft data type: {sqft_col.dtype}")
        print(f"   Non-numeric values: {(~pd.to_numeric(sqft_col, errors='coerce').notna()).sum()}")
        print(f"   Missing values: {sqft_col.isna().sum()}")
    
    # Load targets data
    print("\n6. Loading EUI targets data...")
    df_targets = pd.read_csv(targets_path)
    print(f"   Loaded {len(df_targets)} rows")
    print(f"   Columns: {df_targets.columns.tolist()[:10]}...")  # First 10
    
    # Check for Building ID in targets
    target_id_cols = [col for col in df_targets.columns if 'building' in col.lower() and 'id' in col.lower()]
    print(f"   Building ID columns in targets: {target_id_cols}")
    
    # Data quality summary
    print("\n7. Data Quality Summary:")
    
    # Convert to numeric for analysis
    df_clean = df_comprehensive.copy()
    
    if 'Weather Normalized Site EUI' in df_clean.columns:
        df_clean['Weather Normalized Site EUI'] = pd.to_numeric(
            df_clean['Weather Normalized Site EUI'], errors='coerce'
        )
    
    if 'Master Sq Ft' in df_clean.columns:
        df_clean['Master Sq Ft'] = pd.to_numeric(
            df_clean['Master Sq Ft'], errors='coerce'
        )
    
    # Filter buildings
    valid_eui = df_clean['Weather Normalized Site EUI'] > 0
    valid_sqft = df_clean['Master Sq Ft'] >= 25000
    
    print(f"\n   Total buildings in comprehensive data: {len(df_clean)}")
    print(f"   Buildings with valid EUI (>0): {valid_eui.sum()}")
    print(f"   Buildings with sqft >= 25,000: {valid_sqft.sum()}")
    print(f"   Buildings meeting both criteria: {(valid_eui & valid_sqft).sum()}")
    
    # Show property type distribution
    if 'Master Property Type' in df_clean.columns:
        print("\n8. Property Type Distribution (top 10):")
        prop_types = df_clean[valid_eui & valid_sqft]['Master Property Type'].value_counts().head(10)
        for prop_type, count in prop_types.items():
            print(f"   {prop_type}: {count}")
    
    # Show year distribution
    if 'Most_Recent_Report_Year' in df_clean.columns:
        print("\n9. Reporting Year Distribution:")
        years = df_clean[valid_eui & valid_sqft]['Most_Recent_Report_Year'].value_counts().sort_index()
        for year, count in years.items():
            print(f"   {year}: {count} buildings")
    
    return df_clean, df_targets


def check_column_mapping():
    """Check if we need to update column names in the analyzer"""
    
    print("\n\n📋 COLUMN MAPPING CHECK")
    print("=" * 60)
    
    # Expected columns in portfolio_risk_analyzer.py
    expected_columns = {
        'Building ID': ['Building ID', 'building_id'],
        'Weather Normalized Site EUI': ['Weather Normalized Site EUI', 'weather_normalized_site_eui'],
        'Master Sq Ft': ['Master Sq Ft', 'gross_floor_area', 'Gross Floor Area'],
        'Master Property Type': ['Master Property Type', 'property_type', 'Property Type'],
        'Baseline EUI': ['Baseline EUI', 'baseline_eui'],
        'First Interim Target EUI': ['First Interim Target EUI', 'first_interim_target'],
        'Second Interim Target EUI': ['Second Interim Target EUI', 'second_interim_target'],
        'Adjusted Final Target EUI': ['Adjusted Final Target EUI', 'final_target'],
        'Original Final Target EUI': ['Original Final Target EUI', 'original_final_target']
    }
    
    # Load actual data
    comprehensive_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed/energize_denver_comprehensive_latest.csv'
    df = pd.read_csv(comprehensive_path)
    
    print("\nChecking for expected columns:")
    missing_columns = []
    found_columns = []
    
    for expected, alternatives in expected_columns.items():
        found = False
        for col in alternatives:
            if col in df.columns:
                found_columns.append(f"✅ {expected} -> found as '{col}'")
                found = True
                break
        
        if not found:
            missing_columns.append(f"❌ {expected} -> NOT FOUND")
            # Look for similar columns
            similar = [col for col in df.columns if any(term in col.lower() for term in expected.lower().split())]
            if similar:
                missing_columns.append(f"   Possible matches: {similar[:3]}")
    
    for msg in found_columns:
        print(f"   {msg}")
    
    for msg in missing_columns:
        print(f"   {msg}")
    
    return df


if __name__ == "__main__":
    # Run diagnostic
    df_clean, df_targets = diagnose_portfolio_data()
    
    # Check column mapping
    df = check_column_mapping()
    
    print("\n\n✅ Diagnostic complete!")
    print("\nNext steps:")
    print("1. Fix any column name mismatches in portfolio_risk_analyzer.py")
    print("2. Handle non-numeric data types properly")
    print("3. Re-run the portfolio analysis")
