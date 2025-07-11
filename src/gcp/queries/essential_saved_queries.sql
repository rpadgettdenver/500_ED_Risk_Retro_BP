-- ========================================
-- ESSENTIAL BIGQUERY QUERIES FOR ENERGIZE DENVER
-- ========================================
-- Save these queries in BigQuery for regular use
-- Each query includes SQL basics to help you learn!

-- ========================================
-- Query 1: Simple Master Validation V3
-- ========================================
-- Query Name: "01 - Master Validation Check"
-- Use: Run this weekly/monthly to ensure data integrity

-- SQL Basics: This query uses UNION ALL to stack multiple results
-- Think of it like combining multiple Excel rows into one table

SELECT 
  'V3 VALIDATION RESULTS' as metric_category,
  'Value' as metric_value,
  'Status' as check_status
  
UNION ALL

SELECT 
  '1. Maximum reduction %',
  CAST(ROUND(MAX(pct_reduction_2030), 1) AS STRING),
  CASE WHEN MAX(pct_reduction_2030) <= 42 THEN '✓ PASS' ELSE '✗ FAIL' END
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`

UNION ALL

SELECT 
  '2. Buildings over 42%',
  CAST(COUNT(CASE WHEN pct_reduction_2030 > 42 THEN 1 END) AS STRING),
  CASE WHEN COUNT(CASE WHEN pct_reduction_2030 > 42 THEN 1 END) = 0 THEN '✓ PASS' ELSE '✗ FAIL' END
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`

UNION ALL

SELECT 
  '3. Buildings at 42% cap',
  CAST(COUNT(CASE WHEN hit_42_pct_cap THEN 1 END) AS STRING),
  'Should be > 0'
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`

UNION ALL

SELECT 
  '4. Total buildings',
  CAST(COUNT(*) AS STRING),
  'Info'
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`

UNION ALL

SELECT 
  '5. Opt-in recommendations',
  CONCAT(
    CAST(COUNT(CASE WHEN should_opt_in THEN 1 END) AS STRING), 
    ' (', 
    CAST(ROUND(COUNT(CASE WHEN should_opt_in THEN 1 END) * 100.0 / COUNT(*), 1) AS STRING), 
    '%)'
  ),
  'Info'
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`

UNION ALL

SELECT 
  '6. Total penalties ($M)',
  CAST(ROUND(SUM(total_penalties_default) / 1000000, 1) AS STRING),
  'Info'
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`

UNION ALL

SELECT 
  '7. Opt-in savings ($M)',
  CAST(ROUND(SUM(CASE WHEN should_opt_in 
    THEN total_penalties_default - total_penalties_optin 
    ELSE 0 END) / 1000000, 1) AS STRING),
  'Should be positive'
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`

UNION ALL

SELECT 
  '8. Latest data year',
  CAST(MAX(latest_reporting_year) AS STRING),
  'Should be 2023-2024'
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`

UNION ALL

SELECT 
  '9. Currently exempt',
  CAST(COUNT(CASE WHEN LOWER(status) LIKE '%exempt%' THEN 1 END) AS STRING),
  CASE 
    WHEN COUNT(CASE WHEN LOWER(status) LIKE '%exempt%' THEN 1 END) = 0 
    THEN '✓ Expected' 
    ELSE 'Check these' 
  END
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`

ORDER BY metric_category;

-- ========================================
-- Query 2: Buildings at 42% Cap
-- ========================================
-- Query Name: "02 - Buildings at 42% Cap Detail"
-- Use: See which buildings are affected by the cap

-- SQL Basics: 
-- SELECT = Choose which columns to show (like Excel columns)
-- FROM = Which table to use
-- WHERE = Filter rows (like Excel filter)
-- ORDER BY = Sort results

SELECT 
    building_id,
    building_name,
    property_type,
    ROUND(baseline_eui, 1) as baseline_eui,
    ROUND(current_eui, 1) as current_eui,
    ROUND(target_2030_raw, 1) as original_target,
    ROUND(target_2030_final, 1) as capped_target,
    ROUND(pct_reduction_requested, 1) as reduction_requested_pct,
    ROUND(pct_reduction_2030, 1) as reduction_required_pct,
    should_opt_in,
    primary_rationale
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
WHERE hit_42_pct_cap = TRUE  -- Only show buildings that hit the cap
ORDER BY pct_reduction_requested DESC  -- Biggest reductions first
LIMIT 100;  -- Show top 100

-- ========================================
-- Query 3: Opt-In Decision Summary
-- ========================================
-- Query Name: "03 - Opt-In Summary by Property Type"
-- Use: Understand decisions by building type

-- SQL Basics:
-- GROUP BY = Summarize data by categories (like Excel pivot table)
-- COUNT(*) = Count all rows
-- AVG() = Calculate average
-- ROUND() = Round decimals

SELECT 
    property_type,
    COUNT(*) as total_buildings,
    COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in_count,
    ROUND(COUNT(CASE WHEN should_opt_in THEN 1 END) * 100.0 / COUNT(*), 1) as opt_in_rate_pct,
    ROUND(AVG(pct_reduction_2030), 1) as avg_reduction_needed_pct,
    ROUND(SUM(total_penalties_default) / 1000000, 1) as total_penalties_millions,
    ROUND(SUM(CASE WHEN should_opt_in 
        THEN total_penalties_default - total_penalties_optin 
        ELSE 0 END) / 1000000, 1) as savings_millions
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
GROUP BY property_type
HAVING COUNT(*) >= 10  -- Only show property types with 10+ buildings
ORDER BY opt_in_rate_pct DESC;

-- ========================================
-- Query 4: Data Freshness Check
-- ========================================
-- Query Name: "04 - Data Freshness by Year"
-- Use: Verify we're using current data

-- SQL Basics: Simple grouping and counting

SELECT 
    latest_reporting_year,
    COUNT(*) as building_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percent_of_total
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
GROUP BY latest_reporting_year
ORDER BY latest_reporting_year DESC;

-- ========================================
-- Query 5: High Risk Buildings
-- ========================================
-- Query Name: "05 - Top 50 High Risk Buildings"
-- Use: Identify buildings needing immediate attention

-- SQL Basics:
-- WHERE filters before grouping
-- HAVING filters after grouping
-- || means concatenate (combine) text

SELECT 
    building_id,
    building_name,
    property_type,
    ROUND(gross_floor_area, 0) as sqft,
    ROUND(current_eui, 1) as current_eui,
    ROUND(pct_reduction_2030, 1) as reduction_needed_pct,
    CASE WHEN should_opt_in THEN 'Yes' ELSE 'No' END as recommend_opt_in,
    '$' || FORMAT("%'d", CAST(total_penalties_default AS INT64)) as total_penalties,
    '$' || FORMAT("%'d", CAST(npv_benefit_of_optin AS INT64)) as savings_if_opt_in,
    primary_rationale
FROM `energize-denver-eaas.energize_denver.opt_in_recommendations_v3`
WHERE total_penalties_default > 100000  -- Only high penalty buildings
ORDER BY total_penalties_default DESC
LIMIT 50;

-- ========================================
-- Query 6: Exemption History Check
-- ========================================
-- Query Name: "06 - Buildings with Exemption History"
-- Use: Track buildings that were previously exempt

-- SQL Basics: Subqueries (queries inside queries)

SELECT 
    v3.building_id,
    v3.building_name,
    v3.property_type,
    v3.latest_reporting_year as now_reporting_year,
    v3.status as current_status,
    -- This subquery counts exempt years for each building
    (SELECT COUNT(*) 
     FROM `energize-denver-eaas.energize_denver.building_consumption_corrected` c
     WHERE c.building_id = v3.building_id 
       AND LOWER(c.status) LIKE '%exempt%') as years_was_exempt,
    -- This subquery lists the exempt years
    (SELECT STRING_AGG(CAST(reporting_year AS STRING), ', ' ORDER BY reporting_year)
     FROM `energize-denver-eaas.energize_denver.building_consumption_corrected` c
     WHERE c.building_id = v3.building_id 
       AND LOWER(c.status) LIKE '%exempt%') as exempt_in_years
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3` v3
WHERE EXISTS (  -- Only show if building was EVER exempt
    SELECT 1 
    FROM `energize-denver-eaas.energize_denver.building_consumption_corrected` c
    WHERE c.building_id = v3.building_id 
      AND LOWER(c.status) LIKE '%exempt%'
)
ORDER BY years_was_exempt DESC;

-- ========================================
-- Query 7: Property Type Summary for Dashboards
-- ========================================
-- Query Name: "07 - Property Type Dashboard Metrics"
-- Use: Feed Looker Studio visualizations

SELECT 
    property_type,
    -- Building counts
    COUNT(*) as buildings,
    COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in,
    COUNT(CASE WHEN hit_42_pct_cap THEN 1 END) as at_cap,
    
    -- Percentages
    ROUND(COUNT(CASE WHEN should_opt_in THEN 1 END) * 100.0 / COUNT(*), 1) as opt_in_pct,
    ROUND(AVG(pct_reduction_2030), 1) as avg_reduction_pct,
    
    -- Financial metrics
    ROUND(SUM(total_penalties_default) / 1000000, 1) as penalties_millions,
    ROUND(SUM(estimated_retrofit_cost) / 1000000, 1) as retrofit_cost_millions,
    
    -- Square footage
    ROUND(SUM(gross_floor_area) / 1000000, 1) as total_sqft_millions
    
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
GROUP BY property_type
ORDER BY penalties_millions DESC;

-- ========================================
-- Query 8: Monthly Tracking Base
-- ========================================
-- Query Name: "08 - Monthly Analysis Tracking"
-- Use: Track changes over time as you re-run analysis

-- SQL Basics: This prepares for time-series analysis

SELECT 
    DATE(analysis_timestamp) as analysis_date,
    COUNT(*) as buildings_analyzed,
    COUNT(CASE WHEN recommended_opt_in THEN 1 END) as opt_in_recommendations,
    ROUND(SUM(penalties_if_default) / 1000000, 1) as total_penalties_millions,
    ROUND(SUM(npv_benefit_of_optin) / 1000000, 1) as total_savings_millions,
    COUNT(CASE WHEN hit_42_pct_cap THEN 1 END) as buildings_at_cap
FROM `energize-denver-eaas.energize_denver.opt_in_recommendations_v3`
GROUP BY analysis_date
ORDER BY analysis_date DESC;

-- ========================================
-- Query 9: Decision Confidence Distribution
-- ========================================
-- Query Name: "09 - Decision Confidence Analysis"
-- Use: Understand how confident the model is

SELECT 
    CASE 
        WHEN decision_confidence >= 90 THEN '90-100% (Very High)'
        WHEN decision_confidence >= 75 THEN '75-89% (High)'
        WHEN decision_confidence >= 50 THEN '50-74% (Medium)'
        ELSE 'Below 50% (Low)'
    END as confidence_level,
    should_opt_in,
    COUNT(*) as building_count,
    ROUND(AVG(npv_advantage_optin / 1000), 0) as avg_npv_advantage_thousands
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
GROUP BY confidence_level, should_opt_in
ORDER BY confidence_level DESC, should_opt_in;

-- ========================================
-- Query 10: Quick Metrics Export
-- ========================================
-- Query Name: "10 - Single Row Export for Spreadsheets"
-- Use: Copy/paste all key metrics to Excel

SELECT 
    -- Timestamp
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', CURRENT_TIMESTAMP(), 'America/Denver') as report_timestamp,
    
    -- Building counts
    COUNT(*) as total_buildings,
    COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in_recommendations,
    COUNT(CASE WHEN hit_42_pct_cap THEN 1 END) as buildings_at_cap,
    
    -- Percentages
    ROUND(MAX(pct_reduction_2030), 1) as max_reduction_pct,
    ROUND(COUNT(CASE WHEN should_opt_in THEN 1 END) * 100.0 / COUNT(*), 1) as opt_in_rate_pct,
    
    -- Financial (millions)
    ROUND(SUM(total_penalties_default) / 1000000, 1) as total_penalties_millions,
    ROUND(SUM(CASE WHEN should_opt_in 
              THEN total_penalties_default - total_penalties_optin 
              ELSE 0 END) / 1000000, 1) as opt_in_savings_millions,
    ROUND(SUM(estimated_retrofit_cost) / 1000000, 1) as total_retrofit_cost_millions,
    
    -- Data quality
    MAX(latest_reporting_year) as newest_data_year,
    COUNT(CASE WHEN LOWER(status) LIKE '%exempt%' THEN 1 END) as currently_exempt
    
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`;

-- ========================================
-- SQL BASICS CHEAT SHEET
-- ========================================
/*
Common SQL Commands You'll Use:

SELECT     - Choose columns to display
FROM       - Specify which table(s) to use
WHERE      - Filter rows before grouping
GROUP BY   - Summarize data by categories
HAVING     - Filter after grouping
ORDER BY   - Sort results
LIMIT      - Restrict number of rows

Common Functions:
COUNT(*)   - Count all rows
SUM()      - Add up values
AVG()      - Calculate average
MAX()      - Find maximum value
MIN()      - Find minimum value
ROUND()    - Round decimals

Operators:
=          - Equals
!=         - Not equals
>          - Greater than
>=         - Greater than or equal
LIKE       - Pattern matching (% = wildcard)
AND        - Both conditions must be true
OR         - Either condition can be true

Tips:
- End each query with semicolon ;
- Use -- for comments
- Test with LIMIT 10 first
- Save queries with descriptive names
*/