"""
Insurance & Lending Risk Analysis — Interactive Dashboard
------------------------------------------------------------------
Run locally with:
    streamlit run dashboard/app.py

Reads data/processed/merged_risk_data.csv and data/raw/claims_raw.csv
(run scripts/01_data_cleaning_feature_engineering.py first if those
don't exist yet). No other setup required.
------------------------------------------------------------------
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Insurance & Lending Risk Dashboard",
    page_icon="📊",
    layout="wide",
)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "merged_risk_data.csv")
CLAIMS_PATH = os.path.join(BASE_DIR, "data", "raw", "claims_raw.csv")

RISK_COLORS = {"Low": "#2a9d8f", "Medium": "#e9c46a", "High": "#e76f51"}


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["risk_category"] = pd.Categorical(df["risk_category"], categories=["Low", "Medium", "High"], ordered=True)

    claims = pd.read_csv(CLAIMS_PATH)
    claims["claim_date"] = pd.to_datetime(claims["claim_date"], dayfirst=True, errors="coerce", format="mixed")
    claims["claim_amount"] = claims["claim_amount"].abs()
    return df, claims


df, claims = load_data()

# ------------------------------------------------------------------
# Sidebar filters
# ------------------------------------------------------------------
st.sidebar.header("Filters")
regions = st.sidebar.multiselect("Region", sorted(df["region"].unique()), default=None)
employment = st.sidebar.multiselect("Employment Type", sorted(df["employment_type"].unique()), default=None)
risk_levels = st.sidebar.multiselect("Risk Category", ["Low", "Medium", "High"], default=["Low", "Medium", "High"])

filtered = df.copy()
if regions:
    filtered = filtered[filtered["region"].isin(regions)]
if employment:
    filtered = filtered[filtered["employment_type"].isin(employment)]
if risk_levels:
    filtered = filtered[filtered["risk_category"].isin(risk_levels)]

# ------------------------------------------------------------------
# Header + KPI row
# ------------------------------------------------------------------
st.title("📊 Insurance & Lending Risk Analysis Dashboard")
st.caption("Customer, financial & claims risk profiling — regional segmentation, claim outcomes, and default risk KPIs")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Customers", f"{len(filtered):,}")
k2.metric("Overall Default Rate", f"{filtered['default_flag'].mean() * 100:.1f}%")
k3.metric("% High Risk", f"{(filtered['risk_category'] == 'High').mean() * 100:.1f}%")
k4.metric("Avg Risk Score", f"{filtered['risk_score'].mean():.1f} / 100")
k5.metric("Avg Debt-to-Income", f"{filtered['debt_to_income'].mean():.2f}")

st.divider()

# ------------------------------------------------------------------
# Row 1: Regional heatmap + risk mix
# ------------------------------------------------------------------
col1, col2 = st.columns([1.4, 1])

with col1:
    st.subheader("Regional Risk Segmentation")
    pivot = pd.crosstab(filtered["region"], filtered["risk_category"], normalize="index") * 100
    pivot = pivot.reindex(columns=["Low", "Medium", "High"])
    fig = px.imshow(
        pivot, text_auto=".1f", color_continuous_scale="YlOrRd",
        labels=dict(x="Risk Category", y="Region", color="% of region"),
        aspect="auto",
    )
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Customer Risk Mix")
    counts = filtered["risk_category"].value_counts().reindex(["Low", "Medium", "High"])
    fig = go.Figure(data=[go.Pie(
        labels=counts.index, values=counts.values, hole=0.45,
        marker=dict(colors=[RISK_COLORS[c] for c in counts.index]),
    )])
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# Row 2: Claims time series
# ------------------------------------------------------------------
st.subheader("Claim Value Over Time, by Claim Type")
cust_ids = set(filtered["customer_id"])
claims_f = claims[claims["customer_id"].isin(cust_ids)].dropna(subset=["claim_date"]).copy()
claims_f["month"] = claims_f["claim_date"].dt.to_period("M").dt.to_timestamp()
monthly = claims_f.groupby(["month", "claim_type"])["claim_amount"].sum().reset_index()

fig = px.line(
    monthly, x="month", y="claim_amount", color="claim_type", markers=True,
    labels={"month": "Month", "claim_amount": "Total Claim Value (£)", "claim_type": "Claim Type"},
)
fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# Row 3: Default rate by employment + claim status outcomes
# ------------------------------------------------------------------
col3, col4 = st.columns(2)

with col3:
    st.subheader("Default Rate by Employment Type")
    agg = filtered.groupby("employment_type").agg(
        default_rate=("default_flag", "mean"), n=("customer_id", "count")
    ).reset_index().sort_values("default_rate", ascending=False)
    agg["default_rate_pct"] = agg["default_rate"] * 100
    fig = px.bar(
        agg, x="employment_type", y="default_rate_pct", text="default_rate_pct",
        labels={"employment_type": "Employment Type", "default_rate_pct": "Default Rate (%)"},
        color="default_rate_pct", color_continuous_scale="Reds",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader("Claim Status Outcomes by Risk Category")
    claim_summary = filtered[filtered["claim_count"] > 0].groupby("risk_category", observed=True).agg(
        approved=("approved_claim_count", "sum"),
        rejected=("rejected_claim_count", "sum"),
    ).reset_index()
    claim_summary["other"] = (
        filtered[filtered["claim_count"] > 0].groupby("risk_category", observed=True)["claim_count"].sum().values
        - claim_summary["approved"] - claim_summary["rejected"]
    )
    melted = claim_summary.melt(id_vars="risk_category", value_vars=["approved", "rejected", "other"],
                                 var_name="outcome", value_name="count")
    fig = px.bar(
        melted, x="risk_category", y="count", color="outcome", barmode="stack",
        category_orders={"risk_category": ["Low", "Medium", "High"]},
        labels={"risk_category": "Risk Category", "count": "Claim Count"},
    )
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Highest-Risk Customers")
st.dataframe(
    filtered.sort_values("risk_score", ascending=False)[
        ["customer_id", "region", "employment_type", "credit_score",
         "debt_to_income", "claim_count", "risk_score", "risk_category", "default_flag"]
    ].head(25),
    use_container_width=True,
    hide_index=True,
)

st.caption("Data is synthetic and generated for portfolio/demo purposes — see data/raw/ and scripts/00_generate_dataset.py.")
