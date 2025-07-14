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
- **File**: `src/utils/penalty_calculator.py`

### 4. Discovered and Addressed MAI Complexity
- **Key Finding**: MAI designation is NOT limited to Manufacturing/Industrial Plant
- **MAI Buildings**: Include Data Centers, Distribution Centers, Warehouses, Offices, etc.
- **Identification**: Building must appear in `MAITargetSummary Report.csv`
- **Created**: `mai_data_loader.py` utility module

### 5. Established MAI Target Logic
- **Final Target** = MAX(Adjusted Final Target from CSV, 30% reduction, 52.9 floor)
- This ensures MAI buildings get the most lenient (highest) target
- Protects MAI buildings from overly aggressive targets

## Next Steps for Implementation

### Phase 1: Create Unified EUI Target Loader (Priority)
1. Create `src/utils/eui_target_loader.py` that:
   - Loads targets from Building_EUI_Targets.csv
   - Loads MAI data from MAITargetSummary Report.csv
   - Implements priority logic for target selection
   - Returns standardized format for all scripts

### Phase 2: Update Core Scripts
1. **Update penalty calculations in:**
   - `create_opt_in_decision_model.py` (fix $0.23 rate for ACO)
   - `building_compliance_analyzer.py`
   - `integrated_tes_hp_analyzer.py`

2. **Implement MAI logic in:**
   - All scripts that calculate targets
   - Use MAI designation from CSV, not property type

### Phase 3: Validate and Test
1. Run penalty verification script
2. Compare calculations with technical guidance
3. Test MAI buildings specifically
4. Verify Building 2952 calculations

## Key Files and Locations

### Created Today:
- `/docs/penalty_calculation_source_of_truth.md` - Definitive penalty guide
- `/src/utils/penalty_calculator.py` - Penalty calculation module
- `/src/utils/mai_data_loader.py` - MAI data loading utility
- `/src/gcp/export_high_value_buildings_enhanced_v3_fixed.py` - Fixed export script

### Key Data Files:
- `/data/raw/Building_EUI_Targets.csv` - Main targets
- `/data/raw/MAITargetSummary Report.csv` - MAI designations and targets
- `/data/raw/MAIPropertyUseTypes Report.csv` - MAI property details
- `/data/raw/CopyofWeeklyEPBStatsReport Report.csv` - EPB data

## Important Context for Next Session

1. **Penalty rates are now correct** throughout documentation
2. **MAI logic has been clarified** - use MAX() of three values
3. **Next priority** is creating the unified EUI target loader
4. **Building 2952** should be used for testing (not MAI)
5. **All scripts** need to be updated to use the new modules

## Questions Resolved
- First interim target year: 2025 for most (check CSV)
- MAI identification: Use MAITargetSummary list
- Caps/floors: NOT pre-applied in CSVs, must calculate
- Payment timing: Year after target year

## Open Items
- Need to update all BigQuery views with correct penalty rates
- Need to create comprehensive test suite
- Need to validate calculations against real buildings
