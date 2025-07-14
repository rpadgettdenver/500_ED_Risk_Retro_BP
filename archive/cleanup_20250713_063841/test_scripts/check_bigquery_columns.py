"""
Suggested File Name: check_bigquery_columns.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Quick diagnostic script to check actual column names in BigQuery tables

This script helps identify the exact column names in your BigQuery tables
to avoid naming mismatches.
"""

from google.cloud import bigquery

def check_table_schema(project_id='energize-denver-eaas', dataset_id='energize_denver', table_name='opt_in_decision_analysis_v3'):
    """Check the schema of a BigQuery table"""
    
    client = bigquery.Client(project=project_id)
    
    # Get table reference
    table_ref = f"{project_id}.{dataset_id}.{table_name}"
    
    try:
        # Get table schema
        table = client.get_table(table_ref)
        
        print(f"\n📊 Schema for table: {table_name}")
        print("=" * 80)
        print(f"{'Column Name':<40} {'Type':<15} {'Mode':<10}")
        print("-" * 80)
        
        for field in table.schema:
            print(f"{field.name:<40} {field.field_type:<15} {field.mode:<10}")
            
        print(f"\nTotal columns: {len(table.schema)}")
        print(f"Total rows: {table.num_rows:,}")
        
        # Also run a quick query to see actual column names
        print("\n🔍 Sample data (first row):")
        query = f"SELECT * FROM `{table_ref}` LIMIT 1"
        result = client.query(query).to_dataframe()
        
        if not result.empty:
            print("\nColumn names found in data:")
            for col in result.columns:
                print(f"  - {col}")
                
    except Exception as e:
        print(f"❌ Error accessing table: {e}")
        
        # Try to get column names from a simple query
        print("\n🔄 Attempting to get columns from query...")
        try:
            query = f"SELECT * FROM `{project_id}.{dataset_id}.{table_name}` LIMIT 0"
            result = client.query(query).to_dataframe()
            print("\nColumn names found:")
            for col in result.columns:
                print(f"  - {col}")
        except Exception as e2:
            print(f"❌ Could not retrieve columns: {e2}")


def check_all_key_tables():
    """Check schemas for all key tables in the project"""
    
    tables = [
        'building_consumption_corrected',
        'building_analysis_v2',
        'opt_in_decision_analysis_v3',
        'opt_in_recommendations_v3'
    ]
    
    for table in tables:
        check_table_schema(table_name=table)
        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    print("🔍 BigQuery Column Name Checker")
    print("This will help identify the correct column names in your tables\n")
    
    # Check the main analysis view
    check_table_schema()
    
    # Uncomment to check all tables:
    # check_all_key_tables()