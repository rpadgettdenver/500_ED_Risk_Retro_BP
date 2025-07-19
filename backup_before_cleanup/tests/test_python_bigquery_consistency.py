"""
Suggested File Name: test_python_bigquery_consistency.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/tests/
Use: Test consistency between Python calculations and BigQuery views

This script:
1. Loads sample buildings
2. Calculates penalties using Python modules
3. Compares with BigQuery results (if available)
4. Identifies any discrepancies
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List

# Add project root to path
project_root = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP'
sys.path.insert(0, project_root)

# Import modules
from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator
from src.utils.opt_in_predictor import OptInPredictor
from src.models.hvac_system_impact_modeler import HVACSystemImpactModeler


class PythonBigQueryConsistencyTest:
    """Test consistency between Python and BigQuery implementations"""
    
    def __init__(self):
        self.penalty_calc = EnergizeDenverPenaltyCalculator()
        self.opt_in_predictor = OptInPredictor()
        
    def load_test_buildings(self) -> pd.DataFrame:
        """Load a sample of buildings for testing"""
        # Load from comprehensive data
        data_path = os.path.join(project_root, 'data', 'processed', 
                               'energize_denver_comprehensive_latest.csv')
        
        # Load sample buildings
        df = pd.read_csv(data_path)
        
        # Convert Building ID to string
        df['Building ID'] = df['Building ID'].astype(str)
        
        # Filter to valid buildings
        df['Weather Normalized Site EUI'] = pd.to_numeric(df['Weather Normalized Site EUI'], errors='coerce')
        df['Master Sq Ft'] = pd.to_numeric(df['Master Sq Ft'], errors='coerce')
        
        df = df[
            (df['Weather Normalized Site EUI'] > 0) & 
            (df['Master Sq Ft'] >= 25000)
        ]
        
        # Get a diverse sample
        sample_buildings = []
        
        # Get some from each major property type
        major_types = ['Office', 'Multifamily Housing', 'Hotel', 'Retail Store', 'Medical Office']
        
        for prop_type in major_types:
            type_buildings = df[df['Master Property Type'] == prop_type].head(5)
            sample_buildings.append(type_buildings)
        
        # Add Building 2952 if available
        if '2952' in df['Building ID'].values:
            building_2952 = df[df['Building ID'] == '2952']
            sample_buildings.append(building_2952)
        
        # Combine all samples
        test_df = pd.concat(sample_buildings, ignore_index=True)
        
        print(f"Loaded {len(test_df)} test buildings")
        return test_df
    
    def calculate_python_results(self, building_row) -> Dict:
        """Calculate results using Python modules"""
        
        # Prepare building data
        building_data = {
            'building_id': str(building_row['Building ID']),
            'property_type': building_row['Master Property Type'],
            'sqft': float(building_row['Master Sq Ft']),
            'current_eui': float(building_row['Weather Normalized Site EUI']),
            'baseline_eui': float(building_row.get('Baseline EUI', building_row['Weather Normalized Site EUI'])),
            'first_interim_target': float(building_row.get('First Interim Target EUI', 0)),
            'second_interim_target': float(building_row.get('Second Interim Target EUI', 0)),
            'final_target': float(building_row.get('Original Final Target EUI', 0)),
            'is_epb': bool(building_row.get('Is EPB', False))
        }
        
        # Calculate standard path penalties
        standard_penalties = {}
        
        # 2025
        if building_data['first_interim_target'] > 0:
            gap_2025 = max(0, building_data['current_eui'] - building_data['first_interim_target'])
            standard_penalties['2025'] = gap_2025 * building_data['sqft'] * 0.15
        
        # 2027
        if building_data['second_interim_target'] > 0:
            gap_2027 = max(0, building_data['current_eui'] - building_data['second_interim_target'])
            standard_penalties['2027'] = gap_2027 * building_data['sqft'] * 0.15
        
        # 2030
        if building_data['final_target'] > 0:
            gap_2030 = max(0, building_data['current_eui'] - building_data['final_target'])
            standard_penalties['2030'] = gap_2030 * building_data['sqft'] * 0.15
        
        # Calculate ACO path penalties
        aco_penalties = {}
        
        # 2028 (using first interim target)
        if building_data['first_interim_target'] > 0:
            gap_2028 = max(0, building_data['current_eui'] - building_data['first_interim_target'])
            aco_penalties['2028'] = gap_2028 * building_data['sqft'] * 0.23
        
        # 2032 (using final target)
        if building_data['final_target'] > 0:
            gap_2032 = max(0, building_data['current_eui'] - building_data['final_target'])
            aco_penalties['2032'] = gap_2032 * building_data['sqft'] * 0.23
        
        # Get opt-in decision
        opt_in_decision = self.opt_in_predictor.predict_opt_in(building_data)
        
        # Get HVAC analysis if possible
        hvac_recommendation = 'Unknown'
        try:
            hvac_modeler = HVACSystemImpactModeler(building_data['building_id'])
            hvac_analysis = hvac_modeler.model_system_impact('current')
            if hvac_analysis:
                hvac_recommendation = 'Current System Analysis Complete'
        except:
            # Skip HVAC analysis if building not found
            pass
        
        return {
            'building_id': building_data['building_id'],
            'property_type': building_data['property_type'],
            'sqft': building_data['sqft'],
            'current_eui': building_data['current_eui'],
            'standard_penalty_2025': standard_penalties.get('2025', 0),
            'standard_penalty_2027': standard_penalties.get('2027', 0),
            'standard_penalty_2030': standard_penalties.get('2030', 0),
            'aco_penalty_2028': aco_penalties.get('2028', 0),
            'aco_penalty_2032': aco_penalties.get('2032', 0),
            'should_opt_in': opt_in_decision.should_opt_in,
            'opt_in_confidence': opt_in_decision.confidence,
            'hvac_recommendation': hvac_recommendation
        }
    
    def load_bigquery_results(self) -> pd.DataFrame:
        """Load BigQuery results if available"""
        # Check for exported BigQuery results
        bq_export_path = os.path.join(project_root, 'src', 'utils', 'data', 
                                    'gcp_exports', 'opt_in_analysis_v3.csv')
        
        if os.path.exists(bq_export_path):
            print(f"Loading BigQuery results from: {bq_export_path}")
            return pd.read_csv(bq_export_path)
        else:
            print("No BigQuery export found - skipping comparison")
            return None
    
    def compare_results(self, python_results: List[Dict], bq_df: pd.DataFrame = None):
        """Compare Python and BigQuery results"""
        print("\n📊 COMPARISON RESULTS")
        print("=" * 60)
        
        if bq_df is None:
            print("No BigQuery results available for comparison")
            print("\nPython calculation summary:")
            
            # Summary stats
            df_python = pd.DataFrame(python_results)
            
            print(f"\nBuildings analyzed: {len(df_python)}")
            print(f"Should opt-in: {df_python['should_opt_in'].sum()} "
                  f"({df_python['should_opt_in'].mean()*100:.1f}%)")
            
            print("\nTotal penalties by year:")
            print(f"  2025 (Standard): ${df_python['standard_penalty_2025'].sum():,.0f}")
            print(f"  2028 (ACO):      ${df_python['aco_penalty_2028'].sum():,.0f}")
            
            # Show property type breakdown
            print("\nOpt-in decisions by property type:")
            opt_in_by_type = df_python.groupby('property_type')['should_opt_in'].agg(['sum', 'count', 'mean'])
            opt_in_by_type.columns = ['opt_in_count', 'total_count', 'opt_in_rate']
            opt_in_by_type = opt_in_by_type.sort_values('opt_in_rate', ascending=False)
            
            for prop_type, row in opt_in_by_type.iterrows():
                print(f"  {prop_type}: {row['opt_in_count']}/{row['total_count']} "
                      f"({row['opt_in_rate']*100:.1f}%)")
            
            return
        
        # If we have BigQuery results, compare
        df_python = pd.DataFrame(python_results)
        
        # Convert building_id to string in both dataframes
        df_python['building_id'] = df_python['building_id'].astype(str)
        bq_df['building_id'] = bq_df['building_id'].astype(str)
        
        # Match buildings
        matched = 0
        discrepancies = []
        
        for _, py_row in df_python.iterrows():
            building_id = py_row['building_id']
            
            # Find in BigQuery results
            bq_building = bq_df[bq_df['building_id'] == building_id]
            
            if len(bq_building) > 0:
                matched += 1
                bq_row = bq_building.iloc[0]
                
                # Compare key fields
                tolerance = 0.01  # 1% tolerance
                
                # Compare penalties
                if 'standard_penalty_2025' in bq_row:
                    py_val = py_row['standard_penalty_2025']
                    bq_val = bq_row['standard_penalty_2025']
                    
                    if abs(py_val - bq_val) > max(py_val, bq_val) * tolerance:
                        discrepancies.append({
                            'building_id': building_id,
                            'field': 'standard_penalty_2025',
                            'python': py_val,
                            'bigquery': bq_val,
                            'diff_pct': abs(py_val - bq_val) / max(py_val, bq_val, 1) * 100
                        })
                
                # Compare opt-in decision
                if 'should_opt_in' in bq_row:
                    if py_row['should_opt_in'] != bq_row['should_opt_in']:
                        discrepancies.append({
                            'building_id': building_id,
                            'field': 'should_opt_in',
                            'python': py_row['should_opt_in'],
                            'bigquery': bq_row['should_opt_in']
                        })
        
        print(f"\nMatched {matched}/{len(df_python)} buildings with BigQuery results")
        
        if discrepancies:
            print(f"\n⚠️  Found {len(discrepancies)} discrepancies:")
            
            for disc in discrepancies[:10]:  # Show first 10
                print(f"\nBuilding {disc['building_id']} - {disc['field']}:")
                print(f"  Python:   {disc['python']}")
                print(f"  BigQuery: {disc['bigquery']}")
                if 'diff_pct' in disc:
                    print(f"  Diff:     {disc['diff_pct']:.1f}%")
        else:
            print("\n✅ No significant discrepancies found!")
    
    def run_consistency_test(self):
        """Run the full consistency test"""
        print("=" * 80)
        print("🧪 PYTHON vs BIGQUERY CONSISTENCY TEST")
        print("=" * 80)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Load test buildings
        test_buildings = self.load_test_buildings()
        
        # Calculate Python results
        print("\n📐 Calculating Python results...")
        python_results = []
        
        for idx, building in test_buildings.iterrows():
            try:
                result = self.calculate_python_results(building)
                python_results.append(result)
                
                # Show progress for first few
                if len(python_results) <= 3:
                    print(f"  Processed Building {result['building_id']} ({result['property_type']})")
                    
            except Exception as e:
                print(f"  Error processing building {building['Building ID']}: {e}")
        
        print(f"\n  Calculated results for {len(python_results)} buildings")
        
        # Load BigQuery results
        print("\n📊 Loading BigQuery results...")
        bq_results = self.load_bigquery_results()
        
        # Compare results
        self.compare_results(python_results, bq_results)
        
        # Save Python results for reference
        output_dir = os.path.join(project_root, 'test_results')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(output_dir, f'python_calculations_{timestamp}.csv')
        
        pd.DataFrame(python_results).to_csv(output_path, index=False)
        print(f"\n📁 Python results saved to: {output_path}")
        
        # Show sample results
        print("\n📋 Sample Python Results (first 5 buildings):")
        df_results = pd.DataFrame(python_results)
        print(df_results[['building_id', 'property_type', 'current_eui', 
                         'standard_penalty_2025', 'should_opt_in']].head())


def main():
    """Run consistency test"""
    tester = PythonBigQueryConsistencyTest()
    tester.run_consistency_test()


if __name__ == "__main__":
    main()
