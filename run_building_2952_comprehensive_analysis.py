# Suggested File Name: run_building_2952_comprehensive_analysis.py
# File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
# Use: Execute comprehensive analysis of Building 2952 for 2-pipe to 4-pipe WSHP+TES conversion

"""
How to Run Comprehensive Analysis for Building 2952
This script demonstrates how to use your existing analysis tools
to compare the current 2-pipe changeover system to the proposed
4-pipe WSHP + TES system.
"""

import sys
import os
sys.path.append('/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src')

def run_comprehensive_2952_analysis():
    """Execute all available analysis tools for Building 2952"""
    
    print("🏢 BUILDING 2952 COMPREHENSIVE ANALYSIS")
    print("=" * 60)
    print("Comparing: 2-Pipe Changeover → 4-Pipe WSHP + TES")
    print("=" * 60)
    
    # 1. BUILDING COMPLIANCE ANALYSIS
    print("\n📊 1. COMPLIANCE & PENALTY ANALYSIS")
    print("-" * 40)
    
    try:
        from analysis.building_compliance_analyzer_v2 import EnhancedBuildingComplianceAnalyzer
        
        compliance_analyzer = EnhancedBuildingComplianceAnalyzer('2952')
        compliance_analysis, compliance_fig = compliance_analyzer.generate_enhanced_report()
        
        if compliance_analysis:
            print(f"✅ Current EUI: {compliance_analysis['current_eui']:.1f} kBtu/ft²")
            print(f"✅ Standard Path Penalties (NPV): ${compliance_analysis['standard_path']['total_npv']:,.0f}")
            print(f"✅ Opt-in Path Penalties (NPV): ${compliance_analysis['optin_path']['total_npv']:,.0f}")
            print(f"✅ Recommendation: {compliance_analysis['recommendation']['recommendation'].upper()}")
            print(f"✅ Retrofit Level: {compliance_analysis['retrofit_analysis']['retrofit_level']}")
            
    except ImportError as e:
        print(f"❌ Could not run compliance analysis: {e}")
    
    # 2. HVAC SYSTEM IMPACT MODELING
    print("\n🔧 2. HVAC SYSTEM IMPACT ANALYSIS")
    print("-" * 40)
    
    try:
        from models.hvac_system_impact_modeler import HVACSystemImpactModeler
        
        hvac_modeler = HVACSystemImpactModeler('2952')
        hvac_report = hvac_modeler.generate_scenario_report()
        
        print(f"✅ Building: {hvac_report['building_name']}")
        print(f"✅ Current EUI: {hvac_report['current_eui']:.1f} kBtu/ft²")
        
        # Show system comparisons
        for scenario in hvac_report['scenarios']:
            system_name = scenario['system_name']
            new_eui = scenario['new_eui']
            reduction_pct = scenario['eui_reduction_pct']
            cost = scenario['total_estimated_cost']
            compliant_2030 = scenario['2030_compliant']
            
            print(f"\n   {system_name}:")
            print(f"     EUI: {new_eui} (-{reduction_pct}%)")
            print(f"     Cost: ${cost:,.0f}")
            print(f"     2030 Compliant: {'Yes' if compliant_2030 else 'No'}")
            
    except ImportError as e:
        print(f"❌ Could not run HVAC analysis: {e}")
    
    # 3. INTEGRATED TEAAS BUSINESS CASE
    print("\n💰 3. INTEGRATED TEaaS BUSINESS ANALYSIS")
    print("-" * 40)
    
    try:
        from analysis.integrated_tes_hp_analyzer import IntegratedTESHPAnalyzer
        
        teaas_analyzer = IntegratedTESHPAnalyzer()
        teaas_summary = teaas_analyzer.generate_executive_summary()
        
        # Building info
        building = teaas_summary['building']
        print(f"✅ Building: {building['name']} ({building['units']} units)")
        print(f"✅ Size: {building['sqft']:,} sq ft")
        print(f"✅ EPB Status: {'Yes' if building['is_epb'] else 'No'}")
        
        # Solution
        solution = teaas_summary['recommended_solution']
        print(f"\n   RECOMMENDED: {solution['system']}")
        print(f"   New EUI: {solution['new_eui']} (-{solution['eui_reduction']:.0f}%)")
        print(f"   Penalties Avoided: ${solution['penalties_avoided_15yr']:,.0f}")
        print(f"   2030 Compliant: {'Yes' if solution['compliant_through_2030'] else 'No'}")
        
        # Economics
        economics = teaas_summary['project_economics']
        print(f"\n   PROJECT ECONOMICS:")
        print(f"   Total Cost: ${economics['total_cost']:,.0f}")
        print(f"   Incentives: ${economics['total_incentives']:,.0f} ({economics['incentive_coverage']:.0%})")
        print(f"   Net Cost: ${economics['net_cost']:,.0f}")
        print(f"   Monthly Service: ${economics['monthly_service_fee']:,.0f}")
        print(f"   Annual NOI: ${economics['annual_noi']:,.0f}")
        
        # Developer Returns
        returns = teaas_summary['developer_returns']
        print(f"\n   DEVELOPER RETURNS:")
        print(f"   Upfront Profit: ${returns['total_profit']:,.0f}")
        print(f"   Return on Equity: {returns['return_on_equity']:.0%}")
        print(f"   5-Year Total: ${returns['5yr_total']:,.0f}")
        
        # Exit Valuation
        exit_val = teaas_summary['exit_valuation']
        print(f"\n   EXIT VALUATION:")
        print(f"   Market Value: ${exit_val['market_value']:,.0f}")
        print(f"   Value per Unit: ${exit_val['value_per_unit']:,.0f}")
        print(f"   DCF Value: ${exit_val['dcf_value']:,.0f}")
        
        # Generate charts
        teaas_fig = teaas_analyzer.create_presentation_charts()
        
        # Save outputs
        output_dir = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/building_2952_analysis'
        os.makedirs(output_dir, exist_ok=True)
        
        # Save charts
        if 'teaas_fig' in locals():
            teaas_fig.savefig(f'{output_dir}/teaas_business_case_charts.png', dpi=300, bbox_inches='tight')
            print(f"\n💾 TEaaS charts saved to: {output_dir}/teaas_business_case_charts.png")
        
        if 'compliance_fig' in locals():
            compliance_fig.savefig(f'{output_dir}/compliance_analysis_charts.png', dpi=300, bbox_inches='tight')
            print(f"💾 Compliance charts saved to: {output_dir}/compliance_analysis_charts.png")
        
        # Generate full report
        report_path = f'{output_dir}/comprehensive_analysis_report.json'
        teaas_analyzer.generate_full_report(report_path)
        print(f"💾 Full report saved to: {report_path}")
        
    except ImportError as e:
        print(f"❌ Could not run TEaaS analysis: {e}")
    
    # 4. SUMMARY AND RECOMMENDATIONS
    print("\n🎯 4. EXECUTIVE SUMMARY & RECOMMENDATIONS")
    print("-" * 40)
    
    if 'teaas_summary' in locals():
        print("\n✅ BUSINESS CASE SUMMARY:")
        print(f"   • Convert 2-pipe changeover to 4-pipe WSHP + TES")
        print(f"   • ${teaas_summary['project_economics']['total_cost']:,.0f} total project cost")
        print(f"   • {teaas_summary['project_economics']['incentive_coverage']:.0%} incentive coverage")
        print(f"   • ${teaas_summary['recommended_solution']['penalties_avoided_15yr']:,.0f} penalty avoidance")
        print(f"   • {teaas_summary['recommended_solution']['eui_reduction']:.0f}% energy reduction")
        print(f"   • ${teaas_summary['developer_returns']['return_on_equity']:.0%} developer return on equity")
        
        print("\n✅ KEY BENEFITS FOR OWNER:")
        for benefit in teaas_summary['key_benefits']['owner']:
            print(f"   • {benefit}")
        
        print("\n✅ NEXT STEPS:")
        for i, step in enumerate(teaas_summary['next_steps'], 1):
            print(f"   {i}. {step}")
    
    print("\n🚀 ANALYSIS COMPLETE!")
    print("="*60)
    print("All charts and reports saved to outputs/building_2952_analysis/")
    
    return True


def run_current_vs_proposed_comparison():
    """
    Run specific comparison between current and proposed systems
    """
    
    print("\n🔄 CURRENT vs PROPOSED SYSTEM COMPARISON")
    print("="*50)
    
    # Current System Specs (from your description)
    current_system = {
        'name': 'Current 2-Pipe Changeover',
        'chiller': 'Multistack MS30C5A1W (31.4 ton)',
        'boiler': 'Ajax WG2500 (2,000 MBH)',
        'dhw_boiler': 'LAARS PW0850IN09K1ACJX (688.5 MBH)',
        'pool_boiler': 'Raypak B-R206A-EN-C',
        'distribution': '2-pipe changeover',
        'control': 'Central plant switching',
        'annual_cost': 50000,  # Your estimate
        'comfort_issues': [
            'No simultaneous heating/cooling',
            'Poor shoulder season performance', 
            'Limited zone control',
            'Delayed response to load changes'
        ]
    }
    
    # Proposed System from Analysis
    proposed_system = {
        'name': '4-Pipe WSHP + TES',
        'heat_pump': '35-ton water-to-water chiller-heaters',
        'tes': '150 ton-hour ice storage',
        'distribution': '4-pipe vertical with 6-way valve controllers',
        'control': 'Individual zone control (52 controllers)',
        'annual_service_fee': 93600,  # $150/unit × 52 units × 12 months
        'benefits': [
            'Simultaneous heating and cooling',
            'Individual unit temperature control',
            'Peak demand reduction via TES',
            'Grid flexibility and demand response',
            'Full electrification (no gas)',
            'Predictive maintenance capabilities'
        ]
    }
    
    print(f"\n📊 SYSTEM COMPARISON:")
    print(f"\nCURRENT: {current_system['name']}")
    print(f"  Chiller: {current_system['chiller']}")
    print(f"  Boiler: {current_system['boiler']}")
    print(f"  DHW: {current_system['dhw_boiler']}")
    print(f"  Distribution: {current_system['distribution']}")
    print(f"  Annual Cost: ${current_system['annual_cost']:,}")
    
    print(f"\nPROPOSED: {proposed_system['name']}")
    print(f"  Heat Pump: {proposed_system['heat_pump']}")
    print(f"  TES: {proposed_system['tes']}")
    print(f"  Distribution: {proposed_system['distribution']}")
    print(f"  Service Fee: ${proposed_system['annual_service_fee']:,}")
    
    print(f"\n🎯 KEY UPGRADE BENEFITS:")
    for benefit in proposed_system['benefits']:
        print(f"  ✓ {benefit}")
    
    print(f"\n⚠️  CURRENT SYSTEM LIMITATIONS:")
    for issue in current_system['comfort_issues']:
        print(f"  ✗ {issue}")


if __name__ == "__main__":
    # Run comprehensive analysis
    success = run_comprehensive_2952_analysis()
    
    if success:
        # Run detailed system comparison
        run_current_vs_proposed_comparison()
    
    print("\n" + "="*60)
    print("ANALYSIS READY FOR YOUR MEETING! 🚀")
    print("="*60)