"""
Suggested File Name: mai_data_loader.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Load and process MAI designation and target data for Energize Denver compliance

This module handles loading MAI (Manufacturing/Agricultural/Industrial) building
designations and their specific targets from the official CSV files.
"""

import pandas as pd
import os
from typing import Dict, Tuple, Optional
from pathlib import Path


class MAIDataLoader:
    """Load and process MAI designation and target data"""
    
    def __init__(self, data_dir: str = None):
        """Initialize MAI data loader
        
        Args:
            data_dir: Directory containing MAI CSV files
        """
        if data_dir is None:
            # Default to project data directory
            self.data_dir = Path("/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/raw")
        else:
            self.data_dir = Path(data_dir)
            
        self.mai_types_file = self.data_dir / "MAIPropertyUseTypes Report.csv"
        self.mai_targets_file = self.data_dir / "MAITargetSummary Report.csv"
        
    def load_mai_designations(self) -> Dict[str, Dict]:
        """
        Load MAI building designations from MAIPropertyUseTypes Report.csv
        
        Returns:
            Dictionary mapping building_id to MAI info:
            {
                'building_id': {
                    'is_mai': True,
                    'master_property_type': 'Data Center',
                    'largest_use_type': 'data center',
                    'building_name': 'raymond james & associates',
                    'building_status': 'in compliance'
                }
            }
        """
        if not self.mai_types_file.exists():
            print(f"Warning: MAI types file not found: {self.mai_types_file}")
            return {}
            
        # Read CSV
        df = pd.read_csv(self.mai_types_file)
        
        # Create lookup dictionary
        mai_lookup = {}
        
        for _, row in df.iterrows():
            building_id = str(row['Building ID'])
            
            # Only include approved MAI buildings
            if row.get('Approved Mai', '').lower() == 'yes':
                mai_lookup[building_id] = {
                    'is_mai': True,
                    'master_property_type': row.get('Master Property Type', ''),
                    'largest_use_type': row.get('Largest Property Use Type', ''),
                    'building_name': row.get('Building Name', ''),
                    'building_status': row.get('Building Status', '')
                }
                
        print(f"Loaded {len(mai_lookup)} MAI designated buildings")
        return mai_lookup
        
    def load_mai_targets(self) -> Dict[str, Dict]:
        """
        Load MAI-specific targets from MAITargetSummary Report.csv
        
        Returns:
            Dictionary mapping building_id to target info:
            {
                'building_id': {
                    'baseline_year': 2022,
                    'baseline_value': 536.6,
                    'interim_target_year': 2028,
                    'interim_target': 456.1,
                    'final_target_year': 2032,
                    'original_final_target': 375.6,
                    'adjusted_final_target': 375.6,
                    'applied_performance_pathway': False,
                    'applied_prescriptive_pathway': False
                }
            }
        """
        if not self.mai_targets_file.exists():
            print(f"Warning: MAI targets file not found: {self.mai_targets_file}")
            return {}
            
        # Read CSV
        df = pd.read_csv(self.mai_targets_file)
        
        # Create lookup dictionary
        targets_lookup = {}
        
        for _, row in df.iterrows():
            building_id = str(row['Building ID'])
            
            # Only include approved MAI buildings
            if row.get('Approved Mai', '').lower() == 'yes':
                targets_lookup[building_id] = {
                    'baseline_year': row.get('Baseline Year'),
                    'baseline_value': row.get('Baseline Value'),
                    'interim_target_year': row.get('Interim Target Year'),
                    'interim_target': row.get('Interim Target'),
                    'final_target_year': row.get('Final Target Year'),
                    'original_final_target': row.get('Original Final Target'),
                    'adjusted_final_target': row.get('Adjusted Final Target'),
                    'applied_performance_pathway': pd.notna(row.get('Applied for Performance Pathway?')),
                    'applied_prescriptive_pathway': pd.notna(row.get('Applied for Prescriptive Pathway?')),
                    'percent_above_next_target': row.get('Percent Above or Below Next Target', 0),
                    'percent_above_final_target': row.get('Percent Above or Below Final Target', 0)
                }
                
        print(f"Loaded targets for {len(targets_lookup)} MAI buildings")
        return targets_lookup
        
    def get_combined_mai_data(self) -> Dict[str, Dict]:
        """
        Load and combine all MAI data into a single lookup
        
        Returns:
            Dictionary with complete MAI information for each building
        """
        # Load both datasets
        mai_designations = self.load_mai_designations()
        mai_targets = self.load_mai_targets()
        
        # Combine data
        combined = {}
        
        # Start with all designated MAI buildings
        for building_id, designation_info in mai_designations.items():
            combined[building_id] = designation_info.copy()
            
            # Add target information if available
            if building_id in mai_targets:
                combined[building_id].update(mai_targets[building_id])
            else:
                print(f"Warning: MAI building {building_id} has designation but no targets")
                
        # Check for any buildings with targets but no designation (shouldn't happen)
        for building_id in mai_targets:
            if building_id not in combined:
                print(f"Warning: Building {building_id} has MAI targets but no designation")
                
        return combined
        
    def get_mai_building_ids(self) -> set:
        """
        Get set of all MAI designated building IDs.
        
        Per project guidance: MAI buildings are those listed in MAITargetSummary Report.csv
        
        Returns:
            Set of building IDs that are MAI designated
        """
        mai_targets = self.load_mai_targets()
        return set(mai_targets.keys())
        
    def is_mai_building(self, building_id: str) -> bool:
        """
        Check if a specific building is MAI designated.
        
        Per project guidance: A building is MAI if it appears in MAITargetSummary Report.csv
        
        Args:
            building_id: Building ID to check
            
        Returns:
            True if building appears in MAI Target Summary
        """
        mai_targets = self.load_mai_targets()
        return str(building_id) in mai_targets
        
    def get_mai_targets_for_building(self, building_id: str) -> Optional[Dict]:
        """Get MAI targets for a specific building"""
        targets = self.load_mai_targets()
        return targets.get(str(building_id))
        
    def create_mai_summary_report(self) -> pd.DataFrame:
        """Create a summary report of MAI buildings by property type"""
        mai_data = self.get_combined_mai_data()
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame.from_dict(mai_data, orient='index')
        df.index.name = 'building_id'
        
        # Group by property type
        summary = df.groupby('master_property_type').agg({
            'is_mai': 'count',
            'adjusted_final_target': ['mean', 'min', 'max'],
            'baseline_value': 'mean'
        }).round(1)
        
        summary.columns = ['Count', 'Avg_Final_Target', 'Min_Final_Target', 
                          'Max_Final_Target', 'Avg_Baseline']
        
        return summary


# Example usage
if __name__ == "__main__":
    # Initialize loader
    loader = MAIDataLoader()
    
    # Load MAI designations
    print("\n=== Loading MAI Designations ===")
    mai_buildings = loader.load_mai_designations()
    print(f"Total MAI buildings: {len(mai_buildings)}")
    
    # Show property type distribution
    property_types = {}
    for building_id, info in mai_buildings.items():
        prop_type = info['master_property_type']
        property_types[prop_type] = property_types.get(prop_type, 0) + 1
        
    print("\nMAI Buildings by Property Type:")
    for prop_type, count in sorted(property_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {prop_type}: {count}")
        
    # Load MAI targets
    print("\n=== Loading MAI Targets ===")
    mai_targets = loader.load_mai_targets()
    
    # Show some example buildings with different property types
    print("\nExample MAI Buildings (not just Manufacturing):")
    examples = ['1122', '1153', '1160', '2604', '1887']  # Different property types
    
    for building_id in examples:
        if building_id in mai_buildings:
            info = mai_buildings[building_id]
            print(f"\nBuilding {building_id}:")
            print(f"  Name: {info['building_name']}")
            print(f"  Type: {info['master_property_type']}")
            
            if building_id in mai_targets:
                targets = mai_targets[building_id]
                print(f"  Final Target: {targets['adjusted_final_target']}")
                print(f"  Target Years: {targets['interim_target_year']}/{targets['final_target_year']}")
                
    # Create summary report
    print("\n=== MAI Summary by Property Type ===")
    summary = loader.create_mai_summary_report()
    print(summary)
    
    # Test specific building check
    print("\n=== Testing Building Checks ===")
    test_ids = ['1122', '2952', '1153']
    for bid in test_ids:
        is_mai = loader.is_mai_building(bid)
        print(f"Building {bid} is MAI: {is_mai}")
