"""
Suggested File Name: test_bridge_connection.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Simple test to verify bridge connection and show available columns
"""

from local_gcp_bridge import LocalGCPBridge

def test_connection():
    """Test the bridge connection and show available data"""
    
    print("🔄 Testing LocalGCPBridge connection...\n")
    
    # Initialize bridge
    bridge = LocalGCPBridge()
    
    if bridge.client is None:
        print("❌ Failed to connect to BigQuery")
        return
    
    # Test 1: Get a small sample of data
    print("📊 Test 1: Retrieving sample data (5 rows)")
    try:
        df = bridge.get_opt_in_analysis(limit=5)
        print(f"✅ Retrieved {len(df)} rows")
        print(f"\nAvailable columns ({len(df.columns)} total):")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. {col}")
        
        # Show data types
        print("\n📋 Key column data types:")
        key_cols = ['building_id', 'current_eui', 'total_penalties_default', 
                   'should_opt_in', 'gross_floor_area']
        for col in key_cols:
            if col in df.columns:
                print(f"  {col}: {df[col].dtype}")
            else:
                print(f"  {col}: NOT FOUND")
                
    except Exception as e:
        print(f"❌ Error retrieving data: {e}")
        
    # Test 2: Try property type summary
    print("\n📊 Test 2: Property Type Summary")
    try:
        summary = bridge.analyze_property_type_summary()
        print(f"✅ Retrieved summary for {len(summary)} property types")
        if not summary.empty:
            print("\nTop 3 property types by penalty exposure:")
            print(summary[['property_type', 'building_count', 'total_default_penalties']].head(3))
    except Exception as e:
        print(f"❌ Error: {e}")
        
    # Test 3: Check for zip_code column
    print("\n📊 Test 3: Checking for geographic data")
    try:
        query = f"""
        SELECT 
            COUNT(DISTINCT building_id) as buildings_with_id,
            COUNT(DISTINCT zip_code) as unique_zips,
            COUNT(DISTINCT property_type) as unique_types
        FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
        """
        result = bridge.client.query(query).to_dataframe()
        print("Geographic data availability:")
        print(result)
    except Exception as e:
        print(f"Note: zip_code column may not exist: {e}")
        
        # Try to find what geographic columns do exist
        try:
            query = """
            SELECT *
            FROM `energize-denver-eaas.energize_denver.opt_in_decision_analysis_v3`
            LIMIT 1
            """
            sample = bridge.client.query(query).to_dataframe()
            geo_cols = [col for col in sample.columns if 'zip' in col.lower() or 
                       'lat' in col.lower() or 'lon' in col.lower() or 
                       'address' in col.lower()]
            if geo_cols:
                print(f"Found geographic columns: {geo_cols}")
            else:
                print("No geographic columns found in view")
        except:
            pass


if __name__ == "__main__":
    test_connection()