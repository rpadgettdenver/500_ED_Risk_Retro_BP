"""
Suggested File Name: run_mai_portfolio_analysis.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Execute the MAI-enabled portfolio risk analysis with all refinements

This script runs the portfolio analysis with proper MAI building support.
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP'
sys.path.insert(0, project_root)

# Import the MAI-enabled refined analyzer
from src.analysis.portfolio_risk_analyzer_refined import PortfolioRiskAnalyzer

def main():
    """Run MAI-enabled portfolio analysis with all refinements"""
    print("=" * 80)
    print("🚀 ENERGIZE DENVER PORTFOLIO RISK ANALYSIS - MAI-ENABLED VERSION")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Using corrected penalty rates: Standard=$0.15/kBtu, ACO=$0.23/kBtu")
    print("\nKey features in this version:")
    print("  1. MAI buildings properly identified from MAITargetSummary Report.csv")
    print("  2. MAI buildings forced to ACO path (2028/2032 timeline)")
    print("  3. MAI penalty rate correctly set to $0.23/kBtu")
    print("  4. MAI-specific targets loaded from CSV files")
    print("  5. Separate MAI vs non-MAI NPV tracking")
    print("  6. All previous refinements included")
    print("=" * 80)
    
    try:
        # Initialize analyzer with MAI support
        print("\n📊 Initializing Portfolio Risk Analyzer with MAI support...")
        analyzer = PortfolioRiskAnalyzer()
        
        # Check data loaded
        print(f"\n✅ Successfully loaded {len(analyzer.portfolio)} buildings")
        print(f"   Total square footage: {analyzer.portfolio['Master Sq Ft'].sum():,.0f} sq ft")
        
        # Show MAI breakdown
        mai_count = analyzer.portfolio['is_mai'].sum()
        print(f"\n🏭 MAI Building Summary:")
        print(f"   MAI buildings: {mai_count}")
        print(f"   Non-MAI buildings: {len(analyzer.portfolio) - mai_count}")
        
        # Run analysis
        print("\n🔄 Running comprehensive analysis...")
        print("   Analyzing three scenarios plus sensitivity analysis")
        print("   MAI buildings will be forced to ACO path in all scenarios")
        
        # Generate report
        output_dir = os.path.join(project_root, 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f'portfolio_risk_analysis_mai_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        scenarios, fig = analyzer.generate_report(output_path)
        
        # Show summary results
        print("\n" + "=" * 80)
        print("📊 ANALYSIS COMPLETE - KEY FINDINGS:")
        print("=" * 80)
        
        # Calculate NPV for each scenario (through 2032 only)
        for scenario_name, df in scenarios.items():
            if scenario_name in ['all_standard', 'all_aco', 'hybrid']:
                # Calculate total NPV through 2032
                npv_total = 0
                mai_npv = 0
                penalty_cols = [col for col in df.columns if col.startswith('penalty_')]
                
                for col in penalty_cols:
                    year = int(col.replace('penalty_', ''))
                    if year <= 2032:  # Only through 2032
                        year_penalty = df[col].sum()
                        mai_penalty = df[df['is_mai'] == True][col].sum() if 'is_mai' in df.columns else 0
                        years_from_2025 = year - 2025
                        if years_from_2025 >= 0:
                            npv_total += year_penalty / (1.07 ** years_from_2025)
                            mai_npv += mai_penalty / (1.07 ** years_from_2025)
                
                print(f"\n{scenario_name.replace('_', ' ').title()} Scenario:")
                print(f"  Total NPV of penalties (2025-2032): ${npv_total:,.0f}")
                print(f"  MAI portion of NPV: ${mai_npv:,.0f} ({mai_npv/npv_total*100:.1f}%)" if npv_total > 0 else "  MAI portion of NPV: $0")
                print(f"  Buildings analyzed: {len(df)}")
                
                # Show MAI-specific metrics
                if 'is_mai' in df.columns:
                    mai_df = df[df['is_mai'] == True]
                    mai_2028_at_risk = (mai_df['penalty_2028'] > 0).sum() if 'penalty_2028' in mai_df.columns else 0
                    mai_2032_at_risk = (mai_df['penalty_2032'] > 0).sum() if 'penalty_2032' in mai_df.columns else 0
                    print(f"  MAI buildings at risk in 2028: {mai_2028_at_risk}")
                    print(f"  MAI buildings at risk in 2032: {mai_2032_at_risk}")
                
                # Show at-risk counts for key years
                at_risk_2025 = (df['penalty_2025'] > 0).sum() if 'penalty_2025' in df.columns else 0
                at_risk_2027 = (df['penalty_2027'] > 0).sum() if 'penalty_2027' in df.columns else 0
                at_risk_2028 = (df['penalty_2028'] > 0).sum() if 'penalty_2028' in df.columns else 0
                
                print(f"  Total at risk in 2025: {at_risk_2025}")
                print(f"  Total at risk in 2027: {at_risk_2027}")
                print(f"  Total at risk in 2028: {at_risk_2028}")
                
                if scenario_name == 'hybrid' and 'should_opt_in' in df.columns:
                    opt_in_count = df['should_opt_in'].sum()
                    mai_count = df['is_mai'].sum() if 'is_mai' in df.columns else 0
                    voluntary_opt_in = opt_in_count - mai_count
                    print(f"  Buildings opting into ACO: {opt_in_count} ({opt_in_count/len(df)*100:.1f}%)")
                    print(f"    - MAI (required): {mai_count}")
                    print(f"    - Non-MAI (voluntary): {voluntary_opt_in}")
        
        # Calculate savings
        if 'all_standard' in scenarios and 'hybrid' in scenarios:
            standard_npv = 0
            hybrid_npv = 0
            
            penalty_cols = [col for col in scenarios['all_standard'].columns if col.startswith('penalty_')]
            
            for col in penalty_cols:
                year = int(col.replace('penalty_', ''))
                if year <= 2032:  # Only through 2032
                    years_from_2025 = year - 2025
                    if years_from_2025 >= 0:
                        standard_npv += scenarios['all_standard'][col].sum() / (1.07 ** years_from_2025)
                        hybrid_npv += scenarios['hybrid'][col].sum() / (1.07 ** years_from_2025)
            
            savings = standard_npv - hybrid_npv
            savings_pct = (savings / standard_npv) * 100 if standard_npv > 0 else 0
            
            print("\n" + "=" * 80)
            print(f"💰 POTENTIAL SAVINGS from Hybrid Strategy (NPV 2025-2032):")
            print(f"   ${savings:,.0f} ({savings_pct:.1f}% reduction)")
            print("=" * 80)
        
        # Verify MAI penalties are being calculated
        print("\n🔍 MAI PENALTY VERIFICATION:")
        print("=" * 80)
        
        # Check specific MAI buildings that should have penalties (from debugger)
        test_building_ids = ['1216', '1316', '1496', '3274', '3277']
        
        if 'hybrid' in scenarios:
            hybrid_df = scenarios['hybrid']
            for building_id in test_building_ids:
                building_data = hybrid_df[hybrid_df['building_id'] == building_id]
                if not building_data.empty:
                    row = building_data.iloc[0]
                    penalty_2028 = row['penalty_2028'] if 'penalty_2028' in row else 0
                    print(f"  Building {building_id}: 2028 penalty = ${penalty_2028:,.2f}")
        
        print(f"\n📁 Detailed results saved to:")
        print(f"   Excel: {output_path.replace('.json', '_detailed.xlsx')}")
        print(f"   Visualization: {output_path.replace('.json', '').replace('outputs/', 'outputs/portfolio_analysis/')}.png")
        
        # Explanation of MAI handling
        print("\n📋 Note on MAI Building Treatment:")
        print("   MAI (Multifamily Affordable and Income-Restricted) buildings are")
        print("   required to follow the ACO timeline (2028/2032) with a penalty")
        print("   rate of $0.23/kBtu. In the 'All Standard' scenario, MAI buildings")
        print("   still use ACO timing, reflecting regulatory requirements.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ MAI-enabled portfolio analysis completed successfully!")
    else:
        print("\n❌ Portfolio analysis failed!")
