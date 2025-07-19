"""
Suggested File Name: integrated_tes_hp_analyzer.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis/
Use: Comprehensive analysis tool that integrates HVAC system modeling, cash flow analysis, and business case generation

This tool combines:
1. HVAC system impact modeling (EUI reduction scenarios)
2. Cash flow bridge analysis (month-by-month funding)
3. Bridge loan structuring
4. Developer returns analysis
5. Executive summary generation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import centralized modules
from utils.penalty_calculator import EnergizeDenverPenaltyCalculator

# Import unified configuration
try:
    from config import get_config
    USE_UNIFIED_CONFIG = True
except ImportError:
    USE_UNIFIED_CONFIG = False
    print("Warning: Could not import unified config, using legacy values")

class NumpyEncoder(json.JSONEncoder):
    """Custom encoder to handle NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                          np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        if isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class IntegratedTESHPAnalyzer:
    """Complete TES+HP business analysis for Energize Denver buildings"""
    
    def __init__(self, building_data: Dict = None):
        """
        Initialize with building data
        
        Args:
            building_data: Dict with building information
        """
        # Initialize penalty calculator
        self.penalty_calc = EnergizeDenverPenaltyCalculator()
        # Use unified config if available
        if USE_UNIFIED_CONFIG and building_data is None:
            config = get_config()
            self.building_data = config.config['building'].copy()
            
            # Update system configs from unified config
            system = config.config['systems']['4pipe_wshp_tes']
            self.system_configs = [
                {
                    'name': 'Current System',
                    'type': 'gas_boiler',
                    'cop_heating': 0.85,
                    'cop_cooling': 3.0,
                    'electric_heating': False,
                    'cost_per_sqft': 0,
                },
                {
                    'name': '4-Pipe WSHP',
                    'type': '4pipe_wshp',
                    'cop_heating': 4.0,
                    'cop_cooling': 4.5,
                    'electric_heating': True,
                    'cost_per_sqft': system['cost_per_sqft'] * 0.8,  # 80% of full system
                },
                {
                    'name': '4-Pipe WSHP + TES',
                    'type': '4pipe_wshp_tes',
                    'cop_heating': system['cop_heating'],
                    'cop_cooling': system['cop_cooling'],
                    'electric_heating': system['electric_heating'],
                    'cost_per_sqft': system['cost_per_sqft'],
                    'tes_included': True,
                },
            ]
        else:
            # Default to Building 2952 if no data provided
            self.building_data = building_data or {
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
                'baseline_year': 2019,
                'baseline_eui': 70.5,
                'first_interim_target': 65.4,  # 2025
                'second_interim_target': 63.2,  # 2027
                'final_target': 51.5,  # 2030
                'current_energy_cost_annual': 42000,  # Estimated
                'equipment_replacement_cost': 270000,
            }
            
            # System configurations to analyze
            self.system_configs = [
                {
                    'name': 'Current System',
                    'type': 'gas_boiler',
                    'cop_heating': 0.85,
                    'cop_cooling': 3.0,
                    'electric_heating': False,
                    'cost_per_sqft': 0,
                },
                {
                    'name': '4-Pipe WSHP',
                    'type': '4pipe_wshp',
                    'cop_heating': 4.0,
                    'cop_cooling': 4.5,
                    'electric_heating': True,
                    'cost_per_sqft': 50,  # More realistic cost
                },
                {
                    'name': '4-Pipe WSHP + TES',
                    'type': '4pipe_wshp_tes',
                    'cop_heating': 4.5,
                    'cop_cooling': 5.0,
                    'electric_heating': True,
                    'cost_per_sqft': 60,  # More realistic cost with TES
                    'tes_included': True,
                },
            ]
        
    def calculate_energy_split(self) -> Tuple[float, float, float]:
        """Calculate heating, cooling, and other energy splits"""
        # For multifamily in Denver
        gas_energy = self.building_data['gas_kbtu']
        elec_energy = self.building_data['electricity_kwh'] * 3.412
        total_energy = gas_energy + elec_energy
        
        # Typical splits for multifamily
        heating_fraction = gas_energy / total_energy * 0.9  # 90% of gas is heating
        cooling_fraction = 0.15  # 15% for cooling
        other_fraction = 1 - heating_fraction - cooling_fraction
        
        return heating_fraction, cooling_fraction, other_fraction
    
    def model_system_impacts(self) -> pd.DataFrame:
        """Model EUI and cost impacts of different systems"""
        results = []
        
        heating_frac, cooling_frac, other_frac = self.calculate_energy_split()
        current_total_energy = (self.building_data['gas_kbtu'] + 
                              self.building_data['electricity_kwh'] * 3.412)
        
        for config in self.system_configs:
            # Calculate new energy use
            heating_energy = current_total_energy * heating_frac
            cooling_energy = current_total_energy * cooling_frac
            other_energy = current_total_energy * other_frac
            
            if config['electric_heating']:
                # Convert to electric heating
                new_heating = heating_energy / config['cop_heating'] * 0.9  # 10% reduction
                new_cooling = cooling_energy / config['cop_cooling'] * 0.9
                new_gas = 0
                new_elec = (new_heating + new_cooling + other_energy) / 3.412
            else:
                # Keep gas heating
                new_heating = heating_energy
                new_cooling = cooling_energy / config['cop_cooling']
                new_gas = heating_energy + other_energy * 0.7
                new_elec = (cooling_energy / config['cop_cooling'] + other_energy * 0.3) / 3.412
            
            new_total_energy = new_gas + new_elec * 3.412
            new_eui = new_total_energy / self.building_data['sqft']
            
            # Calculate costs
            install_cost = config['cost_per_sqft'] * self.building_data['sqft'] * 1.3  # 30% escalation
            
            # Electrification bonus
            electrification_bonus = 0.10 if config['electric_heating'] else 0
            effective_eui = new_eui * (1 - electrification_bonus)
            
            # Check compliance
            compliance_2025 = effective_eui <= self.building_data['first_interim_target']
            compliance_2027 = effective_eui <= self.building_data['second_interim_target']
            compliance_2030 = effective_eui <= self.building_data['final_target']
            
            # Calculate penalties using centralized calculator
            penalty_rate_standard = self.penalty_calc.get_penalty_rate('standard')
            
            penalty_2025 = self.penalty_calc.calculate_penalty(
                actual_eui=effective_eui,
                target_eui=self.building_data['first_interim_target'],
                sqft=self.building_data['sqft'],
                penalty_rate=penalty_rate_standard
            )
            
            penalty_2027 = self.penalty_calc.calculate_penalty(
                actual_eui=effective_eui,
                target_eui=self.building_data['second_interim_target'],
                sqft=self.building_data['sqft'],
                penalty_rate=penalty_rate_standard
            )
            
            penalty_2030 = self.penalty_calc.calculate_penalty(
                actual_eui=effective_eui,
                target_eui=self.building_data['final_target'],
                sqft=self.building_data['sqft'],
                penalty_rate=penalty_rate_standard
            )
            
            results.append({
                'system': config['name'],
                'new_eui': round(new_eui, 1),
                'eui_reduction': round(self.building_data['weather_norm_eui'] - new_eui, 1),
                'eui_reduction_pct': round((self.building_data['weather_norm_eui'] - new_eui) / 
                                         self.building_data['weather_norm_eui'] * 100, 1),
                'electric_heating': config['electric_heating'],
                'electrification_bonus': electrification_bonus,
                'effective_eui': round(effective_eui, 1),
                'install_cost': install_cost,
                'compliant_2025': compliance_2025,
                'compliant_2027': compliance_2027,
                'compliant_2030': compliance_2030,
                'penalty_2025': penalty_2025,
                'penalty_2027': penalty_2027,
                'penalty_2030': penalty_2030,
                'total_penalties_15yr': penalty_2025 + penalty_2027 + penalty_2030 * 13,  # 2030 penalty continues annually through 2042
            })
        
        return pd.DataFrame(results)
    
    def calculate_project_economics(self, system_type: str = '4pipe_wshp_tes') -> Dict:
        """Calculate detailed project economics for a specific system"""
        
        # Find system config
        config = next(c for c in self.system_configs if c['type'] == system_type)
        
        # Use unified config if available
        if USE_UNIFIED_CONFIG:
            unified_config = get_config()
            costs = unified_config.calculate_project_costs()
            incentives = unified_config.calculate_incentives(costs)
            financial = unified_config.config['financial']
            
            return {
                'system_type': system_type,
                'total_project_cost': costs['total_project_cost'],
                'equipment_cost': costs['escalated_equipment'],
                'soft_costs': costs['soft_costs'],
                'developer_fee': costs['developer_fee'],
                'contingency': costs['contingency'],
                'itc_amount': incentives['itc_amount'],
                'depreciation_value': incentives['depreciation_tax_value'],
                'drcog_grant': incentives['drcog_grant'],
                'xcel_rebate': incentives['xcel_rebate'],
                'total_incentives': incentives['total_incentives'],
                'net_project_cost': incentives['net_project_cost'],
                'incentive_coverage': incentives['incentive_coverage'],
                'monthly_service_fee': financial['monthly_service_fee_per_unit'] * self.building_data['units'],
                'annual_revenue': financial['annual_service_revenue'],
                'annual_noi': financial['annual_noi'],
                'project_yield': financial['annual_noi'] / costs['total_project_cost'],
                'cash_on_cash': financial['annual_noi'] / incentives['net_project_cost'] if incentives['net_project_cost'] > 0 else float('inf'),
            }
        else:
            # Legacy calculation method
            # Base costs
            base_equipment_cost = config['cost_per_sqft'] * self.building_data['sqft']
            escalated_cost = base_equipment_cost * 1.3  # 30% escalation
            
            # Break down costs
            if config.get('tes_included'):
                heat_pump_cost = escalated_cost * 0.8
                tes_cost = escalated_cost * 0.2
            else:
                heat_pump_cost = escalated_cost
                tes_cost = 0
                
            soft_costs = escalated_cost * 0.25  # 25% soft costs
            developer_fee = escalated_cost * 0.15  # 15% developer fee
            contingency = (escalated_cost + soft_costs + developer_fee) * 0.10
            
            total_project_cost = escalated_cost + soft_costs + developer_fee + contingency
            
            # Calculate incentives
            # ITC - 40% on equipment only
            itc_basis = heat_pump_cost + tes_cost
            itc_amount = itc_basis * 0.40
            
            # Depreciation - 80% bonus
            depreciation_amount = itc_basis * 0.80 * 0.35  # 35% tax rate
            
            # Grants and rebates
            drcog_grant = self.building_data['units'] * 5000 if self.building_data['is_epb'] else 0
            xcel_rebate = self.building_data['units'] * 3500
            
            total_incentives = itc_amount + depreciation_amount + drcog_grant + xcel_rebate
            
            # Net project cost
            net_cost = total_project_cost - total_incentives
            
            # Monthly service fee calculation
            # Target 95% of current energy spend
            monthly_revenue = self.building_data['current_energy_cost_annual'] * 0.95 / 12
            annual_revenue = monthly_revenue * 12
            
            # Operating expenses (30% margin)
            annual_opex = annual_revenue * 0.70
            annual_noi = annual_revenue - annual_opex
            
            return {
                'system_type': system_type,
                'total_project_cost': total_project_cost,
                'equipment_cost': heat_pump_cost + tes_cost,
                'soft_costs': soft_costs,
                'developer_fee': developer_fee,
                'contingency': contingency,
                'itc_amount': itc_amount,
                'depreciation_value': depreciation_amount,
                'drcog_grant': drcog_grant,
                'xcel_rebate': xcel_rebate,
                'total_incentives': total_incentives,
                'net_project_cost': net_cost,
                'incentive_coverage': total_incentives / total_project_cost,
                'monthly_service_fee': monthly_revenue,
                'annual_revenue': annual_revenue,
                'annual_noi': annual_noi,
                'project_yield': annual_noi / total_project_cost,
                'cash_on_cash': annual_noi / net_cost if net_cost > 0 else float('inf'),
            }
    
    def calculate_developer_returns(self, economics: Dict) -> Dict:
        """Calculate developer profit sources and returns"""
        
        # Developer income streams
        developer_fee = economics['developer_fee']
        
        # Tax credit broker spread (5% of ITC)
        tc_broker_spread = economics['itc_amount'] * 0.05
        
        # Depreciation sale (sell at 85% of value)
        depreciation_sale = economics['depreciation_value'] * 0.85 / 0.35  # Gross up
        
        # Rebate origination (2.5% of grants/rebates)
        rebate_origination = (economics['drcog_grant'] + economics['xcel_rebate']) * 0.025
        
        # Total developer profit
        total_profit = developer_fee + tc_broker_spread + depreciation_sale + rebate_origination
        
        # Developer equity needed (pre-construction costs)
        developer_equity = 200000  # Estimated pre-construction costs
        
        # Asset management fee (ongoing)
        annual_asset_mgmt = economics['annual_revenue'] * 0.02  # 2% of revenue
        
        return {
            'developer_fee': developer_fee,
            'tax_credit_spread': tc_broker_spread,
            'depreciation_sale_profit': depreciation_sale * 0.15,  # 15% profit on sale
            'rebate_origination': rebate_origination,
            'total_upfront_profit': total_profit,
            'developer_equity_needed': developer_equity,
            'return_on_equity': total_profit / developer_equity,
            'annual_asset_mgmt_fee': annual_asset_mgmt,
            '5yr_total_return': total_profit + (annual_asset_mgmt * 5),
        }
    
    def calculate_bridge_loan(self, economics: Dict) -> Dict:
        """Structure bridge loan requirements"""
        
        # Peak funding need (before incentives received)
        peak_funding = economics['total_project_cost'] * 0.85  # Assume 15% is developer fee paid over time
        
        # Bridge loan sizing
        bridge_facility = peak_funding * 1.02  # 2% origination fee
        
        # Loan terms
        months_outstanding = 12  # Through construction + 3 months
        interest_rate = 0.12  # 12% annual
        total_interest = bridge_facility * interest_rate * (months_outstanding / 12)
        
        # Take-out sources
        takeout_sources = {
            'tax_credit_sale': economics['itc_amount'] * 0.95,  # 95 cents on dollar
            'depreciation_sale': economics['depreciation_value'] * 0.85,
            'drcog_grant': economics['drcog_grant'],
            'xcel_rebate': economics['xcel_rebate'],
        }
        
        total_takeout = sum(takeout_sources.values())
        
        return {
            'peak_funding_need': peak_funding,
            'bridge_facility_size': bridge_facility,
            'origination_fee': peak_funding * 0.02,
            'interest_rate': interest_rate,
            'months_outstanding': months_outstanding,
            'total_interest': total_interest,
            'all_in_cost': bridge_facility + total_interest - peak_funding,
            'takeout_sources': takeout_sources,
            'total_takeout': total_takeout,
            'coverage_ratio': total_takeout / bridge_facility,
        }
    
    def value_stabilized_cashflows(self, economics: Dict) -> Dict:
        """Calculate exit valuation for stabilized cash flows"""
        
        annual_noi = economics['annual_noi']
        
        # Apply different cap rates
        valuations = {}
        for scenario, cap_rate in [('conservative', 0.10), ('market', 0.08), ('aggressive', 0.06)]:
            value = annual_noi / cap_rate
            valuations[scenario] = {
                'cap_rate': cap_rate,
                'value': value,
                'multiple': 1 / cap_rate,
                'price_per_unit': value / self.building_data['units'],
                'price_per_sqft': value / self.building_data['sqft'],
            }
        
        # DCF valuation with growth
        growth_rate = 0.025  # 2.5% annual
        discount_rate = 0.08
        terminal_cap = 0.08
        
        # 10-year DCF
        dcf_cashflows = []
        for year in range(1, 11):
            cf = annual_noi * ((1 + growth_rate) ** year)
            pv = cf / ((1 + discount_rate) ** year)
            dcf_cashflows.append(pv)
        
        # Terminal value
        terminal_noi = annual_noi * ((1 + growth_rate) ** 10)
        terminal_value = terminal_noi / terminal_cap
        terminal_pv = terminal_value / ((1 + discount_rate) ** 10)
        
        dcf_value = sum(dcf_cashflows) + terminal_pv
        
        return {
            'annual_noi': annual_noi,
            'cap_rate_valuations': valuations,
            'dcf_value': dcf_value,
            'dcf_assumptions': {
                'growth_rate': growth_rate,
                'discount_rate': discount_rate,
                'terminal_cap': terminal_cap,
            },
        }
    
    def generate_executive_summary(self) -> Dict:
        """Generate comprehensive executive summary"""
        
        # Run all analyses
        system_impacts = self.model_system_impacts()
        
        # Focus on recommended system (4-pipe WSHP + TES)
        recommended_system = system_impacts[system_impacts['system'] == '4-Pipe WSHP + TES'].iloc[0]
        
        # Calculate economics
        economics = self.calculate_project_economics('4pipe_wshp_tes')
        developer_returns = self.calculate_developer_returns(economics)
        bridge_loan = self.calculate_bridge_loan(economics)
        exit_value = self.value_stabilized_cashflows(economics)
        
        # Create summary
        summary = {
            'building': {
                'name': self.building_data['building_name'],
                'id': self.building_data['building_id'],
                'type': self.building_data['property_type'],
                'units': self.building_data['units'],
                'sqft': self.building_data['sqft'],
                'is_epb': self.building_data['is_epb'],
                'current_eui': self.building_data['weather_norm_eui'],
                'equipment_replacement_need': self.building_data['equipment_replacement_cost'],
            },
            'recommended_solution': {
                'system': recommended_system['system'],
                'new_eui': recommended_system['new_eui'],
                'eui_reduction': recommended_system['eui_reduction_pct'],
                'penalties_avoided_15yr': recommended_system['total_penalties_15yr'],
                'compliant_through_2030': recommended_system['compliant_2030'],
            },
            'project_economics': {
                'total_cost': economics['total_project_cost'],
                'total_incentives': economics['total_incentives'],
                'net_cost': economics['net_project_cost'],
                'incentive_coverage': economics['incentive_coverage'],
                'monthly_service_fee': economics['monthly_service_fee'],
                'annual_noi': economics['annual_noi'],
            },
            'financing': {
                'developer_equity': developer_returns['developer_equity_needed'],
                'bridge_loan_size': bridge_loan['bridge_facility_size'],
                'bridge_coverage_ratio': bridge_loan['coverage_ratio'],
                'months_to_repayment': bridge_loan['months_outstanding'],
            },
            'developer_returns': {
                'total_profit': developer_returns['total_upfront_profit'],
                'return_on_equity': developer_returns['return_on_equity'],
                '5yr_total': developer_returns['5yr_total_return'],
            },
            'exit_valuation': {
                'market_value': exit_value['cap_rate_valuations']['market']['value'],
                'value_per_unit': exit_value['cap_rate_valuations']['market']['price_per_unit'],
                'dcf_value': exit_value['dcf_value'],
            },
            'key_benefits': {
                'owner': [
                    f"Avoid ${self.building_data['equipment_replacement_cost']:,.0f} upfront cost",
                    f"Save ${recommended_system['total_penalties_15yr']:,.0f} in ED penalties",
                    "No capital investment required",
                    "Predictable monthly costs with 2.5% annual escalation",
                    "Modern 4-pipe system solves comfort issues",
                ],
                'developer': [
                    f"${developer_returns['total_upfront_profit']:,.0f} upfront profit",
                    f"{developer_returns['return_on_equity']:.0%} return on ${developer_returns['developer_equity_needed']:,.0f} equity",
                    f"Exit value ${exit_value['cap_rate_valuations']['market']['value']:,.0f}",
                    "Minimal capital at risk with bridge financing",
                ],
                'society': [
                    f"{recommended_system['eui_reduction_pct']:.0f}% energy reduction",
                    "Fully electric building (no gas combustion)",
                    "Thermal storage enables grid flexibility",
                    "Preserves affordable housing (EPB building)",
                ],
            },
            'next_steps': [
                "Finalize HOA/owner agreement",
                "Secure bridge loan commitment",
                "Submit DRCOG CPRG application",
                "Begin engineering design",
                "Order long-lead equipment",
            ],
            'timeline': {
                'agreement_execution': 'Month 1',
                'financing_close': 'Month 2',
                'construction_start': 'Month 3',
                'system_commissioning': 'Month 12',
                'stabilized_operations': 'Month 15',
            },
        }
        
        return summary
    
    def create_presentation_charts(self):
        """Create charts for presentations"""
        
        # Get data
        system_impacts = self.model_system_impacts()
        economics = self.calculate_project_economics('4pipe_wshp_tes')
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. EUI Comparison
        ax1 = axes[0, 0]
        systems = system_impacts['system']
        euis = system_impacts['new_eui']
        
        bars = ax1.bar(systems, euis, color=['red', 'orange', 'green'])
        ax1.axhline(y=self.building_data['first_interim_target'], color='blue', 
                   linestyle='--', label='2025 Target')
        ax1.axhline(y=self.building_data['second_interim_target'], color='navy', 
                   linestyle='--', label='2027 Target')
        ax1.axhline(y=self.building_data['final_target'], color='darkblue', 
                   linestyle='--', label='2030 Target')
        
        ax1.set_ylabel('Weather Normalized EUI')
        ax1.set_title('System EUI Performance vs Compliance Targets')
        ax1.legend()
        
        # Add value labels
        for bar, eui in zip(bars, euis):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{eui}', ha='center', va='bottom')
        
        # 2. Penalty Comparison
        ax2 = axes[0, 1]
        penalties = system_impacts['total_penalties_15yr']
        bars2 = ax2.bar(systems, penalties / 1000, color=['red', 'orange', 'green'])
        ax2.set_ylabel('Total Penalties ($1000s)')
        ax2.set_title('15-Year Penalty Exposure by System')
        
        for bar, penalty in zip(bars2, penalties):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                    f'${penalty/1000:.0f}k', ha='center', va='bottom')
        
        # 3. Project Economics Waterfall
        ax3 = axes[1, 0]
        
        # Waterfall data
        categories = ['Project\nCost', 'ITC', 'Deprec.', 'DRCOG', 'Xcel', 'Net\nCost']
        values = [
            economics['total_project_cost'],
            -economics['itc_amount'],
            -economics['depreciation_value'],
            -economics['drcog_grant'],
            -economics['xcel_rebate'],
            economics['net_project_cost']
        ]
        
        # Create waterfall
        cumulative = 0
        for i, (cat, val) in enumerate(zip(categories, values)):
            if i == 0:
                ax3.bar(cat, val/1000, color='red', alpha=0.7)
                cumulative = val
            elif i == len(categories) - 1:
                ax3.bar(cat, val/1000, color='green', alpha=0.7)
            else:
                ax3.bar(cat, val/1000, bottom=cumulative/1000, color='blue', alpha=0.7)
                cumulative += val
        
        ax3.set_ylabel('Amount ($1000s)')
        ax3.set_title('Project Economics - Incentive Waterfall')
        ax3.axhline(y=0, color='black', linewidth=0.8)
        
        # 4. Cash Flow Timeline
        ax4 = axes[1, 1]
        
        months = list(range(-6, 25))
        cash_flows = []
        
        # Simplified cash flow projection
        for month in months:
            if month < 0:
                cf = -30000  # Pre-construction
            elif month < 9:
                cf = -economics['total_project_cost'] / 9 * 0.8  # Construction
            elif month == 9:
                cf = economics['itc_amount'] + economics['drcog_grant']  # Incentives
            elif month == 12:
                cf = economics['depreciation_value'] + economics['xcel_rebate']
            else:
                cf = economics['annual_noi'] / 12  # Operations
            
            cash_flows.append(cf)
        
        # Color by phase
        colors = ['red' if m < 0 else 'orange' if m < 9 else 'green' for m in months]
        ax4.bar(months, [cf/1000 for cf in cash_flows], color=colors, alpha=0.7)
        ax4.axhline(y=0, color='black', linewidth=0.8)
        ax4.set_xlabel('Month')
        ax4.set_ylabel('Cash Flow ($1000s)')
        ax4.set_title('Project Cash Flow Timeline')
        ax4.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        ax4.axvline(x=9, color='gray', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        return fig
    
    def generate_full_report(self, output_path: str = None):
        """Generate complete analysis report with all components"""
        
        # Generate all analyses
        summary = self.generate_executive_summary()
        
        # Convert DataFrame to dict and handle boolean values
        system_comparison = self.model_system_impacts().to_dict('records')
        for record in system_comparison:
            for key, value in record.items():
                if isinstance(value, (np.bool_, bool)):
                    record[key] = bool(value)
                elif isinstance(value, np.integer):
                    record[key] = int(value)
                elif isinstance(value, np.floating):
                    record[key] = float(value)
        
        # Create report structure
        report = {
            'generated': datetime.now().isoformat(),
            'executive_summary': summary,
            'system_comparison': system_comparison,
            'recommended_economics': self.calculate_project_economics('4pipe_wshp_tes'),
            'developer_analysis': self.calculate_developer_returns(
                self.calculate_project_economics('4pipe_wshp_tes')
            ),
            'bridge_loan_structure': self.calculate_bridge_loan(
                self.calculate_project_economics('4pipe_wshp_tes')
            ),
            'exit_valuation': self.value_stabilized_cashflows(
                self.calculate_project_economics('4pipe_wshp_tes')
            ),
        }
        
        # Save if path provided
        if output_path:
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, cls=NumpyEncoder)
            
            print(f"Report saved to: {output_path}")
        
        return report


# Example usage
if __name__ == "__main__":
    # Create analyzer for Building 2952
    analyzer = IntegratedTESHPAnalyzer()
    
    # Generate executive summary
    summary = analyzer.generate_executive_summary()
    
    print("\n" + "="*80)
    print("TES+HP BUSINESS CASE - EXECUTIVE SUMMARY")
    print("="*80)
    
    print(f"\nBUILDING: {summary['building']['name']} (ID: {summary['building']['id']})")
    print(f"Type: {summary['building']['type']}")
    print(f"Size: {summary['building']['units']} units, {summary['building']['sqft']:,} sq ft")
    print(f"EPB Status: {'Yes' if summary['building']['is_epb'] else 'No'}")
    print(f"Current EUI: {summary['building']['current_eui']}")
    print(f"Equipment Replacement Need: ${summary['building']['equipment_replacement_need']:,.0f}")
    
    print(f"\nRECOMMENDED SOLUTION: {summary['recommended_solution']['system']}")
    print(f"New EUI: {summary['recommended_solution']['new_eui']} ({summary['recommended_solution']['eui_reduction']:.0f}% reduction)")
    print(f"Penalties Avoided (15-yr): ${summary['recommended_solution']['penalties_avoided_15yr']:,.0f}")
    print(f"Compliant through 2030: {'Yes' if summary['recommended_solution']['compliant_through_2030'] else 'No'}")
    
    print(f"\nPROJECT ECONOMICS:")
    print(f"Total Project Cost: ${summary['project_economics']['total_cost']:,.0f}")
    print(f"Total Incentives: ${summary['project_economics']['total_incentives']:,.0f}")
    print(f"Net Cost: ${summary['project_economics']['net_cost']:,.0f}")
    print(f"Incentive Coverage: {summary['project_economics']['incentive_coverage']:.0%}")
    print(f"Monthly Service Fee: ${summary['project_economics']['monthly_service_fee']:,.0f}")
    print(f"Annual NOI: ${summary['project_economics']['annual_noi']:,.0f}")
    
    print(f"\nFINANCING STRUCTURE:")
    print(f"Developer Equity Needed: ${summary['financing']['developer_equity']:,.0f}")
    print(f"Bridge Loan Size: ${summary['financing']['bridge_loan_size']:,.0f}")
    print(f"Bridge Coverage Ratio: {summary['financing']['bridge_coverage_ratio']:.1f}x")
    print(f"Months to Repayment: {summary['financing']['months_to_repayment']}")
    
    print(f"\nDEVELOPER RETURNS:")
    print(f"Total Upfront Profit: ${summary['developer_returns']['total_profit']:,.0f}")
    print(f"Return on Equity: {summary['developer_returns']['return_on_equity']:.0%}")
    print(f"5-Year Total Return: ${summary['developer_returns']['5yr_total']:,.0f}")
    
    print(f"\nEXIT VALUATION:")
    print(f"Market Value (8% cap): ${summary['exit_valuation']['market_value']:,.0f}")
    print(f"Value per Unit: ${summary['exit_valuation']['value_per_unit']:,.0f}")
    print(f"DCF Value: ${summary['exit_valuation']['dcf_value']:,.0f}")
    
    print("\nKEY BENEFITS:")
    for stakeholder, benefits in summary['key_benefits'].items():
        print(f"\n{stakeholder.upper()}:")
        for benefit in benefits:
            print(f"  • {benefit}")
    
    print("\nNEXT STEPS:")
    for i, step in enumerate(summary['next_steps'], 1):
        print(f"{i}. {step}")
    
    # Generate full report
    report_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/building_2952_tes_hp_analysis.json'
    analyzer.generate_full_report(report_path)
    
    # Create presentation charts
    fig = analyzer.create_presentation_charts()
    chart_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/building_2952_charts.png'
    fig.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"\nCharts saved to: {chart_path}")
