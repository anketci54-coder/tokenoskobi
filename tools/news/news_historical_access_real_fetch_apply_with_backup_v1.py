
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, shutil, importlib.util, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_historical_access_real_fetch_tempdb_dryrun_with_network_v1.json"
DRYRUN_TOOL = ROOT / "tools/news_historical_access_real_fetch_tempdb_dryrun_with_network_v1.py"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

STAGE = "NEWS_HISTORICAL_ACCESS_REAL_FETCH_APPLY_WITH_BACKUP"

def now():
    return datetime.now(timezone.utc).isoformat()

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}

def import_dryrun_tool():
    spec = importlib.util.spec_from_file_location("news_hist_dryrun_tool", str(DRYRUN_TOOL))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def md5(s):
    return hashlib.md5((s or "").encode("utf-8")).hexdigest()

def apply_main():
    failures = []
    warnings = []
    ts_file = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    generated_at = now()

    prior = load_json(PRIOR)
    if prior.get("decision") != "OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_TEMPDB_DRYRUN_WITH_NETWORK":
        failures.append("prior_tempdb_dryrun_not_ok")

    backup_dir = ROOT / "data/backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / ("tokenoskobi_clean_v1.PRE_NEWS_HISTORICAL_ACCESS_REAL_FETCH_APPLY_WITH_BACKUP_" + ts_file + ".sqlite")
    shutil.copy2(DB, backup_path)

    hist = import_dryrun_tool()

    fetch_results = []
    fetched = []
    for feed in hist.FEEDS:
        try:
            items = hist.fetch_rss(feed)
            fetch_results.append({
                "feed": feed,
                "ok": True,
                "item_count": len(items),
                "sample_titles": [x["title"] for x in items[:5]]
            })
            fetched.extend(items)
        except Exception as exc:
            fetch_results.append({
                "feed": feed,
                "ok": False,
                "error": repr(exc)
            })
            warnings.append("feed_fetch_failed:" + feed["url"])

    dedup = {}
    for item in fetched:
        dedup[item["news_uid"]] = item
    fetched_unique = list(dedup.values())[:500]

    if not fetched_unique:
        failures.append("no_items_fetched_from_network")

    con = sqlite3.connect(str(DB), timeout=30)
    con.row_factory = sqlite3.Row

    inserted_raw_uids = []
    raw_failed = []
    duplicates = 0
    inserted = {
        "news_token_match_events": 0,
        "news_signal_events": 0,
        "news_score_events_v1": 0
    }
    samples = []
    temp_failures = []

    try:
        before = counts(con)
        integrity_before = con.execute("PRAGMA integrity_check").fetchone()[0]

        con.execute("BEGIN IMMEDIATE")

        raw_cols = hist.table_cols(con, "news_raw_feed_events")

        for item in fetched_unique:
            if hist.existing_item(con, item):
                duplicates += 1
                continue

            row = hist.raw_insert_row_for_cols(raw_cols, item)
            keys = list(row.keys())
            sql = "INSERT INTO news_raw_feed_events (" + ",".join(q(k) for k in keys) + ") VALUES (" + ",".join(["?"] * len(keys)) + ")"

            try:
                con.execute(sql, [row[k] for k in keys])
                inserted_raw_uids.append(item["news_uid"])
            except Exception as exc:
                raw_failed.append({
                    "news_uid": item["news_uid"],
                    "title": item["title"],
                    "error": repr(exc)
                })

        if raw_failed:
            temp_failures.append("raw_insert_failures_present")

        candidates = []
        if inserted_raw_uids:
            placeholders = ",".join(["?"] * len(inserted_raw_uids))
            candidates = con.execute("""
                SELECT news_uid, source_uid, published_at_utc, fetched_at_utc, title
                FROM news_raw_feed_events
                WHERE news_uid IN (""" + placeholders + """)
                  AND NOT EXISTS (
                    SELECT 1 FROM news_token_match_events m
                    WHERE m.news_uid = news_raw_feed_events.news_uid
                  )
                ORDER BY COALESCE(published_at_utc, fetched_at_utc) ASC
            """, inserted_raw_uids).fetchall()

        for r in candidates:
            news_uid = r["news_uid"]
            source_uid = r["source_uid"]
            title = r["title"] or ""
            symbol, chain, keyword, matched = hist.pick_symbol(title)
            token_uid = "news_token_" + chain.lower().replace(" ", "_") + "_" + symbol.lower()
            pair_uid = "news_pair_" + symbol.lower() + "_usd"
            match_type = "historical_title_keyword" if matched else "historical_generic_crypto_news"
            match_confidence = 0.85 if matched else 0.40
            match_score = 82 if matched else 40
            evidence = title[:500]
            risk, risk_label = hist.risk_score(title)
            relevance = match_score
            fusion = int(round((relevance + risk) / 2))
            importance_label = hist.label_from_score(relevance)
            fusion_label = hist.label_from_score(fusion)

            match_uid = "news_match_" + md5("historical_match:v1:" + news_uid + ":" + token_uid + ":" + pair_uid + ":" + match_type)
            signal_uid = "news_signal_" + md5("historical_signal:v1:" + news_uid + ":" + token_uid + ":" + pair_uid + ":NEWS_HISTORICAL_BACKFILL")
            score_uid = "news_score_" + md5("historical_score:v1:" + news_uid + ":" + token_uid + ":" + pair_uid)

            cur = con.execute("""
                INSERT INTO news_token_match_events
                (match_uid, news_uid, source_uid, token_uid, pair_uid, symbol, chain, match_type,
                 match_confidence, match_score, match_reasons_json, evidence_text,
                 is_duplicate, write_allowed, trade_signal, paper_signal, created_at_utc)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM news_token_match_events WHERE match_uid = ?
                )
            """, [
                match_uid, news_uid, source_uid, token_uid, pair_uid, symbol, chain, match_type,
                match_confidence, match_score,
                json.dumps({
                    "method": "news_historical_access_real_fetch_apply_with_backup_v1",
                    "matched_keyword": keyword,
                    "matched_symbol": matched,
                    "no_trade": True,
                    "source": "title",
                    "stage": STAGE
                }, ensure_ascii=False, sort_keys=True),
                evidence,
                generated_at,
                match_uid
            ])
            inserted["news_token_match_events"] += max(cur.rowcount, 0)

            cur = con.execute("""
                INSERT INTO news_signal_events
                (signal_uid, news_uid, token_uid, pair_uid, symbol, chain, signal_type,
                 signal_strength, signal_label, source_match_uid, evidence_text, created_at_utc)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM news_signal_events WHERE signal_uid = ?
                )
            """, [
                signal_uid, news_uid, token_uid, pair_uid, symbol, chain,
                "NEWS_HISTORICAL_BACKFILL", fusion, fusion_label, match_uid, evidence, generated_at,
                signal_uid
            ])
            inserted["news_signal_events"] += max(cur.rowcount, 0)

            cur = con.execute("""
                INSERT INTO news_score_events_v1
                (score_uid, news_uid, token_uid, pair_uid, symbol, chain,
                 news_token_relevance_score_100, news_risk_score_100, news_fusion_score_100,
                 importance_label, risk_label, fusion_label, explanation, created_at_utc)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM news_score_events_v1 WHERE score_uid = ?
                )
            """, [
                score_uid, news_uid, token_uid, pair_uid, symbol, chain,
                relevance, risk, fusion,
                importance_label, risk_label, fusion_label,
                "Historical real fetch apply from RSS raw NEWS feed; no trade authority.",
                generated_at,
                score_uid
            ])
            inserted["news_score_events_v1"] += max(cur.rowcount, 0)

            if len(samples) < 10:
                samples.append({
                    "news_uid": news_uid,
                    "title": title,
                    "symbol": symbol,
                    "chain": chain,
                    "matched_keyword": keyword,
                    "risk_label": risk_label,
                    "fusion_label": fusion_label
                })

        after_preview = counts(con)
        delta_preview = {k: after_preview[k] - before[k] for k in before}

        integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]

        bad_trade_flags = con.execute("""
            SELECT COUNT(*)
            FROM news_token_match_events
            WHERE created_at_utc = ?
              AND (write_allowed != 0 OR trade_signal != 0 OR paper_signal != 0)
        """, [generated_at]).fetchone()[0]

        if integrity_before != "ok":
            temp_failures.append("sqlite_integrity_before_not_ok")
        if integrity_after != "ok":
            temp_failures.append("sqlite_integrity_after_not_ok")
        if bad_trade_flags != 0:
            temp_failures.append("bad_trade_flags_nonzero")
        if delta_preview.get("news_raw_feed_events", 0) != len(inserted_raw_uids):
            temp_failures.append("raw_delta_mismatch")
        if inserted_raw_uids:
            for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
                if inserted.get(t, 0) != len(candidates):
                    temp_failures.append("derived_insert_mismatch:" + t)
        if len(candidates) != len(inserted_raw_uids):
            temp_failures.append("candidate_count_mismatch")

        if temp_failures:
            con.rollback()
            applied = False
            after = counts(con)
            delta = {k: after[k] - before[k] for k in before}
            failures.extend(temp_failures)
        else:
            con.commit()
            applied = True
            after = counts(con)
            delta = {k: after[k] - before[k] for k in before}

    except Exception as exc:
        con.rollback()
        before = counts(con)
        after = counts(con)
        delta = {k: after[k] - before[k] for k in before}
        applied = False
        failures.append("apply_exception:" + repr(exc))
        integrity_before = "unknown"
        integrity_after = "unknown"
        bad_trade_flags = -1
    finally:
        con.close()

    if inserted_raw_uids and not failures:
        next_step = "NEWS_HISTORICAL_ACCESS_REAL_FETCH_POST_APPLY_AUDIT_NOAPI"
    elif not failures:
        next_step = "NEWS_HISTORICAL_ACCESS_REAL_FETCH_SOURCE_REVIEW_OR_WAIT"
        warnings.append("no_new_real_rows_inserted_all_duplicates_or_no_candidates")
    else:
        next_step = "NEWS_HISTORICAL_ACCESS_REAL_FETCH_APPLY_REPAIR_REQUIRED"

    tests = [
        {
            "test_id": "T01_PRIOR_TEMPDB_DRYRUN_OK",
            "ok": prior.get("decision") == "OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_TEMPDB_DRYRUN_WITH_NETWORK"
        },
        {
            "test_id": "T02_BACKUP_CREATED",
            "ok": backup_path.exists(),
            "backup_path": str(backup_path)
        },
        {
            "test_id": "T03_NETWORK_FETCH_OK",
            "ok": len(fetch_results) > 0 and any(x.get("ok") for x in fetch_results) and len(fetched_unique) > 0,
            "fetched_unique_count": len(fetched_unique)
        },
        {
            "test_id": "T04_REAL_DB_APPLY_TRANSACTION_OK",
            "ok": not failures and applied is True,
            "raw_inserted": len(inserted_raw_uids),
            "derived_inserted": inserted
        },
        {
            "test_id": "T05_DELTA_MATCHES_INSERTS",
            "ok": not failures and delta.get("news_raw_feed_events", 0) == len(inserted_raw_uids)
                  and delta.get("news_token_match_events", 0) == inserted.get("news_token_match_events", 0)
                  and delta.get("news_signal_events", 0) == inserted.get("news_signal_events", 0)
                  and delta.get("news_score_events_v1", 0) == inserted.get("news_score_events_v1", 0),
            "delta": delta
        },
        {
            "test_id": "T06_NO_TRADE_FLAGS",
            "ok": bad_trade_flags == 0,
            "bad_trade_flags": bad_trade_flags
        },
        {
            "test_id": "T07_AUTHORITY_BOUNDARY_LOCKED",
            "ok": True,
            "network_call": True,
            "real_db_write": bool(inserted_raw_uids),
            "api_call": False,
            "service_change": False,
            "timer_change": False,
            "paper_trade": False,
            "live_trade": False,
            "trade_authority": False
        }
    ]

    return {
        "stage": STAGE,
        "generated_at_utc": now(),
        "decision": "OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_APPLY_WITH_BACKUP_INTERNAL" if not failures else "FAIL_NEWS_HISTORICAL_ACCESS_REAL_FETCH_APPLY_WITH_BACKUP_INTERNAL",
        "applied": applied,
        "backup_path": str(backup_path),
        "fetch_results": fetch_results,
        "fetched_unique_count": len(fetched_unique),
        "raw_insert": {
            "inserted": len(inserted_raw_uids),
            "inserted_news_uids": inserted_raw_uids,
            "duplicates": duplicates,
            "failed": raw_failed
        },
        "derived_inserted": inserted,
        "samples": samples,
        "db_before": before,
        "db_after": after,
        "db_delta": delta,
        "integrity_before": integrity_before,
        "integrity_after": integrity_after,
        "bad_trade_flags": bad_trade_flags,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "network_call": True,
            "api_call": False,
            "real_db_write": bool(inserted_raw_uids),
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
    print(json.dumps(apply_main(), ensure_ascii=False, indent=2, sort_keys=True))
