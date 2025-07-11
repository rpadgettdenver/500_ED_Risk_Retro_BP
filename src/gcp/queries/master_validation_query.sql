-- ========================================
-- MASTER VALIDATION QUERY FOR V3 ANALYSIS
-- ========================================
-- Suggested Query Name: Master Validation - V3 Analysis Checks
-- Use: Run this single query to validate all key aspects of the V3 fixes

WITH validation_metrics AS (
  SELECT 
    -- Overall counts
    COUNT(*) as total_buildings,
    
    -- 42% Cap Validation
    MAX(pct_reduction_2030) as max_reduction_pct,
    COUNT(CASE WHEN pct_reduction_2030 > 42 THEN 1 END) as buildings_over_42_pct,
    COUNT(CASE WHEN hit_42_pct_cap THEN 1 END) as buildings_at_cap,
    
    -- Opt-in recommendations
    COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in_count,
    ROUND(COUNT(CASE WHEN should_opt_in THEN 1 END) * 100.0 / COUNT(*), 1) as opt_in_rate_pct,
    
    -- Financial impact
    ROUND(SUM(total_penalties_default) / 1000000, 1) as total_penalties_millions,
    ROUND(SUM(CASE WHEN should_opt_in 
              THEN total_penalties_default - total_penalties_optin 
              ELSE 0 END) / 1000000, 1) as savings_from_optin_millions,
    
    -- Data freshness
    MIN(latest_reporting_year) as oldest_data_year,
    MAX(latest_reporting_year) as newest_data_year,
    
    -- Exemption check
    COUNT(CASE WHEN LOWER(status) LIKE '%exempt%' THEN 1 END) as currently_exempt_count
    
  FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
),
reduction_distribution AS (
  SELECT 
    CASE 
      WHEN pct_reduction_2030 >= 40 THEN '1. At Cap (40-42%)'
      WHEN pct_reduction_2030 >= 30 THEN '2. Very High (30-40%)'
      WHEN pct_reduction_2030 >= 20 THEN '3. High (20-30%)'
      WHEN pct_reduction_2030 >= 10 THEN '4. Moderate (10-20%)'
      ELSE '5. Low (0-10%)'
    END as reduction_range,
    COUNT(*) as buildings,
    COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in
  FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
  GROUP BY reduction_range
)

-- MAIN RESULTS
SELECT 
  '=== VALIDATION SUMMARY ===' as report_section,
  CURRENT_TIMESTAMP() as run_time
UNION ALL
SELECT '1. 42% CAP CHECK', null
UNION ALL
SELECT 
  CONCAT('   Max reduction required: ', CAST(max_reduction_pct AS STRING), '%'),
  CASE WHEN max_reduction_pct <= 42 THEN '✓ PASS' ELSE '✗ FAIL' END
FROM validation_metrics
UNION ALL
SELECT 
  CONCAT('   Buildings over 42%: ', CAST(buildings_over_42_pct AS STRING)),
  CASE WHEN buildings_over_42_pct = 0 THEN '✓ PASS' ELSE '✗ FAIL' END
FROM validation_metrics
UNION ALL
SELECT 
  CONCAT('   Buildings at cap: ', CAST(buildings_at_cap AS STRING)),
  '(Should be > 0)'
FROM validation_metrics

UNION ALL SELECT '', ''
UNION ALL SELECT '2. OPT-IN RECOMMENDATIONS', null
UNION ALL
SELECT 
  CONCAT('   Total buildings: ', CAST(total_buildings AS STRING)),
  ''
FROM validation_metrics
UNION ALL
SELECT 
  CONCAT('   Recommended opt-in: ', CAST(opt_in_count AS STRING), ' (', CAST(opt_in_rate_pct AS STRING), '%)'),
  ''
FROM validation_metrics

UNION ALL SELECT '', ''
UNION ALL SELECT '3. FINANCIAL IMPACT', null
UNION ALL
SELECT 
  CONCAT('   Total penalties: $', CAST(total_penalties_millions AS STRING), 'M'),
  ''
FROM validation_metrics
UNION ALL
SELECT 
  CONCAT('   Savings from opt-in: $', CAST(savings_from_optin_millions AS STRING), 'M'),
  ''
FROM validation_metrics

UNION ALL SELECT '', ''
UNION ALL SELECT '4. DATA FRESHNESS', null
UNION ALL
SELECT 
  CONCAT('   Data years: ', CAST(oldest_data_year AS STRING), ' - ', CAST(newest_data_year AS STRING)),
  ''
FROM validation_metrics
UNION ALL
SELECT 
  CONCAT('   Currently exempt: ', CAST(currently_exempt_count AS STRING)),
  CASE WHEN currently_exempt_count = 0 THEN '✓ Expected' ELSE 'Check these' END
FROM validation_metrics

UNION ALL SELECT '', ''
UNION ALL SELECT '5. REDUCTION DISTRIBUTION', null
UNION ALL
SELECT 
  CONCAT('   ', reduction_range, ': ', CAST(buildings AS STRING), ' buildings (', CAST(opt_in AS STRING), ' opt-in)'),
  ''
FROM reduction_distribution
ORDER BY report_section;