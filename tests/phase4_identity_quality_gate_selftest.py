#!/usr/bin/env python3
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data" / "tokenoskobi_clean_v1.sqlite"

import sys
sys.path.insert(0, str(ROOT))

from core.identity import (
    make_token_uid,
    make_pair_uid,
    make_snapshot_uid,
    canonical_token_identity,
    canonical_pair_identity,
)
from core.validators import (
    validate_token_identity,
    validate_pair_identity,
    validate_snapshot_identity,
    detect_duplicate_identities,
)
from core.source_gate import validate_source, route_from_quality

def run():
    errors = []
    checks = []

    chain = "base"
    token_address = "0x10c56f005a379f8eafc88ff5c3f40d30f0031ac9"
    pair_address = "0x0982b1b0402bd01188ada44daa344274c37f1283"
    deployer = "0x1111111111111111111111111111111111111111"
    source = "MANUAL_PILOT"
    observed = "2026-05-06T20:00:00Z"

    token = canonical_token_identity(chain, token_address, deployer, "Strike Robot", "SR", source)
    pair = canonical_pair_identity(chain, token_address, pair_address, source, "unknown")

    token_check = validate_token_identity(token)
    checks.append({"name": "valid_token_identity", "ok": token_check["ok"], "result": token_check})
    if not token_check["ok"]:
        errors.append("valid_token_identity_failed")

    pair_check = validate_pair_identity(pair)
    checks.append({"name": "valid_pair_identity", "ok": pair_check["ok"], "result": pair_check})
    if not pair_check["ok"]:
        errors.append("valid_pair_identity_failed")

    snap_uid = make_snapshot_uid("liquidity", token["token_uid"], pair["pair_uid"], observed, source)
    snap = {
        "kind": "liquidity",
        "snapshot_uid": snap_uid,
        "token_uid": token["token_uid"],
        "pair_uid": pair["pair_uid"],
        "chain": chain,
        "pair_address": pair_address,
        "observed_at_utc": observed,
        "source": source,
    }
    snap_check = validate_snapshot_identity(snap)
    checks.append({"name": "valid_snapshot_identity", "ok": snap_check["ok"], "result": snap_check})
    if not snap_check["ok"]:
        errors.append("valid_snapshot_identity_failed")

    bad_token = dict(token)
    bad_token["token_uid"] = ""
    bad_token_check = validate_token_identity(bad_token)
    checks.append({"name": "reject_empty_token_uid", "ok": not bad_token_check["ok"], "result": bad_token_check})
    if bad_token_check["ok"]:
        errors.append("empty_token_uid_not_rejected")

    wbnb_token = canonical_token_identity(
        "bnb",
        "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
        None,
        "WBNB",
        "WBNB",
        source
    )
    wbnb_check = validate_token_identity(wbnb_token)
    checks.append({"name": "reject_base_quote_asset_as_token", "ok": not wbnb_check["ok"], "result": wbnb_check})
    if wbnb_check["ok"]:
        errors.append("base_quote_asset_not_rejected")

    dups = detect_duplicate_identities([token, dict(token)], ["chain", "token_address"])
    checks.append({"name": "detect_duplicate_identity", "ok": len(dups) == 1, "result": dups})
    if len(dups) != 1:
        errors.append("duplicate_identity_not_detected")

    src_check = validate_source("MANUAL_PILOT", api_allowed=False)
    checks.append({"name": "manual_source_allowed_noapi", "ok": src_check["ok"], "result": src_check})
    if not src_check["ok"]:
        errors.append("manual_source_not_allowed")

    api_src_check = validate_source("DEXSCREENER_CAPPED_REFRESH", api_allowed=False)
    checks.append({"name": "dexscreener_source_blocked_when_api_blocked", "ok": not api_src_check["ok"], "result": api_src_check})
    if api_src_check["ok"]:
        errors.append("api_source_not_blocked")

    route_check = route_from_quality(hard_fail=False, medium_risk=True, high_opportunity=True)
    checks.append({"name": "medium_risk_high_opp_watch_only", "ok": route_check == "WATCH_ONLY", "result": route_check})
    if route_check != "WATCH_ONLY":
        errors.append("route_rule_failed")

    tempdir = Path(tempfile.mkdtemp(prefix="tokenoskobi_phase4_dbguard_"))
    tempdb = tempdir / "test.sqlite"
    shutil.copy2(DB, tempdb)

    con = sqlite3.connect(str(tempdb))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")

    try:
        now = datetime.now(timezone.utc).isoformat()
        con.execute(
            """
            INSERT INTO tokens(token_uid, chain, token_address, deployer_address, name, symbol,
            first_seen_at_utc, source, identity_status, risk_route, created_at_utc, updated_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (token["token_uid"], token["chain"], token["token_address"], token["deployer_address"],
             token["name"], token["symbol"], now, source, "PILOT_OR_VERIFIED", "WATCH_ONLY", now, now)
        )
        con.execute(
            """
            INSERT INTO pairs(pair_uid, token_uid, chain, pair_address, dex_name, base_token_address,
            quote_token_address, first_seen_at_utc, source, pair_status, quality_status, created_at_utc, updated_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (pair["pair_uid"], pair["token_uid"], pair["chain"], pair["pair_address"], pair["dex_name"],
             token["token_address"], None, now, source, "PILOT_OR_VERIFIED", "QUALITY_GATE_PASS", now, now)
        )
        con.execute(
            """
            INSERT INTO liquidity_snapshots(snapshot_uid, token_uid, pair_uid, chain, pair_address,
            observed_at_utc, liquidity_usd, source, freshness_status, api_budget_checked, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (snap_uid, token["token_uid"], pair["pair_uid"], chain, pair_address, observed, 1234.5,
             source, "LOCAL_TEST", 0, now)
        )
        con.commit()
        checks.append({"name": "db_valid_insert_on_temp_copy", "ok": True})
    except Exception as e:
        errors.append(f"db_valid_insert_failed:{e}")
        checks.append({"name": "db_valid_insert_on_temp_copy", "ok": False, "error": str(e)})

    try:
        con.execute(
            """
            INSERT INTO liquidity_snapshots(snapshot_uid, token_uid, pair_uid, chain, pair_address,
            observed_at_utc, liquidity_usd, source, freshness_status, api_budget_checked, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("", token["token_uid"], pair["pair_uid"], chain, pair_address, observed, 1.0, source, "BAD", 0, now)
        )
        con.commit()
        errors.append("db_empty_snapshot_uid_not_rejected")
        checks.append({"name": "db_reject_empty_snapshot_uid_on_temp_copy", "ok": False})
    except Exception as e:
        checks.append({"name": "db_reject_empty_snapshot_uid_on_temp_copy", "ok": True, "error": str(e)})

    try:
        con.execute(
            """
            INSERT INTO market_snapshots(snapshot_uid, token_uid, pair_uid, chain, pair_address,
            observed_at_utc, price_usd, tx1h, source, freshness_status, api_budget_checked, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("snap_bad_fk", "tok_missing", pair["pair_uid"], chain, pair_address, observed, 1.0, 1, source, "BAD", 0, now)
        )
        con.commit()
        errors.append("db_missing_token_fk_not_rejected")
        checks.append({"name": "db_reject_missing_token_fk_on_temp_copy", "ok": False})
    except Exception as e:
        checks.append({"name": "db_reject_missing_token_fk_on_temp_copy", "ok": True, "error": str(e)})

    con.close()

    return {
        "final_status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "checks": checks,
        "temp_test_db": str(tempdb),
    }

if __name__ == "__main__":
    result = run()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["final_status"] != "PASS":
        raise SystemExit(1)
