"""
02_load_to_sql.py
------------------------------------------------------------------
Loads the cleaned, feature-engineered dataset into a SQLite database
(database/risk_analysis.db) so the queries in sql/risk_analysis_queries.sql
can be run against it directly.

SQLite is used so the project is runnable end-to-end with zero setup;
the SQL in sql/risk_analysis_queries.sql is plain ANSI SQL and will run
unchanged against Postgres / MySQL / SQL Server if you point it at a
real warehouse instead.

Run:
    python scripts/02_load_to_sql.py
------------------------------------------------------------------
"""

import os
import sqlite3
import pandas as pd

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "risk_analysis.db")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    df = pd.read_csv(os.path.join(PROCESSED_DIR, "merged_risk_data.csv"))

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("customer_risk_profile", conn, index=False, if_exists="replace")

    conn.execute("CREATE INDEX idx_region ON customer_risk_profile(region);")
    conn.execute("CREATE INDEX idx_employment ON customer_risk_profile(employment_type);")
    conn.execute("CREATE INDEX idx_risk_category ON customer_risk_profile(risk_category);")
    conn.commit()

    n = conn.execute("SELECT COUNT(*) FROM customer_risk_profile;").fetchone()[0]
    print(f"Loaded {n:,} rows into {DB_PATH} (table: customer_risk_profile)")
    conn.close()
