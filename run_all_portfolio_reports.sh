#!/bin/bash

# Suggested File Name: run_all_portfolio_reports.sh
# File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
# Use: Simple script to generate all portfolio analysis reports with one command

echo "🏢 ENERGIZE DENVER PORTFOLIO ANALYSIS SUITE"
echo "============================================"
echo "This script will generate comprehensive portfolio reports"
echo "Coverage: ~272 buildings, energy use and penalty analysis through 2042"
echo ""

# Navigate to project directory
cd /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source gcp_env/bin/activate

# Create outputs directory if it doesn't exist
mkdir -p outputs

echo ""
echo "📊 GENERATING PORTFOLIO REPORTS..."
echo "=================================="

# 1. Basic Portfolio Analysis (Most Important)
echo ""
echo "1️⃣  Running basic three-scenario analysis..."
python execute_portfolio_analysis.py

# 2. Improved Analysis with Better Formatting
echo ""
echo "2️⃣  Running improved analysis with enhanced tables..."
python run_improved_portfolio_analysis.py

# 3. MAI-Specific Analysis (if you have MAI buildings)
echo ""
echo "3️⃣  Running MAI building analysis..."
python run_mai_portfolio_analysis.py

# 4. Top Risk Buildings
echo ""
echo "4️⃣  Analyzing top 10 highest-risk buildings..."
python run_top_10_analysis.py

# 5. Unified Analysis
echo ""
echo "5️⃣  Running comprehensive unified analysis..."
python run_unified_analysis_v2.py

echo ""
echo "✅ ALL PORTFOLIO REPORTS GENERATED!"
echo "=================================="
echo ""
echo "📁 Check the following directories for outputs:"
echo "   📊 Excel Files: outputs/*.xlsx"
echo "   📈 Charts: outputs/portfolio_analysis/*.png"
echo "   📋 JSON Data: outputs/*.json"
echo ""
echo "🔍 KEY FILES TO REVIEW:"
echo "   • portfolio_risk_analysis_[timestamp]_detailed.xlsx - Main results"
echo "   • portfolio_analysis_[timestamp].png - Visualizations"
echo "   • business_intelligence_summary_[timestamp].txt - Executive summary"
echo ""
echo "💡 NEXT STEPS:"
echo "   1. Open Excel files for detailed building-by-building analysis"
echo "   2. Review PNG charts for executive presentation"
echo "   3. Use JSON files for further analysis or API integration"
echo ""

# Show what files were created
echo "📋 FILES CREATED:"
ls -la outputs/ | grep -E "\.(xlsx|png|json|txt)$" | tail -10