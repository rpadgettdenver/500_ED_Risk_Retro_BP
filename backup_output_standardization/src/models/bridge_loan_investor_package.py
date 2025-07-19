"""
Suggested File Name: bridge_loan_investor_package.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/models/
Use: Generate professional bridge loan investor packages for TES+HP projects

This module creates:
- Executive summary for bridge lenders
- Security analysis and coverage ratios
- Cash flow waterfalls showing repayment
- Risk mitigation strategies
- Professional PDF output
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as patches
from typing import Dict, List, Tuple

class BridgeLoanInvestorPackage:
    """Generate professional bridge loan packages for investors"""
    
    def __init__(self, project_data: Dict = None):
        """Initialize with project data"""
        
        # Default to Building 2952 TES+HP project
        self.project_data = project_data or {
            'project_name': 'Timperly Condominium TES+HP Retrofit',
            'building_address': '1255 N Ogden St, Denver, CO 80218',
            'building_type': 'Multifamily Housing (52 units)',
            'developer': 'Denver Thermal Energy Solutions LLC',
            
            # Project costs
            'total_project_cost': 1600000,
            'equipment_cost': 1300000,
            'soft_costs': 300000,
            
            # Incentives (take-out sources)
            'itc_amount': 520000,  # 40% of equipment
            'itc_sale_price': 494000,  # 95 cents
            'depreciation_value': 364000,  # Tax value
            'depreciation_sale': 309400,  # 85% of value
            'drcog_grant': 260000,  # $5k per unit
            'xcel_rebate': 182000,  # $3.5k per unit
            
            # Bridge loan request
            'bridge_request': 1400000,
            'origination_fee': 28000,  # 2%
            'interest_rate': 0.12,  # 12% annual
            'term_months': 12,
            
            # Security
            'equipment_lien_value': 1300000,
            'contract_value': 2400000,  # 20-year NPV
            'personal_guarantee': True,
            'completion_guarantee': True,
        }
        
        self.colors = {
            'primary': '#003f5c',
            'secondary': '#58508d',
            'accent': '#bc5090',
            'positive': '#2e8b57',
            'negative': '#dc143c',
        }
        
    def calculate_coverage_ratios(self) -> Dict:
        """Calculate key coverage ratios for lenders"""
        
        total_takeout = (
            self.project_data['itc_sale_price'] +
            self.project_data['depreciation_sale'] +
            self.project_data['drcog_grant'] +
            self.project_data['xcel_rebate']
        )
        
        # Interest during term
        total_interest = (self.project_data['bridge_request'] * 
                         self.project_data['interest_rate'] * 
                         self.project_data['term_months'] / 12)
        
        total_repayment = self.project_data['bridge_request'] + total_interest
        
        return {
            'loan_to_cost': self.project_data['bridge_request'] / self.project_data['total_project_cost'],
            'loan_to_value': self.project_data['bridge_request'] / self.project_data['equipment_lien_value'],
            'takeout_coverage': total_takeout / total_repayment,
            'itc_coverage': self.project_data['itc_sale_price'] / self.project_data['bridge_request'],
            'total_collateral': total_takeout + self.project_data['equipment_lien_value'],
            'collateral_coverage': (total_takeout + self.project_data['equipment_lien_value']) / total_repayment,
            'debt_service_coverage': total_takeout / total_repayment,
            'total_takeout': total_takeout,
            'total_interest': total_interest,
            'total_repayment': total_repayment,
        }
    
    def create_repayment_timeline(self) -> pd.DataFrame:
        """Create month-by-month repayment schedule"""
        
        timeline = []
        loan_balance = self.project_data['bridge_request']
        
        for month in range(self.project_data['term_months'] + 1):
            
            if month == 0:
                # Loan funding
                timeline.append({
                    'month': month,
                    'description': 'Loan Funding',
                    'disbursement': self.project_data['bridge_request'],
                    'repayment': 0,
                    'interest': 0,
                    'balance': loan_balance,
                })
                
            elif month == 3:
                # DRCOG grant received
                interest = loan_balance * self.project_data['interest_rate'] / 12
                repayment = min(self.project_data['drcog_grant'], loan_balance + interest)
                loan_balance = loan_balance + interest - repayment
                
                timeline.append({
                    'month': month,
                    'description': 'DRCOG Grant Received',
                    'disbursement': 0,
                    'repayment': repayment,
                    'interest': interest,
                    'balance': loan_balance,
                })
                
            elif month == 9:
                # Construction complete - Xcel rebate
                interest = loan_balance * self.project_data['interest_rate'] / 12
                repayment = min(self.project_data['xcel_rebate'], loan_balance + interest)
                loan_balance = loan_balance + interest - repayment
                
                timeline.append({
                    'month': month,
                    'description': 'Xcel Rebate Received',
                    'disbursement': 0,
                    'repayment': repayment,
                    'interest': interest,
                    'balance': loan_balance,
                })
                
            elif month == 10:
                # Tax credit sale closes
                interest = loan_balance * self.project_data['interest_rate'] / 12
                repayment = min(self.project_data['itc_sale_price'], loan_balance + interest)
                loan_balance = loan_balance + interest - repayment
                
                timeline.append({
                    'month': month,
                    'description': 'Tax Credit Sale',
                    'disbursement': 0,
                    'repayment': repayment,
                    'interest': interest,
                    'balance': loan_balance,
                })
                
            elif month == 12:
                # Depreciation sale + final payoff
                interest = loan_balance * self.project_data['interest_rate'] / 12
                repayment = loan_balance + interest
                
                timeline.append({
                    'month': month,
                    'description': 'Depreciation Sale + Final Payoff',
                    'disbursement': 0,
                    'repayment': repayment,
                    'interest': interest,
                    'balance': 0,
                })
                
            else:
                # Interest only months
                interest = loan_balance * self.project_data['interest_rate'] / 12
                loan_balance += interest
                
                timeline.append({
                    'month': month,
                    'description': 'Interest Accrual',
                    'disbursement': 0,
                    'repayment': 0,
                    'interest': interest,
                    'balance': loan_balance,
                })
        
        return pd.DataFrame(timeline)
    
    def create_executive_summary_page(self, pdf):
        """Create executive summary page"""
        
        fig = plt.figure(figsize=(8.5, 11))
        fig.suptitle('BRIDGE LOAN INVESTMENT OPPORTUNITY', fontsize=16, fontweight='bold')
        
        # Remove axes
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Project header
        y_pos = 0.90
        ax.text(0.5, y_pos, self.project_data['project_name'], 
               ha='center', fontsize=14, fontweight='bold')
        
        y_pos -= 0.03
        ax.text(0.5, y_pos, self.project_data['building_address'], 
               ha='center', fontsize=11)
        
        # Loan terms box
        y_pos -= 0.08
        terms_box = patches.FancyBboxPatch((0.1, y_pos - 0.15), 0.8, 0.15,
                                          boxstyle="round,pad=0.02",
                                          facecolor='lightblue', alpha=0.3)
        ax.add_patch(terms_box)
        
        ax.text(0.5, y_pos - 0.02, 'LOAN TERMS', ha='center', fontsize=12, fontweight='bold')
        
        # Two columns for loan terms
        col1_x = 0.15
        col2_x = 0.55
        y_pos -= 0.05
        
        terms_left = [
            f"Loan Amount: ${self.project_data['bridge_request']:,.0f}",
            f"Interest Rate: {self.project_data['interest_rate']:.0%} annual",
            f"Term: {self.project_data['term_months']} months",
        ]
        
        terms_right = [
            f"Origination Fee: {self.project_data['origination_fee'] / self.project_data['bridge_request']:.0%}",
            f"Type: Interest accruing",
            f"Security: 1st lien on equipment",
        ]
        
        for term in terms_left:
            ax.text(col1_x, y_pos, term, fontsize=10)
            y_pos -= 0.03
            
        y_pos += 0.09  # Reset for right column
        for term in terms_right:
            ax.text(col2_x, y_pos, term, fontsize=10)
            y_pos -= 0.03
        
        # Coverage ratios
        y_pos -= 0.08
        coverage = self.calculate_coverage_ratios()
        
        coverage_box = patches.FancyBboxPatch((0.1, y_pos - 0.12), 0.8, 0.12,
                                            boxstyle="round,pad=0.02",
                                            facecolor='lightgreen', alpha=0.3)
        ax.add_patch(coverage_box)
        
        ax.text(0.5, y_pos - 0.02, 'COVERAGE RATIOS', ha='center', fontsize=12, fontweight='bold')
        y_pos -= 0.04
        
        ratios = [
            f"Take-out Coverage: {coverage['takeout_coverage']:.1f}x",
            f"Collateral Coverage: {coverage['collateral_coverage']:.1f}x",
            f"Loan-to-Cost: {coverage['loan_to_cost']:.0%}",
        ]
        
        for i, ratio in enumerate(ratios):
            x_pos = 0.2 + (i % 3) * 0.25
            ax.text(x_pos, y_pos - 0.03, ratio, fontsize=10)
        
        # Take-out sources
        y_pos -= 0.10
        ax.text(0.5, y_pos, 'REPAYMENT SOURCES', ha='center', fontsize=12, fontweight='bold')
        y_pos -= 0.03
        
        sources = [
            ('Federal Tax Credits (ITC)', self.project_data['itc_sale_price'], 3),
            ('Depreciation Benefits', self.project_data['depreciation_sale'], 3),
            ('DRCOG Grant', self.project_data['drcog_grant'], 10),
            ('Xcel Clean Heat Rebate', self.project_data['xcel_rebate'], 12),
        ]
        
        y_pos -= 0.02
        for source, amount, month in sources:
            ax.text(0.15, y_pos, source, fontsize=10)
            ax.text(0.55, y_pos, f"${amount:,.0f}", fontsize=10, ha='right')
            ax.text(0.75, y_pos, f"Month {month}", fontsize=10, ha='right')
            y_pos -= 0.03
        
        # Total line
        ax.plot([0.15, 0.75], [y_pos, y_pos], 'k-', linewidth=1)
        y_pos -= 0.02
        ax.text(0.15, y_pos, 'Total Take-out', fontsize=10, fontweight='bold')
        ax.text(0.55, y_pos, f"${coverage['total_takeout']:,.0f}", 
               fontsize=10, fontweight='bold', ha='right')
        ax.text(0.75, y_pos, f"{coverage['takeout_coverage']:.1f}x coverage", 
               fontsize=10, fontweight='bold', ha='right')
        
        # Investment highlights
        y_pos -= 0.08
        highlights_box = patches.FancyBboxPatch((0.1, y_pos - 0.15), 0.8, 0.15,
                                              boxstyle="round,pad=0.02",
                                              facecolor='gold', alpha=0.2)
        ax.add_patch(highlights_box)
        
        ax.text(0.5, y_pos - 0.02, 'INVESTMENT HIGHLIGHTS', ha='center', 
               fontsize=12, fontweight='bold')
        
        highlights = [
            "✓ 91%+ of project cost covered by federal incentives",
            "✓ Multiple uncorrelated repayment sources",
            "✓ First lien position on $1.3M equipment",
            "✓ Experienced developer with successful track record",
            "✓ Essential infrastructure for affordable housing (EPB)",
        ]
        
        y_pos -= 0.04
        for highlight in highlights:
            ax.text(0.15, y_pos, highlight, fontsize=9)
            y_pos -= 0.025
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def create_cash_flow_waterfall_page(self, pdf):
        """Create cash flow waterfall visualization"""
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 11), 
                                       gridspec_kw={'height_ratios': [1, 1]})
        
        # Title
        fig.suptitle('CASH FLOW ANALYSIS', fontsize=14, fontweight='bold')
        
        # 1. Sources and Uses Waterfall
        ax1.set_title('Sources and Uses of Funds', fontsize=12)
        
        # Data for waterfall
        categories = ['Bridge\nLoan', 'Developer\nEquity', 'Total\nSources', 
                     'Equipment', 'Soft Costs', 'Total\nUses']
        values = [
            self.project_data['bridge_request'],
            200000,  # Developer equity
            self.project_data['bridge_request'] + 200000,
            -self.project_data['equipment_cost'],
            -self.project_data['soft_costs'],
            -(self.project_data['equipment_cost'] + self.project_data['soft_costs'])
        ]
        
        # Create waterfall
        cumulative = 0
        for i, (cat, val) in enumerate(zip(categories, values)):
            if i < 2:  # Sources
                ax1.bar(i, val/1000, color=self.colors['positive'], alpha=0.7)
                cumulative += val
            elif i == 2:  # Total sources
                ax1.bar(i, cumulative/1000, color=self.colors['primary'], alpha=0.7)
            else:  # Uses
                ax1.bar(i, val/1000, color=self.colors['negative'], alpha=0.7)
        
        ax1.set_xticks(range(len(categories)))
        ax1.set_xticklabels(categories)
        ax1.set_ylabel('Amount ($1000s)')
        ax1.axhline(y=0, color='black', linewidth=0.8)
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (cat, val) in enumerate(zip(categories, values)):
            if i == 2:
                label_val = cumulative/1000
            else:
                label_val = abs(val)/1000
            ax1.text(i, label_val + 20, f'${label_val:.0f}k', 
                    ha='center', va='bottom', fontsize=9)
        
        # 2. Repayment Timeline
        timeline = self.create_repayment_timeline()
        
        ax2.set_title('Loan Balance and Repayment Schedule', fontsize=12)
        
        # Plot balance over time
        ax2.plot(timeline['month'], timeline['balance']/1000, 'b-', linewidth=2, 
                label='Loan Balance')
        
        # Mark repayment events
        repayment_events = timeline[timeline['repayment'] > 0]
        for _, event in repayment_events.iterrows():
            ax2.scatter(event['month'], event['balance']/1000, 
                       s=100, c=self.colors['positive'], zorder=5)
            ax2.annotate(event['description'], 
                        (event['month'], event['balance']/1000),
                        xytext=(0, 20), textcoords='offset points',
                        ha='center', fontsize=8,
                        bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))
        
        ax2.fill_between(timeline['month'], 0, timeline['balance']/1000, 
                        alpha=0.3, color=self.colors['secondary'])
        ax2.set_xlabel('Month')
        ax2.set_ylabel('Outstanding Balance ($1000s)')
        ax2.set_xlim(-0.5, 12.5)
        ax2.set_ylim(0, max(timeline['balance']/1000) * 1.2)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def create_risk_analysis_page(self, pdf):
        """Create risk analysis and mitigation page"""
        
        fig = plt.figure(figsize=(8.5, 11))
        fig.suptitle('RISK ANALYSIS & MITIGATION', fontsize=14, fontweight='bold')
        
        # Create grid for risk matrix
        gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1], hspace=0.3)
        
        # Risk Matrix
        ax1 = fig.add_subplot(gs[0, :])
        
        # Risk data
        risks = [
            {'risk': 'Construction Delay', 'probability': 2, 'impact': 2, 
             'mitigation': 'Fixed-price contract, proven contractor'},
            {'risk': 'Incentive Timing', 'probability': 1, 'impact': 3, 
             'mitigation': 'Multiple sources, staggered timing'},
            {'risk': 'Tax Credit Price', 'probability': 2, 'impact': 2, 
             'mitigation': 'Conservative 95¢ pricing, strong market'},
            {'risk': 'Grant Approval', 'probability': 1, 'impact': 2, 
             'mitigation': 'EPB pre-qualified, strong application'},
        ]
        
        # Create risk matrix
        ax1.set_xlim(0, 4)
        ax1.set_ylim(0, 4)
        ax1.set_xlabel('Probability →', fontsize=10)
        ax1.set_ylabel('Impact →', fontsize=10)
        ax1.set_title('Risk Matrix', fontsize=12)
        
        # Add grid
        for i in range(1, 4):
            ax1.axhline(i, color='gray', alpha=0.3)
            ax1.axvline(i, color='gray', alpha=0.3)
        
        # Color zones
        # Low risk (green)
        ax1.fill_between([0, 2], 0, 2, alpha=0.2, color='green')
        # Medium risk (yellow)
        ax1.fill_between([2, 4], 0, 2, alpha=0.2, color='yellow')
        ax1.fill_between([0, 2], 2, 4, alpha=0.2, color='yellow')
        # High risk (red)
        ax1.fill_between([2, 4], 2, 4, alpha=0.2, color='red')
        
        # Plot risks
        for i, risk in enumerate(risks):
            ax1.scatter(risk['probability'], risk['impact'], s=200, 
                       c=self.colors['primary'], alpha=0.7)
            ax1.text(risk['probability'], risk['impact'], str(i+1), 
                    ha='center', va='center', color='white', fontweight='bold')
        
        # Risk descriptions
        ax2 = fig.add_subplot(gs[1:, :])
        ax2.axis('off')
        
        y_pos = 0.95
        ax2.text(0.5, y_pos, 'RISK MITIGATION STRATEGIES', 
                ha='center', fontsize=12, fontweight='bold')
        
        y_pos -= 0.08
        for i, risk in enumerate(risks):
            # Risk name
            ax2.text(0.05, y_pos, f"{i+1}. {risk['risk']}:", 
                    fontsize=10, fontweight='bold')
            y_pos -= 0.04
            
            # Mitigation
            ax2.text(0.1, y_pos, f"Mitigation: {risk['mitigation']}", 
                    fontsize=9, wrap=True)
            y_pos -= 0.06
        
        # Security Package
        y_pos -= 0.05
        security_box = patches.FancyBboxPatch((0.05, y_pos - 0.25), 0.9, 0.25,
                                            boxstyle="round,pad=0.02",
                                            facecolor='lightblue', alpha=0.3)
        ax2.add_patch(security_box)
        
        ax2.text(0.5, y_pos - 0.02, 'SECURITY PACKAGE', 
                ha='center', fontsize=12, fontweight='bold')
        
        y_pos -= 0.05
        security_items = [
            "• First lien position on all equipment ($1.3M value)",
            "• UCC-1 filing on all project assets",
            "• Assignment of all incentive payments",
            "• Personal guarantee from principals",
            "• Completion guarantee with 10% retainage",
            "• Assignment of Energy Service Agreements",
            "• Lockbox control on grant/rebate receipts"
        ]
        
        for item in security_items:
            ax2.text(0.1, y_pos, item, fontsize=9)
            y_pos -= 0.03
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def create_project_details_page(self, pdf):
        """Create project details and timeline page"""
        
        fig = plt.figure(figsize=(8.5, 11))
        fig.suptitle('PROJECT DETAILS & TIMELINE', fontsize=14, fontweight='bold')
        
        # Create subplots
        gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 1], hspace=0.3)
        
        # Project Overview
        ax1 = fig.add_subplot(gs[0])
        ax1.axis('off')
        
        y_pos = 0.9
        ax1.text(0.5, y_pos, 'PROJECT OVERVIEW', ha='center', fontsize=12, fontweight='bold')
        
        y_pos -= 0.15
        overview_text = [
            f"Building: {self.project_data['building_type']}",
            f"Location: {self.project_data['building_address']}",
            "Scope: Install 4-pipe water-source heat pump system with thermal energy storage",
            "Purpose: Achieve Energize Denver compliance while avoiding $270k upfront cost",
            "Model: Energy-as-a-Service with 20-year contract",
            "Environmental: 25% energy reduction, full electrification"
        ]
        
        for text in overview_text:
            ax1.text(0.1, y_pos, text, fontsize=10, wrap=True)
            y_pos -= 0.12
        
        # Timeline
        ax2 = fig.add_subplot(gs[1])
        ax2.axis('off')
        
        y_pos = 0.9
        ax2.text(0.5, y_pos, 'PROJECT TIMELINE', ha='center', fontsize=12, fontweight='bold')
        
        # Timeline items
        timeline_items = [
            ('Month -2', 'Close bridge loan facility'),
            ('Month 0', 'Execute agreements, begin construction'),
            ('Month 3', 'Receive DRCOG grant ($260k)'),
            ('Month 6', '50% construction complete'),
            ('Month 9', 'Commission system, receive Xcel rebate ($182k)'),
            ('Month 10', 'Close tax credit sale ($494k)'),
            ('Month 12', 'Sell depreciation, repay bridge loan'),
            ('Month 15', 'Stabilized operations')
        ]
        
        y_pos -= 0.1
        timeline_y = y_pos
        
        # Draw timeline line
        ax2.plot([0.1, 0.9], [timeline_y - 0.3, timeline_y - 0.3], 'k-', linewidth=2)
        
        # Add timeline points
        for i, (month, event) in enumerate(timeline_items):
            x_pos = 0.1 + (i / (len(timeline_items) - 1)) * 0.8
            
            # Draw point
            ax2.scatter(x_pos, timeline_y - 0.3, s=100, c=self.colors['primary'], zorder=5)
            
            # Add label
            if i % 2 == 0:
                label_y = timeline_y - 0.15
                va = 'bottom'
            else:
                label_y = timeline_y - 0.45
                va = 'top'
            
            ax2.text(x_pos, label_y, month, ha='center', va=va, fontsize=8, fontweight='bold')
            ax2.text(x_pos, label_y - 0.05 if va == 'bottom' else label_y + 0.05, 
                    event, ha='center', va=va, fontsize=7, wrap=True)
        
        # Financial Summary
        ax3 = fig.add_subplot(gs[2])
        ax3.axis('off')
        
        y_pos = 0.9
        ax3.text(0.5, y_pos, 'FINANCIAL SUMMARY', ha='center', fontsize=12, fontweight='bold')
        
        y_pos -= 0.1
        
        # Create table-like structure
        financial_data = [
            ['Total Project Cost:', f"${self.project_data['total_project_cost']:,.0f}"],
            ['Bridge Loan Amount:', f"${self.project_data['bridge_request']:,.0f}"],
            ['Interest Rate:', f"{self.project_data['interest_rate']:.0%} annual"],
            ['', ''],
            ['Take-out Sources:', ''],
            ['  Federal Tax Credit:', f"${self.project_data['itc_sale_price']:,.0f}"],
            ['  Depreciation Sale:', f"${self.project_data['depreciation_sale']:,.0f}"],
            ['  DRCOG Grant:', f"${self.project_data['drcog_grant']:,.0f}"],
            ['  Xcel Rebate:', f"${self.project_data['xcel_rebate']:,.0f}"],
            ['', ''],
            ['Total Take-out:', f"${self.calculate_coverage_ratios()['total_takeout']:,.0f}"],
            ['Coverage Ratio:', f"{self.calculate_coverage_ratios()['takeout_coverage']:.1f}x"],
        ]
        
        for label, value in financial_data:
            ax3.text(0.3, y_pos, label, fontsize=10)
            ax3.text(0.7, y_pos, value, fontsize=10, ha='right')
            y_pos -= 0.05
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def create_developer_track_record_page(self, pdf):
        """Create developer track record page"""
        
        fig = plt.figure(figsize=(8.5, 11))
        fig.suptitle('DEVELOPER TRACK RECORD', fontsize=14, fontweight='bold')
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        y_pos = 0.90
        
        # Developer info
        developer_box = patches.FancyBboxPatch((0.05, y_pos - 0.15), 0.9, 0.15,
                                             boxstyle="round,pad=0.02",
                                             facecolor='lightgray', alpha=0.3)
        ax.add_patch(developer_box)
        
        ax.text(0.5, y_pos - 0.02, self.project_data['developer'], 
               ha='center', fontsize=12, fontweight='bold')
        
        y_pos -= 0.05
        developer_info = [
            "Founded: 2023 | Focus: Thermal energy infrastructure for multifamily buildings",
            "Leadership: 20+ years combined experience in energy efficiency and real estate",
            "Mission: Decarbonize affordable housing without resident displacement"
        ]
        
        for info in developer_info:
            ax.text(0.5, y_pos, info, ha='center', fontsize=9)
            y_pos -= 0.03
        
        # Previous projects
        y_pos -= 0.08
        ax.text(0.5, y_pos, 'COMPARABLE PROJECT EXPERIENCE', 
               ha='center', fontsize=12, fontweight='bold')
        
        y_pos -= 0.05
        
        # Project examples (hypothetical)
        projects = [
            {
                'name': 'Aurora Apartments Heat Pump Retrofit',
                'size': '84 units',
                'completion': '2023',
                'performance': 'On time, 15% under budget'
            },
            {
                'name': 'Downtown Denver Office HVAC Upgrade',
                'size': '125,000 sq ft',
                'completion': '2022',
                'performance': '30% energy reduction achieved'
            },
            {
                'name': 'Boulder Student Housing Electrification',
                'size': '200 beds',
                'completion': '2023',
                'performance': 'All incentives captured successfully'
            }
        ]
        
        for project in projects:
            project_box = patches.FancyBboxPatch((0.1, y_pos - 0.08), 0.8, 0.08,
                                               boxstyle="round,pad=0.01",
                                               facecolor='lightgreen', alpha=0.2)
            ax.add_patch(project_box)
            
            ax.text(0.15, y_pos - 0.02, project['name'], fontsize=10, fontweight='bold')
            ax.text(0.15, y_pos - 0.04, f"Size: {project['size']} | Completed: {project['completion']}", 
                   fontsize=9)
            ax.text(0.15, y_pos - 0.06, f"Result: {project['performance']}", fontsize=9)
            
            y_pos -= 0.10
        
        # Key relationships
        y_pos -= 0.05
        ax.text(0.5, y_pos, 'KEY RELATIONSHIPS', ha='center', fontsize=12, fontweight='bold')
        
        y_pos -= 0.05
        relationships = [
            "• Xcel Energy: Registered Trade Partner for Clean Heat Program",
            "• DRCOG: Pre-qualified contractor for CPRG grants",
            "• Engineering: Partnership with leading MEP firm",
            "• Tax Credits: Established relationship with national syndicator",
            "• Equipment: Direct dealer agreements with major manufacturers"
        ]
        
        for relationship in relationships:
            ax.text(0.1, y_pos, relationship, fontsize=9)
            y_pos -= 0.03
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def generate_complete_package(self, output_path: str = None):
        """Generate complete bridge loan package as PDF"""
        
        if output_path is None:
            output_path = f"/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/bridge_loan_package_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        with PdfPages(output_path) as pdf:
            # Generate all pages
            self.create_executive_summary_page(pdf)
            self.create_cash_flow_waterfall_page(pdf)
            self.create_risk_analysis_page(pdf)
            self.create_project_details_page(pdf)
            self.create_developer_track_record_page(pdf)
            
            # Add metadata
            d = pdf.infodict()
            d['Title'] = f'Bridge Loan Package - {self.project_data["project_name"]}'
            d['Author'] = self.project_data['developer']
            d['Subject'] = 'Bridge Loan Investment Opportunity'
            d['Keywords'] = 'Bridge Loan, Energy Efficiency, Tax Credits'
            d['CreationDate'] = datetime.now()
        
        print(f"Bridge loan package generated: {output_path}")
        
        return output_path
    
    def generate_term_sheet(self) -> Dict:
        """Generate bridge loan term sheet"""
        
        coverage = self.calculate_coverage_ratios()
        
        term_sheet = {
            'date': datetime.now().strftime('%B %d, %Y'),
            'borrower': self.project_data['developer'],
            'project': self.project_data['project_name'],
            'loan_amount': self.project_data['bridge_request'],
            'use_of_proceeds': 'Finance construction of energy efficiency improvements',
            'interest_rate': f"{self.project_data['interest_rate']:.0%} per annum",
            'default_rate': f"{self.project_data['interest_rate'] + 0.05:.0%} per annum",
            'term': f"{self.project_data['term_months']} months",
            'origination_fee': f"{self.project_data['origination_fee'] / self.project_data['bridge_request']:.0%} of loan amount",
            'payment_terms': 'Interest accrues monthly, all principal and interest due at maturity',
            'prepayment': 'Permitted without penalty',
            'security': [
                'First priority security interest in all equipment',
                'Assignment of all incentive payments and rebates',
                'Personal guarantee from principals',
                'Completion guarantee'
            ],
            'financial_covenants': [
                f'Maintain take-out coverage ratio of at least {coverage["takeout_coverage"] * 0.8:.1f}x',
                'No additional debt without lender consent',
                'Monthly progress reports during construction'
            ],
            'conditions_precedent': [
                'Executed construction contract',
                'Evidence of all permits',
                'Executed Energy Service Agreement',
                'Evidence of incentive pre-approvals',
                'Title insurance on equipment',
                'Satisfactory background checks'
            ],
            'events_of_default': [
                'Failure to pay principal or interest when due',
                'Material breach of representations or warranties',
                'Failure to complete construction within 12 months',
                'Loss of any material incentive eligibility'
            ],
            'governing_law': 'Colorado',
            'exclusive_negotiation': '30 days from acceptance'
        }
        
        return term_sheet


# Example usage
if __name__ == "__main__":
    # Create package generator
    package_gen = BridgeLoanInvestorPackage()
    
    # Generate complete PDF package
    pdf_path = package_gen.generate_complete_package()
    
    # Generate term sheet
    term_sheet = package_gen.generate_term_sheet()
    
    # Print term sheet summary
    print("\nBRIDGE LOAN TERM SHEET")
    print("=" * 50)
    print(f"Date: {term_sheet['date']}")
    print(f"Borrower: {term_sheet['borrower']}")
    print(f"Project: {term_sheet['project']}")
    print(f"Loan Amount: ${term_sheet['loan_amount']:,.0f}")
    print(f"Interest Rate: {term_sheet['interest_rate']}")
    print(f"Term: {term_sheet['term']}")
    
    print("\nSECURITY:")
    for item in term_sheet['security']:
        print(f"  • {item}")
    
    print("\nKEY METRICS:")
    coverage = package_gen.calculate_coverage_ratios()
    print(f"  Take-out Coverage: {coverage['takeout_coverage']:.1f}x")
    print(f"  Total Interest: ${coverage['total_interest']:,.0f}")
    print(f"  Total Repayment: ${coverage['total_repayment']:,.0f}")