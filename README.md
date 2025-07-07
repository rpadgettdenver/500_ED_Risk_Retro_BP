# Energize Denver Risk & Retrofit Strategy Platform

## 🔎 Overview

This platform quantifies market risk, prioritizes building retrofits, and models financial pathways for electrification and decarbonization under Denver's Energize Denver Performance Policy.

## 🏗️ Project Structure

```
energize_denver_eaas/
├── data/                      # Data storage
│   ├── raw/                   # Original data files
│   ├── processed/             # Cleaned and transformed data
│   ├── interim/               # Intermediate processing results
│   └── external/              # External reference data
├── src/                       # Source code
│   ├── data_processing/       # Data loading and cleaning
│   ├── analytics/             # Analysis and calculations
│   ├── models/                # ML and predictive models
│   ├── utils/                 # Utility functions
│   ├── api/                   # API endpoints
│   └── gcp/                   # Google Cloud integrations
├── notebooks/                 # Jupyter notebooks
│   ├── exploratory/           # Data exploration
│   ├── reports/               # Analysis reports
│   └── demos/                 # Demo notebooks
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── scripts/                   # Automation scripts
│   ├── deployment/            # Deployment scripts
│   ├── automation/            # Scheduled jobs
│   └── maintenance/           # Maintenance utilities
├── config/                    # Configuration files
│   ├── development/           # Dev environment config
│   └── production/            # Production config
├── docs/                      # Documentation
│   ├── api/                   # API documentation
│   ├── user_guide/            # User guides
│   └── technical/             # Technical specs
└── outputs/                   # Generated outputs
    ├── reports/               # PDF/HTML reports
    ├── visualizations/        # Charts and maps
    └── exports/               # Data exports
```

## 🚀 Quick Start

1. **Set up environment**
   ```bash
   python3 -m venv gcp_env
   source gcp_env/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Google Cloud**
   ```bash
   gcloud auth application-default login
   gcloud config set project energize-denver-eaas
   ```

3. **Run data loader**
   ```bash
   python src/gcp/load_data_and_calculate.py
   ```

## 📊 Key Features

- **Penalty Calculator**: Automated compliance penalty calculations
- **Risk Analysis**: Building portfolio risk assessment
- **Clustering**: Geospatial analysis for thermal networks
- **Financial Modeling**: ROI calculations for retrofits
- **Reporting**: Automated client reports and dashboards

## 🛠️ Technology Stack

- **Cloud Platform**: Google Cloud Platform
- **Data Storage**: BigQuery, Cloud Storage
- **Languages**: Python 3.11+
- **Key Libraries**: pandas, numpy, google-cloud-bigquery
- **Visualization**: Looker Studio, matplotlib, folium

## 📝 License

Copyright 2024 - All rights reserved
