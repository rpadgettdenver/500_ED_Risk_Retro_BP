"""
Suggested File Name: cluster_analysis_bigquery.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Identify clusters of buildings that could share thermal infrastructure (ambient loops,
     heat recovery, thermal storage) using BigQuery's geospatial functions

This script:
1. Uses BigQuery's ST_DISTANCE to find nearby buildings
2. Identifies high-value clusters based on penalty exposure and building types
3. Finds opportunities for waste heat recovery (e.g., data centers + offices)
4. Prioritizes Equity Priority Buildings (EPBs) in cluster formation
5. Exports results as GeoJSON for visualization
"""

from google.cloud import bigquery
import pandas as pd
import json
from datetime import datetime

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

class DERClusterAnalysis:
    """Analyze building clusters for distributed energy resource opportunities"""
    
    def __init__(self):
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        
    def create_clustering_view(self, distance_meters=500):
        """Create a view that identifies building clusters within specified distance"""
        
        view_id = f"{self.dataset_ref}.building_clusters"
        
        query = f"""
        CREATE OR REPLACE VIEW `{view_id}` AS
        WITH building_points AS (
            -- Convert lat/lon to geography points
            SELECT 
                building_id,
                COALESCE(building_name, consumption_building_name, 
                         CONCAT('Building ', building_id)) as building_name,
                property_type,
                gross_floor_area,
                actual_eui,
                annual_penalty_2024,
                risk_category,
                is_epb,
                latitude,
                longitude,
                ST_GEOGPOINT(longitude, latitude) as location
            FROM `{self.dataset_ref}.penalty_analysis`
            WHERE latitude IS NOT NULL 
                AND longitude IS NOT NULL
                AND latitude BETWEEN 39.0 AND 40.5  -- Denver area bounds
                AND longitude BETWEEN -106.0 AND -104.0
        ),
        
        -- Find all building pairs within distance threshold
        nearby_pairs AS (
            SELECT 
                a.building_id as building_a,
                b.building_id as building_b,
                a.building_name as name_a,
                b.building_name as name_b,
                a.property_type as type_a,
                b.property_type as type_b,
                a.gross_floor_area as sqft_a,
                b.gross_floor_area as sqft_b,
                a.annual_penalty_2024 as penalty_a,
                b.annual_penalty_2024 as penalty_b,
                a.is_epb as epb_a,
                b.is_epb as epb_b,
                a.location as location_a,
                b.location as location_b,
                ST_DISTANCE(a.location, b.location) as distance_meters
            FROM building_points a
            CROSS JOIN building_points b
            WHERE a.building_id < b.building_id  -- Avoid duplicates
                AND ST_DISTANCE(a.location, b.location) <= {distance_meters}
        ),
        
        -- Identify synergistic pairs (e.g., data center + office)
        synergy_scores AS (
            SELECT 
                *,
                -- Calculate synergy score based on complementary building types
                CASE 
                    -- Data center (heat source) + Office/Multifamily (heat sink)
                    WHEN (type_a = 'Data Center' AND type_b IN ('Office', 'Multifamily Housing'))
                      OR (type_b = 'Data Center' AND type_a IN ('Office', 'Multifamily Housing'))
                    THEN 3.0
                    
                    -- Hospital/Medical (24/7 heat) + Residential
                    WHEN (type_a LIKE '%Hospital%' AND type_b LIKE '%Multifamily%')
                      OR (type_b LIKE '%Hospital%' AND type_a LIKE '%Multifamily%')
                    THEN 2.5
                    
                    -- Mixed use combinations
                    WHEN type_a != type_b THEN 1.5
                    
                    -- Same type (economies of scale)
                    ELSE 1.0
                END as synergy_multiplier,
                
                -- Prioritize EPB involvement
                CASE 
                    WHEN epb_a = 1 AND epb_b = 1 THEN 2.0
                    WHEN epb_a = 1 OR epb_b = 1 THEN 1.5
                    ELSE 1.0
                END as epb_multiplier,
                
                -- Combined penalty exposure
                COALESCE(penalty_a, 0) + COALESCE(penalty_b, 0) as combined_penalty
                
            FROM nearby_pairs
        )
        
        -- Final cluster opportunities with scoring
        SELECT 
            *,
            -- Calculate opportunity score
            (combined_penalty * synergy_multiplier * epb_multiplier / 
             GREATEST(distance_meters, 100)) as opportunity_score,
            
            -- Cluster size potential
            sqft_a + sqft_b as total_sqft,
            
            -- Classify opportunity type
            CASE 
                WHEN synergy_multiplier >= 2.5 THEN 'Heat Recovery'
                WHEN synergy_multiplier >= 1.5 THEN 'Shared System'
                ELSE 'Economies of Scale'
            END as opportunity_type
            
        FROM synergy_scores
        WHERE combined_penalty > 0  -- Focus on buildings with penalty exposure
        ORDER BY opportunity_score DESC
        """
        
        print(f"Creating clustering view with {distance_meters}m radius...")
        
        try:
            self.bq_client.query(query).result()
            print(f"✓ Created clustering view: {view_id}")
            return view_id
        except Exception as e:
            print(f"❌ Error creating clustering view: {str(e)}")
            return None
    
    def analyze_cluster_potential(self):
        """Analyze the potential for different types of clusters"""
        
        print("\n=== CLUSTER OPPORTUNITY ANALYSIS ===\n")
        
        # Summary by opportunity type
        query = f"""
        SELECT 
            opportunity_type,
            COUNT(*) as pair_count,
            ROUND(AVG(distance_meters), 0) as avg_distance_m,
            ROUND(SUM(combined_penalty), 0) as total_penalty_exposure,
            ROUND(AVG(total_sqft), 0) as avg_cluster_sqft,
            COUNT(CASE WHEN epb_a = 1 OR epb_b = 1 THEN 1 END) as epb_involved
        FROM `{self.dataset_ref}.building_clusters`
        GROUP BY opportunity_type
        ORDER BY total_penalty_exposure DESC
        """
        
        results = self.bq_client.query(query).to_dataframe()
        
        print("Cluster Opportunities by Type:")
        print("-" * 80)
        for _, row in results.iterrows():
            print(f"{row['opportunity_type']:<20} | "
                  f"{row['pair_count']:>5} pairs | "
                  f"${row['total_penalty_exposure']:>12,.0f} exposure | "
                  f"{row['avg_distance_m']:>4.0f}m avg | "
                  f"{row['epb_involved']:>3} EPB")
        
        # Top individual opportunities
        print("\n\nTop 10 Cluster Opportunities:")
        print("-" * 100)
        
        query2 = f"""
        SELECT 
            name_a,
            name_b,
            type_a,
            type_b,
            ROUND(distance_meters, 0) as distance_m,
            opportunity_type,
            ROUND(combined_penalty, 0) as combined_penalty,
            ROUND(opportunity_score, 2) as score,
            CASE WHEN epb_a = 1 OR epb_b = 1 THEN '✓' ELSE '' END as has_epb
        FROM `{self.dataset_ref}.building_clusters`
        ORDER BY opportunity_score DESC
        LIMIT 10
        """
        
        top_clusters = self.bq_client.query(query2).to_dataframe()
        
        for _, row in top_clusters.iterrows():
            print(f"{row['name_a'][:25]:<25} + {row['name_b'][:25]:<25} | "
                  f"{row['distance_m']:>4.0f}m | "
                  f"${row['combined_penalty']:>10,.0f} | "
                  f"{row['opportunity_type']:<15} | "
                  f"Score: {row['score']:>6.2f} {row['has_epb']}")
    
    def export_cluster_geojson(self, limit=100):
        """Export top clusters as GeoJSON for visualization"""
        
        print("\n=== EXPORTING CLUSTER GEOJSON ===")
        
        query = f"""
        WITH top_clusters AS (
            SELECT 
                building_a,
                building_b,
                name_a,
                name_b,
                type_a,
                type_b,
                location_a,
                location_b,
                distance_meters,
                opportunity_type,
                combined_penalty,
                opportunity_score,
                epb_a,
                epb_b
            FROM `{self.dataset_ref}.building_clusters`
            ORDER BY opportunity_score DESC
            LIMIT {limit}
        )
        SELECT 
            building_a,
            building_b,
            name_a,
            name_b,
            type_a,
            type_b,
            ST_X(location_a) as lon_a,
            ST_Y(location_a) as lat_a,
            ST_X(location_b) as lon_b,
            ST_Y(location_b) as lat_b,
            distance_meters,
            opportunity_type,
            combined_penalty,
            opportunity_score,
            epb_a,
            epb_b
        FROM top_clusters
        """
        
        df = self.bq_client.query(query).to_dataframe()
        
        # Create GeoJSON structure
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for _, row in df.iterrows():
            # Create line feature connecting the two buildings
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [row['lon_a'], row['lat_a']],
                        [row['lon_b'], row['lat_b']]
                    ]
                },
                "properties": {
                    "building_a": row['building_a'],
                    "building_b": row['building_b'],
                    "name_a": row['name_a'],
                    "name_b": row['name_b'],
                    "type_a": row['type_a'],
                    "type_b": row['type_b'],
                    "distance_m": round(row['distance_meters'], 0),
                    "opportunity_type": row['opportunity_type'],
                    "penalty_exposure": round(row['combined_penalty'], 0),
                    "score": round(row['opportunity_score'], 2),
                    "has_epb": bool(row['epb_a'] or row['epb_b']),
                    "color": "#ff0000" if row['opportunity_type'] == 'Heat Recovery' else
                            "#ff8800" if row['opportunity_type'] == 'Shared System' else
                            "#0088ff"
                }
            }
            geojson['features'].append(feature)
        
        # Save to file
        output_path = "outputs/cluster_opportunities.geojson"
        with open(output_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        print(f"✓ Exported {len(df)} cluster opportunities to {output_path}")
        print("\nVisualization tips:")
        print("- Red lines: Heat recovery opportunities")
        print("- Orange lines: Shared system opportunities")
        print("- Blue lines: Economies of scale")
        print("- Upload to geojson.io or use in Looker Studio maps")
        
        return output_path
    
    def create_cluster_summary_table(self):
        """Create a summary table for business development"""
        
        table_id = f"{self.dataset_ref}.cluster_opportunities_summary"
        
        query = f"""
        CREATE OR REPLACE TABLE `{table_id}` AS
        WITH cluster_stats AS (
            SELECT 
                building_a as building_id,
                COUNT(*) as connection_count,
                AVG(distance_meters) as avg_distance,
                SUM(CASE WHEN opportunity_type = 'Heat Recovery' THEN 1 ELSE 0 END) as heat_recovery_opps,
                SUM(CASE WHEN opportunity_type = 'Shared System' THEN 1 ELSE 0 END) as shared_system_opps,
                MAX(opportunity_score) as max_opportunity_score
            FROM `{self.dataset_ref}.building_clusters`
            GROUP BY building_a
            
            UNION ALL
            
            SELECT 
                building_b as building_id,
                COUNT(*) as connection_count,
                AVG(distance_meters) as avg_distance,
                SUM(CASE WHEN opportunity_type = 'Heat Recovery' THEN 1 ELSE 0 END) as heat_recovery_opps,
                SUM(CASE WHEN opportunity_type = 'Shared System' THEN 1 ELSE 0 END) as shared_system_opps,
                MAX(opportunity_score) as max_opportunity_score
            FROM `{self.dataset_ref}.building_clusters`
            GROUP BY building_b
        ),
        building_summary AS (
            SELECT 
                building_id,
                SUM(connection_count) as total_connections,
                AVG(avg_distance) as avg_connection_distance,
                SUM(heat_recovery_opps) as total_heat_recovery_opps,
                SUM(shared_system_opps) as total_shared_system_opps,
                MAX(max_opportunity_score) as best_opportunity_score
            FROM cluster_stats
            GROUP BY building_id
        )
        SELECT 
            b.*,
            p.building_name,
            p.property_type,
            p.gross_floor_area,
            p.annual_penalty_2024,
            p.risk_category,
            p.is_epb,
            p.latitude,
            p.longitude,
            -- Categorize cluster potential
            CASE 
                WHEN b.total_heat_recovery_opps > 0 THEN 'Prime Heat Recovery'
                WHEN b.total_connections >= 5 THEN 'Hub Building'
                WHEN b.total_connections >= 2 THEN 'Good Cluster Potential'
                ELSE 'Limited Cluster Potential'
            END as cluster_category
        FROM building_summary b
        JOIN `{self.dataset_ref}.penalty_analysis` p
            ON b.building_id = p.building_id
        ORDER BY best_opportunity_score DESC
        """
        
        print("\nCreating cluster opportunity summary table...")
        
        self.bq_client.query(query).result()
        print(f"✓ Created summary table: {table_id}")
        
        # Get key statistics
        stats_query = f"""
        SELECT 
            cluster_category,
            COUNT(*) as building_count,
            SUM(CASE WHEN is_epb = 1 THEN 1 ELSE 0 END) as epb_count,
            ROUND(SUM(annual_penalty_2024), 0) as total_penalty_exposure
        FROM `{table_id}`
        GROUP BY cluster_category
        ORDER BY building_count DESC
        """
        
        results = self.bq_client.query(stats_query).to_dataframe()
        
        print("\nCluster Potential Summary:")
        print("-" * 70)
        for _, row in results.iterrows():
            print(f"{row['cluster_category']:<25} | "
                  f"{row['building_count']:>5} buildings | "
                  f"{row['epb_count']:>3} EPB | "
                  f"${row['total_penalty_exposure']:>12,.0f}")
    
    def run_full_analysis(self):
        """Run the complete cluster analysis pipeline"""
        
        print("Starting DER Cluster Analysis...")
        print("=" * 80)
        
        # Create clustering view
        view_id = self.create_clustering_view(distance_meters=500)
        
        if view_id:
            # Analyze potential
            self.analyze_cluster_potential()
            
            # Export visualization
            self.export_cluster_geojson(limit=100)
            
            # Create summary table
            self.create_cluster_summary_table()
            
            print("\n✅ Cluster analysis complete!")
            print("\nBusiness development insights:")
            print("1. Focus on 'Prime Heat Recovery' buildings for highest value")
            print("2. 'Hub Buildings' can anchor district energy systems")
            print("3. EPB clusters qualify for additional funding")
            print("4. Use GeoJSON output for sales team mapping")


def main():
    """Main execution"""
    analyzer = DERClusterAnalysis()
    
    try:
        analyzer.run_full_analysis()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
