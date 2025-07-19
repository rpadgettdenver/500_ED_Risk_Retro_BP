"""
Suggested File Name: analyze_top_penalty_buildings.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis/
Use: Analyze the top 10 buildings contributing to 2025 penalties

This script identifies and analyzes the buildings with the highest 2025 penalty exposure
to understand the concentration of risk in the portfolio.
"""

import pandas as pd
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_risk_analyzer_refined import PortfolioRiskAnalyzer


def analyze_top_penalty_buildings():
    """Analyze the top 10 buildings by 2025 penalty amount"""
    
    # Initialize analyzer
    analyzer = PortfolioRiskAnalyzer()
    
    # Run standard scenario to get 2025 penalties
    print("Running standard scenario analysis...")
    standard_scenario = analyzer.scenario_all_standard()
    
    # Get top 10 buildings by 2025 penalty
    top_10 = standard_scenario.nlargest(10, 'penalty_2025')
    
    # Calculate total penalties for context
    total_2025_penalty = standard_scenario['penalty_2025'].sum()
    top_10_penalty = top_10['penalty_2025'].sum()
    concentration = (top_10_penalty / total_2025_penalty) * 100
    
    print("\n" + "="*80)
    print("TOP 10 BUILDINGS BY 2025 PENALTY EXPOSURE")
    print("="*80)
    print(f"\nTotal 2025 Penalties (All Buildings): ${total_2025_penalty:,.0f}")
    print(f"Top 10 Buildings Penalties: ${top_10_penalty:,.0f}")
    print(f"Concentration: {concentration:.1f}% of total risk")
    
    # Merge with portfolio data to get more details
    portfolio_data = analyzer.portfolio.copy()
    portfolio_data['Building ID'] = portfolio_data['Building ID'].astype(str)
    top_10['building_id'] = top_10['building_id'].astype(str)
    
    top_10_detailed = pd.merge(
        top_10,
        portfolio_data[['Building ID', 'Building Name', 'Weather Normalized Site EUI', 
                       'First Interim Target EUI', 'Second Interim Target EUI', 
                       'Original Final Target EUI', 'Year Built']],
        left_on='building_id',
        right_on='Building ID',
        how='left'
    )
    
    # Calculate EUI gaps
    top_10_detailed['gap_2025'] = (
        top_10_detailed['Weather Normalized Site EUI'] - 
        top_10_detailed['First Interim Target EUI']
    )
    
    top_10_detailed['gap_2030'] = (
        top_10_detailed['Weather Normalized Site EUI'] - 
        top_10_detailed['Original Final Target EUI']
    )
    
    # Calculate penalty per sqft
    top_10_detailed['penalty_per_sqft_2025'] = (
        top_10_detailed['penalty_2025'] / top_10_detailed['sqft']
    )
    
    print("\n" + "-"*80)
    print("DETAILED ANALYSIS OF TOP 10 BUILDINGS")
    print("-"*80)
    
    for idx, (_, building) in enumerate(top_10_detailed.iterrows(), 1):
        print(f"\nRank #{idx}")
        print(f"Building ID: {building['building_id']}")
        print(f"Building Name: {building.get('Building Name', 'N/A')}")
        print(f"Property Type: {building['property_type']}")
        print(f"Size: {building['sqft']:,.0f} sq ft")
        print(f"Year Built: {int(building.get('Year Built', 0)) if pd.notna(building.get('Year Built')) else 'Unknown'}")
        print(f"Current EUI: {building['Weather Normalized Site EUI']:.1f} kBtu/sqft")
        print(f"2025 Target: {building['First Interim Target EUI']:.1f} kBtu/sqft")
        print(f"2025 Gap: {building['gap_2025']:.1f} kBtu/sqft")
        print(f"2025 Penalty: ${building['penalty_2025']:,.0f}")
        print(f"Penalty per sqft: ${building['penalty_per_sqft_2025']:.3f}")
        print(f"2030 Gap: {building['gap_2030']:.1f} kBtu/sqft")
        print(f"2030 Penalty: ${building['penalty_2030']:,.0f}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS FOR TOP 10")
    print("="*80)
    
    print(f"\nAverage Size: {top_10_detailed['sqft'].mean():,.0f} sq ft")
    print(f"Total Square Footage: {top_10_detailed['sqft'].sum():,.0f} sq ft")
    print(f"Average 2025 Penalty: ${top_10_detailed['penalty_2025'].mean():,.0f}")
    print(f"Average EUI Gap (2025): {top_10_detailed['gap_2025'].mean():.1f} kBtu/sqft")
    print(f"Average Penalty per sqft: ${top_10_detailed['penalty_per_sqft_2025'].mean():.3f}")
    
    # Property type breakdown
    print("\nProperty Type Distribution:")
    prop_type_counts = top_10_detailed['property_type'].value_counts()
    for prop_type, count in prop_type_counts.items():
        print(f"  {prop_type}: {count} buildings")
    
    # Age analysis
    current_year = 2025
    top_10_detailed['building_age'] = current_year - top_10_detailed['Year Built']
    avg_age = top_10_detailed['building_age'].mean()
    print(f"\nAverage Building Age: {avg_age:.0f} years")
    
    # Save detailed results
    output_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/top_10_penalty_buildings.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    top_10_detailed.to_csv(output_path, index=False)
    print(f"\nDetailed results saved to: {output_path}")
    
    return top_10_detailed


if __name__ == "__main__":
    top_10 = analyze_top_penalty_buildings()
