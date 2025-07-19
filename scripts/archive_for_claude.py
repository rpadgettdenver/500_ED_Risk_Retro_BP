#!/usr/bin/env python3
"""
📍 SUGGESTED FILE NAME: archive_for_claude.py
📁 FILE LOCATION: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/archive_for_claude.py
🎯 USE: Creates a clean archive of the Energize Denver Risk & Retrofit project files for sharing with Claude via Google Drive.
     Excludes development artifacts while preserving all important source code and data.

Creates a clean archive of project files for sharing with Claude via Google Drive.
Excludes development artifacts while preserving all important source code and data.
"""

import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

class ProjectArchiver:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Files and directories to exclude
        self.exclude_patterns = {
            # Virtual environments
            '.venv', 'venv', 'env', '.env',
            # Python cache
            '__pycache__', '*.pyc', '*.pyo', '*.pyd',
            # Git
            '.git', '.gitignore',
            # IDE files
            '.vscode', '.idea', '.idea/', '*.swp', '*.swo',
            # OS files
            '.DS_Store', 'Thumbs.db',
            # Node modules (if any)
            'node_modules',
            # Large result files and outputs that can be regenerated
            'test_results/large_files',
            'outputs/data/large_files',
            # Logs
            '*.log', 'logs/',
            # Temporary files
            'tmp/', 'temp/', '*.tmp',
            # Model checkpoints
            '*.ckpt', '*.model', '*.weights',
            # GCP environment (may contain sensitive credentials)
            'gcp_env/',
            # Large data files that might be regenerated
            'data/processed/large_datasets',
            # Archive folder to avoid nested archives
            'archive/',
        }
        
        # Important files to always include
        self.always_include = {
            '*.py', '*.md', '*.txt', '*.yml', '*.yaml', '*.json', 
            '*.csv', 'requirements.txt', 'pyproject.toml', 'setup.py',
            '*.ipynb', '*.sql', '*.sh', '*.bat', '*.toml'
        }
    
    def should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded"""
        path_str = str(path)
        name = path.name
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in path_str or pattern == name:
                return True
            if pattern.startswith('*') and name.endswith(pattern[1:]):
                return True
        
        # Special size-based exclusions
        if path.is_file():
            try:
                # Exclude files larger than 50MB
                if path.stat().st_size > 50 * 1024 * 1024:
                    print(f"⚠️  Excluding large file: {path} ({path.stat().st_size / 1024 / 1024:.1f}MB)")
                    return True
            except OSError:
                pass
        
        return False
    
    def create_archive(self, output_dir: str = None) -> Path:
        """Create a clean archive of the project"""
        
        if output_dir is None:
            # Default to user's Desktop for easy Google Drive upload
            output_dir = Path.home() / "Desktop"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(exist_ok=True)
        
        archive_name = f"energize-denver-risk-retrofit-claude-{self.timestamp}.zip"
        archive_path = output_dir / archive_name
        
        print(f"🗜️  Creating clean project archive...")
        print(f"📂 Source: {self.project_path}")
        print(f"💾 Output: {archive_path}")
        
        included_files = []
        excluded_files = []
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.project_path):
                root_path = Path(root)
                
                # Filter directories to avoid walking into excluded ones
                dirs[:] = [d for d in dirs if not self.should_exclude(root_path / d)]
                
                for file in files:
                    file_path = root_path / file
                    
                    if self.should_exclude(file_path):
                        excluded_files.append(file_path)
                        continue
                    
                    # Add to archive with relative path
                    relative_path = file_path.relative_to(self.project_path)
                    zipf.write(file_path, relative_path)
                    included_files.append(relative_path)
        
        print(f"\n✅ Archive created successfully!")
        print(f"📊 Statistics:")
        print(f"   • Included files: {len(included_files)}")
        print(f"   • Excluded files: {len(excluded_files)}")
        print(f"   • Archive size: {archive_path.stat().st_size / 1024 / 1024:.1f}MB")
        
        # Show some included files as examples
        print(f"\n📋 Sample included files:")
        for file in sorted(included_files)[:10]:
            print(f"   ✓ {file}")
        if len(included_files) > 10:
            print(f"   ... and {len(included_files) - 10} more")
        
        # Show some excluded files as examples  
        print(f"\n🚫 Sample excluded files:")
        for file in sorted(excluded_files)[:5]:
            print(f"   ✗ {file}")
        if len(excluded_files) > 5:
            print(f"   ... and {len(excluded_files) - 5} more")
        
        print(f"\n🔗 Next steps:")
        print(f"   1. Upload {archive_name} to your Google Drive")
        print(f"   2. Share the file with Claude in your conversation")
        print(f"   3. Claude can then access all your project files!")
        
        return archive_path
    
    def create_project_summary(self, output_dir: str = None) -> Path:
        """Create a text summary of the project structure"""
        
        if output_dir is None:
            output_dir = Path.home() / "Desktop"
        else:
            output_dir = Path(output_dir)
        
        summary_path = output_dir / f"energize-denver-risk-retrofit-summary-{self.timestamp}.md"
        
        with open(summary_path, 'w') as f:
            f.write(f"# Energize Denver Risk & Retrofit Strategy Platform\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Project Path:** {self.project_path}\n\n")
            
            f.write("## Project Overview\n")
            f.write("This project builds a modular, Python-based analytics system that:\n")
            f.write("- Quantifies building-level penalty risk under Energize Denver BPS\n")
            f.write("- Prioritizes cost-effective retrofits for compliance and decarbonization\n")
            f.write("- Enables DER clustering (e.g., shared loops, heat reuse, thermal storage)\n")
            f.write("- Aligns with Section 48 ITC, Clean Heat Plan, CPRG, and CPF incentives\n")
            f.write("- Prioritizes Equity Priority Buildings (EPBs) for infrastructure access and funding\n\n")
            
            f.write("## Project Structure\n\n")
            
            # Create a tree-like structure
            for root, dirs, files in os.walk(self.project_path):
                root_path = Path(root)
                
                # Skip excluded directories
                dirs[:] = [d for d in dirs if not self.should_exclude(root_path / d)]
                
                level = len(root_path.relative_to(self.project_path).parts)
                indent = "  " * level
                
                if level == 0:
                    f.write(f"{indent}📁 {root_path.name}/\n")
                else:
                    f.write(f"{indent}📁 {root_path.relative_to(self.project_path)}/\n")
                
                # List important files
                for file in sorted(files):
                    file_path = root_path / file
                    if not self.should_exclude(file_path):
                        f.write(f"{indent}  📄 {file}\n")
            
            f.write("\n## Key Files\n\n")
            f.write("- **README.md**: Project overview and setup instructions\n")
            f.write("- **PROJECT_KNOWLEDGE.md**: Detailed project knowledge base\n")
            f.write("- **requirements.txt**: Python dependencies\n")
            f.write("- **pyproject.toml**: Project configuration\n")
            f.write("- **src/**: Core project modules\n")
            f.write("- **scripts/**: Utility scripts\n")
            f.write("- **data/**: Project data files\n")
            f.write("- **notebooks/**: Jupyter notebooks for analysis\n")
            f.write("- **tests/**: Test files\n")
        
        print(f"📝 Project summary created: {summary_path}")
        return summary_path

def main():
    """Main function to create archives"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Archive Energize Denver Risk & Retrofit project for Claude sharing')
    parser.add_argument('--project-path', 
                       default='/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP',
                       help='Path to the project directory')
    parser.add_argument('--output-dir', 
                       help='Output directory (default: Desktop)')
    parser.add_argument('--summary-only', action='store_true',
                       help='Create only summary, not full archive')
    
    args = parser.parse_args()
    
    archiver = ProjectArchiver(args.project_path)
    
    if args.summary_only:
        archiver.create_project_summary(args.output_dir)
    else:
        # Create both archive and summary
        archiver.create_archive(args.output_dir)
        archiver.create_project_summary(args.output_dir)

if __name__ == "__main__":
    main()
