
# BigQuery Penalty Rate Update Summary

## Files to Update:

### 1. create_opt_in_decision_model.py
- **Issue**: Uses $0.15/kBtu for BOTH standard and opt-in paths in calculations
- **Fix**: Update opt-in calculations to use $0.23/kBtu (PENALTY_RATE_OPTIN)
- **Impact**: Opt-in decisions will change significantly

### 2. create_penalty_analysis_corrected.py  
- **Status**: Already has correct rates defined
- **Verify**: Calculations use the correct variables

## SQL Query Updates Needed:

Replace in financial_analysis CTE:
```sql
-- OLD (WRONG):
GREATEST(0, mai_gap_2030 * gross_floor_area * 0.15) as penalty_2028_optin

-- NEW (CORRECT):
GREATEST(0, mai_gap_2030 * gross_floor_area * 0.23) as penalty_2028_optin
```

## Testing After Updates:

1. Re-run opt-in decision analysis
2. Verify NPV calculations reflect higher opt-in penalties
3. Check that fewer buildings are recommended to opt-in
4. Validate against manual calculations for Building 2952

## Expected Impact:

With correct $0.23/kBtu rate for opt-in:
- Opt-in penalties increase by 53%
- NPV advantage of opt-in decreases
- More buildings should stay on standard path
- Decision confidence scores may change
