"""
Suggested File Name: hvac_system_impact_modeler.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/models/
Use: Model how different HVAC system types affect building EUI and calculate Energize Denver compliance impacts

This module models the impact of different HVAC systems on building EUI:
- 4-pipe heat pump systems
- Thermal energy storage impacts
- Electrification scenarios
- Gas vs electric heating trade-offs
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
import os
from datetime import datetime
from src.utils.penalty_calculator import EnergizeDenverPenaltyCalculator


class HVACSystemImpactModeler:
    """Model EUI impacts of different HVAC system configurations"""
    
    def __init__(self, building_id: str, data_path: str = None):
        """
        Initialize with building data
        
        Args:
            building_id: Building ID from Energize Denver database
            data_path: Path to comprehensive building data CSV
        """
        self.building_id = str(building_id)
        
        # Default data path
        if data_path is None:
            data_path = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data/processed/energize_denver_comprehensive_latest.csv"
        
        # Load building data
        self.df = pd.read_csv(data_path)
        self.building_data = self._load_building_data()
        
        # System efficiency factors
        self.system_efficiencies = {
            'gas_boiler': 0.85,  # 85% efficient gas boiler
            'electric_resistance': 1.0,  # 100% efficient but uses grid electricity
            'air_source_hp': 3.0,  # COP 3.0 for air source heat pump
            'water_source_hp': 4.0,  # COP 4.0 for water source heat pump
            'water_source_hp_tes': 4.5,  # COP 4.5 with TES optimization
            'ground_source_hp': 5.0,  # COP 5.0 for ground source
        }
        
        # Denver grid emissions factor (lbs CO2/kWh)
        self.grid_emissions = 1.2  # Xcel Energy Colorado
        
        # Natural gas emissions factor (lbs CO2/therm)
        self.gas_emissions = 11.7
        
    def _load_building_data(self) -> Dict:
        """Load current building data"""
        building_row = self.df[self.df['Building ID'] == self.building_id]
        
        if building_row.empty:
            raise ValueError(f"Building {self.building_id} not found in dataset")
        
        # Extract key metrics
        data = building_row.iloc[0].to_dict()
        
        # Key energy metrics
        return {
            'building_name': data.get('Building Name', 'Unknown'),
            'property_type': data.get('Master Property Type', 'Unknown'),
            'sqft': data.get('Master Sq Ft', 0),
            'current_site_eui': data.get('Site EUI', 0),
            'current_weather_norm_eui': data.get('Weather Normalized Site EUI', 0),
            'electricity_kwh': data.get('Electricity Use Grid Purchase (kWh)', 0),
            'gas_kbtu': data.get('Natural Gas Use (kBtu)', 0),
            'total_ghg': data.get('Total GHG Emissions (mtCO2e)', 0),
            'is_epb': data.get('is_epb', False),
            'baseline_year': data.get('Baseline Year', 2019),
            'baseline_eui': data.get('Baseline EUI', 0),
            # Energize Denver targets
            'first_interim_target': data.get('First Interim Target EUI', 0),
            'second_interim_target': data.get('Second Interim Target EUI', 0),
            'final_target': data.get('Adjusted Final Target EUI', 0),
        }
    
    def calculate_heating_cooling_split(self) -> Tuple[float, float]:
        """
        Estimate heating vs cooling energy split based on building type and current usage
        
        Returns:
            Tuple of (heating_fraction, cooling_fraction)
        """
        # For multifamily in Denver, typical split
        if 'multifamily' in self.building_data['property_type'].lower():
            # Most gas is for heating/hot water
            gas_energy_kbtu = self.building_data['gas_kbtu']
            elec_energy_kbtu = self.building_data['electricity_kwh'] * 3.412
            
            total_energy = gas_energy_kbtu + elec_energy_kbtu
            
            if total_energy > 0:
                heating_fraction = gas_energy_kbtu / total_energy * 0.9  # 90% of gas is heating
                cooling_fraction = 0.15  # 15% of total energy for cooling
                
                # Normalize
                other_fraction = 1 - heating_fraction - cooling_fraction
                
                return heating_fraction, cooling_fraction
            
        # Default for other building types
        return 0.6, 0.2  # 60% heating, 20% cooling, 20% other
    
    def model_system_impact(self, system_type: str, 
                          include_tes: bool = False,
                          tes_size_factor: float = 1.0) -> Dict:
        """
        Model the impact of a specific HVAC system on building EUI
        
        Args:
            system_type: Type of HVAC system
            include_tes: Whether to include thermal energy storage
            tes_size_factor: Size of TES relative to peak load (1.0 = sized for peak)
            
        Returns:
            Dict with new EUI, emissions, and costs
        """
        # Get current energy breakdown
        heating_frac, cooling_frac = self.calculate_heating_cooling_split()
        
        # Current energy by end use
        total_site_energy = (self.building_data['gas_kbtu'] + 
                           self.building_data['electricity_kwh'] * 3.412)
        
        heating_energy = total_site_energy * heating_frac
        cooling_energy = total_site_energy * cooling_frac
        other_energy = total_site_energy * (1 - heating_frac - cooling_frac)
        
        # Model new system
        if system_type == 'current':
            # No change
            new_heating = heating_energy
            new_cooling = cooling_energy
            heating_fuel = 'gas'
            
        elif system_type == '4pipe_wshp':
            # 4-pipe water source heat pump system
            cop = self.system_efficiencies['water_source_hp']
            
            # Convert to electricity at high COP
            new_heating = heating_energy / cop * 0.9  # 10% reduction from better controls
            new_cooling = cooling_energy / cop * 0.9
            heating_fuel = 'electric'
            
            if include_tes:
                # TES provides additional efficiency
                cop_boost = 0.5 * tes_size_factor  # Up to 0.5 COP improvement
                new_heating = new_heating / (1 + cop_boost/cop)
                new_cooling = new_cooling / (1 + cop_boost/cop)
        
        elif system_type == 'ashp':
            # Air source heat pump
            cop = self.system_efficiencies['air_source_hp']
            
            new_heating = heating_energy / cop
            new_cooling = cooling_energy / (cop * 1.2)  # Better cooling efficiency
            heating_fuel = 'electric'
            
        elif system_type == 'gshp':
            # Ground source heat pump
            cop = self.system_efficiencies['ground_source_hp']
            
            new_heating = heating_energy / cop * 0.85  # 15% reduction from ground coupling
            new_cooling = cooling_energy / cop * 0.85
            heating_fuel = 'electric'
            
        else:
            raise ValueError(f"Unknown system type: {system_type}")
        
        # Calculate new total energy and EUI
        if heating_fuel == 'electric':
            # All electric building
            new_electricity_kwh = (new_heating + new_cooling + other_energy) / 3.412
            new_gas_kbtu = 0
        else:
            # Mixed fuel
            new_electricity_kwh = (new_cooling + other_energy * 0.3) / 3.412
            new_gas_kbtu = new_heating + other_energy * 0.7
        
        new_total_energy = new_electricity_kwh * 3.412 + new_gas_kbtu
        new_eui = new_total_energy / self.building_data['sqft']
        
        # Calculate emissions
        new_emissions_mtco2 = (
            (new_electricity_kwh * self.grid_emissions / 2204.62) +  # lbs to metric tons
            (new_gas_kbtu / 100 * self.gas_emissions / 2204.62)  # therms to metric tons
        )
        
        # Electrification bonus - 10% higher EUI allowed while staying compliant
        electrification_bonus = 0
        if new_gas_kbtu == 0:  # Fully electric
            electrification_bonus = 0.10
        
        # Compare to targets
        results = {
            'system_type': system_type,
            'include_tes': include_tes,
            'tes_size_factor': tes_size_factor,
            
            # Current state
            'current_eui': self.building_data['current_weather_norm_eui'],
            'current_emissions_mtco2': self.building_data['total_ghg'],
            
            # New state
            'new_eui': round(new_eui, 1),
            'new_electricity_kwh': round(new_electricity_kwh, 0),
            'new_gas_kbtu': round(new_gas_kbtu, 0),
            'new_emissions_mtco2': round(new_emissions_mtco2, 2),
            
            # Changes
            'eui_reduction': round(self.building_data['current_weather_norm_eui'] - new_eui, 1),
            'eui_reduction_pct': round((self.building_data['current_weather_norm_eui'] - new_eui) / 
                                     self.building_data['current_weather_norm_eui'] * 100, 1),
            'emissions_reduction_mtco2': round(self.building_data['total_ghg'] - new_emissions_mtco2, 2),
            'emissions_reduction_pct': round((self.building_data['total_ghg'] - new_emissions_mtco2) / 
                                           self.building_data['total_ghg'] * 100, 1),
            
            # Compliance
            'electrification_bonus': electrification_bonus,
            'effective_eui_for_compliance': new_eui * (1 - electrification_bonus),
            
            # Capital cost estimates (rough)
            'estimated_cost_per_sqft': self._estimate_cost_per_sqft(system_type, include_tes),
            'total_estimated_cost': self._estimate_cost_per_sqft(system_type, include_tes) * 
                                  self.building_data['sqft'],
        }
        
        # Add compliance analysis
        results.update(self._analyze_compliance(results['effective_eui_for_compliance']))
        
        return results
    
    def _estimate_cost_per_sqft(self, system_type: str, include_tes: bool) -> float:
        """Estimate installation cost per square foot"""
        base_costs = {
            'current': 0,
            '4pipe_wshp': 25,  # $25/sqft for water source HP system
            'ashp': 20,  # $20/sqft for air source HP
            'gshp': 35,  # $35/sqft for ground source
        }
        
        cost = base_costs.get(system_type, 25)
        
        if include_tes:
            cost += 5  # $5/sqft for TES
            
        # Add 30% market escalation
        return cost * 1.3
    
    def _analyze_compliance(self, effective_eui: float) -> Dict:
        """Analyze compliance with Energize Denver targets"""
        targets = {
            '2025_target': self.building_data.get('first_interim_target', 65.4),
            '2027_target': self.building_data.get('second_interim_target', 63.2),
            '2030_target': self.building_data.get('final_target', 51.5),
        }
        
        compliance = {}
        
        for year, target in targets.items():
            if target > 0:
                compliant = effective_eui <= target
                excess = max(0, effective_eui - target)
                
                # TODO: Update to use penalty_calculator module for correct rates
                # Calculate penalty
                if '2025' in year:
                    penalty_rate = 0.15  # Standard path rate
                elif '2027' in year:
                    penalty_rate = 0.15  # Standard path rate
                else:
                    penalty_rate = 0.15  # Standard path rate
                    
                annual_penalty = excess * self.building_data['sqft'] * penalty_rate
                
                compliance[year] = {
                    'target_eui': target,
                    'compliant': compliant,
                    'excess_eui': round(excess, 1),
                    'annual_penalty': round(annual_penalty, 0),
                }
        
        return compliance
    
    def compare_systems(self, systems_to_compare: List[Dict] = None) -> pd.DataFrame:
        """
        Compare multiple system configurations
        
        Args:
            systems_to_compare: List of dicts with system configurations
            
        Returns:
            DataFrame comparing all systems
        """
        if systems_to_compare is None:
            # Default comparison
            systems_to_compare = [
                {'system_type': 'current', 'include_tes': False, 'name': 'Current System'},
                {'system_type': '4pipe_wshp', 'include_tes': False, 'name': '4-Pipe WSHP'},
                {'system_type': '4pipe_wshp', 'include_tes': True, 'tes_size_factor': 1.0, 
                 'name': '4-Pipe WSHP + TES'},
                {'system_type': 'ashp', 'include_tes': False, 'name': 'Air Source HP'},
                {'system_type': 'gshp', 'include_tes': False, 'name': 'Ground Source HP'},
            ]
        
        results = []
        
        for config in systems_to_compare:
            name = config.pop('name', config['system_type'])
            result = self.model_system_impact(**config)
            result['system_name'] = name
            results.append(result)
        
        # Create comparison dataframe
        df_compare = pd.DataFrame(results)
        
        # Select key columns for comparison
        comparison_cols = [
            'system_name', 'new_eui', 'eui_reduction_pct',
            'new_emissions_mtco2', 'emissions_reduction_pct',
            'effective_eui_for_compliance', 'total_estimated_cost',
            '2025_target', '2027_target', '2030_target'
        ]
        
        # Extract compliance data
        for year in ['2025', '2027', '2030']:
            df_compare[f'{year}_compliant'] = df_compare.apply(
                lambda x: x.get(f'{year}_target', {}).get('compliant', False), axis=1
            )
            df_compare[f'{year}_penalty'] = df_compare.apply(
                lambda x: x.get(f'{year}_target', {}).get('annual_penalty', 0), axis=1
            )
        
        return df_compare
    
    def generate_scenario_report(self) -> Dict:
        """Generate comprehensive scenario analysis report"""
        
        # Run comparison
        df_compare = self.compare_systems()
        
        # Calculate total penalties over time
        for idx, row in df_compare.iterrows():
            # Standard path penalties (2025-2030)
            standard_penalties = (
                row['2025_penalty'] * 2 +  # 2025-2026
                row['2027_penalty'] * 3 +  # 2027-2029
                row['2030_penalty'] * 10   # 2030-2039 (assume 10 years)
            )
            
            # Opt-in path would delay by 3 years but same targets
            opt_in_penalties = (
                0 * 3 +  # No penalties 2025-2027
                row['2025_penalty'] * 2 +  # 2028-2029 at 2025 target
                row['2027_penalty'] * 3 +  # 2030-2032 at 2027 target
                row['2030_penalty'] * 7    # 2033-2039 at final target
            )
            
            df_compare.at[idx, 'total_penalties_standard'] = standard_penalties
            df_compare.at[idx, 'total_penalties_optin'] = opt_in_penalties
            df_compare.at[idx, 'recommended_path'] = (
                'Opt-in' if opt_in_penalties < standard_penalties else 'Standard'
            )
        
        report = {
            'building_id': self.building_id,
            'building_name': self.building_data['building_name'],
            'property_type': self.building_data['property_type'],
            'sqft': self.building_data['sqft'],
            'is_epb': self.building_data['is_epb'],
            'current_eui': self.building_data['current_weather_norm_eui'],
            'scenarios': df_compare.to_dict('records'),
            'timestamp': datetime.now().isoformat(),
        }
        
        return report


# Example usage
if __name__ == "__main__":
    # Analyze Building 2952 (Timperly Condominium)
    modeler = HVACSystemImpactModeler('2952')
    
    # Generate scenario report
    report = modeler.generate_scenario_report()
    
    # Print summary
    print(f"\nHVAC System Impact Analysis for {report['building_name']}")
    print(f"Building ID: {report['building_id']}")
    print(f"Size: {report['sqft']:,} sq ft")
    print(f"Current EUI: {report['current_eui']}")
    print(f"EPB Status: {'Yes' if report['is_epb'] else 'No'}")
    
    print("\n" + "="*80)
    print("SYSTEM COMPARISON:")
    print("="*80)
    
    for scenario in report['scenarios']:
        print(f"\n{scenario['system_name']}:")
        print(f"  New EUI: {scenario['new_eui']} (reduction: {scenario['eui_reduction_pct']}%)")
        print(f"  Emissions: {scenario['new_emissions_mtco2']} mtCO2e (reduction: {scenario['emissions_reduction_pct']}%)")
        print(f"  Estimated Cost: ${scenario['total_estimated_cost']:,.0f}")
        print(f"  2025 Compliant: {'Yes' if scenario['2025_compliant'] else 'No'} (Penalty: ${scenario['2025_penalty']:,.0f}/yr)")
        print(f"  2027 Compliant: {'Yes' if scenario['2027_compliant'] else 'No'} (Penalty: ${scenario['2027_penalty']:,.0f}/yr)")
        print(f"  2030 Compliant: {'Yes' if scenario['2030_compliant'] else 'No'} (Penalty: ${scenario['2030_penalty']:,.0f}/yr)")
        print(f"  Recommended Path: {scenario['recommended_path']}")
