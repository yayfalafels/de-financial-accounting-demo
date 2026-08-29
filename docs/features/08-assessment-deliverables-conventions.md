# Assessment Deliverables Conventions - Feature tracker
>Review the guidelines before performing any actions including edits on the document

## 08 (open) assessment deliverables conventions

## Contents

- [Tasks](#tasks)
- [Scope](#scope)
- [References](#references)
- [Design](#design)
- [Test cases](#test-cases)
- [Edit locations](#edit-locations)
- [Implement](#implement)
- [Validate](#validate)
- [Guideline](#guideline)

## Tasks

| id    | seq | status  | milestone                                | 
| ----- | --- | ------- | ---------------------------------------- | 
| 08.01 | 01  | open    | design                                   | 
| 08.02 | 02  | pending | edit locations and implementation guide  | 
| 08.03 | 03  | pending | directory scaffold and naming convention | 
| 08.04 | 04  | pending | cross-reference from assessment trackers | 
| 08.IS | 05  | pending | validate                                 | 

## Scope

decide, once, where every assessment's non-code deliverables live and in what format, so assessments 1-3 aren't each inventing their own layout - see [milestones.md](../milestones.md)'s `08. assessment deliverables conventions` entry for the milestone-level statement this tracker executes.

- covers the full non-code deliverable lists from the **assignment design doc**'s three "Expected Deliverables" sections: 
    - **shared** exception datasets and DQ-control recommendations
    - **assessment 1** data profiling summaries and Source-to-Bronze reconciliation results
    - **assessment 2** GL reconciliation output, accounting-mapping validation, root-cause findings, reconciliation-framework design, and a business-facing summary
    - **assessment 3** profiling results, end-to-end reconciliation, exception tables, root-cause analysis, a data-lineage document, and performance-optimization recommendations
- default format is git-tracked markdown under one consistent per-assessment path (e.g. `results/<assessment-id>/...` or equivalent) - this feature picks the path convention and per-deliverable-type file naming, not the analytical content of any deliverable
- depends on, and does not re-decide, three conventions already established by earlier milestones: 
    - the **jupyter notebook workspace tracker** (07) for where each assessment's working notebook lives
    - the **power bi dashboard setup tracker** (06)'s `.pbip` template/sync workflow for the dashboard/dashboard-mock-up deliverable
    - the **ai closed-loop validation tracker** (05)'s `reconciliation.rc_*` control tables for structured
    - DB-resident reconciliation results - this feature's job is the narrative/markdown write-up layer referencing those, not a second home for the same numbers
- does not implement any assessment's actual profiling, reconciliation, root-cause, lineage, or dashboard content - purely a directory/format/naming decision, exercised for real by the assessment milestones once their own trackers exist
- closure per milestones.md: a documented directory convention exists and is referenced from each of the assessments' own feature scope once those trackers are created

## References

_to fill in_

## Design

_to fill in_

## Test cases

_to fill in_

## Edit locations

_to fill in_

## Implement

_to fill in_

## Validate

**Issues**

- inventory all first out exceptions and issues encountered in this table
- for each issue, create an issue section and use this section to document diagnostics and resolution steps

| id       | seq | status  | issue                                     | 
| -------- | --- | ------- | ------------------------------------------ | 
| 08.IS.01 | 01  | pending | <first out exception>                      | 

_08.IS.01 (pending) <first out exception>_

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
| 08.IS.01.01 | 01  | pending | <diagnostic step 01>                       | 

**diagnostic details**

## Guideline

## instructions

review and strictly follow these relevant skills when performing tasks for this feature implementation and working with this document

## relevant skills

- markdown-tables
- feature-implementation-guide
