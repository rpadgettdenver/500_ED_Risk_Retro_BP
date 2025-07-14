"""
Suggested File Name: opt_in_predictor.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Python implementation of opt-in decision logic for Energize Denver buildings

This module ports the BigQuery opt-in decision model to Python, enabling:
1. Building-level opt-in predictions based on financial and technical factors
2. Confidence scoring for each decision
3. Batch processing for portfolio-wide predictions
4. Integration with other Python-based analysis tools
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class OptInDecision:
    """Data class to hold opt-in decision results"""
    should_opt_in: bool
    confidence: float
    primary_rationale: str
    npv_advantage: float
    decision_factors: Dict[str, float]


class OptInPredictor:
    """
    Predicts whether buildings should opt into the ACO compliance path.
    
    Based on the logic from create_opt_in_decision_model.py but implemented
    in Python for local analysis and integration.
    """
    
    def __init__(self):
        """Initialize with decision parameters"""
        
        # Penalty rates (corrected from BigQuery script)
        self.PENALTY_RATE_STANDARD = 0.15  # $/kBtu over target
        self.PENALTY_RATE_ACO = 0.23       # $/kBtu over target
        self.DISCOUNT_RATE = 0.07           # 7% for NPV calculations
        
        # Retrofit cost assumptions ($/sqft) by reduction needed
        self.retrofit_cost_per_reduction = {
            'light': 5.0,      # <15% reduction
            'moderate': 12.0,  # 15-30% reduction  
            'deep': 25.0       # >30% reduction
        }
        
        # MAI floor for manufacturing buildings
        self.MAI_FLOOR = 52.9  # kBtu/sqft
        
    def predict_opt_in(self, building_data: Dict) -> OptInDecision:
        """
        Predict whether a building should opt into the ACO path.
        
        Args:
            building_data: Dictionary containing:
                - building_id
                - property_type
                - sqft
                - current_eui
                - baseline_eui
                - first_interim_target
                - second_interim_target
                - final_target
                - year_built (optional)
                - is_mai (optional)
                - is_epb (optional)
                
        Returns:
            OptInDecision object with prediction and reasoning
        """
        # Extract data
        sqft = building_data['sqft']
        current_eui = building_data['current_eui']
        baseline_eui = building_data.get('baseline_eui', current_eui)
        
        # Apply MAI floor if applicable
        is_mai = building_data.get('is_mai', False)
        property_type = building_data.get('property_type', '')
        
        # Adjust targets for MAI buildings
        first_target = self._apply_mai_adjustment(
            building_data['first_interim_target'], is_mai, property_type
        )
        second_target = self._apply_mai_adjustment(
            building_data['second_interim_target'], is_mai, property_type
        )
        final_target = self._apply_mai_adjustment(
            building_data['final_target'], is_mai, property_type
        )
        
        # Calculate gaps
        gap_2025 = max(0, current_eui - first_target)
        gap_2027 = max(0, current_eui - second_target)
        gap_2030 = max(0, current_eui - final_target)
        
        # Calculate reduction percentages
        pct_reduction_2030 = (current_eui - final_target) / current_eui * 100 if current_eui > 0 else 0
        
        # Calculate penalties for each path
        standard_penalties = self._calculate_standard_path_penalties(
            sqft, gap_2025, gap_2027, gap_2030
        )
        # ACO 2028 uses First Interim Target (same as standard 2025)
        aco_penalties = self._calculate_aco_path_penalties(
            sqft, gap_2025, gap_2030  # ACO 2028 uses first interim, 2032 uses final
        )
        
        # Calculate NPV advantage of opt-in
        npv_advantage = standard_penalties['npv_total'] - aco_penalties['npv_total']
        
        # Estimate retrofit cost
        retrofit_cost = self._estimate_retrofit_cost(sqft, pct_reduction_2030)
        
        # Calculate technical difficulty
        building_age = 2025 - building_data.get('year_built', 1990)
        technical_score = self._calculate_technical_difficulty(pct_reduction_2030, building_age)
        
        # Check cash flow constraints
        cash_constrained = self._is_cash_flow_constrained(
            property_type, standard_penalties['penalty_2025']
        )
        
        # Decision factors
        decision_factors = {
            'npv_advantage': npv_advantage,
            'pct_reduction_needed': pct_reduction_2030,
            'technical_score': technical_score,
            'cash_constrained': cash_constrained,
            'building_age': building_age,
            'is_mai': is_mai,
            'gap_2025': gap_2025,
            'gap_2027': gap_2027,
            'gap_2030': gap_2030,
            'retrofit_cost': retrofit_cost
        }
        
        # Make decision
        decision, confidence, rationale = self._make_decision(decision_factors)
        
        return OptInDecision(
            should_opt_in=decision,
            confidence=confidence,
            primary_rationale=rationale,
            npv_advantage=npv_advantage,
            decision_factors=decision_factors
        )
    
    def _apply_mai_adjustment(self, target: float, is_mai: bool, 
                            property_type: str) -> float:
        """Apply MAI floor adjustment to targets"""
        if is_mai or property_type == 'Manufacturing/Industrial Plant':
            return max(target, self.MAI_FLOOR)
        return target
    
    def _calculate_standard_path_penalties(self, sqft: float, gap_2025: float,
                                         gap_2027: float, gap_2030: float) -> Dict:
        """Calculate penalties for standard compliance path"""
        # Nominal penalties
        penalty_2025 = gap_2025 * sqft * self.PENALTY_RATE_STANDARD
        penalty_2027 = gap_2027 * sqft * self.PENALTY_RATE_STANDARD
        penalty_2030 = gap_2030 * sqft * self.PENALTY_RATE_STANDARD
        
        # NPV calculations (discounted to 2025)
        npv_2025 = penalty_2025  # No discounting for year 0
        npv_2027 = penalty_2027 / ((1 + self.DISCOUNT_RATE) ** 2)
        npv_2030 = penalty_2030 / ((1 + self.DISCOUNT_RATE) ** 5)
        
        # Annual penalties after 2030 (assuming continued non-compliance)
        # Calculate NPV of 12 years of annual penalties (2031-2042)
        annual_penalty_npv = 0
        for year in range(6, 18):  # Years 6-17 from 2025
            annual_penalty_npv += penalty_2030 / ((1 + self.DISCOUNT_RATE) ** year)
        
        return {
            'penalty_2025': penalty_2025,
            'penalty_2027': penalty_2027,
            'penalty_2030': penalty_2030,
            'npv_2025': npv_2025,
            'npv_2027': npv_2027,
            'npv_2030': npv_2030,
            'npv_annual': annual_penalty_npv,
            'npv_total': npv_2025 + npv_2027 + npv_2030 + annual_penalty_npv,
            'nominal_total': penalty_2025 + penalty_2027 + penalty_2030 * 13  # Through 2042
        }
    
    def _calculate_aco_path_penalties(self, sqft: float, gap_2028: float, gap_2032: float) -> Dict:
        """Calculate penalties for ACO/opt-in path"""
        # ACO has penalties in 2028 (uses First Interim Target) and 2032 (uses Final Target)
        penalty_2028 = gap_2028 * sqft * self.PENALTY_RATE_ACO
        penalty_2032 = gap_2032 * sqft * self.PENALTY_RATE_ACO
        
        # NPV calculations (discounted to 2025)
        npv_2028 = penalty_2028 / ((1 + self.DISCOUNT_RATE) ** 3)
        npv_2032 = penalty_2032 / ((1 + self.DISCOUNT_RATE) ** 7)
        
        # Annual penalties after 2032
        annual_penalty_npv = 0
        for year in range(8, 18):  # Years 8-17 from 2025
            annual_penalty_npv += penalty_2032 / ((1 + self.DISCOUNT_RATE) ** year)
        
        return {
            'penalty_2028': penalty_2028,
            'penalty_2032': penalty_2032,
            'npv_2028': npv_2028,
            'npv_2032': npv_2032,
            'npv_annual': annual_penalty_npv,
            'npv_total': npv_2028 + npv_2032 + annual_penalty_npv,
            'nominal_total': penalty_2028 + penalty_2032 * 11  # Through 2042
        }
    
    def _estimate_retrofit_cost(self, sqft: float, pct_reduction: float) -> float:
        """Estimate retrofit cost based on reduction needed"""
        if pct_reduction < 15:
            cost_per_sqft = self.retrofit_cost_per_reduction['light']
        elif pct_reduction < 30:
            cost_per_sqft = self.retrofit_cost_per_reduction['moderate']
        else:
            cost_per_sqft = self.retrofit_cost_per_reduction['deep']
            
        return sqft * cost_per_sqft
    
    def _calculate_technical_difficulty(self, pct_reduction: float, 
                                      building_age: float) -> float:
        """Calculate technical difficulty score (0-100)"""
        # Base score on reduction percentage
        if pct_reduction > 50:
            base_score = 100
        elif pct_reduction > 40:
            base_score = 80
        elif pct_reduction > 30:
            base_score = 60
        elif pct_reduction > 20:
            base_score = 40
        else:
            base_score = 20
            
        # Adjust for building age
        age_factor = min(20, building_age / 2.5)  # Max 20 points for age
        
        return min(100, base_score + age_factor)
    
    def _is_cash_flow_constrained(self, property_type: str, 
                                penalty_2025: float) -> bool:
        """Determine if building is cash flow constrained"""
        # Certain property types are assumed constrained
        if property_type in ['Affordable Housing', 'Senior Care Community', 
                           'Senior Living Community']:
            return True
            
        # Large early penalties indicate constraint
        if penalty_2025 > 500000:
            return True
            
        return False
    
    def _make_decision(self, factors: Dict) -> Tuple[bool, float, str]:
        """
        Make opt-in decision based on multiple factors.
        
        Returns:
            Tuple of (should_opt_in, confidence, primary_rationale)
        """
        # Extract key factors
        npv_advantage = factors['npv_advantage']
        pct_reduction = factors['pct_reduction_needed']
        technical_score = factors['technical_score']
        cash_constrained = factors['cash_constrained']
        is_mai = factors['is_mai']
        gap_2025 = factors['gap_2025']
        gap_2027 = factors['gap_2027']
        gap_2030 = factors['gap_2030']
        
        # Always opt-in cases
        if gap_2025 > 0 and gap_2027 > 0 and gap_2030 > 0:
            return True, 100, "Cannot meet any targets"
            
        if cash_constrained and gap_2025 > 0:
            penalty_2025 = gap_2025 * factors.get('sqft', 50000) * self.PENALTY_RATE_STANDARD
            if penalty_2025 > 100000:
                return True, 95, "Cash flow constraints"
                
        if technical_score >= 80:
            return True, 90, "Technical infeasibility"
            
        if is_mai and pct_reduction > 30:
            return True, 85, "MAI building with major reduction"
        
        # Never opt-in cases
        if gap_2025 <= 0:
            return False, 100, "Already meets 2025 target"
            
        if npv_advantage < -100000:
            return False, 95, "Opt-in too expensive"
            
        if pct_reduction < 10:
            return False, 90, "Minor reduction needed"
        
        # Financial decision for others
        if npv_advantage > 100000:
            return True, 80, "Significant financial advantage"
        elif npv_advantage > 0:
            return True, 60, "Modest financial advantage"
        else:
            confidence = max(50, 70 - abs(npv_advantage) / 10000)
            return False, confidence, "Marginal decision"
    
    def get_decision_confidence(self, building_data: Dict) -> float:
        """
        Get just the confidence score for a building's opt-in decision.
        
        Args:
            building_data: Building information dictionary
            
        Returns:
            Confidence score (0-100)
        """
        decision = self.predict_opt_in(building_data)
        return decision.confidence
    
    def predict_portfolio(self, buildings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict opt-in decisions for a portfolio of buildings.
        
        Args:
            buildings_df: DataFrame with building data
            
        Returns:
            DataFrame with opt-in predictions added
        """
        predictions = []
        
        for idx, building in buildings_df.iterrows():
            # Convert row to dictionary
            building_data = building.to_dict()
            
            # Make prediction
            decision = self.predict_opt_in(building_data)
            
            # Add results to building data
            building_data['should_opt_in'] = decision.should_opt_in
            building_data['opt_in_confidence'] = decision.confidence
            building_data['opt_in_rationale'] = decision.primary_rationale
            building_data['npv_advantage'] = decision.npv_advantage
            
            predictions.append(building_data)
        
        return pd.DataFrame(predictions)


# Example usage and testing
if __name__ == "__main__":
    # Create predictor
    predictor = OptInPredictor()
    
    # Example building data
    test_building = {
        'building_id': '2952',
        'property_type': 'Multifamily Housing',
        'sqft': 52826,
        'current_eui': 69.0,
        'baseline_eui': 69.0,
        'first_interim_target': 65.4,
        'second_interim_target': 63.2,
        'final_target': 61.0,
        'year_built': 1970,
        'is_mai': False,
        'is_epb': True
    }
    
    # Make prediction
    decision = predictor.predict_opt_in(test_building)
    
    print("Opt-In Decision Analysis")
    print("=" * 50)
    print(f"Building ID: {test_building['building_id']}")
    print(f"Should Opt-In: {decision.should_opt_in}")
    print(f"Confidence: {decision.confidence:.0f}%")
    print(f"Primary Rationale: {decision.primary_rationale}")
    print(f"NPV Advantage: ${decision.npv_advantage:,.0f}")
    print("\nDecision Factors:")
    for factor, value in decision.decision_factors.items():
        if isinstance(value, bool):
            print(f"  {factor}: {value}")
        elif isinstance(value, float):
            print(f"  {factor}: {value:.2f}")
        else:
            print(f"  {factor}: {value}")
    
    # Test portfolio prediction
    print("\n\nPortfolio Analysis Example:")
    print("-" * 50)
    
    portfolio = pd.DataFrame([
        {
            'building_id': '1001',
            'property_type': 'Office',
            'sqft': 100000,
            'current_eui': 85,
            'baseline_eui': 90,
            'first_interim_target': 75,
            'second_interim_target': 65,
            'final_target': 55,
            'year_built': 1980
        },
        {
            'building_id': '1002',
            'property_type': 'Manufacturing/Industrial Plant',
            'sqft': 200000,
            'current_eui': 120,
            'baseline_eui': 130,
            'first_interim_target': 100,
            'second_interim_target': 80,
            'final_target': 60,
            'year_built': 1970,
            'is_mai': True
        },
        {
            'building_id': '1003',
            'property_type': 'Affordable Housing',
            'sqft': 75000,
            'current_eui': 70,
            'baseline_eui': 75,
            'first_interim_target': 68,
            'second_interim_target': 65,
            'final_target': 60,
            'year_built': 1960
        }
    ])
    
    # Predict for portfolio
    results = predictor.predict_portfolio(portfolio)
    
    # Summary
    opt_in_count = results['should_opt_in'].sum()
    print(f"\nPortfolio Summary:")
    print(f"  Total Buildings: {len(results)}")
    print(f"  Recommended Opt-In: {opt_in_count} ({opt_in_count/len(results)*100:.0f}%)")
    print(f"  Average Confidence: {results['opt_in_confidence'].mean():.0f}%")
    
    print("\nIndividual Results:")
    for _, building in results.iterrows():
        print(f"  {building['building_id']}: {'OPT-IN' if building['should_opt_in'] else 'STANDARD'} "
              f"({building['opt_in_confidence']:.0f}% - {building['opt_in_rationale']})")
