#!/usr/bin/env python3
"""data-generators.py

Generates deterministic mock row data for all 9 tables in scope for
feature 04 (seed mock data), plus a ground-truth issue-log.csv recording
every intentionally-injected data-quality issue.

Stdlib-only, no DB driver, no Faker - none of the 9 seeded tables carry
free-text fields (customer name, address, etc.), only codes/IDs/dates/
amounts, so deterministic pools cover it without a third-party dependency.
Writes one CSV per table to a staging directory; scripts/03-mock-data-seed.sh
loads each via `psql \\copy`.

Deterministic: every generation call is seeded from MOCK_DATA_SEED, so a
rerun with the same env produces byte-identical output.

See docs/features/04-seed-mock-data.md -> Design for the full issue
catalogs and volume budget this implements.

Usage:
    python3 scripts/utils/data-generators.py --out-dir data/mock
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# --- configuration (env-parameterized, see .env MOCK_DATA_*) ---

SEED = int(os.environ.get("MOCK_DATA_SEED", "42"))
DAYS = int(os.environ.get("MOCK_DATA_DAYS", "5"))
TXN_PER_DAY = int(os.environ.get("MOCK_DATA_TXN_PER_DAY", "400"))
PAYMENTS_PER_DAY = int(os.environ.get("MOCK_DATA_PAYMENTS_PER_DAY", "400"))
N_CUSTOMERS = int(os.environ.get("MOCK_DATA_CUSTOMERS", "300"))

# fixed anchor so the mock window is stable across runs/dates, not tied to "today"
ANCHOR_DATE = date(2026, 8, 17)  # Monday
BUSINESS_DAYS = [ANCHOR_DATE + timedelta(days=i) for i in range(DAYS)]

rng = random.Random(SEED)

issue_log: list[dict] = []


def log_issue(table: str, row_key: str, issue_type: str, expected: str, injected: str) -> None:
    issue_log.append(
        {
            "table": table,
            "row_key": row_key,
            "issue_type": issue_type,
            "expected_value": expected,
            "injected_value": injected,
        }
    )


def record_hash(*fields) -> str:
    return hashlib.sha256("|".join(str(f) for f in fields).encode()).hexdigest()


def d2(x) -> str:
    """Format a number as a 2-decimal string for CSV output."""
    return str(Decimal(str(x)).quantize(Decimal("0.01")))


def write_csv(out_dir: Path, table_file: str, columns: list[str], rows: list[dict]) -> int:
    out_path = out_dir / f"{table_file}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: ("" if row.get(c) is None else row.get(c)) for c in columns})
    return len(rows)


# ============================================================
# Assessment 1: src_transaction_daily / bronze.transaction_daily
# ============================================================

AS01_SOURCE_COLUMNS = [
    "transaction_id", "account_id", "transaction_date", "posting_date", "transaction_type",
    "currency_code", "transaction_amount", "local_currency_amount", "exchange_rate",
    "branch_code", "product_code", "source_system", "ingestion_file", "source_extract_ts",
]
AS01_BRONZE_COLUMNS = AS01_SOURCE_COLUMNS + [
    "ingestion_timestamp", "batch_id", "record_hash", "source_file_name",
]

CURRENCIES = ["SGD", "USD", "EUR", "GBP", "JPY"]
FX_RATE_ANCHORS = {"SGD": 1.0, "USD": 1.34, "EUR": 1.46, "GBP": 1.71, "JPY": 0.0088}
FX_JITTER_PCT = 0.015  # +/-1.5% day-to-day movement perturbed around each anchor
BRANCHES = [f"BR{n:03d}" for n in range(1, 21)]
AS01_PRODUCTS = ["SAVINGS", "CURRENT", "INVESTMENT", "LOAN"]
ACCOUNTS = [f"ACC-{n:07d}" for n in range(1000000, 1000500)]


def fx_rate(currency: str) -> Decimal:
    """SGD-equivalent exchange rate for `currency`, perturbed around its FX_RATE_ANCHORS anchor.

    Modeling day-to-day FX movement as a small jitter around a realistic anchor,
    rather than one currency-blind rng.uniform(0.6, 1.5) draw, keeps every currency's
    rate in a plausible range - a JPY rate never lands anywhere near a USD/EUR/GBP one.
    """
    if currency == "SGD":
        return Decimal("1.00000000")
    anchor = FX_RATE_ANCHORS[currency]
    jitter = 1 + rng.uniform(-FX_JITTER_PCT, FX_JITTER_PCT)
    return Decimal(str(round(anchor * jitter, 8)))


def gen_assessment1(out_dir: Path) -> None:
    source_rows: list[dict] = []
    midnight_files = {d: f"source_extract_{d.strftime('%y%m%d')}_MIDNIGHT.dat" for d in BUSINESS_DAYS}

    seq = 0
    for day_idx, txn_date in enumerate(BUSINESS_DAYS):
        for i in range(TXN_PER_DAY):
            seq += 1
            txn_id = f"TXN-{seq:07d}"
            currency = rng.choices(CURRENCIES, weights=[55, 20, 10, 10, 5])[0]
            rate = fx_rate(currency)
            amount = Decimal(str(round(rng.uniform(10, 50000), 2)))
            local_amount = (amount * rate).quantize(Decimal("0.01"))
            posting_date = txn_date + timedelta(days=rng.choice([0, 0, 0, 1, 2]))
            file_idx = rng.randint(1, 3)
            ingestion_file = f"source_extract_{txn_date.strftime('%y%m%d')}_{file_idx:02d}.dat"
            extract_ts = datetime.combine(txn_date, datetime.min.time()) + timedelta(
                hours=rng.randint(8, 20), minutes=rng.randint(0, 59)
            )
            source_rows.append(
                {
                    "transaction_id": txn_id,
                    "account_id": rng.choice(ACCOUNTS),
                    "transaction_date": txn_date.isoformat(),
                    "posting_date": posting_date.isoformat(),
                    "transaction_type": rng.choice(["CREDIT", "DEBIT"]),
                    "currency_code": currency,
                    "transaction_amount": d2(amount),
                    "local_currency_amount": d2(local_amount),
                    "exchange_rate": str(rate),
                    "branch_code": rng.choice(BRANCHES),
                    "product_code": rng.choice(AS01_PRODUCTS),
                    "source_system": "COREBANKING",
                    "ingestion_file": ingestion_file,
                    "source_extract_ts": extract_ts.isoformat() + "+08:00",
                }
            )

    def pick(n: int, exclude: set[int] | None = None) -> list[int]:
        pool = [i for i in range(len(source_rows)) if not exclude or i not in exclude]
        return rng.sample(pool, min(n, len(pool)))

    used: set[int] = set()

    # issue 01: duplicate transaction_id (clone an existing row unmutated)
    for idx in pick(10, used):
        used.add(idx)
        clone = dict(source_rows[idx])
        source_rows.append(clone)
        log_issue("src_transaction_daily", clone["transaction_id"], "duplicate_transaction_id",
                   "unique transaction_id", "duplicate row inserted")

    # issue 02: null critical field
    for i, idx in enumerate(pick(10, used)):
        used.add(idx)
        field = "account_id" if i % 2 == 0 else "currency_code"
        old = source_rows[idx][field]
        source_rows[idx][field] = None
        log_issue("src_transaction_daily", source_rows[idx]["transaction_id"], f"null_{field}", old, "NULL")

    # issue 03: invalid currency_code
    for idx in pick(8, used):
        used.add(idx)
        old = source_rows[idx]["currency_code"]
        bad = rng.choice(["XXX", "ZZZ", "usd", "SG"])
        source_rows[idx]["currency_code"] = bad
        log_issue("src_transaction_daily", source_rows[idx]["transaction_id"], "invalid_currency_code", old, bad)

    # issue 04: invalid transaction_type
    for idx in pick(5, used):
        used.add(idx)
        old = source_rows[idx]["transaction_type"]
        bad = rng.choice(["TRANSFER", "REVERSAL", "ADJUSTMENT"])
        source_rows[idx]["transaction_type"] = bad
        log_issue("src_transaction_daily", source_rows[idx]["transaction_id"], "invalid_transaction_type", old, bad)

    # issue 05: negative or zero transaction_amount
    for idx in pick(12, used):
        used.add(idx)
        old = source_rows[idx]["transaction_amount"]
        new = "0.00" if rng.random() < 0.3 else d2(-Decimal(old))
        source_rows[idx]["transaction_amount"] = new
        log_issue("src_transaction_daily", source_rows[idx]["transaction_id"], "negative_or_zero_amount", old, new)

    # issue 06: posting_date precedes transaction_date
    for idx in pick(6, used):
        used.add(idx)
        old = source_rows[idx]["posting_date"]
        txn_d = date.fromisoformat(source_rows[idx]["transaction_date"])
        new = (txn_d - timedelta(days=rng.randint(1, 3))).isoformat()
        source_rows[idx]["posting_date"] = new
        log_issue("src_transaction_daily", source_rows[idx]["transaction_id"], "posting_before_transaction", old, new)

    # issue 07: FX mismatch beyond tolerance
    for idx in pick(15, used):
        used.add(idx)
        old = source_rows[idx]["local_currency_amount"]
        amt = Decimal(source_rows[idx]["transaction_amount"])
        rate = Decimal(source_rows[idx]["exchange_rate"])
        new = d2(amt * rate * Decimal("1.20"))
        source_rows[idx]["local_currency_amount"] = new
        log_issue("src_transaction_daily", source_rows[idx]["transaction_id"], "fx_mismatch", old, new)

    # issue 08: late-arriving (source_extract_ts next day)
    for idx in pick(10, used):
        used.add(idx)
        old = source_rows[idx]["source_extract_ts"]
        txn_d = date.fromisoformat(source_rows[idx]["transaction_date"])
        new_ts = datetime.combine(txn_d + timedelta(days=1), datetime.min.time()) + timedelta(hours=9)
        new = new_ts.isoformat() + "+08:00"
        source_rows[idx]["source_extract_ts"] = new
        log_issue("src_transaction_daily", source_rows[idx]["transaction_id"], "late_arriving", old, new)

    # issue 09: UTC/SGT midnight-boundary rows - reassign ~20 rows to 3 midnight files,
    # with source_extract_ts stamped in UTC just after midnight (no offset), for a
    # transaction that is actually still SGT business-date "today" (SGT = UTC+8, so
    # 23:45 SGT = 15:45 UTC the same day, but 00:15 SGT next day = 16:15 UTC previous
    # day - the ingestion process's SGT-business-date logic drops these).
    midnight_idxs = pick(20, used)
    midnight_txn_ids = []
    for i, idx in enumerate(midnight_idxs):
        used.add(idx)
        txn_d = date.fromisoformat(source_rows[idx]["transaction_date"])
        old_file = source_rows[idx]["ingestion_file"]
        new_file = midnight_files[txn_d]
        source_rows[idx]["ingestion_file"] = new_file
        utc_ts = datetime.combine(txn_d, datetime.min.time()) + timedelta(hours=23, minutes=45 + (i % 15))
        source_rows[idx]["source_extract_ts"] = utc_ts.isoformat() + "+00:00"
        midnight_txn_ids.append(source_rows[idx]["transaction_id"])
        log_issue("src_transaction_daily", source_rows[idx]["transaction_id"], "utc_sgt_midnight_boundary",
                   old_file, f"{new_file} (dropped in Bronze)")

    # --- derive bronze.transaction_daily from source ---
    bronze_rows = [dict(r) for r in source_rows if r["transaction_id"] not in set(midnight_txn_ids)]

    # issue 10: unrelated small ingestion gap
    gap_idxs = rng.sample(range(len(bronze_rows)), min(5, len(bronze_rows)))
    dropped_ids = {bronze_rows[i]["transaction_id"] for i in gap_idxs}
    for tid in dropped_ids:
        log_issue("bronze.transaction_daily", tid, "missing_in_bronze_unrelated", "present", "dropped")
    bronze_rows = [r for r in bronze_rows if r["transaction_id"] not in dropped_ids]

    def add_bronze_metadata(row: dict, batch_suffix: str = "") -> dict:
        row = dict(row)
        extract_ts = row["source_extract_ts"]
        row["ingestion_timestamp"] = extract_ts
        row["batch_id"] = f"BATCH-{row['transaction_date'].replace('-', '')}{batch_suffix}"
        row["record_hash"] = record_hash(row["transaction_id"], row["account_id"], row["transaction_amount"])
        row["source_file_name"] = row["ingestion_file"]
        return row

    bronze_rows = [add_bronze_metadata(r) for r in bronze_rows]

    # issue 11: duplicate record in Bronze (reprocessed file)
    for idx in rng.sample(range(len(bronze_rows)), min(8, len(bronze_rows))):
        clone = add_bronze_metadata(bronze_rows[idx], batch_suffix="-R")
        bronze_rows.append(clone)
        log_issue("bronze.transaction_daily", clone["transaction_id"], "duplicate_in_bronze_reprocessed",
                   "single batch_id", f"{clone['batch_id']} (reprocessed)")

    # issue 12: amount mismatch introduced by Bronze transform
    for idx in rng.sample(range(len(bronze_rows)), min(10, len(bronze_rows))):
        old = bronze_rows[idx]["transaction_amount"]
        new = d2(Decimal(old) + Decimal(str(round(rng.uniform(0.5, 5.0), 2))))
        bronze_rows[idx]["transaction_amount"] = new
        log_issue("bronze.transaction_daily", bronze_rows[idx]["transaction_id"], "bronze_amount_mismatch", old, new)

    # issue 13: currency mismatch introduced by Bronze transform
    for idx in rng.sample(range(len(bronze_rows)), min(4, len(bronze_rows))):
        old = bronze_rows[idx]["currency_code"]
        new = rng.choice([c for c in CURRENCIES if c != old])
        bronze_rows[idx]["currency_code"] = new
        log_issue("bronze.transaction_daily", bronze_rows[idx]["transaction_id"], "bronze_currency_mismatch", old, new)

    # issue 14: posting-date mismatch introduced by transform
    for idx in rng.sample(range(len(bronze_rows)), min(5, len(bronze_rows))):
        old = bronze_rows[idx]["posting_date"]
        new = (date.fromisoformat(old) + timedelta(days=rng.randint(1, 3))).isoformat()
        bronze_rows[idx]["posting_date"] = new
        log_issue("bronze.transaction_daily", bronze_rows[idx]["transaction_id"], "bronze_posting_date_mismatch", old, new)

    n_src = write_csv(out_dir, "src_transaction_daily", AS01_SOURCE_COLUMNS, source_rows)
    n_bronze = write_csv(out_dir, "bronze_transaction_daily", AS01_BRONZE_COLUMNS, bronze_rows)
    print(f"[PASS] generated src_transaction_daily: {n_src} rows")
    print(f"[PASS] generated bronze.transaction_daily: {n_bronze} rows")


# ============================================================
# Assessment 2: bronze.finance_transactions / finance.gl_balance / ref.accounting_mapping
# ============================================================

AS02_TXN_COLUMNS = [
    "transaction_id", "account_id", "transaction_date", "posting_date", "transaction_amount",
    "currency", "exchange_rate", "local_amount", "debit_credit_indicator", "product_code",
    "branch_code", "gl_account", "cost_center", "legal_entity",
]
AS02_MAPPING_COLUMNS = [
    "product_code", "transaction_type", "expected_gl_account", "expected_cost_center",
    "effective_start_date", "effective_end_date",
]
AS02_GL_COLUMNS = [
    "accounting_date", "legal_entity", "gl_account", "cost_center", "currency",
    "opening_balance", "debit_movement", "credit_movement", "closing_balance",
]

AS02_PRODUCTS = [f"P{n}" for n in range(1, 11)]
LEGAL_ENTITIES = ["LE1", "LE2", "LE3", "LE4"]
GL_ACCOUNTS = [f"GL{1000 + n}" for n in range(15)]
COST_CENTERS = [f"CC{n:02d}" for n in range(1, 11)]
SUSPENSE_GL, SUSPENSE_CC = "GL9999", "CC99"


def account_legal_entity(account_id: str) -> str:
    """Deterministic 'correct' legal entity for an account - ground truth for issue 10.

    Uses a stable hash (hashlib, not builtin hash()) since Python randomizes
    str hash() per-process by default - builtin hash() would break the
    "byte-identical rerun" determinism this whole pipeline depends on.
    """
    digest = hashlib.md5(account_id.encode()).hexdigest()
    return LEGAL_ENTITIES[int(digest, 16) % len(LEGAL_ENTITIES)]


def gen_assessment2(out_dir: Path) -> None:
    # --- ref.accounting_mapping ---
    mapping_rows: list[dict] = []
    combos = [(p, t) for p in AS02_PRODUCTS for t in ["DEBIT", "CREDIT"]]
    rng.shuffle(combos)
    missing_combos = set(combos[:5])  # issue 03: no mapping row at all
    mapped_combos = combos[5:]

    gl_by_combo: dict[tuple, tuple[str, str]] = {}
    for i, (product, ttype) in enumerate(mapped_combos):
        gl = GL_ACCOUNTS[i % len(GL_ACCOUNTS)]
        cc = COST_CENTERS[i % len(COST_CENTERS)]
        gl_by_combo[(product, ttype)] = (gl, cc)
        mapping_rows.append(
            {
                "product_code": product, "transaction_type": ttype,
                "expected_gl_account": gl, "expected_cost_center": cc,
                "effective_start_date": (ANCHOR_DATE - timedelta(days=365)).isoformat(),
                "effective_end_date": None,
            }
        )

    # issue 01: overlapping effective-date mapping ranges (3 combos)
    for product, ttype in rng.sample(mapped_combos, 3):
        gl, cc = gl_by_combo[(product, ttype)]
        overlap_start = (ANCHOR_DATE - timedelta(days=30)).isoformat()
        mapping_rows.append(
            {
                "product_code": product, "transaction_type": ttype,
                "expected_gl_account": rng.choice(GL_ACCOUNTS), "expected_cost_center": cc,
                "effective_start_date": overlap_start, "effective_end_date": None,
            }
        )
        log_issue("ref.accounting_mapping", f"{product}|{ttype}|{overlap_start}",
                   "overlapping_effective_dates", "non-overlapping ranges", f"overlaps open-ended row from -365d")

    # issue 02: expired mapping still referenced by recent transactions (2 combos)
    expired_combo_gl: dict[tuple, str] = {}
    for product, ttype in rng.sample(mapped_combos, 2):
        expired_gl = rng.choice(GL_ACCOUNTS)
        start = (ANCHOR_DATE - timedelta(days=200)).isoformat()
        end = (ANCHOR_DATE - timedelta(days=10)).isoformat()
        mapping_rows.append(
            {
                "product_code": product, "transaction_type": ttype,
                "expected_gl_account": expired_gl, "expected_cost_center": COST_CENTERS[0],
                "effective_start_date": start, "effective_end_date": end,
            }
        )
        expired_combo_gl[(product, ttype)] = expired_gl
        log_issue("ref.accounting_mapping", f"{product}|{ttype}|{start}",
                   "expired_mapping_still_used", f"expired {end}", "referenced by post-expiry transactions")

    # issue 04: product mapped to multiple GL accounts unexpectedly (2 products)
    for product, ttype in rng.sample(mapped_combos, 2):
        gl, cc = gl_by_combo[(product, ttype)]
        alt_gl = rng.choice([g for g in GL_ACCOUNTS if g != gl])
        start = (ANCHOR_DATE - timedelta(days=5)).isoformat()
        mapping_rows.append(
            {
                "product_code": product, "transaction_type": ttype,
                "expected_gl_account": alt_gl, "expected_cost_center": cc,
                "effective_start_date": start, "effective_end_date": None,
            }
        )
        log_issue("ref.accounting_mapping", f"{product}|{ttype}|{start}",
                   "product_multiple_gl_accounts", gl, alt_gl)

    # --- bronze.finance_transactions ---
    txn_rows: list[dict] = []
    seq = 0
    txns_per_day = int(os.environ.get("MOCK_DATA_FINANCE_TXN_PER_DAY", "300"))
    for txn_date in BUSINESS_DAYS:
        for _ in range(txns_per_day):
            seq += 1
            txn_id = f"FTX-{seq:07d}"
            account_id = rng.choice(ACCOUNTS)
            product = rng.choice(AS02_PRODUCTS)
            ttype = rng.choice(["DEBIT", "CREDIT"])
            currency = rng.choices(CURRENCIES[:3], weights=[70, 20, 10])[0]
            rate = fx_rate(currency)
            amount = Decimal(str(round(rng.uniform(50, 20000), 2)))
            local = (amount * rate).quantize(Decimal("0.01"))
            gl, cc = gl_by_combo.get((product, ttype), (SUSPENSE_GL, SUSPENSE_CC))
            legal_entity = account_legal_entity(account_id)
            txn_rows.append(
                {
                    "transaction_id": txn_id, "account_id": account_id,
                    "transaction_date": txn_date.isoformat(), "posting_date": txn_date.isoformat(),
                    "transaction_amount": d2(amount), "currency": currency, "exchange_rate": str(rate),
                    "local_amount": d2(local), "debit_credit_indicator": ttype, "product_code": product,
                    "branch_code": rng.choice(BRANCHES), "gl_account": gl, "cost_center": cc,
                    "legal_entity": legal_entity,
                }
            )

    def pick(n: int, exclude: set[int] | None = None) -> list[int]:
        pool = [i for i in range(len(txn_rows)) if not exclude or i not in exclude]
        return rng.sample(pool, min(n, len(pool)))

    used: set[int] = set()

    # issue 05: duplicate accounting entry (exact re-post, new transaction_id)
    for idx in pick(15, used):
        used.add(idx)
        clone = dict(txn_rows[idx])
        clone["transaction_id"] = f"FTX-DUP{len(txn_rows) + 1:06d}"
        txn_rows.append(clone)
        log_issue("bronze.finance_transactions", clone["transaction_id"], "duplicate_accounting_entry",
                   txn_rows[idx]["transaction_id"], "exact re-post under a new transaction_id")

    # issue 06: transaction posted twice under a different ID (same econ event, minor drift)
    for idx in pick(8, used):
        used.add(idx)
        clone = dict(txn_rows[idx])
        clone["transaction_id"] = f"FTX-DUP{len(txn_rows) + 1:06d}"
        clone["posting_date"] = (date.fromisoformat(clone["posting_date"]) + timedelta(days=0)).isoformat()
        txn_rows.append(clone)
        log_issue("bronze.finance_transactions", clone["transaction_id"], "posted_twice_different_id",
                   txn_rows[idx]["transaction_id"], "same economics, second transaction_id")

    # issue 07: incorrect debit/credit indicator
    for idx in pick(10, used):
        used.add(idx)
        old = txn_rows[idx]["debit_credit_indicator"]
        new = "CREDIT" if old == "DEBIT" else "DEBIT"
        txn_rows[idx]["debit_credit_indicator"] = new
        log_issue("bronze.finance_transactions", txn_rows[idx]["transaction_id"], "incorrect_dr_cr_indicator", old, new)

    # issue 08: incorrect FX conversion (stale/wrong rate)
    for idx in pick(8, used):
        if txn_rows[idx]["currency"] == "SGD":
            continue
        used.add(idx)
        old = txn_rows[idx]["local_amount"]
        amt = Decimal(txn_rows[idx]["transaction_amount"])
        rate = Decimal(txn_rows[idx]["exchange_rate"])
        new = d2(amt * rate * Decimal("1.10"))
        txn_rows[idx]["local_amount"] = new
        log_issue("bronze.finance_transactions", txn_rows[idx]["transaction_id"], "incorrect_fx_conversion", old, new)

    # issue 09: posted one accounting day late
    for idx in pick(12, used):
        used.add(idx)
        old = txn_rows[idx]["posting_date"]
        new = (date.fromisoformat(old) + timedelta(days=1)).isoformat()
        txn_rows[idx]["posting_date"] = new
        log_issue("bronze.finance_transactions", txn_rows[idx]["transaction_id"], "posted_one_day_late", old, new)

    # issue 10: incorrect legal-entity allocation (vs account's deterministic "correct" entity)
    for idx in pick(6, used):
        used.add(idx)
        correct = account_legal_entity(txn_rows[idx]["account_id"])
        wrong = rng.choice([le for le in LEGAL_ENTITIES if le != correct])
        txn_rows[idx]["legal_entity"] = wrong
        log_issue("bronze.finance_transactions", txn_rows[idx]["transaction_id"], "incorrect_legal_entity", correct, wrong)

    # issue 11: incorrect cost-center assignment (vs ref.accounting_mapping's expected_cost_center)
    for idx in pick(7, used):
        used.add(idx)
        product, ttype = txn_rows[idx]["product_code"], txn_rows[idx]["debit_credit_indicator"]
        expected_cc = gl_by_combo.get((product, ttype), (SUSPENSE_GL, SUSPENSE_CC))[1]
        wrong_cc = rng.choice([cc for cc in COST_CENTERS if cc != expected_cc])
        txn_rows[idx]["cost_center"] = wrong_cc
        log_issue("bronze.finance_transactions", txn_rows[idx]["transaction_id"], "incorrect_cost_center",
                   expected_cc, wrong_cc)

    # a handful of transactions using an expired mapping's GL account (feeds issue 02's discovery)
    for (product, ttype), expired_gl in expired_combo_gl.items():
        candidates = [i for i, r in enumerate(txn_rows) if r["product_code"] == product and r["debit_credit_indicator"] == ttype]
        for idx in rng.sample(candidates, min(3, len(candidates))):
            txn_rows[idx]["gl_account"] = expired_gl

    # --- finance.gl_balance: aggregate from (already-mutated) transactions ---
    groups: dict[tuple, dict] = {}
    for r in txn_rows:
        key = (r["posting_date"], r["legal_entity"], r["gl_account"], r["cost_center"], r["currency"])
        g = groups.setdefault(key, {"debit": Decimal("0"), "credit": Decimal("0")})
        amt = Decimal(r["transaction_amount"])
        if r["debit_credit_indicator"] == "DEBIT":
            g["debit"] += amt
        else:
            g["credit"] += amt

    gl_rows: list[dict] = []
    opening_carry: dict[tuple, Decimal] = {}
    for key in sorted(groups.keys()):
        accounting_date, legal_entity, gl_account, cost_center, currency = key
        carry_key = (legal_entity, gl_account, cost_center, currency)
        opening = opening_carry.get(carry_key, Decimal(str(round(rng.uniform(1000, 50000), 2))))
        debit, credit = groups[key]["debit"], groups[key]["credit"]
        closing = opening + debit - credit
        opening_carry[carry_key] = closing
        gl_rows.append(
            {
                "accounting_date": accounting_date, "legal_entity": legal_entity, "gl_account": gl_account,
                "cost_center": cost_center, "currency": currency, "opening_balance": d2(opening),
                "debit_movement": d2(debit), "credit_movement": d2(credit), "closing_balance": d2(closing),
            }
        )

    # issue 12: opening + debit - credit != closing violation (5 rows, corrupted post-aggregation)
    for idx in rng.sample(range(len(gl_rows)), min(5, len(gl_rows))):
        old = gl_rows[idx]["closing_balance"]
        delta = Decimal(str(round(rng.uniform(100, 5000), 2))) * rng.choice([1, -1])
        new = d2(Decimal(old) + delta)
        gl_rows[idx]["closing_balance"] = new
        key = f"{gl_rows[idx]['accounting_date']}|{gl_rows[idx]['legal_entity']}|{gl_rows[idx]['gl_account']}|{gl_rows[idx]['cost_center']}|{gl_rows[idx]['currency']}"
        log_issue("finance.gl_balance", key, "arithmetic_integrity_violation", old, new)

    n_map = write_csv(out_dir, "ref_accounting_mapping", AS02_MAPPING_COLUMNS, mapping_rows)
    n_txn = write_csv(out_dir, "bronze_finance_transactions", AS02_TXN_COLUMNS, txn_rows)
    n_gl = write_csv(out_dir, "finance_gl_balance", AS02_GL_COLUMNS, gl_rows)
    print(f"[PASS] generated ref.accounting_mapping: {n_map} rows")
    print(f"[PASS] generated bronze.finance_transactions: {n_txn} rows")
    print(f"[PASS] generated finance.gl_balance: {n_gl} rows")


# ============================================================
# Assessment 3: source.payment_transactions / bronze.payment_transactions /
#               bronze.customer_master / regulatory.payment_reporting
# ============================================================

AS03_PAY_COLUMNS = [
    "payment_id", "customer_id", "account_id", "payment_date", "payment_timestamp",
    "payment_type", "payment_channel", "beneficiary_country", "currency", "amount",
    "status", "legal_entity",
]
AS03_BRONZE_PAY_COLUMNS = AS03_PAY_COLUMNS + [
    "ingestion_timestamp", "batch_id", "record_hash", "source_file_name",
]
AS03_CUSTOMER_COLUMNS = [
    "customer_id", "customer_type", "residence_country", "risk_rating", "segment",
    "legal_entity", "effective_start_date", "effective_end_date",
]
AS03_REPORTING_COLUMNS = [
    "reporting_date", "customer_id", "payment_type", "domestic_crossborder_flag",
    "transaction_count", "total_transaction_amount", "reporting_currency", "legal_entity",
]

COUNTRIES = ["SG", "MY", "ID", "US", "GB", "CN", "IN", "AU", "JP", "HK"]
PAYMENT_TYPES = ["WIRE", "GIRO", "CARD", "INTERNAL", "INSTANT"]
CHANNELS = ["BRANCH", "MOBILE", "INTERNET", "API"]
STATUSES = ["COMPLETED", "PENDING", "FAILED", "REJECTED"]
CUSTOMER_IDS = [f"CUST-{n:06d}" for n in range(1, N_CUSTOMERS + 1)]


def gen_assessment3(out_dir: Path) -> None:
    # --- bronze.customer_master ---
    customer_rows: list[dict] = []
    residence_by_customer: dict[str, str] = {}
    active_customers = list(CUSTOMER_IDS)

    missing_customers = set(rng.sample(active_customers, 5))  # issue 06
    remaining = [c for c in active_customers if c not in missing_customers]
    inactive_customers = set(rng.sample(remaining, 5))  # issue 07
    fanout_customers = set(rng.sample([c for c in remaining if c not in inactive_customers], 20))  # issue 08

    for cid in active_customers:
        if cid in missing_customers:
            continue
        residence = rng.choice(COUNTRIES)
        residence_by_customer[cid] = residence
        base_row = {
            "customer_id": cid, "customer_type": rng.choice(["INDIVIDUAL", "CORPORATE"]),
            "residence_country": residence, "risk_rating": rng.choice(["LOW", "MEDIUM", "HIGH"]),
            "segment": rng.choice(["RETAIL", "PRIVATE", "CORPORATE", "SME"]),
            "legal_entity": rng.choice(LEGAL_ENTITIES),
            "effective_start_date": (ANCHOR_DATE - timedelta(days=400)).isoformat(),
            "effective_end_date": None,
        }
        if cid in inactive_customers:
            base_row["effective_end_date"] = (ANCHOR_DATE - timedelta(days=5)).isoformat()
            log_issue("bronze.customer_master", cid, "inactive_but_referenced",
                       "effective_end_date in the past", "still referenced by recent payments")
        customer_rows.append(base_row)

        if cid in fanout_customers:
            # bug: the prior row's effective_end_date should have been closed to
            # anchor-2 but was left NULL - both rows are "active" to a naive join
            new_row = dict(base_row)
            new_row["residence_country"] = rng.choice([c for c in COUNTRIES if c != residence])
            new_row["segment"] = rng.choice(["RETAIL", "PRIVATE", "CORPORATE", "SME"])
            new_row["effective_start_date"] = (ANCHOR_DATE - timedelta(days=2)).isoformat()
            new_row["effective_end_date"] = None
            customer_rows.append(new_row)
            log_issue("bronze.customer_master", cid, "multiple_active_records",
                       "prior row's effective_end_date closed", "left NULL - two NULL-end rows for one customer_id")

    # --- source.payment_transactions ---
    pay_rows: list[dict] = []
    seq = 0
    referenceable_customers = active_customers  # payments may reference missing/inactive customers on purpose
    for pay_date in BUSINESS_DAYS:
        for _ in range(PAYMENTS_PER_DAY):
            seq += 1
            pay_id = f"PAY-{seq:07d}"
            cid = rng.choice(referenceable_customers)
            residence = residence_by_customer.get(cid, rng.choice(COUNTRIES))
            beneficiary = residence if rng.random() < 0.6 else rng.choice(COUNTRIES)
            currency = rng.choices(CURRENCIES[:3], weights=[70, 20, 10])[0]
            ts = datetime.combine(pay_date, datetime.min.time()) + timedelta(hours=rng.randint(7, 21), minutes=rng.randint(0, 59))
            pay_rows.append(
                {
                    "payment_id": pay_id, "customer_id": cid, "account_id": rng.choice(ACCOUNTS),
                    "payment_date": pay_date.isoformat(), "payment_timestamp": ts.isoformat(),
                    "payment_type": rng.choice(PAYMENT_TYPES), "payment_channel": rng.choice(CHANNELS),
                    "beneficiary_country": beneficiary, "currency": currency,
                    "amount": d2(round(rng.uniform(20, 25000), 2)), "status": rng.choice(STATUSES),
                    "legal_entity": rng.choice(LEGAL_ENTITIES),
                }
            )

    def pick(n: int, exclude: set[int] | None = None) -> list[int]:
        pool = [i for i in range(len(pay_rows)) if not exclude or i not in exclude]
        return rng.sample(pool, min(n, len(pool)))

    used: set[int] = set()

    # issue 01: duplicate payment_id (legitimate repeat payment, control case)
    for idx in pick(5, used):
        used.add(idx)
        clone = dict(pay_rows[idx])
        pay_rows.append(clone)
        log_issue("source.payment_transactions", clone["payment_id"], "legitimate_repeat_payment",
                   "single occurrence", "genuinely repeated payment, same payment_id")

    # issue 02: missing customer_id / invalid beneficiary country
    for i, idx in enumerate(pick(8, used)):
        used.add(idx)
        if i % 2 == 0:
            old = pay_rows[idx]["customer_id"]
            pay_rows[idx]["customer_id"] = None
            log_issue("source.payment_transactions", pay_rows[idx]["payment_id"], "missing_customer_id", old, "NULL")
        else:
            old = pay_rows[idx]["beneficiary_country"]
            new = rng.choice(["XX", "ZZ", "??"])
            pay_rows[idx]["beneficiary_country"] = new
            log_issue("source.payment_transactions", pay_rows[idx]["payment_id"], "invalid_beneficiary_country", old, new)

    # issue 03: negative or zero payment amount
    for idx in pick(6, used):
        used.add(idx)
        old = pay_rows[idx]["amount"]
        new = "0.00" if rng.random() < 0.3 else d2(-Decimal(old))
        pay_rows[idx]["amount"] = new
        log_issue("source.payment_transactions", pay_rows[idx]["payment_id"], "negative_or_zero_amount", old, new)

    # --- bronze.payment_transactions (derive from source) ---
    def add_bronze_metadata(row: dict, batch_suffix: str = "") -> dict:
        row = dict(row)
        row["ingestion_timestamp"] = row["payment_timestamp"]
        row["batch_id"] = f"PBATCH-{row['payment_date'].replace('-', '')}{batch_suffix}"
        row["record_hash"] = record_hash(row["payment_id"], row["customer_id"], row["amount"])
        row["source_file_name"] = f"payments_{row['payment_date'].replace('-', '')}.dat"
        return row

    bronze_pay_rows = [add_bronze_metadata(r) for r in pay_rows]

    # issue 04: duplicate file reload under a second batch_id (~20 rows, one day's file)
    reload_day = BUSINESS_DAYS[2].isoformat()
    reload_candidates = [i for i, r in enumerate(bronze_pay_rows) if r["payment_date"] == reload_day]
    for idx in rng.sample(reload_candidates, min(20, len(reload_candidates))):
        clone = add_bronze_metadata(bronze_pay_rows[idx], batch_suffix="-RELOAD")
        bronze_pay_rows.append(clone)
        log_issue("bronze.payment_transactions", clone["payment_id"], "duplicate_file_reload",
                   bronze_pay_rows[idx]["batch_id"], f"{clone['batch_id']} (same payment_id, second batch)")

    # issue 05: late-arriving, assigned to next day's reporting date (tag only; applied
    # when building regulatory.payment_reporting below)
    late_idxs = rng.sample(range(len(bronze_pay_rows)), min(15, len(bronze_pay_rows)))
    late_payment_ids = {bronze_pay_rows[i]["payment_id"] for i in late_idxs}
    for pid in late_payment_ids:
        log_issue("bronze.payment_transactions", pid, "late_arriving_next_day_reporting",
                   "reporting_date = payment_date", "reporting_date = payment_date + 1 (regulatory mart)")

    # --- regulatory.payment_reporting: naive (non-effective-dated) join, replaying the bug ---
    # index ALL customer_master rows by customer_id (not filtered by effective date)
    customer_rows_by_id: dict[str, list[dict]] = {}
    for r in customer_rows:
        customer_rows_by_id.setdefault(r["customer_id"], []).append(r)

    reg_groups: dict[tuple, dict] = {}
    for r in bronze_pay_rows:
        matches = customer_rows_by_id.get(r["customer_id"], [])
        if not matches:
            continue  # missing customer reference - excluded from regulatory mart (issue 06's downstream effect)
        reporting_date = r["payment_date"]
        if r["payment_id"] in late_payment_ids:
            reporting_date = (date.fromisoformat(reporting_date) + timedelta(days=1)).isoformat()
        for cust in matches:  # naive join fans out over every matching row - the bug under test
            flag = "DOMESTIC" if cust["residence_country"] == r["beneficiary_country"] else "CROSSBORDER"
            # flag is part of the group key, not just a stored attribute: when a
            # customer has >1 active reference row (issue 08), different matches
            # can carry different residence_country -> different flag for the
            # same (date, customer, type, entity), so the fan-out surfaces as a
            # genuine second regulatory *row*, not an inflated count inside one.
            key = (reporting_date, r["customer_id"], r["payment_type"], r["legal_entity"], flag)
            g = reg_groups.setdefault(
                key, {"count": 0, "amount": Decimal("0"), "currency": r["currency"]}
            )
            g["count"] += 1
            g["amount"] += Decimal(r["amount"]) if r["amount"] not in (None, "") else Decimal("0")

    reg_rows: list[dict] = []
    for key in sorted(reg_groups.keys()):
        reporting_date, cid, payment_type, legal_entity, flag = key
        g = reg_groups[key]
        reg_rows.append(
            {
                "reporting_date": reporting_date, "customer_id": cid, "payment_type": payment_type,
                "domestic_crossborder_flag": flag, "transaction_count": g["count"],
                "total_transaction_amount": d2(g["amount"]), "reporting_currency": g["currency"],
                "legal_entity": legal_entity,
            }
        )

    for cid in fanout_customers:
        group_keys = [k for k in reg_groups if k[1] == cid]
        dims = {(k[0], k[2], k[3]) for k in group_keys}
        if len(group_keys) > len(dims):
            log_issue("regulatory.payment_reporting", cid, "join_fanout_duplicate_records",
                       "one row per (reporting_date, payment_type, legal_entity)",
                       f"{len(group_keys)} rows across {len(dims)} dimension combos - differing domestic_crossborder_flag")

    n_cust = write_csv(out_dir, "bronze_customer_master", AS03_CUSTOMER_COLUMNS, customer_rows)
    n_src = write_csv(out_dir, "source_payment_transactions", AS03_PAY_COLUMNS, pay_rows)
    n_bronze = write_csv(out_dir, "bronze_payment_transactions", AS03_BRONZE_PAY_COLUMNS, bronze_pay_rows)
    n_reg = write_csv(out_dir, "regulatory_payment_reporting", AS03_REPORTING_COLUMNS, reg_rows)
    print(f"[PASS] generated bronze.customer_master: {n_cust} rows")
    print(f"[PASS] generated source.payment_transactions: {n_src} rows")
    print(f"[PASS] generated bronze.payment_transactions: {n_bronze} rows")
    print(f"[PASS] generated regulatory.payment_reporting: {n_reg} rows (fan-out from {len(fanout_customers)} multi-active customers)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data" / "mock")
    args = parser.parse_args()

    print(f"[INFO] MOCK_DATA_SEED={SEED} DAYS={DAYS} TXN_PER_DAY={TXN_PER_DAY} "
          f"PAYMENTS_PER_DAY={PAYMENTS_PER_DAY} CUSTOMERS={N_CUSTOMERS}")

    try:
        gen_assessment1(args.out_dir)
        gen_assessment2(args.out_dir)
        gen_assessment3(args.out_dir)

        issue_log_path = args.out_dir / "issue-log.csv"
        issue_log_path.parent.mkdir(parents=True, exist_ok=True)
        with issue_log_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["table", "row_key", "issue_type", "expected_value", "injected_value"])
            writer.writeheader()
            writer.writerows(issue_log)
        print(f"[PASS] wrote {len(issue_log)} issue-log rows to {issue_log_path}")
    except Exception as exc:  # noqa: BLE001 - top-level safe wrapper, no silent failure
        print(f"[FAIL] data-generators: {exc}", file=sys.stderr)
        raise

    print("[PASS] data generation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
