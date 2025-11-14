-- init_dwh.sql
CREATE SCHEMA IF NOT EXISTS ods;
CREATE SCHEMA IF NOT EXISTS dwh;

-- sample table to load from Oracle
CREATE TABLE IF NOT EXISTS ods.transactions (
  tx_id bigint PRIMARY KEY,
  account_no varchar(64),
  amount numeric(18,2),
  tx_time timestamptz,
  source_system varchar(64)
);

-- star schema sample
CREATE TABLE IF NOT EXISTS dwh.dim_account (
  account_id serial PRIMARY KEY,
  account_no varchar(64) UNIQUE,
  customer_name text
);

CREATE TABLE IF NOT EXISTS dwh.fact_transactions (
  fact_id bigserial PRIMARY KEY,
  tx_id bigint,
  account_id int,
  amount numeric(18,2),
  tx_time timestamptz
);