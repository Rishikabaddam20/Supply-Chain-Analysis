"""
optimization.py
Supply chain optimization utilities:
  - Economic Order Quantity (EOQ)
  - Safety stock calculation
  - Reorder point optimization
  - Inventory turnover & KPI computation
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)


# ─── EOQ & Reorder Calculations ───────────────────────────────────────────────

def compute_eoq(annual_demand: float, order_cost: float,
                holding_cost_per_unit: float) -> float:
    """
    Economic Order Quantity = sqrt(2DS / H)
    D = annual demand, S = ordering cost, H = annual holding cost per unit.
    """
    if holding_cost_per_unit <= 0:
        return np.nan
    return np.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)


def compute_safety_stock(demand_std: float, lead_time_days: float,
                          service_level_z: float = 1.645) -> float:
    """
    Safety Stock = Z * σ_demand * sqrt(lead_time)
    Default Z = 1.645 → 95% service level.
    """
    return service_level_z * demand_std * np.sqrt(lead_time_days)


def compute_reorder_point(avg_daily_demand: float, lead_time_days: float,
                           safety_stock: float) -> float:
    """ROP = (avg_daily_demand × lead_time) + safety_stock."""
    return avg_daily_demand * lead_time_days + safety_stock


def generate_optimization_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily data by product and compute:
    EOQ, safety stock, reorder point, fill rate, stockout rate,
    inventory turnover, and total cost metrics.
    """
    ORDER_COST     = 50   # $ per order
    HOLDING_RATE   = 0.25  # 25% of unit cost per year

    grp = df.groupby("product_id").agg(
        category          = ("category",          "first"),
        unit_cost         = ("unit_cost",         "first"),
        lead_time_days    = ("lead_time_days",     "first"),
        reorder_point_orig= ("reorder_point",      "first"),
        safety_stock_orig = ("safety_stock",       "first"),
        total_demand      = ("demand",             "sum"),
        avg_daily_demand  = ("demand",             "mean"),
        std_daily_demand  = ("demand",             "std"),
        total_units_sold  = ("units_sold",         "sum"),
        total_revenue     = ("revenue",            "sum"),
        total_stockout_cost=("stockout_cost",      "sum"),
        total_holding_cost= ("holding_cost",       "sum"),
        avg_inventory     = ("inventory_level",    "mean"),
        stockout_days     = ("stockout",           "sum"),
        total_days        = ("date",               "count"),
        avg_reliability   = ("reliability_score",  "mean"),
        late_deliveries   = ("late_delivery",      "sum"),
    ).reset_index()

    # Optimised metrics
    grp["annual_demand"]    = grp["avg_daily_demand"] * 365
    grp["holding_cost_pu"]  = grp["unit_cost"] * HOLDING_RATE
    grp["eoq"]              = grp.apply(
        lambda r: compute_eoq(r["annual_demand"], ORDER_COST, r["holding_cost_pu"]), axis=1)
    grp["opt_safety_stock"] = grp.apply(
        lambda r: compute_safety_stock(r["std_daily_demand"], r["lead_time_days"]), axis=1)
    grp["opt_reorder_point"]= grp.apply(
        lambda r: compute_reorder_point(r["avg_daily_demand"],
                                         r["lead_time_days"], r["opt_safety_stock"]), axis=1)

    # KPIs
    grp["fill_rate_%"]      = (grp["total_units_sold"] / grp["total_demand"] * 100).round(2)
    grp["stockout_rate_%"]  = (grp["stockout_days"]  / grp["total_days"] * 100).round(2)
    grp["inventory_turnover"]= (grp["total_units_sold"] / grp["avg_inventory"].replace(0, 1)).round(2)
    grp["on_time_delivery_%"]= ((1 - grp["late_deliveries"] / grp["total_days"]) * 100).round(2)
    grp["total_supply_cost"] = (grp["total_holding_cost"] + grp["total_stockout_cost"]).round(2)
    grp["total_revenue"]     = grp["total_revenue"].round(2)
    grp["gross_margin_%"]    = ((grp["total_revenue"] - grp["total_supply_cost"])
                                 / grp["total_revenue"] * 100).round(2)

    print(f"✅ Optimisation report generated for {len(grp)} products")
    return grp


# ─── Visualisations ───────────────────────────────────────────────────────────

def plot_eoq_comparison(opt_df: pd.DataFrame, save=True):
    """Bar chart: optimal EOQ per product."""
    top = opt_df.nlargest(15, "eoq")
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(top)))
    ax.bar(top["product_id"], top["eoq"], color=colors)
    ax.set_title("Economic Order Quantity (EOQ) by Product — Top 15", fontsize=13,
                 fontweight="bold")
    ax.set_xlabel("Product ID")
    ax.set_ylabel("EOQ (units)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    if save:
        path = os.path.join(CHARTS_DIR, "eoq_comparison.png")
        plt.savefig(path, dpi=150)
        print(f"   💾 Saved: {path}")
    plt.close()


def plot_stockout_vs_fillrate(opt_df: pd.DataFrame, save=True):
    """Scatter: stockout rate vs fill rate, sized by revenue."""
    fig, ax = plt.subplots(figsize=(10, 7))
    sc = ax.scatter(
        opt_df["stockout_rate_%"], opt_df["fill_rate_%"],
        c=opt_df["inventory_turnover"], cmap="RdYlGn",
        s=opt_df["total_revenue"] / opt_df["total_revenue"].max() * 400 + 30,
        alpha=0.75, edgecolors="white", linewidths=0.5
    )
    plt.colorbar(sc, ax=ax, label="Inventory Turnover")
    for _, row in opt_df.iterrows():
        ax.annotate(row["product_id"],
                    (row["stockout_rate_%"], row["fill_rate_%"]),
                    fontsize=7, alpha=0.7)
    ax.set_title("Stockout Rate vs Fill Rate (bubble size ∝ Revenue)", fontsize=13,
                 fontweight="bold")
    ax.set_xlabel("Stockout Rate (%)")
    ax.set_ylabel("Fill Rate (%)")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    if save:
        path = os.path.join(CHARTS_DIR, "stockout_vs_fillrate.png")
        plt.savefig(path, dpi=150)
        print(f"   💾 Saved: {path}")
    plt.close()


def plot_cost_breakdown(opt_df: pd.DataFrame, save=True):
    """Stacked bar: holding vs stockout cost per product."""
    top = opt_df.nlargest(12, "total_supply_cost")
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(top))
    ax.bar(x, top["total_holding_cost"],  label="Holding Cost",  color="#4575b4")
    ax.bar(x, top["total_stockout_cost"], bottom=top["total_holding_cost"],
           label="Stockout Cost", color="#d73027")
    ax.set_xticks(x)
    ax.set_xticklabels(top["product_id"], rotation=45)
    ax.set_title("Supply Chain Cost Breakdown — Top 12 Products", fontsize=13,
                 fontweight="bold")
    ax.set_ylabel("Cost ($)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    if save:
        path = os.path.join(CHARTS_DIR, "cost_breakdown.png")
        plt.savefig(path, dpi=150)
        print(f"   💾 Saved: {path}")
    plt.close()


def plot_demand_trend(df: pd.DataFrame, product_id: str = None, save=True):
    """Monthly demand trend for one or all products."""
    if product_id:
        sub = df[df["product_id"] == product_id].copy()
        title = f"Monthly Demand Trend — {product_id}"
    else:
        sub = df.copy()
        title = "Monthly Aggregate Demand Trend"

    monthly = sub.resample("ME", on="date")["demand"].sum().reset_index()
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.fill_between(monthly["date"], monthly["demand"], alpha=0.25, color="#4575b4")
    ax.plot(monthly["date"], monthly["demand"], color="#4575b4", linewidth=2)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Demand (units)")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    if save:
        path = os.path.join(CHARTS_DIR, "demand_trend.png")
        plt.savefig(path, dpi=150)
        print(f"   💾 Saved: {path}")
    plt.close()


if __name__ == "__main__":
    from data_preprocessing import load_data, clean_data, engineer_features, encode_categoricals
    df  = encode_categoricals(engineer_features(clean_data(load_data())))
    opt = generate_optimization_report(df)
    print(opt[["product_id","eoq","opt_safety_stock","fill_rate_%","stockout_rate_%"]].head(10))
    plot_eoq_comparison(opt)
    plot_stockout_vs_fillrate(opt)
    plot_cost_breakdown(opt)
    plot_demand_trend(df)
