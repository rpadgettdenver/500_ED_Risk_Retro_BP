# Energize Denver Opt-In Logic Summary

## Quick Reference Guide

### What We Found

1. **56.7% of buildings (1,659) will opt into ACO path**
   - 97.8% of these literally cannot meet ANY targets
   - Only 2.2% cite technical infeasibility
   - This is a compliance crisis, not a choice

2. **The confidence statistics are CORRECT but misleading**
   - 100% of buildings show ≥80% confidence
   - Average confidence is 99.9%
   - This is because the model is overconfident by design
   - Nearly every decision gets 90-100% confidence

3. **Top 10 buildings drive 26.8% of penalties**
   - Likely large office towers, hotels, or industrial
   - 200,000-500,000 sq ft each
   - 25-40 kBtu/sqft over target
   - $1M+ annual penalties each

### What This Means

**The Big Picture:**
- Over half the portfolio faces impossible efficiency targets
- The opt-in decision is largely forced, not strategic
- Risk is highly concentrated in a few large buildings
- The model needs uncertainty modeling

**For Policy Makers:**
- Current targets may be unachievable for existing buildings
- Consider more gradual compliance paths
- Target interventions at top 10 buildings first

**For Building Owners:**
- If you can't meet any target, opt-in is inevitable
- Focus on 2032 compliance, not 2025
- Large buildings should seek custom solutions

### To Run Analysis

```bash
# Check top 10 buildings
python run_top_10_analysis.py

# Run full portfolio analysis  
python run_portfolio_analysis_v3.py
```

### Key Files
- Opt-in logic: `src/utils/opt_in_predictor.py`
- Portfolio analyzer: `src/analysis/portfolio_risk_analyzer_refined.py`
- This analysis: `docs/opt_in_logic_analysis.md`
