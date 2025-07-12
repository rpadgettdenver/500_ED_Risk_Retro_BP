"""
Test script for Building 2952 analysis
"""

# First, let's create test data for Building 2952
building_2952_data = {
    'building_id': '2952',
    'building_name': 'Timperly Condominium',
    'property_type': 'Multifamily Housing',
    'sqft': 52826,
    'weather_norm_eui': 65.3,
    'electricity_kwh': 210165,
    'gas_kbtu': 2584000,
    'total_ghg': 126.67,
    'is_epb': True,
    'baseline_year': 2019,
    'baseline_eui': 70.5,
    'first_interim_target': 65.4,  # 2025 target
    'second_interim_target': 63.2,  # 2027 target  
    'final_target': 51.5,  # 2030 target
}

print("Building 2952 - Timperly Condominium")
print("=" * 50)
print(f"Size: {building_2952_data['sqft']:,} sq ft")
print(f"Type: {building_2952_data['property_type']}")
print(f"EPB Status: {'Yes' if building_2952_data['is_epb'] else 'No'}")
print(f"\nEnergy Profile:")
print(f"Current Weather Normalized EUI: {building_2952_data['weather_norm_eui']}")
print(f"Baseline EUI (2019): {building_2952_data['baseline_eui']}")
print(f"Improvement from baseline: {((building_2952_data['weather_norm_eui'] - building_2952_data['baseline_eui']) / building_2952_data['baseline_eui'] * 100):.1f}%")
print(f"\nCompliance Targets:")
print(f"2025 Target: {building_2952_data['first_interim_target']} (Gap: {building_2952_data['weather_norm_eui'] - building_2952_data['first_interim_target']:.1f})")
print(f"2027 Target: {building_2952_data['second_interim_target']} (Gap: {building_2952_data['weather_norm_eui'] - building_2952_data['second_interim_target']:.1f})")
print(f"2030 Target: {building_2952_data['final_target']} (Gap: {building_2952_data['weather_norm_eui'] - building_2952_data['final_target']:.1f})")

# Calculate penalties
print(f"\nPenalty Analysis (Standard Path):")
for year, target, rate in [(2025, 65.4, 0.30), (2027, 63.2, 0.50), (2030, 51.5, 0.70)]:
    excess = max(0, building_2952_data['weather_norm_eui'] - target)
    penalty = excess * building_2952_data['sqft'] * rate
    print(f"{year}: ${penalty:,.0f}/year (excess EUI: {excess:.1f})")

print(f"\nImmediate Equipment Needs:")
print(f"Equipment replacement cost: $270,000")
print(f"Need: Failing boilers and cooling systems")
