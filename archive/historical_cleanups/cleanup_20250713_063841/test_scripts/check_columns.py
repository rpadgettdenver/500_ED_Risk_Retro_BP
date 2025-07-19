"""
Check column names in BigQuery tables
=====================================
Suggested filename: check_columns.py
Directory location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
USE: Diagnose column names in your BigQuery tables to fix the view creation

Run with: python src/utils/check_columns.py
"""

from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

def check_table_columns():
    """Check column names in all tables"""
    
    client = bigquery.Client(project=PROJECT_ID)
    
    tables = [
        "building_eui_targets",
        "building_zipcode", 
        "epb_stats",
        "geocoded_buildings"
    ]
    
    print("=== CHECKING COLUMN NAMES IN BIGQUERY TABLES ===\n")
    
    for table_name in tables:
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        
        try:
            # Get table schema
            table = client.get_table(table_id)
            
            print(f"\n📊 Table: {table_name}")
            print(f"   Rows: {table.num_rows:,}")
            print("   Columns:")
            
            # List all columns
            for field in table.schema:
                print(f"     - {field.name} ({field.field_type})")
                
            # Also show first few rows to see actual data
            query = f"""
            SELECT * 
            FROM `{table_id}`
            LIMIT 2
            """
            
            df = client.query(query).to_dataframe()
            print("\n   Sample data:")
            print(df.to_string())
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "="*50)
    print("\n💡 Next steps:")
    print("1. Update the view query to use the correct column names (with backticks for spaces)")
    print("2. Look for common columns across tables for joins")
    print("3. Note which columns contain the building ID for linking")


def create_fixed_penalty_view():
    """Create a fixed version of the penalty calculation view"""
    
    client = bigquery.Client(project=PROJECT_ID)
    view_id = f"{PROJECT_ID}.{DATASET_ID}.penalty_calculations_v2"
    
    # This query will use backticks for column names with spaces
    view_query = f"""
    CREATE OR REPLACE VIEW `{view_id}` AS
    WITH building_data AS (
        SELECT 
            -- Use backticks for columns with spaces
            `Building ID` as building_id,
            `Building Name` as building_name,
            `Property Address` as address,
            `Property Type` as property_type,
            
            -- Handle numeric conversions
            CAST(REPLACE(REPLACE(`Gross Floor Area`, ',', ''), ' ', '') AS FLOAT64) as gross_floor_area,
            CAST(`Baseline EUI` AS FLOAT64) as baseline_eui,
            CAST(`Actual EUI` AS FLOAT64) as actual_eui,
            
            -- Target columns - adjust based on actual column names
            CAST(`Target EUI 2024` AS FLOAT64) as target_eui_2024,
            CAST(`Target EUI 2027` AS FLOAT64) as target_eui_2027,
            CAST(`Target EUI 2030` AS FLOAT64) as target_eui_2030
            
        FROM `{PROJECT_ID}.{DATASET_ID}.building_eui_targets`
        WHERE `Actual EUI` IS NOT NULL
    ),
    penalty_calc AS (
        SELECT 
            *,
            
            -- Calculate EUI gaps
            GREATEST(0, actual_eui - target_eui_2024) as eui_gap_2024,
            GREATEST(0, actual_eui - target_eui_2027) as eui_gap_2027,
            GREATEST(0, actual_eui - target_eui_2030) as eui_gap_2030,
            
            -- Calculate penalties
            ROUND(GREATEST(0, actual_eui - target_eui_2024) * gross_floor_area * 0.15, 2) as penalty_2024,
            ROUND(GREATEST(0, actual_eui - target_eui_2027) * gross_floor_area * 0.15, 2) as penalty_2027,
            ROUND(GREATEST(0, actual_eui - target_eui_2030) * gross_floor_area * 0.15, 2) as penalty_2030,
            
            -- Reduction percentages
            ROUND((baseline_eui - target_eui_2030) / NULLIF(baseline_eui, 0) * 100, 1) as percent_reduction_needed
            
        FROM building_data
        WHERE gross_floor_area > 0
    )
    SELECT 
        *,
        penalty_2024 + penalty_2027 + penalty_2030 as total_penalty_exposure,
        
        CASE 
            WHEN penalty_2024 + penalty_2027 + penalty_2030 > 100000 THEN 'HIGH'
            WHEN penalty_2024 + penalty_2027 + penalty_2030 > 50000 THEN 'MEDIUM'
            WHEN penalty_2024 + penalty_2027 + penalty_2030 > 0 THEN 'LOW'
            ELSE 'COMPLIANT'
        END as risk_category,
        
        CURRENT_TIMESTAMP() as calculated_at
        
    FROM penalty_calc
    """
    
    print("\n🔧 Creating fixed penalty calculation view...")
    print("   (This version handles column names with spaces)")
    
    try:
        query_job = client.query(view_query)
        query_job.result()
        print(f"   ✅ Successfully created view: {view_id}")
        
        # Test the view
        test_query = f"""
        SELECT COUNT(*) as total_buildings,
               COUNT(CASE WHEN risk_category = 'HIGH' THEN 1 END) as high_risk
        FROM `{view_id}`
        """
        
        result = client.query(test_query).to_dataframe()
        print(f"   📊 View contains {result['total_buildings'].iloc[0]} buildings")
        print(f"   🚨 High risk buildings: {result['high_risk'].iloc[0]}")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        print("\n   💡 Check the column names above and update the query accordingly")


if __name__ == "__main__":
    # First check what columns we have
    check_table_columns()
    
    # Then try to create a fixed view
    # Uncomment this after checking column names:
    # create_fixed_penalty_view()
