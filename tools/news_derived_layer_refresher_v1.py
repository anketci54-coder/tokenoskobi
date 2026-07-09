
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, sqlite3

ROOT = Path("/root/tokenoskobi_clean_v1")
DEFAULT_DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

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

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

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

def run_refresher(db_path, write, max_batch, stage):
    failures = []
    warnings = []
    generated_at = now()
    db_path = Path(db_path)

    con = sqlite3.connect(str(db_path), timeout=30)
    con.row_factory = sqlite3.Row

    inserted = {
        "news_token_match_events": 0,
        "news_signal_events": 0,
        "news_score_events_v1": 0
    }
    samples = []

    try:
        integrity_before = con.execute("PRAGMA integrity_check").fetchone()[0]
        before = counts(con)
        latest_derived = latest_derived_ts(con)
        latest_raw = latest_raw_ts(con)

        if latest_derived is None:
            failures.append("latest_derived_missing")

        candidates = []
        if latest_derived is not None:
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

        candidate_count = len(candidates)

        if candidate_count > max_batch:
            failures.append("candidate_count_exceeds_max_batch")

        if candidate_count == 0:
            warnings.append("no_new_raw_candidates_to_refresh")

        if write and not failures:
            con.execute("BEGIN IMMEDIATE")
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
                        "method": "news_derived_layer_refresher_v1",
                        "matched_keyword": keyword,
                        "matched_symbol": matched,
                        "no_trade": True,
                        "source": "title",
                        "stage": stage
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
                    "Derived refresh from raw NEWS feed; no trade authority.",
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

            con.commit()

        elif not write:
            warnings.append("write_flag_false_preview_only")

        after = counts(con)
        delta = {k: after[k] - before[k] for k in before}
        integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]

        latest_derived_after = latest_derived_ts(con)
        latest_raw_after = latest_raw_ts(con)

        remaining_candidates = 0
        if latest_derived is not None:
            remaining_candidates = con.execute("""
                SELECT COUNT(*)
                FROM news_raw_feed_events r
                WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
                  AND NOT EXISTS (
                    SELECT 1 FROM news_token_match_events m
                    WHERE m.news_uid = r.news_uid
                  )
            """, [latest_derived]).fetchone()[0]

        bad_trade_flags = 0
        if write:
            bad_trade_flags = con.execute("""
                SELECT COUNT(*)
                FROM news_token_match_events
                WHERE created_at_utc = ?
                  AND (write_allowed != 0 OR trade_signal != 0 OR paper_signal != 0)
            """, [generated_at]).fetchone()[0]

        if integrity_before != "ok":
            failures.append("sqlite_integrity_before_not_ok")
        if integrity_after != "ok":
            failures.append("sqlite_integrity_after_not_ok")

        if delta.get("news_raw_feed_events", 0) != 0:
            failures.append("raw_feed_delta_not_zero")

        if candidate_count > 0:
            for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
                if inserted.get(t) != candidate_count:
                    failures.append("inserted_count_mismatch:" + t)

        if bad_trade_flags != 0:
            failures.append("bad_trade_flags_nonzero")

        tests = [
            {
                "test_id": "T01_SQLITE_INTEGRITY_OK",
                "ok": integrity_before == "ok" and integrity_after == "ok",
                "integrity_before": integrity_before,
                "integrity_after": integrity_after
            },
            {
                "test_id": "T02_RAW_SELECTION_OK",
                "ok": latest_derived is not None,
                "latest_derived_before": latest_derived,
                "latest_raw_before": latest_raw,
                "candidate_count": candidate_count
            },
            {
                "test_id": "T03_INSERTS_MATCH_CANDIDATES_OR_ZERO",
                "ok": candidate_count == 0 or all(inserted.get(t) == candidate_count for t in inserted),
                "candidate_count": candidate_count,
                "inserted": inserted
            },
            {
                "test_id": "T04_RAW_FEED_UNCHANGED",
                "ok": delta.get("news_raw_feed_events", 0) == 0,
                "delta": delta
            },
            {
                "test_id": "T05_NO_TRADE_FLAGS",
                "ok": bad_trade_flags == 0,
                "bad_trade_flags": bad_trade_flags
            }
        ]

        for t in tests:
            if t.get("ok") is not True:
                failures.append("test_failed:" + t["test_id"])

        return {
            "stage": stage,
            "generated_at_utc": generated_at,
            "decision": "OK_NEWS_DERIVED_LAYER_REFRESHER_V1" if not failures else "FAIL_NEWS_DERIVED_LAYER_REFRESHER_V1",
            "db_path": str(db_path),
            "write": write,
            "candidate_count": candidate_count,
            "inserted": inserted,
            "counts_before": before,
            "counts_after": after,
            "delta": delta,
            "latest": {
                "derived_before": latest_derived,
                "raw_before": latest_raw,
                "derived_after": latest_derived_after,
                "raw_after": latest_raw_after
            },
            "remaining_candidates": remaining_candidates,
            "bad_trade_flags": bad_trade_flags,
            "samples": samples,
            "tests": tests,
            "test_count": len(tests),
            "ok_count": sum(1 for t in tests if t.get("ok") is True),
            "fail_count": sum(1 for t in tests if t.get("ok") is not True),
            "authority": {
                "api_call": False,
                "network_call": False,
                "schema_change": False,
                "index_creation": False,
                "paper_trade": False,
                "live_trade": False,
                "execution_authority": False
            },
            "failures": failures,
            "warnings": warnings
        }

    except Exception as exc:
        try:
            con.rollback()
        except Exception:
            pass
        return {
            "stage": stage,
            "generated_at_utc": generated_at,
            "decision": "FAIL_NEWS_DERIVED_LAYER_REFRESHER_V1",
            "db_path": str(db_path),
            "write": write,
            "failures": ["exception:" + repr(exc)],
            "warnings": warnings
        }
    finally:
        con.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=str(DEFAULT_DB))
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--max-batch", type=int, default=250)
    ap.add_argument("--stage", default="NEWS_DERIVED_LAYER_REFRESHER_V1")
    args = ap.parse_args()
    print(json.dumps(run_refresher(args.db_path, args.write, args.max_batch, args.stage), ensure_ascii=False, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
