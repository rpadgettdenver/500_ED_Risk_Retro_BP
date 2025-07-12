"""
Run TES+HP analysis with unified configuration
"""

import sys
import os

# Add the src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Import modules
from config import get_config, update_config
from models.tes_hp_cash_flow_bridge import TESHPCashFlowBridge
from analysis.integrated_tes_hp_analyzer import IntegratedTESHPAnalyzer
from models.bridge_loan_investor_package import BridgeLoanInvestorPackage

def run_unified_analysis():
    """Run complete analysis using unified configuration"""
    
    print("="*80)
    print("TES+HP ANALYSIS WITH UNIFIED CONFIGURATION")
    print("="*80)
    
    # Get the unified configuration
    config = get_config()
    
    # Show current assumptions
    print("\nCURRENT CONFIGURATION:")
    print("-"*40)
    costs = config.calculate_project_costs()
    incentives = config.calculate_incentives(costs)
    
    print(f"Equipment base cost: ${config.config['systems']['4pipe_wshp_tes']['equipment_cost_base']:,.0f}")
    print(f"TES cost: ${config.config['systems']['4pipe_wshp_tes']['tes_cost']:,.0f}")
    print(f"Market escalation: {config.config['financial']['market_escalation']:.0%}")
    print(f"Total project cost: ${costs['total_project_cost']:,.0f}")
    print(f"Total incentives: ${incentives['total_incentives']:,.0f}")
    print(f"Net project cost: ${incentives['net_project_cost']:,.0f}")
    print(f"Incentive coverage: {incentives['incentive_coverage']:.0%}")
    
    # 1. Run integrated analysis
    print("\n1. INTEGRATED ANALYSIS")
    print("-"*40)
    try:
        analyzer = IntegratedTESHPAnalyzer()
        summary = analyzer.generate_executive_summary()
        
        print(f"Building: {summary['building']['name']}")
        print(f"Recommended system: {summary['recommended_solution']['system']}")
        print(f"EUI reduction: {summary['recommended_solution']['eui_reduction']:.0f}%")
        print(f"Project cost: ${summary['project_economics']['total_cost']:,.0f}")
        print(f"Incentive coverage: {summary['project_economics']['incentive_coverage']:.0%}")
        print(f"Developer ROE: {summary['developer_returns']['return_on_equity']:.0%}")
        
        # Save report
        report_path = os.path.join(project_root, 'outputs', 'unified_analysis.json')
        analyzer.generate_full_report(report_path)
        print(f"✓ Report saved to: {report_path}")
        
        # Generate charts
        fig = analyzer.create_presentation_charts()
        chart_path = os.path.join(project_root, 'outputs', 'unified_charts.png')
        fig.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"✓ Charts saved to: {chart_path}")
        
    except Exception as e:
        print(f"✗ Error in integrated analysis: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Run cash flow analysis
    print("\n2. CASH FLOW ANALYSIS")
    print("-"*40)
    try:
        # Get config for cash flow module
        cf_config = config.get_config_for_modules()['cash_flow']
        cf_model = TESHPCashFlowBridge(cf_config)
        cf_model.model_cash_flows()
        cf_summary = cf_model.generate_summary_report()
        
        print(f"Total project cost: ${cf_summary['project_costs']['total_project_cost']:,.0f}")
        print(f"Bridge loan needed: ${cf_summary['bridge_loan']['maximum_draw']:,.0f}")
        print(f"Developer ROE: {cf_summary['developer_returns']['return_on_equity']:.0%}")
        print("✓ Cash flow analysis complete")
        
    except Exception as e:
        print(f"✗ Error in cash flow analysis: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Generate bridge loan package
    print("\n3. BRIDGE LOAN PACKAGE")
    print("-"*40)
    try:
        # Use calculated values for bridge loan package
        bl_config = {
            'project_name': f"{config.config['building']['building_name']} TES+HP Retrofit",
            'building_address': config.config['building']['address'],
            'building_type': f"{config.config['building']['property_type']} ({config.config['building']['units']} units)",
            'developer': 'Denver Thermal Energy Solutions LLC',
            
            'total_project_cost': costs['total_project_cost'],
            'equipment_cost': costs['escalated_equipment'],
            'soft_costs': costs['soft_costs'],
            
            'itc_amount': incentives['itc_amount'],
            'itc_sale_price': incentives['itc_proceeds'],
            'depreciation_value': incentives['depreciation_tax_value'],
            'depreciation_sale': incentives['depreciation_proceeds'],
            'drcog_grant': incentives['drcog_grant'],
            'xcel_rebate': incentives['xcel_rebate'],
            
            'bridge_request': costs['total_project_cost'] * 0.85,
            'origination_fee': costs['total_project_cost'] * 0.85 * 0.02,
            'interest_rate': config.config['financial']['bridge_loan_rate'],
            'term_months': config.config['financial']['bridge_loan_term_months'],
            
            'equipment_lien_value': costs['escalated_equipment'],
            'contract_value': costs['total_project_cost'] * 2,
            'personal_guarantee': True,
            'completion_guarantee': True,
        }
        
        package_gen = BridgeLoanInvestorPackage(bl_config)
        pdf_path = package_gen.generate_complete_package()
        print(f"✓ Bridge loan package saved to: {pdf_path}")
        
    except Exception as e:
        print(f"✗ Error generating bridge loan package: {e}")
        import traceback
        traceback.print_exc()
    
    # Show how to modify assumptions
    print("\n" + "="*80)
    print("SCENARIO ANALYSIS")
    print("="*80)
    
    print("\nTo modify assumptions, update the configuration:")
    print(">>> from config import update_config")
    print(">>> update_config({'systems': {'4pipe_wshp_tes': {'equipment_cost_base': 1000000}}})")
    print("\nOr save/load configurations:")
    print(">>> config.save_to_file('my_scenario.json')")
    print(">>> config.load_from_file('my_scenario.json')")
    
    # Print assumption reference
    print("\nTo see all assumptions:")
    print(">>> config.print_assumptions_table()")

def run_scenario_analysis():
    """Run multiple scenarios to validate assumptions"""
    
    print("\n" + "="*80)
    print("SCENARIO SENSITIVITY ANALYSIS")
    print("="*80)
    
    config = get_config()
    base_costs = config.calculate_project_costs()
    base_incentives = config.calculate_incentives(base_costs)
    
    scenarios = [
        {
            'name': 'Base Case',
            'changes': {},
        },
        {
            'name': 'Lower Equipment Cost (-20%)',
            'changes': {
                'systems': {
                    '4pipe_wshp_tes': {
                        'equipment_cost_base': 960000,  # $1.2M × 0.8
                    }
                }
            }
        },
        {
            'name': 'Higher Equipment Cost (+20%)',
            'changes': {
                'systems': {
                    '4pipe_wshp_tes': {
                        'equipment_cost_base': 1440000,  # $1.2M × 1.2
                    }
                }
            }
        },
        {
            'name': 'No DRCOG Grant',
            'changes': {
                'financial': {
                    'drcog_grant_per_unit': 0,
                }
            }
        },
        {
            'name': 'Lower ITC (30% only)',
            'changes': {
                'financial': {
                    'itc_rate': 0.30,
                }
            }
        },
    ]
    
    results = []
    
    for scenario in scenarios:
        # Reset to base config
        from config import reset_config
        reset_config()
        
        # Apply changes
        if scenario['changes']:
            update_config(scenario['changes'])
        
        # Recalculate
        config = get_config()
        costs = config.calculate_project_costs()
        incentives = config.calculate_incentives(costs)
        
        results.append({
            'name': scenario['name'],
            'total_cost': costs['total_project_cost'],
            'incentives': incentives['total_incentives'],
            'net_cost': incentives['net_project_cost'],
            'coverage': incentives['incentive_coverage'],
        })
    
    # Print results table
    print(f"\n{'Scenario':<30} {'Total Cost':>15} {'Incentives':>15} {'Net Cost':>15} {'Coverage':>10}")
    print("-" * 85)
    
    for r in results:
        print(f"{r['name']:<30} ${r['total_cost']:>14,.0f} ${r['incentives']:>14,.0f} ${r['net_cost']:>14,.0f} {r['coverage']:>9.0%}")
    
    # Reset to base case
    reset_config()

if __name__ == "__main__":
    # Make sure output directory exists
    os.makedirs('outputs', exist_ok=True)
    
    # Run main analysis
    run_unified_analysis()
    
    # Run scenario analysis
    run_scenario_analysis()
    
    # Print assumptions table
    print("\n" + "="*80)
    print("FULL ASSUMPTIONS TABLE")
    print("="*80)
    config = get_config()
    config.print_assumptions_table()
