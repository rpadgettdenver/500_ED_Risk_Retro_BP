"""
Suggested File Name: investigate_bigquery_schema.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Investigate BigQuery table schemas to understand column names and structure

This script queries the actual schema of BigQuery tables to help fix the view regeneration.
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"


def investigate_schemas():
    """Investigate the schema of key BigQuery tables"""
    
    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    
    print("=" * 80)
    print("BIGQUERY SCHEMA INVESTIGATION")
    print("=" * 80)
    print(f"Dataset: {dataset_ref}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Tables to investigate
    tables_to_check = [
        'building_analysis_v2',
        'building_consumption_corrected',
        'building_targets',
        'building_compliance_analysis',
        'energize_denver_covered_buildings'
    ]
    
    for table_name in tables_to_check:
        print(f"\n\n{'='*60}")
        print(f"TABLE: {table_name}")
        print(f"{'='*60}")
        
        try:
            # Get table reference
            table_ref = f"{dataset_ref}.{table_name}"
            table = client.get_table(table_ref)
            
            print(f"Description: {table.description or 'No description'}")
            print(f"Row count: {table.num_rows:,}")
            print(f"Created: {table.created}")
            print(f"Modified: {table.modified}")
            
            print(f"\nSCHEMA ({len(table.schema)} columns):")
            print("-" * 60)
            
            # Print schema
            for field in table.schema:
                print(f"  {field.name:<40} {field.field_type:<15} {field.mode}")
                
            # For building_analysis_v2, look for year-related columns
            if table_name == 'building_analysis_v2':
                print("\n🔍 LOOKING FOR YEAR-RELATED COLUMNS:")
                year_columns = [field.name for field in table.schema if 'year' in field.name.lower()]
                interim_columns = [field.name for field in table.schema if 'interim' in field.name.lower()]
                
                print(f"Year columns found: {year_columns}")
                print(f"Interim columns found: {interim_columns}")
                
                # Sample data
                print("\n📊 SAMPLE DATA (first 5 rows):")
                query = f"""
                SELECT *
                FROM `{table_ref}`
                LIMIT 5
                """
                df = client.query(query).to_dataframe()
                
                # Show columns related to targets and years
                relevant_cols = [col for col in df.columns if any(term in col.lower() for term in ['year', 'interim', 'target', 'building_id'])]
                if relevant_cols:
                    print(df[relevant_cols].to_string())
                
        except Exception as e:
            print(f"❌ Error accessing table: {str(e)}")
    
    # Look for views that might have the data we need
    print(f"\n\n{'='*60}")
    print("SEARCHING FOR VIEWS WITH TARGET YEAR DATA")
    print(f"{'='*60}")
    
    query = """
    SELECT table_name, table_type
    FROM `energize-denver-eaas.energize_denver.INFORMATION_SCHEMA.TABLES`
    WHERE table_type = 'VIEW'
    AND (
        LOWER(table_name) LIKE '%target%'
        OR LOWER(table_name) LIKE '%analysis%'
        OR LOWER(table_name) LIKE '%compliance%'
    )
    """
    
    try:
        views_df = client.query(query).to_dataframe()
        print("\nViews found:")
        for _, row in views_df.iterrows():
            print(f"  - {row['table_name']}")
    except Exception as e:
        print(f"Error querying views: {str(e)}")
    
    # Check specific columns we need
    print(f"\n\n{'='*60}")
    print("CHECKING FOR REQUIRED COLUMNS")
    print(f"{'='*60}")
    
    # Try to find where first_interim_year and second_interim_year might be
    search_query = f"""
    WITH column_search AS (
        SELECT 
            table_name,
            column_name
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE column_name IN ('first_interim_year', 'second_interim_year', 
                             'First Interim Target Year', 'Second Interim Target Year',
                             'first_interim_target_year', 'second_interim_target_year')
    )
    SELECT * FROM column_search
    """
    
    try:
        search_results = client.query(search_query).to_dataframe()
        if not search_results.empty:
            print("\n✅ Found target year columns in these tables:")
            print(search_results.to_string())
        else:
            print("\n⚠️  Target year columns not found with exact names")
            print("Searching for similar columns...")
            
            # Broader search
            fuzzy_query = f"""
            SELECT 
                table_name,
                column_name
            FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
            WHERE (
                LOWER(column_name) LIKE '%interim%year%'
                OR LOWER(column_name) LIKE '%target%year%'
            )
            AND table_name IN ('building_analysis_v2', 'building_targets', 
                              'energize_denver_covered_buildings', 'building_compliance_analysis')
            ORDER BY table_name, column_name
            """
            
            fuzzy_results = client.query(fuzzy_query).to_dataframe()
            if not fuzzy_results.empty:
                print("\nSimilar columns found:")
                for table, group in fuzzy_results.groupby('table_name'):
                    print(f"\n  Table: {table}")
                    for _, row in group.iterrows():
                        print(f"    - {row['column_name']}")
    
    except Exception as e:
        print(f"Error searching for columns: {str(e)}")
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    investigate_schemas()
