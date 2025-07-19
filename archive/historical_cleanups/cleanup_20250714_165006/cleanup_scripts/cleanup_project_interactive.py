#!/usr/bin/env python3
"""
Interactive cleanup script with dry-run and execute modes
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
            f"archive/cleanup_{self.timestamp}/documentation"
        ]
        
        for dir_path in archive_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {dir_path}")
            
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
    
    def count_files_to_archive(self, files_to_archive):
        """Count how many files will actually be moved"""
        count = 0
        for category, file_list in files_to_archive.items():
            for file_path in file_list:
                if (self.project_root / file_path).exists():
                    count += 1
        return count
    
    def archive_files(self, files_to_archive, dry_run=True):
        """Archive identified files"""
        moved_count = 0
        for category, file_list in files_to_archive.items():
            for file_path in file_list:
                source = self.project_root / file_path
                if source.exists():
                    dest_dir = self.project_root / f"archive/cleanup_{self.timestamp}" / category
                    dest = dest_dir / source.name
                    
                    if dry_run:
                        print(f"  📄 {file_path} → archive/{category}/")
                        self.moves.append({
                            "source": str(file_path),
                            "destination": f"archive/cleanup_{self.timestamp}/{category}/{source.name}",
                            "category": category
                        })
                    else:
                        shutil.move(str(source), str(dest))
                        print(f"  ✅ Moved: {file_path}")
                        moved_count += 1
        
        if not dry_run:
            print(f"\n✅ Successfully moved {moved_count} files to archive")
                        
    def generate_cleanup_report(self, files_to_archive, active_files, dry_run=True):
        """Generate a detailed cleanup report"""
        report_path = self.project_root / f"cleanup_report_{self.timestamp}.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# Project Cleanup Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode: {'DRY RUN' if dry_run else 'EXECUTED'}\n\n")
            
            f.write("## Summary\n")
            f.write(f"- Files archived: {self.count_files_to_archive(files_to_archive)}\n")
            f.write(f"- Files kept active: {sum(len(files) for files in active_files.values())}\n")
            f.write(f"- Archive location: `archive/cleanup_{self.timestamp}/`\n\n")
            
            f.write("## Files Archived\n\n")
            for category, files in files_to_archive.items():
                f.write(f"### {category.replace('_', ' ').title()}\n")
                for file in files:
                    if (self.project_root / file).exists():
                        f.write(f"- {file}\n")
                f.write("\n")
            
            f.write("## Active Files Kept\n\n")
            for category, files in active_files.items():
                f.write(f"### {category}\n")
                for file in files:
                    f.write(f"- {file}\n")
                f.write("\n")
        
        print(f"📊 Report saved: {report_path}")
        return report_path
    
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
            "Utilities": [
                "src/utils/local_gcp_bridge.py",
                "src/utils/mai_data_loader.py",
                "src/utils/penalty_calculator.py"
            ]
        }
        
        return active_files

def main():
    """Main cleanup function"""
    project_root = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP"
    
    print("\n🧹 Energize Denver Project Cleanup Tool")
    print("=" * 50)
    
    cleaner = ProjectCleanup(project_root)
    
    # Identify files
    files_to_archive = cleaner.identify_files_to_archive()
    active_files = cleaner.identify_active_files()
    
    # Show summary
    files_count = cleaner.count_files_to_archive(files_to_archive)
    print(f"\n📊 Cleanup Summary:")
    print(f"   • Files to archive: {files_count}")
    print(f"   • Files to keep active: {sum(len(files) for files in active_files.values())}")
    print(f"   • Archive location: archive/cleanup_{cleaner.timestamp}/")
    
    # Dry run
    print("\n📋 Files that will be moved:")
    print("-" * 50)
    cleaner.archive_files(files_to_archive, dry_run=True)
    
    # Ask for confirmation
    print("\n" + "=" * 50)
    response = input("\n❓ Do you want to execute the cleanup? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        print("\n🚀 Executing cleanup...")
        print("-" * 50)
        
        # Create archive structure
        cleaner.create_archive_structure()
        
        # Execute moves
        cleaner.archive_files(files_to_archive, dry_run=False)
        
        # Generate report
        report_path = cleaner.generate_cleanup_report(files_to_archive, active_files, dry_run=False)
        
        print("\n✨ Cleanup complete!")
        print(f"   • Moved {files_count} files to archive")
        print(f"   • Report saved to: {report_path}")
        print("\n💡 Next steps:")
        print("   1. Review the cleanup report")
        print("   2. Update any broken imports")
        print("   3. Continue with EUI target loader development")
        
    else:
        print("\n❌ Cleanup cancelled")
        print("   • No files were moved")
        print("   • You can run this script again anytime")
        
        # Still generate a dry-run report
        report_path = cleaner.generate_cleanup_report(files_to_archive, active_files, dry_run=True)
        print(f"   • Dry-run report saved to: {report_path}")

if __name__ == "__main__":
    main()
