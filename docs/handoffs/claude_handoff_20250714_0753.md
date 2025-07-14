# Claude Session Handoff - January 14, 2025, 10:40 MST

## Session Summary
This session focused on correcting the ACO 2028 target calculation logic and planning a comprehensive portfolio risk analysis system with three scenarios (All Standard, All ACO, and Hybrid/Realistic). We identified the need for aggregate analysis with year normalization and discovered existing opt-in decision logic that can be leveraged for the hybrid approach.

## Work Completed in This Session

### 1. Corrected ACO Target Understanding ✅
- **Previous Understanding (WRONG)**: ACO 2028 target is interpolated from baseline
- **Corrected Understanding**: ACO 2028 uses the First Interim Target value directly from CSV
- **Impact**: Simplifies calculations and ensures consistency with official targets

### 2. Identified Variable Target Years Challenge ✅
- **Discovery**: Buildings have different First Interim Target Years (2024, 2025, 2026)
- **Solution**: Dual-track approach - actual years for individual analysis, normalized years for aggregate
- **Normalization Strategy**:
  - Standard Path: Map all to 2025, 2027, 2030
  - ACO Path: Map all to 2028, 2032

### 3. Found Existing Opt-In Decision Logic ✅
- **Location**: `/src/gcp/create_opt_in_decision_model.py`
- **Key Features**:
  - NPV-based financial analysis
  - Technical difficulty scoring
  - Cash flow constraint consideration
  - MAI building special handling
- **Issue Found**: Uses incorrect penalty rates ($0.30 and $0.70 instead of $0.15 and $0.23)

### 4. Designed Portfolio Risk Analysis System ✅
- **Three Scenarios**:
  1. All Standard - Assume all buildings stay on standard path
  2. All ACO - Assume all buildings opt into ACO  
  3. Hybrid/Realistic - Use opt-in logic to predict actual behavior
- **Key Components Planned**:
  - Year normalization module
  - Portfolio risk analyzer
  - Opt-in predictor (Python port of BigQuery logic)

### 5. Planning Enhancements ✅
- **Sensitivity Analysis**: ±20% variation in opt-in rates
- **Property Type Analysis**: Which building types predominantly opt-in
- **Time Series Analysis**: Year-by-year penalty evolution
- **Geographic Clustering**: Possible Future Implementation

## Current Project State

### ✅ Working Modules
1. **penalty_calculator.py** - Centralized penalty calculations with correct rates
2. **eui_target_loader.py** - Loads targets with MAI logic and 42% cap applied correctly
3. **mai_data_loader.py** - Loads MAI building designations
4. **building_compliance_analyzer_v2.py** - Confirm this is working with correct imports, rates, and visualizations.  Run and verfiy outputs.

### ⚠️ Scripts Still Needing Updates
1. **create_opt_in_decision_model.py** - BigQuery script has wrong penalty rates ($0.30/$0.70)
2. **integrated_tes_hp_analyzer.py** - Still has hardcoded penalty rates
3. Other analysis scripts that may have inline calculations

### 🆕 Planned New Modules
1. **year_normalization.py** - Handle year mapping for aggregate analysis
2. **opt_in_predictor.py** - Python port of opt-in decision logic
3. **portfolio_risk_analyzer.py** - Three-scenario aggregate analysis

### 📁 Key Files Modified/Created
- `/src/analysis/building_compliance_analyzer_v2.py` - Fixed to use First Interim Target for ACO 2028
- `/docs/penalty_calculation_source_of_truth.md` - Updated with clarifications on pathways
- `/docs/handoffs/claude_handoff_20250114_1040.md` - This session (current file)

## Key Technical Details

### Correct Penalty Rates (Confirmed)
- **Standard Path**: $0.15/kBtu over target
- **ACO/Opt-in Path**: $0.23/kBtu over target
- **Extension**: $0.35/kBtu over target
- **Never Benchmarked**: $10.00/sqft
- **Refererence for Penaly Methodology**: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/docs/penalty_calculation_source_of_truth.md 

### Year Normalization Strategy
```python
NORMALIZED_YEARS = {
    'standard': {
        'first_interim': 2025,   # Map 2024, 2025, 2026 → 2025
        'second_interim': 2027,  # All → 2027
        'final': 2030           # All → 2030
    },
    'aco': {
        'first_interim': 2028,   # All ACO → 2028
        'final': 2032           # All ACO → 2032
    }
}
```

### ACO Target Logic (Corrected)
```python
# For ACO path:
aco_targets = {
    2028: targets_data['first_interim_target'],  # Use First Interim directly
    2032: targets_data['final_target_with_logic']  # Same final as standard
}
```

### Opt-In Decision Logic (from BigQuery)
Key factors in decision:
1. **Financial**: NPV advantage of delaying penalties
2. **Technical**: Difficulty score based on reduction percentage
3. **Cash Flow**: Constraints for certain property types
4. **MAI Status**: Special consideration for manufacturing buildings

## Next Steps for Next Session

### Priority 1: Fix Penalty Rates in Existing Scripts
1. **create_opt_in_decision_model.py**:
   ```python
   # Change:
   self.PENALTY_RATE_DEFAULT = 0.15  # Not 0.30
   self.PENALTY_RATE_OPTIN = 0.23    # Not 0.70
   ```

2. **integrated_tes_hp_analyzer.py**:
   - Import centralized penalty calculator
   - Remove all hardcoded rates

### Priority 2: Create Year Normalization Module
```python
# /src/utils/year_normalization.py
class YearNormalizer:
    def normalize_standard_path_year(self, actual_year, target_type)
    def normalize_aco_path_year(self, target_type)
    def get_year_mapping_summary(self)
```

### Priority 3: Port Opt-In Logic to Python
```python
# /src/utils/opt_in_predictor.py
class OptInPredictor:
    def predict_opt_in(self, building_data)
    def get_decision_confidence(self, building_data)
```

### Priority 4: Build Portfolio Risk Analyzer
```python
# /src/analysis/portfolio_risk_analyzer.py
class PortfolioRiskAnalyzer:
    def analyze_all_scenarios(self)
    def scenario_all_standard(self)
    def scenario_all_aco(self)
    def scenario_hybrid(self)
    def sensitivity_analysis(self, opt_in_rate_adjustment)
    def property_type_analysis(self)
    def time_series_analysis(self)
```

## Important Notes for Next Session

### Building 2952 Characteristics (Reference)
- Building ID: 2952
- Type: Multifamily Housing
- Square Feet: 52,826
- EPB: Yes (Equity Priority Building)
- MAI: No
- Has Target Adjustment: Yes
- Current EUI: ~69
- Targets: 69.0 → 65.4 → 63.2 → 61.0

### Common Pitfalls to Avoid
1. ACO 2028 uses First Interim Target value, NOT interpolated
2. Don't use `compliance_path='alternate'` - use `'aco'` instead
3. Remember penalty calculator expects `actual_eui`, not `exceedance`
4. MAI buildings appear in MAITargetSummary.csv, not just Manufacturing types
5. Both compliance paths start from baseline year/EUI for visualization
6. Year normalization is for aggregate analysis only - individual buildings use actual years

### Testing Commands
```bash
# Test updated analyzer
python src/analysis/building_compliance_analyzer_v2.py

# Check for hardcoded rates
grep -r "0\.30\|0\.70" src/ --include="*.py"

# Test opt-in logic (after fixing rates)
python src/gcp/create_opt_in_decision_model.py
```

## Session Metrics
- Duration: ~3 hours
- Scripts analyzed: 3 (building_compliance_analyzer_v2.py, create_opt_in_decision_model.py, penalty_calculation_source_of_truth.md)
- New modules designed: 3 (year_normalization, opt_in_predictor, portfolio_risk_analyzer)
- Issues identified: 2 (ACO target logic, penalty rates in BigQuery script)
- Educational topics: 2 (Year normalization for aggregation, Portfolio scenario analysis)

## Questions Resolved
1. ✅ ACO 2028 uses First Interim Target directly (not interpolated)
2. ✅ Need for dual-track analysis (individual vs. aggregate)
3. ✅ Year normalization strategy for portfolio analysis
4. ✅ Existence of opt-in decision logic in codebase
5. ✅ Three-scenario approach for portfolio risk

## Outstanding Questions
1. Should sensitivity analysis include building-specific confidence scores?
2. How should we handle buildings that become compliant mid-stream?
3. Should the portfolio analyzer output to BigQuery or stay local?
4. Do we need to account for buildings that might fail and then comply?

## Key Insights from This Session
1. **Variable target years** require thoughtful aggregation strategy
2. **Existing opt-in logic** can be leveraged for realistic scenarios
3. **Portfolio analysis** needs three scenarios for comprehensive risk assessment
4. **Sensitivity analysis** is crucial given uncertainty in behavior
5. **Property type patterns** will inform targeted interventions

---
*Session conducted by: Claude*  
*Human: Robert Padgett*  
*Session end: January 14, 2025, 10:40 MST*
*Next session: Implement year normalization and fix penalty rates*
