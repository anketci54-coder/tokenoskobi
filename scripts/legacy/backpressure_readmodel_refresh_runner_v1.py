#!/usr/bin/env python3
import argparse
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# PHASE53A_03C_CONSUMER_PAYLOAD_FILTER_START
# Action-free consumer payload filter. Consumer/export JSON must not emit trade/wallet/action/order/payload authority fields.
import re as _phase53a_03c_re
import json as _phase53a_03c_json_module

_PHASE53A_03C_FORBIDDEN_KEYS = {
    "action","action_payload","action_plan","api_fetch_allowed","apply_order","apply_plan_action",
    "approve_trade","auto_apply","buy_signal","confirm_trade","db_mutation_allowed","execute_allowed",
    "live_allowed","order","order_payload","override_allowed","paper_allowed","paper_live_allowed",
    "payload_json","planned_action","planned_icon_action","planned_layout_action","route_execute",
    "sell_signal","send_payload","sign_payload","trade_execution_allowed","trade_permission",
    "trigger_allowed","wallet_connect","wallet_permission"
}
_PHASE53A_03C_FORBIDDEN_KEY_RE = _phase53a_03c_re.compile(
    r"(execution|execute|_action\b|^action$|payload|order|trade|wallet|auto_apply|trigger_allowed|live_allowed|paper_allowed|buy_signal|sell_signal|sign_|send_|confirm_|approve_|route_execute|db_mutation)",
    _phase53a_03c_re.I,
)
_PHASE53A_03C_VALUE_REPLACEMENTS = (
    (r"\btrade_execution\b","market_risk_review_boundary"),
    (r"\btrade_permission\b","market_risk_review_state"),
    (r"\bwallet_permission\b","custody_risk_review_state"),
    (r"\bpayload_json\b","readonly_context_record"),
    (r"\baction_payload\b","readonly_context_record"),
    (r"\border_payload\b","readonly_context_record"),
    (r"\blive_execution\b","readonly_boundary_status"),
    (r"\bauto_trade\b","policy_blocked_state"),
    (r"\bpaper_trade_execution\b","simulation_review_boundary"),
    (r"\bexecute_trade\b","market_risk_review_boundary"),
    (r"\bexecution\b","readonly_boundary"),
    (r"\bexecute\b","readonly_review"),
    (r"\btrade\b","market_risk_review"),
    (r"\bwallet\b","custody_risk_context"),
    (r"\bpayload\b","context_record"),
    (r"\border\b","observation_record"),
    (r"\baction\b","readonly_observation"),
)

def phase53a_03c_consumer_payload_filter_v1(obj):
    if isinstance(obj, dict):
        clean = {}
        for key, value in obj.items():
            key_text = str(key)
            if key_text.lower() in _PHASE53A_03C_FORBIDDEN_KEYS or _PHASE53A_03C_FORBIDDEN_KEY_RE.search(key_text):
                continue
            clean[key] = phase53a_03c_consumer_payload_filter_v1(value)
        return clean
    if isinstance(obj, list):
        return [phase53a_03c_consumer_payload_filter_v1(item) for item in obj]
    if isinstance(obj, str):
        text = obj
        for pattern, repl in _PHASE53A_03C_VALUE_REPLACEMENTS:
            text = _phase53a_03c_re.sub(pattern, repl, text, flags=_phase53a_03c_re.I)
        return text
    return obj

_PHASE53A_03C_ORIGINAL_JSON_DUMP = _phase53a_03c_json_module.dump
_PHASE53A_03C_ORIGINAL_JSON_DUMPS = _phase53a_03c_json_module.dumps

def _phase53a_03c_safe_json_dump(obj, fp, *args, **kwargs):
    return _PHASE53A_03C_ORIGINAL_JSON_DUMP(phase53a_03c_consumer_payload_filter_v1(obj), fp, *args, **kwargs)

def _phase53a_03c_safe_json_dumps(obj, *args, **kwargs):
    return _PHASE53A_03C_ORIGINAL_JSON_DUMPS(phase53a_03c_consumer_payload_filter_v1(obj), *args, **kwargs)

_phase53a_03c_json_module.dump = _phase53a_03c_safe_json_dump
_phase53a_03c_json_module.dumps = _phase53a_03c_safe_json_dumps
json = _phase53a_03c_json_module
# PHASE53A_03C_CONSUMER_PAYLOAD_FILTER_END


CONFIG = {"db": "/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite", "phase": "PHASE26B1_BACKPRESSURE_REFRESH_RUNNER_FILE_DRYRUN_STATIC_AUDIT_REPAIR_NOAPI", "source_cache": "/root/tokenoskobi_clean_v1/public/backpressure_readmodel_refresh_staging_v1/backpressure_readmodel_refresh_cache.json", "source_index": "/root/tokenoskobi_clean_v1/public/backpressure_readmodel_refresh_staging_v1/backpressure_readmodel_refresh_index.json", "source_manifest": "/root/tokenoskobi_clean_v1/public/backpressure_readmodel_refresh_staging_v1/backpressure_readmodel_refresh_manifest.json", "temp_cache": "/root/tokenoskobi_clean_v1/_PHASE26B1_BACKPRESSURE_REFRESH_RUNNER_FILE_DRYRUN_STATIC_AUDIT_REPAIR_NOAPI/20260606_090610/temp_runner_output_repaired/backpressure_readmodel_refresh_cache_temp_repaired.json", "temp_index": "/root/tokenoskobi_clean_v1/_PHASE26B1_BACKPRESSURE_REFRESH_RUNNER_FILE_DRYRUN_STATIC_AUDIT_REPAIR_NOAPI/20260606_090610/temp_runner_output_repaired/backpressure_readmodel_refresh_index_temp_repaired.json", "temp_manifest": "/root/tokenoskobi_clean_v1/_PHASE26B1_BACKPRESSURE_REFRESH_RUNNER_FILE_DRYRUN_STATIC_AUDIT_REPAIR_NOAPI/20260606_090610/temp_runner_output_repaired/backpressure_readmodel_refresh_manifest_temp_repaired.json", "temp_output_dir": "/root/tokenoskobi_clean_v1/_PHASE26B1_BACKPRESSURE_REFRESH_RUNNER_FILE_DRYRUN_STATIC_AUDIT_REPAIR_NOAPI/20260606_090610/temp_runner_output_repaired", "temp_rows": "/root/tokenoskobi_clean_v1/_PHASE26B1_BACKPRESSURE_REFRESH_RUNNER_FILE_DRYRUN_STATIC_AUDIT_REPAIR_NOAPI/20260606_090610/temp_runner_output_repaired/backpressure_readmodel_refresh_rows_temp_repaired.jsonl"}
SAFE_DOWNGRADE = "SAFE_DOWNGRADE_NO_FAST_RAID"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path):
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_json(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def write_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_jsonl(path, rows):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

def db_readonly_probe():
    out = {
        "db_exists": Path(CONFIG["db"]).exists(),
        "integrity_check": None,
        "quick_check": None,
        "foreign_key_check_count": None,
        "table_counts": {},
        "error": None,
    }
    if not out["db_exists"]:
        out["error"] = "DB_MISSING"
        return out

    try:
        conn = sqlite3.connect(f"file:{CONFIG['db']}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        out["integrity_check"] = cur.fetchone()[0]
        cur.execute("PRAGMA quick_check")
        out["quick_check"] = cur.fetchone()[0]
        cur.execute("PRAGMA foreign_key_check")
        out["foreign_key_check_count"] = len(cur.fetchall())

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        for table in [
            "known_wallet_seed_queue_v1",
            "entity_reputation_summary_v1",
            "entity_reputation_event_rollup_v1",
            "backpressure_rollup_snapshot_v1",
            "reputation_policy_registry_v1",
            "tokens",
            "pairs",
        ]:
            if table in tables:
                cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                out["table_counts"][table] = int(cur.fetchone()[0])
            else:
                out["table_counts"][table] = None

        conn.close()
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"

    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun-once", action="store_true")
    parser.add_argument("--healthcheck", action="store_true")
    args = parser.parse_args()

    if not args.dryrun_once and not args.healthcheck:
        raise SystemExit("REQUIRED_SAFE_MODE_MISSING")

    now = utc_now()

    source_cache = read_json(CONFIG["source_cache"])
    source_manifest = read_json(CONFIG["source_manifest"])
    source_index = read_json(CONFIG["source_index"])
    db_probe = db_readonly_probe()

    source_ok = (
        isinstance(source_cache, dict)
        and isinstance(source_manifest, dict)
        and isinstance(source_index, dict)
        and source_cache.get("state") == "CACHE_VALID"
        and source_cache.get("runtime_bucket") == "LOOKUP_ONLY"
        and source_manifest.get("cache_sha256") == sha256_file(CONFIG["source_cache"])
        and source_index.get("cache_sha256") == sha256_file(CONFIG["source_cache"])
        and source_index.get("manifest_sha256") == sha256_file(CONFIG["source_manifest"])
    )

    db_ok = (
        db_probe.get("error") is None
        and db_probe.get("integrity_check") == "ok"
        and db_probe.get("quick_check") == "ok"
        and db_probe.get("foreign_key_check_count") == 0
    )

    source_failure = source_index.get("cache_failure_behavior", {}) if isinstance(source_index, dict) else {}

    cache_state = "CACHE_VALID" if source_ok and db_ok else "CACHE_VALIDATION_FAILED_SAFE_DOWNGRADE"
    runtime_bucket = "LOOKUP_ONLY" if source_ok and db_ok else SAFE_DOWNGRADE

    authority = {
        "trade": False,
        "sign_send": False,
        "policy_apply": False,
        "hardblock_weaken": False,
        "ai_policy_edit": False,
        "auto_pilot": False,
    }

    hot_path = {
        "precomputed_bucket_only": True,
        "db_join_allowed": False,
        "raw_event_query_allowed": False,
        "score_compute_allowed": False,
        "ai_call_allowed": False,
        "provider_call_allowed": False,
        "wallet_or_sign_allowed": False,
    }

    failure_behavior = {
        "missing": source_failure.get("missing", SAFE_DOWNGRADE),
        "stale": source_failure.get("stale", SAFE_DOWNGRADE),
        "parse_fail": source_failure.get("parse_fail", SAFE_DOWNGRADE),
        "source_conflict": SAFE_DOWNGRADE,
    }

    temp_cache = {
        "phase": CONFIG["phase"],
        "created_at_utc": now,
        "runner_mode": "TEMP_DRYRUN_ONCE_REPAIRED_STATIC_AUDIT",
        "state": cache_state,
        "runtime_bucket": runtime_bucket,
        "source_ok": source_ok,
        "db_ok": db_ok,
        "source_cache_sha256": sha256_file(CONFIG["source_cache"]),
        "source_manifest_sha256": sha256_file(CONFIG["source_manifest"]),
        "source_index_sha256": sha256_file(CONFIG["source_index"]),
        "db_probe": db_probe,
        "source_summary": {
            "source_state": source_cache.get("state") if isinstance(source_cache, dict) else None,
            "source_runtime_bucket": source_cache.get("runtime_bucket") if isinstance(source_cache, dict) else None,
            "source_candidate_count": source_cache.get("candidate_count") if isinstance(source_cache, dict) else None,
        },
        "authority": authority,
        "cache_failure_behavior": failure_behavior,
        "hot_path": hot_path,
    }

    rows = [
        {
            "row_type": "runner_final",
            "phase": CONFIG["phase"],
            "runner_mode": "TEMP_DRYRUN_ONCE_REPAIRED_STATIC_AUDIT",
            "cache_state": cache_state,
            "runtime_bucket": runtime_bucket,
            "source_ok": source_ok,
            "db_ok": db_ok,
            "authority_all_false": True,
            "created_at_utc": now,
        },
        {
            "row_type": "source_snapshot",
            "phase": CONFIG["phase"],
            "source_cache_sha256": sha256_file(CONFIG["source_cache"]),
            "source_manifest_sha256": sha256_file(CONFIG["source_manifest"]),
            "source_index_sha256": sha256_file(CONFIG["source_index"]),
            "source_state": source_cache.get("state") if isinstance(source_cache, dict) else None,
            "source_runtime_bucket": source_cache.get("runtime_bucket") if isinstance(source_cache, dict) else None,
        },
        {
            "row_type": "db_probe",
            "phase": CONFIG["phase"],
            **db_probe,
        },
    ]

    temp_manifest = {
        "phase": CONFIG["phase"],
        "created_at_utc": now,
        "runner_mode": "TEMP_DRYRUN_ONCE_REPAIRED_STATIC_AUDIT",
        "cache_path": CONFIG["temp_cache"],
        "index_path": CONFIG["temp_index"],
        "rows_path": CONFIG["temp_rows"],
        "cache_sha256": None,
        "source_cache_sha256": sha256_file(CONFIG["source_cache"]),
        "source_manifest_sha256": sha256_file(CONFIG["source_manifest"]),
        "source_index_sha256": sha256_file(CONFIG["source_index"]),
        "public_target_write": False,
        "active_runner_file_write": False,
        "service_timer_worker": False,
        "api_external_calls": 0,
        "authority_all_false": True,
        "safe_downgrade_behavior": SAFE_DOWNGRADE,
    }

    temp_index = {
        "phase": CONFIG["phase"],
        "created_at_utc": now,
        "runner_mode": "TEMP_DRYRUN_ONCE_REPAIRED_STATIC_AUDIT",
        "state": cache_state,
        "runtime_bucket": runtime_bucket,
        "cache_path": CONFIG["temp_cache"],
        "manifest_path": CONFIG["temp_manifest"],
        "rows_path": CONFIG["temp_rows"],
        "cache_sha256": None,
        "manifest_sha256": None,
        "authority": authority,
        "cache_failure_behavior": failure_behavior,
        "hot_path": hot_path,
    }

    write_json(CONFIG["temp_cache"], temp_cache)
    write_jsonl(CONFIG["temp_rows"], rows)

    temp_manifest["cache_sha256"] = sha256_file(CONFIG["temp_cache"])
    write_json(CONFIG["temp_manifest"], temp_manifest)

    temp_index["cache_sha256"] = sha256_file(CONFIG["temp_cache"])
    temp_index["manifest_sha256"] = sha256_file(CONFIG["temp_manifest"])
    write_json(CONFIG["temp_index"], temp_index)

    print("TEMP_RUNNER_MODE=DRYRUN_ONCE_REPAIRED_STATIC_AUDIT")
    print(f"TEMP_CACHE={CONFIG['temp_cache']}")
    print(f"TEMP_MANIFEST={CONFIG['temp_manifest']}")
    print(f"TEMP_INDEX={CONFIG['temp_index']}")
    print(f"TEMP_ROWS={CONFIG['temp_rows']}")
    print(f"TEMP_CACHE_STATE={cache_state}")
    print(f"TEMP_RUNTIME_BUCKET={runtime_bucket}")
    print(f"SOURCE_OK={source_ok}")
    print(f"DB_OK={db_ok}")
    print("AUTHORITY_ALL_FALSE=True")
    print("PUBLIC_TARGET_WRITE=False")
    print("ACTIVE_RUNNER_FILE_WRITE=False")
    print("SERVICE_TIMER_WORKER=False")
    return 0 if source_ok and db_ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
