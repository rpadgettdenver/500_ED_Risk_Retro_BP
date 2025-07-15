# 🏢 Energize Denver TES+HP Risk & Retrofit Platform
## Project Knowledge Base & Source of Truth

**Last Updated:** July 14, 2025, 4:44 PM MDT  
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
8. [Testing & Quality Assurance](#testing--quality-assurance)
9. [Known Issues & Next Steps](#known-issues--next-steps)
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

### ✅ Completed Components (As of July 14, 2025)

1. **Penalty Calculator Module** (`src/utils/penalty_calculator.py`)
   - Single source of truth for all penalty calculations
   - Correct penalty rates: $0.15 (Standard), $0.23 (ACO)
   - NPV analysis for opt-in decisions
   - MAI building support with MAX() logic

2. **Comprehensive Test Suite** (`tests/`)
   - Integration tests covering all major modules
   - Python-BigQuery consistency validation
   - 87.5% test pass rate (21/24 tests)
   - Test runner and documentation

3. **Unified Configuration System** (`src/config/project_config.py`)
   - Single source of truth for all assumptions
   - JSON save/load capability
   - Scenario analysis support

4. **Cash Flow Bridge Model** (`src/models/tes_hp_cash_flow_bridge.py`)
   - Month-by-month project cash flows
   - Bridge loan sizing and timing
   - Developer returns calculation

5. **Integrated Analysis** (`src/analysis/integrated_tes_hp_analyzer.py`)
   - HVAC system EUI impact modeling
   - Project economics with incentives
   - Executive summary generation

6. **Developer Returns Report Generator** (`generate_developer_returns_report.py`)
   - Comprehensive returns analysis
   - Multiple exit scenarios
   - HTML/Markdown/JSON output formats

7. **Building Compliance Analyzer** (`src/analysis/building_compliance_analyzer.py`)
   - Standard vs Opt-in path comparison
   - Historical EUI tracking
   - Penalty calculations with correct rates

8. **Bridge Loan Package Generator** (`src/models/bridge_loan_investor_package.py`)
   - Professional PDF investor packages
   - Coverage ratio analysis
   - Security documentation

9. **MAI Data Loader** (`src/utils/mai_data_loader.py`)
   - Loads MAI designations and targets
   - Handles various property types with MAI designation
   - Integrates with penalty calculator

### 🚧 In Progress

1. **BigQuery Schema Resolution**
   - Investigation tools created
   - Schema mismatch blocking view regeneration
   - Need to update views with correct penalty rates

2. **Unified EUI Target Loader**
   - Consolidate all target loading logic
   - Priority system implementation
   - MAI integration

3. **DER Clustering Analysis**
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
│       ├── penalty_calculator.py  # Core penalty calculations
│       └── mai_data_loader.py     # MAI data handling
├── data/
│   ├── raw/                  # Original ED datasets
│   └── processed/            # Cleaned & merged data
├── tests/
│   ├── test_integration_suite.py
│   ├── test_python_bigquery_consistency.py
│   └── run_all_tests.py
├── docs/
│   ├── handoffs/             # Session continuity
│   └── penalty_calculation_source_of_truth.md
├── outputs/                  # Reports, charts, packages
├── references/               # Policy docs, guides
└── notebooks/                # Jupyter explorations
```

### Key Design Principles
1. **Modular** - Each component can run independently
2. **Configurable** - All assumptions in one place
3. **Scalable** - Ready for 1,700+ building analysis
4. **Tested** - Comprehensive test coverage
5. **API-Ready** - Outputs structured for web service

---

## ⚖️ Key Policy Rules & Corrections

### ✅ VERIFIED: Penalty Rates (Fixed July 13-14, 2025)

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

3. **MAI Buildings**
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
4. **Energize Denver Report Request.xlsx** - Latest compliance data (June 2025)
5. **geocoded_buildings_final.csv** - Building locations for clustering
6. **CopyofWeeklyEPBStatsReport.csv** - Equity Priority Building status

### Processed Datasets
1. **energize_denver_comprehensive_latest.csv** - Master dataset (updated July 11, 2025)
   - Generated by `enhanced_comprehensive_loader.py`
   - Contains all buildings with compliance data
   - Includes EPB status and geocoding

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

#### 1. `src/utils/penalty_calculator.py` ✅
**Purpose:** Single source of truth for penalty calculations  
**Status:** Complete and tested
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

#### 2. `src/config/project_config.py` ✅
**Purpose:** Centralized configuration management  
**Status:** Complete
**Key Features:**
- All assumptions in DEFAULT_CONFIG dictionary
- Dynamic calculation of derived values
- Save/load scenarios to JSON

#### 3. `src/models/tes_hp_cash_flow_bridge.py` ✅
**Purpose:** Month-by-month cash flow modeling  
**Status:** Complete and tested

#### 4. `src/analysis/integrated_tes_hp_analyzer.py` ✅
**Purpose:** Complete project analysis  
**Status:** Complete, uses penalty calculator

#### 5. `src/analysis/building_compliance_analyzer_v2.py` ✅
**Purpose:** ED compliance pathways  
**Status:** Complete, correct penalty rates

#### 6. `src/models/hvac_system_impact_modeler.py` ✅
**Purpose:** Model HVAC system impacts on EUI  
**Status:** Complete, integrated with penalty calculator

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

## 🧪 Testing & Quality Assurance

### Test Coverage (87.5%)
- **Penalty Rate Verification**: ✅ 3/3 tests passing
- **Building 2952 Verification**: ✅ 2/3 tests passing
- **Data Pipeline Integration**: ✅ 3/4 tests passing
- **Edge Case Handling**: ✅ 4/4 tests passing
- **Module Consistency**: ✅ 2/2 tests passing
- **Year Normalization**: ✅ 7/7 tests passing
- **Python-BigQuery Consistency**: ✅ 100% match on 26 buildings

### Running Tests
```bash
cd tests
python run_all_tests.py
```

---

## 🔧 Known Issues & Next Steps

### Immediate Priority
1. **Fix BigQuery Schema**
   - Run `investigate_bigquery_schema.py`
   - Update column references in views
   - Regenerate with correct penalty rates

2. **Create Unified EUI Target Loader**
   - Consolidate target loading logic
   - Implement priority: MAI → CSV → Calculated
   - Include all edge cases

3. **Complete Failed Tests**
   - Fix opt-in predictor key error
   - Add MAI building IDs to test data

### Short Term (This Week)
1. **Portfolio Risk Analysis**
   - Run city-wide analysis with corrected rates
   - Generate executive summary
   - Identify top 20 TEaaS opportunities

2. **DER Clustering Enhancement**
   - Complete spatial analysis
   - Overlay EPB data
   - Identify thermal districts

### Medium Term (This Month)
1. **Web API Development**
   - Design RESTful endpoints
   - Implement FastAPI framework
   - Create API documentation

2. **Client Deliverables**
   - Building scorecards
   - Investor packages
   - Executive presentations

---

## 🚀 API & Future Development

### Planned Endpoints
```
GET  /api/v1/buildings/{id}/compliance
POST /api/v1/buildings/{id}/retrofit-analysis
GET  /api/v1/clusters/thermal-districts
POST /api/v1/financial/bridge-loan-package
GET  /api/v1/portfolio/risk-summary
```

### Frontend Integration
- React dashboard for building owners
- Interactive maps for thermal districts
- Financial modeling tools
- Report generation interface

---

## 📞 Contact & Resources

**Project Lead:** Robert Padgett  
**GitHub:** [https://github.com/rpadgettdenver/500_ED_Risk_Retro_BP]  

**Key References:**
- penalty_calculation_source_of_truth.md - Definitive penalty guide
- ED Technical Guidance v3.0 (April 2025)
- MAI Buildings Technical Guidance (April 2025)
- Federal ITC Guidelines (IRA 2022)
- Denver Climate Action Plan

**Recent Updates (July 14, 2025):**
- Comprehensive integration testing complete
- Python-BigQuery consistency verified
- Project structure cleaned and organized
- Documentation fully updated

---

*This document should be updated with each significant code change or policy clarification.*