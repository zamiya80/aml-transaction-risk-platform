"""
Feature engineering for transaction and customer risk monitoring.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

def build_features():
    tx = pd.read_csv(PROCESSED / "transactions_clean.csv", parse_dates=["transaction_datetime"])
    tx["date"] = tx["transaction_datetime"].dt.date

    customer_features = (
        tx.groupby("customer_id")
        .agg(
            transaction_count=("transaction_id", "count"),
            total_transaction_value=("amount", "sum"),
            average_transaction_value=("amount", "mean"),
            max_transaction_value=("amount", "max"),
            high_risk_country_tx_count=("country_risk_score", lambda s: int((s >= 4).sum())),
            average_country_risk=("country_risk_score", "mean"),
        )
        .reset_index()
    )

    customer_features["high_value_tx_count"] = (
        tx.groupby("customer_id")["amount"].apply(lambda s: int((s >= 10000).sum())).values
    )
    customer_features["velocity_24h"] = (
        tx.assign(transaction_datetime=tx["transaction_datetime"])
        .sort_values(["customer_id","transaction_datetime"])
        .groupby("customer_id")
        .apply(lambda g: max(
            [((g["transaction_datetime"] >= t - pd.Timedelta(hours=24)) &
              (g["transaction_datetime"] <= t)).sum() for t in g["transaction_datetime"]]
        ) if len(g) else 0, include_groups=False)
        .reindex(customer_features["customer_id"]).fillna(0).astype(int).values
    )

    customer_features["average_transaction_value"] = customer_features["average_transaction_value"].round(2)
    customer_features["average_country_risk"] = customer_features["average_country_risk"].round(2)

    customer_features.to_csv(PROCESSED / "customer_risk_features.csv", index=False)
    tx.to_csv(PROCESSED / "transaction_features.csv", index=False)
    print("Feature engineering complete.")

if __name__ == "__main__":
    build_features()
