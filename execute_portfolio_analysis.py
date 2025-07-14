"""
Suggested File Name: execute_portfolio_analysis.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Execute the corrected portfolio risk analysis with updated data

This script runs the portfolio analysis and displays key results.
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP'
sys.path.insert(0, project_root)

# Import modules
from src.analysis.portfolio_risk_analyzer import PortfolioRiskAnalyzer

def main():
    """Run portfolio analysis with corrected rates"""
    print("=" * 80)
    print("🚀 ENERGIZE DENVER PORTFOLIO RISK ANALYSIS")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Using corrected penalty rates: Standard=$0.15/kBtu, ACO=$0.23/kBtu")
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
        print("   This will analyze three scenarios:")
        print("   1. All buildings on Standard path")
        print("   2. All buildings on ACO path")
        print("   3. Hybrid (optimal selection per building)")
        
        # Generate report
        output_dir = os.path.join(project_root, 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f'portfolio_risk_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        scenarios, fig = analyzer.generate_report(output_path)
        
        # Show summary results
        print("\n" + "=" * 80)
        print("📊 ANALYSIS COMPLETE - KEY FINDINGS:")
        print("=" * 80)
        
        # Calculate NPV for each scenario
        for scenario_name, df in scenarios.items():
            if scenario_name in ['all_standard', 'all_aco', 'hybrid']:
                # Calculate total NPV
                npv_total = 0
                penalty_cols = [col for col in df.columns if col.startswith('penalty_')]
                
                for col in penalty_cols:
                    year = int(col.replace('penalty_', ''))
                    year_penalty = df[col].sum()
                    years_from_2025 = year - 2025
                    if years_from_2025 >= 0:
                        npv_total += year_penalty / (1.07 ** years_from_2025)
                
                print(f"\n{scenario_name.replace('_', ' ').title()} Scenario:")
                print(f"  Total NPV of penalties: ${npv_total:,.0f}")
                print(f"  Buildings analyzed: {len(df)}")
                
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
                years_from_2025 = year - 2025
                if years_from_2025 >= 0:
                    standard_npv += scenarios['all_standard'][col].sum() / (1.07 ** years_from_2025)
                    hybrid_npv += scenarios['hybrid'][col].sum() / (1.07 ** years_from_2025)
            
            savings = standard_npv - hybrid_npv
            savings_pct = (savings / standard_npv) * 100 if standard_npv > 0 else 0
            
            print("\n" + "=" * 80)
            print(f"💰 POTENTIAL SAVINGS from Hybrid Strategy:")
            print(f"   ${savings:,.0f} ({savings_pct:.1f}% reduction)")
            print("=" * 80)
        
        print(f"\n📁 Detailed results saved to:")
        print(f"   {output_path}")
        print(f"   {output_path.replace('.json', '_detailed.xlsx')}")
        print(f"   {output_path.replace('.json', '.png')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Portfolio analysis completed successfully!")
    else:
        print("\n❌ Portfolio analysis failed!")
