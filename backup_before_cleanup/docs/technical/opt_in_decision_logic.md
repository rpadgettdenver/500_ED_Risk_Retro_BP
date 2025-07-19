# Opt-In Decision Logic Documentation
**Version:** 1.0  
**Date:** July 14, 2025  
**Purpose:** Document the decision framework for recommending Standard vs ACO compliance paths

---

## Overview

This document explains the logic used to recommend whether a building should opt into the Alternate Compliance Option (ACO) or remain on the Standard compliance path for Energize Denver.

---

## Decision Framework

### Primary Decision Factors (in priority order)

#### 1. **Significant NPV Advantage (>$50,000)**
- **Decision**: OPT-IN
- **Confidence**: 95%
- **Rationale**: Large financial benefit outweighs higher penalty rate

#### 2. **Cash Flow Constraints**
- **Decision**: OPT-IN
- **Confidence**: 85%
- **Applies to**:
  - Affordable Housing
  - Senior Care Communities
  - Buildings with >$500k first-year penalty
- **Rationale**: Delayed penalties preserve operating capital

#### 3. **High Reduction Requirement (>35%)**
- **Decision**: OPT-IN
- **Confidence**: 80%
- **Rationale**: Complex retrofits need more time for planning/execution

#### 4. **Moderate NPV Advantage (>$10,000)**
- **Decision**: OPT-IN
- **Confidence**: 70%
- **Rationale**: Meaningful financial benefit justifies higher rate

#### 5. **Default Case**
- **Decision**: STANDARD
- **Confidence**: 60%
- **Rationale**: Lower penalty rate minimizes long-term costs

---

## NPV Calculation Methodology

### Discount Rate: 7% (industry standard for real estate)

### Standard Path NPV:
```
NPV = Penalty_2025/(1.07^0) + Penalty_2027/(1.07^2) + Penalty_2030/(1.07^5) + Annual_Penalties_2031-2042
```

### ACO Path NPV:
```
NPV = Penalty_2028/(1.07^3) + Penalty_2032/(1.07^7) + Annual_Penalties_2033-2042
```

### NPV Advantage:
```
NPV_Advantage = Standard_Path_NPV - ACO_Path_NPV
```
- **Positive**: ACO saves money (opt-in favorable)
- **Negative**: ACO costs more (standard favorable)

---

## Secondary Decision Factors

### Building Characteristics
1. **MAI Buildings**: More likely to opt-in due to lenient targets
2. **Building Age**: Older buildings (>50 years) favor opt-in
3. **Property Type**: Multifamily and office buildings vary widely

### Technical Complexity Score
```python
technical_score = min(100, reduction_pct * 2 + building_age / 2)
```
- **<30**: Straightforward retrofits
- **30-60**: Moderate complexity
- **60-80**: Technically challenging
- **>80**: Extremely difficult (favors opt-in)

---

## Decision Examples

### Example 1: Building 2952 (Standard Recommended)
```
Current EUI: 65.3
Reduction Needed: 6.6%
NPV Advantage: -$11,942 (negative)
Cash Constrained: No
Technical Score: 42

Decision: STANDARD (60% confidence)
Reason: Opt-in costs more due to higher penalty rate
```

### Example 2: Affordable Housing Complex (Opt-In Recommended)
```
Current EUI: 85.0
Reduction Needed: 25%
First Year Penalty: $750,000
Cash Constrained: Yes
NPV Advantage: $25,000

Decision: OPT-IN (85% confidence)
Reason: Cash flow constraints require delayed penalties
```

### Example 3: Old Manufacturing Plant (Opt-In Recommended)
```
Current EUI: 150.0
Reduction Needed: 45%
Building Age: 75 years
Technical Score: 95
NPV Advantage: $125,000

Decision: OPT-IN (95% confidence)
Reason: Technical infeasibility and large NPV advantage
```

---

## Special Cases

### Always Opt-In
- Cannot meet ANY targets (2025, 2027, and 2030 all exceeded)
- Cash constrained with immediate large penalties
- Technical score ≥80 (extremely difficult retrofits)

### Never Opt-In
- Already meets 2025 target
- NPV disadvantage >$100,000
- Reduction needed <10% (minor improvements only)

---

## Implementation Thresholds

```python
# Decision thresholds
NPV_SIGNIFICANT = 50000    # Strong opt-in signal
NPV_MODERATE = 10000       # Moderate opt-in signal
NPV_NEGATIVE_LARGE = -100000  # Strong standard signal

REDUCTION_HIGH = 35        # Technical difficulty threshold
REDUCTION_MINOR = 10       # Easy retrofit threshold

PENALTY_CASH_CRISIS = 500000  # First-year penalty threshold
TECHNICAL_INFEASIBLE = 80     # Technical score threshold
```

---

## Confidence Scoring

Confidence indicates the strength of the recommendation:

- **95-100%**: Very strong indicators (can't meet targets, huge NPV advantage)
- **80-94%**: Strong indicators (cash constrained, technical difficulty)
- **70-79%**: Moderate indicators (meaningful NPV advantage)
- **60-69%**: Marginal decision (could go either way)
- **<60%**: Weak recommendation (consider other factors)

---

## Key Insights

1. **Small Reductions Favor Standard**: Buildings close to compliance should avoid ACO's higher rate
2. **Cash Flow Trumps NPV**: Operational continuity may outweigh total cost
3. **Technical Feasibility Matters**: Some retrofits simply need more time
4. **NPV Threshold is Critical**: $50k advantage is the tipping point

---

## Updating the Logic

When modifying decision thresholds:
1. Test with representative building samples
2. Validate NPV calculations match financial models
3. Consider market conditions (interest rates, construction costs)
4. Review actual opt-in decisions from previous years

---

## References

- opt_in_predictor.py implementation
- BigQuery opt-in decision model
- Financial analysis methodology documentation