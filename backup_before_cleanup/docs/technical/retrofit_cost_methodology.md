# Retrofit Cost Methodology
**Version:** 1.0  
**Date:** July 14, 2025  
**Purpose:** Document the methodology for estimating building retrofit costs based on EUI reduction requirements

---

## Overview

This document explains the tiered approach to estimating retrofit costs for Energize Denver compliance. Costs are estimated based on the percentage of EUI reduction required and represent industry-standard ranges for commercial building improvements.

---

## Cost Tiers

### Tier 1: Minor Retrofits (≤10% reduction)
**Cost**: $5/sqft  
**Typical Measures**:
- LED lighting upgrades
- Lighting controls and sensors
- Basic weatherization and air sealing
- Programmable thermostats
- Low-flow water fixtures
- Basic retro-commissioning

**Example**: 50,000 sqft office needing 8% reduction = $250,000

### Tier 2: Moderate Retrofits (10-25% reduction)
**Cost**: $15/sqft  
**Typical Measures**:
- All Tier 1 measures PLUS:
- HVAC controls and automation
- Variable frequency drives (VFDs)
- Building automation system (BAS) upgrades
- Envelope improvements (windows, insulation)
- Domestic hot water system upgrades
- Comprehensive retro-commissioning

**Example**: 100,000 sqft multifamily needing 20% reduction = $1,500,000

### Tier 3: Major Retrofits (25-40% reduction)
**Cost**: $30/sqft  
**Typical Measures**:
- All Tier 1 & 2 measures PLUS:
- Boiler or chiller replacement
- Major HVAC equipment upgrades
- Significant envelope improvements
- Heat recovery systems
- Major controls integration
- Partial window replacement

**Example**: 75,000 sqft retail needing 35% reduction = $2,250,000

### Tier 4: Deep Energy Retrofits (>40% reduction)
**Cost**: $50/sqft  
**Typical Measures**:
- Comprehensive system replacement
- Full HVAC system redesign
- Complete envelope retrofit
- Electrification of heating systems
- On-site renewable energy
- Full window replacement
- Advanced energy recovery

**Example**: 200,000 sqft manufacturing needing 45% reduction = $10,000,000

---

## Cost Calculation Formula

```python
def estimate_retrofit_cost(sqft, reduction_pct):
    """Estimate retrofit cost based on reduction needed"""
    if reduction_pct <= 10:
        cost_per_sqft = 5  # Minor
    elif reduction_pct <= 25:
        cost_per_sqft = 15  # Moderate
    elif reduction_pct <= 40:
        cost_per_sqft = 30  # Major
    else:
        cost_per_sqft = 50  # Deep
    
    return sqft * cost_per_sqft
```

---

## Important Considerations

### 1. **These are Planning Estimates**
- Actual costs vary significantly based on:
  - Building condition and age
  - System types and complexity
  - Local labor and material costs
  - Scope bundling opportunities
  - Available incentives

### 2. **Economies of Scale**
- Larger buildings often see lower $/sqft costs
- Portfolio-wide programs reduce unit costs
- Bulk procurement provides savings

### 3. **Cost Escalation**
- Add 3-5% annually for construction inflation
- Account for supply chain variability
- Consider labor availability impacts

### 4. **Soft Costs Not Included**
These estimates cover hard costs only. Add 20-30% for:
- Engineering and design
- Permits and inspections  
- Construction management
- Commissioning
- Financing costs

---

## Adjustment Factors

### Building Type Multipliers
```
Office: 1.0x (baseline)
Multifamily: 0.9x (simpler systems)
Retail: 1.1x (aesthetic considerations)
Healthcare: 1.5x (complex systems)
Manufacturing: 1.3x (process loads)
Historic: 1.4x (preservation requirements)
```

### Age Adjustments
```
<10 years: 0.8x (modern systems)
10-30 years: 1.0x (baseline)
30-50 years: 1.2x (asbestos, outdated systems)
>50 years: 1.4x (major infrastructure needs)
```

---

## Real-World Examples

### Building 2952 (Timperly Condominium)
```
Size: 52,826 sqft
Reduction Needed: 6.6%
Tier: Minor
Base Cost: $5/sqft
Building Type: Multifamily (0.9x)
Age: 57 years (1.4x)
Adjusted Cost: $5 × 0.9 × 1.4 = $6.30/sqft
Total Estimate: $333,000
```

### Large Office Building
```
Size: 250,000 sqft
Reduction Needed: 30%
Tier: Major
Base Cost: $30/sqft
Building Type: Office (1.0x)
Age: 25 years (1.0x)
Total Estimate: $7,500,000
```

---

## Validation Against Market Data

### Denver Market Benchmarks (2025)
- Basic Lighting Retrofit: $2-3/sqft
- Comprehensive Lighting + Controls: $4-6/sqft
- HVAC Tune-up: $3-5/sqft
- Boiler Replacement: $15-20/sqft
- Full HVAC Replacement: $25-35/sqft
- Deep Energy Retrofit: $40-80/sqft

Our tiers align with these market rates when considering bundled measures.

---

## Using Estimates in Decision Making

### Cost-Benefit Analysis
```python
def retrofit_payback(retrofit_cost, annual_penalty_avoided, energy_savings):
    """Calculate simple payback period"""
    annual_benefit = annual_penalty_avoided + energy_savings
    return retrofit_cost / annual_benefit
```

### Financing Thresholds
- <$10/sqft: Often cash-funded
- $10-30/sqft: Traditional financing
- >$30/sqft: Specialized energy financing needed

---

## Limitations and Disclaimers

1. **Estimates are ±30% accuracy** for planning purposes
2. **Detailed energy audits required** for project budgets
3. **Does not include**:
   - Utility incentives or rebates
   - Tax credits or deductions
   - Financing costs
   - Opportunity costs

4. **Special situations** require custom analysis:
   - Historic buildings
   - Mixed-use properties
   - Process-intensive facilities
   - Buildings with deferred maintenance

---

## Updating the Methodology

Review and update annually based on:
1. Actual project cost data
2. Construction cost indices
3. Technology cost trends
4. Labor market conditions
5. Building code changes

---

## References

- RSMeans Building Construction Cost Data
- ASHRAE Energy Efficiency Guide for Existing Commercial Buildings
- DOE Commercial Building Retrofit Cost Database
- Local contractor survey data (2024-2025)