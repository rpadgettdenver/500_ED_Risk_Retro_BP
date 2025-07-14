# Energize Denver BigQuery/SQL Quick Reference
**Version:** 1.0 | **Date:** July 14, 2025

---

## 🎯 ACO Target Logic in SQL

### Correct Implementation - ACO 2028 Uses First Interim Target
```sql
-- CORRECT: ACO 2028 target equals First Interim Target
WITH targets AS (
  SELECT 
    building_id,
    first_interim_target,
    second_interim_target,
    final_target,
    baseline_eui,
    baseline_year
  FROM `project.dataset.building_eui_targets`
)
SELECT
  building_id,
  -- Standard Path Targets
  first_interim_target AS target_2025,
  second_interim_target AS target_2027,
  final_target AS target_2030,
  -- ACO Path Targets (2028 = First Interim, NOT interpolated!)
  first_interim_target AS target_2028_aco,  -- ✓ CORRECT
  final_target AS target_2032_aco
FROM targets;
```

### ❌ WRONG - Do Not Use Interpolation
```sql
-- WRONG: Do not interpolate 2028 target
-- This is the OLD incorrect method
SELECT
  building_id,
  -- INCORRECT interpolation calculation
  baseline_eui - (baseline_eui - final_target) * 
    (2028 - baseline_year) / (2032 - baseline_year) AS target_2028_aco  -- ✗ WRONG!
FROM targets;
```

---

## 💡 Opt-In Decision Logic in BigQuery

```sql
CREATE OR REPLACE VIEW `project.dataset.opt_in_recommendations` AS
WITH penalty_analysis AS (
  SELECT
    b.building_id,
    b.building_name,
    b.property_type,
    b.sqft,
    b.current_eui,
    t.first_interim_target,
    t.final_target,
    
    -- Calculate gaps
    GREATEST(0, b.current_eui - t.first_interim_target) AS gap_2025,
    GREATEST(0, b.current_eui - t.second_interim_target) AS gap_2027,
    GREATEST(0, b.current_eui - t.final_target) AS gap_2030,
    
    -- Standard Path Penalties (correct rate: $0.15)
    GREATEST(0, b.current_eui - t.first_interim_target) * b.sqft * 0.15 AS penalty_2025,
    GREATEST(0, b.current_eui - t.second_interim_target) * b.sqft * 0.15 AS penalty_2027,
    GREATEST(0, b.current_eui - t.final_target) * b.sqft * 0.15 AS penalty_2030,
    
    -- ACO Path Penalties (correct rate: $0.23)
    -- 2028 uses First Interim Target!
    GREATEST(0, b.current_eui - t.first_interim_target) * b.sqft * 0.23 AS penalty_2028_aco,
    GREATEST(0, b.current_eui - t.final_target) * b.sqft * 0.23 AS penalty_2032_aco,
    
    -- Reduction percentage
    (b.current_eui - t.final_target) / b.current_eui * 100 AS reduction_pct,
    
    -- Cash constrained flag
    CASE 
      WHEN b.property_type IN ('Affordable Housing', 'Senior Care Community') THEN TRUE
      WHEN GREATEST(0, b.current_eui - t.first_interim_target) * b.sqft * 0.15 > 500000 THEN TRUE
      ELSE FALSE
    END AS cash_constrained
    
  FROM `project.dataset.buildings` b
  JOIN `project.dataset.building_eui_targets` t
    ON b.building_id = t.building_id
),
npv_calculations AS (
  SELECT
    *,
    -- NPV @ 7% discount rate
    -- Standard Path NPV
    penalty_2025 +                           -- Year 0
    penalty_2027 / POWER(1.07, 2) +         -- Year 2  
    penalty_2030 / POWER(1.07, 5) +         -- Year 5
    (penalty_2030 * 12) / POWER(1.07, 6)    -- Annual 2031-2042 simplified
    AS standard_npv,
    
    -- ACO Path NPV  
    penalty_2028_aco / POWER(1.07, 3) +     -- Year 3
    penalty_2032_aco / POWER(1.07, 7) +     -- Year 7
    (penalty_2032_aco * 10) / POWER(1.07, 8) -- Annual 2033-2042 simplified
    AS aco_npv
    
  FROM penalty_analysis
)
SELECT
  *,
  standard_npv - aco_npv AS npv_advantage,
  
  -- Decision Logic
  CASE
    -- Cannot meet any targets
    WHEN gap_2025 > 0 AND gap_2027 > 0 AND gap_2030 > 0 THEN 'opt-in'
    
    -- Significant NPV advantage
    WHEN standard_npv - aco_npv > 50000 THEN 'opt-in'
    
    -- Cash constrained
    WHEN cash_constrained THEN 'opt-in'
    
    -- High reduction needed
    WHEN reduction_pct > 35 THEN 'opt-in'
    
    -- Moderate NPV advantage
    WHEN standard_npv - aco_npv > 10000 THEN 'opt-in'
    
    -- Default
    ELSE 'standard'
  END AS recommendation,
  
  -- Confidence Score
  CASE
    WHEN gap_2025 > 0 AND gap_2027 > 0 AND gap_2030 > 0 THEN 100
    WHEN standard_npv - aco_npv > 50000 THEN 95
    WHEN cash_constrained AND gap_2025 > 0 THEN 85
    WHEN reduction_pct > 35 THEN 80
    WHEN standard_npv - aco_npv > 10000 THEN 70
    ELSE 60
  END AS confidence

FROM npv_calculations;
```

---

## 💰 Retrofit Cost Estimation in SQL

```sql
CREATE OR REPLACE FUNCTION `project.dataset.estimate_retrofit_cost`(
  sqft FLOAT64,
  reduction_pct FLOAT64,
  property_type STRING,
  building_age INT64
) AS (
  -- Base cost per tier
  CASE
    WHEN reduction_pct <= 10 THEN sqft * 5    -- Minor
    WHEN reduction_pct <= 25 THEN sqft * 15   -- Moderate  
    WHEN reduction_pct <= 40 THEN sqft * 30   -- Major
    ELSE sqft * 50                             -- Deep
  END *
  -- Property type adjustment
  CASE property_type
    WHEN 'Multifamily Housing' THEN 0.9
    WHEN 'Office' THEN 1.0
    WHEN 'Healthcare' THEN 1.5
    WHEN 'Manufacturing/Industrial Plant' THEN 1.3
    ELSE 1.0
  END *
  -- Age adjustment
  CASE
    WHEN building_age < 10 THEN 0.8
    WHEN building_age < 30 THEN 1.0
    WHEN building_age < 50 THEN 1.2
    ELSE 1.4
  END
);
```

---

## 📊 MAI Building Logic in BigQuery

```sql
-- Apply MAI rules (52.9 floor, 30% reduction cap)
CREATE OR REPLACE VIEW `project.dataset.targets_with_mai_logic` AS
WITH mai_buildings AS (
  SELECT DISTINCT building_id
  FROM `project.dataset.mai_target_summary`
)
SELECT
  t.*,
  CASE
    WHEN m.building_id IS NOT NULL THEN
      -- MAI building: use most lenient of options
      GREATEST(
        t.final_target,                    -- Original target
        t.baseline_eui * 0.70,            -- 30% reduction
        52.9                              -- MAI floor
      )
    ELSE
      -- Non-MAI: apply 42% cap
      GREATEST(
        t.final_target,
        t.baseline_eui * 0.58             -- 42% reduction cap
      )
  END AS final_target_adjusted
  
FROM `project.dataset.building_eui_targets` t
LEFT JOIN mai_buildings m ON t.building_id = m.building_id;
```

---

## 🚨 Common BigQuery Mistakes

### ❌ Wrong Penalty Rates
```sql
-- WRONG rates from old scripts
0.30  -- ✗ Should be 0.15 for standard
0.70  -- ✗ Should be 0.23 for ACO
```

### ✅ Correct Penalty Rates
```sql
-- CORRECT rates
0.15  -- ✓ Standard path
0.23  -- ✓ ACO path
0.35  -- ✓ Extension
10.00 -- ✓ Never benchmarked (per sqft)
```

### ❌ Missing Annual Penalties
```sql
-- WRONG: Only calculating target year penalties
SELECT 
  penalty_2030,
  penalty_2030 AS total_penalty  -- Missing annual penalties!
```

### ✅ Including Annual Penalties
```sql
-- CORRECT: Include penalties through 2042
SELECT
  penalty_2030,
  penalty_2030 * 13 AS total_penalties_2030_2042  -- 2030-2042
```

---

## 📋 BigQuery Validation Queries

### Verify 2028 Targets Are Correct
```sql
-- Check that ACO 2028 = First Interim Target
SELECT
  building_id,
  first_interim_target,
  first_interim_target AS aco_2028_target,  -- Should be identical
  ROUND(ABS(first_interim_target - first_interim_target), 2) AS difference  -- Should be 0
FROM `project.dataset.building_eui_targets`
WHERE building_id IN ('2952', '1122', '3456');  -- Test buildings
```

### Audit Penalty Calculations
```sql
-- Verify penalty rates are correct
SELECT
  'Standard' AS path,
  0.15 AS expected_rate,
  COUNT(*) AS building_count
FROM `project.dataset.penalty_calculations`
WHERE compliance_path = 'standard' 
  AND ABS(penalty_rate - 0.15) > 0.001  -- Should return 0 rows

UNION ALL

SELECT
  'ACO' AS path,
  0.23 AS expected_rate,
  COUNT(*) AS building_count
FROM `project.dataset.penalty_calculations`
WHERE compliance_path = 'aco'
  AND ABS(penalty_rate - 0.23) > 0.001;  -- Should return 0 rows
```

### Find Buildings That Should Opt-In
```sql
-- High-confidence opt-in candidates
SELECT
  building_id,
  building_name,
  property_type,
  npv_advantage,
  reduction_pct,
  recommendation,
  confidence
FROM `project.dataset.opt_in_recommendations`
WHERE recommendation = 'opt-in'
  AND confidence >= 80
ORDER BY npv_advantage DESC
LIMIT 100;
```

---

## 🔧 Useful BigQuery Functions

### Calculate Building Age
```sql
CREATE OR REPLACE FUNCTION `project.dataset.get_building_age`(year_built INT64) AS (
  EXTRACT(YEAR FROM CURRENT_DATE()) - COALESCE(year_built, 1990)
);
```

### Format Currency
```sql
CREATE OR REPLACE FUNCTION `project.dataset.format_currency`(amount FLOAT64) AS (
  CONCAT('$', FORMAT("%'.0f", ROUND(amount, 0)))
);
```

### Calculate NPV
```sql
CREATE OR REPLACE FUNCTION `project.dataset.calculate_npv`(
  amount FLOAT64,
  years_from_now INT64,
  discount_rate FLOAT64
) AS (
  amount / POWER(1 + discount_rate, years_from_now)
);
```

---

## 📁 Key BigQuery Scripts to Update

1. **create_opt_in_decision_model.py** - Fix 2028 interpolation
2. **create_building_penalty_forecast.py** - Update penalty rates
3. **run_penalty_calculations.py** - Include annual penalties
4. **create_portfolio_risk_view.py** - Use correct NPV calculations

---

## 📊 BigQuery Best Practices

1. **Always use CTEs** for complex queries
2. **Parameterize penalty rates** - Don't hardcode
3. **Include data validation** queries
4. **Document assumptions** in view comments
5. **Version control** all DDL statements

---

*Remember: ACO 2028 = First Interim Target, NOT interpolated!*