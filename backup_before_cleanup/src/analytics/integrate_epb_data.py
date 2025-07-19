"""
Suggested File Name: integrate_epb_data.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Integrate EPB (Equity Priority Building) data with DER clustering analysis

This script:
1. Loads EPB data from the CSV file
2. Creates EPB lookup based on Building ID
3. Updates the DER clustering analysis to include EPB status
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.local_gcp_bridge import LocalGCPBridge
from analytics.der_clustering_analysis import DERClusterAnalyzer
import pandas as pd
import numpy as np
import json

def load_epb_data(epb_file_path):
    """
    Load and process EPB data from CSV file
    
    Args:
        epb_file_path: Path to EPB CSV file
        
    Returns:
        DataFrame with EPB data
    """
    print("📊 Loading EPB data...")
    epb_df = pd.read_csv(epb_file_path)
    
    # Clean Building ID column (ensure it's a string)
    epb_df['Building ID'] = epb_df['Building ID'].astype(str)
    
    # Count EPB statuses
    print(f"\n📈 EPB Status Summary:")
    print(f"   Total buildings in EPB file: {len(epb_df)}")
    print(f"   Approved EPBs: {(epb_df['EPB Application Status'] == 'Approved').sum()}")
    print(f"   Pending EPBs: {(epb_df['EPB Application Status'] == 'Pending').sum()}")
    
    # Create EPB flag (both approved and pending count as EPBs)
    epb_df['is_epb'] = epb_df['EPB Application Status'].isin(['Approved', 'Pending'])
    
    return epb_df

def integrate_epb_with_buildings(buildings_df, epb_df):
    """
    Integrate EPB status with building data
    
    Args:
        buildings_df: DataFrame with building data from BigQuery
        epb_df: DataFrame with EPB data
        
    Returns:
        DataFrame with EPB status integrated
    """
    print("\n🔄 Integrating EPB data with buildings...")
    
    # Convert building_id to string for matching
    buildings_df['building_id'] = buildings_df['building_id'].astype(str)
    
    # Create EPB lookup dictionary
    epb_lookup = dict(zip(epb_df['Building ID'], epb_df['is_epb']))
    epb_status_lookup = dict(zip(epb_df['Building ID'], epb_df['EPB Application Status']))
    
    # Add EPB status to buildings
    buildings_df['is_epb'] = buildings_df['building_id'].map(epb_lookup).fillna(False)
    buildings_df['epb_status'] = buildings_df['building_id'].map(epb_status_lookup).fillna('Not EPB')
    
    # Count matches
    epb_count = buildings_df['is_epb'].sum()
    print(f"✅ Matched {epb_count} EPBs out of {len(buildings_df)} buildings ({epb_count/len(buildings_df)*100:.1f}%)")
    
    return buildings_df

def run_enhanced_der_clustering(buildings_with_epb):
    """
    Run DER clustering with EPB data integrated
    
    Args:
        buildings_with_epb: DataFrame with EPB status included
        
    Returns:
        Cluster analysis results
    """
    print("\n🏢 Running enhanced DER clustering with EPB data...")
    
    # Initialize analyzer
    analyzer = DERClusterAnalyzer(max_distance_meters=500)
    
    # Run clustering
    clusters_df = analyzer.analyze_clusters(buildings_with_epb)
    
    if clusters_df.empty:
        print("❌ No viable clusters found")
        return None
    
    print(f"\n✅ Found {len(clusters_df)} viable DER clusters!")
    
    # Enhanced statistics with EPB focus
    epb_clusters = clusters_df[clusters_df['epb_count'] > 0]
    print(f"\n📊 EPB Statistics:")
    print(f"   Clusters with EPBs: {len(epb_clusters)} ({len(epb_clusters)/len(clusters_df)*100:.1f}%)")
    print(f"   Total EPBs in clusters: {clusters_df['epb_count'].sum()}")
    print(f"   Average EPBs per cluster: {clusters_df['epb_count'].mean():.1f}")
    
    # Top EPB clusters
    print("\n🏆 Top 5 Clusters by EPB Count:")
    top_epb_clusters = clusters_df.nlargest(5, 'epb_count')
    for idx, cluster in top_epb_clusters.iterrows():
        print(f"   Cluster {cluster['cluster_id']}: {cluster['epb_count']} EPBs, "
              f"{cluster['total_buildings']} total buildings, "
              f"Score: {cluster['economic_potential_score']:.1f}")
    
    return clusters_df

def create_epb_focused_report(clusters_df, output_dir):
    """
    Create a report focused on EPB opportunities
    
    Args:
        clusters_df: Cluster analysis results
        output_dir: Directory to save reports
    """
    print("\n📝 Creating EPB-focused report...")
    
    # Filter for clusters with EPBs
    epb_clusters = clusters_df[clusters_df['epb_count'] > 0].copy()
    
    # Calculate additional metrics
    epb_clusters['epb_density'] = epb_clusters['epb_count'] / epb_clusters['total_buildings']
    epb_clusters['penalty_per_epb'] = epb_clusters['total_penalty_exposure'] / epb_clusters['epb_count']
    
    # Sort by EPB opportunity score (combination of EPB count and economic potential)
    epb_clusters['epb_opportunity_score'] = (
        epb_clusters['epb_count'] * 0.3 +
        epb_clusters['economic_potential_score'] * 0.7
    )
    epb_clusters = epb_clusters.sort_values('epb_opportunity_score', ascending=False)
    
    # Save report
    report_path = os.path.join(output_dir, 'epb_der_clusters_report.csv')
    epb_clusters.to_csv(report_path, index=False)
    print(f"✅ Saved EPB-focused report to: {report_path}")
    
    # Create summary
    summary = {
        'total_epb_clusters': len(epb_clusters),
        'total_epbs_in_clusters': int(epb_clusters['epb_count'].sum()),
        'avg_epbs_per_cluster': float(epb_clusters['epb_count'].mean()),
        'total_epb_penalty_exposure': float(epb_clusters['total_penalty_exposure'].sum()),
        'top_5_epb_clusters': []
    }
    
    for idx, cluster in epb_clusters.head(5).iterrows():
        summary['top_5_epb_clusters'].append({
            'cluster_id': cluster['cluster_id'],
            'epb_count': int(cluster['epb_count']),
            'total_buildings': int(cluster['total_buildings']),
            'epb_density': float(cluster['epb_density']),
            'penalty_exposure': float(cluster['total_penalty_exposure']),
            'opportunity_score': float(cluster['epb_opportunity_score'])
        })
    
    summary_path = os.path.join(output_dir, 'epb_clusters_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Saved EPB summary to: {summary_path}")
    
    return epb_clusters

def main():
    """Main function to run EPB-integrated DER clustering"""
    
    # Paths
    epb_file_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/CopyofWeeklyEPBStatsReport Report.csv'
    output_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs'
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print("🚀 Starting EPB-Integrated DER Clustering Analysis\n")
    
    # Load EPB data
    epb_df = load_epb_data(epb_file_path)
    
    # Initialize GCP bridge and load building data
    bridge = LocalGCPBridge()
    
    print("\n📊 Loading building data from BigQuery...")
    try:
        # Try to get DER-optimized data first
        buildings_df = bridge.get_der_clustering_data()
    except:
        # Fallback to regular data with geo
        buildings_df = bridge.get_opt_in_analysis_with_geo()
    
    # Integrate EPB data
    buildings_with_epb = integrate_epb_with_buildings(buildings_df, epb_df)
    
    # Run enhanced clustering
    clusters_df = run_enhanced_der_clustering(buildings_with_epb)
    
    if clusters_df is not None:
        # Save enhanced results
        output_path = os.path.join(output_dir, 'der_clusters_with_epb.csv')
        clusters_df.to_csv(output_path, index=False)
        print(f"\n💾 Saved enhanced cluster analysis to: {output_path}")
        
        # Create EPB-focused report
        epb_clusters = create_epb_focused_report(clusters_df, output_dir)
        
        # Create enhanced GeoJSON with EPB highlights
        analyzer = DERClusterAnalyzer(max_distance_meters=500)
        geojson_path = os.path.join(output_dir, 'der_clusters_epb_highlighted.geojson')
        analyzer.export_cluster_geojson(clusters_df, buildings_with_epb, geojson_path)
        
        print("\n🎯 Key Findings:")
        print(f"1. {(clusters_df['epb_count'] > 0).sum()} clusters contain EPBs")
        print(f"2. Top cluster has {clusters_df['epb_count'].max()} EPBs")
        print(f"3. Total penalty exposure for EPB clusters: ${clusters_df[clusters_df['epb_count'] > 0]['total_penalty_exposure'].sum():,.0f}")
        print("\n✨ Analysis complete! Check the outputs folder for detailed results.")
    
    return clusters_df, buildings_with_epb

if __name__ == "__main__":
    clusters, buildings = main()
