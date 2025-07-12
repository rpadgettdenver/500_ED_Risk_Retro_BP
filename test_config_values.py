"""
Test script to verify configuration values
"""

import sys
import os

# Add the src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Import configuration
from config import get_config

# Get configuration
config = get_config()

print("="*60)
print("CONFIGURATION VALUE CHECK")
print("="*60)

# Direct access to values
print(f"\nDirect access to config values:")
print(f"ITC Rate: {config.config['financial']['itc_rate']} (decimal)")
print(f"ITC Rate: {config.config['financial']['itc_rate']:.0%} (percentage)")
print(f"DRCOG Grant: ${config.config['financial']['drcog_grant_per_unit']:,} per unit")

# Check if it's loading from file
print(f"\nConfiguration source check:")
print(f"Building name: {config.config['building']['building_name']}")
print(f"Equipment cost base: ${config.config['systems']['4pipe_wshp_tes']['equipment_cost_base']:,}")

# Now let's see what print_assumptions_table shows
print("\n" + "="*60)
print("OUTPUT FROM print_assumptions_table():")
print("="*60)
config.print_assumptions_table()
