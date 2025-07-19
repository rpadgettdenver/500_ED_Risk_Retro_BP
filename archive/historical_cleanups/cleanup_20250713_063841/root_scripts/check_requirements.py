"""
Check and install required packages for TES+HP analysis
"""

import subprocess
import sys

def check_and_install_packages():
    """Check for required packages and install if missing"""
    
    required_packages = [
        'pandas',
        'numpy', 
        'matplotlib',
        'seaborn',
        'openpyxl',  # For Excel support
    ]
    
    missing_packages = []
    
    print("Checking for required packages...")
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is NOT installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("\nAll packages installed successfully!")
    else:
        print("\nAll required packages are already installed!")

if __name__ == "__main__":
    check_and_install_packages()
