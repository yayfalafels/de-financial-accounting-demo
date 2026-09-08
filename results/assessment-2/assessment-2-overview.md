# Assessment 2 - Overview

## Scenario

The Finance division reports that balances generated from the new data platform do not reconcile with the bank's General Ledger. The candidate is asked to determine whether the issue originates from source data, ingestion, data transformation, FX conversion, accounting classification, duplicate transactions, or missing transactions. Three datasets are available: a transaction-level feed, the General Ledger, and an accounting mapping reference table.

>DISCLAIMER: Scaled down mock demo

The assignment scenario states an **Expected Closing Balance of SGD 8,428,770,121.46** against a **Platform Closing Balance of SGD 8,431,992,337.18** - a **SGD 3,222,215.72** variance at production scale. This demo's seeded volume budget is far smaller by design (`MOCK_DATA_FINANCE_TXN_PER_DAY=300`, `MOCK_DATA_DAYS=5`), producing 1,523 `bronze.finance_transactions` rows against 589 `finance.gl_balance` rows for the most recent seed run. Every measurement published in this assessment's deliverables is a finding against that seeded volume, with the assignment's SGD-billion figures cited here only as the scenario framing that motivated the check - never mistaken for a production-scale result, and never a target the seeded data is expected to reproduce exactly.

## Transaction dataset - `bronze.finance_transactions`

| column                  | description                        |
| ------------------------ | ----------------------------------- |
| transaction_id           | unique transaction identifier       |
| account_id               | customer/account identifier         |
| transaction_date         | business transaction date           |
| posting_date             | accounting posting date             |
| transaction_amount       | transaction amount                  |
| currency                 | ISO currency                        |
| exchange_rate            | FX conversion rate                  |
| local_amount             | amount converted to local currency  |
| debit_credit_indicator   | DEBIT / CREDIT                      |
| product_code             | banking product                     |
| branch_code              | booking branch                      |
| gl_account               | GL account posted to                |
| cost_center              | cost center posted to               |
| legal_entity             | legal entity posted to              |

## General Ledger dataset - `finance.gl_balance`

| column           | description                    |
| ----------------- | ------------------------------- |
| accounting_date    | GL accounting date              |
| legal_entity       | legal entity                    |
| gl_account         | GL account                      |
| cost_center        | cost center                     |
| currency           | ISO currency                    |
| opening_balance     | balance at period open          |
| debit_movement      | total debit movement            |
| credit_movement     | total credit movement           |
| closing_balance     | balance at period close         |

## Accounting mapping dataset - `ref.accounting_mapping`

| column                  | description                                |
| ------------------------ | -------------------------------------------- |
| product_code             | banking product                              |
| transaction_type         | DEBIT / CREDIT                               |
| expected_gl_account      | GL account a matching transaction should post to |
| expected_cost_center     | cost center a matching transaction should post to |
| effective_start_date     | mapping rule start date                      |
| effective_end_date       | mapping rule end date, nullable = open-ended |

## Tasks

- **task 1 - validate accounting integrity** - confirm `opening_balance + debit_movement - credit_movement = closing_balance` on `finance.gl_balance`, identify violations, then independently recompute expected debit/credit movements from `bronze.finance_transactions` and reconcile against the GL at legal entity, GL account, cost center, currency, and accounting date
- **task 2 - validate accounting mapping** - using `ref.accounting_mapping`, confirm transactions post to their expected GL account, validate mapping effective dates, identify missing/overlapping/expired mappings and products mapped to multiple GL accounts, and produce an exception output (`Transaction, Product, Actual GL, Expected GL, Accounting Date, Exception`)
- **task 3 - investigate a finance variance** - explain the SGD-scale closing-balance variance, structured rather than transaction-by-transaction, covering duplicate accounting entries, transactions posted twice under a different id, incorrect debit/credit indicators, incorrect FX conversion, missing accounting mappings, transactions posted one accounting day late, incorrect legal-entity allocation, and incorrect cost-center assignment
- **task 4 - create a reconciliation framework** - design a reusable, daily-run framework generating source/Bronze/GL counts and amounts, absolute/percentage variance, exception count, and reconciliation status, with configurable tolerance rules (absolute, percentage, currency-specific, account-specific), `PASS`/`WARNING`/`FAIL` status assignment, and a persistence design for audit and historical analysis

## Expected deliverables

- SQL / notebook
- GL reconciliation output
- accounting mapping validation
- identified root causes of the variance
- exception dataset
- reconciliation-framework design
- business-facing summary

see [README.md](README.md) for current submission status.
