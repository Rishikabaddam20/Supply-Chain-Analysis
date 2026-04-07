"""
main.py
Full-stack supply chain analytics pipeline orchestrator.

Runs:
  1. Data generation (if needed)
  2. Data loading, cleaning, and feature engineering
  3. ML demand forecasting (Random Forest + XGBoost)
  4. Anomaly detection (Isolation Forest)
  5. Supply chain optimisation (EOQ, safety stock, reorder points)
  6. Chart generation
  7. Excel report export

Usage:
    python python/main.py
    python python/main.py --skip-data-gen   # skip synthetic data generation
    python python/main.py --no-excel        # skip Excel export
"""

import argparse
import os
import sys
import time

# ─── Path setup ───────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "python"))

from data_preprocessing import (load_data, clean_data, engineer_features,
                                  encode_categoricals, prepare_modeling_data)
from ml_models import (train_random_forest, train_xgboost, evaluate_model,
                        plot_forecast_vs_actual, plot_feature_importance,
                        detect_anomalies, plot_anomalies, save_metrics)
from optimization import (generate_optimization_report, plot_eoq_comparison,
                           plot_stockout_vs_fillrate, plot_cost_breakdown,
                           plot_demand_trend)
from excel_report import build_excel_report


def banner(text: str):
    width = 60
    print(f"\n{'─'*width}")
    print(f"  {text}")
    print(f"{'─'*width}")


def main(args):
    t0 = time.time()
    banner("SUPPLY CHAIN ANALYTICS PLATFORM — STARTING")

    # ── Step 1: Data generation ──────────────────────────────────────────────
    data_path = os.path.join(PROJECT_ROOT, "data", "supply_chain_data.csv")
    if not os.path.exists(data_path) or not args.skip_data_gen:
        banner("Step 1/7  ·  Generating Synthetic Data")
        gen_script = os.path.join(PROJECT_ROOT, "data", "generate_data.py")
        os.system(f"{sys.executable} {gen_script}")
    else:
        print("⏩  Skipping data generation (file exists)")

    # ── Step 2: Load & preprocess ────────────────────────────────────────────
    banner("Step 2/7  ·  Loading & Preprocessing Data")
    df = load_data()
    df = clean_data(df)
    df = engineer_features(df)
    df = encode_categoricals(df)

    # ── Step 3: ML demand forecasting ────────────────────────────────────────
    banner("Step 3/7  ·  ML Demand Forecasting")
    X_tr, X_te, y_tr, y_te, feat_cols, scaler = prepare_modeling_data(df)

    rf   = train_random_forest(X_tr, y_tr)
    xgbm = train_xgboost(X_tr, y_tr)

    preds_rf,  met_rf  = evaluate_model(rf, X_te, y_te, "Random Forest")
    if xgbm:
        preds_xgb, met_xgb = evaluate_model(xgbm, X_te, y_te, "XGBoost")
    else:
        preds_xgb, met_xgb = None, {}

    print("\n📈 Generating forecast charts …")
    plot_forecast_vs_actual(y_te, preds_rf, preds_xgb)
    plot_feature_importance(rf, feat_cols, "RF")

    save_metrics({"random_forest": met_rf, "xgboost": met_xgb})

    # ── Step 4: Anomaly detection ─────────────────────────────────────────────
    banner("Step 4/7  ·  Anomaly Detection")
    df = detect_anomalies(df)
    plot_anomalies(df)

    # ── Step 5: Supply chain optimisation ────────────────────────────────────
    banner("Step 5/7  ·  Supply Chain Optimisation")
    opt_df = generate_optimization_report(df)
    opt_csv = os.path.join(PROJECT_ROOT, "outputs", "reports", "optimization_report.csv")
    opt_df.to_csv(opt_csv, index=False)
    print(f"   💾 Saved optimisation report: {opt_csv}")

    # ── Step 6: Visualisations ────────────────────────────────────────────────
    banner("Step 6/7  ·  Generating Visualisations")
    plot_eoq_comparison(opt_df)
    plot_stockout_vs_fillrate(opt_df)
    plot_cost_breakdown(opt_df)
    plot_demand_trend(df)
    if hasattr(rf, "feature_importances_") and xgbm:
        plot_feature_importance(xgbm, feat_cols, "XGB")

    # ── Step 7: Excel report ──────────────────────────────────────────────────
    if not args.no_excel:
        banner("Step 7/7  ·  Generating Excel Report")
        metrics_path = os.path.join(PROJECT_ROOT, "outputs", "reports", "model_metrics.json")
        report_path  = build_excel_report(opt_df, metrics_path)

    # ── Done ──────────────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    banner(f"✅ PIPELINE COMPLETE  ({elapsed:.1f}s)")
    print(f"\n   Outputs saved to: {os.path.join(PROJECT_ROOT, 'outputs')}/")
    print(f"   Charts : outputs/charts/")
    print(f"   Reports: outputs/reports/")
    if not args.no_excel:
        print(f"   Excel  : outputs/reports/supply_chain_analytics_report.xlsx")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supply Chain Analytics Platform")
    parser.add_argument("--skip-data-gen", action="store_true",
                        help="Skip synthetic data generation")
    parser.add_argument("--no-excel", action="store_true",
                        help="Skip Excel report generation")
    args = parser.parse_args()
    main(args)
