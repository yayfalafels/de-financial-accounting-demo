---
name: feature-implementation-guide
description: implementation and validation conventions for feature work in this repo — git-tracked rerunnable scripts, .env parameterization, error handling, logging file naming, and the issues/diagnostics workflow used in docs/features/*.md. Load before implementing or validating a feature.
---

## relevant skills

- markdown-tables — apply it to every table produced while following this guide (issues table, diagnostic steps table, etc.)

## implementation guide

Use standard git-tracked, re-runnable paths and scripts for build, deploy, and resource provisioning. Do **NOT** improvise ad-hoc or tmp Python virtual envs or Docker containers when implementing normal tasks. Tmp resources and environments are allowed only for issue-diagnostics purposes — see the diagnostic dir convention in the validation guide below.

**parameterization**

- make use of parameterization and the `.env` file
- avoid hard-coded literals, especially repeated locations
- identify and set all parameters at the beginning of scripts

**error handling**

- wrap risky or complex execution steps in safe runnable wrappers — functions or subscripts that ensure `exit 0`
- for wrapped scripts or functions: non-zero exit on failure, no silent failures
- anticipate, catch, and gracefully handle anticipatable failures and exceptions
- use descriptive error messages for classified failures

**logging**

- write diagnostic log files for every runnable action
- echo diagnostic log lines for key steps to enable informative feedback
- use standard log file naming and save to the standard log file destination
- use standard notations `[PASS]` / `[FAIL]` in log lines for pass and fail

_log file naming_

Use the standard log file naming convention:

```
<YYYYMMDDHHMMSS>-<feature_id>.<subfeature_id>.{...}-<short task name>.log
```

example:

```
20260822185612-02.04.-sql-create-generate.log
```

Parameterize the log file naming in scripts:

```bash
# .env
LOGS_DIR=.dev/logs
TIMEZONE='Asia/Singapore'
TIMESTAMP_FORMAT=%y%m%d%H%M%S

# source .env
FEATURE_ID=02.04
TASK_NAME=sql-create-generate
LOG_FILE=$(TZ=$TIMEZONE date +$TIMESTAMP_FORMAT)-$FEATURE_ID-$TASK_NAME.log
LOG_PATH=$LOGS_DIR/$LOG_FILE
```

```
.dev/
└── features/
    └── <##>-<feature name>/           # ex "02-dev-env-setup-postgresql-db/"
        └── scripts/
            └── 01-read-container-logs.sh  # example adhoc script to read container logs
```

## validation guide

- inventory all first-out exceptions and issues encountered in the issues table
- issue tasks and subtasks are identified by {feature_id}.IS.{issue_id}.{subtask_id}... — ex: 02.IS.01.01...
- for each issue, create an issue section and use it to document diagnostics and resolution steps
- a first-out exception is NOT a diagnostic step
- diagnostic steps reveal information or apply a fix
- assume re-run and validation — these are not diagnostic steps
- keep the step description brief; use the diagnostic details section to elaborate actions and learnings for each step

**issue diagnostics sections**

- problem description
- exception
- triggering actions
- hypothesis
- diagnostic steps
- diagnostic details

**issues table**

| id       | seq | status  | issue                 |
| -------- | --- | ------- | ---------------------- |
| 02.IS.01 | 01  | pending | \<first out exception\> |

**issue section header**

```
_02.IS.01 (pending) <first out exception>_
```

**diagnostic steps table**

| id          | seq | status  | step                    |
| ----------- | --- | ------- | ------------------------ |
| 02.IS.01.01 | 01  | pending | \<diagnostic step 01\>  |

**diagnostic dir**

```
.dev/
└── features/
    └── <##>-<feature name>/           # ex "02-dev-env-setup-postgresql-db/"
        └── scripts/
            └── 01-read-container-logs.sh  # example adhoc script to read container logs
```
