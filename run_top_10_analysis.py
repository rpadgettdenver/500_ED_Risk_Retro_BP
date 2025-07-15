"""
Quick script to run the top 10 analysis
"""
import sys
sys.path.append('/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis')

from analyze_top_penalty_buildings import analyze_top_penalty_buildings

# Run the analysis
top_10 = analyze_top_penalty_buildings()
