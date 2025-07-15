"""Quick test of portfolio analyzer"""

import sys
sys.path.insert(0, '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP')

try:
    from src.analysis.portfolio_risk_analyzer import PortfolioRiskAnalyzer
    print("✅ Import successful")
    
    # Initialize
    analyzer = PortfolioRiskAnalyzer()
    print(f"✅ Loaded {len(analyzer.portfolio)} buildings")
    
    # Quick test - just run one scenario
    print("\n🔄 Running test scenario...")
    df_standard = analyzer.scenario_all_standard()
    print(f"✅ Standard scenario complete: {len(df_standard)} buildings analyzed")
    
    # Check penalty calculation
    total_2025 = df_standard['penalty_2025'].sum()
    print(f"✅ Total 2025 penalties: ${total_2025:,.0f}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
