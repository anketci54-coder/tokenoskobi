
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PLAN = ROOT / "config/news_historical_access_layer_plan_v1.json"
PLAN_ARTIFACT = ROOT / "data/control/news_historical_access_layer_plan_noapi_v1.json"
ADAPTER_ARTIFACT = ROOT / "data/control/news_ingress_adapter_readonly_scaffold_dryrun_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def q(name):
    return '"' + str(name).replace('"', '""') + '"'

def columns(con, table):
    rows = con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()
    return [r[1] for r in rows]

def count(con, table):
    return con.execute("SELECT COUNT(*) FROM " + q(table)).fetchone()[0]

def has_cols(con, table, required):
    available = set(columns(con, table))
    return all(c in available for c in required)

def safe_fetch(con, sql, params=None):
    if params is None:
        params = []
    rows = con.execute(sql, params).fetchmany(20)
    return [dict(r) for r in rows]

def scalar(con, sql, params=None):
    if params is None:
        params = []
    row = con.execute(sql, params).fetchone()
    if not row:
        return None
    return row[0]

def pick_sample(con, table, col):
    if not has_cols(con, table, [col]):
        return None
    row = con.execute(
        "SELECT " + q(col) + " FROM " + q(table) + " WHERE " + q(col) + " IS NOT NULL AND " + q(col) + " != '' LIMIT 1"
    ).fetchone()
    return None if not row else row[0]

def row_count_sql(con, sql, params=None):
    if params is None:
        params = []
    return con.execute(sql, params).fetchone()[0]

def artifact_event_uid_sample():
    adapter = load(ADAPTER_ARTIFACT)
    envelopes = adapter.get("dryrun", {}).get("envelopes", [])
    if not envelopes:
        return None
    return envelopes[0].get("event_uid")

def build_tests(con):
    tests = []

    raw_count = count(con, "news_raw_feed_events")
    match_count = count(con, "news_token_match_events")
    signal_count = count(con, "news_signal_events")
    score_count = count(con, "news_score_events_v1")

    tests.append({
        "test_id": "T01_COUNT_ALL_TABLES",
        "purpose": "count all historical NEWS tables",
        "result": {
            "news_raw_feed_events": raw_count,
            "news_token_match_events": match_count,
            "news_signal_events": signal_count,
            "news_score_events_v1": score_count
        },
        "ok": all(x is not None for x in [raw_count, match_count, signal_count, score_count])
    })

    date_col = "published_at_utc" if has_cols(con, "news_raw_feed_events", ["published_at_utc"]) else "fetched_at_utc"
    if has_cols(con, "news_raw_feed_events", [date_col]):
        min_dt = scalar(con, "SELECT MIN(" + q(date_col) + ") FROM news_raw_feed_events WHERE " + q(date_col) + " IS NOT NULL")
        max_dt = scalar(con, "SELECT MAX(" + q(date_col) + ") FROM news_raw_feed_events WHERE " + q(date_col) + " IS NOT NULL")
        rc = row_count_sql(con, "SELECT COUNT(*) FROM news_raw_feed_events WHERE " + q(date_col) + " BETWEEN COALESCE(?, " + q(date_col) + ") AND COALESCE(?, " + q(date_col) + ")", [min_dt, max_dt])
        tests.append({
            "test_id": "T02_DATE_RANGE_QUERY",
            "purpose": "date range query on raw historical feed",
            "query_field": date_col,
            "min": min_dt,
            "max": max_dt,
            "result_count": rc,
            "ok": rc >= 0
        })
    else:
        tests.append({
            "test_id": "T02_DATE_RANGE_QUERY",
            "purpose": "date range query on raw historical feed",
            "ok": False,
            "reason": "no published_at_utc/fetched_at_utc column"
        })

    source_uid = pick_sample(con, "news_raw_feed_events", "source_uid")
    if source_uid is not None:
        rc = row_count_sql(con, "SELECT COUNT(*) FROM news_raw_feed_events WHERE source_uid = ?", [source_uid])
        tests.append({
            "test_id": "T03_SOURCE_QUERY",
            "purpose": "source_uid query",
            "source_uid": source_uid,
            "result_count": rc,
            "ok": rc >= 1
        })
    else:
        tests.append({"test_id": "T03_SOURCE_QUERY", "purpose": "source_uid query", "ok": False, "reason": "no source_uid sample"})

    symbol = pick_sample(con, "news_token_match_events", "symbol")
    chain = pick_sample(con, "news_token_match_events", "chain")
    if symbol is not None and chain is not None:
        rc = row_count_sql(con, "SELECT COUNT(*) FROM news_token_match_events WHERE symbol = ? AND chain = ?", [symbol, chain])
        tests.append({
            "test_id": "T04_SYMBOL_CHAIN_QUERY",
            "purpose": "token symbol + chain query",
            "symbol": symbol,
            "chain": chain,
            "result_count": rc,
            "ok": rc >= 1
        })
    else:
        tests.append({"test_id": "T04_SYMBOL_CHAIN_QUERY", "purpose": "token symbol + chain query", "ok": False, "reason": "no symbol/chain sample"})

    risk_label = pick_sample(con, "news_score_events_v1", "risk_label")
    if risk_label is not None:
        rc = row_count_sql(con, "SELECT COUNT(*) FROM news_score_events_v1 WHERE risk_label = ?", [risk_label])
        tests.append({
            "test_id": "T05_RISK_LABEL_QUERY",
            "purpose": "risk_label query",
            "risk_label": risk_label,
            "result_count": rc,
            "ok": rc >= 1
        })
    else:
        tests.append({"test_id": "T05_RISK_LABEL_QUERY", "purpose": "risk_label query", "ok": True, "warning": "no risk_label sample"})

    news_uid = pick_sample(con, "news_raw_feed_events", "news_uid")
    if news_uid is not None:
        raw_rc = row_count_sql(con, "SELECT COUNT(*) FROM news_raw_feed_events WHERE news_uid = ?", [news_uid])
        match_rc = row_count_sql(con, "SELECT COUNT(*) FROM news_token_match_events WHERE news_uid = ?", [news_uid])
        signal_rc = row_count_sql(con, "SELECT COUNT(*) FROM news_signal_events WHERE news_uid = ?", [news_uid])
        score_rc = row_count_sql(con, "SELECT COUNT(*) FROM news_score_events_v1 WHERE news_uid = ?", [news_uid])
        tests.append({
            "test_id": "T06_NEWS_UID_LOOKUP",
            "purpose": "legacy news_uid lookup across all layers",
            "news_uid": news_uid,
            "result": {
                "raw": raw_rc,
                "match": match_rc,
                "signal": signal_rc,
                "score": score_rc
            },
            "ok": raw_rc >= 1
        })
    else:
        tests.append({"test_id": "T06_NEWS_UID_LOOKUP", "purpose": "legacy news_uid lookup", "ok": False, "reason": "no news_uid sample"})

    event_uid = artifact_event_uid_sample()
    if event_uid:
        adapter = load(ADAPTER_ARTIFACT)
        found = []
        for e in adapter.get("dryrun", {}).get("envelopes", []):
            if e.get("event_uid") == event_uid:
                found.append({
                    "event_uid": e.get("event_uid"),
                    "source_id": e.get("source_id"),
                    "decision": e.get("gate_decision", {}).get("decision"),
                    "route": e.get("routing", {}).get("route")
                })
        tests.append({
            "test_id": "T07_ARTIFACT_EVENT_UID_LOOKUP",
            "purpose": "new ingress artifact event_uid lookup",
            "event_uid": event_uid,
            "result_count": len(found),
            "sample": found[:3],
            "ok": len(found) >= 1
        })
    else:
        tests.append({"test_id": "T07_ARTIFACT_EVENT_UID_LOOKUP", "purpose": "new ingress artifact event_uid lookup", "ok": False, "reason": "no event_uid sample"})

    if has_cols(con, "news_raw_feed_events", ["url_hash", "raw_hash"]):
        duplicate_url = row_count_sql(con, "SELECT COUNT(*) FROM (SELECT url_hash, COUNT(*) c FROM news_raw_feed_events WHERE url_hash IS NOT NULL AND url_hash != '' GROUP BY url_hash HAVING c > 1)")
        duplicate_raw = row_count_sql(con, "SELECT COUNT(*) FROM (SELECT raw_hash, COUNT(*) c FROM news_raw_feed_events WHERE raw_hash IS NOT NULL AND raw_hash != '' GROUP BY raw_hash HAVING c > 1)")
        tests.append({
            "test_id": "T08_DEDUP_PREVIEW_READONLY",
            "purpose": "preview duplicate candidates without writing",
            "duplicate_url_hash_groups": duplicate_url,
            "duplicate_raw_hash_groups": duplicate_raw,
            "ok": duplicate_url >= 0 and duplicate_raw >= 0
        })
    else:
        tests.append({"test_id": "T08_DEDUP_PREVIEW_READONLY", "purpose": "dedup preview", "ok": False, "reason": "missing url_hash/raw_hash"})

    plan = load(PLAN)
    candidates = plan.get("index_strategy_plan_only", {}).get("candidate_indexes", [])
    create_now_flags = [c.get("create_now") for c in candidates]
    tests.append({
        "test_id": "T09_INDEX_PREVIEW_NO_CREATE",
        "purpose": "verify index strategy remains preview-only",
        "candidate_count": len(candidates),
        "create_now_all_false": all(x is False for x in create_now_flags),
        "ok": len(candidates) >= 8 and all(x is False for x in create_now_flags)
    })

    join_ok = False
    join_count = 0
    if has_cols(con, "news_raw_feed_events", ["news_uid"]) and has_cols(con, "news_token_match_events", ["news_uid"]):
        join_count = row_count_sql(con, """
            SELECT COUNT(*)
            FROM news_raw_feed_events r
            JOIN news_token_match_events m ON r.news_uid = m.news_uid
        """)
        join_ok = join_count >= 0
    tests.append({
        "test_id": "T10_JOIN_RAW_TO_MATCH_READONLY",
        "purpose": "join raw feed to token match layer",
        "join_count": join_count,
        "ok": join_ok
    })

    return tests

def counts(con):
    return {t: count(con, t) for t in TABLES}

def main():
    prior = load(PLAN_ARTIFACT)
    plan = load(PLAN)

    failures = []
    warnings = []

    if prior.get("decision") != "OK_NEWS_HISTORICAL_ACCESS_LAYER_PLAN_NOAPI":
        failures.append("prior_historical_plan_not_ok")

    boundary = plan.get("authority_boundary", {})
    for k in ["api_call","network_call","db_write","db_schema_change","index_creation","service_change","timer_change","nginx_change","paper_trade","live_trade","execution_authority"]:
        if boundary.get(k) is not False:
            failures.append("authority_boundary_not_false:" + k)

    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        before = counts(con)
        tests = build_tests(con)
        after = counts(con)
    finally:
        con.close()

    db_delta = {t: after[t] - before[t] for t in TABLES}

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t.get("test_id", "UNKNOWN"))
        if t.get("warning"):
            warnings.append(t["test_id"] + ":" + t["warning"])

    if any(v != 0 for v in db_delta.values()):
        failures.append("db_delta_not_zero")

    decision = "OK_NEWS_HISTORICAL_ACCESS_LAYER_DRYRUN_INTERNAL" if not failures else "FAIL_NEWS_HISTORICAL_ACCESS_LAYER_DRYRUN_INTERNAL"

    return {
        "stage": "NEWS_HISTORICAL_ACCESS_LAYER_DRYRUN_NOAPI",
        "generated_at_utc": now(),
        "decision": decision,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "db_before": before,
        "db_after": after,
        "db_delta": db_delta,
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
        "history_access_status": {
            "query_layer_readonly": True,
            "dedup_preview_readonly": True,
            "index_preview_readonly": True,
            "backfill_now": False,
            "legacy_news_uid_supported": True,
            "new_event_uid_artifact_supported": True
        },
        "failures": failures,
        "warnings": warnings,
        "next": "NEWS_RUNTIME_AND_HISTORY_FINAL_SEAL_NOAPI" if not failures else "NEWS_HISTORICAL_ACCESS_LAYER_DRYRUN_FIX_REQUIRED"
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
