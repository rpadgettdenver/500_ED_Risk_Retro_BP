# 🏢 Energize Denver TES+HP Risk & Retrofit Platform
## Project Knowledge Base & Source of Truth

**Last Updated:** July 12, 2025, 8:09 AM MDT  
**Project Lead:** Robert Padgett  
**Project Location:** `/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP`

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Current State & Progress](#current-state--progress)
3. [Technical Architecture](#technical-architecture)
4. [Key Policy Rules & Corrections](#key-policy-rules--corrections)
5. [Data Sources](#data-sources)
6. [Module Documentation](#module-documentation)
7. [Financial Model](#financial-model)
8. [Known Issues & Fixes Needed](#known-issues--fixes-needed)
9. [Next Steps & Roadmap](#next-steps--roadmap)
10. [API & Future Development](#api--future-development)

---

## 🎯 Project Overview

### Vision
Build a Python-based analytics platform that:
1. **Quantifies** building-level penalty risk under Energize Denver BPS
2. **Prioritizes** cost-effective retrofits for compliance and decarbonization
3. **Enables** DER clustering (shared thermal loops, heat recovery, thermal storage)
4. **Aligns** with federal/state incentives (ITC, Clean Heat Plan, CPRG, CPF)
5. **Transforms** into a scalable **Thermal Energy as a Service (TEaaS)** business model

### Business Model
Deploy 4-Pipe Water Source Heat Pump (WSHP) systems with Thermal Energy Storage (TES) to:
- Eliminate upfront costs for building owners
- Provide heating/cooling as a monthly service
- Leverage 56% incentive coverage to make projects financeable
- Generate 190-270% developer returns while preserving affordable housing

---

## 📊 Current State & Progress

### ✅ Completed Components

1. **Unified Configuration System** (`src/config/project_config.py`)
   - Single source of truth for all assumptions
   - JSON save/load capability
   - Scenario analysis support

2. **Cash Flow Bridge Model** (`src/models/tes_hp_cash_flow_bridge.py`)
   - Month-by-month project cash flows
   - Bridge loan sizing and timing
   - Developer returns calculation

3. **Integrated Analysis** (`src/analysis/integrated_tes_hp_analyzer.py`)
   - HVAC system EUI impact modeling
   - Project economics with incentives
   - Executive summary generation

4. **Developer Returns Report Generator** (`generate_developer_returns_report.py`)
   - Comprehensive returns analysis
   - Multiple exit scenarios
   - HTML/Markdown/JSON output formats

5. **Building Compliance Analyzer** (`src/analysis/building_compliance_analyzer.py`)
   - Standard vs Opt-in path comparison
   - Historical EUI tracking
   - Penalty calculations (needs correction)

6. **Bridge Loan Package Generator** (`src/models/bridge_loan_investor_package.py`)
   - Professional PDF investor packages
   - Coverage ratio analysis
   - Security documentation

### 🚧 In Progress

1. **BigQuery Integration** (`src/gcp/`)
   - Data warehouse for city-wide analysis
   - Penalty calculations at scale
   - Geographic clustering queries

2. **DER Clustering Analysis** (`src/analytics/der_clustering_analysis.py`)
   - Spatial analysis for shared thermal systems
   - EPB overlay for equity prioritization
   - Heat source/sink matching

---

## 🏗️ Technical Architecture

### Directory Structure
```
500_ED_Risk_Retro_BP/
├── src/
│   ├── config/               # Unified configuration
│   ├── models/               # Financial & system models
│   ├── analysis/             # Building & compliance analysis
│   ├── analytics/            # DER clustering & spatial
│   ├── data_processing/      # Data loaders & mergers
│   ├── gcp/                  # BigQuery integration
│   └── utils/                # Helper functions
├── data/
│   ├── raw/                  # Original ED datasets
│   └── processed/            # Cleaned & merged data
├── outputs/                  # Reports, charts, packages
├── references/               # Policy docs, guides
├── notebooks/                # Jupyter explorations
└── tests/                    # Unit tests (TBD)
```

### Key Design Principles
1. **Modular** - Each component can run independently
2. **Configurable** - All assumptions in one place
3. **Scalable** - Ready for 1,700+ building analysis
4. **API-Ready** - Outputs structured for web service

---

## ⚖️ Key Policy Rules & Corrections

### 🚨 CRITICAL CORRECTION NEEDED: Penalty Rates

**Current Code (WRONG):**
```python
penalties = {
    '2025_rate': 0.30,  # WRONG
    '2027_rate': 0.50,  # WRONG
    '2030_rate': 0.70,  # WRONG
}
```

**Correct Rates per Technical Guidance (Page 70):**
```python
# Standard Path (3 target years)
STANDARD_PATH_PENALTY = 0.15  # $/kBtu over target

# Alternate Compliance (2 target years)  
ALTERNATE_PATH_PENALTY = 0.23  # $/kBtu over target

# Timeline Extension (1 target year)
EXTENSION_PENALTY = 0.35  # $/kBtu over target
```

### Compliance Paths

1. **Standard Path**
   - Targets: 2025 (First Interim), 2027 (Second Interim), 2030 (Final)
   - Penalty: $0.15/kBtu × Building sqft × kBtu over target
   - Applied at each interim year and then annually after 2030 if target is not met

2. **Alternate Compliance Option (Opt-in)**
   - Targets: 2028 (Interim), 2032 (Final)
   - Penalty: $0.23/kBtu × Building sqft × kBtu over target
   - Higher rate but more time to comply
   - Applied at each interim year and then annually after 2032 if target is not met

3. **Electrification Bonus**
   - Buildings that fully electrify get 10% higher EUI allowance
   - Applied as: Allowed EUI = Target EUI × 1.1

### Example: Building 2952 (Timperly Condominium)
- Current EUI: 65.3 kBtu/ft²
- Size: 52,826 sq ft
- 2027 Target: 63.2 kBtu/ft²
- Excess: 2.1 kBtu/ft²

**Correct Interim Penalty**: 2.1 × 52,826 × $0.15 = **$16,640/year** (not $55,467)

---

## 📁 Data Sources

### Primary Datasets
1. **Building_EUI_Targets.csv** - Official ED targets by building
2. **Energize Denver Report Request.xlsx** - Latest compliance data
3. **geocoded_buildings_final.csv** - Building locations for clustering
4. **CopyofWeeklyEPBStatsReport.csv** - Equity Priority Building status

### Key Fields
- **Building ID** - Primary key across all datasets
- **Weather Normalized Site EUI** - Compliance metric
- **Master Sq Ft** - For penalty calculations
- **is_epb** - Equity priority flag
- **latitude/longitude** - For DER clustering

---

## 📦 Module Documentation

### Core Modules

#### 1. `src/config/project_config.py`
**Purpose:** Centralized configuration management  
**Key Features:**
- All assumptions in DEFAULT_CONFIG dictionary
- Dynamic calculation of derived values
- Save/load scenarios to JSON
- Print formatted assumptions table

**Usage:**
```python
from src.config import get_config, update_config
config = get_config()
update_config({'financial': {'itc_rate': 0.30}})
```

#### 2. `src/models/tes_hp_cash_flow_bridge.py`
**Purpose:** Month-by-month cash flow modeling  
**Tracks:**
- Pre-construction expenses
- Construction draws
- Incentive receipts
- Bridge loan balance
- Operating revenues

**Key Output:** 
- Peak funding need
- Developer returns (190%+ ROE)
- Bridge loan sizing

#### 3. `src/analysis/integrated_tes_hp_analyzer.py`
**Purpose:** Complete project analysis  
**Calculates:**
- System EUI reductions (70% for 4-pipe WSHP+TES)
- Total project economics
- Penalty avoidance
- Developer returns
- Exit valuations

#### 4. `src/analysis/building_compliance_analyzer.py`
**Purpose:** ED compliance pathways  
**Status:** ⚠️ NEEDS PENALTY RATE CORRECTION  
**Features:**
- Historical EUI trending
- Standard vs Opt-in comparison
- Visualization suite

---

## 💰 Financial Model

### Current Assumptions (Building 2952) only

**Costs:**
- Equipment: $1,200,000
- TES: $200,000
- Market Escalation: 30%
- Total Project: $2,802,800

**Incentives (56% coverage):**
- Federal ITC: 40% ($728,000)
- Depreciation: 80% bonus ($403,200)
- DRCOG Grant: $5,000/unit ($260,000)
- Xcel Rebate: $3,500/unit ($182,000)

**Returns:**
- Developer Equity: $200,000
- Development Profits: $396,890
- ROE: 198% (development only)
- ROE: 274% (with asset sale)

**Service Model:**
- Monthly Fee: $150/unit
- Annual NOI: $28,080
- Asset Value (8% cap): $351,000

---

## 🔧 Known Issues & Fixes Needed

### 1. 🚨 **CRITICAL: Penalty Rate Corrections**
**Files to Update:**
- `src/config/project_config.py` - Change penalty rates
- `src/analysis/building_compliance_analyzer.py` - Update calculations
- `src/analysis/integrated_tes_hp_analyzer.py` - Fix penalty math

**Required Changes:**
```python
# In project_config.py
'penalties': {
    'standard_rate': 0.15,  # $/kBtu for 3-target path
    'alternate_rate': 0.23,  # $/kBtu for 2-target path
    'extension_rate': 0.35,  # $/kBtu for 1-target path
}
```

### 2. **Display Formatting**
- Fix percentage display for penalty rates
- Show as $/kBtu, not percentages

### 3. **Opt-in Logic Enhancement**
- Calculate breakeven for opt-in decision
- Consider time value of delaying penalties

### 4. **Data Validation**
- Some buildings missing Weather Normalized EUI
- EPB status needs verification
- Geocoding completeness check

---

## 🚀 Next Steps & Roadmap

### Immediate Priority (Week 1)
1. ✅ Fix penalty rate calculations throughout codebase
2. ✅ Update all documentation with correct rates
3. ✅ Re-run Building 2952 analysis with correct penalties
4. ✅ Validate against technical guidance

### Short Term (Month 1)
1. **Complete BigQuery Integration**
   - Load all ED data to cloud
   - Create penalty calculation views
   - Enable city-wide analysis

2. **Enhance DER Clustering**
   - Identify top 10 thermal districts
   - Match heat sources with sinks
   - Prioritize EPB clusters

3. **Automate Reporting**
   - Building scorecards
   - Portfolio summaries
   - Investment packages

### Medium Term (Quarter 1)
1. **Web API Development**
   - REST endpoints for building lookup
   - Penalty calculations
   - Retrofit recommendations

2. **Financial Model Refinement**
   - Dynamic utility rate projections
   - Carbon credit integration
   - Portfolio optimization

3. **Pilot Project Selection**
   - Identify first 5-10 buildings
   - Develop HOA/owner agreements
   - Secure financing commitments

### Long Term (Year 1)
1. **Platform Launch**
   - Public-facing web interface
   - AI chatbot for building owners
   - Automated proposal generation

2. **Business Operations**
   - Project development pipeline
   - Construction management system
   - Performance monitoring dashboard

3. **Scale to 100+ Buildings**
   - Standardized equipment packages
   - Bulk procurement contracts
   - O&M optimization

---

## 🔌 API & Future Development

### Planned Endpoints
```
GET  /api/building/{id}/penalty
POST /api/building/analyze
GET  /api/clusters/thermal
POST /api/proposal/generate
```

### Integration Points
- Energize Denver reporting API
- Xcel Energy rebate portal
- DRCOG grant applications
- Tax credit monetization platforms

### Success Metrics
- Buildings analyzed: 1,700+
- Penalties avoided: $100M+
- GHG reduced: 50,000 tons/year
- EPB buildings served: 200+
- Developer IRR: 25%+

---

## 📞 Contact & Resources

**Project Lead:** Robert Padgett  
**GitHub:** [https://github.com/rpadgettdenver/500_ED_Risk_Retro_BP]  
**Documentation:** This file serves as source of truth

**Key References:**
- ED Technical Guidance v3.0 (April 2025) - ed-technical-guidance-buildings-25k-sf-v3-april-2025-clean.pdf
- ed-technical-guidance-mai-buildings-25k-april-2025-clean.pdf
- Federal ITC Guidelines (IRA 2022)
- Denver Climate Action Plan
- CASR Ambient Loop Study (June 2025)

---

*This document should be updated with each significant code change or policy clarification.*