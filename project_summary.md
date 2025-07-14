# 🧠 Project Summary
_Base directory: `500_ED_Risk_Retro_BP`_

## 📂 src

### 📄 `src/__init__.py`
```

```

### 📄 `src/analysis/building_compliance_analyzer_v2.py`
```
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
"""

import pandas as pd

... (truncated)
```

### 📄 `src/analysis/integrated_tes_hp_analyzer.py`
```
"""
Suggested File Name: integrated_tes_hp_analyzer.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analysis/
Use: Comprehensive analysis tool that integrates HVAC system modeling, cash flow analysis, and business case generation

This tool combines:
1. HVAC system impact modeling (EUI reduction scenarios)
2. Cash flow bridge analysis (month-by-month funding)
3. Bridge loan structuring
4. Developer returns analysis
5. Executive summary generation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import sys

... (truncated)
```

### 📄 `src/config/__init__.py`
```
# Make config module importable
from .project_config import ProjectConfig, get_config, update_config, reset_config

__all__ = ['ProjectConfig', 'get_config', 'update_config', 'reset_config']
```

### 📄 `src/config/project_config.py`
```
"""
Suggested File Name: project_config.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/config/
Use: Centralized configuration for all TES+HP analysis modules to ensure consistency

This module provides a single source of truth for project parameters
"""

import json
import pandas as pd
from typing import Dict, Any
from datetime import datetime

class ProjectConfig:
    """Unified configuration for TES+HP project analysis"""
    
    # Default configuration values with documentation
    DEFAULT_CONFIG = {
        'building': {
            'building_id': '2952',

... (truncated)
```

### 📄 `src/data_processing/enhanced_comprehensive_loader.py`
```
"""
Suggested File Name: enhanced_comprehensive_loader.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/data_processing/
Use: Enhanced loader that creates comprehensive dataset with all buildings reporting after 2021

This script:
1. Timestamps all output files
2. Includes ALL buildings that reported after 2021 (post-COVID)
3. Uses most recent data for each building
4. Tracks when each building last reported
5. Maximizes building coverage while using best available data
6. Calculates trends from baseline years using Building_EUI_Targets.csv
7. Formats numeric columns as float for Excel compatibility
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

... (truncated)
```

### 📄 `src/data_processing/__init__.py`
```

```

### 📄 `src/data_processing/comprehensive_energy_loader.py`
```
"""
Suggested File Name: comprehensive_energy_loader.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/data_processing/
Use: Load all energy data from Energize Denver Report with proper handling of multiple years

This script:
1. Uses 'Building ID' as the unique key
2. Loads ALL years of data to track energy trends
3. Identifies most recent reporting year for current status
4. Preserves all energy columns including Weather Normalized data
5. Includes GHG emissions data
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

def examine_excel_structure(excel_path):

... (truncated)
```

### 📄 `src/data_processing/comprehensive_data_merger.py`
```
"""
Suggested File Name: comprehensive_data_merger.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/data_processing/
Use: Merge all raw data sources to create comprehensive building dataset for DER analysis

This script:
1. Uses Energize Denver Report as the base (source of truth)
2. Joins geocoded data for lat/lon
3. Joins EPB status data
4. Joins zip codes
5. Joins EUI targets
6. Creates a master dataset with all building information
"""

import pandas as pd
import numpy as np
import os
import json

def load_and_examine_data(data_dir):

... (truncated)
```

### 📄 `src/utils/snapshot_handoff.py`
```
"""
📄 snapshot_handoff.py

Utility script to archive the current Claude session handoff (handoff_latest.md)
into a timestamped file for tracking and versioning.

Run this manually after significant updates or at the end of a working session.

Usage:
    python src/utils/snapshot_handoff.py

Output:
    Creates a file like:
    docs/handoffs/claude_handoff_20250713_1045.md
"""

from datetime import datetime
from pathlib import Path
import shutil

... (truncated)
```

### 📄 `src/utils/eui_target_loader.py`
```
#!/usr/bin/env python3
"""
Suggested file name: eui_target_loader.py
Directory Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
USE: Unified module for loading EUI targets with proper priority logic

This module provides a single source of truth for EUI target loading:
1. Loads targets from Building_EUI_Targets.csv
2. Checks MAI designation from MAITargetSummary.csv
3. Applies MAI logic: MAX(CSV target, 30% reduction, 52.9 floor)
4. Applies standard caps and floors
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

# Set up logging

... (truncated)
```

### 📄 `src/utils/__init__.py`
```

```

### 📄 `src/utils/mai_data_loader.py`
```
"""
Suggested File Name: mai_data_loader.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Load and process MAI designation and target data for Energize Denver compliance

This module handles loading MAI (Manufacturing/Agricultural/Industrial) building
designations and their specific targets from the official CSV files.
"""

import pandas as pd
import os
from typing import Dict, Tuple, Optional
from pathlib import Path


class MAIDataLoader:
    """Load and process MAI designation and target data"""
    
    def __init__(self, data_dir: str = None):
        """Initialize MAI data loader

... (truncated)
```

### 📄 `src/utils/penalty_calculator.py`
```
"""
Suggested File Name: penalty_calculator.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Single source of truth for all Energize Denver penalty calculations

This module implements the definitive penalty calculation logic as specified in
the Energize Denver Penalty Calculations - Definitive Source of Truth document.
All scripts should use this module for penalty calculations to ensure consistency.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PenaltyConfig:
    """Configuration for penalty calculations"""

... (truncated)
```

### 📄 `src/utils/local_gcp_bridge.py`
```
"""
Suggested File Name: local_gcp_bridge.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/utils/
Use: Bridge script to work with GCP data locally for development and testing

This script allows you to:
1. Pull data from BigQuery for local analysis
2. Test new algorithms locally before deploying to GCP
3. Create local visualizations and reports
"""

import os
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import numpy as np
from datetime import datetime
import json

class LocalGCPBridge:

... (truncated)
```

### 📄 `src/models/bridge_loan_investor_package.py`
```
"""
Suggested File Name: bridge_loan_investor_package.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/models/
Use: Generate professional bridge loan investor packages for TES+HP projects

This module creates:
- Executive summary for bridge lenders
- Security analysis and coverage ratios
- Cash flow waterfalls showing repayment
- Risk mitigation strategies
- Professional PDF output
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as patches

... (truncated)
```

### 📄 `src/models/hvac_system_impact_modeler.py`
```
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



... (truncated)
```

### 📄 `src/models/__init__.py`
```

```

### 📄 `src/models/tes_hp_cash_flow_bridge.py`
```
"""
Suggested File Name: tes_hp_cash_flow_bridge.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/models/
Use: Detailed month-by-month cash flow analysis for TES+HP projects from development through stabilization

This module creates detailed cash flow bridges showing:
- Pre-construction development costs
- Construction period funding needs
- Bridge loan requirements and timing
- Incentive/rebate receipt timing
- Stabilized operations cash flows
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns


... (truncated)
```

### 📄 `src/models/financial_model_bigquery.py`
```
"""
Suggested File Name: financial_model_bigquery.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/models/
Use: Calculate retrofit costs, available incentives, and ROI for building decarbonization
     projects including ITC, Clean Heat Plan, and utility rebates

This script:
1. Estimates retrofit costs based on building type and EUI reduction needed
2. Calculates Section 48 ITC eligibility (30% base + bonuses)
3. Models Clean Heat Plan rebates for heat pumps
4. Computes payback periods and NPV
5. Prioritizes projects by financial return and social impact (EPB status)
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration

... (truncated)
```

### 📄 `src/gcp/export_high_value_buildings_enhanced_v3_fixed.py`
```
"""
Suggested File Name: export_high_value_buildings_enhanced_v3_fixed.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Enhanced export with EPB data integration and EUI targets for business development

This script identifies and exports buildings that are:
1. High penalty exposure (need immediate solutions)
2. Can't meet targets (desperate for help)
3. Good candidates for 4-pipe WSHP + TES systems
4. Prioritizes EPB buildings for funding opportunities

Version 3 Fixed:
- Fixed property_type_clean error
- Uses Building_EUI_Targets.csv as primary source for all EUI targets
- Falls back to EPB file for buildings not in targets file
- Works with actual BigQuery schema
"""

from google.cloud import bigquery
import pandas as pd

... (truncated)
```

### 📄 `src/gcp/load_data_and_calculate.py`
```
"""
BigQuery Data Loader and Penalty Calculator for Energize Denver - FIXED V2
===========================================================================
This version correctly handles the actual table schemas

Usage:
    python src/gcp/load_data_and_calculate.py
"""

import os
from google.cloud import bigquery
from google.cloud import storage
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"
BUCKET_NAME = "energize-denver-eaas-data"

... (truncated)
```

### 📄 `src/gcp/__init__.py`
```

```

### 📄 `src/gcp/rerun_and_compare_analysis.py`
```
"""
Suggested File Name: rerun_and_compare_analysis.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Re-run BigQuery opt-in analysis and compare with previous results

This script:
1. Captures current analysis results (if any)
2. Re-runs the opt-in decision model
3. Compares before/after results
4. Validates specific buildings (like 2952)
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import os

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

... (truncated)
```

### 📄 `src/gcp/fix_bigquery_penalty_rates.py`
```
"""
Suggested File Name: fix_bigquery_penalty_rates.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Update BigQuery scripts to use correct penalty rates

This script updates the opt-in decision model in BigQuery to use:
- $0.15/kBtu for standard path
- $0.23/kBtu for opt-in path (not $0.15)
"""

import os
import re

def fix_bigquery_opt_in_model():
    """Fix the penalty rates in create_opt_in_decision_model.py"""
    
    file_path = "/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/create_opt_in_decision_model.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")

... (truncated)
```

### 📄 `src/gcp/gcp_migration_setup.py`
```
"""
Energize Denver Risk & Retrofit Platform - Google Cloud Migration Script

Suggested filename: gcp_migration_setup.py
Directory location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/
USE: This script helps migrate your Energize Denver project to Google Cloud Platform
     for enhanced data processing, collaboration, and scalability.

Requirements:
    pip install google-cloud-storage google-cloud-bigquery pandas numpy
"""

import os
import pandas as pd
from google.cloud import storage
from google.cloud import bigquery
from datetime import datetime
import json

class EnergizeDenverGCPMigration:

... (truncated)
```

### 📄 `src/gcp/create_opt_in_decision_model.py`
```
"""
Suggested File Name: create_opt_in_decision_model.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Create a sophisticated model to predict which buildings will opt-in to the ACO path

This script implements decision logic based on:
1. Financial analysis (NPV of penalties vs retrofit costs)
2. Technical feasibility (how hard is it to meet targets)
3. Building characteristics (age, type, current performance)
4. Strategic considerations (time value, cash flow)
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"


... (truncated)
```

### 📄 `src/gcp/create_penalty_analysis_corrected.py`
```
"""
Suggested File Name: create_penalty_analysis_corrected.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Create corrected penalty analysis following the April 2025 Technical Guidance rules

This script implements the correct penalty structure:
- $0.15/kBtu for default path (fines in 2025, 2027, 2030 = 3 years)
- $0.23/kBtu for opt-in path (fines in 2028, 2032 = 2 years)
- Handles MAI buildings separately
- Uses weather-normalized EUI
- Deduplicates buildings (latest year only)
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

... (truncated)
```

### 📄 `src/gcp/create_penalty_view_fixed.py`
```
"""
Suggested File Name: create_penalty_view_fixed.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Create the penalty analysis view using only the most recent year's consumption data
     and weather normalized EUI values

This script:
1. First explores the consumption data structure to understand the year column
2. Creates a view using only the latest year per building
3. Uses weather normalized EUI for more accurate comparisons
"""

from google.cloud import bigquery

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

def explore_consumption_data():
    """First, let's understand the data structure better"""

... (truncated)
```

### 📄 `src/gcp/load_excel_consumption_data.py`
```
"""
Suggested File Name: load_excel_consumption_data.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Load and explore the Excel file containing actual building consumption data,
     then upload to BigQuery for penalty calculations

This script:
1. Reads the Excel file and explores all sheets
2. Identifies actual consumption data columns
3. Cleans and standardizes the data
4. Uploads to BigQuery as a new table
5. Creates an enhanced analysis view with actual vs target EUI
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.cloud import storage
import os
from datetime import datetime

... (truncated)
```

### 📄 `src/gcp/load_geographic_data.py`
```
"""
Suggested File Name: load_geographic_data.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Load and merge geographic data (lat/lon and zip codes) with BigQuery analysis data

This script:
1. Loads geocoded building data from local CSV files
2. Uploads to BigQuery for joining with analysis data
3. Creates a comprehensive view with all geographic info
"""

import pandas as pd
from google.cloud import bigquery
import os

def load_geographic_data_to_bigquery(project_id='energize-denver-eaas', 
                                   dataset_id='energize_denver'):
    """
    Load geographic data from local CSV files and upload to BigQuery
    

... (truncated)
```

### 📄 `src/gcp/fix_42_cap_and_yearwise_exemptions.py`
```
"""
Suggested File Name: fix_42_cap_and_yearwise_exemptions.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/gcp/
Use: Fix buildings showing 100% reduction by applying 42% cap and handle year-specific exemptions

This script:
1. Applies the 42% maximum reduction cap properly
2. Only excludes building data for the specific year it was marked exempt
3. Handles edge cases where targets might be unrealistic
4. Maintains historical exemption records for transparency
"""

from google.cloud import bigquery
import pandas as pd

# Configuration
PROJECT_ID = "energize-denver-eaas"
DATASET_ID = "energize_denver"

class FixCapAndExemptions:

... (truncated)
```

### 📄 `src/api/__init__.py`
```

```

### 📄 `src/analytics/visualize_epb_clusters.py`
```
"""
Suggested File Name: visualize_epb_clusters.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Create visualizations and analysis of EPB DER clusters

This script creates:
1. Summary tables of top opportunities
2. Charts showing EPB distribution
3. Economic analysis visualizations
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

def load_cluster_data(output_dir):
    """Load the cluster analysis results"""
    # Load main cluster data

... (truncated)
```

### 📄 `src/analytics/__init__.py`
```

```

### 📄 `src/analytics/integrate_epb_data.py`
```
"""
Suggested File Name: integrate_epb_data.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Integrate EPB (Equity Priority Building) data with DER clustering analysis

This script:
1. Loads EPB data from the CSV file
2. Creates EPB lookup based on Building ID
3. Updates the DER clustering analysis to include EPB status
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.local_gcp_bridge import LocalGCPBridge
from analytics.der_clustering_analysis import DERClusterAnalyzer
import pandas as pd
import numpy as np
import json

... (truncated)
```

### 📄 `src/analytics/cluster_analysis_bigquery.py`
```
"""
Suggested File Name: cluster_analysis_bigquery.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Identify clusters of buildings that could share thermal infrastructure (ambient loops,
     heat recovery, thermal storage) using BigQuery's geospatial functions

This script:
1. Uses BigQuery's ST_DISTANCE to find nearby buildings
2. Identifies high-value clusters based on penalty exposure and building types
3. Finds opportunities for waste heat recovery (e.g., data centers + offices)
4. Prioritizes Equity Priority Buildings (EPBs) in cluster formation
5. Exports results as GeoJSON for visualization
"""

from google.cloud import bigquery
import pandas as pd
import json
from datetime import datetime

# Configuration

... (truncated)
```

### 📄 `src/analytics/run_der_clustering.py`
```
"""
Suggested File Name: run_der_clustering.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Run DER clustering analysis on Denver buildings using actual geographic data

This script:
1. Loads building data with geographic coordinates from BigQuery
2. Runs the DER clustering analysis
3. Exports results and creates visualizations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.local_gcp_bridge import LocalGCPBridge
from analytics.der_clustering_analysis import DERClusterAnalyzer
import pandas as pd
import json


... (truncated)
```

### 📄 `src/analytics/fixed_enhanced_der_clustering.py`
```
"""
Suggested File Name: fixed_enhanced_der_clustering.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Fixed version of enhanced DER clustering with correct column names and calculations

This script fixes:
1. Building name column mapping
2. Address handling (if not available, use building_id + zip)
3. Thermal load calculations using actual EUI data
4. Thermal diversity score calculation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.local_gcp_bridge import LocalGCPBridge
from analytics.der_clustering_analysis import DERClusterAnalyzer, BuildingProfile
import pandas as pd
import numpy as np

... (truncated)
```

### 📄 `src/analytics/der_clustering_analysis.py`
```
"""
Suggested File Name: der_clustering_analysis.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/src/analytics/
Use: Identify building clusters for shared District Energy Resource (DER) opportunities

This module:
1. Uses geospatial data to find nearby buildings
2. Analyzes thermal load profiles for compatibility
3. Identifies anchor loads (data centers, hospitals)
4. Calculates economic potential of thermal sharing
5. Prioritizes Equity Priority Buildings (EPBs)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from dataclasses import dataclass
from collections import defaultdict
import math

... (truncated)
```
## 📂 scripts

### 📄 `scripts/generate_json_from_handoff.py`
```
#!/usr/bin/env python3
"""
📄 generate_json_from_handoff.py

Reads the current handoff_latest.md file and generates a JSON summary
for use with ChatGPT or Claude.

Usage:
    python scripts/generate_json_from_handoff.py

Output:
    outputs/handoff_latest.json
"""

from pathlib import Path
import json
import re

# Define paths
base_dir = Path(__file__).resolve().parent.parent

... (truncated)
```

### 📄 `scripts/analyze_project.py`
```
#!/usr/bin/env python3
"""
📁 analyze_project.py
Walks your project directory, builds a Markdown summary of file structure and key file content,
and (optionally) sends it to GPT-4 via OpenAI API for suggestions.

Output:
    project_summary.md
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load OpenAI API key from environment or .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "project_summary.md"

... (truncated)
```
## 📂 docs

### 📄 `docs/EUI_Calculations_Summary.md`
```
# Energize Denver Comprehensive Data Calculations Summary

## Overview
This document explains how each calculated field in the `energize_denver_comprehensive_latest.csv` dataset is computed.

---

## 📊 Calculated Fields Explained

### 1. **Average_EUI_Recent** (Float, 2 decimals)
**What it represents:** The average Energy Use Intensity over the most recent reporting period

**Calculation:**
- Takes the last **3 years** of available data (or 2 years if only 2 available)
- Uses **Weather Normalized Site EUI** values
- Computes simple arithmetic mean: `(Year1_EUI + Year2_EUI + Year3_EUI) / Number_of_Years`

**Example:**
```
Building reports: 2021 (EUI=80.5), 2022 (EUI=75.3), 2023 (EUI=70.1)

... (truncated)
```

### 📄 `docs/Improvement_Analysis.md`
```
# Analysis: Why Are So Many Buildings Improving from Baseline?

## 📊 Key Finding
A surprisingly high percentage of buildings show improvement from their baseline year. This is actually **good news** for Denver's climate goals!

## 🔍 Likely Reasons for Widespread Improvement

### 1. **COVID-19 Impact Recovery**
- Many buildings had artificially low occupancy in 2020-2021
- As occupancy returned to normal, building operators optimized operations
- "Return to office" included modernized HVAC and controls

### 2. **Energize Denver Program Effect**
- Program launched in 2019 with clear targets
- Building owners had 4-5 years to prepare for penalties
- Proactive investments in efficiency to avoid future fines

### 3. **Energy Price Signals**
- Rising natural gas and electricity costs (2021-2023)
- Strong financial incentive to reduce consumption

... (truncated)
```

### 📄 `docs/bigquery_penalty_update_summary.md`
```
# BigQuery Penalty Rate Update Summary

## Files to Update:

### 1. create_opt_in_decision_model.py
- **Issue**: Uses $0.15/kBtu for BOTH standard and opt-in paths in calculations
- **Fix**: Update opt-in calculations to use $0.23/kBtu (PENALTY_RATE_OPTIN)
- **Impact**: Opt-in decisions will change significantly

### 2. create_penalty_analysis_corrected.py  
- **Status**: Already has correct rates defined
- **Verify**: Calculations use the correct variables

## SQL Query Updates Needed:

Replace in financial_analysis CTE:
```sql
-- OLD (WRONG):
GREATEST(0, mai_gap_2030 * gross_floor_area * 0.15) as penalty_2028_optin

... (truncated)
```

### 📄 `docs/energize_denver_penalty_summary.md`
```
# Energize Denver Performance Penalty Summary (April 2025 Guidance)

Penalty rates depend on how many performance target years a building has, and whether it maintains compliance. These rates supersede earlier drafts that mentioned $0.30/kBtu.

---

## 📊 Table: Performance Penalty Rates

| Compliance Scenario                                                                     | Penalty Rate     | Assessment                                                    |
|-----------------------------------------------------------------------------------------|------------------|---------------------------------------------------------------|
| 3 Target Years (2024, 2027, 2030), failed maintenance (>5%), or new buildings           | **$0.15 / kBtu** | In target years, then **annually** if noncompliant post-2030  |
| 2 Target Years (2026/2030 or ACO: 2028/2032)                                            | **$0.23 / kBtu** | At each milestone, then **annually** if still noncompliant    |
| 1 Target Year (timeline extension to 2030 or 2032)                                      | **$0.35 / kBtu** | At final year, then **annually** if still noncompliant        |
| Late Timeline Extension (submitted **after** target year ends)                         | **+ $0.10 / kBtu** | Add-on to one of the above rates                             |
| Never Benchmarking (or only pre-2019 data like 2017/2018)                              | **$10 / sq ft**  | One-time penalty, then **annually** if still noncompliant     |

---

## 🔁 Maintenance Clause


... (truncated)
```

### 📄 `docs/penalty_math_explained_v2.md`
```
# Energize Denver Penalty Math Explained
## A Plain English Guide to Our Calculations (Updated December 2024)

### Table of Contents
1. [Basic Penalty Formula](#basic-penalty-formula)
2. [The Two Compliance Paths](#the-two-compliance-paths)
3. [Target Years and Reporting Timeline](#target-years-and-reporting-timeline)
4. [EUI Reduction Caps and Floors](#eui-reduction-caps-and-floors)
5. [NPV Analysis for Opt-In Decisions](#npv-analysis)
6. [Real-World Examples](#real-world-examples)
7. [Key Assumptions](#key-assumptions)

---

## 1. Basic Penalty Formula

The fundamental penalty calculation is straightforward:

**Annual Penalty = EUI Gap × Building Size × Penalty Rate**


... (truncated)
```

### 📄 `docs/penalty_calculation_source_of_truth.md`
```
# Energize Denver Penalty Calculations - Definitive Source of Truth
**Version:** 1.0  
**Date:** July 13, 2025  
**Purpose:** Single authoritative reference for all penalty calculations

---

## 1. Core Penalty Rates

| Compliance Path | Penalty Rate | Target Years | Assessment Schedule |
|-----------------|--------------|--------------|---------------------|
| **Standard Path** (3 targets) | $0.15/kBtu | 2025*, 2027, 2030 | 2026, 2028, 2031, then annually |
| **Alternate Compliance (ACO)** (2 targets) | $0.23/kBtu | 2028, 2032 | 2029, 2033, then annually |
| **Timeline Extension** (1 target) | $0.35/kBtu | 2030 or 2032 | Following year, then annually |
| **Late Timeline Extension** | Base + $0.10/kBtu | Per extension terms | Following year, then annually |
| **Never Benchmarked** | $10.00/sqft | 2025, 2027, 2030 | 2026, 2028, 2031, then annually |

*Or as specified in Building_EUI_Targets.csv "First Interim Target Year" column

---

... (truncated)
```

### 📄 `docs/penalty_rate_update_log.md`
```
# Penalty Rate Update Documentation

## Date: 2025-07-12

## Summary of Changes

Updated all penalty calculations throughout the codebase to match the April 2025 Energize Denver Technical Guidance.

### Correct Penalty Rates (per Technical Guidance)

| Compliance Path | Penalty Rate | Target Years | Annual After Final Target |
|-----------------|--------------|--------------|--------------------------|
| Standard Path (3 targets) | $0.15/kBtu | 2025, 2027, 2030 | Yes, annually after 2030 |
| Alternate/Opt-in Path (2 targets) | $0.23/kBtu | 2028, 2032 | Yes, annually after 2032 |
| Timeline Extension (1 target) | $0.35/kBtu | 2030 or 2032 | Yes, annually thereafter |
| Late Extension | +$0.10/kBtu | (add to base rate) | Same as base path |
| Never Benchmarking | $10/sqft | One-time | Then annual penalties |

### Previous Incorrect Rates (NOW FIXED)


... (truncated)
```

### 📄 `docs/Finanacial Models/tes_hvac_financial_model.md`
```
# Thermal Energy Storage + Heat Pump Financial Model Framework
## Building-Level Energy-as-a-Service Business Plan

**Date:** July 10, 2025  
**Prepared for:** Robert Padgett, Energize Denver Risk & Retrofit Strategy Platform  
**Purpose:** Technical/Financial Framework for DRCOG Presentation & Investor Materials

---

## Executive Summary

This framework outlines a revolutionary Energy-as-a-Service (EaaS) model that leverages Thermal Energy Storage (TES) and heat pump technology to transform Denver's building decarbonization landscape. By combining federal tax incentives, state/local rebates, and innovative financing structures, this model delivers:

- **Zero to minimal** first cost for building owners
- **Cash flow neutral or positive** from day one
- **100% BPS compliance** guarantee
- **20-30% IRR** for development capital with near-zero initial investment
- **8-12% returns** for long-term investors
- **1.5-2.5 million MTCO2e** lifetime emissions reduction across portfolio


... (truncated)
```

### 📄 `docs/handoffs/claude_handoff_20250713_1118.md`
```
# 🤝 Claude Session Handoff – January 13, 2025, 16:45 MDT

## 🧠 Session Summary
Today we completed a major project cleanup and began implementing the unified EUI target loader system. This session focused on organizing the codebase, fixing import issues, and creating foundational modules for consistent penalty and target calculations.

## ✅ Work Completed

### 1. Project Structure Cleanup ✅
- **Archived 30+ outdated files** into organized directories
- Removed duplicate versions (e.g., 5 versions of export_high_value_buildings)
- Moved test scripts from src/ to appropriate locations
- Created timestamp-based archive: `archive/cleanup_[timestamp]/`
- **📝 Result:** Clean, navigable project structure with only active modules

### 2. Fixed Import Issues ✅
- Created and ran `check_imports.py` to find broken imports
- Fixed 2 import issues:
  - `run_unified_analysis_v2.py`: Updated to use building_compliance_analyzer_v2
  - `fixed_enhanced_der_clustering.py`: Removed self-import, added missing functions
- Fixed hardcoded penalty rates in `hvac_system_impact_modeler.py`

... (truncated)
```

### 📄 `docs/handoffs/handoff_latest.md`
```
# 🤝 Claude Session Handoff – January 13, 2025, 16:45 MDT

## 🧠 Session Summary
Today we completed a major project cleanup and began implementing the unified EUI target loader system. This session focused on organizing the codebase, fixing import issues, and creating foundational modules for consistent penalty and target calculations.

## ✅ Work Completed

### 1. Project Structure Cleanup ✅
- **Archived 30+ outdated files** into organized directories
- Removed duplicate versions (e.g., 5 versions of export_high_value_buildings)
- Moved test scripts from src/ to appropriate locations
- Created timestamp-based archive: `archive/cleanup_[timestamp]/`
- **📝 Result:** Clean, navigable project structure with only active modules

### 2. Fixed Import Issues ✅
- Created and ran `check_imports.py` to find broken imports
- Fixed 2 import issues:
  - `run_unified_analysis_v2.py`: Updated to use building_compliance_analyzer_v2
  - `fixed_enhanced_der_clustering.py`: Removed self-import, added missing functions
- Fixed hardcoded penalty rates in `hvac_system_impact_modeler.py`

... (truncated)
```

### 📄 `docs/handoffs/handoff_prompt.md`
```
# TES+HP Energy-as-a-Service Business Model - Project Handoff (Major Update)

## 🎯 Current Project Status

### Project Overview
Developing a **Thermal Energy Storage (TES) + Heat Pump Energy-as-a-Service** business model for multifamily and commercial buildings in Denver subject to Energize Denver Building Performance Standards. This session has created a complete analysis framework with unified configuration management.

**Project Location:** `/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/`

## 🏗️ What We've Built in This Session

### 1. **Unified Configuration System** ✅
Created `src/config/project_config.py` that provides:
- **Single source of truth** for all project assumptions
- **Easy modification** of any parameter in one place
- **Automatic calculation** of derived values
- **Save/load configurations** to JSON for scenario management
- **Print assumptions table** showing all parameters with their locations

Key features:

... (truncated)
```

### 📄 `docs/handoffs/claude_handoff_20250713_1042.md`
```
# 🤝 Claude Session Handoff – January 13, 2025, 16:45 MDT

## 🧠 Session Summary
Today we completed a major project cleanup and began implementing the unified EUI target loader system. This session focused on organizing the codebase, fixing import issues, and creating foundational modules for consistent penalty and target calculations.

## ✅ Work Completed

### 1. Project Structure Cleanup ✅
- **Archived 30+ outdated files** into organized directories
- Removed duplicate versions (e.g., 5 versions of export_high_value_buildings)
- Moved test scripts from src/ to appropriate locations
- Created timestamp-based archive: `archive/cleanup_[timestamp]/`
- **📝 Result:** Clean, navigable project structure with only active modules

### 2. Fixed Import Issues ✅
- Created and ran `check_imports.py` to find broken imports
- Fixed 2 import issues:
  - `run_unified_analysis_v2.py`: Updated to use building_compliance_analyzer_v2
  - `fixed_enhanced_der_clustering.py`: Removed self-import, added missing functions
- Fixed hardcoded penalty rates in `hvac_system_impact_modeler.py`

... (truncated)
```

### 📄 `docs/handoffs/claude_handoff_20250713.md`
```
# Claude Conversation Handoff - July 13, 2025

## Summary of Work Completed

### 1. Fixed BigQuery Export Script (V3)
- **Issue**: `property_type_clean` column didn't exist in `opt_in_decision_analysis` view
- **Solution**: Removed reference to non-existent column, script now runs successfully
- **File**: `export_high_value_buildings_enhanced_v3_fixed.py`

### 2. Created Penalty Calculation Source of Truth
- **Created**: Definitive penalty calculation documentation
- **Key Rates**: 
  - Standard Path: $0.15/kBtu
  - ACO/Opt-in Path: $0.23/kBtu
  - Extension: $0.35/kBtu
- **File**: `penalty_calculation_source_of_truth.md`

### 3. Created Penalty Calculator Module
- **Purpose**: Single source of truth for all penalty calculations
- **Features**: NPV analysis, path comparison, caps/floors

... (truncated)
```

### 📄 `docs/handoffs/claude_handoff_20250113_1045.md`
```
# Claude Session Handoff - January 13, 2025, 10:45 MST

## Session Summary
Successfully debugged and fixed the EUI Target Loader module. Corrected column mapping issues and clarified Building 2952 data discrepancy from previous handoff.

## Work Completed Today

### 1. Fixed EUI Target Loader Module ✅
- **Issue**: Module was looking for wrong column names in Building_EUI_Targets.csv
- **Fixed column mappings**:
  - `Baseline EUI` (was looking for "Baseline Weather Normalized Site EUI")
  - `First Interim Target EUI` (was looking for "2025 1st Interim Target Site EUI")
  - `Second Interim Target EUI` (was looking for "2027 2nd Interim Target Site EUI")
  - `Adjusted Final Target EUI` (was looking for "2030 Final Target Site EUI")
- **Result**: Module now correctly loads all building targets

### 2. Clarified Building 2952 Data ✅
- Previous handoff incorrectly stated all targets were 69.0
- **Actual Building 2952 targets**:
  - Baseline EUI: 69.0

... (truncated)
```

### 📄 `docs/handoffs/project_handoff(rev1).md`
```
# Energize Denver Risk & Retrofit Platform - Project Handoff
**Date:** July 7, 2025  
**Prepared by:** Robert Padgett & Claude  
**Project Location:** `/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP`

---

## 📋 Executive Summary

The Energize Denver Risk & Retrofit Platform has successfully migrated to Google Cloud Platform (GCP) and now provides sophisticated analytics for building compliance under Denver's Building Performance Standards (BPS). The platform analyzes 3,000+ buildings, calculates penalty exposure, and recommends optimal compliance pathways using financial modeling and technical feasibility assessments.

### Key Achievements:
- ✅ Migrated entire data pipeline to Google Cloud Platform
- ✅ Created sophisticated opt-in decision model with NPV analysis
- ✅ Built BigQuery data warehouse with 10+ analytical views
- ✅ Developed Looker Studio dashboard queries for visualization
- ✅ Implemented 42% maximum reduction cap and MAI floor logic
- ✅ Generated $50M+ in potential penalty savings insights

---

... (truncated)
```

### 📄 `docs/handoffs/claude_handoff_20250113_1645.md`
```
# 🤝 Claude Session Handoff – January 13, 2025, 16:45 MDT

## 🧠 Session Summary
Today we completed a major project cleanup and began implementing the unified EUI target loader system. This session focused on organizing the codebase, fixing import issues, and creating foundational modules for consistent penalty and target calculations.

## ✅ Work Completed

### 1. Project Structure Cleanup ✅
- **Archived 30+ outdated files** into organized directories
- Removed duplicate versions (e.g., 5 versions of export_high_value_buildings)
- Moved test scripts from src/ to appropriate locations
- Created timestamp-based archive: `archive/cleanup_[timestamp]/`
- **📝 Result:** Clean, navigable project structure with only active modules

### 2. Fixed Import Issues ✅
- Created and ran `check_imports.py` to find broken imports
- Fixed 2 import issues:
  - `run_unified_analysis_v2.py`: Updated to use building_compliance_analyzer_v2
  - `fixed_enhanced_der_clustering.py`: Removed self-import, added missing functions
- Fixed hardcoded penalty rates in `hvac_system_impact_modeler.py`

... (truncated)
```

### 📄 `docs/technical/bigquery_schemas.md`
```
# BigQuery Schema Documentation
**Project:** energize-denver-eaas  
**Dataset:** energize_denver  
**Last Updated:** July 7, 2025

## 📊 Table Overview

### Core Tables

#### 1. `building_consumption_corrected`
**Description:** Latest energy consumption data with corrected calculations  
**Update Frequency:** Monthly  
**Row Count:** ~3,000  

| Column | Type | Description |
|--------|------|-------------|
| building_id | STRING | Unique building identifier |
| property_name | STRING | Building name |
| property_type | STRING | Building use type category |
| gross_floor_area | FLOAT64 | Total building square footage |

... (truncated)
```