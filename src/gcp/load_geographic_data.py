"""
Suggested File Name: load_geographic_data.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Load and merge geographic data (lat/lon and zip codes) with BigQuery analysis data

This script:
1. Loads geocoded building data from local CSV files
2. Uploads to BigQuery for joining with analysis data
3. Creates a comprehensive view with all geographic info
"""

import pandas as pd
from google.cloud import bigquery
import os

def load_geographic_data_to_bigquery(project_id='energize-denver-eaas', 
                                   dataset_id='energize_denver'):
    """
    Load geographic data from local CSV files and upload to BigQuery
    
    Args:
        project_id: GCP project ID
        dataset_id: BigQuery dataset ID
    """
    client = bigquery.Client(project=project_id)
    
    # Define paths
    base_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw'
    geocoded_path = os.path.join(base_path, 'geocoded_buildings_final.csv')
    zipcode_path = os.path.join(base_path, 'building_zipcode_lookup.csv')
    
    print("📍 Loading geographic data files...")
    
    # Load geocoded data
    geocoded_df = pd.read_csv(geocoded_path)
    print(f"✅ Loaded {len(geocoded_df)} geocoded buildings")
    
    # Load zipcode data
    zipcode_df = pd.read_csv(zipcode_path)
    print(f"✅ Loaded {len(zipcode_df)} zipcode records")
    
    # Clean column names for BigQuery
    geocoded_df.columns = [col.lower().replace(' ', '_') for col in geocoded_df.columns]
    zipcode_df.columns = [col.lower().replace(' ', '_') for col in zipcode_df.columns]
    
    # Ensure building_id is string type
    geocoded_df['building_id'] = geocoded_df['building_id'].astype(str)
    zipcode_df['building_id'] = zipcode_df['building_id'].astype(str)
    
    # Upload to BigQuery
    print("\n📤 Uploading to BigQuery...")
    
    # Define table references
    geocoded_table = f"{project_id}.{dataset_id}.geocoded_buildings"
    zipcode_table = f"{project_id}.{dataset_id}.building_zipcodes"
    
    # Upload geocoded data
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    
    job = client.load_table_from_dataframe(
        geocoded_df, geocoded_table, job_config=job_config
    )
    job.result()
    print(f"✅ Uploaded geocoded data to {geocoded_table}")
    
    # Upload zipcode data
    job = client.load_table_from_dataframe(
        zipcode_df, zipcode_table, job_config=job_config
    )
    job.result()
    print(f"✅ Uploaded zipcode data to {zipcode_table}")
    
    # Create a view that joins all geographic data with analysis
    print("\n🔄 Creating geographic analysis view...")
    
    view_query = f"""
    CREATE OR REPLACE VIEW `{project_id}.{dataset_id}.opt_in_analysis_with_geography` AS
    SELECT 
        a.*,
        g.latitude,
        g.longitude,
        g.geocoded,
        z.zipcode as zip_code
    FROM `{project_id}.{dataset_id}.opt_in_decision_analysis_v3` a
    LEFT JOIN `{project_id}.{dataset_id}.geocoded_buildings` g
        ON a.building_id = g.building_id
    LEFT JOIN `{project_id}.{dataset_id}.building_zipcodes` z
        ON a.building_id = z.building_id
    WHERE g.geocoded = True
    """
    
    client.query(view_query).result()
    print("✅ Created opt_in_analysis_with_geography view")
    
    # Test the view
    test_query = f"""
    SELECT 
        COUNT(*) as total_buildings,
        COUNT(DISTINCT zip_code) as unique_zips,
        COUNT(CASE WHEN latitude IS NOT NULL THEN 1 END) as buildings_with_coords,
        MIN(latitude) as min_lat,
        MAX(latitude) as max_lat,
        MIN(longitude) as min_lon,
        MAX(longitude) as max_lon
    FROM `{project_id}.{dataset_id}.opt_in_analysis_with_geography`
    """
    
    result = client.query(test_query).to_dataframe()
    print("\n📊 Geographic Data Summary:")
    print(result)
    
    return True


def create_der_clustering_view(project_id='energize-denver-eaas', 
                              dataset_id='energize_denver'):
    """
    Create a BigQuery view optimized for DER clustering analysis
    """
    client = bigquery.Client(project=project_id)
    
    view_query = f"""
    CREATE OR REPLACE VIEW `{project_id}.{dataset_id}.der_clustering_data` AS
    SELECT 
        building_id,
        building_name,
        property_type,
        gross_floor_area,
        current_eui,
        
        -- Calculate thermal loads
        CASE 
            WHEN property_type LIKE '%Data Center%' THEN current_eui * 0.8  -- High electric
            WHEN property_type LIKE '%Hospital%' THEN current_eui * 0.4     -- Mixed
            ELSE current_eui * 0.3  -- Default electric fraction
        END as electric_eui,
        
        CASE 
            WHEN property_type LIKE '%Data Center%' THEN current_eui * 0.2  -- Low gas
            WHEN property_type LIKE '%Hospital%' THEN current_eui * 0.6     -- Mixed
            ELSE current_eui * 0.7  -- Default gas fraction
        END as gas_eui,
        
        -- Compliance data
        should_opt_in,
        total_penalties_default,
        npv_advantage_optin,
        
        -- EPB status (we'll need to join this from another table if available)
        FALSE as is_epb,  -- Placeholder
        
        -- Geographic data
        latitude,
        longitude,
        zip_code,
        
        -- Identify anchor potential
        CASE 
            WHEN property_type IN ('Data Center', 'Hospital', 'College/University', 
                                 'Supermarket', 'Manufacturing/Industrial Plant') THEN TRUE
            WHEN gross_floor_area > 100000 THEN TRUE
            ELSE FALSE
        END as potential_anchor
        
    FROM `{project_id}.{dataset_id}.opt_in_analysis_with_geography`
    WHERE latitude IS NOT NULL 
      AND longitude IS NOT NULL
      AND gross_floor_area > 25000  -- Focus on buildings subject to BPS
    """
    
    client.query(view_query).result()
    print("✅ Created der_clustering_data view")
    
    # Get summary statistics
    summary_query = f"""
    SELECT 
        COUNT(*) as total_buildings,
        COUNT(CASE WHEN potential_anchor THEN 1 END) as anchor_buildings,
        COUNT(DISTINCT property_type) as property_types,
        ROUND(AVG(gross_floor_area)) as avg_sqft,
        ROUND(SUM(total_penalties_default)) as total_penalty_exposure
    FROM `{project_id}.{dataset_id}.der_clustering_data`
    """
    
    result = client.query(summary_query).to_dataframe()
    print("\n📊 DER Clustering Data Summary:")
    print(result)


def main():
    """Main function to load geographic data and prepare for clustering"""
    print("🚀 Starting geographic data integration...\n")
    
    # Step 1: Load geographic data to BigQuery
    load_geographic_data_to_bigquery()
    
    # Step 2: Create DER clustering view
    print("\n🔧 Creating DER clustering view...")
    create_der_clustering_view()
    
    print("\n✅ Geographic data integration complete!")
    print("\nYou can now:")
    print("1. Run DER clustering analysis using the der_clustering_data view")
    print("2. Use the local_gcp_bridge.py to pull data with geographic info")
    print("3. Create maps and spatial visualizations with lat/lon data")


if __name__ == "__main__":
    main()