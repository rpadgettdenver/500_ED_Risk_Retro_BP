"""Unit tests for penalty calculations"""
import pytest
import pandas as pd
from src.analytics.penalty_calculator import PenaltyCalculator


class TestPenaltyCalculator:
    """Test penalty calculation logic"""
    
    def test_penalty_calculation(self):
        """Test basic penalty calculation"""
        # Test data
        building_data = {
            'actual_eui': 100,
            'target_eui_2024': 80,
            'gross_floor_area': 50000
        }
        
        # Expected: (100-80) * 50000 * 0.15 = $150,000
        expected_penalty = 150000
        
        calculator = PenaltyCalculator()
        result = calculator.calculate_penalty(building_data)
        
        assert result == expected_penalty
    
    def test_compliant_building_no_penalty(self):
        """Test that compliant buildings have no penalty"""
        building_data = {
            'actual_eui': 70,
            'target_eui_2024': 80,
            'gross_floor_area': 50000
        }
        
        calculator = PenaltyCalculator()
        result = calculator.calculate_penalty(building_data)
        
        assert result == 0
