"""
Suggested File Name: check_data_availability.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Check if there's data in the BigQuery tables and views

This script checks multiple tables to understand where data exists.
"""

from google.cloud import bigquery

def check_data_availability(project_id='energize-denver-eaas', dataset_id='energize_denver'):
    """Check data availability across key tables"""
    
    client = bigquery.Client(project=project_id)
    
    tables_to_check = [
        'building_consumption_corrected',
        'building_analysis_v2',
        'opt_in_decision_analysis_v3',
        'opt_in_recommendations_v3',
        # Try some variations
        'opt_in_decision_analysis',
        'opt_in_decision_analysis_v2',
    ]
    
    print("🔍 Checking data availability in BigQuery tables\n")
    
    for table_name in tables_to_check:
        try:
            query = f"""
            SELECT COUNT(*) as row_count
            FROM `{project_id}.{dataset_id}.{table_name}`
            """
            
            result = client.query(query).to_dataframe()
            row_count = result['row_count'].iloc[0]
            
            if row_count > 0:
                print(f"✅ {table_name:<40} {row_count:,} rows")
                
                # Get a sample row to verify columns
                sample_query = f"""
                SELECT *
                FROM `{project_id}.{dataset_id}.{table_name}`
                LIMIT 1
                """
                sample = client.query(sample_query).to_dataframe()
                
                if not sample.empty:
                    print(f"   Sample columns: {', '.join(sample.columns[:5])}...")
            else:
                print(f"⚠️  {table_name:<40} 0 rows (empty)")
                
        except Exception as e:
            print(f"❌ {table_name:<40} Error: {str(e)[:60]}...")
    
    print("\n📋 Summary:")
    print("If opt_in_decision_analysis_v3 is empty, you may need to:")
    print("1. Run fix_42_cap_and_yearwise_exemptions.py again")
    print("2. Check if the view definition is correct")
    print("3. Use a different version of the view (v2 or base)")


if __name__ == "__main__":
    check_data_availability()