#!/bin/bash
# Auto-generated script to fix import statements
# Review each change before running!


# Fixes for src/analytics/fixed_enhanced_der_clustering.py
cp '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/fixed_enhanced_der_clustering.py' '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/fixed_enhanced_der_clustering.py.backup'
sed -i '' 's/from enhanced_der_clustering import organize_outputs, export_to_excel_friendly_csv/from fixed_enhanced_der_clustering import organize_outputs, export_to_excel_friendly_csv/g' '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/fixed_enhanced_der_clustering.py'

# Fixes for run_unified_analysis_v2.py
cp '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/run_unified_analysis_v2.py' '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/run_unified_analysis_v2.py.backup'
sed -i '' 's/from analysis\.building_compliance_analyzer import BuildingComplianceAnalyzer/from analysis\.building_compliance_analyzer_v2 import BuildingComplianceAnalyzer/g' '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/run_unified_analysis_v2.py'

echo 'Import fixes complete!'
