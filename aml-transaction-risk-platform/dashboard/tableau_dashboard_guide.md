# Tableau Dashboard Guide

## Dashboard objective
Create an interactive AML and transaction-risk monitoring dashboard from the processed CSV files.

## Recommended data sources
- `data/processed/transactions_clean.csv`
- `data/processed/suspicious_alerts.csv`
- `data/processed/customer_risk.csv`
- `data/raw/banks.csv`
- `data/raw/locations.csv`

## Suggested dashboard sheets
1. **Risk Overview**
   - Total transaction value
   - Transaction count
   - Alert count
   - High/Critical customer count
2. **Regional Risk**
   - Map by country/location
   - Transaction value
   - Alert count
   - Average country risk score
3. **Customer Risk**
   - Customer risk tier distribution
   - Top customers by risk score
   - Transaction value by customer type
4. **Alert Monitoring**
   - Alerts over time
   - Risk tier
   - Alert reason
   - Transaction amount
5. **Bank Compliance**
   - KYC compliance score by bank
   - Monitoring status
   - High-value transaction volume

## Suggested filters
- Transaction date
- Bank
- Customer type
- Risk tier
- Transaction type
- Country
- Alert reason

## Important note
This project uses synthetic data and illustrative rules. The rule thresholds are portfolio examples and should not be treated as regulatory thresholds or production AML controls.
