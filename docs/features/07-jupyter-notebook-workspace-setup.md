# Jupyter Notebook Workspace Setup - Feature tracker
>Review the guidelines before performing any actions including edits on the document 

## 07 (open) jupyter notebook workspace setup

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                          | 
| ----- | --- | ------- | -------------------------------------------------- | 
| 07.01 | 01  | open    | design                                             | 
| 07.02 | 02  | pending | edit locations and implementation plan             | 
| 07.03 | 03  | pending | jupyter workspace conventions                      | 
| 07.04 | 04  | pending | template notebook - postgres + spark connectivity  | 
| 07.05 | 05  | pending | per-assessment notebook scaffolding                | 
| 07.IS | 06  | pending | validate                                           | 

## Scope

define the notebook workspace conventions the three assessments build their own working notebooks on top of, plus one template notebook proving the Jupyter container the **spark container dev env tracker** already stood up actually reaches both postgres and the Spark cluster from inside its own environment. This feature stands up conventions and proof-of-connectivity, not any assessment's analysis content.

- depends on the **spark container dev env tracker** - the `jupyter` container, its `notebooks/` mount, and the Spark/postgres network path already exist as of that feature; this feature does not provision new infrastructure or touch the docker compose stack, it only adds notebook files and, if needed, one Python package pin to the existing jupyter image
- one notebook per assessment, named to match the assessment's own naming (e.g. `assessment1_profiling.ipynb`) - this feature fixes that naming convention and scaffolds the starting files, it does not write any assessment's actual profiling, reconciliation, or lineage analysis
- one template notebook (not assessment-specific) proves the connectivity pattern every assessment notebook reuses: a Spark session that reaches the cluster (`spark-master:7077`), and a postgres connection reaching `src_transaction_daily` and the seeded schemas - via JDBC from PySpark and/or a direct Python driver, per the **dev env design doc**'s appendix pattern
- `psycopg2`/`psycopg2-binary` is pinned in the **dev env design doc**'s appendix but was not carried into the **spark container dev env tracker**'s actual `Dockerfile.spark` build list (`pyspark`, `delta-spark`, `faker`, `postgresql-client` only) - if the template notebook needs a direct Python-side postgres connection rather than JDBC-only, adding that pin is in scope here, since this is the first feature that actually needs it
- decides and documents where notebook *outputs* get committed - executed-cell outputs (result tables, printed profiling summaries, small plots) checked into git alongside the `.ipynb` source, versus cleared before commit - so the three assessments aren't each deciding this ad hoc; this is scoped to notebooks specifically and feeds into the broader **assessment deliverables conventions** milestone's per-assessment deliverable-location decision
- does not implement any assessment's actual analysis, profiling, reconciliation, or lineage logic - the template notebook only proves connectivity, the same reusable-scaffold-not-content precedent the **powerbi dashboard setup tracker** already set for its `.pbip` template
- does not change the jupyter container's authentication or networking posture (tokenless, per the **spark container dev env tracker**'s environment & secrets design) - no new ports, no new container, no compose changes beyond the possible package pin above

## References

## Design

## Edit locations

## Implement

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status  | issue                                     | 
| -------- | --- | ------- | ------------------------------------------ | 
| 07.IS.01 | 01  | pending | <first out exception>                      | 

_07.IS.01 (pending) <first out exception>_

**problem description**

<to fill in>

**exception**

```log
<to fill in>
```

**triggering actions**

<to fill in>

**hypothesis**

- use hypothesis framing until a validated fix is applied

<to fill in>

**diagnostic steps**

- first out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation, these are not diagnostic steps
- keep the step description brief, use the diagnostics details section to elaborate actions and learnings for each step

| id          | seq | status  | step                                      | 
| ----------- | --- | ------- | ------------------------------------------ | 
| 07.IS.01.01 | 01  | pending | <diagnostic step 01>                       | 

**diagnostic details**

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
