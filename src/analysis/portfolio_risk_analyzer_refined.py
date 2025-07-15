"""
Suggested File Name: portfolio_risk_analyzer_refined.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis/
Use: Refined portfolio risk analyzer with requested visualization improvements

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


class PortfolioRiskAnalyzer:
    """
    Analyzes portfolio-wide compliance risk under different scenarios.
    
    Provides comprehensive risk assessment for Energize Denver portfolio
    with three scenarios and various analytical views.
    """
    
    def __init__(self, data_dir='/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data'):
        """Initialize with data directory"""
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, 'processed')
        self.raw_dir = os.path.join(data_dir, 'raw')
        
        # Initialize components
        self.penalty_calc = EnergizeDenverPenaltyCalculator()
        self.year_normalizer = YearNormalizer()
        self.opt_in_predictor = OptInPredictor()
        
        # Load portfolio data
        self.load_portfolio_data()
        
    def load_portfolio_data(self):
        """Load all necessary data for portfolio analysis"""
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
        
    def prepare_building_for_analysis(self, building_row) -> Dict:
        """Prepare a building row for analysis"""
        return {
            'building_id': building_row['Building ID'],
            'property_type': building_row['Master Property Type'],
            'sqft': building_row['Master Sq Ft'],
            'current_eui': building_row['Weather Normalized Site EUI'],
            'baseline_eui': building_row['Baseline EUI'],
            'first_interim_target': building_row['First Interim Target EUI'],
            'second_interim_target': building_row['Second Interim Target EUI'],
            'final_target': building_row.get('Adjusted Final Target EUI', 
                                           building_row['Original Final Target EUI']),
            'year_built': building_row.get('Year Built', 1990),
            'is_epb': building_row.get('Is EPB', False),
            'baseline_year': int(building_row.get('Baseline Year', 2019)),
            'first_interim_year': int(building_row.get('First Interim Target Year', 2025)),
            'second_interim_year': int(building_row.get('Second Interim Target Year', 2027))
        }
    
    def calculate_building_penalties(self, building_data: Dict, path: str = 'standard') -> Dict:
        """Calculate penalties for a single building"""
        sqft = building_data['sqft']
        current_eui = building_data['current_eui']
        
        if path == 'standard':
            # Standard path penalties
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
                
        else:  # ACO path
            penalties = {}
            
            # No penalties until 2028
            penalties['2025'] = 0
            penalties['2026'] = 0
            penalties['2027'] = 0
            
            # 2028 penalty (using first interim target)
            gap_2028 = max(0, current_eui - building_data['first_interim_target'])
            penalties['2028'] = gap_2028 * sqft * self.penalty_calc.get_penalty_rate('aco')
            
            # 2029-2031 no penalties
            penalties['2029'] = 0
            penalties['2030'] = 0
            penalties['2031'] = 0
            
            # 2032 penalty (using final target)
            gap_2032 = max(0, current_eui - building_data['final_target'])
            penalties['2032'] = gap_2032 * sqft * self.penalty_calc.get_penalty_rate('aco')
            
            # Annual penalties 2033-2042
            for year in range(2033, 2043):
                penalties[str(year)] = penalties['2032']
                
        return penalties
    
    def scenario_all_standard(self) -> pd.DataFrame:
        """Calculate portfolio risk if all buildings stay on standard path"""
        print("\n📈 Scenario 1: All buildings on STANDARD path")
        
        results = []
        for idx, building in self.portfolio.iterrows():
            building_data = self.prepare_building_for_analysis(building)
            penalties = self.calculate_building_penalties(building_data, 'standard')
            
            # Add normalized years
            normalized_first = self.year_normalizer.normalize_standard_path_year(
                building_data['first_interim_year'], 'first_interim'
            )
            normalized_second = self.year_normalizer.normalize_standard_path_year(
                building_data['second_interim_year'], 'second_interim'
            )
            
            result = {
                'building_id': building_data['building_id'],
                'property_type': building_data['property_type'],
                'sqft': building_data['sqft'],
                'path': 'standard',
                'normalized_first_year': normalized_first,
                'normalized_second_year': normalized_second,
                'normalized_final_year': 2030,
                **{f'penalty_{year}': penalty for year, penalty in penalties.items()}
            }
            results.append(result)
            
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
                'normalized_first_year': 2028,
                'normalized_final_year': 2032,
                **{f'penalty_{year}': penalty for year, penalty in penalties.items()}
            }
            results.append(result)
            
        return pd.DataFrame(results)
    
    def scenario_hybrid(self) -> pd.DataFrame:
        """Calculate portfolio risk using opt-in prediction logic"""
        print("\n📈 Scenario 3: HYBRID - Using opt-in decision logic")
        
        results = []
        opt_in_count = 0
        
        for idx, building in self.portfolio.iterrows():
            building_data = self.prepare_building_for_analysis(building)
            
            # Predict opt-in decision
            decision = self.opt_in_predictor.predict_opt_in(building_data)
            
            if decision.should_opt_in:
                opt_in_count += 1
                path = 'aco'
                penalties = self.calculate_building_penalties(building_data, 'aco')
                normalized_first = 2028
                normalized_second = None
                normalized_final = 2032
            else:
                path = 'standard'
                penalties = self.calculate_building_penalties(building_data, 'standard')
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
                'should_opt_in': decision.should_opt_in,
                'opt_in_confidence': decision.confidence,
                'opt_in_rationale': decision.primary_rationale,
                'npv_advantage': decision.npv_advantage,
                'normalized_first_year': normalized_first,
                'normalized_second_year': normalized_second,
                'normalized_final_year': normalized_final,
                **{f'penalty_{year}': penalty for year, penalty in penalties.items()}
            }
            results.append(result)
        
        print(f"  → {opt_in_count} buildings ({opt_in_count/len(self.portfolio)*100:.1f}%) predicted to opt-in")
        
        return pd.DataFrame(results)
    
    def analyze_all_scenarios(self) -> Dict[str, pd.DataFrame]:
        """Run all three scenarios and return results"""
        print("\n🔍 RUNNING PORTFOLIO RISK ANALYSIS")
        print("=" * 60)
        
        scenarios = {
            'all_standard': self.scenario_all_standard(),
            'all_aco': self.scenario_all_aco(),
            'hybrid': self.scenario_hybrid()
        }
        
        # Print summary comparison
        self.print_scenario_comparison(scenarios)
        
        return scenarios
    
    def print_scenario_comparison(self, scenarios: Dict[str, pd.DataFrame]):
        """Print comparison of all scenarios"""
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
                'Peak Year': f"{peak_year[0]}: ${peak_year[1]:,.0f}",
                '2025 Penalty': penalty_2025,
                '2027 Penalty': penalty_2027,
                '2028 Penalty': penalty_2028,
                '2030 Penalty': penalty_2030,
                '2032 Penalty': penalty_2032,
                'Buildings at Risk 2025': (df[df['penalty_2025'] > 0]['penalty_2025'].count() 
                                         if 'penalty_2025' in df.columns else 0)
            })
        
        comparison_df = pd.DataFrame(comparison)
        
        # Print formatted table
        print("\nKey Metrics Comparison (NPV through 2032 only):")
        print("-" * 80)
        print(f"{'Scenario':<20} {'Total NPV':>15} {'Peak Year Risk':>20} {'2025 Risk':>15}")
        print("-" * 80)
        
        for _, row in comparison_df.iterrows():
            print(f"{row['Scenario']:<20} ${row['Total NPV']:>14,.0f} {row['Peak Year']:>20} "
                  f"${row['2025 Penalty']:>14,.0f}")
        
        # If hybrid scenario, show opt-in breakdown
        if 'hybrid' in scenarios:
            hybrid_df = scenarios['hybrid']
            if 'opt_in_rationale' in hybrid_df.columns:
                print("\n\nHybrid Scenario - Opt-In Decision Breakdown:")
                print("-" * 60)
                rationale_counts = hybrid_df[hybrid_df['should_opt_in'] == True]['opt_in_rationale'].value_counts()
                for rationale, count in rationale_counts.items():
                    print(f"  {rationale}: {count} buildings")
    
    def sensitivity_analysis(self, base_scenario: pd.DataFrame, 
                           adjustment_pct: float = 0.20) -> Dict[str, pd.DataFrame]:
        """
        Perform sensitivity analysis on opt-in rates.
        
        Args:
            base_scenario: The hybrid scenario DataFrame
            adjustment_pct: Percentage to adjust opt-in rates (default ±20%)
            
        Returns:
            Dictionary with high and low sensitivity scenarios
        """
        print(f"\n🔄 SENSITIVITY ANALYSIS (±{adjustment_pct*100:.0f}% opt-in rate)")
        
        # Only works on hybrid scenario
        if 'should_opt_in' not in base_scenario.columns:
            print("  ⚠️  Sensitivity analysis only applicable to hybrid scenario")
            return {}
        
        # Current opt-in rate
        current_opt_in_rate = base_scenario['should_opt_in'].mean()
        print(f"  Current opt-in rate: {current_opt_in_rate*100:.1f}%")
        
        # Create scenarios
        scenarios = {}
        
        # High opt-in scenario
        high_scenario = base_scenario.copy()
        borderline_buildings = high_scenario[
            (high_scenario['opt_in_confidence'] >= 50) & 
            (high_scenario['opt_in_confidence'] <= 80) &
            (~high_scenario['should_opt_in'])
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
        
        new_opt_in_rate = high_scenario['should_opt_in'].mean()
        print(f"  High scenario opt-in rate: {new_opt_in_rate*100:.1f}%")
        scenarios['high_opt_in'] = high_scenario
        
        # Low opt-in scenario (similar logic but opposite)
        low_scenario = base_scenario.copy()
        borderline_opt_ins = low_scenario[
            (low_scenario['opt_in_confidence'] >= 50) & 
            (low_scenario['opt_in_confidence'] <= 80) &
            (low_scenario['should_opt_in'])
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
        
        new_opt_in_rate = low_scenario['should_opt_in'].mean()
        print(f"  Low scenario opt-in rate: {new_opt_in_rate*100:.1f}%")
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
                'npv_advantage': 'mean',
                'penalty_2025': 'sum',
                'penalty_2030': 'sum',
                'sqft': 'sum'
            }).round(2)
            
            # Flatten column names
            analysis.columns = ['_'.join(col).strip() for col in analysis.columns.values]
            analysis.columns = ['total_buildings', 'opt_in_count', 'opt_in_rate', 
                               'avg_npv_advantage', 'total_penalty_2025', 
                               'total_penalty_2030', 'total_sqft']
            
            # Sort by opt-in rate
            analysis = analysis.sort_values('opt_in_rate', ascending=False)
            
            # Filter to significant property types
            analysis = analysis[analysis['total_buildings'] >= 10]
            
            print("\nOpt-In Rates by Property Type (10+ buildings):")
            print("-" * 80)
            for prop_type, row in analysis.iterrows():
                print(f"{prop_type:<35} {row['opt_in_rate']*100:>5.1f}% "
                      f"({int(row['opt_in_count']):>3}/{int(row['total_buildings']):>3}) "
                      f"NPV Adv: ${row['avg_npv_advantage']:>10,.0f}")
        else:
            # For non-hybrid scenarios, just show penalty distribution
            analysis = scenario_df.groupby('property_type').agg({
                'building_id': 'count',
                'penalty_2025': 'sum',
                'penalty_2030': 'sum',
                'sqft': 'sum'
            })
            analysis.columns = ['total_buildings', 'total_penalty_2025', 
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
                    
                    time_series_data.append({
                        'scenario': scenario_name,
                        'year': year,
                        'total_penalty': total_penalty,
                        'buildings_at_risk': buildings_at_risk
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
        
        return time_series_df
    
    def create_visualizations(self, scenarios: Dict[str, pd.DataFrame], 
                            output_dir: str = None):
        """Create comprehensive visualizations with requested improvements"""
        if output_dir is None:
            output_dir = os.path.join(self.data_dir, '..', 'outputs', 'portfolio_analysis')
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up the figure
        fig = plt.figure(figsize=(20, 12))
        
        # 1. Scenario Comparison - Total NPV (ONLY THROUGH 2032)
        ax1 = plt.subplot(2, 3, 1)
        scenario_names = []
        npv_values = []
        
        for name, df in scenarios.items():
            scenario_names.append(name.replace('_', ' ').title())
            
            # Calculate NPV only through 2032
            npv_total = 0
            for year in range(2025, 2033):  # Changed from 2043 to 2033
                col_name = f'penalty_{year}'
                if col_name in df.columns:
                    penalty = df[col_name].sum()
                    years_from_2025 = year - 2025
                    npv_total += penalty / ((1.07) ** years_from_2025)
            
            npv_values.append(npv_total)
        
        # Only show the main 3 scenarios in bar chart
        main_scenarios = ['All Standard', 'All Aco', 'Hybrid']
        main_npvs = npv_values[:3]
        
        bars = ax1.bar(main_scenarios, [v/1e6 for v in main_npvs], 
                       color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        ax1.set_ylabel('Total NPV of Penalties ($M)')
        ax1.set_title('Portfolio Risk by Scenario (NPV @ 7%, 2025-2032)')
        
        # Add value labels
        for bar, val in zip(bars, main_npvs):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'${val/1e6:.1f}M', ha='center', va='bottom')
        
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
                    'building_id': 'count'
                }).sort_values('should_opt_in', ascending=False)
                
                # Filter to top 10 property types by count
                top_types = prop_type_data.nlargest(10, 'building_id')
                
                y_pos = np.arange(len(top_types))
                ax3.barh(y_pos, top_types['should_opt_in'] * 100)
                ax3.set_yticks(y_pos)
                ax3.set_yticklabels(top_types.index)
                ax3.set_xlabel('Opt-In Rate (%)')
                ax3.set_title('Opt-In Rates by Property Type (Top 10)')
                
                # Add improved count labels showing n=x/total
                total_buildings = len(hybrid_df)
                for i, (idx, row) in enumerate(top_types.iterrows()):
                    opt_in_count = int(row['should_opt_in'] * row['building_id'])
                    ax3.text(row['should_opt_in'] * 100 + 1, i,
                            f"n={opt_in_count}/{int(row['building_id'])}", 
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
        
        # 5. Summary Findings Text (replacing confidence distribution)
        ax5 = plt.subplot(2, 3, 5)
        ax5.axis('off')
        
        # Generate summary text based on analysis
        summary_text = "Key Portfolio Insights\n" + "="*40 + "\n\n"
        
        if 'hybrid' in scenarios:
            hybrid_df = scenarios['hybrid']
            
            # Opt-in statistics
            if 'should_opt_in' in hybrid_df.columns:
                opt_in_rate = hybrid_df['should_opt_in'].mean() * 100
                opt_in_count = hybrid_df['should_opt_in'].sum()
                summary_text += f"Opt-In Analysis:\n"
                summary_text += f"  - {opt_in_count:,} buildings ({opt_in_rate:.1f}%) predicted to opt into ACO path\n"
                
                # Confidence analysis
                if 'opt_in_confidence' in hybrid_df.columns:
                    avg_confidence = hybrid_df['opt_in_confidence'].mean()
                    high_confidence = (hybrid_df['opt_in_confidence'] >= 80).sum()
                    low_confidence = (hybrid_df['opt_in_confidence'] <= 50).sum()
                    summary_text += f"  - Average decision confidence: {avg_confidence:.1f}%\n"
                    summary_text += f"  - High confidence (>=80%): {high_confidence:,} buildings\n"
                    summary_text += f"  - Low confidence (<=50%): {low_confidence:,} buildings\n"
                
                # NPV advantage
                if 'npv_advantage' in hybrid_df.columns:
                    opt_in_buildings = hybrid_df[hybrid_df['should_opt_in'] == True]
                    avg_npv_advantage = opt_in_buildings['npv_advantage'].mean()
                    total_npv_advantage = opt_in_buildings['npv_advantage'].sum()
                    summary_text += f"\nFinancial Impact:\n"
                    summary_text += f"  - Average NPV advantage per opt-in building: ${avg_npv_advantage:,.0f}\n"
                    summary_text += f"  - Total portfolio NPV advantage: ${total_npv_advantage/1e6:.1f}M\n"
                
                # Primary rationales
                if 'opt_in_rationale' in hybrid_df.columns:
                    rationale_counts = hybrid_df[hybrid_df['should_opt_in'] == True]['opt_in_rationale'].value_counts()
                    if len(rationale_counts) > 0:
                        summary_text += f"\nPrimary Opt-In Drivers:\n"
                        for i, (rationale, count) in enumerate(rationale_counts.head(3).items()):
                            pct = (count / opt_in_count * 100) if opt_in_count > 0 else 0
                            summary_text += f"  - {rationale}: {count:,} buildings ({pct:.1f}%)\n"
        
        # Risk concentration
        if 'all_standard' in scenarios:
            standard_df = scenarios['all_standard']
            total_2025_penalty = standard_df['penalty_2025'].sum() if 'penalty_2025' in standard_df.columns else 0
            top_10_penalty = standard_df.nlargest(10, 'penalty_2025')['penalty_2025'].sum() if 'penalty_2025' in standard_df.columns else 0
            if total_2025_penalty > 0:
                concentration = (top_10_penalty / total_2025_penalty) * 100
                summary_text += f"\nRisk Concentration:\n"
                summary_text += f"  - Top 10 buildings account for {concentration:.1f}% of 2025 penalties\n"
        
        # Add text to plot with proper formatting
        ax5.text(0.05, 0.95, summary_text, transform=ax5.transAxes, 
                fontsize=9, verticalalignment='top', fontfamily='sans-serif',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.9))
        
        ax5.set_title('Portfolio Analysis Summary', fontsize=14, weight='bold', pad=20)
        
        # 6. Financial Impact Summary - IMPROVED TABLE WITH MORE COLUMNS
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
            
            summary_data.append([
                scenario_label,
                f"{len(df):,}",
                f"{at_risk_2025:,}",
                f"{at_risk_2027:,}",
                f"{at_risk_2028:,}",
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
        table.scale(1.4, 2.0)
        
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
        fig_path = os.path.join(output_dir, f'portfolio_analysis_{timestamp}.png')
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        print(f"\n📊 Visualizations saved to: {fig_path}")
        
        return fig
    
    def generate_report(self, output_path: str = None):
        """Generate comprehensive portfolio risk report"""
        print("\n📋 GENERATING COMPREHENSIVE PORTFOLIO RISK REPORT")
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
            
            # Calculate NPV only through 2032
            npv_total = 0
            for year in range(2025, 2033):
                col_name = f'penalty_{year}'
                if col_name in df.columns:
                    penalty = df[col_name].sum()
                    years_from_2025 = year - 2025
                    npv_total += penalty / ((1.07) ** years_from_2025)
            
            # Buildings at risk by year
            at_risk_2025 = (df['penalty_2025'] > 0).sum() if 'penalty_2025' in df.columns else 0
            at_risk_2027 = (df['penalty_2027'] > 0).sum() if 'penalty_2027' in df.columns else 0
            at_risk_2028 = (df['penalty_2028'] > 0).sum() if 'penalty_2028' in df.columns else 0
            at_risk_2030 = (df['penalty_2030'] > 0).sum() if 'penalty_2030' in df.columns else 0
            at_risk_2032 = (df['penalty_2032'] > 0).sum() if 'penalty_2032' in df.columns else 0
            
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
            
            summary_rows.append({
                'Scenario': name.replace('_', ' ').title(),
                'Total Buildings': len(df),
                'Total Sq Ft': f"{total_sqft:,.0f}",
                'NPV of Penalties (2025-2032)': f"${npv_total:,.0f}",
                'Buildings at Risk 2025': at_risk_2025,
                'Buildings at Risk 2027': at_risk_2027,
                'Buildings at Risk 2028': at_risk_2028,
                'Buildings at Risk 2030': at_risk_2030,
                'Buildings at Risk 2032': at_risk_2032,
                'Avg $/sqft 2028 (at-risk only)': f"${avg_2028:.3f}",
                'Avg $/sqft 2030 (at-risk only)': f"${avg_2030:.3f}",
                'Avg $/sqft 2032 (at-risk only)': f"${avg_2032:.3f}",
                'Opt-In Rate': f"{df['should_opt_in'].mean()*100:.1f}%" if 'should_opt_in' in df.columns else "N/A"
            })
        
        return pd.DataFrame(summary_rows)


# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = PortfolioRiskAnalyzer()
    
    # Generate full report
    output_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/portfolio_risk_analysis_refined.json'
    scenarios, fig = analyzer.generate_report(output_path)
    
    # Show visualizations
    plt.show()
