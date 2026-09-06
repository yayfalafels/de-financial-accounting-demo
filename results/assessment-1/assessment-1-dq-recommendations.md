# Assessment 1 - DQ-Control Recommendations

**Task 3 - Permanent DQ-Control Recommendations**

See [overview](assessment-1-overview.md) for the scenario, source/Bronze table shapes, and the seeded-vs-production scale statement. Every control below closes a specific gap named in [assessment-1-root-cause-analysis.md](assessment-1-root-cause-analysis.md); each is written so it maps onto the existing `reconciliation.rc_*` control-table framework rather than as a standalone process ask.

## Sources

- root cause and remediation this list is derived from: [task 1 root cause analysis](assessment-1-root-cause-analysis.md)
- existing control-table schema each recommendation maps to: `postgresql/rc-batch-control-create-table.sql`, `postgresql/rc-reconciliation-results-create-table.sql`, `postgresql/rc-audit-trail-create-table.sql`
- currently-running check this framework already executes: `scripts/utils/reconciliation-runner.py` -> `reconciliation.rc_batch_control` + `reconciliation.rc_reconciliation_results` (`dimension` in `row_count`, `amount`), thresholds `PASS <0.1%`, `WARNING <1%`, `FAIL >=1%`

## Remediation

Remediation repairs the root cause for this specific case, so the two confirmed hypotheses stop recurring rather than only being caught after the fact.

| id  | control                                                                  | addresses    |
| --- | ------------------------------------------------------------------------ | ------------ |
| P01 | derive business date from `transaction_date` before file-bucketing       | hypothesis 1 |
| P02 | make Bronze ingestion idempotent on `transaction_id` upsert, not append  | hypothesis 2 |
| P03 | require a load `reason_code` (`INITIAL`/`REPROCESS`), reject if absent   | hypothesis 2 |
| P04 | gate Bronze publish on the batch's `rc_*` status                         | both         |

01. **P01** convert `source_extract_ts` to business timezone (or derive business date directly) before assigning a record to a daily ingestion file - closes the UTC/SGT midnight boundary from hypothesis 1.
02. **P03** the `-R` suffix already present in this data shows the signal exists; this makes it a required, validated field instead of an informal file-naming convention.
03. **P04** publish blocked while `rc_reconciliation_results.reconciliation_status = 'FAIL'` for the batch, so a bad batch stops before reaching Finance rather than being caught after.

## Preventative controls

Ongoing checks, each expressed against the `rc_*` schema already in place so a recommendation is something the framework can run, not a new tool.

| id  | check                       | grain        | rc_\* mapping [04]               | 
| --- | --------------------------- | ------------ | -------------------------------- |
| D01 | batch row/amount parity     | per batch    | `rc_batch_control` + results     |
| D02 | per-file row-count parity   | per file     | new `dimension` value            | 
| D03 | duplicate id count          | per batch    | new `dimension` + `audit_trail`  | 
| D04 | reprocess row-count check   | per batch    | `audit_trail.action = NOTIFY`    | 
| D05 | recurring dim. variance     | per batch    | recurring level-2 pass           | 

01. **D01** is the check task 2 already runs each batch (`batch_id = 9` above) - carried forward here as the baseline detective control, not a new recommendation.
02. **D02** is the single highest-value new check: task 3 confirmed both `*_MIDNIGHT.dat` files as 100% absent from Bronze (20/20 rows) - a per-file row-count check would have caught this the same day, before Finance noticed the batch-level gap.
03. **D05** reruns task 2's one-off dimensional pass on every batch instead of only when investigating a reported mismatch, so an `ingestion_file`-concentrated variance is caught the day it occurs.
04. all four new rows (`D02`-`D05`) fit inside `rc_reconciliation_results`/`rc_audit_trail` as additional `dimension`/`action` values, not new tables - the schema extension is additive.

## Prioritisation

Severity reflects the dollar/row impact confirmed in the root-cause analysis; effort reflects implementation cost against the existing schema.

| id  | control                          | 
| --- | -------------------------------- | 
| D02 | per-file row-count parity        | 
| P01 | business-date derivation fix     |
| P02 | idempotent upsert on load        |
| D03 | duplicate-id count per batch     |
| P03 | mandatory load reason code       |
| D04 | reprocess-batch count check      |
| P04 | publish gate on `FAIL` status    |
| D05 | recurring dimensional variance   | 
| D01 | batch parity (already running)   | 

**Reading the list**: 

- **P0** items close the two confirmed hypotheses at the source (P01, P02) and give the earliest possible detection of the specific failure mode already observed (D02).
- **P1** items catch the same failure modes one layer later - after a bad batch lands rather than before. 
- **P2** formalizes a check task 2 already proved useful but only ran once. None of these controls resolve the [5-row unexplained residual](assessment-1-root-cause-analysis.md#unexplained-residual) 
- **D02 and D05** raise the odds a similar future occurrence is caught even if its mechanism is never fully explained.
