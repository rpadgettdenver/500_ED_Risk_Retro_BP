"""
Simple test to verify HVAC modeler penalty rates
"""

import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP')

# Import and test
try:
    from src.models.hvac_system_impact_modeler import HVACSystemImpactModeler
    
    # Create modeler
    modeler = HVACSystemImpactModeler('2952')
    
    # Check if penalty_calc exists
    if hasattr(modeler, 'penalty_calc'):
        # Get rates
        standard_rate = modeler.penalty_calc.get_penalty_rate('standard')
        aco_rate = modeler.penalty_calc.get_penalty_rate('aco')
        
        print("HVAC Modeler Penalty Rates Test")
        print("=" * 40)
        print(f"Standard Path Rate: ${standard_rate}/kBtu")
        print(f"ACO Path Rate: ${aco_rate}/kBtu")
        print(f"ACO Premium: {(aco_rate/standard_rate - 1)*100:.0f}%")
        print("=" * 40)
        
        if standard_rate == 0.15 and aco_rate == 0.23:
            print("✅ PASS - Rates are correct!")
        else:
            print("❌ FAIL - Rates are incorrect!")
            
        # Test compliance calculation
        print("\nTesting compliance calculations...")
        test_eui = 70.0
        
        # Standard path
        standard = modeler._analyze_compliance(test_eui, 'standard')
        print("\nStandard Path:")
        for year, data in standard.items():
            if data['excess_eui'] > 0:
                print(f"  {year}: Rate=${data['penalty_rate']}/kBtu, Penalty=${data['annual_penalty']:,.0f}")
        
        # ACO path  
        aco = modeler._analyze_compliance(test_eui, 'aco')
        print("\nACO Path:")
        for year, data in aco.items():
            if data['excess_eui'] > 0:
                print(f"  {year}: Rate=${data['penalty_rate']}/kBtu, Penalty=${data['annual_penalty']:,.0f}")
                
    else:
        print("❌ FAIL - Penalty calculator not initialized!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
