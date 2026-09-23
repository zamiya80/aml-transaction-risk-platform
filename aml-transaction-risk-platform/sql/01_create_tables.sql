-- 01_create_tables.sql
-- PostgreSQL-compatible illustrative schema.
-- Raw CSV files can be loaded using COPY or an ETL tool.

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(150),
    customer_type VARCHAR(30),
    age INT,
    home_country VARCHAR(100),
    home_country_code CHAR(2),
    annual_income NUMERIC(14,2),
    account_open_date DATE,
    pep_flag INT,
    kyc_status VARCHAR(30)
);

CREATE TABLE banks (
    bank_id VARCHAR(20) PRIMARY KEY,
    bank_name VARCHAR(150),
    country_code CHAR(2),
    kyc_compliance_score NUMERIC(5,2),
    monitoring_status VARCHAR(30)
);

CREATE TABLE locations (
    location_id VARCHAR(20) PRIMARY KEY,
    country VARCHAR(100),
    country_code CHAR(2),
    country_risk_score INT
);

CREATE TABLE transactions (
    transaction_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) REFERENCES customers(customer_id),
    bank_id VARCHAR(20) REFERENCES banks(bank_id),
    transaction_datetime TIMESTAMP,
    transaction_type VARCHAR(50),
    channel VARCHAR(30),
    amount NUMERIC(14,2),
    currency CHAR(3),
    location_id VARCHAR(20) REFERENCES locations(location_id),
    counterparty_country CHAR(2),
    beneficiary_type VARCHAR(30),
    description VARCHAR(100)
);
