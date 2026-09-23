"""
Rule-based transaction monitoring engine.

Rules are illustrative portfolio rules, not a production AML model.
Each flagged transaction receives reasons and a risk score.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

def run_rules():
    tx = pd.read_csv(PROCESSED / "transactions_clean.csv", parse_dates=["transaction_datetime"])
    tx = tx.sort_values(["customer_id", "transaction_datetime"]).copy()

    # Rule 1: high-value transaction
    tx["rule_high_value"] = tx["amount"] >= 10000

    # Rule 2: structuring / near-threshold cash deposits
    tx["rule_structuring"] = (
        tx["transaction_type"].eq("Cash Deposit") &
        tx["amount"].between(7000, 9999.99)
    )

    # Rule 3: high-risk jurisdiction
    tx["rule_high_risk_country"] = tx["country_risk_score"] >= 4

    # Rule 4: rapid transaction velocity
    tx["tx_count_1h"] = (
        tx.set_index("transaction_datetime")
          .groupby("customer_id")["transaction_id"]
          .rolling("1h").count()
          .reset_index(level=0, drop=True)
          .reindex(tx.set_index("transaction_datetime").index)
    )
    # Recompute robustly by original row order
    tx["tx_count_1h"] = 0
    for customer, idx in tx.groupby("customer_id").groups.items():
        g = tx.loc[idx].sort_values("transaction_datetime")
        times = g["transaction_datetime"].tolist()
        counts = []
        left = 0
        for right, t in enumerate(times):
            while left <= right and t - times[left] > pd.Timedelta(hours=1):
                left += 1
            counts.append(right - left + 1)
        tx.loc[g.index, "tx_count_1h"] = counts
    tx["rule_velocity"] = tx["tx_count_1h"] >= 8

    # Rule 5: PEP + elevated transaction
    tx["rule_pep"] = (tx["pep_flag"] == 1) & (tx["amount"] >= 5000)

    rules = [
        "rule_high_value", "rule_structuring", "rule_high_risk_country",
        "rule_velocity", "rule_pep"
    ]
    weights = {
        "rule_high_value": 25,
        "rule_structuring": 30,
        "rule_high_risk_country": 20,
        "rule_velocity": 25,
        "rule_pep": 20
    }

    tx["risk_score"] = sum(tx[r].astype(int) * weights[r] for r in rules)
    tx["alert_flag"] = tx["risk_score"] >= 30

    def reasons(row):
        mapping = {
            "rule_high_value": "High-value transaction",
            "rule_structuring": "Near-threshold cash deposit",
            "rule_high_risk_country": "High-risk jurisdiction",
            "rule_velocity": "Unusually high transaction velocity",
            "rule_pep": "PEP with elevated transaction",
        }
        return "; ".join(mapping[r] for r in rules if row[r])

    tx["alert_reasons"] = tx.apply(reasons, axis=1)
    tx["risk_tier"] = pd.cut(
        tx["risk_score"],
        bins=[-1, 19, 39, 69, 999],
        labels=["Low", "Medium", "High", "Critical"]
    )

    alerts = tx[tx["alert_flag"]].copy()
    alerts["alert_id"] = [f"A{i:06d}" for i in range(1, len(alerts)+1)]

    alerts_cols = [
        "alert_id","transaction_id","customer_id","bank_id",
        "transaction_datetime","amount","transaction_type",
        "counterparty_country","risk_score","risk_tier","alert_reasons"
    ]
    alerts[alerts_cols].to_csv(REPORTS / "sample_alert_report.csv", index=False)
    alerts[alerts_cols].to_csv(PROCESSED / "suspicious_alerts.csv", index=False)

    print(f"Generated {len(alerts):,} alerts from {len(tx):,} transactions.")

if __name__ == "__main__":
    run_rules()
