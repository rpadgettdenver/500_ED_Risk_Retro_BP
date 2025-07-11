"""
Suggested File Name: der_clustering_analysis.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Identify building clusters for shared District Energy Resource (DER) opportunities

This module:
1. Uses geospatial data to find nearby buildings
2. Analyzes thermal load profiles for compatibility
3. Identifies anchor loads (data centers, hospitals)
4. Calculates economic potential of thermal sharing
5. Prioritizes Equity Priority Buildings (EPBs)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from dataclasses import dataclass
from collections import defaultdict
import math

@dataclass
class BuildingProfile:
    """Data class for building thermal profile"""
    building_id: str
    lat: float
    lon: float
    property_type: str
    gross_floor_area: float
    site_eui: float
    electric_eui: float
    gas_eui: float
    opt_in_status: str
    is_epb: bool
    penalty_exposure: float
    
    @property
    def thermal_load_mmbtu(self) -> float:
        """Estimate annual thermal load in MMBtu"""
        return self.gross_floor_area * self.gas_eui / 1000
    
    @property
    def cooling_load_tons(self) -> float:
        """Estimate peak cooling load in tons"""
        # Rule of thumb: 400 sqft per ton for commercial buildings
        return self.gross_floor_area / 400


class DERClusterAnalyzer:
    """Analyzer for identifying DER clustering opportunities"""
    
    # Property types that make good anchor loads
    ANCHOR_PROPERTY_TYPES = [
        'Data Center',
        'Hospital',
        'College/University',
        'Supermarket',
        'Manufacturing/Industrial Plant'
    ]
    
    # Property types with high thermal demands
    HIGH_THERMAL_DEMAND_TYPES = [
        'Hotel',
        'Hospital',
        'Senior Care Community',
        'Multifamily Housing',
        'College/University'
    ]
    
    def __init__(self, max_distance_meters: float = 500):
        """
        Initialize the DER cluster analyzer
        
        Args:
            max_distance_meters: Maximum distance for clustering (default 500m)
        """
        self.max_distance_meters = max_distance_meters
        self.clusters = []
        
    def haversine_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points on Earth using Haversine formula
        
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def identify_anchor_buildings(self, buildings: List[BuildingProfile]) -> List[BuildingProfile]:
        """
        Identify buildings that could serve as anchor loads for DER systems
        
        Args:
            buildings: List of building profiles
            
        Returns:
            List of anchor buildings
        """
        anchors = []
        
        for building in buildings:
            # Check if it's an anchor property type
            if building.property_type in self.ANCHOR_PROPERTY_TYPES:
                anchors.append(building)
            # Also include large buildings with high thermal loads
            elif (building.gross_floor_area > 100000 and 
                  building.thermal_load_mmbtu > 5000):
                anchors.append(building)
                
        return anchors
    
    def find_nearby_buildings(self, anchor: BuildingProfile, 
                            buildings: List[BuildingProfile]) -> List[Tuple[BuildingProfile, float]]:
        """
        Find all buildings within max_distance of an anchor building
        
        Args:
            anchor: The anchor building
            buildings: List of all buildings
            
        Returns:
            List of (building, distance) tuples
        """
        nearby = []
        
        for building in buildings:
            if building.building_id == anchor.building_id:
                continue
                
            distance = self.haversine_distance(
                anchor.lat, anchor.lon,
                building.lat, building.lon
            )
            
            if distance <= self.max_distance_meters:
                nearby.append((building, distance))
                
        return sorted(nearby, key=lambda x: x[1])
    
    def calculate_cluster_metrics(self, anchor: BuildingProfile, 
                                members: List[Tuple[BuildingProfile, float]]) -> Dict:
        """
        Calculate key metrics for a potential DER cluster
        
        Args:
            anchor: The anchor building
            members: List of (building, distance) tuples
            
        Returns:
            Dictionary of cluster metrics
        """
        all_buildings = [anchor] + [b[0] for b in members]
        
        metrics = {
            'cluster_id': f"cluster_{anchor.building_id}",
            'anchor_building_id': anchor.building_id,
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
            'opt_in_count': sum(1 for b in all_buildings if b.opt_in_status == 'Opt-In'),
            'high_thermal_demand_count': sum(1 for b in all_buildings 
                                           if b.property_type in self.HIGH_THERMAL_DEMAND_TYPES),
            'property_type_diversity': len(set(b.property_type for b in all_buildings)),
            'members': [{'building_id': b.building_id, 
                        'distance_m': d,
                        'property_type': b.property_type,
                        'is_epb': b.is_epb} for b, d in members]
        }
        
        # Calculate thermal diversity score (mixing heating/cooling dominated buildings)
        electric_heavy = sum(1 for b in all_buildings if b.electric_eui > b.gas_eui)
        gas_heavy = len(all_buildings) - electric_heavy
        metrics['thermal_diversity_score'] = min(electric_heavy, gas_heavy) / len(all_buildings)
        
        # Calculate economic potential score
        metrics['economic_potential_score'] = self._calculate_economic_score(metrics)
        
        return metrics
    
    def _calculate_economic_score(self, metrics: Dict) -> float:
        """
        Calculate economic potential score for a cluster (0-100)
        
        Factors:
        - Size of cluster (sqft and load)
        - EPB percentage (equity priority)
        - Penalty exposure
        - Thermal diversity
        - Property type diversity
        """
        score = 0
        
        # Size factors (up to 30 points)
        if metrics['total_sqft'] > 1000000:
            score += 15
        elif metrics['total_sqft'] > 500000:
            score += 10
        elif metrics['total_sqft'] > 250000:
            score += 5
            
        if metrics['total_thermal_load_mmbtu'] > 10000:
            score += 15
        elif metrics['total_thermal_load_mmbtu'] > 5000:
            score += 10
        elif metrics['total_thermal_load_mmbtu'] > 2500:
            score += 5
        
        # EPB factor (up to 20 points)
        score += min(20, metrics['epb_percentage'] * 0.4)
        
        # Penalty exposure (up to 20 points)
        if metrics['total_penalty_exposure'] > 1000000:
            score += 20
        elif metrics['total_penalty_exposure'] > 500000:
            score += 15
        elif metrics['total_penalty_exposure'] > 250000:
            score += 10
        elif metrics['total_penalty_exposure'] > 100000:
            score += 5
        
        # Diversity factors (up to 20 points)
        score += metrics['thermal_diversity_score'] * 10
        score += min(10, metrics['property_type_diversity'] * 2)
        
        # Building count (up to 10 points)
        score += min(10, metrics['member_count'])
        
        return min(100, score)
    
    def analyze_clusters(self, buildings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Main analysis function to identify and rank DER clusters
        
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
                    building_id=row['building_id'],
                    lat=row['latitude'],
                    lon=row['longitude'],
                    property_type=row.get('property_type', 'Unknown'),
                    gross_floor_area=row.get('gross_floor_area', 0),
                    site_eui=row.get('most_recent_site_eui', 0),
                    electric_eui=row.get('electric_eui', 0),
                    gas_eui=row.get('gas_eui', 0),
                    opt_in_status=row.get('opt_in_recommendation', 'Unknown'),
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
                    cluster_metrics = self.calculate_cluster_metrics(anchor, nearby_filtered)
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
    
    def export_cluster_geojson(self, clusters_df: pd.DataFrame, 
                             buildings_df: pd.DataFrame,
                             output_path: str):
        """
        Export clusters as GeoJSON for mapping
        
        Args:
            clusters_df: DataFrame with cluster results
            buildings_df: Original buildings DataFrame
            output_path: Path to save GeoJSON file
        """
        features = []
        
        for _, cluster in clusters_df.iterrows():
            # Get anchor building location
            anchor_building = buildings_df[
                buildings_df['building_id'] == cluster['anchor_building_id']
            ].iloc[0]
            
            # Create feature for cluster center
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [anchor_building['longitude'], anchor_building['latitude']]
                },
                'properties': {
                    'cluster_id': cluster['cluster_id'],
                    'anchor_building': cluster['anchor_building_id'],
                    'member_count': cluster['member_count'],
                    'total_sqft': cluster['total_sqft'],
                    'economic_score': cluster['economic_potential_score'],
                    'epb_percentage': cluster['epb_percentage'],
                    'total_penalty': cluster['total_penalty_exposure']
                }
            }
            features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        print(f"📍 Exported cluster GeoJSON to: {output_path}")


def main():
    """Example usage of the DER clustering analyzer"""
    # This would typically load from your GCP bridge
    print("🔄 Loading building data...")
    
    # Example: Create sample data (replace with actual data loading)
    sample_data = pd.DataFrame({
        'building_id': ['B001', 'B002', 'B003', 'B004', 'B005'],
        'latitude': [39.7392, 39.7395, 39.7388, 39.7401, 39.7385],
        'longitude': [-104.9903, -104.9898, -104.9910, -104.9895, -104.9915],
        'property_type': ['Data Center', 'Office', 'Hotel', 'Hospital', 'Multifamily Housing'],
        'gross_floor_area': [150000, 80000, 120000, 200000, 100000],
        'most_recent_site_eui': [250, 65, 80, 180, 55],
        'electric_eui': [200, 40, 45, 120, 25],
        'gas_eui': [50, 25, 35, 60, 30],
        'opt_in_recommendation': ['Opt-In', 'Default', 'Opt-In', 'Opt-In', 'Default'],
        'is_epb': [False, False, True, False, True],
        'total_penalties_default': [500000, 50000, 150000, 800000, 75000]
    })
    
    # Run analysis
    analyzer = DERClusterAnalyzer(max_distance_meters=500)
    clusters_df = analyzer.analyze_clusters(sample_data)
    
    # Display results
    if not clusters_df.empty:
        print("\n📊 Top DER Cluster Opportunities:")
        print(clusters_df[['cluster_id', 'anchor_property_type', 'member_count', 
                          'total_sqft', 'epb_percentage', 'economic_potential_score']].head())
        
        # Export for mapping
        analyzer.export_cluster_geojson(
            clusters_df, 
            sample_data,
            './outputs/der_clusters.geojson'
        )
    else:
        print("No viable clusters found in sample data")


if __name__ == "__main__":
    main()