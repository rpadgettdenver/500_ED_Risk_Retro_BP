#!/usr/bin/env python3
"""
🧹 Automated Project Cleanup Script
Safely reorganizes the ED Risk Retro BP project structure with backup.

This script:
1. Creates a backup of the current state
2. Identifies the active portfolio analysis script
3. Moves deprecated scripts to archive
4. Consolidates dependency management
5. Reorganizes directory structure
6. Provides rollback capability

Run with: python scripts/automated_cleanup.py
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

class ProjectCleanup:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_dir = project_root / "backup_before_cleanup"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.cleanup_log = []
        
    def log_action(self, action: str, details: str = ""):
        """Log cleanup actions for rollback capability"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        self.cleanup_log.append(entry)
        print(f"✓ {action}: {details}")
    
    def create_backup(self):
        """Create a full backup before making changes"""
        print(f"🔄 Creating backup at {self.backup_dir}")
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        # Files/dirs to backup (exclude large/unnecessary items)
        backup_items = [
            "src", "scripts", "tests", "docs", "config", "notebooks",
            "requirements.txt", "pyproject.toml", "setup.py", 
            "README.md", "PROJECT_KNOWLEDGE.md", ".gitignore",
            # Portfolio analysis scripts
            "run_comprehensive_portfolio_analysis.py",
            "run_improved_portfolio_analysis.py",
            "run_mai_portfolio_analysis.py", 
            "run_portfolio_analysis_v3.py",
            "run_refined_portfolio_analysis.py",
            "execute_portfolio_analysis.py",
            # Other root scripts
            "archive_for_claude.py", "check_data_freshness.py",
            "find_and_view_png_files.py", "mai_penalty_debugger.py",
            "test_mai_penalty_calculations.py", "final_cleanup.py",
            "generate_developer_returns_report.py"
        ]
        
        for item in backup_items:
            src_path = self.project_root / item
            if src_path.exists():
                dst_path = self.backup_dir / item
                if src_path.is_dir():
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dst_path)
        
        self.log_action("BACKUP_CREATED", f"Backup saved to {self.backup_dir}")
    
    def identify_active_portfolio_script(self) -> str:
        """Identify which portfolio analysis script is most current"""
        portfolio_scripts = [
            "run_comprehensive_portfolio_analysis.py",
            "run_improved_portfolio_analysis.py", 
            "run_mai_portfolio_analysis.py",
            "run_portfolio_analysis_v3.py",
            "run_refined_portfolio_analysis.py",
            "execute_portfolio_analysis.py"
        ]
        
        # Check modification times and file sizes
        script_info = {}
        for script in portfolio_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                stat = script_path.stat()
                script_info[script] = {
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                    "path": script_path
                }
        
        if not script_info:
            return None
            
        # Find most recently modified script
        active_script = max(script_info.keys(), key=lambda x: script_info[x]["mtime"])
        
        self.log_action("ACTIVE_SCRIPT_IDENTIFIED", active_script)
        return active_script
    
    def consolidate_portfolio_scripts(self):
        """Move deprecated portfolio scripts to archive"""
        active_script = self.identify_active_portfolio_script()
        if not active_script:
            self.log_action("WARNING", "No portfolio scripts found")
            return
            
        # Create deprecated scripts directory
        deprecated_dir = self.project_root / "archive" / "deprecated_scripts"
        deprecated_dir.mkdir(parents=True, exist_ok=True)
        
        portfolio_scripts = [
            "run_comprehensive_portfolio_analysis.py",
            "run_improved_portfolio_analysis.py",
            "run_mai_portfolio_analysis.py", 
            "run_portfolio_analysis_v3.py",
            "run_refined_portfolio_analysis.py",
            "execute_portfolio_analysis.py"
        ]
        
        moved_count = 0
        for script in portfolio_scripts:
            if script != active_script:
                src_path = self.project_root / script
                if src_path.exists():
                    dst_path = deprecated_dir / f"{script}.{self.timestamp}"
                    shutil.move(str(src_path), str(dst_path))
                    moved_count += 1
                    self.log_action("SCRIPT_MOVED", f"{script} → archive/deprecated_scripts/")
        
        self.log_action("PORTFOLIO_CONSOLIDATION", f"Kept {active_script}, moved {moved_count} scripts")
    
    def reorganize_root_scripts(self):
        """Move miscellaneous scripts to appropriate directories"""
        script_moves = {
            "archive_for_claude.py": "scripts/",
            "check_data_freshness.py": "scripts/",
            "find_and_view_png_files.py": "scripts/",
            "mai_penalty_debugger.py": "scripts/debugging/",
            "test_mai_penalty_calculations.py": "tests/",
            "final_cleanup.py": "scripts/"
        }
        
        for script, target_dir in script_moves.items():
            src_path = self.project_root / script
            if src_path.exists():
                # Create target directory
                target_path = self.project_root / target_dir
                target_path.mkdir(parents=True, exist_ok=True)
                
                # Move file
                dst_path = target_path / script
                if not dst_path.exists():  # Don't overwrite existing files
                    shutil.move(str(src_path), str(dst_path))
                    self.log_action("SCRIPT_RELOCATED", f"{script} → {target_dir}")
    
    def consolidate_dependency_management(self):
        """Choose pyproject.toml over requirements.txt and remove conflicts"""
        req_file = self.project_root / "requirements.txt"
        pyproject_file = self.project_root / "pyproject.toml"
        
        if req_file.exists() and pyproject_file.exists():
            # Move requirements.txt to archive
            archive_path = self.project_root / "archive" / f"requirements.txt.{self.timestamp}"
            shutil.move(str(req_file), str(archive_path))
            self.log_action("DEPENDENCY_CONSOLIDATION", "Moved requirements.txt to archive, using pyproject.toml")
    
    def consolidate_archive_cleanups(self):
        """Consolidate multiple cleanup folders in archive"""
        archive_dir = self.project_root / "archive"
        if not archive_dir.exists():
            return
            
        cleanup_dirs = [d for d in archive_dir.iterdir() 
                       if d.is_dir() and d.name.startswith("cleanup_")]
        
        if len(cleanup_dirs) > 1:
            # Create consolidated directory
            consolidated_dir = archive_dir / "historical_cleanups"
            consolidated_dir.mkdir(exist_ok=True)
            
            for cleanup_dir in cleanup_dirs:
                target_dir = consolidated_dir / cleanup_dir.name
                shutil.move(str(cleanup_dir), str(target_dir))
                self.log_action("ARCHIVE_CONSOLIDATED", f"{cleanup_dir.name} → historical_cleanups/")
    
    def organize_outputs(self):
        """Create organized structure in outputs directory"""
        outputs_dir = self.project_root / "outputs"
        if not outputs_dir.exists():
            return
            
        # Create subdirectories
        subdirs = ["reports", "data", "temp", "exports"]
        for subdir in subdirs:
            (outputs_dir / subdir).mkdir(exist_ok=True)
        
        self.log_action("OUTPUTS_ORGANIZED", "Created reports/, data/, temp/, exports/ subdirectories")
    
    def save_cleanup_log(self):
        """Save cleanup log for rollback purposes"""
        log_file = self.project_root / f"cleanup_log_{self.timestamp}.json"
        with open(log_file, 'w') as f:
            json.dump(self.cleanup_log, f, indent=2)
        
        print(f"\n📋 Cleanup log saved to: {log_file}")
        print(f"🔄 Backup available at: {self.backup_dir}")
    
    def run_cleanup(self):
        """Execute the full cleanup process"""
        print("🧹 Starting Automated Project Cleanup")
        print("=" * 50)
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Consolidate portfolio scripts
            self.consolidate_portfolio_scripts()
            
            # Step 3: Reorganize root scripts
            self.reorganize_root_scripts()
            
            # Step 4: Fix dependency management
            self.consolidate_dependency_management()
            
            # Step 5: Consolidate archive cleanups
            self.consolidate_archive_cleanups()
            
            # Step 6: Organize outputs
            self.organize_outputs()
            
            # Step 7: Save log
            self.save_cleanup_log()
            
            print("\n✅ Cleanup completed successfully!")
            print(f"📊 Total actions performed: {len(self.cleanup_log)}")
            
        except Exception as e:
            print(f"\n❌ Error during cleanup: {e}")
            print(f"🔄 Restore from backup: {self.backup_dir}")
            raise

def main():
    """Main execution function"""
    project_root = Path(__file__).resolve().parent.parent
    
    print(f"Project root: {project_root}")
    print("🚀 Running automated cleanup (user approved)...")
    
    # Run cleanup
    cleanup = ProjectCleanup(project_root)
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()
