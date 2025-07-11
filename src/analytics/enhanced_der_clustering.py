"""
Suggested File Name: enhanced_der_clustering.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Enhanced DER clustering analysis with building names, addresses, and better data organization

This script:
1. Adds building names and addresses to cluster analysis
2. Fixes opt_in_count and thermal_diversity_score calculations
3. Organizes outputs into appropriate subdirectories
4. Creates Excel-friendly formatted outputs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.local_gcp_bridge import LocalGCPBridge
from analytics.der_clustering_analysis import DERClusterAnalyzer, BuildingProfile
import pandas as pd
import numpy as np
import json
from typing import List, Dict, Tuple
import math

class EnhancedDERClusterAnalyzer(DERClusterAnalyzer):
    """Enhanced DER Cluster Analyzer with building details and fixed calculations"""
    
    def calculate_cluster_metrics(self, anchor: BuildingProfile, 
                                members: List[Tuple[BuildingProfile, float]],
                                buildings_df: pd.DataFrame) -> Dict:
        """
        Enhanced calculate_cluster_metrics that includes building details
        
        Args:
            anchor: The anchor building
            members: List of (building, distance) tuples
            buildings_df: Full dataframe with building details
            
        Returns:
            Dictionary of cluster metrics with building details
        """
        all_buildings = [anchor] + [b[0] for b in members]
        
        # Get building details from dataframe
        anchor_details = buildings_df[buildings_df['building_id'] == anchor.building_id].iloc[0]
        
        metrics = {
            'cluster_id': f"cluster_{anchor.building_id}",
            'anchor_building_id': anchor.building_id,
            'anchor_building_name': anchor_details.get('property_name', 'Unknown'),
            'anchor_building_address': anchor_details.get('property_address', 'Unknown'),
            'anchor_property_type': anchor.property_type,
            'member_count': len(members),
            'total_buildings': len(all_buildings),
            'total_sqft': sum(b.gross_floor_area for b in all_buildings),
            'total_thermal_load_mmbtu': sum(b.thermal_load_mmbtu for b in all_buildings),
            'total_cooling_load_tons': sum(b.cooling_load_tons for b in all_buildings),
            'avg_distance_m': np.mean([d for _, d in members]) if members else 0,
            'max_distance_m': max([d for _, d in members]) if members else 0,
            'epb_count': sum(1 for b in all_buildings if b.is_epb),
            'epb_percentage': sum(1 for b in all_buildings if b.is_epb) / len(all_buildings) * 100,
            'total_penalty_exposure': sum(b.penalty_exposure for b in all_buildings),
            'property_type_diversity': len(set(b.property_type for b in all_buildings)),
        }
        
        # Fix opt_in_count calculation
        building_ids = [b.building_id for b in all_buildings]
        opt_in_buildings = buildings_df[buildings_df['building_id'].isin(building_ids)]
        
        # Check for different column names
        if 'opt_in_recommendation' in opt_in_buildings.columns:
            metrics['opt_in_count'] = (opt_in_buildings['opt_in_recommendation'] == 'Opt-In').sum()
        elif 'should_opt_in' in opt_in_buildings.columns:
            metrics['opt_in_count'] = (opt_in_buildings['should_opt_in'] == True).sum()
        elif 'opt_in_status' in opt_in_buildings.columns:
            metrics['opt_in_count'] = (opt_in_buildings['opt_in_status'] == 'Opt-In').sum()
        else:
            # If no opt-in column found, set to 0
            metrics['opt_in_count'] = 0
        
        # Fix thermal diversity score calculation
        # Count buildings with significant electric vs gas usage
        electric_heavy = 0
        gas_heavy = 0
        for b in all_buildings:
            if b.electric_eui > 0 and b.gas_eui > 0:
                if b.electric_eui > b.gas_eui * 1.5:  # Significantly more electric
                    electric_heavy += 1
                elif b.gas_eui > b.electric_eui * 1.5:  # Significantly more gas
                    gas_heavy += 1
        
        total_with_energy = electric_heavy + gas_heavy
        if total_with_energy > 0:
            metrics['thermal_diversity_score'] = min(electric_heavy, gas_heavy) / total_with_energy
        else:
            metrics['thermal_diversity_score'] = 0
        
        # Enhanced members list with building details
        members_with_details = []
        for building, distance in members:
            building_info = buildings_df[buildings_df['building_id'] == building.building_id].iloc[0]
            members_with_details.append({
                'building_id': building.building_id,
                'building_name': building_info.get('property_name', 'Unknown'),
                'building_address': building_info.get('property_address', 'Unknown'),
                'distance_m': distance,
                'property_type': building.property_type,
                'is_epb': building.is_epb,
                'sqft': building.gross_floor_area
            })
        
        metrics['members'] = members_with_details
        metrics['economic_potential_score'] = self._calculate_economic_score(metrics)
        
        return metrics

    def analyze_clusters(self, buildings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Enhanced analysis function that preserves building details
        
        Args:
            buildings_df: DataFrame with building data including lat/lon
            
        Returns:
            DataFrame with cluster analysis results
        """
        # Convert to BuildingProfile objects
        buildings = []
        for _, row in buildings_df.iterrows():
            if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
                buildings.append(BuildingProfile(
                    building_id=str(row['building_id']),
                    lat=row['latitude'],
                    lon=row['longitude'],
                    property_type=row.get('property_type', 'Unknown'),
                    gross_floor_area=row.get('gross_floor_area', 0),
                    site_eui=row.get('most_recent_site_eui', 0),
                    electric_eui=row.get('electricity_use_grid_purchase', 0) / row.get('gross_floor_area', 1) * 3.412 if row.get('gross_floor_area', 0) > 0 else 0,
                    gas_eui=row.get('natural_gas_use', 0) / row.get('gross_floor_area', 1) * 10.037 if row.get('gross_floor_area', 0) > 0 else 0,
                    opt_in_status=row.get('opt_in_recommendation', row.get('should_opt_in', row.get('opt_in_status', 'Unknown'))),
                    is_epb=row.get('is_epb', False),
                    penalty_exposure=row.get('total_penalties_default', 0)
                ))
        
        # Identify anchor buildings
        anchors = self.identify_anchor_buildings(buildings)
        print(f"📍 Found {len(anchors)} potential anchor buildings")
        
        # Build clusters around each anchor
        clusters = []
        processed_buildings = set()
        
        for anchor in anchors:
            if anchor.building_id in processed_buildings:
                continue
                
            nearby = self.find_nearby_buildings(anchor, buildings)
            
            # Only create cluster if there are enough nearby buildings
            if len(nearby) >= 3:
                # Filter out buildings already in other clusters
                nearby_filtered = [(b, d) for b, d in nearby 
                                 if b.building_id not in processed_buildings]
                
                if len(nearby_filtered) >= 3:
                    cluster_metrics = self.calculate_cluster_metrics(anchor, nearby_filtered, buildings_df)
                    clusters.append(cluster_metrics)
                    
                    # Mark buildings as processed
                    processed_buildings.add(anchor.building_id)
                    for b, _ in nearby_filtered:
                        processed_buildings.add(b.building_id)
        
        # Convert to DataFrame and sort by economic potential
        clusters_df = pd.DataFrame(clusters)
        if not clusters_df.empty:
            clusters_df = clusters_df.sort_values('economic_potential_score', ascending=False)
        
        print(f"🏢 Identified {len(clusters_df)} viable DER clusters")
        
        return clusters_df

def organize_outputs(base_output_dir):
    """
    Organize outputs into appropriate subdirectories
    
    Args:
        base_output_dir: Base output directory path
        
    Returns:
        Dictionary of organized paths
    """
    # Create subdirectories if they don't exist
    subdirs = {
        'reports': os.path.join(base_output_dir, 'reports'),
        'visualizations': os.path.join(base_output_dir, 'visualizations'),
        'exports': os.path.join(base_output_dir, 'exports'),
        'geojson': os.path.join(base_output_dir, 'exports', 'geojson'),
        'json': os.path.join(base_output_dir, 'exports', 'json')
    }
    
    for dir_path in subdirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    return subdirs

def export_to_excel_friendly_csv(df, filepath):
    """
    Export DataFrame to CSV with Excel-friendly number formatting
    
    Args:
        df: DataFrame to export
        filepath: Path to save CSV
    """
    # Round numeric columns appropriately
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_columns:
        if 'count' in col or 'buildings' in col:
            df[col] = df[col].round(0).astype(int)
        elif 'score' in col or 'percentage' in col or 'density' in col:
            df[col] = df[col].round(2)
        elif 'exposure' in col or 'sqft' in col or 'load' in col:
            df[col] = df[col].round(0)
        else:
            df[col] = df[col].round(2)
    
    # Export to CSV
    df.to_csv(filepath, index=False)
    print(f"💾 Saved Excel-friendly CSV to: {filepath}")

def main():
    """Main function to run enhanced DER clustering"""
    
    # Paths
    epb_file_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/CopyofWeeklyEPBStatsReport Report.csv'
    base_output_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs'
    
    # Organize output directories
    output_paths = organize_outputs(base_output_dir)
    
    print("🚀 Starting Enhanced DER Clustering Analysis\n")
    
    # Load EPB data
    print("📊 Loading EPB data...")
    epb_df = pd.read_csv(epb_file_path)
    epb_df['Building ID'] = epb_df['Building ID'].astype(str)
    epb_df['is_epb'] = epb_df['EPB Application Status'].isin(['Approved', 'Pending'])
    
    # Initialize GCP bridge and load building data
    bridge = LocalGCPBridge()
    
    print("\n📊 Loading building data from BigQuery...")
    try:
        buildings_df = bridge.get_der_clustering_data()
    except:
        buildings_df = bridge.get_opt_in_analysis_with_geo()
    
    # Ensure building_id is string
    buildings_df['building_id'] = buildings_df['building_id'].astype(str)
    
    # Debug: Print available columns
    print("\n📋 Available columns in building data:")
    print(buildings_df.columns.tolist()[:20])  # First 20 columns
    print("...")
    
    # Check for opt-in related columns
    opt_in_cols = [col for col in buildings_df.columns if 'opt' in col.lower()]
    print(f"\n🔍 Opt-in related columns found: {opt_in_cols}")
    
    # Integrate EPB data
    epb_lookup = dict(zip(epb_df['Building ID'], epb_df['is_epb']))
    buildings_df['is_epb'] = buildings_df['building_id'].map(epb_lookup).fillna(False)
    
    # Run enhanced clustering
    print("\n🏢 Running enhanced DER clustering...")
    analyzer = EnhancedDERClusterAnalyzer(max_distance_meters=500)
    clusters_df = analyzer.analyze_clusters(buildings_df)
    
    if clusters_df.empty:
        print("❌ No viable clusters found")
        return
    
    print(f"\n✅ Found {len(clusters_df)} viable DER clusters!")
    
    # Create reports with proper formatting
    
    # 1. Main cluster report
    main_report = clusters_df.drop('members', axis=1)  # Remove nested members for main report
    export_to_excel_friendly_csv(
        main_report,
        os.path.join(output_paths['reports'], 'der_clusters_enhanced.csv')
    )
    
    # 2. EPB-focused report
    epb_clusters = clusters_df[clusters_df['epb_count'] > 0].copy()
    epb_clusters['epb_density'] = epb_clusters['epb_count'] / epb_clusters['total_buildings']
    epb_clusters['penalty_per_epb'] = epb_clusters['total_penalty_exposure'] / epb_clusters['epb_count']
    epb_clusters['epb_opportunity_score'] = (
        epb_clusters['epb_count'] * 0.3 +
        epb_clusters['economic_potential_score'] * 0.7
    )
    
    epb_report = epb_clusters.drop('members', axis=1).sort_values('epb_opportunity_score', ascending=False)
    export_to_excel_friendly_csv(
        epb_report,
        os.path.join(output_paths['reports'], 'epb_clusters_enhanced.csv')
    )
    
    # 3. Detailed members report (flatten the members data)
    members_data = []
    for _, cluster in clusters_df.iterrows():
        for member in cluster['members']:
            members_data.append({
                'cluster_id': cluster['cluster_id'],
                'anchor_building_id': cluster['anchor_building_id'],
                'anchor_building_name': cluster['anchor_building_name'],
                'building_id': member['building_id'],
                'building_name': member['building_name'],
                'building_address': member['building_address'],
                'distance_m': member['distance_m'],
                'property_type': member['property_type'],
                'is_epb': member['is_epb'],
                'sqft': member['sqft']
            })
    
    members_df = pd.DataFrame(members_data)
    export_to_excel_friendly_csv(
        members_df,
        os.path.join(output_paths['reports'], 'cluster_members_detail.csv')
    )
    
    # 4. Save JSON summaries
    summary = {
        'total_clusters': int(len(clusters_df)),
        'clusters_with_epbs': int((clusters_df['epb_count'] > 0).sum()),
        'total_buildings_in_clusters': int(clusters_df['total_buildings'].sum()),
        'total_epbs_in_clusters': int(clusters_df['epb_count'].sum()),
        'total_penalty_exposure': float(clusters_df['total_penalty_exposure'].sum()),
        'clusters_with_opt_in': int((clusters_df['opt_in_count'] > 0).sum()),
        'avg_thermal_diversity': float(clusters_df['thermal_diversity_score'].mean()),
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    with open(os.path.join(output_paths['json'], 'clustering_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # 5. Save GeoJSON
    analyzer.export_cluster_geojson(
        clusters_df, 
        buildings_df,
        os.path.join(output_paths['geojson'], 'der_clusters_enhanced.geojson')
    )
    
    # Print summary
    print("\n📊 Summary Statistics:")
    print(f"   Total clusters: {summary['total_clusters']}")
    print(f"   Clusters with EPBs: {summary['clusters_with_epbs']}")
    print(f"   Clusters with opt-in buildings: {summary['clusters_with_opt_in']}")
    print(f"   Average thermal diversity score: {summary['avg_thermal_diversity']:.2%}")
    
    print("\n📁 Outputs organized in:")
    print(f"   Reports: {output_paths['reports']}")
    print(f"   - der_clusters_enhanced.csv (main report)")
    print(f"   - epb_clusters_enhanced.csv (EPB focus)")
    print(f"   - cluster_members_detail.csv (all building details)")
    print(f"   GeoJSON: {output_paths['geojson']}")
    print(f"   JSON summaries: {output_paths['json']}")
    
    return clusters_df

if __name__ == "__main__":
    clusters = main()
