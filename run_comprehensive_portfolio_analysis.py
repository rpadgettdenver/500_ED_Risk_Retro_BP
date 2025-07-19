"""
Suggested File Name: run_comprehensive_portfolio_analysis.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Generate all portfolio analysis reports with complete business intelligence

This script demonstrates how to generate comprehensive portfolio analysis reports
using your existing Energize Denver codebase. It produces tables, graphs, and 
detailed analytics for energy use and potential fines through 2042.

PREREQUISITES:
1. Activate virtual environment: source gcp_env/bin/activate
2. Ensure you're in the project root directory
3. Data files are current in data/processed/ directory

OUTPUTS GENERATED:
- Excel workbooks with detailed building-by-building analysis
- PNG visualizations with 6-chart dashboard
- JSON data files for API integration
- Summary statistics and business insights
"""

import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add project root to path
project_root = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP'
sys.path.insert(0, project_root)

# Import analysis modules
from src.analysis.portfolio_risk_analyzer import PortfolioRiskAnalyzer
from src.analysis.portfolio_risk_analyzer_improved import PortfolioRiskAnalyzer as ImprovedAnalyzer
from src.analysis.building_compliance_analyzer_v2 import EnhancedBuildingComplianceAnalyzer

def generate_executive_summary():
    """Generate high-level portfolio executive summary"""
    print("=" * 80)
    print("🏢 ENERGIZE DENVER PORTFOLIO ANALYSIS - EXECUTIVE SUMMARY")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Coverage: All buildings 25,000+ sq ft in Denver ordinance")
    print("Analysis Period: 2025-2042 (18 years)")
    print("Penalty Rates: Standard=$0.15/kBtu, ACO=$0.23/kBtu")
    print("=" * 80)
    
    try:
        # Initialize analyzer
        print("\n📊 Loading portfolio data...")
        analyzer = PortfolioRiskAnalyzer()
        
        # Portfolio overview
        total_buildings = len(analyzer.portfolio)
        total_sqft = analyzer.portfolio['Master Sq Ft'].sum()
        avg_eui = analyzer.portfolio['Weather Normalized Site EUI'].mean()
        
        print(f"\n🏗️  PORTFOLIO OVERVIEW:")
        print(f"   Total Buildings: {total_buildings:,}")
        print(f"   Total Square Footage: {total_sqft:,.0f} sq ft")
        print(f"   Average EUI: {avg_eui:.1f} kBtu/sq ft")
        
        # Property type breakdown
        prop_type_summary = analyzer.portfolio.groupby('Master Property Type').agg({
            'Building ID': 'count',
            'Master Sq Ft': 'sum',
            'Weather Normalized Site EUI': 'mean'
        }).sort_values('Master Sq Ft', ascending=False).head(10)
        
        print(f"\n🏢 TOP PROPERTY TYPES (by total sq ft):")
        print("-" * 70)
        print(f"{'Property Type':<30} {'Buildings':>10} {'Sq Ft':>15} {'Avg EUI':>10}")
        print("-" * 70)
        for prop_type, row in prop_type_summary.iterrows():
            print(f"{prop_type[:28]:<30} {int(row['Building ID']):>10,} "
                  f"{int(row['Master Sq Ft']):>14,} {row['Weather Normalized Site EUI']:>9.1f}")
        
        return analyzer
        
    except Exception as e:
        print(f"❌ Error generating executive summary: {e}")
        return None

def run_three_scenario_analysis(analyzer):
    """Run the core three-scenario risk analysis"""
    print("\n" + "=" * 80)
    print("📊 THREE-SCENARIO PENALTY RISK ANALYSIS")
    print("=" * 80)
    
    try:
        # Generate comprehensive analysis
        output_dir = os.path.join(project_root, 'outputs', 'data')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f'portfolio_analysis_{timestamp}.json')
        
        print("\n🔄 Running scenario analysis...")
        print("   1. All Standard Path - Default compliance timeline")
        print("   2. All ACO Path - All buildings opt into alternative")  
        print("   3. Hybrid Optimal - AI-driven pathway selection")
        
        scenarios, fig = analyzer.generate_report(output_path)
        
        # Calculate and display key metrics
        print("\n📈 SCENARIO RESULTS:")
        print("=" * 80)
        
        scenario_summary = {}
        
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
                
                # Key year penalties
                penalty_2025 = df.get('penalty_2025', pd.Series([0])).sum()
                penalty_2030 = df.get('penalty_2030', pd.Series([0])).sum()
                penalty_2032 = df.get('penalty_2032', pd.Series([0])).sum()
                
                # Buildings at risk
                buildings_at_risk_2025 = (df.get('penalty_2025', pd.Series([0])) > 0).sum()
                buildings_at_risk_2030 = (df.get('penalty_2030', pd.Series([0])) > 0).sum()
                
                scenario_summary[scenario_name] = {
                    'npv_total': npv_total,
                    'penalty_2025': penalty_2025,
                    'penalty_2030': penalty_2030,
                    'penalty_2032': penalty_2032,
                    'buildings_2025': buildings_at_risk_2025,
                    'buildings_2030': buildings_at_risk_2030,
                    'total_buildings': len(df)
                }
                
                print(f"\n{scenario_name.replace('_', ' ').title()} Scenario:")
                print(f"  Total NPV (18 years): ${npv_total:,.0f}")
                print(f"  2025 Penalty: ${penalty_2025:,.0f} ({buildings_at_risk_2025} buildings)")
                print(f"  2030 Penalty: ${penalty_2030:,.0f} ({buildings_at_risk_2030} buildings)")
                if penalty_2032 > 0:
                    print(f"  2032 Penalty: ${penalty_2032:,.0f}")
                
                if scenario_name == 'hybrid' and 'should_opt_in' in df.columns:
                    opt_in_count = df['should_opt_in'].sum()
                    opt_in_pct = opt_in_count / len(df) * 100
                    print(f"  Buildings opting into ACO: {opt_in_count} ({opt_in_pct:.1f}%)")
        
        # Calculate potential savings
        if 'all_standard' in scenario_summary and 'hybrid' in scenario_summary:
            savings = scenario_summary['all_standard']['npv_total'] - scenario_summary['hybrid']['npv_total']
            savings_pct = (savings / scenario_summary['all_standard']['npv_total']) * 100
            
            print("\n" + "=" * 80)
            print("💰 OPTIMIZATION IMPACT:")
            print(f"   Potential NPV Savings: ${savings:,.0f}")
            print(f"   Percentage Reduction: {savings_pct:.1f}%")
            print("   Strategy: Optimal pathway selection per building")
            print("=" * 80)
        
        # File outputs
        excel_path = output_path.replace('.json', '_detailed.xlsx')
        viz_path = output_path.replace('.json', '.png').replace('outputs/data/', 'outputs/data/')
        
        print(f"\n📁 OUTPUT FILES GENERATED:")
        print(f"   📊 Excel Report: {excel_path}")
        print(f"   📈 Visualizations: {viz_path}")
        print(f"   📋 JSON Data: {output_path}")
        
        return scenarios, scenario_summary
        
    except Exception as e:
        print(f"❌ Error in scenario analysis: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def generate_time_series_analysis(scenarios):
    """Generate detailed time series penalty analysis"""
    print("\n" + "=" * 80)
    print("📅 TIME SERIES PENALTY ANALYSIS (2025-2042)")
    print("=" * 80)
    
    if not scenarios:
        print("❌ No scenario data available")
        return
    
    # Extract yearly data
    years = list(range(2025, 2043))
    time_series_data = []
    
    for scenario_name, df in scenarios.items():
        if scenario_name in ['all_standard', 'all_aco', 'hybrid']:
            for year in years:
                col_name = f'penalty_{year}'
                if col_name in df.columns:
                    total_penalty = df[col_name].sum()
                    buildings_at_risk = (df[col_name] > 0).sum()
                    
                    time_series_data.append({
                        'scenario': scenario_name,
                        'year': year,
                        'total_penalty': total_penalty,
                        'buildings_at_risk': buildings_at_risk
                    })
    
    time_series_df = pd.DataFrame(time_series_data)
    
    # Display key milestone years
    milestone_years = [2025, 2027, 2028, 2030, 2032, 2035, 2040]
    
    print("\nTOTAL PENALTIES BY YEAR ($M):")
    print("-" * 80)
    print(f"{'Year':<8}", end='')
    scenario_names = ['all_standard', 'all_aco', 'hybrid']
    for scenario in scenario_names:
        print(f"{scenario.replace('_', ' ').title():>20}", end='')
    print()
    print("-" * 80)
    
    for year in milestone_years:
        print(f"{year:<8}", end='')
        for scenario in scenario_names:
            year_data = time_series_df[
                (time_series_df['scenario'] == scenario) & 
                (time_series_df['year'] == year)
            ]
            penalty = year_data['total_penalty'].sum() if not year_data.empty else 0
            print(f"${penalty/1e6:>19.1f}", end='')
        print()
    
    # Find peak years for each scenario
    print(f"\nPEAK PENALTY YEARS:")
    print("-" * 50)
    for scenario in scenario_names:
        scenario_data = time_series_df[time_series_df['scenario'] == scenario]
        if not scenario_data.empty:
            peak_row = scenario_data.loc[scenario_data['total_penalty'].idxmax()]
            print(f"{scenario.replace('_', ' ').title():<20}: {int(peak_row['year'])} "
                  f"(${peak_row['total_penalty']:,.0f})")

def generate_property_type_analysis(scenarios):
    """Analyze risk and opportunity by property type"""
    print("\n" + "=" * 80)
    print("🏢 PROPERTY TYPE RISK ANALYSIS")
    print("=" * 80)
    
    if not scenarios or 'hybrid' not in scenarios:
        print("❌ Hybrid scenario data not available")
        return
    
    hybrid_df = scenarios['hybrid']
    
    # Property type breakdown with opt-in analysis
    if 'should_opt_in' in hybrid_df.columns:
        prop_analysis = hybrid_df.groupby('property_type').agg({
            'building_id': 'count',
            'should_opt_in': ['sum', 'mean'],
            'penalty_2030': ['sum', 'mean'],
            'sqft': 'sum',
            'npv_advantage': 'mean'
        }).round(2)
        
        # Flatten column names
        prop_analysis.columns = ['total_buildings', 'opt_in_count', 'opt_in_rate',
                                'total_penalty_2030', 'avg_penalty_2030', 'total_sqft', 'avg_npv_advantage']
        
        # Filter to significant property types (5+ buildings)
        prop_analysis = prop_analysis[prop_analysis['total_buildings'] >= 5]
        prop_analysis = prop_analysis.sort_values('total_penalty_2030', ascending=False)
        
        print("PROPERTY TYPE BREAKDOWN (5+ buildings, sorted by total penalty exposure):")
        print("-" * 100)
        print(f"{'Property Type':<35} {'Bldgs':>6} {'Opt-In':>8} {'2030 Total':>12} {'Avg NPV Adv':>12}")
        print("-" * 100)
        
        for prop_type, row in prop_analysis.head(15).iterrows():
            opt_in_pct = row['opt_in_rate'] * 100
            print(f"{prop_type[:33]:<35} {int(row['total_buildings']):>6} "
                  f"{opt_in_pct:>7.1f}% ${row['total_penalty_2030']/1e6:>10.1f}M "
                  f"${row['avg_npv_advantage']:>11,.0f}")
        
        # High opportunity targets
        print(f"\n🎯 HIGH OPPORTUNITY PROPERTY TYPES:")
        print("   (High penalty exposure + Low opt-in rates = Business opportunity)")
        print("-" * 70)
        
        # Find types with high penalties but low opt-in rates
        high_opportunity = prop_analysis[
            (prop_analysis['total_penalty_2030'] > prop_analysis['total_penalty_2030'].median()) &
            (prop_analysis['opt_in_rate'] < 0.3)  # Less than 30% opt-in rate
        ].sort_values('total_penalty_2030', ascending=False)
        
        for prop_type, row in high_opportunity.head(5).iterrows():
            print(f"   {prop_type}: ${row['total_penalty_2030']:,.0f} exposure, "
                  f"{row['opt_in_rate']*100:.1f}% opt-in rate")

def generate_top_buildings_analysis(analyzer):
    """Identify and analyze highest-risk buildings"""
    print("\n" + "=" * 80)
    print("🎯 TOP HIGH-RISK BUILDINGS ANALYSIS")
    print("=" * 80)
    
    try:
        # Load building data and calculate individual risks
        buildings_analysis = []
        
        for idx, building in analyzer.portfolio.iterrows():
            building_data = analyzer.prepare_building_for_analysis(building)
            
            # Calculate standard path penalties
            standard_penalties = analyzer.calculate_building_penalties(building_data, 'standard')
            aco_penalties = analyzer.calculate_building_penalties(building_data, 'aco')
            
            # Calculate NPVs
            standard_npv = sum(penalty / (1.07 ** (int(year) - 2025)) 
                             for year, penalty in standard_penalties.items() 
                             if int(year) >= 2025)
            
            aco_npv = sum(penalty / (1.07 ** (int(year) - 2025)) 
                         for year, penalty in aco_penalties.items() 
                         if int(year) >= 2025)
            
            buildings_analysis.append({
                'building_id': building_data['building_id'],
                'property_type': building_data['property_type'],
                'sqft': building_data['sqft'],
                'current_eui': building_data['current_eui'],
                'final_target': building_data['final_target'],
                'eui_gap': building_data['current_eui'] - building_data['final_target'],
                'standard_npv': standard_npv,
                'aco_npv': aco_npv,
                'npv_advantage': standard_npv - aco_npv,
                'penalty_2030': standard_penalties.get('2030', 0)
            })
        
        risk_df = pd.DataFrame(buildings_analysis)
        
        # Top 20 by total NPV exposure
        top_risk = risk_df.nlargest(20, 'standard_npv')
        
        print("TOP 20 HIGHEST-RISK BUILDINGS (by NPV exposure):")
        print("-" * 100)
        print(f"{'Building ID':<12} {'Property Type':<25} {'Sq Ft':>10} {'EUI Gap':>8} {'NPV Risk':>12}")
        print("-" * 100)
        
        for _, building in top_risk.iterrows():
            print(f"{building['building_id']:<12} {building['property_type'][:23]:<25} "
                  f"{building['sqft']:>10,.0f} {building['eui_gap']:>7.1f} "
                  f"${building['standard_npv']:>11,.0f}")
        
        # Summary statistics
        total_portfolio_risk = risk_df['standard_npv'].sum()
        top_20_risk = top_risk['standard_npv'].sum()
        concentration = (top_20_risk / total_portfolio_risk) * 100
        
        print(f"\n📊 RISK CONCENTRATION:")
        print(f"   Total Portfolio NPV Risk: ${total_portfolio_risk:,.0f}")
        print(f"   Top 20 Buildings Risk: ${top_20_risk:,.0f}")
        print(f"   Risk Concentration: {concentration:.1f}% in top 20 buildings")
        
        # TEaaS opportunity analysis
        print(f"\n🔧 TEAAS BUSINESS OPPORTUNITY:")
        avg_building_risk = top_risk['standard_npv'].mean()
        print(f"   Average risk per top building: ${avg_building_risk:,.0f}")
        print(f"   Potential market size: {len(top_risk)} high-priority buildings")
        print(f"   Combined addressable risk: ${top_20_risk:,.0f}")
        
        return risk_df
        
    except Exception as e:
        print(f"❌ Error in top buildings analysis: {e}")
        return None

def save_business_intelligence_summary(scenarios, scenario_summary, output_dir):
    """Generate executive business intelligence summary"""
    print("\n" + "=" * 80)
    print("📋 GENERATING BUSINESS INTELLIGENCE SUMMARY")
    print("=" * 80)
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = os.path.join(output_dir, f'business_intelligence_summary_{timestamp}.txt')
        
        with open(summary_path, 'w') as f:
            f.write("ENERGIZE DENVER PORTFOLIO ANALYSIS\n")
            f.write("BUSINESS INTELLIGENCE SUMMARY\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 20 + "\n")
            if scenario_summary:
                standard_npv = scenario_summary.get('all_standard', {}).get('npv_total', 0)
                hybrid_npv = scenario_summary.get('hybrid', {}).get('npv_total', 0)
                savings = standard_npv - hybrid_npv
                
                f.write(f"Total Portfolio Risk (Standard Path): ${standard_npv:,.0f}\n")
                f.write(f"Optimized Portfolio Risk (Hybrid): ${hybrid_npv:,.0f}\n")
                f.write(f"Potential Savings Through Optimization: ${savings:,.0f}\n")
                f.write(f"Risk Reduction: {(savings/standard_npv)*100:.1f}%\n\n")
            
            f.write("KEY BUSINESS INSIGHTS\n")
            f.write("-" * 20 + "\n")
            f.write("1. Portfolio optimization can reduce penalty exposure significantly\n")
            f.write("2. ACO pathway beneficial for specific building types\n")
            f.write("3. Risk concentrated in largest buildings\n")
            f.write("4. TEaaS opportunity exists for high-risk properties\n")
            f.write("5. Timeline optimization critical for penalty minimization\n\n")
            
            f.write("RECOMMENDED ACTIONS\n")
            f.write("-" * 20 + "\n")
            f.write("1. Target top 20 highest-risk buildings immediately\n")
            f.write("2. Develop ACO education program for optimal property types\n")
            f.write("3. Create TEaaS offerings for buildings with >$100k NPV risk\n")
            f.write("4. Monitor compliance timeline for early intervention\n")
            f.write("5. Establish portfolio monitoring dashboard\n")
        
        print(f"📄 Business intelligence summary saved to: {summary_path}")
        
    except Exception as e:
        print(f"❌ Error saving business intelligence summary: {e}")

def main():
    """Execute comprehensive portfolio analysis"""
    
    # 1. Executive Summary
    analyzer = generate_executive_summary()
    if not analyzer:
        return False
    
    # 2. Three-Scenario Analysis
    scenarios, scenario_summary = run_three_scenario_analysis(analyzer)
    if not scenarios:
        return False
    
    # 3. Time Series Analysis
    generate_time_series_analysis(scenarios)
    
    # 4. Property Type Analysis
    generate_property_type_analysis(scenarios)
    
    # 5. Top Buildings Analysis
    top_buildings = generate_top_buildings_analysis(analyzer)
    
    # 6. Save Business Intelligence Summary
    output_dir = os.path.join(project_root, 'outputs', 'data')
    save_business_intelligence_summary(scenarios, scenario_summary, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ COMPREHENSIVE PORTFOLIO ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nGenerated Reports:")
    print("📊 Executive summary with key metrics")
    print("📈 Three-scenario penalty analysis") 
    print("📅 Time series progression (2025-2042)")
    print("🏢 Property type risk breakdown")
    print("🎯 Top 20 highest-risk buildings")
    print("📋 Business intelligence summary")
    print("📁 Excel workbooks with detailed data")
    print("📈 Visualization dashboards")
    print("\nFiles saved to: /outputs/ directory")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Portfolio analysis failed!")
        sys.exit(1)
