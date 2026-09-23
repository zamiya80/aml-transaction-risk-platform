# Integrated AML & Transaction Risk Platform

An end-to-end portfolio project demonstrating **transaction monitoring, rule-based fraud detection, customer risk profiling, and compliance analytics** using Python, Pandas, SQL, and Tableau.

> **Data notice:** All datasets in this repository are synthetic and generated for educational/portfolio purposes. No real customer, banking, or personally identifiable financial data is included.

## Project objective

Build an integrated analytical workflow that can:
- consolidate transaction, customer, bank, and geographic-risk data;
- engineer transaction- and customer-level risk indicators;
- identify potentially suspicious transaction patterns using transparent rules;
- produce investigation-oriented alert reports; and
- visualise risk and compliance indicators in Tableau.

## Technology stack

- **Python** — data preparation, feature engineering and rule-based monitoring
- **Pandas / NumPy** — data manipulation and analysis
- **SQL** — relational modelling, cleaning, joins and risk analysis
- **Tableau** — interactive risk and compliance dashboards

## Project workflow

```text
Raw datasets
     |
     v
SQL data model + validation
     |
     v
Python cleaning & feature engineering
     |
     +----------------------+
     |                      |
     v                      v
Customer risk scoring   Transaction rules
     |                      |
     +----------+-----------+
                |
                v
        Suspicious alerts
                |
                v
       Tableau risk dashboard
```

## Repository structure

```text
aml-transaction-risk-platform/
├── data/
│   ├── raw/
│   └── processed/
├── sql/
├── src/
├── reports/
├── dashboard/
├── notebooks/
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

## Dataset overview

| Dataset | Description |
|---|---|
| `customers.csv` | Synthetic customer profiles, KYC status and PEP indicators |
| `transactions.csv` | Synthetic transaction-level activity |
| `banks.csv` | Synthetic bank compliance indicators |
| `locations.csv` | Synthetic geographic risk scores |
| `suspicious_alerts.csv` | Transactions flagged by illustrative monitoring rules |
| `customer_risk.csv` | Customer-level risk scoring output |

## Illustrative monitoring rules

The Python monitoring engine includes transparent example rules:

1. **High-value transaction** — flags transactions at or above £10,000.
2. **Near-threshold cash deposit** — flags cash deposits between £7,000 and £9,999.99 as an illustrative structuring scenario.
3. **High-risk jurisdiction** — flags transactions associated with locations assigned a synthetic risk score of 4 or 5.
4. **High transaction velocity** — flags customers with unusually frequent transactions within a one-hour window.
5. **PEP + elevated transaction** — flags transactions of £5,000 or more for customers with a synthetic PEP indicator.

These rules are **illustrative portfolio logic**, not regulatory thresholds or a production AML system.

## Running the project

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run data preparation

```bash
python src/data_cleaning.py
```

### 3. Build analytical features

```bash
python src/feature_engineering.py
```

### 4. Generate transaction alerts

```bash
python src/fraud_detection.py
```

### 5. Score customers

```bash
python src/customer_risk.py
```

### 6. Generate alert summary

```bash
python src/generate_alert_report.py
```

The resulting files will be written to `data/processed/` and `reports/`.

## SQL

The SQL folder demonstrates:
- relational table design;
- primary and foreign keys;
- data-quality checks;
- customer transaction aggregation;
- bank compliance analysis; and
- risk-oriented analytical queries.

The scripts are written in a PostgreSQL-compatible style.

## Tableau dashboard

Use the processed CSV files as Tableau data sources.

Recommended dashboard areas:
- **Risk Overview**
- **Regional Risk Hotspots**
- **Customer Risk Tiers**
- **Transaction Alerts**
- **Bank Compliance**

See [`dashboard/tableau_dashboard_guide.md`](dashboard/tableau_dashboard_guide.md) for the suggested dashboard design.

## Key portfolio outcomes

This project demonstrates an end-to-end data analytics workflow:

- Multi-source data integration
- Data cleaning and validation
- Relational SQL modelling
- Feature engineering
- Rule-based transaction monitoring
- Customer risk scoring
- Suspicious activity alert generation
- Compliance analytics
- Interactive Tableau reporting

## Limitations

This is a portfolio demonstration rather than a production AML solution. Real-world deployment would require, among other things:
- institution-specific policies and regulatory requirements;
- documented model/rule governance;
- threshold calibration and validation;
- sanctions and PEP data from appropriate sources;
- case-management workflows;
- audit trails and access controls;
- false-positive analysis;
- ongoing monitoring and periodic rule review.

## Author

Add your name, LinkedIn profile and portfolio/GitHub links here.

## License

Released under the MIT License. See `LICENSE`.
