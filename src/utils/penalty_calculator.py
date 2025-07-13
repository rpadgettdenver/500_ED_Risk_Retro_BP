"""
Suggested File Name: penalty_calculator.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Single source of truth for all Energize Denver penalty calculations

This module implements the definitive penalty calculation logic as specified in
the Energize Denver Penalty Calculations - Definitive Source of Truth document.
All scripts should use this module for penalty calculations to ensure consistency.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PenaltyConfig:
    """Configuration for penalty calculations"""
    # Penalty rates by compliance path
    STANDARD_RATE: float = 0.15  # $/kBtu for 3-target path
    ACO_RATE: float = 0.23       # $/kBtu for 2-target Alternate Compliance Option
    EXTENSION_RATE: float = 0.35  # $/kBtu for 1-target timeline extension
    LATE_EXTENSION_ADDON: float = 0.10  # $/kBtu added for late extensions
    NEVER_BENCHMARKED_RATE: float = 10.00  # $/sqft for never benchmarked
    
    # Target years by path
    STANDARD_TARGET_YEARS: List[int] = None  # Set in __post_init__
    ACO_TARGET_YEARS: List[int] = None       # Set in __post_init__
    
    # Caps and floors
    MAX_REDUCTION_PCT: float = 0.42  # 42% maximum reduction for non-MAI
    MAI_REDUCTION_PCT: float = 0.30  # 30% reduction for MAI
    MAI_FLOOR_EUI: float = 52.9      # Minimum EUI for MAI buildings
    MAI_BASELINE_THRESHOLD: float = 75.5  # Threshold for MAI floor application
    
    def __post_init__(self):
        if self.STANDARD_TARGET_YEARS is None:
            self.STANDARD_TARGET_YEARS = [2025, 2027, 2030]
        if self.ACO_TARGET_YEARS is None:
            self.ACO_TARGET_YEARS = [2028, 2032]


class EnergizeDenverPenaltyCalculator:
    """
    Unified penalty calculator for Energize Denver compliance.
    
    This class provides all penalty calculation functionality following the
    official technical guidance from April 2025.
    """
    
    def __init__(self, config: Optional[PenaltyConfig] = None, mai_lookup: Optional[Dict] = None):
        """Initialize calculator with configuration
        
        Args:
            config: Penalty configuration
            mai_lookup: Dictionary of building_id -> MAI designation info
        """
        self.config = config or PenaltyConfig()
        self.mai_lookup = mai_lookup or {}
        
    def is_mai_designated(self, building_id: str, property_type: str = None) -> bool:
        """
        Check if a building is MAI designated.
        
        MAI designation is not just based on property type - many building types
        can have MAI designation including Data Centers, Distribution Centers, etc.
        
        Args:
            building_id: Building ID to check
            property_type: Property type (optional, for fallback logic)
            
        Returns:
            True if building is MAI designated
        """
        # First check the MAI lookup if available
        if self.mai_lookup and building_id in self.mai_lookup:
            return self.mai_lookup[building_id]
        
        # Fallback to property type check (less accurate)
        # This should only be used if MAI designation list is not available
        if property_type:
            return property_type == 'Manufacturing/Industrial Plant'
            
        return False
    def apply_target_caps_and_floors(self, raw_target_eui: float, baseline_eui: float, 
                                   is_mai: bool = False, mai_adjusted_target: float = None) -> float:
        """
        Apply caps and floors to raw EUI targets.
        
        Args:
            raw_target_eui: Original target from calculations
            baseline_eui: Building's baseline EUI
            is_mai: Whether building is MAI designated (appears in MAITargetSummary)
            mai_adjusted_target: Adjusted Final Target from MAITargetSummary
            
        Returns:
            Final target EUI after applying caps/floors
        """
        if is_mai:
            return self._apply_mai_rules(raw_target_eui, baseline_eui, mai_adjusted_target)
        else:
            return self._apply_non_mai_cap(raw_target_eui, baseline_eui)
    
    def _apply_non_mai_cap(self, raw_target_eui: float, baseline_eui: float) -> float:
        """Apply 42% maximum reduction cap for non-MAI buildings"""
        cap_target = baseline_eui * (1 - self.config.MAX_REDUCTION_PCT)
        return max(raw_target_eui, cap_target)  # Use less stringent (higher) target
    
    def _apply_mai_rules(self, raw_target_eui: float, baseline_eui: float, 
                        mai_adjusted_target: float = None) -> float:
        """
        Apply MAI-specific rules: 30% reduction or 52.9 floor.
        
        For MAI buildings, use the maximum (most lenient) of:
        - Adjusted Final Target from MAITargetSummary
        - 30% reduction from baseline
        - 52.9 kBtu/sqft floor
        
        Args:
            raw_target_eui: Original calculated target
            baseline_eui: Building's baseline EUI
            mai_adjusted_target: Adjusted Final Target from MAITargetSummary
            
        Returns:
            Final MAI target (highest/most lenient value)
        """
        # Calculate 30% reduction target
        reduction_target = baseline_eui * (1 - self.config.MAI_REDUCTION_PCT)
        
        # Start with the highest of the calculated values
        mai_target = max(reduction_target, self.config.MAI_FLOOR_EUI)
        
        # If we have an adjusted target from MAI summary, include it
        if mai_adjusted_target is not None:
            mai_target = max(mai_target, mai_adjusted_target)
            
        # Also consider the raw target (in case it's more lenient)
        return max(raw_target_eui, mai_target)
    
    def calculate_penalty(self, actual_eui: float, target_eui: float, 
                         sqft: float, penalty_rate: float) -> float:
        """
        Calculate penalty for a single assessment.
        
        Args:
            actual_eui: Weather normalized site EUI for the target year
            target_eui: Final target EUI (after caps/floors applied)
            sqft: Building gross floor area
            penalty_rate: Applicable penalty rate ($/kBtu)
            
        Returns:
            Penalty amount in dollars
        """
        if actual_eui <= target_eui:
            return 0.0
            
        gap = actual_eui - target_eui
        return gap * sqft * penalty_rate
    
    def calculate_never_benchmarked_penalty(self, sqft: float) -> float:
        """Calculate penalty for buildings that never benchmarked"""
        return sqft * self.config.NEVER_BENCHMARKED_RATE
    
    def get_penalty_rate(self, compliance_path: str, is_late_extension: bool = False) -> float:
        """
        Get the appropriate penalty rate for a compliance path.
        
        Args:
            compliance_path: One of 'standard', 'aco', 'extension', 'never_benchmarked'
            is_late_extension: Whether this is a late timeline extension
            
        Returns:
            Penalty rate in $/kBtu (or $/sqft for never benchmarked)
        """
        rates = {
            'standard': self.config.STANDARD_RATE,
            'aco': self.config.ACO_RATE,
            'extension': self.config.EXTENSION_RATE,
            'never_benchmarked': self.config.NEVER_BENCHMARKED_RATE
        }
        
        base_rate = rates.get(compliance_path.lower(), self.config.STANDARD_RATE)
        
        # Add late extension penalty if applicable
        if is_late_extension and compliance_path != 'never_benchmarked':
            base_rate += self.config.LATE_EXTENSION_ADDON
            
        return base_rate
    
    def get_target_years(self, compliance_path: str, 
                        first_interim_year: Optional[int] = None) -> List[int]:
        """
        Get target years for a compliance path.
        
        Args:
            compliance_path: One of 'standard', 'aco', 'extension'
            first_interim_year: Override for first standard path year
            
        Returns:
            List of target years
        """
        if compliance_path.lower() == 'aco':
            return self.config.ACO_TARGET_YEARS
        elif compliance_path.lower() == 'standard':
            if first_interim_year and first_interim_year != 2025:
                # Adjust standard years based on first interim
                offset = first_interim_year - 2025
                return [year + offset for year in self.config.STANDARD_TARGET_YEARS]
            return self.config.STANDARD_TARGET_YEARS
        elif compliance_path.lower() == 'extension':
            # Extension typically to 2030 or 2032
            return [2030]  # Or 2032 depending on specifics
        else:
            return self.config.STANDARD_TARGET_YEARS
    
    def calculate_all_penalties(self, building_data: Dict) -> pd.DataFrame:
        """
        Calculate all penalties for a building through its compliance timeline.
        
        Args:
            building_data: Dictionary with building information including:
                - building_id: Building ID
                - sqft: Gross floor area
                - baseline_eui: Baseline EUI
                - current_eui: Current weather normalized EUI
                - is_mai: Boolean for MAI designation
                - compliance_path: 'standard' or 'aco'
                - first_interim_year: First target year (default 2025)
                - raw_targets: Dict of year -> raw target EUI
                - actual_euis: Dict of year -> actual EUI (optional)
                
        Returns:
            DataFrame with penalty calculations by year
        """
        results = []
        
        # Extract building info
        building_id = building_data['building_id']
        sqft = building_data['sqft']
        baseline_eui = building_data['baseline_eui']
        is_mai = building_data.get('is_mai', False)
        compliance_path = building_data.get('compliance_path', 'standard')
        first_interim_year = building_data.get('first_interim_year', 2025)
        
        # Get penalty rate and target years
        penalty_rate = self.get_penalty_rate(compliance_path)
        target_years = self.get_target_years(compliance_path, first_interim_year)
        
        # Calculate penalties for each target year
        for target_year in target_years:
            # Get raw target and apply caps/floors
            raw_target = building_data['raw_targets'].get(target_year, 0)
            final_target = self.apply_target_caps_and_floors(
                raw_target, baseline_eui, is_mai
            )
            
            # Get actual EUI (use current if not specified)
            actual_eui = building_data.get('actual_euis', {}).get(
                target_year, building_data.get('current_eui', 0)
            )
            
            # Calculate penalty
            penalty = self.calculate_penalty(
                actual_eui, final_target, sqft, penalty_rate
            )
            
            results.append({
                'building_id': building_id,
                'target_year': target_year,
                'payment_year': target_year + 1,
                'actual_eui': actual_eui,
                'raw_target_eui': raw_target,
                'final_target_eui': final_target,
                'gap_eui': max(0, actual_eui - final_target),
                'penalty_rate': penalty_rate,
                'penalty_amount': penalty,
                'compliance_path': compliance_path,
                'is_mai': is_mai
            })
        
        # Add annual penalties after final target if still non-compliant
        final_year = target_years[-1]
        final_result = results[-1]
        
        if final_result['penalty_amount'] > 0:
            # Building is non-compliant at final target
            for year in range(final_year + 1, final_year + 13):  # 12 years of annual
                results.append({
                    'building_id': building_id,
                    'target_year': year,
                    'payment_year': year + 1,
                    'actual_eui': actual_eui,  # Assume no improvement
                    'raw_target_eui': final_result['raw_target_eui'],
                    'final_target_eui': final_result['final_target_eui'],
                    'gap_eui': final_result['gap_eui'],
                    'penalty_rate': penalty_rate,
                    'penalty_amount': final_result['penalty_amount'],
                    'compliance_path': compliance_path,
                    'is_mai': is_mai
                })
        
        return pd.DataFrame(results)
    
    def calculate_npv_penalties(self, penalties_df: pd.DataFrame, 
                               discount_rate: float = 0.07,
                               base_year: int = 2024) -> pd.DataFrame:
        """
        Calculate Net Present Value of penalties.
        
        Args:
            penalties_df: DataFrame from calculate_all_penalties
            discount_rate: Annual discount rate (default 7%)
            base_year: Year to discount to (default 2024)
            
        Returns:
            DataFrame with NPV calculations added
        """
        df = penalties_df.copy()
        
        # Calculate years from base for discounting
        df['years_from_base'] = df['payment_year'] - base_year
        
        # Calculate discount factor
        df['discount_factor'] = 1 / (1 + discount_rate) ** df['years_from_base']
        
        # Calculate NPV of each penalty
        df['penalty_npv'] = df['penalty_amount'] * df['discount_factor']
        
        return df
    
    def compare_compliance_paths(self, building_data: Dict) -> Dict:
        """
        Compare standard vs ACO path for a building.
        
        Args:
            building_data: Building information dictionary
            
        Returns:
            Dictionary with comparison results and recommendation
        """
        # Calculate penalties for standard path
        standard_data = building_data.copy()
        standard_data['compliance_path'] = 'standard'
        standard_penalties = self.calculate_all_penalties(standard_data)
        standard_npv = self.calculate_npv_penalties(standard_penalties)
        
        # Calculate penalties for ACO path
        aco_data = building_data.copy()
        aco_data['compliance_path'] = 'aco'
        aco_penalties = self.calculate_all_penalties(aco_data)
        aco_npv = self.calculate_npv_penalties(aco_penalties)
        
        # Summarize results
        standard_total = standard_penalties['penalty_amount'].sum()
        standard_total_npv = standard_npv['penalty_npv'].sum()
        aco_total = aco_penalties['penalty_amount'].sum()
        aco_total_npv = aco_npv['penalty_npv'].sum()
        
        # Determine recommendation
        npv_savings = standard_total_npv - aco_total_npv
        recommendation = 'aco' if npv_savings > 0 else 'standard'
        
        return {
            'building_id': building_data['building_id'],
            'standard_total_nominal': standard_total,
            'standard_total_npv': standard_total_npv,
            'aco_total_nominal': aco_total,
            'aco_total_npv': aco_total_npv,
            'npv_savings_with_aco': npv_savings,
            'recommendation': recommendation,
            'standard_penalties': standard_penalties,
            'aco_penalties': aco_penalties
        }


# Example usage with MAI designation
if __name__ == "__main__":
    # Example MAI lookup from MAIPropertyUseTypes Report.csv
    mai_buildings = {
        '1122': True,  # Data Center with MAI
        '1153': True,  # Distribution Center with MAI
        '2604': True,  # Data Center with MAI
        # ... etc
    }
    
    # Initialize calculator with MAI lookup
    calculator = EnergizeDenverPenaltyCalculator(mai_lookup=mai_buildings)
    
    # Example building data
    example_building = {
        'building_id': '2952',
        'sqft': 50000,
        'baseline_eui': 100,
        'current_eui': 85,
        'is_mai': False,  # Or check: calculator.is_mai_designated('2952')
        'compliance_path': 'standard',
        'first_interim_year': 2025,
        'raw_targets': {
            2025: 70,
            2027: 55,
            2030: 40  # Will be capped to 58
        }
    }
    
    # Calculate penalties
    penalties = calculator.calculate_all_penalties(example_building)
    print("\nPenalty Schedule:")
    print(penalties[['target_year', 'payment_year', 'final_target_eui', 
                    'gap_eui', 'penalty_amount']].head(10))
    
    # Compare paths
    comparison = calculator.compare_compliance_paths(example_building)
    print(f"\nPath Comparison:")
    print(f"Standard Path NPV: ${comparison['standard_total_npv']:,.0f}")
    print(f"ACO Path NPV: ${comparison['aco_total_npv']:,.0f}")
    print(f"Recommendation: {comparison['recommendation'].upper()}")
