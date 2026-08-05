#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import re
import sqlite3
import hashlib
import subprocess

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_D_PANEL_READMODEL_FRESHNESS_NOAPI"
OUT_JSON = ROOT / "data/control/news_d_panel_readmodel_freshness_noapi_v1.json"
OUT_MD = ROOT / "reports/LATEST_NEWS_D_PANEL_READMODEL_FRESHNESS_NOAPI.md"

DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

REFS = {
    "news_a": ROOT / "data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json",
    "news_b_fix2_post": ROOT / "data/control/news_b_fix_2_post_activation_audit_noapi_v1.json",
    "news_c": ROOT / "data/control/news_c_downstream_checksum_fingerprint_noapi_v1.json",
}

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1",
    "news_runtime_freshness_v1",
]

SEARCH_ROOTS = [
    ROOT / "panel",
    ROOT / "public",
    ROOT / "static",
    ROOT / "templates",
    ROOT / "tools",
    ROOT / "data",
    ROOT / "reports",
    ROOT / "docs",
]

EXCLUDE_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    "checkpoints",
    "backups",
    "backup",
}

TEXT_EXTS = {
    ".py",
    ".json",
    ".jsonl",
    ".md",
    ".html",
    ".htm",
    ".js",
    ".ts",
    ".css",
    ".txt",
    ".service",
    ".timer",
}

NEWS_PATTERNS = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1",
    "news_runtime_freshness_v1",
    "NEWS",
    "news",
    "readmodel",
    "read_model",
    "panel",
    "freshness",
    "heartbeat",
]

COUNT_KEYS = {
    "raw": ["raw", "raw_count", "news_raw_count", "news_raw_feed_events", "news_raw_feed_events_count"],
    "match": ["match", "match_count", "news_match_count", "news_token_match_events", "news_token_match_events_count"],
    "signal": ["signal", "signal_count", "news_signal_count", "news_signal_events", "news_signal_events_count"],
    "score": ["score", "score_count", "news_score_count", "news_score_events_v1", "news_score_events_v1_count"],
    "freshness": ["freshness", "freshness_count", "news_runtime_freshness_v1", "news_runtime_freshness_v1_count"],
}


def now_utc():
    return datetime.now(timezone.utc)


def iso_now():
    return now_utc().isoformat()


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def run_cmd(args, timeout=25):
    try:
        p = subprocess.run(args, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"cmd": args, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as e:
        return {"cmd": args, "rc": None, "stdout": "", "stderr": type(e).__name__ + ":" + str(e)[:300]}


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


def sha256_bytes(path, limit=None):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            if limit:
                h.update(f.read(limit))
            else:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def parse_ts(value):
    if not value:
        return None
    try:
        s = str(value).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def age_seconds_from_iso(value):
    dt = parse_ts(value)
    if not dt:
        return None
    return max(0, int((now_utc() - dt).total_seconds()))


def file_info(path):
    try:
        st = path.stat()
        return {
            "path": rel(path),
            "exists": True,
            "is_file": path.is_file(),
            "size_bytes": st.st_size,
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            "mtime_age_seconds": max(0, int((now_utc() - datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)).total_seconds())),
            "sha256": sha256_bytes(path) if path.is_file() and st.st_size <= 5_000_000 else None,
        }
    except Exception as e:
        return {"path": rel(path), "exists": False, "error": type(e).__name__ + ":" + str(e)[:200]}


def open_db_ro():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True, timeout=8)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    return con


def db_snapshot():
    out = {"error": None, "tables": {}}
    if not DB.exists():
        out["error"] = "DB_NOT_FOUND"
        return out
    try:
        con = open_db_ro()
        cur = con.cursor()
        for table in TABLES:
            item = {
                "exists": False,
                "count": None,
                "timestamp_col": None,
                "min_ts": None,
                "max_ts": None,
                "max_ts_age_seconds": None,
                "columns": [],
                "sample_last": None,
                "error": None,
            }
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cur.fetchone() is None:
                out["tables"][table] = item
                continue
            item["exists"] = True
            cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
            item["count"] = int(cur.fetchone()["c"])
            cols = [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
            item["columns"] = cols
            ts_col = None
            for c in ["created_at_utc", "fetched_at_utc", "generated_at_utc", "updated_at_utc", "last_observed_at_utc", "published_at_utc"]:
                if c in cols:
                    ts_col = c
                    break
            item["timestamp_col"] = ts_col
            if ts_col:
                cur.execute(f"SELECT MIN({ts_col}) AS mn, MAX({ts_col}) AS mx FROM {table}")
                r = cur.fetchone()
                item["min_ts"] = r["mn"]
                item["max_ts"] = r["mx"]
                item["max_ts_age_seconds"] = age_seconds_from_iso(r["mx"])
                cur.execute(f"SELECT * FROM {table} ORDER BY {ts_col} DESC LIMIT 1")
                rr = cur.fetchone()
                item["sample_last"] = dict(rr) if rr else None
            out["tables"][table] = item
        con.close()
    except Exception as e:
        out["error"] = type(e).__name__ + ":" + str(e)[:400]
    return out


def db_counts_from_snapshot(snap):
    t = snap.get("tables", {})
    return {
        "raw": t.get("news_raw_feed_events", {}).get("count"),
        "match": t.get("news_token_match_events", {}).get("count"),
        "signal": t.get("news_signal_events", {}).get("count"),
        "score": t.get("news_score_events_v1", {}).get("count"),
        "freshness": t.get("news_runtime_freshness_v1", {}).get("count"),
    }


def should_skip(path):
    parts = set(path.parts)
    return bool(parts & EXCLUDE_DIR_NAMES)


def iter_candidate_files():
    seen = set()
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        if root.is_file():
            files = [root]
        else:
            files = []
            for p in root.rglob("*"):
                if should_skip(p):
                    continue
                if p.is_file() and p.suffix.lower() in TEXT_EXTS:
                    files.append(p)
        for p in files:
            rp = rel(p)
            if rp in seen:
                continue
            seen.add(rp)
            yield p


def read_text_limited(path, max_bytes=1_500_000):
    try:
        if path.stat().st_size > max_bytes:
            return None, "TOO_LARGE"
        return path.read_text(encoding="utf-8", errors="replace"), None
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:200]


def contains_news_signal(path, text):
    low_path = rel(path).lower()
    low_text = (text or "").lower()
    if any(x.lower() in low_path for x in ["news", "readmodel", "read_model", "panel", "freshness"]):
        return True
    hits = 0
    for p in NEWS_PATTERNS:
        if p.lower() in low_text:
            hits += 1
    return hits >= 2


def find_json_count_values(obj):
    found = {}

    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                kl = str(k).lower()
                if isinstance(v, int):
                    for label, keys in COUNT_KEYS.items():
                        if kl in [kk.lower() for kk in keys]:
                            found.setdefault(label, []).append({"path": path + [str(k)], "value": v})
                if isinstance(v, dict):
                    if "count" in v and isinstance(v.get("count"), int):
                        for label, keys in COUNT_KEYS.items():
                            if kl in [kk.lower() for kk in keys]:
                                found.setdefault(label, []).append({"path": path + [str(k), "count"], "value": v.get("count")})
                walk(v, path + [str(k)])
        elif isinstance(x, list):
            for i, v in enumerate(x[:500]):
                walk(v, path + [str(i)])

    walk(obj, [])
    return found


def score_file_role(path, text, json_obj=None):
    rp = rel(path).lower()
    low = (text or "").lower()
    score = 0
    reasons = []
    if "news" in rp:
        score += 4
        reasons.append("path_news")
    if "panel" in rp:
        score += 3
        reasons.append("path_panel")
    if "readmodel" in rp or "read_model" in rp:
        score += 4
        reasons.append("path_readmodel")
    if "freshness" in rp:
        score += 3
        reasons.append("path_freshness")
    for pat in ["news_token_match_events", "news_signal_events", "news_score_events_v1", "news_runtime_freshness_v1"]:
        if pat in low:
            score += 5
            reasons.append("contains_" + pat)
    for pat in ["match_count", "signal_count", "score_count", "raw_count", "generated_at", "created_at_utc", "heartbeat"]:
        if pat in low:
            score += 2
            reasons.append("contains_" + pat)
    if json_obj is not None:
        score += 2
        reasons.append("json_parse_ok")
        counts = find_json_count_values(json_obj)
        if counts:
            score += 3
            reasons.append("json_counts_found")
    return score, reasons[:20]


def discover_files():
    candidates = []
    json_candidates = []
    html_candidates = []
    py_candidates = []
    md_candidates = []
    for p in iter_candidate_files():
        text, err = read_text_limited(p)
        if text is None:
            continue
        if not contains_news_signal(p, text):
            continue

        json_obj = None
        json_error = None
        if p.suffix.lower() == ".json":
            try:
                json_obj = json.loads(text)
            except Exception as e:
                json_error = type(e).__name__ + ":" + str(e)[:200]

        score, reasons = score_file_role(p, text, json_obj)
        count_values = find_json_count_values(json_obj) if json_obj is not None else {}

        item = file_info(p)
        item.update({
            "role_score": score,
            "role_reasons": reasons,
            "suffix": p.suffix.lower(),
            "json_parse_ok": json_obj is not None,
            "json_parse_error": json_error,
            "json_count_values": count_values,
            "content_hits": {pat: text.lower().count(pat.lower()) for pat in NEWS_PATTERNS if pat.lower() in text.lower()},
        })

        candidates.append(item)
        if p.suffix.lower() == ".json":
            json_candidates.append(item)
        elif p.suffix.lower() in {".html", ".htm", ".js"}:
            html_candidates.append(item)
        elif p.suffix.lower() == ".py":
            py_candidates.append(item)
        elif p.suffix.lower() == ".md":
            md_candidates.append(item)

    candidates.sort(key=lambda x: (x.get("role_score", 0), x.get("mtime_utc") or ""), reverse=True)
    return {
        "all_top": candidates[:80],
        "json_top": json_candidates[:50],
        "html_js_top": html_candidates[:50],
        "python_top": py_candidates[:50],
        "markdown_top": md_candidates[:40],
        "counts": {
            "all_news_related": len(candidates),
            "json": len(json_candidates),
            "html_js": len(html_candidates),
            "python": len(py_candidates),
            "markdown": len(md_candidates),
        }
    }


def matching_count_candidate(json_candidates, db_counts):
    matches = []
    partials = []
    for item in json_candidates:
        vals = item.get("json_count_values") or {}
        candidate_counts = {}
        for label, arr in vals.items():
            unique = sorted(set(x.get("value") for x in arr if isinstance(x.get("value"), int)))
            candidate_counts[label] = unique
        score = 0
        checked = 0
        for label, dbv in db_counts.items():
            values = candidate_counts.get(label) or []
            if values:
                checked += 1
                if dbv in values:
                    score += 1
        if score >= 3:
            matches.append({"path": item.get("path"), "score": score, "checked": checked, "candidate_counts": candidate_counts, "mtime_utc": item.get("mtime_utc"), "mtime_age_seconds": item.get("mtime_age_seconds")})
        elif score > 0:
            partials.append({"path": item.get("path"), "score": score, "checked": checked, "candidate_counts": candidate_counts, "mtime_utc": item.get("mtime_utc"), "mtime_age_seconds": item.get("mtime_age_seconds")})
    matches.sort(key=lambda x: (x["score"], -1 * (x.get("mtime_age_seconds") or 10**12)), reverse=True)
    partials.sort(key=lambda x: (x["score"], -1 * (x.get("mtime_age_seconds") or 10**12)), reverse=True)
    return {"strong_matches": matches[:20], "partial_matches": partials[:20]}


def systemd_news_status():
    return {
        "timer_active": run_cmd(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"]),
        "timer_enabled": run_cmd(["systemctl", "is-enabled", "tokenoskobi-news-radar-refresh.timer"]),
        "list_timers": run_cmd(["systemctl", "list-timers", "--all", "tokenoskobi-news-radar-refresh.timer", "--no-pager"]),
    }


def freshness_eval(db_snap):
    tables = db_snap.get("tables", {})
    raw = tables.get("news_raw_feed_events", {})
    match = tables.get("news_token_match_events", {})
    signal = tables.get("news_signal_events", {})
    score = tables.get("news_score_events_v1", {})
    fresh = tables.get("news_runtime_freshness_v1", {})
    return {
        "raw_max_ts": raw.get("max_ts"),
        "raw_max_age_seconds": raw.get("max_ts_age_seconds"),
        "match_max_ts": match.get("max_ts"),
        "match_max_age_seconds": match.get("max_ts_age_seconds"),
        "signal_max_ts": signal.get("max_ts"),
        "signal_max_age_seconds": signal.get("max_ts_age_seconds"),
        "score_max_ts": score.get("max_ts"),
        "score_max_age_seconds": score.get("max_ts_age_seconds"),
        "freshness_max_ts": fresh.get("max_ts"),
        "freshness_max_age_seconds": fresh.get("max_ts_age_seconds"),
        "raw_newer_than_downstream": bool(parse_ts(raw.get("max_ts")) and parse_ts(match.get("max_ts")) and parse_ts(raw.get("max_ts")) > parse_ts(match.get("max_ts"))),
    }


def build_markdown(result):
    lines = []
    lines.append("# NEWS-D Panel Readmodel Freshness NOAPI")
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
    lines.append("## DB Counts")
    lines.append("")
    lines.append("| Layer | Count | Max TS | Age Sec |")
    lines.append("|---|---:|---|---:|")
    for table, r in result["db_snapshot"].get("tables", {}).items():
        lines.append(f"| {table} | {r.get('count')} | {r.get('max_ts')} | {r.get('max_ts_age_seconds')} |")
    lines.append("")
    lines.append("## Strong JSON Count Matches")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(result["panel_readmodel_alignment"].get("strong_matches", [])[:10], ensure_ascii=False, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("## Top News Related Files")
    lines.append("")
    lines.append("| Path | Score | Mtime UTC | Size | Reasons |")
    lines.append("|---|---:|---|---:|---|")
    for item in result["discovery"].get("all_top", [])[:30]:
        lines.append(f"| {item.get('path')} | {item.get('role_score')} | {item.get('mtime_utc')} | {item.get('size_bytes')} | {','.join(item.get('role_reasons', [])[:5])} |")
    lines.append("")
    lines.append("## Timer")
    lines.append("")
    lines.append("```text")
    lines.append(result["systemd_news"].get("list_timers", {}).get("stdout", ""))
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

    db = db_snapshot()
    db_counts = db_counts_from_snapshot(db)
    discovery = discover_files()
    alignment = matching_count_candidate(discovery.get("json_top", []), db_counts)
    sysd = systemd_news_status()
    fresh = freshness_eval(db)

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    if db.get("error"):
        add("FAIL", "DB_READ_ERROR", db.get("error"))
    else:
        add("OK", "DB_READONLY_SNAPSHOT_OK", "DB read-only snapshot alındı.")

    if db_counts.get("match") == 47 and db_counts.get("signal") == 47 and db_counts.get("score") == 47:
        add("OK", "DOWNSTREAM_COUNTS_STILL_47", "match/signal/score hâlâ 47/47/47.")
    else:
        add("FAIL", "DOWNSTREAM_COUNTS_CHANGED", f"match/signal/score={db_counts.get('match')}/{db_counts.get('signal')}/{db_counts.get('score')}")

    if (sysd.get("timer_active", {}).get("stdout") or "").strip() == "active" and (sysd.get("timer_enabled", {}).get("stdout") or "").strip() == "enabled":
        add("OK", "NEWS_TIMER_STILL_ACTIVE_ENABLED", "NEWS timer active/enabled.")
    else:
        add("FAIL", "NEWS_TIMER_NOT_ACTIVE_ENABLED", "NEWS timer active/enabled değil.")

    if discovery.get("counts", {}).get("all_news_related", 0) > 0:
        add("OK", "NEWS_PANEL_READMODEL_FILES_DISCOVERED", f"NEWS ilişkili dosya adayı bulundu: {discovery.get('counts', {}).get('all_news_related')}")
    else:
        add("WARN", "NO_NEWS_PANEL_READMODEL_FILES_DISCOVERED", "NEWS panel/readmodel adayı bulunamadı.")

    if alignment.get("strong_matches"):
        add("OK", "PANEL_READMODEL_COUNT_MATCH_FOUND", f"DB sayılarıyla eşleşen JSON/readmodel adayı bulundu: {len(alignment.get('strong_matches'))}")
    elif alignment.get("partial_matches"):
        add("WARN", "PANEL_READMODEL_PARTIAL_COUNT_MATCH_FOUND", f"Kısmi sayı eşleşmesi var: {len(alignment.get('partial_matches'))}")
    else:
        add("WARN", "PANEL_READMODEL_COUNT_MATCH_NOT_FOUND", "DB sayılarıyla güçlü JSON/readmodel count eşleşmesi bulunamadı.")

    if fresh.get("raw_newer_than_downstream"):
        add("WARN", "RAW_NEWER_THAN_DOWNSTREAM", "Raw haberler downstream match/signal/score zamanından daha yeni; downstream freshness/staleness takip edilmeli.")
    else:
        add("OK", "RAW_DOWNSTREAM_TIME_ORDER_OK", "Raw/downstream timestamp sırası kritik fark göstermiyor.")

    if fresh.get("freshness_max_age_seconds") is not None and fresh.get("raw_max_age_seconds") is not None:
        if fresh.get("freshness_max_age_seconds") > fresh.get("raw_max_age_seconds"):
            add("WARN", "FRESHNESS_HEARTBEAT_STALER_THAN_RAW", "freshness heartbeat raw max timestamp'ten daha eski.")
        else:
            add("OK", "FRESHNESS_HEARTBEAT_NOT_STALER_THAN_RAW", "freshness heartbeat raw max timestamp'ten eski görünmüyor.")
    else:
        add("WARN", "FRESHNESS_AGE_UNKNOWN", "freshness/raw age hesaplanamadı.")

    if refs.get("news_c", {}).get("decision") == "OK_NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_CLEAN":
        add("OK", "NEWS_C_REFERENCE_CLEAN", "NEWS-C clean referansı okundu.")
    else:
        add("WARN", "NEWS_C_REFERENCE_NOT_CLEAN_OR_MISSING", "NEWS-C clean referansı net değil.")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if fail_count:
        decision = "FAIL_NEWS_D_PANEL_READMODEL_FRESHNESS_BLOCKED"
        next_step = "REVIEW_NEWS_D_PANEL_READMODEL_FAILURE"
    elif warn_count:
        decision = "WARN_NEWS_D_PANEL_READMODEL_FRESHNESS_REVIEW_REQUIRED"
        next_step = "NEWS_E_REVIEW_PROMPT_AND_SEAL_PREP_NOAPI"
    else:
        decision = "OK_NEWS_D_PANEL_READMODEL_FRESHNESS_CLEAN"
        next_step = "NEWS_E_REVIEW_PROMPT_AND_SEAL_PREP_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": iso_now(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "readonly_audit": True,
            "readonly_db_open_mode": "sqlite_uri_mode_ro_query_only",
            "real_db_write": False,
            "db_schema_write": False,
            "panel_write": False,
            "readmodel_write": False,
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
        "db_snapshot": db,
        "db_counts": db_counts,
        "freshness_eval": fresh,
        "systemd_news": sysd,
        "discovery": discovery,
        "panel_readmodel_alignment": alignment,
        "summary": {
            "raw_count": db_counts.get("raw"),
            "match_count": db_counts.get("match"),
            "signal_count": db_counts.get("signal"),
            "score_count": db_counts.get("score"),
            "freshness_count": db_counts.get("freshness"),
            "raw_max_ts": fresh.get("raw_max_ts"),
            "match_max_ts": fresh.get("match_max_ts"),
            "signal_max_ts": fresh.get("signal_max_ts"),
            "score_max_ts": fresh.get("score_max_ts"),
            "freshness_max_ts": fresh.get("freshness_max_ts"),
            "raw_newer_than_downstream": fresh.get("raw_newer_than_downstream"),
            "news_related_file_count": discovery.get("counts", {}).get("all_news_related"),
            "json_candidate_count": discovery.get("counts", {}).get("json"),
            "html_js_candidate_count": discovery.get("counts", {}).get("html_js"),
            "python_candidate_count": discovery.get("counts", {}).get("python"),
            "strong_panel_readmodel_count_matches": len(alignment.get("strong_matches", [])),
            "partial_panel_readmodel_count_matches": len(alignment.get("partial_matches", [])),
            "timer_active": (sysd.get("timer_active", {}).get("stdout") or "").strip(),
            "timer_enabled": (sysd.get("timer_enabled", {}).get("stdout") or "").strip(),
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
        "findings": findings,
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_markdown(result))

    print("OK_NEWS_D_PANEL_READMODEL_FRESHNESS_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + str(OUT_JSON.relative_to(ROOT)))
    print("REPORT=" + str(OUT_MD.relative_to(ROOT)))
    print("RAW=" + str(db_counts.get("raw")))
    print("MATCH=" + str(db_counts.get("match")))
    print("SIGNAL=" + str(db_counts.get("signal")))
    print("SCORE=" + str(db_counts.get("score")))
    print("FRESHNESS=" + str(db_counts.get("freshness")))
    print("TIMER_ACTIVE=" + str(result["summary"]["timer_active"]))
    print("TIMER_ENABLED=" + str(result["summary"]["timer_enabled"]))
    print("NEWS_RELATED_FILE_COUNT=" + str(result["summary"]["news_related_file_count"]))
    print("STRONG_PANEL_READMODEL_COUNT_MATCHES=" + str(result["summary"]["strong_panel_readmodel_count_matches"]))
    print("PARTIAL_PANEL_READMODEL_COUNT_MATCHES=" + str(result["summary"]["partial_panel_readmodel_count_matches"]))
    print("RAW_NEWER_THAN_DOWNSTREAM=" + str(result["summary"]["raw_newer_than_downstream"]))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
