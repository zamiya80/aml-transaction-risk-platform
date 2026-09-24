"""
04_generate_visuals.py
------------------------------------------------------------------
Generates the core static charts for the project (used in the README
and as a reference for the interactive dashboard):

  1. Regional risk heatmap        -> outputs/charts/regional_risk_heatmap.png
  2. Claim type time series       -> outputs/charts/claims_time_series.png
  3. Default rate by employment   -> outputs/charts/default_rate_by_employment.png
  4. Risk KPI summary panel       -> outputs/charts/risk_kpi_summary.png
  5. Risk score distribution      -> outputs/charts/risk_score_distribution.png

Run:
    python scripts/04_generate_visuals.py
------------------------------------------------------------------
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "merged_risk_data.csv")
RAW_CLAIMS_PATH = os.path.join(BASE_DIR, "data", "raw", "claims_raw.csv")
CHART_DIR = os.path.join(BASE_DIR, "outputs", "charts")
os.makedirs(CHART_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="viridis")
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.size"] = 10

RISK_COLORS = {"Low": "#2a9d8f", "Medium": "#e9c46a", "High": "#e76f51"}


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["risk_category"] = pd.Categorical(df["risk_category"], categories=["Low", "Medium", "High"], ordered=True)
    claims = pd.read_csv(RAW_CLAIMS_PATH)
    claims["claim_date"] = pd.to_datetime(claims["claim_date"], dayfirst=True, errors="coerce", format="mixed")
    claims["claim_amount"] = claims["claim_amount"].abs()
    return df, claims


# ------------------------------------------------------------------
# 1. Regional risk heatmap
# ------------------------------------------------------------------
def regional_risk_heatmap(df):
    pivot = pd.crosstab(df["region"], df["risk_category"], normalize="index") * 100
    pivot = pivot.loc[pivot["High"].sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd", cbar_kws={"label": "% of regional customers"}, ax=ax)
    ax.set_title("Regional Risk Segmentation Heatmap\n(% of customers by risk category, per region)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Risk Category")
    ax.set_ylabel("Region")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "regional_risk_heatmap.png"))
    plt.close()


# ------------------------------------------------------------------
# 2. Claim type time series
# ------------------------------------------------------------------
def claims_time_series(claims):
    ts = claims.dropna(subset=["claim_date"]).copy()
    ts["month"] = ts["claim_date"].dt.to_period("M").dt.to_timestamp()
    monthly = ts.groupby(["month", "claim_type"])["claim_amount"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(11, 5.5))
    for claim_type, grp in monthly.groupby("claim_type"):
        ax.plot(grp["month"], grp["claim_amount"], marker="o", markersize=2.5, linewidth=1.3, label=claim_type)

    ax.set_title("Monthly Claim Value by Claim Type (2019 - 2026)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Claim Value (£)")
    ax.legend(title="Claim Type", loc="upper left", fontsize=8)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"£{x/1000:.0f}k"))
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "claims_time_series.png"))
    plt.close()


# ------------------------------------------------------------------
# 3. Default rate by employment type
# ------------------------------------------------------------------
def default_rate_by_employment(df):
    agg = df.groupby("employment_type").agg(
        default_rate=("default_flag", "mean"),
        n=("customer_id", "count"),
    ).reset_index().sort_values("default_rate", ascending=False)
    agg["default_rate_pct"] = agg["default_rate"] * 100

    fig, ax = plt.subplots(figsize=(8, 5.5))
    bars = ax.bar(agg["employment_type"], agg["default_rate_pct"], color=sns.color_palette("rocket", len(agg)))
    ax.set_title("Default Rate by Employment Type", fontsize=12, fontweight="bold")
    ax.set_xlabel("Employment Type")
    ax.set_ylabel("Default Rate (%)")
    for bar, pct, n in zip(bars, agg["default_rate_pct"], agg["n"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                 f"{pct:.1f}%\n(n={n:,})", ha="center", va="bottom", fontsize=8)
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "default_rate_by_employment.png"))
    plt.close()


# ------------------------------------------------------------------
# 4. Risk KPI summary panel
# ------------------------------------------------------------------
def risk_kpi_summary(df):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

    # Risk category split (donut)
    counts = df["risk_category"].value_counts().reindex(["Low", "Medium", "High"])
    axes[0].pie(counts, labels=counts.index, autopct="%1.1f%%", startangle=90,
                colors=[RISK_COLORS[c] for c in counts.index],
                wedgeprops={"width": 0.4})
    axes[0].set_title("Customer Risk Mix", fontweight="bold")

    # Default rate by risk category
    dr = df.groupby("risk_category", observed=True)["default_flag"].mean() * 100
    dr = dr.reindex(["Low", "Medium", "High"])
    axes[1].bar(dr.index, dr.values, color=[RISK_COLORS[c] for c in dr.index])
    axes[1].set_title("Default Rate by Risk Category", fontweight="bold")
    axes[1].set_ylabel("Default Rate (%)")
    for i, v in enumerate(dr.values):
        axes[1].text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=9)

    # Avg DTI by risk category
    dti = df.groupby("risk_category", observed=True)["debt_to_income"].mean()
    dti = dti.reindex(["Low", "Medium", "High"])
    axes[2].bar(dti.index, dti.values, color=[RISK_COLORS[c] for c in dti.index])
    axes[2].set_title("Avg Debt-to-Income by Risk Category", fontweight="bold")
    axes[2].set_ylabel("Debt-to-Income Ratio")
    for i, v in enumerate(dti.values):
        axes[2].text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=9)

    fig.suptitle("Core Risk KPI Tracker", fontsize=13, fontweight="bold", y=1.03)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "risk_kpi_summary.png"), bbox_inches="tight")
    plt.close()


# ------------------------------------------------------------------
# 5. Risk score distribution
# ------------------------------------------------------------------
def risk_score_distribution(df):
    fig, ax = plt.subplots(figsize=(9, 5))
    for cat in ["Low", "Medium", "High"]:
        subset = df[df["risk_category"] == cat]
        sns.kdeplot(subset["risk_score"], fill=True, alpha=0.4, label=cat, color=RISK_COLORS[cat], ax=ax)
    ax.set_title("Risk Score Distribution by Category", fontsize=12, fontweight="bold")
    ax.set_xlabel("Composite Risk Score (0-100)")
    ax.set_ylabel("Density")
    ax.legend(title="Risk Category")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "risk_score_distribution.png"))
    plt.close()


if __name__ == "__main__":
    df, claims = load_data()
    regional_risk_heatmap(df)
    claims_time_series(claims)
    default_rate_by_employment(df)
    risk_kpi_summary(df)
    risk_score_distribution(df)
    print(f"Saved 5 charts to {CHART_DIR}")
