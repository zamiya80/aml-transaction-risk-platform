"""
Creates a concise periodic alert summary from the generated alert file.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

def create_summary():
    alerts = pd.read_csv(PROCESSED / "suspicious_alerts.csv")
    summary = (
        alerts.groupby(["risk_tier"])
        .agg(
            alert_count=("alert_id","count"),
            total_value=("amount","sum"),
            average_value=("amount","mean")
        )
        .reset_index()
    )
    summary["total_value"] = summary["total_value"].round(2)
    summary["average_value"] = summary["average_value"].round(2)
    summary.to_csv(REPORTS / "alert_summary.csv", index=False)
    print(summary)

if __name__ == "__main__":
    create_summary()
