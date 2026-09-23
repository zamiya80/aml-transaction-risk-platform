-- 04_risk_analysis.sql

-- High-value transactions
SELECT *
FROM transactions
WHERE amount >= 10000
ORDER BY amount DESC;

-- Transactions involving higher-risk jurisdictions
SELECT
    t.transaction_id,
    t.customer_id,
    t.amount,
    l.country,
    l.country_risk_score
FROM transactions t
JOIN locations l ON t.location_id = l.location_id
WHERE l.country_risk_score >= 4
ORDER BY t.amount DESC;

-- Customers with elevated transaction volume
SELECT *
FROM customer_transaction_features
WHERE total_transaction_value >= 100000
   OR high_value_tx_count >= 3
ORDER BY total_transaction_value DESC;

-- Banks requiring review based on illustrative indicators
SELECT *
FROM bank_compliance_summary
WHERE kyc_compliance_score < 80
   OR monitoring_status = 'Review Required'
ORDER BY kyc_compliance_score;
