"""
Suggested File Name: check_consumption_schema.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Check the actual columns in the building_consumption table to fix the penalty view

This script examines the schema to see what columns are actually available.
"""

from google.cloud import bigquery

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

def check_table_schema():
    """Check the schema of building_consumption table"""
    
    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    
    print("=== CHECKING BUILDING_CONSUMPTION SCHEMA ===\n")
    
    # Get table schema
    table_ref = f"{dataset_ref}.building_consumption"
    table = client.get_table(table_ref)
    
    print(f"Table: {table_ref}")
    print(f"Total rows: {table.num_rows:,}")
    print("\nColumns:")
    print("-" * 50)
    
    for field in table.schema:
        print(f"{field.name:<30} {field.field_type}")
    
    # Also check a sample of data
    print("\n\n=== SAMPLE DATA ===")
    query = f"""
    SELECT *
    FROM `{table_ref}`
    LIMIT 3
    """
    
    sample_df = client.query(query).to_dataframe()
    print(sample_df)
    
    # Check what columns we actually have that might be useful
    print("\n\n=== AVAILABLE COLUMNS FOR PENALTY VIEW ===")
    print("Columns we can use:")
    for col in sample_df.columns:
        print(f"  - {col}")


if __name__ == "__main__":
    check_table_schema()
