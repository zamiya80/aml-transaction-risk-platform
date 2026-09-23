-- 02_data_cleaning.sql

-- Check duplicate transaction IDs
SELECT transaction_id, COUNT(*) AS duplicate_count
FROM transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- Check orphaned customer references
SELECT t.customer_id
FROM transactions t
LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- Check invalid transaction values
SELECT *
FROM transactions
WHERE amount IS NULL OR amount <= 0;

-- Standardise/inspect KYC statuses
SELECT DISTINCT TRIM(kyc_status) AS kyc_status
FROM customers
ORDER BY 1;
