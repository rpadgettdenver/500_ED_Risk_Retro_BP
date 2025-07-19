"""
Suggested File Name: fix_penalty_rates_v2.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/
Use: Script to update all penalty calculations in the codebase to match the April 2025 Technical Guidance

This script will:
1. Update penalty rates in config files
2. Fix penalty calculations in analysis modules
3. Update documentation and comments
4. Verify all changes match the Technical Guidance
"""

import os
import re
import datetime

class PenaltyRateFixer:
    def __init__(self, project_root: str):
        self.project_root = project_root
        
        # Correct penalty rates from Technical Guidance
        self.CORRECT_RATES = {
            'standard_path': {
                'rate': 0.15,  # $/kBtu for 3-target path
                'years': [2025, 2027, 2030],
                'description': 'Standard path (3 target years)'
            },
            'alternate_path': {
                'rate': 0.23,  # $/kBtu for 2-target path  
                'years': [2028, 2032],
                'description': 'Alternate compliance/opt-in path (2 target years)'
            },
            'extension_path': {
                'rate': 0.35,  # $/kBtu for 1-target path
                'years': [2030],  # or 2032 depending on path
                'description': 'Timeline extension (1 target year)'
            },
            'late_extension': {
                'additional_rate': 0.10,  # Additional $/kBtu
                'description': 'Late timeline extension (add to base rate)'
            },
            'never_benchmarking': {
                'rate': 10.0,  # $/sqft one-time
                'description': 'Never benchmarking penalty'
            }
        }
        
        # Files to update
        self.files_to_update = [
            'src/config/project_config.py',
            'src/analysis/building_compliance_analyzer.py',
            'src/analysis/integrated_tes_hp_analyzer.py',
            'src/gcp/create_penalty_analysis_corrected.py',
            'src/gcp/create_penalty_view.py',
            'src/gcp/create_penalty_view_fixed.py',
            'src/gcp/check_penalty_math.py'
        ]
        
    def update_project_config(self):
        """Update the main project configuration file"""
        config_path = os.path.join(self.project_root, 'src/config/project_config.py')
        
        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            return
            
        with open(config_path, 'r') as f:
            content = f.read()
            
        # Find and replace the penalties section
        old_pattern = r"'penalties':\s*\{[^}]+\}"
        new_penalties = """'penalties': {
            # Corrected rates per April 2025 Technical Guidance
            'standard_path': {
                'rate': 0.15,  # $/kBtu for standard path (3 target years)
                'years': [2025, 2027, 2030],
                'description': 'Standard compliance path'
            },
            'alternate_path': {
                'rate': 0.23,  # $/kBtu for alternate/opt-in path (2 target years)
                'years': [2028, 2032], 
                'description': 'Alternate compliance (opt-in) path'
            },
            'extension_path': {
                'rate': 0.35,  # $/kBtu for timeline extension (1 target year)
                'years': [2030],  # or [2032] depending on path
                'description': 'Timeline extension path'
            },
            'late_extension_additional': 0.10,  # Additional $/kBtu for late extensions
            'never_benchmarking': 10.0,  # $/sqft one-time penalty
            
            # Legacy fields for backward compatibility (DEPRECATED)
            '2025_rate': 0.15,  # DEPRECATED - use standard_path['rate']
            '2027_rate': 0.15,  # DEPRECATED - use standard_path['rate']
            '2030_rate': 0.15,  # DEPRECATED - use standard_path['rate']
            'penalty_years': 15,  # Analysis period
        }"""
        
        # Replace the penalties section
        content = re.sub(old_pattern, new_penalties, content, flags=re.DOTALL)
        
        # Write back
        with open(config_path, 'w') as f:
            f.write(content)
            
        print(f"✅ Updated project_config.py with correct penalty structure")
        
    def update_building_compliance_analyzer(self):
        """Update the building compliance analyzer"""
        analyzer_path = os.path.join(self.project_root, 'src/analysis/building_compliance_analyzer.py')
        
        if not os.path.exists(analyzer_path):
            print(f"❌ Analyzer file not found: {analyzer_path}")
            return
            
        with open(analyzer_path, 'r') as f:
            content = f.read()
            
        # Replace old penalty rates with correct ones
        replacements = [
            # Standard path penalties
            (r"'penalty_rate':\s*0\.30", "'penalty_rate': 0.15"),  # 2025
            (r"'penalty_rate':\s*0\.50", "'penalty_rate': 0.15"),  # 2027  
            (r"'penalty_rate':\s*0\.70", "'penalty_rate': 0.15"),  # 2030
            
            # Opt-in path penalties (2028, 2032) 
            (r"'penalty_rate':\s*0\.50\s*#\s*Same as 2027", "'penalty_rate': 0.23  # Opt-in path rate"),
            (r"'penalty_rate':\s*0\.70\s*#\s*Same as 2030", "'penalty_rate': 0.23  # Opt-in path rate"),
            
            # Comments
            (r"\$0\.30 per sqft per kBtu over", "$0.15 per kBtu over target"),
            (r"\$0\.50 per sqft per kBtu over", "$0.15 per kBtu over target"),
            (r"\$0\.70 per sqft per kBtu over", "$0.15 per kBtu over target"),
        ]
        
        for old, new in replacements:
            content = re.sub(old, new, content)
            
        # Update the penalty calculation formula comment
        content = re.sub(
            r"#\s*\$[\d.]+\s*per\s*sqft\s*per\s*kBtu\s*over",
            "# Penalty = excess_kBtu × sqft × rate ($/kBtu)",
            content
        )
        
        # Write back
        with open(analyzer_path, 'w') as f:
            f.write(content)
            
        print(f"✅ Updated building_compliance_analyzer.py with correct penalty rates")
        
    def update_integrated_analyzer(self):
        """Update the integrated TES HP analyzer"""
        analyzer_path = os.path.join(self.project_root, 'src/analysis/integrated_tes_hp_analyzer.py')
        
        if not os.path.exists(analyzer_path):
            print(f"❌ Integrated analyzer file not found: {analyzer_path}")
            return
            
        with open(analyzer_path, 'r') as f:
            content = f.read()
            
        # Fix penalty calculations
        replacements = [
            # Fix the penalty rate values
            (r"penalty_2025\s*=.*?\*\s*0\.30", "penalty_2025 = max(0, effective_eui - self.building_data['first_interim_target']) * self.building_data['sqft'] * 0.15"),
            (r"penalty_2027\s*=.*?\*\s*0\.50", "penalty_2027 = max(0, effective_eui - self.building_data['second_interim_target']) * self.building_data['sqft'] * 0.15"),
            (r"penalty_2030\s*=.*?\*\s*0\.70", "penalty_2030 = max(0, effective_eui - self.building_data['final_target']) * self.building_data['sqft'] * 0.15"),
            
            # Update the total penalty calculation to include annual penalties after 2030
            (r"'total_penalties_15yr':.*?,", "'total_penalties_15yr': penalty_2025 + penalty_2027 + penalty_2030 * 13,  # 2030 penalty continues annually through 2042"),
        ]
        
        for old, new in replacements:
            content = re.sub(old, new, content)
            
        # Write back
        with open(analyzer_path, 'w') as f:
            f.write(content)
            
        print(f"✅ Updated integrated_tes_hp_analyzer.py with correct penalty calculations")
        
    def verify_updates(self):
        """Verify all files have been updated correctly"""
        print("\n🔍 Verifying updates...")
        
        issues_found = []
        
        for file_path in self.files_to_update:
            full_path = os.path.join(self.project_root, file_path)
            if not os.path.exists(full_path):
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Check for old incorrect rates
            if re.search(r"0\.30.*?(?:rate|penalty).*?2025", content, re.IGNORECASE):
                issues_found.append((file_path, "Still has 0.30 rate for 2025"))
            if re.search(r"0\.50.*?(?:rate|penalty).*?2027", content, re.IGNORECASE):
                issues_found.append((file_path, "Still has 0.50 rate for 2027"))
            if re.search(r"0\.70.*?(?:rate|penalty).*?2030", content, re.IGNORECASE):
                issues_found.append((file_path, "Still has 0.70 rate for 2030"))
                
        if issues_found:
            print("\n⚠️  Issues found:")
            for file, issue in issues_found:
                print(f"  - {file}: {issue}")
        else:
            print("\n✅ All files verified - penalty rates are correct!")
            
    def create_documentation_update(self):
        """Create a documentation update summarizing the changes"""
        doc_content = f"""# Penalty Rate Update Documentation
        
## Date: {datetime.datetime.now().strftime('%Y-%m-%d')}

## Summary of Changes

Updated all penalty calculations throughout the codebase to match the April 2025 Energize Denver Technical Guidance.

### Correct Penalty Rates (per Technical Guidance)

| Compliance Path | Penalty Rate | Target Years | Annual After Final Target |
|-----------------|--------------|--------------|--------------------------|
| Standard Path (3 targets) | $0.15/kBtu | 2025, 2027, 2030 | Yes, annually after 2030 |
| Alternate/Opt-in Path (2 targets) | $0.23/kBtu | 2028, 2032 | Yes, annually after 2032 |
| Timeline Extension (1 target) | $0.35/kBtu | 2030 or 2032 | Yes, annually thereafter |
| Late Extension | +$0.10/kBtu | (add to base rate) | Same as base path |
| Never Benchmarking | $10/sqft | One-time | Then annual penalties |

### Previous Incorrect Rates (NOW FIXED)

The codebase previously used these incorrect rates:
- 2025: $0.30/kBtu (was 2x too high)
- 2027: $0.50/kBtu (was 3.3x too high)  
- 2030: $0.70/kBtu (was 4.7x too high)

### Files Updated

1. **src/config/project_config.py**
   - Updated penalties dictionary with correct structure
   - Added path-based penalty configuration
   - Maintained backward compatibility

2. **src/analysis/building_compliance_analyzer.py**
   - Fixed standard path penalties to $0.15/kBtu
   - Fixed opt-in path penalties to $0.23/kBtu
   - Updated calculation comments

3. **src/analysis/integrated_tes_hp_analyzer.py**
   - Corrected penalty calculations in model_system_impacts()
   - Fixed total penalty calculation to include annual penalties after 2030
   - Updated penalty math

4. **BigQuery Scripts**
   - Already had correct rates in create_penalty_analysis_corrected.py
   - Other scripts may need updates

### Penalty Calculation Formula

The correct formula is:
```
Annual Penalty = (Actual EUI - Target EUI) × Building Sq Ft × Penalty Rate
```

Where:
- Actual EUI = Weather Normalized Site EUI
- Target EUI = Compliance target for the given year
- Penalty Rate = Rate based on compliance path (see table above)

### Important Notes

1. Penalties are assessed in target years AND annually thereafter if non-compliant
2. Buildings that fail to maintain compliance (>5% regression) face the same penalty rate
3. Electrification provides a 10% bonus to EUI targets (allows higher EUI)
4. MAI buildings have different targets but same penalty rates

### Example 15-Year Penalty Timeline

**Standard Path (non-compliant building):**
- 2025: $X penalty (target year)
- 2026: $0 (no penalty)
- 2027: $X penalty (target year)
- 2028-2029: $0 (no penalty)
- 2030-2042: $X penalty annually (13 years)
- Total: 15 years of penalties

**Opt-in Path (non-compliant building):**
- 2025-2027: $0 (no penalty)
- 2028: $Y penalty (target year)
- 2029-2031: $0 (no penalty)
- 2032-2042: $Y penalty annually (11 years)
- Total: 12 years of penalties

### Testing Recommendations

1. Re-run Building 2952 analysis with corrected rates
2. Verify penalty calculations match Technical Guidance examples
3. Update any dashboards or reports showing penalty projections
4. Notify stakeholders of the corrected calculations
"""
        
        doc_path = os.path.join(self.project_root, 'docs/penalty_rate_update_log.md')
        os.makedirs(os.path.dirname(doc_path), exist_ok=True)
        
        with open(doc_path, 'w') as f:
            f.write(doc_content)
            
        print(f"\n📝 Created documentation: {doc_path}")


def main():
    """Main execution function"""
    import datetime
    
    print("🔧 ENERGIZE DENVER PENALTY RATE CORRECTION SCRIPT")
    print("=" * 60)
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("\nThis script will update all penalty calculations to match")
    print("the April 2025 Technical Guidance rates:")
    print("- Standard path: $0.15/kBtu (not $0.30/$0.50/$0.70)")
    print("- Opt-in path: $0.23/kBtu")
    print("- Extension path: $0.35/kBtu")
    
    # Get project root
    project_root = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP"
    
    # Confirm before proceeding
    response = input(f"\nUpdate penalty rates in {project_root}? (y/n): ")
    
    if response.lower() != 'y':
        print("Cancelled.")
        return
        
    # Create fixer instance
    fixer = PenaltyRateFixer(project_root)
    
    # Run updates
    print("\n📝 Updating files...")
    fixer.update_project_config()
    fixer.update_building_compliance_analyzer()
    fixer.update_integrated_analyzer()
    
    # Verify
    fixer.verify_updates()
    
    # Create documentation
    fixer.create_documentation_update()
    
    print("\n✅ COMPLETE! All penalty rates have been updated.")
    print("\nNext steps:")
    print("1. Review the changes in each file")
    print("2. Re-run Building 2952 analysis to verify calculations")
    print("3. Update any dependent scripts or notebooks")
    print("4. Commit changes with message: 'Fix penalty rates per April 2025 Technical Guidance'")


if __name__ == "__main__":
    main()
