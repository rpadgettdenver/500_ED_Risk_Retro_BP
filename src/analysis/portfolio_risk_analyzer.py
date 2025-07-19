"""
Suggested File Name: portfolio_risk_analyzer.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis/
Use: Comprehensive portfolio risk analysis with three scenarios and enhanced analytics

This analyzer provides:
1. Three scenarios: All Standard, All ACO, and Hybrid/Realistic
2. Year normalization for aggregate analysis
3. Sensitivity analysis on opt-in rates
4. Property type trends analysis
5. Time series penalty evolution
6. Comprehensive risk metrics for the entire portfolio
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
            
            # Calculate NPV (7% discount rate from 2025)
            npv_total = 0
            for year_str, penalty in yearly_totals.items():
                year = int(year_str)
                years_from_2025 = year - 2025
                if years_from_2025 >= 0:
                    npv_total += penalty / ((1.07) ** years_from_2025)
            
            # Key years
            penalty_2025 = yearly_totals.get('2025', 0)
            penalty_2027 = yearly_totals.get('2027', 0)
            penalty_2028 = yearly_totals.get('2028', 0)
            penalty_2030 = yearly_totals.get('2030', 0)
            penalty_2032 = yearly_totals.get('2032', 0)
            
            # Peak year
            peak_year = max(yearly_totals.items(), key=lambda x: x[1])
            
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
        print("\nKey Metrics Comparison:")
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
        
        # Extract yearly penalties for each scenario
        years = list(range(2025, 2043))
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
        key_years = [2025, 2027, 2028, 2030, 2032, 2035, 2040]
        
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
        """Create comprehensive visualizations"""
        if output_dir is None:
            output_dir = os.path.join(self.data_dir, '..', 'outputs', 'portfolio_analysis')
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up the figure
        fig = plt.figure(figsize=(20, 12))
        
        # 1. Scenario Comparison - Total NPV
        ax1 = plt.subplot(2, 3, 1)
        scenario_names = []
        npv_values = []
        
        for name, df in scenarios.items():
            scenario_names.append(name.replace('_', ' ').title())
            
            # Calculate NPV
            npv_total = 0
            for year in range(2025, 2043):
                col_name = f'penalty_{year}'
                if col_name in df.columns:
                    penalty = df[col_name].sum()
                    years_from_2025 = year - 2025
                    npv_total += penalty / ((1.07) ** years_from_2025)
            
            npv_values.append(npv_total)
        
        bars = ax1.bar(scenario_names, [v/1e6 for v in npv_values], 
                       color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        ax1.set_ylabel('Total NPV of Penalties ($M)')
        ax1.set_title('Portfolio Risk by Scenario (NPV @ 7%)')
        
        # Add value labels
        for bar, val in zip(bars, npv_values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'${val/1e6:.1f}M', ha='center', va='bottom')
        
        # 2. Time Series - Penalty Evolution
        ax2 = plt.subplot(2, 3, 2)
        time_series_df = self.time_series_analysis(scenarios)
        
        for scenario in scenarios.keys():
            scenario_data = time_series_df[time_series_df['scenario'] == scenario]
            ax2.plot(scenario_data['year'], scenario_data['total_penalty']/1e6,
                    label=scenario.replace('_', ' ').title(), linewidth=2, marker='o')
        
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Total Penalties ($M)')
        ax2.set_title('Penalty Evolution Over Time')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Property Type Analysis (for hybrid scenario)
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
                
                # Add count labels
                for i, (idx, row) in enumerate(top_types.iterrows()):
                    ax3.text(row['should_opt_in'] * 100 + 1, i,
                            f"n={int(row['building_id'])}", 
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
        
        # 5. Opt-In Decision Confidence (for hybrid)
        ax5 = plt.subplot(2, 3, 5)
        if 'hybrid' in scenarios and 'opt_in_confidence' in scenarios['hybrid'].columns:
            confidence_data = scenarios['hybrid']['opt_in_confidence']
            ax5.hist(confidence_data, bins=20, edgecolor='black')
            ax5.set_xlabel('Decision Confidence (%)')
            ax5.set_ylabel('Number of Buildings')
            ax5.set_title('Opt-In Decision Confidence Distribution')
            ax5.axvline(x=confidence_data.mean(), color='red', linestyle='--',
                       label=f'Mean: {confidence_data.mean():.1f}%')
            ax5.legend()
        
        # 6. Financial Impact Summary
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        # Create summary table
        summary_data = []
        for name, df in scenarios.items():
            total_sqft = df['sqft'].sum()
            buildings_at_risk_2025 = (df['penalty_2025'] > 0).sum() if 'penalty_2025' in df.columns else 0
            avg_penalty_per_sqft = df['penalty_2030'].sum() / total_sqft if 'penalty_2030' in df.columns else 0
            
            summary_data.append([
                name.replace('_', ' ').title(),
                f"{len(df):,}",
                f"{buildings_at_risk_2025:,}",
                f"${avg_penalty_per_sqft:.3f}"
            ])
        
        table = ax6.table(cellText=summary_data,
                         colLabels=['Scenario', 'Total Buildings', 
                                   'At Risk 2025', 'Avg $/sqft 2030'],
                         cellLoc='center',
                         loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2)
        ax6.set_title('Portfolio Summary Statistics', pad=20)
        
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
                for name, df in scenarios.items():
                    df.to_excel(writer, sheet_name=name, index=False)
                
                # Add property type analysis
                for name, analysis in property_analysis.items():
                    analysis.to_excel(writer, sheet_name=f'{name}_by_type')
            
            print(f"\n✓ Detailed results saved to: {excel_path}")
        
        print("\n🎯 ANALYSIS COMPLETE!")
        
        return scenarios, fig


# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = PortfolioRiskAnalyzer()
    
    # Generate full report
    output_path = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/outputs/data/portfolio_risk_analysis.json'
    scenarios, fig = analyzer.generate_report(output_path)
    
    # Show visualizations
    plt.show()
