# Assessment 3 - Overview

## Scenario

A bank is preparing a regulatory submission based on customer transaction data. Regulatory Reporting identifies that transaction volumes shown in the regulatory reporting mart do not match Transaction Banking records. Management requires an investigation demonstrating Source -> Bronze -> Reporting dataset lineage and reconciliation. Four datasets are available: a payment-transaction source feed, its Bronze copy, a customer reference table, and the regulatory reporting mart itself.

>DISCLAIMER: Scaled down mock demo

The assignment's reconciliation matrix example states production-scale row counts in the low millions per dimension (e.g. 2,510,442 SG Payments), and its performance question poses a 5-billion-row Bronze table against a 40-minute reconciliation-query baseline. This demo's seeded volume budget is far smaller by design (`MOCK_DATA_PAYMENTS_PER_DAY=400`, `MOCK_DATA_CUSTOMERS=300`, `MOCK_DATA_DAYS=5`), producing 2,005 `source.payment_transactions` rows, 2,025 `bronze.payment_transactions` rows, 315 `bronze.customer_master` rows, and 2,021 `regulatory.payment_reporting` rows for the most recent seed run. Every measurement published in this assessment's deliverables is a finding against that seeded volume, with the assignment's production-scale figures cited here only as the scenario framing that motivated the check - never mistaken for a production-scale result, and never a target the seeded data is expected to reproduce exactly.

## Source Payments dataset - `source.payment_transactions`

| column              | description                             |
| -------------------- | ---------------------------------------- |
| payment_id           | unique payment identifier                |
| customer_id          | customer identifier                      |
| account_id           | debited/credited account identifier      |
| payment_date         | business payment date                    |
| payment_timestamp    | payment processing timestamp             |
| payment_type         | WIRE / GIRO / CARD / INTERNAL / INSTANT  |
| payment_channel      | BRANCH / MOBILE / INTERNET / API         |
| beneficiary_country  | beneficiary country, ISO 3166-1 alpha-2  |
| currency             | ISO currency                             |
| amount               | payment amount                           |
| status               | COMPLETED / PENDING / FAILED / REJECTED  |
| legal_entity         | booking legal entity                     |

## Bronze Payments dataset - `bronze.payment_transactions`

Same business fields as source, plus:

| column               | description                       |
| --------------------- | ---------------------------------- |
| ingestion_timestamp   | Bronze ingestion timestamp         |
| batch_id              | ingestion batch identifier         |
| record_hash           | hash of the row's business fields  |
| source_file_name      | source file this row loaded from   |

## Customer Reference dataset - `bronze.customer_master`

| column                | description                                 |
| ---------------------- | -------------------------------------------- |
| customer_id            | customer identifier                          |
| customer_type          | INDIVIDUAL / CORPORATE                       |
| residence_country      | residence country, ISO 3166-1 alpha-2        |
| risk_rating            | LOW / MEDIUM / HIGH                          |
| segment                | RETAIL / PRIVATE / CORPORATE / SME           |
| legal_entity           | legal entity                                 |
| effective_start_date   | effective start date                         |
| effective_end_date     | effective end date, null = currently active  |

## Regulatory Reporting dataset - `regulatory.payment_reporting`

| column                     | description                       |
| --------------------------- | ----------------------------------|
| reporting_date              | regulatory reporting date         |
| customer_id                 | customer identifier                |
| payment_type                | WIRE / GIRO / CARD / INTERNAL / INSTANT |
| domestic_crossborder_flag   | DOMESTIC / CROSSBORDER             |
| transaction_count           | count of payments in the group     |
| total_transaction_amount    | sum of payment amounts in the group |
| reporting_currency          | ISO currency                       |
| legal_entity                | legal entity                       |

## Tasks

- **task 1 - profile transaction banking data** - profile the source and Bronze payment datasets: duplicate payment ids, missing customer ids, invalid payment status, missing currency, invalid beneficiary countries, negative or zero amounts, missing or inactive customer reference records, multiple active customer records, unusual transaction-volume spikes, unexpected payment-channel distributions, and cross-border classification anomalies, plus how these checks would run efficiently in Spark/Databricks at scale
- **task 2 - build end-to-end reconciliation** - reconcile Source -> Bronze -> Regulatory Reporting across transaction count, payment amount, customer count, currency, legal entity, payment type, domestic vs. cross-border classification, and reporting date, producing a reconciliation matrix (`Dimension | Source | Bronze | Regulatory | Variance | Status`)
- **task 3 - detect complex data issues** - determine how to distinguish a legitimate repeated payment from a duplicate file reload, detect and correct an effective-dated customer join issue that creates duplicate regulatory records, assess whether the current cross-border classification rule is sufficient, and identify and quantify the regulatory impact of transactions assigned to the wrong reporting date
- **task 4 - document data lineage** - lineage documentation for at least five critical regulatory attributes, each naming source, source column, Bronze location, transformation, and the data-quality control that guards it
- **task 5 - Power BI dashboard** - a data-quality and reconciliation dashboard with executive KPIs (source/Bronze/regulatory record counts, reconciliation rate, financial variance, data-quality issue count, critical exception count), the recommended visuals, and a filter set for date, legal entity, currency, and payment type
- **technical optimization question** - explain, and where possible demonstrate, the techniques that keep a reconciliation query against a 5-billion-row Bronze table under a 40-minute baseline

## Expected deliverables

- notebook
- profiling results
- end-to-end reconciliation
- exception tables
- root-cause analysis
- data-lineage document
- Power BI dashboard or dashboard design
- performance-optimization recommendations
- five-minute presentation summary

see [README.md](README.md) for current submission status.
