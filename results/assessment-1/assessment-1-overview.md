# Assessment 1 - Overview

## Scenario

A bank is migrating transaction and accounting data from multiple source systems into a Databricks-based lakehouse. The daily ingestion under test moves a Core Banking transaction extract into the Bronze layer. Finance reports that the Bronze total local-currency balance does not match source - the reconciliation gap this assessment traces to a record-level cause.

## Source table - `src_transaction_daily`

| column                | description                         |
| --------------------- | ------------------------------------ |
| transaction_id        | unique transaction identifier        |
| account_id            | customer/account identifier          |
| transaction_date      | business transaction date            |
| posting_date          | accounting posting date              |
| transaction_type      | CREDIT / DEBIT                       |
| currency_code         | ISO currency                         |
| transaction_amount    | transaction amount                   |
| local_currency_amount | amount converted to local currency   |
| exchange_rate         | FX conversion rate                   |
| branch_code           | booking branch                       |
| product_code          | banking product                      |
| source_system         | source application                   |
| ingestion_file        | source file name                     |
| source_extract_ts     | source extraction timestamp          |

## Bronze table - `bronze.transaction_daily`

Same business fields as source, plus:

| column               | description                    |
| --------------------- | ------------------------------ |
| ingestion_timestamp    | when the record landed Bronze  |
| batch_id               | ingestion batch identifier     |
| record_hash            | row-level hash for dedup/audit |
| source_file_name       | Bronze-side source-file name   |

## Tasks

- **task 1 - data profiling** - profile both datasets against the assignment's stated checks (record/distinct counts, duplicate ids, null percentages, date ranges, currency/type validity, negative/zero amounts, branch/product/source-file distributions, late arrivals, posting-date ordering, and FX tolerance), and nominate and justify the critical data elements
- **task 2 - source-to-bronze reconciliation** - level 1 batch totals, level 2 dimensional reconciliation with the largest-variance combinations identified, and level 3 record-level classification into exact match, missing in Bronze, unexpected in Bronze, amount/currency/posting-date mismatch, and duplicates on either side
- **task 3 - root cause** - explain, evidence, and quantify the missing-record population concentrated in near-midnight source files where UTC source timestamps meet Singapore business-date ingestion, then recommend remediation plus permanent preventive controls

## Expected deliverables

notebook, profiling summary, reconciliation results, exception dataset, root-cause analysis, DQ-control recommendations, and a short reconciliation dashboard or mock-up - see [results/assessment-1/README.md](README.md) for current submission status.

## Scale statement

The assignment scenario states the Core Banking extract runs at approximately **25 million records per day** in production. This demo's seeded volume budget is far smaller by design (`MOCK_DATA_DAYS=5`, `MOCK_DATA_TXN_PER_DAY=400`), producing 2,010 `src_transaction_daily` rows against 1,993 `bronze.transaction_daily` rows for the most recent seed run - a 17-row / 0.85% gap engineered to be traceable, not a scaled-down replica of the production symptom's absolute size. Every measurement published in this assessment's deliverables is a finding against that seeded volume, with the production figure cited here only as the scenario framing that motivated the check - never mistaken for a production-scale result.
