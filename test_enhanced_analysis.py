"""
Suggested File Name: test_enhanced_analysis.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Test the enhanced building compliance analyzer with correct penalty rates

This script tests the new features:
1. Correct penalty rates
2. NPV calculations
3. 42% cap and MAI floor
4. Enhanced visualizations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from analysis.building_compliance_analyzer_v2 import EnhancedBuildingComplianceAnalyzer

def test_building_2952():
    """Test analysis for Building 2952"""
    
    print("🧪 TESTING ENHANCED COMPLIANCE ANALYZER")
    print("=" * 60)
    print("\nTesting with Building 2952 (Timperly Condominium)")
    print("This will verify:")
    print("- Correct penalty rates ($0.15 standard, $0.23 opt-in)")
    print("- NPV calculations with 7% discount rate")
    print("- Target adjustments (42% cap, MAI floor)")
    print("- Comprehensive recommendation logic\n")
    
    try:
        # Create analyzer
        analyzer = EnhancedBuildingComplianceAnalyzer(
            building_id="2952",
            data_dir="/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data"
        )
        
        # Generate report
        analysis, fig = analyzer.generate_enhanced_report()
        
        if analysis:
            print("\n✅ Analysis completed successfully!")
            
            # Verify penalty rates
            print("\n🔍 Verifying Penalty Calculations:")
            
            # Standard path
            standard_rate = analysis['standard_path']['penalty_rate']
            print(f"   Standard path rate: ${standard_rate:.2f}/kBtu {'✅' if standard_rate == 0.15 else '❌'}")
            
            # Opt-in path
            optin_rate = analysis['optin_path']['penalty_rate']
            print(f"   Opt-in path rate: ${optin_rate:.2f}/kBtu {'✅' if optin_rate == 0.23 else '❌'}")
            
            # Check NPV calculations
            print("\n💰 NPV Analysis:")
            print(f"   Standard path total (nominal): ${analysis['standard_path']['total_nominal']:,.0f}")
            print(f"   Standard path total (NPV): ${analysis['standard_path']['total_npv']:,.0f}")
            print(f"   Opt-in path total (nominal): ${analysis['optin_path']['total_nominal']:,.0f}")
            print(f"   Opt-in path total (NPV): ${analysis['optin_path']['total_npv']:,.0f}")
            
            # NPV discount verification
            if analysis['standard_path']['total_nominal'] > 0:
                npv_ratio = analysis['standard_path']['total_npv'] / analysis['standard_path']['total_nominal']
                print(f"   NPV discount factor: {npv_ratio:.2%} (should be < 100%)")
            
            # Check recommendation
            print(f"\n📊 Recommendation: {analysis['recommendation']['recommendation'].upper()}")
            print(f"   Confidence: {analysis['recommendation']['confidence']}%")
            print(f"   Primary reason: {analysis['recommendation']['primary_reason']}")
            
            # Show visualization if available
            if fig:
                print("\n📈 Visualizations generated successfully!")
                print("   Check the data/analysis folder for the output files")
                
                # Optionally show the plot
                response = input("\nShow visualizations? (y/n): ")
                if response.lower() == 'y':
                    import matplotlib.pyplot as plt
                    plt.show()
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

def test_penalty_calculator():
    """Test the unified penalty calculator directly"""
    
    print("\n\n🧪 TESTING PENALTY CALCULATOR MODULE")
    print("=" * 60)
    
    try:
        from utils.penalty_calculator import PenaltyCalculator, calculate_building_penalties
        
        calc = PenaltyCalculator()
        
        # Test data for Building 2952
        test_building = {
            'building_id': '2952',
            'building_name': 'Timperly Condominium',
            'current_eui': 65.3,
            'baseline_eui': 70.5,
            'sqft': 52826,
            'property_type': 'Multifamily Housing',
            'is_mai': False,
            'targets': {
                2025: 65.4,
                2027: 63.2,
                2030: 51.5
            },
            'building_age': 30,
            'cash_constrained': False
        }
        
        print("\n📏 Testing target adjustments:")
        
        # Test 42% cap
        adjusted_2030, reason = calc.apply_target_adjustments(
            target_eui=51.5,
            baseline_eui=70.5,
            property_type='Multifamily Housing',
            is_mai=False
        )
        
        cap_target = 70.5 * (1 - 0.42)  # 40.89
        print(f"   Original 2030 target: 51.5")
        print(f"   42% cap would be: {cap_target:.1f}")
        print(f"   Adjusted target: {adjusted_2030:.1f}")
        print(f"   Reason: {reason}")
        
        # Test MAI floor
        print("\n   Testing MAI floor:")
        mai_adjusted, mai_reason = calc.apply_target_adjustments(
            target_eui=45.0,
            baseline_eui=100.0,
            property_type='Manufacturing/Industrial Plant',
            is_mai=True
        )
        print(f"   Original MAI target: 45.0")
        print(f"   Adjusted target: {mai_adjusted:.1f}")
        print(f"   Reason: {mai_reason}")
        
        # Test full analysis
        print("\n📊 Running full penalty analysis:")
        full_analysis = calculate_building_penalties(test_building)
        
        print(f"\n   Standard path:")
        for year, details in full_analysis['standard_path']['penalties_by_year'].items():
            print(f"      {year}: ${details['penalty']:,.0f} (NPV: ${details['npv']:,.0f})")
        
        print(f"\n   Opt-in path:")
        for year, details in full_analysis['optin_path']['penalties_by_year'].items():
            print(f"      {year}: ${details['penalty']:,.0f} (NPV: ${details['npv']:,.0f})")
        
        print(f"\n   Recommendation: {full_analysis['recommendation']['recommendation'].upper()}")
        print(f"   NPV advantage of opt-in: ${full_analysis['recommendation']['npv_advantage']:,.0f}")
        
        print("\n✅ Penalty calculator tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error testing penalty calculator: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main test execution"""
    
    # Test the penalty calculator
    test_penalty_calculator()
    
    # Test the enhanced analyzer
    test_building_2952()
    
    print("\n\n🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Authenticate with Google Cloud: gcloud auth application-default login")
    print("2. Run the BigQuery analysis: python src/gcp/rerun_and_compare_analysis.py")
    print("3. Review the results and validate against these local calculations")

if __name__ == "__main__":
    main()
