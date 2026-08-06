
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, shutil

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_historical_access_real_fetch_post_apply_audit_noapi_v1.json"

NEWS_TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

FRESH_TABLE = "news_runtime_freshness_v1"
TARGET_UID = "news_runtime_freshness_historical_access_v1"
TARGET_COMPONENT = "NEWS_HISTORICAL_ACCESS_LAYER"

def now():
    return datetime.now(timezone.utc).isoformat()

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def table_exists(con, table):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        [table]
    ).fetchone() is not None

def table_cols(con, table):
    return [r[1] for r in con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()]

def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in NEWS_TABLES}

def row_count(con, table):
    if not table_exists(con, table):
        return None
    return con.execute("SELECT COUNT(*) FROM " + q(table)).fetchone()[0]

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

def max_iso(values):
    best = None
    for v in values:
        dt = parse_dt(v)
        if dt and (best is None or dt > best):
            best = dt
    return best.isoformat() if best else None

def freshness_snapshot(con):
    if not table_exists(con, FRESH_TABLE):
        return {
            "exists": False,
            "row_count": None,
            "columns": [],
            "target_rows": [],
            "latest_created_at_utc": None,
            "latest_last_observed_at_utc": None
        }
    cols = table_cols(con, FRESH_TABLE)
    target_rows = []
    where = []
    params = []
    if "freshness_uid" in cols:
        where.append("freshness_uid=?")
        params.append(TARGET_UID)
    if "component" in cols:
        where.append("component=?")
        params.append(TARGET_COMPONENT)
    if where:
        sql = "SELECT * FROM " + q(FRESH_TABLE) + " WHERE " + " OR ".join(where)
        target_rows = [dict(r) for r in con.execute(sql, params).fetchall()]
    return {
        "exists": True,
        "row_count": row_count(con, FRESH_TABLE),
        "columns": cols,
        "target_rows": target_rows,
        "latest_created_at_utc": con.execute("SELECT MAX(created_at_utc) FROM " + q(FRESH_TABLE)).fetchone()[0] if "created_at_utc" in cols else None,
        "latest_last_observed_at_utc": con.execute("SELECT MAX(last_observed_at_utc) FROM " + q(FRESH_TABLE)).fetchone()[0] if "last_observed_at_utc" in cols else None
    }

def choose_checkpoint(con, expected_uids):
    raw_cols = table_cols(con, "news_raw_feed_events")
    values = []
    rows = []
    preferred = []
    if "received_at_utc" in raw_cols:
        preferred.append("received_at_utc")
    if "fetched_at_utc" in raw_cols:
        preferred.append("fetched_at_utc")
    if "published_at_utc" in raw_cols:
        preferred.append("published_at_utc")
    if "created_at_utc" in raw_cols:
        preferred.append("created_at_utc")

    for uid in expected_uids:
        r = con.execute("SELECT * FROM news_raw_feed_events WHERE news_uid=?", [uid]).fetchone()
        if not r:
            continue
        d = dict(r)
        row_values = {c: d.get(c) for c in preferred}
        rows.append({"news_uid": uid, "timestamps": row_values})
        for c in preferred:
            if d.get(c):
                values.append(d.get(c))

    return {
        "checkpoint_utc": max_iso(values),
        "preferred_columns": preferred,
        "received_at_column_exists": "received_at_utc" in raw_cols,
        "rows": rows,
        "warning": None if "received_at_utc" in raw_cols else "received_at_utc_absent_used_fetched_or_published_checkpoint"
    }

def upsert_freshness(con, cols, counts_now, checkpoint_utc, generated_at):
    row = {}
    if "freshness_uid" in cols:
        row["freshness_uid"] = TARGET_UID
    if "component" in cols:
        row["component"] = TARGET_COMPONENT
    if "last_observed_at_utc" in cols:
        row["last_observed_at_utc"] = checkpoint_utc
    if "raw_count" in cols:
        row["raw_count"] = counts_now["news_raw_feed_events"]
    if "match_count" in cols:
        row["match_count"] = counts_now["news_token_match_events"]
    if "signal_count" in cols:
        row["signal_count"] = counts_now["news_signal_events"]
    if "score_count" in cols:
        row["score_count"] = counts_now["news_score_events_v1"]
    if "heartbeat_status" in cols:
        row["heartbeat_status"] = "OK_HISTORICAL_ACCESS_SYNCED"
    if "created_at_utc" in cols:
        row["created_at_utc"] = generated_at

    existing = None
    if "freshness_uid" in cols:
        existing = con.execute("SELECT rowid FROM " + q(FRESH_TABLE) + " WHERE freshness_uid=? LIMIT 1", [TARGET_UID]).fetchone()
    if existing is None and "component" in cols:
        existing = con.execute("SELECT rowid FROM " + q(FRESH_TABLE) + " WHERE component=? LIMIT 1", [TARGET_COMPONENT]).fetchone()

    if existing:
        rowid = existing[0]
        keys = [k for k in row if k not in ["freshness_uid"]]
        sql = "UPDATE " + q(FRESH_TABLE) + " SET " + ", ".join(q(k) + "=?" for k in keys) + " WHERE rowid=?"
        con.execute(sql, [row[k] for k in keys] + [rowid])
        action = "UPDATED_EXISTING_ROW"
    else:
        keys = list(row.keys())
        sql = "INSERT INTO " + q(FRESH_TABLE) + " (" + ",".join(q(k) for k in keys) + ") VALUES (" + ",".join(["?"] * len(keys)) + ")"
        con.execute(sql, [row[k] for k in keys])
        action = "INSERTED_NEW_ROW"

    return {"action": action, "row": row}

def main():
    failures = []
    warnings = []
    generated_at = now()
    ts_file = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    prior = load_json(PRIOR)
    prior_result = prior.get("result", {})
    expected_uids = prior_result.get("expected_news_uids", [])
    expected_count = int(prior_result.get("expected_count", 0) or 0)

    if prior.get("decision") != "OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_POST_APPLY_AUDIT_NOAPI":
        failures.append("prior_post_apply_audit_not_ok")
    if expected_count != len(expected_uids) or expected_count <= 0:
        failures.append("expected_uids_invalid")

    backup_dir = ROOT / "data/backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / ("tokenoskobi_clean_v1.PRE_NEWS_RUNTIME_FRESHNESS_STATE_CLEANUP_" + ts_file + ".sqlite")
    shutil.copy2(DB, backup_path)

    con = sqlite3.connect(str(DB), timeout=30)
    con.row_factory = sqlite3.Row

    applied = False
    try:
        missing_news_tables = [t for t in NEWS_TABLES if not table_exists(con, t)]
        if missing_news_tables:
            failures.append("missing_news_tables:" + ",".join(missing_news_tables))
        if not table_exists(con, FRESH_TABLE):
            failures.append("freshness_table_missing")

        before_counts = counts(con) if not missing_news_tables else {}
        before_freshness = freshness_snapshot(con)

        integrity_before = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity_before != "ok":
            failures.append("sqlite_integrity_before_not_ok")

        expected_chain = []
        for uid in expected_uids:
            c_raw = con.execute("SELECT COUNT(*) FROM news_raw_feed_events WHERE news_uid=?", [uid]).fetchone()[0]
            c_match = con.execute("SELECT COUNT(*) FROM news_token_match_events WHERE news_uid=?", [uid]).fetchone()[0]
            c_signal = con.execute("SELECT COUNT(*) FROM news_signal_events WHERE news_uid=?", [uid]).fetchone()[0]
            c_score = con.execute("SELECT COUNT(*) FROM news_score_events_v1 WHERE news_uid=?", [uid]).fetchone()[0]
            expected_chain.append({
                "news_uid": uid,
                "raw_count": c_raw,
                "match_count": c_match,
                "signal_count": c_signal,
                "score_count": c_score
            })
            if not (c_raw == c_match == c_signal == c_score == 1):
                failures.append("expected_chain_not_1_to_1:" + uid)

        checkpoint = choose_checkpoint(con, expected_uids)
        if checkpoint.get("warning"):
            warnings.append(checkpoint["warning"])
        if not checkpoint.get("checkpoint_utc"):
            failures.append("checkpoint_timestamp_missing")

        freshness_cols = table_cols(con, FRESH_TABLE) if table_exists(con, FRESH_TABLE) else []
        required_cols = ["last_observed_at_utc", "raw_count", "match_count", "signal_count", "score_count"]
        missing_required_cols = [c for c in required_cols if c not in freshness_cols]
        if missing_required_cols:
            failures.append("freshness_required_columns_missing:" + ",".join(missing_required_cols))

        if not failures:
            con.execute("BEGIN IMMEDIATE")
            upsert_result = upsert_freshness(con, freshness_cols, before_counts, checkpoint["checkpoint_utc"], generated_at)
            after_counts_preview = counts(con)
            after_freshness_preview = freshness_snapshot(con)
            integrity_after_preview = con.execute("PRAGMA integrity_check").fetchone()[0]

            sync_row = None
            if after_freshness_preview["target_rows"]:
                sync_row = after_freshness_preview["target_rows"][0]

            sync_ok = bool(sync_row)
            if sync_row:
                if "last_observed_at_utc" in sync_row and sync_row.get("last_observed_at_utc") != checkpoint["checkpoint_utc"]:
                    sync_ok = False
                if "raw_count" in sync_row and int(sync_row.get("raw_count")) != before_counts["news_raw_feed_events"]:
                    sync_ok = False
                if "match_count" in sync_row and int(sync_row.get("match_count")) != before_counts["news_token_match_events"]:
                    sync_ok = False
                if "signal_count" in sync_row and int(sync_row.get("signal_count")) != before_counts["news_signal_events"]:
                    sync_ok = False
                if "score_count" in sync_row and int(sync_row.get("score_count")) != before_counts["news_score_events_v1"]:
                    sync_ok = False

            news_delta_preview = {k: after_counts_preview[k] - before_counts[k] for k in before_counts}

            temp_failures = []
            if integrity_after_preview != "ok":
                temp_failures.append("sqlite_integrity_after_not_ok")
            if any(v != 0 for v in news_delta_preview.values()):
                temp_failures.append("news_tables_changed_during_freshness_cleanup")
            if not sync_ok:
                temp_failures.append("freshness_sync_row_not_verified")

            if temp_failures:
                con.rollback()
                failures.extend(temp_failures)
                applied = False
                after_counts = counts(con)
                after_freshness = freshness_snapshot(con)
                integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]
                upsert_result = {"action": "ROLLED_BACK", "row": {}}
            else:
                con.commit()
                applied = True
                after_counts = counts(con)
                after_freshness = freshness_snapshot(con)
                integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]
        else:
            after_counts = counts(con) if not missing_news_tables else {}
            after_freshness = freshness_snapshot(con)
            integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]
            upsert_result = {"action": "NOT_ATTEMPTED", "row": {}}

    except Exception as exc:
        try:
            con.rollback()
        except Exception:
            pass
        failures.append("cleanup_exception:" + repr(exc))
        applied = False
        before_counts = {}
        after_counts = {}
        before_freshness = {}
        after_freshness = {}
        integrity_before = "unknown"
        integrity_after = "unknown"
        checkpoint = {}
        expected_chain = []
        upsert_result = {"action": "EXCEPTION", "row": {}}
    finally:
        con.close()

    news_delta = {k: after_counts[k] - before_counts[k] for k in before_counts} if before_counts and after_counts else {}

    freshness_updated = False
    target_rows = after_freshness.get("target_rows", []) if isinstance(after_freshness, dict) else []
    if target_rows:
        r = target_rows[0]
        freshness_updated = (
            r.get("last_observed_at_utc") == checkpoint.get("checkpoint_utc")
            and int(r.get("raw_count", -1)) == after_counts.get("news_raw_feed_events")
            and int(r.get("match_count", -1)) == after_counts.get("news_token_match_events")
            and int(r.get("signal_count", -1)) == after_counts.get("news_signal_events")
            and int(r.get("score_count", -1)) == after_counts.get("news_score_events_v1")
        )

    tests = [
        {
            "test_id": "T01_PRIOR_POST_APPLY_AUDIT_OK",
            "ok": prior.get("decision") == "OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_POST_APPLY_AUDIT_NOAPI"
        },
        {
            "test_id": "T02_BACKUP_CREATED",
            "ok": backup_path.exists(),
            "backup_path": str(backup_path)
        },
        {
            "test_id": "T03_EXPECTED_CHAIN_STILL_1_TO_1",
            "ok": all(r["raw_count"] == r["match_count"] == r["signal_count"] == r["score_count"] == 1 for r in expected_chain),
            "expected_chain": expected_chain
        },
        {
            "test_id": "T04_CHECKPOINT_TIMESTAMP_SELECTED",
            "ok": bool(checkpoint.get("checkpoint_utc")),
            "checkpoint": checkpoint
        },
        {
            "test_id": "T05_FRESHNESS_SYNC_APPLIED",
            "ok": applied and freshness_updated,
            "upsert_result": upsert_result,
            "after_freshness": after_freshness
        },
        {
            "test_id": "T06_NEWS_TABLES_UNCHANGED",
            "ok": all(v == 0 for v in news_delta.values()),
            "news_delta": news_delta
        },
        {
            "test_id": "T07_SQLITE_INTEGRITY_OK",
            "ok": integrity_before == "ok" and integrity_after == "ok",
            "integrity_before": integrity_before,
            "integrity_after": integrity_after
        },
        {
            "test_id": "T08_NOAPI_BOUNDARY_LOCKED",
            "ok": True,
            "network_call": False,
            "api_call": False,
            "db_write": True,
            "schema_change": False,
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

    next_step = "NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW" if not failures else "NEWS_RUNTIME_FRESHNESS_STATE_CLEANUP_HOLD"

    return {
        "stage": "NEWS_RUNTIME_FRESHNESS_STATE_CLEANUP_APPLY_WITH_BACKUP_NOAPI",
        "generated_at_utc": generated_at,
        "decision": "OK_NEWS_RUNTIME_FRESHNESS_STATE_CLEANUP_APPLY_WITH_BACKUP_NOAPI_INTERNAL" if not failures else "FAIL_NEWS_RUNTIME_FRESHNESS_STATE_CLEANUP_APPLY_WITH_BACKUP_NOAPI_INTERNAL",
        "applied": applied,
        "backup_path": str(backup_path),
        "prior": "data/control/news_historical_access_real_fetch_post_apply_audit_noapi_v1.json",
        "expected_count": expected_count,
        "checkpoint": checkpoint,
        "upsert_result": upsert_result,
        "before_counts": before_counts,
        "after_counts": after_counts,
        "news_delta": news_delta,
        "before_freshness": before_freshness,
        "after_freshness": after_freshness,
        "freshness_updated": freshness_updated,
        "integrity_before": integrity_before,
        "integrity_after": integrity_after,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "network_call": False,
            "api_call": False,
            "db_write": True,
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
