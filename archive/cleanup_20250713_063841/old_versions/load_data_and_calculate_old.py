"""
BigQuery Data Loader and Penalty Calculator for Energize Denver
===============================================================
Suggested filename: load_data_and_calculate.py
Directory location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/
USE: This script loads your CSV files into BigQuery and runs initial penalty calculations

Requirements:
    pip install google-cloud-bigquery google-cloud-storage pandas numpy

Run with:
    python load_data_and_calculate.py
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
    
    def create_penalty_calculation_view(self):
        """Create a view that calculates penalties for all buildings"""
        
        view_id = f"{self.dataset_ref}.penalty_calculations"
        
        view_query = f"""
        CREATE OR REPLACE VIEW `{view_id}` AS
        WITH building_data AS (
            SELECT 
                -- Handle different possible column names for building ID
                COALESCE(
                    CAST(Building_ID AS STRING),
                    CAST(building_id AS STRING),
                    CAST(BuildingID AS STRING)
                ) as building_id,
                
                -- Building details
                COALESCE(Building_Name, building_name, Property_Name) as building_name,
                COALESCE(Property_Address, Address, property_address) as address,
                COALESCE(Property_Type, property_type, Building_Type) as property_type,
                
                -- Size and EUI data - handle different column names and convert to numeric
                CAST(REPLACE(REPLACE(COALESCE(Gross_Floor_Area, GFA, Square_Footage), ',', ''), ' ', '') AS FLOAT64) as gross_floor_area,
                CAST(COALESCE(Baseline_EUI, baseline_eui) AS FLOAT64) as baseline_eui,
                CAST(COALESCE(Actual_EUI, actual_eui, Current_EUI) AS FLOAT64) as actual_eui,
                
                -- Targets - these might have different column names
                CAST(COALESCE(Target_EUI_2024, target_2024) AS FLOAT64) as target_eui_2024,
                CAST(COALESCE(Target_EUI_2027, target_2027) AS FLOAT64) as target_eui_2027,
                CAST(COALESCE(Target_EUI_2030, target_2030, Final_Target) AS FLOAT64) as target_eui_2030
                
            FROM `{self.dataset_ref}.building_eui_targets`
        ),
        penalty_calc AS (
            SELECT 
                *,
                
                -- Calculate EUI gaps (positive means over target)
                GREATEST(0, actual_eui - target_eui_2024) as eui_gap_2024,
                GREATEST(0, actual_eui - target_eui_2027) as eui_gap_2027,
                GREATEST(0, actual_eui - target_eui_2030) as eui_gap_2030,
                
                -- Calculate annual penalties ($0.15 per kBtu over target)
                ROUND(GREATEST(0, actual_eui - target_eui_2024) * gross_floor_area * 0.15, 2) as penalty_2024,
                ROUND(GREATEST(0, actual_eui - target_eui_2027) * gross_floor_area * 0.15, 2) as penalty_2027,
                ROUND(GREATEST(0, actual_eui - target_eui_2030) * gross_floor_area * 0.15, 2) as penalty_2030,
                
                -- Calculate reduction needed
                ROUND((baseline_eui - target_eui_2030) / baseline_eui * 100, 1) as percent_reduction_needed,
                ROUND((actual_eui - target_eui_2030) / actual_eui * 100, 1) as percent_reduction_from_current
                
            FROM building_data
            WHERE actual_eui IS NOT NULL 
                AND gross_floor_area IS NOT NULL
                AND gross_floor_area > 0
        )
        SELECT 
            *,
            -- Total penalty exposure (sum of all years)
            penalty_2024 + penalty_2027 + penalty_2030 as total_penalty_exposure,
            
            -- Risk categorization
            CASE 
                WHEN penalty_2024 + penalty_2027 + penalty_2030 > 100000 THEN 'HIGH'
                WHEN penalty_2024 + penalty_2027 + penalty_2030 > 50000 THEN 'MEDIUM'
                WHEN penalty_2024 + penalty_2027 + penalty_2030 > 0 THEN 'LOW'
                ELSE 'COMPLIANT'
            END as risk_category,
            
            -- Compliance status
            CASE
                WHEN actual_eui <= target_eui_2024 THEN 'COMPLIANT'
                ELSE 'NON-COMPLIANT'
            END as compliance_2024,
            
            -- Add timestamp
            CURRENT_TIMESTAMP() as calculated_at
            
        FROM penalty_calc
        """
        
        print("\nCreating penalty calculation view...")
        
        # Execute the query
        query_job = self.bq_client.query(view_query)
        query_job.result()
        
        print(f"✓ Created view: {view_id}")
        
        return view_id
    
    def get_summary_statistics(self):
        """Get summary statistics from the penalty calculations"""
        
        query = f"""
        SELECT 
            COUNT(*) as total_buildings,
            COUNT(CASE WHEN risk_category = 'HIGH' THEN 1 END) as high_risk_buildings,
            COUNT(CASE WHEN risk_category = 'MEDIUM' THEN 1 END) as medium_risk_buildings,
            COUNT(CASE WHEN risk_category = 'LOW' THEN 1 END) as low_risk_buildings,
            COUNT(CASE WHEN risk_category = 'COMPLIANT' THEN 1 END) as compliant_buildings,
            
            ROUND(SUM(total_penalty_exposure), 2) as total_penalty_exposure,
            ROUND(AVG(total_penalty_exposure), 2) as avg_penalty_exposure,
            ROUND(MAX(total_penalty_exposure), 2) as max_penalty_exposure,
            
            ROUND(SUM(gross_floor_area), 0) as total_square_feet,
            ROUND(AVG(percent_reduction_needed), 1) as avg_reduction_needed
            
        FROM `{self.dataset_ref}.penalty_calculations`
        """
        
        results = self.bq_client.query(query).to_dataframe()
        
        return results
    
    def get_top_risk_buildings(self, limit=20):
        """Get the buildings with highest penalty exposure"""
        
        query = f"""
        SELECT 
            building_name,
            address,
            property_type,
            ROUND(gross_floor_area, 0) as square_feet,
            ROUND(actual_eui, 1) as actual_eui,
            ROUND(target_eui_2030, 1) as target_2030,
            ROUND(percent_reduction_needed, 1) as reduction_needed_pct,
            ROUND(total_penalty_exposure, 0) as total_penalty,
            risk_category,
            compliance_2024
            
        FROM `{self.dataset_ref}.penalty_calculations`
        WHERE building_name IS NOT NULL
        ORDER BY total_penalty_exposure DESC
        LIMIT {limit}
        """
        
        return self.bq_client.query(query).to_dataframe()
    
    def generate_summary_report(self):
        """Generate a summary report of the analysis"""
        
        print("\n=== ENERGIZE DENVER COMPLIANCE ANALYSIS ===")
        print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Get summary statistics
        summary = self.get_summary_statistics()
        
        if not summary.empty:
            row = summary.iloc[0]
            
            print("PORTFOLIO SUMMARY:")
            print(f"  Total Buildings Analyzed: {row['total_buildings']:,}")
            print(f"  Total Square Footage: {row['total_square_feet']:,.0f}")
            print(f"  Average Reduction Needed: {row['avg_reduction_needed']:.1f}%\n")
            
            print("RISK DISTRIBUTION:")
            print(f"  High Risk Buildings: {row['high_risk_buildings']:,} ({row['high_risk_buildings']/row['total_buildings']*100:.1f}%)")
            print(f"  Medium Risk Buildings: {row['medium_risk_buildings']:,} ({row['medium_risk_buildings']/row['total_buildings']*100:.1f}%)")
            print(f"  Low Risk Buildings: {row['low_risk_buildings']:,} ({row['low_risk_buildings']/row['total_buildings']*100:.1f}%)")
            print(f"  Compliant Buildings: {row['compliant_buildings']:,} ({row['compliant_buildings']/row['total_buildings']*100:.1f}%)\n")
            
            print("FINANCIAL EXPOSURE:")
            print(f"  Total Penalty Exposure: ${row['total_penalty_exposure']:,.2f}")
            print(f"  Average Penalty per Building: ${row['avg_penalty_exposure']:,.2f}")
            print(f"  Maximum Single Building Penalty: ${row['max_penalty_exposure']:,.2f}\n")
        
        # Get top risk buildings
        print("TOP 10 HIGHEST RISK BUILDINGS:")
        print("-" * 100)
        
        top_buildings = self.get_top_risk_buildings(10)
        if not top_buildings.empty:
            for idx, building in top_buildings.iterrows():
                print(f"{idx+1}. {building['building_name'][:40]:<40} | "
                      f"${building['total_penalty']:>10,.0f} | "
                      f"{building['risk_category']:<8} | "
                      f"{building['reduction_needed_pct']:>5.1f}% reduction needed")
        
        print("\n✓ Analysis complete! Data is now available in BigQuery for further analysis.")
        print(f"  View your data at: https://console.cloud.google.com/bigquery?project={PROJECT_ID}")


def main():
    """Main execution function"""
    
    # Initialize loader
    loader = EnergizeDenverDataLoader()
    
    try:
        # Step 1: Load all data
        loader.load_all_data()
        
        # Step 2: Create penalty calculation view
        loader.create_penalty_calculation_view()
        
        # Step 3: Generate summary report
        loader.generate_summary_report()
        
        # Provide next steps
        print("\n=== NEXT STEPS ===")
        print("1. View your data in BigQuery Console")
        print("2. Connect to Looker Studio for visualizations")
        print("3. Run custom queries for specific buildings")
        print("4. Export results for client reports")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Ensure you're authenticated: gcloud auth application-default login")
        print("2. Check your project ID is correct")
        print("3. Verify your CSV files are in Cloud Storage")


if __name__ == "__main__":
    main()
