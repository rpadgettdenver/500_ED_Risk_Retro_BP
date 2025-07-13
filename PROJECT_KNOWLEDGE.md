# 🏢 Energize Denver TES+HP Risk & Retrofit Platform
## Project Knowledge Base & Source of Truth

**Last Updated:** July 13, 2025, 4:00 PM MDT  
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
   - Penalty calculations (✅ FIXED July 13, 2025)

6. **Bridge Loan Package Generator** (`src/models/bridge_loan_investor_package.py`)
   - Professional PDF investor packages
   - Coverage ratio analysis
   - Security documentation

7. **Penalty Calculator Module** (`src/utils/penalty_calculator.py`) - **NEW July 13, 2025**
   - Single source of truth for all penalty calculations
   - NPV analysis for opt-in decisions
   - Correct penalty rates implemented

8. **MAI Data Loader** (`src/utils/mai_data_loader.py`) - **NEW July 13, 2025**
   - Loads MAI designations and targets
   - Handles various property types with MAI designation
   - Integrates with penalty calculator

### 🚧 In Progress

1. **BigQuery Integration** (`src/gcp/`)
   - Data warehouse for city-wide analysis
   - Penalty calculations at scale (V3 script fixed)
   - Geographic clustering queries

2. **DER Clustering Analysis** (`src/analytics/der_clustering_analysis.py`)
   - Spatial analysis for shared thermal systems
   - EPB overlay for equity prioritization
   - Heat source/sink matching

3. **Unified EUI Target Loader** - **Next Priority**
   - Single module for all target loading
   - Priority logic implementation
   - MAI integration

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
│       ├── penalty_calculator.py  # NEW: Penalty calculations
│       └── mai_data_loader.py     # NEW: MAI data handling
├── data/
│   ├── raw/                  # Original ED datasets
│   │   ├── MAITargetSummary Report.csv      # MAI targets
│   │   └── MAIPropertyUseTypes Report.csv   # MAI details
│   └── processed/            # Cleaned & merged data
├── docs/
│   └── penalty_calculation_source_of_truth.md  # NEW: Definitive guide
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

### ✅ CORRECTED: Penalty Rates (Fixed July 13, 2025)

**Correct Rates per Technical Guidance:**
```python
# Standard Path (3 target years)
STANDARD_PATH_PENALTY = 0.15  # $/kBtu over target

# Alternate Compliance Option (2 target years)  
ALTERNATE_PATH_PENALTY = 0.23  # $/kBtu over target

# Timeline Extension (1 target year)
EXTENSION_PENALTY = 0.35  # $/kBtu over target

# Never Benchmarked
NEVER_BENCHMARKED = 10.00  # $/sqft
```

### Compliance Paths

1. **Standard Path**
   - Targets: 2025 (First Interim), 2027 (Second Interim), 2030 (Final)
   - Penalty: $0.15/kBtu × Building sqft × kBtu over target
   - Payment years: 2026, 2028, 2031, then annually if non-compliant

2. **Alternate Compliance Option (ACO/Opt-in)**
   - Targets: 2028 (Interim), 2032 (Final)
   - Penalty: $0.23/kBtu × Building sqft × kBtu over target
   - Payment years: 2029, 2033, then annually if non-compliant

3. **MAI Buildings** - **UPDATED July 13, 2025**
   - Identification: Building ID appears in MAITargetSummary Report.csv
   - NOT limited to Manufacturing/Industrial property type
   - Target = MAX(Adjusted Final Target, 30% reduction, 52.9 floor)

### Target Caps and Floors

1. **Non-MAI Buildings**: 42% maximum reduction from baseline
2. **MAI Buildings**: MAX(CSV Adjusted Target, 30% reduction, 52.9 kBtu/sqft)

---

## 📁 Data Sources

### Primary Datasets
1. **Building_EUI_Targets.csv** - Official ED targets by building
2. **MAITargetSummary Report.csv** - MAI building designations and targets
3. **MAIPropertyUseTypes Report.csv** - MAI property type details
4. **Energize Denver Report Request.xlsx** - Latest compliance data
5. **geocoded_buildings_final.csv** - Building locations for clustering
6. **CopyofWeeklyEPBStatsReport.csv** - Equity Priority Building status

### Key Fields
- **Building ID** - Primary key across all datasets
- **Weather Normalized Site EUI** - Compliance metric
- **Master Sq Ft** - For penalty calculations
- **is_epb** - Equity priority flag
- **is_mai** - MAI designation (from MAITargetSummary)
- **latitude/longitude** - For DER clustering

---

## 📦 Module Documentation

### Core Modules

#### 1. `src/config/project_config.py`
**Purpose:** Centralized configuration management  
**Status:** Needs update with correct penalty rates
**Key Features:**
- All assumptions in DEFAULT_CONFIG dictionary
- Dynamic calculation of derived values
- Save/load scenarios to JSON

#### 2. `src/utils/penalty_calculator.py` - **NEW**
**Purpose:** Single source of truth for penalty calculations
**Key Features:**
- Correct penalty rates implemented
- MAI building support with MAX() logic
- NPV analysis for opt-in decisions
- Path comparison functionality

**Usage:**
```python
from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator
calculator = EnergizeDenverPenaltyCalculator()
penalty = calculator.calculate_penalty(actual_eui, target_eui, sqft, penalty_rate)
```

#### 3. `src/utils/mai_data_loader.py` - **NEW**
**Purpose:** Load and process MAI building data
**Key Features:**
- Loads MAI designations from CSV
- Handles various property types
- Provides MAI target lookups

#### 4. `src/models/tes_hp_cash_flow_bridge.py`
**Purpose:** Month-by-month cash flow modeling  
**Status:** Working correctly

#### 5. `src/analysis/integrated_tes_hp_analyzer.py`
**Purpose:** Complete project analysis  
**Status:** Needs penalty rate update

#### 6. `src/analysis/building_compliance_analyzer.py`
**Purpose:** ED compliance pathways  
**Status:** Needs penalty rate update

---

## 💰 Financial Model

### Current Assumptions (Building 2952)

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

---

## 🔧 Known Issues & Fixes Needed

### 1. ✅ **COMPLETED: Penalty Rate Corrections**
- Created penalty_calculator.py with correct rates
- Created definitive source of truth document
- Still need to update individual scripts

### 2. **Scripts Needing Updates**
- `create_opt_in_decision_model.py` - Uses $0.15 for both paths
- `integrated_tes_hp_analyzer.py` - Uses wrong penalty structure
- `building_compliance_analyzer.py` - Uses wrong rates

### 3. **BigQuery Views**
- Need to update penalty calculations in views
- Ensure MAI logic is correct

### 4. **Data Validation**
- Some buildings missing Weather Normalized EUI
- EPB status needs verification
- MAI targets need validation against calculations

---

## 🚀 Next Steps & Roadmap

### Immediate Priority (This Week)
1. **Create Unified EUI Target Loader**
   - Consolidate all target loading logic
   - Implement priority system
   - Include MAI designation checks

2. **Update Core Scripts**
   - Use new penalty_calculator module
   - Fix penalty rates throughout
   - Add MAI logic where needed

3. **Validate Calculations**
   - Test Building 2952 (non-MAI)
   - Test MAI buildings with various baselines
   - Compare with technical guidance

### Short Term (Month 1)
1. **Complete BigQuery Integration**
   - Update all views with correct rates
   - Add MAI designation column
   - Enable city-wide analysis

2. **Enhance DER Clustering**
   - Identify top 10 thermal districts
   - Prioritize EPB + MAI clusters
   - Match heat sources with sinks

3. **Automate Reporting**
   - Building scorecards with correct penalties
   - MAI building special reports
   - Investment packages

### Medium Term (Quarter 1)
1. **Web API Development**
   - REST endpoints using new modules
   - MAI building endpoints
   - Penalty calculation service

2. **Financial Model Refinement**
   - MAI building special considerations
   - Updated penalty projections
   - Portfolio optimization

---

## 📞 Contact & Resources

**Project Lead:** Robert Padgett  
**GitHub:** [https://github.com/rpadgettdenver/500_ED_Risk_Retro_BP]  
**Documentation:** This file serves as source of truth

**Key References:**
- penalty_calculation_source_of_truth.md - Definitive penalty guide (NEW)
- ED Technical Guidance v3.0 (April 2025)
- MAI Buildings Technical Guidance (April 2025)
- Federal ITC Guidelines (IRA 2022)
- Denver Climate Action Plan

**Recent Updates (July 13, 2025):**
- Fixed BigQuery export script (V3)
- Created penalty calculator module
- Discovered MAI complexity
- Updated all documentation

---

*This document should be updated with each significant code change or policy clarification.*