"""
Suggested File Name: fixed_enhanced_der_clustering.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Fixed version of enhanced DER clustering with correct column names and calculations

This script fixes:
1. Building name column mapping
2. Address handling (if not available, use building_id + zip)
3. Thermal load calculations using actual EUI data
4. Thermal diversity score calculation
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

class FixedDERClusterAnalyzer(DERClusterAnalyzer):
    """Fixed DER Cluster Analyzer with correct column mappings"""
    
    def calculate_cluster_metrics(self, anchor: BuildingProfile, 
                                members: List[Tuple[BuildingProfile, float]],
                                buildings_df: pd.DataFrame) -> Dict:
        """
        Fixed calculate_cluster_metrics with proper column names
        """
        all_buildings = [anchor] + [b[0] for b in members]
        
        # Get building details from dataframe with correct column names
        anchor_details = buildings_df[buildings_df['building_id'] == anchor.building_id].iloc[0]
        
        # Handle building name and address
        anchor_name = anchor_details.get('building_name', f"Building {anchor.building_id}")
        # If no address column, create one from building_id and zip
        anchor_address = anchor_details.get('address', 
                                           anchor_details.get('property_address',
                                           f"Building {anchor.building_id}, ZIP: {anchor_details.get('zip_code', 'Unknown')}"))
        
        metrics = {
            'cluster_id': f"cluster_{anchor.building_id}",
            'anchor_building_id': anchor.building_id,
            'anchor_building_name': anchor_name,
            'anchor_building_address': anchor_address,
            'anchor_property_type': anchor.property_type,
            'member_count': len(members),
            'total_buildings': len(all_buildings),
            'total_sqft': sum(b.gross_floor_area for b in all_buildings),
            'avg_distance_m': np.mean([d for _, d in members]) if members else 0,
            'max_distance_m': max([d for _, d in members]) if members else 0,
            'epb_count': sum(1 for b in all_buildings if b.is_epb),
            'epb_percentage': sum(1 for b in all_buildings if b.is_epb) / len(all_buildings) * 100,
            'total_penalty_exposure': sum(b.penalty_exposure for b in all_buildings),
            'property_type_diversity': len(set(b.property_type for b in all_buildings)),
        }
        
        # Fix thermal load calculations using actual EUI data
        total_thermal_load = 0
        total_cooling_load = 0
        
        for b in all_buildings:
            # Thermal load (heating) from gas EUI
            # Convert from kBtu/sqft to MMBtu total
            thermal_load_mmbtu = (b.gross_floor_area * b.gas_eui) / 1000 if b.gas_eui > 0 else 0
            total_thermal_load += thermal_load_mmbtu
            
            # Cooling load estimation from electric EUI
            # Assume 30% of electric use is for cooling in commercial buildings
            # Convert to tons (1 ton = 12,000 BTU/hr, assume 2000 cooling hours/year)
            if b.electric_eui > 0:
                cooling_energy_kbtu = b.gross_floor_area * b.electric_eui * 0.3
                cooling_tons = cooling_energy_kbtu * 1000 / (12 * 2000)  # Convert to tons
                total_cooling_load += cooling_tons
            else:
                # Fallback to rule of thumb if no electric data
                total_cooling_load += b.gross_floor_area / 400
        
        metrics['total_thermal_load_mmbtu'] = total_thermal_load
        metrics['total_cooling_load_tons'] = total_cooling_load
        
        # Fix opt_in_count calculation using 'should_opt_in' column
        building_ids = [b.building_id for b in all_buildings]
        opt_in_buildings = buildings_df[buildings_df['building_id'].isin(building_ids)]
        
        if 'should_opt_in' in opt_in_buildings.columns:
            metrics['opt_in_count'] = opt_in_buildings['should_opt_in'].sum()
        else:
            metrics['opt_in_count'] = 0
        
        # Fix thermal diversity score calculation
        electric_heavy = 0
        gas_heavy = 0
        balanced = 0
        
        for b in all_buildings:
            if b.electric_eui > 0 and b.gas_eui > 0:
                ratio = b.electric_eui / b.gas_eui
                if ratio > 2:  # Heavily electric
                    electric_heavy += 1
                elif ratio < 0.5:  # Heavily gas
                    gas_heavy += 1
                else:  # Balanced
                    balanced += 1
        
        # Thermal diversity is good when you have a mix of heating and cooling loads
        if len(all_buildings) > 0:
            # Best diversity is 50/50 split
            diversity_ratio = min(electric_heavy, gas_heavy) / len(all_buildings)
            # Also give credit for balanced buildings
            metrics['thermal_diversity_score'] = diversity_ratio + (balanced / len(all_buildings) * 0.5)
        else:
            metrics['thermal_diversity_score'] = 0
        
        # Enhanced members list with building details
        members_with_details = []
        for building, distance in members:
            building_info = buildings_df[buildings_df['building_id'] == building.building_id].iloc[0]
            
            member_name = building_info.get('building_name', f"Building {building.building_id}")
            member_address = building_info.get('address',
                                             building_info.get('property_address',
                                             f"Building {building.building_id}, ZIP: {building_info.get('zip_code', 'Unknown')}"))
            
            members_with_details.append({
                'building_id': building.building_id,
                'building_name': member_name,
                'building_address': member_address,
                'distance_m': distance,
                'property_type': building.property_type,
                'is_epb': building.is_epb,
                'sqft': building.gross_floor_area,
                'gas_eui': building.gas_eui,
                'electric_eui': building.electric_eui
            })
        
        metrics['members'] = members_with_details
        metrics['economic_potential_score'] = self._calculate_economic_score(metrics)
        
        return metrics

    def analyze_clusters(self, buildings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fixed analysis function with proper EUI calculations
        """
        # Print data quality info
        print("\n📊 Data Quality Check:")
        print(f"   Buildings with gas EUI > 0: {(buildings_df['gas_eui'] > 0).sum()}")
        print(f"   Buildings with electric EUI > 0: {(buildings_df['electric_eui'] > 0).sum()}")
        print(f"   Average gas EUI: {buildings_df['gas_eui'].mean():.1f}")
        print(f"   Average electric EUI: {buildings_df['electric_eui'].mean():.1f}")
        
        # Convert to BuildingProfile objects with fixed calculations
        buildings = []
        for _, row in buildings_df.iterrows():
            if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
                # Use the actual EUI values from the data
                electric_eui = row.get('electric_eui', 0)
                gas_eui = row.get('gas_eui', 0)
                
                buildings.append(BuildingProfile(
                    building_id=str(row['building_id']),
                    lat=row['latitude'],
                    lon=row['longitude'],
                    property_type=row.get('property_type', 'Unknown'),
                    gross_floor_area=row.get('gross_floor_area', 0),
                    site_eui=row.get('current_eui', 0),
                    electric_eui=electric_eui,
                    gas_eui=gas_eui,
                    opt_in_status='Opt-In' if row.get('should_opt_in', False) else 'Default',
                    is_epb=row.get('is_epb', False),
                    penalty_exposure=row.get('total_penalties_default', 0)
                ))
        
        # Rest of the analysis continues as before
        anchors = self.identify_anchor_buildings(buildings)
        print(f"\n📍 Found {len(anchors)} potential anchor buildings")
        
        clusters = []
        processed_buildings = set()
        
        for anchor in anchors:
            if anchor.building_id in processed_buildings:
                continue
                
            nearby = self.find_nearby_buildings(anchor, buildings)
            
            if len(nearby) >= 3:
                nearby_filtered = [(b, d) for b, d in nearby 
                                 if b.building_id not in processed_buildings]
                
                if len(nearby_filtered) >= 3:
                    cluster_metrics = self.calculate_cluster_metrics(anchor, nearby_filtered, buildings_df)
                    clusters.append(cluster_metrics)
                    
                    processed_buildings.add(anchor.building_id)
                    for b, _ in nearby_filtered:
                        processed_buildings.add(b.building_id)
        
        clusters_df = pd.DataFrame(clusters)
        if not clusters_df.empty:
            clusters_df = clusters_df.sort_values('economic_potential_score', ascending=False)
        
        print(f"\n🏢 Identified {len(clusters_df)} viable DER clusters")
        
        return clusters_df


def organize_outputs(base_output_dir):
    """Organize output directories"""
    import os
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(base_output_dir, 'der_clustering', timestamp)
    
    paths = {
        'reports': os.path.join(output_dir, 'reports'),
        'json': os.path.join(output_dir, 'json'),
        'visualizations': os.path.join(output_dir, 'visualizations')
    }
    
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    
    return paths

def export_to_excel_friendly_csv(df, filepath):
    """Export DataFrame to Excel-friendly CSV"""
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"   Saved: {os.path.basename(filepath)}")


def main():
    """Main function to run fixed DER clustering"""
    
    # Paths
    epb_file_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/CopyofWeeklyEPBStatsReport Report.csv'
    base_output_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs'
    
    # Organize output directories
    from fixed_enhanced_der_clustering import organize_outputs, export_to_excel_friendly_csv
    output_paths = organize_outputs(base_output_dir)
    
    print("🚀 Starting Fixed Enhanced DER Clustering Analysis\n")
    
    # Load EPB data
    print("📊 Loading EPB data...")
    epb_df = pd.read_csv(epb_file_path)
    epb_df['Building ID'] = epb_df['Building ID'].astype(str)
    epb_df['is_epb'] = epb_df['EPB Application Status'].isin(['Approved', 'Pending'])
    
    # Also create building name lookup from EPB data
    epb_names = dict(zip(epb_df['Building ID'], epb_df['Building Name']))
    epb_addresses = dict(zip(epb_df['Building ID'], epb_df['Building Address']))
    
    # Initialize GCP bridge and load building data
    bridge = LocalGCPBridge()
    
    print("\n📊 Loading building data from BigQuery...")
    try:
        buildings_df = bridge.get_der_clustering_data()
    except:
        buildings_df = bridge.get_opt_in_analysis_with_geo()
    
    # Ensure building_id is string
    buildings_df['building_id'] = buildings_df['building_id'].astype(str)
    
    # Add EPB names and addresses to main data
    buildings_df['building_name_epb'] = buildings_df['building_id'].map(epb_names)
    buildings_df['building_address_epb'] = buildings_df['building_id'].map(epb_addresses)
    
    # Use EPB name/address if available, otherwise use existing
    buildings_df['building_name'] = buildings_df['building_name_epb'].fillna(buildings_df.get('building_name', buildings_df['building_id']))
    buildings_df['address'] = buildings_df['building_address_epb'].fillna('Address not available')
    
    print("\n📋 Data columns check:")
    print(f"   Has building_name: {'building_name' in buildings_df.columns}")
    print(f"   Has address: {'address' in buildings_df.columns}")
    print(f"   Sample names: {buildings_df['building_name'].head(3).tolist()}")
    
    # Integrate EPB status
    epb_lookup = dict(zip(epb_df['Building ID'], epb_df['is_epb']))
    buildings_df['is_epb'] = buildings_df['building_id'].map(epb_lookup).fillna(False)
    
    # Run fixed clustering
    print("\n🏢 Running fixed DER clustering...")
    analyzer = FixedDERClusterAnalyzer(max_distance_meters=500)
    clusters_df = analyzer.analyze_clusters(buildings_df)
    
    if clusters_df.empty:
        print("❌ No viable clusters found")
        return
    
    print(f"\n✅ Found {len(clusters_df)} viable DER clusters!")
    
    # Print sample results to verify fixes
    print("\n🔍 Sample cluster data (first cluster):")
    if len(clusters_df) > 0:
        first_cluster = clusters_df.iloc[0]
        print(f"   Anchor name: {first_cluster['anchor_building_name']}")
        print(f"   Anchor address: {first_cluster['anchor_building_address']}")
        print(f"   Thermal load: {first_cluster['total_thermal_load_mmbtu']:.1f} MMBtu")
        print(f"   Cooling load: {first_cluster['total_cooling_load_tons']:.1f} tons")
        print(f"   Thermal diversity: {first_cluster['thermal_diversity_score']:.2%}")
    
    # Create reports with proper formatting
    
    # 1. Main cluster report
    main_report = clusters_df.drop('members', axis=1)
    export_to_excel_friendly_csv(
        main_report,
        os.path.join(output_paths['reports'], 'der_clusters_fixed.csv')
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
        os.path.join(output_paths['reports'], 'epb_clusters_fixed.csv')
    )
    
    # 3. Detailed members report
    members_data = []
    for _, cluster in clusters_df.iterrows():
        for member in cluster['members']:
            members_data.append({
                'cluster_id': cluster['cluster_id'],
                'anchor_building_id': cluster['anchor_building_id'],
                'anchor_building_name': cluster['anchor_building_name'],
                'anchor_building_address': cluster['anchor_building_address'],
                'building_id': member['building_id'],
                'building_name': member['building_name'],
                'building_address': member['building_address'],
                'distance_m': member['distance_m'],
                'property_type': member['property_type'],
                'is_epb': member['is_epb'],
                'sqft': member['sqft'],
                'gas_eui': member['gas_eui'],
                'electric_eui': member['electric_eui']
            })
    
    members_df = pd.DataFrame(members_data)
    export_to_excel_friendly_csv(
        members_df,
        os.path.join(output_paths['reports'], 'cluster_members_detail_fixed.csv')
    )
    
    # 4. Save summary with thermal stats
    summary = {
        'total_clusters': int(len(clusters_df)),
        'clusters_with_epbs': int((clusters_df['epb_count'] > 0).sum()),
        'total_buildings_in_clusters': int(clusters_df['total_buildings'].sum()),
        'total_thermal_load_mmbtu': float(clusters_df['total_thermal_load_mmbtu'].sum()),
        'total_cooling_load_tons': float(clusters_df['total_cooling_load_tons'].sum()),
        'avg_thermal_diversity': float(clusters_df['thermal_diversity_score'].mean()),
        'clusters_with_good_diversity': int((clusters_df['thermal_diversity_score'] > 0.3).sum()),
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    with open(os.path.join(output_paths['json'], 'clustering_summary_fixed.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n📊 Summary Statistics:")
    print(f"   Total clusters: {summary['total_clusters']}")
    print(f"   Total thermal load: {summary['total_thermal_load_mmbtu']:,.0f} MMBtu")
    print(f"   Total cooling load: {summary['total_cooling_load_tons']:,.0f} tons")
    print(f"   Average thermal diversity: {summary['avg_thermal_diversity']:.2%}")
    print(f"   Clusters with good diversity (>30%): {summary['clusters_with_good_diversity']}")
    
    print("\n📁 Fixed outputs saved in:")
    print(f"   Reports: {output_paths['reports']}")
    print(f"   - der_clusters_fixed.csv")
    print(f"   - epb_clusters_fixed.csv")
    print(f"   - cluster_members_detail_fixed.csv")
    
    return clusters_df

if __name__ == "__main__":
    clusters = main()
