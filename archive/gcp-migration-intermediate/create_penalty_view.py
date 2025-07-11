"""
Suggested File Name: create_penalty_view.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Create the penalty analysis view that combines target and consumption data

This script creates the penalty_analysis view needed by the clustering and financial models.
"""

from google.cloud import bigquery

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

def create_penalty_analysis_view():
    """Create the penalty analysis view"""
    
    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    view_id = f"{dataset_ref}.penalty_analysis"
    
    # First, let's check what tables we have
    print("=== CHECKING AVAILABLE TABLES ===")
    
    query = f"""
    SELECT table_name 
    FROM `{dataset_ref}.INFORMATION_SCHEMA.TABLES`
    ORDER BY table_name
    """
    
    tables = client.query(query).to_dataframe()
    print("\nAvailable tables:")
    for table in tables['table_name']:
        print(f"  - {table}")
    
    # Now create the penalty view
    print("\n=== CREATING PENALTY ANALYSIS VIEW ===")
    
    query = f"""
    CREATE OR REPLACE VIEW `{view_id}` AS
    WITH combined_data AS (
        SELECT 
            t.*,
            c.actual_eui,
            c.building_name as consumption_building_name,
            -- c.address as consumption_address,  -- Column doesn't exist in consumption table
            -- c.owner,  -- Column doesn't exist in consumption table
            
            -- Calculate gaps
            c.actual_eui - t.first_interim_target as interim_gap,
            c.actual_eui - COALESCE(t.adjusted_final_target, t.original_final_target) as final_gap,
            
            -- Determine compliance path (opt-in if over 2024 target)
            CASE 
                WHEN c.actual_eui > t.first_interim_target THEN 'Opt-in (2028/2032)'
                ELSE 'Default (2024/2030)'
            END as compliance_path
            
        FROM `{dataset_ref}.building_analysis_v2` t
        LEFT JOIN `{dataset_ref}.building_consumption` c
            ON t.building_id = c.building_id
    )
    SELECT 
        *,
        -- Calculate penalties
        CASE 
            WHEN actual_eui IS NULL THEN NULL
            WHEN compliance_path = 'Default (2024/2030)' THEN
                GREATEST(0, interim_gap * gross_floor_area * 0.15)
            ELSE
                GREATEST(0, interim_gap * gross_floor_area * 0.23)
        END as annual_penalty_2024,
        
        CASE 
            WHEN actual_eui IS NULL THEN NULL
            WHEN compliance_path = 'Default (2024/2030)' THEN
                GREATEST(0, final_gap * gross_floor_area * 0.15)
            ELSE
                GREATEST(0, final_gap * gross_floor_area * 0.23)
        END as annual_penalty_2030,
        
        -- Risk categorization
        CASE 
            WHEN actual_eui IS NULL THEN 'Unknown'
            WHEN interim_gap <= 0 THEN 'Compliant'
            WHEN interim_gap * gross_floor_area * 0.15 > 50000 THEN 'High Risk'
            WHEN interim_gap * gross_floor_area * 0.15 > 10000 THEN 'Medium Risk'
            ELSE 'Low Risk'
        END as risk_category
        
    FROM combined_data
    """
    
    try:
        client.query(query).result()
        print(f"✓ Created penalty analysis view: {view_id}")
        
        # Get summary
        summary_query = f"""
        SELECT 
            COUNT(*) as total_buildings,
            COUNT(actual_eui) as buildings_with_consumption,
            COUNT(CASE WHEN risk_category = 'High Risk' THEN 1 END) as high_risk_count,
            COUNT(CASE WHEN risk_category = 'Compliant' THEN 1 END) as compliant_count,
            ROUND(SUM(annual_penalty_2024), 0) as total_penalty_exposure_2024,
            ROUND(AVG(CASE WHEN annual_penalty_2024 > 0 THEN annual_penalty_2024 END), 0) as avg_penalty_2024
        FROM `{view_id}`
        """
        
        results = client.query(summary_query).to_dataframe()
        
        print("\n📊 Penalty Analysis Summary:")
        print(f"   Total buildings: {results['total_buildings'].iloc[0]:,}")
        print(f"   Buildings with consumption data: {results['buildings_with_consumption'].iloc[0]:,}")
        print(f"   Compliant buildings: {results['compliant_count'].iloc[0]:,}")
        print(f"   High risk buildings: {results['high_risk_count'].iloc[0]:,}")
        print(f"   Total 2024 penalty exposure: ${results['total_penalty_exposure_2024'].iloc[0]:,.0f}")
        print(f"   Average penalty (non-compliant): ${results['avg_penalty_2024'].iloc[0]:,.0f}")
        
        # Top 10 high-risk buildings
        print("\n\nTop 10 High-Risk Buildings:")
        print("-" * 100)
        
        high_risk_query = f"""
        SELECT 
            building_id,
            COALESCE(building_name, consumption_building_name) as building_name,
            property_type,
            ROUND(gross_floor_area, 0) as sqft,
            ROUND(actual_eui, 1) as actual_eui,
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
            name = row['building_name'][:35] if row['building_name'] else f"Building {row['building_id']}"
            print(f"{name:<35} | {row['property_type']:<20} | {row['sqft']:>10,.0f} sqft | "
                  f"EUI: {row['actual_eui']:>5.0f} → {row['target_eui']:>5.0f} | "
                  f"${row['penalty_2024']:>10,.0f}")
        
        print("\n✅ Penalty analysis view ready for use!")
        
    except Exception as e:
        print(f"❌ Error creating penalty view: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if building_analysis_v2 view exists")
        print("2. Check if building_consumption table was created")
        print("3. Verify column names match between tables")


if __name__ == "__main__":
    create_penalty_analysis_view()
