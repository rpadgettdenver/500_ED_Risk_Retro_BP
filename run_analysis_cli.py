#!/usr/bin/env python3
"""
🖥️ Command Line Interface for TES+HP Analysis
Allows you to run analysis with custom parameters from the terminal.

Usage Examples:
    # Basic run with default parameters
    python3 run_analysis_cli.py
    
    # Change equipment costs
    python3 run_analysis_cli.py --equipment-cost 1500000 --tes-cost 300000
    
    # Change financial parameters
    python3 run_analysis_cli.py --market-escalation 1.50 --itc-rate 0.40
    
    # Change building parameters
    python3 run_analysis_cli.py --building-id 1234 --sqft 60000
    
    # Combine multiple parameters
    python3 run_analysis_cli.py \
        --equipment-cost 1500000 \
        --tes-cost 300000 \
        --market-escalation 1.50 \
        --itc-rate 0.40 \
        --building-id 2952
    
    # Save scenario to file
    python3 run_analysis_cli.py --equipment-cost 1500000 --save-scenario high_cost.json
    
    # Load scenario from file
    python3 run_analysis_cli.py --load-scenario high_cost.json
"""

import argparse
import sys
import os
from datetime import datetime

# Add the src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from config import get_config, update_config

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Run TES+HP Analysis with custom parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --equipment-cost 1500000 --tes-cost 300000
  %(prog)s --market-escalation 1.50 --itc-rate 0.40
  %(prog)s --building-id 1234 --sqft 60000
  %(prog)s --load-scenario my_scenario.json
        """
    )
    
    # Building parameters
    building_group = parser.add_argument_group('Building Parameters')
    building_group.add_argument('--building-id', type=str, 
                               help='Building ID to analyze (default: 2952)')
    building_group.add_argument('--building-name', type=str,
                               help='Building name')
    building_group.add_argument('--sqft', type=int,
                               help='Building square footage')
    building_group.add_argument('--units', type=int,
                               help='Number of units in building')
    
    # System parameters
    system_group = parser.add_argument_group('System Parameters')
    system_group.add_argument('--equipment-cost', type=int,
                             help='Base equipment cost in dollars (e.g., 1500000)')
    system_group.add_argument('--tes-cost', type=int,
                             help='TES system cost in dollars (e.g., 300000)')
    system_group.add_argument('--eui-reduction', type=float,
                             help='EUI reduction percentage (e.g., 0.70 for 70%%)')
    
    # Financial parameters
    financial_group = parser.add_argument_group('Financial Parameters')
    financial_group.add_argument('--market-escalation', type=float,
                                help='Market escalation factor (e.g., 1.50 for 150%%)')
    financial_group.add_argument('--itc-rate', type=float,
                                help='ITC rate as decimal (e.g., 0.40 for 40%%)')
    financial_group.add_argument('--developer-equity', type=int,
                                help='Developer equity in dollars')
    financial_group.add_argument('--bridge-loan-rate', type=float,
                                help='Bridge loan rate as decimal (e.g., 0.12 for 12%%)')
    financial_group.add_argument('--xcel-rebate', type=int,
                                help='Xcel rebate per unit in dollars')
    financial_group.add_argument('--drcog-grant', type=int,
                                help='DRCOG grant per unit in dollars')
    
    # Scenario management
    scenario_group = parser.add_argument_group('Scenario Management')
    scenario_group.add_argument('--save-scenario', type=str,
                               help='Save current parameters to JSON file')
    scenario_group.add_argument('--load-scenario', type=str,
                               help='Load parameters from JSON file')
    scenario_group.add_argument('--list-scenarios', action='store_true',
                               help='List available scenario files')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--output-prefix', type=str,
                             help='Prefix for output files')
    output_group.add_argument('--quiet', action='store_true',
                             help='Suppress detailed output')
    output_group.add_argument('--show-config', action='store_true',
                             help='Show current configuration and exit')
    output_group.add_argument('--export-config', type=str,
                             help='Export current configuration to file (JSON format)')
    output_group.add_argument('--export-readable', type=str,
                             help='Export current configuration to readable text file')
    
    return parser

def apply_cli_parameters(args):
    """Apply command line parameters to configuration"""
    updates = {}
    
    # Building parameters
    if args.building_id:
        updates.setdefault('building', {})['building_id'] = args.building_id
    if args.building_name:
        updates.setdefault('building', {})['building_name'] = args.building_name
    if args.sqft:
        updates.setdefault('building', {})['sqft'] = args.sqft
    if args.units:
        updates.setdefault('building', {})['units'] = args.units
    
    # System parameters
    if args.equipment_cost:
        updates.setdefault('systems', {}).setdefault('4pipe_wshp_tes', {})['equipment_cost_base'] = args.equipment_cost
    if args.tes_cost:
        updates.setdefault('systems', {}).setdefault('4pipe_wshp_tes', {})['tes_cost'] = args.tes_cost
    if args.eui_reduction:
        updates.setdefault('systems', {}).setdefault('4pipe_wshp_tes', {})['eui_reduction_pct'] = args.eui_reduction
    
    # Financial parameters
    if args.market_escalation:
        updates.setdefault('financial', {})['market_escalation'] = args.market_escalation
    if args.itc_rate:
        updates.setdefault('financial', {})['itc_rate'] = args.itc_rate
    if args.developer_equity:
        updates.setdefault('financial', {})['developer_equity'] = args.developer_equity
    if args.bridge_loan_rate:
        updates.setdefault('financial', {})['bridge_loan_rate'] = args.bridge_loan_rate
    if args.xcel_rebate:
        updates.setdefault('financial', {})['xcel_rebate_per_unit'] = args.xcel_rebate
    if args.drcog_grant:
        updates.setdefault('financial', {})['drcog_grant_per_unit'] = args.drcog_grant
    
    # Apply updates if any
    if updates:
        update_config(updates)
        print("📝 Applied CLI parameters:")
        for section, params in updates.items():
            print(f"  {section}:")
            if isinstance(params, dict):
                for key, value in params.items():
                    if isinstance(value, dict):
                        print(f"    {key}:")
                        for subkey, subvalue in value.items():
                            print(f"      {subkey}: {subvalue}")
                    else:
                        print(f"    {key}: {value}")
            else:
                print(f"    {params}")
        print()

def save_scenario(filename, config):
    """Save current configuration to JSON file"""
    import json
    
    # Create a clean config dict for saving
    scenario_data = {
        'scenario_name': f"CLI Scenario - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        'created_at': datetime.now().isoformat(),
        'config': config.config
    }
    
    with open(filename, 'w') as f:
        json.dump(scenario_data, f, indent=2, default=str)
    
    print(f"💾 Scenario saved to: {filename}")

def load_scenario(filename):
    """Load configuration from JSON file"""
    import json
    
    try:
        with open(filename, 'r') as f:
            scenario_data = json.load(f)
        
        if 'config' in scenario_data:
            update_config(scenario_data['config'])
            print(f"📂 Loaded scenario from: {filename}")
            if 'scenario_name' in scenario_data:
                print(f"   Name: {scenario_data['scenario_name']}")
        else:
            # Assume it's a direct config file
            update_config(scenario_data)
            print(f"📂 Loaded configuration from: {filename}")
            
    except FileNotFoundError:
        print(f"❌ Scenario file not found: {filename}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in scenario file: {e}")
        sys.exit(1)

def list_scenarios():
    """List available scenario files"""
    import glob
    
    json_files = glob.glob("*.json")
    if json_files:
        print("📋 Available scenario files:")
        for file in sorted(json_files):
            print(f"  - {file}")
    else:
        print("📋 No scenario files found in current directory")

def export_config_json(filename, config):
    """Export current configuration to JSON file"""
    import json
    
    export_data = {
        'export_info': {
            'exported_at': datetime.now().isoformat(),
            'export_type': 'hardcoded_defaults',
            'description': 'Current hardcoded configuration defaults'
        },
        'config': config.config
    }
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print(f"📄 Configuration exported to JSON: {filename}")

def export_config_readable(filename, config):
    """Export current configuration to readable text file"""
    import io
    from contextlib import redirect_stdout
    
    with open(filename, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("CURRENT HARDCODED CONFIGURATION DEFAULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Exported at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: project_config.py DEFAULT_CONFIG\n")
        f.write("=" * 80 + "\n\n")
        
        # Capture the assumptions table output
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            config.print_assumptions_table()
        
        f.write(output_buffer.getvalue())
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF CONFIGURATION EXPORT\n")
        f.write("=" * 80 + "\n")
    
    print(f"📄 Configuration exported to readable file: {filename}")

def main():
    """Main CLI function"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.list_scenarios:
        list_scenarios()
        return
    
    # Get configuration
    config = get_config()
    
    # Load scenario if specified
    if args.load_scenario:
        load_scenario(args.load_scenario)
    
    # Apply CLI parameters
    apply_cli_parameters(args)
    
    # Show configuration if requested
    if args.show_config:
        print("🔧 Current Configuration:")
        config.print_assumptions_table()
        return
    
    # Save scenario if requested
    if args.save_scenario:
        save_scenario(args.save_scenario, config)
    
    # Export configuration if requested
    if args.export_config:
        export_config_json(args.export_config, config)
    if args.export_readable:
        export_config_readable(args.export_readable, config)
    
    # Exit if only showing config or exporting
    if args.show_config or args.export_config or args.export_readable:
        return
    
    # Run the analysis
    print("🚀 Starting TES+HP Analysis with CLI parameters...")
    print("=" * 80)
    
    # Import and run the unified analysis
    from run_unified_analysis_v2 import run_unified_analysis
    
    try:
        run_unified_analysis()
        print("\n✅ Analysis completed successfully!")
        
        # Show output location
        print(f"\n📁 Outputs saved to:")
        print(f"   Reports: outputs/reports/")
        print(f"   Data: outputs/data/")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
