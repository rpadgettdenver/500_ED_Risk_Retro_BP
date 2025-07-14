#!/usr/bin/env python3
"""
Suggested file name: eui_target_loader.py
Directory Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
USE: Unified module for loading EUI targets with proper priority logic

This module provides a single source of truth for EUI target loading:
1. Loads targets from Building_EUI_Targets.csv
2. Checks MAI designation from MAITargetSummary.csv
3. Applies MAI logic: MAX(CSV target, 30% reduction, 52.9 floor)
4. Applies standard caps and floors
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EUITargetLoader:
    """Unified loader for Energize Denver EUI targets"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize with data directory path"""
        if data_dir is None:
            # Default to project data directory
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
        else:
            self.data_dir = Path(data_dir)
            
        # File paths
        self.targets_file = self.data_dir / "Building_EUI_Targets.csv"
        self.mai_file = self.data_dir / "MAITargetSummary Report.csv"
        self.epb_file = self.data_dir / "CopyofWeeklyEPBStatsReport Report.csv"
        
        # Cache for loaded data
        self._targets_df = None
        self._mai_df = None
        self._epb_df = None
        
    def load_targets_data(self) -> pd.DataFrame:
        """Load the main targets CSV"""
        if self._targets_df is None:
            logger.info(f"Loading targets from {self.targets_file}")
            self._targets_df = pd.read_csv(self.targets_file)
            
            # Standardize column names
            self._targets_df.columns = self._targets_df.columns.str.strip()
            
            # Ensure Building ID is string for consistent joining
            if 'Building ID' in self._targets_df.columns:
                self._targets_df['Building ID'] = self._targets_df['Building ID'].astype(str)
                
        return self._targets_df
    
    def load_mai_data(self) -> pd.DataFrame:
        """Load MAI designations and targets"""
        if self._mai_df is None:
            logger.info(f"Loading MAI data from {self.mai_file}")
            try:
                self._mai_df = pd.read_csv(self.mai_file)
                self._mai_df.columns = self._mai_df.columns.str.strip()
                
                # Ensure Building ID is string
                if 'Building ID' in self._mai_df.columns:
                    self._mai_df['Building ID'] = self._mai_df['Building ID'].astype(str)
                    
                logger.info(f"Loaded {len(self._mai_df)} MAI buildings")
            except FileNotFoundError:
                logger.warning("MAI file not found, proceeding without MAI data")
                self._mai_df = pd.DataFrame()
                
        return self._mai_df
    
    def is_mai_building(self, building_id: str) -> bool:
        """Check if a building has MAI designation"""
        mai_df = self.load_mai_data()
        if mai_df.empty:
            return False
            
        return str(building_id) in mai_df['Building ID'].values
    
    def calculate_mai_target(self, baseline_eui: float, csv_target: float) -> float:
        """
        Calculate MAI target using the MAX of three values:
        1. Adjusted Final Target from CSV
        2. 30% reduction from baseline
        3. 52.9 kBtu/sqft floor
        """
        thirty_pct_reduction = baseline_eui * 0.70  # 30% reduction
        mai_floor = 52.9
        
        # Return the maximum (most lenient) of the three values
        final_target = max(csv_target, thirty_pct_reduction, mai_floor)
        
        logger.info(f"MAI target calculation: CSV={csv_target:.1f}, "
                   f"30% reduction={thirty_pct_reduction:.1f}, "
                   f"floor={mai_floor}, final={final_target:.1f}")
        
        return final_target
    
    def apply_standard_caps(self, baseline_eui: float, target_eui: float, 
                           is_mai: bool = False) -> float:
        """Apply standard caps and floors to targets"""
        if is_mai:
            # MAI buildings use their special calculation
            return target_eui
        else:
            # Non-MAI: 42% maximum reduction from baseline
            max_reduction_target = baseline_eui * 0.58  # 42% reduction
            
            # Apply the cap (target can't be lower than 58% of baseline)
            capped_target = max(target_eui, max_reduction_target)
            
            if capped_target != target_eui:
                logger.info(f"Applied 42% cap: {target_eui:.1f} -> {capped_target:.1f}")
                
            return capped_target
    
    def get_building_targets(self, building_id: str) -> Dict[str, any]:
        """
        Get all targets for a building with proper logic applied
        
        Returns dict with:
        - building_id: str
        - is_mai: bool
        - baseline_eui: float
        - first_interim_target: float
        - second_interim_target: float  
        - final_target: float
        - adjusted_final_target: float (with MAI/caps applied)
        """
        building_id = str(building_id)
        targets_df = self.load_targets_data()
        
        # Find building in targets
        building_data = targets_df[targets_df['Building ID'] == building_id]
        
        if building_data.empty:
            raise ValueError(f"Building {building_id} not found in targets data")
            
        row = building_data.iloc[0]
        
        # Extract base values
        result = {
            'building_id': building_id,
            'property_type': row.get('Master Property Type', ''),
            'is_mai': self.is_mai_building(building_id),
            'square_feet': row.get('Master Sq Ft', 0),
        }
        
        # Get baseline EUI (correct column name)
        baseline_eui = row.get('Baseline EUI', 0)
        if pd.isna(baseline_eui) or baseline_eui == 0:
            logger.warning(f"Building {building_id} has no/zero baseline EUI")
            baseline_eui = 0
            
        result['baseline_eui'] = float(baseline_eui)
        
        # Get interim targets (correct column names)
        result['first_interim_target'] = float(row.get('First Interim Target EUI', baseline_eui))
        result['second_interim_target'] = float(row.get('Second Interim Target EUI', baseline_eui))
        
        # Get final targets
        original_final = float(row.get('Original Final Target EUI', baseline_eui))
        adjusted_final = float(row.get('Adjusted Final Target EUI', original_final))
        
        result['original_final_target'] = original_final
        result['csv_adjusted_final_target'] = adjusted_final
        
        # Apply MAI logic if applicable
        if result['is_mai'] and baseline_eui > 0:
            # Use the adjusted final target from CSV as input to MAI calculation
            mai_adjusted_target = self.calculate_mai_target(baseline_eui, adjusted_final)
            result['final_target_with_logic'] = mai_adjusted_target
        else:
            # Apply standard 42% cap for non-MAI buildings
            if baseline_eui > 0:
                capped_target = self.apply_standard_caps(baseline_eui, adjusted_final, is_mai=False)
                result['final_target_with_logic'] = capped_target
            else:
                result['final_target_with_logic'] = adjusted_final
        
        # Add flags for special cases
        result['has_target_adjustment'] = row.get('Applied for Target Adjustment', 0) == 1
        result['has_electrification_credit'] = row.get('Electrification Credit Applied', 0) == 1
        
        # Log summary
        logger.info(f"Building {building_id} ({result['property_type']}): "
                   f"Baseline={baseline_eui:.1f}, "
                   f"Interim1={result['first_interim_target']:.1f}, "
                   f"Interim2={result['second_interim_target']:.1f}, "
                   f"Final={adjusted_final:.1f}, "
                   f"Logic Applied={result['final_target_with_logic']:.1f}, "
                   f"MAI={result['is_mai']}")
        
        return result
    
    def get_all_building_targets(self) -> pd.DataFrame:
        """Get targets for all buildings with logic applied"""
        targets_df = self.load_targets_data()
        
        results = []
        for building_id in targets_df['Building ID'].unique():
            try:
                targets = self.get_building_targets(building_id)
                results.append(targets)
            except Exception as e:
                logger.error(f"Error processing building {building_id}: {e}")
                
        return pd.DataFrame(results)
    
    def validate_targets(self, building_id: str) -> Dict[str, any]:
        """Validate targets for a building and flag any issues"""
        targets = self.get_building_targets(building_id)
        
        issues = []
        
        # Skip validation if no baseline
        if targets['baseline_eui'] == 0:
            issues.append("No baseline EUI - cannot validate targets")
            return {
                'building_id': building_id,
                'valid': False,
                'issues': issues,
                'targets': targets
            }
        
        # Check if targets decrease over time (allow small tolerance for rounding)
        if targets['first_interim_target'] > targets['baseline_eui'] + 0.1:
            issues.append("First interim target is higher than baseline")
            
        if targets['second_interim_target'] > targets['first_interim_target'] + 0.1:
            issues.append("Second interim target is higher than first")
            
        if targets['csv_adjusted_final_target'] > targets['second_interim_target'] + 0.1:
            issues.append("Final target is higher than second interim")
            
        # Check if MAI logic was applied correctly
        if targets['is_mai']:
            expected_mai = self.calculate_mai_target(
                targets['baseline_eui'], 
                targets['csv_adjusted_final_target']
            )
            if abs(targets['final_target_with_logic'] - expected_mai) > 0.1:
                issues.append("MAI logic may not be applied correctly")
                
        # Check 42% cap for non-MAI
        if not targets['is_mai']:
            max_reduction = targets['baseline_eui'] * 0.58
            if targets['final_target_with_logic'] < max_reduction - 0.1:
                issues.append("42% cap may not be applied correctly")
                
        return {
            'building_id': building_id,
            'valid': len(issues) == 0,
            'issues': issues,
            'targets': targets
        }


# Convenience functions for direct use
def load_building_targets(building_id: str, data_dir: Optional[Path] = None) -> Dict[str, any]:
    """Quick function to load targets for a single building"""
    loader = EUITargetLoader(data_dir)
    return loader.get_building_targets(building_id)


def load_all_targets(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Quick function to load all building targets"""
    loader = EUITargetLoader(data_dir)
    return loader.get_all_building_targets()


# Example usage and testing
if __name__ == "__main__":
    # Test with Building 2952 (non-MAI)
    print("Testing Building 2952 (EPB, non-MAI):")
    targets_2952 = load_building_targets("2952")
    for key, value in targets_2952.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*50 + "\n")
    
    # Test with an MAI building if available
    loader = EUITargetLoader()
    mai_df = loader.load_mai_data()
    if not mai_df.empty:
        mai_building_id = mai_df.iloc[0]['Building ID']
        print(f"Testing MAI Building {mai_building_id}:")
        mai_targets = load_building_targets(mai_building_id)
        for key, value in mai_targets.items():
            print(f"  {key}: {value}")
    
    print("\n" + "="*50 + "\n")
    
    # Test building with zero baseline (Building 1122)
    print("Testing Building 1122 (Data Center with zero baseline):")
    try:
        targets_1122 = load_building_targets("1122")
        for key, value in targets_1122.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"  Error: {e}")
