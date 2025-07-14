"""
Portfolio analysis summary with corrected rates
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP')

try:
    # Import required modules
    from src.analysis.portfolio_risk_analyzer import PortfolioRiskAnalyzer
    
    print("🚀 PORTFOLIO RISK ANALYSIS - CORRECTED RATES")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("\n📊 Loading portfolio data...")
    
    # Initialize analyzer
    analyzer = PortfolioRiskAnalyzer()
    
    print(f"✓ Loaded {len(analyzer.portfolio)} buildings")
    print(f"✓ Total square footage: {analyzer.portfolio['Master Sq Ft'].sum():,.0f} sq ft")
    
    # Run scenarios
    print("\n📈 Running scenarios...")
    
    # Scenario 1: All Standard
    print("\n1. All Standard Path:")
    df_standard = analyzer.scenario_all_standard()
    
    # Calculate key metrics
    penalty_2025_std = df_standard['penalty_2025'].sum()
    penalty_2030_std = df_standard['penalty_2030'].sum()
    buildings_at_risk_std = (df_standard['penalty_2025'] > 0).sum()
    
    print(f"   Buildings at risk in 2025: {buildings_at_risk_std}")
    print(f"   Total 2025 penalties: ${penalty_2025_std:,.0f}")
    print(f"   Total 2030 penalties: ${penalty_2030_std:,.0f}")
    
    # Scenario 2: All ACO
    print("\n2. All ACO Path:")
    df_aco = analyzer.scenario_all_aco()
    
    # Calculate key metrics
    penalty_2028_aco = df_aco['penalty_2028'].sum()
    penalty_2032_aco = df_aco['penalty_2032'].sum()
    
    print(f"   No penalties until 2028")
    print(f"   Total 2028 penalties: ${penalty_2028_aco:,.0f}")
    print(f"   Total 2032 penalties: ${penalty_2032_aco:,.0f}")
    
    # Compare rates
    if penalty_2025_std > 0 and penalty_2028_aco > 0:
        # Both use first interim target, so compare rates
        rate_ratio = penalty_2028_aco / penalty_2025_std
        print(f"   ACO/Standard penalty ratio: {rate_ratio:.2f}x (should be ~1.53x)")
    
    # Scenario 3: Hybrid
    print("\n3. Hybrid (Opt-in Logic):")
    df_hybrid = analyzer.scenario_hybrid()
    
    # Calculate metrics
    opt_in_count = df_hybrid['should_opt_in'].sum()
    opt_in_rate = opt_in_count / len(df_hybrid) * 100
    
    print(f"   Buildings opting into ACO: {opt_in_count} ({opt_in_rate:.1f}%)")
    print(f"   Buildings on standard path: {len(df_hybrid) - opt_in_count}")
    
    # Show top opt-in reasons
    if 'opt_in_rationale' in df_hybrid.columns:
        print("\n   Top opt-in rationales:")
        rationales = df_hybrid[df_hybrid['should_opt_in']]['opt_in_rationale'].value_counts().head(5)
        for rationale, count in rationales.items():
            print(f"     {rationale}: {count} buildings")
    
    # NPV Comparison
    print("\n💰 NPV COMPARISON (7% discount rate):")
    print("-" * 60)
    
    # Calculate NPV for each scenario
    discount_rate = 0.07
    
    # Standard NPV
    npv_standard = 0
    for year in range(2025, 2043):
        col = f'penalty_{year}'
        if col in df_standard.columns:
            penalties = df_standard[col].sum()
            years_from_2025 = year - 2025
            npv_standard += penalties / ((1 + discount_rate) ** years_from_2025)
    
    # ACO NPV
    npv_aco = 0
    for year in range(2025, 2043):
        col = f'penalty_{year}'
        if col in df_aco.columns:
            penalties = df_aco[col].sum()
            years_from_2025 = year - 2025
            npv_aco += penalties / ((1 + discount_rate) ** years_from_2025)
    
    # Hybrid NPV
    npv_hybrid = 0
    for year in range(2025, 2043):
        col = f'penalty_{year}'
        if col in df_hybrid.columns:
            penalties = df_hybrid[col].sum()
            years_from_2025 = year - 2025
            npv_hybrid += penalties / ((1 + discount_rate) ** years_from_2025)
    
    print(f"All Standard Path: ${npv_standard:,.0f}")
    print(f"All ACO Path: ${npv_aco:,.0f}")
    print(f"Hybrid (Realistic): ${npv_hybrid:,.0f}")
    print(f"\nSavings from optimal strategy: ${npv_standard - npv_hybrid:,.0f}")
    
    # Property type analysis
    print("\n🏢 TOP PROPERTY TYPES BY PENALTY EXPOSURE:")
    print("-" * 60)
    
    prop_type_risk = df_hybrid.groupby('property_type').agg({
        'building_id': 'count',
        'penalty_2025': 'sum',
        'should_opt_in': 'mean'
    }).sort_values('penalty_2025', ascending=False).head(10)
    
    print(f"{'Property Type':<30} {'Count':>6} {'2025 Penalty':>15} {'Opt-in %':>10}")
    for prop_type, row in prop_type_risk.iterrows():
        print(f"{prop_type[:30]:<30} {int(row['building_id']):>6} "
              f"${row['penalty_2025']:>14,.0f} {row['should_opt_in']*100:>9.1f}%")
    
    print("\n✅ Analysis complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
