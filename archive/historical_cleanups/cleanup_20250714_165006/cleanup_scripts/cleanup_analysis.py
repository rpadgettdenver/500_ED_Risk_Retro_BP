#!/usr/bin/env python3
"""
Suggested file name: cleanup_analysis.py
Directory location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Analyze project structure and identify cleanup opportunities
"""

import os
import re
from collections import defaultdict
from pathlib import Path
import json

def analyze_project_structure():
    """Analyze project and identify cleanup opportunities"""
    
    project_root = Path("/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP")
    
    # Categories for organization
    analysis = {
        "test_files_in_root": [],
        "backup_files": [],
        "duplicate_scripts": [],
        "cleanup_scripts": [],
        "imports_found": defaultdict(set),
        "archive_candidates": [],
        "gcp_specific_files": [],
        "active_modules": []
    }
    
    # Standard library modules to exclude
    standard_lib = {
        'os', 'sys', 'json', 'datetime', 'math', 'csv', 'logging', 'warnings',
        'pathlib', 'time', 'copy', 'collections', 'typing', 'io', 're', 'shutil',
        'tempfile', 'subprocess', 'platform', 'argparse', 'configparser', 'ast',
        'functools', 'itertools', 'pickle', 'hashlib', 'uuid', 'random'
    }
    
    # Walk through project
    for root, dirs, files in os.walk(project_root):
        # Skip certain directories
        if any(skip in root for skip in ['gcp_env', '.git', '__pycache__', '.idea']):
            continue
            
        rel_root = Path(root).relative_to(project_root)
        
        for file in files:
            filepath = Path(root) / file
            rel_path = filepath.relative_to(project_root)
            
            # Categorize files
            if file.endswith('.py'):
                # Test files in root
                if root == str(project_root) and file.startswith('test_'):
                    analysis["test_files_in_root"].append(str(rel_path))
                
                # Backup files
                if '.backup' in file or file.endswith('_backup.py'):
                    analysis["backup_files"].append(str(rel_path))
                
                # Cleanup scripts
                if 'cleanup' in file or 'fix_' in file:
                    analysis["cleanup_scripts"].append(str(rel_path))
                
                # Extract imports
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find imports
                    import_matches = re.findall(r'^\s*(?:from\s+(\S+)\s+)?import\s+(.+)$', 
                                               content, re.MULTILINE)
                    
                    for from_module, import_items in import_matches:
                        if from_module:
                            base_module = from_module.split('.')[0]
                            if base_module not in standard_lib and not base_module.startswith('src'):
                                analysis["imports_found"][base_module].add(str(rel_path))
                        else:
                            items = import_items.split(',')
                            for item in items:
                                module = item.strip().split(' as ')[0].split('.')[0]
                                if module not in standard_lib and not module.startswith('src'):
                                    analysis["imports_found"][module].add(str(rel_path))
                
                except Exception:
                    pass
                
                # Check if it's an active module
                if str(rel_path).startswith('src/') and not any(x in file for x in ['__pycache__', '.pyc']):
                    analysis["active_modules"].append(str(rel_path))
    
    # Identify duplicate functionality
    duplicate_patterns = {
        'der_clustering': ['der_clustering', 'cluster_analysis'],
        'data_loading': ['loader', 'load_data'],
        'penalty_fixing': ['fix_penalty', 'penalty_rate']
    }
    
    for pattern_name, keywords in duplicate_patterns.items():
        matches = []
        for root, dirs, files in os.walk(project_root / 'src'):
            for file in files:
                if file.endswith('.py') and any(kw in file.lower() for kw in keywords):
                    matches.append(str(Path(root).relative_to(project_root) / file))
        if len(matches) > 1:
            analysis["duplicate_scripts"].extend(matches)
    
    return analysis


def generate_cleanup_report():
    """Generate a cleanup report"""
    
    analysis = analyze_project_structure()
    
    report = []
    report.append("# Project Cleanup Analysis Report")
    report.append("=" * 60)
    
    # Test files in root
    if analysis["test_files_in_root"]:
        report.append("\n## Test Files in Root Directory (Should Move to tests/)")
        for file in analysis["test_files_in_root"]:
            report.append(f"- {file}")
    
    # Backup files
    if analysis["backup_files"]:
        report.append("\n## Backup Files (Consider Archiving)")
        for file in analysis["backup_files"]:
            report.append(f"- {file}")
    
    # Cleanup scripts
    if analysis["cleanup_scripts"]:
        report.append("\n## Cleanup/Fix Scripts (May Be Obsolete)")
        for file in sorted(set(analysis["cleanup_scripts"])):
            report.append(f"- {file}")
    
    # Duplicate scripts
    if analysis["duplicate_scripts"]:
        report.append("\n## Potentially Duplicate Functionality")
        for file in sorted(set(analysis["duplicate_scripts"])):
            report.append(f"- {file}")
    
    # Required packages
    report.append("\n## Required Python Packages")
    report.append("Based on imports found in the codebase:")
    for package in sorted(analysis["imports_found"].keys()):
        count = len(analysis["imports_found"][package])
        report.append(f"- {package} (used in {count} files)")
    
    # Recommended requirements.txt
    report.append("\n## Recommended requirements.txt")
    report.append("```")
    
    # Map common import names to package names
    package_mapping = {
        'google': 'google-cloud-bigquery\ngoogle-cloud-storage',
        'pandas': 'pandas>=2.0.0',
        'numpy': 'numpy>=1.24.0',
        'matplotlib': 'matplotlib>=3.6.0',
        'seaborn': 'seaborn>=0.12.0',
        'openpyxl': 'openpyxl>=3.1.0',
        'sklearn': 'scikit-learn>=1.3.0',
        'scipy': 'scipy>=1.10.0',
        'folium': 'folium>=0.14.0',
        'plotly': 'plotly>=5.14.0',
        'pyarrow': 'pyarrow>=12.0.0',
        'db_dtypes': 'db-dtypes>=1.1.0',
        'pandas_gbq': 'pandas-gbq>=0.19.0',
        'reportlab': 'reportlab>=4.0.0',
        'fpdf': 'fpdf2>=2.7.0',
        'markdown': 'markdown>=3.4.0',
        'geopy': 'geopy>=2.3.0',
        'haversine': 'haversine>=2.8.0'
    }
    
    seen_packages = set()
    for import_name in sorted(analysis["imports_found"].keys()):
        if import_name in package_mapping:
            packages = package_mapping[import_name].split('\n')
            for pkg in packages:
                if pkg not in seen_packages:
                    report.append(pkg)
                    seen_packages.add(pkg)
        else:
            # Use the import name as-is if not in mapping
            if import_name not in seen_packages:
                report.append(import_name)
                seen_packages.add(import_name)
    
    report.append("```")
    
    # Active modules summary
    report.append("\n## Active Source Modules")
    report.append(f"Total active modules: {len(analysis['active_modules'])}")
    
    # Save report
    report_content = '\n'.join(report)
    
    with open('cleanup_report.md', 'w') as f:
        f.write(report_content)
    
    print(report_content)
    
    return analysis


if __name__ == "__main__":
    print("Analyzing project structure...")
    analysis = generate_cleanup_report()
    print(f"\nReport saved to cleanup_report.md")
    
    # Generate archive recommendations
    archive_files = (
        analysis["test_files_in_root"] + 
        analysis["backup_files"] + 
        [f for f in analysis["cleanup_scripts"] if 'cleanup_project' in f or 'fix_imports' in f]
    )
    
    if archive_files:
        print("\n\nRecommended files to archive:")
        print("=" * 40)
        for file in sorted(set(archive_files)):
            print(f"  {file}")
