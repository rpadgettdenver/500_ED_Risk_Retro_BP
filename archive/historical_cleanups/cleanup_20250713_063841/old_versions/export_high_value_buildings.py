"""
Suggested File Name: export_high_value_buildings.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Export high-value building targets for thermal energy service business development

This script identifies and exports buildings that are:
1. High penalty exposure (need immediate solutions)
2. Can't meet targets (desperate for help)
3. Good candidates for 4-pipe WSHP + TES systems
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import os

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"


class BusinessDevelopmentExporter:
    """Export high-value building targets for business development"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        
    def export_high_value_targets(self):
        """Export buildings with highest business development potential"""
        
        print("🎯 EXPORTING HIGH-VALUE BUILDING TARGETS")
        print("=" * 60)
        
        # Query for buildings that need immediate help
        query = f"""
        WITH building_details AS (
            SELECT 
                oda.building_id,
                oda.building_name,
                oda.property_type,
                oda.gross_floor_area as sqft,
                oda.current_eui,
                oda.gap_2025,
                oda.gap_2030,
                oda.pct_reduction_2030 as reduction_needed_pct,
                oda.should_opt_in,
                oda.primary_rationale,
                oda.penalty_2025,
                oda.penalty_2027,
                oda.penalty_2030_default,
                oda.total_penalties_default,
                oda.total_penalties_optin,
                oda.npv_penalties_default,
                oda.estimated_retrofit_cost,
                oda.technical_difficulty_score,
                oda.building_age,
                
                -- Calculate annual penalty exposure if no action
                CASE 
                    WHEN oda.gap_2030 > 0 THEN oda.gap_2030 * oda.gross_floor_area * 0.15
                    ELSE 0
                END as annual_penalty_after_2030,
                
                -- EPB status (if available)
                CASE 
                    WHEN oda.property_type IN ('Affordable Housing', 'Senior Living Community') 
                    THEN TRUE 
                    ELSE FALSE 
                END as likely_epb,
                
                -- Business opportunity score
                CASE
                    -- Highest priority: Can't meet any targets + large building
                    WHEN oda.primary_rationale = 'Cannot meet any targets' 
                         AND oda.gross_floor_area > 50000 
                    THEN 100
                    
                    -- High priority: Large penalties + technical difficulty
                    WHEN oda.total_penalties_default > 500000 
                         AND oda.technical_difficulty_score >= 60
                    THEN 90
                    
                    -- Good opportunity: Multifamily with penalties
                    WHEN oda.property_type = 'Multifamily Housing' 
                         AND oda.total_penalties_default > 100000
                    THEN 80
                    
                    -- Manufacturing always interesting
                    WHEN oda.property_type = 'Manufacturing/Industrial Plant'
                    THEN 85
                    
                    -- Office buildings with high penalties
                    WHEN oda.property_type = 'Office' 
                         AND oda.total_penalties_default > 200000
                    THEN 75
                    
                    ELSE 50
                END as business_opportunity_score
                
            FROM `{self.dataset_ref}.opt_in_decision_analysis` oda
        ),
        
        ranked_opportunities AS (
            SELECT 
                *,
                -- Calculate 15-year penalty exposure
                total_penalties_default + (annual_penalty_after_2030 * 12) as total_15yr_exposure,
                
                -- Rank by opportunity
                ROW_NUMBER() OVER (
                    PARTITION BY property_type 
                    ORDER BY business_opportunity_score DESC, 
                             total_penalties_default DESC
                ) as rank_in_type,
                
                ROW_NUMBER() OVER (
                    ORDER BY business_opportunity_score DESC, 
                             total_penalties_default DESC
                ) as overall_rank
                
            FROM building_details
            WHERE gap_2030 > 0  -- Only buildings that need retrofits
        )
        
        SELECT 
            overall_rank,
            building_id,
            building_name,
            property_type,
            ROUND(sqft, 0) as sqft,
            ROUND(current_eui, 1) as current_eui,
            ROUND(reduction_needed_pct, 1) as reduction_pct,
            primary_rationale,
            
            -- Financial metrics
            ROUND(penalty_2025, 0) as penalty_2025,
            ROUND(penalty_2027, 0) as penalty_2027,
            ROUND(total_penalties_default, 0) as penalties_through_2030,
            ROUND(total_15yr_exposure, 0) as total_15yr_exposure,
            ROUND(estimated_retrofit_cost, 0) as est_retrofit_cost,
            
            -- Opportunity metrics
            business_opportunity_score,
            technical_difficulty_score,
            likely_epb,
            should_opt_in,
            
            -- Building characteristics
            building_age,
            ROUND(sqft * 0.00001, 1) as size_10k_sqft,  -- Size in 10k sqft units
            
            -- TES+HP system sizing estimate (rough)
            ROUND(sqft * 0.003, 0) as estimated_tons,  -- ~300 sqft/ton
            ROUND(sqft * 60 * 1.3, -3) as estimated_project_cost  -- $60/sqft + 30% escalation
            
        FROM ranked_opportunities
        WHERE overall_rank <= 500  -- Top 500 opportunities
        ORDER BY overall_rank
        """
        
        # Execute query
        print("\n📊 Querying high-value targets...")
        results_df = self.client.query(query).to_dataframe()
        
        print(f"✓ Found {len(results_df)} high-value building targets")
        
        # Create segmented lists
        self.create_segmented_lists(results_df)
        
        # Export to Excel with multiple sheets
        self.export_to_excel(results_df)
        
        # Generate summary statistics
        self.generate_summary_stats(results_df)
        
        return results_df
    
    def create_segmented_lists(self, df):
        """Create segmented lists for different outreach strategies"""
        
        print("\n📋 Creating segmented lists...")
        
        segments = {
            'urgent_large': df[
                (df['primary_rationale'] == 'Cannot meet any targets') & 
                (df['sqft'] > 100000)
            ],
            'multifamily_high_penalty': df[
                (df['property_type'] == 'Multifamily Housing') & 
                (df['penalties_through_2030'] > 200000)
            ],
            'manufacturing': df[
                df['property_type'] == 'Manufacturing/Industrial Plant'
            ],
            'epb_priority': df[
                df['likely_epb'] == True
            ],
            'quick_wins': df[
                (df['reduction_pct'] < 20) & 
                (df['penalties_through_2030'] > 100000) &
                (df['technical_difficulty_score'] < 40)
            ]
        }
        
        for segment_name, segment_df in segments.items():
            print(f"   {segment_name}: {len(segment_df)} buildings")
    
    def export_to_excel(self, df):
        """Export to Excel with multiple sheets for different teams"""
        
        output_path = f"high_value_buildings_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        print(f"\n📤 Exporting to {output_path}...")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main list
            df.to_excel(writer, sheet_name='All High Value Targets', index=False)
            
            # Urgent action needed
            urgent = df[df['primary_rationale'] == 'Cannot meet any targets'].head(100)
            urgent.to_excel(writer, sheet_name='Urgent - Cant Meet Targets', index=False)
            
            # By property type
            for prop_type in df['property_type'].unique()[:10]:  # Top 10 property types
                type_df = df[df['property_type'] == prop_type].head(50)
                # Clean sheet name - remove invalid characters
                sheet_name = prop_type.replace('/', '-').replace('\\', '-')[:30]  # Excel sheet name limit
                type_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Buildings',
                    'Total 15-Year Penalty Exposure',
                    'Average Building Size',
                    'Buildings Over 100k sqft',
                    'Likely EPB Buildings',
                    'Average Reduction Needed',
                    'Total Estimated Project Value'
                ],
                'Value': [
                    len(df),
                    f"${df['total_15yr_exposure'].sum():,.0f}",
                    f"{df['sqft'].mean():,.0f} sqft",
                    len(df[df['sqft'] > 100000]),
                    df['likely_epb'].sum(),
                    f"{df['reduction_pct'].mean():.1f}%",
                    f"${df['estimated_project_cost'].sum():,.0f}"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"✓ Exported to {output_path}")
    
    def generate_summary_stats(self, df):
        """Generate summary statistics for business planning"""
        
        print("\n📊 BUSINESS OPPORTUNITY SUMMARY")
        print("=" * 60)
        
        # Overall opportunity
        total_penalty_exposure = df['total_15yr_exposure'].sum()
        total_project_value = df['estimated_project_cost'].sum()
        
        print(f"\n💰 Total Market Opportunity:")
        print(f"   15-Year Penalty Exposure: ${total_penalty_exposure:,.0f}")
        print(f"   Estimated Project Value: ${total_project_value:,.0f}")
        print(f"   Number of Buildings: {len(df)}")
        
        # By property type
        print(f"\n🏢 Top Property Types by Opportunity:")
        prop_summary = df.groupby('property_type').agg({
            'building_id': 'count',
            'total_15yr_exposure': 'sum',
            'estimated_project_cost': 'sum',
            'sqft': 'mean'
        }).sort_values('total_15yr_exposure', ascending=False).head(10)
        
        for prop_type, row in prop_summary.iterrows():
            print(f"\n   {prop_type}:")
            print(f"      Buildings: {row['building_id']}")
            print(f"      Avg Size: {row['sqft']:,.0f} sqft")
            print(f"      15-yr Exposure: ${row['total_15yr_exposure']:,.0f}")
            print(f"      Project Value: ${row['estimated_project_cost']:,.0f}")
        
        # Urgent opportunities
        urgent = df[df['primary_rationale'] == 'Cannot meet any targets']
        print(f"\n🚨 Urgent Opportunities (Can't Meet Any Targets):")
        print(f"   Buildings: {len(urgent)}")
        print(f"   Total Project Value: ${urgent['estimated_project_cost'].sum():,.0f}")
        print(f"   Average Size: {urgent['sqft'].mean():,.0f} sqft")
        
        # Quick wins
        quick_wins = df[
            (df['reduction_pct'] < 20) & 
            (df['technical_difficulty_score'] < 40)
        ]
        print(f"\n✅ Quick Wins (Low Reduction, Low Difficulty):")
        print(f"   Buildings: {len(quick_wins)}")
        print(f"   Total Project Value: ${quick_wins['estimated_project_cost'].sum():,.0f}")
        print(f"   Avg Penalty Savings: ${quick_wins['total_15yr_exposure'].mean():,.0f}")


def main():
    """Main execution"""
    
    print("🏢 ENERGIZE DENVER - HIGH VALUE BUILDING EXPORT")
    print("=" * 80)
    print("\nThis tool exports buildings with the highest potential for")
    print("thermal energy service (TES+HP) business development.\n")
    
    exporter = BusinessDevelopmentExporter()
    
    # Export high-value targets
    df = exporter.export_high_value_targets()
    
    print("\n\n✅ Export complete!")
    print("\nUse the Excel file for:")
    print("- Sales team outreach lists")
    print("- Project pipeline development")
    print("- Financial modeling")
    print("- Grant application targeting")
    
    # Optional: Show top 10
    response = input("\nShow top 10 opportunities? (y/n): ")
    if response.lower() == 'y':
        print("\n🏆 TOP 10 OPPORTUNITIES:")
        print("-" * 120)
        
        top10 = df.head(10)[['overall_rank', 'building_name', 'property_type', 
                            'sqft', 'total_15yr_exposure', 'estimated_project_cost']]
        
        for _, row in top10.iterrows():
            print(f"\n#{row['overall_rank']} - {row['building_name'][:40]}")
            print(f"   Type: {row['property_type']}")
            print(f"   Size: {row['sqft']:,.0f} sqft")
            print(f"   15-yr Penalty: ${row['total_15yr_exposure']:,.0f}")
            print(f"   Est. Project: ${row['estimated_project_cost']:,.0f}")


if __name__ == "__main__":
    main()
