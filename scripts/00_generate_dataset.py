"""
00_generate_dataset.py
------------------------------------------------------------------
Generates the raw, intentionally-messy source data for the
Insurance & Lending Risk Analysis & Predictive Modeling project:

    data/raw/customers_raw.csv    (20,500 records)
    data/raw/financials_raw.csv   (20,500 records)
    data/raw/claims_raw.csv       (~11,000 records)

The data is synthetic but internally consistent (customer_id is the
shared key) and is deliberately seeded with the kinds of anomalies a
real-world risk dataset would contain, so the cleaning stage in
01_data_cleaning_feature_engineering.py has real work to do:

  - negative / impossible incomes and claim amounts
  - out-of-range credit scores (negatives, >850, 0, nulls)
  - inconsistent categorical labels (e.g. "Male"/"M"/"male")
  - missing values scattered across columns
  - duplicate customer rows
  - inconsistent date formats
  - stray whitespace / casing issues in text fields

Run:
    python scripts/00_generate_dataset.py
------------------------------------------------------------------
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import os

SEED = 42
np.random.seed(SEED)
random.seed(SEED)

N_CUSTOMERS = 20500
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

REGIONS = [
    "London", "South East", "South West", "East of England",
    "West Midlands", "East Midlands", "North West", "North East",
    "Yorkshire and the Humber", "Scotland", "Wales", "Northern Ireland",
]
REGION_WEIGHTS = [0.20, 0.13, 0.08, 0.08, 0.09, 0.07, 0.10, 0.05, 0.07, 0.06, 0.04, 0.03]

EMPLOYMENT_TYPES = ["Employed", "Self-Employed", "Unemployed", "Retired", "Student"]
EMPLOYMENT_WEIGHTS = [0.55, 0.16, 0.08, 0.15, 0.06]

EDUCATION = ["High School", "Undergraduate", "Postgraduate", "Vocational", "None"]
MARITAL = ["Single", "Married", "Divorced", "Widowed"]

CLAIM_TYPES = ["Auto", "Home", "Health", "Life", "Travel"]
CLAIM_STATUS = ["Approved", "Rejected", "Pending", "Under Review"]


def messy_gender(g):
    """Return an inconsistently-formatted version of a gender label."""
    variants = {
        "Male": ["Male", "male", "M", " Male", "MALE"],
        "Female": ["Female", "female", "F", " Female", "FEMALE"],
        "Other": ["Other", "other", "O"],
    }
    return random.choice(variants[g])


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def format_messy_date(d):
    """Return a date string in one of several inconsistent formats."""
    fmt = random.choice(["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"])
    return d.strftime(fmt)


# ------------------------------------------------------------------
# 1. CUSTOMERS
# ------------------------------------------------------------------
def generate_customers(n):
    ids = np.arange(100000, 100000 + n)
    rows = []
    signup_start = datetime(2018, 1, 1)
    signup_end = datetime(2026, 8, 31)

    for cid in ids:
        age = int(np.clip(np.random.normal(41, 13), 18, 85))
        gender_clean = random.choices(["Male", "Female", "Other"], weights=[0.49, 0.49, 0.02])[0]
        gender = messy_gender(gender_clean)
        region = random.choices(REGIONS, weights=REGION_WEIGHTS)[0]
        employment_type = random.choices(EMPLOYMENT_TYPES, weights=EMPLOYMENT_WEIGHTS)[0]
        education = random.choices(EDUCATION, weights=[0.28, 0.32, 0.18, 0.16, 0.06])[0]
        marital_status = random.choices(MARITAL, weights=[0.38, 0.45, 0.13, 0.04])[0]

        # Credit score: mostly a realistic 300-850 range, with injected anomalies
        base_score = int(np.clip(np.random.normal(650, 90), 300, 850))
        credit_score = base_score
        anomaly_roll = random.random()
        if anomaly_roll < 0.02:
            credit_score = -abs(base_score)              # negative score
        elif anomaly_roll < 0.035:
            credit_score = base_score + 900               # out of range (>850)
        elif anomaly_roll < 0.045:
            credit_score = 0                              # zero / not scored
        elif anomaly_roll < 0.06:
            credit_score = np.nan                          # missing

        signup_date = random_date(signup_start, signup_end)

        rows.append({
            "customer_id": cid,
            "age": age,
            "gender": gender,
            "region": region,
            "employment_type": employment_type,
            "education_level": education,
            "marital_status": marital_status,
            "credit_score": credit_score,
            "signup_date": format_messy_date(signup_date),
        })

    df = pd.DataFrame(rows)

    # Inject missing values scattered across a few columns
    for col in ["age", "region", "employment_type", "marital_status"]:
        mask = df.sample(frac=0.01, random_state=SEED).index
        df.loc[mask, col] = np.nan

    # Inject ~1.5% duplicate customer rows (simulating a system export glitch)
    dup_rows = df.sample(frac=0.015, random_state=SEED)
    df = pd.concat([df, dup_rows], ignore_index=True)

    # Shuffle
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    return df


# ------------------------------------------------------------------
# 2. FINANCIALS
# ------------------------------------------------------------------
def generate_financials(customer_ids):
    rows = []
    open_start = datetime(2018, 1, 1)
    open_end = datetime(2026, 8, 31)

    for cid in customer_ids:
        base_income = np.random.lognormal(mean=10.3, sigma=0.45)  # ~£25k-£90k typical
        annual_income = round(base_income, 2)

        anomaly_roll = random.random()
        if anomaly_roll < 0.025:
            annual_income = -abs(annual_income)   # negative income
        elif anomaly_roll < 0.04:
            annual_income = np.nan                # missing income
        elif anomaly_roll < 0.05:
            annual_income = round(annual_income * 40, 2)  # absurd outlier (data-entry error, e.g. extra digit)

        monthly_debt_payment = round(max(0, np.random.normal(650, 400)), 2)
        if random.random() < 0.02:
            monthly_debt_payment = -abs(monthly_debt_payment)  # negative debt payment

        loan_amount = round(max(500, np.random.lognormal(mean=9.2, sigma=0.6)), 2)
        loan_term_months = random.choice([12, 24, 36, 48, 60, 84, 120, 180, 240, 300])
        existing_loans_count = np.random.poisson(1.1)
        account_open_date = format_messy_date(random_date(open_start, open_end))

        rows.append({
            "customer_id": cid,
            "annual_income": annual_income,
            "monthly_debt_payment": monthly_debt_payment,
            "loan_amount": loan_amount,
            "loan_term_months": loan_term_months,
            "existing_loans_count": existing_loans_count,
            "account_open_date": account_open_date,
        })

    df = pd.DataFrame(rows)

    # Missing values scattered
    for col in ["monthly_debt_payment", "loan_amount", "existing_loans_count"]:
        mask = df.sample(frac=0.012, random_state=SEED).index
        df.loc[mask, col] = np.nan

    return df


# ------------------------------------------------------------------
# 3. CLAIMS  (not every customer has one; some have several)
# ------------------------------------------------------------------
def generate_claims(customer_ids):
    rows = []
    claim_id = 500000
    claim_start = datetime(2019, 1, 1)
    claim_end = datetime(2026, 9, 1)

    # ~55% of customers have never claimed; the rest have 1-4 claims
    for cid in customer_ids:
        if random.random() < 0.55:
            continue
        n_claims = random.choices([1, 2, 3, 4], weights=[0.6, 0.25, 0.1, 0.05])[0]
        for _ in range(n_claims):
            claim_type = random.choices(CLAIM_TYPES, weights=[0.32, 0.24, 0.22, 0.10, 0.12])[0]
            status = random.choices(CLAIM_STATUS, weights=[0.55, 0.2, 0.12, 0.13])[0]

            base_amount = {
                "Auto": np.random.lognormal(7.3, 0.6),
                "Home": np.random.lognormal(7.8, 0.7),
                "Health": np.random.lognormal(6.6, 0.8),
                "Life": np.random.lognormal(9.0, 0.5),
                "Travel": np.random.lognormal(5.8, 0.6),
            }[claim_type]
            claim_amount = round(base_amount, 2)

            anomaly_roll = random.random()
            if anomaly_roll < 0.03:
                claim_amount = -abs(claim_amount)     # negative claim amount
            elif anomaly_roll < 0.045:
                claim_amount = np.nan                  # missing amount

            claim_date = format_messy_date(random_date(claim_start, claim_end))

            rows.append({
                "claim_id": claim_id,
                "customer_id": cid,
                "claim_date": claim_date,
                "claim_type": claim_type,
                "claim_amount": claim_amount,
                "claim_status": status,
            })
            claim_id += 1

    df = pd.DataFrame(rows)

    # A few duplicate claim rows (export glitch)
    dup_rows = df.sample(frac=0.01, random_state=SEED)
    df = pd.concat([df, dup_rows], ignore_index=True)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    return df


if __name__ == "__main__":
    customers_df = generate_customers(N_CUSTOMERS)
    unique_ids = customers_df["customer_id"].unique()

    financials_df = generate_financials(unique_ids)
    claims_df = generate_claims(unique_ids)

    customers_df.to_csv(os.path.join(OUT_DIR, "customers_raw.csv"), index=False)
    financials_df.to_csv(os.path.join(OUT_DIR, "financials_raw.csv"), index=False)
    claims_df.to_csv(os.path.join(OUT_DIR, "claims_raw.csv"), index=False)

    print(f"customers_raw.csv  : {len(customers_df):,} rows")
    print(f"financials_raw.csv : {len(financials_df):,} rows")
    print(f"claims_raw.csv     : {len(claims_df):,} rows")
    print(f"Total records      : {len(customers_df) + len(financials_df) + len(claims_df):,}")
