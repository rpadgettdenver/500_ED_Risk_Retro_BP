#!/usr/bin/env python3
"""
Suggested file name: cleanup_project_structure.py
Directory Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
USE: Reorganize project structure by archiving outdated scripts and organizing active modules

This script will:
1. Create organized archive directories
2. Move outdated/duplicate scripts to archive
3. Update import statements if needed
4. Create a cleanup report
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import json

class ProjectCleanup:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.archive_root = self.project_root / "archive"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.moves = []
        self.kept_files = []
        
    def create_archive_structure(self):
        """Create organized archive directories"""
        archive_dirs = [
            f"archive/cleanup_{self.timestamp}",
            f"archive/cleanup_{self.timestamp}/root_scripts",
            f"archive/cleanup_{self.timestamp}/old_versions",
            f"archive/cleanup_{self.timestamp}/test_scripts",
            f"archive/cleanup_{self.timestamp}/gcp_duplicates",
            f"archive/cleanup_{self.timestamp}/deprecated_analysis"
        ]
        
        for dir_path in archive_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {dir_path}")
            
    def identify_files_to_archive(self):
        """Identify which files should be archived"""
        files_to_archive = {
            # Root level scripts that should be archived
            "root_scripts": [
                "fix_penalty_rates.py",
                "fix_penalty_rates_v2.py",
                "run_analysis.py",  # Replaced by run_unified_analysis_v2.py
                "run_unified_analysis.py",  # Old version
                "test_config_values.py",  # Should be in tests/
                "test_enhanced_analysis.py",  # Should be in tests/
                "check_requirements.py",  # One-time utility
                "setup_project_structure.sh",  # Already completed
                "organize_and_setup.sh",  # Already completed
            ],
            
            # Old versions and duplicates
            "old_versions": [
                "src/analysis/building_compliance_analyzer.py",  # Keep v2
                "src/gcp/create_penalty_view.py",  # Keep fixed version
                "src/gcp/export_high_value_buildings.py",  # Keep v3_fixed
                "src/gcp/export_high_value_buildings_enhanced.py",
                "src/gcp/export_high_value_buildings_enhanced_v2.py",
                "src/gcp/export_high_value_buildings_enhanced_v3.py",
                "src/gcp/load_data_and_calculate_old.py",
                "src/analytics/enhanced_der_clustering.py",  # Keep fixed version
            ],
            
            # Test/check scripts that should be in different locations
            "test_scripts": [
                "src/analysis/check_columns.py",
                "src/analysis/extract_building_2952.py",
                "src/analysis/test_building_2952.py",
                "src/gcp/check_consumption_schema.py",
                "src/gcp/check_penalty_math.py",
                "src/utils/check_bigquery_columns.py",
                "src/utils/check_columns.py",
                "src/utils/check_data_availability.py",
                "src/utils/test_bridge_connection.py",
                "src/test_unified_config.py",
            ],
            
            # Duplicate handoff/knowledge files
            "documentation": [
                "project_handoff.md",  # Keep project_handoff(rev1).md
                "project_knowledge.txt",  # Keep PROJECT_KNOWLEDGE.md
                "READMEtxt.txt",  # Keep README.md
            ]
        }
        
        return files_to_archive
    
    def archive_files(self, files_to_archive, dry_run=True):
        """Archive identified files"""
        for category, file_list in files_to_archive.items():
            for file_path in file_list:
                source = self.project_root / file_path
                if source.exists():
                    dest_dir = self.project_root / f"archive/cleanup_{self.timestamp}" / category
                    dest = dest_dir / source.name
                    
                    if dry_run:
                        print(f"Would move: {file_path} -> archive/cleanup_{self.timestamp}/{category}/")
                        self.moves.append({
                            "source": str(file_path),
                            "destination": f"archive/cleanup_{self.timestamp}/{category}/{source.name}",
                            "category": category
                        })
                    else:
                        shutil.move(str(source), str(dest))
                        print(f"Moved: {file_path} -> {dest}")
                        
    def identify_active_files(self):
        """Identify files that should remain in the active structure"""
        active_files = {
            "Core Scripts": [
                "generate_developer_returns_report.py",
                "run_unified_analysis_v2.py",
                "setup.py"
            ],
            "Configuration": [
                "src/config/project_config.py"
            ],
            "Analysis Modules": [
                "src/analysis/building_compliance_analyzer_v2.py",
                "src/analysis/integrated_tes_hp_analyzer.py"
            ],
            "Analytics": [
                "src/analytics/cluster_analysis_bigquery.py",
                "src/analytics/der_clustering_analysis.py",
                "src/analytics/fixed_enhanced_der_clustering.py",
                "src/analytics/integrate_epb_data.py",
                "src/analytics/run_der_clustering.py",
                "src/analytics/visualize_epb_clusters.py"
            ],
            "Data Processing": [
                "src/data_processing/comprehensive_data_merger.py",
                "src/data_processing/comprehensive_energy_loader.py",
                "src/data_processing/enhanced_comprehensive_loader.py"
            ],
            "GCP Integration": [
                "src/gcp/create_opt_in_decision_model.py",
                "src/gcp/create_penalty_analysis_corrected.py",
                "src/gcp/create_penalty_view_fixed.py",
                "src/gcp/export_high_value_buildings_enhanced_v3_fixed.py",
                "src/gcp/fix_42_cap_and_yearwise_exemptions.py",
                "src/gcp/fix_bigquery_penalty_rates.py",
                "src/gcp/gcp_migration_setup.py",
                "src/gcp/load_data_and_calculate.py",
                "src/gcp/load_excel_consumption_data.py",
                "src/gcp/load_geographic_data.py",
                "src/gcp/rerun_and_compare_analysis.py"
            ],
            "Models": [
                "src/models/bridge_loan_investor_package.py",
                "src/models/financial_model_bigquery.py",
                "src/models/hvac_system_impact_modeler.py",
                "src/models/tes_hp_cash_flow_bridge.py"
            ],
            "Utilities": [
                "src/utils/local_gcp_bridge.py",
                "src/utils/mai_data_loader.py",
                "src/utils/penalty_calculator.py"
            ],
            "Tests": [
                "tests/test_mai_target_calculations.py",
                "tests/unit/test_penalty_calculations.py"
            ]
        }
        
        return active_files
    
    def create_recommended_structure(self):
        """Create a recommended new directory structure"""
        recommended_dirs = [
            "src/scripts",  # For one-time scripts
            "src/notebooks",  # For Jupyter notebooks
            "docs/technical",  # For technical documentation
            "docs/business",  # For business documentation
            "tests/scripts",  # For test/check scripts
        ]
        
        for dir_path in recommended_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                print(f"Recommend creating: {dir_path}")
                
    def generate_cleanup_report(self, files_to_archive, active_files, dry_run=True):
        """Generate a detailed cleanup report"""
        report_path = self.project_root / f"cleanup_report_{self.timestamp}.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# Project Cleanup Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode: {'DRY RUN' if dry_run else 'EXECUTED'}\n\n")
            
            f.write("## Files to Archive\n\n")
            total_to_archive = 0
            for category, files in files_to_archive.items():
                f.write(f"### {category.replace('_', ' ').title()}\n")
                for file in files:
                    if (self.project_root / file).exists():
                        f.write(f"- {file}\n")
                        total_to_archive += 1
                f.write("\n")
            
            f.write(f"**Total files to archive: {total_to_archive}**\n\n")
            
            f.write("## Active Files to Keep\n\n")
            total_active = 0
            for category, files in active_files.items():
                f.write(f"### {category}\n")
                for file in files:
                    f.write(f"- {file}\n")
                    total_active += 1
                f.write("\n")
                
            f.write(f"**Total active files: {total_active}**\n\n")
            
            f.write("## Recommended Actions\n\n")
            f.write("1. Review the files marked for archiving\n")
            f.write("2. Run with `dry_run=False` to execute the cleanup\n")
            f.write("3. Update any import statements if needed\n")
            f.write("4. Consider reorganizing test scripts into proper test directories\n")
            f.write("5. Consolidate duplicate functionality where possible\n")
            
            if self.moves:
                f.write("\n## Planned Moves\n\n")
                f.write("| Source | Destination | Category |\n")
                f.write("|--------|-------------|----------|\n")
                for move in self.moves:
                    f.write(f"| {move['source']} | {move['destination']} | {move['category']} |\n")
        
        print(f"\nCleanup report generated: {report_path}")
        return report_path

def main():
    """Main cleanup function"""
    project_root = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP"
    
    print("🧹 Project Structure Cleanup Tool")
    print("=" * 50)
    
    cleaner = ProjectCleanup(project_root)
    
    # Create archive structure
    print("\n📁 Creating archive structure...")
    cleaner.create_archive_structure()
    
    # Identify files
    print("\n🔍 Analyzing project structure...")
    files_to_archive = cleaner.identify_files_to_archive()
    active_files = cleaner.identify_active_files()
    
    # Dry run first
    print("\n📋 Performing dry run...")
    cleaner.archive_files(files_to_archive, dry_run=True)
    
    # Generate report
    print("\n📊 Generating cleanup report...")
    report_path = cleaner.generate_cleanup_report(files_to_archive, active_files, dry_run=True)
    
    # Show recommendations
    print("\n💡 Recommendations:")
    cleaner.create_recommended_structure()
    
    print("\n✅ Dry run complete!")
    print(f"Review the report at: {report_path}")
    print("\nTo execute the cleanup, modify this script and set dry_run=False")
    
    # Ask for confirmation
    response = input("\nWould you like to see a summary of files to be moved? (y/n): ")
    if response.lower() == 'y':
        print("\n📦 Files to be archived:")
        for category, files in files_to_archive.items():
            existing_files = [f for f in files if (Path(project_root) / f).exists()]
            if existing_files:
                print(f"\n{category.replace('_', ' ').title()}:")
                for f in existing_files:
                    print(f"  - {f}")

if __name__ == "__main__":
    main()
