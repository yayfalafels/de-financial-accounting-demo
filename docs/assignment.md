# Data Analyst – Banking Data Ingestion & Reconciliation

## Table of Contents

- [Role Overview](#role-overview)
- [Key Responsibilities](#key-responsibilities)
- [Required Experience](#required-experience)
- [Technical Skills](#technical-skills)
- [Key Competencies](#key-competencies)
- [Preferred Qualifications](#preferred-qualifications)
- [Technical Hands-On Assessments – Data Analyst](#technical-hands-on-assessments--data-analyst)
  - [Assessment 1 – Source-to-Bronze Data Profiling and Reconciliation](#assessment-1--source-to-bronze-data-profiling-and-reconciliation)
  - [Assessment 2 – Financial Accounting and General Ledger Reconciliation](#assessment-2--financial-accounting-and-general-ledger-reconciliation)
  - [Assessment 3 – Regulatory / Transaction Banking Data Quality, Lineage and Executive Dashboard](#assessment-3--regulatory--transaction-banking-data-quality-lineage-and-executive-dashboard)

## Role Overview

We are seeking an experienced **Data Analyst** with strong banking domain knowledge and hands-on expertise in **data profiling, validation, reconciliation, and source-to-target analysis**. The role will focus on ensuring the completeness, accuracy, and integrity of source data ingested into the **Bronze layer** of the data platform across key banking domains including **Management Accounting, Financial Accounting, Regulatory Reporting, and Transaction Banking**.

The successful candidate will work closely with business, finance, data engineering, and technology teams to identify data quality issues, validate ingestion outcomes, reconcile source-to-Bronze data, and document data lineage and transformation requirements.

## Key Responsibilities

- Perform detailed **data profiling, validation, and reconciliation** of source data loaded into the Bronze layer.
- Validate source-to-Bronze ingestion for **completeness, accuracy, consistency, and integrity**.
- Develop and execute reconciliation checks covering record counts, balances, control totals, field-level comparisons, duplicates, null values, data types, and business-rule validations.
- Investigate and analyze data discrepancies between source systems and the target data platform.
- Identify root causes of data quality and reconciliation issues and work with data engineering and source-system teams to resolve them.
- Perform source data analysis across banking domains such as:
  - Management Accounting
  - Financial Accounting
  - Regulatory Reporting
  - Transaction Banking

- Translate business and finance requirements into detailed data validation and reconciliation rules.
- Create and maintain **source-to-target mappings, data lineage documentation, reconciliation evidence, and data quality reports**.
- Use **SQL, Databricks, Spark, Python, notebooks, and Excel** to perform large-scale data analysis and profiling.
- Build dashboards and visualizations using **Power BI** to communicate data quality, reconciliation results, trends, exceptions, and key metrics.
- Collaborate with Finance, Risk, Regulatory Reporting, Transaction Banking, Data Governance, Data Engineering, and Technology teams.
- Support testing activities including data validation, SIT/UAT reconciliation, defect investigation, and production data verification.
- Ensure data controls and reconciliation processes comply with established banking data governance and audit requirements.

## Required Experience

- **6 years of experience in data analysis within the banking or financial services industry**.

- Demonstrated hands-on experience in **data profiling and source-to-target reconciliation**, particularly for source-to-Bronze or similar raw data ingestion layers.
- Strong domain knowledge in at least one of the following:
  - Management Accounting
  - Financial Accounting
  - Regulatory Reporting
  - Transaction Banking

- Strong understanding of banking data, financial data structures, accounting concepts, transactional datasets, and data quality controls.
- Experience investigating complex data discrepancies and performing root-cause analysis.

## Technical Skills

- **Advanced SQL** for querying, profiling, reconciliation, and validation of large datasets.
- Hands-on experience with **Databricks and/or Apache Spark**.
- Experience working with **Databricks notebooks or similar notebook-based analytical environments**.
- Proficiency in **Python and/or advanced Excel** for data analysis, reconciliation, and automation.
- Experience documenting **data lineage, source-to-target mappings, and reconciliation rules**.
- Working knowledge of **Power BI** for dashboarding, reporting, and data visualization.
- Familiarity with modern data lake, lakehouse, or cloud-based data architectures would be advantageous.

## Key Competencies

- Strong analytical and problem-solving skills.
- High attention to detail, particularly when working with financial and regulatory data.
- Ability to analyze large and complex datasets and identify data anomalies efficiently.
- Strong communication skills with the ability to explain data issues to both technical and business stakeholders.
- Ability to work collaboratively across Finance, Business, Data, and Technology teams.
- Strong documentation and stakeholder management skills.

## Preferred Qualifications

- Degree in **Computer Science, Information Systems, Data Analytics, Finance, Accounting, Engineering**, or a related discipline.
- Experience working on large-scale banking data transformation, modernization, or data platform programs.
- Exposure to data governance, data quality frameworks, financial controls, or regulatory reporting environments.
- Understanding of medallion architecture and **Bronze/Silver/Gold data layers** is highly desirable.

# Technical Hands-On Assessments – Data Analyst

The following three assessments are designed for candidates with **4–6 years of banking data analysis experience** and test practical capability across **SQL, Databricks/Spark, Python, data profiling, reconciliation, lineage, banking-domain analysis, and Power BI**.

Each assessment is intentionally scenario-based and should require the candidate to investigate issues rather than simply execute predefined queries.

## Assessment 1 – Source-to-Bronze Data Profiling and Reconciliation

### Scenario

A bank is migrating transaction and accounting data from multiple source systems into a Databricks-based lakehouse.
You are responsible for validating a daily ingestion from the **Core Banking source system** into the **Bronze layer**.
The source system produces a transaction extract containing approximately **25 million records per day**.

### Source Table

src_transaction_daily

| **Column**            | **Description**                    |
|-----------------------|------------------------------------|
| transaction_id        | Unique transaction identifier      |
| account_id            | Customer/account identifier        |
| transaction_date      | Business transaction date          |
| posting_date          | Accounting posting date            |
| transaction_type      | CREDIT / DEBIT                     |
| currency_code         | ISO currency                       |
| transaction_amount    | Transaction amount                 |
| local_currency_amount | Amount converted to local currency |
| exchange_rate         | FX conversion rate                 |
| branch_code           | Booking branch                     |
| product_code          | Banking product                    |
| source_system         | Source application                 |
| ingestion_file        | Source file name                   |
| source_extract_ts     | Source extraction timestamp        |

### Bronze Table

bronze.transaction_daily

The Bronze table contains the same business fields plus:

- ingestion_timestamp
- batch_id
- record_hash
- source_file_name

During the latest production run, Finance reports that the total local currency balance from Bronze does not match the source.

### Candidate Tasks

### Task 1 – Perform Data Profiling

Using **SQL, Spark SQL, PySpark, or Python**, profile both datasets and produce profiling statistics including:

- Total record count
- Distinct transaction count
- Duplicate transaction IDs
- Null percentage for each critical field
- Minimum and maximum transaction dates
- Minimum and maximum posting dates
- Distinct currency codes
- Distinct transaction types
- Invalid currency codes
- Negative or zero transaction amounts
- Invalid transaction types
- Distribution by branch
- Distribution by product
- Distribution by source file
- Late-arriving transactions
- Records where posting date precedes transaction date unexpectedly

- Records where:

local_currency_amount != transaction_amount × exchange_rate

within an agreed tolerance.

The candidate must identify which columns should be considered **critical data elements** and explain why.

### Task 2 – Perform Source-to-Bronze Reconciliation

Build reconciliation logic comparing Source and Bronze at multiple levels.

#### Level 1 – Batch-Level Reconciliation

Compare:

- Record count
- Distinct transaction count
- Sum of debit amounts
- Sum of credit amounts
- Net transaction amount
- Sum of local currency amounts

#### Level 2 – Dimensional Reconciliation

Perform reconciliation by:

- Transaction date
- Branch
- Currency
- Product
- Transaction type
- Source file

Identify the combinations causing the largest mismatches.

#### Level 3 – Record-Level Reconciliation

Join Source and Bronze using the appropriate business key and classify records into:

- Exact match
- Missing in Bronze
- Unexpected record in Bronze
- Amount mismatch
- Currency mismatch
- Posting-date mismatch
- Duplicate in Source
- Duplicate in Bronze

Produce an exception table containing at minimum:

transaction_id, issue_type, source_value, bronze_value, variance, batch_id

### Task 3 – Investigate the Root Cause

The candidate discovers the following symptoms:

- Source count: **25,017,842**
- Bronze count: **24,998,131**

- 19,711 records appear to be missing.

- Almost all missing records belong to three source files.
- The files were created close to midnight.
- Some transactions contain timestamps in UTC while the ingestion process uses Singapore business dates.

The candidate must:

1.  Determine the likely root cause.
2.  Demonstrate the SQL/Spark queries used to validate the hypothesis.
3.  Quantify the financial impact.
4.  Identify affected branches, products, currencies, and accounting dates.
5.  Recommend remediation.
6.  Recommend permanent controls preventing recurrence.

### Expected Deliverables

The candidate should submit:

1.  SQL/Spark/Python notebook.
2.  Data profiling summary.
3.  Source-to-Bronze reconciliation results.
4.  Exception dataset.
5.  Root-cause analysis.
6.  Data-quality control recommendations.
7.  A short reconciliation dashboard or mock-up.

## Assessment 2 – Financial Accounting and General Ledger Reconciliation

### Scenario

The Finance division has reported that balances generated from the new data platform do not reconcile with the bank's General Ledger.

You are asked to determine whether the issue originates from:

- Source data
- Ingestion
- Data transformation
- FX conversion
- Accounting classification
- Duplicate transactions
- Missing transactions

Three datasets are available.

### Transaction Dataset

bronze.finance_transactions

Key columns:

- transaction_id
- account_id
- transaction_date
- posting_date
- transaction_amount
- currency
- exchange_rate
- local_amount
- debit_credit_indicator
- product_code
- branch_code
- gl_account
- cost_center
- legal_entity

### General Ledger Dataset

finance.gl_balance

Key columns:

- accounting_date
- legal_entity
- gl_account
- cost_center
- currency
- opening_balance
- debit_movement
- credit_movement
- closing_balance

### Accounting Mapping Dataset

ref.accounting_mapping

Key columns:

- product_code
- transaction_type
- expected_gl_account
- expected_cost_center
- effective_start_date
- effective_end_date

### Candidate Tasks

### Task 1 – Validate Accounting Integrity

Develop checks confirming that:

Opening Balance + Debit Movement - Credit Movement = Closing Balance

Identify violations.

Then independently calculate expected debit and credit movements from transaction-level data and reconcile against the General Ledger.

Perform reconciliation at:

- Legal entity
- GL account
- Cost center
- Currency
- Accounting date

### Task 2 – Validate Accounting Mapping

Using the accounting mapping table:

1.  Determine whether transactions are posted to the expected GL accounts.
2.  Validate mapping effective dates.
3.  Identify transactions with missing accounting mappings.
4.  Detect overlapping effective-date mappings.
5.  Identify expired mappings still being used.
6.  Identify products mapped to multiple GL accounts unexpectedly.

Create an exception output such as:

| **Transaction** | **Product** | **Actual GL** | **Expected GL** | **Accounting Date** | **Exception** |
|-----------------|-------------|---------------|-----------------|---------------------|---------------|

### Task 3 – Investigate a Finance Variance

Finance reports the following variance:

**Expected Closing Balance:** SGD 8,428,770,121.46  
**Platform Closing Balance:** SGD 8,431,992,337.18

Variance:

**SGD 3,222,215.72**

The candidate must determine which transactions explain the variance.

The dataset intentionally contains multiple issues, such as:

- Duplicate accounting entries
- Transactions posted twice
- Incorrect debit/credit indicators
- Incorrect FX conversion
- Missing accounting mappings
- Transactions posted one accounting day late
- Incorrect legal-entity allocation
- Incorrect cost-center assignment

The candidate must develop a structured investigation rather than searching transaction by transaction manually.

### Task 4 – Create a Reconciliation Framework

Design a reusable reconciliation framework supporting daily runs.

The framework should generate metrics such as:

- Source count
- Bronze count
- GL transaction count
- Source amount
- Bronze amount
- GL amount
- Absolute variance
- Percentage variance
- Exception count
- Reconciliation status

Propose configurable tolerance rules, for example:

- Absolute tolerance
- Percentage tolerance
- Currency-specific tolerance
- Account-specific tolerance

The framework should assign statuses:

- PASS
- WARNING
- FAIL

Explain how reconciliation results should be persisted for audit and historical analysis.

### Advanced SQL Requirement

The candidate should demonstrate advanced SQL capabilities including several of the following:

- CTEs
- Window functions
- Conditional aggregation
- MERGE
- Ranking
- Deduplication
- Effective-dated joins
- Hash comparison
- Incremental processing
- Exception categorization

### Expected Deliverables

1.  SQL or Databricks notebook.
2.  GL reconciliation output.
3.  Accounting mapping validation.
4.  Identified root causes of the SGD 3.22m variance.
5.  Exception dataset.
6.  Design for reusable reconciliation controls.
7.  Short business-facing summary explaining findings to Finance.

## Assessment 3 – Regulatory / Transaction Banking Data Quality, Lineage and Executive Dashboard

### Scenario

The bank is preparing a regulatory submission based on customer transaction data.
Regulatory Reporting identifies that transaction volumes shown in the regulatory reporting mart do not match Transaction Banking records.
Management requires an investigation demonstrating:

**Source → Bronze → Reporting dataset**

lineage and reconciliation.
The candidate receives four datasets.

### Source Payments

source.payment_transactions

Contains:

- payment_id
- customer_id
- account_id
- payment_date
- payment_timestamp
- payment_type
- payment_channel
- beneficiary_country
- currency
- amount
- status
- legal_entity

### Bronze Payments

bronze.payment_transactions

Contains source attributes plus ingestion metadata.

### Customer Reference

bronze.customer_master

Contains:

- customer_id
- customer_type
- residence_country
- risk_rating
- segment
- legal_entity
- effective_start_date
- effective_end_date

### Regulatory Dataset

regulatory.payment_reporting

Contains:

- reporting_date
- customer_id
- payment_type
- domestic_crossborder_flag
- transaction_count
- total_transaction_amount
- reporting_currency
- legal_entity

### Candidate Tasks

### Task 1 – Profile Transaction Banking Data

Perform detailed data profiling.

Identify:

- Duplicate payment IDs
- Missing customer IDs
- Invalid payment status
- Missing currency
- Invalid beneficiary countries
- Negative or zero payment amounts
- Missing customer reference records
- Payments linked to inactive customer records
- Multiple active customer records
- Unusual transaction-volume spikes
- Unexpected payment-channel distributions
- Cross-border classification anomalies

Candidate should demonstrate how large datasets would be handled efficiently in Spark/Databricks.

### Task 2 – Build End-to-End Reconciliation

Reconcile data across:

**Source → Bronze → Regulatory Reporting**

At minimum compare:

- Transaction count
- Payment amount
- Customer count
- Currency
- Legal entity
- Payment type
- Domestic vs cross-border classification

- Reporting date

Produce a reconciliation matrix such as:

| **Dimension** | **Source** | **Bronze** | **Regulatory** | **Variance** | **Status** |
|---------------|------------|------------|----------------|--------------|------------|
| SG Payments   | 2,510,442  | 2,510,442  | 2,508,103      | -2,339       | FAIL       |
| Cross Border  | 878,221    | 878,220    | 878,220        | -1           | WARNING    |

### Task 3 – Detect Complex Data Issues

The candidate must identify multiple hidden defects.
Examples include:

#### Duplicate Processing

A subset of payment files has been loaded twice under different ingestion batch IDs.
Candidate must determine how to distinguish legitimate repeated payments from duplicate ingestion.

#### Effective-Dated Customer Join Issue

The reporting pipeline joins customer data only by customer_id rather than:

customer_id + transaction date within effective date range

This creates duplicate regulatory records.
Candidate should detect and correct the issue.

#### Cross-Border Misclassification

Current logic:

customer residence country != beneficiary country

Candidate must assess whether this is sufficient and explain potential banking/business problems with this definition.

#### Late Arriving Transactions

Transactions received after the regulatory cutoff have been assigned to the next reporting date.

Candidate must identify affected transactions and quantify regulatory impact.

### Task 4 – Document Data Lineage

Create lineage documentation for at least five critical regulatory attributes.

Example:

| **Regulatory Attribute** | **Source**     | **Source Column**   | **Bronze**                         | **Transformation**          | **Data Quality Control**             |
|--------------------------|----------------|---------------------|------------------------------------|-----------------------------|--------------------------------------|
| Total Payment Amount     | Payment System | amount              | bronze.payment_transactions.amount | SUM by reporting dimensions | Source/Bronze amount reconciliation  |
| Cross Border Flag        | Payment System | beneficiary_country | Bronze Payments                    | Classification rule         | Valid country + classification check |

Candidate should identify appropriate critical data elements and controls.

### Task 5 – Power BI Dashboard

Create or design a **Power BI Data Quality & Reconciliation Dashboard** containing:

#### Executive KPIs

- Source records
- Bronze records
- Regulatory records
- Reconciliation rate
- Financial variance
- Data-quality issue count
- Critical exception count

#### Recommended Visuals

- Reconciliation status by reporting date
- Exception trend
- Variance by legal entity
- Variance by payment type
- Data-quality issues by category
- Top failing controls
- Source-to-Bronze reconciliation trend
- Regulatory reconciliation trend

The dashboard should allow filtering by:

- Date
- Legal entity
- Currency
- Payment type
- Data-quality status

### Technical Optimization Question

The Bronze table contains **5 billion historical records**.

A reconciliation query scanning the entire table takes more than 40 minutes.

The candidate must explain and, where possible, demonstrate improvements using appropriate techniques such as:

- Incremental processing
- Partition pruning
- Delta optimization
- Appropriate partition strategy
- Data skipping
- Predicate pushdown
- Broadcast joins
- Join optimization
- Caching where appropriate
- Pre-aggregated reconciliation tables

The candidate should explain both **what they would change and why** rather than simply listing Spark features.

### Expected Deliverables

1.  Databricks notebook containing SQL/PySpark.
2.  Profiling results.
3.  End-to-end reconciliation.
4.  Exception tables.
5.  Root-cause analysis.
6.  Data-lineage document.
7.  Power BI dashboard or dashboard design.
8.  Performance-optimization recommendations.
9.  Five-minute presentation summarizing findings.
