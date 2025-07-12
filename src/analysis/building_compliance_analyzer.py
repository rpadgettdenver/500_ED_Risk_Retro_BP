"""
Suggested File Name: building_compliance_analyzer.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis/
Use: Analyze individual building compliance paths, calculate penalties, and generate visualizations

This script:
1. Analyzes a specific building's historical energy use
2. Calculates penalties for standard vs. opt-in compliance paths
3. Generates visualizations showing trends and targets
4. Considers electrification credits
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import json

class BuildingComplianceAnalyzer:
    def __init__(self, building_id, data_dir='/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/data'):
        """Initialize analyzer for a specific building"""
        self.building_id = str(building_id)
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, 'processed')
        self.raw_dir = os.path.join(data_dir, 'raw')
        
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
        
    def calculate_penalties(self):
        """Calculate penalties for both compliance paths"""
        
        # Get building details
        building = self.building_current.iloc[0]
        current_eui = pd.to_numeric(building['Weather Normalized Site EUI'], errors='coerce')
        sqft = pd.to_numeric(building['Master Sq Ft'], errors='coerce')
        
        # Get targets
        targets = self.building_targets.iloc[0] if len(self.building_targets) > 0 else None
        
        if targets is None:
            print("⚠️  No targets found for this building")
            return None
        
        # Standard compliance path (2025, 2027, 2030)
        standard_path = {
            '2025': {
                'target': targets.get('First Interim Target EUI', 0),
                'year': 2025,
                'penalty_rate': 0.15  # $0.15 per kBtu over target
            },
            '2027': {
                'target': targets.get('Second Interim Target EUI', 0),
                'year': 2027,
                'penalty_rate': 0.15  # $0.15 per kBtu over target
            },
            '2030': {
                'target': targets.get('Adjusted Final Target EUI', targets.get('Original Final Target EUI', 0)),
                'year': 2030,
                'penalty_rate': 0.15  # $0.15 per kBtu over target
            }
        }
        
        # Opt-in alternative path (2028, 2032)
        # Targets are typically less stringent for interim but same final
        opt_in_path = {
            '2028': {
                'target': self.calculate_opt_in_target(targets, 2028),
                'year': 2028,
                'penalty_rate': 0.15  # Same as 2027 rate
            },
            '2032': {
                'target': targets.get('Adjusted Final Target EUI', targets.get('Original Final Target EUI', 0)),
                'year': 2032,
                'penalty_rate': 0.15  # Same as 2030 rate
            }
        }
        
        # Calculate penalties
        penalties = {
            'standard_path': {},
            'opt_in_path': {},
            'current_eui': current_eui,
            'sqft': sqft
        }
        
        # Check if we have valid data
        if pd.isna(current_eui) or pd.isna(sqft):
            print("⚠️  Missing EUI or square footage data")
            return None
        
        # Standard path penalties
        for year, details in standard_path.items():
            if current_eui > details['target']:
                excess_eui = current_eui - details['target']
                penalty = excess_eui * sqft * details['penalty_rate']
                penalties['standard_path'][year] = {
                    'target_eui': details['target'],
                    'excess_eui': excess_eui,
                    'penalty': penalty
                }
            else:
                penalties['standard_path'][year] = {
                    'target_eui': details['target'],
                    'excess_eui': 0,
                    'penalty': 0
                }
        
        # Opt-in path penalties
        for year, details in opt_in_path.items():
            if current_eui > details['target']:
                excess_eui = current_eui - details['target']
                penalty = excess_eui * sqft * details['penalty_rate']
                penalties['opt_in_path'][year] = {
                    'target_eui': details['target'],
                    'excess_eui': excess_eui,
                    'penalty': penalty
                }
            else:
                penalties['opt_in_path'][year] = {
                    'target_eui': details['target'],
                    'excess_eui': 0,
                    'penalty': 0
                }
        
        # Calculate total penalties
        penalties['standard_total'] = sum(p['penalty'] for p in penalties['standard_path'].values())
        penalties['opt_in_total'] = sum(p['penalty'] for p in penalties['opt_in_path'].values())
        penalties['recommendation'] = 'Opt-in' if penalties['opt_in_total'] < penalties['standard_total'] else 'Standard'
        
        return penalties
    
    def calculate_opt_in_target(self, targets, year):
        """Calculate opt-in compliance targets based on linear interpolation"""
        baseline_eui = targets.get('Baseline EUI', 0)
        final_target = targets.get('Adjusted Final Target EUI', targets.get('Original Final Target EUI', 0))
        baseline_year = int(targets.get('Baseline Year', 2019))
        
        # Opt-in gives more time but linear reduction
        if year == 2028:
            # Linear interpolation from baseline to final (2032)
            years_total = 2032 - baseline_year
            years_to_interim = 2028 - baseline_year
            reduction_needed = baseline_eui - final_target
            interim_reduction = reduction_needed * (years_to_interim / years_total)
            return baseline_eui - interim_reduction
        
        return final_target
    
    def create_visualizations(self):
        """Create comprehensive visualizations for the building"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Building {self.building_id} - Compliance Analysis', fontsize=16)
        
        # Get building info for subtitle
        building = self.building_current.iloc[0]
        property_type = building['Master Property Type']
        building_name = building.get('Building Name', 'Unknown')
        
        fig.text(0.5, 0.94, f'{building_name} ({property_type})', ha='center', fontsize=12)
        
        # 1. Historical Energy Use and EUI
        self.plot_historical_energy(axes[0, 0])
        
        # 2. Weather Normalized EUI Trends
        self.plot_weather_normalized_trends(axes[0, 1])
        
        # 3. Compliance Pathways Comparison
        self.plot_compliance_pathways(axes[1, 0])
        
        # 4. Penalty Analysis
        self.plot_penalty_analysis(axes[1, 1])
        
        plt.tight_layout()
        return fig
    
    def plot_historical_energy(self, ax):
        """Plot historical energy use and EUI"""
        # Sort history by year
        history = self.building_history.sort_values('Reporting Year')
        
        # Convert to numeric
        history['Weather Normalized Site EUI'] = pd.to_numeric(history['Weather Normalized Site EUI'], errors='coerce')
        
        # Convert numeric columns
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
        
        # Color the y-axis labels
        ax.tick_params(axis='y', labelcolor='steelblue')
        ax2.tick_params(axis='y', labelcolor='darkred')
        
        # Grid
        ax.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
    def plot_weather_normalized_trends(self, ax):
        """Plot weather normalized EUI with trend lines"""
        history = self.building_history.sort_values('Reporting Year')
        
        # Convert to numeric first
        history['Weather Normalized Site EUI'] = pd.to_numeric(history['Weather Normalized Site EUI'], errors='coerce')
        
        # Filter out NaN values
        history_clean = history[history['Weather Normalized Site EUI'].notna()].copy()
        
        if len(history_clean) == 0:
            ax.text(0.5, 0.5, 'No weather normalized data available', ha='center', va='center')
            ax.set_title('Weather Normalized EUI Trends')
            return
        
        # Plot weather normalized EUI
        ax.plot(history_clean['Reporting Year'], 
               history_clean['Weather Normalized Site EUI'], 
               color='green', marker='o', linewidth=2, markersize=8,
               label='Weather Normalized EUI')
        
        # Add baseline year marker if available
        if len(self.building_targets) > 0:
            baseline_year = int(self.building_targets.iloc[0]['Baseline Year'])
            baseline_eui = self.building_targets.iloc[0]['Baseline EUI']
            ax.axhline(y=baseline_eui, color='red', linestyle='--', alpha=0.7, 
                      label=f'Baseline EUI ({baseline_year})')
        
        # Add trend line
        if len(history_clean) > 1:
            years = history_clean['Reporting Year'].values
            euis = history_clean['Weather Normalized Site EUI'].values
            
            # Fit polynomial
            z = np.polyfit(years, euis, 1)
            p = np.poly1d(z)
            ax.plot(years, p(years), "r--", alpha=0.7, label=f'Trend: {z[0]:.2f} kBtu/ft²/year')
        
        ax.set_xlabel('Year')
        ax.set_ylabel('Weather Normalized EUI (kBtu/ft²)')
        ax.set_title('Weather Normalized EUI Trends')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
    def plot_compliance_pathways(self, ax):
        """Plot standard vs opt-in compliance pathways"""
        if len(self.building_targets) == 0:
            ax.text(0.5, 0.5, 'No targets available', ha='center', va='center')
            return
        
        targets = self.building_targets.iloc[0]
        baseline_year = int(targets['Baseline Year'])
        baseline_eui = targets['Baseline EUI']
        
        # Years for projection
        years = range(baseline_year, 2033)
        
        # Standard path targets
        standard_years = [baseline_year, 2025, 2027, 2030]
        standard_euis = [
            baseline_eui,
            targets['First Interim Target EUI'],
            targets['Second Interim Target EUI'],
            targets.get('Adjusted Final Target EUI', targets['Original Final Target EUI'])
        ]
        
        # Opt-in path targets
        opt_in_years = [baseline_year, 2028, 2032]
        opt_in_euis = [
            baseline_eui,
            self.calculate_opt_in_target(targets, 2028),
            targets.get('Adjusted Final Target EUI', targets['Original Final Target EUI'])
        ]
        
        # Plot pathways
        ax.plot(standard_years, standard_euis, 'b-o', linewidth=2, markersize=8, 
               label='Standard Path (2025, 2027, 2030)')
        ax.plot(opt_in_years, opt_in_euis, 'g-s', linewidth=2, markersize=8,
               label='Opt-in Path (2028, 2032)')
        
        # Plot actual historical data
        history = self.building_history.sort_values('Reporting Year')
        history['Weather Normalized Site EUI'] = pd.to_numeric(history['Weather Normalized Site EUI'], errors='coerce')
        
        ax.scatter(history['Reporting Year'], 
                  history['Weather Normalized Site EUI'],
                  color='red', s=100, zorder=5, label='Actual Performance')
        
        # Add electrification credit scenarios (10% credit allows HIGHER EUI targets)
        # Standard path with electrification - multiply by 1.1 (10% higher allowed)
        standard_euis_elec = [eui * 1.1 for eui in standard_euis]
        ax.plot(standard_years, standard_euis_elec, 'b:', linewidth=2, markersize=6, alpha=0.7,
               label='Standard Path w/ Elec Credit')
        
        # Opt-in path with electrification - multiply by 1.1 (10% higher allowed)
        opt_in_euis_elec = [eui * 1.1 for eui in opt_in_euis]
        ax.plot(opt_in_years, opt_in_euis_elec, 'g:', linewidth=2, markersize=6, alpha=0.7,
               label='Opt-in Path w/ Elec Credit')
        
        ax.set_xlabel('Year')
        ax.set_ylabel('Weather Normalized EUI (kBtu/ft²)')
        ax.set_title('Compliance Pathways Comparison')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(baseline_year - 1, 2033)
        
    def plot_penalty_analysis(self, ax):
        """Plot penalty comparison between pathways"""
        penalties = self.calculate_penalties()
        
        if penalties is None:
            ax.text(0.5, 0.5, 'Cannot calculate penalties', ha='center', va='center')
            return
        
        # Create timeline with all years
        all_years = [2025, 2027, 2028, 2030, 2032]
        year_positions = {year: i for i, year in enumerate(all_years)}
        
        # Standard path data
        standard_years = [2025, 2027, 2030]
        standard_penalties = [penalties['standard_path'][str(year)]['penalty'] for year in standard_years]
        standard_positions = [year_positions[year] for year in standard_years]
        
        # Opt-in path data
        opt_in_years = [2028, 2032]
        opt_in_penalties = [penalties['opt_in_path'][str(year)]['penalty'] for year in opt_in_years]
        opt_in_positions = [year_positions[year] for year in opt_in_years]
        
        # Plot bars
        width = 0.6
        bars1 = ax.bar(standard_positions, standard_penalties, width, 
                       label='Standard Path', color='steelblue', alpha=0.8)
        bars2 = ax.bar(opt_in_positions, opt_in_penalties, width, 
                       label='Opt-in Path', color='lightgreen', alpha=0.8)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:,.0f}', ha='center', va='bottom')
        
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:,.0f}', ha='center', va='bottom')
        
        # Set x-axis
        ax.set_xticks(range(len(all_years)))
        ax.set_xticklabels(all_years)
        ax.set_xlabel('Compliance Year')
        ax.set_ylabel('Penalty Amount ($)')
        ax.set_title('Penalty Analysis by Compliance Path')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add recommendation text
        total_standard = penalties['standard_total']
        total_opt_in = penalties['opt_in_total']
        recommendation = penalties['recommendation']
        
        ax.text(0.02, 0.98, f'Total Standard Path: ${total_standard:,.0f}\n' + 
                           f'Total Opt-in Path: ${total_opt_in:,.0f}\n' +
                           f'Recommendation: {recommendation} Path',
               transform=ax.transAxes, fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
    def generate_report(self):
        """Generate a comprehensive report for the building"""
        print(f"\n📊 COMPLIANCE ANALYSIS REPORT - Building {self.building_id}")
        print("="*60)
        
        # Building details
        building = self.building_current.iloc[0]
        # Convert numeric columns to float
        numeric_cols = ['Weather Normalized Site EUI', 'Site EUI', 'Site Energy Use', 'Master Sq Ft']
        for col in numeric_cols:
            if col in building:
                try:
                    building[col] = pd.to_numeric(building[col], errors='coerce')
                except:
                    pass
        
        print(f"\n🏢 Building Details:")
        print(f"   Name: {building.get('Building Name', 'Unknown')}")
        print(f"   Type: {building['Master Property Type']}")
        print(f"   Size: {building['Master Sq Ft']:,.0f} sq ft")
        
        # Check if we have a valid EUI value
        if pd.notna(building['Weather Normalized Site EUI']):
            print(f"   Current Weather Normalized EUI: {float(building['Weather Normalized Site EUI']):.2f} kBtu/ft²")
        else:
            print(f"   Current Weather Normalized EUI: Not available")
        
        # Historical performance
        if 'EUI_Change_From_Baseline_Pct' in building and pd.notna(building['EUI_Change_From_Baseline_Pct']):
            print(f"   Change from Baseline: {building['EUI_Change_From_Baseline_Pct']:.2f}%")
        
        # Penalty analysis
        penalties = self.calculate_penalties()
        if penalties:
            print(f"\n💰 Penalty Analysis:")
            print(f"\n   Standard Path (2025, 2027, 2030):")
            for year, details in penalties['standard_path'].items():
                print(f"      {year}: ${details['penalty']:,.0f} " + 
                     f"(Target: {details['target_eui']:.1f}, Excess: {details['excess_eui']:.1f})")
            print(f"      TOTAL: ${penalties['standard_total']:,.0f}")
            
            print(f"\n   Opt-in Path (2028, 2032):")
            for year, details in penalties['opt_in_path'].items():
                print(f"      {year}: ${details['penalty']:,.0f} " +
                     f"(Target: {details['target_eui']:.1f}, Excess: {details['excess_eui']:.1f})")
            print(f"      TOTAL: ${penalties['opt_in_total']:,.0f}")
            
            print(f"\n   ✅ RECOMMENDATION: {penalties['recommendation']} Path")
            
            savings = abs(penalties['standard_total'] - penalties['opt_in_total'])
            print(f"   💵 Potential Savings: ${savings:,.0f}")
        
        # Create visualizations
        print(f"\n📈 Generating visualizations...")
        fig = self.create_visualizations()
        
        # Save figure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(self.data_dir, 'analysis', f'building_{self.building_id}_analysis_{timestamp}.png')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"   ✓ Saved to: {output_path}")
        
        return penalties, fig


# Example usage
if __name__ == "__main__":
    # Analyze building 2952
    building_id = "2952"
    
    analyzer = BuildingComplianceAnalyzer(building_id)
    penalties, fig = analyzer.generate_report()
    
    plt.show()
