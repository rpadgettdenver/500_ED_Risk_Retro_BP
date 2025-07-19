"""
Test and demonstrate the unified configuration system
Shows all assumptions and where they're used
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import get_config, update_config

def main():
    # Get the configuration instance
    config = get_config()
    
    # Print all assumptions in a table
    config.print_assumptions_table()
    
    # Show calculated project costs
    print("\n" + "="*80)
    print("CALCULATED PROJECT COSTS")
    print("="*80)
    
    costs = config.calculate_project_costs()
    for key, value in costs.items():
        print(f"{key.replace('_', ' ').title():<30} ${value:>15,.2f}")
    
    # Show calculated incentives
    print("\n" + "="*80)
    print("CALCULATED INCENTIVES")
    print("="*80)
    
    incentives = config.calculate_incentives(costs)
    for key, value in incentives.items():
        if 'coverage' in key or 'pct' in key:
            print(f"{key.replace('_', ' ').title():<30} {value:>15.1%}")
        else:
            print(f"{key.replace('_', ' ').title():<30} ${value:>15,.2f}")
    
    # Show how to modify assumptions
    print("\n" + "="*80)
    print("MODIFYING ASSUMPTIONS EXAMPLE")
    print("="*80)
    
    print("\nOriginal equipment cost: ${:,.0f}".format(
        config.config['systems']['4pipe_wshp_tes']['equipment_cost_base']
    ))
    
    # Update the equipment cost
    update_config({
        'systems': {
            '4pipe_wshp_tes': {
                'equipment_cost_base': 1000000  # Reduce to $1M
            }
        }
    })
    
    print("Updated equipment cost: ${:,.0f}".format(
        config.config['systems']['4pipe_wshp_tes']['equipment_cost_base']
    ))
    
    # Recalculate with new assumption
    new_costs = config.calculate_project_costs()
    print(f"\nNew total project cost: ${new_costs['total_project_cost']:,.0f}")
    print(f"Original was: ${costs['total_project_cost']:,.0f}")
    print(f"Difference: ${costs['total_project_cost'] - new_costs['total_project_cost']:,.0f}")
    
    # Save configuration to file
    print("\n" + "="*80)
    print("SAVING/LOADING CONFIGURATION")
    print("="*80)
    
    # Create config directory if it doesn't exist
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, 'building_2952_config.json')
    config.save_to_file(config_file)
    
    # Show where assumptions are used in code
    print("\n" + "="*80)
    print("WHERE ASSUMPTIONS ARE USED IN CODE")
    print("="*80)
    
    usage_map = {
        'building.units': [
            'Cash flow model: monthly service revenue calculation',
            'Incentives: DRCOG grant calculation ($5k × units)',
            'Incentives: Xcel rebate calculation ($3.5k × units)',
            'Metrics: cost per unit calculations'
        ],
        'financial.market_escalation': [
            'Project costs: escalating equipment from base cost',
            'Project costs: escalating soft costs',
            'All modules: converting 2024 costs to 2025'
        ],
        'financial.itc_rate': [
            'Incentives: calculating federal tax credit',
            'Bridge loan: determining take-out sources',
            'Developer returns: tax credit broker spread'
        ],
        'financial.bridge_loan_rate': [
            'Cash flow model: monthly interest calculations',
            'Bridge loan: total interest cost',
            'Developer returns: cost of capital'
        ],
        'systems.4pipe_wshp_tes.equipment_cost_base': [
            'Project costs: base for all calculations',
            'Cash flow: construction draw schedule',
            'Incentives: ITC and depreciation basis'
        ]
    }
    
    for assumption, uses in usage_map.items():
        print(f"\n{assumption}:")
        for use in uses:
            print(f"  • {use}")

if __name__ == "__main__":
    main()
