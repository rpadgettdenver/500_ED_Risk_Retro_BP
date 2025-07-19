"""
Suggested File Name: find_and_view_png_files.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Locate and display PNG visualization files from portfolio analysis

This script helps you find your PNG visualization files and optionally display them.
"""

import os
import sys
from datetime import datetime
import subprocess
import platform

def find_png_files():
    """Find all PNG files in the outputs directory"""
    project_root = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP'
    outputs_dir = os.path.join(project_root, 'outputs')
    
    png_files = []
    
    # Search in all subdirectories of outputs
    for root, dirs, files in os.walk(outputs_dir):
        for file in files:
            if file.endswith('.png'):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, project_root)
                
                # Get file info
                stat_info = os.stat(full_path)
                modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                file_size = stat_info.st_size
                
                png_files.append({
                    'filename': file,
                    'full_path': full_path,
                    'relative_path': relative_path,
                    'directory': os.path.relpath(root, project_root),
                    'modified': modified_time,
                    'size_kb': round(file_size / 1024, 1)
                })
    
    # Sort by modification time (newest first)
    png_files.sort(key=lambda x: x['modified'], reverse=True)
    return png_files

def display_png_files(png_files):
    """Display found PNG files in a nice format"""
    print("=" * 80)
    print("📊 PORTFOLIO ANALYSIS PNG VISUALIZATION FILES")
    print("=" * 80)
    print(f"Search completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total PNG files found: {len(png_files)}")
    print("=" * 80)
    
    if not png_files:
        print("❌ No PNG files found in outputs directory")
        print("   Make sure you've run the portfolio analysis scripts")
        return
    
    print("\n📁 FOUND PNG FILES (sorted by newest first):")
    print("-" * 80)
    print(f"{'File Name':<40} {'Modified':<20} {'Size':>10} {'Location'}")
    print("-" * 80)
    
    for i, file_info in enumerate(png_files, 1):
        print(f"{file_info['filename']:<40} "
              f"{file_info['modified'].strftime('%Y-%m-%d %H:%M'):<20} "
              f"{file_info['size_kb']:>7.1f}KB {file_info['directory']}")
    
    # Highlight the most recent portfolio analysis files
    print(f"\n🎯 MOST RECENT PORTFOLIO ANALYSIS FILES:")
    print("-" * 50)
    
    portfolio_files = [f for f in png_files if 'portfolio_analysis' in f['filename']]
    for file_info in portfolio_files[:3]:  # Show top 3 most recent
        print(f"📈 {file_info['filename']}")
        print(f"   📁 {file_info['full_path']}")
        print(f"   🕒 {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def open_png_file(file_path):
    """Open PNG file with default system viewer"""
    try:
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', file_path])
        elif platform.system() == 'Windows':  # Windows
            os.startfile(file_path)
        else:  # Linux
            subprocess.run(['xdg-open', file_path])
        print(f"✅ Opened: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"❌ Error opening file: {e}")
        return False

def main():
    """Main function to find and optionally view PNG files"""
    print("🔍 Searching for PNG visualization files...")
    
    png_files = find_png_files()
    display_png_files(png_files)
    
    if not png_files:
        return
    
    # Ask user if they want to open the most recent file
    portfolio_files = [f for f in png_files if 'portfolio_analysis' in f['filename']]
    
    if portfolio_files:
        most_recent = portfolio_files[0]
        print(f"\n💡 QUICK ACTIONS:")
        print(f"   Most recent file: {most_recent['filename']}")
        print(f"   Full path: {most_recent['full_path']}")
        
        response = input(f"\n❓ Open the most recent portfolio analysis PNG? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            open_png_file(most_recent['full_path'])
        
        # Show command to open manually
        print(f"\n🖥️  MANUAL COMMANDS TO OPEN FILES:")
        print(f"   macOS: open '{most_recent['full_path']}'")
        print(f"   Windows: start '{most_recent['full_path']}'")
        print(f"   Linux: xdg-open '{most_recent['full_path']}'")
    
    print(f"\n📂 QUICK NAVIGATION:")
    print(f"   cd {os.path.dirname(most_recent['full_path']) if portfolio_files else 'outputs/'}")
    print(f"   ls -la *.png")

if __name__ == "__main__":
    main()
