#!/usr/bin/env python3
"""
Suggested file name: final_cleanup.py
Directory location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Final cleanup - move test files and old scripts to archive
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_project():
    """Clean up project by archiving old files"""
    
    project_root = Path("/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create archive directory
    archive_dir = project_root / "archive" / f"cleanup_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to archive
    files_to_archive = [
        # Test files in root
        "test_2028_fix.py",
        "test_building_2952.py",
        "test_hvac_direct.py",
        "simple_hvac_test.py",
        "test_portfolio_quick.py",
        
        # Cleanup scripts
        "cleanup_project_interactive.py",
        "cleanup_project_structure.py",
        "cleanup_analysis.py",
        "organize_project_final.py",
        "fix_imports.sh",
        "fix_imports_corrected.sh",
        "fix_remaining_issues.py",
        "organize_and_setup.sh",
        "setup_project_structure.sh",
        
        # Old runners
        "run_portfolio_analysis_corrected.py",
        "run_unified_analysis_v2.py.backup",
        "portfolio_summary.py",
        "check_imports.py",
        
        # Old reports
        "cleanup_report_20250713_063841.md",
        "cleanup_report_20250713_064506.md",
        "project_summary.md"
    ]
    
    # Also find backup files in src
    for root, dirs, files in os.walk(project_root / "src"):
        for file in files:
            if '.backup' in file:
                rel_path = Path(root).relative_to(project_root) / file
                files_to_archive.append(str(rel_path))
    
    # Archive files
    archived = []
    for file_path in files_to_archive:
        src = project_root / file_path
        if src.exists():
            # Determine subdirectory
            if 'test_' in file_path and file_path.endswith('.py'):
                subdir = "test_files"
            elif 'cleanup' in file_path or 'fix_' in file_path:
                subdir = "cleanup_scripts"
            elif '.backup' in file_path:
                subdir = "backup_files"
            else:
                subdir = "old_scripts"
            
            # Create subdirectory
            (archive_dir / subdir).mkdir(exist_ok=True)
            
            # Move file
            dst = archive_dir / subdir / Path(file_path).name
            try:
                shutil.move(str(src), str(dst))
                archived.append(file_path)
                print(f"✓ Archived: {file_path}")
            except Exception as e:
                print(f"✗ Error archiving {file_path}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Cleanup Summary:")
    print(f"{'='*60}")
    print(f"Files archived: {len(archived)}")
    print(f"Archive location: {archive_dir.relative_to(project_root)}")
    
    # Create archive README
    readme_content = f"""# Archive - {timestamp}

This directory contains files archived during project cleanup.

## Contents

### test_files/
Test scripts that were in the root directory. These have been moved here because proper tests are now in the tests/ directory.

### cleanup_scripts/
Various cleanup and fix scripts that are no longer needed.

### old_scripts/
Old runner scripts and utilities that have been replaced.

### backup_files/
Backup files that were created during development.

## Files Archived
Total files: {len(archived)}

"""
    
    with open(archive_dir / "README.md", 'w') as f:
        f.write(readme_content)
        f.write("\nDetailed list:\n")
        for file in sorted(archived):
            f.write(f"- {file}\n")
    
    return archive_dir, archived

if __name__ == "__main__":
    print("Starting project cleanup...")
    archive_dir, archived_files = cleanup_project()
    print("\n✅ Cleanup complete!")
    print("\nNext steps:")
    print("1. Review archived files if needed")
    print("2. Run 'pip install -r requirements.txt' to ensure all dependencies")
    print("3. Commit changes to git")
