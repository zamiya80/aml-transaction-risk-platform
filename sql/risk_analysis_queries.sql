-- ==================================================================
-- risk_analysis_queries.sql
-- Insurance & Lending Risk Analysis & Predictive Modeling
--
-- Runs against the `customer_risk_profile` table produced by
-- scripts/02_load_to_sql.py (database/risk_analysis.db, SQLite).
-- Plain ANSI SQL — portable to Postgres / MySQL / SQL Server.
-- ==================================================================


-- ------------------------------------------------------------------
-- 1. REGIONAL RISK SEGMENTATION
-- Customer count and risk mix by region, plus an average risk score,
-- so regions can be ranked by concentration of high-risk customers.
-- ------------------------------------------------------------------
SELECT
    region,
    COUNT(*)                                                   AS total_customers,
    ROUND(AVG(risk_score), 2)                                  AS avg_risk_score,
    SUM(CASE WHEN risk_category = 'Low'    THEN 1 ELSE 0 END)  AS low_risk_count,
    SUM(CASE WHEN risk_category = 'Medium' THEN 1 ELSE 0 END)  AS medium_risk_count,
    SUM(CASE WHEN risk_category = 'High'   THEN 1 ELSE 0 END)  AS high_risk_count,
    ROUND(
        100.0 * SUM(CASE WHEN risk_category = 'High' THEN 1 ELSE 0 END) / COUNT(*), 2
    )                                                           AS pct_high_risk
FROM customer_risk_profile
GROUP BY region
ORDER BY pct_high_risk DESC;


-- ------------------------------------------------------------------
-- 2. CLAIM STATUS OUTCOMES FOR HIGH-RISK PROFILES
-- Among customers flagged High risk, how do their claims resolve?
-- (approved / rejected counts and rates, plus average claim value)
-- ------------------------------------------------------------------
SELECT
    risk_category,
    SUM(claim_count)                                            AS total_claims,
    SUM(approved_claim_count)                                   AS approved_claims,
    SUM(rejected_claim_count)                                   AS rejected_claims,
    ROUND(
        100.0 * SUM(approved_claim_count) / NULLIF(SUM(claim_count), 0), 2
    )                                                            AS approval_rate_pct,
    ROUND(
        100.0 * SUM(rejected_claim_count) / NULLIF(SUM(claim_count), 0), 2
    )                                                            AS rejection_rate_pct,
    ROUND(AVG(avg_claim_amount), 2)                              AS avg_claim_value
FROM customer_risk_profile
WHERE claim_count > 0
GROUP BY risk_category
ORDER BY
    CASE risk_category WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;


-- ------------------------------------------------------------------
-- 3. DEFAULT RATES ACROSS EMPLOYMENT TYPES
-- Default rate and average risk score by employment type, ordered
-- riskiest-first.
-- ------------------------------------------------------------------
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


-- ------------------------------------------------------------------
-- 4. (Supporting) CORE RISK KPI SUMMARY
-- The headline numbers for the dashboard's KPI tracker row.
-- ------------------------------------------------------------------
SELECT
    COUNT(*)                                                    AS total_customers,
    ROUND(100.0 * SUM(default_flag) / COUNT(*), 2)              AS overall_default_rate_pct,
    ROUND(
        100.0 * SUM(CASE WHEN risk_category = 'High' THEN 1 ELSE 0 END) / COUNT(*), 2
    )                                                            AS pct_high_risk_customers,
    ROUND(AVG(risk_score), 2)                                   AS avg_risk_score,
    ROUND(AVG(debt_to_income), 3)                                AS avg_debt_to_income,
    ROUND(SUM(total_claim_amount), 2)                            AS total_claims_paid_value
FROM customer_risk_profile;


-- ------------------------------------------------------------------
-- 5. (Supporting) TOP 10 HIGHEST-RISK CUSTOMERS
-- Drill-down list for underwriting review.
-- ------------------------------------------------------------------
SELECT
    customer_id, region, employment_type, credit_score,
    debt_to_income, claim_count, risk_score, risk_category, default_flag
FROM customer_risk_profile
ORDER BY risk_score DESC
LIMIT 10;
