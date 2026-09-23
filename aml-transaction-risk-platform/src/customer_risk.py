"""
Customer risk scoring using transaction behaviour and KYC indicators.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

def score_customers():
    features = pd.read_csv(PROCESSED / "customer_risk_features.csv")
    customers = pd.read_csv(PROCESSED / "customers_clean.csv")

    df = features.merge(
        customers[["customer_id","pep_flag","kyc_status","customer_type"]],
        on="customer_id", how="left"
    )

    score = (
        (df["total_transaction_value"] >= 100000).astype(int) * 20 +
        (df["average_country_risk"] >= 3).astype(int) * 20 +
        (df["high_value_tx_count"] >= 3).astype(int) * 20 +
        (df["velocity_24h"] >= 8).astype(int) * 20 +
        (df["pep_flag"] == 1).astype(int) * 15 +
        (df["kyc_status"] == "Review Required").astype(int) * 10
    )

    df["customer_risk_score"] = score
    df["customer_risk_tier"] = pd.cut(
        df["customer_risk_score"],
        bins=[-1, 19, 39, 69, 999],
        labels=["Low", "Medium", "High", "Critical"]
    )
    df.to_csv(PROCESSED / "customer_risk.csv", index=False)
    print("Customer risk scoring complete.")

if __name__ == "__main__":
    score_customers()
