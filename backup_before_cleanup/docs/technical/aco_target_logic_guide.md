# ACO Target Logic Guide
**Version:** 1.0  
**Date:** July 14, 2025  
**Purpose:** Explain the Alternate Compliance Option (ACO) target structure and rationale

---

## Executive Summary

The Energize Denver Alternate Compliance Option (ACO) allows buildings to opt for a different compliance timeline with only two target years (2028 and 2032) instead of three (2025, 2027, 2030). Critically, the **2028 ACO target uses the same value as the Standard Path's 2025 First Interim Target**.

---

## Why ACO 2028 Uses the First Interim Target

### 1. **Program Simplicity**
Rather than creating entirely new targets for ACO buildings, the program reuses existing calculated targets:
- **2028 ACO Target** = First Interim Target EUI (same as typical 2025 Standard, some buildings may have a different 'First Interim Target Year')
- **2032 ACO Target** = Final Target EUI (same as 2030 Standard)

### 2. **Fairness Principle**
Buildings choosing ACO get more time but don't get easier targets:
- Standard Path: Meet targets in 2025, 2027, 2030
- ACO Path: Meet the SAME targets but in 2028, 2032
- This prevents gaming the system by choosing ACO for easier targets

### 3. **Administrative Efficiency**
- Only one set of targets needs to be calculated per building
- Reduces complexity in target setting and appeals
- Simplifies tracking and enforcement

---

## Target Comparison Table

| Path | First Target | Second Target | Third Target | Penalty Rate |
|------|--------------|---------------|--------------|--------------|
| **Standard** | 2025: First Interim EUI | 2027: Second Interim EUI | 2030: Final Target EUI | $0.15/kBtu |
| **ACO** | 2028: First Interim EUI | 2032: Final Target EUI | N/A | $0.23/kBtu |

---

## Key Differences Between Paths

### Timeline
- **Standard**: 5 years to final target (2025-2030)
- **ACO**: 7 years to final target (2025-2032)

### Penalty Structure
- **Standard**: Lower rate ($0.15) but earlier penalties
- **ACO**: Higher rate ($0.23) but delayed penalties

### Target Values
- **Both paths use the same target values**
- Only the years differ, not the EUI requirements

---

## Implementation in Code

### Correct Implementation:
```python
def get_aco_2028_target(building_data):
    """ACO 2028 uses the First Interim Target"""
    return building_data['first_interim_target']

def get_aco_2032_target(building_data):
    """ACO 2032 uses the Final Target"""
    return building_data['final_target']
```

### Incorrect Implementation (OLD):
```python
# WRONG - Do not interpolate!
def calculate_aco_2028_target(baseline_eui, final_target):
    # This interpolation approach is incorrect
    years_to_2028 = 2028 - baseline_year
    years_to_2032 = 2032 - baseline_year
    return baseline_eui - (baseline_eui - final_target) * (years_to_2028/years_to_2032)
```

---

## Decision to Opt-In

Buildings must decide by 2026 whether to follow Standard or ACO path. Key considerations:

1. **Cash Flow**: ACO delays penalties by 3 years
2. **Total Cost**: Higher penalty rate may result in higher total cost
3. **Technical Feasibility**: More time for complex retrofits
4. **Market Conditions**: Time to secure financing or wait for technology

---

## Example: Building 2952

```
Current EUI: 65.3 kBtu/sqft
First Interim Target: 65.4 kBtu/sqft
Final Target: 61.0 kBtu/sqft

Standard Path:
- 2025: No penalty (65.3 < 65.4)
- 2027: Penalty on 2.1 kBtu excess
- 2030: Penalty on 4.3 kBtu excess

ACO Path:
- 2028: No penalty (65.3 < 65.4)
- 2032: Penalty on 4.3 kBtu excess at higher rate
```

**Result**: Standard path recommended due to lower total cost

---

## Common Misconceptions

❌ **Wrong**: ACO buildings get easier targets  
✅ **Right**: ACO buildings get more time to meet the same targets

❌ **Wrong**: 2028 target is interpolated between baseline and final  
✅ **Right**: 2028 target equals the First Interim Target

❌ **Wrong**: ACO is always better for cash flow  
✅ **Right**: ACO costs more if penalties are inevitable due to higher rate

---

## References

- Energize Denver Ordinance No. 2021-1310
- Building Performance Standards Rulemaking 2024
- penalty_calculation_source_of_truth.md v1.3
