"""
Suggested File Name: rerun_and_compare_analysis.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Re-run BigQuery opt-in analysis and compare with previous results

This script:
1. Captures current analysis results (if any)
2. Re-runs the opt-in decision model
3. Compares before/after results
4. Validates specific buildings (like 2952)
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import os

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"


class AnalysisComparison:
    """Compare BigQuery analysis results before and after updates"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        
    def capture_current_results(self):
        """Capture current opt-in recommendations if they exist"""
        
        print("📸 Capturing current analysis results (if any)...")
        
        # Check if recommendations table exists
        table_id = f"{self.dataset_ref}.opt_in_recommendations"
        
        try:
            # Get current recommendations
            query = f"""
            SELECT 
                building_id,
                building_name,
                property_type,
                sqft,
                current_eui,
                reduction_needed_pct,
                recommended_opt_in,
                penalties_if_default,
                penalties_if_optin,
                npv_benefit_of_optin,
                primary_rationale,
                analysis_timestamp
            FROM `{table_id}`
            ORDER BY building_id
            """
            
            current_df = self.client.query(query).to_dataframe()
            
            # Save to CSV for comparison
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"opt_in_recommendations_backup_{timestamp}.csv"
            current_df.to_csv(backup_path, index=False)
            
            print(f"✓ Saved {len(current_df)} current recommendations to {backup_path}")
            
            # Get summary statistics
            opt_in_count = current_df['recommended_opt_in'].sum()
            print(f"\nCurrent Analysis Summary:")
            print(f"  Total buildings: {len(current_df)}")
            print(f"  Recommended opt-in: {opt_in_count} ({opt_in_count/len(current_df)*100:.1f}%)")
            print(f"  Recommended default: {len(current_df) - opt_in_count}")
            
            return current_df
            
        except Exception as e:
            print(f"⚠️  No current results found or error: {str(e)}")
            return None
    
    def run_updated_analysis(self):
        """Re-run the opt-in decision analysis"""
        
        print("\n🔄 Re-running opt-in decision analysis with correct penalty rates...")
        
        # Import and run the opt-in model
        from create_opt_in_decision_model import main as run_opt_in_model
        
        # Run the analysis
        run_opt_in_model()
        
        print("\n✓ Analysis complete!")
    
    def compare_results(self, before_df):
        """Compare before and after results"""
        
        if before_df is None:
            print("\n⚠️  No previous results to compare")
            return
            
        print("\n📊 Comparing analysis results...")
        
        # Get new results
        table_id = f"{self.dataset_ref}.opt_in_recommendations"
        
        query = f"""
        SELECT 
            building_id,
            building_name,
            property_type,
            sqft,
            current_eui,
            reduction_needed_pct,
            recommended_opt_in,
            penalties_if_default,
            penalties_if_optin,
            npv_benefit_of_optin,
            primary_rationale
        FROM `{table_id}`
        ORDER BY building_id
        """
        
        after_df = self.client.query(query).to_dataframe()
        
        # Merge for comparison
        comparison = before_df.merge(
            after_df,
            on='building_id',
            suffixes=('_before', '_after')
        )
        
        # Find buildings that changed recommendation
        changed_mask = comparison['recommended_opt_in_before'] != comparison['recommended_opt_in_after']
        changed_buildings = comparison[changed_mask]
        
        print(f"\n🔍 Buildings that changed recommendation: {len(changed_buildings)}")
        
        if len(changed_buildings) > 0:
            print("\nTop 10 buildings that changed:")
            print("-" * 120)
            print(f"{'Building ID':<12} {'Name':<30} {'Type':<25} {'Before':<10} {'After':<10} {'NPV Change':<15}")
            print("-" * 120)
            
            for _, row in changed_buildings.head(10).iterrows():
                npv_change = row['npv_benefit_of_optin_after'] - row['npv_benefit_of_optin_before']
                print(f"{row['building_id']:<12} "
                      f"{row['building_name_after'][:30]:<30} "
                      f"{row['property_type_after'][:25]:<25} "
                      f"{'OPT-IN' if row['recommended_opt_in_before'] else 'DEFAULT':<10} "
                      f"{'OPT-IN' if row['recommended_opt_in_after'] else 'DEFAULT':<10} "
                      f"${npv_change:>14,.0f}")
        
        # Summary statistics
        print("\n📈 Summary Statistics Comparison:")
        print("-" * 60)
        
        before_optin = before_df['recommended_opt_in'].sum()
        after_optin = after_df['recommended_opt_in'].sum()
        
        print(f"Total buildings analyzed: {len(before_df)} → {len(after_df)}")
        print(f"Recommended opt-in: {before_optin} → {after_optin} ({after_optin - before_optin:+d})")
        print(f"Opt-in rate: {before_optin/len(before_df)*100:.1f}% → {after_optin/len(after_df)*100:.1f}%")
        
        # Financial impact
        before_npv_total = before_df['npv_benefit_of_optin'].sum()
        after_npv_total = after_df['npv_benefit_of_optin'].sum()
        
        print(f"\nTotal NPV benefit of opt-in decisions:")
        print(f"  Before: ${before_npv_total:,.0f}")
        print(f"  After: ${after_npv_total:,.0f}")
        print(f"  Change: ${after_npv_total - before_npv_total:,.0f}")
        
        # Save detailed comparison
        comparison_path = f"opt_in_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        changed_buildings.to_csv(comparison_path, index=False)
        print(f"\n✓ Saved detailed comparison to {comparison_path}")
    
    def validate_specific_buildings(self):
        """Validate calculations for specific buildings like 2952"""
        
        print("\n🔍 Validating specific building calculations...")
        
        # Query for Building 2952
        query = f"""
        WITH building_details AS (
            SELECT 
                building_id,
                building_name,
                property_type,
                gross_floor_area,
                current_eui,
                target_2025,
                target_2027,
                target_2030,
                gap_2025,
                gap_2030,
                penalty_2025,
                penalty_2027,
                penalty_2030_default,
                penalty_2028_optin,
                penalty_2032_optin,
                npv_penalties_default,
                npv_penalties_optin,
                npv_advantage_optin,
                should_opt_in,
                primary_rationale
            FROM `{self.dataset_ref}.opt_in_decision_analysis`
            WHERE building_id = '2952'
        )
        SELECT * FROM building_details
        """
        
        result = self.client.query(query).to_dataframe()
        
        if len(result) > 0:
            building = result.iloc[0]
            
            print(f"\n🏢 Building 2952 - {building['building_name']}")
            print(f"   Type: {building['property_type']}")
            print(f"   Size: {building['gross_floor_area']:,.0f} sq ft")
            print(f"   Current EUI: {building['current_eui']:.1f} kBtu/ft²")
            
            print(f"\n   Targets:")
            print(f"   2025: {building['target_2025']:.1f} (gap: {building['gap_2025']:.1f})")
            print(f"   2027: {building['target_2027']:.1f}")
            print(f"   2030: {building['target_2030']:.1f} (gap: {building['gap_2030']:.1f})")
            
            print(f"\n   Standard Path Penalties:")
            print(f"   2025: ${building['penalty_2025']:,.0f}")
            print(f"   2027: ${building['penalty_2027']:,.0f}")
            print(f"   2030: ${building['penalty_2030_default']:,.0f}")
            print(f"   Total Nominal: ${building['penalty_2025'] + building['penalty_2027'] + building['penalty_2030_default']:,.0f}")
            print(f"   Total NPV: ${building['npv_penalties_default']:,.0f}")
            
            print(f"\n   Opt-in Path Penalties:")
            print(f"   2028: ${building['penalty_2028_optin']:,.0f}")
            print(f"   2032: ${building['penalty_2032_optin']:,.0f}")
            print(f"   Total Nominal: ${building['penalty_2028_optin'] + building['penalty_2032_optin']:,.0f}")
            print(f"   Total NPV: ${building['npv_penalties_optin']:,.0f}")
            
            print(f"\n   Recommendation: {'OPT-IN' if building['should_opt_in'] else 'STANDARD'}")
            print(f"   NPV Advantage: ${building['npv_advantage_optin']:,.0f}")
            print(f"   Rationale: {building['primary_rationale']}")
            
            # Manual validation
            print(f"\n   📐 Manual Calculation Check:")
            gap_2025 = building['gap_2025']
            sqft = building['gross_floor_area']
            
            # Standard path
            manual_2025 = max(0, gap_2025 * sqft * 0.15)
            print(f"   2025 penalty: {gap_2025:.1f} × {sqft:,.0f} × $0.15 = ${manual_2025:,.0f}")
            print(f"   Matches BigQuery: {'✅' if abs(manual_2025 - building['penalty_2025']) < 1 else '❌'}")
            
            # Opt-in path
            gap_2030 = building['gap_2030']
            manual_2028 = max(0, gap_2030 * sqft * 0.23)
            print(f"   2028 penalty: {gap_2030:.1f} × {sqft:,.0f} × $0.23 = ${manual_2028:,.0f}")
            print(f"   Matches BigQuery: {'✅' if abs(manual_2028 - building['penalty_2028_optin']) < 1 else '❌'}")
            
            # NPV calculation
            manual_npv_2025 = manual_2025 / 1.07**1
            print(f"\n   NPV of 2025 penalty: ${manual_2025:,.0f} / 1.07¹ = ${manual_npv_2025:,.0f}")
            
    def export_recommendations_for_review(self):
        """Export recommendations in a format suitable for review"""
        
        print("\n📤 Exporting recommendations for review...")
        
        # Get high-impact buildings
        query = f"""
        SELECT 
            building_id,
            building_name,
            property_type,
            sqft,
            current_eui,
            reduction_needed_pct,
            recommended_opt_in,
            penalties_if_default,
            penalties_if_optin,
            npv_benefit_of_optin,
            primary_rationale,
            decision_confidence,
            misses_2025_target,
            technical_difficulty_score
        FROM `{self.dataset_ref}.opt_in_recommendations`
        WHERE ABS(npv_benefit_of_optin) > 50000  -- High financial impact
           OR technical_difficulty_score >= 80   -- Very difficult
           OR (misses_2025_target AND NOT recommended_opt_in)  -- Counterintuitive
        ORDER BY ABS(npv_benefit_of_optin) DESC
        LIMIT 100
        """
        
        high_impact_df = self.client.query(query).to_dataframe()
        
        # Save to Excel with formatting
        output_path = f"high_impact_opt_in_decisions_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            high_impact_df.to_excel(writer, sheet_name='High Impact Buildings', index=False)
            
            # Add summary sheet
            summary_data = {
                'Metric': ['Total High Impact Buildings', 
                          'Recommended Opt-in', 
                          'Total NPV Benefit',
                          'Buildings Missing 2025 Target'],
                'Value': [len(high_impact_df),
                         high_impact_df['recommended_opt_in'].sum(),
                         f"${high_impact_df['npv_benefit_of_optin'].sum():,.0f}",
                         high_impact_df['misses_2025_target'].sum()]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"✓ Exported {len(high_impact_df)} high-impact buildings to {output_path}")


def main():
    """Main execution"""
    
    print("🔄 BIGQUERY OPT-IN ANALYSIS RE-RUN AND COMPARISON")
    print("=" * 80)
    print("\nThis script will:")
    print("1. Capture current analysis results")
    print("2. Re-run the opt-in decision model")
    print("3. Compare before/after results")
    print("4. Validate specific building calculations\n")
    
    comparison = AnalysisComparison()
    
    # Step 1: Capture current results
    before_df = comparison.capture_current_results()
    
    # Step 2: Re-run analysis
    response = input("\nRe-run the opt-in analysis? (y/n): ")
    
    if response.lower() == 'y':
        comparison.run_updated_analysis()
        
        # Step 3: Compare results
        if before_df is not None:
            comparison.compare_results(before_df)
        
        # Step 4: Validate specific buildings
        comparison.validate_specific_buildings()
        
        # Step 5: Export for review
        comparison.export_recommendations_for_review()
        
        print("\n✅ Analysis complete!")
        print("\nNext steps:")
        print("1. Review the comparison results")
        print("2. Check high-impact buildings in the Excel export")
        print("3. Update any dependent dashboards or reports")
        print("4. Communicate changes to stakeholders")
    else:
        print("\nAnalysis cancelled.")


if __name__ == "__main__":
    main()
