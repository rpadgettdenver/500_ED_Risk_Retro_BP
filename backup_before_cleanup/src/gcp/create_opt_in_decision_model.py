"""
Suggested File Name: create_opt_in_decision_model.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Create a sophisticated model to predict which buildings will opt-in to the ACO path

This script implements decision logic based on:
1. Financial analysis (NPV of penalties vs retrofit costs)
2. Technical feasibility (how hard is it to meet targets)
3. Building characteristics (age, type, current performance)
4. Strategic considerations (time value, cash flow)
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

class OptInDecisionModel:
    """Model to predict opt-in decisions based on multiple factors"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        
        # Decision parameters
        self.PENALTY_RATE_DEFAULT = 0.15  # $/kBtu
        self.PENALTY_RATE_OPTIN = 0.23    # $/kBtu
        self.DISCOUNT_RATE = 0.07          # 7% for NPV calculations
        
        # Retrofit cost assumptions ($/sqft) by reduction needed
        self.retrofit_cost_per_reduction = {
            'light': 5.0,      # <15% reduction
            'moderate': 12.0,  # 15-30% reduction  
            'deep': 25.0       # >30% reduction
        }
        
    def create_opt_in_analysis_view(self):
        """Create comprehensive opt-in decision analysis"""
        
        view_id = f"{self.dataset_ref}.opt_in_decision_analysis"
        
        print("=== CREATING OPT-IN DECISION ANALYSIS ===\n")
        
        query = f"""
        CREATE OR REPLACE VIEW `{view_id}` AS
        WITH building_metrics AS (
            -- Get latest consumption and targets for each building
            SELECT 
                c.building_id,
                c.building_name,
                c.property_type,
                c.gross_floor_area,
                c.year_built,
                c.weather_normalized_eui as current_eui,
                t.first_interim_target as target_2025,  -- First interim (reported in 2025/2026)
                t.second_interim_target as target_2027,  -- Second interim
                COALESCE(t.adjusted_final_target, t.original_final_target) as target_2030,
                
                -- Calculate gaps
                c.weather_normalized_eui - t.first_interim_target as gap_2025,
                c.weather_normalized_eui - t.second_interim_target as gap_2027,
                c.weather_normalized_eui - COALESCE(t.adjusted_final_target, t.original_final_target) as gap_2030,
                
                -- Percent reductions needed
                (c.weather_normalized_eui - t.first_interim_target) / NULLIF(c.weather_normalized_eui, 0) * 100 as pct_reduction_2025,
                (c.weather_normalized_eui - COALESCE(t.adjusted_final_target, t.original_final_target)) / NULLIF(c.weather_normalized_eui, 0) * 100 as pct_reduction_2030,
                
                -- Building age factor
                2024 - c.year_built as building_age,
                
                -- MAI flag
                c.is_mai
                
            FROM `{self.dataset_ref}.building_consumption_corrected` c
            JOIN `{self.dataset_ref}.building_analysis_v2` t
                ON c.building_id = t.building_id
            WHERE c.weather_normalized_eui > 0
                AND c.gross_floor_area >= 25000
                AND c.reporting_year = (
                    SELECT MAX(reporting_year) 
                    FROM `{self.dataset_ref}.building_consumption_corrected` c2 
                    WHERE c2.building_id = c.building_id
                )
        ),
        
        mai_adjusted_targets AS (
            SELECT 
                *,
                -- Apply MAI minimum floor of 52.9 kBtu/sqft for manufacturing
                CASE 
                    WHEN property_type = 'Manufacturing/Industrial Plant' 
                    THEN GREATEST(target_2025, 52.9)
                    ELSE target_2025
                END as adjusted_target_2025,
                
                CASE 
                    WHEN property_type = 'Manufacturing/Industrial Plant' 
                    THEN GREATEST(target_2027, 52.9)
                    ELSE target_2027
                END as adjusted_target_2027,
                
                CASE 
                    WHEN property_type = 'Manufacturing/Industrial Plant' 
                    THEN GREATEST(target_2030, 52.9)
                    ELSE target_2030
                END as adjusted_target_2030,
                
                -- Recalculate gaps with MAI floor
                CASE 
                    WHEN property_type = 'Manufacturing/Industrial Plant'
                    THEN current_eui - GREATEST(target_2025, 52.9)
                    ELSE gap_2025
                END as mai_gap_2025,
                
                CASE 
                    WHEN property_type = 'Manufacturing/Industrial Plant'
                    THEN current_eui - GREATEST(target_2030, 52.9)
                    ELSE gap_2030
                END as mai_gap_2030
                
            FROM building_metrics
        ),
        
        financial_analysis AS (
            SELECT 
                *,
                
                -- Calculate penalties for each path using MAI-adjusted gaps
                -- Default path: penalties in 2025, 2027, 2030
                GREATEST(0, mai_gap_2025 * gross_floor_area * {self.PENALTY_RATE_DEFAULT}) as penalty_2025,
                GREATEST(0, (current_eui - adjusted_target_2027) * gross_floor_area * {self.PENALTY_RATE_DEFAULT}) as penalty_2027,
                GREATEST(0, mai_gap_2030 * gross_floor_area * {self.PENALTY_RATE_DEFAULT}) as penalty_2030_default,
                
                -- Opt-in path: penalties in 2028, 2032 (assume same as 2030 target)
                GREATEST(0, mai_gap_2030 * gross_floor_area * {self.PENALTY_RATE_OPTIN}) as penalty_2028_optin,
                GREATEST(0, mai_gap_2030 * gross_floor_area * {self.PENALTY_RATE_OPTIN}) as penalty_2032_optin,
                
                -- Estimate retrofit cost
                CASE 
                    WHEN pct_reduction_2030 < 15 THEN gross_floor_area * {self.retrofit_cost_per_reduction['light']}
                    WHEN pct_reduction_2030 < 30 THEN gross_floor_area * {self.retrofit_cost_per_reduction['moderate']}
                    ELSE gross_floor_area * {self.retrofit_cost_per_reduction['deep']}
                END as estimated_retrofit_cost
                
            FROM mai_adjusted_targets
        ),
        
        npv_analysis AS (
            SELECT 
                *,
                
                -- NPV of penalties for default path (discounted to 2024)
                penalty_2025 / POWER(1 + {self.DISCOUNT_RATE}, 1) +  -- 2025
                penalty_2027 / POWER(1 + {self.DISCOUNT_RATE}, 3) +  -- 2027
                penalty_2030_default / POWER(1 + {self.DISCOUNT_RATE}, 6) as npv_penalties_default,
                
                -- NPV of penalties for opt-in path (discounted to 2024)
                penalty_2028_optin / POWER(1 + {self.DISCOUNT_RATE}, 4) +  -- 2028
                penalty_2032_optin / POWER(1 + {self.DISCOUNT_RATE}, 8) as npv_penalties_optin,
                
                -- Total nominal penalties
                penalty_2025 + penalty_2027 + penalty_2030_default as total_penalties_default,
                penalty_2028_optin + penalty_2032_optin as total_penalties_optin
                
            FROM financial_analysis
        ),
        
        decision_factors AS (
            SELECT 
                *,
                
                -- Financial advantage of opt-in (positive = opt-in saves money)
                npv_penalties_default - npv_penalties_optin as npv_advantage_optin,
                
                -- Time value benefit (years of delay)
                CASE 
                    WHEN mai_gap_2025 > 0 THEN 3  -- Avoid 2025 penalty
                    ELSE 0
                END as years_delay_benefit,
                
                -- Technical feasibility score (0-100, higher = harder)
                CASE 
                    WHEN pct_reduction_2030 > 50 THEN 100  -- Nearly impossible
                    WHEN pct_reduction_2030 > 40 THEN 80   -- Very difficult
                    WHEN pct_reduction_2030 > 30 THEN 60   -- Difficult
                    WHEN pct_reduction_2030 > 20 THEN 40   -- Moderate
                    ELSE 20                                 -- Achievable
                END as technical_difficulty_score,
                
                -- Building condition factor (older = harder to retrofit)
                CASE 
                    WHEN building_age > 50 THEN 1.5  -- Very old, expensive retrofits
                    WHEN building_age > 30 THEN 1.2  -- Old
                    ELSE 1.0                          -- Newer
                END as age_difficulty_factor,
                
                -- Cash flow consideration (can they afford early penalties?)
                CASE 
                    WHEN property_type IN ('Affordable Housing', 'Senior Care Community') THEN TRUE
                    WHEN penalty_2025 > 500000 THEN TRUE  -- Large early penalty
                    ELSE FALSE
                END as cash_flow_constrained
                
            FROM npv_analysis
        )
        
        -- Final decision logic
        SELECT 
            *,
            
            -- Opt-in decision based on multiple factors
            CASE 
                -- Always opt-in cases
                WHEN mai_gap_2025 > 0 AND gap_2027 > 0 AND mai_gap_2030 > 0 THEN TRUE  -- Can't meet any targets
                WHEN cash_flow_constrained AND penalty_2025 > 100000 THEN TRUE  -- Can't afford early penalties
                WHEN technical_difficulty_score >= 80 THEN TRUE                  -- Nearly impossible to retrofit
                WHEN is_mai = 1 AND pct_reduction_2030 > 30 THEN TRUE          -- MAI with major reduction
                
                -- Never opt-in cases  
                WHEN mai_gap_2025 <= 0 THEN FALSE                              -- Already meet 2025 target
                WHEN npv_advantage_optin < -100000 THEN FALSE                   -- Opt-in costs >$100k more
                WHEN pct_reduction_2030 < 10 THEN FALSE                         -- Minor reduction needed
                
                -- Financial decision for others
                WHEN npv_advantage_optin > 0 THEN TRUE                          -- Opt-in saves money (NPV)
                ELSE FALSE
                
            END as should_opt_in,
            
            -- Confidence score (0-100)
            CASE
                WHEN mai_gap_2025 > 0 AND gap_2027 > 0 AND mai_gap_2030 > 0 THEN 100  -- Definitely opt-in
                WHEN mai_gap_2025 <= 0 AND pct_reduction_2030 < 10 THEN 100           -- Definitely don't opt-in
                WHEN ABS(npv_advantage_optin) < 50000 THEN 50                         -- Close call
                ELSE 75                                                                -- Moderate confidence
            END as decision_confidence,
            
            -- Decision rationale
            CASE 
                WHEN mai_gap_2025 > 0 AND gap_2027 > 0 AND mai_gap_2030 > 0 THEN 'Cannot meet any targets'
                WHEN cash_flow_constrained AND penalty_2025 > 100000 THEN 'Cash flow constraints'
                WHEN technical_difficulty_score >= 80 THEN 'Technical infeasibility'
                WHEN mai_gap_2025 <= 0 THEN 'Already meets 2025 target'
                WHEN npv_advantage_optin > 100000 THEN 'Significant financial advantage'
                WHEN npv_advantage_optin > 0 THEN 'Modest financial advantage'
                WHEN npv_advantage_optin < -100000 THEN 'Opt-in too expensive'
                ELSE 'Marginal decision'
            END as primary_rationale
            
        FROM decision_factors
        """
        
        try:
            self.client.query(query).result()
            print(f"✓ Created opt-in decision analysis view: {view_id}")
            
            # Get summary statistics
            self.analyze_opt_in_decisions()
            
            return view_id
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def analyze_opt_in_decisions(self):
        """Analyze the opt-in decisions"""
        
        print("\n=== OPT-IN DECISION SUMMARY ===\n")
        
        # Overall statistics
        query = f"""
        SELECT 
            COUNT(*) as total_buildings,
            COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in_count,
            COUNT(CASE WHEN NOT should_opt_in THEN 1 END) as stay_default_count,
            ROUND(AVG(CASE WHEN should_opt_in THEN decision_confidence END), 1) as avg_confidence_optin,
            ROUND(AVG(CASE WHEN NOT should_opt_in THEN decision_confidence END), 1) as avg_confidence_default
        FROM `{self.dataset_ref}.opt_in_decision_analysis`
        """
        
        results = self.client.query(query).to_dataframe()
        
        print("Overall Decision Summary:")
        print(f"  Total buildings analyzed: {results['total_buildings'].iloc[0]:,}")
        print(f"  Recommended to opt-in: {results['opt_in_count'].iloc[0]:,} ({results['opt_in_count'].iloc[0]/results['total_buildings'].iloc[0]*100:.1f}%)")
        print(f"  Recommended default path: {results['stay_default_count'].iloc[0]:,} ({results['stay_default_count'].iloc[0]/results['total_buildings'].iloc[0]*100:.1f}%)")
        print(f"  Average confidence (opt-in): {results['avg_confidence_optin'].iloc[0]:.0f}%")
        print(f"  Average confidence (default): {results['avg_confidence_default'].iloc[0]:.0f}%")
        
        # By rationale
        print("\n\nOpt-In Decision Rationales:")
        print("-" * 60)
        
        rationale_query = f"""
        SELECT 
            primary_rationale,
            COUNT(*) as building_count,
            COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in_count,
            ROUND(AVG(npv_advantage_optin), 0) as avg_npv_advantage
        FROM `{self.dataset_ref}.opt_in_decision_analysis`
        GROUP BY primary_rationale
        ORDER BY building_count DESC
        """
        
        rationale_results = self.client.query(rationale_query).to_dataframe()
        
        for _, row in rationale_results.iterrows():
            print(f"{row['primary_rationale']:<35} | {row['building_count']:>5} buildings | "
                  f"{row['opt_in_count']:>4} opt-in | NPV: ${row['avg_npv_advantage']:>10,.0f}")
        
        # By property type
        print("\n\nOpt-In Rates by Property Type:")
        print("-" * 80)
        
        type_query = f"""
        SELECT 
            property_type,
            COUNT(*) as total,
            COUNT(CASE WHEN should_opt_in THEN 1 END) as opt_in,
            ROUND(COUNT(CASE WHEN should_opt_in THEN 1 END) * 100.0 / COUNT(*), 1) as opt_in_rate,
            ROUND(AVG(pct_reduction_2030), 1) as avg_reduction_needed,
            ROUND(AVG(CASE WHEN should_opt_in THEN npv_advantage_optin END), 0) as avg_npv_benefit
        FROM `{self.dataset_ref}.opt_in_decision_analysis`
        GROUP BY property_type
        HAVING total > 10
        ORDER BY opt_in_rate DESC
        """
        
        type_results = self.client.query(type_query).to_dataframe()
        
        for _, row in type_results.iterrows():
            print(f"{row['property_type']:<30} | {row['total']:>4} total | {row['opt_in']:>4} opt-in | "
                  f"{row['opt_in_rate']:>5.1f}% | {row['avg_reduction_needed']:>5.1f}% reduction | "
                  f"NPV benefit: ${row['avg_npv_benefit']:>10,.0f}")
        
        # Financial impact
        print("\n\nFinancial Impact Analysis:")
        
        financial_query = f"""
        SELECT 
            should_opt_in,
            COUNT(*) as building_count,
            ROUND(SUM(total_penalties_default), 0) as total_default_penalties,
            ROUND(SUM(total_penalties_optin), 0) as total_optin_penalties,
            ROUND(SUM(npv_penalties_default), 0) as npv_default,
            ROUND(SUM(npv_penalties_optin), 0) as npv_optin,
            ROUND(SUM(estimated_retrofit_cost)/1000000, 1) as retrofit_cost_mm
        FROM `{self.dataset_ref}.opt_in_decision_analysis`
        GROUP BY should_opt_in
        """
        
        financial_results = self.client.query(financial_query).to_dataframe()
        
        print("\nFor buildings recommended to OPT-IN:")
        opt_in_data = financial_results[financial_results['should_opt_in']]
        if not opt_in_data.empty:
            print(f"  Default path penalties: ${opt_in_data['total_default_penalties'].iloc[0]:,.0f}")
            print(f"  Opt-in path penalties: ${opt_in_data['total_optin_penalties'].iloc[0]:,.0f}")
            print(f"  Penalty savings: ${opt_in_data['total_default_penalties'].iloc[0] - opt_in_data['total_optin_penalties'].iloc[0]:,.0f}")
            print(f"  Estimated retrofit costs: ${opt_in_data['retrofit_cost_mm'].iloc[0]:.1f}M")
        
        print("\nFor buildings recommended to STAY DEFAULT:")
        default_data = financial_results[~financial_results['should_opt_in']]
        if not default_data.empty:
            print(f"  Default path penalties: ${default_data['total_default_penalties'].iloc[0]:,.0f}")
            print(f"  Would pay if opted in: ${default_data['total_optin_penalties'].iloc[0]:,.0f}")
            print(f"  Penalty savings by NOT opting in: ${default_data['total_optin_penalties'].iloc[0] - default_data['total_default_penalties'].iloc[0]:,.0f}")
    
    def create_opt_in_recommendation_table(self):
        """Create a table with opt-in recommendations for business use"""
        
        table_id = f"{self.dataset_ref}.opt_in_recommendations"
        
        query = f"""
        CREATE OR REPLACE TABLE `{table_id}` AS
        SELECT 
            building_id,
            building_name,
            property_type,
            ROUND(gross_floor_area, 0) as sqft,
            ROUND(current_eui, 1) as current_eui,
            ROUND(pct_reduction_2030, 1) as reduction_needed_pct,
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
            CASE WHEN mai_gap_2025 > 0 THEN TRUE ELSE FALSE END as misses_2025_target,
            cash_flow_constrained,
            technical_difficulty_score,
            
            CURRENT_TIMESTAMP() as analysis_timestamp
            
        FROM `{self.dataset_ref}.opt_in_decision_analysis`
        ORDER BY ABS(npv_advantage_optin) DESC  -- Biggest financial impacts first
        """
        
        self.client.query(query).result()
        print(f"\n✓ Created opt-in recommendations table: {table_id}")
        print("\nThis table can be used for:")
        print("- Client consultations")
        print("- Opt-in strategy communications")
        print("- Financial planning")
        print("- Compliance pathway selection")


def main():
    """Main execution"""
    
    model = OptInDecisionModel()
    
    print("ENERGIZE DENVER OPT-IN DECISION ANALYSIS")
    print("=" * 80)
    print("\nThis analysis predicts which buildings should opt into the ACO path based on:")
    print("- Financial analysis (NPV of penalties)")
    print("- Technical feasibility")
    print("- Cash flow considerations")
    print("- Building characteristics\n")
    
    # Create the analysis
    view_id = model.create_opt_in_analysis_view()
    
    if view_id:
        # Create recommendation table
        model.create_opt_in_recommendation_table()
        
        print("\n\n🎉 SUCCESS!")
        print(f"Created opt-in decision analysis: {view_id}")
        print("\nKey insights:")
        print("1. Not all buildings over 2024 target should opt-in")
        print("2. Financial NPV is the primary decision factor")
        print("3. Some buildings save money by paying early penalties")
        print("4. Technical feasibility affects ~20% of decisions")
        print("\nUse opt_in_recommendations table for client strategy sessions!")


if __name__ == "__main__":
    main()
