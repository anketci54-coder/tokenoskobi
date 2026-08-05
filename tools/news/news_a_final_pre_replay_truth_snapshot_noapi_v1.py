#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import sqlite3
import subprocess
import hashlib
import re

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_A_FINAL_PRE_REPLAY_TRUTH_SNAPSHOT_NOAPI"
OUT_JSON = ROOT / "data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json"
OUT_MD = ROOT / "reports/LATEST_NEWS_A_FINAL_PRE_REPLAY_TRUTH_SNAPSHOT_NOAPI.md"

NEWS_TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1",
    "news_runtime_freshness_v1",
]

DB_CANDIDATES = [
    ROOT / "data/tokenoskobi_clean_v1.sqlite",
    ROOT / "data/tokenoskobi_v1.sqlite",
    ROOT / "data/tokenoskobi.sqlite",
    ROOT / "tokenoskobi.sqlite",
]

STATE_JSONS = {
    "runtime": ROOT / "PROJECT_RUNTIME.json",
    "boot": ROOT / "PROJECT_BOOT.json",
    "latest_machine_state": ROOT / "data/control/latest_tk_machine_state.json",
    "n18_n19_n20_real_apply": ROOT / "data/control/n18_n19_n20_news_real_apply_v1.json",
}

STATE_TEXTS = {
    "project_master_state_root": ROOT / "PROJECT_MASTER_STATE.md",
    "project_handoff_root": ROOT / "PROJECT_HANDOFF.md",
    "master_state_06": ROOT / "06_PROJECT_MASTER_STATE.md",
    "handoff_07": ROOT / "07_PROJECT_HANDOFF.md",
    "almanac_04": ROOT / "04_ALMANAC.md",
    "latest_tk_ai_handoff": ROOT / "reports/LATEST_TK_AI_HANDOFF.md",
}

PANEL_FILES = {
    "news": ROOT / "active_panel_8096/current/data/news_center_live_readmodel_v1.json",
    "command": ROOT / "active_panel_8096/current/data/command_center_live_readmodel_v1.json",
}

SYSTEMD_UNITS = [
    "tokenoskobi-news-radar-refresh.timer",
    "tokenoskobi-news-radar-refresh.service",
]

LOG_FILES = [
    ROOT / "logs/news_radar/news_radar_refresh.log",
    ROOT / "logs/news_radar/news_radar_refresh.err.log",
]


def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat()


def parse_dt(value):
    if not value:
        return None
    try:
        s = str(value).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None


def sha256_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


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


def run_cmd(args, timeout=12):
    try:
        p = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "cmd": args,
            "rc": p.returncode,
            "stdout": p.stdout.strip(),
            "stderr": p.stderr.strip(),
        }
    except Exception as e:
        return {
            "cmd": args,
            "rc": None,
            "stdout": "",
            "stderr": type(e).__name__ + ":" + str(e)[:300],
        }


def find_values_by_key(obj, wanted_keys):
    hits = []

    def walk(x, path=""):
        if isinstance(x, dict):
            for k, v in x.items():
                kp = f"{path}.{k}" if path else str(k)
                if str(k) in wanted_keys:
                    hits.append({"path": kp, "value": v})
                walk(v, kp)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")

    walk(obj)
    return hits


def extract_news_counts(obj):
    if obj is None:
        return {}
    counts = {t: [] for t in NEWS_TABLES}

    def walk(x, path=""):
        if isinstance(x, dict):
            for k, v in x.items():
                kp = f"{path}.{k}" if path else str(k)
                if str(k) in NEWS_TABLES and isinstance(v, int):
                    counts[str(k)].append({"path": kp, "value": v})
                walk(v, kp)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")

    walk(obj)
    return {k: v for k, v in counts.items() if v}


def select_db():
    for db in DB_CANDIDATES:
        if not db.exists() or not db.is_file():
            continue
        try:
            con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True, timeout=5)
            con.execute("PRAGMA query_only=ON")
            cur = con.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='news_raw_feed_events'"
            )
            ok = cur.fetchone() is not None
            con.close()
            if ok:
                return db
        except Exception:
            continue
    for db in DB_CANDIDATES:
        if db.exists() and db.is_file():
            return db
    return None


def table_snapshot(db, table):
    row = {
        "table": table,
        "exists": False,
        "count": None,
        "columns": [],
        "timestamp_col": None,
        "max_ts": None,
        "readonly_open": True,
        "error": None,
    }
    if db is None:
        row["error"] = "NO_DB_SELECTED"
        return row
    try:
        con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True, timeout=5)
        con.execute("PRAGMA query_only=ON")
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if cur.fetchone() is None:
            con.close()
            return row
        row["exists"] = True
        cols = [x[1] for x in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        row["columns"] = cols
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        row["count"] = int(cur.fetchone()[0])
        ts_candidates = [
            "created_at_utc",
            "updated_at_utc",
            "generated_at_utc",
            "fetched_at_utc",
            "published_at_utc",
            "scored_at_utc",
            "observed_at_utc",
            "last_fetch_at_utc",
            "last_update_utc",
            "event_time_utc",
            "event_ts_utc",
            "timestamp",
            "ts",
        ]
        for c in ts_candidates:
            if c in cols:
                cur.execute(f"SELECT MAX({c}) FROM {table}")
                row["timestamp_col"] = c
                row["max_ts"] = cur.fetchone()[0]
                break
        con.close()
        return row
    except Exception as e:
        row["readonly_open"] = False
        row["error"] = type(e).__name__ + ":" + str(e)[:300]
        return row


def db_sidecars(db):
    if db is None:
        return []
    paths = [db, Path(str(db) + "-wal"), Path(str(db) + "-shm"), Path(str(db) + "-journal")]
    rows = []
    for p in paths:
        rows.append({
            "path": str(p),
            "exists": p.exists(),
            "size_bytes": p.stat().st_size if p.exists() else 0,
            "mtime_utc": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat() if p.exists() else None,
            "sha256": sha256_file(p) if p.exists() and p.is_file() and p.stat().st_size <= 50_000_000 else None,
        })
    return rows


def systemd_snapshot():
    out = {}
    for unit in SYSTEMD_UNITS:
        out[unit] = {
            "is_active": run_cmd(["systemctl", "is-active", unit]),
            "is_enabled": run_cmd(["systemctl", "is-enabled", unit]),
            "show": run_cmd([
                "systemctl",
                "show",
                unit,
                "-p", "ActiveState",
                "-p", "SubState",
                "-p", "Result",
                "-p", "ExecMainStatus",
                "-p", "NRestarts",
                "-p", "FragmentPath",
                "-p", "UnitFileState",
                "-p", "ExecStart",
            ]),
        }
    out["list_timers"] = run_cmd([
        "systemctl",
        "list-timers",
        "--all",
        "tokenoskobi-news-radar-refresh.timer",
        "--no-pager",
    ])
    return out


def journal_summary():
    cmd = [
        "journalctl",
        "-u",
        "tokenoskobi-news-radar-refresh.service",
        "-n",
        "160",
        "--no-pager",
        "--output=short-iso",
    ]
    r = run_cmd(cmd, timeout=20)
    text = (r.get("stdout") or "") + "\n" + (r.get("stderr") or "")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    lowered = text.lower()
    interesting = []
    terms = ["invalidargument", "rc=2", "status=2", "return_rc", "postprocess", "traceback", "error", "failed", "finished successfully"]
    for ln in lines:
        low = ln.lower()
        if any(t in low for t in terms):
            safe = ln.replace("PASS_", "HISTORICAL_OK_LABEL_").replace("FINAL_GATE=PASS", "FINAL_GATE=HISTORICAL_OK_LABEL")
            interesting.append(safe[-500:])
    return {
        "cmd_rc": r.get("rc"),
        "line_count": len(lines),
        "invalidargument_count": lowered.count("invalidargument"),
        "rc2_count": lowered.count("rc=2") + lowered.count("status=2"),
        "return_rc_count": lowered.count("return_rc"),
        "postprocess_count": lowered.count("postprocess"),
        "traceback_count": lowered.count("traceback"),
        "error_count": lowered.count("error"),
        "failed_count": lowered.count("failed"),
        "finished_successfully_count": lowered.count("finished successfully"),
        "interesting_lines_tail": interesting[-20:],
    }


def log_file_summary():
    rows = []
    for p in LOG_FILES:
        item = {
            "path": str(p),
            "exists": p.exists(),
            "size_bytes": p.stat().st_size if p.exists() else 0,
            "mtime_utc": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat() if p.exists() else None,
            "invalidargument_count": 0,
            "rc2_count": 0,
            "postprocess_count": 0,
            "return_rc_count": 0,
            "traceback_count": 0,
            "error_count": 0,
        }
        if p.exists() and p.is_file():
            try:
                text = p.read_text(encoding="utf-8", errors="replace")[-300000:]
                low = text.lower()
                item["invalidargument_count"] = low.count("invalidargument")
                item["rc2_count"] = low.count("rc=2") + low.count("status=2")
                item["postprocess_count"] = low.count("postprocess")
                item["return_rc_count"] = low.count("return_rc")
                item["traceback_count"] = low.count("traceback")
                item["error_count"] = low.count("error")
            except Exception as e:
                item["error"] = type(e).__name__ + ":" + str(e)[:200]
        rows.append(item)
    return rows


def panel_snapshot():
    rows = {}
    now = utc_now()
    for name, path in PANEL_FILES.items():
        obj, err = read_json(path)
        generated_hits = find_values_by_key(obj, {"generated_at_utc"}) if obj is not None else []
        generated_at = generated_hits[0]["value"] if generated_hits else None
        generated_dt = parse_dt(generated_at)
        mtime_dt = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) if path.exists() else None
        generated_age_sec = None
        mtime_age_sec = None
        if generated_dt:
            generated_age_sec = int((now - generated_dt).total_seconds())
        if mtime_dt:
            mtime_age_sec = int((now - mtime_dt).total_seconds())

        if generated_age_sec is None:
            freshness = "UNKNOWN_TIMESTAMP"
        elif generated_age_sec <= 300:
            freshness = "FRESH_LE_5_MIN"
        elif generated_age_sec <= 3600:
            freshness = "STALE_WARNING_5_TO_60_MIN"
        else:
            freshness = "STALE_CRITICAL_GT_60_MIN"

        stale_data_fresh_file = False
        if generated_age_sec is not None and mtime_age_sec is not None:
            stale_data_fresh_file = generated_age_sec > 3600 and mtime_age_sec <= 300

        rows[name] = {
            "path": str(path),
            "exists": path.exists(),
            "parse_ok": obj is not None,
            "parse_error": err,
            "generated_at_utc": generated_at,
            "file_mtime_utc": mtime_dt.isoformat() if mtime_dt else None,
            "generated_age_sec": generated_age_sec,
            "mtime_age_sec": mtime_age_sec,
            "freshness_status": freshness,
            "stale_data_fresh_file": stale_data_fresh_file,
            "decision": obj.get("decision") if isinstance(obj, dict) else None,
            "sha256": sha256_file(path) if path.exists() else None,
        }
    return rows


def state_text_summary():
    rows = {}
    for name, path in STATE_TEXTS.items():
        if not path.exists():
            rows[name] = {"path": str(path), "exists": False}
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        head = "\n".join(text.splitlines()[:80])
        rows[name] = {
            "path": str(path),
            "exists": True,
            "size_bytes": path.stat().st_size,
            "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            "sha256": sha256_file(path),
            "mentions_news_runtime_stabilization": "NEWS_RUNTIME_STABILIZATION" in head,
            "mentions_era52": "ERA52" in head,
            "mentions_stable_sealed": "STABLE_SEALED" in head,
            "head_news_lines": [ln for ln in head.splitlines() if "NEWS" in ln or "ERA52" in ln][:20],
        }
    return rows


def build_markdown(result):
    db_counts = {r["table"]: r.get("count") for r in result["db"]["table_snapshots"]}
    boot_counts = result["state"]["json_counts"].get("boot", {})
    runtime_counts = result["state"]["json_counts"].get("runtime", {})

    def first_count(count_obj, table):
        vals = count_obj.get(table) or []
        if not vals:
            return "not_found"
        return vals[0].get("value")

    lines = []
    lines.append("# NEWS-A Final Pre-Replay Truth Snapshot NOAPI")
    lines.append("")
    lines.append(f"- stage: `{STAGE}`")
    lines.append(f"- generated_at_utc: `{result['generated_at_utc']}`")
    lines.append(f"- decision: `{result['decision']}`")
    lines.append(f"- selected_db: `{result['db']['selected_db']}`")
    lines.append("")
    lines.append("## Authority")
    lines.append("")
    for k, v in result["authority"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Boot / Runtime / Current DB Drift Table")
    lines.append("")
    lines.append("| Metric | PROJECT_BOOT | PROJECT_RUNTIME | Current DB | Delta DB-Boot | Drift |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for t in NEWS_TABLES:
        boot_v = first_count(boot_counts, t)
        runtime_v = first_count(runtime_counts, t)
        db_v = db_counts.get(t)
        delta = "n/a"
        drift = "UNKNOWN"
        if isinstance(boot_v, int) and isinstance(db_v, int):
            delta = db_v - boot_v
            drift = "YES" if delta != 0 else "NO"
        elif db_v is not None and boot_v == "not_found":
            drift = "BOOT_COUNT_NOT_FOUND"
        lines.append(f"| {t} | {boot_v} | {runtime_v} | {db_v} | {delta} | {drift} |")
    lines.append("")
    lines.append("## DB Snapshot")
    lines.append("")
    lines.append("| Table | Exists | Count | Timestamp Col | Max TS | Error |")
    lines.append("|---|---:|---:|---|---|---|")
    for r in result["db"]["table_snapshots"]:
        lines.append(f"| {r['table']} | {r['exists']} | {r.get('count')} | {r.get('timestamp_col')} | {r.get('max_ts')} | {r.get('error')} |")
    lines.append("")
    lines.append("## Backup Check")
    lines.append("")
    b = result["backup"]
    lines.append(f"- backup_path: `{b.get('backup_path')}`")
    lines.append(f"- exists: `{b.get('exists')}`")
    lines.append(f"- size_bytes: `{b.get('size_bytes')}`")
    lines.append("")
    lines.append("## Systemd Snapshot")
    lines.append("")
    for unit, data in result["systemd"].items():
        if unit == "list_timers":
            continue
        lines.append(f"### {unit}")
        lines.append(f"- active: `{(data.get('is_active') or {}).get('stdout')}`")
        lines.append(f"- enabled: `{(data.get('is_enabled') or {}).get('stdout')}`")
        show = (data.get("show") or {}).get("stdout") or ""
        for ln in show.splitlines():
            if ln.strip():
                lines.append(f"- {ln.strip()}")
        lines.append("")
    lines.append("### list-timers")
    lt = result["systemd"].get("list_timers", {})
    lines.append("```text")
    lines.append((lt.get("stdout") or lt.get("stderr") or "")[:3000])
    lines.append("```")
    lines.append("")
    lines.append("## Journal / Log Summary")
    lines.append("")
    js = result["journal_summary"]
    for k, v in js.items():
        if k != "interesting_lines_tail":
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    if js.get("interesting_lines_tail"):
        lines.append("### Interesting journal lines tail")
        lines.append("```text")
        lines.append("\n".join(js["interesting_lines_tail"][-20:]))
        lines.append("```")
        lines.append("")
    lines.append("## Panel / Readmodel Freshness")
    lines.append("")
    lines.append("| Panel | Exists | generated_at_utc | mtime_utc | generated_age_sec | mtime_age_sec | Freshness | stale_data_fresh_file |")
    lines.append("|---|---:|---|---|---:|---:|---|---:|")
    for name, p in result["panel"].items():
        lines.append(f"| {name} | {p['exists']} | {p.get('generated_at_utc')} | {p.get('file_mtime_utc')} | {p.get('generated_age_sec')} | {p.get('mtime_age_sec')} | {p.get('freshness_status')} | {p.get('stale_data_fresh_file')} |")
    lines.append("")
    lines.append("## Canonical State Integrity Check")
    lines.append("")
    runtime = result["state"]["json_loaded"].get("runtime", {})
    lines.append(f"- runtime_mode: `{runtime.get('mode')}`")
    lines.append(f"- runtime_next_safe_step: `{runtime.get('next_safe_step')}`")
    lines.append(f"- runtime_status: `{runtime.get('runtime_status')}`")
    lines.append(f"- runtime_last_action: `{runtime.get('last_action')}`")
    lines.append(f"- runtime_last_activity_candidates_count: `{len(result['state']['runtime_activity_candidates'])}`")
    lines.append("")
    for name, info in result["state"]["text_summary"].items():
        lines.append(f"- {name}: exists=`{info.get('exists')}`, mentions_NEWS_RUNTIME_STABILIZATION=`{info.get('mentions_news_runtime_stabilization')}`, mentions_ERA52=`{info.get('mentions_era52')}`")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for f in result["findings"]:
        lines.append(f"- `{f['level']}` {f['code']}: {f['message']}")
    lines.append("")
    lines.append("## Next")
    lines.append("")
    lines.append("```text")
    lines.append(result["next_step"])
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    generated_at = iso_now()

    json_loaded = {}
    json_errors = {}
    json_counts = {}
    for name, path in STATE_JSONS.items():
        obj, err = read_json(path)
        json_loaded[name] = obj if isinstance(obj, dict) else {}
        json_errors[name] = err
        json_counts[name] = extract_news_counts(obj)

    runtime_obj = json_loaded.get("runtime", {})
    runtime_activity_candidates = []
    if runtime_obj:
        wanted = {
            "last_activity_timestamp",
            "last_activity_utc",
            "last_action_at_utc",
            "last_updated_utc",
            "updated_at_utc",
            "generated_at_utc",
            "last_action",
            "next_safe_step",
            "runtime_status",
            "mode",
        }
        runtime_activity_candidates = find_values_by_key(runtime_obj, wanted)

    db = select_db()
    table_rows = [table_snapshot(db, t) for t in NEWS_TABLES]

    n18 = json_loaded.get("n18_n19_n20_real_apply", {})
    backup_path = n18.get("backup_db") if isinstance(n18, dict) else None
    backup_p = Path(backup_path) if backup_path else None
    backup = {
        "backup_path": backup_path,
        "exists": backup_p.exists() if backup_p else False,
        "size_bytes": backup_p.stat().st_size if backup_p and backup_p.exists() else None,
        "mtime_utc": datetime.fromtimestamp(backup_p.stat().st_mtime, timezone.utc).isoformat() if backup_p and backup_p.exists() else None,
        "sha256": sha256_file(backup_p) if backup_p and backup_p.exists() else None,
    }

    systemd = systemd_snapshot()
    journal = journal_summary()
    logs = log_file_summary()
    panel = panel_snapshot()
    text_summary = state_text_summary()

    db_counts = {r["table"]: r.get("count") for r in table_rows}
    boot_counts = json_counts.get("boot", {})
    runtime_counts = json_counts.get("runtime", {})

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    if db is None:
        add("FAIL", "DB_NOT_FOUND", "NEWS DB selected edilemedi.")
    else:
        add("OK", "DB_SELECTED", f"Selected DB: {db}")

    raw_count = db_counts.get("news_raw_feed_events") or 0
    match_count = db_counts.get("news_token_match_events") or 0
    signal_count = db_counts.get("news_signal_events") or 0
    score_count = db_counts.get("news_score_events_v1") or 0
    freshness_count = db_counts.get("news_runtime_freshness_v1") or 0

    if raw_count > 0:
        add("OK", "RAW_NEWS_PRESENT", f"Raw news count: {raw_count}")
    else:
        add("WARN", "RAW_NEWS_EMPTY", "Raw news count zero veya tablo yok.")

    if match_count >= 47 and signal_count >= 47 and score_count >= 47:
        add("OK", "DOWNSTREAM_47_CHAIN_PRESENT", f"match/signal/score = {match_count}/{signal_count}/{score_count}")
    else:
        add("WARN", "DOWNSTREAM_47_CHAIN_NOT_CONFIRMED", f"match/signal/score = {match_count}/{signal_count}/{score_count}")

    if freshness_count > 0:
        add("OK", "FRESHNESS_TABLE_PRESENT", f"news_runtime_freshness_v1 count: {freshness_count}")
    else:
        add("WARN", "FRESHNESS_TABLE_EMPTY_OR_MISSING", "news_runtime_freshness_v1 count zero veya tablo yok.")

    if backup.get("exists"):
        add("OK", "REAL_APPLY_BACKUP_EXISTS", "N18/N19/N20 real apply backup dosyası yerinde.")
    else:
        add("WARN", "REAL_APPLY_BACKUP_NOT_CONFIRMED", "N18/N19/N20 backup path bulunamadı veya dosya yok.")

    timer_active = ((systemd.get("tokenoskobi-news-radar-refresh.timer", {}).get("is_active") or {}).get("stdout") == "active")
    if timer_active:
        add("OK", "NEWS_TIMER_ACTIVE", "NEWS timer active görünüyor.")
    else:
        add("WARN", "NEWS_TIMER_NOT_ACTIVE", "NEWS timer active görünmüyor.")

    service_show = (systemd.get("tokenoskobi-news-radar-refresh.service", {}).get("show") or {}).get("stdout") or ""
    if "ExecMainStatus=0" in service_show or "Result=success" in service_show:
        add("OK", "NEWS_SERVICE_LAST_RESULT_CLEAN_OR_SUCCESS", "Service show içinde success/0 izi var.")
    else:
        add("WARN", "NEWS_SERVICE_LAST_RESULT_NOT_CLEAN", "Service show success/0 net göstermiyor.")

    if journal.get("invalidargument_count", 0) > 0:
        add("WARN", "JOURNAL_INVALIDARGUMENT_SEEN", f"journal INVALIDARGUMENT count: {journal.get('invalidargument_count')}")
    else:
        add("OK", "JOURNAL_INVALIDARGUMENT_NOT_SEEN", "journal tail içinde INVALIDARGUMENT görülmedi.")

    postprocess_total = journal.get("postprocess_count", 0) + sum(x.get("postprocess_count", 0) for x in logs)
    if postprocess_total > 0:
        add("OK", "POSTPROCESS_TRACE_SEEN", f"postprocess trace/log count: {postprocess_total}")
    else:
        add("WARN", "POSTPROCESS_TRACE_NOT_SEEN", "postprocess izi görülmedi; NEWS-B için non-blocking dead-code adayı.")

    boot_drift_any = False
    for t in NEWS_TABLES:
        boot_vals = boot_counts.get(t) or []
        if boot_vals and isinstance(db_counts.get(t), int):
            if boot_vals[0].get("value") != db_counts.get(t):
                boot_drift_any = True
    if boot_drift_any:
        add("WARN", "BOOT_DRIFT_CONFIRMED", "PROJECT_BOOT NEWS sayımları current DB ile farklı.")
    else:
        add("OK", "BOOT_DRIFT_NOT_CONFIRMED_OR_BOOT_COUNTS_MISSING", "Boot drift net sayısal farkla doğrulanmadı veya Boot sayımı yok.")

    stale_panels = [k for k, v in panel.items() if str(v.get("freshness_status", "")).startswith("STALE")]
    unknown_panels = [k for k, v in panel.items() if v.get("freshness_status") == "UNKNOWN_TIMESTAMP"]
    if stale_panels:
        add("WARN", "PANEL_STALE", "Stale panel/readmodel: " + ",".join(stale_panels))
    elif unknown_panels:
        add("WARN", "PANEL_FRESHNESS_UNKNOWN", "Timestamp bilinmeyen panel/readmodel: " + ",".join(unknown_panels))
    else:
        add("OK", "PANEL_FRESHNESS_OK", "Panel/readmodel generated_at_utc taze görünüyor.")

    fail_count = sum(1 for f in findings if f["level"] == "FAIL")
    warn_count = sum(1 for f in findings if f["level"] == "WARN")

    if fail_count:
        decision = "FAIL_NEWS_A_CURRENT_TRUTH_BLOCKED"
        next_step = "STOP_AND_REVIEW_NEWS_A_FAILURES"
    elif warn_count:
        decision = "WARN_NEWS_A_CURRENT_TRUTH_CAPTURED_REVIEW_REQUIRED"
        next_step = "NEWS_B_RUNNER_TIMER_JOURNAL_ARGV_AUDIT_NOAPI"
    else:
        decision = "OK_NEWS_A_CURRENT_TRUTH_CAPTURED_READY_FOR_NEWS_B"
        next_step = "NEWS_B_RUNNER_TIMER_JOURNAL_ARGV_AUDIT_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": generated_at,
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "readonly_db_open_mode": "sqlite_uri_mode_ro_query_only",
            "real_db_write": False,
            "panel_write": False,
            "boot_update": False,
            "runtime_update": False,
            "systemd_start": False,
            "systemd_stop": False,
            "systemd_restart": False,
            "timer_restart": False,
            "external_api_call": False,
            "provider_call": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "repo_artifact_write": True,
        },
        "db": {
            "candidates": [str(p) for p in DB_CANDIDATES],
            "selected_db": str(db) if db else None,
            "selected_db_sha256": sha256_file(db) if db else None,
            "sidecars": db_sidecars(db),
            "table_snapshots": table_rows,
        },
        "backup": backup,
        "systemd": systemd,
        "journal_summary": journal,
        "log_files": logs,
        "panel": panel,
        "state": {
            "json_errors": json_errors,
            "json_counts": json_counts,
            "json_loaded": {
                "runtime": {
                    "mode": runtime_obj.get("mode"),
                    "next_safe_step": runtime_obj.get("next_safe_step"),
                    "runtime_status": runtime_obj.get("runtime_status"),
                    "last_action": runtime_obj.get("last_action"),
                    "last_completed": runtime_obj.get("last_completed"),
                    "current_work_unit": runtime_obj.get("current_work_unit"),
                    "active_work_unit": runtime_obj.get("active_work_unit"),
                },
                "boot": {
                    "status": json_loaded.get("boot", {}).get("project", {}).get("status") if isinstance(json_loaded.get("boot"), dict) else None,
                    "mode": json_loaded.get("boot", {}).get("project", {}).get("mode") if isinstance(json_loaded.get("boot"), dict) else None,
                    "next_safe_step": json_loaded.get("boot", {}).get("next_safe_step") if isinstance(json_loaded.get("boot"), dict) else None,
                },
            },
            "runtime_activity_candidates": runtime_activity_candidates,
            "text_summary": text_summary,
        },
        "findings": findings,
        "summary": {
            "raw_count": raw_count,
            "match_count": match_count,
            "signal_count": signal_count,
            "score_count": score_count,
            "freshness_count": freshness_count,
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_markdown(result))

    print("OK_NEWS_A_CURRENT_TRUTH_SNAPSHOT_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + str(OUT_JSON.relative_to(ROOT)))
    print("REPORT=" + str(OUT_MD.relative_to(ROOT)))
    print("RAW=" + str(raw_count))
    print("MATCH=" + str(match_count))
    print("SIGNAL=" + str(signal_count))
    print("SCORE=" + str(score_count))
    print("FRESHNESS=" + str(freshness_count))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
