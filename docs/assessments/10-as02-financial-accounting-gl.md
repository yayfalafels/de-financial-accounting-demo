# Assessment 2 - Financial Accounting and General Ledger Reconciliation - Feature tracker
>Review the guidelines before performing any actions including edits on the document

## 10 (open) assessment 2 - financial accounting and GL reconciliation

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
  - [prerequisites](#prerequisites)
  - [assessment task to deliverable map](#assessment-task-to-deliverable-map)
  - [workflow cycle](#workflow-cycle)
  - [assessment context documentation](#assessment-context-documentation)
  - [presentation boundary - blind-analyst results](#presentation-boundary--blind-analyst-results)
  - [GL integrity design - task 1](#gl-integrity-design--task-1)
  - [mapping validation design - task 2](#mapping-validation-design--task-2)
  - [variance investigation design - task 3](#variance-investigation-design--task-3)
  - [reconciliation framework design - task 4](#reconciliation-framework-design--task-4)
  - [exception dataset](#exception-dataset)
  - [advanced sql coverage](#advanced-sql-coverage)
  - [notebook organisation](#notebook-organisation)
  - [idempotency / rerun-safety](#idempotency--rerun-safety)
  - [environment & secrets](#environment--secrets)
  - [workflow validation runner](#workflow-validation-runner)
  - [publishing](#publishing)
- [Test cases](#test-cases)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                 |
| ----- | --- | ------- | ----------------------------------------- |
| 10.01 | 01  | closed  | design                                    |
| 10.02 | 02  | closed  | prerequisites and seed data readiness     |
| 10.03 | 03  | closed  | assessment scope and context write-up     |
| 10.04 | 04  | closed  | task 1 - GL integrity and reconciliation  |
| 10.05 | 05  | pending | task 2 - accounting mapping validation    |
| 10.06 | 06  | pending | exception dataset                         |
| 10.07 | 07  | pending | task 3 - finance variance investigation   |
| 10.08 | 08  | pending | task 4 - reconciliation framework design  |
| 10.09 | 09  | pending | business-facing summary                   |
| 10.10 | 10  | pending | notebook consolidation and clean rerun    |
| 10.11 | 11  | pending | deliverable review and status promotion   |
| 10.12 | 12  | pending | publish assessment site                   |
| 10.IS | 13  | pending | validate                                  |

## Scope

Assessment 2 of the **assignment design doc** end to end 

- validate `finance.gl_balance` arithmetic integrity
- independently recompute GL movements from `bronze.finance_transactions`
- validate `ref.accounting_mapping`
- explain the SGD-scale finance variance symptom,
- design a reusable reconciliation framework
- publish the resulting deliverable set together with the assignment context that motivated it 

see [milestones.md](../milestones.md)'s `assessment 2` entry for the milestone-level statement this tracker executes.

**assessment scope**

- **scenario** Finance reports that balances generated from the new data platform do not reconcile with the bank's General Ledger.  
- **the problem** platform closing balance disagrees with the expected closing balance by a material amount. trace the cause(s) to: 
  - source data
  - ingestion
  - transformation
  - FX conversion
  - accounting classification
  - duplicate transactions
  - missing transactions

- **checks to perform**

| id       | task ref | scope                  | check                                                |
| -------- | -------- | ---------------------- | ----------------------------------------------------- |
| 10.CK.01 | 01.01    | GL integrity           | opening + debit - credit = closing arithmetic check   |
| 10.CK.02 | 01.02    | GL integrity           | recomputed debit movement vs `gl_balance.debit_movement`  |
| 10.CK.03 | 01.03    | GL integrity           | recomputed credit movement vs `gl_balance.credit_movement` |
| 10.CK.04 | 01.04    | dim reconcile          | legal entity                                          |
| 10.CK.05 | 01.05    | dim reconcile          | GL account                                            |
| 10.CK.06 | 01.06    | dim reconcile          | cost center                                           |
| 10.CK.07 | 01.07    | dim reconcile          | currency                                              |
| 10.CK.08 | 01.08    | dim reconcile          | accounting date                                       |
| 10.CK.09 | 02.01    | mapping validate       | transaction posted to expected GL account             |
| 10.CK.10 | 02.02    | mapping validate       | mapping effective-date validity                       |
| 10.CK.11 | 02.03    | mapping validate       | transactions with missing accounting mapping          |
| 10.CK.12 | 02.04    | mapping validate       | overlapping effective-date mapping ranges             |
| 10.CK.13 | 02.05    | mapping validate       | expired mapping still referenced                      |
| 10.CK.14 | 02.06    | mapping validate       | product mapped to multiple GL accounts unexpectedly   |
| 10.CK.15 | 03.01    | variance investigation | duplicate accounting entry                            |
| 10.CK.16 | 03.02    | variance investigation | transaction posted twice under a different id         |
| 10.CK.17 | 03.03    | variance investigation | incorrect debit/credit indicator                      |
| 10.CK.18 | 03.04    | variance investigation | incorrect FX conversion                               |
| 10.CK.19 | 03.05    | variance investigation | missing accounting mapping's variance contribution    |
| 10.CK.20 | 03.06    | variance investigation | transaction posted one accounting day late            |
| 10.CK.21 | 03.07    | variance investigation | incorrect legal-entity allocation                     |
| 10.CK.22 | 03.08    | variance investigation | incorrect cost-center assignment                      |
| 10.CK.23 | 04.01    | framework metrics      | source/Bronze/GL counts, amounts, variance, status    |

- **task 1 - validate accounting integrity** - confirm `opening_balance + debit_movement - credit_movement = closing_balance` on `finance.gl_balance`, identify violations, then independently recompute expected debit/credit movements from `bronze.finance_transactions` and reconcile against the GL at legal entity, GL account, cost center, currency, and accounting date

**task 1 checks**

| id       | check                                                      |
| -------- | ---------------------------------------------------------- |
| 10.CK.01 | opening + debit - credit = closing arithmetic check        |
| 10.CK.02 | recomputed debit movement vs `gl_balance.debit_movement`   |
| 10.CK.03 | recomputed credit movement vs `gl_balance.credit_movement` |
| 10.CK.04 | reconcile by legal entity                                  |
| 10.CK.05 | reconcile by GL account                                    |
| 10.CK.06 | reconcile by cost center                                   |
| 10.CK.07 | reconcile by currency                                      |
| 10.CK.08 | reconcile by accounting date                               |

- **task 2 - validate accounting mapping** - using `ref.accounting_mapping`, confirm transactions post to their expected GL account, validate mapping effective dates, and produce an exception output (`Transaction, Product, Actual GL, Expected GL, Accounting Date, Exception`)

**task 2 checks**

| id       | check                                                |
| -------- | ---------------------------------------------------- |
| 10.CK.09 | transaction posted to expected GL account            |
| 10.CK.10 | mapping effective-date validity                      |
| 10.CK.11 | transactions with missing accounting mapping         |
| 10.CK.12 | overlapping effective-date mapping ranges            |
| 10.CK.13 | expired mapping still referenced                     |
| 10.CK.14 | product mapped to multiple GL accounts unexpectedly  |

- **task 3 - investigate a finance variance** - explain the SGD-scale closing-balance variance between expected and platform figures, structured rather than transaction-by-transaction, covering:

| id       | issue category                                      |
| -------- | --------------------------------------------------- |
| 10.CK.15 | duplicate accounting entry                          |
| 10.CK.16 | transaction posted twice under a different id       |
| 10.CK.17 | incorrect debit/credit indicator                    |
| 10.CK.18 | incorrect FX conversion                             |
| 10.CK.19 | missing accounting mapping's variance contribution  |
| 10.CK.20 | transaction posted one accounting day late          |
| 10.CK.21 | incorrect legal-entity allocation                   |
| 10.CK.22 | incorrect cost-center assignment                    |

- **task 4 - create a reconciliation framework** - design a reusable, daily-run framework generating the metrics in **10.CK.23**, configurable tolerance rules (absolute, percentage, currency-specific, account-specific), `PASS`/`WARNING`/`FAIL` status assignment, and a persistence design for audit and historical analysis
- **advanced SQL requirement** - demonstrate several of CTEs, window functions, conditional aggregation, `MERGE`, ranking, deduplication, effective-dated joins, hash comparison, incremental processing, exception categorization - see [advanced sql coverage](#advanced-sql-coverage)
- **expected deliverables** - notebook, GL reconciliation output, accounting mapping validation, identified root causes of the variance, exception dataset, reconciliation-framework design, and a business-facing summary
- **assessment context** - the published results must state the assignment scenario, tasks, and scale framing they answer, so a reader is not handed measurements without the question they respond to - see [assessment context documentation](#assessment-context-documentation)

**prerequisite scope**

already-closed infrastructure this assessment consumes, not re-decided here

- **postgres db** ([02](../features/02-dev-env-setup-postgresql-db.md)) running, extended by the seed feature's schema JSON for `finance.gl_balance`, `bronze.finance_transactions`, and `ref.accounting_mapping`
- **spark + jupyter containers** ([03](../features/03-dev-env-setup-spark-container.md)) up, so the notebook can reach both postgres over JDBC and the Spark master
- **seed data** ([04](../features/04-seed-mock-data.md)) loaded through `scripts/03-mock-data-seed.sh`, with `data/mock/issue-log.csv` as the ground-truth catalog of every injected Assessment 2 issue
- **reconciliation control tables** ([05](../features/05-ai-closed-loop-validation.md)) `reconciliation.rc_*` present, the same schema this assessment's task 1/4 results are written into
- **deliverable paths** ([08](../features/08-assessment-deliverables-conventions.md)) scaffolded under `results/assessment-2/`, indexed by [results/assessment-2/README.md](../../results/assessment-2/README.md) - that manifest, not this tracker, is the single list of what must be produced
- **notebook path** ([07](../features/07-jupyter-notebook-workspace-setup.md)) `notebooks/assessment2_gl_reconciliation.ipynb`

**out of scope**

- does not seed, extend, or regenerate mock data - if a check has nothing to find, that is a [04](../features/04-seed-mock-data.md) defect raised there, not a data edit made here
- does not change the `reconciliation.rc_*` schema; task 4's framework design proposes tolerance/status logic expressed against the existing schema, it does not add new columns
- does not attempt the assignment's literal SGD 8.4B-scale GL volumes - measured numbers come from the seeded volume budget, and the assignment's own SGD 3,222,215.72 variance is cited only as the scenario's framing figure, never as a target the seeded data is expected to reproduce exactly (per [04](../features/04-seed-mock-data.md#injected-issue-catalog--assessment-2), the actual seeded variance is whatever that run's RNG produces)
- does not build a dashboard deliverable - the [deliverable-type taxonomy](../features/08-assessment-deliverables-conventions.md#deliverable-type-taxonomy) has no dashboard row for Assessment 2
- does not cover Assessment 1 or Assessment 3 datasets, deliverables, or notebooks

**closure**

Every deliverable listed in [results/assessment-2/README.md](../../results/assessment-2/README.md) carries `status: final`, the assessment context page exists and is referenced from every deliverable, each finding is traceable to a `reconciliation.rc_batch_control.batch_id` or a notebook section, `scripts/07-deliverables-scaffold.sh --check` passes, and the published site shows the Assessment 2 pages.

## References

- **assignment design doc** `docs/design/assignment.md` (Assessment 2 scenario, Tasks 1-4, Advanced SQL Requirement, Expected Deliverables)
- **milestones** `docs/milestones.md` (`assessment 2` scope and closure statement)
- **postgresql db tracker** `docs/features/02-dev-env-setup-postgresql-db.md`
- **spark container tracker** `docs/features/03-dev-env-setup-spark-container.md`
- **seed mock data tracker** `docs/features/04-seed-mock-data.md` (assessment 2 injected issue catalog)
- **ai closed-loop validation tracker** `docs/features/05-ai-closed-loop-validation.md` (`rc_*` schema)
- **jupyter notebook workspace tracker** `docs/features/07-jupyter-notebook-workspace-setup.md`
- **deliverables conventions tracker** `docs/features/08-assessment-deliverables-conventions.md`
- **deliverable manifest** `results/assessment-2/README.md`
- **issue log** `data/mock/issue-log.csv` gitignored, regenerated every seed run
- **schemas** `data/schemas/as02-finance-transactions-schema.json`, `data/schemas/as02-gl-balance-schema.json`, `data/schemas/as02-accounting-mapping-schema.json`

## Design

### prerequisites

Ordered, rerunnable setup steps that must pass before any analysis task starts. Each is an existing script from a closed feature. this tracker only fixes the order and the evidence each step must leave behind.

| id       | step                        | command                                       | evidence         |
| -------- | --------------------------- | --------------------------------------------- | ----------------- |
| 10.PR.01 | host prerequisites          | `scripts/00-prereq-check.sh`                  | `[PASS]` log      |
| 10.PR.02 | postgres + tables           | `scripts/01-dev-env-setup.sh`                 | 9 tables exist    |
| 10.PR.03 | spark + jupyter containers  | `docker compose` full profile                 | `docker ps`       |
| 10.PR.04 | seed mock data              | `scripts/03-mock-data-seed.sh`                | `issue-log.csv`   |
| 10.PR.05 | seed validation             | `scripts/04-mock-data-validate.sh`            | row/issue counts  |
| 10.PR.06 | notebook connectivity       | `scripts/06-notebook-validate.sh`             | template passes   |
| 10.PR.07 | deliverable scaffold check  | `scripts/07-deliverables-scaffold.sh --check` | current           |

01. **10.PR.02** covers only DDL; a fresh clone must still run step 04 before any GL query returns rows.
02. **10.PR.03** uses `docker/docker-compose.full.yml`; the master, both workers, and the Jupyter container must all be `Up` before the notebook is executed.
03. unlike [09](09-as01-data-profiling-reconciliation.md#prerequisites), there is no assessment-2-specific control-table smoke run prerequisite - `reconciliation.rc_*` already exists and is proven end to end by Assessment 1's own closed-loop run; this tracker's task 1/4 steps are the first ones to write an `assessment_id = 'assessment-2'` batch into it.

### assessment task to deliverable map

One row per assignment task, naming the deliverable file it lands in and the executable artifact it is derived from. This is the traceability contract every write-up's **Sources** section must satisfy.

| id       | assignment task                    | deliverable file [01]  | artifact          |
| -------- | ---------------------------------- | ----------------------- | ------------------ |
| 10.DM.01 | task 1 GL arithmetic integrity     | `reconciliation-results` | `rc_*` + notebook  |
| 10.DM.02 | task 1 dimensional reconciliation  | `reconciliation-results` | notebook           |
| 10.DM.03 | task 2 mapping validation          | `mapping-validation`     | notebook           |
| 10.DM.04 | task 2 exception output            | `mapping-validation`     | notebook           |
| 10.DM.05 | task 3 variance investigation      | `root-cause-analysis`    | notebook           |
| 10.DM.06 | task 3 record-level exceptions     | `exception-dataset`      | notebook           |
| 10.DM.07 | task 4 framework design            | `framework-design`       | narrative          |
| 10.DM.08 | task 4 tolerance/status design     | `framework-design`       | narrative          |
| 10.DM.09 | task 4 persistence design          | `framework-design`       | `rc_*` (existing)  |
| 10.DM.10 | business-facing summary            | `business-summary`       | narrative          |
| 10.DM.11 | notebook                           | manifest reference row  | notebook           |
| 10.DM.12 | scenario and task context          | `overview`               | assignment doc     |

01. file names are `results/assessment-2/assessment-2-<slug>.md` per [08](../features/08-assessment-deliverables-conventions.md#directory-and-naming-convention).
02. **10.DM.12** is the authored context page introduced by this tracker, outside feature 08's generated taxonomy - see [assessment context documentation](#assessment-context-documentation).
03. **10.DM.06** and **10.DM.05** are both sourced from the same task 3 investigation - the exception dataset is the row-level detail (one row per flagged transaction/GL entry), the root-cause analysis is the narrative explaining what that detail adds up to; a number is never restated between the two, one links the other.

### workflow cycle

Identical five-stage loop to [09](09-as01-data-profiling-reconciliation.md#workflow-cycle), reused rather than redesigned so every claim in a markdown deliverable stays reproducible from a seeded database.

```
seed db  ->  notebook / spark  ->  rc_* control tables  ->  results markdown  ->  validation run
   ^                                                                                     |
   |_____________________________ rerun on any change ___________________________________|
```

| id       | stage             | action                                                   |
| -------- | ----------------- | ---------------------------------------------------------- |
| 10.WS.01 | seed db           | confirm seeded state, capture the seed run's `issue-log`    |
| 10.WS.02 | notebook / spark  | add or update the task's cells, execute top to bottom       |
| 10.WS.03 | control tables    | write measured results to `reconciliation.rc_*`             |
| 10.WS.04 | results markdown  | update the mapped deliverable and its **Sources** section   |
| 10.WS.05 | validation run    | rerun the scripted checks and record `[PASS]`/`[FAIL]`      |

01. **10.WS.03** applies to task 1 (GL reconciliation) and task 4 (framework metrics) only; task 2 mapping validation and task 3's narrative findings stop at **10.WS.02** and are cited by notebook cell rather than `batch_id`, the same split [09](09-as01-data-profiling-reconciliation.md#workflow-cycle) draws for profiling vs. reconciliation.
02. **10.WS.04** never restates a number the notebook did not produce in the same run - a changed measurement means the deliverable is edited in the same cycle, not the next one.

### assessment context documentation

Same gap and same fix as [09](09-as01-data-profiling-reconciliation.md#assessment-context-documentation): the deliverables scaffolded by [08](../features/08-assessment-deliverables-conventions.md) present measurements without the assignment context that motivated them.

- **overview page** - `results/assessment-2/assessment-2-overview.md` restates the Assessment 2 scenario, the three dataset shapes (`bronze.finance_transactions`, `finance.gl_balance`, `ref.accounting_mapping`), Tasks 1-4, and the expected deliverable list in the assignment's own framing
- **scale statement** - one paragraph naming the assignment's SGD 8.4B-scale closing balances and SGD 3,222,215.72 variance figure alongside this demo's seeded volume budget, so every number published elsewhere is read against the right scale rather than mistaken for a production figure
- **per-deliverable context** - each deliverable opens with a single line, directly under its `status:` marker, naming the assignment task it answers and linking the overview page
- **linkage** - the overview is authored content outside feature 08's generated taxonomy, so it is linked from `results/index.md` and from each deliverable rather than from the generated manifest
- **no restatement of findings** - the overview carries assignment context only; measured results stay in their own deliverables so there is one place a number can change

### presentation boundary - blind-analyst results

Per user direction during 10.05/10.07 review: this assessment's results-facing content - the notebook and every `results/assessment-2/*.md` deliverable except `assessment-2-audit.md` - is written and read as work product a candidate would actually submit, not as a readout of this tracker's own project state. Four rules apply, retrofitted onto every already-closed task's deliverable, not just new ones:

- **no tracker apparatus** - never reference this tracker's own ids (`10.CK.xx`, `10.PR.xx`, `10.WS.xx`, `10.EL.xx`, task ids like `10.07`) or workflow-step language in the notebook or a results markdown file. Reference only the assignment's own structure - task names, and the `NN.MM` task-ref numbering the [checks to perform](#scope) table already assigns each check. A technical artifact the assignment itself asks for (e.g. `batch_id` as the answer to task 4's persistence question) is not tracker apparatus and stays.
- **audit is one-directional** - `assessment-2-audit.md` sits above the main analysis and is the only page allowed to know the ground truth (`issue-log.csv`, the seed generator, injected-issue tags) or reference this tracker directly; every other deliverable never links to or cites it. The main analysis is written as if the audit page does not exist.
- **blind, non-omnipotent analyst** - every deliverable except the audit reads as an analyst with the assignment brief in hand (so referencing a later task by its assignment name is fine) but no knowledge of which findings were deliberately injected, how, or what a later task's investigation will reveal. A finding is stated as what this level of analysis shows, not as confirmation of a known answer.
- **no revision language** - a correction found during review is applied and the deliverable is rewritten to read as if that were always the only version; it never narrates "previously reported X, now Y" or similar. This tracker's own Implement section is the place that history is recorded (see 10.05/10.07 below), never the deliverable itself.

### GL integrity design - task 1

**detectability analysis - which causes can this reconciliation surface, and why**

the assignment names seven candidate causes; before designing the recomputation, each is tested against one question: since the platform generates `finance.gl_balance` by aggregating `bronze.finance_transactions` directly, does a given cause have any way to end up making the two *disagree*, or does it pass through into both sides identically?

| id | candidate cause                    | amt basis?   | exp value?  | observability |
| -- | ---------------------------------- | ------------ | ----------- | ------------- |
| 01 | duplicate / posted twice           | no           | no          | pass-through  |
| 02 | wrong debit/credit indicator       | no           | no          | pass-through  |
| 03 | posted one day late                | no           | no          | pass-through  |
| 04 | missing accounting mapping         | no           | no          | pass-through  |
| 05 | incorrect FX conversion            | wrong column | no          | invisible     |
| 06 | incorrect legal-entity             | no           | **yes**     | conditional   |
| 07 | incorrect cost-center / GL-account | no           | **yes**     | conditional   |

01. extra row, same amount, same classification. every row, duplicates included, is aggregated into the Ledger as posted; a duplicate's value enters both sides identically.
02. moves the amount to the other side of the same posted record; the indicator selects which side a value adds to, it is not itself a grouping key. the Ledger's `debit_movement`/`credit_movement` already reflect whichever indicator the transaction carries.
03. `accounting_date` is technically a grouping dimension, but there is no independent "expected posting date" to substitute - the posting date is itself the fact in question. The Ledger is keyed/classified by the transaction's own actual value; recomputing on that same value can only agree - nothing to substitute on either side.
04. `gl_account`/`cost_center` are grouping dimensions, but by definition no valid expected value exists for these transactions.
05. the defect lives in `local_amount`, a column the Ledger's own movement figures do not read at all - not pass-through so much as untouched; a comparison built on the Ledger's real amount basis (`transaction_amount`) cannot see an error confined to a different column.
06. detectable only if the recomputation groups by the *expected* value; grouping by the transaction's actual value (the same value the Ledger used) is tautological.
07. except for a handful of product/type combinations where the reference itself carries more than one active, conflicting row - no single expected value exists for those.

Only three of the seven candidates - legal-entity, cost-center, and (unambiguous) GL-account misclassification - can, even in principle, produce a gap this reconciliation is capable of finding, and only if the recomputation substitutes each transaction's *expected* classification rather than reusing the actual, as-posted values the Ledger itself was built from. The other four are pass-through or column-invisible regardless of how carefully the recomputation is implemented. 

**business key, date convention, and classification basis** - `finance.gl_balance`'s five-dimension grouping key (`accounting_date, legal_entity, gl_account, cost_center, currency`) is also the grouping key every recomputation below aggregates `bronze.finance_transactions` onto, joining `bronze.finance_transactions.posting_date` to `gl_balance.accounting_date` - the Ledger is dated by *posting*. per the table above, this is a pass-through dimension - the join convention matters for correctly locating a transaction's Ledger key. The amount recomputed is `transaction_amount` in native currency. This is the column the Ledger's own `debit_movement`/`credit_movement` are themselves aggregated from. `legal_entity`, `gl_account`, and `cost_center` are recomputed on each transaction's *expected* value - majority-vote per account for legal entity, `ref.accounting_mapping`'s expected value for GL account and cost center wherever a transaction matches exactly one active mapping row - falling back to the transaction's actual value only where no expected value is determinable (unmapped transactions) or where the reference itself is ambiguous (a product/transaction-type combination with more than one currently-active, conflicting mapping row - see [mapping validation design](#mapping-validation-design--task-2)'s overlapping/multi-GL checks for that population).

**10.CK.01 - arithmetic integrity**

```sql
SELECT accounting_date, legal_entity, gl_account, cost_center, currency,
       opening_balance, debit_movement, credit_movement, closing_balance,
       (opening_balance + debit_movement - credit_movement) AS computed_closing,
       closing_balance - (opening_balance + debit_movement - credit_movement) AS variance
FROM finance.gl_balance
WHERE closing_balance <> opening_balance + debit_movement - credit_movement
```

Tolerance: exact equality - any nonzero `variance` is a violation. No rounding tolerance applies here: all four columns are `decimal(20,2)` and the expression is pure addition/subtraction, so a nonzero result is a genuine arithmetic break, not a rounding artifact.

**10.CK.02 / 10.CK.03 - independent movement recomputation**

```sql
WITH flip_candidates AS (
  -- a transaction whose actual (gl_account, cost_center) doesn't match any active mapping row for
  -- its own indicator, but exactly matches one for the opposite indicator - its own posted values
  -- are internally consistent with a real, valid combination, just filed under the wrong sign
  SELECT t.transaction_id
  FROM bronze.finance_transactions t
  LEFT JOIN (
    SELECT t.transaction_id, MAX(CASE WHEN t.gl_account = m.expected_gl_account
                                        AND t.cost_center = m.expected_cost_center THEN 1 ELSE 0 END) AS matches_current
    FROM bronze.finance_transactions t
    JOIN ref.accounting_mapping m
      ON t.product_code = m.product_code AND t.debit_credit_indicator = m.transaction_type
      AND t.transaction_date >= m.effective_start_date AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
    GROUP BY t.transaction_id
  ) cm ON t.transaction_id = cm.transaction_id
  JOIN (
    SELECT t.transaction_id, MAX(CASE WHEN t.gl_account = m.expected_gl_account
                                        AND t.cost_center = m.expected_cost_center THEN 1 ELSE 0 END) AS matches_opposite
    FROM bronze.finance_transactions t
    JOIN ref.accounting_mapping m
      ON t.product_code = m.product_code
      AND m.transaction_type = CASE WHEN t.debit_credit_indicator = 'DEBIT' THEN 'CREDIT' ELSE 'DEBIT' END
      AND t.transaction_date >= m.effective_start_date AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
    GROUP BY t.transaction_id
  ) om ON t.transaction_id = om.transaction_id
  WHERE COALESCE(cm.matches_current, 0) = 0 AND om.matches_opposite = 1
),
corrected AS (
  -- the mapping lookup is keyed on the transaction's indicator - a flip candidate's own posted
  -- indicator is the wrong key to look up under, so the opposite indicator is used instead
  SELECT t.*, CASE WHEN fc.transaction_id IS NOT NULL
                    THEN (CASE WHEN t.debit_credit_indicator = 'DEBIT' THEN 'CREDIT' ELSE 'DEBIT' END)
                    ELSE t.debit_credit_indicator END AS lookup_type
  FROM bronze.finance_transactions t
  LEFT JOIN flip_candidates fc ON t.transaction_id = fc.transaction_id
),
single_match AS (
  -- exactly one active mapping row per transaction; drops product/type combinations with more
  -- than one currently-active, conflicting row - no single expected value exists for those
  SELECT transaction_id, expected_gl_account, expected_cost_center FROM (
    SELECT t.transaction_id, m.expected_gl_account, m.expected_cost_center,
           COUNT(*) OVER (PARTITION BY t.transaction_id) AS match_count
    FROM corrected t
    JOIN ref.accounting_mapping m
      ON t.product_code = m.product_code AND t.lookup_type = m.transaction_type
      AND t.transaction_date >= m.effective_start_date
      AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
  ) matched WHERE match_count = 1
),
account_entity_mode AS (
  -- majority-vote legal entity per account - the mapping table carries no legal-entity field
  SELECT account_id, legal_entity FROM (
    SELECT account_id, legal_entity,
           ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY COUNT(*) DESC) AS rnk
    FROM bronze.finance_transactions GROUP BY account_id, legal_entity
  ) ranked WHERE rnk = 1
),
recomputed AS (
  SELECT
    t.posting_date AS accounting_date,
    COALESCE(em.legal_entity, t.legal_entity) AS legal_entity,
    COALESCE(sm.expected_gl_account, t.gl_account) AS gl_account,
    COALESCE(sm.expected_cost_center, t.cost_center) AS cost_center,
    t.currency,
    SUM(CASE WHEN t.debit_credit_indicator = 'DEBIT'  THEN t.transaction_amount ELSE 0 END) AS recomputed_debit,
    SUM(CASE WHEN t.debit_credit_indicator = 'CREDIT' THEN t.transaction_amount ELSE 0 END) AS recomputed_credit
  FROM bronze.finance_transactions t
  LEFT JOIN single_match sm ON t.transaction_id = sm.transaction_id
  LEFT JOIN account_entity_mode em ON t.account_id = em.account_id
  GROUP BY t.posting_date, COALESCE(em.legal_entity, t.legal_entity),
           COALESCE(sm.expected_gl_account, t.gl_account), COALESCE(sm.expected_cost_center, t.cost_center), t.currency
)
SELECT
  g.accounting_date, g.legal_entity, g.gl_account, g.cost_center, g.currency,
  g.debit_movement,  r.recomputed_debit,  g.debit_movement  - r.recomputed_debit  AS debit_variance,
  g.credit_movement, r.recomputed_credit, g.credit_movement - r.recomputed_credit AS credit_variance
FROM finance.gl_balance g
FULL OUTER JOIN recomputed r
  ON  g.accounting_date = r.accounting_date AND g.legal_entity = r.legal_entity
  AND g.gl_account      = r.gl_account      AND g.cost_center  = r.cost_center
  AND g.currency        = r.currency
WHERE ABS(COALESCE(g.debit_movement,0)  - COALESCE(r.recomputed_debit,0))  > 0.01
   OR ABS(COALESCE(g.credit_movement,0) - COALESCE(r.recomputed_credit,0)) > 0.01
```

Tolerance: `MOVEMENT_TOLERANCE_ABS = 0.01` (one minor-currency-unit) applied independently to each side - loose enough to absorb ordinary rounding, tight enough that it never masks a genuine one-record miss. `FULL OUTER JOIN` (not `LEFT`/`INNER`) so a GL key with no matching transactions, or a transaction key with no matching GL row, both surface as a variance instead of silently dropping out of the comparison.

**implementation decision - grouping by expected classification, not actual** - grouping this recomputation by each transaction's *actual* `gl_account`/`cost_center`/`legal_entity` (the values `finance.gl_balance` was itself built from) would make the check tautological on those three dimensions regardless of how much misclassification exists in the data - see the detectability analysis above. Grouping by the expected value instead is what makes **10.CK.04**-**10.CK.08**'s dimensional roll-up capable of finding anything at all on those dimensions.

**implementation decision - correcting the mapping lookup for the indicator** - the mapping join is itself keyed on the transaction's own posted debit/credit indicator; a transaction carrying the wrong indicator would otherwise be looked up under the wrong key, measured against the expected value for the *opposite* of its true type. `flip_candidates` catches these the same way **10.CK.17** does (see [variance investigation design](#variance-investigation-design--task-3)) and looks them up under the corrected indicator instead - without this, `single_match` can supply an expected value that is neither the transaction's actual value nor its genuinely correct one, for a transaction this reconciliation has no other way to place correctly.

**10.CK.04-10.CK.08 - dimensional reconciliation** - the same recomputation, rolled up to one dimension at a time instead of the full five-key grain:

```sql
-- <dimension> is one of: legal_entity, gl_account, cost_center, currency, accounting_date
SELECT <dimension>,
       SUM(g.debit_movement)  AS gl_debit,  SUM(r.recomputed_debit)  AS recomputed_debit,
       SUM(g.credit_movement) AS gl_credit, SUM(r.recomputed_credit) AS recomputed_credit,
       SUM(g.debit_movement)  - SUM(r.recomputed_debit)  AS debit_variance,
       SUM(g.credit_movement) - SUM(r.recomputed_credit) AS credit_variance,
       ABS(SUM(g.debit_movement) - SUM(r.recomputed_debit))
         / NULLIF(ABS(SUM(g.debit_movement)), 0) AS debit_variance_pct
FROM finance.gl_balance g
FULL OUTER JOIN recomputed r ON <same five-column join as 10.CK.02/10.CK.03>
GROUP BY <dimension>
```

`reconciliation_status` per row: `PASS` if `variance_pct < 0.001`, `WARNING` if `< 0.01`, `FAIL` otherwise - the same thresholds `reconciliation.rc_batch_control.status` already fixes ([05](../features/05-ai-closed-loop-validation.md#reconciliation-control-schema)), reused rather than reinvented. Per the detectability analysis, `currency` and `accounting_date` are expected to `PASS` regardless of how much misclassification exists elsewhere (neither dimension is substituted with an expected value); `legal_entity`, `gl_account`, and `cost_center` are the three dimensions capable of showing a genuine `WARNING`/`FAIL`.

**presentation** - one summary table per dimension (source/GL amount, variance, variance %, status) in the notebook, carried into the reconciliation-results write-up.

**expected findings** - per the detectability analysis, this reconciliation is expected to find a nonzero gap only on `legal_entity`, `gl_account`, and `cost_center`, driven by whatever misclassification exists in [04](../features/04-seed-mock-data.md#injected-issue-catalog--assessment-2)'s injected `incorrect_legal_entity`/`incorrect_cost_center` populations (plus any unambiguous GL-account misclassification Task 2 finds) - not by duplicate entries, the debit/credit indicator, late posting, missing mappings, or FX conversion, all five of which are expected to leave this reconciliation clean by design. Issue 12 (`opening + debit - credit != closing`, injected directly into `gl_balance`) is caught by **10.CK.01** instead, independent of this recomputation.

### mapping validation design - task 2

**join key** - `ref.accounting_mapping.transaction_type` and `bronze.finance_transactions.debit_credit_indicator` carry the same domain (`DEBIT`/`CREDIT`) under different column names; every check below effective-dates the join on the transaction's own `transaction_date` (not `posting_date` - the mapping rule governs which policy applied when the transaction occurred, independent of when it was later posted):

```sql
FROM bronze.finance_transactions t
JOIN ref.accounting_mapping m
  ON  t.product_code = m.product_code
  AND t.debit_credit_indicator = m.transaction_type
  AND t.transaction_date >= m.effective_start_date
  AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
```

**10.CK.09 - expected GL account**

```sql
SELECT t.transaction_id, t.product_code, t.gl_account AS actual_gl,
       m.expected_gl_account, t.posting_date AS accounting_date,
       'GL_MISMATCH' AS exception
FROM bronze.finance_transactions t
JOIN ref.accounting_mapping m
  ON  t.product_code = m.product_code AND t.debit_credit_indicator = m.transaction_type
  AND t.transaction_date >= m.effective_start_date
  AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
WHERE t.gl_account <> m.expected_gl_account
```

If the join returns more than one mapping row per transaction (an overlapping-range case, **10.CK.12**), every matched row is evaluated independently rather than one being picked arbitrarily - a transaction is `GL_MISMATCH` if it disagrees with *any* matched mapping, so an overlap never hides a genuine misclassification behind whichever row happens to sort first.

**10.CK.10 - effective-date validity** - a transaction whose `(product_code, debit_credit_indicator)` exists in `ref.accounting_mapping` but for which no row's window covers `transaction_date` is `NO_EFFECTIVE_MAPPING`:

```sql
SELECT t.transaction_id, t.product_code, t.debit_credit_indicator
FROM bronze.finance_transactions t
WHERE EXISTS (
  SELECT 1 FROM ref.accounting_mapping m
  WHERE m.product_code = t.product_code AND m.transaction_type = t.debit_credit_indicator
)
AND NOT EXISTS (
  SELECT 1 FROM ref.accounting_mapping m
  WHERE m.product_code = t.product_code AND m.transaction_type = t.debit_credit_indicator
    AND t.transaction_date >= m.effective_start_date
    AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
)
```

**10.CK.11 - missing mapping** - distinguished from **10.CK.10** by whether *any* row exists for the `(product_code, transaction_type)` pair at all, not just whether one covers the right date:

```sql
SELECT t.transaction_id, t.product_code, t.debit_credit_indicator
FROM bronze.finance_transactions t
WHERE NOT EXISTS (
  SELECT 1 FROM ref.accounting_mapping m
  WHERE m.product_code = t.product_code AND m.transaction_type = t.debit_credit_indicator
)
```

**10.CK.12 - overlapping effective-date ranges** - two mapping rows for the same `(product_code, transaction_type)` whose windows intersect:

```sql
SELECT a.product_code, a.transaction_type, a.effective_start_date, a.effective_end_date,
       b.effective_start_date AS overlap_start, b.effective_end_date AS overlap_end
FROM ref.accounting_mapping a
JOIN ref.accounting_mapping b
  ON  a.product_code = b.product_code AND a.transaction_type = b.transaction_type
  AND a.effective_start_date < b.effective_start_date
  AND a.effective_start_date <= COALESCE(b.effective_end_date, DATE '9999-12-31')
  AND COALESCE(a.effective_end_date, DATE '9999-12-31') >= b.effective_start_date
```

(`a.effective_start_date < b.effective_start_date` breaks the symmetric self-join into one row per overlapping pair rather than two.)

**10.CK.13 - expired mapping still referenced**

```sql
SELECT t.transaction_id, m.product_code, m.effective_end_date, t.transaction_date
FROM bronze.finance_transactions t
JOIN ref.accounting_mapping m
  ON t.product_code = m.product_code AND t.debit_credit_indicator = m.transaction_type
WHERE m.effective_end_date IS NOT NULL
  AND t.transaction_date > m.effective_end_date
  AND NOT EXISTS ( -- no *other*, currently-valid mapping row exists for this transaction
    SELECT 1 FROM ref.accounting_mapping m2
    WHERE m2.product_code = t.product_code AND m2.transaction_type = t.debit_credit_indicator
      AND t.transaction_date >= m2.effective_start_date
      AND (t.transaction_date <= m2.effective_end_date OR m2.effective_end_date IS NULL)
  )
```

The `NOT EXISTS` clause is what separates this from **10.CK.09**: a transaction can reference an expired row while *also* having a currently-valid mapping row it should have used instead - that combination is `GL_MISMATCH` (posted against the wrong, expired GL account), not `EXPIRED_MAPPING`. **10.CK.13** fires only when the expired row is the sole candidate.

**10.CK.14 - product mapped to multiple GL accounts unexpectedly**

```sql
SELECT product_code, transaction_type, COUNT(DISTINCT expected_gl_account) AS gl_account_count
FROM ref.accounting_mapping
WHERE effective_end_date IS NULL OR effective_end_date >= CURRENT_DATE
GROUP BY product_code, transaction_type
HAVING COUNT(DISTINCT expected_gl_account) > 1
```

Distinct from **10.CK.12**: this flags currently-active rows (open-ended or not yet expired) that disagree on `expected_gl_account` - a genuine data conflict rather than a time-ordered supersession. Two active rows can have non-overlapping windows and still trip this check if both windows are current and they disagree.

**exception output** - the assignment's own shape: `Transaction, Product, Actual GL, Expected GL, Accounting Date, Exception`, one row per flagged transaction, `Exception` populated from the closed vocabulary in [exception dataset](#exception-dataset).

### variance investigation design - task 3

**seven candidates, seven designed checks** - [GL integrity design](#gl-integrity-design--task-1)'s detectability analysis only answers whether a candidate can make *that* Ledger-vs-transaction movement reconciliation disagree; it says nothing about whether the candidate is detectable at all. Six of the assignment's seven named candidate causes have their own direct, independent detection method that never depends on the Ledger reconciliation succeeding, and each is designed below in its own right: **10.CK.15**/**10.CK.16** (duplicate/re-posted entries, a hash collision over the transaction data itself), **10.CK.17** (the debit/credit indicator, a mapping-consistency check independent of the Ledger - see below), **10.CK.18** (incorrect FX conversion, `local_amount` checked against its own inputs), **10.CK.19** (missing accounting mapping, a direct join failure against `ref.accounting_mapping`), and **10.CK.20** (posted one day late, `posting_date` compared to `transaction_date` directly). Late posting's raw detection is independent and designed below, but a second step some designs use to confirm each candidate against the Ledger's per-day shortfall is not - that confirmation is the ruled-out Ledger mechanism itself and is guaranteed to reject every candidate regardless of the data. The remaining two candidates - incorrect legal-entity allocation and incorrect cost-center/GL-account assignment - are the ones the screening marks conditionally detectable, and are also the only two bridged against [GL integrity design](#gl-integrity-design--task-1)'s recomputation, each at twice face value (a misclassified transaction's value is missing from its correct bucket and present in its wrong one); **10.CK.17**'s own findings feed into that same recomputation's classification lookup (see its implementation decision) without being part of the bridge themselves, since the indicator stays pass-through to the Ledger's movement figures regardless.

**10.CK.15 - duplicate accounting entry** - hash the business fields (every column except `transaction_id`) and find hash collisions across distinct `transaction_id`s posted on the same `posting_date`:

```sql
SELECT transaction_id, account_id, posting_date, local_amount,
       MD5(CONCAT_WS('|', account_id, posting_date, transaction_amount, currency,
                      debit_credit_indicator, product_code, gl_account, cost_center)) AS entry_hash
FROM bronze.finance_transactions
-- rows sharing entry_hash + posting_date but a different transaction_id are the duplicate group
```

Every row in an `entry_hash` group of size > 1 is flagged except the first (ordered by `transaction_id`); the *extra* rows' `local_amount` is reported as this category's finding - per the detectability analysis, not a contribution to [GL integrity design](#gl-integrity-design--task-1)'s variance, since a duplicate's value is aggregated into the Ledger identically to how it appears in the recomputation.

**10.CK.16 - transaction posted twice under a different id** - the same hash-collision query as **10.CK.15** (the hash deliberately excludes `transaction_id`, so a same-fields/different-id repost is already caught there); this is a second `issue_type` label applied to the same detected rows, kept separate only because the assignment names the two scenarios independently.

**10.CK.17 - incorrect debit/credit indicator** - `ref.accounting_mapping` keys the expected GL account and cost center off *both* the product code and the debit/credit indicator, so a transaction carrying the wrong indicator doesn't just fail to match its own mapping row - its actual posted classification often becomes an exact match for a *different*, valid mapping row under the opposite indicator. That is a distinguishable signature (every field right, filed under the wrong sign), independent of the Ledger entirely:

```sql
WITH current_match AS (
  SELECT t.transaction_id,
         MAX(CASE WHEN t.gl_account = m.expected_gl_account
                   AND t.cost_center = m.expected_cost_center THEN 1 ELSE 0 END) AS matches_current
  FROM bronze.finance_transactions t
  JOIN ref.accounting_mapping m
    ON t.product_code = m.product_code AND t.debit_credit_indicator = m.transaction_type
    AND t.transaction_date >= m.effective_start_date AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
  GROUP BY t.transaction_id
),
opposite_match AS (
  SELECT t.transaction_id,
         MAX(CASE WHEN t.gl_account = m.expected_gl_account
                   AND t.cost_center = m.expected_cost_center THEN 1 ELSE 0 END) AS matches_opposite
  FROM bronze.finance_transactions t
  JOIN ref.accounting_mapping m
    ON t.product_code = m.product_code
    AND m.transaction_type = CASE WHEN t.debit_credit_indicator = 'DEBIT' THEN 'CREDIT' ELSE 'DEBIT' END
    AND t.transaction_date >= m.effective_start_date AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
  GROUP BY t.transaction_id
)
SELECT t.transaction_id, t.product_code, t.debit_credit_indicator, t.gl_account, t.cost_center, t.local_amount
FROM bronze.finance_transactions t
LEFT JOIN current_match cm ON t.transaction_id = cm.transaction_id
JOIN opposite_match om ON t.transaction_id = om.transaction_id
WHERE COALESCE(cm.matches_current, 0) = 0 AND om.matches_opposite = 1
```

A transaction matching more than one active mapping row under either indicator is treated as matching if *any* row matches (`MAX(...)` over the group), consistent with **10.CK.09**'s own fan-out handling. Structurally can't confirm a transaction with no active mapping row at all under the opposite indicator - genuinely nothing to swap-match against, not a method weakness.

**10.CK.18 - incorrect FX conversion** - the same tolerance check Assessment 1 uses for its own FX field ([09.CK.10](09-as01-data-profiling-reconciliation.md#profiling-design--task-1)):

```sql
SELECT transaction_id, transaction_amount, exchange_rate, local_amount,
       ROUND(transaction_amount * exchange_rate, 2) AS expected_local_amount,
       local_amount - ROUND(transaction_amount * exchange_rate, 2) AS fx_variance
FROM bronze.finance_transactions
WHERE ABS(local_amount - ROUND(transaction_amount * exchange_rate, 2)) > 0.01
```

**10.CK.19 - missing accounting mapping** - the `local_amount` sum of every transaction flagged by **10.CK.10** (no effective mapping) or **10.CK.11** (missing mapping). Per [GL integrity design](#gl-integrity-design--task-1)'s detectability analysis this is a disclosure figure, not a variance contribution: with no expected value to substitute, these transactions keep their actual classification in that design's recomputation on both sides, so their value cannot register as a bridgeable gap - a transaction with no valid mapping simply cannot be confirmed correct or incorrect, which is the finding itself, not folded into **10.CK.09**'s `GL_MISMATCH` count.

**10.CK.20 - transaction posted one accounting day late** - candidates are transactions whose `posting_date` is exactly one calendar day after `transaction_date`:

```sql
SELECT posting_date, transaction_date, transaction_id, local_amount
FROM bronze.finance_transactions
WHERE posting_date = transaction_date + INTERVAL '1 day'
```

Reported as-is, with no attempt to confirm a candidate against [GL integrity design](#gl-integrity-design--task-1)'s per-day variance: the Ledger is aggregated using each transaction's own (possibly late) posting date, so the Ledger and the recomputation already agree on where it lands and there is no shortfall left to match against, by the same reasoning the screening applies to this candidate. This means the raw candidate count may include a transaction the bank's own processing calendar legitimately posts a day later (e.g. a weekend transaction posted the next business day) alongside a genuine late-posting error - this design has no test available that tells the two apart.

**10.CK.21 - incorrect legal-entity allocation** - one of the two categories [GL integrity design](#gl-integrity-design--task-1)'s detectability analysis marks conditionally detectable: this majority-vote value is exactly the "expected" substitution that design's recomputation applies for `legal_entity`, so this check's flagged transactions are where that design's own legal-entity variance traces to, not a separate, unrelated finding. `ref.accounting_mapping` carries no `expected_legal_entity` column, so this is a majority-vote check per `account_id`: an account's legal entity is expected to be stable, so a transaction whose `legal_entity` disagrees with that account's most-frequent posted value elsewhere in the seeded period is a probable misallocation:

```sql
WITH account_entity_mode AS (
  SELECT account_id, legal_entity, COUNT(*) AS n,
         ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY COUNT(*) DESC) AS rnk
  FROM bronze.finance_transactions
  GROUP BY account_id, legal_entity
)
SELECT t.transaction_id, t.legal_entity AS actual_entity, e.legal_entity AS expected_entity
FROM bronze.finance_transactions t
JOIN account_entity_mode e ON t.account_id = e.account_id AND e.rnk = 1
WHERE t.legal_entity <> e.legal_entity
```

**10.CK.22 - incorrect cost-center assignment** - the second conditionally-detectable category, and (with **10.CK.09**'s GL-account misclassification, where unambiguous) the other input to [GL integrity design](#gl-integrity-design--task-1)'s recomputation's `cost_center` substitution. Unlike legal entity, `ref.accounting_mapping.expected_cost_center` exists, so this reuses **10.CK.09**'s effective-dated join directly, excluding **10.CK.17**'s own transactions: a transaction whose indicator is wrong looks wrong on cost center only when checked against the wrong-indicator mapping row, not against the one its actual indicator implies - the indicator, not the cost center, is the finding for those:

```sql
SELECT t.transaction_id, t.cost_center AS actual_cost_center, m.expected_cost_center
FROM bronze.finance_transactions t
JOIN ref.accounting_mapping m
  ON t.product_code = m.product_code AND t.debit_credit_indicator = m.transaction_type
  AND t.transaction_date >= m.effective_start_date
  AND (t.transaction_date <= m.effective_end_date OR m.effective_end_date IS NULL)
WHERE t.cost_center <> m.expected_cost_center
  AND t.transaction_id NOT IN (SELECT transaction_id FROM flip_candidates)  -- 10.CK.17, see above
```

**scale note** - the standard wording stating measured values come from the seeded volume budget, with the assignment's SGD 3,222,215.72 figure cited as the scenario framing, not the seeded target.

**affected dimensions** - the legal entities, GL accounts, and cost centers carrying the largest share of **10.CK.21**/**10.CK.22**'s bridgeable variance (per the detectability analysis, `currency` and `accounting_date` are not expected to show one).

### reconciliation framework design - task 4

This is a design deliverable, not new code - the framework it specifies already exists as `reconciliation.rc_*` ([05](../features/05-ai-closed-loop-validation.md#reconciliation-control-schema)); task 4 documents how that existing schema satisfies the assignment's ask, and where it would need to extend.

**10.CK.23 - metrics** - this dataset has no separate raw-source ingestion tier the way Assessment 1's `src_transaction_daily` does (no `source.*` schema for finance) - `bronze.finance_transactions` is the earliest tier available, so `source_count`/`source_amount` and `bronze_count`/`bronze_amount` are measured as the same value for this assessment; the split is kept in the vocabulary only so the metric names stay uniform with Assessment 1/3's frameworks, and the design states this explicitly rather than leaving two identical numbers unexplained.

| metric              | expression                                                          |
| -------------------- | -------------------------------------------------------------------- |
| `source_count`        | `SELECT COUNT(*) FROM bronze.finance_transactions`                    |
| `bronze_count`        | same query as `source_count` (see note above)                         |
| `gl_transaction_count`| `SELECT COUNT(*) FROM finance.gl_balance`                             |
| `source_amount`       | `SELECT SUM(local_amount) FROM bronze.finance_transactions`           |
| `bronze_amount`       | same query as `source_amount`                                         |
| `gl_amount`           | `SELECT SUM(closing_balance) FROM finance.gl_balance`                 |
| `absolute_variance`   | `gl_amount - source_amount`                                           |
| `percentage_variance` | `ABS(gl_amount - source_amount) / NULLIF(ABS(source_amount), 0)`      |
| `exception_count`     | `COUNT(*)` across the unioned [exception dataset](#exception-dataset) |
| `reconciliation_status` | `PASS`/`WARNING`/`FAIL` per the thresholds below                    |

Each row lands in `reconciliation.rc_reconciliation_results` with `dimension` carrying the metric name and `source_value`/`target_value`/`variance`/`variance_pct`/`reconciliation_status` populated from the table above:

```sql
INSERT INTO reconciliation.rc_reconciliation_results
  (batch_id, dimension, source_value, target_value, variance, variance_pct, reconciliation_status)
SELECT :batch_id, 'gl_amount', s.source_amount, g.gl_amount,
       g.gl_amount - s.source_amount AS variance,
       ABS(g.gl_amount - s.source_amount) / NULLIF(ABS(s.source_amount), 0) AS variance_pct,
       CASE
         WHEN ABS(g.gl_amount - s.source_amount) / NULLIF(ABS(s.source_amount), 0) < :pct_warning THEN 'PASS'
         WHEN ABS(g.gl_amount - s.source_amount) / NULLIF(ABS(s.source_amount), 0) < :pct_fail    THEN 'WARNING'
         ELSE 'FAIL'
       END
FROM (SELECT SUM(local_amount) AS source_amount FROM bronze.finance_transactions) s
CROSS JOIN (SELECT SUM(closing_balance) AS gl_amount FROM finance.gl_balance) g
```

**tolerance rules** - absolute, percentage, currency-specific, and account-specific tolerance, expressed as a design proposal for a `rc_tolerance_rules`-shaped lookup, not a table this tracker adds (doing so is a [05](../features/05-ai-closed-loop-validation.md) change if adopted):

```
rc_tolerance_rules(assessment_id, dimension, currency NULL=all, gl_account NULL=all,
                    abs_tolerance, pct_warning, pct_fail)
```

`currency`/`gl_account` are nullable wildcard columns; the most specific non-null match wins in the order `(currency, gl_account)` > `currency only` > `(NULL, NULL)` default row, so `:pct_warning`/`:pct_fail` above are resolved by that lookup rather than hardcoded per call site.

**status assignment** - `PASS`/`WARNING`/`FAIL` default to the thresholds `reconciliation.rc_batch_control.status` already establishes (per [05](../features/05-ai-closed-loop-validation.md#reconciliation-control-schema): `PASS` under 0.1%, `WARNING` under 1%, `FAIL` at or above 1%), overridable per currency/GL account by the tolerance-rule lookup above.

**persistence for audit/historical analysis** - answered by `rc_batch_control`'s existing append-only design ([05](../features/05-ai-closed-loop-validation.md#idempotency--rerun-safety)): every daily run inserts a new batch rather than overwriting, so history is a `SELECT ... WHERE assessment_id = 'assessment-2' ORDER BY batch_date` away.

### exception dataset

- **schema** - at minimum `transaction_id`, `issue_type`, `source_value`, `bronze_value`/`gl_value`, `variance`, `batch_id`, mirroring [09](09-as01-data-profiling-reconciliation.md#exception-dataset)'s minimum columns adapted to this assessment's GL-vs-transaction comparison
- **materialisation** - table, notebook output, or embedded markdown extract, with the full row set's location stated where the write-up shows only a sample
- **ground-truth check** - the comparison against `issue-log.csv` proving detected issues match injected ones

**issue_type vocabulary** - the closed set of string values every check writes, one per check id, matched against `issue-log.csv`'s own `issue_type` spelling so ground-truth comparison is a direct join:

| check id | `issue_type`             |
| -------- | -------------------------- |
| 10.CK.09 | `GL_MISMATCH`                |
| 10.CK.10 | `NO_EFFECTIVE_MAPPING`       |
| 10.CK.11 | `MAPPING_NOT_FOUND`          |
| 10.CK.12 | `OVERLAPPING_MAPPING`        |
| 10.CK.13 | `EXPIRED_MAPPING`            |
| 10.CK.14 | `MULTI_GL_MAPPING`           |
| 10.CK.15 | `DUPLICATE_ENTRY`            |
| 10.CK.16 | `DUPLICATE_REPOST`           |
| 10.CK.17 | `WRONG_DR_CR_INDICATOR`      |
| 10.CK.18 | `FX_CONVERSION_ERROR`        |
| 10.CK.19 | `UNMAPPED_VARIANCE`          |
| 10.CK.20 | `LATE_POSTING`               |
| 10.CK.21 | `WRONG_LEGAL_ENTITY`         |
| 10.CK.22 | `WRONG_COST_CENTER`          |

01. a row may legitimately carry more than one `issue_type` for the same `transaction_id` (e.g. `WRONG_DR_CR_INDICATOR` and `FX_CONVERSION_ERROR` both true) - the exception dataset is one row per `(transaction_id, issue_type)` pair, not one row per transaction, so `exception_count` in [reconciliation framework design](#reconciliation-framework-design--task-4) counts flagged pairs.

### advanced sql coverage

The assignment asks for "several" of ten named techniques, not all ten; this tracker commits to a specific subset so 10.10's notebook consolidation has a concrete checklist rather than a vague aspiration.

| id       | technique                | where it is used                                              |
| -------- | --------------------------- | ------------------------------------------------------------------ |
| 10.SQ.01 | CTEs                        | staged recomputation (transactions -> movements -> variance)        |
| 10.SQ.02 | window functions            | ranking largest-variance dimension combinations (task 1/3)          |
| 10.SQ.03 | conditional aggregation     | debit/credit split from `debit_credit_indicator` in one pass        |
| 10.SQ.04 | effective-dated joins       | `ref.accounting_mapping` join, task 2                                |
| 10.SQ.05 | deduplication                | duplicate/re-posted accounting entry detection, task 3               |
| 10.SQ.06 | exception categorization    | the closed `issue_type` vocabulary applied across tasks 2-3           |

01. `MERGE`, hash comparison, ranking (beyond window-function ranking already covered), and incremental processing are not committed to a specific cell - if a natural fit appears during 10.04-10.07 it is added and this table updated, but they are not required to close this tracker.

### notebook organisation

`notebooks/assessment2_gl_reconciliation.ipynb` is the single executable artifact for this assessment, sectioned in assignment order - connectivity, task 1 GL integrity, task 2 mapping validation, task 3 variance investigation, task 4 framework demonstration - so a deliverable's **Sources** reference can name a section rather than a cell index that shifts on edit. Output commit policy follows [07](../features/07-jupyter-notebook-workspace-setup.md); the notebook must execute cleanly top to bottom against a freshly seeded database before 10.10 closes.

### idempotency / rerun-safety

- **notebook** - re-executable end to end against a freshly seeded database with no manual cell ordering; any writes it makes are keyed by `batch_id` so a rerun appends a new batch rather than mutating a prior one.
- **control tables** - reruns insert a new `rc_batch_control` row (`assessment_id = 'assessment-2'`); existing batches are never updated in place, preserving the evidence a published deliverable already cites.
- **deliverable markdown** - authored content, never regenerated by a script; `07-deliverables-scaffold.sh` remains verify-or-create and only the derived `README.md` manifest is rewritten.
- **seed data** - regenerated only by `scripts/03-mock-data-seed.sh`, which is deterministic under the fixed `MOCK_DATA_SEED`; this tracker never edits seeded rows directly.

### environment & secrets

No new variables and no new secrets. The work reuses the existing postgres connection settings, `LOGS_DIR`, `TIMEZONE`, and `TIMESTAMP_FORMAT` from `.env`. Credentials are never written into a notebook cell, a deliverable markdown file, or the published site.

### workflow validation runner

Assessment 2 introduces no new runner by default; validation composes the existing scripts in [prerequisites](#prerequisites) plus `scripts/06-notebook-validate.sh` for headless notebook execution and `scripts/07-deliverables-scaffold.sh --check` for deliverable completeness. If a per-assessment orchestration step proves necessary, it is added as the next free script number and logged under `.dev/logs/` with `<ts>-10.<nn>-<name>.log` naming, printing one `[PASS]`/`[FAIL]` line per stage of the [workflow cycle](#workflow-cycle).

### publishing

Once every deliverable is promoted to `status: final`, `scripts/07-deliverables-scaffold.sh` regenerates the Assessment 2 manifest with the updated statuses, `scripts/08-assessment-site.sh build` validates the strict MkDocs build, and `scripts/08-assessment-site.sh deploy` publishes to `gh-pages` from a clean, reviewed worktree. The overview page must be reachable from the published navigation before deploy. Deployment is never run with uncommitted assessment evidence in the tree.

## Test cases

_test strategy_

Findings are validated at three layers so a measurement is never trusted on the strength of the write-up alone:

1. **script self-report** - `[PASS]`/`[FAIL]` lines and timestamped logs from the prerequisite and validation scripts show each stage ran.
2. **ground-truth comparison** - detected issues are joined against `data/mock/issue-log.csv`, the injected catalog from [04](../features/04-seed-mock-data.md), rather than eyeballed.
3. **content inspection** - deliverable markdown is checked for required headings, `status:` markers, context and source references, and table shape independently of the notebook that produced the numbers.

_test cases_

| id       | task  | layer        | check                                        |
| -------- | ----- | ------------ | -------------------------------------------- |
| 10.TC.01 | 10.02 | script       | all prerequisite steps report `[PASS]`        |
| 10.TC.02 | 10.02 | ground-truth | seeded issue counts match the issue log       |
| 10.TC.03 | 10.03 | content      | overview states scenario, tasks, and scale    |
| 10.TC.04 | 10.03 | content      | every deliverable links the overview page     |
| 10.TC.05 | 10.04 | content      | GL arithmetic violations reported with counts |
| 10.TC.06 | 10.04 | ground-truth | violation counts match injected issue rows    |
| 10.TC.07 | 10.04 | script       | task 1 results land in `rc_*` for one batch   |
| 10.TC.08 | 10.05 | content      | mapping exception table carries six columns   |
| 10.TC.09 | 10.05 | ground-truth | mapping exceptions reconcile to the issue log |
| 10.TC.10 | 10.06 | content      | exception dataset carries the minimum columns |
| 10.TC.11 | 10.07 | content      | variance decomposition sums to stated total   |
| 10.TC.12 | 10.08 | content      | framework maps each metric onto `rc_*`        |
| 10.TC.13 | 10.09 | content      | business summary states findings in plain terms |
| 10.TC.14 | 10.10 | script       | notebook executes clean top to bottom         |
| 10.TC.15 | 10.11 | content      | every deliverable reads `status: final`       |
| 10.TC.16 | 10.12 | build        | strict MkDocs build succeeds                  |
| 10.TC.17 | 10.12 | deployment   | published site shows assessment 2 pages       |

**tools**

```bash
cd /home/taylor-hickem/repos/de-financial-accounting-demo
./scripts/00-prereq-check.sh
./scripts/03-mock-data-seed.sh
./scripts/04-mock-data-validate.sh
./scripts/06-notebook-validate.sh
./scripts/07-deliverables-scaffold.sh --check
./scripts/08-assessment-site.sh build
grep -R --line-number '^status: \(draft\|final\)$' results/assessment-2
grep -RL 'assessment-2-overview.md' results/assessment-2/assessment-2-*.md
awk '/^\|/ && length($0) >= 115 { print FILENAME ":" FNR ": row too long"; bad = 1 } END { exit bad }' results/assessment-2/*.md
```

## Edit locations

| id       | path                                                           | change                        |
| -------- | ---------------------------------------------------------------- | ------------------------------ |
| 10.EL.01 | `notebooks/assessment2_gl_reconciliation.ipynb`                  | full analysis notebook         |
| 10.EL.02 | `results/assessment-2/assessment-2-reconciliation-results.md`    | task 1 write-up                |
| 10.EL.03 | `results/assessment-2/assessment-2-mapping-validation.md`        | task 2 write-up                |
| 10.EL.04 | `results/assessment-2/assessment-2-exception-dataset.md`         | task 3 exception write-up      |
| 10.EL.05 | `results/assessment-2/assessment-2-root-cause-analysis.md`       | task 3 variance write-up       |
| 10.EL.06 | `results/assessment-2/assessment-2-framework-design.md`          | task 4 write-up                |
| 10.EL.07 | `results/assessment-2/assessment-2-business-summary.md`          | business-facing summary        |
| 10.EL.08 | `results/assessment-2/README.md`                                 | regenerated manifest           |
| 10.EL.09 | `src/sparksql/`                                                   | reusable query files           |
| 10.EL.10 | `docs/milestones.md`                                              | milestone 10 status/closure    |
| 10.EL.11 | `results/assessment-2/assessment-2-overview.md`                  | assessment scope context       |
| 10.EL.12 | `results/index.md`                                                | link to the overview page      |
| 10.EL.13 | `mkdocs.yml`                                                      | overview in site nav           |

01. **10.EL.08** is generated by `scripts/07-deliverables-scaffold.sh`; never hand-edited.
02. **10.EL.09** is optional - used only where a query is worth extracting from the notebook for reuse, following the existing `src/pyspark/` naming pattern.
03. **10.EL.11** is authored content outside feature 08's generated taxonomy, so the scaffold neither creates nor validates it; it is created by hand in 10.03.
04. **10.EL.13** is only required if the strict build cannot reach the overview through `10.EL.12`'s link alone.

No `.env`, `.env.sample`, schema JSON, DDL, or seed-script change is expected. A required change to any of those is a defect in the owning feature and is raised there rather than patched from this tracker.

## Implement

Implementation order is prerequisites -> assessment context -> GL integrity -> mapping validation -> exceptions -> variance investigation -> framework design -> business summary -> notebook rerun -> review -> publish. Each step runs the full [workflow cycle](#workflow-cycle) before the next begins.

### 1. Prerequisites and seed data readiness

edit locations: none

_closed 10.02_ - ran every [prerequisites](#prerequisites) step in order; the host VM restarted mid-session (all containers exited 255, uptime reset), so the full sequence was rerun end to end from a cold state for the evidence below:

| id       | evidence observed                                              |
| -------- | ------------------------------------------------------------------ |
| 10.PR.01 | `[PASS]` docker 29.7.2 + python3.14 + venv module                  |
| 10.PR.02 | `[PASS]` DDL applied; 12 non-system tables confirmed [01]          |
| 10.PR.03 | `[PASS]` `docker ps`: 5/5 full-profile containers `Up`             |
| 10.PR.04 | `[PASS]` `bronze.finance_transactions`/`gl_balance`/`accounting_mapping` = 1523/589/22 rows [02] |
| 10.PR.05 | `[PASS]` all row-count and ground-truth checks vs. `issue-log.csv` [03] |
| 10.PR.06 | `[PASS]` connectivity notebook executed clean in 22s [04]          |
| 10.PR.07 | `[PASS]` `07-deliverables-scaffold.sh --check` current for all three assessments |

01. **10.PR.02** direct `information_schema.tables` query, spanning `public/bronze/finance/ref/reconciliation/regulatory/source`.
02. **10.PR.04** identical counts on a second reseed - deterministic under `MOCK_DATA_SEED=42`.
03. **10.PR.05** 300 rows/34 categories overall; includes `gl_balance arithmetic violations >= 3: 5` and `overlapping/duplicate mapping rows... >= 3: 6`.
04. **10.PR.06** summary marker `[PASS] 00-template-connectivity-check: overall status=PASS`; first failed twice under host resource contention (`CellTimeoutError` at 120s, then a diagnostic 300s) - diagnosed and closed as [10.IS.01](#validate) before this clean-rerun evidence was captured.

Independent direct-SQL inspection (bypassing the seed/validate scripts' own self-report) confirmed the same baseline: `SELECT COUNT(*)` on all three Assessment 2 tables matched the seed log exactly, and the tracker's own [10.CK.01](#gl-integrity-design--task-1) arithmetic-integrity query against `finance.gl_balance` returned 5 violations, matching `issue-log.csv`'s `arithmetic_integrity_violation` count exactly.

Baseline for later ground-truth comparison, from `bronze.finance_transactions`'s 61 issue-log rows (1523 total rows / 1523 distinct `transaction_id`): 15 `duplicate_accounting_entry`, 8 `posted_twice_different_id`, 10 `incorrect_dr_cr_indicator`, 3 `incorrect_fx_conversion`, 12 `posted_one_day_late`, 6 `incorrect_legal_entity`, 7 `incorrect_cost_center`; `finance.gl_balance`'s 5 `arithmetic_integrity_violation` rows; `ref.accounting_mapping`'s 7 rows (2 `expired_mapping_still_used`, 3 `overlapping_effective_dates`, 2 `product_multiple_gl_accounts`).

### 2. Assessment scope and context write-up

edit locations: `10.EL.11, 10.EL.12, 10.EL.13`

_closed 10.03_ - authored [`results/assessment-2/assessment-2-overview.md`](../../results/assessment-2/assessment-2-overview.md): the scenario verbatim from `docs/design/assignment.md`'s Assessment 2 section, all three table shapes (columns matched 1:1 against `data/schemas/as02-*-schema.json`, not re-typed from the assignment prose), Tasks 1-4, the expected deliverable list, and the scale statement (SGD 8,428,770,121.46 expected / SGD 8,431,992,337.18 platform / SGD 3,222,215.72 variance at production scale vs. this seed run's 1,523/589-row budget). Linked from `results/index.md`. `mkdocs.yml` nav (`10.EL.13`) was **not** touched - the strict build reaches the overview through that link alone (confirmed at 10.04's `07-deliverables-scaffold.sh --check` pass), per the design footnote.

This step was done before the task 1 write-up so its deliverable could be authored with its context line already pointing at an existing page.

### 3. Task 1 - GL integrity and reconciliation

edit locations: `10.EL.01, 10.EL.02`

_closed 10.04_ - **10.CK.01**-**10.CK.08** implemented in `notebooks/assessment2_gl_reconciliation.ipynb`'s "Task 1 - GL Integrity and Reconciliation" section, executed headlessly against the freshly seeded database (containers came up cold - see [10.02](#1-prerequisites-and-seed-data-readiness)'s evidence table for that seed run's baseline).

| check                | result                                          |
| ---------------------- | -------------------------------------------------- |
| 10.CK.01 arithmetic     | 5 violations (589 rows checked) [01]              |
| 10.CK.02/10.CK.03 recompute | 284/589 keys exceed the 0.01 movement tolerance |
| 10.CK.04-10.CK.08 dimensional | every dimension `FAIL`s except `currency=SGD` [02] |

01. **10.CK.01** matches `issue-log.csv`'s `arithmetic_integrity_violation` count exactly.
02. **10.CK.04-10.CK.08** `currency=SGD` is `0.0%`; `EUR`/`USD` fail widest (45.78%/34.12%).

**implementation decision** - the first pass of 10.CK.01 cast `finance.gl_balance`'s four `decimal(20,2)` columns to `double` before comparing, which introduced floating-point rounding noise (`~1e-12`) and inflated the true 5 violations to 203 false ones; fixed by keeping that specific comparison in native decimal arithmetic (double stays safe for the 0.01-tolerance movement/dimensional checks further down, where the noise is far below the threshold). Caught by comparing against the direct-SQL ground truth already captured in [10.02](#1-prerequisites-and-seed-data-readiness)'s evidence, not left unnoticed.

`row_count` and `amount` (the two dimensions `reconciliation.rc_reconciliation_results.dimension`'s closed enum supports - the same constraint [09](09-as01-data-profiling-reconciliation.md#workflow-cycle) hit for its own level 1 totals) were written to a fresh `batch_id=12` (`assessment_id = 'assessment-2'`, the first row that assessment id has ever carried in `rc_batch_control`) - confirmed via direct SQL against `rc_reconciliation_results WHERE batch_id = 12`, independent of the notebook's own printed summary. Overall batch status: `FAIL`. Wrote [`results/assessment-2/assessment-2-reconciliation-results.md`](../../results/assessment-2/assessment-2-reconciliation-results.md) citing that batch and the overview page, and added the task 1 row to [`assessment-2-audit.md`](../../results/assessment-2/assessment-2-audit.md).

**superseded by [10.IS.02](#validate)** - the movement recomputation above (`10.CK.02`-`10.CK.08`, the "every dimension `FAIL`s except `currency=SGD`" finding) and the write-back `amount` dimension both used `local_amount` where the Ledger's own `debit_movement`/`credit_movement` are aggregated from `transaction_amount` - a basis error, confirmed directly against the seed generator's own GL-aggregation code and fixed in the notebook. Recomputing on `transaction_amount` alone (grouped by each transaction's actual classification): 0 of 589 keys exceeded tolerance - this result was itself superseded one step later.

**superseded again by [10.IS.03](#validate)** - user question: "wouldn't incorrect mapping cause a discrepancy between the [source] and the [GL]?" It should, and the 0.00 result above couldn't show it, because the recomputation grouped by each transaction's *actual* `gl_account`/`cost_center`/`legal_entity` - the same values the Ledger was built from - making the dimensional check tautological regardless of how much misclassification exists. Grouping instead by the *expected* classification (`ref.accounting_mapping` wherever unambiguous, majority-vote `legal_entity`, six genuinely-conflicting mapping combos excluded and left at actual): **34 of 589 keys exceed tolerance, 305,281.76 total variance** - legal entity and cost center both now `FAIL`/`WARNING`, currency and accounting date stay a clean `PASS` (unaffected by this substitution), and the write-back `amount` dimension still matches exactly (a grand total, unaffected by which bucket a transaction's value is classified into). Re-executed clean, a fresh `batch_id=20` written, `results/assessment-2/assessment-2-reconciliation-results.md` and the task 1 row in `assessment-2-audit.md` rewritten to these findings.

**superseded a third time by [10.IS.04](#validate)** - user challenge: "you only have two checks, that doesn't sound like a very comprehensive diagnostics." Re-deriving a detection method for the previously-ruled-out "incorrect debit/credit indicator" candidate (rather than accepting the prior ruling) surfaced that `10.IS.03`'s mapping lookup, keyed on each transaction's own posted indicator, would look up the wrong mapping row for a transaction whose indicator is itself wrong. Correcting the lookup to the indicator a transaction's own actual classification is consistent with, for those 9 transactions only: **30 of 589 keys exceed tolerance, 268,250.94 total variance**, GL account's worst case moves from `4.3023%` to `4.3972%` (GL1005 stays worst either way), legal entity/cost center/currency/accounting date unchanged at the dimension level. Re-executed clean, a fresh `batch_id=21` written, `results/assessment-2/assessment-2-reconciliation-results.md` and the task 1 row in `assessment-2-audit.md` rewritten again. See [10.IS.02](#validate), [10.IS.03](#validate), and [10.IS.04](#validate) for the full diagnostic trail from residual to root cause, in three stages.

### 4. Task 2 - accounting mapping validation

edit locations: `10.EL.01, 10.EL.03`

_closed 10.05_ - **10.CK.09**-**10.CK.14** implemented in `notebooks/assessment2_gl_reconciliation.ipynb`'s "Task 2 - Accounting Mapping Validation" section, via Spark SQL over temp views (`finance_transactions`, `accounting_mapping`) rather than the DataFrame API - the effective-dated join and the self-joins for overlap/multi-GL detection read directly as the design's own SQL, doubling as the notebook's effective-dated-joins demonstration. Executed headlessly against the same seeded database as 10.04, no cell errors.

| check                | result                                              |
| ----------------------- | ------------------------------------------------------ |
| 10.CK.09 GL_MISMATCH     | 403 rows / 319 distinct transactions                   |
| 10.CK.10 NO_EFFECTIVE_MAPPING | 0                                                  |
| 10.CK.11 MAPPING_NOT_FOUND | 385 rows                                              |
| 10.CK.12 OVERLAPPING_MAPPING | 8 pairs, 6 (product, type) combos                   |
| 10.CK.13 EXPIRED_MAPPING | 0                                                       |
| 10.CK.14 MULTI_GL_MAPPING | 4 (product, type) combos                               |

**finding** - 401 of 403 `GL_MISMATCH` rows (99.5%) sit on the same 6 `(product, type)` combos `10.CK.12`/`10.CK.14` independently flag as carrying conflicting mapping definitions - a mapping-data conflict, not scattered per-transaction miscoding; only 2 rows are a genuine unexplained residual. `MAPPING_NOT_FOUND`'s 385 rows all fall on 5 `(product, type)` combos with **no** mapping row at all - `ref.accounting_mapping`'s 22 rows structurally cover only 15 of the 20 combos transactions actually use.

**caught during review, fixed before publishing** - the first pass of the mapping-validation write-up mislabeled `P4/DEBIT` (4 rows) and `P8/CREDIT` (3 rows) as an unexplained residual; direct SQL against `10.CK.12`'s own overlapping-pairs query showed both combos are in fact covered by an overlapping mapping window, just not by `10.CK.14`'s multi-GL check - corrected the deliverable and audit before this step closed, dropping the residual from 9 rows to the genuine 2 (`P8/DEBIT`, `P3/DEBIT`).

**second catch, this one a real seed-data defect** - the first write-up also described `MAPPING_NOT_FOUND` as an unexplained "structural coverage gap" with no ground-truth tag to check it against, per user direction this was investigated rather than left as an assessment-level finding: `gen_assessment2()` (feature 04) has *always* deliberately injected this exact scenario (`missing_combos`, catalog issue 03) but never called `log_issue()` for it, unlike every sibling issue in the same function - so `issue-log.csv` genuinely had no row for it, this was not a misreading. Fixed at the source ([04.IS.03](../features/04-seed-mock-data.md)), reseeded (data unchanged - a logging-only fix, confirmed identical row counts), and this deliverable/the audit corrected to report `MAPPING_NOT_FOUND` as the intentional, exactly-matched issue category it is, not an open question.

Produced the exception output in the assignment's stated shape (`Transaction, Product, Actual GL, Expected GL, Accounting Date, Exception`, 788 rows across the four per-transaction checks - `10.CK.12`/`10.CK.14` are mapping-level and reported separately). Wrote [`results/assessment-2/assessment-2-mapping-validation.md`](../../results/assessment-2/assessment-2-mapping-validation.md) and the task 2 rows in [`assessment-2-audit.md`](../../results/assessment-2/assessment-2-audit.md).

### 5. Exception dataset

edit locations: `10.EL.01, 10.EL.04`

_closed 10.06_ - unioned the row sets from **10.CK.09**-**10.CK.14** (task 2's own checks) into the exception dataset's minimum columns (`transaction_id, issue_type, source_value, gl_value, variance`) - 788 rows total (403 `GL_MISMATCH`, 385 `MAPPING_NOT_FOUND`). **10.CK.15**-**10.CK.22** (task 3's categories) are not yet available and are explicitly deferred to [10.07](#6-task-3---finance-variance-investigation)'s cycle rather than restated ahead of that run, per [10.WS.04](#workflow-cycle)'s rule against restating a number the notebook did not produce in the same run. No `batch_id` per row - task 2/exception-dataset findings are cited by notebook section, not written to `reconciliation.rc_*`, per [workflow cycle](#workflow-cycle) note 01. Wrote [`results/assessment-2/assessment-2-exception-dataset.md`](../../results/assessment-2/assessment-2-exception-dataset.md), sampling in the markdown and pointing at the notebook's full cell output.

### 6. Task 3 - finance variance investigation

edit locations: `10.EL.01, 10.EL.05`

_closed 10.07_ - **10.CK.15**-**10.CK.22** implemented in the notebook's variance-investigation section, executed headlessly against the same seeded database as 10.04/10.05, no cell errors.

| check                     | result                                       |
| ---------------------------- | ------------------------------------------------ |
| 10.CK.15/16 duplicate entry    | one query covers both [01]                       |
| 10.CK.17 wrong dr/cr indicator | 0 candidates - see note below                     |
| 10.CK.18 FX conversion          | 3 rows, 4,467.53                                  |
| 10.CK.19 unmapped variance      | 385 rows, 4,387,367.89 - largest contribution      |
| 10.CK.20 late posting            | 12 raw candidates, 0 confirmed [02]              |
| 10.CK.21 wrong legal entity      | 6 rows, 60,697.50                                 |
| 10.CK.22 wrong cost center        | 8 distinct transactions [03]                     |

01. **10.CK.15/16** the design's own note: hash-collision detection can't distinguish the two named scenarios - 21 rows, 255,845.35.
02. **10.CK.20** the raw candidate count matches ground truth exactly; see note below on why confirmation still rejected all 12.
03. **10.CK.22** 11 raw rows before removing mapping-conflict join fan-out, 85,485.13.

**10.CK.17/10.CK.20 both underperformed against the ground truth** (0 found vs. 10 tagged; 0 confirmed vs. 12 tagged) - initially attributed to co-occurring variance swamping the signal at each key; **superseded by [10.IS.02](#validate)'s finding** that this is structural, not a swamped signal: `finance.gl_balance` is aggregated from the same (already-mutated) transaction rows these checks read, so both a flipped indicator and a late posting date are baked into the Ledger and the recomputation identically, on any dataset generated this way - there is no signal for either method to find, regardless of how much other variance is present. Reported honestly in the root-cause deliverable as 0 found/confirmed rather than substituting the known ground-truth count.

**bridge closed to 96%, per [10.IS.03](#validate)** - once Task 1's recomputation used the expected classification (34 keys, 305,281.76 - see 10.04 above), **10.CK.21**/**10.CK.22** (wrong legal entity, 60,697.50; wrong cost center, 85,485.13) became directly testable against it, each at twice face value (a misposted transaction's value is missing from its correct bucket and present in its wrong one): `2 x (60,697.50 + 85,485.13) = 292,365.26`, 96% of the variance. Confirmed the two categories' transactions don't overlap before adding them (zero overlap - the x2 arithmetic would break if a transaction were wrong on both dimensions). The remaining 12,916.50 traces to one specific transaction (`FTX-0000660`) that is wrong on cost center *and* is one of **10.CK.09**'s two mapping-conflict-unexplained `GL_MISMATCH` rows - a multi-dimension interaction not decomposed further.

**revised by [10.IS.04](#validate), per user challenge** - "you only have two checks, that doesn't sound like a very comprehensive diagnostics." **10.CK.17** got a real, independent method (a mapping-consistency swap-check, not the ruled-out Ledger-cancellation search): 9 rows, 78,480.32 - 3 of which (`FTX-0000158`, `FTX-0000660`, `FTX-0001297`) were previously counted in **10.CK.22**'s cost-center population, now excluded there (5 distinct, 55,515.89) since the indicator, not the cost center, is their real finding. Task 1's own recomputation corrected the same way (see 10.04 above) lands at 30 keys, 268,250.94. Re-bridged: `2 x (60,697.50 + 55,515.89) = 232,426.78`, 87%. The residual grew to 35,824.16 rather than shrinking - removing `FTX-0001297` from the bridge removes 2x its value without removing anything from the total (its corrected classification is still one of the 6 mapping-conflict combos, a no-op before and after), which necessarily widens the gap; 22,907.66 of it (2x `FTX-0001297`) is now precisely attributed. The remaining 12,916.50 is the *same* amount this step originally attributed to `FTX-0000660`'s "two dimensions at once" - that transaction is now fully explained by the indicator alone, so that specific attribution is retracted; the 12,916.50 itself was never actually resolved and stays open. Notebook, reconciliation-results, root-cause-analysis, exception-dataset (1214 -> 1223 rows, adding `WRONG_DR_CR_INDICATOR`), and audit all rewritten to these findings and re-executed clean.

**caught during review, fixed before publishing** - the first pass of **10.CK.22** reported 11 raw joined rows without checking for the same mapping-conflict join fan-out already documented for **10.CK.09** in 10.05 (a transaction matching more than one active mapping row is evaluated against each match independently); corrected to report both the raw row count and the distinct-transaction count (8), matching **10.CK.09**'s own precedent.

**presentation boundary retrofit** - per [presentation boundary](#presentation-boundary--blind-analyst-results) (a rule introduced during this step's review), 10.04's and 10.05's already-closed deliverables and the notebook's task 1/2 sections were also rewritten to remove tracker ids and workflow language, decouple the audit page from the main analysis, and drop ground-truth-aware phrasing - re-executed clean, all measured values unchanged from their original closure. This step's own deliverables were authored under the new rule from the start.

Wrote [`results/assessment-2/assessment-2-root-cause-analysis.md`](../../results/assessment-2/assessment-2-root-cause-analysis.md) (findings, per-category detail, remediation, permanent controls), rewrote [`assessment-2-exception-dataset.md`](../../results/assessment-2/assessment-2-exception-dataset.md) to union task 2's and task 3's categories (1214 rows total), and added the task 3 rows to [`assessment-2-audit.md`](../../results/assessment-2/assessment-2-audit.md).

**top-down/bottom-up reconciliation added per user direction** - three rows appended to the notebook's decomposition cell and the root-cause deliverable's findings table: the independent Ledger total variance (`gl_amount - txn_amount` from 10.04's write-back, reused rather than recomputed - 4,002,303.12), the bottom-up sum of the seven category contributions above (4,793,863.40), and the residual between them (-791,560.28).

**the residual's stated cause was then tested, per user direction, rather than left asserted** - two more rows measure it directly instead of assuming it: removing **10.CK.21**/**10.CK.22** (legal-entity/cost-center misclassification, which redistribute value between sub-totals without changing the Ledger's grand total) accounts for 146,182.63; removing the value double-counted where a transaction is flagged by more than one of the remaining checks (computed via a union-minus-distinct over the three category row sets, not assumed - traced entirely to overlap between **10.CK.15/16** and **10.CK.19**) accounts for another 125,566.69. Together these two predictions explain 271,749.32 of the original gap (34.3%) - the remaining 519,810.96 was reported as a genuine unexplained residual, not closed by either predicted cause and not forced to zero.

**partially resolved by [10.IS.02](#validate), then superseded by [10.IS.03](#validate)** - per user direction ("solve it"), the remaining 65.7% was diagnosed rather than left open: querying `finance.gl_balance` directly showed it is a chained daily ledger (`opening_balance` on day N equals `closing_balance` on day N-1 for the same key), so the write-back `amount` dimension's `SUM(closing_balance)` was summing a cumulative stock across 5 accounting dates against a flat flow (`SUM(local_amount)`) - not comparable. Counterfactual removal tests on the bottom-up side (excluding unmapped, then duplicate, transactions from the recomputation) each made variance *worse*, the opposite of the working hypothesis, which was the signal to inspect the top-down side instead of continuing to patch the bottom-up one. Reading `scripts/utils/data-generators.py`'s `gen_assessment2()` directly showed `finance.gl_balance`'s `debit_movement`/`credit_movement` are aggregated from `transaction_amount`, not `local_amount` - every recomputation in this notebook from 10.04 onward used the wrong column. Recomputed on `transaction_amount` (still grouped by each transaction's actual classification at this point): 0 of 589 keys exceeded tolerance.

**that 0.00 was itself incomplete** - a user question asked immediately after ("wouldn't incorrect mapping cause a discrepancy between the [source] and the [GL]?") surfaced [10.IS.03](#validate): grouping by each transaction's *actual* classification (the same values the Ledger was built from) made the dimensional check tautological, regardless of how much misclassification existed. Grouping instead by the *expected* classification: **34 of 589 keys exceed tolerance, 305,281.76 total variance** - a real, material, non-tautological result. Of the eight named categories, only the two Task 1's recomputation substitutes an expected value for (incorrect legal-entity allocation, incorrect cost-center assignment) can move this figure, and together at twice face value they explain 96% of it (see 10.07 below) - duplicate entries, FX errors, and unmapped transactions remain real, individually-detected findings, just not ones a Ledger-vs-transaction reconciliation was ever going to surface, for reasons specific to each (already documented in 10.07). Notebook, reconciliation-results, root-cause-analysis, and audit all rewritten to these findings and re-executed clean.

### 7. Task 4 - reconciliation framework design

edit locations: `10.EL.06`

Write the framework design deliverable from [reconciliation framework design](#reconciliation-framework-design--task-4) directly: the metrics table (**10.CK.23**), the `rc_tolerance_rules` proposal, the status-assignment thresholds, and the persistence design - this step is a narrative write-up of an already-fully-specified design, not new query development.

### 8. Business-facing summary

edit locations: `10.EL.07`

Write a short, non-technical summary of the variance findings and recommended controls aimed at a Finance stakeholder, distinct from the technical root-cause write-up.

### 9. Notebook consolidation and clean rerun

edit locations: `10.EL.01`

Reorder the notebook into assignment task order, remove scratch cells, reseed the database, and execute the notebook headless with `scripts/06-notebook-validate.sh`. Confirm every number cited in a deliverable still matches the rerun output; where it does not, correct the deliverable in the same cycle. Confirm the [advanced sql coverage](#advanced-sql-coverage) checklist is satisfied.

### 10. Deliverable review and status promotion

edit locations: `10.EL.02-10.EL.08, 10.EL.11`

Review each deliverable against the [task to deliverable map](#assessment-task-to-deliverable-map) for coverage, a populated **Sources** section, a context line linking the overview, and consistent numbers. Promote each `status: draft` to `status: final`, then run `scripts/07-deliverables-scaffold.sh` to regenerate the manifest with the new statuses and `--check` to confirm the result is current.

### 11. Publish

edit locations: `10.EL.10`

Commit the reviewed work, run `scripts/08-assessment-site.sh build` for the strict build, then `scripts/08-assessment-site.sh deploy` from the clean worktree. Confirm the published Assessment 2 pages, then update `docs/milestones.md` to mark milestone 10 closed with its closure evidence.

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

_10.02 run (prerequisites and seed data readiness): one exception surfaced, logged below - every other prerequisite step reported `[PASS]` on its first attempt._

| id       | seq | status | issue                                                    |
| -------- | --- | ------ | ----------------------------------------------------------- |
| 10.IS.01 | 01  | closed | notebook connectivity check timed out under host contention |
| 10.IS.02 | 02  | closed | GL movement recomputation used the wrong amount column       |
| 10.IS.03 | 03  | closed | GL movement recomputation grouped by actual, not expected, classification |
| 10.IS.04 | 04  | closed | expected-classification lookup keyed on a possibly-wrong indicator |

_10.IS.01 (closed) notebook connectivity check timed out under host contention_

**problem description**

`scripts/06-notebook-validate.sh` (10.PR.06) failed twice in a row - the template connectivity notebook's trivial `spark.range(1000).count()` cell exceeded nbconvert's `ExecutePreprocessor.timeout` (120s, then a manually-raised 300s diagnostic run), while the Spark standalone cluster itself reported two alive workers with 0 cores/memory in use throughout.

**exception**

```log
nbclient.exceptions.CellTimeoutError: A cell timed out while it was being executed, after 120 seconds.
The message was: Cell execution timed out.
Here is a preview of the cell contents:
-------------------
spark = (
    SparkSession.builder.master("spark://spark-master:7077")
    .appName("00-template-connectivity-check")
    .getOrCreate()
)
spark_check_count = spark.range(1000).count()
```

**triggering actions**

ran `./scripts/06-notebook-validate.sh` for 10.PR.06 right after `01-dev-env-setup.sh`/`03-mock-data-seed.sh`, while a second concurrent Claude Code session and the VS Code extension host were active on the same 3.8 GiB/8-vCPU WSL2 VM; the host also restarted mid-diagnosis (all containers exited 255, `uptime` reset to minutes), independently confirming host-level pressure rather than a notebook or Spark defect.

**hypothesis**

host CPU/memory contention (load average observed up to 25 on 8 cores, swap fully exhausted) was slowing JVM scheduling past the fixed 120s nbconvert timeout; the Spark standalone cluster wiring itself was not broken.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status | step                                            |
| ----------- | --- | ------ | ---------------------------------------------------- |
| 10.IS.01.01 | 01  | closed | checked host load/memory during the hang [01]        |
| 10.IS.01.02 | 02  | closed | isolated Spark local mode vs. cluster mode [02]      |
| 10.IS.01.03 | 03  | closed | traced a bare cluster-mode job end to end [03]       |
| 10.IS.01.04 | 04  | closed | reran nbconvert once host load settled - passed      |

01. **10.IS.01.01** `free -h`/`uptime` showed swap exhausted and load average 18-25 on an 8-vCPU host; a mid-diagnosis WSL restart reset load to near-zero.
02. **10.IS.01.02** `local[2]` mode completed `spark.range(1000).count()` in ~14s inside the same container, isolating the slowdown to the standalone-cluster path specifically.
03. **10.IS.01.03** a `docker exec` Python driver against `spark://spark-master:7077` (bypassing the Jupyter kernel entirely) registered, ran both stages, and shut down cleanly in ~12s - worker executor stderr shows `Finished task 0.0 in stage 0.0`/`stage 2.0` for every attempt, including ones nbconvert reported as timed out.

**diagnostic details**

Executor stderr on both workers confirmed `Successfully registered with driver` and full task completion for every attempt - the driver-executor RPC path was healthy throughout; what varied was elapsed wall-clock time under contention. No code or script change was needed: `06-notebook-validate.sh` and `00_template_connectivity_check.ipynb` are unmodified from [07](../features/07-jupyter-notebook-workspace-setup.md)'s closed design. This is an environment-capacity constraint on this WSL2 host (3.8 GiB RAM, frequently oversubscribed by concurrent Claude Code sessions and the VS Code extension host), not a defect in this tracker's prerequisite ordering - carried forward as an operating note for 10.10's notebook rerun, which will hit the same cluster-mode path at greater scale.

**validation evidence**

Rerun once host load dropped (load average 0.19-3.72): `[PASS] [07.IS] nbconvert execution completed - no cell raised` in 22s wall-clock, summary marker `[PASS] 00-template-connectivity-check: overall status=PASS`, cross-checked against `src_transaction_daily` row count 2010 via both JDBC and psycopg2 paths.

_10.IS.02 (closed) GL movement recomputation used the wrong amount column_

**problem description**

10.07's top-down/bottom-up variance reconciliation, added and then tested at user request, would not close: the independent Ledger total variance (4,002,303.12) and the bottom-up sum of Task 3's seven category contributions (4,793,863.40) left a residual of -791,560.28; two specific, testable corrections (removing the dimensional-only categories, removing measured double-counting between categories) explained only 271,749.32 of it (34.3%), leaving 519,810.96 genuinely unexplained. The user asked for this to be solved, not left open.

**exception**

```log
<no error - the notebook and every script ran clean; this is a numeric discrepancy in a
reconciliation that should close, not a runtime failure>
```

**triggering actions**

ran the notebook's Task 1 (GL integrity) and Task 3 (variance investigation) sections against the seeded database, per the normal workflow cycle; the residual was visible in the decomposition cell's own printed output, not from an error.

**hypothesis**

- use hypothesis framing until a validated fix is applied

initially: the residual is caused by one or more of Task 3's eight named categories not being fully/correctly attributed (an incomplete bottom-up decomposition). Revised after diagnostic steps 3-5 falsified that: the residual is not a Task 3 attribution problem at all, but a basis error in Task 1's own movement recomputation - the wrong transaction-amount column was used for the recomputation from the start, and the true root cause was in this tracker's own implementation, not in the seeded data.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostic details section to elaborate actions and learnings for each step

| id          | seq | status | step                                                    |
| ----------- | --- | ------ | ------------------------------------------------------------ |
| 10.IS.02.01 | 01  | closed | checked whether the Ledger is a chained stock or a flow [01]  |
| 10.IS.02.02 | 02  | closed | checked per-key movement-variance sign consistency [02]       |
| 10.IS.02.03 | 03  | closed | tested the "missing mapping" category causally [03]           |
| 10.IS.02.04 | 04  | closed | tested the "duplicate entry" category causally [04]           |
| 10.IS.02.05 | 05  | closed | tested a fully-combined correction [05]                       |
| 10.IS.02.06 | 06  | closed | inspected the seed generator's GL aggregation source [06]     |
| 10.IS.02.07 | 07  | closed | recomputed movement using `transaction_amount` [07]           |

**diagnostic details**

01. (closed) queried one `(legal_entity, gl_account, cost_center, currency)` key's rows across all 5 accounting dates: `opening_balance` on day N equals `closing_balance` on day N-1 exactly, every time - `finance.gl_balance` is a chained running-balance (stock) ledger, not an independent daily flow. This meant 10.04's "amount" dimension top-down figure (`SUM(closing_balance)` across all 589 rows, spanning 5 dates, compared against `SUM(local_amount)` across all transactions) was summing a cumulative stock measure against a flow measure - not a valid comparison basis, and not what should have been used as the top-down variance in 10.07's reconciliation.
02. (closed) checked the sign of `debit_variance`/`credit_variance` at every one of the 589 keys from the existing movement recomputation: 167 keys have a negative debit variance, 137 a negative credit variance, **zero** keys of either sign are positive. Every discrepant key has the Ledger reading *lower* than the recomputation, never higher - confirming the already-computed `total_gl_variance` (sum of absolute per-key variances, 1,691,814.92) is a clean, sign-consistent, flow-basis figure equal to the plain global difference, unlike the stock-based one - the figure that should have anchored 10.07's decomposition instead of the one actually used.
03. (closed) recomputed movement with every "missing accounting mapping" transaction *excluded*, expecting variance to fall (the working hypothesis: these transactions inflate the recomputation relative to the Ledger). It rose instead, from 1,691,814.92 to 5,184,155.87 - the opposite of the hypothesis. This transaction population was already correctly reflected in the Ledger; counting its face value (4,387,367.89) as a variance contribution in 10.07 was backwards from the start.
04. (closed) same test for "duplicate / re-posted entries": excluding them raised variance too (1,691,814.92 to 1,783,952.65), again counter to the working hypothesis that removing an erroneous extra posting should bring the recomputation closer to the Ledger.
05. (closed) combined every plausible correction at once - deduplication, FX-amount correction, legal-entity reassignment to the account's majority-vote value, cost-center reassignment to the mapping's expected value - into one recomputation, expecting the largest drop yet. Variance rose sharply instead, to 6,415,780.65. Three independent tests all moving the same direction, away from the working hypothesis, was the signal to stop patching the bottom-up side and question the top-down side instead.
06. (closed) read `scripts/utils/data-generators.py`'s `gen_assessment2()` directly: `finance.gl_balance`'s `debit_movement`/`credit_movement` are aggregated from the same (already-mutated, post-injected-issue) transaction rows Task 1/3 already use - but keyed on `r["transaction_amount"]` (line ~527), not `r["local_amount"]`. Every recomputation in this tracker's notebook, from 10.04 onward, grouped and summed `local_amount`.
07. (closed) reran the movement recomputation with `transaction_amount` substituted for `local_amount`, everything else unchanged (same grouping key, same full outer join): **total variance 0.00, 0 of 589 keys outside tolerance.** Root cause confirmed and the fix validated in the same step - this is not a hypothesis still being narrowed, the corrected basis accounts for the entire movement variance exactly.

**validation evidence**

Direct SQL against the freshly seeded database (`MOCK_DATA_SEED=42`, same seed run 10.04-10.07 used): `SUM(ABS(debit_variance)) + SUM(ABS(credit_variance)) = 0.00` across all 589 `finance.gl_balance` keys when the recomputation groups `bronze.finance_transactions` by `posting_date, legal_entity, gl_account, cost_center, currency` and sums `transaction_amount` - full outer join, no rows excluded, no dataset edits. The fix is applied in the notebook and re-executed clean; see 10.04's and 10.07's Implement sections below for the corrected findings this produces.

**amendment - this issue's "0.00 = fully reconciled" conclusion was itself incomplete** - see [10.IS.03](#validate): the recomputation above grouped by the transaction's own *actual* `gl_account`/`cost_center`/`legal_entity`, the same values the Ledger was built from, so the 0.00 result was still partly tautological on those three dimensions. The amount-column fix documented here was necessary and remains correct (the Ledger genuinely is built from `transaction_amount`, confirmed directly against the generator's source) - it was just not sufficient on its own to make the recomputation a genuine independent check on every dimension.

_10.IS.03 (closed) GL movement recomputation grouped by actual classification, not expected classification_

**problem description**

User question, asked after 10.IS.02 closed: "the idea here is to compare two different methods for aggregation, one is against the source data, and the other is against the gl after transformation and aggregation - so wouldn't incorrect mapping cause a discrepancy between the former and the later?" It should, and it did not, in either the pre- or post-10.IS.02 recomputation - both grouped `bronze.finance_transactions` by the transaction's own `gl_account`, `cost_center`, and `legal_entity`, the exact same (possibly-misclassified) values `finance.gl_balance` was built from. A `GL_MISMATCH` transaction's value lands in the same aggregation bucket whether you sum by its actual or its expected classification, if both sides of the comparison use "actual" - the check could never show a classification-driven variance, by construction, regardless of how much misclassification exists.

**exception**

```log
<no error - a design gap surfaced by a user question, not a runtime failure>
```

**triggering actions**

user asked whether incorrect mapping should cause a discrepancy between the source-based recomputation and the Ledger, immediately after 10.IS.02 reported a 0.00 residual explained entirely by an amount-column fix.

**hypothesis**

- use hypothesis framing until a validated fix is applied

grouping the recomputation by each transaction's *expected* classification (`ref.accounting_mapping.expected_gl_account`/`expected_cost_center`, majority-vote `legal_entity`) instead of its actual, recorded classification should surface a genuine variance wherever Task 2's `GL_MISMATCH`/wrong-cost-center/wrong-legal-entity findings exist, since the Ledger only ever recorded the transaction under its actual (possibly wrong) classification.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostic details section to elaborate actions and learnings for each step

| id          | seq | status | step                                                       |
| ----------- | --- | ------ | ----------------------------------------------------------- |
| 10.IS.03.01 | 01  | closed | recomputed grouping by expected `gl_account` alone [01]      |
| 10.IS.03.02 | 02  | closed | isolated expected `cost_center` and `legal_entity` alone [02] |
| 10.IS.03.03 | 03  | closed | checked the mapping join for fan-out [03]                    |
| 10.IS.03.04 | 04  | closed | recomputed with one canonical mapping row per transaction [04] |
| 10.IS.03.05 | 05  | closed | excluded the 6 genuinely-conflicting product/type combos [05] |

**diagnostic details**

01. (closed) substituted `expected_gl_account` (falling back to the transaction's actual `gl_account` where unmapped) for the grouping key, everything else unchanged: 209 of 589 keys now show a variance, totaling 4,148,271.34 - confirming the hypothesis immediately. The "0.0% every dimension" result from 10.IS.02 was a construction artifact, not evidence of a clean Ledger.
02. (closed) same substitution for `expected_cost_center` alone (161 keys, 4,127,753.78) and for majority-vote `legal_entity` alone (11 keys, 114,301.16) - both independently confirm the same pattern, at different scales.
03. (closed) before trusting a combined figure, checked whether a transaction can match more than one `ref.accounting_mapping` row: yes - some transactions match 3 rows (the same 6 conflicting product/type combos [10.CK.12](#mapping-validation-design--task-2)/[10.CK.14](#mapping-validation-design--task-2) already flag), and a naive join multiplies that transaction's amount into the recomputation once per match. The first combined test (all three dimensions substituted, naive join) read 224 keys / 4,307,990.04 - not yet trustworthy given the fan-out risk just found.
04. (closed) forced exactly one mapping row per transaction (`ROW_NUMBER() ... ORDER BY effective_start_date DESC`) before substituting: 327 keys / 6,494,579.30 - larger, not smaller, than the un-deduplicated figure, because concentrating a transaction's full value into one picked bucket (rather than spreading it across every matched bucket) moves further from wherever the Ledger actually recorded it. Confirms the fan-out was a real distortion, but picking a single "winner" among genuinely conflicting mapping rows is itself an arbitrary tie-break, not a clean number to publish.
05. (closed) excluded the 6 product/type combos with more than one *currently active* mapping row (Task 2's own `MULTI_GL_MAPPING`/`OVERLAPPING_MAPPING` findings - there is no single unambiguous "expected" value for these, so substituting one arbitrarily would misattribute a data-integrity problem in the reference table as if it were resolved) - fell back to the transaction's actual classification for those combos only, kept the expected-classification substitution everywhere else. Result: **34 keys, 305,281.76** - roughly double the combined face value of the wrong-legal-entity (60,697.50) and wrong-cost-center (85,485.13) findings from 10.07 (a misposted transaction's value is missing from its correct bucket *and* present in its wrong one, so each contributes to variance twice), consistent with 10.07's own transaction-level findings rather than contradicting them.

**validation evidence**

`34` keys / `305,281.76` total variance, computed via direct SQL against the freshly seeded database, grouping by expected `gl_account`/`cost_center` (unambiguous mapping matches only) and majority-vote `legal_entity`, summing `transaction_amount`, full outer join against `finance.gl_balance`. This is a materially different, non-tautological result from 10.IS.02's 0.00 - the fix is applied in the notebook (10.04's recomputation and 10.07's dependent checks) and re-executed clean; see 10.04's and 10.07's Implement sections for the corrected findings.

_10.IS.04 (closed) expected-classification lookup keyed on a possibly-wrong indicator_

**problem description**

User question, asked after 10.IS.03's design was documented: "you only have two checks, that doesn't sound like a very comprehensive diagnostics - you have a GL discrepancy, the problem statement suggests several lines of enquiry, you can only think of two diagnostic checks?" - a challenge to treat the assignment's seven named candidate causes as fixed, closed inventory rather than actually reasoning about what else could be checked. Re-examining the "incorrect debit/credit indicator" candidate specifically (previously ruled undetectable by any method, not just the Ledger-based one) surfaced that `ref.accounting_mapping` keys the expected GL account and cost center off *both* product code and indicator - a fact the existing checks never exploited. That, in turn, meant **10.IS.03**'s own `single_match` join (keyed on each transaction's actual, posted indicator) would look up the wrong mapping row for a transaction whose indicator is itself wrong, supplying an expected value that is neither the transaction's actual value nor its genuinely correct one.

**exception**

```log
<no error - a design gap surfaced by a user question, not a runtime failure>
```

**triggering actions**

user challenged the completeness of the checks-designed-so-far list; re-deriving a detection method for the previously-ruled-out "incorrect indicator" candidate (rather than accepting the prior ruling) surfaced this as a second-order effect on **10.IS.03**'s own fix.

**hypothesis**

- use hypothesis framing until a validated fix is applied

a transaction whose actual `(gl_account, cost_center)` fails to match any active mapping row under its own posted indicator, but matches one exactly under the opposite indicator, is carrying the wrong indicator - correcting the mapping lookup to that opposite indicator, for those transactions only, should remove a real (if small) distortion from **10.IS.03**'s recomputation, changing its total variance.

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostic details section to elaborate actions and learnings for each step

| id          | seq | status | step                                                          |
| ----------- | --- | ------ | -------------------------------------------------------------- |
| 10.IS.04.01 | 01  | closed | tested the swap-match rule against the seeded CSVs directly [01] |
| 10.IS.04.02 | 02  | closed | checked overlap against the existing GL_MISMATCH/cost-center findings [02] |
| 10.IS.04.03 | 03  | closed | measured the effect on 10.IS.03's own total before committing to the fix [03] |
| 10.IS.04.04 | 04  | closed | implemented in the notebook and re-executed clean [04]         |
| 10.IS.04.05 | 05  | closed | re-decomposed 10.07's bridge against the corrected total [05]  |

**diagnostic details**

01. (closed) against `data/mock/bronze_finance_transactions.csv`/`ref_accounting_mapping.csv` directly (no Spark): flag a transaction if its actual `(gl_account, cost_center)` doesn't match any active mapping row for its own indicator, but exactly matches one for the opposite indicator. 9 of `issue-log.csv`'s 10 `incorrect_dr_cr_indicator`-tagged rows found, zero false positives across all 1,523 transactions. The one miss (`FTX-0001358`) has no active mapping row at all for the opposite indicator - genuinely nothing to swap-match, not a method weakness.
02. (closed) 3 of the 9 (`FTX-0000158`, `FTX-0000660`, `FTX-0001297`) were already present in **10.CK.09**'s `GL_MISMATCH` population and **10.CK.22**'s cost-center population, joined (like both of those checks) on each transaction's actual indicator - confirming the wrong-mapping-row-lookup hypothesis structurally, not just by coincidence of transaction id. `FTX-0000158`/`FTX-0000660` are exactly the 2-row residual the mapping-validation deliverable reported as unexplained.
03. (closed) live SQL against the seeded Postgres, correcting only the mapping lookup for these 9 (not the debit/credit amount split, which stays on the actual indicator - the same basis the Ledger itself was built on, per the detectability analysis): total variance dropped from `305,281.76`/34 keys to `268,250.94`/30 keys - a genuine, material, exactly-attributable change (the drop equals precisely 2x the combined value of the 2 transactions, `FTX-0000158`+`FTX-0000660`, whose corrected lookup actually changes; `FTX-0001297`'s corrected lookup still falls back to its actual value, since its true product/indicator combination is one of the 6 mapping-conflict combos - a no-op, before and after).
04. (closed) implemented `flip_candidates` in the notebook (Task 1's recomputation, Task 3's rebuilt copy, and the exception dataset), a real `10.CK.17` check replacing the previously-ruled-out Ledger-cancellation method, and excluded `10.CK.17`'s transactions from `10.CK.22`'s cost-center population - re-executed headlessly end to end, zero cell errors, 30 keys/`268,250.94` confirmed via the notebook's own `[INFO]` output, not asserted.
05. (closed) re-ran 10.07's bridge against the corrected total: legal-entity (unchanged, 60,697.50) and cost-center (now 5 distinct after excluding **10.CK.17**'s 3, 55,515.89) at twice face value = 232,426.78, 87% of 268,250.94. The residual grew from 12,916.50 to 35,824.16, not shrank - removing `FTX-0001297` from the cost-center bucket removes 2x its value from the bridge sum without removing anything from the total (it was never contributing there), which necessarily widens the gap. Of that, 22,907.66 (2x `FTX-0001297`) is now precisely attributed; the remaining 12,916.50 is the *same* unexplained amount 10.07 already carried, previously (and incorrectly) attributed to `FTX-0000660` being "wrong on two dimensions at once" - that transaction is now fully and cleanly explained by the indicator alone, so that specific explanation is retracted, not carried forward. The 12,916.50 itself stays genuinely open.

**validation evidence**

`30` keys / `268,250.94` total variance, computed by the notebook's own executed cell output (not hand-computed) against the freshly seeded database - `flip_candidates` correcting the mapping lookup for the 9 transactions identified in step 01, everything else unchanged from 10.IS.03. `10.CK.17` (the same swap-match rule, standalone) finds the same 9 rows, `78,480.32`, independently of the Ledger. Cross-checked zero overlap between `10.CK.17`, `10.CK.21` (legal-entity), and `10.CK.22` (cost-center)'s transaction populations before combining them in 10.07's bridge. This does not fully close 10.07's residual - 12,916.50 remains open, explicitly not force-fit to the smaller, since-retracted explanation.

**user actions**

- GitHub authentication and the deploy confirmation for the published site (10.12)

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this
feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
- jupyter-notebook-workspace
