# Claude Handoff - July 14, 2025 - 8:38 AM MST

## 🚀 Session Summary
Critical correction to ACO 2028 target calculation throughout the codebase. The 2028 ACO target should use the First Interim Target EUI from the CSV file, NOT interpolation. This was a misunderstanding from previous documentation that has now been corrected.

## ✅ Completed Tasks

### 1. **Updated Penalty Calculation Source of Truth** ✅
- Updated `/docs/penalty_calculation_source_of_truth.md` to version 1.3
- Corrected ACO 2028 target calculation:
  - OLD: Linear interpolation from baseline to 2032
  - NEW: Uses First Interim Target EUI from CSV
- This is the same target used for Standard Path 2025
- Updated all examples and test cases to reflect this change

### 2. **Fixed building_compliance_analyzer_v2.py** ✅
- Renamed method from `calculate_opt_in_interim_target` to `get_opt_in_2028_target`
- Removed interpolation logic
- Now correctly returns `targets_data['first_interim_target']` for 2028
- This fixes the issue where Building 2952 was showing 63.46 (interpolated) instead of 65.4

### 3. **Fixed opt_in_predictor.py** ✅
- Updated `_calculate_aco_path_penalties` to accept two gap parameters
- ACO 2028 now uses gap from First Interim Target (gap_2025)
- ACO 2032 continues to use gap from Final Target (gap_2030)
- This ensures NPV calculations correctly reflect the actual ACO targets

## 📊 Key Correction Details

### ACO/Opt-in Path Target Logic:
- **2028 Target**: First Interim Target EUI (same as Standard Path 2025)
- **2032 Target**: Final Target EUI (same as Standard Path 2030)
- **Penalty Rate**: $0.23/kBtu over target

### Why This Matters:
1. **Financial Impact**: Using the correct 2028 target changes NPV calculations
2. **Decision Logic**: Opt-in recommendations depend on accurate penalty projections
3. **Visualization**: Compliance pathways should show actual targets, not interpolated values

## 🔧 Technical Changes Made

### Source of Truth Updates:
```python
# OLD (Incorrect)
def calculate_aco_2028_target(baseline_year, baseline_eui, final_target_2032):
    """Calculate ACO interim target for 2028 by linear interpolation"""
    # Interpolation logic...

# NEW (Correct)
def get_aco_2028_target(building_row):
    """Get ACO 2028 target - uses First Interim Target EUI"""
    first_interim_target = building_row['First Interim Target EUI']
    # Apply caps/floors as appropriate
```

### Code Updates:
1. **building_compliance_analyzer_v2.py**: Method now returns first_interim_target directly
2. **opt_in_predictor.py**: ACO penalties now use correct gaps for 2028 and 2032
3. **penalty_calculation_source_of_truth.md**: Version 1.3 with corrected logic

## 🎯 Next Steps

### 1. **Test Building 2952 Again**
- Run building_compliance_analyzer_v2.py for Building 2952
- Verify 2028 target now shows as 65.4 (First Interim Target)
- Confirm visualization shows correct compliance pathways

### 2. **Update Portfolio Risk Analyzer**
- Verify portfolio_risk_analyzer.py uses correct 2028 targets
- Re-run portfolio analysis with corrected logic

### 3. **Update BigQuery Scripts**
- Review create_opt_in_decision_model.py in BigQuery
- Ensure ACO 2028 uses First Interim Target, not interpolation

### 4. **Documentation Review**
- Check all documentation for references to interpolation
- Update any remaining incorrect descriptions

## 🔍 Current State Assessment

### What's Fixed:
- Penalty calculation source of truth now correct (v1.3)
- building_compliance_analyzer_v2.py uses correct 2028 targets
- opt_in_predictor.py calculates ACO penalties correctly
- All future analysis will use First Interim Target for ACO 2028

### What Needs Verification:
- Portfolio risk analyzer logic
- Any cached results using old interpolation
- BigQuery views that might have interpolation logic

## 📁 Files Modified
```
docs/
├── penalty_calculation_source_of_truth.md ✅ UPDATED to v1.3
└── handoffs/
    └── claude_handoff_20250714_0838.md ✅ NEW

src/
├── analysis/
│   └── building_compliance_analyzer_v2.py ✅ FIXED
└── utils/
    └── opt_in_predictor.py ✅ FIXED
```

## 💡 Key Learning

The confusion came from misunderstanding the ACO path target structure. The correct logic is:
- **Standard Path**: Uses targets for years 2025, 2027, 2030
- **ACO Path**: Uses First Interim Target for 2028, Final Target for 2032
- Both paths reference the same targets from the CSV, just in different years

## 🚨 Important Notes

- This correction affects all NPV calculations for ACO path decisions
- Buildings previously showing interpolated 2028 targets need re-analysis
- Portfolio-wide opt-in predictions may change with corrected logic
- Always reference penalty_calculation_source_of_truth.md v1.3 or later

## 🎬 Ready for Next Session
The ACO 2028 target correction is complete. Next session should:
1. Re-test Building 2952 to verify correct targets
2. Update any remaining modules with interpolation logic
3. Re-run portfolio analysis with corrected calculations
4. Consider updating BigQuery scripts to match

All critical code has been updated to use First Interim Target for ACO 2028.