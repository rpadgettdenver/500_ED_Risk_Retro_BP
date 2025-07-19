#!/usr/bin/env python3
"""
Suggested file name: check_imports.py
Directory Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
USE: Check all Python files for imports of archived modules and suggest fixes

This script will:
1. Scan all active Python files
2. Check for imports of archived modules
3. Suggest corrections
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class ImportChecker:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        
        # Map old modules to their replacements
        self.module_replacements = {
            # Old analyzer to new version
            'building_compliance_analyzer': 'building_compliance_analyzer_v2',
            
            # Old penalty scripts (should use penalty_calculator now)
            'fix_penalty_rates': 'utils.penalty_calculator',
            'fix_penalty_rates_v2': 'utils.penalty_calculator',
            
            # Old export scripts to latest version
            'export_high_value_buildings': 'export_high_value_buildings_enhanced_v3_fixed',
            'export_high_value_buildings_enhanced': 'export_high_value_buildings_enhanced_v3_fixed',
            'export_high_value_buildings_enhanced_v2': 'export_high_value_buildings_enhanced_v3_fixed',
            'export_high_value_buildings_enhanced_v3': 'export_high_value_buildings_enhanced_v3_fixed',
            
            # Old clustering to fixed version
            'enhanced_der_clustering': 'fixed_enhanced_der_clustering',
            
            # Old run scripts
            'run_analysis': 'run_unified_analysis_v2',
            'run_unified_analysis': 'run_unified_analysis_v2',
        }
        
        # Files that were moved to tests directory
        self.moved_to_tests = [
            'check_columns',
            'extract_building_2952',
            'test_building_2952',
            'check_consumption_schema',
            'check_penalty_math',
            'test_config_values',
            'test_enhanced_analysis',
        ]
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in src directory"""
        python_files = []
        for root, dirs, files in os.walk(self.project_root / 'src'):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
                    
        # Also check root directory scripts
        for file in ['generate_developer_returns_report.py', 
                     'run_unified_analysis_v2.py']:
            path = self.project_root / file
            if path.exists():
                python_files.append(path)
                
        return python_files
    
    def check_imports(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Check a file for problematic imports"""
        issues = []
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                # Check for import statements
                if 'import' in line and not line.strip().startswith('#'):
                    # Check each old module
                    for old_module, new_module in self.module_replacements.items():
                        if old_module in line:
                            suggestion = line.replace(old_module, new_module)
                            issues.append((i, line.strip(), suggestion.strip()))
                            
                    # Check for moved test scripts
                    for test_module in self.moved_to_tests:
                        if test_module in line and 'from' in line:
                            issues.append((i, line.strip(), 
                                         f"# This import needs updating - {test_module} was moved to tests/"))
                            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return issues
    
    def generate_fix_script(self, all_issues: Dict[Path, List[Tuple[int, str, str]]]):
        """Generate a script to fix the issues"""
        fix_script_path = self.project_root / 'fix_imports.sh'
        
        with open(fix_script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated script to fix import statements\n")
            f.write("# Review each change before running!\n\n")
            
            for file_path, issues in all_issues.items():
                if issues:
                    f.write(f"\n# Fixes for {file_path.relative_to(self.project_root)}\n")
                    
                    # Create backup
                    f.write(f"cp '{file_path}' '{file_path}.backup'\n")
                    
                    # Generate sed commands for each fix
                    for line_num, old_import, new_import in issues:
                        # Escape special characters for sed
                        old_escaped = old_import.replace('/', '\\/').replace('.', '\\.')
                        new_escaped = new_import.replace('/', '\\/').replace('.', '\\.')
                        
                        f.write(f"sed -i '' 's/{old_escaped}/{new_escaped}/g' '{file_path}'\n")
            
            f.write("\necho 'Import fixes complete!'\n")
        
        # Make script executable
        os.chmod(fix_script_path, 0o755)
        print(f"Fix script generated: {fix_script_path}")
    
    def run_check(self):
        """Run the import check"""
        print("🔍 Checking Python files for outdated imports...")
        print("=" * 60)
        
        python_files = self.find_python_files()
        all_issues = {}
        total_issues = 0
        
        for file_path in python_files:
            issues = self.check_imports(file_path)
            if issues:
                all_issues[file_path] = issues
                total_issues += len(issues)
                
                print(f"\n📄 {file_path.relative_to(self.project_root)}")
                for line_num, old_import, suggestion in issues:
                    print(f"   Line {line_num}: {old_import}")
                    print(f"   Suggest: {suggestion}")
        
        if total_issues == 0:
            print("\n✅ No import issues found! All imports are up to date.")
        else:
            print(f"\n⚠️  Found {total_issues} import issues in {len(all_issues)} files")
            
            # Generate fix script
            self.generate_fix_script(all_issues)
            
            print("\n📝 Next steps:")
            print("1. Review the generated fix_imports.sh script")
            print("2. Run: ./fix_imports.sh to apply fixes")
            print("3. Test that everything still works")
            
        return all_issues

def main():
    project_root = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP"
    
    checker = ImportChecker(project_root)
    issues = checker.run_check()
    
    # Also check for hardcoded penalty rates that need updating
    print("\n" + "=" * 60)
    print("🔍 Checking for hardcoded penalty rates to update...")
    
    penalty_patterns = [
        (r'0\.30\s*#.*penalty', '0.15  # Standard path penalty rate'),
        (r'penalty.*=\s*0\.30', 'penalty = 0.15  # Standard path'),
        (r'penalty_rate\s*=\s*0\.30', 'penalty_rate = 0.15'),
    ]
    
    files_with_penalties = []
    for file_path in checker.find_python_files():
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            for pattern, suggestion in penalty_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    files_with_penalties.append(file_path)
                    print(f"\n📄 {file_path.relative_to(project_root)}")
                    print(f"   Found hardcoded penalty rate - should use penalty_calculator module")
                    break
                    
        except Exception as e:
            pass
    
    if files_with_penalties:
        print(f"\n⚠️  Found {len(files_with_penalties)} files with hardcoded penalty rates")
        print("These should be updated to use the new penalty_calculator module")
    else:
        print("\n✅ No hardcoded penalty rates found")

if __name__ == "__main__":
    main()
