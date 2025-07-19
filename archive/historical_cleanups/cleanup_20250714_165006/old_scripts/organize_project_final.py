#!/usr/bin/env python3
"""
Suggested file name: organize_project_final.py
Directory location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Final project organization and cleanup
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def organize_project():
    """Organize project files and clean up structure"""
    
    project_root = Path("/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create archive directory for this cleanup
    archive_dir = project_root / "archive" / f"cleanup_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created archive directory: {archive_dir}")
    
    # Files to move to archive
    files_to_archive = {
        # Test files in root that should move to tests/
        "test_files": [
            "test_2028_fix.py",
            "test_building_2952.py", 
            "test_hvac_direct.py",
            "simple_hvac_test.py",
            "test_portfolio_quick.py"
        ],
        # Cleanup scripts that are now obsolete
        "cleanup_scripts": [
            "cleanup_project_interactive.py",
            "cleanup_project_structure.py",
            "fix_imports.sh",
            "fix_imports_corrected.sh",
            "fix_remaining_issues.py",
            "organize_and_setup.sh",
            "setup_project_structure.sh"
        ],
        # Old run scripts
        "old_runners": [
            "run_portfolio_analysis_corrected.py",
            "run_unified_analysis_v2.py.backup",
            "portfolio_summary.py"
        ],
        # Backup files in src
        "backup_files": []
    }
    
    # Find backup files in src
    for root, dirs, files in os.walk(project_root / "src"):
        for file in files:
            if '.backup' in file or file.endswith('_backup.py'):
                rel_path = Path(root).relative_to(project_root) / file
                files_to_archive["backup_files"].append(str(rel_path))
    
    # Archive files
    archived_count = 0
    for category, file_list in files_to_archive.items():
        if file_list:
            category_dir = archive_dir / category
            category_dir.mkdir(exist_ok=True)
            
            for file_path in file_list:
                src = project_root / file_path
                if src.exists():
                    dst = category_dir / Path(file_path).name
                    try:
                        shutil.move(str(src), str(dst))
                        print(f"Archived: {file_path} -> {category}/{Path(file_path).name}")
                        archived_count += 1
                    except Exception as e:
                        print(f"Error archiving {file_path}: {e}")
    
    print(f"\nArchived {archived_count} files")
    
    # Create updated requirements.txt
    requirements_content = """# Core dependencies
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.6.0
seaborn>=0.12.0

# Google Cloud Platform
google-cloud-bigquery>=3.11.0
google-cloud-storage>=2.10.0
pandas-gbq>=0.19.0
pyarrow>=12.0.0
db-dtypes>=1.1.0

# Excel/Data handling
openpyxl>=3.1.0

# Spatial analysis
folium>=0.14.0
geopy>=2.3.0
haversine>=2.8.0

# Machine Learning (if needed)
scikit-learn>=1.3.0
scipy>=1.10.0

# Reporting
reportlab>=4.0.0
fpdf2>=2.7.0
markdown>=3.4.0

# Visualization
plotly>=5.14.0

# Development tools
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
"""
    
    req_path = project_root / "requirements.txt"
    with open(req_path, 'w') as f:
        f.write(requirements_content)
    print(f"\nUpdated requirements.txt")
    
    # Create/Update .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
gcp_env/
ENV/
.venv

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
data/raw/*.xlsx
data/raw/*.csv
!data/raw/Building_EUI_Targets.csv
!data/raw/MAITargetSummary Report.csv
!data/raw/MAIPropertyUseTypes Report.csv
outputs/reports/*.pdf
outputs/reports/*.html
*.log
.env
secrets/

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Test results
test_results/
.coverage
htmlcov/
.pytest_cache/

# Temporary files
*.tmp
*.temp
*.bak
*.backup

# BigQuery exports
src/utils/data/gcp_exports/
"""
    
    gitignore_path = project_root / ".gitignore"
    with open(gitignore_path, 'w') as f:
        f.write(gitignore_content)
    print("\nUpdated .gitignore")
    
    # Create project structure documentation
    structure_doc = """# Project Structure

```
500_ED_Risk_Retro_BP/
├── data/                      # Data storage
│   ├── raw/                   # Original ED datasets
│   ├── processed/             # Cleaned and merged data
│   └── interim/               # Intermediate processing
│
├── src/                       # Source code
│   ├── analysis/              # Building and portfolio analysis
│   │   ├── building_compliance_analyzer_v2.py
│   │   ├── integrated_tes_hp_analyzer.py
│   │   └── portfolio_risk_analyzer.py
│   │
│   ├── analytics/             # Spatial and clustering analysis
│   │   ├── der_clustering_analysis.py
│   │   └── cluster_analysis_bigquery.py
│   │
│   ├── config/                # Configuration management
│   │   └── project_config.py
│   │
│   ├── data_processing/       # Data loaders
│   │   ├── enhanced_comprehensive_loader.py
│   │   └── comprehensive_data_merger.py
│   │
│   ├── gcp/                   # Google Cloud integration
│   │   ├── load_data_and_calculate.py
│   │   ├── create_opt_in_decision_model.py
│   │   └── queries/           # SQL queries
│   │
│   ├── models/                # Financial and system models
│   │   ├── tes_hp_cash_flow_bridge.py
│   │   ├── hvac_system_impact_modeler.py
│   │   └── bridge_loan_investor_package.py
│   │
│   └── utils/                 # Helper utilities
│       ├── penalty_calculator.py     # Core penalty calculations
│       ├── mai_data_loader.py        # MAI building handling
│       ├── eui_target_loader.py      # Target loading
│       └── year_normalization.py     # Year calculations
│
├── tests/                     # Test suite
│   ├── test_integration_suite.py
│   ├── test_python_bigquery_consistency.py
│   └── run_all_tests.py
│
├── docs/                      # Documentation
│   ├── handoffs/              # Session handoff documents
│   └── penalty_calculation_source_of_truth.md
│
├── notebooks/                 # Jupyter notebooks
│
├── outputs/                   # Generated outputs
│   ├── reports/               # Analysis reports
│   └── visualizations/        # Maps and charts
│
├── archive/                   # Archived code and docs
│
├── references/                # Policy documents
│
├── README.md                  # Project overview
├── PROJECT_KNOWLEDGE.md       # Detailed knowledge base
├── requirements.txt           # Python dependencies
└── .gitignore                # Git ignore rules
```
"""
    
    structure_path = project_root / "docs" / "project_structure.md"
    structure_path.parent.mkdir(exist_ok=True)
    with open(structure_path, 'w') as f:
        f.write(structure_doc)
    print("\nCreated project structure documentation")
    
    # Summary report
    print("\n" + "="*60)
    print("CLEANUP SUMMARY")
    print("="*60)
    print(f"Files archived: {archived_count}")
    print("Updated files:")
    print("  - requirements.txt")
    print("  - .gitignore") 
    print("  - docs/project_structure.md")
    print(f"\nArchive location: {archive_dir.relative_to(project_root)}")
    print("\nNext steps:")
    print("1. Review archived files in case any are still needed")
    print("2. Run 'pip install -r requirements.txt' to update dependencies")
    print("3. Update README.md and PROJECT_KNOWLEDGE.md as needed")
    print("4. Commit changes to git")
    
    return archive_dir


if __name__ == "__main__":
    organize_project()
