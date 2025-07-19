#!/bin/bash
# Auto-generated script to fix import statements
# Review each change before running!

echo "🔧 Fixing import statements..."

# Fix 1: fixed_enhanced_der_clustering.py
echo "Fixing src/analytics/fixed_enhanced_der_clustering.py..."
cp '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/fixed_enhanced_der_clustering.py' '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/fixed_enhanced_der_clustering.py.backup'
sed -i '' 's/from enhanced_der_clustering import/from fixed_enhanced_der_clustering import/g' '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/fixed_enhanced_der_clustering.py'

# Fix 2: run_unified_analysis_v2.py
echo "Fixing run_unified_analysis_v2.py..."
cp '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/run_unified_analysis_v2.py' '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/run_unified_analysis_v2.py.backup'
# Need to fix the import path - should be src.analysis not just analysis
sed -i '' 's/from analysis\.building_compliance_analyzer import/from src\.analysis\.building_compliance_analyzer_v2 import/g' '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/run_unified_analysis_v2.py'

echo "✅ Import fixes complete!"
echo "📁 Backup files created with .backup extension"
