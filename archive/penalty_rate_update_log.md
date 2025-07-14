# Penalty Rate Update Documentation

## Date: 2025-07-12

## Summary of Changes

Updated all penalty calculations throughout the codebase to match the April 2025 Energize Denver Technical Guidance.

### Correct Penalty Rates (per Technical Guidance)

| Compliance Path | Penalty Rate | Target Years | Annual After Final Target |
|-----------------|--------------|--------------|--------------------------|
| Standard Path (3 targets) | $0.15/kBtu | 2025, 2027, 2030 | Yes, annually after 2030 |
| Alternate/Opt-in Path (2 targets) | $0.23/kBtu | 2028, 2032 | Yes, annually after 2032 |
| Timeline Extension (1 target) | $0.35/kBtu | 2030 or 2032 | Yes, annually thereafter |
| Late Extension | +$0.10/kBtu | (add to base rate) | Same as base path |
| Never Benchmarking | $10/sqft | One-time | Then annual penalties |

### Previous Incorrect Rates (NOW FIXED)

The codebase previously used these incorrect rates:
- 2025: $0.30/kBtu (was 2x too high)
- 2027: $0.50/kBtu (was 3.3x too high)  
- 2030: $0.70/kBtu (was 4.7x too high)

### Files Updated

1. **src/config/project_config.py**
   - Updated penalties dictionary with correct structure
   - Added path-based penalty configuration
   - Maintained backward compatibility

2. **src/analysis/building_compliance_analyzer.py**
   - Fixed standard path penalties to $0.15/kBtu
   - Fixed opt-in path penalties to $0.23/kBtu
   - Updated calculation comments

3. **src/analysis/integrated_tes_hp_analyzer.py**
   - Corrected penalty calculations in model_system_impacts()
   - Fixed total penalty calculation to include annual penalties after 2030
   - Updated penalty math

4. **BigQuery Scripts**
   - Already had correct rates in create_penalty_analysis_corrected.py
   - Other scripts may need updates

### Penalty Calculation Formula

The correct formula is:
```
Annual Penalty = (Actual EUI - Target EUI) × Building Sq Ft × Penalty Rate
```

Where:
- Actual EUI = Weather Normalized Site EUI
- Target EUI = Compliance target for the given year
- Penalty Rate = Rate based on compliance path (see table above)

### Important Notes

1. Penalties are assessed in target years AND annually thereafter if non-compliant
2. Buildings that fail to maintain compliance (>5% regression) face the same penalty rate
3. Electrification provides a 10% bonus to EUI targets (allows higher EUI)
4. MAI buildings have different targets but same penalty rates

### Example 15-Year Penalty Timeline

**Standard Path (non-compliant building):**
- 2025: $X penalty (target year)
- 2026: $0 (no penalty)
- 2027: $X penalty (target year)
- 2028-2029: $0 (no penalty)
- 2030: $X penalty (Final target year)
- 2031-2042: $X penalty annually (12 years)
- Total: 15 years of penalties
- For the Standard Path, the 2025 target will be shown as 

**Opt-in Path (non-compliant building):**
- 2025-2027: $0 (no penalty)
- 2028: $Y penalty (target year)
- 2029-2031: $0 (no penalty)
- 2032: $Y penalty (target year)
- 2033-2042: $Y penalty annually (10 years)
- Total: 12 years of penalties

### Testing Recommendations

1. Re-run Building 2952 analysis with corrected rates
2. Verify penalty calculations match Technical Guidance examples
3. Update any dashboards or reports showing penalty projections
4. Notify stakeholders of the corrected calculations
