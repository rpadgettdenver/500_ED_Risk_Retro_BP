"""
Suggested File Name: fix_42_cap_and_yearwise_exemptions.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Fix buildings showing 100% reduction by applying 42% cap and handle year-specific exemptions

This script:
1. Applies the 42% maximum reduction cap properly
2. Only excludes building data for the specific year it was marked exempt
3. Handles edge cases where targets might be unrealistic
4. Maintains historical exemption records for transparency
"""

from google.cloud import bigquery
import pandas as pd

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

class FixCapAndExemptions:
    """Fix extreme reduction requirements and handle year-specific exemptions"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        
    def create_fixed_analysis_view(self):
        """Create a corrected version that handles exemptions by year and applies 42% cap"""
        
        view_id = f"{self.dataset_ref}.opt_in_decision_analysis_v3"
        
        print("=== CREATING FIXED OPT-IN DECISION ANALYSIS V3 ===\n")
        print("Changes in this version:")
        print("1. Only exclude building-years marked as 'Exempt', not entire buildings")
        print("2. Properly apply 42% maximum reduction cap")
        print("3. Handle MAI floor of 52.9 kBtu/sqft")
        print("4. Keep historical context of exemptions\n")
        
        query = f"""
        CREATE OR REPLACE VIEW `{view_id}` AS
        WITH 
        -- Get the latest non-exempt year data for each building
        latest_valid_consumption AS (
            SELECT 
                c.*,
                -- Flag if this specific year was exempt
                CASE 
                    WHEN LOWER(c.status) LIKE '%exempt%' THEN TRUE
                    ELSE FALSE
                END as was_exempt_this_year
            FROM `{self.dataset_ref}.building_consumption_corrected` c
            WHERE c.weather_normalized_eui > 0
                AND c.gross_floor_area >= 25000
                -- Include all data, but flag exempt years
                AND c.reporting_year = (
                    -- Get the latest year where building wasn't exempt
                    SELECT MAX(reporting_year) 
                    FROM `{self.dataset_ref}.building_consumption_corrected` c2 
                    WHERE c2.building_id = c.building_id
                        AND (LOWER(c2.status) NOT LIKE '%exempt%' OR c2.status IS NULL)
                        AND c2.weather_normalized_eui > 0
                )
        ),
        
        building_metrics AS (
            -- Join with targets for buildings that have valid (non-exempt) recent data
            SELECT 
                c.building_id,
                c.building_name,
                c.property_type,
                c.gross_floor_area,
                c.year_built,
                c.weather_normalized_eui as current_eui,
                c.reporting_year as latest_reporting_year,
                c.status,
                c.was_exempt_this_year,
                t.baseline_eui,
                t.first_interim_target as target_2025_raw,
                t.second_interim_target as target_2027_raw,
                COALESCE(t.adjusted_final_target, t.original_final_target) as target_2030_raw,
                
                -- Apply 42% maximum reduction cap to ALL targets
                -- Target cannot be less than 58% of baseline (42% reduction)
                GREATEST(
                    t.first_interim_target,
                    t.baseline_eui * 0.58
                ) as target_2025_capped,
                
                GREATEST(
                    t.second_interim_target,
                    t.baseline_eui * 0.58
                ) as target_2027_capped,
                
                GREATEST(
                    COALESCE(t.adjusted_final_target, t.original_final_target),
                    t.baseline_eui * 0.58
                ) as target_2030_capped,
                
                -- MAI flag
                c.is_mai,
                
                -- Building age
                2024 - c.year_built as building_age
                
            FROM latest_valid_consumption c
            JOIN `{self.dataset_ref}.building_analysis_v2` t
                ON c.building_id = t.building_id
        ),
        
        targets_with_all_caps AS (
            SELECT 
                *,
                -- Apply MAI floor AFTER 42% cap
                CASE 
                    WHEN property_type = 'Manufacturing/Industrial Plant' AND is_mai = 1
                    THEN GREATEST(target_2025_capped, 52.9)
                    ELSE target_2025_capped
                END as target_2025_final,
                
                CASE 
                    WHEN property_type = 'Manufacturing/Industrial Plant' AND is_mai = 1
                    THEN GREATEST(target_2027_capped, 52.9)
                    ELSE target_2027_capped
                END as target_2027_final,
                
                CASE 
                    WHEN property_type = 'Manufacturing/Industrial Plant' AND is_mai = 1
                    THEN GREATEST(target_2030_capped, 52.9)
                    ELSE target_2030_capped
                END as target_2030_final,
                
                -- Track if caps were applied
                CASE 
                    WHEN target_2030_raw < baseline_eui * 0.58 THEN TRUE
                    ELSE FALSE
                END as hit_42_pct_cap,
                
                CASE 
                    WHEN property_type = 'Manufacturing/Industrial Plant' 
                        AND is_mai = 1 
                        AND target_2030_capped < 52.9 
                    THEN TRUE
                    ELSE FALSE
                END as hit_mai_floor
                
            FROM building_metrics
        ),
        
        gap_calculations AS (
            SELECT 
                *,
                -- Calculate gaps with fully capped targets
                current_eui - target_2025_final as gap_2025,
                current_eui - target_2027_final as gap_2027,
                current_eui - target_2030_final as gap_2030,
                
                -- Calculate percent reductions (capped at realistic values)
                LEAST(
                    100,  -- Cap at 100%
                    GREATEST(
                        0,  -- Floor at 0%
                        (current_eui - target_2030_final) / NULLIF(current_eui, 0) * 100
                    )
                ) as pct_reduction_2030,
                
                -- Also calculate what reduction was originally requested
                CASE 
                    WHEN baseline_eui > 0 
                    THEN (baseline_eui - target_2030_raw) / baseline_eui * 100
                    ELSE 0
                END as pct_reduction_requested
                
            FROM targets_with_all_caps
        ),
        
        financial_analysis AS (
            SELECT 
                *,
                
                -- Calculate penalties for each path
                -- Default path: penalties in 2025, 2027, 2030
                GREATEST(0, gap_2025 * gross_floor_area * 0.15) as penalty_2025,
                GREATEST(0, gap_2027 * gross_floor_area * 0.15) as penalty_2027,
                GREATEST(0, gap_2030 * gross_floor_area * 0.15) as penalty_2030_default,
                
                -- Opt-in path: penalties in 2028, 2032
                GREATEST(0, gap_2030 * gross_floor_area * 0.23) as penalty_2028_optin,
                GREATEST(0, gap_2030 * gross_floor_area * 0.23) as penalty_2032_optin,
                
                -- Estimate retrofit cost (with realistic caps)
                CASE 
                    WHEN pct_reduction_2030 < 15 THEN gross_floor_area * 5.0
                    WHEN pct_reduction_2030 < 30 THEN gross_floor_area * 12.0
                    WHEN pct_reduction_2030 < 42 THEN gross_floor_area * 25.0
                    ELSE gross_floor_area * 35.0  -- At or near cap
                END as estimated_retrofit_cost
                
            FROM gap_calculations
        ),
        
        npv_analysis AS (
            SELECT 
                *,
                
                -- NPV of penalties for default path
                penalty_2025 / POWER(1.07, 1) +
                penalty_2027 / POWER(1.07, 3) +
                penalty_2030_default / POWER(1.07, 6) as npv_penalties_default,
                
                -- NPV of penalties for opt-in path
                penalty_2028_optin / POWER(1.07, 4) +
                penalty_2032_optin / POWER(1.07, 8) as npv_penalties_optin,
                
                -- Total nominal penalties
                penalty_2025 + penalty_2027 + penalty_2030_default as total_penalties_default,
                penalty_2028_optin + penalty_2032_optin as total_penalties_optin
                
            FROM financial_analysis
        ),
        
        decision_factors AS (
            SELECT 
                *,
                
                -- Financial advantage of opt-in
                npv_penalties_default - npv_penalties_optin as npv_advantage_optin,
                
                -- Technical difficulty score (updated for 42% cap reality)
                CASE 
                    WHEN pct_reduction_2030 >= 40 THEN 100  -- At or near cap
                    WHEN pct_reduction_2030 > 35 THEN 90    -- Approaching cap
                    WHEN pct_reduction_2030 > 30 THEN 70    -- Very difficult
                    WHEN pct_reduction_2030 > 20 THEN 50    -- Difficult
                    WHEN pct_reduction_2030 > 10 THEN 30    -- Moderate
                    ELSE 10                                  -- Achievable
                END as technical_difficulty_score,
                
                -- Cash flow consideration
                CASE 
                    WHEN property_type IN ('Affordable Housing', 'Senior Care Community') THEN TRUE
                    WHEN penalty_2025 > 500000 THEN TRUE
                    ELSE FALSE
                END as cash_flow_constrained
                
            FROM npv_analysis
        )
        
        -- Final decision logic
        SELECT 
            *,
            
            -- Opt-in decision
            CASE 
                -- Always opt-in cases
                WHEN pct_reduction_2030 >= 40 THEN TRUE  -- Near or at cap
                WHEN gap_2025 > 0 AND gap_2027 > 0 AND gap_2030 > 0 THEN TRUE
                WHEN cash_flow_constrained AND penalty_2025 > 100000 THEN TRUE
                WHEN technical_difficulty_score >= 90 THEN TRUE
                WHEN hit_42_pct_cap THEN TRUE  -- Building hit the cap
                
                -- Never opt-in cases  
                WHEN gap_2025 <= 0 THEN FALSE
                WHEN npv_advantage_optin < -100000 THEN FALSE
                WHEN pct_reduction_2030 < 10 THEN FALSE
                
                -- Financial decision for others
                WHEN npv_advantage_optin > 0 THEN TRUE
                ELSE FALSE
                
            END as should_opt_in,
            
            -- Confidence score
            CASE
                WHEN hit_42_pct_cap THEN 100  -- Definitely opt-in if at cap
                WHEN gap_2025 <= 0 AND pct_reduction_2030 < 10 THEN 100
                WHEN ABS(npv_advantage_optin) < 50000 THEN 50
                ELSE 75
            END as decision_confidence,
            
            -- Decision rationale
            CASE 
                WHEN hit_42_pct_cap THEN 'Hit 42% reduction cap'
                WHEN pct_reduction_2030 >= 40 THEN 'Near maximum reduction cap'
                WHEN gap_2025 > 0 AND gap_2027 > 0 AND gap_2030 > 0 THEN 'Cannot meet any targets'
                WHEN cash_flow_constrained AND penalty_2025 > 100000 THEN 'Cash flow constraints'
                WHEN technical_difficulty_score >= 90 THEN 'Technical near-impossibility'
                WHEN gap_2025 <= 0 THEN 'Already meets 2025 target'
                WHEN npv_advantage_optin > 100000 THEN 'Significant financial advantage'
                WHEN npv_advantage_optin > 0 THEN 'Modest financial advantage'
                WHEN npv_advantage_optin < -100000 THEN 'Opt-in too expensive'
                ELSE 'Marginal decision'
            END as primary_rationale,
            
            -- Additional context fields
            CONCAT('Latest data from ', latest_reporting_year) as data_recency,
            CASE 
                WHEN was_exempt_this_year THEN 'Was exempt in reporting year'
                ELSE 'Active in reporting year'
            END as reporting_year_status
            
        FROM decision_factors
        """
        
        try:
            self.client.query(query).result()
            print(f"✓ Created fixed opt-in decision analysis view: {view_id}")
            return view_id
            
        except Exception as e:
            print(f"❌ Error creating view: {str(e)}")
            return None
    
    def analyze_fixes(self):
        """Analyze the impact of fixes"""
        
        print("\n=== ANALYZING IMPACT OF FIXES ===\n")
        
        # Check buildings at the cap
        cap_query = f"""
        SELECT 
            COUNT(*) as total_buildings,
            COUNT(CASE WHEN hit_42_pct_cap THEN 1 END) as at_42_pct_cap,
            COUNT(CASE WHEN hit_mai_floor THEN 1 END) as at_mai_floor,
            COUNT(CASE WHEN pct_reduction_requested > 42 THEN 1 END) as originally_over_42_pct,
            ROUND(AVG(pct_reduction_2030), 1) as avg_actual_reduction_pct,
            ROUND(AVG(pct_reduction_requested), 1) as avg_requested_reduction_pct
        FROM `{self.dataset_ref}.opt_in_decision_analysis_v3`
        """
        
        cap_results = self.client.query(cap_query).to_dataframe()
        
        print("Impact of 42% Cap:")
        print(f"  Total buildings analyzed: {cap_results['total_buildings'].iloc[0]:,}")
        print(f"  Buildings that hit 42% cap: {cap_results['at_42_pct_cap'].iloc[0]:,}")
        print(f"  Buildings that hit MAI floor: {cap_results['at_mai_floor'].iloc[0]:,}")
        print(f"  Originally requested >42% reduction: {cap_results['originally_over_42_pct'].iloc[0]:,}")
        print(f"  Average actual reduction required: {cap_results['avg_actual_reduction_pct'].iloc[0]:.1f}%")
        print(f"  Average originally requested: {cap_results['avg_requested_reduction_pct'].iloc[0]:.1f}%")
        
        # Check year-based exemption handling
        exempt_query = f"""
        SELECT 
            latest_reporting_year,
            COUNT(*) as building_count,
            COUNT(CASE WHEN was_exempt_this_year THEN 1 END) as was_exempt_count,
            COUNT(CASE WHEN status LIKE '%Exempt%' THEN 1 END) as exempt_in_latest_year
        FROM `{self.dataset_ref}.opt_in_decision_analysis_v3`
        GROUP BY latest_reporting_year
        ORDER BY latest_reporting_year DESC
        LIMIT 10
        """
        
        exempt_results = self.client.query(exempt_query).to_dataframe()
        
        print("\n\nYear-Based Exemption Analysis:")
        print("Latest reporting years and exemption status:")
        for _, row in exempt_results.iterrows():
            print(f"  Year {row['latest_reporting_year']}: {row['building_count']} buildings"
                  f" ({row['exempt_in_latest_year']} marked exempt)")
        
        # Distribution after fixes
        dist_query = f"""
        SELECT 
            CASE 
                WHEN pct_reduction_2030 >= 42 THEN '42% (Cap)'
                WHEN pct_reduction_2030 >= 35 THEN '35-42%'
                WHEN pct_reduction_2030 >= 25 THEN '25-35%'
                WHEN pct_reduction_2030 >= 15 THEN '15-25%'
                WHEN pct_reduction_2030 >= 5 THEN '5-15%'
                ELSE '0-5%'
            END as reduction_range,
            COUNT(*) as building_count,
            COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in_count,
            ROUND(AVG(total_penalties_default), 0) as avg_default_penalty
        FROM `{self.dataset_ref}.opt_in_decision_analysis_v3`
        GROUP BY reduction_range
        ORDER BY 
            CASE reduction_range
                WHEN '42% (Cap)' THEN 1
                WHEN '35-42%' THEN 2
                WHEN '25-35%' THEN 3
                WHEN '15-25%' THEN 4
                WHEN '5-15%' THEN 5
                ELSE 6
            END
        """
        
        dist_results = self.client.query(dist_query).to_dataframe()
        
        print("\n\nReduction Requirement Distribution (After Fixes):")
        print("-" * 70)
        print(f"{'Range':<15} | {'Buildings':<10} | {'Opt-In':<8} | {'Avg Penalty':<15}")
        print("-" * 70)
        for _, row in dist_results.iterrows():
            print(f"{row['reduction_range']:<15} | {row['building_count']:<10} | "
                  f"{row['opt_in_count']:<8} | ${row['avg_default_penalty']:>14,.0f}")
    
    def create_diagnostic_query(self):
        """Create a query to check specific buildings that might have issues"""
        
        diagnostic_query = f"""
        -- Check buildings with extreme reductions before and after fix
        WITH comparison AS (
            SELECT 
                v3.building_id,
                v3.building_name,
                v3.property_type,
                v3.baseline_eui,
                v3.current_eui,
                v3.target_2030_raw as original_target,
                v3.target_2030_final as fixed_target,
                v3.pct_reduction_requested as original_reduction_pct,
                v3.pct_reduction_2030 as fixed_reduction_pct,
                v3.hit_42_pct_cap,
                v3.hit_mai_floor,
                v3.should_opt_in,
                v3.latest_reporting_year,
                v3.status
            FROM `{self.dataset_ref}.opt_in_decision_analysis_v3` v3
            WHERE v3.pct_reduction_requested > 50  -- Originally requested >50% reduction
               OR v3.hit_42_pct_cap = TRUE
               OR v3.status LIKE '%Exempt%'
            ORDER BY v3.pct_reduction_requested DESC
            LIMIT 20
        )
        SELECT * FROM comparison;
        
        -- This query will show you:
        -- 1. Buildings that originally had >50% reduction requirements
        -- 2. How the 42% cap affected them
        -- 3. Any buildings with exempt status in their latest data
        """
        
        print("\n\nDiagnostic Query to Check Specific Buildings:")
        print(diagnostic_query)
        
        return diagnostic_query
    
    def create_updated_recommendations_table(self):
        """Create updated recommendations table with fixes"""
        
        table_id = f"{self.dataset_ref}.opt_in_recommendations_v3"
        
        query = f"""
        CREATE OR REPLACE TABLE `{table_id}` AS
        SELECT 
            building_id,
            building_name,
            property_type,
            ROUND(gross_floor_area, 0) as sqft,
            ROUND(current_eui, 1) as current_eui,
            ROUND(baseline_eui, 1) as baseline_eui,
            ROUND(target_2030_final, 1) as final_target,
            ROUND(pct_reduction_2030, 1) as reduction_needed_pct,
            hit_42_pct_cap,
            hit_mai_floor,
            should_opt_in as recommended_opt_in,
            decision_confidence,
            primary_rationale,
            
            -- Financial summary
            ROUND(total_penalties_default, 0) as penalties_if_default,
            ROUND(total_penalties_optin, 0) as penalties_if_optin,
            ROUND(npv_advantage_optin, 0) as npv_benefit_of_optin,
            ROUND(estimated_retrofit_cost, 0) as estimated_retrofit_cost,
            
            -- Key dates
            CASE WHEN should_opt_in THEN 2028 ELSE 2025 END as first_penalty_year,
            CASE WHEN should_opt_in THEN 2032 ELSE 2030 END as final_target_year,
            
            -- Risk flags
            CASE WHEN gap_2025 > 0 THEN TRUE ELSE FALSE END as misses_2025_target,
            cash_flow_constrained,
            technical_difficulty_score,
            
            -- Data context
            latest_reporting_year,
            reporting_year_status,
            
            CURRENT_TIMESTAMP() as analysis_timestamp
            
        FROM `{self.dataset_ref}.opt_in_decision_analysis_v3`
        ORDER BY 
            hit_42_pct_cap DESC,
            ABS(npv_advantage_optin) DESC
        """
        
        self.client.query(query).result()
        print(f"\n✓ Created updated recommendations table: {table_id}")


def main():
    """Main execution"""
    
    fixer = FixCapAndExemptions()
    
    print("FIXING 42% CAP AND YEAR-SPECIFIC EXEMPTIONS")
    print("=" * 80)
    print("\nThis script addresses:")
    print("1. Buildings showing 100% reduction (applies 42% cap)")
    print("2. Year-specific exempt status (only excludes data for exempt years)")
    print("3. Technical difficulty scoring aligned with 42% cap")
    print("4. Maintains historical context\n")
    
    # Create fixed views
    view_id = fixer.create_fixed_analysis_view()
    
    if view_id:
        # Analyze the fixes
        fixer.analyze_fixes()
        
        # Create diagnostic query
        fixer.create_diagnostic_query()
        
        # Create updated recommendations
        fixer.create_updated_recommendations_table()
        
        print("\n\n🎉 SUCCESS!")
        print("Fixed analysis created with:")
        print("- 42% maximum reduction cap properly applied")
        print("- Year-specific exemptions handled correctly")
        print("- Technical difficulty scores updated")
        print("- Historical context preserved")
        print("\nUse opt_in_recommendations_v3 table for analysis!")
        print("\nNote: Buildings marked 'Exempt' in recent years are excluded,")
        print("but we use their last valid (non-exempt) year data.")


if __name__ == "__main__":
    main()
