-- 03_feature_engineering.sql

-- Customer transaction profile
CREATE VIEW customer_transaction_features AS
SELECT
    c.customer_id,
    c.customer_type,
    c.pep_flag,
    c.kyc_status,
    COUNT(t.transaction_id) AS transaction_count,
    SUM(t.amount) AS total_transaction_value,
    AVG(t.amount) AS average_transaction_value,
    MAX(t.amount) AS maximum_transaction_value,
    SUM(CASE WHEN t.amount >= 10000 THEN 1 ELSE 0 END) AS high_value_tx_count,
    SUM(CASE WHEN l.country_risk_score >= 4 THEN 1 ELSE 0 END) AS high_risk_country_tx_count,
    AVG(l.country_risk_score) AS average_country_risk
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
LEFT JOIN locations l ON t.location_id = l.location_id
GROUP BY
    c.customer_id, c.customer_type, c.pep_flag, c.kyc_status;

-- Bank-level compliance indicators
CREATE VIEW bank_compliance_summary AS
SELECT
    b.bank_id,
    b.bank_name,
    b.kyc_compliance_score,
    b.monitoring_status,
    COUNT(t.transaction_id) AS transaction_count,
    SUM(CASE WHEN t.amount >= 10000 THEN 1 ELSE 0 END) AS high_value_transactions
FROM banks b
LEFT JOIN transactions t ON b.bank_id = t.bank_id
GROUP BY
    b.bank_id, b.bank_name, b.kyc_compliance_score, b.monitoring_status;
