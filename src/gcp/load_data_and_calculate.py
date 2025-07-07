"""
BigQuery Data Loader and Penalty Calculator for Energize Denver - FIXED V2
===========================================================================
This version correctly handles the actual table schemas

Usage:
    python src/gcp/load_data_and_calculate.py
"""

import os
from google.cloud import bigquery
from google.cloud import storage
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"
BUCKET_NAME = "energize-denver-eaas-data"

class EnergizeDenverDataLoader:
    """Load and process Energize Denver compliance data"""
    
    def __init__(self):
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        self.storage_client = storage.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        
    def load_csv_to_bigquery(self, gcs_path, table_name, schema=None):
        """Load a CSV file from Cloud Storage to BigQuery"""
        
        table_id = f"{self.dataset_ref}.{table_name}"
        
        # Configure load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=True,  # Let BigQuery detect schema
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE  # Overwrite table
        )
        
        # If custom schema provided, use it
        if schema:
            job_config.schema = schema
            job_config.autodetect = False
        
        print(f"Loading {gcs_path} to {table_id}...")
        
        # Load data
        load_job = self.bq_client.load_table_from_uri(
            gcs_path, table_id, job_config=job_config
        )
        
        # Wait for job to complete
        load_job.result()
        
        # Get table info
        table = self.bq_client.get_table(table_id)
        print(f"✓ Loaded {table.num_rows} rows to {table_id}")
        
        return table_id
    
    def load_all_data(self):
        """Load all CSV files to BigQuery"""
        
        print("=== LOADING DATA TO BIGQUERY ===\n")
        
        # Define the files to load and their table names
        files_to_load = [
            ("gs://energize-denver-eaas-data/raw-data/Building_EUI_Targets.csv", "building_eui_targets"),
            ("gs://energize-denver-eaas-data/raw-data/building_zipcode_lookup.csv", "building_zipcode"),
            ("gs://energize-denver-eaas-data/raw-data/CopyofWeeklyEPBStatsReport Report.csv", "epb_stats"),
            ("gs://energize-denver-eaas-data/raw-data/geocoded_buildings_final.csv", "geocoded_buildings")
        ]
        
        loaded_tables = []
        for gcs_path, table_name in files_to_load:
            try:
                table_id = self.load_csv_to_bigquery(gcs_path, table_name)
                loaded_tables.append(table_id)
            except Exception as e:
                print(f"⚠️  Error loading {gcs_path}: {str(e)}")
        
        print(f"\n✓ Successfully loaded {len(loaded_tables)} tables")
        return loaded_tables
    
    def check_all_tables(self):
        """Check what columns we have in all tables"""
        
        print("\n=== CHECKING ALL TABLE SCHEMAS ===\n")
        
        tables = ['building_eui_targets', 'building_zipcode', 'epb_stats', 'geocoded_buildings']
        
        for table_name in tables:
            query = f"""
            SELECT column_name, data_type
            FROM `{self.dataset_ref}.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
            """
            
            df = self.bq_client.query(query).to_dataframe()
            print(f"\n📊 Table: {table_name}")
            print(df.to_string(index=False))
            
        # Also check building_zipcode for additional data
        print("\n\nSample from building_zipcode (might have names/addresses):")
        query = f"""
        SELECT *
        FROM `{self.dataset_ref}.building_zipcode`
        LIMIT 3
        """
        df = self.bq_client.query(query).to_dataframe()
        print(df.head())
    
    def create_analysis_view_v2(self):
        """Create an analysis view based on actual available data"""
        
        view_id = f"{self.dataset_ref}.building_analysis_v2"
        
        # First, let's check what's in building_zipcode
        self.check_all_tables()
        
        # Create a simpler view that works with available data
        view_query = f"""
        CREATE OR REPLACE VIEW `{view_id}` AS
        WITH target_data AS (
            SELECT 
                CAST(`Building ID` AS STRING) as building_id,
                `Master Property Type` as property_type,
                `Master Sq Ft` as gross_floor_area,
                `Applied for Target Adjustment` as has_target_adjustment,
                `Electrification Credit Applied` as has_electrification_credit,
                `Baseline EUI` as baseline_eui,
                `First Interim Target EUI` as first_interim_target,
                `Second Interim Target EUI` as second_interim_target,
                `Original Final Target EUI` as original_final_target,
                `Adjusted Final Target EUI` as adjusted_final_target,
                `Baseline Year` as baseline_year,
                `First Interim Target Year` as first_target_year,
                `Second Interim Target Year` as second_target_year
            FROM `{self.dataset_ref}.building_eui_targets`
        ),
        location_data AS (
            SELECT 
                CAST(Building_ID AS STRING) as building_id,
                latitude,
                longitude
            FROM `{self.dataset_ref}.geocoded_buildings`
            WHERE geocoded = TRUE
        ),
        epb_data AS (
            SELECT DISTINCT
                CAST(`Building ID` AS STRING) as building_id,
                1 as is_epb
            FROM `{self.dataset_ref}.epb_stats`
            WHERE `Building ID` IS NOT NULL
        ),
        zipcode_data AS (
            SELECT 
                CAST(`Building ID` AS STRING) as building_id,
                `Zipcode` as zipcode
            FROM `{self.dataset_ref}.building_zipcode`
        ),
        name_data AS (
            -- Get building names from EPB stats table
            SELECT 
                CAST(`Building ID` AS STRING) as building_id,
                `Building Name` as building_name,
                `Building Address` as property_address
            FROM `{self.dataset_ref}.epb_stats`
        )
        SELECT 
            t.*,
            n.building_name,
            n.property_address as address,
            z.zipcode,
            l.latitude,
            l.longitude,
            COALESCE(e.is_epb, 0) as is_epb,
            
            -- Calculate reduction needed from baseline
            ROUND((t.baseline_eui - COALESCE(t.adjusted_final_target, t.original_final_target)) / 
                  NULLIF(t.baseline_eui, 0) * 100, 1) as percent_reduction_needed,
            
            -- Flag high reduction buildings
            CASE 
                WHEN (t.baseline_eui - COALESCE(t.adjusted_final_target, t.original_final_target)) / 
                     NULLIF(t.baseline_eui, 0) > 0.30 THEN 'HIGH'
                WHEN (t.baseline_eui - COALESCE(t.adjusted_final_target, t.original_final_target)) / 
                     NULLIF(t.baseline_eui, 0) > 0.20 THEN 'MEDIUM'
                ELSE 'LOW'
            END as reduction_difficulty
            
        FROM target_data t
        LEFT JOIN zipcode_data z ON t.building_id = z.building_id
        LEFT JOIN name_data n ON t.building_id = n.building_id
        LEFT JOIN location_data l ON t.building_id = l.building_id
        LEFT JOIN epb_data e ON t.building_id = e.building_id
        WHERE t.baseline_eui IS NOT NULL
            AND t.gross_floor_area > 0
        """
        
        print("\nCreating building analysis view V2...")
        
        try:
            query_job = self.bq_client.query(view_query)
            query_job.result()
            print(f"✓ Created view: {view_id}")
            
            # Get summary stats
            summary_query = f"""
            SELECT 
                COUNT(*) as total_buildings,
                COUNT(CASE WHEN is_epb = 1 THEN 1 END) as epb_buildings,
                COUNT(CASE WHEN building_name IS NOT NULL THEN 1 END) as buildings_with_names,
                COUNT(CASE WHEN latitude IS NOT NULL THEN 1 END) as geocoded_buildings,
                ROUND(AVG(percent_reduction_needed), 1) as avg_reduction_needed,
                COUNT(CASE WHEN reduction_difficulty = 'HIGH' THEN 1 END) as high_difficulty_count
            FROM `{view_id}`
            """
            
            results = self.bq_client.query(summary_query).to_dataframe()
            
            print("\n📊 Summary Statistics:")
            print(f"   Total buildings with targets: {results['total_buildings'].iloc[0]:,}")
            print(f"   Buildings with names: {results['buildings_with_names'].iloc[0]:,}")
            print(f"   Geocoded buildings: {results['geocoded_buildings'].iloc[0]:,}")
            print(f"   EPB buildings: {results['epb_buildings'].iloc[0]:,}")
            print(f"   Average reduction needed: {results['avg_reduction_needed'].iloc[0]}%")
            print(f"   High difficulty reductions: {results['high_difficulty_count'].iloc[0]:,}")
            
            return view_id
            
        except Exception as e:
            print(f"❌ Error creating view: {str(e)}")
            return None
    
    def generate_summary_report(self, view_id):
        """Generate a summary report of the analysis"""
        
        if not view_id:
            print("⚠️  No view available for analysis")
            return
            
        print("\n=== ENERGIZE DENVER COMPLIANCE ANALYSIS ===")
        print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Query the analysis view
        query = f"""
        SELECT 
            property_type,
            COUNT(*) as building_count,
            ROUND(AVG(gross_floor_area), 0) as avg_sqft,
            ROUND(AVG(baseline_eui), 1) as avg_baseline_eui,
            ROUND(AVG(percent_reduction_needed), 1) as avg_reduction_pct,
            COUNT(CASE WHEN is_epb = 1 THEN 1 END) as epb_count,
            COUNT(CASE WHEN reduction_difficulty = 'HIGH' THEN 1 END) as high_difficulty
        FROM `{view_id}`
        GROUP BY property_type
        ORDER BY building_count DESC
        LIMIT 10
        """
        
        results = self.bq_client.query(query).to_dataframe()
        
        print("TOP PROPERTY TYPES BY BUILDING COUNT:")
        print("-" * 100)
        
        for idx, row in results.iterrows():
            print(f"{row['property_type']:<30} | "
                  f"{row['building_count']:>5} buildings | "
                  f"{row['avg_sqft']:>10,.0f} avg sqft | "
                  f"{row['avg_reduction_pct']:>5.1f}% reduction | "
                  f"{row['high_difficulty']:>3} difficult")
        
        # Get some sample high-risk buildings
        print("\n\nSAMPLE HIGH-RISK BUILDINGS (Need >30% reduction):")
        print("-" * 100)
        
        query2 = f"""
        SELECT 
            building_name,
            address,
            property_type,
            ROUND(gross_floor_area, 0) as sqft,
            ROUND(baseline_eui, 1) as baseline_eui,
            ROUND(COALESCE(adjusted_final_target, original_final_target), 1) as target_eui,
            ROUND(percent_reduction_needed, 1) as reduction_pct,
            is_epb
        FROM `{view_id}`
        WHERE reduction_difficulty = 'HIGH'
            AND building_name IS NOT NULL
        ORDER BY percent_reduction_needed DESC
        LIMIT 10
        """
        
        high_risk = self.bq_client.query(query2).to_dataframe()
        
        if not high_risk.empty:
            for idx, row in high_risk.iterrows():
                name = row['building_name'][:40] if row['building_name'] else 'Unknown'
                print(f"{name:<40} | "
                      f"{row['property_type']:<20} | "
                      f"{row['sqft']:>10,.0f} sqft | "
                      f"{row['reduction_pct']:>5.1f}% | "
                      f"{'EPB' if row['is_epb'] == 1 else ''}")
        
        print("\n✓ Analysis complete!")
        print(f"  View your data at: https://console.cloud.google.com/bigquery?project={PROJECT_ID}")
        print("\n⚠️  Note: This analysis is based on target data only.")
        print("    To calculate actual penalties, we need current EUI data.")
        print("    Consider loading the 'Energize Denver Report Request 060225.xlsx' file")
        print("    which may contain actual consumption data.")


def main():
    """Main execution function"""
    
    # Initialize loader
    loader = EnergizeDenverDataLoader()
    
    try:
        # Step 1: Check what data we have in all tables
        # This will show us the schema of building_zipcode
        
        # Step 2: Create analysis view based on available data
        view_id = loader.create_analysis_view_v2()
        
        # Step 3: Generate summary report
        if view_id:
            loader.generate_summary_report(view_id)
        
        # Provide next steps
        print("\n=== NEXT STEPS ===")
        print("1. Load the Excel file 'Energize Denver Report Request 060225.xlsx'")
        print("   - This likely contains actual EUI data needed for penalties")
        print("2. Create a penalty calculation view once we have actual consumption")
        print("3. Build clustering analysis for thermal network opportunities")
        print("4. Create Looker Studio dashboard for visualizations")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting tips:")
        print("1. Ensure you're authenticated: gcloud auth application-default login")
        print("2. Check your project ID is correct")
        print("3. Verify your CSV files are in Cloud Storage")


if __name__ == "__main__":
    main()
