"""
Data preparation for the AML transaction-risk project.
Uses only synthetic portfolio data.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

def clean_data():
    customers = pd.read_csv(RAW / "customers.csv", parse_dates=["account_open_date"])
    transactions = pd.read_csv(RAW / "transactions.csv", parse_dates=["transaction_datetime"])
    banks = pd.read_csv(RAW / "banks.csv")
    locations = pd.read_csv(RAW / "locations.csv")

    customers.columns = customers.columns.str.strip().str.lower()
    transactions.columns = transactions.columns.str.strip().str.lower()

    transactions["amount"] = pd.to_numeric(transactions["amount"], errors="coerce")
    transactions = transactions.dropna(subset=["transaction_id", "customer_id", "amount"])
    transactions = transactions[transactions["amount"] > 0].drop_duplicates("transaction_id")

    customers["customer_type"] = customers["customer_type"].str.strip().str.title()
    customers["kyc_status"] = customers["kyc_status"].str.strip().str.title()

    transactions = transactions.merge(
        locations[["location_id", "country_risk_score"]],
        on="location_id", how="left"
    )
    transactions = transactions.merge(
        customers[["customer_id", "home_country_code", "pep_flag", "kyc_status"]],
        on="customer_id", how="left"
    )

    customers.to_csv(PROCESSED / "customers_clean.csv", index=False)
    banks.to_csv(PROCESSED / "banks_clean.csv", index=False)
    locations.to_csv(PROCESSED / "locations_clean.csv", index=False)
    transactions.to_csv(PROCESSED / "transactions_clean.csv", index=False)

    print(f"Saved {len(transactions):,} cleaned transactions.")

if __name__ == "__main__":
    clean_data()
