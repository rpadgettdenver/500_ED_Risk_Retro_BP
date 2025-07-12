"""
Suggested File Name: project_config.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/config/
Use: Centralized configuration for all TES+HP analysis modules to ensure consistency

This module provides a single source of truth for project parameters
"""

import json
import pandas as pd
from typing import Dict, Any
from datetime import datetime

class ProjectConfig:
    """Unified configuration for TES+HP project analysis"""
    
    # Default configuration values with documentation
    DEFAULT_CONFIG = {
        'building': {
            'building_id': '2952',
            'building_name': 'Timperly Condominium',
            'address': '1255 N Ogden St, Denver, CO 80218',
            'property_type': 'Multifamily Housing',
            'units': 52,
            'sqft': 52826,
            'is_epb': True,
            
            # Energy profile
            'weather_norm_eui': 65.3,
            'electricity_kwh': 210165,
            'gas_kbtu': 2584000,
            'total_ghg': 126.67,
            'current_energy_cost_annual': 42000,
            
            # Compliance targets
            'baseline_year': 2019,
            'baseline_eui': 70.5,
            'first_interim_target': 65.4,  # 2025
            'second_interim_target': 63.2,  # 2027
            'final_target': 51.5,  # 2030
            
            # Current needs
            'equipment_replacement_cost': 270000,
        },
        
        'systems': {
            '4pipe_wshp_tes': {
                'name': '4-Pipe WSHP + TES',
                'equipment_cost_base': 1200000,  # Base equipment cost
                'tes_cost': 200000,  # Additional TES cost
                'cost_per_sqft': None,  # Will be calculated
                'cop_heating': 4.5,
                'cop_cooling': 5.0,
                'electric_heating': True,
                'eui_reduction_pct': 0.70,  # 70% reduction
            }
        },
        
        'financial': {
            # Cost escalation
            'market_escalation': 1.30,  # 30% escalation
            'soft_cost_pct': 0.25,  # % of hard costs
            'developer_fee_pct': 0.15,  # % of hard costs
            'contingency_pct': 0.10,  # % of subtotal
            
            # Federal incentives
            'itc_rate': 0.40,  # 30% base + 10% energy community
            'depreciation_rate': 0.80,  # Bonus depreciation
            'depreciation_tax_rate': 0.35,  # Corporate tax rate
            'depreciation_sale_discount': 0.85,  # Sell at 85% of value
            'tax_credit_sale_rate': 0.95,  # Sell at 95 cents on dollar
            
            # Local incentives
            'drcog_grant_per_unit': 5000,  # EPB buildings only
            'xcel_rebate_per_unit': 3500,  # Clean Heat Plan
            'rebate_origination_fee': 0.025,  # Broker fee
            
            # Financing
            'bridge_loan_rate': 0.12,  # Annual rate
            'bridge_loan_fee': 0.02,  # Origination fee
            'bridge_loan_term_months': 12,
            'developer_equity': 200000,  # Pre-dev costs
            
            # Operations
            'monthly_service_fee_per_unit': 150,
            'annual_escalation': 0.025,  # 2.5%
            'operating_margin': 0.30,  # NOI margin
            'asset_mgmt_fee_pct': 0.02,  # % of revenue
        },
        
        'timeline': {
            'pre_construction_months': 6,
            'construction_months': 9,
            'stabilization_months': 3,
        },
        
        'valuation': {
            'cap_rates': {
                'conservative': 0.10,
                'market': 0.08,
                'aggressive': 0.06,
            },
            'growth_rate': 0.025,
            'discount_rate': 0.08,
            'terminal_year': 10,
        },
        
        'penalties': {
            '2025_rate': 0.30,  # $/sqft/kBtu over
            '2027_rate': 0.50,
            '2030_rate': 0.70,
            'penalty_years': 15,  # Analysis period
        }
    }
    
    def __init__(self, config_override: Dict = None):
        """Initialize with optional config override"""
        self.config = self.DEFAULT_CONFIG.copy()
        if config_override:
            self._deep_update(self.config, config_override)
        
        # Calculate derived values
        self._calculate_derived_values()
    
    def _deep_update(self, base: Dict, update: Dict):
        """Recursively update nested dictionary"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base:
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def _calculate_derived_values(self):
        """Calculate values that depend on other config values"""
        # Calculate cost per sqft for system
        system = self.config['systems']['4pipe_wshp_tes']
        total_equipment = system['equipment_cost_base'] + system['tes_cost']
        system['cost_per_sqft'] = total_equipment / self.config['building']['sqft']
        
        # Calculate annual values
        financial = self.config['financial']
        financial['annual_service_revenue'] = (
            financial['monthly_service_fee_per_unit'] * 
            self.config['building']['units'] * 12
        )
        financial['annual_noi'] = (
            financial['annual_service_revenue'] * 
            financial['operating_margin']
        )
    
    def calculate_project_costs(self) -> Dict[str, float]:
        """Calculate total project costs"""
        system = self.config['systems']['4pipe_wshp_tes']
        financial = self.config['financial']
        
        # Base equipment
        base_equipment = system['equipment_cost_base'] + system['tes_cost']
        
        # Apply escalation
        escalated_equipment = base_equipment * financial['market_escalation']
        
        # Soft costs
        soft_costs = escalated_equipment * financial['soft_cost_pct']
        
        # Developer fee
        developer_fee = escalated_equipment * financial['developer_fee_pct']
        
        # Subtotal
        subtotal = escalated_equipment + soft_costs + developer_fee
        
        # Contingency
        contingency = subtotal * financial['contingency_pct']
        
        # Total
        total_cost = subtotal + contingency
        
        return {
            'base_equipment': base_equipment,
            'escalated_equipment': escalated_equipment,
            'soft_costs': soft_costs,
            'developer_fee': developer_fee,
            'contingency': contingency,
            'subtotal': subtotal,
            'total_project_cost': total_cost,
            'cost_per_unit': total_cost / self.config['building']['units'],
            'cost_per_sqft': total_cost / self.config['building']['sqft'],
        }
    
    def calculate_incentives(self, project_costs: Dict) -> Dict[str, float]:
        """Calculate all incentives"""
        financial = self.config['financial']
        building = self.config['building']
        
        # Federal tax credit
        itc_basis = project_costs['escalated_equipment']
        itc_amount = itc_basis * financial['itc_rate']
        itc_proceeds = itc_amount * financial['tax_credit_sale_rate']
        
        # Depreciation
        depreciation_amount = itc_basis * financial['depreciation_rate']
        tax_value = depreciation_amount * financial['depreciation_tax_rate']
        depreciation_proceeds = tax_value * financial['depreciation_sale_discount']
        
        # Grants
        drcog = building['units'] * financial['drcog_grant_per_unit'] if building['is_epb'] else 0
        xcel = building['units'] * financial['xcel_rebate_per_unit']
        
        # Broker fees
        rebate_origination = (drcog + xcel) * financial['rebate_origination_fee']
        tc_broker_spread = itc_amount * 0.05  # 5% spread
        
        total = itc_proceeds + depreciation_proceeds + drcog + xcel
        
        return {
            'itc_amount': itc_amount,
            'itc_proceeds': itc_proceeds,
            'depreciation_amount': depreciation_amount,
            'depreciation_tax_value': tax_value,
            'depreciation_proceeds': depreciation_proceeds,
            'drcog_grant': drcog,
            'xcel_rebate': xcel,
            'rebate_origination_fee': rebate_origination,
            'tc_broker_spread': tc_broker_spread,
            'total_incentives': total,
            'net_project_cost': project_costs['total_project_cost'] - total,
            'incentive_coverage': total / project_costs['total_project_cost'],
        }
    
    def print_assumptions_table(self):
        """Print a comprehensive table of all assumptions"""
        print("\n" + "="*80)
        print("PROJECT ASSUMPTIONS REFERENCE TABLE")
        print("="*80)
        
        # Flatten the config for display
        def flatten_dict(d, parent_key='', sep='.'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        flat_config = flatten_dict(self.config)
        
        # Group by category
        categories = {}
        for key, value in flat_config.items():
            category = key.split('.')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append((key, value))
        
        # Print each category
        for category, items in categories.items():
            print(f"\n{category.upper()} ASSUMPTIONS:")
            print("-" * 80)
            print(f"{'Variable Path':<45} {'Value':>20} {'Type':>12}")
            print("-" * 80)
            
            for key, value in sorted(items):
                if isinstance(value, float):
                    # Special handling for penalty rates (they're $/sqft/kBtu, not percentages)
                    if 'penalties' in key and 'rate' in key:
                        value_str = f"${value:.2f}/sqft/kBtu"
                    elif value < 1 and value > 0:
                        value_str = f"{value:.1%}"
                    else:
                        value_str = f"{value:,.2f}"
                elif isinstance(value, int):
                    value_str = f"{value:,}"
                elif isinstance(value, bool):
                    value_str = str(value)
                else:
                    value_str = str(value)[:20]
                
                type_str = type(value).__name__
                print(f"{key:<45} {value_str:>20} {type_str:>12}")
    
    def save_to_file(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"Configuration saved to: {filepath}")
    
    def load_from_file(self, filepath: str):
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            self.config = json.load(f)
        self._calculate_derived_values()
        print(f"Configuration loaded from: {filepath}")
    
    def get_config_for_modules(self) -> Dict[str, Any]:
        """Get configuration formatted for existing modules"""
        building = self.config['building']
        system = self.config['systems']['4pipe_wshp_tes']
        financial = self.config['financial']
        timeline = self.config['timeline']
        
        # Format for cash flow bridge module
        cash_flow_config = {
            'building_name': building['building_name'],
            'building_id': building['building_id'],
            'units': building['units'],
            'sqft': building['sqft'],
            'is_epb': building['is_epb'],
            
            'equipment_cost': system['equipment_cost_base'],
            'tes_cost': system['tes_cost'],
            'soft_costs': system['equipment_cost_base'] * 0.25,  # Approximate
            
            'developer_fee_pct': financial['developer_fee_pct'],
            'contingency_pct': financial['contingency_pct'],
            'market_escalation': financial['market_escalation'],
            
            'itc_rate': financial['itc_rate'],
            'depreciation_rate': financial['depreciation_rate'],
            'depreciation_value_pct': financial['depreciation_sale_discount'],
            'drcog_grant_per_unit': financial['drcog_grant_per_unit'],
            'xcel_rebate_per_unit': financial['xcel_rebate_per_unit'],
            'tax_credit_sale_rate': financial['tax_credit_sale_rate'],
            
            'bridge_loan_rate': financial['bridge_loan_rate'],
            'bridge_loan_fee': financial['bridge_loan_fee'],
            
            'monthly_service_fee_per_unit': financial['monthly_service_fee_per_unit'],
            'annual_escalation': financial['annual_escalation'],
            'operating_margin': financial['operating_margin'],
            
            'pre_construction_months': timeline['pre_construction_months'],
            'construction_months': timeline['construction_months'],
        }
        
        # Format for bridge loan package
        bridge_loan_config = {
            'project_name': f"{building['building_name']} TES+HP Retrofit",
            'building_address': building['address'],
            'building_type': f"{building['property_type']} ({building['units']} units)",
            'developer': 'Denver Thermal Energy Solutions LLC',
            
            'total_project_cost': self.calculate_project_costs()['total_project_cost'],
            'equipment_cost': system['equipment_cost_base'] + system['tes_cost'],
            'soft_costs': self.calculate_project_costs()['soft_costs'],
            
            'itc_amount': 0,  # Will be calculated
            'bridge_request': 0,  # Will be calculated
            
            # Copy other fields...
        }
        
        return {
            'cash_flow': cash_flow_config,
            'bridge_loan': bridge_loan_config,
            'building': building,
            'financial': financial,
        }


# Create global instance
PROJECT_CONFIG = ProjectConfig()

# Helper functions for easy access
def get_config():
    """Get the global configuration"""
    return PROJECT_CONFIG

def update_config(updates: Dict):
    """Update configuration values"""
    PROJECT_CONFIG._deep_update(PROJECT_CONFIG.config, updates)
    PROJECT_CONFIG._calculate_derived_values()

def reset_config():
    """Reset to default configuration"""
    PROJECT_CONFIG.config = ProjectConfig.DEFAULT_CONFIG.copy()
    PROJECT_CONFIG._calculate_derived_values()
