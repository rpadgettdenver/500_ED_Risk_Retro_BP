#!/bin/bash
# Professional Project Structure Setup for Energize Denver EaaS Platform
# Run this script from your project root: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP

echo "Setting up professional project structure..."

# Create main directories
mkdir -p src/{data_processing,analytics,models,utils,api,gcp}
mkdir -p notebooks/{exploratory,reports,demos}
mkdir -p tests/{unit,integration}
mkdir -p docs/{api,user_guide,technical}
mkdir -p scripts/{deployment,automation,maintenance}
mkdir -p config/{development,production}
mkdir -p outputs/{reports,visualizations,exports}
mkdir -p data/{processed,interim,external}

# Create __init__.py files to make directories Python packages
touch src/__init__.py
touch src/data_processing/__init__.py
touch src/analytics/__init__.py
touch src/models/__init__.py
touch src/utils/__init__.py
touch src/api/__init__.py
touch src/gcp/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Create .gitignore file
cat > .gitignore << 'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
gcp_env/
venv/
ENV/
env/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Project specific
data/raw/*.csv
data/processed/*.csv
outputs/reports/*.pdf
outputs/exports/*.xlsx
*.log
.cache/

# Google Cloud
*.json
!requirements.json
.gcloud/
credentials/

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Documentation
docs/_build/
GITIGNORE

# Create README.md (proper markdown format)
cat > README.md << 'README'
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
README

# Create setup.py for package installation
cat > setup.py << 'SETUP'
from setuptools import setup, find_packages

setup(
    name="energize_denver_eaas",
    version="0.1.0",
    author="Your Name",
    author_email="rpadgett@clms.com",
    description="Energize Denver Risk & Retrofit Strategy Platform",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "google-cloud-storage>=2.10.0",
        "google-cloud-bigquery>=3.11.0",
        "pandas>=2.0.0",
        "numpy>=1.26.0",
        "pyarrow>=14.0.0",
    ],
)
SETUP

# Create a proper pyproject.toml for modern Python packaging
cat > pyproject.toml << 'TOML'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "energize_denver_eaas"
version = "0.1.0"
description = "Energize Denver Risk & Retrofit Strategy Platform"
authors = [{name = "Robert Padgett", email = "rpadgett@clms.com"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "google-cloud-storage>=2.10.0",
    "google-cloud-bigquery>=3.11.0",
    "pandas>=2.0.0",
    "numpy>=1.26.0",
    "pyarrow>=14.0.0",
    "db-dtypes>=1.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]
viz = [
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
    "folium>=0.14.0",
    "plotly>=5.14.0",
]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
TOML

# Create config files
cat > config/development/config.yaml << 'CONFIG'
# Development Configuration
project_id: energize-denver-eaas
dataset_id: energize_denver
bucket_name: energize-denver-eaas-data

# BigQuery settings
bq:
  location: us-central1
  default_table_expiration: null

# Penalty calculation parameters
penalties:
  rate_per_kbtu: 0.15
  opt_in_rate: 0.23
  
# Risk thresholds
risk_thresholds:
  high: 100000
  medium: 50000
  low: 0

# Clustering parameters
clustering:
  max_distance_meters: 500
  min_cluster_size: 3
CONFIG

# Create sample test file
cat > tests/unit/test_penalty_calculations.py << 'TEST'
"""Unit tests for penalty calculations"""
import pytest
import pandas as pd
from src.analytics.penalty_calculator import PenaltyCalculator


class TestPenaltyCalculator:
    """Test penalty calculation logic"""
    
    def test_penalty_calculation(self):
        """Test basic penalty calculation"""
        # Test data
        building_data = {
            'actual_eui': 100,
            'target_eui_2024': 80,
            'gross_floor_area': 50000
        }
        
        # Expected: (100-80) * 50000 * 0.15 = $150,000
        expected_penalty = 150000
        
        calculator = PenaltyCalculator()
        result = calculator.calculate_penalty(building_data)
        
        assert result == expected_penalty
    
    def test_compliant_building_no_penalty(self):
        """Test that compliant buildings have no penalty"""
        building_data = {
            'actual_eui': 70,
            'target_eui_2024': 80,
            'gross_floor_area': 50000
        }
        
        calculator = PenaltyCalculator()
        result = calculator.calculate_penalty(building_data)
        
        assert result == 0
TEST

echo "✅ Professional project structure created successfully!"
echo ""
echo "Next steps:"
echo "1. Move your penalty calculator to: src/gcp/load_data_and_calculate.py"
echo "2. Organize existing notebooks into notebooks/exploratory/"
echo "3. Add your GCP credentials to a credentials/ folder (git-ignored)"
echo "4. Run tests with: pytest tests/"
echo ""
echo "Your project now follows industry best practices!"
