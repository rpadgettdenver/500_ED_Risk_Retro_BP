"""
Suggested File Name: load_excel_consumption_data.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Load and explore the Excel file containing actual building consumption data,
     then upload to BigQuery for penalty calculations

This script:
1. Reads the Excel file and explores all sheets
2. Identifies actual consumption data columns
3. Cleans and standardizes the data
4. Uploads to BigQuery as a new table
5. Creates an enhanced analysis view with actual vs target EUI
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.cloud import storage
import os
from datetime import datetime

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"
BUCKET_NAME = "energize-denver-eaas-data"

class ExcelDataLoader:
    """Load and process Excel consumption data for Energize Denver"""
    
    def __init__(self):
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        self.storage_client = storage.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        self.excel_path = "data/raw/Energize Denver Report Request 060225.xlsx"
        
    def explore_excel_file(self):
        """Explore the Excel file to understand its structure"""
        print("=== EXPLORING EXCEL FILE ===\n")
        print(f"Reading: {self.excel_path}")
        
        # Read Excel file
        excel_file = pd.ExcelFile(self.excel_path)
        
        print(f"\nFound {len(excel_file.sheet_names)} sheets:")
        for sheet in excel_file.sheet_names:
            print(f"  - {sheet}")
        
        # Examine each sheet
        all_data = {}
        for sheet_name in excel_file.sheet_names:
            print(f"\n📊 Sheet: '{sheet_name}'")
            df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
            all_data[sheet_name] = df
            
            print(f"   Shape: {df.shape[0]} rows x {df.shape[1]} columns")
            print(f"   Columns: {', '.join(df.columns[:5])}")
            if len(df.columns) > 5:
                print(f"            ... and {len(df.columns) - 5} more columns")
            
            # Check for consumption-related columns
            consumption_cols = [col for col in df.columns if any(
                keyword in col.lower() for keyword in 
                ['eui', 'consumption', 'energy', 'usage', 'actual', 'kwh', 'therm', 'btu']
            )]
            
            if consumption_cols:
                print(f"   🔋 Found energy columns: {', '.join(consumption_cols[:3])}")
                if len(consumption_cols) > 3:
                    print(f"      ... and {len(consumption_cols) - 3} more")
            
            # Check for Building ID column
            id_cols = [col for col in df.columns if 'building' in col.lower() and 'id' in col.lower()]
            if id_cols:
                print(f"   🔑 Building ID column: {id_cols[0]}")
                
        return all_data
    
    def process_consumption_data(self, all_data):
        """Process and standardize consumption data from Excel"""
        print("\n=== PROCESSING CONSUMPTION DATA ===\n")
        
        # Assuming the main data is in the first sheet (adjust if needed)
        main_sheet_name = list(all_data.keys())[0]
        df = all_data[main_sheet_name].copy()
        
        print(f"Processing sheet: '{main_sheet_name}'")
        
        # Standardize column names
        df.columns = [col.strip() for col in df.columns]
        
        # Look for actual EUI columns
        eui_cols = [col for col in df.columns if 'eui' in col.lower()]
        print(f"\nEUI columns found: {eui_cols}")
        
        # Find the most recent actual EUI
        actual_eui_col = None
        for col in eui_cols:
            if any(word in col.lower() for word in ['actual', 'report', '2023', '2024']):
                actual_eui_col = col
                break
        
        if actual_eui_col:
            print(f"✓ Using '{actual_eui_col}' as actual EUI")
        else:
            print("⚠️  No clear actual EUI column found")
            # Let's examine the data more closely
            print("\nFirst few rows to understand the data:")
            print(df.head(3))
        
        # Identify Building ID column
        building_id_col = None
        for col in df.columns:
            if 'building' in col.lower() and 'id' in col.lower():
                building_id_col = col
                break
        
        if not building_id_col:
            print("❌ No Building ID column found!")
            return None
            
        print(f"✓ Building ID column: '{building_id_col}'")
        
        # Create standardized dataframe
        processed_df = pd.DataFrame()
        processed_df['building_id'] = df[building_id_col].astype(str)
        
        # Add available data
        useful_columns = {
            'building_name': ['building name', 'name', 'property name'],
            'address': ['address', 'street address', 'property address'],
            'year_built': ['year built', 'construction year'],
            'owner': ['owner', 'owner name', 'property owner'],
            'property_type': ['property type', 'building type', 'use type'],
            'gross_floor_area': ['gross floor area', 'gross square', 'gsf', 'sqft'],
            'actual_eui': ['actual', 'eui', 'site eui', 'weather normalized']
        }
        
        for new_col, search_terms in useful_columns.items():
            found_col = None
            for col in df.columns:
                if any(term in col.lower() for term in search_terms):
                    found_col = col
                    break
            
            if found_col:
                processed_df[new_col] = df[found_col]
                print(f"✓ Mapped '{found_col}' → '{new_col}'")
        
        # Clean numeric columns
        numeric_cols = ['gross_floor_area', 'actual_eui', 'year_built']
        for col in numeric_cols:
            if col in processed_df.columns:
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
        
        # Ensure building_id is string type
        processed_df['building_id'] = processed_df['building_id'].astype(str)
        
        # Clean string columns - remove any NaN values and convert to string
        string_cols = ['building_name', 'address', 'owner', 'property_type']
        for col in string_cols:
            if col in processed_df.columns:
                processed_df[col] = processed_df[col].fillna('').astype(str)
        
        # Add metadata
        processed_df['source_file'] = 'Energize Denver Report Request 060225.xlsx'
        processed_df['load_timestamp'] = datetime.now().isoformat()  # Use ISO format for timestamp
        
        # Summary statistics
        print(f"\n📊 Processed Data Summary:")
        print(f"   Total buildings: {len(processed_df)}")
        if 'actual_eui' in processed_df.columns:
            print(f"   Buildings with actual EUI: {processed_df['actual_eui'].notna().sum()}")
            print(f"   Average actual EUI: {processed_df['actual_eui'].mean():.1f}")
        
        return processed_df
    
    def upload_to_bigquery(self, df, table_name='building_consumption'):
        """Upload processed data to BigQuery"""
        table_id = f"{self.dataset_ref}.{table_name}"
        
        print(f"\n=== UPLOADING TO BIGQUERY ===")
        print(f"Target table: {table_id}")
        
        # First, let's check for problematic columns
        print("\nData types before upload:")
        for col in df.columns:
            print(f"  {col}: {df[col].dtype}")
        
        # Create a copy to avoid modifying the original
        upload_df = df.copy()
        
        # Ensure all object columns are strings
        for col in upload_df.select_dtypes(include=['object']).columns:
            upload_df[col] = upload_df[col].astype(str)
        
        # Configure job with explicit schema
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True,
            create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED
        )
        
        # Upload
        try:
            job = self.bq_client.load_table_from_dataframe(
                upload_df, table_id, job_config=job_config
            )
            job.result()  # Wait for completion
        except Exception as e:
            print(f"\nError during upload: {str(e)}")
            print("\nTrying alternative upload method...")
            
            # Alternative: Save to CSV and upload
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                upload_df.to_csv(tmp_file.name, index=False)
                tmp_path = tmp_file.name
            
            # Upload CSV file
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                skip_leading_rows=1,
                autodetect=True,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
            )
            
            with open(tmp_path, 'rb') as csv_file:
                job = self.bq_client.load_table_from_file(
                    csv_file, table_id, job_config=job_config
                )
                job.result()
            
            # Clean up temp file
            os.unlink(tmp_path)
        
        # Verify
        table = self.bq_client.get_table(table_id)
        print(f"✓ Uploaded {table.num_rows} rows to {table_id}")
        
        return table_id
    
    def create_penalty_view(self):
        """Create a view that calculates penalties based on actual vs target EUI"""
        view_id = f"{self.dataset_ref}.penalty_analysis"
        
        query = f"""
        CREATE OR REPLACE VIEW `{view_id}` AS
        WITH combined_data AS (
            SELECT 
                t.*,
                c.actual_eui,
                c.building_name as consumption_building_name,
                c.address as consumption_address,
                c.owner,
                
                -- Calculate gaps
                c.actual_eui - t.first_interim_target as interim_gap,
                c.actual_eui - COALESCE(t.adjusted_final_target, t.original_final_target) as final_gap,
                
                -- Determine compliance path (opt-in if over 2024 target)
                CASE 
                    WHEN c.actual_eui > t.first_interim_target THEN 'Opt-in (2028/2032)'
                    ELSE 'Default (2024/2030)'
                END as compliance_path
                
            FROM `{self.dataset_ref}.building_analysis_v2` t
            LEFT JOIN `{self.dataset_ref}.building_consumption` c
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
        
        print("\n=== CREATING PENALTY ANALYSIS VIEW ===")
        
        try:
            self.bq_client.query(query).result()
            print(f"✓ Created penalty analysis view: {view_id}")
            
            # Get summary
            summary_query = f"""
            SELECT 
                COUNT(*) as total_buildings,
                COUNT(actual_eui) as buildings_with_consumption,
                COUNT(CASE WHEN risk_category = 'High Risk' THEN 1 END) as high_risk_count,
                ROUND(SUM(annual_penalty_2024), 0) as total_penalty_exposure_2024,
                ROUND(AVG(CASE WHEN annual_penalty_2024 > 0 THEN annual_penalty_2024 END), 0) as avg_penalty_2024
            FROM `{view_id}`
            """
            
            results = self.bq_client.query(summary_query).to_dataframe()
            
            print("\n📊 Penalty Analysis Summary:")
            print(f"   Buildings with consumption data: {results['buildings_with_consumption'].iloc[0]:,}")
            print(f"   High risk buildings: {results['high_risk_count'].iloc[0]:,}")
            print(f"   Total 2024 penalty exposure: ${results['total_penalty_exposure_2024'].iloc[0]:,.0f}")
            print(f"   Average penalty (non-compliant): ${results['avg_penalty_2024'].iloc[0]:,.0f}")
            
        except Exception as e:
            print(f"❌ Error creating penalty view: {str(e)}")
    
    def run_full_pipeline(self):
        """Run the complete data loading and analysis pipeline"""
        
        # Step 1: Explore Excel file
        all_data = self.explore_excel_file()
        
        if not all_data:
            print("❌ Failed to read Excel file")
            return
        
        # Step 2: Process consumption data
        processed_df = self.process_consumption_data(all_data)
        
        if processed_df is None or processed_df.empty:
            print("❌ No data to process")
            return
            
        # Step 3: Upload to BigQuery
        table_id = self.upload_to_bigquery(processed_df)
        
        # Step 4: Create penalty analysis view
        self.create_penalty_view()
        
        print("\n✅ Pipeline complete!")
        print(f"\nNext steps:")
        print("1. Query the penalty_analysis view for specific insights")
        print("2. Build clustering analysis for DER opportunities")
        print("3. Create financial models for retrofit ROI")
        print("4. Design Looker Studio dashboards")


def main():
    """Main execution"""
    loader = ExcelDataLoader()
    
    try:
        loader.run_full_pipeline()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
