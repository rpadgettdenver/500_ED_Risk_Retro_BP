"""
Suggested File Name: create_penalty_analysis_corrected.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Create corrected penalty analysis following the April 2025 Technical Guidance rules

This script implements the correct penalty structure:
- $0.15/kBtu for default path (fines in 2025, 2027, 2030 = 3 years)
- $0.23/kBtu for opt-in path (fines in 2028, 2032 = 2 years)
- Handles MAI buildings separately
- Uses weather-normalized EUI
- Deduplicates buildings (latest year only)
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

class CorrectedPenaltyModel:
    """Implement correct penalty calculations per technical guidance"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        
        # Penalty rates per technical guidance
        self.PENALTY_RATE_DEFAULT = 0.15  # $/kBtu for 2024-2030 path
        self.PENALTY_RATE_OPTIN = 0.23    # $/kBtu for 2028-2032 path
        self.NON_SUBMISSION_PENALTY = 10.0  # $/sqft one-time
        self.NON_SUBMISSION_MONTHLY = 2000  # $/month
        
    def reload_consumption_with_years(self):
        """First reload the consumption data with proper year extraction"""
        
        print("=== RELOADING CONSUMPTION DATA WITH YEAR INFO ===\n")
        
        import pandas as pd
        
        # Read Excel file
        excel_path = "data/raw/Energize Denver Report Request 060225.xlsx"
        df = pd.read_excel(excel_path)
        
        print(f"Loaded {len(df)} rows from Excel")
        
        # Debug: Show available columns
        print("\nAvailable columns in Excel:")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2}. {col}")
        
        # Create comprehensive dataframe
        processed_df = pd.DataFrame()
        
        # Core identification
        processed_df['building_id'] = df['Building ID'].astype(str)
        # Extract year from ID-Yr column (e.g., "1001-2023" -> 2023)
        processed_df['reporting_year'] = pd.to_numeric(
            df['ID-Yr'].astype(str).str.extract(r'-(\d{4})')[0], 
            errors='coerce'
        )
        
        # Building info
        processed_df['building_name'] = df['Building Name'].fillna('').astype(str)
        processed_df['parent_property'] = df['Parent Property'].fillna('').astype(str)
        processed_df['property_type'] = df['Master Property Type'].fillna('').astype(str)
        processed_df['year_built'] = pd.to_numeric(df['Year Built'], errors='coerce')
        
        # Size metrics
        processed_df['gross_floor_area'] = pd.to_numeric(df['Master Sq Ft'], errors='coerce')
        
        # Energy metrics - both regular and weather normalized
        processed_df['site_energy_use'] = pd.to_numeric(df['Site Energy Use'], errors='coerce')
        processed_df['site_eui'] = pd.to_numeric(df['Site EUI'], errors='coerce')
        processed_df['weather_normalized_energy'] = pd.to_numeric(
            df['Weather Normalized Site Energy Use'], errors='coerce'
        )
        processed_df['weather_normalized_eui'] = pd.to_numeric(
            df['Weather Normalized Site EUI'], errors='coerce'
        )
        
        # Compliance info - check if columns exist
        if 'Energy Star Score' in df.columns:
            processed_df['energy_star_score'] = pd.to_numeric(df['Energy Star Score'], errors='coerce')
        else:
            processed_df['energy_star_score'] = None
            
        if 'Status' in df.columns:
            processed_df['status'] = df['Status'].fillna('').astype(str)
        else:
            processed_df['status'] = ''
            
        if 'Submission Date' in df.columns:
            processed_df['submission_date'] = pd.to_datetime(df['Submission Date'], errors='coerce')
        else:
            processed_df['submission_date'] = None
        
        # Check for MAI property types
        mai_types = ['Manufacturing/Industrial Plant', 'Data Center', 'Agricultural']
        processed_df['is_mai'] = processed_df['property_type'].isin(mai_types).astype(int)
        
        # Metadata
        processed_df['source_file'] = 'Energize Denver Report Request 060225.xlsx'
        processed_df['load_timestamp'] = datetime.now().isoformat()
        
        # Summary
        print(f"\n📊 Processed Data Summary:")
        print(f"   Total records: {len(processed_df)}")
        print(f"   Unique buildings: {processed_df['building_id'].nunique()}")
        print(f"   Year range: {processed_df['reporting_year'].min():.0f} - {processed_df['reporting_year'].max():.0f}")
        print(f"   Buildings with weather normalized EUI: {processed_df['weather_normalized_eui'].notna().sum()}")
        print(f"   MAI buildings identified: {processed_df['is_mai'].sum()}")
        
        # Upload to BigQuery
        table_id = f"{self.dataset_ref}.building_consumption_corrected"
        
        print(f"\nUploading to {table_id}...")
        
        # Ensure all object columns are strings
        for col in processed_df.select_dtypes(include=['object']).columns:
            processed_df[col] = processed_df[col].astype(str)
        
        # Upload
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True
        )
        
        job = self.client.load_table_from_dataframe(
            processed_df, table_id, job_config=job_config
        )
        job.result()
        
        table = self.client.get_table(table_id)
        print(f"✓ Uploaded {table.num_rows} rows to {table_id}")
        
        return table_id
    
    def create_corrected_penalty_view(self):
        """Create penalty view with correct calculations"""
        
        view_id = f"{self.dataset_ref}.penalty_analysis_corrected"
        
        print("\n=== CREATING CORRECTED PENALTY ANALYSIS VIEW ===")
        
        query = f"""
        CREATE OR REPLACE VIEW `{view_id}` AS
        WITH latest_consumption AS (
            -- Get only the most recent year of data for each building
            SELECT *
            FROM (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY building_id 
                        ORDER BY reporting_year DESC
                    ) as rn
                FROM `{self.dataset_ref}.building_consumption_corrected`
                WHERE weather_normalized_eui IS NOT NULL
                    AND weather_normalized_eui > 0
                    AND reporting_year >= 2022  -- Focus on recent data
                    AND gross_floor_area >= 25000  -- Only buildings ≥25k sqft
            )
            WHERE rn = 1
        ),
        combined_data AS (
            SELECT 
                t.*,
                c.reporting_year,
                c.weather_normalized_eui as actual_eui,
                c.site_eui as raw_site_eui,
                c.building_name as consumption_building_name,
                c.parent_property,
                c.energy_star_score,
                c.status as consumption_status,
                c.is_mai,
                
                -- Calculate gaps using weather normalized EUI
                c.weather_normalized_eui - t.first_interim_target as interim_gap,
                c.weather_normalized_eui - COALESCE(t.adjusted_final_target, t.original_final_target) as final_gap,
                
                -- Determine compliance path
                -- If building is over 2024 target, assume opt-in to 2028/2032 path
                CASE 
                    WHEN c.weather_normalized_eui > t.first_interim_target THEN TRUE
                    ELSE FALSE
                END as opted_in,
                
                -- Compliance path label
                CASE 
                    WHEN c.weather_normalized_eui > t.first_interim_target THEN 'Opt-in (2028/2032)'
                    ELSE 'Default (2024/2030)'
                END as compliance_path
                
            FROM `{self.dataset_ref}.building_analysis_v2` t
            INNER JOIN latest_consumption c  -- INNER JOIN to only include buildings with consumption data
                ON t.building_id = c.building_id
        )
        SELECT 
            *,
            -- Calculate ANNUAL penalties based on weather normalized EUI
            -- Default path: $0.15/kBtu
            -- Opt-in path: $0.23/kBtu
            CASE 
                WHEN consumption_status = 'Exempt' THEN 0  -- Exempt buildings pay no penalty
                WHEN is_mai = 1 THEN 
                    -- MAI buildings use same penalty rates but may have different targets
                    -- For now, apply standard calculation pending MAI-specific targets
                    CASE
                        WHEN opted_in THEN 
                            GREATEST(0, interim_gap * gross_floor_area * {self.PENALTY_RATE_OPTIN})
                        ELSE 
                            GREATEST(0, interim_gap * gross_floor_area * {self.PENALTY_RATE_DEFAULT})
                    END
                WHEN opted_in THEN 
                    -- Opt-in path: penalties start 2028
                    GREATEST(0, interim_gap * gross_floor_area * {self.PENALTY_RATE_OPTIN})
                ELSE 
                    -- Default path: penalties start 2024
                    GREATEST(0, interim_gap * gross_floor_area * {self.PENALTY_RATE_DEFAULT})
            END as annual_penalty_2024,
            
            -- Final target penalties (2030 or 2032)
            CASE 
                WHEN consumption_status = 'Exempt' THEN 0
                WHEN is_mai = 1 THEN 
                    CASE
                        WHEN opted_in THEN 
                            GREATEST(0, final_gap * gross_floor_area * {self.PENALTY_RATE_OPTIN})
                        ELSE 
                            GREATEST(0, final_gap * gross_floor_area * {self.PENALTY_RATE_DEFAULT})
                    END
                WHEN opted_in THEN 
                    GREATEST(0, final_gap * gross_floor_area * {self.PENALTY_RATE_OPTIN})
                ELSE 
                    GREATEST(0, final_gap * gross_floor_area * {self.PENALTY_RATE_DEFAULT})
            END as annual_penalty_2030,
            
            -- Total penalty exposure over compliance period
            -- Default: 3 fine years (2025, 2027, 2030) at $0.15/kBtu
            -- Opt-in: 2 fine years (2028, 2032) at $0.23/kBtu
            CASE 
                WHEN consumption_status = 'Exempt' THEN 0
                WHEN opted_in THEN 
                    -- 2 years of fines at opt-in rate (2028 and 2032)
                    GREATEST(0, interim_gap * gross_floor_area * {self.PENALTY_RATE_OPTIN} * 2)
                ELSE 
                    -- 3 years of fines at default rate (2025, 2027, 2030)
                    GREATEST(0, interim_gap * gross_floor_area * {self.PENALTY_RATE_DEFAULT} * 3)
            END as total_penalty_exposure,
            
            -- Risk categorization
            CASE 
                WHEN consumption_status = 'Exempt' THEN 'Exempt'
                WHEN interim_gap <= 0 THEN 'Compliant'
                WHEN interim_gap * gross_floor_area * 
                     CASE WHEN opted_in THEN {self.PENALTY_RATE_OPTIN} ELSE {self.PENALTY_RATE_DEFAULT} END 
                     > 50000 THEN 'High Risk'
                WHEN interim_gap * gross_floor_area * 
                     CASE WHEN opted_in THEN {self.PENALTY_RATE_OPTIN} ELSE {self.PENALTY_RATE_DEFAULT} END 
                     > 10000 THEN 'Medium Risk'
                ELSE 'Low Risk'
            END as risk_category,
            
            -- Additional flags
            CASE WHEN interim_gap <= 0 THEN TRUE ELSE FALSE END as meets_2024_target,
            CASE WHEN final_gap <= 0 THEN TRUE ELSE FALSE END as meets_final_target
            
        FROM combined_data
        """
        
        try:
            self.client.query(query).result()
            print(f"✓ Created corrected penalty analysis view: {view_id}")
            
            # Get summary
            summary_query = f"""
            SELECT 
                COUNT(DISTINCT building_id) as unique_buildings,
                COUNT(DISTINCT CASE WHEN opted_in THEN building_id END) as opted_in_buildings,
                COUNT(DISTINCT CASE WHEN is_mai = 1 THEN building_id END) as mai_buildings,
                COUNT(DISTINCT CASE WHEN risk_category = 'High Risk' THEN building_id END) as high_risk_buildings,
                COUNT(DISTINCT CASE WHEN risk_category = 'Compliant' THEN building_id END) as compliant_buildings,
                COUNT(DISTINCT CASE WHEN risk_category = 'Exempt' THEN building_id END) as exempt_buildings,
                
                -- Annual penalties
                ROUND(SUM(annual_penalty_2024), 0) as total_annual_penalty_2024,
                ROUND(AVG(CASE WHEN annual_penalty_2024 > 0 THEN annual_penalty_2024 END), 0) as avg_annual_penalty,
                
                -- Total exposure over compliance period
                ROUND(SUM(total_penalty_exposure), 0) as total_penalty_exposure,
                
                -- By path
                ROUND(SUM(CASE WHEN NOT opted_in THEN annual_penalty_2024 END), 0) as default_path_annual,
                ROUND(SUM(CASE WHEN opted_in THEN annual_penalty_2024 END), 0) as optin_path_annual
                
            FROM `{view_id}`
            """
            
            results = self.client.query(summary_query).to_dataframe()
            
            print("\n📊 Corrected Penalty Analysis Summary:")
            print(f"   Unique buildings analyzed: {results['unique_buildings'].iloc[0]:,}")
            print(f"   Buildings opting in (2028/2032): {results['opted_in_buildings'].iloc[0]:,}")
            print(f"   MAI buildings: {results['mai_buildings'].iloc[0]:,}")
            print(f"   Compliant buildings: {results['compliant_buildings'].iloc[0]:,}")
            print(f"   Exempt buildings: {results['exempt_buildings'].iloc[0]:,}")
            print(f"   High risk buildings: {results['high_risk_buildings'].iloc[0]:,}")
            print(f"\n💰 Annual Penalty Exposure (if no improvements):")
            print(f"   Total annual penalties: ${results['total_annual_penalty_2024'].iloc[0]:,.0f}")
            print(f"   Default path (2024-2030): ${results['default_path_annual'].iloc[0]:,.0f}/year")
            print(f"   Opt-in path (2028-2032): ${results['optin_path_annual'].iloc[0]:,.0f}/year")
            print(f"   Average penalty per non-compliant building: ${results['avg_annual_penalty'].iloc[0]:,.0f}/year")
            print(f"\n📈 Total Penalty Exposure Over Compliance Period:")
            print(f"   ${results['total_penalty_exposure'].iloc[0]:,.0f}")
            
            # Show example calculations
            self.show_example_calculations()
            
            return view_id
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def show_example_calculations(self):
        """Show detailed penalty calculations for specific buildings"""
        
        print("\n\n=== EXAMPLE PENALTY CALCULATIONS ===")
        
        # Get a few examples
        query = f"""
        SELECT 
            building_id,
            COALESCE(building_name, consumption_building_name) as building_name,
            property_type,
            is_mai,
            ROUND(gross_floor_area, 0) as sqft,
            ROUND(actual_eui, 1) as weather_normalized_eui,
            ROUND(first_interim_target, 1) as target_2024,
            ROUND(interim_gap, 1) as eui_gap,
            opted_in,
            compliance_path,
            ROUND(annual_penalty_2024, 0) as annual_penalty,
            ROUND(total_penalty_exposure, 0) as total_exposure,
            risk_category
        FROM `{self.dataset_ref}.penalty_analysis_corrected`
        WHERE annual_penalty_2024 > 0
            AND building_name IS NOT NULL
        ORDER BY annual_penalty_2024 DESC
        LIMIT 5
        """
        
        examples = self.client.query(query).to_dataframe()
        
        print("\nTop 5 Buildings by Annual Penalty:")
        print("-" * 120)
        
        for _, row in examples.iterrows():
            print(f"\n{row['building_name'][:40]} ({row['property_type']})")
            print(f"  Square footage: {row['sqft']:,.0f} sqft")
            print(f"  Current EUI: {row['weather_normalized_eui']:.1f} kBtu/sqft/year")
            print(f"  Target EUI: {row['target_2024']:.1f} kBtu/sqft/year")
            print(f"  EUI Gap: {row['eui_gap']:.1f} kBtu/sqft/year")
            print(f"  Compliance path: {row['compliance_path']}")
            
            # Show the math
            if row['opted_in']:
                rate = self.PENALTY_RATE_OPTIN
                years = 2  # Fines only in 2028 and 2032
                print(f"  Calculation: {row['eui_gap']:.1f} × {row['sqft']:,.0f} × ${rate} = ${row['annual_penalty']:,.0f}/year")
                print(f"  Fine years: 2028 and 2032 (2 years)")
                print(f"  Total exposure: ${row['annual_penalty']:,.0f} × {years} years = ${row['total_exposure']:,.0f}")
            else:
                rate = self.PENALTY_RATE_DEFAULT
                years = 3  # Fines only in 2025, 2027, and 2030
                print(f"  Calculation: {row['eui_gap']:.1f} × {row['sqft']:,.0f} × ${rate} = ${row['annual_penalty']:,.0f}/year")
                print(f"  Fine years: 2025, 2027, and 2030 (3 years)")
                print(f"  Total exposure: ${row['annual_penalty']:,.0f} × {years} years = ${row['total_exposure']:,.0f}")
    
    def create_summary_tables(self):
        """Create summary tables for reporting"""
        
        print("\n\n=== CREATING SUMMARY TABLES ===")
        
        # By property type
        query = f"""
        CREATE OR REPLACE TABLE `{self.dataset_ref}.penalty_summary_by_type` AS
        SELECT 
            property_type,
            COUNT(DISTINCT building_id) as building_count,
            ROUND(AVG(gross_floor_area), 0) as avg_sqft,
            ROUND(AVG(actual_eui), 1) as avg_actual_eui,
            ROUND(AVG(first_interim_target), 1) as avg_target_eui,
            COUNT(DISTINCT CASE WHEN opted_in THEN building_id END) as opted_in_count,
            COUNT(DISTINCT CASE WHEN is_mai = 1 THEN building_id END) as mai_count,
            COUNT(DISTINCT CASE WHEN risk_category = 'High Risk' THEN building_id END) as high_risk_count,
            ROUND(SUM(annual_penalty_2024), 0) as total_annual_penalty,
            ROUND(SUM(total_penalty_exposure), 0) as total_exposure
        FROM `{self.dataset_ref}.penalty_analysis_corrected`
        GROUP BY property_type
        HAVING building_count > 5
        ORDER BY total_annual_penalty DESC
        """
        
        self.client.query(query).result()
        print("✓ Created penalty_summary_by_type table")
        
        # Create action list for business development
        query2 = f"""
        CREATE OR REPLACE TABLE `{self.dataset_ref}.high_priority_targets` AS
        SELECT 
            building_id,
            COALESCE(building_name, consumption_building_name) as building_name,
            property_type,
            ROUND(gross_floor_area, 0) as sqft,
            ROUND(actual_eui, 1) as current_eui,
            ROUND(first_interim_target, 1) as target_eui,
            ROUND(percent_reduction_needed, 1) as reduction_pct,
            compliance_path,
            ROUND(annual_penalty_2024, 0) as annual_penalty,
            ROUND(total_penalty_exposure, 0) as total_exposure,
            is_epb,
            is_mai,
            risk_category,
            CURRENT_TIMESTAMP() as analysis_date
        FROM `{self.dataset_ref}.penalty_analysis_corrected`
        WHERE risk_category IN ('High Risk', 'Medium Risk')
        ORDER BY annual_penalty_2024 DESC
        """
        
        self.client.query(query2).result()
        print("✓ Created high_priority_targets table")
        
        print("\n✅ All tables created successfully!")
        print("\nUse these tables for:")
        print("- penalty_summary_by_type: Understand market segments")
        print("- high_priority_targets: Sales outreach list")
        print("- penalty_analysis_corrected: Detailed analysis")


def main():
    """Main execution"""
    
    model = CorrectedPenaltyModel()
    
    print("ENERGIZE DENVER CORRECTED PENALTY ANALYSIS")
    print("=" * 80)
    print("\nThis analysis follows the April 2025 Technical Guidance:")
    print("- $0.15/kBtu for default path (fines in 2025, 2027, 2030)")
    print("- $0.23/kBtu for opt-in path (fines in 2028, 2032)")
    print("- Fines are ONLY levied in target years, not annually")
    print("- Weather-normalized EUI")
    print("- Latest year data only\n")
    
    # Step 1: Reload consumption data with year info
    response = input("Reload consumption data with corrections? (y/n): ")
    
    if response.lower() == 'y':
        table_id = model.reload_consumption_with_years()
        
        # Step 2: Create corrected penalty view
        view_id = model.create_corrected_penalty_view()
        
        if view_id:
            # Step 3: Create summary tables
            model.create_summary_tables()
            
            print("\n\n🎉 SUCCESS!")
            print(f"Created corrected penalty analysis: {view_id}")
            print("\nNext steps:")
            print("1. Update clustering analysis to use penalty_analysis_corrected")
            print("2. Update financial model to use penalty_analysis_corrected")
            print("3. Create Looker Studio dashboards with realistic penalties")
            print("4. Use high_priority_targets table for sales outreach")


if __name__ == "__main__":
    main()
