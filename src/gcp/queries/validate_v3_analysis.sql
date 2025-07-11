-- Suggested File Name: validate_v3_analysis.sql
-- File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/queries/
-- Use: Run these queries in BigQuery Console to validate the v3 analysis fixes

-- ========================================
-- Query 1: Validate 42% Cap is Applied
-- ========================================
-- This should show NO buildings with >42% reduction required
SELECT 
    COUNT(*) as total_buildings,
    MAX(pct_reduction_2030) as max_reduction_pct,
    COUNT(CASE WHEN pct_reduction_2030 > 42 THEN 1 END) as over_42_pct_count,
    COUNT(CASE WHEN pct_reduction_2030 = 42 THEN 1 END) as exactly_42_pct_count,
    COUNT(CASE WHEN hit_42_pct_cap THEN 1 END) as hit_cap_flag_count
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`;

-- Expected results:
-- max_reduction_pct should be ≤ 42.0
-- over_42_pct_count should be 0
-- exactly_42_pct_count and hit_cap_flag_count should match

-- ========================================
-- Query 2: Check Buildings That Hit the Cap
-- ========================================
-- Shows specific buildings affected by the 42% cap
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
WHERE hit_42_pct_cap = TRUE
ORDER BY pct_reduction_requested DESC
LIMIT 20;

-- ========================================
-- Query 3: Verify Exemption Handling
-- ========================================
-- Check that we're using latest non-exempt data
WITH exemption_check AS (
    SELECT 
        v3.building_id,
        v3.building_name,
        v3.latest_reporting_year,
        v3.status as latest_status,
        -- Check if this building had exempt status in earlier years
        (SELECT COUNT(*) 
         FROM `energize-denver-eaas.energize_denver.building_consumption_corrected` c
         WHERE c.building_id = v3.building_id 
           AND LOWER(c.status) LIKE '%exempt%') as exempt_year_count,
        -- Get years when building was exempt
        (SELECT STRING_AGG(CAST(reporting_year AS STRING), ', ' ORDER BY reporting_year)
         FROM `energize-denver-eaas.energize_denver.building_consumption_corrected` c
         WHERE c.building_id = v3.building_id 
           AND LOWER(c.status) LIKE '%exempt%') as exempt_years
    FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3` v3
)
SELECT 
    COUNT(*) as total_buildings,
    COUNT(CASE WHEN exempt_year_count > 0 THEN 1 END) as buildings_with_exempt_history,
    COUNT(CASE WHEN LOWER(latest_status) LIKE '%exempt%' THEN 1 END) as currently_exempt
FROM exemption_check;

-- Also show some examples of buildings that were previously exempt
SELECT * FROM exemption_check 
WHERE exempt_year_count > 0 
LIMIT 10;

-- ========================================
-- Query 4: Compare V3 vs Original Analysis
-- ========================================
-- Shows the impact of our fixes
WITH comparison AS (
    SELECT 
        'Original' as version,
        COUNT(*) as building_count,
        COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in_count,
        ROUND(AVG(pct_reduction_2030), 1) as avg_reduction_pct,
        MAX(pct_reduction_2030) as max_reduction_pct
    FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis`
    
    UNION ALL
    
    SELECT 
        'V3 (Fixed)' as version,
        COUNT(*) as building_count,
        COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in_count,
        ROUND(AVG(pct_reduction_2030), 1) as avg_reduction_pct,
        MAX(pct_reduction_2030) as max_reduction_pct
    FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
)
SELECT * FROM comparison;

-- ========================================
-- Query 5: Validate Opt-In Recommendations
-- ========================================
-- Check that high-reduction buildings are recommended to opt-in
SELECT 
    CASE 
        WHEN pct_reduction_2030 >= 40 THEN '40-42% (At Cap)'
        WHEN pct_reduction_2030 >= 35 THEN '35-40%'
        WHEN pct_reduction_2030 >= 30 THEN '30-35%'
        WHEN pct_reduction_2030 >= 20 THEN '20-30%'
        WHEN pct_reduction_2030 >= 10 THEN '10-20%'
        ELSE '0-10%'
    END as reduction_range,
    COUNT(*) as building_count,
    COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in_count,
    ROUND(COUNT(CASE WHEN should_opt_in THEN 1 END) * 100.0 / COUNT(*), 1) as opt_in_rate_pct,
    ROUND(AVG(decision_confidence), 1) as avg_confidence
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
GROUP BY reduction_range
ORDER BY 
    CASE reduction_range
        WHEN '40-42% (At Cap)' THEN 1
        WHEN '35-40%' THEN 2
        WHEN '30-35%' THEN 3
        WHEN '20-30%' THEN 4
        WHEN '10-20%' THEN 5
        ELSE 6
    END;

-- ========================================
-- Query 6: Financial Impact Summary
-- ========================================
-- Verify the financial calculations make sense
SELECT 
    should_opt_in,
    COUNT(*) as building_count,
    ROUND(SUM(total_penalties_default) / 1000000, 1) as default_penalties_millions,
    ROUND(SUM(total_penalties_optin) / 1000000, 1) as optin_penalties_millions,
    ROUND(SUM(CASE WHEN should_opt_in 
              THEN total_penalties_default - total_penalties_optin 
              ELSE total_penalties_optin - total_penalties_default 
         END) / 1000000, 1) as savings_from_recommendation_millions,
    ROUND(AVG(npv_advantage_optin), 0) as avg_npv_advantage
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
GROUP BY should_opt_in;

-- ========================================
-- Query 7: Quick Data Quality Check
-- ========================================
SELECT 
    'Data Quality Metrics' as metric_type,
    COUNT(*) as total_records,
    COUNT(CASE WHEN current_eui IS NULL OR current_eui <= 0 THEN 1 END) as invalid_eui,
    COUNT(CASE WHEN gross_floor_area IS NULL OR gross_floor_area < 25000 THEN 1 END) as invalid_sqft,
    COUNT(CASE WHEN target_2030_final IS NULL THEN 1 END) as missing_targets,
    MIN(latest_reporting_year) as oldest_data_year,
    MAX(latest_reporting_year) as newest_data_year
FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`;