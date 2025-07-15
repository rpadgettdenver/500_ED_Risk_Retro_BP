"""
Suggested File Name: mai_handler.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/data_processing/
Use: Unified handler for MAI building identification and target calculations

This module handles all MAI (Multifamily Affordable and Income-Restricted) building logic:
1. Identifies MAI buildings from MAITargetSummary Report.csv
2. Applies MAI-specific target calculations
3. Handles buildings with zero baseline EUI
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MAIHandler:
    """Handler for MAI building identification and calculations"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize with data directory path"""
        if data_dir is None:
            # Default to project data directory
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
        else:
            self.data_dir = Path(data_dir)
            
        # File paths
        self.mai_summary_file = self.data_dir / "MAITargetSummary Report.csv"
        self.mai_property_file = self.data_dir / "MAIPropertyUseTypes Report.csv"
        
        # Cache for loaded data
        self._mai_summary_df = None
        self._mai_property_df = None
        self._mai_building_ids = None
        self._mai_targets = None
        
    def load_mai_summary(self) -> pd.DataFrame:
        """Load the MAI Target Summary file"""
        if self._mai_summary_df is None:
            logger.info(f"Loading MAI summary from {self.mai_summary_file}")
            try:
                self._mai_summary_df = pd.read_csv(self.mai_summary_file)
                
                # Standardize column names
                self._mai_summary_df.columns = self._mai_summary_df.columns.str.strip()
                
                # Ensure Building ID is string for consistent joining
                if 'Building ID' in self._mai_summary_df.columns:
                    self._mai_summary_df['Building ID'] = self._mai_summary_df['Building ID'].astype(str)
                
                # Log statistics
                logger.info(f"Loaded {len(self._mai_summary_df)} MAI building records")
                
                # Check for buildings with valid baselines
                valid_baseline = self._mai_summary_df['Baseline Value'] > 0
                logger.info(f"Buildings with valid baselines: {valid_baseline.sum()}")
                logger.info(f"Buildings with zero baselines: {(~valid_baseline).sum()}")
                
            except FileNotFoundError:
                logger.warning("MAI summary file not found, proceeding without MAI data")
                self._mai_summary_df = pd.DataFrame()
                
        return self._mai_summary_df
    
    def load_mai_properties(self) -> pd.DataFrame:
        """Load the MAI Property Use Types file"""
        if self._mai_property_df is None:
            logger.info(f"Loading MAI properties from {self.mai_property_file}")
            try:
                self._mai_property_df = pd.read_csv(self.mai_property_file)
                
                # Standardize column names
                self._mai_property_df.columns = self._mai_property_df.columns.str.strip()
                
                # Ensure Building ID is string
                if 'Building ID' in self._mai_property_df.columns:
                    self._mai_property_df['Building ID'] = self._mai_property_df['Building ID'].astype(str)
                    
            except FileNotFoundError:
                logger.warning("MAI property file not found")
                self._mai_property_df = pd.DataFrame()
                
        return self._mai_property_df
    
    def get_mai_building_ids(self) -> List[str]:
        """Get list of all MAI building IDs"""
        if self._mai_building_ids is None:
            mai_df = self.load_mai_summary()
            if not mai_df.empty:
                self._mai_building_ids = mai_df['Building ID'].unique().tolist()
            else:
                self._mai_building_ids = []
                
        return self._mai_building_ids
    
    def is_mai_building(self, building_id: str) -> bool:
        """Check if a building is MAI designated"""
        mai_ids = self.get_mai_building_ids()
        return str(building_id) in mai_ids
    
    def get_mai_targets(self, building_id: str) -> Dict[str, any]:
        """Get MAI-specific targets for a building"""
        building_id = str(building_id)
        
        mai_df = self.load_mai_summary()
        if mai_df.empty:
            return None
            
        # Find building in MAI summary
        building_data = mai_df[mai_df['Building ID'] == building_id]
        
        if building_data.empty:
            return None
            
        row = building_data.iloc[0]
        
        # Extract MAI-specific values
        result = {
            'building_id': building_id,
            'approved_mai': row.get('Approved Mai', 'Yes') == 'Yes',
            'building_status': row.get('Building Status', 'unknown'),
            'baseline_year': int(row.get('Baseline Year', 0)) if pd.notna(row.get('Baseline Year')) else 0,
            'baseline_value': float(row.get('Baseline Value', 0)) if pd.notna(row.get('Baseline Value')) else 0,
            'interim_target_year': int(row.get('Interim Target Year', 0)) if pd.notna(row.get('Interim Target Year')) else 0,
            'interim_target': float(row.get('Interim Target', 0)) if pd.notna(row.get('Interim Target')) else 0,
            'final_target_year': int(row.get('Final Target Year', 0)) if pd.notna(row.get('Final Target Year')) else 0,
            'original_final_target': float(row.get('Original Final Target', 0)) if pd.notna(row.get('Original Final Target')) else 0,
            'adjusted_final_target': float(row.get('Adjusted Final Target', 0)) if pd.notna(row.get('Adjusted Final Target')) else 0,
            'current_ff_usage': float(row.get('Current FF Usage', 0)) if pd.notna(row.get('Current FF Usage')) else 0,
            'natural_gas_use': float(row.get('Natural Gas Use (kBtu)', 0)) if pd.notna(row.get('Natural Gas Use (kBtu)')) else 0
        }
        
        # Check if building has valid baseline for calculations
        result['has_valid_baseline'] = result['baseline_value'] > 0
        
        return result
    
    def calculate_mai_final_target(self, baseline_eui: float, 
                                 csv_adjusted_target: float,
                                 mai_data: Optional[Dict] = None) -> float:
        """
        Calculate MAI final target using the MAX of:
        1. Adjusted Final Target from MAI summary
        2. 30% reduction from baseline (baseline × 0.70)
        3. 52.9 kBtu/sqft floor
        
        Args:
            baseline_eui: Building's baseline EUI
            csv_adjusted_target: Adjusted target from Building_EUI_Targets.csv
            mai_data: MAI-specific data from get_mai_targets()
            
        Returns:
            Final MAI target (highest/most lenient value)
        """
        # If no valid baseline, cannot calculate targets
        if baseline_eui <= 0:
            logger.warning(f"Cannot calculate MAI target with zero baseline EUI")
            return 0
        
        # Calculate 30% reduction target
        thirty_pct_reduction = baseline_eui * 0.70
        
        # MAI floor
        mai_floor = 52.9
        
        # Start with the highest of reduction and floor
        mai_target = max(thirty_pct_reduction, mai_floor)
        
        # Include CSV adjusted target
        mai_target = max(mai_target, csv_adjusted_target)
        
        # If we have MAI-specific adjusted target, include it
        if mai_data and mai_data.get('adjusted_final_target', 0) > 0:
            mai_target = max(mai_target, mai_data['adjusted_final_target'])
        
        logger.info(f"MAI target calculation: "
                   f"30% reduction={thirty_pct_reduction:.1f}, "
                   f"floor={mai_floor}, "
                   f"CSV target={csv_adjusted_target:.1f}, "
                   f"MAI adjusted={mai_data.get('adjusted_final_target', 0):.1f} if applicable, "
                   f"final={mai_target:.1f}")
        
        return mai_target
    
    def get_mai_property_info(self, building_id: str) -> Dict[str, any]:
        """Get property type information for MAI building"""
        building_id = str(building_id)
        
        prop_df = self.load_mai_properties()
        if prop_df.empty:
            return None
            
        building_data = prop_df[prop_df['Building ID'] == building_id]
        
        if building_data.empty:
            return None
            
        row = building_data.iloc[0]
        
        return {
            'building_id': building_id,
            'building_name': row.get('Building Name', ''),
            'building_address': row.get('Building Address', ''),
            'master_property_type': row.get('Master Property Type', ''),
            'largest_property_type': row.get('Largest Property Use Type', ''),
            'second_largest_type': row.get('Second Largest Property Use Type', ''),
            'all_property_types': row.get('All Property Use Types and GFA', '')
        }
    
    def create_mai_lookup(self) -> Dict[str, bool]:
        """Create a lookup dictionary for quick MAI checking"""
        mai_ids = self.get_mai_building_ids()
        return {building_id: True for building_id in mai_ids}
    
    def get_mai_summary_stats(self) -> Dict[str, any]:
        """Get summary statistics about MAI buildings"""
        mai_df = self.load_mai_summary()
        
        if mai_df.empty:
            return {
                'total_mai_buildings': 0,
                'with_valid_baseline': 0,
                'zero_baseline': 0,
                'property_type_counts': {}
            }
        
        # Basic counts
        total = len(mai_df)
        valid_baseline = (mai_df['Baseline Value'] > 0).sum()
        zero_baseline = (mai_df['Baseline Value'] == 0).sum()
        
        # Property type distribution
        prop_df = self.load_mai_properties()
        if not prop_df.empty:
            property_types = prop_df['Master Property Type'].value_counts().to_dict()
        else:
            property_types = {}
        
        # Building status distribution
        status_counts = mai_df['Building Status'].value_counts().to_dict()
        
        return {
            'total_mai_buildings': total,
            'with_valid_baseline': valid_baseline,
            'zero_baseline': zero_baseline,
            'percent_zero_baseline': (zero_baseline / total * 100) if total > 0 else 0,
            'property_type_counts': property_types,
            'building_status_counts': status_counts,
            'top_property_types': list(property_types.keys())[:10] if property_types else []
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize MAI handler
    handler = MAIHandler()
    
    # Get summary statistics
    print("MAI Building Summary Statistics:")
    print("=" * 60)
    stats = handler.get_mai_summary_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60 + "\n")
    
    # Test with a specific MAI building
    test_building_id = "1153"  # Distribution Center from the data
    
    print(f"Testing MAI Building {test_building_id}:")
    print("-" * 40)
    
    # Check if MAI
    is_mai = handler.is_mai_building(test_building_id)
    print(f"Is MAI: {is_mai}")
    
    # Get MAI targets
    mai_targets = handler.get_mai_targets(test_building_id)
    if mai_targets:
        print("\nMAI Target Data:")
        for key, value in mai_targets.items():
            print(f"  {key}: {value}")
    
    # Get property info
    prop_info = handler.get_mai_property_info(test_building_id)
    if prop_info:
        print("\nProperty Information:")
        for key, value in prop_info.items():
            if value:  # Only print non-empty values
                print(f"  {key}: {value}")
    
    # Test MAI target calculation
    if mai_targets and mai_targets['has_valid_baseline']:
        print("\nMAI Target Calculation Test:")
        baseline = mai_targets['baseline_value']
        csv_target = 30  # Example
        
        final_target = handler.calculate_mai_final_target(
            baseline_eui=baseline,
            csv_adjusted_target=csv_target,
            mai_data=mai_targets
        )
        
        print(f"  Baseline EUI: {baseline:.1f}")
        print(f"  CSV Target: {csv_target:.1f}")
        print(f"  Final MAI Target: {final_target:.1f}")
    
    # Test building with zero baseline
    print("\n" + "=" * 60 + "\n")
    print("Testing Building with Zero Baseline (1122 - Data Center):")
    print("-" * 40)
    
    zero_baseline_targets = handler.get_mai_targets("1122")
    if zero_baseline_targets:
        print(f"Has valid baseline: {zero_baseline_targets['has_valid_baseline']}")
        print(f"Baseline Value: {zero_baseline_targets['baseline_value']}")
        print("Note: Buildings with zero baseline cannot have penalties calculated")
