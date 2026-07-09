
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, re

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
RUNTIME = ROOT / "PROJECT_RUNTIME.json"
PRIOR = ROOT / "data/control/news_derived_layer_refresher_runtime_binding_post_apply_audit_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

def now():
    return datetime.now(timezone.utc).isoformat()

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def db_snapshot():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        counts = {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]

        latest_raw = con.execute("""
            SELECT MAX(COALESCE(published_at_utc, fetched_at_utc))
            FROM news_raw_feed_events
            WHERE COALESCE(published_at_utc, fetched_at_utc) IS NOT NULL
        """).fetchone()[0]

        earliest_raw = con.execute("""
            SELECT MIN(COALESCE(published_at_utc, fetched_at_utc))
            FROM news_raw_feed_events
            WHERE COALESCE(published_at_utc, fetched_at_utc) IS NOT NULL
        """).fetchone()[0]

        source_counts = [
            dict(r) for r in con.execute("""
                SELECT source_uid, COUNT(*) AS row_count,
                       MIN(COALESCE(published_at_utc, fetched_at_utc)) AS earliest_seen,
                       MAX(COALESCE(published_at_utc, fetched_at_utc)) AS latest_seen
                FROM news_raw_feed_events
                GROUP BY source_uid
                ORDER BY row_count DESC, source_uid ASC
                LIMIT 20
            """).fetchall()
        ]

        latest_by_table = {}
        for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
            latest_by_table[t] = con.execute(
                "SELECT MAX(created_at_utc) FROM " + q(t) + " WHERE created_at_utc IS NOT NULL"
            ).fetchone()[0]

        derived_balanced = counts["news_token_match_events"] == counts["news_signal_events"] == counts["news_score_events_v1"]

        return {
            "counts": counts,
            "integrity": integrity,
            "earliest_raw": earliest_raw,
            "latest_raw": latest_raw,
            "latest_by_table": latest_by_table,
            "derived_balanced": derived_balanced,
            "source_counts": source_counts
        }
    finally:
        con.close()

def discover_sources():
    files = []
    for base in ["config", "tools"]:
        p = ROOT / base
        if p.exists():
            files.extend([x for x in p.rglob("*") if x.is_file() and x.suffix in [".json", ".py", ".md", ".txt"]])

    url_re = re.compile(r"https?://[^\s\"'<>]+")
    found_urls = []
    source_refs = []
    for p in files:
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        urls = sorted(set(url_re.findall(txt)))
        if urls:
            found_urls.append({
                "path": str(p.relative_to(ROOT)),
                "urls": urls[:25],
                "url_count": len(urls)
            })

        for m in re.finditer(r"src_[A-Za-z0-9_\-]+", txt):
            source_refs.append({
                "path": str(p.relative_to(ROOT)),
                "source_uid": m.group(0)
            })

    uniq_sources = {}
    for r in source_refs:
        uniq_sources.setdefault(r["source_uid"], set()).add(r["path"])

    return {
        "url_sources": found_urls[:50],
        "url_source_file_count": len(found_urls),
        "source_uids": [
            {"source_uid": k, "paths": sorted(v)[:10]}
            for k, v in sorted(uniq_sources.items())
        ],
        "source_uid_count": len(uniq_sources)
    }

def main():
    prior = load_json(PRIOR)
    runtime = load_json(RUNTIME)

    failures = []
    warnings = []

    before = db_snapshot()
    sources = discover_sources()
    after = db_snapshot()

    db_delta = {
        k: after["counts"][k] - before["counts"][k]
        for k in before["counts"]
    }

    current_state = runtime.get("current_state", {})
    next_safe = current_state.get("next_safe_step", {})

    if prior.get("decision") != "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI":
        failures.append("prior_runtime_binding_post_apply_audit_not_ok")

    if prior.get("audit", {}).get("runtime_effect_observed") is not True:
        failures.append("runtime_effect_not_observed_in_prior")

    if before.get("integrity") != "ok":
        failures.append("sqlite_integrity_not_ok")

    if before.get("derived_balanced") is not True:
        failures.append("derived_layers_not_balanced")

    if before["counts"].get("news_raw_feed_events", 0) <= 0:
        failures.append("raw_feed_empty")

    if sources.get("source_uid_count", 0) <= 0:
        warnings.append("no_source_uid_discovered_from_repo_scan")

    if sources.get("url_source_file_count", 0) <= 0:
        warnings.append("no_url_discovered_from_repo_scan_real_fetch_may_need_source_registry_review")

    if any(v != 0 for v in db_delta.values()):
        warnings.append("db_changed_during_readonly_plan_external_timer_possible")

    planned_fetch = {
        "plan_version": "NEWS_HISTORICAL_ACCESS_REAL_FETCH_PLAN_V1",
        "generated_at_utc": now(),
        "purpose": "Prepare historical NEWS fetch using existing source registry/runtime knowledge without performing network or DB writes in this step.",
        "scope_this_step": {
            "plan_only": True,
            "network_call_now": False,
            "api_call_now": False,
            "db_write_now": False,
            "schema_change_now": False,
            "service_change_now": False,
            "timer_change_now": False,
            "trade_authority_now": False
        },
        "required_previous_state": {
            "runtime_binding_post_apply_audit": "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI",
            "derived_runtime_binding_effect_observed": True,
            "tail_candidates": 0
        },
        "fetch_strategy_next_step": {
            "next_step": "NEWS_HISTORICAL_ACCESS_REAL_FETCH_TEMPDB_DRYRUN_WITH_NETWORK",
            "mode": "TEMPDB_ONLY_FIRST",
            "network_allowed_next_step": "REQUIRES_COMMANDER_APPROVAL",
            "real_db_write_next_step": False,
            "source_priority": [
                "existing_repo_source_registry_urls",
                "existing_raw_feed_source_uids",
                "current_news_radar_runner_source_config",
                "manual_source_registry_repair_if_no_url_available"
            ],
            "fetch_limits_first_dryrun": {
                "max_sources": 3,
                "max_items_per_source": 200,
                "max_total_items": 500,
                "request_timeout_seconds": 20,
                "retry_count": 1,
                "user_agent": "TokenoskobiHistoricalNewsDryrun/1.0",
                "historical_window_policy": "backfill older than current earliest_raw where source supports it; otherwise collect available feed history"
            },
            "dedup_policy": {
                "primary": "news_uid deterministic from source_uid + canonical_url_or_title + published_at",
                "secondary": "title + published_at_utc + source_uid",
                "do_not_duplicate_existing_raw": True,
                "do_not_duplicate_existing_derived": True
            },
            "tempdb_pipeline_required": [
                "copy real sqlite to tempdb",
                "fetch historical raw candidates into tempdb only",
                "run derived refresher helper on tempdb only",
                "verify raw/derived balance",
                "verify no trade flags",
                "verify real DB delta zero",
                "write artifact",
                "then ask for real DB apply approval if tempdb clean"
            ]
        },
        "current_db_snapshot": before,
        "source_discovery": sources
    }

    tests = [
        {
            "test_id": "T01_PRIOR_RUNTIME_BINDING_POST_APPLY_AUDIT_OK",
            "ok": prior.get("decision") == "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI"
                  and prior.get("audit", {}).get("runtime_effect_observed") is True
        },
        {
            "test_id": "T02_DB_HEALTH_OK",
            "ok": before.get("integrity") == "ok"
                  and before.get("derived_balanced") is True
                  and before["counts"].get("news_raw_feed_events", 0) > 0,
            "snapshot": before
        },
        {
            "test_id": "T03_SOURCE_DISCOVERY_DONE",
            "ok": sources.get("source_uid_count", 0) > 0 or sources.get("url_source_file_count", 0) > 0,
            "source_uid_count": sources.get("source_uid_count"),
            "url_source_file_count": sources.get("url_source_file_count")
        },
        {
            "test_id": "T04_PLAN_AUTHORITY_LOCKED_NOAPI",
            "ok": planned_fetch["scope_this_step"]["network_call_now"] is False
                  and planned_fetch["scope_this_step"]["api_call_now"] is False
                  and planned_fetch["scope_this_step"]["db_write_now"] is False
                  and planned_fetch["scope_this_step"]["service_change_now"] is False
                  and planned_fetch["scope_this_step"]["trade_authority_now"] is False
        },
        {
            "test_id": "T05_REAL_DB_UNTOUCHED_BY_PLAN",
            "ok": all(v == 0 for v in db_delta.values()),
            "db_delta": db_delta
        },
        {
            "test_id": "T06_NEXT_STEP_DEFINED",
            "ok": planned_fetch["fetch_strategy_next_step"]["next_step"] == "NEWS_HISTORICAL_ACCESS_REAL_FETCH_TEMPDB_DRYRUN_WITH_NETWORK"
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_HISTORICAL_ACCESS_REAL_FETCH_TEMPDB_DRYRUN_WITH_NETWORK" if not failures else "NEWS_HISTORICAL_ACCESS_REAL_FETCH_PLAN_REPAIR_REQUIRED"

    return {
        "stage": "NEWS_HISTORICAL_ACCESS_REAL_FETCH_PLAN_NOAPI",
        "generated_at_utc": now(),
        "decision": "OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_PLAN_NOAPI_INTERNAL" if not failures else "FAIL_NEWS_HISTORICAL_ACCESS_REAL_FETCH_PLAN_NOAPI_INTERNAL",
        "planned_fetch": planned_fetch,
        "db_before": before,
        "db_after": after,
        "db_delta": db_delta,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "api_call": False,
            "network_call": False,
            "db_write": False,
            "db_schema_change": False,
            "index_creation": False,
            "service_change": False,
            "timer_change": False,
            "nginx_change": False,
            "paper_trade": False,
            "live_trade": False,
            "execution_authority": False
        },
        "failures": failures,
        "warnings": warnings,
        "next": next_step
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
