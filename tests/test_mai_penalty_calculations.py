"""
Suggested File Name: test_mai_penalty_calculations.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Test script to verify MAI penalty calculations are working correctly

This script:
1. Loads MAI building data
2. Calculates penalties for specific MAI buildings
3. Verifies the calculations match expected values
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.penalty_calculator import EnergizeDenverPenaltyCalculator
from data_processing.mai_handler import MAIHandler


def test_mai_penalty_calculations():
    """Test MAI penalty calculations for buildings identified in the debugger"""
    print("MAI Penalty Calculation Test")
    print("=" * 60)
    
    # Initialize MAI handler
    data_dir = Path(__file__).parent / 'data' / 'raw'
    mai_handler = MAIHandler(data_dir)
    
    # Get MAI building IDs
    mai_ids = mai_handler.get_mai_building_ids()
    mai_lookup = {building_id: True for building_id in mai_ids}
    
    # Initialize penalty calculator with MAI lookup
    penalty_calc = EnergizeDenverPenaltyCalculator(mai_lookup=mai_lookup)
    
    # Test buildings from the debugger output that should have penalties
    test_buildings = [
        {'id': '1216', 'name': '4890 ironton', 'gap': 4.3},
        {'id': '1316', 'name': 'bimbo bakeries usa mile-hi bakery', 'gap': 27.1},
        {'id': '1496', 'name': '1496 - 6275 e 39th ave', 'gap': 21.7},
        {'id': '3274', 'name': 'denver osage partners, llc', 'gap': 0.2},
        {'id': '3277', 'name': 'bron aero tech', 'gap': 3.1}
    ]
    
    print("\nTesting MAI buildings that should have penalties:")
    print("-" * 60)
    
    for test_building in test_buildings:
        building_id = test_building['id']
        
        # Get MAI data
        mai_data = mai_handler.get_mai_targets(building_id)
        
        if mai_data:
            print(f"\nBuilding ID: {building_id} - {test_building['name']}")
            print(f"  Expected gap: {test_building['gap']:.1f}%")
            print(f"  MAI Status: {'Yes' if mai_data['approved_mai'] else 'No'}")
            print(f"  Building Status: {mai_data['building_status']}")
            print(f"  Current FF Usage: {mai_data['current_ff_usage']:,.0f} kBtu")
            print(f"  Interim Target Year: {mai_data['interim_target_year']}")
            print(f"  Interim Target EUI: {mai_data['interim_target']}")
            
            # To calculate actual penalty, we need square footage
            # Let's load the main building data to get sqft
            try:
                # Try to load from the comprehensive file
                comprehensive_file = Path(__file__).parent / 'data' / 'processed' / 'energize_denver_comprehensive_latest.csv'
                if comprehensive_file.exists():
                    df_comp = pd.read_csv(comprehensive_file)
                    df_comp['Building ID'] = df_comp['Building ID'].astype(str)
                    
                    building_info = df_comp[df_comp['Building ID'] == building_id]
                    if not building_info.empty:
                        sqft = building_info.iloc[0]['Master Sq Ft']
                        current_eui = building_info.iloc[0]['Weather Normalized Site EUI']
                        
                        print(f"  Square Footage: {sqft:,.0f}")
                        print(f"  Current EUI: {current_eui:.1f}")
                        
                        # Calculate penalty
                        if mai_data['interim_target'] > 0:
                            gap_eui = max(0, current_eui - mai_data['interim_target'])
                            penalty_rate = penalty_calc.get_penalty_rate('aco')  # MAI uses ACO rate
                            penalty = gap_eui * sqft * penalty_rate
                            
                            print(f"  EUI Gap: {gap_eui:.1f} kBtu/sqft")
                            print(f"  Penalty Rate: ${penalty_rate}/kBtu")
                            print(f"  2028 Penalty: ${penalty:,.2f}")
                        else:
                            print("  ⚠️  No interim target available")
                    else:
                        print("  ⚠️  Building not found in comprehensive data")
                        
                        # Try alternative calculation with FF usage
                        if mai_data['current_ff_usage'] > 0 and mai_data['interim_target'] > 0:
                            # Estimate sqft from FF usage and target
                            # This is approximate: sqft = FF_usage / target_eui
                            estimated_sqft = mai_data['current_ff_usage'] / mai_data['interim_target']
                            print(f"\n  Estimated Square Footage: {estimated_sqft:,.0f}")
                            print(f"  (Calculated from FF usage / target EUI)")
                            
            except Exception as e:
                print(f"  ⚠️  Could not load comprehensive data: {e}")
        else:
            print(f"\n⚠️  No MAI data found for building {building_id}")
    
    # Summary statistics
    print("\n\nMAI Portfolio Summary:")
    print("-" * 60)
    
    mai_stats = mai_handler.get_mai_summary_stats()
    print(f"Total MAI buildings: {mai_stats['total_mai_buildings']}")
    print(f"Buildings with valid baseline: {mai_stats['with_valid_baseline']}")
    print(f"Buildings with zero baseline: {mai_stats['zero_baseline']} ({mai_stats['percent_zero_baseline']:.1f}%)")
    
    print("\nBuilding Status Distribution:")
    for status, count in mai_stats['building_status_counts'].items():
        print(f"  {status}: {count}")
    
    print("\nTop Property Types:")
    for i, prop_type in enumerate(mai_stats['top_property_types'][:5], 1):
        count = mai_stats['property_type_counts'].get(prop_type, 0)
        print(f"  {i}. {prop_type}: {count} buildings")


def verify_mai_penalty_logic():
    """Verify the penalty calculation logic for MAI buildings"""
    print("\n\nMAI Penalty Logic Verification")
    print("=" * 60)
    
    # Create test cases
    test_cases = [
        {
            'name': 'MAI building above interim target',
            'current_eui': 100,
            'interim_target': 80,
            'sqft': 50000,
            'expected_gap': 20,
            'expected_penalty': 20 * 50000 * 0.23  # Gap * sqft * ACO rate
        },
        {
            'name': 'MAI building below interim target',
            'current_eui': 70,
            'interim_target': 80,
            'sqft': 50000,
            'expected_gap': 0,
            'expected_penalty': 0
        },
        {
            'name': 'MAI building with large gap',
            'current_eui': 150,
            'interim_target': 100,
            'sqft': 100000,
            'expected_gap': 50,
            'expected_penalty': 50 * 100000 * 0.23
        }
    ]
    
    # Initialize calculator
    penalty_calc = EnergizeDenverPenaltyCalculator()
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"  Current EUI: {test_case['current_eui']}")
        print(f"  Target EUI: {test_case['interim_target']}")
        print(f"  Square Footage: {test_case['sqft']:,}")
        
        # Calculate penalty
        penalty = penalty_calc.calculate_penalty(
            actual_eui=test_case['current_eui'],
            target_eui=test_case['interim_target'],
            sqft=test_case['sqft'],
            penalty_rate=penalty_calc.get_penalty_rate('aco')
        )
        
        print(f"  Expected Gap: {test_case['expected_gap']} kBtu/sqft")
        print(f"  Expected Penalty: ${test_case['expected_penalty']:,.2f}")
        print(f"  Calculated Penalty: ${penalty:,.2f}")
        print(f"  ✓ PASS" if abs(penalty - test_case['expected_penalty']) < 0.01 else "  ✗ FAIL")


if __name__ == "__main__":
    # Run tests
    test_mai_penalty_calculations()
    verify_mai_penalty_logic()
    
    print("\n\nTest complete!")
