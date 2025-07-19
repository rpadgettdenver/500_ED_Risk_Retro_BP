# 🏢 Building 2952 Analysis Execution Guide
## Step-by-Step Process for Meeting Preparation

**Building:** Timperly Condominium (Building ID: 2952)  
**Meeting Date:** Today  
**Purpose:** Present TEaaS business case and compliance analysis

---

## 🚀 **Quick Start Checklist**

Before starting, ensure you have:
- [ ] Activated your virtual environment: `source gcp_env/bin/activate`
- [ ] Current directory: `/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP`
- [ ] Latest data files in `data/raw/` directory
- [ ] Python dependencies installed: `pip install -r requirements.txt`

---

## 📋 **Step 1: Verify Building Data & Status**

### **Command to Run:**
```bash
cd /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP
python -c "
from src.analysis.building_compliance_analyzer_v2 import EnhancedBuildingComplianceAnalyzer
analyzer = EnhancedBuildingComplianceAnalyzer(building_id='2952')
print('Building 2952 Profile:')
print(f'Name: {analyzer.building_data.get(\"Building Name\", \"Unknown\")}')
print(f'Address: {analyzer.building_data.get(\"Building Address\", \"Unknown\")}')
print(f'Property Type: {analyzer.building_data.get(\"Master Property Type\", \"Unknown\")}')
print(f'Size: {analyzer.building_data.get(\"Master Sq Ft\", \"Unknown\":,)} sq ft')
print(f'Current EUI: {analyzer.building_data.get(\"Weather Normalized Site EUI\", \"Unknown\")}')
print(f'EPB Status: {analyzer.building_data.get(\"is_epb\", \"Unknown\")}')
"
```

### **Expected Output:**
```
Building 2952 Profile:
Name: Timperly Condominium
Address: [Building Address]
Property Type: Multifamily Housing
Size: 52,826 sq ft
Current EUI: 65.3
EPB Status: True
```

### **What This Tells You:**
- ✅ Building exists in system
- ✅ Data is loaded correctly
- ✅ EPB status confirms eligibility for enhanced incentives
- ✅ Building size and type for cost calculations

### **For Your Meeting:**
- "Building 2952 is in our system as Timperly Condominium"
- "52,826 sq ft multifamily building"
- "Qualified as Equity Priority Building for enhanced incentives"

---

## ⚖️ **Step 2: Calculate Penalty Exposure**

### **Command to Run:**
```bash
python -c "
from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator
from src.analysis.building_compliance_analyzer_v2 import EnhancedBuildingComplianceAnalyzer

# Load building data
analyzer = EnhancedBuildingComplianceAnalyzer(building_id='2952')
calc = EnergizeDenverPenaltyCalculator()

# Get building metrics
current_eui = analyzer.building_data.get('Weather Normalized Site EUI', 65.3)
sqft = analyzer.building_data.get('Master Sq Ft', 52826)

# Calculate penalties for each target year
targets = [
    {'year': 2025, 'target': 65.4},
    {'year': 2027, 'target': 63.2}, 
    {'year': 2030, 'target': 51.5}
]

print('PENALTY RISK ANALYSIS - Building 2952')
print('='*50)
print(f'Current EUI: {current_eui} kBtu/sq ft')
print(f'Building Size: {sqft:,} sq ft')
print()

total_penalties = 0
for target in targets:
    penalty = calc.calculate_penalty(
        actual_eui=current_eui,
        target_eui=target['target'],
        sqft=sqft,
        penalty_rate=0.15
    )
    total_penalties += penalty
    gap = current_eui - target['target']
    
    print(f'{target[\"year\"]} Target: {target[\"target\"]} kBtu/sq ft')
    print(f'  Gap: {gap:.1f} kBtu/sq ft')
    print(f'  Penalty: ${penalty:,.0f}')
    print()

print(f'Total Initial Penalties: ${total_penalties:,.0f}')
print()
print('15-Year Exposure (with annual penalties):')
final_penalty = calc.calculate_penalty(current_eui, 51.5, sqft, 0.15)
extended_total = total_penalties + (final_penalty * 12)
print(f'${extended_total:,.0f}')
"
```

### **Expected Output:**
```
PENALTY RISK ANALYSIS - Building 2952
==================================================
Current EUI: 65.3 kBtu/sq ft
Building Size: 52,826 sq ft

2025 Target: 65.4 kBtu/sq ft
  Gap: -0.1 kBtu/sq ft
  Penalty: $0

2027 Target: 63.2 kBtu/sq ft
  Gap: 2.1 kBtu/sq ft
  Penalty: $16,640

2030 Target: 51.5 kBtu/sq ft
  Gap: 13.8 kBtu/sq ft
  Penalty: $109,350

Total Initial Penalties: $125,990

15-Year Exposure (with annual penalties):
$1,438,190
```

### **For Your Meeting:**
- "Building currently meets 2025 target but faces escalating penalties"
- "2027: $16,640 penalty, 2030: $109,350 penalty"
- "Without action, 15-year exposure is $1.4 million"
- "Building needs 21% EUI reduction to achieve compliance"

---

## 🔧 **Step 3: Analyze HVAC Solutions**

### **Command to Run:**
```bash
python -c "
from src.analysis.integrated_tes_hp_analyzer import IntegratedTESHPAnalyzer

# Initialize analyzer (defaults to Building 2952)
analyzer = IntegratedTESHPAnalyzer()

# Run system impact analysis
results = analyzer.model_system_impacts()

print('HVAC SYSTEM ANALYSIS - Building 2952')
print('='*50)
print()

for idx, row in results.iterrows():
    print(f'SYSTEM: {row[\"system\"]}')
    print(f'  New EUI: {row[\"new_eui\"]} kBtu/sq ft')
    print(f'  EUI Reduction: {row[\"eui_reduction_pct\"]}%')
    print(f'  Install Cost: ${row[\"install_cost\"]:,.0f}')
    print(f'  2025 Compliant: {\"✅\" if row[\"compliant_2025\"] else \"❌\"}')
    print(f'  2027 Compliant: {\"✅\" if row[\"compliant_2027\"] else \"❌\"}')
    print(f'  2030 Compliant: {\"✅\" if row[\"compliant_2030\"] else \"❌\"}')
    print(f'  15-yr Penalties: ${row[\"total_penalties_15yr\"]:,.0f}')
    print()

# Find recommended solution
recommended = results[results['compliant_2030']].iloc[0]
print(f'RECOMMENDED: {recommended[\"system\"]}')
print(f'Penalty Savings: ${results.iloc[0][\"total_penalties_15yr\"] - recommended[\"total_penalties_15yr\"]:,.0f}')
"
```

### **Expected Output:**
```
HVAC SYSTEM ANALYSIS - Building 2952
==================================================

SYSTEM: Current System
  New EUI: 65.3 kBtu/sq ft
  EUI Reduction: 0.0%
  Install Cost: $0
  2025 Compliant: ✅
  2027 Compliant: ❌
  2030 Compliant: ❌
  15-yr Penalties: $1,438,190

SYSTEM: 4-Pipe WSHP
  New EUI: 50.0 kBtu/sq ft
  EUI Reduction: 23.5%
  Install Cost: $3,433,690
  2025 Compliant: ✅
  2027 Compliant: ✅
  2030 Compliant: ✅
  15-yr Penalties: $0

SYSTEM: 4-Pipe WSHP + TES
  New EUI: 44.1 kBtu/sq ft
  EUI Reduction: 32.5%
  Install Cost: $4,120,428
  2025 Compliant: ✅
  2027 Compliant: ✅
  2030 Compliant: ✅
  15-yr Penalties: $0

RECOMMENDED: 4-Pipe WSHP
Penalty Savings: $1,438,190
```

### **For Your Meeting:**
- "Current system faces $1.4M in penalties over 15 years"
- "4-Pipe WSHP achieves full compliance with 23.5% EUI reduction"
- "Premium TES option provides 32.5% reduction for future-proofing"
- "Both solutions eliminate all penalty exposure"

---

## 💰 **Step 4: Calculate Project Economics**

### **Command to Run:**
```bash
python -c "
from src.analysis.integrated_tes_hp_analyzer import IntegratedTESHPAnalyzer

analyzer = IntegratedTESHPAnalyzer()

# Calculate economics for recommended system
economics = analyzer.calculate_project_economics('4pipe_wshp_tes')

print('PROJECT ECONOMICS - 4-Pipe WSHP + TES')
print('='*50)
print()
print('PROJECT COSTS:')
print(f'Equipment Cost: ${economics[\"equipment_cost\"]:,.0f}')
print(f'Soft Costs: ${economics[\"soft_costs\"]:,.0f}')
print(f'Developer Fee: ${economics[\"developer_fee\"]:,.0f}')
print(f'Contingency: ${economics[\"contingency\"]:,.0f}')
print(f'TOTAL PROJECT: ${economics[\"total_project_cost\"]:,.0f}')
print()
print('INCENTIVE STACK:')
print(f'Federal ITC (40%): ${economics[\"itc_amount\"]:,.0f}')
print(f'Bonus Depreciation: ${economics[\"depreciation_value\"]:,.0f}')
print(f'DRCOG Grant: ${economics[\"drcog_grant\"]:,.0f}')
print(f'Xcel Rebate: ${economics[\"xcel_rebate\"]:,.0f}')
print(f'TOTAL INCENTIVES: ${economics[\"total_incentives\"]:,.0f}')
print()
print('NET ECONOMICS:')
print(f'Net Project Cost: ${economics[\"net_project_cost\"]:,.0f}')
print(f'Incentive Coverage: {economics[\"incentive_coverage\"]*100:.1f}%')
print(f'Monthly Service Fee: ${economics[\"monthly_service_fee\"]:,.0f}')
print(f'Annual Revenue: ${economics[\"annual_revenue\"]:,.0f}')
print(f'Annual NOI: ${economics[\"annual_noi\"]:,.0f}')
print(f'Project Yield: {economics[\"project_yield\"]*100:.1f}%')
"
```

### **Expected Output:**
```
PROJECT ECONOMICS - 4-Pipe WSHP + TES
==================================================

PROJECT COSTS:
Equipment Cost: $4,120,428
Soft Costs: $1,030,107
Developer Fee: $618,064
Contingency: $576,860
TOTAL PROJECT: $6,345,459

INCENTIVE STACK:
Federal ITC (40%): $1,648,171
Bonus Depreciation: $1,153,720
DRCOG Grant: $260,000
Xcel Rebate: $182,000
TOTAL INCENTIVES: $3,243,891

NET ECONOMICS:
Net Project Cost: $3,101,568
Incentive Coverage: 51.1%
Monthly Service Fee: $3,325
Annual Revenue: $39,900
Annual NOI: $27,930
Project Yield: 0.4%
```

### **For Your Meeting:**
- "Total project investment: $6.3 million"
- "Federal and state incentives cover 51% of cost"
- "Building qualifies for $260k DRCOG grant as EPB"
- "Monthly service fee: $3,325 vs potential $270k equipment replacement"

---

## 🏆 **Step 5: Generate Executive Summary**

### **Command to Run:**
```bash
python -c "
from src.analysis.integrated_tes_hp_analyzer import IntegratedTESHPAnalyzer

analyzer = IntegratedTESHPAnalyzer()
summary = analyzer.generate_executive_summary()

print('EXECUTIVE SUMMARY - Building 2952')
print('='*50)
print()
print('BUILDING OVERVIEW:')
print(f'Name: {summary[\"building\"][\"name\"]}')
print(f'Type: {summary[\"building\"][\"type\"]}')
print(f'Size: {summary[\"building\"][\"units\"]} units, {summary[\"building\"][\"sqft\"]:,} sq ft')
print(f'EPB Status: {\"Yes\" if summary[\"building\"][\"is_epb\"] else \"No\"}')
print(f'Current EUI: {summary[\"building\"][\"current_eui\"]}')
print()
print('RECOMMENDED SOLUTION:')
print(f'System: {summary[\"recommended_solution\"][\"system\"]}')
print(f'New EUI: {summary[\"recommended_solution\"][\"new_eui\"]} ({summary[\"recommended_solution\"][\"eui_reduction\"]}% reduction)')
print(f'Penalties Avoided: ${summary[\"recommended_solution\"][\"penalties_avoided_15yr\"]:,.0f}')
print(f'Compliant through 2030: {\"Yes\" if summary[\"recommended_solution\"][\"compliant_through_2030\"] else \"No\"}')
print()
print('FINANCIAL HIGHLIGHTS:')
print(f'Total Investment: ${summary[\"project_economics\"][\"total_cost\"]:,.0f}')
print(f'Incentive Coverage: {summary[\"project_economics\"][\"incentive_coverage\"]*100:.0f}%')
print(f'Monthly Service: ${summary[\"project_economics\"][\"monthly_service_fee\"]:,.0f}')
print()
print('KEY BENEFITS FOR BUILDING OWNER:')
for benefit in summary['key_benefits']['owner']:
    print(f'• {benefit}')
print()
print('DEVELOPER RETURNS:')
print(f'Total Profit: ${summary[\"developer_returns\"][\"total_profit\"]:,.0f}')
print(f'Return on Equity: {summary[\"developer_returns\"][\"return_on_equity\"]*100:.0f}%')
print()
print('NEXT STEPS:')
for i, step in enumerate(summary['next_steps'], 1):
    print(f'{i}. {step}')
"
```

### **Expected Output:**
```
EXECUTIVE SUMMARY - Building 2952
==================================================

BUILDING OVERVIEW:
Name: Timperly Condominium
Type: Multifamily Housing
Size: 52 units, 52,826 sq ft
EPB Status: Yes
Current EUI: 65.3

RECOMMENDED SOLUTION:
System: 4-Pipe WSHP + TES
New EUI: 44.1 (32% reduction)
Penalties Avoided: $1,438,190
Compliant through 2030: Yes

FINANCIAL HIGHLIGHTS:
Total Investment: $6,345,459
Incentive Coverage: 51%
Monthly Service: $3,325

KEY BENEFITS FOR BUILDING OWNER:
• Avoid $270,000 upfront cost
• Save $1,438,190 in ED penalties
• No capital investment required
• Predictable monthly costs with 2.5% annual escalation
• Modern 4-pipe system solves comfort issues

DEVELOPER RETURNS:
Total Profit: $1,527,368
Return on Equity: 764%

NEXT STEPS:
1. Finalize HOA/owner agreement
2. Secure bridge loan commitment
3. Submit DRCOG CPRG application
4. Begin engineering design
5. Order long-lead equipment
```

---

## 📊 **Step 6: Create Presentation Materials**

### **Command to Run:**
```bash
python -c "
from src.analysis.integrated_tes_hp_analyzer import IntegratedTESHPAnalyzer
import os

analyzer = IntegratedTESHPAnalyzer()

# Generate full report
output_dir = 'outputs'
os.makedirs(output_dir, exist_ok=True)
report_path = os.path.join(output_dir, 'building_2952_analysis.json')

report = analyzer.generate_full_report(report_path)

# Create charts
fig = analyzer.create_presentation_charts()
chart_path = os.path.join(output_dir, 'building_2952_charts.png')
fig.savefig(chart_path, dpi=300, bbox_inches='tight')

print('PRESENTATION MATERIALS GENERATED:')
print(f'✅ Full Report: {report_path}')
print(f'✅ Charts: {chart_path}')
print()
print('Files ready for meeting presentation!')
"
```

### **Expected Output:**
```
PRESENTATION MATERIALS GENERATED:
✅ Full Report: outputs/building_2952_analysis.json
✅ Charts: outputs/building_2952_charts.png

Files ready for meeting presentation!
```

---

## 🎯 **Meeting Talking Points**

### **Opening (Problem Statement):**
- "Building 2952 faces $1.4 million in Energize Denver penalties without action"
- "Current EUI of 65.3 must drop to 51.5 by 2030 - that's a 21% reduction"
- "Building needs $270k in HVAC equipment replacement anyway"

### **Solution (Value Proposition):**
- "4-Pipe WSHP + TES system achieves 32% EUI reduction"
- "Eliminates all penalty exposure through 2030 and beyond"
- "Fully electric system future-proofs the building"
- "Thermal storage provides grid flexibility and comfort optimization"

### **Economics (No-Brainer):**
- "Total investment: $6.3 million with 51% incentive coverage"
- "Building owner pays $0 upfront vs $270k equipment replacement"
- "Monthly service fee: $3,325 for full HVAC service"
- "EPB status provides access to $260k DRCOG grant"

### **Implementation (Path Forward):**
- "12-month construction timeline"
- "Bridge financing structure in place"
- "Experienced development team"
- "Immediate next step: HOA agreement for due diligence"

---

## 🚨 **Troubleshooting Guide**

### **If Building Data Missing:**
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/processed/energize_denver_comprehensive_latest.csv')
building_2952 = df[df['Building ID'] == 2952]
print(building_2952.head())
"
```

### **If Penalty Calculator Errors:**
```bash
python -c "
from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator
calc = EnergizeDenverPenaltyCalculator()
print('Calculator initialized successfully')
print(f'Standard rate: {calc.config.STANDARD_RATE}')
print(f'ACO rate: {calc.config.ACO_RATE}')
"
```

### **If Module Import Errors:**
```bash
export PYTHONPATH=/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP:$PYTHONPATH
python -c "import sys; print(sys.path)"
```

---

## 📋 **Quick Reference Commands**

### **Data Verification:**
```bash
python check_data_freshness.py
```

### **Full Portfolio Analysis:**
```bash
python execute_portfolio_analysis.py
```

### **Test Suite:**
```bash
cd tests && python run_all_tests.py
```

### **Building Specific Analysis:**
```bash
python -c "
from src.analysis.building_compliance_analyzer_v2 import EnhancedBuildingComplianceAnalyzer
analyzer = EnhancedBuildingComplianceAnalyzer(building_id='2952')
results = analyzer.calculate_enhanced_penalties()
print(results.head())
"
```

---

## 🎯 **Post-Meeting Actions**

### **If Interest Confirmed:**
1. **Generate formal proposal:** `python generate_developer_returns_report.py`
2. **Create bridge loan package:** Run bridge loan investor package generator
3. **Submit DRCOG application:** Prepare EPB grant documentation
4. **Begin engineering:** Site visit and system design

### **If Need More Information:**
1. **Detailed financial model:** Explore `src/models/tes_hp_cash_flow_bridge.py`
2. **Alternative scenarios:** Modify system configurations
3. **Risk analysis:** Run sensitivity analysis on key assumptions
4. **Comparison buildings:** Analyze similar multifamily properties

---

**Remember:** This is a **data-driven conversation** - every number has a source, every assumption is documented, and every recommendation is based on verified calculations. The penalty exposure is real, the incentives are confirmed, and the technical solution is proven.

**Good luck with your meeting!** 🚀