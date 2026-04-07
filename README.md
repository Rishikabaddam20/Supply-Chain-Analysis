#  Supply Chain Analytics Platform

A full-stack, production-ready analytics platform combining Python ML pipelines and R statistical modelling to deliver end-to-end supply chain intelligence — from raw data through forecasting, optimisation, anomaly detection, and automated Excel reporting.

---

## ️ Project Structure

```
supply-chain-analytics-platform/
├── data/
│   ├── generate_data.py          # Synthetic supply chain data generator
│   ├── supply_chain_data.csv     # Generated dataset (auto-created)
│   ├── products.csv
│   └── suppliers.csv
│
├── python/
│   ├── __init__.py
│   ├── data_preprocessing.py     # Cleaning, feature engineering, train/test split
│   ├── ml_models.py              # Random Forest + XGBoost demand forecasting
│   │                               Isolation Forest anomaly detection
│   ├── optimization.py           # EOQ, safety stock, reorder point, KPI computation
│   ├── excel_report.py           # Auto-generate Excel workbook with charts & KPIs
│   └── main.py                   #  Full pipeline orchestrator
│
├── r/
│   ├── statistical_analysis.R    # Descriptive stats, regression, ANOVA, correlation
│   ├── time_series.R             # STL decomposition, Auto-ARIMA, ETS forecasting
│   └── run_all.R                 # R orchestrator
│
├── outputs/
│   ├── charts/                   # All generated PNG visualisations
│   └── reports/                  # Excel report, CSV exports, JSON metrics
│
├── notebooks/                    # Jupyter notebooks for exploration
├── requirements.txt
├── setup.sh
└── .gitignore
```

---

##  Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/supply-chain-analytics-platform.git
cd supply-chain-analytics-platform
```

### 2. One-Click Setup
```bash
bash setup.sh
```
This creates a Python virtual environment, installs all dependencies, and sets up R packages.

### 3. Run the Full Pipeline
```bash
source venv/bin/activate
python python/main.py
```

### 4. Run R Analysis
```bash
Rscript r/run_all.R
```

---

##  What the Platform Does

### Python Pipeline (`python/main.py`)
| Step | Module | Description |
|------|--------|-------------|
| 1 | `generate_data.py` | Generates 4 years of synthetic supply chain data (20 products, 8 suppliers, 5 warehouses) |
| 2 | `data_preprocessing.py` | Cleans data, engineers 20+ features (rolling stats, lags, cyclical encodings) |
| 3 | `ml_models.py` | Trains **Random Forest** + **XGBoost** for demand forecasting |
| 4 | `ml_models.py` | **Isolation Forest** anomaly detection (demand spikes, inventory irregularities) |
| 5 | `optimization.py` | Computes **EOQ**, safety stock, reorder points, fill rates, inventory turnover |
| 6 | `optimization.py` | Generates 8 publication-quality charts |
| 7 | `excel_report.py` | Builds a 4-sheet **Excel workbook** with KPI tables, conditional formatting, and embedded charts |

### R Analysis (`r/run_all.R`)
| Script | Techniques |
|--------|-----------|
| `statistical_analysis.R` | Descriptive stats, Pearson correlation heatmap, multiple linear regression, one-way ANOVA + Tukey HSD |
| `time_series.R` | STL decomposition, ADF stationarity test, **Auto-ARIMA**, **ETS exponential smoothing**, seasonal heatmap, 26-week forecast |

---

## 📊 Outputs

After running the pipeline you'll find:

**`outputs/charts/`**
- `demand_trend.png` — Monthly aggregate demand trend
- `forecast_vs_actual.png` — ML forecast vs actual demand
- `feature_importance_RF.png` — Random Forest feature importances
- `anomaly_detection.png` — Isolation Forest anomaly scatter
- `eoq_comparison.png` — EOQ by product
- `stockout_vs_fillrate.png` — Bubble chart (stockout vs fill rate)
- `cost_breakdown.png` — Stacked bar (holding + stockout costs)
- `correlation_matrix.png` — Pearson correlation heatmap (R)
- `arima_forecast.png` — 26-week ARIMA demand forecast (R)
- `seasonal_heatmap.png` — Monthly seasonal patterns (R)
- `weekly_demand_inventory.png` — Weekly trends (R)

**`outputs/reports/`**
- `supply_chain_analytics_report.xlsx` — Executive Excel workbook (4 sheets)
- `optimization_report.csv` — Full product-level KPI table
- `model_metrics.json` — ML model performance (MAE, RMSE, MAPE, R²)
- `descriptive_stats.csv` — Summary statistics (R)
- `regression_coefficients.csv` — Linear regression output (R)
- `ts_model_accuracy.csv` — ARIMA/ETS accuracy metrics (R)

---

##  Tech Stack

| Area | Tools |
|------|-------|
| **Language** | Python 3.10+ · R 4.3+ |
| **ML / Stats** | scikit-learn · XGBoost · forecast · tseries |
| **Data** | pandas · NumPy · tidyverse · lubridate |
| **Visualisation** | matplotlib · seaborn · ggplot2 · corrplot · patchwork |
| **Reporting** | openpyxl · broom · scales |
| **Version Control** | Git |

---

## Key Analytics Skills Demonstrated

- Predictive modelling (Random Forest, XGBoost, ARIMA, ETS)
- Statistical modelling (regression, ANOVA, correlation)
- Supply chain optimisation (EOQ, safety stock, service level)
- Anomaly / outlier detection (Isolation Forest)
- Time series decomposition and forecasting
- Executive-level reporting (automated Excel workbooks)
- Data engineering (feature engineering, rolling windows, lag features)

---

## Pushing to GitHub

```bash
# Initialise and push for the first time
git init
git add .
git commit -m "Initial commit: Supply Chain Analytics Platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/supply-chain-analytics-platform.git
git push -u origin main

# Subsequent pushes
git add .
git commit -m "Your commit message"
git push
```

---

## Requirements

- Python 3.10+
- R 4.3+ (optional, for statistical and time series analysis)
- ~500 MB disk space for generated data and outputs

---


# Supply-Chain-Analytics-platform
