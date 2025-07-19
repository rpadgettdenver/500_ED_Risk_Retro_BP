"""
Suggested File Name: tes_hp_cash_flow_bridge.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/models/
Use: Detailed month-by-month cash flow analysis for TES+HP projects from development through stabilization

This module creates detailed cash flow bridges showing:
- Pre-construction development costs
- Construction period funding needs
- Bridge loan requirements and timing
- Incentive/rebate receipt timing
- Stabilized operations cash flows
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

class TESHPCashFlowBridge:
    """Model month-by-month cash flows for TES+HP Energy-as-a-Service projects"""
    
    def __init__(self, project_data: Dict = None):
        """
        Initialize with project configuration

        Args:
            project_data: Dict with project parameters
        """
        # Default configuration for 50-unit multifamily (Building 2952 as example)
        self.project_data = {
            'building_name': 'Timperly Condominium',
            'building_id': '2952',
            'units': 52,
            'sqft': 52826,
            'is_epb': True,

            # Project costs
            'equipment_cost': 1000000,  # Heat pumps, controls
            'tes_cost': 200000,  # Thermal storage
            'soft_costs': 300000,  # Engineering, permits, legal
            'developer_fee_pct': 0.15,  # 15% of hard costs
            'contingency_pct': 0.10,  # 10% contingency
            'market_escalation': 1.30,  # 30% escalation factor

            # Incentives
            'itc_rate': 0.40,  # 40% (30% base + 10% energy community)
            'depreciation_rate': 0.80,  # 80% bonus depreciation
            'depreciation_value_pct': 0.85,  # Sell at 85% of value
            'drcog_grant_per_unit': 5000,  # $5k per unit for EPB
            'xcel_rebate_per_unit': 3500,  # Clean Heat Plan
            'tax_credit_sale_rate': 0.95,  # Sell credits at 95 cents

            # Financing
            'bridge_loan_rate': 0.12,  # 12% annual
            'bridge_loan_fee': 0.02,  # 2% origination
            'perm_loan_rate': 0.07,  # 7% permanent financing
            'perm_loan_ltv': 0.70,  # 70% LTV on cash flows

            # Operations
            'monthly_service_fee_per_unit': 150,  # Starting fee
            'annual_escalation': 0.025,  # 2.5% annual
            'operating_margin': 0.30,  # 30% operating margin

            # Timeline (months)
            'pre_construction_months': 6,
            'construction_months': 9,
            'stabilization_months': 3,
        }
        if project_data:
            for k, v in project_data.items():
                self.project_data[k] = v

        self.timeline = self._create_timeline()
        self.cash_flows = None

    def _create_timeline(self) -> List[Dict]:
        """Create month-by-month timeline"""
        timeline = []
        pre_construction_months = int(float(self.project_data.get('pre_construction_months', 6)))
        construction_months = int(float(self.project_data.get('construction_months', 9)))
        # Use default if not present
        month_counter = -pre_construction_months

        # Pre-construction phase
        for i in range(pre_construction_months):
            timeline.append({
                'month': month_counter,
                'phase': 'pre_construction',
                'month_in_phase': i + 1,
                'calendar_month': (datetime.now() + timedelta(days=30 * month_counter)).strftime('%Y-%m')
            })
            month_counter += 1

        # Construction phase
        for i in range(construction_months):
            timeline.append({
                'month': month_counter,
                'phase': 'construction',
                'month_in_phase': i + 1,
                'calendar_month': (datetime.now() + timedelta(days=30 * month_counter)).strftime('%Y-%m')
            })
            month_counter += 1

        # Operations phase (24 months shown)
        for i in range(24):
            timeline.append({
                'month': month_counter,
                'phase': 'operations',
                'month_in_phase': i + 1,
                'calendar_month': (datetime.now() + timedelta(days=30 * month_counter)).strftime('%Y-%m')
            })
            month_counter += 1

        return timeline

    def calculate_project_costs(self) -> Dict:
        """Calculate total project costs with all components"""
        base_hard_costs = float(self.project_data.get('equipment_cost', 0)) + float(self.project_data.get('tes_cost', 0))

        # Apply escalation to hard costs
        escalated_hard_costs = base_hard_costs * float(self.project_data.get('market_escalation', 1.0))

        # Developer fee on escalated hard costs
        developer_fee = escalated_hard_costs * float(self.project_data.get('developer_fee_pct', 0.0))

        # Soft costs (also escalated)
        escalated_soft_costs = float(self.project_data.get('soft_costs', 0)) * float(self.project_data.get('market_escalation', 1.0))

        # Subtotal before contingency
        subtotal = escalated_hard_costs + developer_fee + escalated_soft_costs

        # Contingency
        contingency = subtotal * float(self.project_data.get('contingency_pct', 0.0))

        # Total project cost
        total_cost = subtotal + contingency

        return {
            'base_hard_costs': base_hard_costs,
            'escalated_hard_costs': escalated_hard_costs,
            'developer_fee': developer_fee,
            'escalated_soft_costs': escalated_soft_costs,
            'contingency': contingency,
            'total_project_cost': total_cost,
        }

    def calculate_incentives(self, project_costs: Dict) -> Dict:
        """Calculate all available incentives"""

        # ITC on eligible basis (equipment only, not soft costs)
        itc_basis = project_costs['escalated_hard_costs']
        itc_amount = itc_basis * self.project_data['itc_rate']

        # Depreciation
        depreciation_basis = project_costs['escalated_hard_costs']
        depreciation_amount = depreciation_basis * self.project_data['depreciation_rate']
        depreciation_value = depreciation_amount * 0.35  # 35% tax rate
        depreciation_sale_proceeds = depreciation_value * self.project_data['depreciation_value_pct']

        # Grants and rebates
        drcog_grant = float(self.project_data.get('units', 0)) * float(self.project_data.get('drcog_grant_per_unit', 0))
        xcel_rebate = float(self.project_data.get('units', 0)) * float(self.project_data.get('xcel_rebate_per_unit', 0))

        # Tax credit sale proceeds
        tax_credit_proceeds = itc_amount * float(self.project_data.get('tax_credit_sale_rate', 1.0))

        # Origination fees on incentives
        rebate_origination = (drcog_grant + xcel_rebate) * 0.025  # 2.5% fee

        return {
            'itc_amount': itc_amount,
            'tax_credit_proceeds': tax_credit_proceeds,
            'depreciation_amount': depreciation_amount,
            'depreciation_value': depreciation_value,
            'depreciation_sale_proceeds': depreciation_sale_proceeds,
            'drcog_grant': drcog_grant,
            'xcel_rebate': xcel_rebate,
            'rebate_origination': rebate_origination,
            'total_incentives': (tax_credit_proceeds + depreciation_sale_proceeds +
                               drcog_grant + xcel_rebate),
        }

    def model_cash_flows(self) -> pd.DataFrame:
        """Create detailed month-by-month cash flow model"""

        # Calculate project economics
        project_costs = self.calculate_project_costs()
        incentives = self.calculate_incentives(project_costs)

        # Initialize cash flow dataframe
        cf_data = []

        # Track cumulative values
        cumulative_spend = 0
        bridge_loan_balance = 0
        cumulative_cash = 0

        for month_data in self.timeline:
            month = month_data['month']
            phase = month_data['phase']

            # Initialize month's cash flows
            month_cf = {
                'month': month,
                'phase': phase,
                'calendar_month': month_data['calendar_month'],
            }

            # PRE-CONSTRUCTION PHASE
            if phase == 'pre_construction':
                if month == -6:
                    # Initial development costs
                    month_cf['development_costs'] = -50000  # Legal, initial engineering
                    month_cf['cash_out'] = -50000

                elif month == -4:
                    # Major engineering and sales costs
                    month_cf['development_costs'] = -75000
                    month_cf['cash_out'] = -75000

                elif month == -2:
                    # Final pre-construction costs
                    month_cf['development_costs'] = -50000
                    month_cf['cash_out'] = -50000

                else:
                    month_cf['development_costs'] = -10000  # Ongoing costs
                    month_cf['cash_out'] = -10000

            # CONSTRUCTION PHASE
            elif phase == 'construction':
                month_in_phase = month_data['month_in_phase']

                # Construction draws (S-curve)
                if month_in_phase <= 3:
                    draw_pct = 0.15  # 15% per month for first 3 months
                elif month_in_phase <= 6:
                    draw_pct = 0.20  # 20% per month for months 4-6
                else:
                    draw_pct = 0.05  # 5% per month for final months

                construction_draw = project_costs['total_project_cost'] * draw_pct
                month_cf['construction_draw'] = -construction_draw

                # Developer fee timing (25% at start, 50% at month 6, 25% at completion)
                if month_in_phase == 1:
                    month_cf['developer_fee'] = project_costs['developer_fee'] * 0.25
                elif month_in_phase == 6:
                    month_cf['developer_fee'] = project_costs['developer_fee'] * 0.50
                elif month_in_phase == 9:
                    month_cf['developer_fee'] = project_costs['developer_fee'] * 0.25

                # Incentive timing
                if month_in_phase == 3:
                    # DRCOG grant on 25% completion
                    month_cf['drcog_grant'] = incentives['drcog_grant']
                    month_cf['rebate_origination'] = incentives['rebate_origination'] * 0.5

                elif month_in_phase == 9:
                    # Xcel rebate at commissioning
                    month_cf['xcel_rebate'] = incentives['xcel_rebate']
                    month_cf['rebate_origination'] = incentives['rebate_origination'] * 0.5

                # Calculate net cash need
                cash_in = sum([v for k, v in month_cf.items() if isinstance(v, (int, float)) and v > 0])
                cash_out = sum([v for k, v in month_cf.items() if isinstance(v, (int, float)) and v < 0])
                month_cf['net_cash_flow'] = cash_in + cash_out

                # Bridge loan calculations
                if month_cf['net_cash_flow'] < 0:
                    # Need to draw on bridge
                    bridge_draw = -month_cf['net_cash_flow']
                    bridge_loan_balance += bridge_draw
                    month_cf['bridge_draw'] = bridge_draw
                else:
                    # Can pay down bridge
                    bridge_paydown = min(month_cf['net_cash_flow'], bridge_loan_balance)
                    bridge_loan_balance -= bridge_paydown
                    month_cf['bridge_paydown'] = -bridge_paydown

                # Bridge loan interest
                bridge_loan_rate = float(self.project_data.get('loan_interest_rate', self.project_data.get('bridge_loan_rate', 0.12)))
                month_cf['bridge_interest'] = -bridge_loan_balance * bridge_loan_rate / 12

            # OPERATIONS PHASE
            elif phase == 'operations':
                month_in_phase = month_data['month_in_phase']

                # Monthly service fees
                base_fee = float(self.project_data.get('monthly_service_fee_per_unit', 0)) * float(self.project_data.get('units', 0))
                # Apply annual escalation
                years_operating = (month - float(self.project_data.get('construction_months', 9))) / 12
                escalation_factor = (1 + float(self.project_data.get('annual_escalation', 0.0))) ** years_operating

                month_cf['service_revenue'] = base_fee * escalation_factor

                # Operating expenses (70% of revenue for 30% margin)
                month_cf['operating_expenses'] = -month_cf['service_revenue'] * (1 - float(self.project_data.get('operating_margin', 0.0)))

                # Special items in early operations
                if month_in_phase == 1:
                    # Bridge loan payoff with tax credit sale
                    month_cf['tax_credit_sale'] = incentives['tax_credit_proceeds']
                    month_cf['bridge_payoff'] = -bridge_loan_balance
                    bridge_loan_balance = 0

                elif month_in_phase == 3:
                    # Depreciation sale
                    month_cf['depreciation_sale'] = incentives['depreciation_sale_proceeds']

                # NOI
                month_cf['noi'] = (month_cf.get('service_revenue', 0) +
                                 month_cf.get('operating_expenses', 0))

            # Update cumulative tracking
            all_cash_items = [k for k in month_cf.keys() if k not in ['month', 'phase', 'calendar_month']]
            month_cf['total_cash_flow'] = sum([month_cf.get(k, 0) for k in all_cash_items])

            cumulative_cash += month_cf['total_cash_flow']
            month_cf['cumulative_cash'] = cumulative_cash
            month_cf['bridge_balance'] = bridge_loan_balance

            cf_data.append(month_cf)

        # Convert to dataframe
        self.cash_flows = pd.DataFrame(cf_data)

        # Fill NaN with 0
        self.cash_flows = self.cash_flows.fillna(0)

        return self.cash_flows

    def calculate_bridge_loan_needs(self) -> Dict:
        """Calculate bridge loan requirements"""
        if self.cash_flows is None:
            self.model_cash_flows()

        # Find maximum bridge loan balance
        max_bridge = self.cash_flows['bridge_balance'].max()

        # Add origination fee
        total_bridge_needed = max_bridge * (1 + self.project_data['bridge_loan_fee'])

        # Calculate interest costs
        total_interest = -self.cash_flows['bridge_interest'].sum()

        # Find payoff timing
        payoff_rows = self.cash_flows[self.cash_flows['bridge_payoff'] < 0]
        if len(payoff_rows) > 0:
            payoff_month = payoff_rows['month'].values[0]
        else:
            payoff_month = float(self.project_data.get('construction_months', 9))

        pre_construction_months = float(self.project_data.get('pre_construction_months', 6))
        return {
            'maximum_draw': max_bridge,
            'total_facility_needed': total_bridge_needed,
            'total_interest_paid': total_interest,
            'months_outstanding': payoff_month + pre_construction_months,
            'effective_rate': total_interest / max_bridge / (payoff_month + pre_construction_months) * 12 if max_bridge > 0 else 0,
            'security': {
                'tax_credits': self.calculate_incentives(self.calculate_project_costs())['tax_credit_proceeds'],
                'grants_rebates': (self.calculate_incentives(self.calculate_project_costs())['drcog_grant'] +
                                 self.calculate_incentives(self.calculate_project_costs())['xcel_rebate']),
                'equipment_lien': self.calculate_project_costs()['escalated_hard_costs'],
            }
        }

    def calculate_developer_returns(self) -> Dict:
        """Calculate total developer returns"""
        if self.cash_flows is None:
            self.model_cash_flows()

        # Sum up developer income streams
        developer_fee = self.cash_flows['developer_fee'].sum()
        rebate_origination = self.cash_flows['rebate_origination'].sum()
        depreciation_sale = self.cash_flows['depreciation_sale'].sum()

        # Tax credit broker spread (not explicitly in cash flows)
        project_costs = self.calculate_project_costs()
        incentives = self.calculate_incentives(project_costs)
        tc_broker_spread = incentives['itc_amount'] * 0.05  # 5% spread

        # Calculate developer equity needed (max negative cumulative cash before bridge draws)
        cf_before_bridge = self.cash_flows[self.cash_flows['month'] < 0]
        max_equity_needed = -cf_before_bridge['total_cash_flow'].sum()

        total_developer_profit = developer_fee + rebate_origination + depreciation_sale + tc_broker_spread

        return {
            'developer_fee': developer_fee,
            'rebate_origination': rebate_origination,
            'depreciation_sale': depreciation_sale,
            'tax_credit_spread': tc_broker_spread,
            'total_profit': total_developer_profit,
            'equity_invested': max_equity_needed,
            'return_on_equity': total_developer_profit / max_equity_needed if max_equity_needed > 0 else 0,
            'irr_estimate': (total_developer_profit / max_equity_needed) ** (12 / 18) - 1 if max_equity_needed > 0 else 0,
        }

    def calculate_stabilized_value(self) -> Dict:
        """Calculate value of stabilized cash flows"""
        if self.cash_flows is None:
            self.model_cash_flows()

        # Get stabilized NOI (year 2 operations)
        ops_months = self.cash_flows[self.cash_flows['phase'] == 'operations']
        year2_ops = ops_months[(ops_months['month'] >= 12) & (ops_months['month'] < 24)]

        annual_noi = float(self.project_data.get('annual_noi', year2_ops['noi'].sum()))

        # Apply cap rates for infrastructure assets
        cap_rates = {
            'conservative': 0.10,  # 10% cap rate
            'market': 0.08,  # 8% cap rate
            'aggressive': 0.06,  # 6% cap rate
        }

        values = {}
        for scenario, cap_rate in cap_rates.items():
            values[scenario] = {
                'cap_rate': cap_rate,
                'asset_value': annual_noi / cap_rate,
                'multiple': 1 / cap_rate,
            }

        # Add growth assumptions
        # With 2.5% annual escalation and 20-year contract
        pv_factor = sum([(1.025 ** i) / (1.08 ** i) for i in range(20)])  # 8% discount rate
        contract_value = annual_noi * pv_factor

        return {
            'year2_noi': annual_noi,
            'monthly_noi': annual_noi / 12,
            'cap_rate_valuations': values,
            'contract_pv': contract_value,
            'perpetuity_value': annual_noi / (0.08 - 0.025),  # Gordon growth model
        }

    def generate_summary_report(self) -> Dict:
        """Generate comprehensive summary report"""
        if self.cash_flows is None:
            self.model_cash_flows()

        project_costs = self.calculate_project_costs()
        incentives = self.calculate_incentives(project_costs)
        bridge_needs = self.calculate_bridge_loan_needs()
        developer_returns = self.calculate_developer_returns()
        stabilized_value = self.calculate_stabilized_value()

        return {
            'project_summary': {
                'building': self.project_data.get('building_name', ''),
                'units': self.project_data.get('units', ''),
                'sqft': self.project_data.get('sqft', ''),
                'is_epb': self.project_data.get('is_epb', False),
            },
            'project_costs': project_costs,
            'incentives': incentives,
            'net_developer_cost': float(project_costs['total_project_cost']) - float(incentives['total_incentives']),
            'bridge_loan': bridge_needs,
            'developer_returns': developer_returns,
            'stabilized_value': stabilized_value,
            'key_metrics': {
                'total_project_cost': float(project_costs['total_project_cost']),
                'incentive_coverage': float(incentives['total_incentives']) / float(project_costs['total_project_cost']) if float(project_costs['total_project_cost']) != 0 else 0,
                'developer_equity_needed': developer_returns['equity_invested'],
                'developer_total_profit': developer_returns['total_profit'],
                'developer_roe': developer_returns['return_on_equity'],
                'stabilized_asset_value': stabilized_value['cap_rate_valuations']['market']['asset_value'],
            }
        }
    
    def plot_cash_flow_bridge(self):
        """Create visualization of cash flow bridge"""
        if self.cash_flows is None:
            self.model_cash_flows()
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        # 1. Monthly Cash Flows
        ax1 = axes[0]
        months = self.cash_flows['month']
        
        # Separate inflows and outflows
        inflow_cols = ['developer_fee', 'drcog_grant', 'xcel_rebate', 'tax_credit_sale', 
                      'depreciation_sale', 'service_revenue', 'bridge_draw']
        outflow_cols = ['development_costs', 'construction_draw', 'operating_expenses', 
                       'bridge_interest', 'bridge_paydown', 'bridge_payoff']
        
        # Stack inflows
        bottom = np.zeros(len(months))
        for col in inflow_cols:
            if col in self.cash_flows.columns:
                values = self.cash_flows[col].fillna(0)
                if values.sum() > 0:
                    ax1.bar(months, values, bottom=bottom, label=col.replace('_', ' ').title())
                    bottom += values
        
        # Stack outflows
        bottom = np.zeros(len(months))
        for col in outflow_cols:
            if col in self.cash_flows.columns:
                values = self.cash_flows[col].fillna(0)
                if values.sum() < 0:
                    ax1.bar(months, values, bottom=bottom, label=col.replace('_', ' ').title())
                    bottom += values
        
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Cash Flow ($)')
        ax1.set_title('Monthly Cash Flows by Source')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # 2. Cumulative Cash and Bridge Balance
        ax2 = axes[1]
        ax2.plot(months, self.cash_flows['cumulative_cash'], 'b-', label='Cumulative Cash', linewidth=2)
        ax2.plot(months, self.cash_flows['bridge_balance'], 'r--', label='Bridge Loan Balance', linewidth=2)
        ax2.fill_between(months, 0, self.cash_flows['bridge_balance'], alpha=0.3, color='red')
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax2.set_xlabel('Month')
        ax2.set_ylabel('Amount ($)')
        ax2.set_title('Cumulative Cash Position and Bridge Loan Balance')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Phase Summary
        ax3 = axes[2]
        phase_summary = self.cash_flows.groupby('phase')['total_cash_flow'].sum()
        colors = {'pre_construction': 'red', 'construction': 'orange', 'operations': 'green'}
        bars = ax3.bar(phase_summary.index, phase_summary.values, 
                       color=[colors[x] for x in phase_summary.index])
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax3.set_xlabel('Phase')
        ax3.set_ylabel('Total Cash Flow ($)')
        ax3.set_title('Cash Flow by Project Phase')
        ax3.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:,.0f}', ha='center', va='bottom' if height > 0 else 'top')
        
        plt.tight_layout()
        return fig


# Example usage
if __name__ == "__main__":
    # Create cash flow model for Building 2952
    cf_model = TESHPCashFlowBridge()
    
    # Generate cash flows
    cash_flows = cf_model.model_cash_flows()
    
    # Get summary report
    summary = cf_model.generate_summary_report()
    
    # Print key insights
    print("TES+HP CASH FLOW BRIDGE ANALYSIS")
    print("=" * 80)
    print(f"\nProject: {summary['project_summary']['building']}")
    print(f"Size: {summary['project_summary']['units']} units, {summary['project_summary']['sqft']:,} sq ft")
    print(f"EPB Status: {'Yes' if summary['project_summary']['is_epb'] else 'No'}")
    
    print(f"\nPROJECT ECONOMICS:")
    print(f"Total Project Cost: ${summary['project_costs']['total_project_cost']:,.0f}")
    print(f"Total Incentives: ${summary['incentives']['total_incentives']:,.0f}")
    print(f"Net Developer Cost: ${summary['net_developer_cost']:,.0f}")
    print(f"Incentive Coverage: {summary['key_metrics']['incentive_coverage']:.1%}")
    
    print(f"\nBRIDGE LOAN REQUIREMENTS:")
    print(f"Maximum Draw: ${summary['bridge_loan']['maximum_draw']:,.0f}")
    print(f"Total Facility Needed: ${summary['bridge_loan']['total_facility_needed']:,.0f}")
    print(f"Months Outstanding: {summary['bridge_loan']['months_outstanding']}")
    print(f"Total Interest Paid: ${summary['bridge_loan']['total_interest_paid']:,.0f}")
    
    print(f"\nBRIDGE LOAN SECURITY:")
    for asset, value in summary['bridge_loan']['security'].items():
        print(f"  {asset.replace('_', ' ').title()}: ${value:,.0f}")
    
    print(f"\nDEVELOPER RETURNS:")
    print(f"Equity Invested: ${summary['developer_returns']['equity_invested']:,.0f}")
    print(f"Developer Fee: ${summary['developer_returns']['developer_fee']:,.0f}")
    print(f"Rebate Origination: ${summary['developer_returns']['rebate_origination']:,.0f}")
    print(f"Depreciation Sale: ${summary['developer_returns']['depreciation_sale']:,.0f}")
    print(f"Tax Credit Spread: ${summary['developer_returns']['tax_credit_spread']:,.0f}")
    print(f"Total Profit: ${summary['developer_returns']['total_profit']:,.0f}")
    print(f"Return on Equity: {summary['developer_returns']['return_on_equity']:.0%}")
    
    print(f"\nSTABILIZED VALUE:")
    print(f"Year 2 NOI: ${summary['stabilized_value']['year2_noi']:,.0f}")
    print(f"Monthly NOI: ${summary['stabilized_value']['monthly_noi']:,.0f}")
    print(f"\nValuation Scenarios:")
    for scenario, details in summary['stabilized_value']['cap_rate_valuations'].items():
        print(f"  {scenario.title()} ({details['cap_rate']:.0%} cap): ${details['asset_value']:,.0f} ({details['multiple']:.1f}x NOI)")
    
    # Create visualization
    fig = cf_model.plot_cash_flow_bridge()
    plt.savefig('/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/cash_flow_bridge.png', 
                dpi=300, bbox_inches='tight')
