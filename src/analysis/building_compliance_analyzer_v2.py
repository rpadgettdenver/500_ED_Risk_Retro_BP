"""
Suggested File Name: building_compliance_analyzer_v2.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis/
Use: Enhanced building compliance analyzer with NPV, caps/floors, and sophisticated opt-in logic

This updated script:
1. Uses the unified penalty calculator and EUI target loader
2. Implements NPV analysis with 7% discount rate
3. Applies 42% reduction cap and MAI floor via the modules
4. Provides sophisticated opt-in recommendations
5. Includes technical feasibility scoring

CHANGES MADE:
- Import from correct modules: EnergizeDenverPenaltyCalculator and load_building_targets
- Remove hardcoded penalty rates
- Use centralized target loading logic
- Fixed method calls to match actual penalty calculator API
- Fixed opt-in path visualization to start from baseline year, not current year
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import json
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the correct unified modules
from utils.penalty_calculator import EnergizeDenverPenaltyCalculator
from utils.eui_target_loader import load_building_targets

class EnhancedBuildingComplianceAnalyzer:
    def __init__(self, building_id, data_dir='/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data'):
        """Initialize analyzer for a specific building"""
        self.building_id = str(building_id)
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, 'processed')
        self.raw_dir = os.path.join(data_dir, 'raw')
        
        # Initialize penalty calculator with correct class
        self.calc = EnergizeDenverPenaltyCalculator()
        
        # Load necessary data
        self.load_data()
        
    def load_data(self):
        """Load all necessary data files"""
        print(f"📊 Loading data for Building {self.building_id}...")
        
        # Load comprehensive current data
        self.df_current = pd.read_csv(os.path.join(self.processed_dir, 'energize_denver_comprehensive_latest.csv'))
        self.df_current['Building ID'] = self.df_current['Building ID'].astype(str)
        
        # Load all years data for historical analysis
        all_years_files = [f for f in os.listdir(self.processed_dir) if f.startswith('energize_denver_all_years_')]
        if all_years_files:
            latest_all_years = sorted(all_years_files)[-1]
            self.df_all_years = pd.read_csv(os.path.join(self.processed_dir, latest_all_years))
            self.df_all_years['Building ID'] = self.df_all_years['Building ID'].astype(str)
        
        # Get building-specific data
        self.building_current = self.df_current[self.df_current['Building ID'] == self.building_id]
        self.building_history = self.df_all_years[self.df_all_years['Building ID'] == self.building_id]
        
        # Load targets using the centralized loader
        try:
            self.building_targets_data = load_building_targets(self.building_id)
            print(f"✓ Loaded targets for Building {self.building_id} using centralized loader")
        except Exception as e:
            print(f"⚠️  Error loading targets: {e}")
            self.building_targets_data = None
        
        if len(self.building_current) == 0:
            raise ValueError(f"Building {self.building_id} not found in current data")
        
        print(f"✓ Found data for Building {self.building_id}")
        print(f"  Property Type: {self.building_current.iloc[0]['Master Property Type']}")
        print(f"  Square Footage: {self.building_current.iloc[0]['Master Sq Ft']:,.0f}")
        
    def prepare_building_data(self):
        """Prepare building data for penalty calculations"""
        building = self.building_current.iloc[0]
        
        if self.building_targets_data is None:
            print("⚠️  No targets found for this building")
            return None
            
        # Extract key data from current building record
        current_eui = pd.to_numeric(building['Weather Normalized Site EUI'], errors='coerce')
        sqft = pd.to_numeric(building['Master Sq Ft'], errors='coerce')
        property_type = building['Master Property Type']
        year_built = pd.to_numeric(building.get('Year Built', 1990), errors='coerce')
        
        # Use data from centralized loader
        targets_data = self.building_targets_data
        
        # Extract targets from the centralized loader
        targets = {
            2025: targets_data['first_interim_target'],
            2027: targets_data['second_interim_target'],
            2030: targets_data['final_target_with_logic']  # Uses adjusted target with caps/MAI logic
        }
        
        # For opt-in path, calculate 2028 interim and use same final for 2032
        targets[2028] = self.calculate_opt_in_interim_target(targets_data)
        targets[2032] = targets[2030]  # Same final target
        
        # Check for cash constraints (simplified logic)
        cash_constrained = property_type in ['Affordable Housing', 'Senior Care Community']
        
        return {
            'building_id': self.building_id,
            'building_name': building.get('Building Name', 'Unknown'),
            'current_eui': current_eui,
            'baseline_eui': targets_data['baseline_eui'],
            'sqft': sqft,
            'property_type': property_type,
            'is_mai': targets_data['is_mai'],
            'targets': targets,
            'building_age': 2024 - year_built if not pd.isna(year_built) else 30,
            'cash_constrained': cash_constrained,
            'has_target_adjustment': targets_data.get('has_target_adjustment', False),
            'has_electrification_credit': targets_data.get('has_electrification_credit', False)
        }
    
    def calculate_opt_in_interim_target(self, targets_data):
        """Calculate opt-in path interim target for 2028"""
        baseline_eui = targets_data['baseline_eui']
        final_target = targets_data['final_target_with_logic']
        
        # Assume baseline year is 2019 (could enhance to read from data)
        baseline_year = 2019
        
        # Linear interpolation from baseline (2019) to final (2032)
        total_years = 2032 - baseline_year  # 13 years
        years_to_2028 = 2028 - baseline_year  # 9 years
        
        if total_years > 0 and baseline_eui > 0:
            progress_ratio = years_to_2028 / total_years
            interim_target = baseline_eui - (baseline_eui - final_target) * progress_ratio
            return interim_target
        
        return final_target
    
    def calculate_enhanced_penalties(self):
        """Calculate penalties using centralized calculator with NPV analysis"""
        
        # Prepare building data
        building_data = self.prepare_building_data()
        if building_data is None:
            return None
            
        # Initialize results structure
        analysis = {
            'building_id': self.building_id,
            'current_eui': building_data['current_eui'],
            'baseline_eui': building_data['baseline_eui'],
            'is_mai': building_data['is_mai'],
            'adjusted_targets': building_data['targets'],
            'standard_path': {
                'penalties_by_year': {},
                'total_nominal': 0,
                'total_npv': 0
            },
            'optin_path': {
                'penalties_by_year': {},
                'total_nominal': 0,
                'total_npv': 0
            }
        }
        
        # Calculate standard path penalties (2025, 2027, 2030)
        standard_years = [2025, 2027, 2030]
        for year in standard_years:
            target = building_data['targets'].get(year, 0)
            if target > 0 and building_data['current_eui'] > target:
                exceedance = building_data['current_eui'] - target
                
                # Get penalty rate for standard path
                penalty_rate = self.calc.get_penalty_rate('standard')  # $0.15/kBtu
                
                # Calculate penalty using the correct method signature
                penalty = self.calc.calculate_penalty(
                    actual_eui=building_data['current_eui'],
                    target_eui=target,
                    sqft=building_data['sqft'],
                    penalty_rate=penalty_rate
                )
                
                # Calculate NPV (7% discount rate)
                years_from_now = year - 2025
                npv = penalty / ((1.07) ** years_from_now)
                
                analysis['standard_path']['penalties_by_year'][year] = {
                    'target': target,
                    'exceedance': exceedance,
                    'penalty': penalty,
                    'npv': npv
                }
                analysis['standard_path']['total_nominal'] += penalty
                analysis['standard_path']['total_npv'] += npv
        
        # Calculate opt-in path penalties (2028, 2032)
        optin_years = [2028, 2032]
        for year in optin_years:
            target = building_data['targets'].get(year, 0)
            if target > 0 and building_data['current_eui'] > target:
                exceedance = building_data['current_eui'] - target
                
                # Get penalty rate for ACO (alternate compliance option)
                penalty_rate = self.calc.get_penalty_rate('aco')  # $0.23/kBtu
                
                # Calculate penalty
                penalty = self.calc.calculate_penalty(
                    actual_eui=building_data['current_eui'],
                    target_eui=target,
                    sqft=building_data['sqft'],
                    penalty_rate=penalty_rate
                )
                
                # Calculate NPV
                years_from_now = year - 2025
                npv = penalty / ((1.07) ** years_from_now)
                
                analysis['optin_path']['penalties_by_year'][year] = {
                    'target': target,
                    'exceedance': exceedance,
                    'penalty': penalty,
                    'npv': npv
                }
                analysis['optin_path']['total_nominal'] += penalty
                analysis['optin_path']['total_npv'] += npv
        
        # Add retrofit analysis
        reduction_needed = max(0, building_data['current_eui'] - building_data['targets'][2030])
        reduction_pct = reduction_needed / building_data['current_eui'] * 100 if building_data['current_eui'] > 0 else 0
        
        # Estimate retrofit costs based on reduction needed
        if reduction_pct <= 10:
            cost_per_sqft = 5
            retrofit_level = "minor"
        elif reduction_pct <= 25:
            cost_per_sqft = 15
            retrofit_level = "moderate"
        elif reduction_pct <= 40:
            cost_per_sqft = 30
            retrofit_level = "major"
        else:
            cost_per_sqft = 50
            retrofit_level = "deep"
            
        analysis['retrofit_analysis'] = {
            'reduction_needed': reduction_needed,
            'reduction_pct': reduction_pct,
            'retrofit_level': retrofit_level,
            'cost_per_sqft': cost_per_sqft,
            'total_cost': cost_per_sqft * building_data['sqft']
        }
        
        # Technical difficulty assessment
        building_age = building_data['building_age']
        difficulty_score = min(100, reduction_pct * 2 + building_age / 2)
        
        if difficulty_score < 30:
            feasibility = "straightforward"
        elif difficulty_score < 60:
            feasibility = "moderate_complexity"
        elif difficulty_score < 80:
            feasibility = "technically_challenging"
        else:
            feasibility = "extremely_difficult"
            
        analysis['technical_difficulty'] = {
            'score': difficulty_score,
            'feasibility': feasibility,
            'building_age': building_age
        }
        
        # Generate recommendation
        npv_advantage = analysis['standard_path']['total_npv'] - analysis['optin_path']['total_npv']
        
        # Decision logic
        if npv_advantage > 50000:
            recommendation = "opt-in"
            confidence = min(95, 50 + npv_advantage / 5000)
            primary_reason = f"Significant NPV advantage of ${npv_advantage:,.0f}"
        elif building_data['cash_constrained']:
            recommendation = "opt-in"
            confidence = 85
            primary_reason = "Cash flow constraints favor delayed penalties"
        elif reduction_pct > 35:
            recommendation = "opt-in"
            confidence = 80
            primary_reason = f"High reduction requirement ({reduction_pct:.1f}%) needs more time"
        elif npv_advantage > 10000:
            recommendation = "opt-in"
            confidence = 70
            primary_reason = f"Moderate NPV advantage of ${npv_advantage:,.0f}"
        else:
            recommendation = "standard"
            confidence = 60
            primary_reason = "Lower overall costs with standard path"
            
        analysis['recommendation'] = {
            'recommendation': recommendation,
            'confidence': confidence,
            'primary_reason': primary_reason,
            'npv_advantage': npv_advantage,
            'decision_factors': {
                'npv_advantage': npv_advantage,
                'reduction_pct': reduction_pct,
                'technical_score': difficulty_score,
                'cash_constrained': building_data['cash_constrained'],
                'building_age': building_age
            },
            'secondary_reasons': []
        }
        
        # Add secondary reasons
        if building_data['is_mai']:
            analysis['recommendation']['secondary_reasons'].append("MAI building has more lenient targets")
        if building_data['has_target_adjustment']:
            analysis['recommendation']['secondary_reasons'].append("Building has approved target adjustment")
        if difficulty_score > 70:
            analysis['recommendation']['secondary_reasons'].append("Technical complexity favors more time")
            
        return analysis
    
    def create_enhanced_visualizations(self):
        """Create comprehensive visualizations including NPV analysis"""
        fig, axes = plt.subplots(2, 3, figsize=(20, 14))
        fig.suptitle(f'Building {self.building_id} - Enhanced Compliance Analysis', fontsize=16)
        
        # Get building info for subtitle
        building = self.building_current.iloc[0]
        property_type = building['Master Property Type']
        building_name = building.get('Building Name', 'Unknown')
        
        fig.text(0.5, 0.94, f'{building_name} ({property_type})', ha='center', fontsize=12)
        
        # 1. Historical Energy Use and EUI
        self.plot_historical_energy(axes[0, 0])
        
        # 2. Weather Normalized EUI Trends with Targets
        self.plot_weather_normalized_with_caps(axes[0, 1])
        
        # 3. NPV Comparison
        self.plot_npv_comparison(axes[0, 2])
        
        # 4. Compliance Pathways with Adjustments
        self.plot_adjusted_pathways(axes[1, 0])
        
        # 5. Decision Factors
        self.plot_decision_factors(axes[1, 1])
        
        # 6. Financial Summary
        self.plot_financial_summary(axes[1, 2])
        
        plt.tight_layout()
        return fig
    
    def plot_historical_energy(self, ax):
        """Plot historical energy use and EUI"""
        history = self.building_history.sort_values('Reporting Year')
        
        # Convert to numeric
        history['Site Energy Use'] = pd.to_numeric(history['Site Energy Use'], errors='coerce')
        history['Site EUI'] = pd.to_numeric(history['Site EUI'], errors='coerce')
        
        # Create twin axis for EUI
        ax2 = ax.twinx()
        
        # Plot total energy use
        ax.bar(history['Reporting Year'], 
               history['Site Energy Use'], 
               alpha=0.7, color='steelblue', label='Site Energy Use')
        
        # Plot EUI
        ax2.plot(history['Reporting Year'], 
                history['Site EUI'], 
                color='darkred', marker='o', linewidth=2, markersize=8, 
                label='Site EUI')
        
        ax.set_xlabel('Year')
        ax.set_ylabel('Site Energy Use (kBtu)', color='steelblue')
        ax2.set_ylabel('Site EUI (kBtu/ft²)', color='darkred')
        ax.set_title('Historical Energy Use and EUI')
        
        ax.tick_params(axis='y', labelcolor='steelblue')
        ax2.tick_params(axis='y', labelcolor='darkred')
        
        ax.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
    
    def plot_weather_normalized_with_caps(self, ax):
        """Plot weather normalized EUI with cap/floor adjustments"""
        analysis = self.calculate_enhanced_penalties()
        if analysis is None:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
            
        history = self.building_history.sort_values('Reporting Year')
        history['Weather Normalized Site EUI'] = pd.to_numeric(
            history['Weather Normalized Site EUI'], errors='coerce')
        
        # Plot historical data
        history_clean = history[history['Weather Normalized Site EUI'].notna()]
        ax.plot(history_clean['Reporting Year'], 
               history_clean['Weather Normalized Site EUI'], 
               'ko-', linewidth=2, markersize=8, label='Actual EUI')
        
        # Plot adjusted targets
        years = [2025, 2027, 2030]
        adjusted_targets = [analysis['adjusted_targets'].get(year, 0) for year in years]
        
        ax.plot(years, adjusted_targets, 'g^-', linewidth=2, markersize=10,
               label='Adjusted Targets')
        
        # Add 42% cap line if not MAI
        if not analysis.get('is_mai', False):
            baseline_eui = analysis.get('baseline_eui', analysis['current_eui'])
            cap_eui = baseline_eui * 0.58  # 42% reduction = 58% of baseline
            ax.axhline(y=cap_eui, color='orange', linestyle='--', 
                      label=f'42% Cap ({cap_eui:.1f})')
        
        # Add MAI floor if applicable
        if analysis.get('is_mai', False):
            ax.axhline(y=52.9, color='red', linestyle='--', 
                      label='MAI Floor (52.9)')
        
        ax.set_xlabel('Year')
        ax.set_ylabel('Weather Normalized EUI (kBtu/ft²)')
        ax.set_title('EUI Trends with Target Adjustments')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def plot_npv_comparison(self, ax):
        """Plot NPV comparison between paths"""
        analysis = self.calculate_enhanced_penalties()
        if analysis is None:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
            
        # Extract data
        standard_npv = analysis['standard_path']['total_npv']
        optin_npv = analysis['optin_path']['total_npv']
        standard_nominal = analysis['standard_path']['total_nominal']
        optin_nominal = analysis['optin_path']['total_nominal']
        
        # Create comparison bars
        paths = ['Standard\n(Nominal)', 'Standard\n(NPV)', 'Opt-in\n(Nominal)', 'Opt-in\n(NPV)']
        values = [standard_nominal, standard_npv, optin_nominal, optin_npv]
        colors = ['lightblue', 'darkblue', 'lightgreen', 'darkgreen']
        
        bars = ax.bar(paths, values, color=colors)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'${value:,.0f}', ha='center', va='bottom')
        
        # Add NPV savings annotation
        npv_advantage = standard_npv - optin_npv
        ax.text(0.5, 0.95, f'NPV Advantage of Opt-in: ${npv_advantage:,.0f}',
               transform=ax.transAxes, ha='center', fontsize=12,
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Add penalty rates annotation
        ax.text(0.02, 0.02, 'Standard: $0.15/kBtu\nOpt-in: $0.23/kBtu',
               transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        ax.set_ylabel('Penalty Amount ($)')
        ax.set_title('Nominal vs NPV Penalty Comparison (7% Discount Rate)')
        ax.grid(True, alpha=0.3, axis='y')
    
    def plot_adjusted_pathways(self, ax):
        """Plot compliance pathways with all adjustments"""
        analysis = self.calculate_enhanced_penalties()
        if analysis is None:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
            
        # Get targets
        targets = analysis['adjusted_targets']
        current_eui = analysis['current_eui']
        baseline_eui = analysis.get('baseline_eui', current_eui)
        
        # Get baseline year from targets data (default to 2019)
        baseline_year = 2019
        if self.building_targets_data:
            # Could enhance to read baseline year from data if available
            baseline_year = 2019
        
        # Standard path: baseline → 2025 → 2027 → 2030
        standard_years = [baseline_year, 2025, 2027, 2030]
        standard_euis = [
            baseline_eui,
            targets.get(2025, 0),
            targets.get(2027, 0),
            targets.get(2030, 0)
        ]
        
        # ACO/Opt-in path: baseline → 2028 → 2032
        # Per source of truth: opt-in path also starts from baseline year/EUI
        optin_years = [baseline_year, 2028, 2032]
        optin_euis = [
            baseline_eui,  # Start from baseline, not current
            targets.get(2028, 0),
            targets.get(2032, 0)
        ]
        
        # Plot paths
        ax.plot(standard_years, standard_euis, 'b-o', linewidth=2, markersize=8,
               label='Standard Path ($0.15/kBtu)')
        ax.plot(optin_years, optin_euis, 'g-s', linewidth=2, markersize=8,
               label='ACO/Opt-in Path ($0.23/kBtu)')
        
        # Current EUI line
        ax.axhline(y=current_eui, color='red', linestyle='-', alpha=0.7,
                  label=f'Current EUI ({current_eui:.1f})')
        
        # Baseline EUI line (if different from current)
        if abs(baseline_eui - current_eui) > 0.1:
            ax.axhline(y=baseline_eui, color='gray', linestyle=':', alpha=0.5,
                      label=f'Baseline EUI ({baseline_eui:.1f})')
        
        # Shade penalty zones for both paths
        # Standard path penalty zone
        ax.fill_between(standard_years, current_eui, standard_euis, 
                       where=[eui < current_eui for eui in standard_euis],
                       alpha=0.15, color='blue', label='Standard Penalty Zone')
        
        # Opt-in path penalty zone (lighter shade)
        ax.fill_between(optin_years, current_eui, optin_euis, 
                       where=[eui < current_eui for eui in optin_euis],
                       alpha=0.15, color='green')
        
        # Add target year annotations
        for year, eui in zip([2025, 2027, 2030], [targets.get(2025, 0), targets.get(2027, 0), targets.get(2030, 0)]):
            if eui > 0:
                ax.annotate(f'{year}', xy=(year, eui), xytext=(year, eui-3),
                           ha='center', fontsize=8, color='blue')
        
        for year, eui in zip([2028, 2032], [targets.get(2028, 0), targets.get(2032, 0)]):
            if eui > 0:
                ax.annotate(f'{year}', xy=(year, eui), xytext=(year, eui+3),
                           ha='center', fontsize=8, color='green')
        
        ax.set_xlabel('Year')
        ax.set_ylabel('Weather Normalized EUI (kBtu/ft²)')
        ax.set_title('Compliance Pathways with Adjusted Targets')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(2018, 2033)
    
    def plot_decision_factors(self, ax):
        """Plot decision factors as a bar chart"""
        analysis = self.calculate_enhanced_penalties()
        if analysis is None:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
            
        recommendation = analysis['recommendation']
        factors = recommendation['decision_factors']
        
        # Create factor scores (0-100 scale)
        categories = ['Financial\nAdvantage', 'Technical\nDifficulty', 
                     'Reduction\nRequired', 'Cash Flow\nRisk', 'Confidence']
        
        # Normalize factors to 0-100 scale
        scores = [
            max(0, min(100, 50 + factors['npv_advantage'] / 10000)),  # Scale NPV
            factors['technical_score'],
            min(100, factors['reduction_pct'] * 2),  # Scale percentage
            100 if factors['cash_constrained'] else 20,
            recommendation['confidence']
        ]
        
        # Create bar chart
        bars = ax.bar(categories, scores, color=['green' if s > 50 else 'orange' if s > 30 else 'red' for s in scores])
        
        # Add value labels on bars
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{score:.0f}', ha='center', va='bottom')
        
        # Set y-axis limits
        ax.set_ylim(0, 110)
        ax.set_ylabel('Score (0-100)')
        
        # Add title
        ax.set_title(f'Decision Factors\nRecommendation: {recommendation["recommendation"].upper()}')
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        
        # Rotate x labels
        ax.tick_params(axis='x', rotation=45)
    
    def plot_financial_summary(self, ax):
        """Plot financial summary table"""
        analysis = self.calculate_enhanced_penalties()
        if analysis is None:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
            
        # Create summary data
        summary_data = {
            'Metric': [
                'Standard Path Penalties (Nominal)',
                'Standard Path Penalties (NPV)',
                'Opt-in Path Penalties (Nominal)',
                'Opt-in Path Penalties (NPV)',
                'NPV Advantage of Opt-in',
                'Estimated Retrofit Cost',
                'Technical Difficulty Score',
                'Recommendation',
                'Confidence Level'
            ],
            'Value': [
                f"${analysis['standard_path']['total_nominal']:,.0f}",
                f"${analysis['standard_path']['total_npv']:,.0f}",
                f"${analysis['optin_path']['total_nominal']:,.0f}",
                f"${analysis['optin_path']['total_npv']:,.0f}",
                f"${analysis['recommendation']['npv_advantage']:,.0f}",
                f"${analysis['retrofit_analysis']['total_cost']:,.0f}",
                f"{analysis['technical_difficulty']['score']:.0f}/100",
                analysis['recommendation']['recommendation'].upper(),
                f"{analysis['recommendation']['confidence']}%"
            ]
        }
        
        # Clear axis
        ax.axis('off')
        
        # Create table
        table_data = list(zip(summary_data['Metric'], summary_data['Value']))
        
        # Create the table
        table = ax.table(cellText=table_data,
                        colLabels=['Metric', 'Value'],
                        cellLoc='left',
                        loc='center',
                        colWidths=[0.7, 0.3])
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Color code recommendation row
        recommendation_row = 8  # Index of recommendation row
        if analysis['recommendation']['recommendation'] == 'opt-in':
            table[(recommendation_row, 1)].set_facecolor('#90EE90')  # Light green
        else:
            table[(recommendation_row, 1)].set_facecolor('#87CEEB')  # Sky blue
            
        ax.set_title('Financial Summary & Recommendation', fontsize=12, pad=20)
    
    def generate_enhanced_report(self):
        """Generate a comprehensive report with NPV analysis"""
        print(f"\n📊 ENHANCED COMPLIANCE ANALYSIS REPORT - Building {self.building_id}")
        print("="*80)
        
        # Get analysis
        analysis = self.calculate_enhanced_penalties()
        if analysis is None:
            print("Unable to generate report - missing data")
            return None, None
            
        # Building details
        building = self.building_current.iloc[0]
        print(f"\n🏢 Building Details:")
        print(f"   Name: {building.get('Building Name', 'Unknown')}")
        print(f"   Type: {building['Master Property Type']}")
        print(f"   Size: {building['Master Sq Ft']:,.0f} sq ft")
        print(f"   Current EUI: {analysis['current_eui']:.1f} kBtu/ft²")
        
        # Target information from centralized loader
        if self.building_targets_data:
            print(f"\n🎯 Target Information:")
            print(f"   Is MAI Building: {self.building_targets_data['is_mai']}")
            print(f"   Has Target Adjustment: {self.building_targets_data.get('has_target_adjustment', False)}")
            print(f"   Has Electrification Credit: {self.building_targets_data.get('has_electrification_credit', False)}")
            print(f"   Baseline EUI: {self.building_targets_data['baseline_eui']:.1f}")
            print(f"   Final Target (with logic): {self.building_targets_data['final_target_with_logic']:.1f}")
        
        # Penalty analysis with NPV
        print(f"\n💰 Penalty Analysis (with NPV @ 7% discount rate):")
        
        print(f"\n   Standard Path ($0.15/kBtu - penalties in 2025, 2027, 2030):")
        for year, details in analysis['standard_path']['penalties_by_year'].items():
            print(f"      {year}: ${details['penalty']:,.0f} (NPV: ${details['npv']:,.0f})")
        print(f"      Total Nominal: ${analysis['standard_path']['total_nominal']:,.0f}")
        print(f"      Total NPV: ${analysis['standard_path']['total_npv']:,.0f}")
        
        print(f"\n   Opt-in Path ($0.23/kBtu - penalties in 2028, 2032):")
        for year, details in analysis['optin_path']['penalties_by_year'].items():
            print(f"      {year}: ${details['penalty']:,.0f} (NPV: ${details['npv']:,.0f})")
        print(f"      Total Nominal: ${analysis['optin_path']['total_nominal']:,.0f}")
        print(f"      Total NPV: ${analysis['optin_path']['total_npv']:,.0f}")
        
        # Recommendation
        rec = analysis['recommendation']
        print(f"\n✅ RECOMMENDATION: {rec['recommendation'].upper()} PATH")
        print(f"   Confidence: {rec['confidence']}%")
        print(f"   Primary Reason: {rec['primary_reason']}")
        if rec['secondary_reasons']:
            print(f"   Additional Factors:")
            for reason in rec['secondary_reasons']:
                print(f"      - {reason}")
        
        print(f"\n   💵 NPV Analysis:")
        print(f"      Standard Path NPV: ${analysis['standard_path']['total_npv']:,.0f}")
        print(f"      Opt-in Path NPV: ${analysis['optin_path']['total_npv']:,.0f}")
        print(f"      NPV Advantage: ${rec['npv_advantage']:,.0f}")
        
        # Retrofit analysis
        retrofit = analysis['retrofit_analysis']
        print(f"\n🔧 Retrofit Requirements:")
        print(f"   Reduction Needed: {retrofit['reduction_pct']:.1f}%")
        print(f"   Retrofit Level: {retrofit['retrofit_level'].title()}")
        print(f"   Estimated Cost: ${retrofit['total_cost']:,.0f} (${retrofit['cost_per_sqft']:.0f}/sqft)")
        
        # Technical difficulty
        tech = analysis['technical_difficulty']
        print(f"\n📈 Technical Feasibility:")
        print(f"   Difficulty Score: {tech['score']:.0f}/100")
        print(f"   Assessment: {tech['feasibility'].replace('_', ' ').title()}")
        
        # Create visualizations
        print(f"\n📈 Generating enhanced visualizations...")
        fig = self.create_enhanced_visualizations()
        
        # Save figure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(self.data_dir, 'analysis', 
                                  f'building_{self.building_id}_enhanced_analysis_{timestamp}.png')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"   ✓ Saved to: {output_path}")
        
        # Save analysis JSON
        json_path = output_path.replace('.png', '.json')
        with open(json_path, 'w') as f:
            # Convert numpy types to native Python types for JSON serialization
            def convert_types(obj):
                if isinstance(obj, (np.bool_, bool)):
                    return bool(obj)
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_types(v) for v in obj]
                return obj
                
            json.dump(convert_types(analysis), f, indent=2)
        print(f"   ✓ Analysis data saved to: {json_path}")
        
        return analysis, fig


# Example usage
if __name__ == "__main__":
    # Analyze building 2952
    building_id = "2952"
    
    analyzer = EnhancedBuildingComplianceAnalyzer(building_id)
    analysis, fig = analyzer.generate_enhanced_report()
    
    if fig:
        plt.show()
