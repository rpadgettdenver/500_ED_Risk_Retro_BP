# Suggested File Name: mai_penalty_debugger.py
# Directory Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
# USE: Diagnose MAI data quality issues and verify penalty calculation logic

import pandas as pd
import os
from pathlib import Path

def load_mai_data():
    """
    Load and merge MAI property and target data files
    
    Returns:
        pd.DataFrame: Merged MAI data with all relevant columns
    """
    try:
        # Define the base directory - adjust path to find data files
        base_dir = Path(__file__).parent
        data_dir = base_dir / 'data' / 'raw'
        
        # Load both MAI CSV files from the correct location
        property_file = data_dir / 'MAIPropertyUseTypes Report.csv'
        target_file = data_dir / 'MAITargetSummary Report.csv'
        
        print(f"Looking for files in: {data_dir}")
        print(f"Property file exists: {property_file.exists()}")
        print(f"Target file exists: {target_file.exists()}")
        
        property_df = pd.read_csv(property_file)
        target_df = pd.read_csv(target_file)
        
        print(f"Property data loaded: {len(property_df)} rows")
        print(f"Target data loaded: {len(target_df)} rows")
        
        # Merge on Building ID
        merged_df = pd.merge(
            target_df, 
            property_df[['Building ID', 'Master Property Type', 'Building Name']], 
            on='Building ID', 
            how='left'
        )
        
        print(f"Merged data: {len(merged_df)} rows")
        
        return merged_df
        
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")
        return None
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        return None

def analyze_mai_buildings(df):
    """
    Analyze MAI building data to identify penalty calculation issues
    
    Args:
        df (pd.DataFrame): Merged MAI data
    
    Returns:
        dict: Analysis results with key findings
    """
    if df is None:
        return None
    
    # Filter to MAI approved buildings only
    mai_df = df[df['Approved Mai'] == 'Yes'].copy()
    
    print(f"\n=== MAI BUILDINGS ANALYSIS ===")
    print(f"Total MAI approved buildings: {len(mai_df)}")
    
    # Timeline analysis
    timeline_counts = mai_df.groupby(['Interim Target Year', 'Final Target Year']).size()
    print(f"\nTimeline Distribution:")
    for (interim, final), count in timeline_counts.items():
        print(f"  {interim}-{final}: {count} buildings")
    
    # Status analysis
    status_counts = mai_df['Building Status'].value_counts()
    print(f"\nBuilding Status Distribution:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} buildings")
    
    # Critical: Buildings with performance gaps (should trigger penalties)
    gap_buildings = mai_df[
        (mai_df['Percent Above or Below Next Target'] > 0) |
        (mai_df['Percent Above or Below Final Target'] > 0)
    ].copy()
    
    zero_gap_buildings = mai_df[
        (mai_df['Percent Above or Below Next Target'] == 0) &
        (mai_df['Percent Above or Below Final Target'] == 0)
    ].copy()
    
    print(f"\nPerformance Gap Analysis:")
    print(f"  Buildings with performance gaps (penalty eligible): {len(gap_buildings)}")
    print(f"  Buildings with zero gaps (potential issue source): {len(zero_gap_buildings)}")
    
    # Focus on 2028-2032 timeline (main MAI timeline)
    timeline_2028 = mai_df[
        (mai_df['Interim Target Year'] == 2028) & 
        (mai_df['Final Target Year'] == 2032)
    ].copy()
    
    penalty_eligible_2028 = timeline_2028[
        timeline_2028['Percent Above or Below Next Target'] > 0
    ].copy()
    
    print(f"\n2028-2032 Timeline Analysis:")
    print(f"  Total buildings: {len(timeline_2028)}")
    print(f"  Penalty eligible (above target): {len(penalty_eligible_2028)}")
    
    # Show specific buildings that should have penalties
    if len(penalty_eligible_2028) > 0:
        print(f"\nBuildings that SHOULD have penalties:")
        for idx, row in penalty_eligible_2028.head(10).iterrows():
            print(f"  Building ID: {row['Building ID']}, "
                  f"Gap: {row['Percent Above or Below Next Target']:.1f}%, "
                  f"Status: {row['Building Status']}")
    
    return {
        'total_mai': len(mai_df),
        'gap_buildings': gap_buildings,
        'zero_gap_buildings': zero_gap_buildings,
        'timeline_2028': timeline_2028,
        'penalty_eligible_2028': penalty_eligible_2028,
        'timeline_counts': timeline_counts,
        'status_counts': status_counts
    }

def validate_penalty_calculations(analysis_results):
    """
    Validate penalty calculation logic against actual MAI data
    
    Args:
        analysis_results (dict): Results from analyze_mai_buildings()
    """
    if analysis_results is None:
        return
    
    penalty_buildings = analysis_results['penalty_eligible_2028']
    
    print(f"\n=== PENALTY CALCULATION VALIDATION ===")
    print(f"Buildings that SHOULD have penalties calculated: {len(penalty_buildings)}")
    
    # Show top 5 buildings with penalties
    for idx, row in penalty_buildings.head(5).iterrows():
        building_id = row['Building ID']
        current_usage = row['Current FF Usage']
        baseline = row['Baseline Value']
        target_2028 = row['Interim Target']
        gap_percent = row['Percent Above or Below Next Target']
        
        print(f"\nBuilding ID: {building_id}")
        print(f"  Building Name: {row.get('Building Name', 'N/A')}")
        print(f"  Current FF Usage: {current_usage:,.0f} kBtu" if pd.notna(current_usage) else "  Current FF Usage: N/A")
        print(f"  2028 Target EUI: {target_2028}" if pd.notna(target_2028) else "  2028 Target EUI: N/A")
        print(f"  Gap above target: {gap_percent:.1f}%")
        
        # Note: Actual penalty calculation would need building square footage
        # to convert between total usage and EUI
        if pd.notna(current_usage) and pd.notna(target_2028) and target_2028 > 0:
            # This is a simplified estimate - actual calculation needs square footage
            penalty_rate = 0.23  # $0.23/kBtu
            # We'd need: penalty = (current_eui - target_eui) * sq_ft * penalty_rate
            print(f"  Note: Penalty calculation requires building square footage")

def identify_zero_penalty_issues(analysis_results):
    """
    Identify why many MAI buildings show zero penalties
    
    Args:
        analysis_results (dict): Results from analyze_mai_buildings()
    """
    if analysis_results is None:
        return
    
    zero_gap_buildings = analysis_results['zero_gap_buildings']
    timeline_2028_zeros = zero_gap_buildings[
        (zero_gap_buildings['Interim Target Year'] == 2028) &
        (zero_gap_buildings['Final Target Year'] == 2032)
    ]
    
    print(f"\n=== ZERO PENALTY ISSUE DIAGNOSIS ===")
    print(f"2028-2032 buildings with zero gaps: {len(timeline_2028_zeros)}")
    
    # Check for data quality issues
    missing_usage = timeline_2028_zeros[
        (timeline_2028_zeros['Current FF Usage'].isna()) |
        (timeline_2028_zeros['Current FF Usage'] == 0)
    ]
    
    missing_targets = timeline_2028_zeros[
        (timeline_2028_zeros['Interim Target'].isna()) |
        (timeline_2028_zeros['Interim Target'] == 0)
    ]
    
    print(f"\nPotential Data Issues:")
    print(f"  Buildings with missing/zero Current FF Usage: {len(missing_usage)}")
    print(f"  Buildings with missing/zero Interim Target: {len(missing_targets)}")
    
    # Sample zero-gap buildings for manual inspection
    if len(timeline_2028_zeros) > 0:
        print(f"\nSample zero-gap buildings (first 5):")
        for idx, row in timeline_2028_zeros.head().iterrows():
            print(f"  ID: {row['Building ID']}, "
                  f"Usage: {row['Current FF Usage']:.0f}" if pd.notna(row['Current FF Usage']) else "N/A", 
                  f", Target: {row['Interim Target']}" if pd.notna(row['Interim Target']) else "N/A",
                  f", Status: {row['Building Status']}")

def generate_mai_penalty_checklist(analysis_results):
    """
    Generate a checklist for fixing MAI penalty calculations
    """
    print(f"\n=== MAI PENALTY CALCULATION CHECKLIST ===")
    print(f"Based on data analysis, check these items in your code:")
    print(f"")
    print(f"1. MAI Building Identification:")
    print(f"   □ Filter buildings where 'Approved Mai' == 'Yes'")
    
    if analysis_results:
        timeline_2028 = analysis_results.get('timeline_2028', pd.DataFrame())
        penalty_eligible = analysis_results.get('penalty_eligible_2028', pd.DataFrame())
        print(f"   □ Focus on 2028-2032 timeline buildings ({len(timeline_2028)} total)")
        if len(penalty_eligible) > 0:
            building_ids = penalty_eligible['Building ID'].head(5).tolist()
            print(f"   □ Building IDs that should have penalties: {', '.join(map(str, building_ids))}")
    
    print(f"")
    print(f"2. Timeline Logic:")
    print(f"   □ Use 'Interim Target Year' (2028) for current penalty calculations")
    print(f"   □ Use 'Final Target Year' (2032) for future projections")
    print(f"   □ Penalty rate: $0.23/kBtu")
    print(f"")
    print(f"3. EUI Gap Calculation:")
    print(f"   □ Current EUI vs 'Interim Target' (2028)")
    print(f"   □ Use 'Current FF Usage' as current consumption")
    print(f"   □ Positive 'Percent Above or Below Next Target' = penalty situation")
    print(f"   □ Need building square footage to convert total usage to EUI")
    print(f"")
    print(f"4. Data Quality Checks:")
    print(f"   □ Handle buildings with zero 'Current FF Usage'")
    print(f"   □ Verify building square footage for EUI calculations")
    print(f"   □ Check why many buildings show 0% performance gaps")
    print(f"")
    print(f"5. Code Debugging:")
    print(f"   □ Add logging for MAI building filtering")
    print(f"   □ Print intermediate calculations for penalty-eligible buildings")
    print(f"   □ Verify join/merge operations preserve MAI flags")
    print(f"   □ Ensure file paths are correct relative to script location")

def main():
    """
    Main diagnostic function
    """
    print("MAI Penalty Calculation Diagnostic Tool")
    print("=" * 50)
    
    # Load and analyze MAI data
    df = load_mai_data()
    if df is None:
        print("\nFailed to load data. Please check file paths.")
        return
    
    analysis_results = analyze_mai_buildings(df)
    
    # Validate penalty calculations
    validate_penalty_calculations(analysis_results)
    
    # Identify zero penalty issues
    identify_zero_penalty_issues(analysis_results)
    
    # Generate checklist
    generate_mai_penalty_checklist(analysis_results)
    
    print(f"\n" + "=" * 50)
    print(f"Diagnostic complete. Use this analysis to fix your penalty calculation code.")

if __name__ == "__main__":
    main()