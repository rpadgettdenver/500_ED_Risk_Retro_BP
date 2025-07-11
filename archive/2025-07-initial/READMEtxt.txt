# Energize Denver Risk & Retrofit Strategy Platform

## 🔎 Overview
This project quantifies market risk, prioritizes building retrofits, and models financial pathways for electrification and decarbonization under the City and County of Denver's Energize Denver Performance Policy. It is designed to support engineering, financial, and strategic decisions for retrofitting commercial and multifamily buildings, especially those serving equity-priority communities.

The platform integrates energy use data, compliance targets, penalty structures, EPB designations, and geographic clustering to:
- Calculate penalties for non-compliance under both opt-in and default schedules
- Identify high-risk buildings and retrofit opportunities
- Prioritize shared DER potential such as thermal storage, GSHP, and data center waste heat reuse
- Model eligibility for Section 48 ITC, Clean Heat Plan rebates, CPRG funding, and CPF alignment

---

## 🏛️ Policy Context: Energize Denver Compliance Logic

| Feature | Description |
|--------|-------------|
| **Applies To** | Commercial and multifamily buildings ≥25,000 sqft |
| **Targets** | Baseline EUI → Interim (2024/2025/2027) → Final (2030) or opt-in to 2028/2032 |
| **Penalty (No Opt-In)** | $0.15 per kBtu missed, annually from 2024 to 2030 |
| **Penalty (Opt-In)** | $0.23 per kBtu missed, annually from 2028 to 2032 |
| **Equity Priority Buildings** | Eligible for alternate compliance, enhanced funding, and prioritization |
| **Thermal Networks** | Buildings sharing non-emitting thermal energy may receive performance credit |

---

## 🚀 Project Goals
- Quantify total penalty exposure across Denver buildings
- Build spatial and equity overlays for targeting EPB clusters
- Recommend retrofit strategies aligned with funding incentives
- Identify opportunities for thermal DERs and symbiotic heating/cooling

---

## 📁 File Structure
```bash
energize_denver_project/
│
├── data/                         # Raw input data
│   ├── Building_EUI_Targets.csv
│   ├── Energize Denver Report Request.xlsx
│   ├── CopyofWeeklyEPBStatsReport.csv
│   ├── geocoded_buildings_final.csv
│   └── building_zipcode_lookup.csv
│
├── notebooks/                    # Jupyter analysis & reports
│   ├── risk_dashboard.ipynb
│   └── retrofit_scenarios.ipynb
│
├── src/                          # Python modules
│   ├── data_loader.py
│   ├── penalty_model.py
│   ├── epb_join.py
│   ├── cluster_analysis.py
│   ├── financial_model.py
│   └── utils.py
│
├── outputs/                      # Final CSVs & GeoJSONs
│   ├── high_risk_buildings.csv
│   └── cluster_targets.geojson
│
├── tests/                        # Unit test cases
│   └── test_penalty_model.py
│
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
└── .gitignore                    # Exclude cache/output files
```

---

## 🚪 Key Modules

### `data_loader.py`
- Ingests and standardizes datasets
- Filters to most recent year
- Tags exempt vs. covered buildings

### `penalty_model.py`
- Computes EUI gaps and penalties for each target
- Applies both opt-in and non-opt-in compliance logic

### `epb_join.py`
- Integrates Equity Priority Building (EPB) data
- Filters or flags buildings serving vulnerable communities

### `cluster_analysis.py`
- Performs spatial joins using lat/lon
- Flags thermal loops and ambient loop sharing potential

### `financial_model.py`
- Estimates eligibility for tax credits and incentives
- Calculates ROI vs. penalty cost avoidance

---

## 📊 Outputs
- Ranked list of high-risk buildings by penalty exposure
- EPB overlay and geospatial cluster maps
- Eligibility matrix for funding sources (ITC, Xcel, CPF)
- Scenario modeling of retrofit vs. compliance penalties

---

## 📊 Next Steps
1. Create PyCharm environment with this folder structure
2. Load and clean all datasets using `data_loader.py`
3. Implement and test `penalty_model.py`
4. Merge EPB + geolocation + energy use data
5. Conduct spatial cluster and retrofit analysis
6. Add financial modeling tools and summary tables

---

## 🚀 Goal
To enable engineering teams, policy strategists, and retrofit developers to prioritize decarbonization investments in a way that reduces compliance risk, maximizes public funding leverage, and supports Denver's climate and equity goals.
