# Energize Denver Quick Reference Guide
**Version:** 1.0 | **Date:** July 14, 2025

---

## 🎯 ACO Target Logic - At a Glance

| Path | 2025/2028 | 2027 | 2030/2032 | Rate |
|------|-----------|------|-----------|------|
| **Standard** | First Interim Target | Second Interim Target | Final Target | $0.15/kBtu |
| **ACO** | First Interim Target | *(skip)* | Final Target | $0.23/kBtu |

**Key Point**: ACO 2028 = Standard 2025 target (NOT interpolated!)

```python
# CORRECT
aco_2028_target = building_data['first_interim_target']

# WRONG - DO NOT USE
aco_2028_target = interpolate(baseline, final)  # ❌
```

---

## 💡 Opt-In Decision Tree

```
NPV Advantage > $50,000? ────────► YES ─► OPT-IN (95%)
    │
    NO
    ▼
Cash Constrained? ───────────────► YES ─► OPT-IN (85%)
    │
    NO
    ▼
Reduction > 35%? ────────────────► YES ─► OPT-IN (80%)
    │
    NO
    ▼
NPV Advantage > $10,000? ────────► YES ─► OPT-IN (70%)
    │
    NO
    ▼
STANDARD PATH (60%)
```

### Cash Constrained = 
- Affordable Housing
- Senior Care Community  
- First year penalty > $500k

---

## 💰 Retrofit Cost Quick Lookup

| Reduction Needed | Cost/sqft | Retrofit Level | Typical Measures |
|-----------------|-----------|----------------|------------------|
| **≤10%** | $5 | Minor | LEDs, controls, weatherization |
| **10-25%** | $15 | Moderate | + HVAC controls, BAS, envelope |
| **25-40%** | $30 | Major | + Equipment replacement |
| **>40%** | $50 | Deep | Full system redesign |

### Quick Calc
```
Retrofit Cost = Square Feet × Cost/sqft × Adjustments

Adjustments:
- Multifamily: 0.9x
- Office: 1.0x  
- Healthcare: 1.5x
- Age >50 years: 1.4x
```

---

## 📊 NPV Calculation

**Discount Rate**: 7%

**Standard Path NPV**:
```
Year 0 (2025): Penalty₂₀₂₅
Year 2 (2027): Penalty₂₀₂₇ ÷ 1.07²
Year 5 (2030): Penalty₂₀₃₀ ÷ 1.07⁵
+ Annual penalties 2031-2042
```

**ACO Path NPV**:
```
Year 3 (2028): Penalty₂₀₂₈ ÷ 1.07³
Year 7 (2032): Penalty₂₀₃₂ ÷ 1.07⁷
+ Annual penalties 2033-2042
```

---

## 🚨 Common Mistakes to Avoid

❌ **Interpolating 2028 target**  
✅ Use First Interim Target directly

❌ **Using $0.30 or $0.70 penalty rates**  
✅ Standard: $0.15, ACO: $0.23

❌ **Assuming ACO is always better**  
✅ Check NPV - higher rate often costs more

❌ **Forgetting annual penalties after final year**  
✅ Penalties continue through 2042

---

## 📋 Building Analysis Checklist

- [ ] Load First Interim Target for 2028 (no interpolation)
- [ ] Apply MAI floor (52.9) if applicable  
- [ ] Apply 42% cap for non-MAI buildings
- [ ] Calculate penalties at correct rates ($0.15 or $0.23)
- [ ] Include annual penalties through 2042
- [ ] Discount to NPV using 7% rate
- [ ] Check all 5 decision criteria for opt-in
- [ ] Estimate retrofit costs using tier system

---

## 🔧 Code Snippets

### Get Correct Targets
```python
# Standard Path
targets_standard = {
    2025: data['first_interim_target'],
    2027: data['second_interim_target'], 
    2030: data['final_target_with_logic']
}

# ACO Path  
targets_aco = {
    2028: data['first_interim_target'],  # Same as 2025!
    2032: data['final_target_with_logic'] # Same as 2030!
}
```

### Calculate Penalty
```python
def calculate_penalty(eui_actual, eui_target, sqft, path='standard'):
    rate = 0.15 if path == 'standard' else 0.23
    gap = max(0, eui_actual - eui_target)
    return gap * sqft * rate
```

### Estimate Retrofit
```python
def estimate_retrofit_cost(sqft, reduction_pct):
    if reduction_pct <= 10: return sqft * 5
    elif reduction_pct <= 25: return sqft * 15
    elif reduction_pct <= 40: return sqft * 30
    else: return sqft * 50
```

---

## 📞 Quick Decision Examples

**Small reduction (5-10%)** → Standard Path  
**Cash tight + penalties** → ACO Path  
**Old building + 30%+ reduction** → ACO Path  
**Already meeting 2025** → Standard Path  
**Can't meet any targets** → ACO Path  

---

## 📁 Key Files Reference

- **Source of Truth**: `/docs/penalty_calculation_source_of_truth.md`
- **Penalty Calculator**: `/src/utils/penalty_calculator.py`
- **Target Loader**: `/src/utils/eui_target_loader.py`
- **Opt-In Logic**: `/src/utils/opt_in_predictor.py`
- **Building Analyzer**: `/src/analysis/building_compliance_analyzer_v2.py`

---

*Remember: When in doubt, check the source of truth documentation!*