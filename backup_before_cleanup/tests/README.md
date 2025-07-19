# Integration Test Suite

## Overview
This directory contains comprehensive integration tests for the Energize Denver Risk & Retrofit system. These tests verify that all modules work correctly together and that the corrected penalty rates ($0.15 for Standard, $0.23 for ACO) are properly implemented throughout the system.

## Test Suites

### 1. **Integration Test Suite** (`test_integration_suite.py`)
Comprehensive tests covering:
- ✅ Penalty rate verification across all modules
- ✅ Building 2952 calculations with known values
- ✅ Data pipeline integration
- ✅ Edge case handling
- ✅ Module consistency verification
- ✅ HVAC modeler integration
- ✅ Year normalization logic

### 2. **Python-BigQuery Consistency Test** (`test_python_bigquery_consistency.py`)
Verifies consistency between:
- Python module calculations
- BigQuery view results
- Opt-in decisions
- Penalty calculations

## Running Tests

### Run All Tests:
```bash
cd /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/tests
python run_all_tests.py
```

### Run Individual Test Suites:
```bash
# Integration tests only
python test_integration_suite.py

# Consistency tests only
python test_python_bigquery_consistency.py
```

## Test Results

Test results are saved in the `test_results/` directory with timestamps:
- `integration_test_results_YYYYMMDD_HHMMSS.json` - Detailed test results
- `python_calculations_YYYYMMDD_HHMMSS.csv` - Python calculation outputs

## Key Test Cases

### Building 2952 (Known Values)
- Building ID: 2952
- Property Type: Multifamily Housing
- Square Footage: 59,650 sq ft
- Current EUI: 89.3
- First Interim Target: 76.5
- Expected 2025 Standard Penalty: $114,032.25

### Penalty Rate Verification
- Standard Path: $0.15 per kBtu over target
- ACO Path: $0.23 per kBtu over target (53% higher)

## What Tests Verify

1. **Correct Penalty Rates**: All modules use $0.15 (Standard) and $0.23 (ACO)
2. **No 2028 Interpolation**: Confirms no old interpolation logic exists
3. **Module Integration**: All modules work together correctly
4. **Data Flow**: Data flows correctly from raw input to final calculations
5. **Edge Cases**: System handles missing data, zero values, etc.
6. **Consistency**: Results are consistent across different calculation methods

## Success Criteria

All tests should pass with:
- ✅ 100% of penalty rate tests passing
- ✅ Building 2952 calculations matching expected values
- ✅ No negative penalties
- ✅ Consistent results across modules
- ✅ ACO penalties exactly 53% higher than Standard

## Troubleshooting

If tests fail:
1. Check error messages for specific module issues
2. Verify data files exist in expected locations
3. Ensure all dependencies are installed
4. Check that penalty_calculator.py has correct rates
5. Verify HVAC modeler is using penalty calculator (not hardcoded rates)

## Next Steps After Testing

Once all tests pass:
1. ✅ Regenerate BigQuery views with corrected logic
2. ✅ Update documentation
3. ✅ Deploy to production
4. ✅ Monitor results
