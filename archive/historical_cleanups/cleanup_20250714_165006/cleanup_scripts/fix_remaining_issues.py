#!/usr/bin/env python3
"""
Fix remaining issues after import corrections
"""

import os
from pathlib import Path

project_root = Path("/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP")

# Fix 1: Remove self-import from fixed_enhanced_der_clustering.py
print("🔧 Fixing self-import in fixed_enhanced_der_clustering.py...")
clustering_file = project_root / "src/analytics/fixed_enhanced_der_clustering.py"

with open(clustering_file, 'r') as f:
    content = f.read()

# Comment out the problematic import line
content = content.replace(
    "from enhanced_der_clustering import organize_outputs, export_to_excel_friendly_csv",
    "# from enhanced_der_clustering import organize_outputs, export_to_excel_friendly_csv  # Removed self-import"
)

# Add the actual functions that were being imported
if "def organize_outputs" not in content:
    # Add the functions at the end of the file before main()
    functions_to_add = '''
def organize_outputs(base_output_dir):
    """Organize output directories"""
    import os
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(base_output_dir, 'der_clustering', timestamp)
    
    paths = {
        'reports': os.path.join(output_dir, 'reports'),
        'json': os.path.join(output_dir, 'json'),
        'visualizations': os.path.join(output_dir, 'visualizations')
    }
    
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    
    return paths

def export_to_excel_friendly_csv(df, filepath):
    """Export DataFrame to Excel-friendly CSV"""
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"   Saved: {os.path.basename(filepath)}")

'''
    # Insert before main()
    content = content.replace("def main():", functions_to_add + "\ndef main():")

with open(clustering_file, 'w') as f:
    f.write(content)

print("✅ Fixed self-import")

# Fix 2: Update penalty rates in hvac_system_impact_modeler.py
print("\n🔧 Fixing penalty rates in hvac_system_impact_modeler.py...")
hvac_file = project_root / "src/models/hvac_system_impact_modeler.py"

with open(hvac_file, 'r') as f:
    content = f.read()

# Add import for penalty calculator at the top
if "from src.utils.penalty_calculator import" not in content:
    import_statement = "from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator\n"
    # Find where to insert (after other imports)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('from datetime import'):
            lines.insert(i + 1, import_statement)
            break
    content = '\n'.join(lines)

# Replace hardcoded penalty rates
content = content.replace("penalty_rate = 0.30", "penalty_rate = 0.15  # Standard path rate")
content = content.replace("penalty_rate = 0.50", "penalty_rate = 0.15  # Standard path rate")  
content = content.replace("penalty_rate = 0.70", "penalty_rate = 0.15  # Standard path rate")

# Add note about using penalty calculator
if "# TODO: Update to use penalty_calculator module" not in content:
    content = content.replace(
        "# Calculate penalty",
        "# TODO: Update to use penalty_calculator module for correct rates\n                # Calculate penalty"
    )

with open(hvac_file, 'w') as f:
    f.write(content)

print("✅ Updated penalty rates to 0.15 (standard path)")
print("   Note: Full integration with penalty_calculator module still needed")

print("\n✅ All fixes complete!")
print("\n📝 Summary of changes:")
print("1. Fixed self-import in fixed_enhanced_der_clustering.py")
print("2. Updated penalty rates from 0.30/0.50/0.70 to 0.15")
print("3. Added TODO for full penalty_calculator integration")
