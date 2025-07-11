"""
Suggested File Name: local_gcp_bridge.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Bridge script to work with GCP data locally for development and testing

This script allows you to:
1. Pull data from BigQuery for local analysis
2. Test new algorithms locally before deploying to GCP
3. Create local visualizations and reports
"""

import os
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import numpy as np
from datetime import datetime
import json

class LocalGCPBridge:
    """Bridge class to work with GCP data locally"""
    
    def __init__(self, project_id='energize-denver-eaas', dataset_id='energize_denver'):
        """
        Initialize the bridge connection to GCP
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = self._initialize_client()
        
    def _initialize_client(self):
        """Initialize BigQuery client with proper authentication"""
        try:
            # Try to use application default credentials first
            client = bigquery.Client(project=self.project_id)
            print("✅ Connected to BigQuery using application default credentials")
            return client
        except Exception as e:
            print(f"❌ Could not connect to BigQuery: {e}")
            print("Run 'gcloud auth application-default login' to authenticate")
            return None
    
    def get_opt_in_analysis(self, limit=None):
        """
        Retrieve the latest opt-in decision analysis from BigQuery
        
        Args:
            limit: Number of rows to retrieve (None for all)
            
        Returns:
            DataFrame with opt-in analysis data
        """
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.dataset_id}.opt_in_decision_analysis_v3`
        """
        
        if limit:
            query += f" LIMIT {limit}"
            
        print(f"📊 Retrieving opt-in analysis data...")
        df = self.client.query(query).to_dataframe()
        print(f"✅ Retrieved {len(df)} buildings")
        return df
    
    def get_opt_in_analysis_with_geo(self, limit=None):
        """
        Retrieve opt-in analysis with geographic data
        
        Args:
            limit: Number of rows to retrieve (None for all)
            
        Returns:
            DataFrame with opt-in analysis and geographic data
        """
        # First try the view if it exists
        try:
            query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset_id}.opt_in_analysis_with_geography`
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """
            
            if limit:
                query += f" LIMIT {limit}"
                
            print(f"📊 Retrieving opt-in analysis data with geographic info...")
            df = self.client.query(query).to_dataframe()
            print(f"✅ Retrieved {len(df)} buildings with coordinates")
            return df
            
        except Exception as e:
            print(f"⚠️  Geographic view not found, creating join query...")
            # Fallback to manual join
            query = f"""
            SELECT 
                a.*,
                g.latitude,
                g.longitude,
                z.zipcode as zip_code
            FROM `{self.project_id}.{self.dataset_id}.opt_in_decision_analysis_v3` a
            LEFT JOIN `{self.project_id}.{self.dataset_id}.geocoded_buildings` g
                ON a.building_id = g.building_id
            LEFT JOIN `{self.project_id}.{self.dataset_id}.building_zipcodes` z
                ON a.building_id = z.building_id
            WHERE g.geocoded = True
            """
            
            if limit:
                query += f" LIMIT {limit}"
                
            df = self.client.query(query).to_dataframe()
            print(f"✅ Retrieved {len(df)} buildings")
            return df
    
    def get_der_clustering_data(self, limit=None):
        """
        Get data optimized for DER clustering analysis
        
        Args:
            limit: Number of rows to retrieve (None for all)
            
        Returns:
            DataFrame ready for DER clustering
        """
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.dataset_id}.der_clustering_data`
        """
        
        if limit:
            query += f" LIMIT {limit}"
            
        print(f"🏢 Retrieving DER clustering data...")
        df = self.client.query(query).to_dataframe()
        print(f"✅ Retrieved {len(df)} buildings for clustering analysis")
        return df
    
    def get_high_risk_buildings(self, penalty_threshold=100000):
        """
        Get buildings with high penalty exposure
        
        Args:
            penalty_threshold: Minimum total penalty to be considered high risk
            
        Returns:
            DataFrame of high-risk buildings
        """
        query = f"""
        SELECT 
            building_id,
            property_type,
            current_eui,
            baseline_eui,
            pct_reduction_requested,
            total_penalties_default,
            total_penalties_optin,
            should_opt_in,
            primary_rationale
        FROM `{self.project_id}.{self.dataset_id}.opt_in_decision_analysis_v3`
        WHERE total_penalties_default > {penalty_threshold}
        ORDER BY total_penalties_default DESC
        """
        
        return self.client.query(query).to_dataframe()
    
    def get_building_by_id(self, building_id):
        """
        Get detailed information for a specific building
        
        Args:
            building_id: The building ID to look up
            
        Returns:
            Dictionary with building details
        """
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.dataset_id}.opt_in_decision_analysis_v3`
        WHERE building_id = '{building_id}'
        """
        
        df = self.client.query(query).to_dataframe()
        if len(df) == 0:
            return None
        return df.iloc[0].to_dict()
    
    def analyze_property_type_summary(self):
        """
        Create a summary analysis by property type
        
        Returns:
            DataFrame with property type statistics
        """
        query = f"""
        SELECT 
            property_type,
            COUNT(*) as building_count,
            AVG(current_eui) as avg_current_eui,
            AVG(pct_reduction_requested) as avg_reduction_required,
            SUM(CASE WHEN should_opt_in = TRUE THEN 1 ELSE 0 END) as opt_in_count,
            ROUND(100.0 * SUM(CASE WHEN should_opt_in = TRUE THEN 1 ELSE 0 END) / COUNT(*), 1) as opt_in_pct,
            SUM(total_penalties_default) as total_default_penalties,
            SUM(total_penalties_optin) as total_optin_penalties,
            SUM(npv_advantage_optin) as total_npv_savings
        FROM `{self.project_id}.{self.dataset_id}.opt_in_decision_analysis_v3`
        WHERE property_type IS NOT NULL
        GROUP BY property_type
        ORDER BY total_default_penalties DESC
        """
        
        return self.client.query(query).to_dataframe()
    
    def export_for_local_analysis(self, output_dir='./data/gcp_exports/'):
        """
        Export key datasets for local analysis
        
        Args:
            output_dir: Directory to save exported files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Export main analysis
        print("📥 Exporting opt-in analysis...")
        opt_in_df = self.get_opt_in_analysis()
        opt_in_df.to_csv(os.path.join(output_dir, 'opt_in_analysis_v3.csv'), index=False)
        
        # Export property type summary
        print("📥 Exporting property type summary...")
        property_summary = self.analyze_property_type_summary()
        property_summary.to_csv(os.path.join(output_dir, 'property_type_summary.csv'), index=False)
        
        # Export high risk buildings
        print("📥 Exporting high-risk buildings...")
        high_risk = self.get_high_risk_buildings()
        high_risk.to_csv(os.path.join(output_dir, 'high_risk_buildings.csv'), index=False)
        
        # Export with geographic data
        print("📥 Exporting data with geographic info...")
        geo_df = self.get_opt_in_analysis_with_geo()
        geo_df.to_csv(os.path.join(output_dir, 'opt_in_analysis_with_geo.csv'), index=False)
        
        print(f"✅ All exports complete! Files saved to: {output_dir}")
        
    def test_local_algorithm(self, df, algorithm_func):
        """
        Test a local algorithm against GCP data
        
        Args:
            df: DataFrame with building data
            algorithm_func: Function to test
            
        Returns:
            Results of the algorithm
        """
        print(f"🧪 Testing algorithm: {algorithm_func.__name__}")
        results = algorithm_func(df)
        print(f"✅ Algorithm complete")
        return results


# Example usage functions
def example_der_clustering_algorithm(df):
    """
    Example algorithm for DER clustering analysis
    This would be developed and tested locally before deploying to GCP
    """
    # Example: Find buildings within 500m of each other
    # This is placeholder logic - real implementation would use lat/lon
    results = []
    
    # Group by zip code as a proxy for proximity
    if 'zip_code' in df.columns:
        for zip_code, group in df.groupby('zip_code'):
            if pd.notna(zip_code) and len(group) > 5:  # At least 5 buildings for a cluster
                cluster_info = {
                    'zip_code': zip_code,
                    'building_count': len(group),
                    'total_sqft': group['gross_floor_area'].sum() if 'gross_floor_area' in group.columns else 0,
                    'avg_eui': group['current_eui'].mean() if 'current_eui' in group.columns else 0,
                    'total_penalty_exposure': group['total_penalties_default'].sum() if 'total_penalties_default' in group.columns else 0,
                    'opt_in_percentage': (group['should_opt_in'] == True).mean() * 100 if 'should_opt_in' in group.columns else 0
                }
                results.append(cluster_info)
    else:
        print("Warning: 'zip_code' column not found in data")
    
    return pd.DataFrame(results)


def main():
    """Main function to demonstrate usage"""
    # Initialize bridge
    bridge = LocalGCPBridge()
    
    # Example 1: Get high-risk buildings
    print("\n📊 Example 1: High-Risk Buildings")
    high_risk = bridge.get_high_risk_buildings(penalty_threshold=500000)
    print(f"Found {len(high_risk)} buildings with >$500k penalty exposure")
    print(high_risk[['building_id', 'property_type', 'total_penalties_default']].head())
    
    # Example 2: Property type analysis
    print("\n📊 Example 2: Property Type Summary")
    property_summary = bridge.analyze_property_type_summary()
    print(property_summary[['property_type', 'building_count', 'opt_in_pct', 'total_npv_savings']].head())
    
    # Example 3: Export for local work
    print("\n📊 Example 3: Exporting Data for Local Analysis")
    # Create directory if it doesn't exist
    import os
    os.makedirs('./data/gcp_exports/', exist_ok=True)
    bridge.export_for_local_analysis()
    
    # Example 4: Test with geographic data
    print("\n📊 Example 4: Testing with Geographic Data")
    df_with_geo = bridge.get_opt_in_analysis_with_geo(limit=100)
    if 'zip_code' in df_with_geo.columns:
        clusters = bridge.test_local_algorithm(df_with_geo, example_der_clustering_algorithm)
        print(f"Found {len(clusters)} potential DER clusters")
        print(clusters.head())
    else:
        print("No geographic data available for clustering")


if __name__ == "__main__":
    main()