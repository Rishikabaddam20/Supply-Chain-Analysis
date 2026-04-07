"""
generate_data.py
Generates synthetic supply chain dataset for the analytics platform.
Simulates realistic demand, inventory, supplier, and logistics data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ─── Configuration ────────────────────────────────────────────────────────────
START_DATE    = datetime(2022, 1, 1)
END_DATE      = datetime(2025, 12, 31)
N_PRODUCTS    = 20
N_SUPPLIERS   = 8
N_WAREHOUSES  = 5
REGIONS       = ["North", "South", "East", "West", "Central"]
CATEGORIES    = ["Electronics", "Apparel", "Furniture", "Grocery", "Automotive"]

# ─── Date range ───────────────────────────────────────────────────────────────
dates = pd.date_range(START_DATE, END_DATE, freq="D")
n_days = len(dates)

# ─── Products ─────────────────────────────────────────────────────────────────
products = pd.DataFrame({
    "product_id":   [f"P{str(i).zfill(3)}" for i in range(1, N_PRODUCTS + 1)],
    "product_name": [f"Product_{i}" for i in range(1, N_PRODUCTS + 1)],
    "category":     np.random.choice(CATEGORIES, N_PRODUCTS),
    "unit_cost":    np.round(np.random.uniform(5, 500, N_PRODUCTS), 2),
    "lead_time_days": np.random.randint(3, 30, N_PRODUCTS),
    "reorder_point":  np.random.randint(50, 300, N_PRODUCTS),
    "safety_stock":   np.random.randint(20, 150, N_PRODUCTS),
})

# ─── Suppliers ────────────────────────────────────────────────────────────────
suppliers = pd.DataFrame({
    "supplier_id":       [f"S{str(i).zfill(2)}" for i in range(1, N_SUPPLIERS + 1)],
    "supplier_name":     [f"Supplier_{chr(64+i)}" for i in range(1, N_SUPPLIERS + 1)],
    "reliability_score": np.round(np.random.uniform(0.70, 0.99, N_SUPPLIERS), 2),
    "avg_delivery_days": np.random.randint(2, 21, N_SUPPLIERS),
    "region":            np.random.choice(REGIONS, N_SUPPLIERS),
})

# ─── Daily demand data ────────────────────────────────────────────────────────
records = []
for pid in products["product_id"]:
    base_demand = np.random.randint(10, 200)
    trend       = np.linspace(0, np.random.uniform(-0.3, 0.5) * base_demand, n_days)
    seasonality = 20 * np.sin(2 * np.pi * np.arange(n_days) / 365)
    noise       = np.random.normal(0, base_demand * 0.15, n_days)
    demand      = np.clip(base_demand + trend + seasonality + noise, 0, None).astype(int)

    # Inject a few stockout / anomaly spikes
    spike_idx = np.random.choice(n_days, size=12, replace=False)
    demand[spike_idx] = demand[spike_idx] * np.random.uniform(2, 4, 12)

    inventory   = np.clip(
        np.random.randint(100, 1000) - np.cumsum(demand) % 1000,
        0, 2000
    )
    supplier_id = np.random.choice(suppliers["supplier_id"])
    warehouse   = np.random.choice([f"WH{i}" for i in range(1, N_WAREHOUSES + 1)])

    for i, d in enumerate(dates):
        records.append({
            "date":           d,
            "product_id":     pid,
            "supplier_id":    supplier_id,
            "warehouse_id":   warehouse,
            "region":         np.random.choice(REGIONS),
            "demand":         int(demand[i]),
            "inventory_level":int(inventory[i]),
            "units_sold":     int(min(demand[i], inventory[i])),
            "units_ordered":  int(np.random.randint(0, 300)),
            "lead_time_actual": int(np.random.randint(1, 35)),
            "defect_rate":    round(np.random.beta(1, 20), 4),
            "shipping_cost":  round(np.random.uniform(5, 150), 2),
            "stockout":       int(demand[i] > inventory[i]),
        })

df = pd.DataFrame(records)

# ─── Merge product metadata ───────────────────────────────────────────────────
df = df.merge(products[["product_id", "category", "unit_cost", "lead_time_days",
                         "reorder_point", "safety_stock"]], on="product_id")
df = df.merge(suppliers[["supplier_id", "reliability_score"]], on="supplier_id")

# ─── Derived columns ──────────────────────────────────────────────────────────
df["revenue"]           = df["units_sold"] * df["unit_cost"]
df["stockout_cost"]     = (df["demand"] - df["units_sold"]).clip(lower=0) * df["unit_cost"] * 1.5
df["holding_cost"]      = df["inventory_level"] * df["unit_cost"] * 0.0002
df["day_of_week"]       = df["date"].dt.dayofweek
df["month"]             = df["date"].dt.month
df["quarter"]           = df["date"].dt.quarter
df["year"]              = df["date"].dt.year
df["is_weekend"]        = (df["day_of_week"] >= 5).astype(int)
df["late_delivery"]     = (df["lead_time_actual"] > df["lead_time_days"]).astype(int)

# ─── Save ─────────────────────────────────────────────────────────────────────
out_dir = os.path.join(os.path.dirname(__file__))
df.to_csv(os.path.join(out_dir, "supply_chain_data.csv"), index=False)
products.to_csv(os.path.join(out_dir, "products.csv"), index=False)
suppliers.to_csv(os.path.join(out_dir, "suppliers.csv"), index=False)

print(f"✅ Generated {len(df):,} rows of supply chain data")
print(f"   Products : {N_PRODUCTS}  |  Suppliers : {N_SUPPLIERS}  |  Warehouses : {N_WAREHOUSES}")
print(f"   Date range: {START_DATE.date()} → {END_DATE.date()}")
print(f"   Saved to  : {out_dir}/")
