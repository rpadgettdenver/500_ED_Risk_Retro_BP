"""
Test script to verify Building 2952 ACO 2028 target is correct
"""
import sys
import os
sys.path.append('/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP')

from src.analysis.building_compliance_analyzer_v2 import EnhancedBuildingComplianceAnalyzer

# Test Building 2952
print("Testing Building 2952 ACO 2028 Target Correction")
print("=" * 60)

analyzer = EnhancedBuildingComplianceAnalyzer("2952")
analysis = analyzer.calculate_enhanced_penalties()

if analysis:
    print(f"\nBuilding 2952 Target Analysis:")
    print(f"Baseline Year: {analysis.get('baseline_year', 'Not found')}")
    print(f"Baseline EUI: {analysis.get('baseline_eui', 'Not found')}")
    print(f"Current EUI: {analysis.get('current_eui', 'Not found')}")
    
    print(f"\nTargets:")
    targets = analysis.get('adjusted_targets', {})
    for year in sorted(targets.keys()):
        print(f"  {year}: {targets[year]:.1f}")
    
    # Check if 2028 target matches First Interim Target
    first_interim = analyzer.building_targets_data.get('first_interim_target') if analyzer.building_targets_data else None
    target_2028 = targets.get(2028)
    
    print(f"\nVerification:")
    print(f"First Interim Target EUI: {first_interim}")
    print(f"ACO 2028 Target: {target_2028}")
    
    if first_interim and target_2028:
        if abs(first_interim - target_2028) < 0.01:
            print("✅ CORRECT: ACO 2028 target matches First Interim Target!")
        else:
            print("❌ ERROR: ACO 2028 target does NOT match First Interim Target!")
            print(f"   Expected: {first_interim}")
            print(f"   Got: {target_2028}")
else:
    print("Error: Could not generate analysis")
