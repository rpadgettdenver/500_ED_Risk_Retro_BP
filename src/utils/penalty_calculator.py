"""
Suggested File Name: penalty_calculator.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Unified penalty calculation module ensuring consistency across all scripts

This module provides:
1. Correct penalty rates per April 2025 Technical Guidance
2. NPV calculations with 7% discount rate
3. 42% maximum reduction cap for all buildings
4. MAI floor of 52.9 kBtu/sqft
5. Opt-in decision logic with multiple factors
6. Technical feasibility scoring
"""

import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime


class PenaltyCalculator:
    """Unified penalty calculator for Energize Denver compliance analysis"""
    
    def __init__(self):
        # Penalty rates per April 2025 Technical Guidance
        self.PENALTY_RATE_STANDARD = 0.15  # $/kBtu for standard path
        self.PENALTY_RATE_OPTIN = 0.23    # $/kBtu for opt-in path
        self.PENALTY_RATE_EXTENSION = 0.35  # $/kBtu for timeline extension
        
        # Financial parameters
        self.DISCOUNT_RATE = 0.07  # 7% for NPV calculations
        
        # Compliance parameters
        self.MAX_REDUCTION_CAP = 0.42  # 42% maximum reduction from baseline
        self.MAI_FLOOR = 52.9  # Minimum EUI for MAI buildings
        
        # Target years for each path
        self.STANDARD_PATH_YEARS = [2025, 2027, 2030]
        self.OPTIN_PATH_YEARS = [2028, 2032]
        
        # Retrofit cost estimates ($/sqft)
        self.RETROFIT_COSTS = {
            'light': 5.0,      # <15% reduction
            'moderate': 12.0,  # 15-30% reduction
            'deep': 25.0       # >30% reduction
        }
        
    def apply_target_adjustments(self, 
                               target_eui: float, 
                               baseline_eui: float,
                               property_type: str,
                               is_mai: bool = False) -> Tuple[float, str]:
        """
        Apply 42% cap and MAI floor to target EUI
        
        Args:
            target_eui: Original calculated target
            baseline_eui: Building's baseline EUI
            property_type: Building property type
            is_mai: Whether building is Manufacturing/Agricultural/Industrial
            
        Returns:
            Tuple of (adjusted_target, adjustment_reason)
        """
        # Calculate 42% reduction cap
        cap_target = baseline_eui * (1 - self.MAX_REDUCTION_CAP)
        
        # For MAI buildings, also consider the floor
        if is_mai or property_type in ['Manufacturing/Industrial Plant', 'Data Center', 'Agricultural']:
            # Target is the HIGHEST (least stringent) of:
            # 1. Original target
            # 2. 42% cap
            # 3. MAI floor
            adjusted_target = max(target_eui, cap_target, self.MAI_FLOOR)
            
            if adjusted_target == self.MAI_FLOOR:
                reason = f"MAI floor applied ({self.MAI_FLOOR} kBtu/sqft)"
            elif adjusted_target == cap_target:
                reason = f"42% cap applied (from {baseline_eui:.1f} to {cap_target:.1f})"
            else:
                reason = "No adjustment needed"
        else:
            # For non-MAI buildings, apply only the 42% cap
            adjusted_target = max(target_eui, cap_target)
            
            if adjusted_target == cap_target:
                reason = f"42% cap applied (from {baseline_eui:.1f} to {cap_target:.1f})"
            else:
                reason = "No adjustment needed"
                
        return adjusted_target, reason
    
    def calculate_penalty(self, 
                         current_eui: float,
                         target_eui: float,
                         sqft: float,
                         penalty_rate: float) -> float:
        """
        Calculate penalty for a single year
        
        Args:
            current_eui: Building's current EUI
            target_eui: Target EUI for the year
            sqft: Building square footage
            penalty_rate: Penalty rate ($/kBtu)
            
        Returns:
            Penalty amount in dollars
        """
        if current_eui <= target_eui:
            return 0.0
            
        excess_eui = current_eui - target_eui
        penalty = excess_eui * sqft * penalty_rate
        return penalty
    
    def calculate_npv(self, amount: float, year: int, base_year: int = 2024) -> float:
        """
        Calculate Net Present Value of a future payment
        
        Args:
            amount: Future payment amount
            year: Year of payment
            base_year: Base year for NPV calculation (default 2024)
            
        Returns:
            Present value of the payment
        """
        years_from_base = year - base_year
        if years_from_base < 0:
            return amount  # Past payments are at full value
            
        npv = amount / ((1 + self.DISCOUNT_RATE) ** years_from_base)
        return npv
    
    def calculate_path_penalties(self,
                               current_eui: float,
                               sqft: float,
                               targets: Dict[int, float],
                               path: str = 'standard',
                               include_ongoing: bool = False,
                               analysis_years: int = 15) -> Dict:
        """
        Calculate penalties for a compliance path
        
        Args:
            current_eui: Building's current EUI
            sqft: Building square footage
            targets: Dictionary of {year: target_eui}
            path: 'standard' or 'optin'
            include_ongoing: Whether to include annual penalties after final target
            analysis_years: Total years to analyze (if include_ongoing=True)
            
        Returns:
            Dictionary with penalty details
        """
        penalty_rate = self.PENALTY_RATE_STANDARD if path == 'standard' else self.PENALTY_RATE_OPTIN
        target_years = self.STANDARD_PATH_YEARS if path == 'standard' else self.OPTIN_PATH_YEARS
        
        penalties = {}
        total_nominal = 0
        total_npv = 0
        
        # Calculate penalties for target years
        for year in target_years:
            if year in targets:
                penalty = self.calculate_penalty(current_eui, targets[year], sqft, penalty_rate)
                npv = self.calculate_npv(penalty, year)
                
                penalties[year] = {
                    'target': targets[year],
                    'excess': max(0, current_eui - targets[year]),
                    'penalty': penalty,
                    'npv': npv
                }
                
                total_nominal += penalty
                total_npv += npv
        
        # Add ongoing annual penalties if requested
        if include_ongoing:
            final_year = target_years[-1]
            final_target = targets.get(final_year, 0)
            end_year = 2024 + analysis_years
            
            for year in range(final_year + 1, end_year + 1):
                penalty = self.calculate_penalty(current_eui, final_target, sqft, penalty_rate)
                npv = self.calculate_npv(penalty, year)
                
                total_nominal += penalty
                total_npv += npv
        
        return {
            'penalties_by_year': penalties,
            'total_nominal': total_nominal,
            'total_npv': total_npv,
            'penalty_rate': penalty_rate,
            'path': path
        }
    
    def estimate_retrofit_cost(self, 
                             current_eui: float,
                             target_eui: float,
                             sqft: float) -> Dict:
        """
        Estimate retrofit cost based on required reduction
        
        Args:
            current_eui: Current building EUI
            target_eui: Target EUI
            sqft: Building square footage
            
        Returns:
            Dictionary with retrofit cost estimates
        """
        if current_eui <= target_eui:
            return {
                'reduction_needed': 0,
                'reduction_pct': 0,
                'retrofit_level': 'none',
                'cost_per_sqft': 0,
                'total_cost': 0
            }
            
        reduction_needed = current_eui - target_eui
        reduction_pct = (reduction_needed / current_eui) * 100
        
        # Determine retrofit level
        if reduction_pct < 15:
            level = 'light'
        elif reduction_pct < 30:
            level = 'moderate'
        else:
            level = 'deep'
            
        cost_per_sqft = self.RETROFIT_COSTS[level]
        total_cost = cost_per_sqft * sqft
        
        return {
            'reduction_needed': reduction_needed,
            'reduction_pct': reduction_pct,
            'retrofit_level': level,
            'cost_per_sqft': cost_per_sqft,
            'total_cost': total_cost
        }
    
    def calculate_technical_difficulty(self,
                                     reduction_pct: float,
                                     building_age: int,
                                     property_type: str) -> Dict:
        """
        Calculate technical difficulty score for achieving targets
        
        Args:
            reduction_pct: Required % reduction
            building_age: Age of building in years
            property_type: Building type
            
        Returns:
            Dictionary with difficulty assessment
        """
        # Base difficulty from reduction percentage
        if reduction_pct > 50:
            base_score = 100  # Nearly impossible
        elif reduction_pct > 40:
            base_score = 80   # Very difficult
        elif reduction_pct > 30:
            base_score = 60   # Difficult
        elif reduction_pct > 20:
            base_score = 40   # Moderate
        else:
            base_score = 20   # Achievable
            
        # Age adjustment
        age_factor = 1.0
        if building_age > 50:
            age_factor = 1.5  # Very old buildings are harder
        elif building_age > 30:
            age_factor = 1.2
            
        # Property type adjustment
        type_factor = 1.0
        difficult_types = ['Hospital', 'Data Center', 'Manufacturing/Industrial Plant']
        if property_type in difficult_types:
            type_factor = 1.3
            
        final_score = min(100, base_score * age_factor * type_factor)
        
        # Determine feasibility
        if final_score >= 80:
            feasibility = 'very_difficult'
        elif final_score >= 60:
            feasibility = 'difficult'
        elif final_score >= 40:
            feasibility = 'moderate'
        else:
            feasibility = 'achievable'
            
        return {
            'score': final_score,
            'feasibility': feasibility,
            'base_difficulty': base_score,
            'age_factor': age_factor,
            'type_factor': type_factor
        }
    
    def make_optin_recommendation(self,
                                building_data: Dict,
                                standard_penalties: Dict,
                                optin_penalties: Dict,
                                retrofit_cost: Dict,
                                technical_difficulty: Dict) -> Dict:
        """
        Make opt-in recommendation based on multiple factors
        
        Args:
            building_data: Building information
            standard_penalties: Standard path penalty analysis
            optin_penalties: Opt-in path penalty analysis
            retrofit_cost: Retrofit cost estimates
            technical_difficulty: Technical difficulty assessment
            
        Returns:
            Dictionary with recommendation and reasoning
        """
        # Financial advantage of opt-in (positive = opt-in saves money)
        npv_advantage = standard_penalties['total_npv'] - optin_penalties['total_npv']
        
        # Decision factors
        factors = {
            'npv_advantage': npv_advantage,
            'meets_2025_target': building_data.get('meets_2025_target', False),
            'meets_all_targets': building_data.get('meets_all_targets', False),
            'reduction_pct': retrofit_cost['reduction_pct'],
            'technical_score': technical_difficulty['score'],
            'cash_constrained': building_data.get('cash_constrained', False),
            'is_mai': building_data.get('is_mai', False)
        }
        
        # Decision logic
        should_optin = False
        confidence = 50  # Default moderate confidence
        primary_reason = ""
        secondary_reasons = []
        
        # Always opt-in cases
        if not factors['meets_all_targets'] and factors['reduction_pct'] > 40:
            should_optin = True
            confidence = 100
            primary_reason = "Cannot meet targets - reduction >40% required"
            
        elif factors['cash_constrained'] and standard_penalties['penalties_by_year'].get(2025, {}).get('penalty', 0) > 100000:
            should_optin = True
            confidence = 90
            primary_reason = "Cash flow constraints - cannot afford early penalties"
            
        elif factors['technical_score'] >= 80:
            should_optin = True
            confidence = 95
            primary_reason = "Technical infeasibility - nearly impossible to retrofit"
            
        # Never opt-in cases
        elif factors['meets_2025_target']:
            should_optin = False
            confidence = 100
            primary_reason = "Already meets 2025 target"
            
        elif factors['reduction_pct'] < 10:
            should_optin = False
            confidence = 95
            primary_reason = "Minor reduction needed (<10%)"
            
        elif npv_advantage < -100000:
            should_optin = False
            confidence = 90
            primary_reason = f"Opt-in costs ${abs(npv_advantage):,.0f} more (NPV)"
            
        # Financial decision for others
        elif npv_advantage > 50000:
            should_optin = True
            confidence = 85
            primary_reason = f"Opt-in saves ${npv_advantage:,.0f} (NPV)"
            
        elif npv_advantage > 0:
            should_optin = True
            confidence = 70
            primary_reason = f"Modest financial advantage ${npv_advantage:,.0f} (NPV)"
            
        else:
            should_optin = False
            confidence = 60
            primary_reason = "Default path slightly favorable"
            
        # Add secondary reasons
        if factors['is_mai']:
            secondary_reasons.append("MAI building considerations apply")
            
        if factors['technical_score'] >= 60:
            secondary_reasons.append("Difficult retrofit required")
            
        if abs(npv_advantage) < 50000:
            secondary_reasons.append("Close financial decision")
            
        return {
            'recommendation': 'opt-in' if should_optin else 'standard',
            'confidence': confidence,
            'primary_reason': primary_reason,
            'secondary_reasons': secondary_reasons,
            'npv_advantage': npv_advantage,
            'decision_factors': factors
        }


# Convenience functions for common use cases
def calculate_building_penalties(building_data: Dict, 
                               include_ongoing: bool = False) -> Dict:
    """
    Calculate complete penalty analysis for a building
    
    Args:
        building_data: Dictionary with building information including:
            - current_eui
            - baseline_eui
            - sqft
            - property_type
            - is_mai
            - targets (dict of year: target_eui)
            - building_age
            - cash_constrained (optional)
        include_ongoing: Whether to include ongoing annual penalties
        
    Returns:
        Complete analysis including penalties, NPV, and recommendations
    """
    calc = PenaltyCalculator()
    
    # Apply target adjustments
    adjusted_targets = {}
    for year, target in building_data['targets'].items():
        adjusted, reason = calc.apply_target_adjustments(
            target,
            building_data['baseline_eui'],
            building_data['property_type'],
            building_data.get('is_mai', False)
        )
        adjusted_targets[year] = adjusted
    
    # Calculate penalties for both paths
    standard_penalties = calc.calculate_path_penalties(
        building_data['current_eui'],
        building_data['sqft'],
        adjusted_targets,
        'standard',
        include_ongoing
    )
    
    optin_penalties = calc.calculate_path_penalties(
        building_data['current_eui'],
        building_data['sqft'],
        adjusted_targets,
        'optin',
        include_ongoing
    )
    
    # Estimate retrofit costs
    final_target = adjusted_targets.get(2030, adjusted_targets.get(2032, 0))
    retrofit_cost = calc.estimate_retrofit_cost(
        building_data['current_eui'],
        final_target,
        building_data['sqft']
    )
    
    # Calculate technical difficulty
    technical_difficulty = calc.calculate_technical_difficulty(
        retrofit_cost['reduction_pct'],
        building_data.get('building_age', 30),
        building_data['property_type']
    )
    
    # Check if meets targets
    building_data['meets_2025_target'] = building_data['current_eui'] <= adjusted_targets.get(2025, float('inf'))
    building_data['meets_all_targets'] = all(
        building_data['current_eui'] <= adjusted_targets.get(year, float('inf'))
        for year in [2025, 2027, 2030]
    )
    
    # Make recommendation
    recommendation = calc.make_optin_recommendation(
        building_data,
        standard_penalties,
        optin_penalties,
        retrofit_cost,
        technical_difficulty
    )
    
    return {
        'building_id': building_data.get('building_id'),
        'current_eui': building_data['current_eui'],
        'adjusted_targets': adjusted_targets,
        'standard_path': standard_penalties,
        'optin_path': optin_penalties,
        'retrofit_analysis': retrofit_cost,
        'technical_difficulty': technical_difficulty,
        'recommendation': recommendation,
        'analysis_date': datetime.now().isoformat()
    }
