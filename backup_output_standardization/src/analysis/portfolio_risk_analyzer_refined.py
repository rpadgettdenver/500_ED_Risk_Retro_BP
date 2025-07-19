"""
Suggested File Name: portfolio_risk_analyzer_mai_refined.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis/
Use: Refined portfolio risk analyzer with full MAI building support

Changes (v1 - July 14, 2025):
1. NPV calculated only through 2032 (not 2042)
2. Added Hybrid line to penalty evolution chart
3. Modified property type labels to show n=x/total
4. Added At Risk 2027 and 2028 columns
5. Clarified $/sqft calculations for at-risk buildings only

Changes (v2 - July 15, 2025):
6. Added Avg $/sqft 2028 column for consistency across interim penalty years
7. Added At Risk 2030 and 2032 columns for complete analysis
8. Replaced Opt-In Decision Confidence histogram with comprehensive summary text

Changes (v3 - MAI Support Added):
9. Added MAI building identification from MAITargetSummary Report.csv
10. MAI buildings forced to ACO path with 2028/2032 timeline
11. MAI penalty rate correctly set to $0.23/kBtu
12. MAI-specific targets loaded from CSV files
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import sys
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our custom modules
from utils.penalty_calculator import EnergizeDenverPenaltyCalculator
from utils.eui_target_loader import load_building_targets
from utils.year_normalization import YearNormalizer
from utils.opt_in_predictor import OptInPredictor
from data_processing.mai_handler import MAIHandler


class PortfolioRiskAnalyzer:
    """
    Analyzes portfolio-wide compliance risk under different scenarios.
    
    Provides comprehensive risk assessment for Energize Denver portfolio
    with three scenarios and various analytical views.
    Now includes proper MAI building handling.
    """
    
    def __init__(self, data_dir='/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data'):
        """Initialize with data directory"""
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, 'processed')
        self.raw_dir = os.path.join(data_dir, 'raw')
        
        # Initialize MAI handler FIRST
        self.mai_handler = MAIHandler(self.raw_dir)
        
        # Load MAI building lookup
        mai_building_ids = self.mai_handler.get_mai_building_ids()
        mai_lookup = {building_id: True for building_id in mai_building_ids}
        
        # Initialize components with MAI lookup
        self.penalty_calc = EnergizeDenverPenaltyCalculator(mai_lookup=mai_lookup)
        self.year_normalizer = YearNormalizer()
        self.opt_in_predictor = OptInPredictor()
        
        # Load portfolio data
        self.load_portfolio_data()
        
    def load_portfolio_data(self):
        """Load all necessary data for portfolio analysis including MAI data"""
        print("📊 Loading portfolio data...")
        
        # Load current comprehensive data
        self.df_current = pd.read_csv(
            os.path.join(self.processed_dir, 'energize_denver_comprehensive_latest.csv')
        )
        self.df_current['Building ID'] = self.df_current['Building ID'].astype(str)
        
        # Load target data
        self.df_targets = pd.read_csv(
            os.path.join(self.raw_dir, 'Building_EUI_Targets.csv')
        )
        self.df_targets['Building ID'] = self.df_targets['Building ID'].astype(str)
        
        # Merge data
        self.portfolio = pd.merge(
            self.df_current,
            self.df_targets,
            on='Building ID',
            how='inner',
            suffixes=('', '_targets')
        )
        
        # Add MAI designation to portfolio
        mai_building_ids = self.mai_handler.get_mai_building_ids()
        self.portfolio['is_mai'] = self.portfolio['Building ID'].isin(mai_building_ids)
        
        # For MAI buildings, get their specific target data
        for idx, row in self.portfolio[self.portfolio['is_mai']].iterrows():
            mai_data = self.mai_handler.get_mai_targets(row['Building ID'])
            if mai_data:
                # Update with MAI-specific values
                if mai_data['interim_target'] > 0:
                    self.portfolio.at[idx, 'mai_interim_target'] = mai_data['interim_target']
                if mai_data['adjusted_final_target'] > 0:
                    self.portfolio.at[idx, 'mai_final_target'] = mai_data['adjusted_final_target']
                
                # Store MAI timeline info
                self.portfolio.at[idx, 'mai_interim_year'] = mai_data['interim_target_year']
                self.portfolio.at[idx, 'mai_final_year'] = mai_data['final_target_year']
        
        # Clean up - convert to numeric first
        self.portfolio['Weather Normalized Site EUI'] = pd.to_numeric(
            self.portfolio['Weather Normalized Site EUI'], errors='coerce'
        )
        self.portfolio['Master Sq Ft'] = pd.to_numeric(
            self.portfolio['Master Sq Ft'], errors='coerce'
        )
        
        # Filter out invalid data
        self.portfolio = self.portfolio[
            (self.portfolio['Weather Normalized Site EUI'] > 0) & 
            (self.portfolio['Weather Normalized Site EUI'].notna())
        ]
        self.portfolio = self.portfolio[
            (self.portfolio['Master Sq Ft'] >= 25000) & 
            (self.portfolio['Master Sq Ft'].notna())
        ]
        
        print(f"✓ Loaded {len(self.portfolio)} buildings for analysis")
        print(f"  - Standard buildings: {len(self.portfolio[~self.portfolio['is_mai']])}")
        print(f"  - MAI buildings: {len(self.portfolio[self.portfolio['is_mai']])}")
        
    def prepare_building_for_analysis(self, building_row) -> Dict:
        """Prepare a building row for analysis, including MAI-specific data"""
        # Base building data
        building_data = {
            'building_id': building_row['Building ID'],
            'property_type': building_row['Master Property Type'],
            'sqft': building_row['Master Sq Ft'],
            'current_eui': building_row['Weather Normalized Site EUI'],
            'baseline_eui': building_row['Baseline EUI'],
            'year_built': building_row.get('Year Built', 1990),
            'is_epb': building_row.get('Is EPB', False),
            'is_mai': building_row.get('is_mai', False)
        }
        
        # Handle MAI vs standard buildings differently
        if building_data['is_mai']:
            # MAI buildings use different timeline and targets
            building_data['baseline_year'] = int(building_row.get('Baseline Year', 2019))
            building_data['first_interim_year'] = int(building_row.get('mai_interim_year', 2028))
            building_data['second_interim_year'] = None  # MAI has no second interim
            building_data['final_year'] = int(building_row.get('mai_final_year', 2032))
            
            # Use MAI-specific targets if available
            building_data['first_interim_target'] = building_row.get('mai_interim_target', 
                                                                    building_row['First Interim Target EUI'])
            building_data['second_interim_target'] = None  # MAI has no second interim
            building_data['final_target'] = building_row.get('mai_final_target',
                                                            building_row.get('Adjusted Final Target EUI', 
                                                                           building_row['Original Final Target EUI']))
        else:
            # Standard buildings
            building_data['baseline_year'] = int(building_row.get('Baseline Year', 2019))
            building_data['first_interim_year'] = int(building_row.get('First Interim Target Year', 2025))
            building_data['second_interim_year'] = int(building_row.get('Second Interim Target Year', 2027))
            building_data['final_year'] = 2030
            
            building_data['first_interim_target'] = building_row['First Interim Target EUI']
            building_data['second_interim_target'] = building_row['Second Interim Target EUI']
            building_data['final_target'] = building_row.get('Adjusted Final Target EUI', 
                                                           building_row['Original Final Target EUI'])
        
        return building_data
    
    def calculate_building_penalties(self, building_data: Dict, path: str = 'standard') -> Dict:
        """Calculate penalties for a single building, accounting for MAI status"""
        sqft = building_data['sqft']
        current_eui = building_data['current_eui']
        is_mai = building_data['is_mai']
        
        # MAI buildings must follow ACO timeline regardless of path choice
        if is_mai:
            path = 'aco'  # Force ACO path for MAI buildings
        
        if path == 'standard':
            # Standard path penalties (non-MAI buildings only)
            penalties = {}
            
            # 2025 penalty
            gap_2025 = max(0, current_eui - building_data['first_interim_target'])
            penalties['2025'] = gap_2025 * sqft * self.penalty_calc.get_penalty_rate('standard')
            
            # 2027 penalty  
            gap_2027 = max(0, current_eui - building_data['second_interim_target'])
            penalties['2027'] = gap_2027 * sqft * self.penalty_calc.get_penalty_rate('standard')
            
            # 2030 penalty
            gap_2030 = max(0, current_eui - building_data['final_target'])
            penalties['2030'] = gap_2030 * sqft * self.penalty_calc.get_penalty_rate('standard')
            
            # Annual penalties 2031-2042
            for year in range(2031, 2043):
                penalties[str(year)] = penalties['2030']  # Same as 2030
                
        else:  # ACO path (including all MAI buildings)
            penalties = {}
            
            # MAI buildings use their specific timeline
            if is_mai:
                interim_year = building_data['first_interim_year']  # Should be 2028
                final_year = building_data['final_year']  # Should be 2032
            else:
                interim_year = 2028
                final_year = 2032
            
            # No penalties before interim year
            for year in range(2025, interim_year):
                penalties[str(year)] = 0
            
            # Interim year penalty
            gap_interim = max(0, current_eui - building_data['first_interim_target'])
            penalties[str(interim_year)] = gap_interim * sqft * self.penalty_calc.get_penalty_rate('aco')
            
            # No penalties between interim and final
            for year in range(interim_year + 1, final_year):
                penalties[str(year)] = 0
            
            # Final year penalty
            gap_final = max(0, current_eui - building_data['final_target'])
            penalties[str(final_year)] = gap_final * sqft * self.penalty_calc.get_penalty_rate('aco')
            
            # Annual penalties after final year
            for year in range(final_year + 1, 2043):
                penalties[str(year)] = penalties[str(final_year)]
                
        return penalties
    
    def scenario_all_standard(self) -> pd.DataFrame:
        """Calculate portfolio risk if all non-MAI buildings stay on standard path"""
        print("\n📈 Scenario 1: All non-MAI buildings on STANDARD path (MAI on ACO)")
        
        results = []
        mai_count = 0
        
        for idx, building in self.portfolio.iterrows():
            building_data = self.prepare_building_for_analysis(building)
            
            # MAI buildings must use ACO path
            if building_data['is_mai']:
                path = 'aco'
                mai_count += 1
            else:
                path = 'standard'
            
            penalties = self.calculate_building_penalties(building_data, path)
            
            # Add normalized years
            if path == 'standard':
                normalized_first = self.year_normalizer.normalize_standard_path_year(
                    building_data['first_interim_year'], 'first_interim'
                )
                normalized_second = self.year_normalizer.normalize_standard_path_year(
                    building_data['second_interim_year'], 'second_interim'
                )
                normalized_final = 2030
            else:  # ACO/MAI
                normalized_first = building_data['first_interim_year']
                normalized_second = None
                normalized_final = building_data['final_year']
            
            result = {
                'building_id': building_data['building_id'],
                'property_type': building_data['property_type'],
                'sqft': building_data['sqft'],
                'path': path,
                'is_mai': building_data['is_mai'],
                'normalized_first_year': normalized_first,
                'normalized_second_year': normalized_second,
                'normalized_final_year': normalized_final,
                **{f'penalty_{year}': penalty for year, penalty in penalties.items()}
            }
            results.append(result)
        
        print(f"  → {mai_count} MAI buildings automatically on ACO path")
        
        return pd.DataFrame(results)
    
    def scenario_all_aco(self) -> pd.DataFrame:
        """Calculate portfolio risk if all buildings opt into ACO path"""
        print("\n📈 Scenario 2: All buildings on ACO path")
        
        results = []
        for idx, building in self.portfolio.iterrows():
            building_data = self.prepare_building_for_analysis(building)
            penalties = self.calculate_building_penalties(building_data, 'aco')
            
            result = {
                'building_id': building_data['building_id'],
                'property_type': building_data['property_type'],
                'sqft': building_data['sqft'],
                'path': 'aco',
                'is_mai': building_data['is_mai'],
                'normalized_first_year': building_data.get('first_interim_year', 2028),
                'normalized_final_year': building_data.get('final_year', 2032),
                **{f'penalty_{year}': penalty for year, penalty in penalties.items()}
            }
            results.append(result)
            
        return pd.DataFrame(results)
    
    def scenario_hybrid(self) -> pd.DataFrame:
        """Calculate portfolio risk using opt-in prediction logic"""
        print("\n📈 Scenario 3: HYBRID - Using opt-in decision logic")
        
        results = []
        opt_in_count = 0
        mai_count = 0
        
        for idx, building in self.portfolio.iterrows():
            building_data = self.prepare_building_for_analysis(building)
            
            # MAI buildings must use ACO
            if building_data['is_mai']:
                decision_dict = {
                    'should_opt_in': True,
                    'confidence': 100,
                    'primary_rationale': 'MAI Required ACO',
                    'npv_advantage': 0
                }
                path = 'aco'
                mai_count += 1
            else:
                # Predict opt-in decision for non-MAI
                decision = self.opt_in_predictor.predict_opt_in(building_data)
                decision_dict = {
                    'should_opt_in': decision.should_opt_in,
                    'confidence': decision.confidence,
                    'primary_rationale': decision.primary_rationale,
                    'npv_advantage': decision.npv_advantage
                }
                path = 'aco' if decision.should_opt_in else 'standard'
            
            if decision_dict['should_opt_in']:
                opt_in_count += 1
            
            penalties = self.calculate_building_penalties(building_data, path)
            
            # Normalized years based on path
            if path == 'aco':
                normalized_first = building_data.get('first_interim_year', 2028)
                normalized_second = None
                normalized_final = building_data.get('final_year', 2032)
            else:
                normalized_first = self.year_normalizer.normalize_standard_path_year(
                    building_data['first_interim_year'], 'first_interim'
                )
                normalized_second = self.year_normalizer.normalize_standard_path_year(
                    building_data['second_interim_year'], 'second_interim'
                )
                normalized_final = 2030
            
            result = {
                'building_id': building_data['building_id'],
                'property_type': building_data['property_type'],
                'sqft': building_data['sqft'],
                'path': path,
                'is_mai': building_data['is_mai'],
                'should_opt_in': decision_dict['should_opt_in'],
                'opt_in_confidence': decision_dict['confidence'],
                'opt_in_rationale': decision_dict['primary_rationale'],
                'npv_advantage': decision_dict['npv_advantage'],
                'normalized_first_year': normalized_first,
                'normalized_second_year': normalized_second,
                'normalized_final_year': normalized_final,
                **{f'penalty_{year}': penalty for year, penalty in penalties.items()}
            }
            results.append(result)
        
        print(f"  → {opt_in_count} buildings ({opt_in_count/len(self.portfolio)*100:.1f}%) on ACO path")
        print(f"    - {mai_count} MAI buildings (required ACO)")
        print(f"    - {opt_in_count - mai_count} non-MAI buildings (voluntary ACO)")
        
        return pd.DataFrame(results)
    
    def analyze_mai_penalties(self, scenario_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze MAI building penalties specifically"""
        print("\n🏭 MAI BUILDING PENALTY ANALYSIS")
        
        mai_df = scenario_df[scenario_df['is_mai'] == True].copy()
        
        if len(mai_df) == 0:
            print("  No MAI buildings found in scenario")
            return pd.DataFrame()
        
        # Calculate key metrics for MAI buildings
        mai_with_penalties_2028 = mai_df[mai_df['penalty_2028'] > 0]
        mai_with_penalties_2032 = mai_df[mai_df['penalty_2032'] > 0]
        
        print(f"  Total MAI buildings: {len(mai_df)}")
        print(f"  MAI buildings with 2028 penalties: {len(mai_with_penalties_2028)}")
        print(f"  MAI buildings with 2032 penalties: {len(mai_with_penalties_2032)}")
        print(f"  Total 2028 MAI penalties: ${mai_df['penalty_2028'].sum():,.0f}")
        print(f"  Total 2032 MAI penalties: ${mai_df['penalty_2032'].sum():,.0f}")
        
        # Show top MAI buildings by penalty
        if len(mai_with_penalties_2028) > 0:
            print("\n  Top MAI buildings by 2028 penalty:")
            top_mai = mai_with_penalties_2028.nlargest(5, 'penalty_2028')[
                ['building_id', 'property_type', 'penalty_2028']
            ]
            for idx, row in top_mai.iterrows():
                print(f"    ID {row['building_id']}: ${row['penalty_2028']:,.0f} ({row['property_type']})")
        
        return mai_df
    
    def analyze_all_scenarios(self) -> Dict[str, pd.DataFrame]:
        """Run all three scenarios and return results"""
        print("\n🔍 RUNNING PORTFOLIO RISK ANALYSIS WITH MAI SUPPORT")
        print("=" * 60)
        
        scenarios = {
            'all_standard': self.scenario_all_standard(),
            'all_aco': self.scenario_all_aco(),
            'hybrid': self.scenario_hybrid()
        }
        
        # Analyze MAI penalties in each scenario
        for scenario_name, df in scenarios.items():
            print(f"\n--- {scenario_name.upper()} ---")
            self.analyze_mai_penalties(df)
        
        # Print summary comparison
        self.print_scenario_comparison(scenarios)
        
        return scenarios
    
    def print_scenario_comparison(self, scenarios: Dict[str, pd.DataFrame]):
        """Print comparison of all scenarios including MAI breakdowns"""
        print("\n📊 SCENARIO COMPARISON")
        print("=" * 60)
        
        # Calculate key metrics for each scenario
        comparison = []
        
        for scenario_name, df in scenarios.items():
            # Total penalties by year
            penalty_cols = [col for col in df.columns if col.startswith('penalty_')]
            yearly_totals = {}
            
            for col in penalty_cols:
                year = col.replace('penalty_', '')
                yearly_totals[year] = df[col].sum()
            
            # Calculate NPV (7% discount rate from 2025) - ONLY THROUGH 2032
            npv_total = 0
            for year_str, penalty in yearly_totals.items():
                year = int(year_str)
                if year <= 2032:  # Only include penalties through 2032
                    years_from_2025 = year - 2025
                    if years_from_2025 >= 0:
                        npv_total += penalty / ((1.07) ** years_from_2025)
            
            # MAI vs non-MAI breakdown
            mai_df = df[df['is_mai'] == True]
            non_mai_df = df[df['is_mai'] == False]
            
            mai_npv = 0
            non_mai_npv = 0
            
            for col in penalty_cols:
                year = int(col.replace('penalty_', ''))
                if year <= 2032:  # Only through 2032
                    years_from_2025 = year - 2025
                    if years_from_2025 >= 0:
                        mai_penalty = mai_df[col].sum()
                        non_mai_penalty = non_mai_df[col].sum()
                        mai_npv += mai_penalty / ((1.07) ** years_from_2025)
                        non_mai_npv += non_mai_penalty / ((1.07) ** years_from_2025)
            
            # Key years
            penalty_2025 = yearly_totals.get('2025', 0)
            penalty_2027 = yearly_totals.get('2027', 0)
            penalty_2028 = yearly_totals.get('2028', 0)
            penalty_2030 = yearly_totals.get('2030', 0)
            penalty_2032 = yearly_totals.get('2032', 0)
            
            # Peak year (only through 2032)
            peak_year = max([(k, v) for k, v in yearly_totals.items() if int(k) <= 2032], 
                           key=lambda x: x[1])
            
            comparison.append({
                'Scenario': scenario_name.replace('_', ' ').title(),
                'Total NPV': npv_total,
                'MAI NPV': mai_npv,
                'Non-MAI NPV': non_mai_npv,
                'Peak Year': f"{peak_year[0]}: ${peak_year[1]:,.0f}",
                '2025 Penalty': penalty_2025,
                '2027 Penalty': penalty_2027,
                '2028 Penalty': penalty_2028,
                '2030 Penalty': penalty_2030,
                '2032 Penalty': penalty_2032,
                'Buildings at Risk 2025': (df[df['penalty_2025'] > 0]['penalty_2025'].count() 
                                         if 'penalty_2025' in df.columns else 0),
                'MAI Buildings': len(mai_df),
                'Non-MAI Buildings': len(non_mai_df)
            })
        
        comparison_df = pd.DataFrame(comparison)
        
        # Print formatted table
        print("\nKey Metrics Comparison (NPV through 2032 only):")
        print("-" * 100)
        print(f"{'Scenario':<20} {'Total NPV':>15} {'MAI NPV':>15} {'Non-MAI NPV':>15} {'Peak Year Risk':>20}")
        print("-" * 100)
        
        for _, row in comparison_df.iterrows():
            print(f"{row['Scenario']:<20} ${row['Total NPV']:>14,.0f} ${row['MAI NPV']:>14,.0f} "
                  f"${row['Non-MAI NPV']:>14,.0f} {row['Peak Year']:>20}")
        
        # If hybrid scenario, show opt-in breakdown
        if 'hybrid' in scenarios:
            hybrid_df = scenarios['hybrid']
            if 'opt_in_rationale' in hybrid_df.columns:
                print("\n\nHybrid Scenario - Opt-In Decision Breakdown:")
                print("-" * 60)
                
                # MAI buildings
                mai_count = len(hybrid_df[hybrid_df['is_mai'] == True])
                print(f"  MAI Buildings (Required ACO): {mai_count}")
                
                # Non-MAI opt-ins
                non_mai_opt_ins = hybrid_df[
                    (hybrid_df['is_mai'] == False) & 
                    (hybrid_df['should_opt_in'] == True)
                ]
                
                if len(non_mai_opt_ins) > 0:
                    rationale_counts = non_mai_opt_ins['opt_in_rationale'].value_counts()
                    print("\n  Non-MAI Voluntary Opt-Ins:")
                    for rationale, count in rationale_counts.items():
                        print(f"    {rationale}: {count} buildings")
    
    def sensitivity_analysis(self, base_scenario: pd.DataFrame, 
                           adjustment_pct: float = 0.20) -> Dict[str, pd.DataFrame]:
        """
        Perform sensitivity analysis on opt-in rates.
        Note: MAI buildings are excluded from adjustment as they must remain on ACO.
        """
        print(f"\n🔄 SENSITIVITY ANALYSIS (±{adjustment_pct*100:.0f}% opt-in rate)")
        
        # Only works on hybrid scenario
        if 'should_opt_in' not in base_scenario.columns:
            print("  ⚠️  Sensitivity analysis only applicable to hybrid scenario")
            return {}
        
        # Current opt-in rate (excluding MAI which are forced)
        non_mai_df = base_scenario[base_scenario['is_mai'] == False]
        current_opt_in_rate = non_mai_df['should_opt_in'].mean()
        print(f"  Current opt-in rate (non-MAI only): {current_opt_in_rate*100:.1f}%")
        
        # Create scenarios
        scenarios = {}
        
        # High opt-in scenario
        high_scenario = base_scenario.copy()
        borderline_buildings = high_scenario[
            (high_scenario['opt_in_confidence'] >= 50) & 
            (high_scenario['opt_in_confidence'] <= 80) &
            (~high_scenario['should_opt_in']) &
            (~high_scenario['is_mai'])  # Exclude MAI
        ]
        
        # Flip some borderline buildings to opt-in
        num_to_flip = int(len(borderline_buildings) * adjustment_pct)
        if num_to_flip > 0:
            buildings_to_flip = borderline_buildings.sample(n=num_to_flip).index
            
            for idx in buildings_to_flip:
                building_data = self.prepare_building_for_analysis(self.portfolio.loc[idx])
                
                # Recalculate as ACO
                high_scenario.loc[idx, 'should_opt_in'] = True
                high_scenario.loc[idx, 'path'] = 'aco'
                
                # Recalculate penalties
                penalties = self.calculate_building_penalties(building_data, 'aco')
                for year, penalty in penalties.items():
                    if f'penalty_{year}' in high_scenario.columns:
                        high_scenario.loc[idx, f'penalty_{year}'] = penalty
        
        non_mai_high = high_scenario[high_scenario['is_mai'] == False]
        new_opt_in_rate = non_mai_high['should_opt_in'].mean()
        print(f"  High scenario opt-in rate (non-MAI): {new_opt_in_rate*100:.1f}%")
        scenarios['high_opt_in'] = high_scenario
        
        # Low opt-in scenario (similar logic but opposite)
        low_scenario = base_scenario.copy()
        borderline_opt_ins = low_scenario[
            (low_scenario['opt_in_confidence'] >= 50) & 
            (low_scenario['opt_in_confidence'] <= 80) &
            (low_scenario['should_opt_in']) &
            (~low_scenario['is_mai'])  # Exclude MAI
        ]
        
        num_to_flip = int(len(borderline_opt_ins) * adjustment_pct)
        if num_to_flip > 0:
            buildings_to_flip = borderline_opt_ins.sample(n=num_to_flip).index
            
            for idx in buildings_to_flip:
                building_data = self.prepare_building_for_analysis(self.portfolio.loc[idx])
                
                # Recalculate as standard
                low_scenario.loc[idx, 'should_opt_in'] = False
                low_scenario.loc[idx, 'path'] = 'standard'
                
                # Recalculate penalties
                penalties = self.calculate_building_penalties(building_data, 'standard')
                for year, penalty in penalties.items():
                    if f'penalty_{year}' in low_scenario.columns:
                        low_scenario.loc[idx, f'penalty_{year}'] = penalty
        
        non_mai_low = low_scenario[low_scenario['is_mai'] == False]
        new_opt_in_rate = non_mai_low['should_opt_in'].mean()
        print(f"  Low scenario opt-in rate (non-MAI): {new_opt_in_rate*100:.1f}%")
        scenarios['low_opt_in'] = low_scenario
        
        return scenarios
    
    def property_type_analysis(self, scenario_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze opt-in trends by property type"""
        print("\n🏢 PROPERTY TYPE ANALYSIS")
        
        # Only meaningful for scenarios with opt-in decisions
        if 'should_opt_in' in scenario_df.columns:
            analysis = scenario_df.groupby('property_type').agg({
                'building_id': 'count',
                'should_opt_in': ['sum', 'mean'],
                'is_mai': 'sum',
                'npv_advantage': 'mean',
                'penalty_2025': 'sum',
                'penalty_2030': 'sum',
                'sqft': 'sum'
            }).round(2)
            
            # Flatten column names
            analysis.columns = ['_'.join(col).strip() for col in analysis.columns.values]
            analysis.columns = ['total_buildings', 'opt_in_count', 'opt_in_rate', 
                               'mai_count', 'avg_npv_advantage', 'total_penalty_2025', 
                               'total_penalty_2030', 'total_sqft']
            
            # Sort by opt-in rate
            analysis = analysis.sort_values('opt_in_rate', ascending=False)
            
            # Filter to significant property types
            analysis = analysis[analysis['total_buildings'] >= 10]
            
            print("\nOpt-In Rates by Property Type (10+ buildings):")
            print("-" * 90)
            for prop_type, row in analysis.iterrows():
                mai_info = f" (MAI: {int(row['mai_count'])})" if row['mai_count'] > 0 else ""
                print(f"{prop_type:<35} {row['opt_in_rate']*100:>5.1f}% "
                      f"({int(row['opt_in_count']):>3}/{int(row['total_buildings']):>3}){mai_info} "
                      f"NPV Adv: ${row['avg_npv_advantage']:>10,.0f}")
        else:
            # For non-hybrid scenarios, just show penalty distribution
            analysis = scenario_df.groupby('property_type').agg({
                'building_id': 'count',
                'is_mai': 'sum',
                'penalty_2025': 'sum',
                'penalty_2030': 'sum',
                'sqft': 'sum'
            })
            analysis.columns = ['total_buildings', 'mai_count', 'total_penalty_2025', 
                               'total_penalty_2030', 'total_sqft']
            
        return analysis
    
    def time_series_analysis(self, scenarios: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Analyze penalty evolution over time"""
        print("\n📅 TIME SERIES ANALYSIS")
        
        # Extract yearly penalties for each scenario (only through 2032)
        years = list(range(2025, 2033))  # Changed from 2043 to 2033
        time_series_data = []
        
        for scenario_name, df in scenarios.items():
            for year in years:
                col_name = f'penalty_{year}'
                if col_name in df.columns:
                    total_penalty = df[col_name].sum()
                    buildings_at_risk = (df[col_name] > 0).sum()
                    mai_penalty = df[df['is_mai'] == True][col_name].sum()
                    mai_at_risk = (df[df['is_mai'] == True][col_name] > 0).sum()
                    
                    time_series_data.append({
                        'scenario': scenario_name,
                        'year': year,
                        'total_penalty': total_penalty,
                        'buildings_at_risk': buildings_at_risk,
                        'mai_penalty': mai_penalty,
                        'mai_at_risk': mai_at_risk
                    })
        
        time_series_df = pd.DataFrame(time_series_data)
        
        # Print summary for key years
        key_years = [2025, 2027, 2028, 2030, 2032]
        
        print("\nTotal Penalties by Year and Scenario ($M):")
        print("-" * 80)
        print(f"{'Year':<8}", end='')
        for scenario in scenarios.keys():
            print(f"{scenario.replace('_', ' ').title():>20}", end='')
        print()
        print("-" * 80)
        
        for year in key_years:
            print(f"{year:<8}", end='')
            for scenario in scenarios.keys():
                penalty = time_series_df[
                    (time_series_df['scenario'] == scenario) & 
                    (time_series_df['year'] == year)
                ]['total_penalty'].sum()
                print(f"${penalty/1e6:>19.1f}", end='')
            print()
        
        # MAI breakdown for key years
        print("\n\nMAI Penalties by Year ($M):")
        print("-" * 80)
        print(f"{'Year':<8}", end='')
        for scenario in ['all_standard', 'all_aco', 'hybrid']:
            print(f"{scenario.replace('_', ' ').title():>20}", end='')
        print()
        print("-" * 80)
        
        for year in [2028, 2032]:  # MAI key years
            print(f"{year:<8}", end='')
            for scenario in ['all_standard', 'all_aco', 'hybrid']:
                mai_penalty = time_series_df[
                    (time_series_df['scenario'] == scenario) & 
                    (time_series_df['year'] == year)
                ]['mai_penalty'].sum()
                print(f"${mai_penalty/1e6:>19.1f}", end='')
            print()
        
        return time_series_df
    
    def create_visualizations(self, scenarios: Dict[str, pd.DataFrame], 
                            output_dir: str = None):
        """Create comprehensive visualizations with MAI information"""
        if output_dir is None:
            output_dir = os.path.join(self.data_dir, '..', 'outputs', 'portfolio_analysis')
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up the figure
        fig = plt.figure(figsize=(20, 12))
        
        # 1. Scenario Comparison - Total NPV (ONLY THROUGH 2032)
        ax1 = plt.subplot(2, 3, 1)
        scenario_names = []
        npv_values = []
        mai_npv_values = []
        
        for name, df in scenarios.items():
            scenario_names.append(name.replace('_', ' ').title())
            
            # Calculate NPV only through 2032
            npv_total = 0
            mai_npv = 0
            for year in range(2025, 2033):  # Changed from 2043 to 2033
                col_name = f'penalty_{year}'
                if col_name in df.columns:
                    penalty = df[col_name].sum()
                    mai_penalty = df[df['is_mai'] == True][col_name].sum()
                    years_from_2025 = year - 2025
                    npv_total += penalty / ((1.07) ** years_from_2025)
                    mai_npv += mai_penalty / ((1.07) ** years_from_2025)
            
            npv_values.append(npv_total)
            mai_npv_values.append(mai_npv)
        
        # Only show the main 3 scenarios in bar chart
        main_scenarios = ['All Standard', 'All Aco', 'Hybrid']
        main_npvs = npv_values[:3]
        main_mai_npvs = mai_npv_values[:3]
        
        x = np.arange(len(main_scenarios))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, [v/1e6 for v in main_npvs], width, 
                        label='Total NPV', color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        bars2 = ax1.bar(x + width/2, [v/1e6 for v in main_mai_npvs], width,
                        label='MAI NPV', color=['#4a90e2', '#ff9f40', '#5cb85c'])
        
        ax1.set_ylabel('Total NPV of Penalties ($M)')
        ax1.set_title('Portfolio Risk by Scenario (NPV @ 7%, 2025-2032)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(main_scenarios)
        ax1.legend()
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'${height:.1f}M', ha='center', va='bottom', fontsize=8)
        
        # 2. Time Series - Penalty Evolution (INCLUDING HYBRID)
        ax2 = plt.subplot(2, 3, 2)
        time_series_df = self.time_series_analysis(scenarios)
        
        # Plot only main scenarios
        for scenario in ['all_standard', 'all_aco', 'hybrid']:
            if scenario in scenarios:
                scenario_data = time_series_df[time_series_df['scenario'] == scenario]
                ax2.plot(scenario_data['year'], scenario_data['total_penalty']/1e6,
                        label=scenario.replace('_', ' ').title(), linewidth=2, marker='o')
        
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Total Penalties ($M)')
        ax2.set_title('Penalty Evolution Over Time (2025-2032)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(2024.5, 2032.5)
        
        # 3. Property Type Analysis with improved labels
        ax3 = plt.subplot(2, 3, 3)
        if 'hybrid' in scenarios:
            hybrid_df = scenarios['hybrid']
            if 'should_opt_in' in hybrid_df.columns:
                prop_type_data = hybrid_df.groupby('property_type').agg({
                    'should_opt_in': 'mean',
                    'building_id': 'count',
                    'is_mai': 'sum'
                }).sort_values('should_opt_in', ascending=False)
                
                # Filter to top 10 property types by count
                top_types = prop_type_data.nlargest(10, 'building_id')
                
                y_pos = np.arange(len(top_types))
                ax3.barh(y_pos, top_types['should_opt_in'] * 100)
                ax3.set_yticks(y_pos)
                ax3.set_yticklabels(top_types.index)
                ax3.set_xlabel('Opt-In Rate (%)')
                ax3.set_title('Opt-In Rates by Property Type (Top 10)')
                
                # Add improved count labels showing n=x/total and MAI count
                total_buildings = len(hybrid_df)
                for i, (idx, row) in enumerate(top_types.iterrows()):
                    opt_in_count = int(row['should_opt_in'] * row['building_id'])
                    mai_count = int(row['is_mai'])
                    label = f"n={opt_in_count}/{int(row['building_id'])}"
                    if mai_count > 0:
                        label += f" (MAI:{mai_count})"
                    ax3.text(row['should_opt_in'] * 100 + 1, i, label, 
                            va='center', fontsize=8)
        
        # 4. Year Normalization Impact
        ax4 = plt.subplot(2, 3, 4)
        if 'all_standard' in scenarios:
            standard_df = scenarios['all_standard']
            
            # Count buildings by actual vs normalized year
            actual_years = self.portfolio['First Interim Target Year'].value_counts()
            normalized_count = len(standard_df[standard_df['normalized_first_year'] == 2025])
            
            years = sorted(actual_years.index)
            counts = [actual_years[year] for year in years]
            
            x = np.arange(len(years))
            width = 0.35
            
            bars1 = ax4.bar(x - width/2, counts, width, label='Actual Years')
            bars2 = ax4.bar(x + width/2, [normalized_count if y == 2025 else 0 for y in years],
                           width, label='Normalized to 2025')
            
            ax4.set_xlabel('First Interim Target Year')
            ax4.set_ylabel('Number of Buildings')
            ax4.set_title('Year Normalization Impact')
            ax4.set_xticks(x)
            ax4.set_xticklabels(years)
            ax4.legend()
        
        # 5. Summary Findings Text (including MAI info)
        ax5 = plt.subplot(2, 3, 5)
        ax5.axis('off')
        
        # Generate summary text based on analysis
        summary_text = "Key Portfolio Insights\n" + "="*40 + "\n\n"
        
        if 'hybrid' in scenarios:
            hybrid_df = scenarios['hybrid']
            
            # MAI statistics
            mai_count = len(hybrid_df[hybrid_df['is_mai'] == True])
            summary_text += f"MAI Buildings:\n"
            summary_text += f"  - {mai_count:,} MAI buildings (required ACO path)\n"
            
            # MAI penalties
            mai_2028_penalty = hybrid_df[hybrid_df['is_mai'] == True]['penalty_2028'].sum()
            mai_2032_penalty = hybrid_df[hybrid_df['is_mai'] == True]['penalty_2032'].sum()
            if mai_2028_penalty > 0 or mai_2032_penalty > 0:
                summary_text += f"  - 2028 MAI penalties: ${mai_2028_penalty/1e6:.1f}M\n"
                summary_text += f"  - 2032 MAI penalties: ${mai_2032_penalty/1e6:.1f}M\n"
            
            # Opt-in statistics (non-MAI)
            if 'should_opt_in' in hybrid_df.columns:
                non_mai_df = hybrid_df[hybrid_df['is_mai'] == False]
                opt_in_rate = non_mai_df['should_opt_in'].mean() * 100
                opt_in_count = non_mai_df['should_opt_in'].sum()
                summary_text += f"\nNon-MAI Opt-In Analysis:\n"
                summary_text += f"  - {opt_in_count:,} buildings ({opt_in_rate:.1f}%) voluntarily opt into ACO\n"
                
                # Confidence analysis
                if 'opt_in_confidence' in non_mai_df.columns:
                    avg_confidence = non_mai_df['opt_in_confidence'].mean()
                    high_confidence = (non_mai_df['opt_in_confidence'] >= 80).sum()
                    low_confidence = (non_mai_df['opt_in_confidence'] <= 50).sum()
                    summary_text += f"  - Average decision confidence: {avg_confidence:.1f}%\n"
                    summary_text += f"  - High confidence (>=80%): {high_confidence:,} buildings\n"
                    summary_text += f"  - Low confidence (<=50%): {low_confidence:,} buildings\n"
                
                # NPV advantage
                if 'npv_advantage' in non_mai_df.columns:
                    opt_in_buildings = non_mai_df[non_mai_df['should_opt_in'] == True]
                    avg_npv_advantage = opt_in_buildings['npv_advantage'].mean()
                    total_npv_advantage = opt_in_buildings['npv_advantage'].sum()
                    summary_text += f"\nFinancial Impact (Non-MAI):\n"
                    summary_text += f"  - Avg NPV advantage per opt-in: ${avg_npv_advantage:,.0f}\n"
                    summary_text += f"  - Total NPV advantage: ${total_npv_advantage/1e6:.1f}M\n"
        
        # Risk concentration
        if 'all_standard' in scenarios:
            standard_df = scenarios['all_standard']
            total_2025_penalty = standard_df['penalty_2025'].sum() if 'penalty_2025' in standard_df.columns else 0
            top_10_penalty = standard_df.nlargest(10, 'penalty_2025')['penalty_2025'].sum() if 'penalty_2025' in standard_df.columns else 0
            if total_2025_penalty > 0:
                concentration = (top_10_penalty / total_2025_penalty) * 100
                summary_text += f"\nRisk Concentration:\n"
                summary_text += f"  - Top 10 buildings: {concentration:.1f}% of 2025 penalties\n"
        
        # Add text to plot with proper formatting
        ax5.text(0.05, 0.95, summary_text, transform=ax5.transAxes, 
                fontsize=9, verticalalignment='top', fontfamily='sans-serif',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.9))
        
        ax5.set_title('Portfolio Analysis Summary', fontsize=14, weight='bold', pad=20)
        
        # 6. Financial Impact Summary - IMPROVED TABLE WITH MAI INFO
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        # Create summary table with wrapped labels and cohort-specific $/sqft
        summary_data = []
        for name, df in scenarios.items():
            # Buildings at risk by year
            at_risk_2025 = (df['penalty_2025'] > 0).sum() if 'penalty_2025' in df.columns else 0
            at_risk_2027 = (df['penalty_2027'] > 0).sum() if 'penalty_2027' in df.columns else 0
            at_risk_2028 = (df['penalty_2028'] > 0).sum() if 'penalty_2028' in df.columns else 0
            at_risk_2030 = (df['penalty_2030'] > 0).sum() if 'penalty_2030' in df.columns else 0
            at_risk_2032 = (df['penalty_2032'] > 0).sum() if 'penalty_2032' in df.columns else 0
            
            # MAI at risk
            mai_at_risk_2028 = ((df['is_mai'] == True) & (df['penalty_2028'] > 0)).sum() if 'penalty_2028' in df.columns else 0
            
            # Calculate $/sqft ONLY for buildings with penalties in each year
            if 'penalty_2028' in df.columns:
                at_risk_2028_df = df[df['penalty_2028'] > 0]
                if len(at_risk_2028_df) > 0:
                    avg_2028 = at_risk_2028_df['penalty_2028'].sum() / at_risk_2028_df['sqft'].sum()
                else:
                    avg_2028 = 0
            else:
                avg_2028 = 0
                
            if 'penalty_2030' in df.columns:
                at_risk_2030_df = df[df['penalty_2030'] > 0]
                if len(at_risk_2030_df) > 0:
                    avg_2030 = at_risk_2030_df['penalty_2030'].sum() / at_risk_2030_df['sqft'].sum()
                else:
                    avg_2030 = 0
            else:
                avg_2030 = 0
                
            if 'penalty_2032' in df.columns:
                at_risk_2032_df = df[df['penalty_2032'] > 0]
                if len(at_risk_2032_df) > 0:
                    avg_2032 = at_risk_2032_df['penalty_2032'].sum() / at_risk_2032_df['sqft'].sum()
                else:
                    avg_2032 = 0
            else:
                avg_2032 = 0
            
            # Shorter scenario names
            scenario_label = name.replace('_', ' ').replace('all ', '').title()
            if scenario_label == 'Standard':
                scenario_label = 'All\nStandard'
            elif scenario_label == 'Aco':
                scenario_label = 'All\nACO'
            elif scenario_label == 'High Opt In':
                scenario_label = 'High\nOpt In'
            elif scenario_label == 'Low Opt In':
                scenario_label = 'Low\nOpt In'
            
            # Add MAI count to at-risk 2028 if significant
            at_risk_2028_label = f"{at_risk_2028:,}"
            if mai_at_risk_2028 > 0:
                at_risk_2028_label += f"\n({mai_at_risk_2028} MAI)"
            
            summary_data.append([
                scenario_label,
                f"{len(df):,}",
                f"{at_risk_2025:,}",
                f"{at_risk_2027:,}",
                at_risk_2028_label,
                f"{at_risk_2030:,}",
                f"{at_risk_2032:,}",
                f"${avg_2028:.3f}",
                f"${avg_2030:.3f}",
                f"${avg_2032:.3f}"
            ])
        
        # Create table with wrapped column labels
        col_labels = ['Scenario', 'Total\nBuildings', 'At Risk\n2025', 'At Risk\n2027', 
                     'At Risk\n2028', 'At Risk\n2030', 'At Risk\n2032', 
                     'Avg $/sqft\n2028*', 'Avg $/sqft\n2030*', 'Avg $/sqft\n2032*']
        
        table = ax6.table(cellText=summary_data,
                         colLabels=col_labels,
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.1] * 10)  # Equal width for all 10 columns
        
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        table.scale(1.4, 2.2)  # Slightly taller for MAI info
        
        # Style the header row
        for (i, j), cell in table.get_celld().items():
            if i == 0:  # Header row
                cell.set_facecolor('#40466e')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
        
        ax6.set_title('Portfolio Summary Statistics', pad=20, fontsize=14, weight='bold')
        
        # Add footnote about $/sqft calculation
        ax6.text(0.5, -0.15, '*Avg $/sqft calculated only for buildings with penalties in that year', 
                ha='center', transform=ax6.transAxes, fontsize=9, style='italic')
        
        plt.tight_layout()
        
        # Save figure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fig_path = os.path.join(output_dir, f'portfolio_analysis_mai_{timestamp}.png')
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        print(f"\n📊 Visualizations saved to: {fig_path}")
        
        return fig
    
    def generate_report(self, output_path: str = None):
        """Generate comprehensive portfolio risk report with MAI analysis"""
        print("\n📋 GENERATING COMPREHENSIVE PORTFOLIO RISK REPORT WITH MAI SUPPORT")
        print("=" * 60)
        
        # Run all analyses
        scenarios = self.analyze_all_scenarios()
        
        # Sensitivity analysis on hybrid scenario
        if 'hybrid' in scenarios:
            sensitivity_scenarios = self.sensitivity_analysis(scenarios['hybrid'])
            scenarios.update(sensitivity_scenarios)
        
        # Property type analysis
        property_analysis = {}
        for name, df in scenarios.items():
            if name in ['all_standard', 'all_aco', 'hybrid']:
                property_analysis[name] = self.property_type_analysis(df)
        
        # Create visualizations
        fig = self.create_visualizations(scenarios)
        
        # Save detailed results
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save scenario results to Excel
            excel_path = output_path.replace('.json', '_detailed.xlsx')
            with pd.ExcelWriter(excel_path) as writer:
                # Create executive summary sheet first
                exec_summary = self.create_executive_summary(scenarios)
                exec_summary.to_excel(writer, sheet_name='Executive Summary', index=False)
                
                # Create MAI summary sheet
                mai_summary = self.create_mai_summary(scenarios)
                mai_summary.to_excel(writer, sheet_name='MAI Summary', index=False)
                
                # Save all scenarios
                for name, df in scenarios.items():
                    df.to_excel(writer, sheet_name=name, index=False)
                
                # Add property type analysis
                for name, analysis in property_analysis.items():
                    analysis.to_excel(writer, sheet_name=f'{name}_by_type')
            
            print(f"\n✓ Detailed results saved to: {excel_path}")
        
        print("\n🎯 ANALYSIS COMPLETE!")
        
        return scenarios, fig
    
    def create_executive_summary(self, scenarios: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create executive summary sheet for Excel"""
        summary_rows = []
        
        for name, df in scenarios.items():
            total_sqft = df['sqft'].sum()
            mai_count = len(df[df['is_mai'] == True])
            
            # Calculate NPV only through 2032
            npv_total = 0
            mai_npv = 0
            for year in range(2025, 2033):
                col_name = f'penalty_{year}'
                if col_name in df.columns:
                    penalty = df[col_name].sum()
                    mai_penalty = df[df['is_mai'] == True][col_name].sum()
                    years_from_2025 = year - 2025
                    npv_total += penalty / ((1.07) ** years_from_2025)
                    mai_npv += mai_penalty / ((1.07) ** years_from_2025)
            
            # Buildings at risk by year
            at_risk_2025 = (df['penalty_2025'] > 0).sum() if 'penalty_2025' in df.columns else 0
            at_risk_2027 = (df['penalty_2027'] > 0).sum() if 'penalty_2027' in df.columns else 0
            at_risk_2028 = (df['penalty_2028'] > 0).sum() if 'penalty_2028' in df.columns else 0
            at_risk_2030 = (df['penalty_2030'] > 0).sum() if 'penalty_2030' in df.columns else 0
            at_risk_2032 = (df['penalty_2032'] > 0).sum() if 'penalty_2032' in df.columns else 0
            
            # MAI at risk
            mai_at_risk_2028 = ((df['is_mai'] == True) & (df['penalty_2028'] > 0)).sum() if 'penalty_2028' in df.columns else 0
            mai_at_risk_2032 = ((df['is_mai'] == True) & (df['penalty_2032'] > 0)).sum() if 'penalty_2032' in df.columns else 0
            
            # Average penalties (only for at-risk buildings)
            if 'penalty_2028' in df.columns:
                at_risk_2028_df = df[df['penalty_2028'] > 0]
                avg_2028 = at_risk_2028_df['penalty_2028'].sum() / at_risk_2028_df['sqft'].sum() if len(at_risk_2028_df) > 0 else 0
            else:
                avg_2028 = 0
                
            if 'penalty_2030' in df.columns:
                at_risk_2030_df = df[df['penalty_2030'] > 0]
                avg_2030 = at_risk_2030_df['penalty_2030'].sum() / at_risk_2030_df['sqft'].sum() if len(at_risk_2030_df) > 0 else 0
            else:
                avg_2030 = 0
                
            if 'penalty_2032' in df.columns:
                at_risk_2032_df = df[df['penalty_2032'] > 0]
                avg_2032 = at_risk_2032_df['penalty_2032'].sum() / at_risk_2032_df['sqft'].sum() if len(at_risk_2032_df) > 0 else 0
            else:
                avg_2032 = 0
            
            # Add row to summary
            summary_rows.append({
                'Scenario': name.replace('_', ' ').title(),
                'Total Buildings': len(df),
                'MAI Buildings': mai_count,
                'Total Sq Ft': f"{total_sqft:,.0f}",
                'NPV of Penalties (2025-2032)': f"${npv_total:,.0f}",
                'MAI NPV': f"${mai_npv:,.0f}",
                'Buildings at Risk 2025': at_risk_2025,
                'Buildings at Risk 2027': at_risk_2027,
                'Buildings at Risk 2028': f"{at_risk_2028} ({mai_at_risk_2028} MAI)",
                'Buildings at Risk 2030': at_risk_2030,
                'Buildings at Risk 2032': f"{at_risk_2032} ({mai_at_risk_2032} MAI)",
                'Avg $/sqft 2028 (at-risk only)': f"${avg_2028:.3f}",
                'Avg $/sqft 2030 (at-risk only)': f"${avg_2030:.3f}",
                'Avg $/sqft 2032 (at-risk only)': f"${avg_2032:.3f}",
                'Opt-In Rate': f"{df['should_opt_in'].mean()*100:.1f}%" if 'should_opt_in' in df.columns else "N/A"
            })
        
        return pd.DataFrame(summary_rows)
    
    def create_mai_summary(self, scenarios: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create MAI-specific summary sheet for Excel"""
        mai_rows = []
        
        for name, df in scenarios.items():
            if name in ['all_standard', 'all_aco', 'hybrid']:
                mai_df = df[df['is_mai'] == True]
                
                if len(mai_df) > 0:
                    # MAI buildings with penalties
                    mai_2028_at_risk = (mai_df['penalty_2028'] > 0).sum() if 'penalty_2028' in mai_df.columns else 0
                    mai_2032_at_risk = (mai_df['penalty_2032'] > 0).sum() if 'penalty_2032' in mai_df.columns else 0
                    
                    # MAI penalties
                    mai_2028_penalty = mai_df['penalty_2028'].sum() if 'penalty_2028' in mai_df.columns else 0
                    mai_2032_penalty = mai_df['penalty_2032'].sum() if 'penalty_2032' in mai_df.columns else 0
                    
                    # Top 5 MAI buildings by 2028 penalty
                    if mai_2028_at_risk > 0:
                        top_mai = mai_df.nlargest(5, 'penalty_2028')[['building_id', 'property_type', 'penalty_2028']]
                        top_mai_list = [f"{row['building_id']} ({row['property_type']}): ${row['penalty_2028']:,.0f}" 
                                       for _, row in top_mai.iterrows()]
                    else:
                        top_mai_list = ["No MAI buildings with 2028 penalties"]
                    
                    mai_rows.append({
                        'Scenario': name.replace('_', ' ').title(),
                        'Total MAI Buildings': len(mai_df),
                        'MAI Buildings at Risk 2028': mai_2028_at_risk,
                        'MAI Buildings at Risk 2032': mai_2032_at_risk,
                        'Total MAI Penalty 2028': f"${mai_2028_penalty:,.0f}",
                        'Total MAI Penalty 2032': f"${mai_2032_penalty:,.0f}",
                        'Top MAI Buildings by 2028 Penalty': '; '.join(top_mai_list[:3])
                    })
        
        return pd.DataFrame(mai_rows)


# Example usage
if __name__ == "__main__":
    # Create analyzer with MAI support
    analyzer = PortfolioRiskAnalyzer()
    
    # Generate full report
    output_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/portfolio_risk_analysis_mai_refined.json'
    scenarios, fig = analyzer.generate_report(output_path)
    
    # Show visualizations
    plt.show()
