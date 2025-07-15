# Energize Denver Risk & Retrofit Strategy Platform

## 🔎 Overview

This platform quantifies building-level penalty risk under Denver's Energize Denver Building Performance Standards (BPS), prioritizes cost-effective retrofits for compliance and decarbonization, and models financial pathways for electrification using Thermal Energy as a Service (TEaaS) business models.

**Key Features:**
- **Penalty Calculator**: Automated compliance penalty calculations with correct rates ($0.15 Standard, $0.23 ACO)
- **Risk Analysis**: Building portfolio risk assessment across 1,700+ covered buildings
- **Clustering Analysis**: Geospatial analysis for shared thermal energy networks
- **Financial Modeling**: ROI calculations for TES+HP retrofits with federal/state incentives
- **BigQuery Integration**: City-wide analysis at scale with SQL views
- **Reporting**: Automated client reports, bridge loan packages, and dashboards

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Google Cloud SDK (for BigQuery features)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rpadgettdenver/500_ED_Risk_Retro_BP.git
   cd 500_ED_Risk_Retro_BP
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv gcp_env
   source gcp_env/bin/activate  # On Windows: gcp_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Google Cloud (optional, for BigQuery features)**
   ```bash
   gcloud auth application-default login
   gcloud config set project energize-denver-eaas
   ```

## 📊 Core Modules

### Penalty Calculation (`src/utils/penalty_calculator.py`)
Single source of truth for all penalty calculations with correct rates:
```python
from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator

calculator = EnergizeDenverPenaltyCalculator()
penalty = calculator.calculate_penalty(
    actual_eui=70.0,
    target_eui=60.0,
    sqft=50000,
    penalty_rate=0.15  # Standard path
)
```

### Building Compliance Analysis (`src/analysis/building_compliance_analyzer_v2.py`)
Analyzes compliance pathways for individual buildings:
```python
from src.analysis.building_compliance_analyzer_v2 import EnhancedBuildingComplianceAnalyzer

analyzer = EnhancedBuildingComplianceAnalyzer(building_id="2952")
results = analyzer.calculate_enhanced_penalties()
```

### Financial Modeling (`src/models/tes_hp_cash_flow_bridge.py`)
Models month-by-month cash flows for TES+HP projects:
```python
from src.models.tes_hp_cash_flow_bridge import TESHPCashFlowBridge

model = TESHPCashFlowBridge()
cash_flows = model.generate_monthly_cash_flows()
```

### DER Clustering (`src/analytics/der_clustering_analysis.py`)
Identifies opportunities for shared thermal energy systems:
```python
from src.analytics.der_clustering_analysis import DERClusteringAnalysis

clustering = DERClusteringAnalysis()
clusters = clustering.identify_thermal_clusters(radius_meters=100)
```

## 🏗️ Project Structure

```
500_ED_Risk_Retro_BP/
├── src/                       # Source code
│   ├── analysis/              # Building and portfolio analysis
│   ├── analytics/             # Spatial and clustering analysis
│   ├── config/                # Configuration management
│   ├── data_processing/       # Data loaders and cleaners
│   ├── gcp/                   # Google Cloud integration
│   ├── models/                # Financial and system models
│   └── utils/                 # Helper utilities
├── data/                      # Data storage
│   ├── raw/                   # Original datasets
│   └── processed/             # Cleaned data
├── tests/                     # Test suite
├── docs/                      # Documentation
├── notebooks/                 # Jupyter notebooks
└── outputs/                   # Generated reports
```

## 📋 Key Policy Rules

### Penalty Rates (Corrected July 2025)
- **Standard Path**: $0.15/kBtu over target
- **Alternate Compliance Option (ACO)**: $0.23/kBtu over target
- **Timeline Extension**: $0.35/kBtu over target
- **Never Benchmarked**: $10.00/sqft

### Compliance Timelines
- **Standard Path**: 2025, 2027, 2030 (3 target years)
- **ACO Path**: 2028, 2032 (2 target years)
- **MAI Buildings**: Special targets with 30% reduction cap

## 🧪 Testing

Run the test suite to verify all calculations:
```bash
cd tests
python run_all_tests.py
```

Current test coverage: 87.5% (21/24 tests passing)

## 📊 Data Sources

**Required data files in `data/raw/`:**
- `Building_EUI_Targets.csv` - Official ED targets
- `MAITargetSummary Report.csv` - MAI building designations
- `Energize Denver Report Request.xlsx` - Latest compliance data
- `geocoded_buildings_final.csv` - Building locations

## 🛠️ Development

### Contributing
1. Create a feature branch
2. Make changes with clear commit messages
3. Run tests to ensure nothing breaks
4. Submit pull request

### Code Style
- Use meaningful variable names
- Add docstrings to all functions
- Follow PEP 8 guidelines
- Keep functions focused and modular

## 📝 Documentation

- **PROJECT_KNOWLEDGE.md** - Detailed technical documentation
- **docs/penalty_calculation_source_of_truth.md** - Definitive penalty guide
- **docs/handoffs/** - Session continuity documents

## 🤝 Support

For questions or issues:
- Check existing documentation
- Review test cases for examples
- Contact: Robert Padgett

## 📄 License

Copyright 2025 - All rights reserved

---

*Last updated: July 2025*