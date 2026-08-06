#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import re
import sqlite3
import subprocess
import time
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_B_FIX_1_SYSTEMD_STDOUT_STDERR_PATH_TARGETED_APPLY"
OUT_JSON = ROOT / "data/control/news_b_fix_1_systemd_stdout_stderr_path_targeted_apply_v1.json"
OUT_MD = ROOT / "reports/LATEST_NEWS_B_FIX_1_SYSTEMD_STDOUT_STDERR_PATH_TARGETED_APPLY.md"

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"
LOG_DIR = ROOT / "logs/news_radar"
LOG_OUT = LOG_DIR / "news_radar_refresh.log"
LOG_ERR = LOG_DIR / "news_radar_refresh.err.log"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

NEWS_TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1",
    "news_runtime_freshness_v1",
]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def run_cmd(args, timeout=40):
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
            "stderr": type(e).__name__ + ":" + str(e)[:500],
        }


def sha256_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def file_info(path):
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir() if path.exists() else False,
        "is_file": path.is_file() if path.exists() else False,
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat() if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() and path.is_file() and path.stat().st_size <= 50_000_000 else None,
    }


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


def db_counts():
    rows = {}
    if not DB.exists():
        return {"error": "DB_NOT_FOUND", "tables": rows}
    try:
        con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True, timeout=8)
        con.execute("PRAGMA query_only=ON")
        cur = con.cursor()
        for t in NEWS_TABLES:
            item = {"exists": False, "count": None, "max_ts": None, "timestamp_col": None, "error": None}
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,))
            if cur.fetchone() is None:
                rows[t] = item
                continue
            item["exists"] = True
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            item["count"] = int(cur.fetchone()[0])
            cols = [x[1] for x in cur.execute(f"PRAGMA table_info({t})").fetchall()]
            for c in ["created_at_utc", "fetched_at_utc", "generated_at_utc", "updated_at_utc", "last_observed_at_utc"]:
                if c in cols:
                    cur.execute(f"SELECT MAX({c}) FROM {t}")
                    item["timestamp_col"] = c
                    item["max_ts"] = cur.fetchone()[0]
                    break
            rows[t] = item
        con.close()
        return {"error": None, "tables": rows}
    except Exception as e:
        return {"error": type(e).__name__ + ":" + str(e)[:400], "tables": rows}


def systemd_status():
    return {
        "service_is_active": run_cmd(["systemctl", "is-active", SERVICE]),
        "service_is_enabled": run_cmd(["systemctl", "is-enabled", SERVICE]),
        "service_show": run_cmd([
            "systemctl", "show", SERVICE,
            "-p", "ActiveState",
            "-p", "SubState",
            "-p", "Result",
            "-p", "ExecMainStatus",
            "-p", "StandardOutput",
            "-p", "StandardError",
            "-p", "ExecStart",
            "-p", "FragmentPath",
            "-p", "UnitFileState",
        ]),
        "timer_is_active": run_cmd(["systemctl", "is-active", TIMER]),
        "timer_is_enabled": run_cmd(["systemctl", "is-enabled", TIMER]),
        "timer_show": run_cmd([
            "systemctl", "show", TIMER,
            "-p", "ActiveState",
            "-p", "SubState",
            "-p", "Result",
            "-p", "NextElapseUSecRealtime",
            "-p", "LastTriggerUSec",
            "-p", "UnitFileState",
        ]),
        "list_timers": run_cmd(["systemctl", "list-timers", "--all", TIMER, "--no-pager"]),
    }


def parse_stdio_paths(show_stdout):
    rows = []
    text = show_stdout or ""
    for key in ["StandardOutput", "StandardError"]:
        m = re.search(rf"^{key}=(.+)$", text, re.MULTILINE)
        raw = m.group(1).strip() if m else None
        path = None
        if raw and raw.startswith("append:"):
            path = Path(raw.split("append:", 1)[1])
        elif raw and raw.startswith("file:"):
            path = Path(raw.split("file:", 1)[1])
        rows.append({
            "key": key,
            "raw": raw,
            "path": str(path) if path else None,
            "parent": str(path.parent) if path else None,
            "parent_exists": path.parent.exists() if path else None,
            "target_exists": path.exists() if path else None,
        })
    return rows


def journal_since(epoch):
    r = run_cmd([
        "journalctl", "-u", SERVICE,
        "--since", "@" + str(epoch),
        "--no-pager",
        "--output=short-iso",
    ], timeout=30)
    text = (r.get("stdout") or "") + "\n" + (r.get("stderr") or "")
    low = text.lower()
    lines = [x for x in text.splitlines() if x.strip()]
    interesting = []
    for ln in lines:
        l = ln.lower()
        if any(t in l for t in ["stdout", "stderr", "failed", "status=", "invalidargument", "traceback", "error", "finished", "success", "return_rc", "postprocess"]):
            interesting.append(ln[-700:])
    return {
        "cmd_rc": r.get("rc"),
        "line_count": len(lines),
        "status_209_stdout_count": low.count("status=209/stdout"),
        "failed_set_up_stdout_count": low.count("failed to set up standard output"),
        "failed_at_step_stdout_count": low.count("failed at step stdout"),
        "no_such_file_count": low.count("no such file or directory"),
        "invalidargument_count": low.count("invalidargument"),
        "rc2_count": low.count("rc=2") + low.count("status=2"),
        "traceback_count": low.count("traceback"),
        "error_count": low.count("error"),
        "failed_count": low.count("failed"),
        "postprocess_count": low.count("postprocess"),
        "return_rc_count": low.count("return_rc"),
        "interesting_lines_tail": interesting[-80:],
    }


def build_md(result):
    lines = []
    lines.append("# NEWS-B FIX 1 Systemd STDOUT STDERR Path Targeted Apply")
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
    lines.append("## Stdio Path Checks")
    lines.append("")
    lines.append("| Phase | Key | Raw | Path | Parent Exists | Target Exists |")
    lines.append("|---|---|---|---|---:|---:|")
    for phase in ["before", "after"]:
        for r in result["stdio_paths"][phase]:
            lines.append(f"| {phase} | {r.get('key')} | `{r.get('raw')}` | `{r.get('path')}` | {r.get('parent_exists')} | {r.get('target_exists')} |")
    lines.append("")
    lines.append("## Apply Commands")
    lines.append("")
    for k, v in result["apply"].items():
        if isinstance(v, dict):
            lines.append(f"- {k}: rc=`{v.get('rc')}` stdout=`{(v.get('stdout') or '')[:300]}` stderr=`{(v.get('stderr') or '')[:300]}`")
        else:
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Journal After Apply")
    lines.append("")
    for k, v in result["journal_after"].items():
        if k != "interesting_lines_tail":
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("```text")
    lines.append("\n".join(result["journal_after"].get("interesting_lines_tail", [])[-80:]) or "NONE")
    lines.append("```")
    lines.append("")
    lines.append("## DB Counts After")
    lines.append("")
    lines.append("| Table | Exists | Count | Max TS |")
    lines.append("|---|---:|---:|---|")
    for t, r in result["db_after"].get("tables", {}).items():
        lines.append(f"| {t} | {r.get('exists')} | {r.get('count')} | {r.get('max_ts')} |")
    lines.append("")
    return "\n".join(lines)


def main():
    before_epoch = int(time.time())
    before_systemd = systemd_status()
    before_show = before_systemd.get("service_show", {}).get("stdout") or ""
    before_stdio = parse_stdio_paths(before_show)
    before_db = db_counts()

    apply = {}
    apply["mkdir_log_dir"] = None
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(LOG_DIR, 0o755)
        apply["mkdir_log_dir"] = {"rc": 0, "stdout": str(LOG_DIR), "stderr": ""}
    except Exception as e:
        apply["mkdir_log_dir"] = {"rc": 1, "stdout": "", "stderr": type(e).__name__ + ":" + str(e)[:300]}

    for p in [LOG_OUT, LOG_ERR]:
        try:
            p.touch(exist_ok=True)
            os.chmod(p, 0o644)
        except Exception:
            pass

    apply["daemon_reload"] = run_cmd(["systemctl", "daemon-reload"], timeout=30)
    apply["reset_failed_service"] = run_cmd(["systemctl", "reset-failed", SERVICE], timeout=20)

    start_epoch = int(time.time())
    apply["start_service_once"] = run_cmd(["systemctl", "start", SERVICE], timeout=90)
    time.sleep(4)

    after_systemd = systemd_status()
    after_show = after_systemd.get("service_show", {}).get("stdout") or ""
    after_stdio = parse_stdio_paths(after_show)
    after_journal = journal_since(start_epoch)
    after_db = db_counts()

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    if apply["mkdir_log_dir"]["rc"] == 0 and LOG_DIR.exists():
        add("OK", "LOG_DIR_CREATED_OR_EXISTS", "logs/news_radar klasörü mevcut.")
    else:
        add("FAIL", "LOG_DIR_CREATE_FAILED", "logs/news_radar klasörü oluşturulamadı.")

    missing_after = [x for x in after_stdio if x.get("parent_exists") is False]
    if missing_after:
        add("FAIL", "STDIO_PARENT_STILL_MISSING", "StandardOutput/StandardError parent path hâlâ eksik.")
    else:
        add("OK", "STDIO_PARENT_EXISTS_AFTER", "StandardOutput/StandardError parent path mevcut.")

    if after_journal.get("status_209_stdout_count", 0) == 0 and after_journal.get("failed_set_up_stdout_count", 0) == 0:
        add("OK", "STDOUT_209_CLEARED_AFTER_START", "Yeni service start denemesinde 209/STDOUT görülmedi.")
    else:
        add("FAIL", "STDOUT_209_STILL_PRESENT_AFTER_START", "Yeni service start denemesinde 209/STDOUT devam ediyor.")

    start_rc = apply["start_service_once"].get("rc")
    if start_rc == 0:
        add("OK", "SERVICE_START_RC_ZERO", "systemctl start service rc=0.")
    else:
        add("WARN", "SERVICE_START_RC_NONZERO", f"systemctl start service rc={start_rc}; journal ayrı değerlendirildi.")

    raw = after_db.get("tables", {}).get("news_raw_feed_events", {}).get("count")
    match = after_db.get("tables", {}).get("news_token_match_events", {}).get("count")
    signal = after_db.get("tables", {}).get("news_signal_events", {}).get("count")
    score = after_db.get("tables", {}).get("news_score_events_v1", {}).get("count")
    freshness = after_db.get("tables", {}).get("news_runtime_freshness_v1", {}).get("count")

    if raw and raw >= 250 and match == 47 and signal == 47 and score == 47:
        add("OK", "DB_CHAIN_PRESERVED", f"DB chain preserved raw/match/signal/score={raw}/{match}/{signal}/{score}")
    else:
        add("WARN", "DB_CHAIN_NEEDS_REVIEW", f"DB chain after raw/match/signal/score={raw}/{match}/{signal}/{score}")

    if after_journal.get("invalidargument_count", 0) == 0:
        add("OK", "INVALIDARGUMENT_NOT_SEEN_AFTER_START", "Yeni start sonrası INVALIDARGUMENT görülmedi.")
    else:
        add("WARN", "INVALIDARGUMENT_SEEN_AFTER_START", "Yeni start sonrası INVALIDARGUMENT görüldü.")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if fail_count:
        decision = "FAIL_NEWS_B_FIX_1_STDOUT_STDERR_PATH_NOT_CLEARED"
        next_step = "REVIEW_NEWS_B_FIX_1_FAILURE"
    elif warn_count:
        decision = "WARN_NEWS_B_FIX_1_STDOUT_STDERR_PATH_CLEARED_REVIEW_SERVICE_RC"
        next_step = "NEWS_B_FIX_1_POST_APPLY_AUDIT_NOAPI"
    else:
        decision = "OK_NEWS_B_FIX_1_STDOUT_STDERR_PATH_CLEARED"
        next_step = "NEWS_B_FIX_1_POST_APPLY_AUDIT_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": utc_now(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "targeted_filesystem_apply": True,
            "created_log_directory": True,
            "systemd_daemon_reload": True,
            "service_start_once": True,
            "timer_enable": False,
            "timer_start": False,
            "timer_restart": False,
            "unit_file_write": False,
            "db_schema_write": False,
            "db_data_write_by_this_script": False,
            "panel_write": False,
            "runner_code_change": False,
            "matcher_code_change": False,
            "boot_update": False,
            "runtime_update": False,
            "external_api_call_by_this_script": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "repo_artifact_write": True,
        },
        "before": {
            "epoch": before_epoch,
            "systemd": before_systemd,
            "db": before_db,
        },
        "after": {
            "systemd": after_systemd,
            "db": after_db,
        },
        "stdio_paths": {
            "before": before_stdio,
            "after": after_stdio,
        },
        "log_files": {
            "dir": file_info(LOG_DIR),
            "stdout": file_info(LOG_OUT),
            "stderr": file_info(LOG_ERR),
        },
        "apply": apply,
        "journal_after": after_journal,
        "db_after": after_db,
        "summary": {
            "service_start_rc": start_rc,
            "stdio_missing_parent_after": len(missing_after),
            "journal_status_209_stdout_after": after_journal.get("status_209_stdout_count"),
            "journal_failed_set_up_stdout_after": after_journal.get("failed_set_up_stdout_count"),
            "journal_invalidargument_after": after_journal.get("invalidargument_count"),
            "raw_count_after": raw,
            "match_count_after": match,
            "signal_count_after": signal,
            "score_count_after": score,
            "freshness_count_after": freshness,
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
        "findings": findings,
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_md(result))

    print("OK_NEWS_B_FIX_1_SYSTEMD_STDOUT_STDERR_PATH_TARGETED_APPLY_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + str(OUT_JSON.relative_to(ROOT)))
    print("REPORT=" + str(OUT_MD.relative_to(ROOT)))
    print("SERVICE_START_RC=" + str(start_rc))
    print("STDIO_MISSING_PARENT_AFTER=" + str(len(missing_after)))
    print("JOURNAL_209_STDOUT_AFTER=" + str(after_journal.get("status_209_stdout_count")))
    print("JOURNAL_FAILED_STDOUT_SETUP_AFTER=" + str(after_journal.get("failed_set_up_stdout_count")))
    print("RAW_AFTER=" + str(raw))
    print("MATCH_AFTER=" + str(match))
    print("SIGNAL_AFTER=" + str(signal))
    print("SCORE_AFTER=" + str(score))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
