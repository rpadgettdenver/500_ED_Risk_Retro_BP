"""
Suggested File Name: fix_hvac_penalty_rates.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/scripts/
Use: Fix the HVAC system impact modeler to use the penalty calculator module instead of hardcoded rates

This script updates the HVAC system impact modeler to:
1. Import and use the penalty calculator module
2. Remove hardcoded penalty rates
3. Use correct rates for each compliance path
"""

import os
import re


def fix_hvac_system_impact_modeler():
    """Fix the penalty rates in hvac_system_impact_modeler.py"""
    
    file_path = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/models/hvac_system_impact_modeler.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("🔍 Analyzing HVAC system impact modeler...")
    
    # Check if penalty calculator is already imported
    if "from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator" not in content:
        print("❌ Penalty calculator not imported")
    else:
        print("✅ Penalty calculator already imported")
    
    # Check for hardcoded rates in _analyze_compliance method
    hardcoded_pattern = r"penalty_rate = 0\.15\s*#.*(?:Standard path rate|$)"
    if re.search(hardcoded_pattern, content):
        print("❌ Found hardcoded penalty rates in _analyze_compliance method")
        
        # Apply fixes
        print("\n📝 Applying fixes...")
        
        # 1. Make sure penalty calculator is initialized in __init__
        if "self.penalty_calc = EnergizeDenverPenaltyCalculator()" not in content:
            # Find the __init__ method and add penalty calculator
            init_pattern = r"(def __init__.*?:\n(?:.*?\n)*?)(        # System efficiency factors)"
            replacement = r"\1        # Initialize penalty calculator\n        self.penalty_calc = EnergizeDenverPenaltyCalculator()\n        \n\2"
            content = re.sub(init_pattern, replacement, content, flags=re.DOTALL)
            print("  ✅ Added penalty calculator initialization")
        
        # 2. Fix the _analyze_compliance method
        # Find the method and replace it completely
        analyze_compliance_pattern = r"def _analyze_compliance\(self, effective_eui: float\) -> Dict:(?:.*?)return compliance"
        
        new_analyze_compliance = '''def _analyze_compliance(self, effective_eui: float, compliance_path: str = 'standard') -> Dict:
        """Analyze compliance with Energize Denver targets
        
        Args:
            effective_eui: Effective EUI after electrification bonus
            compliance_path: 'standard' or 'aco' compliance path
        """
        targets = {
            '2025_target': self.building_data.get('first_interim_target', 65.4),
            '2027_target': self.building_data.get('second_interim_target', 63.2),
            '2030_target': self.building_data.get('final_target', 51.5),
        }
        
        # ACO path uses different years
        if compliance_path == 'aco':
            targets = {
                '2028_target': self.building_data.get('first_interim_target', 65.4),
                '2032_target': self.building_data.get('final_target', 51.5),
            }
        
        compliance = {}
        
        for year, target in targets.items():
            if target > 0:
                compliant = effective_eui <= target
                excess = max(0, effective_eui - target)
                
                # Use penalty calculator for correct rates
                penalty_rate = self.penalty_calc.get_penalty_rate(compliance_path)
                    
                annual_penalty = excess * self.building_data['sqft'] * penalty_rate
                
                compliance[year] = {
                    'target_eui': target,
                    'compliant': compliant,
                    'excess_eui': round(excess, 1),
                    'penalty_rate': penalty_rate,
                    'annual_penalty': round(annual_penalty, 0),
                }
        
        return compliance'''
        
        content = re.sub(analyze_compliance_pattern, new_analyze_compliance, content, flags=re.DOTALL)
        print("  ✅ Fixed _analyze_compliance method to use penalty calculator")
        
        # 3. Update the model_system_impact method to pass compliance path
        # Find where _analyze_compliance is called
        analyze_call_pattern = r"results\.update\(self\._analyze_compliance\(results\['effective_eui_for_compliance'\]\)\)"
        new_analyze_call = "results.update(self._analyze_compliance(results['effective_eui_for_compliance'], 'standard'))"
        content = content.replace(analyze_call_pattern, new_analyze_call)
        print("  ✅ Updated _analyze_compliance call")
        
        # 4. Fix the TODO comment
        todo_pattern = r"# TODO: Update to use penalty_calculator module for correct rates"
        content = content.replace(todo_pattern, "# Using penalty_calculator module for correct rates")
        
        # Write back the fixed content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("\n✅ Successfully fixed HVAC system impact modeler!")
        return True
    
    else:
        print("✅ No hardcoded penalty rates found - file may already be fixed")
        return True


def verify_fix():
    """Verify the fix was applied correctly"""
    
    file_path = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/models/hvac_system_impact_modeler.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("\n🔍 Verifying fix...")
    
    checks = [
        ("Penalty calculator imported", "from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator" in content),
        ("Penalty calculator initialized", "self.penalty_calc = EnergizeDenverPenaltyCalculator()" in content),
        ("No hardcoded rates", "penalty_rate = 0.15" not in content),
        ("Uses get_penalty_rate", "self.penalty_calc.get_penalty_rate" in content),
        ("Compliance path parameter", "_analyze_compliance(self, effective_eui: float, compliance_path: str = 'standard')" in content)
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def create_test_script():
    """Create a test script to verify the fix works"""
    
    test_script = '''"""
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
    print("\\n1. Testing Standard Path Compliance:")
    standard_compliance = modeler._analyze_compliance(70.0, 'standard')
    
    for year, data in standard_compliance.items():
        print(f"   {year}: Rate = ${data.get('penalty_rate', 'N/A')}/kBtu")
        
    # Verify standard rate is 0.15
    if any(data.get('penalty_rate') == 0.15 for data in standard_compliance.values()):
        print("   ✅ Standard path uses correct rate ($0.15/kBtu)")
    else:
        print("   ❌ Standard path rate is incorrect!")
    
    # Test ACO path compliance
    print("\\n2. Testing ACO Path Compliance:")
    aco_compliance = modeler._analyze_compliance(70.0, 'aco')
    
    for year, data in aco_compliance.items():
        print(f"   {year}: Rate = ${data.get('penalty_rate', 'N/A')}/kBtu")
    
    # Verify ACO rate is 0.23
    if any(data.get('penalty_rate') == 0.23 for data in aco_compliance.values()):
        print("   ✅ ACO path uses correct rate ($0.23/kBtu)")
    else:
        print("   ❌ ACO path rate is incorrect!")
    
    # Test a full system comparison
    print("\\n3. Testing Full System Comparison:")
    report = modeler.generate_scenario_report()
    
    print(f"\\nBuilding: {report['building_name']}")
    print(f"Current EUI: {report['current_eui']}")
    
    # Check that penalties are calculated
    for scenario in report['scenarios']:
        if scenario['system_name'] == 'Current System':
            print(f"\\nCurrent System Penalties:")
            print(f"  2025: ${scenario.get('2025_penalty', 0):,.0f}")
            print(f"  2027: ${scenario.get('2027_penalty', 0):,.0f}")
            print(f"  2030: ${scenario.get('2030_penalty', 0):,.0f}")
    
    print("\\n✅ Test completed successfully!")


if __name__ == "__main__":
    test_penalty_rates()
'''
    
    test_path = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/scripts/test_hvac_penalty_fix.py"
    
    with open(test_path, 'w') as f:
        f.write(test_script)
    
    print(f"\n📝 Created test script: {test_path}")
    print("   Run it to verify the fix works correctly")


def main():
    """Main execution"""
    print("🔧 FIXING HVAC SYSTEM IMPACT MODELER")
    print("=" * 60)
    print("This script fixes hardcoded penalty rates in the HVAC modeler")
    print("Correct rates: Standard=$0.15/kBtu, ACO=$0.23/kBtu\n")
    
    # Apply the fix
    success = fix_hvac_system_impact_modeler()
    
    if success:
        # Verify the fix
        if verify_fix():
            print("\n✅ All checks passed!")
            
            # Create test script
            create_test_script()
            
            print("\n🎉 HVAC System Impact Modeler successfully updated!")
            print("\nNext steps:")
            print("1. Run the test script to verify functionality")
            print("2. Re-run any HVAC system analyses")
            print("3. Check for similar issues in other models")
        else:
            print("\n⚠️  Some verification checks failed")
            print("Please review the file manually")
    else:
        print("\n❌ Failed to apply fixes")
        print("Please check the file manually")


if __name__ == "__main__":
    main()
