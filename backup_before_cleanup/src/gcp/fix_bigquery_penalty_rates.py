"""
Suggested File Name: fix_bigquery_penalty_rates.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Update BigQuery scripts to use correct penalty rates

This script updates the opt-in decision model in BigQuery to use:
- $0.15/kBtu for standard path
- $0.23/kBtu for opt-in path (not $0.15)
"""

import os
import re

def fix_bigquery_opt_in_model():
    """Fix the penalty rates in create_opt_in_decision_model.py"""
    
    file_path = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/create_opt_in_decision_model.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check current rates
    print("🔍 Checking current penalty rates in BigQuery script...")
    
    # Find penalty rate definitions
    if "PENALTY_RATE_OPTIN = 0.23" in content:
        print("✅ Opt-in rate is already correct ($0.23/kBtu)")
        rates_correct = True
    else:
        print("❌ Opt-in rate needs to be updated")
        rates_correct = False
    
    # Check penalty calculations
    # Look for opt-in penalty calculations that might use wrong rate
    incorrect_patterns = [
        # Pattern where opt-in uses 0.15 instead of PENALTY_RATE_OPTIN
        r"penalty_2028_optin.*?\*\s*0\.15",
        r"penalty_2032_optin.*?\*\s*0\.15",
        # Pattern where it calculates opt-in with wrong variable
        r"GREATEST\(0,\s*mai_gap_2030\s*\*\s*gross_floor_area\s*\*\s*{self\.PENALTY_RATE_DEFAULT}\)\s*as\s*penalty_2028_optin",
    ]
    
    issues_found = []
    for pattern in incorrect_patterns:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            issues_found.append(pattern)
    
    if issues_found:
        print(f"\n❌ Found {len(issues_found)} incorrect penalty calculations")
        
        # Apply fixes
        replacements = [
            # Fix opt-in penalty calculations to use PENALTY_RATE_OPTIN
            (r"(penalty_2028_optin.*?)\*\s*0\.15", r"\1* {self.PENALTY_RATE_OPTIN}"),
            (r"(penalty_2032_optin.*?)\*\s*0\.15", r"\1* {self.PENALTY_RATE_OPTIN}"),
            
            # Fix the SQL query penalty calculations
            (r"GREATEST\(0,\s*mai_gap_2030\s*\*\s*gross_floor_area\s*\*\s*{self\.PENALTY_RATE_DEFAULT}\)\s*as\s*penalty_2028_optin",
             "GREATEST(0, mai_gap_2030 * gross_floor_area * {self.PENALTY_RATE_OPTIN}) as penalty_2028_optin"),
            (r"GREATEST\(0,\s*mai_gap_2030\s*\*\s*gross_floor_area\s*\*\s*{self\.PENALTY_RATE_DEFAULT}\)\s*as\s*penalty_2032_optin",
             "GREATEST(0, mai_gap_2030 * gross_floor_area * {self.PENALTY_RATE_OPTIN}) as penalty_2032_optin"),
        ]
        
        for old, new in replacements:
            content = re.sub(old, new, content, flags=re.DOTALL)
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ Fixed penalty calculations in BigQuery script")
        return True
    
    elif not rates_correct:
        print("⚠️  Rates need updating but calculations appear correct")
        return False
    else:
        print("✅ All penalty calculations appear correct")
        return True

def verify_bigquery_compliance():
    """Verify the penalty analysis corrected script"""
    
    file_path = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/create_penalty_analysis_corrected.py"
    
    if not os.path.exists(file_path):
        print(f"\n❌ File not found: {file_path}")
        return
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("\n🔍 Checking create_penalty_analysis_corrected.py...")
    
    # This file should already be correct
    if "PENALTY_RATE_DEFAULT = 0.15" in content and "PENALTY_RATE_OPTIN = 0.23" in content:
        print("✅ Penalty rates are correct in this file")
    else:
        print("❌ This file also needs rate corrections")

def create_summary_report():
    """Create a summary of all BigQuery updates needed"""
    
    summary = """
# BigQuery Penalty Rate Update Summary

## Files to Update:

### 1. create_opt_in_decision_model.py
- **Issue**: Uses $0.15/kBtu for BOTH standard and opt-in paths in calculations
- **Fix**: Update opt-in calculations to use $0.23/kBtu (PENALTY_RATE_OPTIN)
- **Impact**: Opt-in decisions will change significantly

### 2. create_penalty_analysis_corrected.py  
- **Status**: Already has correct rates defined
- **Verify**: Calculations use the correct variables

## SQL Query Updates Needed:

Replace in financial_analysis CTE:
```sql
-- OLD (WRONG):
GREATEST(0, mai_gap_2030 * gross_floor_area * 0.15) as penalty_2028_optin

-- NEW (CORRECT):
GREATEST(0, mai_gap_2030 * gross_floor_area * 0.23) as penalty_2028_optin
```

## Testing After Updates:

1. Re-run opt-in decision analysis
2. Verify NPV calculations reflect higher opt-in penalties
3. Check that fewer buildings are recommended to opt-in
4. Validate against manual calculations for Building 2952

## Expected Impact:

With correct $0.23/kBtu rate for opt-in:
- Opt-in penalties increase by 53%
- NPV advantage of opt-in decreases
- More buildings should stay on standard path
- Decision confidence scores may change
"""
    
    report_path = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/docs/bigquery_penalty_update_summary.md"
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(summary)
    
    print(f"\n📝 Created summary report: {report_path}")

def main():
    """Main execution"""
    print("🔧 BIGQUERY PENALTY RATE CORRECTION")
    print("=" * 60)
    print("This script fixes opt-in penalty rates in BigQuery scripts")
    print("Correct rates: Standard=$0.15/kBtu, Opt-in=$0.23/kBtu\n")
    
    # Fix the opt-in model
    success = fix_bigquery_opt_in_model()
    
    # Verify other scripts
    verify_bigquery_compliance()
    
    # Create summary
    create_summary_report()
    
    if success:
        print("\n✅ BigQuery scripts updated successfully!")
        print("\nNext steps:")
        print("1. Review the changes in create_opt_in_decision_model.py")
        print("2. Re-run the BigQuery analysis")
        print("3. Compare results with previous analysis")
        print("4. Update any dependent views or tables")
    else:
        print("\n⚠️  Some updates may still be needed")
        print("Please review the files manually")

if __name__ == "__main__":
    main()
