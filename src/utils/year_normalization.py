"""
Suggested File Name: year_normalization.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Handle year mapping for aggregate portfolio analysis of Energize Denver buildings

This module provides functionality to:
1. Map actual target years to normalized years for aggregation
2. Track how many buildings map to each normalized year
3. Support both Standard and ACO pathway normalization
4. Enable portfolio-wide risk assessment across different compliance years
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class YearNormalizer:
    """
    Handles year normalization for aggregate portfolio analysis.
    
    Individual buildings have different baseline and target years, but for
    portfolio-wide analysis we need to normalize to common years.
    """
    
    def __init__(self):
        """Initialize with standard normalized year mappings"""
        
        # Define normalized years for aggregation
        self.NORMALIZED_YEARS = {
            'standard': {
                'first_interim': 2025,   # Map 2024, 2025, 2026 → 2025
                'second_interim': 2027,  # All → 2027
                'final': 2030           # All → 2030
            },
            'aco': {
                'first_interim': 2028,   # All ACO → 2028
                'final': 2032           # All ACO → 2032
            }
        }
        
        # Track mapping statistics
        self.mapping_stats = defaultdict(lambda: defaultdict(int))
        
    def normalize_standard_path_year(self, actual_year: int, target_type: str) -> int:
        """
        Map actual target year to normalized year for standard path aggregation.
        
        Args:
            actual_year: The actual target year from the building data
            target_type: One of 'first_interim', 'second_interim', or 'final'
            
        Returns:
            Normalized year for aggregation
        """
        if target_type not in self.NORMALIZED_YEARS['standard']:
            raise ValueError(f"Invalid target type: {target_type}")
            
        normalized_year = self.NORMALIZED_YEARS['standard'][target_type]
        
        # Track the mapping
        self.mapping_stats[f'standard_{target_type}'][actual_year] += 1
        
        return normalized_year
    
    def normalize_aco_path_year(self, target_type: str) -> int:
        """
        Return normalized ACO years.
        
        Args:
            target_type: One of 'first_interim' or 'final'
            
        Returns:
            Normalized year for ACO path
        """
        if target_type not in self.NORMALIZED_YEARS['aco']:
            raise ValueError(f"Invalid ACO target type: {target_type}")
            
        return self.NORMALIZED_YEARS['aco'][target_type]
    
    def get_year_mapping_summary(self) -> Dict[str, Dict[int, int]]:
        """
        Get summary of how many buildings map to each normalized year.
        
        Returns:
            Dictionary showing mapping counts
        """
        return dict(self.mapping_stats)
    
    def normalize_building_targets(self, building_df: pd.DataFrame, 
                                 path: str = 'standard') -> pd.DataFrame:
        """
        Add normalized year columns to a building dataframe.
        
        Args:
            building_df: DataFrame with building data including actual target years
            path: 'standard' or 'aco' compliance path
            
        Returns:
            DataFrame with additional normalized year columns
        """
        df = building_df.copy()
        
        if path == 'standard':
            # Map actual years to normalized years
            if 'First Interim Target Year' in df.columns:
                df['normalized_first_interim_year'] = df['First Interim Target Year'].apply(
                    lambda x: self.normalize_standard_path_year(x, 'first_interim')
                )
            else:
                df['normalized_first_interim_year'] = self.NORMALIZED_YEARS['standard']['first_interim']
                
            if 'Second Interim Target Year' in df.columns:
                df['normalized_second_interim_year'] = df['Second Interim Target Year'].apply(
                    lambda x: self.normalize_standard_path_year(x, 'second_interim')
                )
            else:
                df['normalized_second_interim_year'] = self.NORMALIZED_YEARS['standard']['second_interim']
                
            df['normalized_final_year'] = self.NORMALIZED_YEARS['standard']['final']
            
        elif path == 'aco':
            # ACO path uses fixed normalized years
            df['normalized_first_interim_year'] = self.NORMALIZED_YEARS['aco']['first_interim']
            df['normalized_final_year'] = self.NORMALIZED_YEARS['aco']['final']
            
        else:
            raise ValueError(f"Invalid path: {path}. Must be 'standard' or 'aco'")
            
        return df
    
    def aggregate_penalties_by_normalized_year(self, buildings_df: pd.DataFrame,
                                             penalty_columns: Dict[str, str]) -> Dict[int, float]:
        """
        Aggregate penalties by normalized year for portfolio analysis.
        
        Args:
            buildings_df: DataFrame with building penalties and normalized years
            penalty_columns: Mapping of penalty column names to normalized year columns
                e.g., {'penalty_2025': 'normalized_first_interim_year'}
                
        Returns:
            Dictionary mapping normalized years to total penalties
        """
        aggregated = defaultdict(float)
        
        for penalty_col, year_col in penalty_columns.items():
            if penalty_col in buildings_df.columns and year_col in buildings_df.columns:
                # Group by normalized year and sum penalties
                grouped = buildings_df.groupby(year_col)[penalty_col].sum()
                for year, total_penalty in grouped.items():
                    aggregated[int(year)] += total_penalty
                    
        return dict(aggregated)
    
    def create_year_alignment_report(self, buildings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a report showing how actual years align to normalized years.
        
        Args:
            buildings_df: DataFrame with actual target year columns
            
        Returns:
            DataFrame summarizing year alignments
        """
        alignment_data = []
        
        # Analyze first interim year alignment
        if 'First Interim Target Year' in buildings_df.columns:
            first_interim_counts = buildings_df['First Interim Target Year'].value_counts()
            for actual_year, count in first_interim_counts.items():
                alignment_data.append({
                    'Target Type': 'First Interim',
                    'Actual Year': int(actual_year),
                    'Normalized Year (Standard)': self.NORMALIZED_YEARS['standard']['first_interim'],
                    'Normalized Year (ACO)': self.NORMALIZED_YEARS['aco']['first_interim'],
                    'Building Count': count,
                    'Percentage': count / len(buildings_df) * 100
                })
        
        # Analyze second interim year alignment
        if 'Second Interim Target Year' in buildings_df.columns:
            second_interim_counts = buildings_df['Second Interim Target Year'].value_counts()
            for actual_year, count in second_interim_counts.items():
                alignment_data.append({
                    'Target Type': 'Second Interim',
                    'Actual Year': int(actual_year),
                    'Normalized Year (Standard)': self.NORMALIZED_YEARS['standard']['second_interim'],
                    'Normalized Year (ACO)': '-',  # ACO doesn't have second interim
                    'Building Count': count,
                    'Percentage': count / len(buildings_df) * 100
                })
        
        return pd.DataFrame(alignment_data)
    
    def calculate_year_shift_impact(self, buildings_df: pd.DataFrame,
                                  penalty_rate: float = 0.15) -> Dict[str, float]:
        """
        Calculate the financial impact of year normalization.
        
        This shows how much penalty timing changes when we normalize years.
        
        Args:
            buildings_df: DataFrame with building data
            penalty_rate: Penalty rate per kBtu over target
            
        Returns:
            Dictionary with impact metrics
        """
        impact = {
            'buildings_with_earlier_penalties': 0,
            'buildings_with_later_penalties': 0,
            'buildings_unchanged': 0,
            'total_penalty_shift_amount': 0.0,
            'average_months_shifted': 0.0
        }
        
        if 'First Interim Target Year' not in buildings_df.columns:
            return impact
            
        # Calculate shifts for each building
        shifts = []
        for _, building in buildings_df.iterrows():
            actual_year = building.get('First Interim Target Year', 2025)
            normalized_year = self.NORMALIZED_YEARS['standard']['first_interim']
            
            year_shift = normalized_year - actual_year
            
            if year_shift < 0:
                impact['buildings_with_earlier_penalties'] += 1
            elif year_shift > 0:
                impact['buildings_with_later_penalties'] += 1
            else:
                impact['buildings_unchanged'] += 1
                
            shifts.append(year_shift)
            
            # Calculate penalty timing impact (simplified)
            if 'penalty_first_interim' in building:
                penalty = building['penalty_first_interim']
                # Discount/compound based on shift
                if year_shift != 0:
                    discount_factor = 1.07 ** year_shift  # 7% discount rate
                    impact['total_penalty_shift_amount'] += penalty * (1 - discount_factor)
        
        if shifts:
            impact['average_months_shifted'] = abs(sum(shifts) / len(shifts)) * 12
            
        return impact


# Example usage and testing
if __name__ == "__main__":
    # Create normalizer
    normalizer = YearNormalizer()
    
    # Example building data
    sample_buildings = pd.DataFrame({
        'Building ID': ['1001', '1002', '1003', '1004', '1005'],
        'First Interim Target Year': [2024, 2025, 2025, 2026, 2025],
        'Second Interim Target Year': [2027, 2027, 2027, 2027, 2027],
        'penalty_first_interim': [50000, 75000, 0, 100000, 25000],
        'penalty_second_interim': [40000, 60000, 10000, 80000, 20000],
        'penalty_final': [30000, 45000, 20000, 60000, 15000]
    })
    
    # Normalize years
    normalized_df = normalizer.normalize_building_targets(sample_buildings, 'standard')
    print("Sample normalized data:")
    print(normalized_df[['Building ID', 'First Interim Target Year', 
                        'normalized_first_interim_year']].head())
    
    # Get mapping summary
    print("\nYear mapping summary:")
    print(normalizer.get_year_mapping_summary())
    
    # Create alignment report
    alignment_report = normalizer.create_year_alignment_report(sample_buildings)
    print("\nYear alignment report:")
    print(alignment_report)
    
    # Calculate impact
    impact = normalizer.calculate_year_shift_impact(sample_buildings)
    print("\nYear normalization impact:")
    for key, value in impact.items():
        print(f"  {key}: {value}")
    
    # Aggregate penalties by normalized year
    penalty_mapping = {
        'penalty_first_interim': 'normalized_first_interim_year',
        'penalty_second_interim': 'normalized_second_interim_year',
        'penalty_final': 'normalized_final_year'
    }
    
    aggregated = normalizer.aggregate_penalties_by_normalized_year(
        normalized_df, penalty_mapping
    )
    print("\nAggregated penalties by normalized year:")
    for year, total in sorted(aggregated.items()):
        print(f"  {year}: ${total:,.0f}")
