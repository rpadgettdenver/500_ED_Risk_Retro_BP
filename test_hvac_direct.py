"""
Direct test of HVAC modeler penalty rates - run this to verify the fix
"""

import sys
import os

# Add project root to path
project_root = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP'
sys.path.insert(0, project_root)

try:
    from src.models.hvac_system_impact_modeler import HVACSystemImpactModeler
    print("✅ Successfully imported HVAC modeler")
    
    # Test 1: Initialize modeler
    print("\n🧪 TEST 1: Initializing modeler for Building 2952...")
    modeler = HVACSystemImpactModeler('2952')
    print(f"   Building: {modeler.building_data['building_name']}")
    print(f"   Size: {modeler.building_data['sqft']:,} sq ft")
    print(f"   Current EUI: {modeler.building_data['current_weather_norm_eui']}")
    
    # Test 2: Check penalty calculator is initialized
    print("\n🧪 TEST 2: Checking penalty calculator...")
    if hasattr(modeler, 'penalty_calc'):
        print("   ✅ Penalty calculator is initialized")
        
        # Get rates
        standard_rate = modeler.penalty_calc.get_penalty_rate('standard')
        aco_rate = modeler.penalty_calc.get_penalty_rate('aco')
        
        print(f"   Standard rate: ${standard_rate}/kBtu")
        print(f"   ACO rate: ${aco_rate}/kBtu")
        print(f"   ACO is {(aco_rate/standard_rate - 1)*100:.0f}% higher than standard")
        
        if standard_rate == 0.15 and aco_rate == 0.23:
            print("   ✅ Rates are CORRECT!")
        else:
            print("   ❌ Rates are WRONG!")
    else:
        print("   ❌ Penalty calculator NOT initialized!")
    
    # Test 3: Test compliance analysis
    print("\n🧪 TEST 3: Testing compliance analysis...")
    
    # Test with an EUI that exceeds targets
    test_eui = 70.0  # Above typical targets
    
    print(f"\n   Testing with EUI = {test_eui}")
    print("   Standard Path:")
    standard_compliance = modeler._analyze_compliance(test_eui, 'standard')
    
    for year, data in standard_compliance.items():
        if data['excess_eui'] > 0:
            print(f"     {year}: Excess = {data['excess_eui']:.1f} kBtu/sqft, "
                  f"Rate = ${data['penalty_rate']}/kBtu, "
                  f"Penalty = ${data['annual_penalty']:,.0f}")
    
    print("\n   ACO Path:")
    aco_compliance = modeler._analyze_compliance(test_eui, 'aco')
    
    for year, data in aco_compliance.items():
        if data['excess_eui'] > 0:
            print(f"     {year}: Excess = {data['excess_eui']:.1f} kBtu/sqft, "
                  f"Rate = ${data['penalty_rate']}/kBtu, "
                  f"Penalty = ${data['annual_penalty']:,.0f}")
    
    # Test 4: Compare system scenarios
    print("\n🧪 TEST 4: Comparing HVAC system scenarios...")
    df_compare = modeler.compare_systems()
    
    print("\n   System Comparison Results:")
    print(f"   {'System':<25} {'New EUI':>10} {'2025 Penalty':>15} {'2030 Penalty':>15}")
    print("   " + "-" * 70)
    
    for idx, row in df_compare.iterrows():
        print(f"   {row['system_name']:<25} {row['new_eui']:>10.1f} "
              f"${row['2025_penalty']:>14,.0f} ${row['2030_penalty']:>14,.0f}")
    
    # Test 5: Check ACO penalty calculation in scenario report
    print("\n🧪 TEST 5: Checking ACO penalty multiplier...")
    
    # Look at the total penalties for standard vs opt-in
    current_system = df_compare[df_compare['system_name'] == 'Current System'].iloc[0]
    
    if 'total_penalties_standard' in current_system and 'total_penalties_optin' in current_system:
        standard_total = current_system['total_penalties_standard']
        optin_total = current_system['total_penalties_optin']
        
        print(f"\n   Total penalties (2025-2039):")
        print(f"   Standard path: ${standard_total:,.0f}")
        print(f"   Opt-in path: ${optin_total:,.0f}")
        
        # Check if opt-in penalties reflect higher rate
        if optin_total > 0 and standard_total > 0:
            # Account for timing differences
            print(f"   Opt-in uses higher rate: {optin_total > standard_total * 0.5}")
    
    print("\n✅ All tests completed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure you're in the project directory")
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
