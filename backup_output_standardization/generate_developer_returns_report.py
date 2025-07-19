"""
Suggested File Name: generate_developer_returns_report.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Generate comprehensive developer returns analysis report in multiple formats (PDF, HTML, Markdown)

This script creates a detailed developer returns analysis including:
- Project economics breakdown
- Multiple profit centers analysis
- Exit strategy scenarios
- Cash flow timeline
- Risk analysis
- Investment highlights
"""

import sys
import os
from datetime import datetime
import json
from typing import Dict, List

# Add the src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Import modules
from config import get_config, update_config
from models.tes_hp_cash_flow_bridge import TESHPCashFlowBridge
from analysis.integrated_tes_hp_analyzer import IntegratedTESHPAnalyzer

# For PDF generation (optional)
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Note: reportlab not installed. PDF generation will be skipped.")

class DeveloperReturnsReportGenerator:
    """Generate comprehensive developer returns analysis reports"""
    
    def __init__(self, building_id: str = '2952'):
        """Initialize with building data"""
        self.config = get_config()
        self.building_id = building_id
        
        # Initialize analyzers
        self.integrated_analyzer = IntegratedTESHPAnalyzer()
        cf_config = self.config.get_config_for_modules()['cash_flow']
        self.cash_flow_analyzer = TESHPCashFlowBridge(cf_config)
        
        # Run analyses
        self.executive_summary = self.integrated_analyzer.generate_executive_summary()
        self.cash_flows = self.cash_flow_analyzer.model_cash_flows()
        self.cf_summary = self.cash_flow_analyzer.generate_summary_report()
        
        # Calculate additional metrics
        self.project_costs = self.config.calculate_project_costs()
        self.incentives = self.config.calculate_incentives(self.project_costs)
        self.developer_returns = self._calculate_detailed_developer_returns()
        
        # Calculate bridge loan coverage ratio
        if 'security' in self.cf_summary.get('bridge_loan', {}):
            security = self.cf_summary['bridge_loan']['security']
            total_takeout = security['tax_credits'] + security['grants_rebates']
            self.bridge_coverage_ratio = total_takeout / self.cf_summary['bridge_loan']['maximum_draw'] if self.cf_summary['bridge_loan']['maximum_draw'] > 0 else 0
        else:
            self.bridge_coverage_ratio = 0
        
    def _calculate_detailed_developer_returns(self) -> Dict:
        """Calculate comprehensive developer returns with all revenue streams"""
        
        # Get base calculations
        economics = self.integrated_analyzer.calculate_project_economics('4pipe_wshp_tes')
        base_returns = self.integrated_analyzer.calculate_developer_returns(economics)
        cf_returns = self.cash_flow_analyzer.calculate_developer_returns()
        
        # Development phase profits
        developer_fee = self.project_costs['developer_fee']
        tc_broker_spread = self.incentives['tc_broker_spread']
        rebate_origination = self.incentives['rebate_origination_fee']
        
        # Depreciation monetization
        depreciation_tax_value = self.incentives['depreciation_tax_value']
        depreciation_sale = self.incentives['depreciation_proceeds']
        depreciation_spread = depreciation_tax_value * 0.15  # 15% spread on sale
        
        # Total development profits
        total_dev_profits = (developer_fee + tc_broker_spread + 
                           rebate_origination + depreciation_spread)
        
        # Stabilized value calculations
        annual_noi = self.config.config['financial']['annual_noi']
        
        # Exit scenarios
        exit_scenarios = {
            'immediate_sale': {
                'timing': 'Month 15',
                'conservative': {
                    'cap_rate': 0.10,
                    'value': annual_noi / 0.10,
                    'proceeds': annual_noi / 0.10 + total_dev_profits
                },
                'market': {
                    'cap_rate': 0.08,
                    'value': annual_noi / 0.08,
                    'proceeds': annual_noi / 0.08 + total_dev_profits
                },
                'aggressive': {
                    'cap_rate': 0.06,
                    'value': annual_noi / 0.06,
                    'proceeds': annual_noi / 0.06 + total_dev_profits
                }
            },
            'five_year_hold': {
                'timing': 'Year 5',
                'noi_growth': [],
                'cumulative_noi': 0,
                'year5_noi': 0,
                'sale_value': 0,
                'total_proceeds': 0
            },
            'perpetual_hold': {
                'timing': '20-Year NPV',
                'npv_cashflows': 0,
                'terminal_value': 0,
                'total_value': 0
            }
        }
        
        # Calculate 5-year hold scenario
        growth_rate = self.config.config['financial']['annual_escalation']
        for year in range(1, 6):
            year_noi = annual_noi * ((1 + growth_rate) ** (year - 1))
            exit_scenarios['five_year_hold']['noi_growth'].append(year_noi)
            exit_scenarios['five_year_hold']['cumulative_noi'] += year_noi
        
        exit_scenarios['five_year_hold']['year5_noi'] = annual_noi * ((1 + growth_rate) ** 4)
        exit_scenarios['five_year_hold']['sale_value'] = exit_scenarios['five_year_hold']['year5_noi'] / 0.08
        exit_scenarios['five_year_hold']['total_proceeds'] = (
            total_dev_profits + 
            exit_scenarios['five_year_hold']['cumulative_noi'] +
            exit_scenarios['five_year_hold']['sale_value']
        )
        
        # Calculate perpetual hold (20-year NPV)
        discount_rate = 0.08
        npv_sum = 0
        for year in range(1, 21):
            year_noi = annual_noi * ((1 + growth_rate) ** (year - 1))
            pv = year_noi / ((1 + discount_rate) ** year)
            npv_sum += pv
        
        # Terminal value at year 20
        year20_noi = annual_noi * ((1 + growth_rate) ** 19)
        terminal_value = year20_noi / (discount_rate - growth_rate)  # Gordon growth
        terminal_pv = terminal_value / ((1 + discount_rate) ** 20)
        
        exit_scenarios['perpetual_hold']['npv_cashflows'] = npv_sum
        exit_scenarios['perpetual_hold']['terminal_value'] = terminal_pv
        exit_scenarios['perpetual_hold']['total_value'] = npv_sum + terminal_pv + total_dev_profits
        
        # Developer equity requirement
        developer_equity = self.config.config['financial']['developer_equity']
        
        return {
            'developer_fee': developer_fee,
            'tc_broker_spread': tc_broker_spread,
            'rebate_origination': rebate_origination,
            'depreciation_spread': depreciation_spread,
            'total_development_profits': total_dev_profits,
            'developer_equity': developer_equity,
            'annual_noi': annual_noi,
            'exit_scenarios': exit_scenarios,
            'return_metrics': {
                'development_only': {
                    'profit': total_dev_profits,
                    'roe': total_dev_profits / developer_equity,
                    'irr': (total_dev_profits / developer_equity) ** (12/15) - 1
                },
                'with_market_sale': {
                    'profit': exit_scenarios['immediate_sale']['market']['proceeds'] - developer_equity,
                    'roe': (exit_scenarios['immediate_sale']['market']['proceeds'] - developer_equity) / developer_equity,
                    'irr': ((exit_scenarios['immediate_sale']['market']['proceeds'] / developer_equity) ** (12/15)) - 1
                },
                'five_year_hold': {
                    'profit': exit_scenarios['five_year_hold']['total_proceeds'] - developer_equity,
                    'roe': (exit_scenarios['five_year_hold']['total_proceeds'] - developer_equity) / developer_equity,
                    'irr': ((exit_scenarios['five_year_hold']['total_proceeds'] / developer_equity) ** (1/5)) - 1
                }
            }
        }
    
    def generate_markdown_report(self) -> str:
        """Generate markdown formatted report"""
        
        building = self.config.config['building']
        financial = self.config.config['financial']
        returns = self.developer_returns
        
        # Calculate bridge loan coverage ratio if not already calculated
        bridge_coverage_ratio = getattr(self, 'bridge_coverage_ratio', 0)
        if bridge_coverage_ratio == 0 and 'security' in self.cf_summary.get('bridge_loan', {}):
            security = self.cf_summary['bridge_loan']['security']
            total_takeout = security['tax_credits'] + security['grants_rebates']
            bridge_coverage_ratio = total_takeout / self.cf_summary['bridge_loan']['maximum_draw'] if self.cf_summary['bridge_loan']['maximum_draw'] > 0 else 0
        
        report = f"""# TES+HP Developer Returns Analysis
## Building {building['building_id']} - {building['building_name']}

---

## Executive Summary

The 4-Pipe WSHP + TES retrofit project for {building['building_name']} presents an exceptional investment opportunity with **{returns['return_metrics']['development_only']['roe']:.0%} return on equity** from development profits alone. With a market-rate exit, returns increase to **{returns['return_metrics']['with_market_sale']['roe']:.0%}**.

---

## Project Overview

**Building Details:**
- Name: {building['building_name']}
- Address: {building['address']}
- Type: {building['property_type']}
- Units: {building['units']}
- Square Footage: {building['sqft']:,}
- EPB Status: {'Yes' if building['is_epb'] else 'No'}
- Current EUI: {building['weather_norm_eui']}
- Equipment Replacement Need: ${building['equipment_replacement_cost']:,.0f}

**Proposed System:**
- 4-Pipe Water Source Heat Pump + Thermal Energy Storage
- {int(self.config.config['systems']['4pipe_wshp_tes']['eui_reduction_pct'] * 100)}% EUI reduction capability
- Full building electrification
- 20-year Energy-as-a-Service contract

---

## Project Economics

### Total Project Costs
| Component | Amount | % of Total |
|-----------|--------|------------|
| Equipment Base Cost | ${self.project_costs['base_equipment']:,.0f} | {self.project_costs['base_equipment']/self.project_costs['total_project_cost']:.1%} |
| Market Escalation (30%) | ${self.project_costs['escalated_equipment'] - self.project_costs['base_equipment']:,.0f} | {(self.project_costs['escalated_equipment'] - self.project_costs['base_equipment'])/self.project_costs['total_project_cost']:.1%} |
| Soft Costs | ${self.project_costs['soft_costs']:,.0f} | {self.project_costs['soft_costs']/self.project_costs['total_project_cost']:.1%} |
| Developer Fee | ${self.project_costs['developer_fee']:,.0f} | {self.project_costs['developer_fee']/self.project_costs['total_project_cost']:.1%} |
| Contingency | ${self.project_costs['contingency']:,.0f} | {self.project_costs['contingency']/self.project_costs['total_project_cost']:.1%} |
| **TOTAL PROJECT COST** | **${self.project_costs['total_project_cost']:,.0f}** | **100%** |

### Incentive Stack
| Incentive Source | Amount | Coverage |
|-----------------|--------|----------|
| Federal ITC ({int(financial['itc_rate']*100)}%) | ${self.incentives['itc_amount']:,.0f} | {self.incentives['itc_amount']/self.project_costs['total_project_cost']:.1%} |
| ITC Sale Proceeds | ${self.incentives['itc_proceeds']:,.0f} | {self.incentives['itc_proceeds']/self.project_costs['total_project_cost']:.1%} |
| Depreciation Value | ${self.incentives['depreciation_tax_value']:,.0f} | {self.incentives['depreciation_tax_value']/self.project_costs['total_project_cost']:.1%} |
| Depreciation Sale | ${self.incentives['depreciation_proceeds']:,.0f} | {self.incentives['depreciation_proceeds']/self.project_costs['total_project_cost']:.1%} |
| DRCOG Grant | ${self.incentives['drcog_grant']:,.0f} | {self.incentives['drcog_grant']/self.project_costs['total_project_cost']:.1%} |
| Xcel Rebate | ${self.incentives['xcel_rebate']:,.0f} | {self.incentives['xcel_rebate']/self.project_costs['total_project_cost']:.1%} |
| **TOTAL INCENTIVES** | **${self.incentives['total_incentives']:,.0f}** | **{self.incentives['incentive_coverage']:.1%}** |

**Net Project Cost After Incentives:** ${self.incentives['net_project_cost']:,.0f}

---

## Developer Profit Centers

### 1. Development Phase Profits (Months 0-12)

**A. Developer Fee**
- Base: {int(financial['developer_fee_pct']*100)}% of hard costs = ${returns['developer_fee']:,.0f}
- Timing: 25% at start, 50% mid-construction, 25% at completion
- Risk: Low (contractual)

**B. Tax Credit Brokerage**
- ITC Amount: ${self.incentives['itc_amount']:,.0f}
- Sale at {int(financial['tax_credit_sale_rate']*100)}¢ = ${self.incentives['itc_proceeds']:,.0f}
- Broker Spread: **${returns['tc_broker_spread']:,.0f}**
- Timing: Month 12 (commercial operation)

**C. Rebate Origination**
- Total Rebates: ${self.incentives['drcog_grant'] + self.incentives['xcel_rebate']:,.0f}
- Origination Fee ({financial['rebate_origination_fee']:.1%}): **${returns['rebate_origination']:,.0f}**
- Timing: Months 6 & 12

**D. Depreciation Monetization**
- Tax Value: ${self.incentives['depreciation_tax_value']:,.0f}
- Sale at {int(financial['depreciation_sale_discount']*100)}%: ${self.incentives['depreciation_proceeds']:,.0f}
- Developer Spread: **${returns['depreciation_spread']:,.0f}**

**Total Development Phase Profit: ${returns['total_development_profits']:,.0f}**

### 2. Stabilized Operations Income

**Annual Cash Flows:**
- Service Revenue: ${financial['annual_service_revenue']:,.0f}
- Operating Margin: {int(financial['operating_margin']*100)}%
- Annual NOI: **${returns['annual_noi']:,.0f}**
- Asset Management Fee ({int(financial['asset_mgmt_fee_pct']*100)}%): **${financial['annual_service_revenue'] * financial['asset_mgmt_fee_pct']:,.0f}/year**

### 3. Exit Value Scenarios

**A. Immediate Sale (Month 15)**
| Cap Rate | Asset Value | Total Proceeds* |
|----------|-------------|-----------------|
| 10% (Conservative) | ${returns['exit_scenarios']['immediate_sale']['conservative']['value']:,.0f} | ${returns['exit_scenarios']['immediate_sale']['conservative']['proceeds']:,.0f} |
| 8% (Market) | ${returns['exit_scenarios']['immediate_sale']['market']['value']:,.0f} | ${returns['exit_scenarios']['immediate_sale']['market']['proceeds']:,.0f} |
| 6% (Aggressive) | ${returns['exit_scenarios']['immediate_sale']['aggressive']['value']:,.0f} | ${returns['exit_scenarios']['immediate_sale']['aggressive']['proceeds']:,.0f} |

*Includes development profits + asset sale

**B. Hold 5 Years Then Sell**
- Cumulative NOI (Years 1-5): ${returns['exit_scenarios']['five_year_hold']['cumulative_noi']:,.0f}
- Year 5 NOI: ${returns['exit_scenarios']['five_year_hold']['year5_noi']:,.0f}
- Sale at 8% cap: ${returns['exit_scenarios']['five_year_hold']['sale_value']:,.0f}
- **Total 5-Year Proceeds: ${returns['exit_scenarios']['five_year_hold']['total_proceeds']:,.0f}**

**C. Perpetual Hold (20-Year NPV)**
- PV of 20-year cash flows: ${returns['exit_scenarios']['perpetual_hold']['npv_cashflows']:,.0f}
- PV of terminal value: ${returns['exit_scenarios']['perpetual_hold']['terminal_value']:,.0f}
- **Total NPV: ${returns['exit_scenarios']['perpetual_hold']['total_value']:,.0f}**

---

## Return Analysis

### Developer Equity Investment
- Pre-development costs: ${returns['developer_equity'] * 0.4:,.0f}
- Working capital: ${returns['developer_equity'] * 0.3:,.0f}
- Contingency reserve: ${returns['developer_equity'] * 0.3:,.0f}
- **Total Equity: ${returns['developer_equity']:,.0f}**

### Return Metrics
| Exit Strategy | Net Profit | ROE | IRR |
|--------------|------------|-----|-----|
| Development Only | ${returns['return_metrics']['development_only']['profit']:,.0f} | {returns['return_metrics']['development_only']['roe']:.0%} | {returns['return_metrics']['development_only']['irr']:.0%} |
| With Market Sale | ${returns['return_metrics']['with_market_sale']['profit']:,.0f} | {returns['return_metrics']['with_market_sale']['roe']:.0%} | {returns['return_metrics']['with_market_sale']['irr']:.0%} |
| 5-Year Hold | ${returns['return_metrics']['five_year_hold']['profit']:,.0f} | {returns['return_metrics']['five_year_hold']['roe']:.0%} | {returns['return_metrics']['five_year_hold']['irr']:.0%} |

---

## Cash Flow Timeline

### Pre-Construction (Months -6 to 0)
- Developer Equity In: -${returns['developer_equity']:,.0f}
- Development Activities: Engineering, permitting, sales

### Construction (Months 0-9)
- Bridge Loan Draws: ${self.cf_summary['bridge_loan']['maximum_draw']:,.0f}
- Developer Fee Receipts: +${returns['developer_fee']:,.0f}
- DRCOG Grant: +${self.incentives['drcog_grant']:,.0f}

### Commissioning (Months 9-12)
- Xcel Rebate: +${self.incentives['xcel_rebate']:,.0f}
- Tax Credit Sale: +${self.incentives['itc_proceeds']:,.0f}
- Bridge Loan Payoff: -${self.cf_summary['bridge_loan']['maximum_draw']:,.0f}

### Stabilized Operations (Month 12+)
- Monthly NOI: ${returns['annual_noi']/12:,.0f}
- Annual NOI: ${returns['annual_noi']:,.0f}
- Depreciation Sale: +${self.incentives['depreciation_proceeds']:,.0f}

---

## Risk Mitigation

### Secured Takeout Sources
1. **Tax Credits**: Pre-sold to institutional buyer
2. **Grants**: Government commitment letters
3. **Equipment**: First lien position
4. **Contract**: 20-year take-or-pay agreement

### Coverage Ratios
- Incentive Coverage: {self.incentives['incentive_coverage']:.0%}
- Bridge Loan Coverage: {bridge_coverage_ratio:.1f}x
- Debt Service Coverage: {returns['annual_noi']/(self.incentives['net_project_cost']*0.08):.1f}x

---

## Investment Highlights

✅ **Exceptional Returns**: {returns['return_metrics']['development_only']['roe']:.0%}-{returns['return_metrics']['with_market_sale']['roe']:.0%} ROE

✅ **Multiple Revenue Streams**: Development, brokerage, management, exit

✅ **Social Impact**: Preserving affordable EPB housing

✅ **Risk Mitigation**: {self.incentives['incentive_coverage']:.0%} incentive coverage

✅ **Scalability**: 1,700+ buildings in Denver need retrofits

✅ **Policy Alignment**: Full compliance with Energize Denver

---

## Recommendation

**STRONG BUY** - Exceptional risk-adjusted returns with meaningful impact

---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report
    
    def generate_html_report(self) -> str:
        """Generate HTML formatted report with styling"""
        
        markdown_content = self.generate_markdown_report()
        
        # Convert markdown to HTML (basic conversion)
        html_content = markdown_content.replace('\n', '<br>\n')
        html_content = html_content.replace('# ', '<h1>')
        html_content = html_content.replace('## ', '<h2>')
        html_content = html_content.replace('### ', '<h3>')
        html_content = html_content.replace('**', '<strong>')
        html_content = html_content.replace('✅', '✔️')
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Developer Returns Analysis - Building {self.building_id}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        table, th, td {{
            border: 1px solid #ddd;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .highlight {{
            background-color: #ffffcc;
        }}
        .metric {{
            font-size: 24px;
            font-weight: bold;
            color: #27ae60;
        }}
        hr {{
            margin: 30px 0;
            border: 0;
            border-top: 2px solid #eee;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""
        
        return html_template
    
    def generate_pdf_report(self, output_path: str):
        """Generate PDF report (requires reportlab)"""
        
        if not REPORTLAB_AVAILABLE:
            print("PDF generation skipped - reportlab not installed")
            print("Install with: pip install reportlab")
            return None
        
        # This would require significant formatting work
        # For now, recommend using the HTML report and printing to PDF
        print("PDF generation not fully implemented.")
        print("Recommend using HTML report and printing to PDF from browser.")
        
        return None
    
    def save_all_reports(self, output_dir: str = None):
        """Save reports in all formats"""
        
        if output_dir is None:
            output_dir = os.path.join(project_root, 'outputs', 'developer_reports')
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"developer_returns_{self.building_id}_{timestamp}"
        
        # Save markdown
        md_path = os.path.join(output_dir, f"{base_name}.md")
        with open(md_path, 'w') as f:
            f.write(self.generate_markdown_report())
        print(f"✓ Markdown report saved to: {md_path}")
        
        # Save HTML
        html_path = os.path.join(output_dir, f"{base_name}.html")
        with open(html_path, 'w') as f:
            f.write(self.generate_html_report())
        print(f"✓ HTML report saved to: {html_path}")
        
        # Save JSON data
        json_data = {
            'generated': datetime.now().isoformat(),
            'building_id': self.building_id,
            'project_costs': self.project_costs,
            'incentives': self.incentives,
            'developer_returns': self.developer_returns,
            'cash_flow_summary': self.cf_summary,
            'executive_summary': self.executive_summary
        }
        
        json_path = os.path.join(output_dir, f"{base_name}_data.json")
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        print(f"✓ JSON data saved to: {json_path}")
        
        # Try PDF if available
        if REPORTLAB_AVAILABLE:
            pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
            self.generate_pdf_report(pdf_path)
        
        return {
            'markdown': md_path,
            'html': html_path,
            'json': json_path
        }


def main():
    """Generate developer returns report"""
    
    print("="*80)
    print("TES+HP DEVELOPER RETURNS REPORT GENERATOR")
    print("="*80)
    
    # Create report generator
    generator = DeveloperReturnsReportGenerator('2952')
    
    # Display key metrics
    returns = generator.developer_returns
    print(f"\nBuilding: {generator.config.config['building']['building_name']}")
    print(f"Total Project Cost: ${generator.project_costs['total_project_cost']:,.0f}")
    print(f"Incentive Coverage: {generator.incentives['incentive_coverage']:.1%}")
    print(f"Developer Equity: ${returns['developer_equity']:,.0f}")
    print(f"Development Profits: ${returns['total_development_profits']:,.0f}")
    print(f"ROE (Dev Only): {returns['return_metrics']['development_only']['roe']:.0%}")
    print(f"ROE (With Sale): {returns['return_metrics']['with_market_sale']['roe']:.0%}")
    
    # Save all reports
    print("\nGenerating reports...")
    paths = generator.save_all_reports()
    
    print("\n✅ All reports generated successfully!")
    print("\nOpen the HTML report in a browser for the best viewing experience:")
    print(f"file://{paths['html']}")


if __name__ == "__main__":
    main()
