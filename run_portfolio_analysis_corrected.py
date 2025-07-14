"""
Run full portfolio analysis with corrected penalty rates and logic
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP')

# Import the portfolio analyzer
from src.analysis.portfolio_risk_analyzer import PortfolioRiskAnalyzer

def main():
    """Run comprehensive portfolio analysis"""
    
    print("🚀 ENERGIZE DENVER PORTFOLIO RISK ANALYSIS")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Using corrected penalty rates: Standard=$0.15/kBtu, ACO=$0.23/kBtu")
    print("=" * 80)
    
    try:
        # Initialize analyzer
        print("\n📊 Initializing Portfolio Risk Analyzer...")
        analyzer = PortfolioRiskAnalyzer()
        
        # Generate full report
        print("\n📈 Running comprehensive analysis...")
        output_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/portfolio_risk_analysis_corrected.json'
        scenarios, fig = analyzer.generate_report(output_path)
        
        # Print summary statistics
        print("\n📊 PORTFOLIO SUMMARY:")
        print(f"Total buildings analyzed: {len(analyzer.portfolio)}")
        print(f"Total square footage: {analyzer.portfolio['Master Sq Ft'].sum():,.0f} sq ft")
        
        # Show EPB distribution
        if 'Is EPB' in analyzer.portfolio.columns:
            epb_count = analyzer.portfolio['Is EPB'].sum()
            print(f"EPB buildings: {epb_count} ({epb_count/len(analyzer.portfolio)*100:.1f}%)")
        
        # Show property type distribution
        print("\n🏢 Top Property Types:")
        top_types = analyzer.portfolio['Master Property Type'].value_counts().head(5)
        for prop_type, count in top_types.items():
            print(f"  {prop_type}: {count} buildings")
        
        # Extract key metrics from scenarios
        print("\n💰 FINANCIAL IMPACT SUMMARY:")
        print("-" * 60)
        
        for scenario_name, df in scenarios.items():
            if scenario_name in ['all_standard', 'all_aco', 'hybrid']:
                # Calculate total NPV
                penalty_cols = [col for col in df.columns if col.startswith('penalty_')]
                npv_total = 0
                
                for year_col in penalty_cols:
                    year = int(year_col.replace('penalty_', ''))
                    year_penalties = df[year_col].sum()
                    years_from_2025 = year - 2025
                    if years_from_2025 >= 0:
                        npv_total += year_penalties / (1.07 ** years_from_2025)
                
                print(f"\n{scenario_name.replace('_', ' ').title()}:")
                print(f"  Total NPV of penalties (7% discount): ${npv_total:,.0f}")
                print(f"  Buildings at risk in 2025: {(df['penalty_2025'] > 0).sum() if 'penalty_2025' in df.columns else 0}")
                print(f"  Average penalty per building: ${npv_total/len(df):,.0f}")
                
                # For hybrid, show opt-in statistics
                if scenario_name == 'hybrid' and 'should_opt_in' in df.columns:
                    opt_in_count = df['should_opt_in'].sum()
                    print(f"  Buildings opting into ACO: {opt_in_count} ({opt_in_count/len(df)*100:.1f}%)")
                    
                    # Show top reasons for opt-in
                    if 'opt_in_rationale' in df.columns:
                        print("\n  Opt-in rationales:")
                        rationale_counts = df[df['should_opt_in']]['opt_in_rationale'].value_counts().head(5)
                        for rationale, count in rationale_counts.items():
                            print(f"    {rationale}: {count} buildings")
        
        # Property type risk analysis
        if 'hybrid' in scenarios:
            hybrid_df = scenarios['hybrid']
            print("\n🏢 PROPERTY TYPE RISK ANALYSIS (Hybrid Scenario):")
            print("-" * 80)
            
            # Group by property type
            prop_type_summary = hybrid_df.groupby('property_type').agg({
                'building_id': 'count',
                'penalty_2025': 'sum',
                'penalty_2030': 'sum',
                'should_opt_in': 'mean'
            }).round(2)
            
            # Sort by 2025 penalty exposure
            prop_type_summary = prop_type_summary.sort_values('penalty_2025', ascending=False).head(10)
            
            print(f"{'Property Type':<30} {'Count':>6} {'2025 Penalty':>15} {'2030 Penalty':>15} {'Opt-in %':>10}")
            print("-" * 80)
            
            for prop_type, row in prop_type_summary.iterrows():
                print(f"{prop_type[:30]:<30} {int(row['building_id']):>6} "
                      f"${row['penalty_2025']:>14,.0f} ${row['penalty_2030']:>14,.0f} "
                      f"{row['should_opt_in']*100:>9.1f}%")
        
        # Year-over-year penalty evolution
        print("\n📅 PENALTY EVOLUTION (Hybrid Scenario):")
        print("-" * 60)
        
        if 'hybrid' in scenarios:
            hybrid_df = scenarios['hybrid']
            years_to_show = [2025, 2027, 2028, 2030, 2032, 2035, 2040, 2042]
            
            print(f"{'Year':<6}", end='')
            for year in years_to_show:
                print(f"{year:>12}", end='')
            print()
            print("-" * 60)
            
            print("Total $", end='')
            for year in years_to_show:
                col_name = f'penalty_{year}'
                if col_name in hybrid_df.columns:
                    total = hybrid_df[col_name].sum()
                    print(f"{total/1e6:>11.1f}M", end='')
                else:
                    print(f"{'N/A':>12}", end='')
            print()
        
        # Save detailed results
        print(f"\n💾 Detailed results saved to:")
        print(f"  {output_path.replace('.json', '_detailed.xlsx')}")
        print(f"  {output_path.replace('.json', '.png')}")
        
        print("\n✅ Portfolio analysis complete!")
        
        # Return key metrics for summary
        return {
            'total_buildings': len(analyzer.portfolio),
            'scenarios': scenarios,
            'output_path': output_path
        }
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = main()
