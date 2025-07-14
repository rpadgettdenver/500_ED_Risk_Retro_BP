# Energize Denver Penalty Calculations - Definitive Source of Truth
**Version:** 1.2  
**Date:** January 14, 2025  
**Purpose:** Single authoritative reference for all penalty calculations

---

## 1. Core Penalty Rates

| Compliance Path | Penalty Rate | Target Years | Assessment Schedule |
|-----------------|--------------|--------------|---------------------|
| **Standard Path** (3 targets) | $0.15/kBtu | 2025*, 2027, 2030 | 2026, 2028, 2031, then annually |
| **Alternate Compliance (ACO)** (2 targets) | $0.23/kBtu | 2028, 2032 | 2029, 2033, then annually |
| **Timeline Extension** (1 target) | $0.35/kBtu | 2030 or 2032 | Following year, then annually |
| **Late Timeline Extension** | Base + $0.10/kBtu | Per extension terms | Following year, then annually |
| **Never Benchmarked** | $10.00/sqft | 2025, 2027, 2030 | 2026, 2028, 2031, then annually |

*Or as specified in Building_EUI_Targets.csv "First Interim Target Year" column

---

## 2. Critical Timing Rules

### 2.1 Target Year vs Payment Year
- **Target Year**: The calendar year of energy consumption being evaluated
- **Payment Year**: The following year when penalties are assessed and paid
- **Example**: 2025 target year → measured using 2025 consumption → penalties paid in 2026

### 2.2 Annual Penalties After Final Target
- Begin the year after final target if building remains non-compliant
- Continue indefinitely at the same rate until compliance achieved
- Standard Path: Annual penalties start 2031
- ACO Path: Annual penalties start 2033

### 2.3 Compliance Pathway Visualization
**IMPORTANT**: Both Standard and ACO paths start from the same baseline year and baseline EUI
- **Standard Path**: Baseline Year/EUI → 2025 → 2027 → 2030
- **ACO Path**: Baseline Year/EUI → 2028 → 2032
- Baseline Year is found in Building_EUI_Targets.csv "Baseline Year" column
- Penalties are calculated based on current EUI vs target EUI
- Visualizations should show both paths starting from baseline, not current year

---

## 3. Penalty Calculation Formula

### 3.1 Standard Formula (EUI-based penalties)
```
Annual Penalty = MAX(0, (Actual_EUI - Final_Target_EUI)) × Building_SqFt × Penalty_Rate

Where:
- Actual_EUI = Weather Normalized Site EUI for the target year
- Final_Target_EUI = Target after applying caps/floors (see Section 4)
- Building_SqFt = Gross floor area from Building_EUI_Targets.csv
- Penalty_Rate = Rate based on compliance path (see Section 1)
```

### 3.2 Never Benchmarked Formula
```
Annual Penalty = Building_SqFt × $10.00

Where:
- Building_SqFt = Square footage from Office of the Assessor
- Applied in years 2025, 2027, 2030, then annually if non-compliant
```

---

## 4. Target Caps and Floors

**CRITICAL**: Raw targets in CSV must be adjusted before penalty calculations

### 4.1 Non-MAI Buildings - 42% Maximum Reduction Cap
```python
def apply_non_mai_cap(raw_target_eui, baseline_eui):
    """Apply 42% maximum reduction cap"""
    cap_target = baseline_eui * 0.58  # Maximum 42% reduction
    return max(raw_target_eui, cap_target)  # Use less stringent target
```

**Example:**
- Baseline EUI: 100 kBtu/sqft
- Raw Target: 40 kBtu/sqft (60% reduction - too aggressive)
- Capped Target: 58 kBtu/sqft (42% reduction)
- **Use: 58 kBtu/sqft**

### 4.2 MAI Buildings - 30% Reduction or 52.9 Floor
**IMPORTANT**: MAI designation is determined by presence in MAITargetSummary Report.csv, NOT by property type.

```python
def apply_mai_rules(raw_target_eui, baseline_eui, mai_adjusted_target=None):
    """Apply MAI-specific rules
    
    For MAI buildings, use the MAXIMUM (most lenient) of:
    - Adjusted Final Target from MAITargetSummary Report.csv
    - 30% reduction from baseline (baseline × 0.70)
    - 52.9 kBtu/sqft floor
    """
    # Calculate 30% reduction
    reduction_target = baseline_eui * 0.70
    
    # Start with maximum of reduction and floor
    mai_target = max(reduction_target, 52.9)
    
    # If we have adjusted target from CSV, include it
    if mai_adjusted_target is not None:
        mai_target = max(mai_target, mai_adjusted_target)
        
    # Also consider raw target
    return max(raw_target_eui, mai_target)  # Use most lenient target
```

**MAI Building Identification:**
- Load building IDs from MAITargetSummary Report.csv
- A building is MAI if its ID appears in this file
- MAI buildings include various property types: Manufacturing, Data Centers, Distribution Centers, Warehouses, etc.

**Example 1 (High Baseline MAI):**
- Baseline EUI: 200 kBtu/sqft
- Raw Target: 50 kBtu/sqft
- MAI Target: 140 kBtu/sqft (30% reduction)
- **Use: 140 kBtu/sqft**

**Example 2 (Low Baseline MAI):**
- Baseline EUI: 70 kBtu/sqft
- Raw Target: 35 kBtu/sqft
- MAI Target: 52.9 kBtu/sqft (floor)
- **Use: 52.9 kBtu/sqft**

---

## 5. Target Selection by Path

### 5.1 Standard Path Targets
Use columns from Building_EUI_Targets.csv:
- **2025 Target**: "First Interim Target EUI" (apply caps/floors)
- **2027 Target**: "Second Interim Target EUI" (apply caps/floors)
- **2030 Target**: "Adjusted Final Target EUI" or "Original Final Target EUI" (apply caps/floors)

### 5.2 ACO/Opt-in Path Targets
- **2028 Target**: Use "First Interim Target EUI" from Building_EUI_Targets.csv (apply caps/floors)
- **2032 Target**: Use same as 2030 target from "Adjusted Final Target EUI" or "Original Final Target EUI" (apply caps/floors)
- **No 2027 target** for opt-in buildings

### 5.3 ACO 2028 Target Selection
```python
def get_aco_2028_target(building_row):
    """Get ACO 2028 target - uses First Interim Target EUI"""
    # ACO 2028 target uses the same target as Standard Path 2025
    # This is the First Interim Target EUI from the CSV
    first_interim_target = building_row['First Interim Target EUI']
    
    # Apply caps/floors as appropriate
    if is_mai_building:
        return apply_mai_rules(first_interim_target, baseline_eui)
    else:
        return apply_non_mai_cap(first_interim_target, baseline_eui)
```

---

## 6. Complete Calculation Process

### Step 1: Load Building Data
```python
# From Building_EUI_Targets.csv
building_id = row['Building ID']
baseline_eui = row['Baseline EUI']
baseline_year = row['Baseline Year']
sqft = row['Master Sq Ft']
first_interim_year = row['First Interim Target Year'] or 2025

# Check MAI designation (from MAITargetSummary Report.csv)
is_mai = building_id in mai_target_summary_ids

# If MAI, get adjusted target from MAITargetSummary
if is_mai:
    mai_adjusted_target = mai_targets.get(building_id, {}).get('adjusted_final_target')
else:
    mai_adjusted_target = None
```

### Step 2: Determine Compliance Path
```python
if building_opted_in:  # Must decide by 2026
    path = 'ACO'
    target_years = [2028, 2032]
    penalty_rate = 0.23
else:
    path = 'Standard'
    target_years = [first_interim_year, 2027, 2030]
    penalty_rate = 0.15
```

### Step 3: Apply Caps/Floors to Targets
```python
for year in target_years:
    if path == 'ACO' and year == 2028:
        # ACO 2028 uses First Interim Target EUI
        raw_target = row['First Interim Target EUI']
    else:
        raw_target = get_raw_target_for_year(year)  # From CSV
    
    if is_mai:
        # For MAI: MAX(adjusted_target, 30% reduction, 52.9)
        final_target = apply_mai_rules(raw_target, baseline_eui, mai_adjusted_target)
    else:
        # For non-MAI: 42% cap
        final_target = apply_non_mai_cap(raw_target, baseline_eui)
```

### Step 4: Calculate Penalties
```python
for target_year in target_years:
    actual_eui = get_weather_normalized_eui(building_id, target_year)
    final_target_eui = get_final_target_after_caps(target_year)
    
    if actual_eui > final_target_eui:
        gap = actual_eui - final_target_eui
        penalty = gap * sqft * penalty_rate
        payment_year = target_year + 1
        
        record_penalty(building_id, target_year, payment_year, penalty)
```

### Step 5: Annual Penalties After Final Target
```python
final_target_year = target_years[-1]  # 2030 or 2032
if still_non_compliant_after(final_target_year):
    for year in range(final_target_year + 1, 2043):  # 12+ years
        penalty = gap * sqft * penalty_rate
        record_penalty(building_id, year - 1, year, penalty)
```

---

## 7. Special Cases and Exceptions

### 7.1 Never Benchmarked Buildings
- No EUI-based calculation
- Flat $10/sqft in years 2026, 2028, 2031
- Then $10/sqft annually if still non-benchmarking

### 7.2 Late Timeline Extensions
- Add $0.10/kBtu to whatever base rate applies
- Example: Standard path late extension = $0.15 + $0.10 = $0.25/kBtu

### 7.3 Buildings That Regress
- If compliance achieved but then EUI increases >5%
- Same penalty rate applies as original path

### 7.4 Exempt Buildings
- Government buildings, hospitals, qualifying affordable housing
- Must still report but pay no penalties

---

## 8. Implementation Checklist

When implementing these calculations:

- [ ] Read Baseline Year from CSV for pathway starting points
- [ ] Read First Interim Target Year from CSV (default to 2025 if missing)
- [ ] Apply caps/floors to ALL targets before using them
- [ ] Use weather normalized EUI for actual consumption
- [ ] Calculate penalties in target year, assess in following year
- [ ] Include annual penalties after final target year
- [ ] Handle MAI buildings with special rules
- [ ] Account for never-benchmarked buildings differently
- [ ] Store both target year and payment year for each penalty
- [ ] For ACO path, use First Interim Target EUI for 2028 target

---

## 9. Testing Validation

### Test Case 1: Standard Path Building
- Building: 50,000 sqft office
- Baseline Year: 2019
- Baseline: 100 kBtu/sqft
- Current: 85 kBtu/sqft
- 2030 Raw Target: 40 kBtu/sqft
- 2030 Capped Target: 58 kBtu/sqft (42% cap)
- 2030 Penalty: (85 - 58) × 50,000 × $0.15 = $202,500

### Test Case 2: MAI Building
- Building: 100,000 sqft manufacturing
- Baseline Year: 2019
- Baseline: 200 kBtu/sqft
- Current: 180 kBtu/sqft
- 2030 Raw Target: 50 kBtu/sqft
- 2030 MAI Adjusted (from CSV): 140 kBtu/sqft
- 2030 Final Target: MAX(140, 200×0.70, 52.9) = 140 kBtu/sqft
- 2030 Penalty: (180 - 140) × 100,000 × $0.15 = $600,000

### Test Case 3: Opt-in Building
- Building: 30,000 sqft multifamily
- Baseline Year: 2019
- Baseline: 100 kBtu/sqft
- Current: 70 kBtu/sqft
- First Interim Target: 75 kBtu/sqft
- 2028 Target: 75 kBtu/sqft (uses First Interim Target)
- 2032 Target: 50 kBtu/sqft (after caps)
- 2028 Penalty: $0 (current < target)
- 2032 Penalty: (70 - 50) × 30,000 × $0.23 = $138,000

---

## 10. Version Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-07-13 | Initial definitive version consolidating all sources |
| 1.1 | 2025-07-13 | Updated MAI logic: identification via MAITargetSummary, MAX() calculation |
| 1.2 | 2025-01-14 | Added clarification on pathway visualization, baseline year usage, and ACO 2028 target calculation |
| 1.3 | 2025-07-14 | CRITICAL CORRECTION: ACO 2028 target uses First Interim Target EUI from CSV, NOT interpolation |

---

**This document supersedes all previous penalty calculation documentation and should be the sole reference for implementation.**