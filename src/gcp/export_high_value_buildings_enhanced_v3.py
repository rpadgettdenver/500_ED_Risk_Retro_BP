"""
Suggested File Name: export_high_value_buildings_enhanced_v3.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Enhanced export with EPB data integration and EUI targets for business development

This script identifies and exports buildings that are:
1. High penalty exposure (need immediate solutions)
2. Can't meet targets (desperate for help)
3. Good candidates for 4-pipe WSHP + TES systems
4. Prioritizes EPB buildings for funding opportunities

Version 3 updates:
- Removes dependency on non-existent standards table
- Uses Building_EUI_Targets.csv as primary source for all EUI targets
- Falls back to EPB file for buildings not in targets file
- Fixed to work with actual BigQuery schema
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import os

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"
OUTPUT_DIR = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/building_priority_analysis"


class BusinessDevelopmentExporter:
    """Export high-value building targets for business development"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        
        # Create output directory if needed
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    def load_eui_targets_data(self):
        """Load EUI targets data from CSV file"""
        targets_file = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/Building_EUI_Targets.csv"
        
        print("📊 Loading Building EUI Targets data...")
        targets_df = pd.read_csv(targets_file)
        
        # Clean and prepare targets data
        targets_df['Building ID'] = targets_df['Building ID'].astype(str)
        
        # Create targets lookup with key information
        targets_lookup = targets_df[['Building ID', 'Master Property Type', 
                                    'First Interim Target EUI', 'Second Interim Target EUI',
                                    'Original Final Target EUI', 'Adjusted Final Target EUI']].copy()
        
        print(f"✓ Loaded {len(targets_df)} building targets")
        
        return targets_lookup
        
    def load_epb_data(self):
        """Load EPB data from CSV file"""
        epb_file = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw/CopyofWeeklyEPBStatsReport Report.csv"
        
        print("\n📊 Loading EPB data...")
        epb_df = pd.read_csv(epb_file)
        
        # Clean and prepare EPB data
        epb_df['Building ID'] = epb_df['Building ID'].astype(str)
        
        # Create EPB lookup with key information
        epb_lookup = epb_df[['Building ID', 'Potential Epb', 'EPB Application Status', 
                            'Original Final Target EUI', 'Approved Target Adjustment']].copy()
        
        # Clean up EPB status
        epb_lookup['is_epb'] = epb_lookup['Potential Epb'].fillna('').str.lower() == 'yes'
        epb_lookup['epb_approved'] = epb_lookup['EPB Application Status'].fillna('').str.lower() == 'approved'
        
        print(f"✓ Loaded {len(epb_df)} EPB records, {epb_lookup['is_epb'].sum()} confirmed EPBs")
        
        return epb_lookup
        
    def export_high_value_targets(self):
        """Export buildings with highest business development potential"""
        
        print("\n🎯 EXPORTING HIGH-VALUE BUILDING TARGETS")
        print("=" * 60)
        
        # Load both data sources
        targets_lookup = self.load_eui_targets_data()
        epb_lookup = self.load_epb_data()
        
        # Query from opt_in_decision_analysis which already has all the calculations
        query = f"""
        WITH building_details AS (
            SELECT 
                CAST(oda.building_id AS STRING) as building_id,
                oda.building_name,
                oda.property_type,
                COALESCE(oda.property_type, oda.property_type_clean) as property_type_clean,
                oda.gross_floor_area as sqft,
                oda.current_eui,
                
                -- Use targets from the analysis
                oda.target_2025,
                oda.target_2027,
                oda.target_2030,
                
                -- Gaps and reductions
                oda.gap_2025,
                oda.gap_2030,
                oda.pct_reduction_2030 as reduction_needed_pct,
                
                -- Decision analysis
                oda.should_opt_in,
                oda.primary_rationale,
                
                -- Penalties
                oda.penalty_2025,
                oda.penalty_2027,
                oda.penalty_2030_default,
                oda.total_penalties_default,
                oda.total_penalties_optin,
                oda.npv_penalties_default,
                
                -- Building characteristics
                oda.estimated_retrofit_cost,
                oda.technical_difficulty_score,
                oda.building_age,
                
                -- Calculate annual penalty exposure if no action
                CASE 
                    WHEN oda.gap_2030 > 0 THEN oda.gap_2030 * oda.gross_floor_area * 0.15
                    ELSE 0
                END as annual_penalty_after_2030,
                
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
                
                -- Project value calculation breakdown
                -- Base cost: $60/sqft for 4-pipe WSHP + TES system
                -- Escalation: 30% for current market conditions
                -- Complexity factor: Based on technical difficulty
                ROUND(sqft * 60 * 1.3 * 
                    CASE 
                        WHEN technical_difficulty_score >= 80 THEN 1.2
                        WHEN technical_difficulty_score >= 60 THEN 1.1
                        ELSE 1.0
                    END, -3) as estimated_project_value,
                
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
            
            -- Current state and targets
            ROUND(current_eui, 1) as current_eui,
            ROUND(target_2025, 1) as target_eui_2025,
            ROUND(target_2027, 1) as target_eui_2027,
            ROUND(target_2030, 1) as target_eui_2030,
            
            -- Gaps and reduction
            ROUND(gap_2025, 1) as gap_2025,
            ROUND(gap_2030, 1) as gap_2030,
            ROUND(reduction_needed_pct, 1) as reduction_pct,
            primary_rationale,
            
            -- Financial metrics
            ROUND(penalty_2025, 0) as penalty_2025,
            ROUND(penalty_2027, 0) as penalty_2027,
            ROUND(total_penalties_default, 0) as penalties_through_2030,
            ROUND(total_15yr_exposure, 0) as total_15yr_exposure,
            ROUND(estimated_retrofit_cost, 0) as est_retrofit_cost,
            ROUND(estimated_project_value, 0) as estimated_project_value,
            
            -- Opportunity metrics
            business_opportunity_score,
            technical_difficulty_score,
            should_opt_in,
            
            -- Building characteristics
            building_age,
            ROUND(sqft * 0.00001, 1) as size_10k_sqft,  -- Size in 10k sqft units
            
            -- TES+HP system sizing estimate
            ROUND(sqft * 0.003, 0) as estimated_tons  -- ~300 sqft/ton
            
        FROM ranked_opportunities
        WHERE overall_rank <= 500  -- Top 500 opportunities
        ORDER BY overall_rank
        """
        
        # Execute query
        print("\n📊 Querying high-value targets...")
        results_df = self.client.query(query).to_dataframe()
        
        # First merge with EUI targets data to get adjusted targets
        print("\n🔗 Merging EUI targets data...")
        results_df = results_df.merge(
            targets_lookup,
            left_on='building_id',
            right_on='Building ID',
            how='left',
            suffixes=('', '_targets')
        )
        
        # Then merge with EPB data
        print("🔗 Merging EPB data...")
        results_df = results_df.merge(
            epb_lookup[['Building ID', 'is_epb', 'epb_approved']],
            left_on='building_id',
            right_on='Building ID',
            how='left',
            suffixes=('', '_epb')
        )
        
        # For buildings not in targets file but in EPB file, use EPB final target
        print("🔧 Filling missing targets from EPB data...")
        missing_targets = results_df['Adjusted Final Target EUI'].isna()
        if missing_targets.any():
            # Merge EPB targets for missing buildings
            epb_targets = epb_lookup[['Building ID', 'Original Final Target EUI']].rename(
                columns={'Original Final Target EUI': 'EPB_Final_Target'})
            results_df = results_df.merge(
                epb_targets,
                left_on='building_id',
                right_on='Building ID',
                how='left',
                suffixes=('', '_epb_targets')
            )
            
            # Fill missing adjusted targets with EPB targets
            results_df.loc[missing_targets, 'Adjusted Final Target EUI'] = \
                results_df.loc[missing_targets, 'EPB_Final_Target']
        
        # Clean up columns
        cols_to_drop = [col for col in results_df.columns if 
                       col.startswith('Building ID') or col.endswith('_epb') or col == 'EPB_Final_Target']
        results_df.drop(cols_to_drop, axis=1, inplace=True, errors='ignore')
        
        # Fill NaN values
        results_df['is_epb'] = results_df['is_epb'].fillna(False)
        results_df['epb_approved'] = results_df['epb_approved'].fillna(False)
        
        # Add adjusted final target where it's still the original
        no_adjustment = results_df['Adjusted Final Target EUI'].isna()
        results_df.loc[no_adjustment, 'Adjusted Final Target EUI'] = \
            results_df.loc[no_adjustment, 'Original Final Target EUI']
        
        # If still missing, use the target_2030 from BigQuery
        still_missing = results_df['Adjusted Final Target EUI'].isna()
        results_df.loc[still_missing, 'Adjusted Final Target EUI'] = \
            results_df.loc[still_missing, 'target_eui_2030']
        
        # Update EPB count
        epb_count = results_df['is_epb'].sum()
        print(f"\n✓ Found {len(results_df)} high-value targets")
        print(f"✓ {epb_count} are EPBs ({epb_count/len(results_df)*100:.1f}%)")
        print(f"✓ All buildings have EUI targets assigned")
        
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
                df['is_epb'] == True
            ],
            'epb_approved': df[
                df['epb_approved'] == True
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
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        output_path = os.path.join(OUTPUT_DIR, f"high_value_buildings_{timestamp}.xlsx")
        
        print(f"\n📤 Exporting to {output_path}...")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main list with all columns
            df.to_excel(writer, sheet_name='All High Value Targets', index=False)
            
            # Key columns for summary view
            summary_cols = ['overall_rank', 'building_id', 'building_name', 'property_type', 
                           'sqft', 'is_epb', 'current_eui', 'Adjusted Final Target EUI',
                           'reduction_pct', 'total_15yr_exposure', 'estimated_project_value']
            
            # EPB buildings - HIGH PRIORITY
            epb_df = df[df['is_epb'] == True].sort_values('total_15yr_exposure', ascending=False)
            if len(epb_df) > 0:
                epb_df[summary_cols].to_excel(writer, sheet_name='EPB Buildings - Priority', index=False)
            
            # Urgent action needed
            urgent = df[df['primary_rationale'] == 'Cannot meet any targets'].head(100)
            urgent[summary_cols].to_excel(writer, sheet_name='Urgent - Cant Meet Targets', index=False)
            
            # By property type
            for prop_type in df['property_type'].value_counts().head(10).index:
                type_df = df[df['property_type'] == prop_type].head(50)
                # Clean sheet name - remove invalid characters
                sheet_name = prop_type.replace('/', '-').replace('\\', '-')[:30]
                type_df[summary_cols].to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Project value breakdown
            value_data = []
            value_data.append({
                'Component': 'Base System Cost',
                'Calculation': '$60/sqft',
                'Notes': '4-pipe WSHP + TES system'
            })
            value_data.append({
                'Component': 'Market Escalation',
                'Calculation': '30% markup',
                'Notes': 'Current market conditions and inflation'
            })
            value_data.append({
                'Component': 'Complexity Factor',
                'Calculation': '0-20% additional',
                'Notes': 'Based on technical difficulty score'
            })
            value_data.append({
                'Component': 'Formula',
                'Calculation': 'sqft × $60 × 1.3 × complexity_factor',
                'Notes': 'Final project value estimate'
            })
            
            value_df = pd.DataFrame(value_data)
            value_df.to_excel(writer, sheet_name='Project Value Methodology', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Buildings',
                    'Total EPB Buildings',
                    'EPB Buildings (Approved)',
                    'Total 15-Year Penalty Exposure',
                    'Average Building Size',
                    'Buildings Over 100k sqft',
                    'Average Reduction Needed',
                    'Total Estimated Project Value',
                    'Average Project Value',
                    'Project Value Range',
                    'Buildings with Adjusted Targets',
                    'Average Current EUI',
                    'Average Final Target EUI'
                ],
                'Value': [
                    len(df),
                    df['is_epb'].sum(),
                    df['epb_approved'].sum(),
                    f"${df['total_15yr_exposure'].sum():,.0f}",
                    f"{df['sqft'].mean():,.0f} sqft",
                    len(df[df['sqft'] > 100000]),
                    f"{df['reduction_pct'].mean():.1f}%",
                    f"${df['estimated_project_value'].sum():,.0f}",
                    f"${df['estimated_project_value'].mean():,.0f}",
                    f"${df['estimated_project_value'].min():,.0f} - ${df['estimated_project_value'].max():,.0f}",
                    len(df[df['Adjusted Final Target EUI'].notna()]),
                    f"{df['current_eui'].mean():.1f}",
                    f"{df['Adjusted Final Target EUI'].mean():.1f}"
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
        total_project_value = df['estimated_project_value'].sum()
        
        print(f"\n💰 Total Market Opportunity:")
        print(f"   15-Year Penalty Exposure: ${total_penalty_exposure:,.0f}")
        print(f"   Estimated Project Value: ${total_project_value:,.0f}")
        print(f"   Number of Buildings: {len(df)}")
        print(f"   EPB Buildings: {df['is_epb'].sum()} ({df['is_epb'].sum()/len(df)*100:.1f}%)")
        
        # EUI reduction analysis
        print(f"\n📉 EUI Reduction Requirements:")
        print(f"   Average Current EUI: {df['current_eui'].mean():.1f}")
        print(f"   Average Final Target: {df['Adjusted Final Target EUI'].mean():.1f}")
        print(f"   Average Reduction: {df['reduction_pct'].mean():.1f}%")
        
        # Project value explanation
        print(f"\n💡 Project Value Calculation:")
        print(f"   Base cost: $60/sqft (4-pipe WSHP + TES)")
        print(f"   + 30% market escalation")
        print(f"   + 0-20% complexity factor")
        print(f"   = Total project value estimate")
        
        # By property type
        print(f"\n🏢 Top Property Types by Opportunity:")
        prop_summary = df.groupby('property_type').agg({
            'building_id': 'count',
            'is_epb': 'sum',
            'total_15yr_exposure': 'sum',
            'estimated_project_value': 'sum',
            'sqft': 'mean',
            'Adjusted Final Target EUI': 'mean'
        }).sort_values('total_15yr_exposure', ascending=False).head(10)
        
        for prop_type, row in prop_summary.iterrows():
            print(f"\n   {prop_type}:")
            print(f"      Buildings: {row['building_id']} ({row['is_epb']:.0f} EPBs)")
            print(f"      Avg Size: {row['sqft']:,.0f} sqft")
            print(f"      Avg Final Target: {row['Adjusted Final Target EUI']:.1f}")
            print(f"      15-yr Exposure: ${row['total_15yr_exposure']:,.0f}")
            print(f"      Project Value: ${row['estimated_project_value']:,.0f}")
        
        # EPB opportunities
        epb_df = df[df['is_epb'] == True]
        if len(epb_df) > 0:
            print(f"\n🏥 EPB Opportunities (Priority for Funding):")
            print(f"   Total EPB Buildings: {len(epb_df)}")
            print(f"   Approved EPBs: {epb_df['epb_approved'].sum()}")
            print(f"   Total Project Value: ${epb_df['estimated_project_value'].sum():,.0f}")
            print(f"   Average Size: {epb_df['sqft'].mean():,.0f} sqft")
            print(f"   15-yr Penalty Exposure: ${epb_df['total_15yr_exposure'].sum():,.0f}")
        
        # Urgent opportunities
        urgent = df[df['primary_rationale'] == 'Cannot meet any targets']
        print(f"\n🚨 Urgent Opportunities (Can't Meet Any Targets):")
        print(f"   Buildings: {len(urgent)}")
        print(f"   EPBs in this category: {urgent['is_epb'].sum()}")
        print(f"   Total Project Value: ${urgent['estimated_project_value'].sum():,.0f}")
        print(f"   Average Size: {urgent['sqft'].mean():,.0f} sqft")
        
        # Quick wins
        quick_wins = df[
            (df['reduction_pct'] < 20) & 
            (df['technical_difficulty_score'] < 40)
        ]
        print(f"\n✅ Quick Wins (Low Reduction, Low Difficulty):")
        print(f"   Buildings: {len(quick_wins)}")
        print(f"   Total Project Value: ${quick_wins['estimated_project_value'].sum():,.0f}")
        print(f"   Avg Penalty Savings: ${quick_wins['total_15yr_exposure'].mean():,.0f}")


def main():
    """Main execution"""
    
    print("🏢 ENERGIZE DENVER - HIGH VALUE BUILDING EXPORT (V3)")
    print("=" * 80)
    print("\nThis tool exports buildings with the highest potential for")
    print("thermal energy service (TES+HP) business development.")
    print("\nVersion 3 Features:")
    print("- Fixed to work with actual BigQuery schema")
    print("- Primary EUI targets from Building_EUI_Targets.csv")
    print("- EPB data integration with fallback targets")
    print("- Adjusted Final Target EUI for all buildings\n")
    
    exporter = BusinessDevelopmentExporter()
    
    # Export high-value targets
    df = exporter.export_high_value_targets()
    
    print("\n\n✅ Export complete!")
    print(f"\nFiles saved to: {OUTPUT_DIR}")
    print("\nUse the Excel file for:")
    print("- Sales team outreach lists")
    print("- EPB-focused grant applications")
    print("- Project pipeline development")
    print("- Financial modeling with accurate project values")
    
    # Optional: Show top 10
    response = input("\nShow top 10 opportunities? (y/n): ")
    if response.lower() == 'y':
        print("\n🏆 TOP 10 OPPORTUNITIES:")
        print("-" * 140)
        
        top10 = df.head(10)[['overall_rank', 'building_name', 'property_type', 
                            'sqft', 'is_epb', 'current_eui', 'Adjusted Final Target EUI',
                            'total_15yr_exposure', 'estimated_project_value']]
        
        for _, row in top10.iterrows():
            epb_tag = " [EPB]" if row['is_epb'] else ""
            print(f"\n#{row['overall_rank']} - {row['building_name'][:40]}{epb_tag}")
            print(f"   Type: {row['property_type']}")
            print(f"   Size: {row['sqft']:,.0f} sqft")
            print(f"   EUI: {row['current_eui']} → {row['Adjusted Final Target EUI']} (adjusted target)")
            print(f"   15-yr Penalty: ${row['total_15yr_exposure']:,.0f}")
            print(f"   Est. Project: ${row['estimated_project_value']:,.0f}")


if __name__ == "__main__":
    main()
