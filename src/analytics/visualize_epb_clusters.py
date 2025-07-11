"""
Suggested File Name: visualize_epb_clusters.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Create visualizations and analysis of EPB DER clusters

This script creates:
1. Summary tables of top opportunities
2. Charts showing EPB distribution
3. Economic analysis visualizations
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

def load_cluster_data(output_dir):
    """Load the cluster analysis results"""
    # Load main cluster data
    clusters_df = pd.read_csv(os.path.join(output_dir, 'der_clusters_with_epb.csv'))
    
    # Load EPB-focused report
    epb_clusters_df = pd.read_csv(os.path.join(output_dir, 'epb_der_clusters_report.csv'))
    
    # Load summary
    with open(os.path.join(output_dir, 'epb_clusters_summary.json'), 'r') as f:
        summary = json.load(f)
    
    return clusters_df, epb_clusters_df, summary

def print_top_opportunities(epb_clusters_df):
    """Print formatted table of top EPB cluster opportunities"""
    print("\n" + "="*80)
    print("🏆 TOP 10 EPB CLUSTER OPPORTUNITIES")
    print("="*80)
    
    top_10 = epb_clusters_df.head(10)
    
    for idx, cluster in top_10.iterrows():
        print(f"\n#{idx+1} - Cluster ID: {cluster['cluster_id']}")
        print(f"   Anchor Type: {cluster['anchor_property_type']}")
        print(f"   EPB Buildings: {cluster['epb_count']:.0f} out of {cluster['total_buildings']:.0f} ({cluster['epb_density']*100:.1f}% EPB)")
        print(f"   Total Square Feet: {cluster['total_sqft']:,.0f}")
        print(f"   Penalty Exposure: ${cluster['total_penalty_exposure']:,.0f}")
        print(f"   Thermal Load: {cluster['total_thermal_load_mmbtu']:,.0f} MMBtu")
        print(f"   Opportunity Score: {cluster['epb_opportunity_score']:.1f}/100")

def create_visualizations(clusters_df, epb_clusters_df, output_dir):
    """Create visualization charts"""
    
    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('EPB DER Cluster Analysis', fontsize=16)
    
    # 1. EPB Distribution across clusters
    ax1 = axes[0, 0]
    epb_counts = clusters_df['epb_count'].value_counts().sort_index()
    ax1.bar(epb_counts.index, epb_counts.values, color='#2E86AB')
    ax1.set_xlabel('Number of EPBs in Cluster')
    ax1.set_ylabel('Number of Clusters')
    ax1.set_title('Distribution of EPBs Across Clusters')
    
    # 2. Economic Potential vs EPB Count
    ax2 = axes[0, 1]
    scatter = ax2.scatter(clusters_df['epb_count'], 
                         clusters_df['economic_potential_score'],
                         s=clusters_df['total_sqft']/10000,  # Size by square footage
                         alpha=0.6,
                         c=clusters_df['total_penalty_exposure'],
                         cmap='YlOrRd')
    ax2.set_xlabel('Number of EPBs in Cluster')
    ax2.set_ylabel('Economic Potential Score')
    ax2.set_title('Economic Potential vs EPB Count (size = sqft, color = penalty $)')
    plt.colorbar(scatter, ax=ax2, label='Penalty Exposure ($)')
    
    # 3. Top Property Types with EPBs
    ax3 = axes[1, 0]
    property_types = epb_clusters_df.groupby('anchor_property_type').agg({
        'epb_count': 'sum',
        'cluster_id': 'count'
    }).sort_values('epb_count', ascending=False).head(10)
    
    x_pos = range(len(property_types))
    ax3.bar(x_pos, property_types['epb_count'], color='#A23B72')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(property_types.index, rotation=45, ha='right')
    ax3.set_ylabel('Total EPBs')
    ax3.set_title('EPBs by Anchor Property Type')
    
    # Add cluster count as text on bars
    for i, (epb_count, cluster_count) in enumerate(zip(property_types['epb_count'], property_types['cluster_id'])):
        ax3.text(i, epb_count + 0.5, f'{cluster_count} clusters', ha='center', fontsize=8)
    
    # 4. Penalty Exposure by EPB Density
    ax4 = axes[1, 1]
    # Create bins for EPB density
    epb_clusters_df['epb_density_bin'] = pd.cut(epb_clusters_df['epb_density'], 
                                                bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                                                labels=['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'])
    
    density_penalties = epb_clusters_df.groupby('epb_density_bin')['total_penalty_exposure'].sum()
    ax4.bar(density_penalties.index, density_penalties.values/1e6, color='#F18F01')
    ax4.set_xlabel('EPB Density in Cluster')
    ax4.set_ylabel('Total Penalty Exposure ($M)')
    ax4.set_title('Penalty Exposure by EPB Density')
    
    plt.tight_layout()
    
    # Save figure
    viz_path = os.path.join(output_dir, 'epb_cluster_visualizations.png')
    plt.savefig(viz_path, dpi=300, bbox_inches='tight')
    print(f"\n📊 Saved visualizations to: {viz_path}")
    plt.close()
    
def create_implementation_roadmap(epb_clusters_df, output_dir):
    """Create an implementation roadmap for top clusters"""
    
    print("\n" + "="*80)
    print("📋 IMPLEMENTATION ROADMAP")
    print("="*80)
    
    # Phase 1: Quick Wins (High EPB density, smaller size)
    phase1 = epb_clusters_df[
        (epb_clusters_df['epb_density'] > 0.5) & 
        (epb_clusters_df['total_buildings'] <= 15)
    ].head(5)
    
    print("\n🚀 PHASE 1: Quick Wins (High EPB Density, <15 buildings)")
    print(f"   {len(phase1)} clusters identified")
    print(f"   Total EPBs: {phase1['epb_count'].sum():.0f}")
    print(f"   Total Penalty Avoidance: ${phase1['total_penalty_exposure'].sum():,.0f}")
    
    # Phase 2: Major Impact (Large clusters with good economics)
    phase2 = epb_clusters_df[
        (epb_clusters_df['economic_potential_score'] > 70) & 
        (epb_clusters_df['total_buildings'] > 15)
    ].head(5)
    
    print("\n🏗️ PHASE 2: Major Impact (Score >70, >15 buildings)")
    print(f"   {len(phase2)} clusters identified")
    print(f"   Total Buildings: {phase2['total_buildings'].sum():.0f}")
    print(f"   Total Penalty Avoidance: ${phase2['total_penalty_exposure'].sum():,.0f}")
    
    # Phase 3: Equity Focus (Highest EPB counts)
    phase3 = epb_clusters_df.nlargest(5, 'epb_count')
    
    print("\n❤️ PHASE 3: Maximum Equity Impact (Highest EPB counts)")
    print(f"   {len(phase3)} clusters identified")
    print(f"   Total EPBs: {phase3['epb_count'].sum():.0f}")
    print(f"   Average EPB density: {phase3['epb_density'].mean()*100:.1f}%")
    
    # Save roadmap
    roadmap = {
        'phase1_quick_wins': phase1[['cluster_id', 'epb_count', 'total_buildings', 'total_penalty_exposure']].to_dict('records'),
        'phase2_major_impact': phase2[['cluster_id', 'epb_count', 'total_buildings', 'total_penalty_exposure']].to_dict('records'),
        'phase3_equity_focus': phase3[['cluster_id', 'epb_count', 'total_buildings', 'total_penalty_exposure']].to_dict('records')
    }
    
    roadmap_path = os.path.join(output_dir, 'epb_implementation_roadmap.json')
    with open(roadmap_path, 'w') as f:
        json.dump(roadmap, f, indent=2)
    print(f"\n💾 Saved implementation roadmap to: {roadmap_path}")

def main():
    """Main function to visualize and analyze EPB clusters"""
    
    output_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs'
    
    print("🔍 Loading EPB Cluster Analysis Results...")
    
    # Load data
    clusters_df, epb_clusters_df, summary = load_cluster_data(output_dir)
    
    # Print summary
    print(f"\n📊 SUMMARY:")
    print(f"   Total EPB Clusters: {summary['total_epb_clusters']}")
    print(f"   Total EPBs in Clusters: {summary['total_epbs_in_clusters']}")
    print(f"   Total Penalty Exposure: ${summary['total_epb_penalty_exposure']:,.0f}")
    
    # Show top opportunities
    print_top_opportunities(epb_clusters_df)
    
    # Create visualizations
    print("\n📊 Creating visualizations...")
    create_visualizations(clusters_df, epb_clusters_df, output_dir)
    
    # Create implementation roadmap
    create_implementation_roadmap(epb_clusters_df, output_dir)
    
    print("\n✅ Analysis complete! Check the outputs folder for:")
    print("   - epb_cluster_visualizations.png")
    print("   - epb_implementation_roadmap.json")
    print("\n🗺️ To view clusters on a map:")
    print("   1. Go to geojson.io")
    print("   2. Open der_clusters_epb_highlighted.geojson")

if __name__ == "__main__":
    main()
