"""
Run this script to test all the modules we've created
for the TES + HP retrofit analysis for Building 2952.
"""

import os
import sys

# Add the 'src' directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Import analysis modules
from models.hvac_system_impact_modeler import HVACSystemImpactModeler
from models.tes_hp_cash_flow_bridge import TESHPCashFlowBridge
from analysis.integrated_tes_hp_analyzer import IntegratedTESHPAnalyzer
from models.bridge_loan_investor_package import BridgeLoanInvestorPackage


def test_building_2952():
    print("=" * 80)
    print("TES+HP ANALYSIS FOR BUILDING 2952 (TIMPERLY CONDOMINIUM)")
    print("=" * 80)

    # 1. Test HVAC System Impact Model
    print("\n1. TESTING HVAC SYSTEM IMPACT MODEL...")
    try:
        building_data = {
            'building_id': '2952',
            'building_name': 'Timperly Condominium',
            'property_type': 'Multifamily Housing',
            'units': 52,
            'sqft': 52826,
            'weather_norm_eui': 65.3,
            'electricity_kwh': 210165,
            'gas_kbtu': 2584000,
            'total_ghg': 126.67,
            'is_epb': True,
            'first_interim_target': 65.4,
            'second_interim_target': 63.2,
            'final_target': 51.5,
        }
        print(f"Building: {building_data['building_name']}")
        print(f"Current EUI: {building_data['weather_norm_eui']}")
        print("✓ HVAC model data loaded")
    except Exception as e:
        print(f"✗ Error loading HVAC model: {e}")

    # 2. Test Cash Flow Bridge
    print("\n2. TESTING CASH FLOW BRIDGE...")
    try:
        cf_model = TESHPCashFlowBridge(project_data={
            'total_project_cost': '525000',
            'incentives': '12000'
        })
        cash_flows = cf_model.model_cash_flows()
        summary = cf_model.generate_summary_report()

        print(f"Total Project Cost: ${summary['project_costs']['total_project_cost']:,.0f}")
        print(f"Total Incentives: ${summary['incentives']['total_incentives']:,.0f}")
        print(f"Bridge Loan Needed: ${summary['bridge_loan']['maximum_draw']:,.0f}")
        print(f"Developer ROE: {summary['developer_returns']['return_on_equity']:.0%}")
        print("✓ Cash flow model complete")
    except Exception as e:
        print(f"✗ Error in cash flow model: {e}")

    # 3. Test Integrated Analyzer
    print("\n3. TESTING INTEGRATED ANALYZER...")
    try:
        analyzer = IntegratedTESHPAnalyzer()
        executive_summary = analyzer.generate_executive_summary()

        print(f"Recommended System: {executive_summary['recommended_solution']['system']}")
        print(f"Current EUI: {executive_summary['building']['current_eui']}")
        print(f"New EUI: {executive_summary['recommended_solution']['new_eui']}")
        print(f"EUI Reduction: {executive_summary['recommended_solution']['eui_reduction']:.0f}%")
        print(f"Penalties Avoided: ${executive_summary['recommended_solution']['penalties_avoided_15yr']:,.0f}")
        print(f"Compliant through 2030: {executive_summary['recommended_solution']['compliant_through_2030']}")
        print(f"Market Value: ${executive_summary['exit_valuation']['market_value']:,.0f}")
        print(f"Incentive Coverage: {executive_summary['project_economics']['incentive_coverage']:.0%}")

        # Generate full report
        report_path = os.path.join(project_root, 'outputs', 'building_2952_analysis.json')
        analyzer.generate_full_report(report_path)
        print(f"✓ Full report saved to: {report_path}")

        # Generate charts
        fig = analyzer.create_presentation_charts()
        chart_path = os.path.join(project_root, 'outputs', 'building_2952_charts.png')
        fig.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"✓ Charts saved to: {chart_path}")
    except Exception as e:
        print(f"✗ Error in integrated analyzer: {e}")

    # 4. Test Bridge Loan Package
    print("\n4. TESTING BRIDGE LOAN PACKAGE...")
    try:
        package_gen = BridgeLoanInvestorPackage()
        pdf_path = package_gen.generate_complete_package()
        print(f"✓ Bridge loan package saved to: {pdf_path}")

        term_sheet = package_gen.generate_term_sheet()
        print(f"✓ Term sheet generated for ${term_sheet['loan_amount']:,.0f} loan")
    except Exception as e:
        print(f"✗ Error generating bridge loan package: {e}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    os.makedirs('outputs', exist_ok=True)
    test_building_2952()
