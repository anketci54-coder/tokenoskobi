#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import sqlite3
import hashlib
import subprocess
from collections import Counter, defaultdict

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_NOAPI"
OUT_JSON = ROOT / "data/control/news_c_downstream_checksum_fingerprint_noapi_v1.json"
OUT_MD = ROOT / "reports/LATEST_NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_NOAPI.md"

DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

REFS = {
    "news_a": ROOT / "data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json",
    "news_b": ROOT / "data/control/news_b_runner_timer_journal_argv_audit_noapi_v1.json",
    "news_b_fix1": ROOT / "data/control/news_b_fix_1_systemd_stdout_stderr_path_targeted_apply_v1.json",
    "news_b_fix1_post": ROOT / "data/control/news_b_fix_1_post_apply_audit_noapi_v1.json",
    "news_b_fix2": ROOT / "data/control/news_b_fix_2_timer_activation_targeted_apply_v1.json",
    "news_b_fix2_post": ROOT / "data/control/news_b_fix_2_post_activation_audit_noapi_v1.json",
}

TABLES = {
    "raw": "news_raw_feed_events",
    "match": "news_token_match_events",
    "signal": "news_signal_events",
    "score": "news_score_events_v1",
    "freshness": "news_runtime_freshness_v1",
}

EXPECTED_DOWNSTREAM_COUNT = 47


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def run_cmd(args, timeout=20):
    try:
        p = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {"cmd": args, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as e:
        return {"cmd": args, "rc": None, "stdout": "", "stderr": type(e).__name__ + ":" + str(e)[:300]}


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_json(path):
    if not path.exists():
        return None, "MISSING"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:300]


def safe_write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    with open(tmp, encoding="utf-8") as f:
        json.load(f)
    os.replace(tmp, path)


def safe_write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def open_ro_db():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True, timeout=8)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    return con


def table_exists(cur, table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def table_columns(cur, table):
    return [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]


def table_count(cur, table):
    cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
    return int(cur.fetchone()["c"])


def max_ts(cur, table, cols):
    for c in ["created_at_utc", "fetched_at_utc", "generated_at_utc", "updated_at_utc", "last_observed_at_utc", "published_at_utc"]:
        if c in cols:
            cur.execute(f"SELECT MIN({c}) AS mn, MAX({c}) AS mx FROM {table}")
            r = cur.fetchone()
            return {"timestamp_col": c, "min_ts": r["mn"], "max_ts": r["mx"]}
    return {"timestamp_col": None, "min_ts": None, "max_ts": None}


def fetch_rows(cur, table, cols):
    order_candidates = [
        "match_uid",
        "signal_uid",
        "score_uid",
        "news_uid",
        "created_at_utc",
        "fetched_at_utc",
    ]
    order_cols = [c for c in order_candidates if c in cols]
    order_sql = ", ".join(order_cols) if order_cols else "rowid"
    cur.execute(f"SELECT * FROM {table} ORDER BY {order_sql}")
    return [dict(r) for r in cur.fetchall()]


def canonical_key(row):
    return {
        "news_uid": row.get("news_uid"),
        "token_uid": row.get("token_uid"),
        "pair_uid": row.get("pair_uid"),
        "symbol": row.get("symbol"),
        "chain": row.get("chain"),
    }


def canonical_key_tuple(row):
    k = canonical_key(row)
    return (k.get("news_uid"), k.get("token_uid"), k.get("pair_uid"), k.get("symbol"), k.get("chain"))


def row_digest(row, mode):
    if mode == "full":
        return sha256_text(stable_json(row))
    if mode == "canonical":
        return sha256_text(stable_json(canonical_key(row)))
    return sha256_text(stable_json(row))


def collection_digest(rows, mode):
    digests = [row_digest(r, mode) for r in rows]
    return sha256_text(stable_json(sorted(digests)))


def duplicate_report(rows, mode):
    if mode == "canonical":
        vals = [stable_json(canonical_key(r)) for r in rows]
    else:
        vals = [stable_json(r) for r in rows]
    c = Counter(vals)
    dup = [{"key": k, "count": v} for k, v in c.items() if v > 1]
    return {"duplicate_group_count": len(dup), "duplicate_row_total": sum(x["count"] for x in dup), "sample": dup[:10]}


def nonzero_flag_count(rows, col):
    n = 0
    for r in rows:
        v = r.get(col)
        if v in (1, "1", True, "true", "TRUE", "yes", "YES"):
            n += 1
    return n


def sample_keys(rows, limit=8):
    out = []
    for r in rows[:limit]:
        item = canonical_key(r)
        for extra in ["match_uid", "signal_uid", "score_uid", "source_match_uid", "signal_type", "importance_label", "risk_label", "fusion_label"]:
            if extra in r:
                item[extra] = r.get(extra)
        out.append(item)
    return out


def build_markdown(result):
    lines = []
    lines.append("# NEWS-C Downstream Checksum Fingerprint NOAPI")
    lines.append("")
    lines.append(f"- stage: `{STAGE}`")
    lines.append(f"- generated_at_utc: `{result['generated_at_utc']}`")
    lines.append(f"- decision: `{result['decision']}`")
    lines.append(f"- next_step: `{result['next_step']}`")
    lines.append("")
    lines.append("## Authority")
    lines.append("")
    for k, v in result["authority"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for k, v in result["summary"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for f in result["findings"]:
        lines.append(f"- `{f['level']}` {f['code']}: {f['message']}")
    lines.append("")
    lines.append("## Table Snapshots")
    lines.append("")
    lines.append("| Table | Exists | Count | Timestamp Col | Min TS | Max TS |")
    lines.append("|---|---:|---:|---|---|---|")
    for name, r in result["tables"].items():
        lines.append(f"| {r.get('table')} | {r.get('exists')} | {r.get('count')} | {r.get('timestamp_col')} | {r.get('min_ts')} | {r.get('max_ts')} |")
    lines.append("")
    lines.append("## Fingerprints")
    lines.append("")
    lines.append("| Layer | Full Digest | Canonical Digest |")
    lines.append("|---|---|---|")
    for k, r in result["fingerprints"].items():
        lines.append(f"| {k} | `{r.get('full_collection_sha256')}` | `{r.get('canonical_collection_sha256')}` |")
    lines.append("")
    lines.append("## Relation Audit")
    lines.append("")
    for k, v in result["relation_audit"].items():
        if not isinstance(v, (dict, list)):
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Duplicate Audit")
    lines.append("")
    for k, v in result["duplicate_audit"].items():
        if isinstance(v, dict):
            lines.append(f"- {k}: canonical_duplicate_groups=`{v.get('canonical', {}).get('duplicate_group_count')}`, full_duplicate_groups=`{v.get('full', {}).get('duplicate_group_count')}`")
    lines.append("")
    lines.append("## Trade Authority Flags")
    lines.append("")
    for k, v in result["trade_authority_flags"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Sample Keys")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(result["sample_keys"], ensure_ascii=False, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    refs = {}
    for name, path in REFS.items():
        obj, err = read_json(path)
        refs[name] = {
            "path": str(path),
            "read_error": err,
            "decision": obj.get("decision") if isinstance(obj, dict) else None,
            "next_step": obj.get("next_step") if isinstance(obj, dict) else None,
            "generated_at_utc": obj.get("generated_at_utc") if isinstance(obj, dict) else None,
        }

    con = open_ro_db()
    cur = con.cursor()

    table_meta = {}
    rows = {}

    for name, table in TABLES.items():
        exists = table_exists(cur, table)
        meta = {
            "layer": name,
            "table": table,
            "exists": exists,
            "count": None,
            "columns": [],
            "timestamp_col": None,
            "min_ts": None,
            "max_ts": None,
            "error": None,
        }
        if exists:
            cols = table_columns(cur, table)
            meta["columns"] = cols
            meta["count"] = table_count(cur, table)
            meta.update(max_ts(cur, table, cols))
            rows[name] = fetch_rows(cur, table, cols)
        else:
            rows[name] = []
        table_meta[name] = meta

    raw_news_uids = set(r.get("news_uid") for r in rows["raw"] if r.get("news_uid"))
    match_uids = set(r.get("match_uid") for r in rows["match"] if r.get("match_uid"))
    signal_uids = set(r.get("signal_uid") for r in rows["signal"] if r.get("signal_uid"))
    score_uids = set(r.get("score_uid") for r in rows["score"] if r.get("score_uid"))

    match_keys = set(canonical_key_tuple(r) for r in rows["match"])
    signal_keys = set(canonical_key_tuple(r) for r in rows["signal"])
    score_keys = set(canonical_key_tuple(r) for r in rows["score"])

    signal_source_refs = [r.get("source_match_uid") for r in rows["signal"] if "source_match_uid" in r]
    signal_missing_source_match_uid = [r for r in rows["signal"] if "source_match_uid" in r and not r.get("source_match_uid")]
    signal_bad_source_refs = [x for x in signal_source_refs if x and x not in match_uids]

    match_without_signal_key = sorted(list(match_keys - signal_keys))
    signal_without_match_key = sorted(list(signal_keys - match_keys))
    signal_without_score_key = sorted(list(signal_keys - score_keys))
    score_without_signal_key = sorted(list(score_keys - signal_keys))
    match_without_score_key = sorted(list(match_keys - score_keys))
    score_without_match_key = sorted(list(score_keys - match_keys))

    downstream_news_uids = {
        "match": set(r.get("news_uid") for r in rows["match"] if r.get("news_uid")),
        "signal": set(r.get("news_uid") for r in rows["signal"] if r.get("news_uid")),
        "score": set(r.get("news_uid") for r in rows["score"] if r.get("news_uid")),
    }
    raw_link_missing = {
        k: sorted(list(v - raw_news_uids))[:50]
        for k, v in downstream_news_uids.items()
    }
    raw_link_missing_count = {k: len(v - raw_news_uids) for k, v in downstream_news_uids.items()}

    fingerprints = {}
    for layer in ["match", "signal", "score"]:
        fingerprints[layer] = {
            "row_count": len(rows[layer]),
            "full_collection_sha256": collection_digest(rows[layer], "full"),
            "canonical_collection_sha256": collection_digest(rows[layer], "canonical"),
            "first_5_row_sha256": [row_digest(r, "full") for r in rows[layer][:5]],
        }

    duplicate_audit = {}
    for layer in ["match", "signal", "score"]:
        duplicate_audit[layer] = {
            "canonical": duplicate_report(rows[layer], "canonical"),
            "full": duplicate_report(rows[layer], "full"),
        }

    trade_flags = {
        "match_trade_signal_nonzero": nonzero_flag_count(rows["match"], "trade_signal"),
        "match_paper_signal_nonzero": nonzero_flag_count(rows["match"], "paper_signal"),
        "match_write_allowed_nonzero": nonzero_flag_count(rows["match"], "write_allowed"),
    }

    relation_audit = {
        "match_uid_count": len(match_uids),
        "signal_uid_count": len(signal_uids),
        "score_uid_count": len(score_uids),
        "signal_source_match_uid_present_count": len([x for x in signal_source_refs if x]),
        "signal_missing_source_match_uid_count": len(signal_missing_source_match_uid),
        "signal_bad_source_match_ref_count": len(signal_bad_source_refs),
        "match_without_signal_key_count": len(match_without_signal_key),
        "signal_without_match_key_count": len(signal_without_match_key),
        "signal_without_score_key_count": len(signal_without_score_key),
        "score_without_signal_key_count": len(score_without_signal_key),
        "match_without_score_key_count": len(match_without_score_key),
        "score_without_match_key_count": len(score_without_match_key),
        "raw_link_missing_count": raw_link_missing_count,
        "samples": {
            "signal_bad_source_refs": signal_bad_source_refs[:20],
            "match_without_signal_key": match_without_signal_key[:10],
            "signal_without_match_key": signal_without_match_key[:10],
            "signal_without_score_key": signal_without_score_key[:10],
            "score_without_signal_key": score_without_signal_key[:10],
            "match_without_score_key": match_without_score_key[:10],
            "score_without_match_key": score_without_match_key[:10],
            "raw_link_missing": raw_link_missing,
        },
    }

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    if DB.exists():
        add("OK", "DB_EXISTS", f"DB mevcut: {DB}")
    else:
        add("FAIL", "DB_MISSING", f"DB yok: {DB}")

    missing_tables = [name for name, meta in table_meta.items() if not meta["exists"]]
    if missing_tables:
        add("FAIL", "NEWS_TABLES_MISSING", f"Eksik tablolar: {missing_tables}")
    else:
        add("OK", "NEWS_TABLES_EXIST", "NEWS raw/match/signal/score/freshness tabloları mevcut.")

    raw_count = table_meta["raw"]["count"]
    match_count = table_meta["match"]["count"]
    signal_count = table_meta["signal"]["count"]
    score_count = table_meta["score"]["count"]
    freshness_count = table_meta["freshness"]["count"]

    if match_count == EXPECTED_DOWNSTREAM_COUNT and signal_count == EXPECTED_DOWNSTREAM_COUNT and score_count == EXPECTED_DOWNSTREAM_COUNT:
        add("OK", "DOWNSTREAM_47_47_47_CONFIRMED", "match/signal/score = 47/47/47.")
    else:
        add("FAIL", "DOWNSTREAM_COUNT_NOT_EXPECTED", f"match/signal/score={match_count}/{signal_count}/{score_count}")

    if isinstance(raw_count, int) and raw_count >= 269:
        add("OK", "RAW_COUNT_CURRENT_OR_HIGHER", f"Raw count: {raw_count}")
    else:
        add("WARN", "RAW_COUNT_REVIEW", f"Raw count review: {raw_count}")

    if relation_audit["signal_bad_source_match_ref_count"] == 0:
        add("OK", "SIGNAL_SOURCE_MATCH_REFS_VALID", "signal.source_match_uid referansları match_uid seti içinde.")
    else:
        add("FAIL", "SIGNAL_SOURCE_MATCH_REFS_BROKEN", f"Broken source_match_uid count: {relation_audit['signal_bad_source_match_ref_count']}")

    if relation_audit["signal_missing_source_match_uid_count"] == 0:
        add("OK", "SIGNAL_SOURCE_MATCH_UID_PRESENT", "Tüm signal satırlarında source_match_uid var.")
    else:
        add("WARN", "SIGNAL_SOURCE_MATCH_UID_MISSING", f"source_match_uid boş signal count: {relation_audit['signal_missing_source_match_uid_count']}")

    if relation_audit["match_without_signal_key_count"] == 0 and relation_audit["signal_without_match_key_count"] == 0:
        add("OK", "MATCH_SIGNAL_CANONICAL_KEYS_ALIGNED", "match ↔ signal canonical key hizası temiz.")
    else:
        add("FAIL", "MATCH_SIGNAL_CANONICAL_KEY_MISMATCH", "match ↔ signal canonical key kopukluğu var.")

    if relation_audit["signal_without_score_key_count"] == 0 and relation_audit["score_without_signal_key_count"] == 0:
        add("OK", "SIGNAL_SCORE_CANONICAL_KEYS_ALIGNED", "signal ↔ score canonical key hizası temiz.")
    else:
        add("FAIL", "SIGNAL_SCORE_CANONICAL_KEY_MISMATCH", "signal ↔ score canonical key kopukluğu var.")

    if relation_audit["match_without_score_key_count"] == 0 and relation_audit["score_without_match_key_count"] == 0:
        add("OK", "MATCH_SCORE_CANONICAL_KEYS_ALIGNED", "match ↔ score canonical key hizası temiz.")
    else:
        add("FAIL", "MATCH_SCORE_CANONICAL_KEY_MISMATCH", "match ↔ score canonical key kopukluğu var.")

    if all(v == 0 for v in raw_link_missing_count.values()):
        add("OK", "DOWNSTREAM_RAW_NEWS_LINKS_VALID", "Downstream news_uid değerleri raw tabloya bağlı.")
    else:
        add("FAIL", "DOWNSTREAM_RAW_NEWS_LINKS_BROKEN", f"Raw link missing: {raw_link_missing_count}")

    duplicate_fail = False
    duplicate_warn = False
    for layer in ["match", "signal", "score"]:
        if duplicate_audit[layer]["full"]["duplicate_group_count"] > 0:
            duplicate_fail = True
        if duplicate_audit[layer]["canonical"]["duplicate_group_count"] > 0:
            duplicate_warn = True

    if not duplicate_fail:
        add("OK", "NO_FULL_ROW_DUPLICATES", "Full row duplicate yok.")
    else:
        add("FAIL", "FULL_ROW_DUPLICATES_FOUND", "Full row duplicate bulundu.")

    if not duplicate_warn:
        add("OK", "NO_CANONICAL_KEY_DUPLICATES", "Canonical key duplicate yok.")
    else:
        add("WARN", "CANONICAL_KEY_DUPLICATES_FOUND", "Canonical key duplicate bulundu; gözden geçir.")

    if trade_flags["match_trade_signal_nonzero"] == 0 and trade_flags["match_paper_signal_nonzero"] == 0:
        add("OK", "NO_TRADE_OR_PAPER_SIGNAL_AUTHORITY", "trade_signal/paper_signal nonzero değil.")
    else:
        add("FAIL", "TRADE_OR_PAPER_SIGNAL_NONZERO", f"trade/paper nonzero: {trade_flags}")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if fail_count:
        decision = "FAIL_NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_BLOCKED"
        next_step = "REVIEW_NEWS_C_DOWNSTREAM_RELATION_FAILURE"
    elif warn_count:
        decision = "WARN_NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_REVIEW_REQUIRED"
        next_step = "NEWS_D_PANEL_READMODEL_FRESHNESS_NOAPI"
    else:
        decision = "OK_NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_CLEAN"
        next_step = "NEWS_D_PANEL_READMODEL_FRESHNESS_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": utc_now(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "readonly_db_open_mode": "sqlite_uri_mode_ro_query_only",
            "real_db_write": False,
            "db_schema_write": False,
            "panel_write": False,
            "runner_code_change": False,
            "matcher_code_change": False,
            "systemd_change": False,
            "timer_change": False,
            "service_change": False,
            "boot_update": False,
            "runtime_update": False,
            "external_api_call": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "repo_artifact_write": True,
        },
        "references": refs,
        "tables": table_meta,
        "fingerprints": fingerprints,
        "relation_audit": relation_audit,
        "duplicate_audit": duplicate_audit,
        "trade_authority_flags": trade_flags,
        "sample_keys": {
            "match": sample_keys(rows["match"]),
            "signal": sample_keys(rows["signal"]),
            "score": sample_keys(rows["score"]),
        },
        "summary": {
            "raw_count": raw_count,
            "match_count": match_count,
            "signal_count": signal_count,
            "score_count": score_count,
            "freshness_count": freshness_count,
            "match_uid_count": len(match_uids),
            "signal_uid_count": len(signal_uids),
            "score_uid_count": len(score_uids),
            "signal_bad_source_match_ref_count": relation_audit["signal_bad_source_match_ref_count"],
            "signal_missing_source_match_uid_count": relation_audit["signal_missing_source_match_uid_count"],
            "match_signal_mismatch_total": relation_audit["match_without_signal_key_count"] + relation_audit["signal_without_match_key_count"],
            "signal_score_mismatch_total": relation_audit["signal_without_score_key_count"] + relation_audit["score_without_signal_key_count"],
            "match_score_mismatch_total": relation_audit["match_without_score_key_count"] + relation_audit["score_without_match_key_count"],
            "raw_link_missing_total": sum(raw_link_missing_count.values()),
            "full_duplicate_group_total": sum(duplicate_audit[layer]["full"]["duplicate_group_count"] for layer in ["match", "signal", "score"]),
            "canonical_duplicate_group_total": sum(duplicate_audit[layer]["canonical"]["duplicate_group_count"] for layer in ["match", "signal", "score"]),
            "trade_signal_nonzero": trade_flags["match_trade_signal_nonzero"],
            "paper_signal_nonzero": trade_flags["match_paper_signal_nonzero"],
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
        "findings": findings,
    }

    con.close()

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_markdown(result))

    print("OK_NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + str(OUT_JSON.relative_to(ROOT)))
    print("REPORT=" + str(OUT_MD.relative_to(ROOT)))
    print("RAW=" + str(raw_count))
    print("MATCH=" + str(match_count))
    print("SIGNAL=" + str(signal_count))
    print("SCORE=" + str(score_count))
    print("FRESHNESS=" + str(freshness_count))
    print("MATCH_SIGNAL_MISMATCH_TOTAL=" + str(result["summary"]["match_signal_mismatch_total"]))
    print("SIGNAL_SCORE_MISMATCH_TOTAL=" + str(result["summary"]["signal_score_mismatch_total"]))
    print("RAW_LINK_MISSING_TOTAL=" + str(result["summary"]["raw_link_missing_total"]))
    print("FULL_DUPLICATE_GROUP_TOTAL=" + str(result["summary"]["full_duplicate_group_total"]))
    print("CANONICAL_DUPLICATE_GROUP_TOTAL=" + str(result["summary"]["canonical_duplicate_group_total"]))
    print("TRADE_SIGNAL_NONZERO=" + str(result["summary"]["trade_signal_nonzero"]))
    print("PAPER_SIGNAL_NONZERO=" + str(result["summary"]["paper_signal_nonzero"]))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
