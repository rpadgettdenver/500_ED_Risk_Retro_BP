import pandas as pd

# Quick script to check column names
df = pd.read_csv('/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed/energize_denver_comprehensive_latest.csv', nrows=1)

print("All columns:")
for col in df.columns:
    print(col)
    
print("\n\nLooking for area/sqft columns:")
for col in df.columns:
    if any(term in col.lower() for term in ['area', 'sqft', 'square', 'ft²', 'ft2', 'gross', 'floor']):
        print(f"Found: {col}")
