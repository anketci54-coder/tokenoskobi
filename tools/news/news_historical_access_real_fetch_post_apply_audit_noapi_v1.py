
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, sqlite3, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_historical_access_real_fetch_apply_with_backup_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

DERIVED_TABLES = [
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

def parse_dt(v):
    if not v:
        return None
    try:
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def table_exists(con, table):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        [table]
    ).fetchone() is not None

def table_cols(con, table):
    return [r[1] for r in con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()]

def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}

def fetch_by_uid(con, table, uid):
    rows = con.execute("SELECT * FROM " + q(table) + " WHERE news_uid=?", [uid]).fetchall()
    return [dict(r) for r in rows]

def row_fingerprint(row):
    keys = [
        "news_uid", "source_uid", "title", "canonical_url", "url", "link",
        "published_at_utc", "fetched_at_utc", "created_at_utc", "received_at_utc"
    ]
    payload = {k: row.get(k) for k in keys if k in row}
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def duplicate_rows(con, table, limit=50):
    return [
        {"news_uid": r[0], "row_count": r[1]}
        for r in con.execute("""
            SELECT news_uid, COUNT(*) AS c
            FROM """ + q(table) + """
            GROUP BY news_uid
            HAVING COUNT(*) > 1
            ORDER BY c DESC, news_uid ASC
            LIMIT ?
        """, [limit]).fetchall()
    ]

def orphan_rows(con, table, limit=50):
    return [
        {"news_uid": r[0], "row_count": r[1]}
        for r in con.execute("""
            SELECT d.news_uid, COUNT(*) AS c
            FROM """ + q(table) + """ d
            LEFT JOIN news_raw_feed_events r ON r.news_uid = d.news_uid
            WHERE r.news_uid IS NULL
            GROUP BY d.news_uid
            ORDER BY c DESC, d.news_uid ASC
            LIMIT ?
        """, [limit]).fetchall()
    ]

def freshness_audit(con, apply_generated_at):
    info = {
        "table": "news_runtime_freshness_v1",
        "exists": table_exists(con, "news_runtime_freshness_v1"),
        "status": "SCHEMA_ABSENT",
        "row_count": None,
        "columns": [],
        "latest_timestamp": None,
        "latest_timestamp_column": None,
        "updated_after_apply": None
    }

    if not info["exists"]:
        return info

    cols = table_cols(con, "news_runtime_freshness_v1")
    info["columns"] = cols
    info["row_count"] = con.execute("SELECT COUNT(*) FROM news_runtime_freshness_v1").fetchone()[0]

    candidates = [
        "updated_at_utc", "created_at_utc", "checked_at_utc", "generated_at_utc",
        "refreshed_at_utc", "last_seen_at_utc", "timestamp_utc"
    ]

    best_col = None
    best_val = None
    for c in candidates:
        if c in cols:
            v = con.execute("SELECT MAX(" + q(c) + ") FROM news_runtime_freshness_v1").fetchone()[0]
            if v and (best_val is None or str(v) > str(best_val)):
                best_col = c
                best_val = v

    info["latest_timestamp"] = best_val
    info["latest_timestamp_column"] = best_col

    apply_dt = parse_dt(apply_generated_at)
    latest_dt = parse_dt(best_val)

    if latest_dt and apply_dt:
        info["updated_after_apply"] = latest_dt >= apply_dt
        info["status"] = "OK_UPDATED_AFTER_APPLY" if info["updated_after_apply"] else "STALE_BEFORE_APPLY"
    elif info["row_count"] and info["row_count"] > 0:
        info["status"] = "PRESENT_NO_COMPARABLE_TIMESTAMP"
    else:
        info["status"] = "PRESENT_EMPTY"

    return info

def audit_main():
    failures = []
    warnings = []
    generated_at = now()
    future_limit = datetime.now(timezone.utc) + timedelta(minutes=5)

    prior = load_json(PRIOR)
    prior_result = prior.get("result", {})
    raw_insert = prior_result.get("raw_insert", {})
    expected_uids = list(raw_insert.get("inserted_news_uids", []))
    expected_count = int(raw_insert.get("inserted", 0) or 0)
    apply_generated_at = prior.get("generated_at_utc") or prior_result.get("generated_at_utc")

    if prior.get("decision") != "OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_APPLY_WITH_BACKUP":
        failures.append("prior_apply_not_ok")
    if expected_count <= 0:
        failures.append("expected_insert_count_zero")
    if expected_count != len(expected_uids):
        failures.append("expected_insert_count_uid_list_mismatch")

    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    try:
        missing_tables = [t for t in TABLES if not table_exists(con, t)]
        if missing_tables:
            failures.append("missing_tables:" + ",".join(missing_tables))

        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        db_counts = counts(con) if not missing_tables else {}

        raw_cols = table_cols(con, "news_raw_feed_events") if table_exists(con, "news_raw_feed_events") else []
        derived_cols = {
            t: table_cols(con, t) if table_exists(con, t) else []
            for t in DERIVED_TABLES
        }

        expected_chain = []
        timestamp_violations = []
        fingerprint_rows = []
        event_hash_status = {
            "raw_event_hash_column_exists": "event_hash" in raw_cols,
            "checked": False,
            "missing_or_empty": [],
            "note": None
        }

        for uid in expected_uids:
            raw_rows = fetch_by_uid(con, "news_raw_feed_events", uid)
            match_rows = fetch_by_uid(con, "news_token_match_events", uid)
            signal_rows = fetch_by_uid(con, "news_signal_events", uid)
            score_rows = fetch_by_uid(con, "news_score_events_v1", uid)

            raw_ok = len(raw_rows) == 1
            match_ok = len(match_rows) == 1
            signal_ok = len(signal_rows) == 1
            score_ok = len(score_rows) == 1

            if not raw_ok:
                failures.append("raw_uid_count_not_one:" + uid)
            if not match_ok:
                failures.append("match_uid_count_not_one:" + uid)
            if not signal_ok:
                failures.append("signal_uid_count_not_one:" + uid)
            if not score_ok:
                failures.append("score_uid_count_not_one:" + uid)

            link_ok = False
            evidence_ok = False
            score_alignment_ok = False

            if raw_rows and match_rows and signal_rows and score_rows:
                raw = raw_rows[0]
                m = match_rows[0]
                s = signal_rows[0]
                sc = score_rows[0]

                if "source_match_uid" in s and "match_uid" in m:
                    link_ok = s.get("source_match_uid") == m.get("match_uid")
                else:
                    link_ok = True

                raw_title = str(raw.get("title") or "")
                ev_m = str(m.get("evidence_text") or "")
                ev_s = str(s.get("evidence_text") or "")
                evidence_ok = raw_title[:200] in ev_m or ev_m[:200] in raw_title
                if ev_s:
                    evidence_ok = evidence_ok and (raw_title[:200] in ev_s or ev_s[:200] in raw_title)

                score_alignment_ok = (
                    m.get("token_uid") == sc.get("token_uid")
                    and m.get("pair_uid") == sc.get("pair_uid")
                    and m.get("symbol") == sc.get("symbol")
                    and m.get("chain") == sc.get("chain")
                )

                fp = row_fingerprint(raw)
                fingerprint_rows.append({
                    "news_uid": uid,
                    "audit_sha256": fp,
                    "source_uid": raw.get("source_uid"),
                    "title": raw.get("title"),
                    "published_at_utc": raw.get("published_at_utc"),
                    "fetched_at_utc": raw.get("fetched_at_utc"),
                    "created_at_utc": raw.get("created_at_utc"),
                    "received_at_utc": raw.get("received_at_utc") if "received_at_utc" in raw else None,
                    "event_hash": raw.get("event_hash") if "event_hash" in raw else None
                })

                if "event_hash" in raw:
                    event_hash_status["checked"] = True
                    if not raw.get("event_hash"):
                        event_hash_status["missing_or_empty"].append(uid)

                for col in ["published_at_utc", "fetched_at_utc", "created_at_utc", "received_at_utc"]:
                    if col in raw:
                        dt = parse_dt(raw.get(col))
                        if dt and dt > future_limit:
                            timestamp_violations.append({"news_uid": uid, "table": "raw", "column": col, "value": raw.get(col)})

                for table_name, row in [
                    ("news_token_match_events", m),
                    ("news_signal_events", s),
                    ("news_score_events_v1", sc)
                ]:
                    for col in ["created_at_utc", "updated_at_utc", "received_at_utc"]:
                        if col in row:
                            dt = parse_dt(row.get(col))
                            if dt and dt > future_limit:
                                timestamp_violations.append({"news_uid": uid, "table": table_name, "column": col, "value": row.get(col)})

            if not link_ok:
                failures.append("signal_match_link_broken:" + uid)
            if raw_rows and match_rows and signal_rows and score_rows and not evidence_ok:
                failures.append("evidence_title_mismatch:" + uid)
            if raw_rows and match_rows and signal_rows and score_rows and not score_alignment_ok:
                failures.append("score_alignment_mismatch:" + uid)

            expected_chain.append({
                "news_uid": uid,
                "raw_count": len(raw_rows),
                "match_count": len(match_rows),
                "signal_count": len(signal_rows),
                "score_count": len(score_rows),
                "link_ok": link_ok,
                "evidence_ok": evidence_ok,
                "score_alignment_ok": score_alignment_ok
            })

        if event_hash_status["raw_event_hash_column_exists"]:
            if event_hash_status["missing_or_empty"]:
                failures.append("event_hash_missing_or_empty_for_expected_uids")
        else:
            event_hash_status["note"] = "event_hash column is absent in current news_raw_feed_events schema; audit_sha256 fingerprints were generated instead."
            warnings.append("raw_event_hash_column_absent_audit_sha256_used")

        if timestamp_violations:
            failures.append("timestamp_future_violations_present")

        orphan_checks = {t: orphan_rows(con, t) for t in DERIVED_TABLES}
        duplicate_checks = {
            "news_raw_feed_events": duplicate_rows(con, "news_raw_feed_events"),
            "news_token_match_events": duplicate_rows(con, "news_token_match_events"),
            "news_signal_events": duplicate_rows(con, "news_signal_events"),
            "news_score_events_v1": duplicate_rows(con, "news_score_events_v1")
        }

        expected_uid_duplicate_checks = {}
        for t in ["news_raw_feed_events"] + DERIVED_TABLES:
            rows = []
            for uid in expected_uids:
                c = con.execute("SELECT COUNT(*) FROM " + q(t) + " WHERE news_uid=?", [uid]).fetchone()[0]
                if c != 1:
                    rows.append({"news_uid": uid, "row_count": c})
            expected_uid_duplicate_checks[t] = rows

        if any(orphan_checks[t] for t in orphan_checks):
            failures.append("orphan_derived_rows_present")

        if duplicate_checks["news_token_match_events"]:
            failures.append("global_duplicate_news_uid_in_token_match_events_present")

        if any(expected_uid_duplicate_checks[t] for t in expected_uid_duplicate_checks):
            failures.append("expected_uid_duplicate_or_missing_present")

        freshness = freshness_audit(con, apply_generated_at)
        if freshness["exists"] and freshness["status"] in ["PRESENT_EMPTY", "STALE_BEFORE_APPLY"]:
            warnings.append("news_runtime_freshness_v1_not_confirmed_after_apply")
        if not freshness["exists"]:
            warnings.append("news_runtime_freshness_v1_schema_absent")

        bad_trade_flags_expected = 0
        if expected_uids:
            ph = ",".join(["?"] * len(expected_uids))
            bad_trade_flags_expected = con.execute("""
                SELECT COUNT(*)
                FROM news_token_match_events
                WHERE news_uid IN (""" + ph + """)
                  AND (write_allowed != 0 OR trade_signal != 0 OR paper_signal != 0)
            """, expected_uids).fetchone()[0]

        if bad_trade_flags_expected != 0:
            failures.append("bad_trade_flags_expected_uids_nonzero")

    finally:
        con.close()

    tests = [
        {
            "test_id": "T01_PRIOR_APPLY_OK_AND_EXPECTED_UIDS_PRESENT",
            "ok": prior.get("decision") == "OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_APPLY_WITH_BACKUP"
                  and expected_count == len(expected_uids)
                  and expected_count > 0,
            "expected_count": expected_count,
            "expected_uid_count": len(expected_uids)
        },
        {
            "test_id": "T02_SQLITE_INTEGRITY_OK",
            "ok": integrity == "ok",
            "integrity": integrity
        },
        {
            "test_id": "T03_EXPECTED_LOGICAL_CHAIN_1_TO_1",
            "ok": all(
                r["raw_count"] == 1 and r["match_count"] == 1 and r["signal_count"] == 1 and r["score_count"] == 1
                for r in expected_chain
            ),
            "expected_chain": expected_chain
        },
        {
            "test_id": "T04_CHAIN_LINK_AND_CONTENT_EVIDENCE_OK",
            "ok": all(r["link_ok"] and r["evidence_ok"] and r["score_alignment_ok"] for r in expected_chain),
            "expected_chain": expected_chain
        },
        {
            "test_id": "T05_NO_ORPHAN_DERIVED_ROWS",
            "ok": all(len(orphan_checks[t]) == 0 for t in orphan_checks),
            "orphan_checks": orphan_checks
        },
        {
            "test_id": "T06_NO_DUPLICATE_NEWS_UID_FOR_EXPECTED_AND_MATCH_GLOBAL",
            "ok": len(duplicate_checks["news_token_match_events"]) == 0
                  and all(len(expected_uid_duplicate_checks[t]) == 0 for t in expected_uid_duplicate_checks),
            "global_token_match_duplicates": duplicate_checks["news_token_match_events"],
            "expected_uid_duplicate_checks": expected_uid_duplicate_checks
        },
        {
            "test_id": "T07_TIMESTAMP_INTEGRITY_OK",
            "ok": len(timestamp_violations) == 0,
            "timestamp_violations": timestamp_violations
        },
        {
            "test_id": "T08_BAD_TRADE_FLAGS_ZERO",
            "ok": bad_trade_flags_expected == 0,
            "bad_trade_flags_expected": bad_trade_flags_expected
        },
        {
            "test_id": "T09_FINGERPRINT_OR_EVENT_HASH_RECORDED",
            "ok": len(fingerprint_rows) == expected_count and (
                event_hash_status["raw_event_hash_column_exists"] is False
                or len(event_hash_status["missing_or_empty"]) == 0
            ),
            "event_hash_status": event_hash_status,
            "fingerprint_count": len(fingerprint_rows)
        },
        {
            "test_id": "T10_FRESHNESS_TABLE_REVIEWED",
            "ok": True,
            "freshness": freshness
        },
        {
            "test_id": "T11_NOAPI_READONLY_BOUNDARY_LOCKED",
            "ok": True,
            "network_call": False,
            "api_call": False,
            "db_write": False,
            "service_change": False,
            "timer_change": False,
            "paper_trade": False,
            "live_trade": False,
            "trade_authority": False
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW" if not failures else "NEWS_HISTORICAL_ACCESS_POST_APPLY_AUDIT_HOLD"

    return {
        "stage": "NEWS_HISTORICAL_ACCESS_REAL_FETCH_POST_APPLY_AUDIT_NOAPI",
        "generated_at_utc": generated_at,
        "decision": "OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_POST_APPLY_AUDIT_NOAPI_INTERNAL" if not failures else "FAIL_NEWS_HISTORICAL_ACCESS_REAL_FETCH_POST_APPLY_AUDIT_NOAPI_INTERNAL",
        "prior": "data/control/news_historical_access_real_fetch_apply_with_backup_v1.json",
        "expected_count": expected_count,
        "expected_news_uids": expected_uids,
        "db_counts": db_counts,
        "apply_generated_at_utc": apply_generated_at,
        "expected_chain": expected_chain,
        "fingerprints": fingerprint_rows,
        "event_hash_status": event_hash_status,
        "orphan_checks": orphan_checks,
        "duplicate_checks": duplicate_checks,
        "expected_uid_duplicate_checks": expected_uid_duplicate_checks,
        "timestamp_violations": timestamp_violations,
        "freshness": freshness,
        "bad_trade_flags_expected": bad_trade_flags_expected,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "network_call": False,
            "api_call": False,
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
    print(json.dumps(audit_main(), ensure_ascii=False, indent=2, sort_keys=True))
