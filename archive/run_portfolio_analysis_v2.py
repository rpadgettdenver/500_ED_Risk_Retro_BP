"""
Suggested File Name: run_portfolio_analysis_v2.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Execute the portfolio risk analysis with 2028 $/sqft column added
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP'
sys.path.insert(0, project_root)

# Import the refined analyzer (v2)
from src.analysis.portfolio_risk_analyzer_refined import PortfolioRiskAnalyzer

def main():
    """Run portfolio analysis with updated table including 2028 $/sqft column"""
    print("=" * 80)
    print("🚀 ENERGIZE DENVER PORTFOLIO RISK ANALYSIS - VERSION 2")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Using corrected penalty rates: Standard=$0.15/kBtu, ACO=$0.23/kBtu")
    print("\nRefinements in this version:")
    print("  1. NPV calculated only through 2032 (not 2042)")
    print("  2. Hybrid line added to penalty evolution chart")
    print("  3. Property type labels show n=x/total format")
    print("  4. Added At Risk 2027 and 2028 columns")
    print("  5. $/sqft calculated for at-risk buildings only")
    print("  6. NEW: Added Avg $/sqft 2028 column for interim year consistency")
    print("  7. NEW: Added At Risk 2030 and 2032 columns for complete analysis")
    print("  8. NEW: Replaced confidence histogram with comprehensive summary text")
    print("\nNote: The Portfolio Summary Statistics table now includes all penalty years")
    print("      for comprehensive multi-year risk assessment.")
    print("=" * 80)
    
    try:
        # Initialize analyzer
        print("\n📊 Initializing Portfolio Risk Analyzer...")
        analyzer = PortfolioRiskAnalyzer()
        
        # Check data loaded
        print(f"\n✅ Successfully loaded {len(analyzer.portfolio)} buildings")
        print(f"   Total square footage: {analyzer.portfolio['Master Sq Ft'].sum():,.0f} sq ft")
        
        # Run analysis
        print("\n🔄 Running comprehensive analysis...")
        print("   Analyzing three scenarios plus sensitivity analysis")
        
        # Generate report
        output_dir = os.path.join(project_root, 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f'portfolio_risk_analysis_v2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
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
                penalty_cols = [col for col in df.columns if col.startswith('penalty_')]
                
                for col in penalty_cols:
                    year = int(col.replace('penalty_', ''))
                    if year <= 2032:  # Only through 2032
                        year_penalty = df[col].sum()
                        years_from_2025 = year - 2025
                        if years_from_2025 >= 0:
                            npv_total += year_penalty / (1.07 ** years_from_2025)
                
                print(f"\n{scenario_name.replace('_', ' ').title()} Scenario:")
                print(f"  Total NPV of penalties (2025-2032): ${npv_total:,.0f}")
                print(f"  Buildings analyzed: {len(df)}")
                
                # Show at-risk counts and $/sqft for key years
                at_risk_2025 = (df['penalty_2025'] > 0).sum() if 'penalty_2025' in df.columns else 0
                at_risk_2027 = (df['penalty_2027'] > 0).sum() if 'penalty_2027' in df.columns else 0
                at_risk_2028 = (df['penalty_2028'] > 0).sum() if 'penalty_2028' in df.columns else 0
                at_risk_2030 = (df['penalty_2030'] > 0).sum() if 'penalty_2030' in df.columns else 0
                at_risk_2032 = (df['penalty_2032'] > 0).sum() if 'penalty_2032' in df.columns else 0
                
                print(f"  At risk in 2025: {at_risk_2025}")
                print(f"  At risk in 2027: {at_risk_2027}")
                print(f"  At risk in 2028: {at_risk_2028}")
                print(f"  At risk in 2030: {at_risk_2030}")
                print(f"  At risk in 2032: {at_risk_2032}")
                
                # Calculate $/sqft for 2028
                if 'penalty_2028' in df.columns and at_risk_2028 > 0:
                    at_risk_2028_df = df[df['penalty_2028'] > 0]
                    avg_2028 = at_risk_2028_df['penalty_2028'].sum() / at_risk_2028_df['sqft'].sum()
                    print(f"  Avg $/sqft for at-risk buildings in 2028: ${avg_2028:.3f}")
                
                if scenario_name == 'hybrid' and 'should_opt_in' in df.columns:
                    opt_in_count = df['should_opt_in'].sum()
                    print(f"  Buildings opting into ACO: {opt_in_count} ({opt_in_count/len(df)*100:.1f}%)")
        
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
        
        print(f"\n📁 Detailed results saved to:")
        print(f"   Excel: {output_path.replace('.json', '_detailed.xlsx')}")
        print(f"   Visualization: {output_path.replace('.json', '').replace('outputs/', 'outputs/portfolio_analysis/')}.png")
        
        # Explanation of $/sqft calculation
        print("\n📋 Note on $/sqft calculations:")
        print("   The $/sqft values in the table represent the average penalty")
        print("   per square foot ONLY for buildings that have penalties in that year.")
        print("   This provides consistency across interim penalty years (2028, 2030, 2032)")
        print("   and gives a more accurate picture of the penalty burden for")
        print("   non-compliant buildings.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Portfolio analysis v2 completed successfully!")
    else:
        print("\n❌ Portfolio analysis failed!")
