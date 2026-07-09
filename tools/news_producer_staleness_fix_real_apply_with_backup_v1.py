
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, shutil, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PLAN_ART = ROOT / "data/control/news_producer_staleness_fix_real_apply_plan_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

KEYWORDS = [
    ("BTC", "Bitcoin", ["bitcoin", "btc"]),
    ("ETH", "Ethereum", ["ethereum", "ether", "eth"]),
    ("SOL", "Solana", ["solana", " sol "]),
    ("LINK", "Chainlink", ["chainlink", "link", "ccip"]),
    ("AAVE", "Ethereum", ["aave"]),
    ("ZRO", "LayerZero", ["layerzero"]),
    ("MNT", "Mantle", ["mantle"]),
    ("USDC", "Multi", ["usdc", "stablecoin", "stablecoins"]),
    ("USDT", "Multi", ["usdt", "tether"]),
    ("XRP", "Ripple", ["xrp", "ripple"]),
    ("BNB", "BNB", ["bnb", "binance"]),
    ("TON", "TON", ["toncoin", " ton "]),
    ("ADA", "Cardano", ["cardano", " ada "]),
    ("AVAX", "Avalanche", ["avalanche", "avax"]),
    ("TRX", "Tron", ["tron", "trx"]),
    ("UNI", "Ethereum", ["uniswap", " uni "])
]

RISK_WORDS = ["hack", "exploit", "phishing", "scam", "launder", "laundering", "stolen", "breach", "attack", "fraud"]
REG_WORDS = ["regulator", "regulation", "orders", "compliance", "sec", "law", "policy", "verification"]

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def pick_symbol(title):
    text = " " + (title or "").lower() + " "
    for symbol, chain, keys in KEYWORDS:
        for k in keys:
            if k.lower() in text:
                return symbol, chain, k.strip(), True
    return "CRYPTO", "Multi", "generic_crypto_news", False

def risk_score(title):
    text = (title or "").lower()
    if any(w in text for w in RISK_WORDS):
        return 85, "HIGH"
    if any(w in text for w in REG_WORDS):
        return 70, "MEDIUM"
    return 45, "LOW"

def label_from_score(v):
    if v >= 80:
        return "HIGH"
    if v >= 55:
        return "MEDIUM"
    return "LOW"

def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}

def latest_derived_ts(con):
    vals = []
    for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
        v = con.execute("SELECT MAX(created_at_utc) FROM " + q(t) + " WHERE created_at_utc IS NOT NULL").fetchone()[0]
        if v:
            vals.append(v)
    return max(vals) if vals else None

def latest_raw_ts(con):
    return con.execute("""
        SELECT MAX(COALESCE(published_at_utc, fetched_at_utc))
        FROM news_raw_feed_events
        WHERE COALESCE(published_at_utc, fetched_at_utc) IS NOT NULL
    """).fetchone()[0]

def integrity_check(db_path):
    con = sqlite3.connect("file:" + str(db_path) + "?mode=ro", uri=True)
    try:
        return con.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        con.close()

def main():
    plan_art = load(PLAN_ART)
    plan = load(ROOT / plan_art["plan"])
    failures = []
    warnings = []

    if plan_art.get("decision") != "OK_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_PLAN_NOAPI":
        failures.append("prior_real_apply_plan_not_ok")

    scope = plan_art.get("real_apply_scope", {})
    if scope.get("requires_commander_approval_before_next") is not True:
        failures.append("commander_approval_gate_missing_in_plan")

    if scope.get("backup_required_before_write") is not True:
        failures.append("backup_required_missing_in_plan")

    backup_db = Path(plan_art.get("backup_plan", {}).get("backup_db", ""))
    if not backup_db:
        failures.append("backup_db_path_missing")

    timer_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    before_sha = sha256(DB)
    backup_db.parent.mkdir(parents=True, exist_ok=True)
    (backup_db.parent.parent / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
    shutil.copy2(DB, backup_db)
    backup_sha = sha256(backup_db)

    if backup_sha != before_sha:
        failures.append("backup_sha_mismatch")

    integrity_before = integrity_check(DB)
    if integrity_before != "ok":
        failures.append("sqlite_integrity_before_not_ok")

    con = sqlite3.connect(str(DB), timeout=30)
    con.row_factory = sqlite3.Row
    inserted = {
        "news_token_match_events": 0,
        "news_signal_events": 0,
        "news_score_events_v1": 0
    }
    samples = []
    generated_at = now()

    try:
        con.execute("BEGIN IMMEDIATE")
        before_counts = counts(con)
        latest_derived = latest_derived_ts(con)
        latest_raw = latest_raw_ts(con)

        candidates = con.execute("""
            SELECT news_uid, source_uid, published_at_utc, fetched_at_utc, title
            FROM news_raw_feed_events r
            WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
              AND NOT EXISTS (
                SELECT 1 FROM news_token_match_events m
                WHERE m.news_uid = r.news_uid
              )
            ORDER BY COALESCE(r.published_at_utc, r.fetched_at_utc) ASC
        """, [latest_derived]).fetchall()

        batch_limit = int(plan.get("apply_algorithm_locked", {}).get("batch_limit", 250))
        if len(candidates) <= 0:
            failures.append("no_candidates_at_apply_time")
        if len(candidates) > batch_limit:
            failures.append("candidate_count_exceeds_batch_limit")

        if failures:
            con.rollback()
        else:
            for r in candidates:
                news_uid = r["news_uid"]
                source_uid = r["source_uid"]
                title = r["title"] or ""
                symbol, chain, keyword, matched = pick_symbol(title)
                token_uid = "news_token_" + chain.lower().replace(" ", "_") + "_" + symbol.lower()
                pair_uid = "news_pair_" + symbol.lower() + "_usd"
                match_type = "title_keyword" if matched else "generic_crypto_news"
                match_confidence = 0.85 if matched else 0.40
                match_score = 82 if matched else 40
                evidence = title[:500]
                risk, risk_label = risk_score(title)
                relevance = match_score
                fusion = int(round((relevance + risk) / 2))
                importance_label = label_from_score(relevance)
                fusion_label = label_from_score(fusion)

                match_uid = "news_match_" + md5("match:v1:" + news_uid + ":" + token_uid + ":" + pair_uid + ":" + match_type)
                signal_uid = "news_signal_" + md5("signal:v1:" + news_uid + ":" + token_uid + ":" + pair_uid + ":NEWS_DERIVED_REFRESH")
                score_uid = "news_score_" + md5("score:v1:" + news_uid + ":" + token_uid + ":" + pair_uid)

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
                        "method": "real_db_derived_layer_rebind_v1",
                        "matched_keyword": keyword,
                        "matched_symbol": matched,
                        "no_trade": True,
                        "source": "title"
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
                    "NEWS_DERIVED_REFRESH", fusion, fusion_label, match_uid, evidence, generated_at,
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
                    "Real DB derived refresh from current raw feed; no trade authority.",
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

            after_counts = counts(con)
            delta = {k: after_counts[k] - before_counts[k] for k in before_counts}

            flag_bad = con.execute("""
                SELECT COUNT(*)
                FROM news_token_match_events
                WHERE created_at_utc = ?
                  AND (write_allowed != 0 OR trade_signal != 0 OR paper_signal != 0)
            """, [generated_at]).fetchone()[0]

            remaining = con.execute("""
                SELECT COUNT(*)
                FROM news_raw_feed_events r
                WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
                  AND NOT EXISTS (
                    SELECT 1 FROM news_token_match_events m
                    WHERE m.news_uid = r.news_uid
                  )
            """, [latest_derived]).fetchone()[0]

            if flag_bad != 0:
                failures.append("write_trade_paper_flag_not_zero")

            if remaining != 0:
                warnings.append("remaining_candidates_after_apply_nonzero")

            con.commit()

    except Exception as exc:
        try:
            con.rollback()
        except Exception:
            pass
        failures.append("real_apply_exception:" + repr(exc))
        before_counts = {}
        after_counts = {}
        delta = {}
        latest_derived = None
        latest_raw = None
        remaining = None
        flag_bad = None
    finally:
        con.close()

    after_sha = sha256(DB)
    integrity_after = integrity_check(DB)

    con2 = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        final_counts = counts(con2)
        final_latest_derived = latest_derived_ts(con2)
        final_latest_raw = latest_raw_ts(con2)
    finally:
        con2.close()

    timer_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    if integrity_after != "ok":
        failures.append("sqlite_integrity_after_not_ok")

    if timer_before.get("stdout") != timer_after.get("stdout"):
        failures.append("timer_state_changed")

    if service_before.get("stdout") != service_after.get("stdout"):
        warnings.append("service_state_changed_during_apply")

    if inserted.get("news_token_match_events", 0) <= 0:
        failures.append("no_token_match_inserted")
    if inserted.get("news_signal_events", 0) <= 0:
        failures.append("no_signal_inserted")
    if inserted.get("news_score_events_v1", 0) <= 0:
        failures.append("no_score_inserted")

    if inserted.get("news_token_match_events") != inserted.get("news_signal_events") or inserted.get("news_token_match_events") != inserted.get("news_score_events_v1"):
        failures.append("derived_insert_counts_not_equal")

    tests = [
        {
            "test_id": "T01_BACKUP_CREATED_AND_SHA_MATCH",
            "ok": backup_db.exists() and backup_sha == before_sha,
            "backup_db": str(backup_db),
            "backup_sha256": backup_sha,
            "real_db_sha256_before": before_sha
        },
        {
            "test_id": "T02_SQLITE_INTEGRITY_BEFORE_AFTER_OK",
            "ok": integrity_before == "ok" and integrity_after == "ok",
            "integrity_before": integrity_before,
            "integrity_after": integrity_after
        },
        {
            "test_id": "T03_REAL_DERIVED_INSERT_DELTA_POSITIVE",
            "ok": inserted.get("news_token_match_events", 0) > 0 and inserted.get("news_signal_events", 0) > 0 and inserted.get("news_score_events_v1", 0) > 0,
            "inserted": inserted
        },
        {
            "test_id": "T04_RAW_FEED_NOT_MUTATED_BY_APPLY",
            "ok": delta.get("news_raw_feed_events", 0) == 0,
            "transaction_delta": delta
        },
        {
            "test_id": "T05_NO_TRADE_FLAGS_SET",
            "ok": flag_bad == 0,
            "bad_flag_count": flag_bad
        },
        {
            "test_id": "T06_RUNTIME_BOUNDARY_UNCHANGED",
            "ok": timer_before.get("stdout") == timer_after.get("stdout"),
            "timer_before": timer_before.get("stdout"),
            "timer_after": timer_after.get("stdout"),
            "service_before": service_before.get("stdout"),
            "service_after": service_after.get("stdout")
        },
        {
            "test_id": "T07_FRESHNESS_ADVANCED",
            "ok": final_latest_derived is not None and final_latest_derived != latest_derived,
            "latest_derived_before": latest_derived,
            "latest_derived_after": final_latest_derived,
            "latest_raw_after": final_latest_raw
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI" if not failures else "NEWS_PRODUCER_STALENESS_REAL_APPLY_REPAIR_OR_ROLLBACK_REQUIRED"

    return {
        "stage": "NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP",
        "generated_at_utc": now(),
        "decision": "OK_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP_INTERNAL" if not failures else "FAIL_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP_INTERNAL",
        "backup": {
            "backup_db": str(backup_db),
            "backup_sha256": backup_sha,
            "real_db_sha256_before": before_sha,
            "real_db_sha256_after": after_sha
        },
        "integrity": {
            "before": integrity_before,
            "after": integrity_after
        },
        "latest": {
            "derived_before": latest_derived,
            "raw_before": latest_raw,
            "derived_after": final_latest_derived,
            "raw_after": final_latest_raw
        },
        "transaction_counts": {
            "before": before_counts,
            "after": after_counts,
            "delta": delta
        },
        "final_counts": final_counts,
        "inserted": inserted,
        "remaining_candidates_after_apply": remaining,
        "bad_trade_flag_count": flag_bad,
        "samples": samples,
        "timer_before": timer_before,
        "timer_after": timer_after,
        "service_before": service_before,
        "service_after": service_after,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "api_call": False,
            "network_call": False,
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
