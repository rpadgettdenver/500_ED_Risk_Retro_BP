"""
Suggested File Name: building_compliance_analyzer_v2.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis/
Use: Enhanced building compliance analyzer with NPV, caps/floors, and sophisticated opt-in logic

This updated script:
1. Uses the unified penalty calculator for consistency
2. Implements NPV analysis with 7% discount rate
3. Applies 42% reduction cap and MAI floor
4. Provides sophisticated opt-in recommendations
5. Includes technical feasibility scoring
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

# Import the unified penalty calculator
try:
    from utils.penalty_calculator import PenaltyCalculator, calculate_building_penalties
except ImportError:
    print("Warning: Could not import penalty_calculator. Please ensure it's in src/utils/")
    # We'll define a minimal version inline if needed

class EnhancedBuildingComplianceAnalyzer:
    def __init__(self, building_id, data_dir='/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data'):
        """Initialize analyzer for a specific building"""
        self.building_id = str(building_id)
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, 'processed')
        self.raw_dir = os.path.join(data_dir, 'raw')
        
        # Initialize penalty calculator
        self.calc = PenaltyCalculator()
        
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
        
        # Load EUI targets
        self.df_targets = pd.read_csv(os.path.join(self.raw_dir, 'Building_EUI_Targets.csv'))
        self.df_targets['Building ID'] = self.df_targets['Building ID'].astype(str)
        
        # Get building-specific data
        self.building_current = self.df_current[self.df_current['Building ID'] == self.building_id]
        self.building_history = self.df_all_years[self.df_all_years['Building ID'] == self.building_id]
        self.building_targets = self.df_targets[self.df_targets['Building ID'] == self.building_id]
        
        if len(self.building_current) == 0:
            raise ValueError(f"Building {self.building_id} not found in current data")
        
        print(f"✓ Found data for Building {self.building_id}")
        print(f"  Property Type: {self.building_current.iloc[0]['Master Property Type']}")
        print(f"  Square Footage: {self.building_current.iloc[0]['Master Sq Ft']:,.0f}")
        
    def prepare_building_data(self):
        """Prepare building data for penalty calculations"""
        building = self.building_current.iloc[0]
        targets_row = self.building_targets.iloc[0] if len(self.building_targets) > 0 else None
        
        if targets_row is None:
            print("⚠️  No targets found for this building")
            return None
            
        # Extract key data
        current_eui = pd.to_numeric(building['Weather Normalized Site EUI'], errors='coerce')
        sqft = pd.to_numeric(building['Master Sq Ft'], errors='coerce')
        property_type = building['Master Property Type']
        year_built = pd.to_numeric(building.get('Year Built', 1990), errors='coerce')
        
        # Check if MAI building
        mai_types = ['Manufacturing/Industrial Plant', 'Data Center', 'Agricultural']
        is_mai = property_type in mai_types
        
        # Extract targets
        targets = {
            2025: targets_row.get('First Interim Target EUI', 0),
            2027: targets_row.get('Second Interim Target EUI', 0),
            2030: targets_row.get('Adjusted Final Target EUI', targets_row.get('Original Final Target EUI', 0))
        }
        
        # For opt-in path, use the same final target for 2028 and 2032
        targets[2028] = self.calculate_opt_in_interim_target(targets_row)
        targets[2032] = targets[2030]  # Same final target
        
        # Check for cash constraints (simplified logic)
        cash_constrained = property_type in ['Affordable Housing', 'Senior Care Community']
        
        return {
            'building_id': self.building_id,
            'building_name': building.get('Building Name', 'Unknown'),
            'current_eui': current_eui,
            'baseline_eui': targets_row.get('Baseline EUI', current_eui),
            'sqft': sqft,
            'property_type': property_type,
            'is_mai': is_mai,
            'targets': targets,
            'building_age': 2024 - year_built if not pd.isna(year_built) else 30,
            'cash_constrained': cash_constrained
        }
    
    def calculate_opt_in_interim_target(self, targets_row):
        """Calculate opt-in path interim target for 2028"""
        baseline_eui = targets_row.get('Baseline EUI', 0)
        final_target = targets_row.get('Adjusted Final Target EUI', 
                                     targets_row.get('Original Final Target EUI', 0))
        baseline_year = int(targets_row.get('Baseline Year', 2019))
        
        # Linear interpolation from baseline (2019) to final (2032)
        total_years = 2032 - baseline_year  # 13 years
        years_to_2028 = 2028 - baseline_year  # 9 years
        
        if total_years > 0:
            progress_ratio = years_to_2028 / total_years
            interim_target = baseline_eui - (baseline_eui - final_target) * progress_ratio
            return interim_target
        
        return final_target
    
    def calculate_enhanced_penalties(self):
        """Calculate penalties with NPV analysis and sophisticated logic"""
        
        # Prepare building data
        building_data = self.prepare_building_data()
        if building_data is None:
            return None
            
        # Use the unified calculator
        analysis = calculate_building_penalties(building_data, include_ongoing=False)
        
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
        # Same as original implementation
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
        original_targets = []
        adjusted_targets = []
        
        for year in years:
            if year in analysis['adjusted_targets']:
                adjusted_targets.append(analysis['adjusted_targets'][year])
                # We'd need to store original targets to show adjustment
                
        ax.plot(years, adjusted_targets, 'g^-', linewidth=2, markersize=10,
               label='Adjusted Targets')
        
        # Add 42% cap line
        baseline_eui = analysis.get('baseline_eui', analysis['current_eui'])
        cap_eui = baseline_eui * (1 - 0.42)
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
        
        # Standard path
        standard_years = [2019, 2025, 2027, 2030]
        standard_euis = [
            analysis.get('baseline_eui', current_eui),
            targets.get(2025, 0),
            targets.get(2027, 0),
            targets.get(2030, 0)
        ]
        
        # Opt-in path
        optin_years = [2019, 2028, 2032]
        optin_euis = [
            analysis.get('baseline_eui', current_eui),
            targets.get(2028, 0),
            targets.get(2032, 0)
        ]
        
        # Plot paths
        ax.plot(standard_years, standard_euis, 'b-o', linewidth=2, markersize=8,
               label='Standard Path ($0.15/kBtu)')
        ax.plot(optin_years, optin_euis, 'g-s', linewidth=2, markersize=8,
               label='Opt-in Path ($0.23/kBtu)')
        
        # Current EUI line
        ax.axhline(y=current_eui, color='red', linestyle='-', alpha=0.7,
                  label=f'Current EUI ({current_eui:.1f})')
        
        # Shade penalty zones
        ax.fill_between(standard_years, current_eui, standard_euis, 
                       where=[eui < current_eui for eui in standard_euis],
                       alpha=0.2, color='red', label='Penalty Zone')
        
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
        
        # Target adjustments
        print(f"\n🎯 Target Adjustments:")
        building_data = self.prepare_building_data()
        for year, original in building_data['targets'].items():
            adjusted = analysis['adjusted_targets'][year]
            if adjusted != original:
                print(f"   {year}: {original:.1f} → {adjusted:.1f} kBtu/ft² (adjusted)")
            else:
                print(f"   {year}: {adjusted:.1f} kBtu/ft²")
        
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
