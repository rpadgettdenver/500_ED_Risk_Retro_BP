"""
Suggested File Name: run_der_clustering.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Run DER clustering analysis on Denver buildings using actual geographic data

This script:
1. Loads building data with geographic coordinates from BigQuery
2. Runs the DER clustering analysis
3. Exports results and creates visualizations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.local_gcp_bridge import LocalGCPBridge
from analytics.der_clustering_analysis import DERClusterAnalyzer
import pandas as pd
import json

def main():
    """Run DER clustering analysis on Denver buildings"""
    
    print("🚀 Starting DER Clustering Analysis for Denver Buildings\n")
    
    # Initialize bridge to GCP
    bridge = LocalGCPBridge()
    
    # Load data with geographic coordinates
    print("📊 Loading building data from BigQuery...")
    try:
        # Try to get DER-optimized data first
        df = bridge.get_der_clustering_data()
    except:
        # Fallback to regular data with geo
        df = bridge.get_opt_in_analysis_with_geo()
    
    print(f"\n📍 Data loaded: {len(df)} buildings with coordinates")
    
    # Check data quality
    print("\n🔍 Data Quality Check:")
    print(f"Buildings with lat/lon: {df['latitude'].notna().sum()}")
    print(f"Buildings with zip code: {df['zip_code'].notna().sum()}")
    print(f"Unique property types: {df['property_type'].nunique()}")
    print(f"Total square footage: {df['gross_floor_area'].sum():,.0f}")
    
    # Initialize analyzer with 500m radius (about 3 blocks)
    analyzer = DERClusterAnalyzer(max_distance_meters=500)
    
    # Run clustering analysis
    print("\n🏢 Running DER clustering analysis...")
    clusters_df = analyzer.analyze_clusters(df)
    
    if clusters_df.empty:
        print("❌ No viable clusters found")
        return
    
    # Display results
    print(f"\n✅ Found {len(clusters_df)} viable DER clusters!")
    
    # Top clusters by economic potential
    print("\n📊 Top 10 DER Clusters by Economic Potential:")
    top_clusters = clusters_df.nlargest(10, 'economic_potential_score')
    
    for idx, cluster in top_clusters.iterrows():
        print(f"\n🏢 Cluster #{idx+1} - Score: {cluster['economic_potential_score']:.1f}/100")
        print(f"   Anchor: {cluster['anchor_property_type']} (ID: {cluster['anchor_building_id']})")
        print(f"   Buildings: {cluster['total_buildings']} ({cluster['member_count']} nearby)")
        print(f"   Total sqft: {cluster['total_sqft']:,.0f}")
        print(f"   Thermal load: {cluster['total_thermal_load_mmbtu']:,.0f} MMBtu")
        print(f"   Penalty exposure: ${cluster['total_penalty_exposure']:,.0f}")
        print(f"   EPB percentage: {cluster['epb_percentage']:.1f}%")
        print(f"   Max distance: {cluster['max_distance_m']:.0f}m")
    
    # Save results
    output_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs'
    os.makedirs(output_dir, exist_ok=True)
    
    # Save cluster analysis
    output_path = os.path.join(output_dir, 'der_clusters_analysis.csv')
    clusters_df.to_csv(output_path, index=False)
    print(f"\n💾 Saved cluster analysis to: {output_path}")
    
    # Export GeoJSON for mapping
    geojson_path = os.path.join(output_dir, 'der_clusters.geojson')
    analyzer.export_cluster_geojson(clusters_df, df, geojson_path)
    
    # Create summary statistics
    summary = {
        'total_clusters': int(len(clusters_df)),
        'total_buildings_in_clusters': int(clusters_df['total_buildings'].sum()),
        'total_sqft_in_clusters': float(clusters_df['total_sqft'].sum()),
        'total_penalty_exposure': float(clusters_df['total_penalty_exposure'].sum()),
        'avg_economic_score': float(clusters_df['economic_potential_score'].mean()),
        'high_potential_clusters': int(len(clusters_df[clusters_df['economic_potential_score'] > 70])),
        'clusters_with_epbs': int(len(clusters_df[clusters_df['epb_count'] > 0])),
        'property_type_breakdown': {k: int(v) for k, v in clusters_df['anchor_property_type'].value_counts().to_dict().items()}
    }
    
    print("\n📈 Summary Statistics:")
    print(f"   Total clusters: {summary['total_clusters']}")
    print(f"   Buildings in clusters: {summary['total_buildings_in_clusters']:,}")
    print(f"   Total sqft: {summary['total_sqft_in_clusters']:,.0f}")
    print(f"   Total penalty exposure: ${summary['total_penalty_exposure']:,.0f}")
    print(f"   High-potential clusters (>70 score): {summary['high_potential_clusters']}")
    
    # Save summary
    summary_path = os.path.join(output_dir, 'der_clusters_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n💾 Saved summary to: {summary_path}")
    
    # Recommendations
    print("\n🎯 Key Recommendations:")
    print("1. Focus on high-scoring clusters (>70) for initial DER development")
    print("2. Prioritize clusters with EPB participation for equity funding")
    print("3. Data centers and hospitals make excellent anchor loads")
    print("4. Consider phased approach starting with top 5 clusters")
    
    return clusters_df


if __name__ == "__main__":
    clusters = main()