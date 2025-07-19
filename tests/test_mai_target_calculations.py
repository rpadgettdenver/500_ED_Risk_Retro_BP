"""
Suggested File Name: test_mai_target_calculations.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/tests/
Use: Verify MAI target calculations with the new logic

This script demonstrates and tests the MAI target calculation logic:
- MAI buildings are identified from MAITargetSummary Report.csv
- Final target = MAX(Adjusted Final Target, 30% reduction, 52.9 floor)
"""

import sys
sys.path.append('/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP')

from src.utils.mai_data_loader import MAIDataLoader
from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator
import pandas as pd


def test_mai_target_calculations():
    """Test MAI target calculations with various scenarios"""
    
    print("🏭 TESTING MAI TARGET CALCULATIONS")
    print("=" * 60)
    
    # Load MAI data
    mai_loader = MAIDataLoader()
    mai_targets_data = mai_loader.load_mai_targets()
    
    # Initialize penalty calculator
    calculator = EnergizeDenverPenaltyCalculator()
    
    # Test cases from the MAI Target Summary
    test_cases = [
        # Building ID, Baseline, Adj Final from CSV, Expected Result, Notes
        ('1122', 536.6, 375.6, 375.6, "30% reduction matches CSV"),
        ('1427', 50.9, 52.9, 52.9, "Floor applies"),
        ('1854', 50.8, 35.6, 52.9, "Floor should override CSV"),
        ('3633', 20.3, 58.2, 58.2, "CSV target above floor"),
        ('2047', 1826.5, 1278.5, 1278.5, "Large building 30% reduction"),
        ('1433', 966.7, 998.6, 998.6, "CSV target above baseline"),
    ]
    
    print("\nTesting MAI Final Target Logic:")
    print("Final Target = MAX(CSV Adjusted, 30% reduction, 52.9 floor)")
    print("-" * 100)
    print(f"{'Building':<10} {'Baseline':<10} {'CSV Adj':<10} {'30% Red':<10} {'Floor':<10} {'Final':<10} {'Notes':<30}")
    print("-" * 100)
    
    for building_id, baseline, csv_adjusted, expected, notes in test_cases:
        # Calculate components
        reduction_30pct = baseline * 0.70
        floor = 52.9
        
        # Apply MAI rules
        final_target = calculator._apply_mai_rules(
            raw_target_eui=0,  # Not used in this case
            baseline_eui=baseline,
            mai_adjusted_target=csv_adjusted
        )
        
        # Verify
        status = "✅" if abs(final_target - expected) < 0.1 else "❌"
        
        print(f"{building_id:<10} {baseline:<10.1f} {csv_adjusted:<10.1f} "
              f"{reduction_30pct:<10.1f} {floor:<10.1f} {final_target:<10.1f} "
              f"{status} {notes:<30}")
    
    # Analyze all MAI buildings
    print("\n\n📊 ANALYZING ALL MAI BUILDINGS")
    print("=" * 60)
    
    analysis_results = []
    
    for building_id, target_info in mai_targets_data.items():
        baseline = target_info['baseline_value']
        csv_adjusted = target_info['adjusted_final_target']
        
        if baseline and csv_adjusted:  # Skip if missing data
            # Calculate components
            reduction_30pct = baseline * 0.70
            
            # Determine which rule applies
            if csv_adjusted >= reduction_30pct and csv_adjusted >= 52.9:
                rule = "CSV Target"
            elif reduction_30pct >= csv_adjusted and reduction_30pct >= 52.9:
                rule = "30% Reduction"
            else:
                rule = "52.9 Floor"
            
            # Check if CSV violates floor
            violates_floor = csv_adjusted < 52.9
            
            analysis_results.append({
                'building_id': building_id,
                'baseline': baseline,
                'csv_adjusted': csv_adjusted,
                'reduction_30pct': reduction_30pct,
                'rule_applied': rule,
                'violates_floor': violates_floor,
                'pct_reduction': (baseline - csv_adjusted) / baseline * 100
            })
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(analysis_results)
    
    # Summary statistics
    print(f"\nTotal MAI Buildings Analyzed: {len(df)}")
    print(f"\nRule Application Summary:")
    print(df['rule_applied'].value_counts())
    
    print(f"\nBuildings where CSV target < 52.9 floor: {df['violates_floor'].sum()}")
    
    if df['violates_floor'].sum() > 0:
        print("\nBuildings violating 52.9 floor in CSV:")
        violators = df[df['violates_floor']]
        for _, row in violators.iterrows():
            print(f"  {row['building_id']}: CSV={row['csv_adjusted']:.1f}, "
                  f"Baseline={row['baseline']:.1f}")
    
    # Reduction percentage analysis
    print(f"\nReduction Percentage Statistics:")
    print(f"  Mean: {df['pct_reduction'].mean():.1f}%")
    print(f"  Min: {df['pct_reduction'].min():.1f}%")
    print(f"  Max: {df['pct_reduction'].max():.1f}%")
    
    # Buildings with unusual patterns
    print(f"\nBuildings with CSV target > baseline: {len(df[df['pct_reduction'] < 0])}")
    
    return df


def create_mai_verification_report(df: pd.DataFrame):
    """Create a detailed verification report"""
    
    print("\n\n📑 CREATING MAI VERIFICATION REPORT")
    print("=" * 60)
    
    # Group by which rule would apply
    report = []
    
    for _, row in df.iterrows():
        # Calculate what our logic would produce
        final_target = max(
            row['csv_adjusted'],
            row['reduction_30pct'],
            52.9
        )
        
        # Check if it matches CSV
        matches_csv = abs(final_target - row['csv_adjusted']) < 0.1
        
        report.append({
            'building_id': row['building_id'],
            'our_final_target': final_target,
            'csv_target': row['csv_adjusted'],
            'matches': matches_csv,
            'difference': final_target - row['csv_adjusted']
        })
    
    report_df = pd.DataFrame(report)
    
    print(f"Buildings where our logic differs from CSV: {(~report_df['matches']).sum()}")
    
    if (~report_df['matches']).sum() > 0:
        print("\nDifferences found:")
        diffs = report_df[~report_df['matches']].sort_values('difference', ascending=False)
        for _, row in diffs.head(10).iterrows():
            print(f"  Building {row['building_id']}: "
                  f"Our={row['our_final_target']:.1f}, "
                  f"CSV={row['csv_target']:.1f}, "
                  f"Diff={row['difference']:.1f}")
    
    return report_df


if __name__ == "__main__":
    # Run tests
    analysis_df = test_mai_target_calculations()
    
    # Create verification report
    report_df = create_mai_verification_report(analysis_df)
    
    # Save results
    output_file = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/data/mai_target_verification.csv"
    report_df.to_csv(output_file, index=False)
    print(f"\n✅ Verification report saved to: {output_file}")
    
    print("\n🎯 KEY TAKEAWAY:")
    print("Using MAX(CSV Adjusted, 30% reduction, 52.9) ensures we always")
    print("apply the most lenient target for MAI buildings, protecting them")
    print("from overly aggressive reduction requirements.")
