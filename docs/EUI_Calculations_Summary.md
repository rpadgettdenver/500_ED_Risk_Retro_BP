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
Average_EUI_Recent = (80.5 + 75.3 + 70.1) / 3 = 75.30
```

**Purpose:** Shows the building's average energy performance over recent years, smoothing out year-to-year variations

---

### 2. **EUI_Trend_Pct** (Float, 2 decimals)
**What it represents:** The percentage change in EUI from the first to last year in the recent period

**Calculation:**
```
((Last_Year_EUI - First_Year_EUI) / First_Year_EUI) × 100
```

**Sign Convention:**
- **Negative values** = Improvement (energy use decreasing) ✅
- **Positive values** = Worsening (energy use increasing) ❌

**Example:**
```
First year (2021): EUI = 80.5
Last year (2023): EUI = 70.1
EUI_Trend_Pct = ((70.1 - 80.5) / 80.5) × 100 = -12.92%
```

**Purpose:** Shows the recent trajectory of energy performance

---

### 3. **EUI_Change_From_Baseline_Pct** (Float, 2 decimals)
**What it represents:** The percentage change from the building's official baseline year to current

**Calculation:**
```
((Current_Year_EUI - Baseline_Year_EUI) / Baseline_Year_EUI) × 100
```

**Baseline Year Source:** From `Building_EUI_Targets.csv`
- Most buildings: 2019 (Energize Denver program start)
- Some buildings: 2020, 2021, or 2022 (per technical guidelines)

**Sign Convention:**
- **Negative values** = Improvement from baseline ✅
- **Positive values** = Worsening from baseline ❌

**Example:**
```
Baseline (2019): EUI = 100.0
Current (2023): EUI = 85.0
EUI_Change_From_Baseline_Pct = ((85.0 - 100.0) / 100.0) × 100 = -15.00%
```

**Purpose:** Measures progress toward Energize Denver compliance targets

---

### 4. **Current_EUI** (Float, 2 decimals)
**What it represents:** The building's most recent Weather Normalized Site EUI

**Calculation:**
- No calculation needed - direct value from most recent reporting year
- Simply the Weather Normalized Site EUI from the latest year on record

**Example:**
```
Building last reported in 2023 with Weather Normalized Site EUI = 85.47
Current_EUI = 85.47
```

**Purpose:** Shows the building's current energy performance for compliance assessment

---

### 5. **Baseline_EUI** (Float, 2 decimals)
**What it represents:** The building's Weather Normalized Site EUI in its baseline year

**Calculation:**
- Looks up the building's baseline year from `Building_EUI_Targets.csv`
- Retrieves the Weather Normalized Site EUI from that specific year

**Example:**
```
Baseline Year = 2019
Weather Normalized Site EUI in 2019 = 100.00
Baseline_EUI = 100.00
```

**Purpose:** Reference point for measuring improvement and compliance

---

## 📈 Additional Context Fields

### **Most_Recent_Report_Year**
- The latest year for which the building reported data
- Integer value (2022, 2023, or 2024)

### **Years_Reported**
- List of all years the building has reported
- Example: [2018, 2019, 2020, 2021, 2022, 2023]

### **Number_Years_Reported**
- Count of unique reporting years
- Used to determine data availability for trend calculations

---

## 🎯 Why These Calculations Matter

1. **Compliance Assessment**: Buildings must meet specific EUI reduction targets
2. **Trend Analysis**: Shows whether buildings are on track to meet future targets
3. **Baseline Comparison**: Energize Denver penalties are based on performance vs. baseline
4. **Investment Decisions**: Helps prioritize which buildings need retrofits

---

## 📊 Data Quality Notes

- All percentage calculations require non-zero denominators
- Buildings need at least 2 years of data for trend calculations
- Missing values are left as NaN rather than filled with zeros
- All EUI values use **Weather Normalized Site EUI** for fair comparison
- Float formatting with 2 decimals ensures Excel compatibility

---

## 🔄 Update Frequency

- Data refreshed annually when new benchmarking reports are submitted
- Baseline years remain fixed per building unless officially adjusted
- Calculations automatically update when new years are added
