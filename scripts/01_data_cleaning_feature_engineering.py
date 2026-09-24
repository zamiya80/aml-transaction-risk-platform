"""
01_data_cleaning_feature_engineering.py
------------------------------------------------------------------
Cleans the three raw source files and engineers the analytical
features used throughout the rest of the project.

Cleaning steps:
  - Standardise gender / date / categorical formatting
  - Remove exact duplicate customer & claim rows
  - Null-out / correct impossible values (negative incomes, negative
    claim amounts, out-of-range credit scores) rather than silently
    dropping records, then impute or flag as appropriate
  - Parse mixed-format date strings into a single ISO format

Feature engineering:
  - debt_to_income        : (monthly_debt_payment * 12) / annual_income
  - claim_count            : claims per customer
  - total_claim_amount     : sum of claim amounts per customer
  - has_high_value_claim   : flag for any single claim > 90th percentile
  - risk_score              : weighted composite of credit score, DTI,
                              employment type and claim history
  - risk_category           : Low / Medium / High, binned from risk_score
  - default_flag            : synthetic target label for the predictive
                              model (see 05_predictive_model.py), derived
                              from risk_score with realistic noise

Output:
  data/processed/merged_risk_data.csv
------------------------------------------------------------------
"""

import os
import numpy as np
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

SEED = 42
np.random.seed(SEED)


def parse_mixed_dates(series):
    """Parse a column containing several different date string formats."""
    return pd.to_datetime(series, dayfirst=True, errors="coerce", format="mixed")


def clean_customers(path):
    df = pd.read_csv(path)

    # Standardise gender labels
    df["gender"] = (
        df["gender"].astype(str).str.strip().str.lower()
        .map({"male": "Male", "m": "Male", "female": "Female", "f": "Female",
              "other": "Other", "o": "Other"})
    )

    # Standardise text categorical columns
    for col in ["region", "employment_type", "education_level", "marital_status"]:
        df[col] = df[col].astype(str).str.strip()
        df.loc[df[col].isin(["nan", "None", ""]), col] = np.nan

    # Parse signup_date (mixed formats)
    df["signup_date"] = parse_mixed_dates(df["signup_date"])

    # Drop exact duplicate rows (same customer_id + identical attributes)
    df = df.drop_duplicates(subset="customer_id", keep="first")

    # Age: clip to plausible adult range, null out anything impossible
    df.loc[(df["age"] < 18) | (df["age"] > 100), "age"] = np.nan
    df["age"] = df["age"].fillna(df["age"].median())

    # Credit score: null-out impossible values (outside 300-850, or 0 =
    # "not yet scored"), then impute the remainder with the column median
    # so downstream numeric features stay usable — imputed rows are
    # flagged for transparency.
    df["credit_score_was_invalid"] = ~df["credit_score"].between(300, 850)
    df.loc[df["credit_score_was_invalid"], "credit_score"] = np.nan
    median_score = df["credit_score"].median()
    df["credit_score"] = df["credit_score"].fillna(median_score)

    # Fill remaining categorical nulls with an explicit "Unknown" bucket
    # rather than dropping the record (preserves sample size for the
    # financials/claims joins).
    for col in ["region", "employment_type", "education_level", "marital_status"]:
        df[col] = df[col].fillna("Unknown")

    return df


def clean_financials(path):
    df = pd.read_csv(path)

    df["account_open_date"] = parse_mixed_dates(df["account_open_date"])

    # Negative or missing income: null-out negatives, then impute
    # missing/negative income with the median income for that record's
    # loan-term bracket (a reasonable proxy absent other signal).
    df["income_was_invalid"] = (df["annual_income"] < 0) | df["annual_income"].isna()
    df.loc[df["annual_income"] < 0, "annual_income"] = np.nan

    # Cap absurd outliers (data-entry "extra digit" errors) at the 99th percentile
    cap = df["annual_income"].quantile(0.99)
    df.loc[df["annual_income"] > cap, "annual_income"] = cap

    median_income = df["annual_income"].median()
    df["annual_income"] = df["annual_income"].fillna(median_income)

    # Negative debt payments are a sign error -> take absolute value
    df["monthly_debt_payment"] = df["monthly_debt_payment"].abs()
    df["monthly_debt_payment"] = df["monthly_debt_payment"].fillna(
        df["monthly_debt_payment"].median()
    )

    df["loan_amount"] = df["loan_amount"].fillna(df["loan_amount"].median())
    df["existing_loans_count"] = df["existing_loans_count"].fillna(0).astype(int)

    return df


def clean_claims(path):
    df = pd.read_csv(path)
    df = df.drop_duplicates(subset="claim_id", keep="first")

    df["claim_date"] = parse_mixed_dates(df["claim_date"])

    # Negative claim amounts are a sign error -> take absolute value;
    # missing amounts are imputed with the median for that claim_type
    # (claim size varies a lot by type, so a global median would be misleading).
    df["claim_amount"] = df["claim_amount"].abs()
    df["claim_amount"] = df.groupby("claim_type")["claim_amount"].transform(
        lambda s: s.fillna(s.median())
    )

    df["claim_status"] = df["claim_status"].astype(str).str.strip()
    return df


def engineer_features(customers, financials, claims):
    # --- merge customer + financial profile ---
    merged = customers.merge(financials, on="customer_id", how="left")

    # debt-to-income ratio (annual debt / annual income)
    merged["debt_to_income"] = (
        (merged["monthly_debt_payment"] * 12) / merged["annual_income"]
    ).round(3)
    merged["debt_to_income"] = merged["debt_to_income"].clip(upper=5)  # cap runaway ratios

    # --- claim history aggregates per customer ---
    claim_agg = claims.groupby("customer_id").agg(
        claim_count=("claim_id", "count"),
        total_claim_amount=("claim_amount", "sum"),
        avg_claim_amount=("claim_amount", "mean"),
        approved_claim_count=("claim_status", lambda s: (s == "Approved").sum()),
        rejected_claim_count=("claim_status", lambda s: (s == "Rejected").sum()),
    ).reset_index()

    merged = merged.merge(claim_agg, on="customer_id", how="left")
    for col in ["claim_count", "total_claim_amount", "avg_claim_amount",
                "approved_claim_count", "rejected_claim_count"]:
        merged[col] = merged[col].fillna(0)

    high_value_threshold = claims["claim_amount"].quantile(0.90)
    hv_customers = set(claims.loc[claims["claim_amount"] > high_value_threshold, "customer_id"])
    merged["has_high_value_claim"] = merged["customer_id"].isin(hv_customers).astype(int)

    # --- composite risk score (0-100, higher = riskier) ---
    # Normalise each driver to 0-1 then weight it.
    credit_component = 1 - (merged["credit_score"] - 300) / (850 - 300)          # lower score = higher risk
    dti_component = (merged["debt_to_income"] / merged["debt_to_income"].clip(upper=1).max()).clip(0, 1)
    claim_component = (merged["claim_count"] / merged["claim_count"].replace(0, np.nan).quantile(0.95)).clip(0, 1).fillna(0)
    employment_risk_map = {
        "Unemployed": 1.0, "Student": 0.6, "Self-Employed": 0.5,
        "Employed": 0.25, "Retired": 0.35, "Unknown": 0.5,
    }
    employment_component = merged["employment_type"].map(employment_risk_map).fillna(0.5)

    merged["risk_score"] = (
        credit_component * 40 +
        dti_component * 25 +
        claim_component * 20 +
        employment_component * 15
    ).round(2)

    # Percentile-based bins (bottom 50% = Low, next 35% = Medium, top 15% =
    # High) rather than fixed score thresholds — keeps the segmentation
    # meaningful regardless of how the underlying score distribution shifts.
    low_cut = merged["risk_score"].quantile(0.50)
    med_cut = merged["risk_score"].quantile(0.85)
    merged["risk_category"] = pd.cut(
        merged["risk_score"],
        bins=[-0.1, low_cut, med_cut, 100],
        labels=["Low", "Medium", "High"],
    )

    # --- synthetic default flag (target variable for predictive model) ---
    # Logistic function of risk_score plus noise, so it's realistically
    # correlated with risk but not perfectly deterministic.
    rng = np.random.default_rng(SEED)
    z = (merged["risk_score"] - 55) / 12
    prob_default = 1 / (1 + np.exp(-z))
    merged["default_flag"] = (rng.random(len(merged)) < prob_default).astype(int)

    return merged


if __name__ == "__main__":
    customers = clean_customers(os.path.join(RAW_DIR, "customers_raw.csv"))
    financials = clean_financials(os.path.join(RAW_DIR, "financials_raw.csv"))
    claims = clean_claims(os.path.join(RAW_DIR, "claims_raw.csv"))

    merged = engineer_features(customers, financials, claims)

    out_path = os.path.join(PROCESSED_DIR, "merged_risk_data.csv")
    merged.to_csv(out_path, index=False)

    print(f"Cleaned customers   : {len(customers):,} rows")
    print(f"Cleaned financials  : {len(financials):,} rows")
    print(f"Cleaned claims      : {len(claims):,} rows")
    print(f"Merged risk dataset : {len(merged):,} rows -> {out_path}")
    print()
    print("Risk category distribution:")
    print(merged["risk_category"].value_counts())
    print()
    print("Default rate overall: {:.2%}".format(merged["default_flag"].mean()))
