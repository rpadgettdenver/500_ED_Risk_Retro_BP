"""
Suggested File Name: create_penalty_view_fixed.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Create the penalty analysis view using only the most recent year's consumption data
     and weather normalized EUI values

This script:
1. First explores the consumption data structure to understand the year column
2. Creates a view using only the latest year per building
3. Uses weather normalized EUI for more accurate comparisons
"""

from google.cloud import bigquery

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

def explore_consumption_data():
    """First, let's understand the data structure better"""
    
    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    
    print("=== EXPLORING CONSUMPTION DATA STRUCTURE ===\n")
    
    # Check all columns
    query = f"""
    SELECT column_name, data_type
    FROM `{dataset_ref}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'building_consumption'
    ORDER BY ordinal_position
    """
    
    columns_df = client.query(query).to_dataframe()
    print("All columns in building_consumption:")
    for _, row in columns_df.iterrows():
        print(f"  {row['column_name']:<35} {row['data_type']}")
    
    # Check if we need to re-read the Excel to get year and weather normalized data
    print("\n\nChecking for year/weather normalized data...")
    
    sample_query = f"""
    SELECT *
    FROM `{dataset_ref}.building_consumption`
    WHERE building_id = '1001'
    ORDER BY building_id
    LIMIT 5
    """
    
    sample = client.query(sample_query).to_dataframe()
    print("\nSample data for building 1001:")
    print(sample)
    
    # Check unique years
    years_query = f"""
    SELECT 
        EXTRACT(YEAR FROM PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S', load_timestamp)) as data_year,
        COUNT(DISTINCT building_id) as unique_buildings,
        COUNT(*) as total_records
    FROM `{dataset_ref}.building_consumption`
    GROUP BY data_year
    ORDER BY data_year
    """
    
    print("\n\nRecords by year (from timestamp):")
    years_df = client.query(years_query).to_dataframe()
    print(years_df)

def reload_excel_with_all_columns():
    """Reload the Excel file to get all necessary columns including year and weather normalized EUI"""
    
    import pandas as pd
    from datetime import datetime
    
    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    
    print("\n\n=== RELOADING EXCEL WITH ALL COLUMNS ===\n")
    
    # Read Excel file
    excel_path = "data/raw/Energize Denver Report Request 060225.xlsx"
    df = pd.read_excel(excel_path)
    
    print(f"Loaded {len(df)} rows from Excel")
    print("\nAll columns:")
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2}. {col}")
    
    # Create comprehensive dataframe
    processed_df = pd.DataFrame()
    
    # Core identification
    processed_df['building_id'] = df['Building ID'].astype(str)
    processed_df['reporting_year'] = pd.to_numeric(df['ID-Yr'].astype(str).str[-4:], errors='coerce')
    
    # Building info
    processed_df['building_name'] = df['Building Name'].fillna('').astype(str)
    processed_df['parent_property'] = df['Parent Property'].fillna('').astype(str)
    processed_df['property_type'] = df['Master Property Type'].fillna('').astype(str)
    processed_df['year_built'] = pd.to_numeric(df['Year Built'], errors='coerce')
    
    # Size metrics
    processed_df['gross_floor_area'] = pd.to_numeric(df['Master Sq Ft'], errors='coerce')
    
    # Energy metrics - both regular and weather normalized
    processed_df['site_energy_use'] = pd.to_numeric(df['Site Energy Use'], errors='coerce')
    processed_df['site_eui'] = pd.to_numeric(df['Site EUI'], errors='coerce')
    processed_df['weather_normalized_energy'] = pd.to_numeric(df['Weather Normalized Site Energy Use'], errors='coerce')
    processed_df['weather_normalized_eui'] = pd.to_numeric(df['Weather Normalized Site EUI'], errors='coerce')
    
    # Compliance info
    processed_df['energy_star_score'] = pd.to_numeric(df['Energy Star Score'], errors='coerce')
    processed_df['status'] = df['Status'].fillna('').astype(str)
    processed_df['submission_date'] = pd.to_datetime(df['Submission Date'], errors='coerce')
    
    # Metadata
    processed_df['source_file'] = 'Energize Denver Report Request 060225.xlsx'
    processed_df['load_timestamp'] = datetime.now().isoformat()
    
    # Summary
    print(f"\n📊 Processed Data Summary:")
    print(f"   Total records: {len(processed_df)}")
    print(f"   Unique buildings: {processed_df['building_id'].nunique()}")
    print(f"   Year range: {processed_df['reporting_year'].min():.0f} - {processed_df['reporting_year'].max():.0f}")
    print(f"   Buildings with weather normalized EUI: {processed_df['weather_normalized_eui'].notna().sum()}")
    
    # Upload to BigQuery (replacing old table)
    table_id = f"{dataset_ref}.building_consumption_v2"
    
    print(f"\nUploading to {table_id}...")
    
    # Ensure all object columns are strings
    for col in processed_df.select_dtypes(include=['object']).columns:
        processed_df[col] = processed_df[col].astype(str)
    
    # Upload
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(
        processed_df, table_id, job_config=job_config
    )
    job.result()
    
    table = client.get_table(table_id)
    print(f"✓ Uploaded {table.num_rows} rows to {table_id}")
    
    return table_id

def create_improved_penalty_view():
    """Create penalty view using only latest year and weather normalized EUI"""
    
    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    view_id = f"{dataset_ref}.penalty_analysis_v2"
    
    print("\n\n=== CREATING IMPROVED PENALTY ANALYSIS VIEW ===")
    
    query = f"""
    CREATE OR REPLACE VIEW `{view_id}` AS
    WITH latest_consumption AS (
        -- Get only the most recent year of data for each building
        SELECT *
        FROM (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY building_id ORDER BY reporting_year DESC) as rn
            FROM `{dataset_ref}.building_consumption_v2`
            WHERE weather_normalized_eui IS NOT NULL
                AND weather_normalized_eui > 0
                AND reporting_year >= 2022  -- Focus on recent data
        )
        WHERE rn = 1
    ),
    combined_data AS (
        SELECT 
            t.*,
            c.reporting_year,
            c.weather_normalized_eui as actual_eui,
            c.site_eui as raw_site_eui,
            c.building_name as consumption_building_name,
            c.parent_property,
            c.energy_star_score,
            c.status as consumption_status,
            
            -- Calculate gaps using weather normalized EUI
            c.weather_normalized_eui - t.first_interim_target as interim_gap,
            c.weather_normalized_eui - COALESCE(t.adjusted_final_target, t.original_final_target) as final_gap,
            
            -- Determine compliance path (opt-in if over 2024 target)
            CASE 
                WHEN c.weather_normalized_eui > t.first_interim_target THEN 'Opt-in (2028/2032)'
                ELSE 'Default (2024/2030)'
            END as compliance_path
            
        FROM `{dataset_ref}.building_analysis_v2` t
        LEFT JOIN latest_consumption c
            ON t.building_id = c.building_id
    )
    SELECT 
        *,
        -- Calculate penalties based on weather normalized EUI
        CASE 
            WHEN actual_eui IS NULL THEN NULL
            WHEN consumption_status = 'Exempt' THEN 0  -- Exempt buildings pay no penalty
            WHEN compliance_path = 'Default (2024/2030)' THEN
                GREATEST(0, interim_gap * gross_floor_area * 0.15)
            ELSE
                GREATEST(0, interim_gap * gross_floor_area * 0.23)
        END as annual_penalty_2024,
        
        CASE 
            WHEN actual_eui IS NULL THEN NULL
            WHEN consumption_status = 'Exempt' THEN 0
            WHEN compliance_path = 'Default (2024/2030)' THEN
                GREATEST(0, final_gap * gross_floor_area * 0.15)
            ELSE
                GREATEST(0, final_gap * gross_floor_area * 0.23)
        END as annual_penalty_2030,
        
        -- Risk categorization
        CASE 
            WHEN actual_eui IS NULL THEN 'No Data'
            WHEN consumption_status = 'Exempt' THEN 'Exempt'
            WHEN interim_gap <= 0 THEN 'Compliant'
            WHEN interim_gap * gross_floor_area * 0.15 > 50000 THEN 'High Risk'
            WHEN interim_gap * gross_floor_area * 0.15 > 10000 THEN 'Medium Risk'
            ELSE 'Low Risk'
        END as risk_category
        
    FROM combined_data
    """
    
    try:
        client.query(query).result()
        print(f"✓ Created improved penalty analysis view: {view_id}")
        
        # Get summary with proper deduplication
        summary_query = f"""
        SELECT 
            COUNT(DISTINCT building_id) as unique_buildings,
            COUNT(*) as total_records,
            COUNT(DISTINCT CASE WHEN actual_eui IS NOT NULL THEN building_id END) as buildings_with_data,
            COUNT(DISTINCT CASE WHEN risk_category = 'High Risk' THEN building_id END) as high_risk_buildings,
            COUNT(DISTINCT CASE WHEN risk_category = 'Compliant' THEN building_id END) as compliant_buildings,
            COUNT(DISTINCT CASE WHEN risk_category = 'Exempt' THEN building_id END) as exempt_buildings,
            ROUND(SUM(annual_penalty_2024), 0) as total_penalty_2024,
            ROUND(AVG(CASE WHEN annual_penalty_2024 > 0 THEN annual_penalty_2024 END), 0) as avg_penalty_2024
        FROM `{view_id}`
        """
        
        results = client.query(summary_query).to_dataframe()
        
        print("\n📊 Penalty Analysis Summary (Deduplicated):")
        print(f"   Unique buildings: {results['unique_buildings'].iloc[0]:,}")
        print(f"   Buildings with consumption data: {results['buildings_with_data'].iloc[0]:,}")
        print(f"   Compliant buildings: {results['compliant_buildings'].iloc[0]:,}")
        print(f"   Exempt buildings: {results['exempt_buildings'].iloc[0]:,}")
        print(f"   High risk buildings: {results['high_risk_buildings'].iloc[0]:,}")
        print(f"   Total 2024 penalty exposure: ${results['total_penalty_2024'].iloc[0]:,.0f}")
        print(f"   Average penalty (non-compliant): ${results['avg_penalty_2024'].iloc[0]:,.0f}")
        
        # Show reasonable top risks
        print("\n\nTop 10 High-Risk Buildings (Latest Year, Weather Normalized):")
        print("-" * 110)
        
        high_risk_query = f"""
        SELECT 
            building_id,
            COALESCE(building_name, consumption_building_name) as building_name,
            property_type,
            reporting_year,
            ROUND(gross_floor_area, 0) as sqft,
            ROUND(actual_eui, 1) as weather_normalized_eui,
            ROUND(COALESCE(adjusted_final_target, original_final_target), 1) as target_eui,
            ROUND(percent_reduction_needed, 1) as reduction_pct,
            ROUND(annual_penalty_2024, 0) as penalty_2024,
            is_epb
        FROM `{view_id}`
        WHERE risk_category = 'High Risk'
            AND building_name IS NOT NULL
        ORDER BY annual_penalty_2024 DESC
        LIMIT 10
        """
        
        high_risk = client.query(high_risk_query).to_dataframe()
        
        for _, row in high_risk.iterrows():
            name = row['building_name'][:30] if row['building_name'] else f"Building {row['building_id']}"
            print(f"{name:<30} | {row['property_type']:<20} | {row['reporting_year']} | "
                  f"{row['sqft']:>10,.0f} sqft | "
                  f"EUI: {row['weather_normalized_eui']:>5.0f} → {row['target_eui']:>5.0f} | "
                  f"${row['penalty_2024']:>10,.0f}")
        
        print("\n✅ Improved penalty analysis ready!")
        print("\nThis view now:")
        print("- Uses only the most recent year per building")
        print("- Uses weather normalized EUI for fair comparisons")
        print("- Properly handles exempt buildings")
        print("- Avoids double-counting buildings across years")
        
        return view_id
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Main execution"""
    
    # Step 1: Explore current data
    explore_consumption_data()
    
    # Step 2: Reload Excel with all columns
    print("\n" + "="*80 + "\n")
    response = input("Reload Excel file with year and weather normalized data? (y/n): ")
    
    if response.lower() == 'y':
        table_id = reload_excel_with_all_columns()
        
        # Step 3: Create improved penalty view
        view_id = create_improved_penalty_view()
        
        if view_id:
            print(f"\n\n🎉 SUCCESS! Use '{view_id}' for all downstream analysis")
            print("\nNext steps:")
            print("1. Update cluster analysis to use penalty_analysis_v2")
            print("2. Update financial model to use penalty_analysis_v2")
            print("3. Create dashboards with deduplicated data")
    else:
        print("\nSkipping reload. Current data may have duplicates.")


if __name__ == "__main__":
    main()
