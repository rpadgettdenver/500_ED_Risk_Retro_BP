"""
Suggested File Name: financial_model_bigquery.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/models/
Use: Calculate retrofit costs, available incentives, and ROI for building decarbonization
     projects including ITC, Clean Heat Plan, and utility rebates

This script:
1. Estimates retrofit costs based on building type and EUI reduction needed
2. Calculates Section 48 ITC eligibility (30% base + bonuses)
3. Models Clean Heat Plan rebates for heat pumps
4. Computes payback periods and NPV
5. Prioritizes projects by financial return and social impact (EPB status)
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

class RetrofitFinancialModel:
    """Financial modeling for building retrofits and incentives"""
    
    def __init__(self):
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        self.dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
        
        # Cost assumptions ($/sqft) - these would come from a config table in production
        self.retrofit_costs = {
            'heat_pump_basic': 8.0,      # Basic air-source heat pump
            'heat_pump_premium': 15.0,   # Ground-source or high-efficiency
            'envelope_basic': 5.0,        # Basic insulation/air sealing
            'envelope_advanced': 12.0,    # Deep envelope retrofit
            'controls_basic': 2.0,        # Basic BMS upgrade
            'solar_pv': 3.0,             # Rooftop solar per sqft of roof
            'thermal_storage': 4.0,       # Thermal battery system
        }
        
        # Incentive parameters
        self.itc_base = 0.30  # 30% base ITC
        self.itc_bonus_labor = 0.10  # Prevailing wage bonus
        self.itc_bonus_location = 0.10  # Energy community bonus
        self.clean_heat_per_ton = 1000  # Clean Heat Plan $/ton
        
    def create_financial_model_view(self):
        """Create a comprehensive financial model view in BigQuery"""
        
        view_id = f"{self.dataset_ref}.retrofit_financial_model"
        
        # First check if cluster table exists
        check_query = f"""
        SELECT table_name 
        FROM `{self.dataset_ref}.INFORMATION_SCHEMA.TABLES` 
        WHERE table_name = 'cluster_opportunities_summary'
        """
        
        check_result = self.bq_client.query(check_query).to_dataframe()
        has_cluster_data = not check_result.empty
        
        # Build query with or without cluster data
        if has_cluster_data:
            query = f"""
            CREATE OR REPLACE VIEW `{view_id}` AS
            WITH building_data AS (
                SELECT 
                    p.*,
                    c.cluster_category,
                    c.total_connections,
                    c.total_heat_recovery_opps,
                    
                    -- Calculate required EUI reduction
                    GREATEST(0, actual_eui - COALESCE(adjusted_final_target, original_final_target)) 
                        as eui_reduction_needed,
                    
                    -- Estimate HVAC tonnage (rough: 400 sqft/ton)
                    ROUND(gross_floor_area / 400, 0) as estimated_hvac_tons,
                    
                    -- Determine retrofit intensity needed
                    CASE 
                        WHEN percent_reduction_needed > 40 THEN 'Deep Retrofit'
                        WHEN percent_reduction_needed > 25 THEN 'Major Retrofit'
                        WHEN percent_reduction_needed > 15 THEN 'Moderate Retrofit'
                        ELSE 'Light Retrofit'
                    END as retrofit_level
                    
                FROM `{self.dataset_ref}.penalty_analysis` p
                LEFT JOIN `{self.dataset_ref}.cluster_opportunities_summary` c
                    ON p.building_id = c.building_id
                WHERE p.actual_eui IS NOT NULL
            )
            """
        else:
            query = f"""
            CREATE OR REPLACE VIEW `{view_id}` AS
            WITH building_data AS (
                SELECT 
                    p.*,
                    'Unknown' as cluster_category,
                    0 as total_connections,
                    0 as total_heat_recovery_opps,
                    
                    -- Calculate required EUI reduction
                    GREATEST(0, actual_eui - COALESCE(adjusted_final_target, original_final_target)) 
                        as eui_reduction_needed,
                    
                    -- Estimate HVAC tonnage (rough: 400 sqft/ton)
                    ROUND(gross_floor_area / 400, 0) as estimated_hvac_tons,
                    
                    -- Determine retrofit intensity needed
                    CASE 
                        WHEN percent_reduction_needed > 40 THEN 'Deep Retrofit'
                        WHEN percent_reduction_needed > 25 THEN 'Major Retrofit'
                        WHEN percent_reduction_needed > 15 THEN 'Moderate Retrofit'
                        ELSE 'Light Retrofit'
                    END as retrofit_level
                    
                FROM `{self.dataset_ref}.penalty_analysis` p
                WHERE p.actual_eui IS NOT NULL
            )
            """
        
        # Continue with the rest of the query
        query += f""",
        cost_estimates AS (
            SELECT 
                *,
                -- Base retrofit costs by level
                CASE retrofit_level
                    WHEN 'Deep Retrofit' THEN 
                        gross_floor_area * ({self.retrofit_costs['heat_pump_premium']} + 
                                           {self.retrofit_costs['envelope_advanced']} +
                                           {self.retrofit_costs['controls_basic']})
                    WHEN 'Major Retrofit' THEN 
                        gross_floor_area * ({self.retrofit_costs['heat_pump_basic']} + 
                                           {self.retrofit_costs['envelope_basic']} +
                                           {self.retrofit_costs['controls_basic']})
                    WHEN 'Moderate Retrofit' THEN 
                        gross_floor_area * ({self.retrofit_costs['heat_pump_basic']} + 
                                           {self.retrofit_costs['envelope_basic']})
                    ELSE 
                        gross_floor_area * {self.retrofit_costs['heat_pump_basic']}
                END as base_retrofit_cost,
                
                -- Additional costs for special features
                CASE 
                    WHEN cluster_category = 'Prime Heat Recovery' 
                    THEN gross_floor_area * {self.retrofit_costs['thermal_storage']}
                    ELSE 0
                END as thermal_storage_cost,
                
                -- Solar potential (assume 50% of floor area for roof)
                gross_floor_area * 0.5 * {self.retrofit_costs['solar_pv']} as solar_cost_potential
                
            FROM building_data
        ),
        
        incentive_calculations AS (
            SELECT 
                *,
                base_retrofit_cost + thermal_storage_cost as total_project_cost,
                
                -- ITC Calculation
                -- Base 30% + 10% prevailing wage + 10% if in energy community
                (base_retrofit_cost + thermal_storage_cost) * 
                    ({self.itc_base} + {self.itc_bonus_labor} + 
                     CASE WHEN zipcode IN ('80216', '80205', '80239') -- Example energy communities
                     THEN {self.itc_bonus_location} ELSE 0 END) as itc_value,
                
                -- Clean Heat Plan rebate
                estimated_hvac_tons * {self.clean_heat_per_ton} as clean_heat_rebate,
                
                -- Utility rebates (simplified - would be more complex in reality)
                CASE 
                    WHEN property_type IN ('Multifamily Housing', 'Affordable Housing')
                    THEN gross_floor_area * 2.0  -- $2/sqft for residential
                    ELSE gross_floor_area * 1.0   -- $1/sqft for commercial
                END as utility_rebate,
                
                -- Annual energy savings (rough estimate based on EUI reduction)
                eui_reduction_needed * gross_floor_area * 0.10 as annual_energy_savings,
                
                -- Avoided penalties
                annual_penalty_2030 as annual_avoided_penalty
                
            FROM cost_estimates
        )
        
        -- Final financial metrics
        SELECT 
            building_id,
            building_name,
            property_type,
            gross_floor_area,
            actual_eui,
            percent_reduction_needed,
            retrofit_level,
            is_epb,
            cluster_category,
            
            -- Costs
            ROUND(total_project_cost, 0) as total_project_cost,
            ROUND(total_project_cost / gross_floor_area, 2) as cost_per_sqft,
            
            -- Incentives
            ROUND(itc_value, 0) as itc_incentive,
            ROUND(clean_heat_rebate, 0) as clean_heat_rebate,
            ROUND(utility_rebate, 0) as utility_rebate,
            ROUND(itc_value + clean_heat_rebate + utility_rebate, 0) as total_incentives,
            
            -- Net cost
            ROUND(total_project_cost - (itc_value + clean_heat_rebate + utility_rebate), 0) as net_project_cost,
            
            -- Annual benefits
            ROUND(annual_energy_savings, 0) as annual_energy_savings,
            ROUND(annual_avoided_penalty, 0) as annual_avoided_penalty,
            ROUND(annual_energy_savings + annual_avoided_penalty, 0) as total_annual_benefit,
            
            -- ROI Metrics
            CASE 
                WHEN (annual_energy_savings + annual_avoided_penalty) > 0
                THEN ROUND((total_project_cost - (itc_value + clean_heat_rebate + utility_rebate)) / 
                          (annual_energy_savings + annual_avoided_penalty), 1)
                ELSE NULL
            END as simple_payback_years,
            
            -- Project score (for prioritization)
            CASE 
                WHEN (annual_energy_savings + annual_avoided_penalty) > 0
                THEN ROUND(
                    ((annual_energy_savings + annual_avoided_penalty) * 10) / -- 10-year NPV proxy
                    (total_project_cost - (itc_value + clean_heat_rebate + utility_rebate)) *
                    (1 + CASE WHEN is_epb = 1 THEN 0.5 ELSE 0 END) * -- EPB bonus
                    (1 + CASE WHEN cluster_category LIKE '%Heat Recovery%' THEN 0.3 ELSE 0 END), -- Cluster bonus
                    2)
                ELSE 0
            END as project_priority_score
            
        FROM incentive_calculations
        WHERE total_project_cost > 0
        """
        
        print("Creating financial model view...")
        
        try:
            self.bq_client.query(query).result()
            print(f"✓ Created financial model view: {view_id}")
            if not has_cluster_data:
                print("  Note: Running without cluster data. Run cluster analysis first for full insights.")
            return view_id
        except Exception as e:
            print(f"❌ Error creating financial model view: {str(e)}")
            return None
    
    def analyze_portfolio_opportunities(self):
        """Analyze the retrofit portfolio by financial metrics"""
        
        print("\n=== PORTFOLIO FINANCIAL ANALYSIS ===\n")
        
        # Overall portfolio summary
        query = f"""
        SELECT 
            COUNT(*) as total_buildings,
            ROUND(SUM(total_project_cost)/1000000, 1) as total_capex_mm,
            ROUND(SUM(total_incentives)/1000000, 1) as total_incentives_mm,
            ROUND(SUM(net_project_cost)/1000000, 1) as net_capex_mm,
            ROUND(SUM(total_annual_benefit)/1000000, 1) as annual_benefit_mm,
            ROUND(AVG(simple_payback_years), 1) as avg_payback_years,
            COUNT(CASE WHEN simple_payback_years <= 5 THEN 1 END) as projects_under_5yr,
            COUNT(CASE WHEN is_epb = 1 THEN 1 END) as epb_projects
        FROM `{self.dataset_ref}.retrofit_financial_model`
        WHERE simple_payback_years IS NOT NULL
        """
        
        results = self.bq_client.query(query).to_dataframe()
        
        print("Portfolio Summary:")
        print(f"  Total buildings analyzed: {results['total_buildings'].iloc[0]:,}")
        print(f"  Total project cost: ${results['total_capex_mm'].iloc[0]:.1f}M")
        print(f"  Total incentives available: ${results['total_incentives_mm'].iloc[0]:.1f}M")
        print(f"  Net investment needed: ${results['net_capex_mm'].iloc[0]:.1f}M")
        print(f"  Annual savings + avoided penalties: ${results['annual_benefit_mm'].iloc[0]:.1f}M")
        print(f"  Average payback: {results['avg_payback_years'].iloc[0]:.1f} years")
        print(f"  Projects with <5yr payback: {results['projects_under_5yr'].iloc[0]:,}")
        print(f"  EPB projects: {results['epb_projects'].iloc[0]:,}")
        
        # Breakdown by property type
        print("\n\nFinancial Metrics by Property Type:")
        print("-" * 90)
        
        query2 = f"""
        SELECT 
            property_type,
            COUNT(*) as count,
            ROUND(AVG(cost_per_sqft), 2) as avg_cost_per_sqft,
            ROUND(AVG(total_incentives/total_project_cost * 100), 1) as avg_incentive_pct,
            ROUND(AVG(simple_payback_years), 1) as avg_payback,
            ROUND(SUM(net_project_cost)/1000000, 1) as total_net_cost_mm
        FROM `{self.dataset_ref}.retrofit_financial_model`
        WHERE simple_payback_years IS NOT NULL
        GROUP BY property_type
        HAVING count > 5
        ORDER BY total_net_cost_mm DESC
        LIMIT 10
        """
        
        type_results = self.bq_client.query(query2).to_dataframe()
        
        for _, row in type_results.iterrows():
            print(f"{row['property_type']:<25} | "
                  f"{row['count']:>4} bldgs | "
                  f"${row['avg_cost_per_sqft']:>5.2f}/sqft | "
                  f"{row['avg_incentive_pct']:>4.1f}% incentives | "
                  f"{row['avg_payback']:>4.1f}yr payback | "
                  f"${row['total_net_cost_mm']:>6.1f}M total")
    
    def identify_priority_projects(self, top_n=20):
        """Identify the highest priority projects based on financial and social metrics"""
        
        print("\n\n=== TOP PRIORITY RETROFIT PROJECTS ===\n")
        
        query = f"""
        SELECT 
            building_name,
            property_type,
            ROUND(gross_floor_area, 0) as sqft,
            retrofit_level,
            ROUND(total_project_cost/1000, 0) as project_cost_k,
            ROUND(total_incentives/1000, 0) as incentives_k,
            ROUND(net_project_cost/1000, 0) as net_cost_k,
            ROUND(total_annual_benefit/1000, 0) as annual_benefit_k,
            simple_payback_years,
            project_priority_score,
            CASE WHEN is_epb = 1 THEN '✓' ELSE '' END as epb,
            cluster_category
        FROM `{self.dataset_ref}.retrofit_financial_model`
        WHERE project_priority_score > 0
            AND building_name IS NOT NULL
        ORDER BY project_priority_score DESC
        LIMIT {top_n}
        """
        
        priority_projects = self.bq_client.query(query).to_dataframe()
        
        print(f"Top {top_n} Projects by Priority Score:")
        print("-" * 120)
        print(f"{'Building':<30} {'Type':<20} {'SqFt':>8} {'Retrofit':<15} "
              f"{'Cost':>8} {'Incent':>8} {'Net':>8} {'Benefit':>8} {'Payback':>8} {'Score':>7} EPB")
        print("-" * 120)
        
        for _, row in priority_projects.iterrows():
            print(f"{row['building_name'][:30]:<30} "
                  f"{row['property_type'][:20]:<20} "
                  f"{row['sqft']:>8,.0f} "
                  f"{row['retrofit_level']:<15} "
                  f"${row['project_cost_k']:>7.0f}k "
                  f"${row['incentives_k']:>7.0f}k "
                  f"${row['net_cost_k']:>7.0f}k "
                  f"${row['annual_benefit_k']:>7.0f}k "
                  f"{row['simple_payback_years']:>7.1f}y "
                  f"{row['project_priority_score']:>7.1f} "
                  f"{row['epb']:>3}")
    
    def create_investment_scenarios(self):
        """Create different investment scenarios for portfolio planning"""
        
        print("\n\n=== INVESTMENT SCENARIOS ===\n")
        
        scenarios = [
            ("Quick Wins", "simple_payback_years <= 3"),
            ("EPB Focus", "is_epb = 1 AND simple_payback_years <= 7"),
            ("Cluster Development", "cluster_category IN ('Prime Heat Recovery', 'Hub Building')"),
            ("Large Commercial", "property_type = 'Office' AND gross_floor_area > 100000"),
            ("Multifamily Impact", "property_type LIKE '%Multifamily%'")
        ]
        
        print(f"{'Scenario':<20} {'Buildings':>10} {'Total Cost':>12} {'Net Cost':>12} "
              f"{'Annual Benefit':>15} {'Avg Payback':>12} {'EPB Count':>10}")
        print("-" * 110)
        
        for scenario_name, where_clause in scenarios:
            query = f"""
            SELECT 
                COUNT(*) as building_count,
                ROUND(SUM(total_project_cost)/1000000, 1) as total_cost_mm,
                ROUND(SUM(net_project_cost)/1000000, 1) as net_cost_mm,
                ROUND(SUM(total_annual_benefit)/1000000, 1) as annual_benefit_mm,
                ROUND(AVG(simple_payback_years), 1) as avg_payback,
                SUM(CASE WHEN is_epb = 1 THEN 1 ELSE 0 END) as epb_count
            FROM `{self.dataset_ref}.retrofit_financial_model`
            WHERE {where_clause}
                AND simple_payback_years IS NOT NULL
            """
            
            try:
                result = self.bq_client.query(query).to_dataframe()
                
                if not result.empty and result['building_count'].iloc[0] > 0:
                    print(f"{scenario_name:<20} "
                          f"{result['building_count'].iloc[0]:>10,} "
                          f"${result['total_cost_mm'].iloc[0]:>11.1f}M "
                          f"${result['net_cost_mm'].iloc[0]:>11.1f}M "
                          f"${result['annual_benefit_mm'].iloc[0]:>14.1f}M "
                          f"{result['avg_payback'].iloc[0]:>11.1f}y "
                          f"{result['epb_count'].iloc[0]:>10,}")
            except:
                print(f"{scenario_name:<20} No qualifying buildings")
    
    def export_financial_summary(self):
        """Export financial summary for business development"""
        
        table_id = f"{self.dataset_ref}.financial_summary_export"
        
        query = f"""
        CREATE OR REPLACE TABLE `{table_id}` AS
        SELECT 
            building_id,
            building_name,
            property_type,
            gross_floor_area,
            retrofit_level,
            is_epb,
            cluster_category,
            total_project_cost,
            total_incentives,
            net_project_cost,
            total_annual_benefit,
            simple_payback_years,
            project_priority_score,
            
            -- Business development fields
            CASE 
                WHEN simple_payback_years <= 3 THEN 'Immediate'
                WHEN simple_payback_years <= 5 THEN 'Near-term'
                WHEN simple_payback_years <= 7 THEN 'Medium-term'
                ELSE 'Long-term'
            END as development_timeline,
            
            CASE 
                WHEN net_project_cost < 500000 THEN 'Small (<$500k)'
                WHEN net_project_cost < 2000000 THEN 'Medium ($500k-$2M)'
                WHEN net_project_cost < 5000000 THEN 'Large ($2M-$5M)'
                ELSE 'Mega (>$5M)'
            END as project_size,
            
            CURRENT_TIMESTAMP() as analysis_timestamp
            
        FROM `{self.dataset_ref}.retrofit_financial_model`
        WHERE simple_payback_years IS NOT NULL
        ORDER BY project_priority_score DESC
        """
        
        print("\n\nExporting financial summary table...")
        
        self.bq_client.query(query).result()
        print(f"✓ Created export table: {table_id}")
        print("\nThis table can be used for:")
        print("- Looker Studio dashboards")
        print("- Sales team prioritization")
        print("- Investment committee presentations")
        print("- Grant application support")
    
    def run_full_analysis(self):
        """Run the complete financial analysis pipeline"""
        
        print("Starting Retrofit Financial Analysis...")
        print("=" * 80)
        
        # Create financial model view
        view_id = self.create_financial_model_view()
        
        if view_id:
            # Analyze portfolio
            self.analyze_portfolio_opportunities()
            
            # Identify priority projects
            self.identify_priority_projects(top_n=20)
            
            # Create investment scenarios
            self.create_investment_scenarios()
            
            # Export summary
            self.export_financial_summary()
            
            print("\n✅ Financial analysis complete!")
            print("\nKey insights for business development:")
            print("1. Focus on buildings with <5 year payback for quick wins")
            print("2. EPB projects unlock additional funding sources")
            print("3. Cluster projects create economies of scale")
            print("4. ITC can cover 40-50% of project costs with bonuses")


def main():
    """Main execution"""
    model = RetrofitFinancialModel()
    
    try:
        model.run_full_analysis()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
