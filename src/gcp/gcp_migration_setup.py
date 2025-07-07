"""
Energize Denver Risk & Retrofit Platform - Google Cloud Migration Script

Suggested filename: gcp_migration_setup.py
Directory location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/
USE: This script helps migrate your Energize Denver project to Google Cloud Platform
     for enhanced data processing, collaboration, and scalability.

Requirements:
    pip install google-cloud-storage google-cloud-bigquery pandas numpy
"""

import os
import pandas as pd
from google.cloud import storage
from google.cloud import bigquery
from datetime import datetime
import json

class EnergizeDenverGCPMigration:
    """
    Manages the migration and operation of Energize Denver data on Google Cloud
    """
    
    def __init__(self, project_id, bucket_name, dataset_name='energize_denver'):
        """
        Initialize Google Cloud clients
        
        Args:
            project_id: Your Google Cloud project ID
            bucket_name: Name for your Cloud Storage bucket
            dataset_name: BigQuery dataset name
        """
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.dataset_name = dataset_name
        
        # Initialize clients
        self.storage_client = storage.Client(project=project_id)
        self.bq_client = bigquery.Client(project=project_id)
        
        # Create bucket if it doesn't exist
        self._create_bucket_if_needed()
        
        # Create BigQuery dataset if it doesn't exist
        self._create_dataset_if_needed()
    
    def _create_bucket_if_needed(self):
        """Create Cloud Storage bucket if it doesn't exist"""
        try:
            self.bucket = self.storage_client.get_bucket(self.bucket_name)
            print(f"✓ Using existing bucket: {self.bucket_name}")
        except:
            self.bucket = self.storage_client.create_bucket(self.bucket_name)
            print(f"✓ Created new bucket: {self.bucket_name}")
    
    def _create_dataset_if_needed(self):
        """Create BigQuery dataset if it doesn't exist"""
        dataset_id = f"{self.project_id}.{self.dataset_name}"
        
        try:
            self.bq_client.get_dataset(dataset_id)
            print(f"✓ Using existing dataset: {self.dataset_name}")
        except:
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = "US"
            dataset = self.bq_client.create_dataset(dataset, timeout=30)
            print(f"✓ Created new dataset: {self.dataset_name}")
    
    def upload_file_to_storage(self, local_path, cloud_path=None):
        """
        Upload a file to Cloud Storage
        
        Args:
            local_path: Path to local file
            cloud_path: Path in cloud (defaults to same as local)
        """
        if cloud_path is None:
            cloud_path = os.path.basename(local_path)
        
        blob = self.bucket.blob(cloud_path)
        blob.upload_from_filename(local_path)
        print(f"✓ Uploaded {local_path} to gs://{self.bucket_name}/{cloud_path}")
        
        return f"gs://{self.bucket_name}/{cloud_path}"
    
    def load_csv_to_bigquery(self, csv_path, table_name, schema=None):
        """
        Load CSV file to BigQuery table
        
        Args:
            csv_path: Path to CSV file (local or gs://)
            table_name: Name for BigQuery table
            schema: Optional schema definition
        """
        table_id = f"{self.project_id}.{self.dataset_name}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=True if schema is None else False,
            schema=schema
        )
        
        # If local file, upload to Cloud Storage first
        if not csv_path.startswith('gs://'):
            csv_path = self.upload_file_to_storage(csv_path, f"data/{os.path.basename(csv_path)}")
        
        load_job = self.bq_client.load_table_from_uri(
            csv_path, table_id, job_config=job_config
        )
        
        load_job.result()  # Wait for job to complete
        
        table = self.bq_client.get_table(table_id)
        print(f"✓ Loaded {table.num_rows} rows to {table_id}")
        
        return table_id
    
    def create_penalty_calculation_view(self):
        """
        Create a BigQuery view for penalty calculations
        """
        view_id = f"{self.project_id}.{self.dataset_name}.penalty_calculations"
        
        view = bigquery.Table(view_id)
        view.view_query = """
        WITH penalty_calc AS (
            SELECT 
                building_id,
                building_name,
                address,
                property_type,
                gross_floor_area,
                baseline_eui,
                target_eui_2024,
                target_eui_2027,
                target_eui_2030,
                actual_eui,
                
                -- Calculate EUI gaps
                GREATEST(0, actual_eui - target_eui_2024) as eui_gap_2024,
                GREATEST(0, actual_eui - target_eui_2027) as eui_gap_2027,
                GREATEST(0, actual_eui - target_eui_2030) as eui_gap_2030,
                
                -- Calculate penalties (no opt-in)
                GREATEST(0, actual_eui - target_eui_2024) * gross_floor_area * 0.15 as penalty_2024,
                GREATEST(0, actual_eui - target_eui_2027) * gross_floor_area * 0.15 as penalty_2027,
                GREATEST(0, actual_eui - target_eui_2030) * gross_floor_area * 0.15 as penalty_2030,
                
                -- Total penalty exposure
                (GREATEST(0, actual_eui - target_eui_2024) + 
                 GREATEST(0, actual_eui - target_eui_2027) + 
                 GREATEST(0, actual_eui - target_eui_2030)) * gross_floor_area * 0.15 as total_penalty_exposure,
                
                -- EPB status
                is_epb,
                zipcode,
                latitude,
                longitude
                
            FROM `{project_id}.{dataset_name}.building_eui_targets` t
            LEFT JOIN `{project_id}.{dataset_name}.geocoded_buildings` g
                ON t.building_id = g.building_id
            LEFT JOIN `{project_id}.{dataset_name}.epb_status` e
                ON t.building_id = e.building_id
        )
        SELECT *,
            -- Risk categorization
            CASE 
                WHEN total_penalty_exposure > 100000 THEN 'HIGH'
                WHEN total_penalty_exposure > 50000 THEN 'MEDIUM'
                WHEN total_penalty_exposure > 0 THEN 'LOW'
                ELSE 'COMPLIANT'
            END as risk_category
        FROM penalty_calc
        """.format(project_id=self.project_id, dataset_name=self.dataset_name)
        
        view = self.bq_client.create_table(view, exists_ok=True)
        print(f"✓ Created penalty calculation view: {view_id}")
        
        return view_id
    
    def run_cluster_analysis(self):
        """
        Run geospatial clustering analysis to identify thermal network opportunities
        """
        query = """
        WITH building_clusters AS (
            SELECT 
                a.building_id,
                a.building_name,
                a.latitude,
                a.longitude,
                a.total_penalty_exposure,
                a.is_epb,
                
                -- Find nearby buildings within 500 meters
                ARRAY_AGG(
                    STRUCT(
                        b.building_id as nearby_building_id,
                        b.building_name as nearby_building_name,
                        ST_DISTANCE(
                            ST_GEOGPOINT(a.longitude, a.latitude),
                            ST_GEOGPOINT(b.longitude, b.latitude)
                        ) as distance_meters,
                        b.property_type,
                        b.total_penalty_exposure as nearby_penalty_exposure
                    )
                ) as nearby_buildings
                
            FROM `{project_id}.{dataset_name}.penalty_calculations` a
            JOIN `{project_id}.{dataset_name}.penalty_calculations` b
                ON ST_DWITHIN(
                    ST_GEOGPOINT(a.longitude, a.latitude),
                    ST_GEOGPOINT(b.longitude, b.latitude),
                    500  -- 500 meters
                )
                AND a.building_id != b.building_id
            WHERE a.latitude IS NOT NULL 
                AND a.longitude IS NOT NULL
            GROUP BY 1,2,3,4,5,6
        )
        SELECT 
            building_id,
            building_name,
            latitude,
            longitude,
            total_penalty_exposure,
            is_epb,
            ARRAY_LENGTH(nearby_buildings) as nearby_building_count,
            
            -- Calculate cluster metrics
            (SELECT SUM(nearby_penalty_exposure) 
             FROM UNNEST(nearby_buildings)) as cluster_total_penalty,
            
            (SELECT COUNT(1) 
             FROM UNNEST(nearby_buildings) 
             WHERE property_type IN ('Office', 'Retail')) as nearby_commercial_count,
            
            (SELECT COUNT(1) 
             FROM UNNEST(nearby_buildings) 
             WHERE property_type = 'Multifamily') as nearby_multifamily_count,
            
            -- Thermal network potential score
            CASE 
                WHEN ARRAY_LENGTH(nearby_buildings) >= 5 
                    AND total_penalty_exposure > 50000 THEN 'HIGH'
                WHEN ARRAY_LENGTH(nearby_buildings) >= 3 
                    AND total_penalty_exposure > 25000 THEN 'MEDIUM'
                ELSE 'LOW'
            END as thermal_network_potential
            
        FROM building_clusters
        ORDER BY cluster_total_penalty DESC
        """.format(project_id=self.project_id, dataset_name=self.dataset_name)
        
        results = self.bq_client.query(query).to_dataframe()
        print(f"✓ Completed cluster analysis for {len(results)} buildings")
        
        return results
    
    def create_cloud_function_for_updates(self):
        """
        Generate Cloud Function code for automatic processing
        """
        cloud_function_code = '''
import functions_framework
from google.cloud import bigquery
from google.cloud import storage
import pandas as pd

@functions_framework.cloud_event
def process_new_building_data(cloud_event):
    """
    Triggered when new CSV file is uploaded to bucket
    Automatically processes and updates BigQuery tables
    """
    data = cloud_event.data
    
    bucket_name = data['bucket']
    file_name = data['name']
    
    # Only process CSV files in the 'new_data' folder
    if not file_name.startswith('new_data/') or not file_name.endswith('.csv'):
        return
    
    # Initialize clients
    storage_client = storage.Client()
    bq_client = bigquery.Client()
    
    # Download file
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    # Process based on file type
    if 'eui' in file_name.lower():
        # Update EUI targets table
        table_id = 'your-project.energize_denver.building_eui_targets'
        
    elif 'epb' in file_name.lower():
        # Update EPB status table
        table_id = 'your-project.energize_denver.epb_status'
    
    # Load to BigQuery
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    load_job = bq_client.load_table_from_uri(
        f"gs://{bucket_name}/{file_name}",
        table_id,
        job_config=job_config
    )
    
    load_job.result()
    print(f"Loaded {file_name} to {table_id}")
    
    # Trigger penalty recalculation
    # (Your penalty calculation logic here)
    
    return 'Success'
'''
        
        # Save cloud function code
        with open('cloud_function_update.py', 'w') as f:
            f.write(cloud_function_code)
        
        print("✓ Generated Cloud Function code for automatic updates")
        print("  Deploy with: gcloud functions deploy process_new_building_data --trigger-bucket=your-bucket-name")
    
    def generate_dashboard_query(self):
        """
        Generate SQL for a Looker Studio dashboard
        """
        dashboard_query = """
        -- Energize Denver Risk Dashboard Query
        SELECT 
            -- Building details
            building_id,
            building_name,
            address,
            property_type,
            gross_floor_area,
            
            -- Compliance metrics
            baseline_eui,
            actual_eui,
            target_eui_2030,
            
            -- Risk metrics
            total_penalty_exposure,
            risk_category,
            
            -- EPB and location
            is_epb,
            zipcode,
            latitude,
            longitude,
            
            -- Cluster metrics
            thermal_network_potential,
            nearby_building_count,
            cluster_total_penalty,
            
            -- Calculated fields for visualization
            ROUND(actual_eui - target_eui_2030, 1) as eui_gap_2030,
            ROUND((1 - target_eui_2030/baseline_eui) * 100, 1) as required_reduction_pct,
            
            -- Date for time series
            CURRENT_DATE() as report_date
            
        FROM `{project_id}.{dataset_name}.penalty_calculations` p
        LEFT JOIN `{project_id}.{dataset_name}.cluster_analysis` c
            USING(building_id)
        WHERE actual_eui IS NOT NULL
        """.format(project_id=self.project_id, dataset_name=self.dataset_name)
        
        return dashboard_query


# Example usage
if __name__ == "__main__":
    # Initialize migration tool
    migration = EnergizeDenverGCPMigration(
        project_id='your-project-id',  # Replace with your GCP project ID
        bucket_name='energize-denver-data'
    )
    
    # Example: Upload your data files
    data_files = [
        '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/Building_EUI_Targets.csv',
        '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/geocoded_buildings_final.csv',
        '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/CopyofWeeklyEPBStatsReport Report.csv'
    ]
    
    # Upload files and load to BigQuery
    for file_path in data_files:
        if os.path.exists(file_path):
            # Upload to Cloud Storage
            gs_path = migration.upload_file_to_storage(file_path)
            
            # Load to BigQuery
            table_name = os.path.basename(file_path).replace('.csv', '').lower()
            migration.load_csv_to_bigquery(file_path, table_name)
    
    # Create penalty calculation view
    migration.create_penalty_calculation_view()
    
    # Run cluster analysis
    cluster_results = migration.run_cluster_analysis()
    print(f"\nTop 10 buildings by cluster penalty exposure:")
    print(cluster_results[['building_name', 'cluster_total_penalty', 'thermal_network_potential']].head(10))
    
    # Generate dashboard query
    dashboard_sql = migration.generate_dashboard_query()
    print(f"\n✓ Dashboard query generated - use in Looker Studio or Data Studio")
    
    # Generate Cloud Function for updates
    migration.create_cloud_function_for_updates()
