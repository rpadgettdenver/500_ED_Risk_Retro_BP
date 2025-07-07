# Energize Denver Penalty Math Explained
## A Plain English Guide to Our Calculations (Updated December 2024)

### Table of Contents
1. [Basic Penalty Formula](#basic-penalty-formula)
2. [The Two Compliance Paths](#the-two-compliance-paths)
3. [Target Years and Reporting Timeline](#target-years-and-reporting-timeline)
4. [EUI Reduction Caps and Floors](#eui-reduction-caps-and-floors)
5. [NPV Analysis for Opt-In Decisions](#npv-analysis)
6. [Real-World Examples](#real-world-examples)
7. [Key Assumptions](#key-assumptions)

---

## 1. Basic Penalty Formula

The fundamental penalty calculation is straightforward:

**Annual Penalty = EUI Gap × Building Size × Penalty Rate**

Where:
- **EUI Gap** = How much your building exceeds the target (in kBtu/sqft/year)
- **Building Size** = Gross floor area (in square feet)
- **Penalty Rate** = $0.15 or $0.23 per kBtu

### Example:
- Building has 100 kBtu/sqft actual EUI
- Target is 80 kBtu/sqft
- Building is 50,000 sqft
- EUI Gap = 100 - 80 = 20 kBtu/sqft
- Annual Penalty = 20 × 50,000 × $0.15 = **$150,000**

### Important Note:
**Penalties are only assessed in specific target years, not every year!**

---

## 2. The Two Compliance Paths

### Default Path
- **Penalty Rate**: $0.15 per kBtu
- **Fine Years**: 2025, 2027, and 2030 (3 penalty assessments total)
- **Timeline**: 6 years to achieve compliance
- **Who Should Choose**: Buildings that can meet targets with moderate effort

### Opt-In Alternative Compliance Option (ACO) Path
- **Penalty Rate**: $0.23 per kBtu (53% higher!)
- **Fine Years**: 2028 and 2032 (2 penalty assessments total)
- **Timeline**: 8 years to achieve compliance
- **Who Should Choose**: Buildings that need more time or face impossible targets

### The Trade-Off:
- Opt-in gives you 3 extra years before first penalty
- But you pay a higher rate when penalties do apply
- Fewer penalty years (2 vs 3) can actually result in lower total cost despite higher rate

---

## 3. Target Years and Reporting Timeline

### Understanding the Timeline:
- **Target Year**: The year your building's EUI is measured against
- **Reporting Year**: The following year when you report a full year of data
- **Fine Year**: When penalties are assessed (same as reporting year)

### Default Path Timeline:
- **2024**: First interim target year → Report and pay fines in 2025
- **2026**: Second interim target year → Report and pay fines in 2027
- **2029**: Final target year → Report and pay fines in 2030

### Opt-In Path Timeline:
- **2027**: First target year → Report and pay fines in 2028
- **2031**: Final target year → Report and pay fines in 2032

### Why This Matters:
Buildings need a full calendar year of energy data to report, so fines are always assessed the year after the target year.

---

## 4. EUI Reduction Caps and Floors

### Maximum Required Reduction: ~42% from baseline

No building is required to reduce more than 42% from its baseline EUI:
- If baseline = 100, final target ≥ 58
- If baseline = 1,000, final target ≥ 580
- Prevents technically impossible requirements

### MAI Minimum Floor: 52.9 kBtu/sqft

For Manufacturing/Agricultural/Industrial (MAI) buildings:
- **No target will ever be set below 52.9 kBtu/sqft**
- This overrides all percentage-based calculations
- Recognizes that industrial processes require minimum energy

### How Caps and Floors Work:

1. **Calculate normal target** based on building type and baseline
2. **Apply 42% maximum reduction cap** if needed
3. **For MAI buildings, apply 52.9 minimum floor**
4. **Use whichever gives the highest (least strict) target**

### Example - High-Energy Manufacturing:
- Baseline EUI: 1,000 kBtu/sqft
- Normal calculation: 50 kBtu/sqft target (95% reduction - impossible!)
- 42% cap: 1,000 × (1 - 0.42) = 580 kBtu/sqft
- MAI floor: 52.9 kBtu/sqft
- **Final target: 580 kBtu/sqft** (42% cap governs)

### Example - Efficient Manufacturing:
- Baseline EUI: 100 kBtu/sqft
- Normal calculation: 40 kBtu/sqft target
- 42% cap: 100 × (1 - 0.42) = 58 kBtu/sqft
- MAI floor: 52.9 kBtu/sqft
- **Final target: 58 kBtu/sqft** (42% cap governs, still above floor)

### Example - Very Efficient Manufacturing:
- Baseline EUI: 80 kBtu/sqft
- Normal calculation: 35 kBtu/sqft target
- 42% cap: 80 × (1 - 0.42) = 46.4 kBtu/sqft
- MAI floor: 52.9 kBtu/sqft
- **Final target: 52.9 kBtu/sqft** (MAI floor governs)

---

## 5. NPV Analysis for Opt-In Decisions

### What is NPV?
**Net Present Value** calculates today's value of future payments, accounting for the time value of money.

### Key Concept:
**Money paid later is worth less than money paid today**

### Our Assumptions:
- **Discount Rate**: 7% (typical for commercial real estate)
- **Formula**: Present Value = Future Payment ÷ (1.07)^years

### Example NPV Calculation:

Assume a building faces $150,000 penalty each assessment year:

**Default Path (Total nominal: $450,000)**
- 2025: $150,000 ÷ 1.07¹ = $140,187 (PV)
- 2027: $150,000 ÷ 1.07³ = $122,470 (PV)
- 2030: $150,000 ÷ 1.07⁶ = $100,028 (PV)
- **Total NPV: $362,685**

**Opt-In Path (Total nominal: $460,000)**
Same building, higher rate: $230,000 per assessment
- 2028: $230,000 ÷ 1.07⁴ = $175,394 (PV)
- 2032: $230,000 ÷ 1.07⁸ = $133,902 (PV)
- **Total NPV: $309,296**

**Result: Opt-in saves $53,389 in present value despite higher nominal cost!**

---

## 6. Real-World Examples

### Example 1: Small Office Building (Don't Opt-In)
- **Size**: 30,000 sqft
- **Current EUI**: 95 kBtu/sqft
- **2025 Target**: 85 kBtu/sqft
- **2030 Target**: 75 kBtu/sqft

**Default Path:**
- 2025: (95-85) × 30,000 × $0.15 = $45,000
- 2027: (95-80) × 30,000 × $0.15 = $67,500
- 2030: (95-75) × 30,000 × $0.15 = $90,000
- **Total: $202,500 (NPV: $164,091)**

**Opt-In Path:**
- 2028: (95-75) × 30,000 × $0.23 = $138,000
- 2032: (95-75) × 30,000 × $0.23 = $138,000
- **Total: $276,000 (NPV: $185,629)**

**Decision: Stay default (saves $21,538 in NPV)**

### Example 2: Manufacturing Building (Opt-In)
- **Size**: 50,000 sqft
- **Current EUI**: 500 kBtu/sqft
- **Baseline**: 500 kBtu/sqft
- **Calculated Target**: 50 kBtu/sqft
- **Applied Target**: 290 kBtu/sqft (42% cap)
- **Gap**: 210 kBtu/sqft

**Default Path:**
- 2025: 210 × 50,000 × $0.15 = $1,575,000
- 2027: 210 × 50,000 × $0.15 = $1,575,000
- 2030: 210 × 50,000 × $0.15 = $1,575,000
- **Total: $4,725,000 (NPV: $3,821,476)**

**Opt-In Path:**
- 2028: 210 × 50,000 × $0.23 = $2,415,000
- 2032: 210 × 50,000 × $0.23 = $2,415,000
- **Total: $4,830,000 (NPV: $3,249,135)**

**Decision: Opt-in (saves $572,341 in NPV)**

### Example 3: Multifamily Building (Close Call)
- **Size**: 100,000 sqft
- **Current EUI**: 65 kBtu/sqft
- **2025 Target**: 60 kBtu/sqft
- **2030 Target**: 50 kBtu/sqft

**Default Path:**
- 2025: (65-60) × 100,000 × $0.15 = $75,000
- 2027: (65-55) × 100,000 × $0.15 = $150,000
- 2030: (65-50) × 100,000 × $0.15 = $225,000
- **Total: $450,000 (NPV: $381,318)**

**Opt-In Path:**
- 2028: (65-50) × 100,000 × $0.23 = $345,000
- 2032: (65-50) × 100,000 × $0.23 = $345,000
- **Total: $690,000 (NPV: $364,443)**

**Decision: Stay default (saves $16,875 in NPV) - but it's close!**

---

## 7. Key Assumptions in Our Model

### Financial Parameters:
- **Discount Rate**: 7% annually
- **No Inflation**: Penalty rates remain constant
- **No EUI Improvements**: Conservative assumption
- **Weather Normalized EUI**: Used for fair comparisons

### Retrofit Cost Estimates (per sqft):
- **Light Retrofit** (<15% reduction): $5
- **Moderate Retrofit** (15-30% reduction): $12
- **Deep Retrofit** (>30% reduction): $25

### Decision Rules:

**Always Opt-In If:**
- Cannot meet any targets (2025, 2027, and 2030)
- Required reduction >40%
- Cash flow constraints prevent paying early penalties
- Technical infeasibility (very old buildings, complex systems)

**Never Opt-In If:**
- Already meet 2025 target
- Required reduction <10%
- NPV analysis shows opt-in costs >$100k more

**Use NPV Analysis If:**
- Between 10-40% reduction needed
- Can potentially meet some but not all targets
- Cash flow is not a constraint

### Special Considerations:

**MAI Buildings:**
- Minimum target floor: 52.9 kBtu/sqft
- Often have process loads that can't be reduced
- May have different compliance pathways

**Equity Priority Buildings (EPB):**
- Same penalty structure
- Priority for incentive funding
- May receive additional technical assistance

**Exempt Buildings:**
- Government buildings
- Hospitals
- Buildings with significant affordable housing
- Pay no penalties but must still report

---

## Summary: The Opt-In Decision Framework

### Step 1: Check Immediate Constraints
- Can you meet the 2025 target? If yes → Don't opt-in
- Is reduction >40% needed? If yes → Opt-in
- Cash flow problems? If yes → Consider opt-in

### Step 2: Run Financial Analysis
- Calculate penalties for both paths
- Apply NPV discounting
- Compare total present values

### Step 3: Consider Strategic Factors
- Planning to sell the building?
- Major renovation scheduled?
- Waiting for new technology?
- Need time to secure financing?

### The Key Insight:
**Opt-in is not always the best choice, even for buildings that miss early targets!**

The combination of:
- Time value of money (7% discount rate)
- Different penalty rates ($0.15 vs $0.23)
- Different number of assessments (3 vs 2)

Creates a complex decision that requires careful analysis.

### Bottom Line:
Our model helps buildings make data-driven decisions to minimize total compliance costs while meeting Denver's climate goals. The opt-in decision should be based on financial analysis, not just whether you can meet the first target.