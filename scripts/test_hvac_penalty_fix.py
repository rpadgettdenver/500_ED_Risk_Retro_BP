"""
Test script to verify HVAC system impact modeler uses correct penalty rates
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.hvac_system_impact_modeler import HVACSystemImpactModeler


def test_penalty_rates():
    """Test that penalty rates are correct"""
    
    print("🧪 Testing HVAC System Impact Modeler Penalty Rates")
    print("=" * 60)
    
    # Initialize modeler for Building 2952
    modeler = HVACSystemImpactModeler('2952')
    
    # Test standard path compliance
    print("\n1. Testing Standard Path Compliance:")
    standard_compliance = modeler._analyze_compliance(70.0, 'standard')
    
    for year, data in standard_compliance.items():
        print(f"   {year}: Rate = ${data.get('penalty_rate', 'N/A')}/kBtu")
        
    # Verify standard rate is 0.15
    if any(data.get('penalty_rate') == 0.15 for data in standard_compliance.values()):
        print("   ✅ Standard path uses correct rate ($0.15/kBtu)")
    else:
        print("   ❌ Standard path rate is incorrect!")
    
    # Test ACO path compliance
    print("\n2. Testing ACO Path Compliance:")
    aco_compliance = modeler._analyze_compliance(70.0, 'aco')
    
    for year, data in aco_compliance.items():
        print(f"   {year}: Rate = ${data.get('penalty_rate', 'N/A')}/kBtu")
    
    # Verify ACO rate is 0.23
    if any(data.get('penalty_rate') == 0.23 for data in aco_compliance.values()):
        print("   ✅ ACO path uses correct rate ($0.23/kBtu)")
    else:
        print("   ❌ ACO path rate is incorrect!")
    
    # Test a full system comparison
    print("\n3. Testing Full System Comparison:")
    report = modeler.generate_scenario_report()
    
    print(f"\nBuilding: {report['building_name']}")
    print(f"Current EUI: {report['current_eui']}")
    
    # Check that penalties are calculated
    for scenario in report['scenarios']:
        if scenario['system_name'] == 'Current System':
            print(f"\nCurrent System Penalties:")
            print(f"  2025: ${scenario.get('2025_penalty', 0):,.0f}")
            print(f"  2027: ${scenario.get('2027_penalty', 0):,.0f}")
            print(f"  2030: ${scenario.get('2030_penalty', 0):,.0f}")
    
    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    test_penalty_rates()
