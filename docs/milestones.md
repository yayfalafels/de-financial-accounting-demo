# assessment milestones

| id | seq | status  | milestone                                        | 
| -- | --- | ------- | ------------------------------------------------- | 
| 01 | 01  | closed  | scope requirements tasks                         | 
| 02 | 02  | closed  | dev env setup postgresql db                      | 
| 04 | 03  | closed  | seed mock data                                   | 
| 03 | 03  | open    | dev env setup spark container                    | 
| 05 | 05  | open    | ai closed loop develop and validation            | 
| 06 | 06  | pending | power bi dashboard setup                         | 
| 07 | 07  | pending | jupyter notebook workspace setup                 | 
| 08 | 08  | pending | assessment deliverables conventions              | 
| 09 | 09  | pending | assessment 1 - source-to-bronze profiling recon  | 
| 10 | 10  | pending | assessment 2 - financial accounting gl recon     | 
| 11 | 11  | pending | assessment 3 - regulatory dq lineage dashboard   | 

**01. scope requirements tasks** — read `docs/design/asssignment.md` and `docs/design/development-environment.md` and lay out / maintain this table: dev env build-out sequenced ahead of the three graded assessments, each producing its own `docs/features/<id>-<name>.md` tracker when work on it starts. 

**Closure**: every milestone below has a stated scope and closure condition, every gap found by auditing the assessments' deliverables against the planned infra either has a milestone or an explicit recorded decision not to cover it, and no further gaps surface on the next review pass.

**02. dev env setup postgresql db** — stand up the `src_transaction_daily` postgres table on its own docker container, script-driven and idempotent. 

**Closure**: closed — `02-workflow-validate.sh` passes end to end with a real log artifact (`.dev/logs/*-02.IS-workflow-validate.log`, all 14 columns PASS).

**03. dev env setup spark container** — extend the postgres container with a Spark cluster (master + 2 workers) and Jupyter, per its design doc, without disturbing the running postgres service/volume. 

**Closure**: `docker ps` shows master + both workers registered, and a smoke-test PySpark job submitted inside spark-master reads `src_transaction_daily` over JDBC successfully.

**04. seed mock data** — create the 8 postgres schemas/tables the three assessments reference beyond `src_transaction_daily`, and seed all 9 tables with mock data carrying every issue each assessment's tasks expect a candidate to find. 

**Closure**: all 9 tables exist with row counts matching the volume budget, `data/mock/issue-log.csv` enumerates every injected issue, and rerunning the seed script reproduces byte-identical data.

**05. ai closed loop develop and validation** — build the generic reconciliation control-table stack (`reconciliation.rc_*`) plus a runner + feedback script proving the pattern end to end on one concrete check (Assessment 1's batch-level source-vs-bronze reconciliation). 

**Closure**: `04-closed-loop-run.sh` passes, inserting a batch/result/audit row set whose measured variance matches the expected variance derived from `issue-log.csv` within tolerance.

**09. power bi dashboard setup** — set up a git-tracked, version-controlled Power BI workspace using `.pbip` (Power BI Project) template files, plus a sync script keeping them mirrored between the Windows-side `/mnt/...` path (where Power BI Desktop actually runs — it's Windows-only and can't run inside this Linux/Docker sandbox) and this repo's `/home/...` working copy. 

**Closure**: a `.pbip` template exists in the repo, the sync script round-trips a change made on the `/mnt` side back into the git-tracked copy without data loss, and the workflow is documented well enough that assessments (both need a dashboard deliverable) can open the template and start building.

**10. jupyter notebook workspace setup** — define the notebook workspace conventions: one notebook per assessment (matching the assessment's own naming, e.g. `assessment1_profiling.ipynb`), a template notebook proving it reaches both postgres (JDBC/psycopg2) and the Spark cluster from inside the Jupyter container, and where notebook outputs get committed. 

**Closure**: the template notebook runs cleanly end to end inside the Jupyter container that gets standed up, successfully querying both postgres and Spark, and the convention for where each assessment's working notebook lives is written down.

**11. assessment deliverables conventions** — decide, once, where every assessment's non-code deliverables live and in what format: profiling summaries, exception datasets, root-cause write-ups, lineage documentation, dashboard mock-ups — defaulting to git-tracked markdown (plus the `.pbip` dashboard) under a consistent per-assessment path, so the assessments aren't each inventing their own layout. 

**Closure**: a documented directory convention exists (e.g. `results/<assessment-id>/...` or equivalent) and is referenced from each of the assessments own feature scope once those trackers are created.

**assessment 1** — source-to-Bronze profiling and reconciliation against `src_transaction_daily` / `bronze.transaction_daily`; depends on postgresql, seeded data, and reconciliation scaffold since the source/bronze tables and the closed-loop pattern it builds on live there. 

**Closure**: all deliverables produced

- notebook
- profiling summary
- reconciliation results
- exception dataset
- root-cause analysis
- DQ-control recommendations
- dashboard mock-up

**assessment 2** — financial accounting and GL reconciliation across `bronze.finance_transactions`, `finance.gl_balance`, and `ref.accounting_mapping`; depends on the seeded tables and the reconciliation-framework groundwork it reuses. , so be it if  the portions of Task 4 (design a reusable reconciliation framework) overlaps with the generic control-table scaffold that the ai validation loop proves the pattern once for the scaffold's own self-check. that just means Task 4 is already partially complete by the time that the ai validation loop is implemented.

**Closure**: all deliverables produced, including the SGD 3.22m variance root cause and the reconciliation-framework design.

**assessment 3** — regulatory / transaction-banking data quality, lineage, and executive dashboard across the source → Bronze → regulatory reporting chain; depends on Spark cluster for the Spark-scale profiling work, assessments for the dashboard and notebook deliverables, and for the shared reconciliation framework. 

The 5B-row performance-optimization task is answered by design, not by simulation: no billion-row dataset gets generated. the seed data volume budget stays low-thousands-of-rows across the board. Instead, the Spark SQL is written to scale to a job much larger than the seeded data — the master + 2 worker topology exists for this reason — and demonstrated against the small seeded dataset, with descriptive notes in the submission explaining the delta between this demo's scale and real-world production behavior. 

**Closure**: all deliverables produced, with the performance question answered via technique explanation + small-scale demonstration per the above, not literal 5B-row execution.
