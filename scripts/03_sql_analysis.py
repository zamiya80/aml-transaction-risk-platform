"""
03_sql_analysis.py
------------------------------------------------------------------
Runs the analysis queries from sql/risk_analysis_queries.sql against
database/risk_analysis.db and saves each result to
outputs/sql_query_results/ as a CSV (used by the README and the
dashboard). The query text below is kept identical to the .sql file
so the two stay in sync -- sql/risk_analysis_queries.sql remains the
canonical, human-readable / portable copy.

Run:
    python scripts/03_sql_analysis.py
------------------------------------------------------------------
"""

import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(BASE_DIR, "database", "risk_analysis.db")
OUT_DIR = os.path.join(BASE_DIR, "outputs", "sql_query_results")

QUERIES = {
    "regional_risk_segmentation.csv": """
        SELECT
            region,
            COUNT(*)                                                   AS total_customers,
            ROUND(AVG(risk_score), 2)                                  AS avg_risk_score,
            SUM(CASE WHEN risk_category = 'Low'    THEN 1 ELSE 0 END)  AS low_risk_count,
            SUM(CASE WHEN risk_category = 'Medium' THEN 1 ELSE 0 END)  AS medium_risk_count,
            SUM(CASE WHEN risk_category = 'High'   THEN 1 ELSE 0 END)  AS high_risk_count,
            ROUND(100.0 * SUM(CASE WHEN risk_category = 'High' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_high_risk
        FROM customer_risk_profile
        GROUP BY region
        ORDER BY pct_high_risk DESC;
    """,
    "claim_status_high_risk.csv": """
        SELECT
            risk_category,
            SUM(claim_count)                                            AS total_claims,
            SUM(approved_claim_count)                                   AS approved_claims,
            SUM(rejected_claim_count)                                   AS rejected_claims,
            ROUND(100.0 * SUM(approved_claim_count) / NULLIF(SUM(claim_count), 0), 2) AS approval_rate_pct,
            ROUND(100.0 * SUM(rejected_claim_count) / NULLIF(SUM(claim_count), 0), 2) AS rejection_rate_pct,
            ROUND(AVG(avg_claim_amount), 2)                              AS avg_claim_value
        FROM customer_risk_profile
        WHERE claim_count > 0
        GROUP BY risk_category
        ORDER BY CASE risk_category WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;
    """,
    "default_rates_employment.csv": """
        SELECT
            employment_type,
            COUNT(*)                                                    AS total_customers,
            SUM(default_flag)                                           AS total_defaults,
            ROUND(100.0 * SUM(default_flag) / COUNT(*), 2)              AS default_rate_pct,
            ROUND(AVG(risk_score), 2)                                   AS avg_risk_score,
            ROUND(AVG(debt_to_income), 3)                                AS avg_debt_to_income
        FROM customer_risk_profile
        GROUP BY employment_type
        ORDER BY default_rate_pct DESC;
    """,
    "core_risk_kpi_summary.csv": """
        SELECT
            COUNT(*)                                                    AS total_customers,
            ROUND(100.0 * SUM(default_flag) / COUNT(*), 2)              AS overall_default_rate_pct,
            ROUND(100.0 * SUM(CASE WHEN risk_category = 'High' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_high_risk_customers,
            ROUND(AVG(risk_score), 2)                                   AS avg_risk_score,
            ROUND(AVG(debt_to_income), 3)                                AS avg_debt_to_income,
            ROUND(SUM(total_claim_amount), 2)                            AS total_claims_paid_value
        FROM customer_risk_profile;
    """,
    "top10_highest_risk_customers.csv": """
        SELECT
            customer_id, region, employment_type, credit_score,
            debt_to_income, claim_count, risk_score, risk_category, default_flag
        FROM customer_risk_profile
        ORDER BY risk_score DESC
        LIMIT 10;
    """,
}

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    for filename, stmt in QUERIES.items():
        result = pd.read_sql_query(stmt, conn)
        out_path = os.path.join(OUT_DIR, filename)
        result.to_csv(out_path, index=False)
        print(f"-> {filename}  ({len(result)} rows)")
        print(result.to_string(index=False))
        print()

    conn.close()
