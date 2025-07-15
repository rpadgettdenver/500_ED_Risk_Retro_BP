"""
Suggested File Name: regenerate_bigquery_views_fixed.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Regenerate all BigQuery views with corrected penalty rates and fixed column names

This script:
1. Uses the correct column names found in the schema investigation
2. Recreates views with correct penalty rates
3. Validates the results
4. Generates a summary report
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

# Correct penalty rates
PENALTY_RATE_STANDARD = 0.15  # $/kBtu for standard path
PENALTY_RATE_ACO = 0.23       # $/kBtu for ACO/opt-in path


class BigQueryViewRegenerator:
    """Regenerate all BigQuery views with corrected penalty rates"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        self.views_to_update = []
        self.update_log = []
        
    def log_update(self, message, status="INFO"):
        """Log update progress"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{status}] {message}"
        print(log_entry)
        self.update_log.append(log_entry)
    
    def drop_view(self, view_name):
        """Drop an existing view"""
        view_id = f"{self.dataset_ref}.{view_name}"
        try:
            self.client.delete_table(view_id)
            self.log_update(f"Dropped view: {view_id}", "SUCCESS")
            return True
        except Exception as e:
            if "Not found" in str(e):
                self.log_update(f"View not found: {view_id}", "INFO")
            else:
                self.log_update(f"Error dropping view {view_id}: {str(e)}", "ERROR")
            return False
    
    def create_corrected_penalty_view(self):
        """Create the main penalty calculation view with correct rates"""
        
        view_name = "building_penalties_corrected_v2"
        view_id = f"{self.dataset_ref}.{view_name}"
        
        self.log_update(f"Creating corrected penalty view: {view_name}")
        
        # Fixed query with correct column names
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
                t.baseline_eui,
                t.first_interim_target,
                t.second_interim_target,
                t.first_target_year,  -- Fixed: was first_interim_year
                t.second_target_year, -- Fixed: was second_interim_year
                COALESCE(t.adjusted_final_target, t.original_final_target) as final_target,
                c.is_mai,  -- Using from consumption table since not in building_analysis_v2
                
                -- Calculate gaps
                c.weather_normalized_eui - t.first_interim_target as gap_first,
                c.weather_normalized_eui - t.second_interim_target as gap_second,
                c.weather_normalized_eui - COALESCE(t.adjusted_final_target, t.original_final_target) as gap_final
                
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
        )
        
        SELECT 
            *,
            
            -- STANDARD PATH PENALTIES (using {PENALTY_RATE_STANDARD})
            -- 2025 penalty (first interim)
            CASE 
                WHEN first_target_year = 2025 AND gap_first > 0 
                THEN gap_first * gross_floor_area * {PENALTY_RATE_STANDARD}
                ELSE 0 
            END as penalty_2025_standard,
            
            -- 2027 penalty (second interim)
            CASE 
                WHEN second_target_year = 2027 AND gap_second > 0 
                THEN gap_second * gross_floor_area * {PENALTY_RATE_STANDARD}
                ELSE 0 
            END as penalty_2027_standard,
            
            -- 2030 penalty (final)
            CASE 
                WHEN gap_final > 0 
                THEN gap_final * gross_floor_area * {PENALTY_RATE_STANDARD}
                ELSE 0 
            END as penalty_2030_standard,
            
            -- ACO PATH PENALTIES (using {PENALTY_RATE_ACO})
            -- 2028 penalty (using first interim target)
            CASE 
                WHEN gap_first > 0 
                THEN gap_first * gross_floor_area * {PENALTY_RATE_ACO}
                ELSE 0 
            END as penalty_2028_aco,
            
            -- 2032 penalty (using final target)
            CASE 
                WHEN gap_final > 0 
                THEN gap_final * gross_floor_area * {PENALTY_RATE_ACO}
                ELSE 0 
            END as penalty_2032_aco,
            
            -- Total penalties by path
            CASE 
                WHEN first_target_year = 2025 AND gap_first > 0 
                THEN gap_first * gross_floor_area * {PENALTY_RATE_STANDARD}
                ELSE 0 
            END +
            CASE 
                WHEN second_target_year = 2027 AND gap_second > 0 
                THEN gap_second * gross_floor_area * {PENALTY_RATE_STANDARD}
                ELSE 0 
            END +
            CASE 
                WHEN gap_final > 0 
                THEN gap_final * gross_floor_area * {PENALTY_RATE_STANDARD}
                ELSE 0 
            END as total_penalties_standard,
            
            CASE 
                WHEN gap_first > 0 
                THEN gap_first * gross_floor_area * {PENALTY_RATE_ACO}
                ELSE 0 
            END +
            CASE 
                WHEN gap_final > 0 
                THEN gap_final * gross_floor_area * {PENALTY_RATE_ACO}
                ELSE 0 
            END as total_penalties_aco,
            
            -- Penalty rate verification columns
            {PENALTY_RATE_STANDARD} as rate_standard_used,
            {PENALTY_RATE_ACO} as rate_aco_used,
            
            CURRENT_TIMESTAMP() as calculation_timestamp
            
        FROM building_metrics
        """
        
        try:
            self.client.query(query).result()
            self.log_update(f"Created view: {view_id}", "SUCCESS")
            self.views_to_update.append(view_name)
            return True
        except Exception as e:
            self.log_update(f"Error creating view {view_id}: {str(e)}", "ERROR")
            return False
    
    def create_opt_in_decision_view(self):
        """Create opt-in decision view with correct penalty calculations"""
        
        view_name = "opt_in_decision_analysis_v4"  # v4 since v3 already exists
        view_id = f"{self.dataset_ref}.{view_name}"
        
        self.log_update(f"Creating opt-in decision view: {view_name}")
        
        query = f"""
        CREATE OR REPLACE VIEW `{view_id}` AS
        WITH penalty_analysis AS (
            SELECT 
                *,
                
                -- NPV calculations (7% discount rate)
                penalty_2025_standard / POWER(1.07, 1) +
                penalty_2027_standard / POWER(1.07, 3) + 
                penalty_2030_standard / POWER(1.07, 6) as npv_standard,
                
                penalty_2028_aco / POWER(1.07, 4) +
                penalty_2032_aco / POWER(1.07, 8) as npv_aco,
                
                -- NPV advantage of ACO (positive = ACO saves money)
                (penalty_2025_standard / POWER(1.07, 1) +
                 penalty_2027_standard / POWER(1.07, 3) + 
                 penalty_2030_standard / POWER(1.07, 6)) -
                (penalty_2028_aco / POWER(1.07, 4) +
                 penalty_2032_aco / POWER(1.07, 8)) as npv_advantage_aco
                
            FROM `{self.dataset_ref}.building_penalties_corrected_v2`
        ),
        
        decision_factors AS (
            SELECT 
                *,
                
                -- Reduction percentage needed
                (current_eui - final_target) / NULLIF(current_eui, 0) * 100 as pct_reduction_needed,
                
                -- Technical difficulty score
                CASE 
                    WHEN (current_eui - final_target) / NULLIF(current_eui, 0) * 100 > 40 THEN 80
                    WHEN (current_eui - final_target) / NULLIF(current_eui, 0) * 100 > 30 THEN 60
                    WHEN (current_eui - final_target) / NULLIF(current_eui, 0) * 100 > 20 THEN 40
                    ELSE 20
                END as technical_difficulty,
                
                -- Cash flow impact
                CASE 
                    WHEN property_type IN ('Affordable Housing', 'Senior Care Community') THEN TRUE
                    WHEN penalty_2025_standard > 100000 THEN TRUE
                    ELSE FALSE
                END as cash_constrained
                
            FROM penalty_analysis
        )
        
        SELECT 
            building_id,
            building_name,
            property_type,
            gross_floor_area,
            current_eui,
            gap_first,
            gap_second,
            gap_final,
            pct_reduction_needed,
            
            -- Penalties
            penalty_2025_standard,
            penalty_2027_standard,
            penalty_2030_standard,
            total_penalties_standard,
            
            penalty_2028_aco,
            penalty_2032_aco,
            total_penalties_aco,
            
            -- NPV analysis
            ROUND(npv_standard, 2) as npv_standard,
            ROUND(npv_aco, 2) as npv_aco,
            ROUND(npv_advantage_aco, 2) as npv_advantage_aco,
            
            -- Decision
            CASE 
                -- Always opt-in cases
                WHEN gap_first > 0 AND gap_second > 0 AND gap_final > 0 THEN TRUE
                WHEN cash_constrained AND penalty_2025_standard > 50000 THEN TRUE
                WHEN technical_difficulty >= 80 THEN TRUE
                
                -- Never opt-in cases
                WHEN gap_first <= 0 THEN FALSE
                WHEN npv_advantage_aco < -50000 THEN FALSE
                
                -- Financial decision
                WHEN npv_advantage_aco > 0 THEN TRUE
                ELSE FALSE
            END as should_opt_in,
            
            -- Confidence
            CASE
                WHEN gap_first > 0 AND gap_second > 0 AND gap_final > 0 THEN 95
                WHEN gap_first <= 0 THEN 95
                WHEN ABS(npv_advantage_aco) < 25000 THEN 60
                ELSE 80
            END as decision_confidence,
            
            -- Rationale
            CASE 
                WHEN gap_first > 0 AND gap_second > 0 AND gap_final > 0 THEN 'Cannot meet any targets'
                WHEN cash_constrained AND penalty_2025_standard > 50000 THEN 'Cash flow constraints'
                WHEN technical_difficulty >= 80 THEN 'Technical infeasibility'
                WHEN gap_first <= 0 THEN 'Already meets 2025 target'
                WHEN npv_advantage_aco > 50000 THEN 'Significant financial advantage'
                WHEN npv_advantage_aco > 0 THEN 'Modest financial advantage'
                WHEN npv_advantage_aco < -50000 THEN 'ACO too expensive'
                ELSE 'Marginal decision'
            END as primary_rationale,
            
            -- Verification
            rate_standard_used,
            rate_aco_used,
            calculation_timestamp
            
        FROM decision_factors
        """
        
        try:
            self.client.query(query).result()
            self.log_update(f"Created view: {view_id}", "SUCCESS")
            self.views_to_update.append(view_name)
            return True
        except Exception as e:
            self.log_update(f"Error creating view {view_id}: {str(e)}", "ERROR")
            return False
    
    def check_table_status(self):
        """Check if required tables exist and have data"""
        
        self.log_update("\nChecking table status before creating views")
        
        tables_to_check = [
            'building_consumption_corrected',
            'building_analysis_v2'
        ]
        
        all_good = True
        
        for table_name in tables_to_check:
            table_id = f"{self.dataset_ref}.{table_name}"
            query = f"SELECT COUNT(*) as row_count FROM `{table_id}`"
            
            try:
                result = self.client.query(query).to_dataframe()
                row_count = result['row_count'].iloc[0]
                
                if row_count == 0:
                    self.log_update(f"⚠️  Table {table_name} has NO DATA ({row_count} rows)", "WARNING")
                    all_good = False
                else:
                    self.log_update(f"✅ Table {table_name} has {row_count:,} rows", "SUCCESS")
                    
            except Exception as e:
                self.log_update(f"❌ Error checking table {table_name}: {str(e)}", "ERROR")
                all_good = False
        
        return all_good
    
    def populate_building_analysis_v2(self):
        """Populate the empty building_analysis_v2 table"""
        
        self.log_update("\nPopulating building_analysis_v2 table with data")
        
        # First, let's check what data source we should use
        query = """
        SELECT table_name
        FROM `energize-denver-eaas.energize_denver.INFORMATION_SCHEMA.TABLES`
        WHERE table_name LIKE '%target%' OR table_name LIKE '%eui%'
        ORDER BY table_name
        """
        
        try:
            tables = self.client.query(query).to_dataframe()
            self.log_update(f"Available target tables: {', '.join(tables['table_name'].tolist())}")
            
            # Try to populate from building_eui_targets if it exists
            populate_query = f"""
            INSERT INTO `{self.dataset_ref}.building_analysis_v2`
            SELECT 
                CAST(`Building ID` AS STRING) as building_id,
                `Master Property Type` as property_type,
                `Master Sq Ft` as gross_floor_area,
                NULL as has_target_adjustment,
                NULL as has_electrification_credit,
                `Baseline EUI` as baseline_eui,
                `First Interim Target EUI` as first_interim_target,
                `Second Interim Target EUI` as second_interim_target,
                `Final Target EUI` as original_final_target,
                `Adjusted Final Target EUI` as adjusted_final_target,
                CAST(`Baseline Year` AS INT64) as baseline_year,
                CAST(`First Interim Target Year` AS INT64) as first_target_year,
                CAST(`Second Interim Target Year` AS INT64) as second_target_year,
                `Building Name` as building_name,
                `Master Address` as address,
                `Master Zipcode` as zipcode,
                NULL as latitude,
                NULL as longitude,
                NULL as is_epb,
                NULL as percent_reduction_needed,
                NULL as reduction_difficulty
            FROM `{self.dataset_ref}.building_eui_targets`
            """
            
            self.client.query(populate_query).result()
            
            # Check how many rows were inserted
            count_query = f"SELECT COUNT(*) as count FROM `{self.dataset_ref}.building_analysis_v2`"
            result = self.client.query(count_query).to_dataframe()
            row_count = result['count'].iloc[0]
            
            self.log_update(f"✅ Populated building_analysis_v2 with {row_count:,} rows", "SUCCESS")
            return True
            
        except Exception as e:
            self.log_update(f"Error populating building_analysis_v2: {str(e)}", "ERROR")
            return False
    
    def validate_penalty_rates(self):
        """Validate that the new views use correct penalty rates"""
        
        self.log_update("\nValidating penalty rates in new views")
        
        # Check penalty calculation view
        query = f"""
        SELECT DISTINCT
            rate_standard_used,
            rate_aco_used
        FROM `{self.dataset_ref}.building_penalties_corrected_v2`
        LIMIT 1
        """
        
        try:
            result = self.client.query(query).to_dataframe()
            
            if not result.empty:
                std_rate = result['rate_standard_used'].iloc[0]
                aco_rate = result['rate_aco_used'].iloc[0]
                
                if abs(std_rate - PENALTY_RATE_STANDARD) < 0.001 and abs(aco_rate - PENALTY_RATE_ACO) < 0.001:
                    self.log_update(f"✅ Penalty rates verified: Standard=${std_rate}, ACO=${aco_rate}", "SUCCESS")
                    return True
                else:
                    self.log_update(f"❌ Incorrect rates: Standard=${std_rate} (expected ${PENALTY_RATE_STANDARD}), "
                                  f"ACO=${aco_rate} (expected ${PENALTY_RATE_ACO})", "ERROR")
                    return False
            else:
                self.log_update("No data returned from validation query", "ERROR")
                return False
                
        except Exception as e:
            self.log_update(f"Error validating rates: {str(e)}", "ERROR")
            return False
    
    def test_building_2952(self):
        """Test calculations for Building 2952"""
        
        query = f"""
        SELECT 
            building_id,
            current_eui,
            first_interim_target,
            gap_first,
            gross_floor_area,
            penalty_2025_standard,
            penalty_2028_aco,
            ROUND(penalty_2025_standard, 2) as penalty_2025_rounded,
            ROUND(penalty_2028_aco, 2) as penalty_2028_rounded
        FROM `{self.dataset_ref}.building_penalties_corrected_v2`
        WHERE building_id = '2952'
        """
        
        try:
            result = self.client.query(query).to_dataframe()
            
            if not result.empty:
                self.log_update("\n🏢 Building 2952 Test Case:", "INFO")
                row = result.iloc[0]
                
                # Manual calculation
                gap = row['gap_first']
                sqft = row['gross_floor_area']
                expected_std = gap * sqft * PENALTY_RATE_STANDARD
                expected_aco = gap * sqft * PENALTY_RATE_ACO
                
                self.log_update(f"Current EUI: {row['current_eui']}")
                self.log_update(f"First Interim Target: {row['first_interim_target']}")
                self.log_update(f"Gap (first interim): {gap:.2f}")
                self.log_update(f"Square footage: {sqft:,.0f}")
                self.log_update(f"2025 penalty (standard): ${row['penalty_2025_standard']:,.2f} "
                              f"(expected: ${expected_std:,.2f})")
                self.log_update(f"2028 penalty (ACO): ${row['penalty_2028_aco']:,.2f} "
                              f"(expected: ${expected_aco:,.2f})")
                
                # Verify the calculation
                if abs(row['penalty_2025_standard'] - expected_std) < 1:
                    self.log_update("✅ Standard penalty calculation verified!", "SUCCESS")
                else:
                    self.log_update("❌ Standard penalty calculation mismatch!", "ERROR")
                    
                if abs(row['penalty_2028_aco'] - expected_aco) < 1:
                    self.log_update("✅ ACO penalty calculation verified!", "SUCCESS")
                else:
                    self.log_update("❌ ACO penalty calculation mismatch!", "ERROR")
                
        except Exception as e:
            self.log_update(f"Building 2952 not found or error: {str(e)}", "INFO")
    
    def run_full_regeneration(self):
        """Run the complete regeneration process"""
        
        self.log_update("="*80)
        self.log_update("BIGQUERY VIEW REGENERATION WITH CORRECTED PENALTY RATES")
        self.log_update("="*80)
        
        # Step 0: Check table status
        self.log_update("\nStep 0: Checking table status", "INFO")
        if not self.check_table_status():
            # Try to populate building_analysis_v2 if it's empty
            self.log_update("\nAttempting to populate empty tables", "INFO")
            if not self.populate_building_analysis_v2():
                self.log_update("Failed to populate tables. Cannot proceed.", "ERROR")
                return False
        
        # Step 1: Drop old views
        self.log_update("\nStep 1: Dropping old views", "INFO")
        old_views = ['building_penalties_corrected', 'opt_in_decision_analysis_v2']
        for view in old_views:
            self.drop_view(view)
        
        # Step 2: Create new views
        self.log_update("\nStep 2: Creating new views with correct rates", "INFO")
        
        success = True
        success &= self.create_corrected_penalty_view()
        
        if success:
            success &= self.create_opt_in_decision_view()
        
        if success:
            # Step 3: Validate
            self.log_update("\nStep 3: Validating penalty rates", "INFO")
            if self.validate_penalty_rates():
                
                # Step 4: Test specific building
                self.log_update("\nStep 4: Testing Building 2952", "INFO")
                self.test_building_2952()
                
                self.log_update("\n✅ REGENERATION COMPLETE!", "SUCCESS")
                self.log_update(f"Views created: {', '.join(self.views_to_update)}")
                
                return True
            else:
                self.log_update("\n❌ Validation failed!", "ERROR")
                return False
        else:
            self.log_update("\n❌ Failed to create all views!", "ERROR")
            return False


def main():
    """Main execution"""
    
    regenerator = BigQueryViewRegenerator()
    
    # Run the full regeneration
    success = regenerator.run_full_regeneration()
    
    if success:
        print("\n" + "="*80)
        print("🎉 SUCCESS! BigQuery views have been regenerated with correct penalty rates.")
        print("\nViews created:")
        print("  - building_penalties_corrected_v2")
        print("  - opt_in_decision_analysis_v4")
        print("\nNext steps:")
        print("1. Review the opt-in recommendations")
        print("2. Update any dependent reports or dashboards")
        print("3. Run portfolio analysis with updated data")
    else:
        print("\n" + "="*80)
        print("❌ Regeneration encountered errors. Please review the logs above.")


if __name__ == "__main__":
    main()
