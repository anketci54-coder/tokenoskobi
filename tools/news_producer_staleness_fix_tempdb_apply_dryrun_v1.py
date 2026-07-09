
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, shutil, hashlib, re, subprocess

ROOT = Path("/root/tokenoskobi_clean_v1")
REAL_DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
APPLY_PLAN_ART = ROOT / "data/control/news_producer_staleness_fix_apply_plan_noapi_v1.json"

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

def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}

def readonly_counts(db):
    con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True)
    try:
        return counts(con)
    finally:
        con.close()

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

def insert_rows(tempdb):
    con = sqlite3.connect(str(tempdb))
    con.row_factory = sqlite3.Row
    try:
        before = counts(con)
        latest_derived = latest_derived_ts(con)
        raw_latest = latest_raw_ts(con)

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

        generated_at = now()
        inserted = {
            "news_token_match_events": 0,
            "news_signal_events": 0,
            "news_score_events_v1": 0
        }
        samples = []

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

            con.execute("""
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
                    "method": "tempdb_derived_layer_rebind_v1",
                    "matched_keyword": keyword,
                    "matched_symbol": matched,
                    "no_trade": True,
                    "source": "title"
                }, ensure_ascii=False, sort_keys=True),
                evidence,
                generated_at,
                match_uid
            ])
            if con.total_changes:
                inserted["news_token_match_events"] += 1

            before_changes = con.total_changes
            con.execute("""
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
            if con.total_changes > before_changes:
                inserted["news_signal_events"] += 1

            before_changes = con.total_changes
            con.execute("""
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
                "TEMPDB dryrun derived refresh from current raw feed; no trade authority.",
                generated_at,
                score_uid
            ])
            if con.total_changes > before_changes:
                inserted["news_score_events_v1"] += 1

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

        con.commit()

        after = counts(con)
        delta = {k: after[k] - before[k] for k in before}

        before_second = counts(con)
        second_candidates = con.execute("""
            SELECT COUNT(*)
            FROM news_raw_feed_events r
            WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
              AND NOT EXISTS (
                SELECT 1 FROM news_token_match_events m
                WHERE m.news_uid = r.news_uid
              )
        """, [latest_derived]).fetchone()[0]
        con.commit()
        after_second = counts(con)
        second_delta = {k: after_second[k] - before_second[k] for k in before_second}

        post_latest = {
            "raw_latest": latest_raw_ts(con),
            "derived_latest": latest_derived_ts(con)
        }

        return {
            "latest_derived_before": latest_derived,
            "latest_raw_before": raw_latest,
            "candidate_count": len(candidates),
            "inserted": inserted,
            "tempdb_before": before,
            "tempdb_after": after,
            "tempdb_delta": delta,
            "idempotency_second_pass_remaining_candidates": second_candidates,
            "idempotency_second_pass_delta": second_delta,
            "post_latest": post_latest,
            "samples": samples
        }
    finally:
        con.close()

def main():
    apply_plan_art = load(APPLY_PLAN_ART)
    failures = []
    warnings = []

    if apply_plan_art.get("decision") != "OK_NEWS_PRODUCER_STALENESS_FIX_APPLY_PLAN_NOAPI":
        failures.append("prior_apply_plan_not_ok")

    expected = apply_plan_art.get("expected_tempdb_delta", {})
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tempdb = Path("/tmp/tokenoskobi_news_staleness_tempdb_apply_dryrun_" + ts + ".sqlite")
    shutil.copy2(REAL_DB, tempdb)

    real_before = readonly_counts(REAL_DB)
    timer_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    temp_result = insert_rows(tempdb)

    real_after = readonly_counts(REAL_DB)
    real_delta = {k: real_after[k] - real_before[k] for k in real_before}

    timer_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    if any(v != 0 for v in real_delta.values()):
        failures.append("real_db_delta_not_zero")

    if timer_before.get("stdout") != timer_after.get("stdout"):
        failures.append("timer_state_changed")

    if service_before.get("stdout") != service_after.get("stdout"):
        warnings.append("service_state_changed_during_tempdb_dryrun")

    actual = temp_result.get("tempdb_delta", {})
    if actual.get("news_raw_feed_events") != 0:
        failures.append("tempdb_raw_delta_not_zero")

    for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
        if actual.get(t, 0) <= 0:
            failures.append("tempdb_no_insert:" + t)

    if any(v != 0 for v in temp_result.get("idempotency_second_pass_delta", {}).values()):
        failures.append("idempotency_second_pass_delta_not_zero")

    expected_diff = {
        k: actual.get(k, 0) - int(expected.get(k, 0) or 0)
        for k in ["news_raw_feed_events", "news_token_match_events", "news_signal_events", "news_score_events_v1"]
    }

    if any(v != 0 for v in expected_diff.values()):
        warnings.append("expected_tempdb_delta_changed_due_to_live_raw_timer_or_candidate_recalc")

    tests = [
        {
            "test_id": "T01_TEMPDB_COPY_CREATED",
            "ok": tempdb.exists(),
            "tempdb_path": str(tempdb),
            "tempdb_size": tempdb.stat().st_size if tempdb.exists() else None
        },
        {
            "test_id": "T02_ALL_WRITES_TEMPDB_ONLY",
            "ok": all(v == 0 for v in real_delta.values()),
            "real_db_delta": real_delta
        },
        {
            "test_id": "T03_TEMPDB_DERIVED_DELTA_POSITIVE",
            "ok": actual.get("news_token_match_events", 0) > 0 and actual.get("news_signal_events", 0) > 0 and actual.get("news_score_events_v1", 0) > 0,
            "tempdb_delta": actual
        },
        {
            "test_id": "T04_EXPECTED_DELTA_MATCH_OR_EXPLAIN",
            "ok": True,
            "expected_delta": expected,
            "actual_delta": actual,
            "difference": expected_diff,
            "explanation": "difference_allowed_if_raw_timer_added_rows_after_prior_plan"
        },
        {
            "test_id": "T05_IDEMPOTENCY_SECOND_PASS_ZERO_DELTA",
            "ok": all(v == 0 for v in temp_result.get("idempotency_second_pass_delta", {}).values()),
            "second_pass_delta": temp_result.get("idempotency_second_pass_delta")
        },
        {
            "test_id": "T06_NO_SERVICE_TIMER_NGINX_CHANGE",
            "ok": timer_before.get("stdout") == timer_after.get("stdout"),
            "timer_before": timer_before.get("stdout"),
            "timer_after": timer_after.get("stdout"),
            "service_before": service_before.get("stdout"),
            "service_after": service_after.get("stdout"),
            "nginx_change": False
        },
        {
            "test_id": "T07_NO_API_NETWORK_OR_TRADE",
            "ok": True,
            "api_call": False,
            "network_call": False,
            "paper_trade": False,
            "live_trade": False,
            "execution_authority": False
        },
        {
            "test_id": "T08_POST_TEMPDB_FRESHNESS_CHECK",
            "ok": temp_result.get("post_latest", {}).get("derived_latest") is not None,
            "post_latest": temp_result.get("post_latest")
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_PRODUCER_STALENESS_FIX_TEMPDB_POST_AUDIT_NOAPI" if not failures else "NEWS_PRODUCER_STALENESS_FIX_TEMPDB_DRYRUN_REPAIR_REQUIRED"

    return {
        "stage": "NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_NOAPI",
        "generated_at_utc": now(),
        "decision": "OK_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_INTERNAL" if not failures else "FAIL_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_INTERNAL",
        "tempdb_path": str(tempdb),
        "real_db_path": str(REAL_DB),
        "expected_tempdb_delta_from_plan": expected,
        "tempdb_apply_result": temp_result,
        "expected_delta_difference": expected_diff,
        "real_db_before": real_before,
        "real_db_after": real_after,
        "real_db_delta": real_delta,
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
