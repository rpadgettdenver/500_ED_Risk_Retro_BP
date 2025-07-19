"""
Fix penalty calculations based on Energize Denver Technical Guidance v3.0

This script updates all penalty calculations to use the correct rates:
- Standard Path (3 targets): $0.15/kBtu
- Alternate Path (2 targets): $0.23/kBtu  
- Extension Path (1 target): $0.35/kBtu
"""

import os
import sys

# Add src to path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from config import get_config, update_config

# Fix the configuration
print("Updating penalty rates to match ED Technical Guidance...")

update_config({
    'penalties': {
        'standard_rate': 0.15,      # $/kBtu for 3-target path (2025, 2027, 2030)
        'alternate_rate': 0.23,     # $/kBtu for 2-target path (2028, 2032)
        'extension_rate': 0.35,     # $/kBtu for 1-target path
        'penalty_years': 15,        # Analysis period
        # Keep old keys for backward compatibility but mark as deprecated
        '2025_rate': 0.15,  # DEPRECATED - use standard_rate
        '2027_rate': 0.15,  # DEPRECATED - use standard_rate  
        '2030_rate': 0.15,  # DEPRECATED - use standard_rate
    }
})

config = get_config()

# Show the corrected penalty calculations for Building 2952
building = config.config['building']
current_eui = building['weather_norm_eui']
sqft = building['sqft']

print(f"\nBuilding 2952 - Timperly Condominium")
print(f"Current EUI: {current_eui} kBtu/ft²")
print(f"Square Footage: {sqft:,} sq ft")

print("\n" + "="*60)
print("CORRECTED PENALTY CALCULATIONS")
print("="*60)

# Standard Path
print("\nStandard Path (2025, 2027, 2030) - $0.15/kBtu:")
targets = {
    2025: building['first_interim_target'],
    2027: building['second_interim_target'],
    2030: building['final_target']
}

total_standard = 0
for year, target in targets.items():
    if current_eui > target:
        excess = current_eui - target
        annual_penalty = excess * sqft * 0.15
        if year == 2025:
            years = 2  # 2025-2026
        elif year == 2027:
            years = 3  # 2027-2029
        else:  # 2030
            years = 10  # 2030-2039
        total_penalty = annual_penalty * years
        total_standard += total_penalty
        print(f"  {year}: Excess {excess:.1f} kBtu/ft² = ${annual_penalty:,.0f}/year × {years} years = ${total_penalty:,.0f}")
    else:
        print(f"  {year}: ✓ Compliant (target: {target:.1f})")

print(f"\n  15-Year Total Standard Path: ${total_standard:,.0f}")

# Alternate Path (Opt-in)
print("\n\nAlternate Path (2028, 2032) - $0.23/kBtu:")
# Linear interpolation for 2028 target
baseline_eui = building['baseline_eui']
final_target = building['final_target']
years_total = 2032 - building['baseline_year']
years_to_2028 = 2028 - building['baseline_year']
target_2028 = baseline_eui - (baseline_eui - final_target) * (years_to_2028 / years_total)

alt_targets = {
    2028: target_2028,
    2032: final_target
}

total_alternate = 0
for year, target in alt_targets.items():
    if current_eui > target:
        excess = current_eui - target
        annual_penalty = excess * sqft * 0.23
        if year == 2028:
            years = 4  # 2028-2031
        else:  # 2032
            years = 8  # 2032-2039
        total_penalty = annual_penalty * years
        total_alternate += total_penalty
        print(f"  {year}: Excess {excess:.1f} kBtu/ft² = ${annual_penalty:,.0f}/year × {years} years = ${total_penalty:,.0f}")
    else:
        print(f"  {year}: ✓ Compliant (target: {target:.1f})")

print(f"\n  15-Year Total Alternate Path: ${total_alternate:,.0f}")

print(f"\n\n💰 SAVINGS BY CHOOSING ALTERNATE PATH: ${total_standard - total_alternate:,.0f}")
print(f"   Annual Penalty Difference: ${(total_standard - total_alternate) / 15:,.0f}/year")

# Compare to old (wrong) calculations
print("\n" + "="*60)
print("COMPARISON TO OLD (INCORRECT) CALCULATIONS")
print("="*60)
print("Old calculations used escalating rates: $0.30, $0.50, $0.70")
print("This resulted in 15-year penalties of ~$5.3M (standard) and ~$4.8M (opt-in)")
print("\nCorrected calculations show MUCH lower penalties:")
print(f"  Standard Path: ${total_standard:,.0f} (was $5,265,536)")
print(f"  Alternate Path: ${total_alternate:,.0f} (was $4,797,740)")

# Impact on project economics
print("\n" + "="*60)
print("IMPACT ON PROJECT ECONOMICS")
print("="*60)
old_penalty_avoided = 5_265_536
new_penalty_avoided = total_standard
penalty_difference = old_penalty_avoided - new_penalty_avoided

print(f"Previous analysis showed ${old_penalty_avoided:,.0f} in penalties avoided")
print(f"Correct analysis shows ${new_penalty_avoided:,.0f} in penalties avoided")
print(f"Difference: ${penalty_difference:,.0f} LESS value from penalty avoidance")

print("\nThis means:")
print("1. The TES+HP system still provides value through:")
print("   - Energy cost savings")
print("   - Avoiding equipment replacement ($270,000)")
print("   - Comfort improvements")
print("   - Decarbonization")
print("2. But the penalty avoidance benefit is much smaller than previously calculated")
print("3. The focus should shift to energy savings and incentive capture")

print("\n✅ Configuration updated. Re-run analysis scripts for corrected results.")
