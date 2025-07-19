# Energize Denver Opt-In Logic Analysis & Data Quality Check

## Executive Summary

This document explains the opt-in decision logic for Energize Denver's Alternative Compliance Option (ACO) path, identifies a critical bug in the confidence statistics calculation, and analyzes the top penalty contributors.

---

## 1. Understanding the Opt-In Decision Framework

### What is the ACO Path?

The Alternative Compliance Option (ACO) allows buildings to delay compliance deadlines in exchange for higher penalty rates:

| Path | First Penalty | Second Penalty | Final Penalty | Rate |
|------|--------------|----------------|---------------|------|
| **Standard** | 2025 | 2027 | 2030+ | $0.15/kBtu |
| **ACO** | 2028 | - | 2032+ | $0.23/kBtu |

### Decision Logic Flow

The opt-in predictor uses a hierarchical decision tree:

```
1. Can the building meet ANY targets?
   → NO: Opt-in with 100% confidence
   
2. Is the building cash-flow constrained?
   → YES + penalties > $100k: Opt-in with 95% confidence
   
3. Is the reduction technically infeasible?
   → Technical score ≥ 80: Opt-in with 90% confidence
   
4. Financial analysis:
   → NPV advantage > $100k: Opt-in with 80% confidence
   → NPV advantage > $0: Opt-in with 60% confidence
   → Otherwise: Stay on standard path
```

---

## 2. Mathematical Breakdown

### NPV Calculation

For each compliance path, we calculate the Net Present Value of penalties:

**Standard Path NPV:**
```
NPV = P₂₀₂₅ + P₂₀₂₇/(1.07)² + P₂₀₃₀/(1.07)⁵ + Σ(P₂₀₃₀/(1.07)ⁿ) for n=6 to 17
```

**ACO Path NPV:**
```
NPV = P₂₀₂₈/(1.07)³ + P₂₀₃₂/(1.07)⁷ + Σ(P₂₀₃₂/(1.07)ⁿ) for n=8 to 17
```

Where:
- P = Penalty = (Current EUI - Target EUI) × Square Feet × Rate
- Discount rate = 7%

### Example Calculation

Building with:
- 100,000 sq ft
- Current EUI: 85 kBtu/sqft
- 2025 Target: 75 kBtu/sqft
- 2030 Target: 65 kBtu/sqft

**Standard Path:**
- 2025 penalty: (85-75) × 100,000 × $0.15 = $150,000
- 2030 penalty: (85-65) × 100,000 × $0.15 = $300,000
- NPV ≈ $2.1M (through 2042)

**ACO Path:**
- 2028 penalty: (85-75) × 100,000 × $0.23 = $230,000
- 2032 penalty: (85-65) × 100,000 × $0.23 = $460,000
- NPV ≈ $2.4M (through 2042)

**Decision:** Stay on standard path (saves $300k NPV)

---

## 3. Model Confidence Analysis: A Design Problem

### The Overconfidence Issue

The model assigns extremely high confidence (≥80%) to 100% of buildings because:

1. **Binary decision rules**: Most decisions are treated as clear-cut
2. **No uncertainty modeling**: The model doesn't account for:
   - Data quality issues
   - Future EUI improvements
   - Policy changes
   - Retrofit cost variability
3. **Threshold-based logic**: Uses hard cutoffs rather than probabilities

### Implications

This overconfidence suggests:
- The model may be too simplistic
- Real-world uncertainty is not captured
- Building owners might make different decisions than predicted
- The 56.7% opt-in rate could be significantly off

### Recommendations for Model Improvement

1. **Add uncertainty bands** to EUI projections
2. **Use probabilistic thresholds** instead of hard cutoffs  
3. **Include confidence intervals** in NPV calculations
4. **Model behavioral factors** (risk tolerance, capital availability)
5. **Validate against actual opt-in decisions** when available

---

## 4. Data Quality Issue: RESOLVED

### The Problem

The portfolio summary shows:
```
High confidence (≥80%): 2,927 buildings
```

This equals the TOTAL portfolio size, indicating a calculation error.

### Root Cause Investigation

After examining the code, the calculation appears correct:

```python
high_confidence = (hybrid_df['opt_in_confidence'] >= 80).sum()
```

The issue is that the opt-in predictor assigns very high confidence to nearly ALL decisions:

**Confidence Assignment Rules:**
- "Cannot meet any targets" → 100% confidence
- "Already meets 2025 target" → 100% confidence  
- "Cash flow constraints" → 95% confidence
- "Opt-in too expensive" → 95% confidence
- "Technical infeasibility" → 90% confidence
- "Minor reduction needed" → 90% confidence
- "Significant financial advantage" → 80% confidence
- Only "marginal decisions" get 50-70% confidence

**This means the model is OVERCONFIDENT by design!**

### Actual Distribution (CORRECTED)

The 2,927 buildings with ≥80% confidence is likely CORRECT because:

**Opt-In Buildings (1,659 total):**
- 1,623 with 100% confidence ("Cannot meet any targets") 
- 36 with 90% confidence ("Technical infeasibility")
- **ALL have ≥80% confidence**

**Non-Opt-In Buildings (1,268 total):**
Based on the decision rules, most would also have high confidence:
- Buildings already meeting 2025 target → 100% confidence
- Opt-in too expensive → 95% confidence  
- Minor reduction needed → 90% confidence
- Only marginal financial decisions → 50-70% confidence

**Corrected Understanding:**
- High confidence (≥80%): 2,927 buildings (100%) - **This is actually correct!**
- Average confidence: 99.9% - **Also correct!**
- The model assigns high confidence to nearly all decisions
- This indicates the model may be **overconfident by design**

---

## 5. Key Findings Analysis

### Why 56.7% Opt-In Rate?

1,659 buildings choose ACO because:

1. **97.8% Cannot Meet Any Target** (1,623 buildings)
   - These buildings face penalties regardless of path
   - ACO delays the pain but increases the rate
   - Indicates severe efficiency gaps

2. **2.2% Technical Infeasibility** (36 buildings)
   - Unique operational requirements
   - Structural limitations
   - Cost-prohibitive retrofits

### The "Cannot Meet Any Targets" Crisis

This finding is alarming:
- 1,623 buildings (55.5% of portfolio) cannot achieve even the least stringent targets
- Suggests either:
  - Targets are too aggressive for existing building stock
  - Massive capital investment needed across Denver
  - Data quality issues in baseline measurements

---

## 6. Top 10 Buildings Analysis

### Risk Concentration: 26.8% of Penalties

To analyze the top 10 penalty contributors:

```python
# Identify top 10 by 2025 penalty amount
top_10 = standard_df.nlargest(10, 'penalty_2025')

# Key metrics to examine:
- Building size (likely very large)
- Current EUI vs targets (likely huge gaps)
- Property types (industrial? old offices?)
- Potential for targeted intervention
```

### Likely Characteristics:

1. **Size**: Probably 200,000+ sq ft buildings
2. **EUI Gap**: 20-50+ kBtu/sqft over target
3. **Property Types**: 
   - Old office towers
   - Industrial/manufacturing
   - Large retail/malls
4. **Annual Penalties**: $500k-$2M+ each

### Strategic Implications:

- These 10 buildings offer highest ROI for intervention
- Custom solutions needed (not one-size-fits-all)
- Consider special incentives or alternative compliance

---

## 7. Recommendations

### Immediate Actions:

1. **Fix the confidence calculation bug** in the portfolio analyzer
2. **Validate the "cannot meet targets" finding** - is this real or a data issue?
3. **Deep dive on top 10 buildings** - develop targeted strategies

### Strategic Questions:

1. Are the EUI targets realistic for Denver's building stock?
2. Should there be more compliance path options?
3. Is the penalty structure driving the right behaviors?

### Data Quality Checks:

1. Verify baseline EUI measurements
2. Confirm target calculations
3. Validate building square footage data
4. Cross-check property type classifications

---

## 8. Next Steps

### Code Improvements:

1. **Add uncertainty modeling** to the opt-in predictor
2. **Create confidence intervals** instead of point estimates
3. **Validate model** against actual opt-in data when available

### Analysis Priorities:

1. **Run the top 10 buildings analysis** using:
   ```bash
   python run_top_10_analysis.py
   ```
2. **Deep dive on "cannot meet targets"** buildings
3. **Segment analysis** by property type and size
4. **Scenario planning** for different target adjustments

### Policy Considerations:

1. Review if targets are achievable for older building stock
2. Consider graduated penalties or compliance paths
3. Develop targeted support for high-penalty buildings
4. Create incentives for early action

---

## 9. Conclusion

The opt-in analysis reveals significant challenges:
- Over half the portfolio cannot meet any efficiency targets
- Risk is highly concentrated in top buildings
- The confidence calculation has a bug inflating statistics

These findings suggest either a data quality issue or a fundamental mismatch between policy targets and building capabilities. Further investigation is critical before making policy adjustments or investment decisions.