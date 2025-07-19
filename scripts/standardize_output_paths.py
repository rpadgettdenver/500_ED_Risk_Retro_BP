#!/usr/bin/env python3
"""
📁 Standardize Output Paths Script
Updates all scripts to use the organized output directory structure.

This script:
1. Scans all Python files for output operations
2. Updates paths to use standardized output directories:
   - /outputs/reports/ - for Excel, PDF, and report files
   - /outputs/data/ - for CSV and JSON data files
   - /outputs/temp/ - for temporary files
   - /outputs/exports/ - for export files
3. Creates a mapping of old vs new paths
4. Backs up modified files

Run with: python scripts/standardize_output_paths.py
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class OutputPathStandardizer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_dir = project_root / "backup_output_standardization"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.changes_log = []
        
        # Define output directory mappings
        self.output_mappings = {
            # Reports (Excel, PDF, HTML, MD)
            r"\.xlsx|\.pdf|\.html|\.md": "reports",
            # Data files (CSV, JSON)
            r"\.csv|\.json": "data", 
            # Images and visualizations
            r"\.png|\.jpg|\.jpeg|\.svg": "reports",
            # Temporary files
            r"_temp|temp_|temporary": "temp",
            # Export files
            r"export|Export": "exports"
        }
        
        # Files to process (exclude backups and archives)
        self.target_files = []
        self.find_target_files()
    
    def find_target_files(self):
        """Find all Python files that need path standardization"""
        exclude_dirs = {"backup_before_cleanup", "archive", "__pycache__", ".git", "gcp_env"}
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    self.target_files.append(file_path)
    
    def determine_output_subdir(self, file_path: str) -> str:
        """Determine which output subdirectory to use based on file extension"""
        file_path_lower = file_path.lower()
        
        # Check each mapping pattern
        for pattern, subdir in self.output_mappings.items():
            if re.search(pattern, file_path_lower):
                return subdir
        
        # Default to data for unmatched files
        return "data"
    
    def standardize_output_path(self, original_path: str) -> str:
        """Convert an output path to use standardized directory structure"""
        # Handle different path formats
        if "outputs/data/" in original_path:
            # Extract the filename part
            filename = os.path.basename(original_path)
            subdir = self.determine_output_subdir(filename)
            return f"outputs/data/{filename}"
        elif original_path.startswith("/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/data/"):
            # Handle absolute paths
            filename = os.path.basename(original_path)
            subdir = self.determine_output_subdir(filename)
            return f"/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/data/{filename}"
        else:
            # For other paths, add outputs prefix
            filename = os.path.basename(original_path)
            subdir = self.determine_output_subdir(filename)
            return f"outputs/data/{filename}"
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single file to standardize output paths"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes_made = []
            
            # Patterns to find and replace output paths
            patterns = [
                # Direct output directory references
                (r"os\.path\.join\(project_root,\s*['\"]outputs['\"](?:\s*,\s*['\"][^'\"]*['\"])?\)", 
                 self.replace_output_join),
                
                # String concatenation with outputs
                (r"['\"]outputs/[^'\"]*['\"]", self.replace_output_string),
                
                # Absolute paths to outputs
                (r"['\"][^'\"/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/data/[^"\"]*['\"]", 
                 self.replace_absolute_output),
                
                # Variable assignments with output paths
                (r"(\w+_path\s*=\s*[^'\"]*)(['\"]outputs/[^'\"]*['\"])", 
                 self.replace_variable_output),
            ]
            
            for pattern, replacer in patterns:
                matches = list(re.finditer(pattern, content))
                for match in reversed(matches):  # Reverse to maintain positions
                    old_text = match.group(0)
                    new_text = replacer(match)
                    if new_text != old_text:
                        content = content[:match.start()] + new_text + content[match.end():]
                        changes_made.append(f"'{old_text}' → '{new_text}'")
            
            # Only write if changes were made
            if content != original_content:
                # Create backup
                backup_path = self.backup_dir / file_path.relative_to(self.project_root)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_path)
                
                # Write updated content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.changes_log.append({
                    "file": str(file_path.relative_to(self.project_root)),
                    "changes": changes_made,
                    "backup": str(backup_path.relative_to(self.project_root))
                })
                
                print(f"✓ Updated: {file_path.relative_to(self.project_root)}")
                for change in changes_made:
                    print(f"  - {change}")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False
    
    def replace_output_join(self, match) -> str:
        """Replace os.path.join patterns with standardized paths"""
        original = match.group(0)
        
        # Extract any subdirectory from the join
        subdir_match = re.search(r"['\"]([^'\"]+)['\"](?:\s*\))?$", original)
        if subdir_match:
            subdir = subdir_match.group(1)
            if subdir in ["reports", "data", "temp", "exports"]:
                return original  # Already standardized
            else:
                # Determine appropriate subdir
                new_subdir = self.determine_output_subdir(subdir)
                return f"os.path.join(project_root, 'outputs', 'data')"
        
        return "os.path.join(project_root, 'outputs', 'data')"
    
    def replace_output_string(self, match) -> str:
        """Replace output string literals"""
        original = match.group(0)
        path = original.strip("'\"")
        
        # Extract filename and determine subdir
        filename = os.path.basename(path)
        subdir = self.determine_output_subdir(filename)
        
        quote_char = original[0]
        return f"{quote_char}outputs/{subdir}/{filename}{quote_char}"
    
    def replace_absolute_output(self, match) -> str:
        """Replace absolute output paths"""
        original = match.group(0)
        path = original.strip("'\"")
        
        # Extract filename and determine subdir
        filename = os.path.basename(path)
        subdir = self.determine_output_subdir(filename)
        
        quote_char = original[0]
        base_path = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP"
        return f"{quote_char}{base_path}/outputs/{subdir}/{filename}{quote_char}"
    
    def replace_variable_output(self, match) -> str:
        """Replace variable assignments with output paths"""
        prefix = match.group(1)
        path_part = match.group(2)
        
        # Process the path part
        path = path_part.strip("'\"")
        filename = os.path.basename(path)
        subdir = self.determine_output_subdir(filename)
        
        quote_char = path_part[0]
        new_path = f"{quote_char}outputs/{subdir}/{filename}{quote_char}"
        
        return prefix + new_path
    
    def create_output_config(self):
        """Create a configuration file for output paths"""
        config_content = '''"""
Output Directory Configuration
Generated by standardize_output_paths.py

This module provides standardized output paths for the project.
"""

import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Standardized output directories
OUTPUT_DIRS = {
    "reports": PROJECT_ROOT / "outputs" / "reports",
    "data": PROJECT_ROOT / "outputs" / "data", 
    "temp": PROJECT_ROOT / "outputs" / "temp",
    "exports": PROJECT_ROOT / "outputs" / "exports"
}

def get_output_path(filename: str, output_type: str = None) -> str:
    """
    Get standardized output path for a file.
    
    Args:
        filename: Name of the output file
        output_type: Type of output ('reports', 'data', 'temp', 'exports')
                    If None, will be determined from filename
    
    Returns:
        Full path to the output file
    """
    if output_type is None:
        # Determine type from filename
        if any(ext in filename.lower() for ext in ['.xlsx', '.pdf', '.html', '.md', '.png']):
            output_type = 'reports'
        elif any(ext in filename.lower() for ext in ['.csv', '.json']):
            output_type = 'data'
        elif 'temp' in filename.lower():
            output_type = 'temp'
        elif 'export' in filename.lower():
            output_type = 'exports'
        else:
            output_type = 'data'
    
    # Ensure directory exists
    OUTPUT_DIRS[output_type].mkdir(parents=True, exist_ok=True)
    
    return str(OUTPUT_DIRS[output_type] / filename)

def ensure_output_dirs():
    """Ensure all output directories exist"""
    for dir_path in OUTPUT_DIRS.values():
        dir_path.mkdir(parents=True, exist_ok=True)
'''
        
        config_path = self.project_root / "src" / "config" / "output_paths.py"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        print(f"✓ Created output configuration: {config_path.relative_to(self.project_root)}")
    
    def run_standardization(self):
        """Execute the full standardization process"""
        print("📁 Starting Output Path Standardization")
        print("=" * 50)
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        print(f"🔄 Backup directory: {self.backup_dir.relative_to(self.project_root)}")
        
        # Process all files
        files_changed = 0
        for file_path in self.target_files:
            if self.process_file(file_path):
                files_changed += 1
        
        # Create output configuration
        self.create_output_config()
        
        # Save changes log
        import json
        log_path = self.project_root / f"output_standardization_log_{self.timestamp}.json"
        with open(log_path, 'w') as f:
            json.dump(self.changes_log, f, indent=2)
        
        print(f"\n✅ Standardization completed!")
        print(f"📊 Files processed: {len(self.target_files)}")
        print(f"📝 Files changed: {files_changed}")
        print(f"📋 Log saved: {log_path.relative_to(self.project_root)}")
        print(f"🔄 Backups available: {self.backup_dir.relative_to(self.project_root)}")

def main():
    """Main execution function"""
    project_root = Path(__file__).resolve().parent.parent
    
    print(f"Project root: {project_root}")
    print("🚀 Running output path standardization...")
    
    # Run standardization
    standardizer = OutputPathStandardizer(project_root)
    standardizer.run_standardization()

if __name__ == "__main__":
    main()
