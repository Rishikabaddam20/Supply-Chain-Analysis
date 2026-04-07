"""
data_preprocessing.py
Loads raw supply chain data, cleans it, engineers features,
and prepares train/test splits for modeling.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_data() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "supply_chain_data.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    print(f"✅ Loaded {len(df):,} rows from {path}")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicates, fill gaps, clip outliers."""
    df = df.drop_duplicates()
    df = df.sort_values(["product_id", "date"]).reset_index(drop=True)

    # Fill missing numeric columns with forward-fill then median
    numeric_cols = df.select_dtypes(include=np.number).columns
    df[numeric_cols] = df[numeric_cols].ffill().fillna(df[numeric_cols].median())

    # Clip extreme demand outliers (> 3 sigma per product)
    def clip_outliers(series):
        mu, sigma = series.mean(), series.std()
        return series.clip(lower=mu - 3*sigma, upper=mu + 3*sigma)

    df["demand"] = df.groupby("product_id")["demand"].transform(clip_outliers)

    print(f"✅ Cleaned data — {df.shape[0]:,} rows, {df.shape[1]} columns")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add rolling stats, lag features, and cyclical encodings."""
    df = df.sort_values(["product_id", "date"])

    grp = df.groupby("product_id")["demand"]

    # Rolling window features
    for window in [7, 14, 30]:
        df[f"demand_rolling_mean_{window}d"] = grp.transform(
            lambda x: x.rolling(window, min_periods=1).mean())
        df[f"demand_rolling_std_{window}d"] = grp.transform(
            lambda x: x.rolling(window, min_periods=1).std().fillna(0))

    # Lag features
    for lag in [1, 7, 14]:
        df[f"demand_lag_{lag}d"] = grp.transform(lambda x: x.shift(lag)).fillna(0)

    # Cyclical date encodings
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["dow_sin"]   = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"]   = np.cos(2 * np.pi * df["day_of_week"] / 7)

    # Inventory health ratio
    df["inventory_ratio"] = df["inventory_level"] / (df["reorder_point"] + 1)

    # Service level (fill rate)
    df["fill_rate"] = df["units_sold"] / (df["demand"] + 1e-9)

    print(f"✅ Engineered features — {df.shape[1]} total columns")
    return df


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Label-encode string columns."""
    le = LabelEncoder()
    for col in ["product_id", "supplier_id", "warehouse_id", "region", "category"]:
        if col in df.columns:
            df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))
    return df


def prepare_modeling_data(df: pd.DataFrame, target: str = "demand",
                           test_size: float = 0.2):
    """Return scaled train/test splits and the scaler."""
    feature_cols = [c for c in df.columns if c.endswith("_enc") or c in [
        "month_sin", "month_cos", "dow_sin", "dow_cos",
        "demand_rolling_mean_7d", "demand_rolling_mean_14d", "demand_rolling_mean_30d",
        "demand_rolling_std_7d", "demand_rolling_std_14d",
        "demand_lag_1d", "demand_lag_7d", "demand_lag_14d",
        "inventory_ratio", "fill_rate", "is_weekend",
        "shipping_cost", "reliability_score", "quarter",
    ]]

    df_clean = df.dropna(subset=feature_cols + [target])
    X = df_clean[feature_cols].values
    y = df_clean[target].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, shuffle=False
    )

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    print(f"✅ Modeling data ready — train: {X_train_sc.shape}, test: {X_test_sc.shape}")
    return X_train_sc, X_test_sc, y_train, y_test, feature_cols, scaler


if __name__ == "__main__":
    df = load_data()
    df = clean_data(df)
    df = engineer_features(df)
    df = encode_categoricals(df)
    X_train, X_test, y_train, y_test, features, scaler = prepare_modeling_data(df)
