"""
Suggested File Name: check_penalty_math.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Debug the penalty calculations to understand why they're so high

This script will:
1. Look at specific building examples
2. Show the math step by step
3. Check against the technical guidance rules
"""

from google.cloud import bigquery
import pandas as pd

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

def check_penalty_calculations():
    """Check the penalty math for specific buildings"""
    
    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    
    print("=== CHECKING PENALTY CALCULATION MATH ===\n")
    
    # First, let's look at the "ready foods" building that shows $10M penalty
    query = f"""
    SELECT 
        building_id,
        building_name,
        property_type,
        gross_floor_area,
        actual_eui,
        first_interim_target,
        adjusted_final_target,
        original_final_target,
        interim_gap,
        compliance_path,
        annual_penalty_2024,
        -- Show the calculation components
        ROUND(gross_floor_area, 0) as sqft,
        ROUND(actual_eui, 1) as current_eui,
        ROUND(first_interim_target, 1) as target_2024,
        ROUND(actual_eui - first_interim_target, 1) as eui_gap,
        ROUND((actual_eui - first_interim_target) * gross_floor_area, 0) as total_kbtu_over,
        CASE 
            WHEN compliance_path = 'Default (2024/2030)' THEN 0.15
            ELSE 0.23
        END as penalty_rate
    FROM `{dataset_ref}.penalty_analysis`
    WHERE building_name LIKE '%ready foods%'
    ORDER BY annual_penalty_2024 DESC
    LIMIT 5
    """
    
    results = client.query(query).to_dataframe()
    
    print("Example: Ready Foods Building")
    print("-" * 80)
    
    for idx, row in results.iterrows():
        print(f"\nBuilding: {row['building_name']}")
        print(f"Square Footage: {row['sqft']:,.0f}")
        print(f"Current EUI: {row['current_eui']:.1f} kBtu/sqft/year")
        print(f"2024 Target EUI: {row['target_2024']:.1f} kBtu/sqft/year")
        print(f"EUI Gap: {row['eui_gap']:.1f} kBtu/sqft/year")
        print(f"Total kBtu over target: {row['total_kbtu_over']:,.0f} kBtu/year")
        print(f"Penalty rate: ${row['penalty_rate']:.2f} per kBtu")
        print(f"Annual penalty: ${row['annual_penalty_2024']:,.2f}")
        
        # Manual calculation check
        manual_calc = row['eui_gap'] * row['sqft'] * row['penalty_rate']
        print(f"Manual calculation: {row['eui_gap']:.1f} × {row['sqft']:,.0f} × ${row['penalty_rate']:.2f} = ${manual_calc:,.2f}")
    
    # Check for data issues - multiple years?
    print("\n\n=== CHECKING FOR DUPLICATE BUILDINGS ===")
    
    dup_query = f"""
    SELECT 
        building_name,
        COUNT(*) as record_count,
        COUNT(DISTINCT building_id) as unique_ids,
        MIN(actual_eui) as min_eui,
        MAX(actual_eui) as max_eui,
        SUM(annual_penalty_2024) as total_penalties
    FROM `{dataset_ref}.penalty_analysis`
    WHERE building_name IS NOT NULL
    GROUP BY building_name
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 10
    """
    
    duplicates = client.query(dup_query).to_dataframe()
    
    if not duplicates.empty:
        print("\nBuildings appearing multiple times:")
        for _, row in duplicates.iterrows():
            print(f"{row['building_name'][:40]:<40} | {row['record_count']} records | "
                  f"EUI range: {row['min_eui']:.0f}-{row['max_eui']:.0f} | "
                  f"Total penalties: ${row['total_penalties']:,.0f}")
    
    # Check the actual data in building_consumption
    print("\n\n=== CHECKING SOURCE DATA ===")
    
    source_query = f"""
    SELECT 
        building_id,
        building_name,
        COUNT(*) as year_count,
        MIN(CAST(building_id AS STRING)) as min_year,
        MAX(CAST(building_id AS STRING)) as max_year,
        AVG(actual_eui) as avg_eui
    FROM `{dataset_ref}.building_consumption`
    WHERE building_name LIKE '%ready foods%'
    GROUP BY building_id, building_name
    """
    
    source_data = client.query(source_query).to_dataframe()
    print("\nSource data for Ready Foods:")
    print(source_data)
    
    # Summary statistics
    print("\n\n=== PENALTY DISTRIBUTION ===")
    
    dist_query = f"""
    SELECT 
        CASE 
            WHEN annual_penalty_2024 = 0 THEN '0. No Penalty'
            WHEN annual_penalty_2024 < 10000 THEN '1. Under $10K'
            WHEN annual_penalty_2024 < 50000 THEN '2. $10K - $50K'
            WHEN annual_penalty_2024 < 100000 THEN '3. $50K - $100K'
            WHEN annual_penalty_2024 < 500000 THEN '4. $100K - $500K'
            WHEN annual_penalty_2024 < 1000000 THEN '5. $500K - $1M'
            ELSE '6. Over $1M'
        END as penalty_range,
        COUNT(*) as building_count,
        SUM(annual_penalty_2024) as total_penalties
    FROM `{dataset_ref}.penalty_analysis`
    GROUP BY penalty_range
    ORDER BY penalty_range
    """
    
    distribution = client.query(dist_query).to_dataframe()
    
    print("\nPenalty Distribution:")
    for _, row in distribution.iterrows():
        print(f"{row['penalty_range']:<20} | {row['building_count']:>6,} buildings | ${row['total_penalties']:>15,.0f}")
    
    # Check the technical guidance rules
    print("\n\n=== TECHNICAL GUIDANCE RULES CHECK ===")
    print("\nAccording to the guidance:")
    print("- Penalty = $0.15/kBtu over target (default path)")
    print("- Penalty = $0.23/kBtu over target (opt-in path)")
    print("- Buildings ≥25,000 sqft are covered")
    print("- Some buildings may be exempt")
    print("- Penalties apply to the gap between actual and target EUI")
    
    # Let's check what might be wrong
    print("\n\n=== POTENTIAL ISSUES ===")
    
    # Issue 1: Are we counting each year as a separate building?
    year_check_query = f"""
    SELECT 
        COUNT(DISTINCT building_id) as unique_buildings,
        COUNT(*) as total_records
    FROM `{dataset_ref}.penalty_analysis`
    """
    
    year_check = client.query(year_check_query).to_dataframe()
    print(f"\nUnique buildings: {year_check['unique_buildings'].iloc[0]:,}")
    print(f"Total records: {year_check['total_records'].iloc[0]:,}")
    
    if year_check['total_records'].iloc[0] > year_check['unique_buildings'].iloc[0]:
        print("⚠️  WARNING: We have more records than buildings - likely counting multiple years!")


def check_technical_guidance():
    """Review key rules from the technical guidance"""
    
    print("\n\n=== KEY RULES FROM TECHNICAL GUIDANCE ===")
    print("\n1. PENALTY CALCULATION:")
    print("   - Penalty = (Actual EUI - Target EUI) × Gross Floor Area × Penalty Rate")
    print("   - Default path: $0.15 per kBtu")
    print("   - Opt-in path: $0.23 per kBtu")
    print("\n2. COVERED BUILDINGS:")
    print("   - ≥ 25,000 square feet")
    print("   - Commercial and multifamily")
    print("   - Some exemptions apply")
    print("\n3. TIMELINE:")
    print("   - 2024: First interim target")
    print("   - 2027: Second interim target (default path)")
    print("   - 2030: Final target")
    print("\n4. OPT-IN ALTERNATIVE:")
    print("   - 2028: First target (instead of 2024)")
    print("   - 2032: Final target (instead of 2030)")
    print("   - Higher penalty rate but more time")


def main():
    """Main execution"""
    
    # Check the math
    check_penalty_calculations()
    
    # Review technical guidance
    check_technical_guidance()
    
    print("\n\n=== DIAGNOSIS ===")
    print("\nThe $38 billion penalty is likely due to:")
    print("1. Counting multiple years of data per building (duplicates)")
    print("2. Using raw Site EUI instead of Weather Normalized Site EUI")
    print("3. Not filtering for the most recent reporting year")
    print("\nRun the create_penalty_view_fixed.py script to fix these issues!")


if __name__ == "__main__":
    main()
