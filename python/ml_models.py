"""
ml_models.py
Demand forecasting (Random Forest + XGBoost), anomaly detection
(Isolation Forest), and model evaluation utilities.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, json

from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                              mean_absolute_percentage_error, r2_score)

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not installed — skipping XGBoost model")

CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)


# ─── Demand Forecasting ───────────────────────────────────────────────────────

def train_random_forest(X_train, y_train,
                        n_estimators=200, max_depth=12, random_state=42):
    """Train Random Forest regressor for demand forecasting."""
    print("🌲 Training Random Forest …")
    rf = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=5,
        n_jobs=-1,
        random_state=random_state,
    )
    rf.fit(X_train, y_train)
    print("   ✅ Random Forest trained")
    return rf


def train_xgboost(X_train, y_train):
    """Train XGBoost regressor for demand forecasting."""
    if not XGBOOST_AVAILABLE:
        return None
    print("⚡ Training XGBoost …")
    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X_train, y_train)
    print("   ✅ XGBoost trained")
    return model


def evaluate_model(model, X_test, y_test, model_name="Model"):
    """Compute and print regression metrics."""
    preds = model.predict(X_test)
    preds = np.clip(preds, 0, None)
    metrics = {
        "MAE":  round(mean_absolute_error(y_test, preds), 2),
        "RMSE": round(np.sqrt(mean_squared_error(y_test, preds)), 2),
        "MAPE": round(mean_absolute_percentage_error(y_test, preds) * 100, 2),
        "R2":   round(r2_score(y_test, preds), 4),
    }
    print(f"\n📊 {model_name} Metrics:")
    for k, v in metrics.items():
        print(f"   {k}: {v}")
    return preds, metrics


def plot_forecast_vs_actual(y_test, preds_rf, preds_xgb=None,
                            n_points=300, save=True):
    """Plot actual vs predicted demand for the first N test samples."""
    idx = np.arange(min(n_points, len(y_test)))
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(idx, y_test[:n_points], label="Actual", color="#2c7bb6", linewidth=1.5)
    ax.plot(idx, preds_rf[:n_points], label="Random Forest", color="#d7191c",
            linestyle="--", linewidth=1.5)
    if preds_xgb is not None:
        ax.plot(idx, preds_xgb[:n_points], label="XGBoost", color="#1a9641",
                linestyle="-.", linewidth=1.5)
    ax.set_title("Demand Forecast: Actual vs Predicted", fontsize=14, fontweight="bold")
    ax.set_xlabel("Test Sample Index")
    ax.set_ylabel("Units Demand")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    if save:
        path = os.path.join(CHARTS_DIR, "forecast_vs_actual.png")
        plt.savefig(path, dpi=150)
        print(f"   💾 Saved: {path}")
    plt.close()


def plot_feature_importance(model, feature_names, model_name="RF", top_n=15, save=True):
    """Bar chart of top-N feature importances."""
    importances = model.feature_importances_
    idx = np.argsort(importances)[::-1][:top_n]
    top_features = [feature_names[i] for i in idx]
    top_imp      = importances[idx]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(top_features[::-1], top_imp[::-1], color="#4575b4")
    ax.set_title(f"Feature Importances ({model_name}) — Top {top_n}", fontsize=13,
                 fontweight="bold")
    ax.set_xlabel("Importance Score")
    for bar in bars:
        ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
                f"{bar.get_width():.3f}", va="center", fontsize=8)
    plt.tight_layout()
    if save:
        path = os.path.join(CHARTS_DIR, f"feature_importance_{model_name}.png")
        plt.savefig(path, dpi=150)
        print(f"   💾 Saved: {path}")
    plt.close()


# ─── Anomaly Detection ────────────────────────────────────────────────────────

def detect_anomalies(df: pd.DataFrame, features=None, contamination=0.05) -> pd.DataFrame:
    """
    Run Isolation Forest on supply chain data to flag
    demand spikes, inventory anomalies, and suspicious lead times.
    """
    print("\n🔍 Running Anomaly Detection (Isolation Forest) …")
    if features is None:
        features = ["demand", "inventory_level", "lead_time_actual",
                    "defect_rate", "shipping_cost"]
    features = [f for f in features if f in df.columns]

    iso = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    df["anomaly_score"] = iso.fit_predict(df[features].fillna(df[features].median()))
    df["is_anomaly"]    = (df["anomaly_score"] == -1).astype(int)

    n_anomalies = df["is_anomaly"].sum()
    print(f"   ✅ Detected {n_anomalies:,} anomalies ({contamination*100:.0f}% contamination)")
    return df


def plot_anomalies(df: pd.DataFrame, save=True):
    """Scatter: demand vs inventory coloured by anomaly flag."""
    sample = df.sample(min(5000, len(df)), random_state=42)
    normal  = sample[sample["is_anomaly"] == 0]
    anomaly = sample[sample["is_anomaly"] == 1]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(normal["demand"], normal["inventory_level"],
               c="#4575b4", alpha=0.4, s=8, label="Normal")
    ax.scatter(anomaly["demand"], anomaly["inventory_level"],
               c="#d73027", alpha=0.8, s=20, marker="x", label="Anomaly")
    ax.set_title("Anomaly Detection: Demand vs Inventory Level", fontsize=13,
                 fontweight="bold")
    ax.set_xlabel("Demand (units)")
    ax.set_ylabel("Inventory Level (units)")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    if save:
        path = os.path.join(CHARTS_DIR, "anomaly_detection.png")
        plt.savefig(path, dpi=150)
        print(f"   💾 Saved: {path}")
    plt.close()


# ─── Save Metrics ─────────────────────────────────────────────────────────────

def save_metrics(metrics_dict: dict, filename="model_metrics.json"):
    out_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "reports", filename)
    with open(out_path, "w") as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"   💾 Metrics saved: {out_path}")


if __name__ == "__main__":
    from data_preprocessing import (load_data, clean_data, engineer_features,
                                    encode_categoricals, prepare_modeling_data)
    df = encode_categoricals(engineer_features(clean_data(load_data())))
    X_tr, X_te, y_tr, y_te, feat_cols, _ = prepare_modeling_data(df)

    rf   = train_random_forest(X_tr, y_tr)
    xgbm = train_xgboost(X_tr, y_tr)

    preds_rf,  met_rf  = evaluate_model(rf,   X_te, y_te, "Random Forest")
    preds_xgb, met_xgb = (evaluate_model(xgbm, X_te, y_te, "XGBoost")
                           if xgbm else (None, {}))

    plot_forecast_vs_actual(y_te, preds_rf, preds_xgb)
    plot_feature_importance(rf, feat_cols, "RF")

    df = detect_anomalies(df)
    plot_anomalies(df)

    save_metrics({"random_forest": met_rf, "xgboost": met_xgb})
