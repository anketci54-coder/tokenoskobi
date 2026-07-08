#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import os
import sqlite3
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_B_FIX_1_POST_APPLY_AUDIT_NOAPI"
OUT_JSON = ROOT / "data/control/news_b_fix_1_post_apply_audit_noapi_v1.json"
OUT_MD = ROOT / "reports/LATEST_NEWS_B_FIX_1_POST_APPLY_AUDIT_NOAPI.md"

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

FIX_JSON = ROOT / "data/control/news_b_fix_1_systemd_stdout_stderr_path_targeted_apply_v1.json"
NEWS_B_JSON = ROOT / "data/control/news_b_runner_timer_journal_argv_audit_noapi_v1.json"
NEWS_A_JSON = ROOT / "data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json"

LOG_DIR = ROOT / "logs/news_radar"
LOG_OUT = LOG_DIR / "news_radar_refresh.log"
LOG_ERR = LOG_DIR / "news_radar_refresh.err.log"

NEWS_TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1",
    "news_runtime_freshness_v1",
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


def run_cmd(args, timeout=30):
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


def read_json(path):
    if not path.exists():
        return None, "MISSING"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:400]


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


def systemd_snapshot():
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


def journal_window(since_dt):
    since_arg = since_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    r = run_cmd([
        "journalctl",
        "-u",
        SERVICE,
        "--since",
        since_arg,
        "--no-pager",
        "--output=short-iso",
    ], timeout=40)
    text = (r.get("stdout") or "") + "\n" + (r.get("stderr") or "")
    low = text.lower()
    lines = [x for x in text.splitlines() if x.strip()]
    interesting = []
    terms = [
        "stdout",
        "stderr",
        "failed",
        "status=",
        "invalidargument",
        "traceback",
        "error",
        "finished",
        "success",
        "deactivated",
        "rc=2",
        "status=2",
        "no such file or directory",
    ]
    for ln in lines:
        l = ln.lower()
        if any(t in l for t in terms):
            interesting.append(ln[-700:])
    return {
        "since_utc": since_dt.isoformat(),
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
        "finished_count": low.count("finished"),
        "deactivated_successfully_count": low.count("deactivated successfully"),
        "interesting_lines_tail": interesting[-80:],
    }


def extract_counts_from_artifact(obj):
    if not isinstance(obj, dict):
        return {}
    s = obj.get("summary")
    if isinstance(s, dict):
        return {
            "raw": s.get("raw_count_after") or s.get("raw_count"),
            "match": s.get("match_count_after") or s.get("match_count"),
            "signal": s.get("signal_count_after") or s.get("signal_count"),
            "score": s.get("score_count_after") or s.get("score_count"),
            "freshness": s.get("freshness_count_after") or s.get("freshness_count"),
        }
    after = obj.get("after", {}).get("db", {}).get("tables", {}) if isinstance(obj.get("after"), dict) else {}
    if after:
        return {
            "raw": after.get("news_raw_feed_events", {}).get("count"),
            "match": after.get("news_token_match_events", {}).get("count"),
            "signal": after.get("news_signal_events", {}).get("count"),
            "score": after.get("news_score_events_v1", {}).get("count"),
            "freshness": after.get("news_runtime_freshness_v1", {}).get("count"),
        }
    return {}


def build_md(result):
    lines = []
    lines.append("# NEWS-B FIX 1 Post Apply Audit NOAPI")
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
    lines.append("## DB Current")
    lines.append("")
    lines.append("| Table | Exists | Count | Max TS |")
    lines.append("|---|---:|---:|---|")
    for t, r in result["db_current"].get("tables", {}).items():
        lines.append(f"| {t} | {r.get('exists')} | {r.get('count')} | {r.get('max_ts')} |")
    lines.append("")
    lines.append("## Service / Timer")
    lines.append("")
    sysd = result["systemd"]
    for k in ["service_is_active", "service_is_enabled", "timer_is_active", "timer_is_enabled"]:
        v = sysd.get(k, {})
        lines.append(f"- {k}: rc=`{v.get('rc')}` stdout=`{v.get('stdout')}` stderr=`{v.get('stderr')}`")
    lines.append("")
    lines.append("### service_show")
    lines.append("```text")
    lines.append(sysd.get("service_show", {}).get("stdout", ""))
    lines.append("```")
    lines.append("")
    lines.append("### timer_show")
    lines.append("```text")
    lines.append(sysd.get("timer_show", {}).get("stdout", ""))
    lines.append("```")
    lines.append("")
    lines.append("### list_timers")
    lines.append("```text")
    lines.append(sysd.get("list_timers", {}).get("stdout", ""))
    lines.append("```")
    lines.append("")
    lines.append("## Journal Since Fix")
    lines.append("")
    for k, v in result["journal_since_fix"].items():
        if k != "interesting_lines_tail":
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("```text")
    lines.append("\n".join(result["journal_since_fix"].get("interesting_lines_tail", [])[-80:]) or "NONE")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    fix_obj, fix_err = read_json(FIX_JSON)
    news_b_obj, news_b_err = read_json(NEWS_B_JSON)
    news_a_obj, news_a_err = read_json(NEWS_A_JSON)

    fix_dt = parse_dt(fix_obj.get("generated_at_utc")) if isinstance(fix_obj, dict) else None
    since_dt = fix_dt - timedelta(minutes=2) if fix_dt else utc_now() - timedelta(hours=2)

    db = db_counts()
    sysd = systemd_snapshot()
    journal = journal_window(since_dt)

    fix_counts = extract_counts_from_artifact(fix_obj)
    current_tables = db.get("tables", {})
    raw = current_tables.get("news_raw_feed_events", {}).get("count")
    match = current_tables.get("news_token_match_events", {}).get("count")
    signal = current_tables.get("news_signal_events", {}).get("count")
    score = current_tables.get("news_score_events_v1", {}).get("count")
    freshness = current_tables.get("news_runtime_freshness_v1", {}).get("count")

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    if fix_err:
        add("WARN", "FIX_1_ARTIFACT_NOT_READ", f"Fix-1 artifact okunamadı: {fix_err}")
    else:
        add("OK", "FIX_1_ARTIFACT_READ", "Fix-1 artifact okundu.")

    if LOG_DIR.exists() and LOG_DIR.is_dir():
        add("OK", "LOG_DIR_EXISTS", "logs/news_radar klasörü mevcut.")
    else:
        add("FAIL", "LOG_DIR_MISSING", "logs/news_radar klasörü yok.")

    if LOG_OUT.exists() and LOG_ERR.exists():
        add("OK", "LOG_FILES_EXIST", "stdout/stderr log dosyaları mevcut.")
    else:
        add("FAIL", "LOG_FILES_MISSING", "stdout/stderr log dosyaları eksik.")

    if journal.get("status_209_stdout_count", 0) == 0 and journal.get("failed_set_up_stdout_count", 0) == 0:
        add("OK", "STDOUT_209_REMAINS_CLEARED", "Fix sonrası journal penceresinde 209/STDOUT yok.")
    else:
        add("FAIL", "STDOUT_209_REAPPEARED", "Fix sonrası journal penceresinde 209/STDOUT tekrar görüldü.")

    if journal.get("invalidargument_count", 0) == 0:
        add("OK", "INVALIDARGUMENT_REMAINS_ABSENT", "Fix sonrası INVALIDARGUMENT yok.")
    else:
        add("WARN", "INVALIDARGUMENT_REAPPEARED", "Fix sonrası INVALIDARGUMENT görüldü.")

    service_show = sysd.get("service_show", {}).get("stdout") or ""
    if "Result=success" in service_show and "ExecMainStatus=0" in service_show:
        add("OK", "SERVICE_RESULT_CLEAN", "Service Result=success ve ExecMainStatus=0.")
    else:
        add("WARN", "SERVICE_RESULT_NOT_CLEAN", "Service success/0 net değil.")

    service_active = (sysd.get("service_is_active", {}).get("stdout") or "").strip()
    if service_active in {"inactive", "active"}:
        add("OK", "SERVICE_STATE_ACCEPTABLE", f"Service state kabul edilebilir: {service_active}")
    else:
        add("WARN", "SERVICE_STATE_REVIEW", f"Service state review gerekir: {service_active}")

    timer_active = (sysd.get("timer_is_active", {}).get("stdout") or "").strip()
    timer_enabled = (sysd.get("timer_is_enabled", {}).get("stdout") or "").strip()
    if timer_active == "inactive" and timer_enabled == "disabled":
        add("OK", "TIMER_STILL_DISABLED_BY_DESIGN", "Timer hâlâ disabled/inactive; Fix-1 kapsamında beklenen durum.")
    else:
        add("WARN", "TIMER_STATE_CHANGED", f"Timer state değişmiş olabilir: active={timer_active}, enabled={timer_enabled}")

    if raw is not None and raw >= 269 and match == 47 and signal == 47 and score == 47:
        add("OK", "DB_CHAIN_PRESERVED_AFTER_FIX", f"DB chain korunuyor: {raw}/{match}/{signal}/{score}")
    else:
        add("FAIL", "DB_CHAIN_NOT_PRESERVED_AFTER_FIX", f"DB chain beklenen değil: {raw}/{match}/{signal}/{score}")

    if fix_counts:
        raw_delta = raw - fix_counts.get("raw") if isinstance(raw, int) and isinstance(fix_counts.get("raw"), int) else None
        if raw_delta is not None and raw_delta >= 0:
            add("OK", "RAW_COUNT_NOT_DECREASING", f"Raw count fix sonrasına göre azalmadı; delta={raw_delta}")
        elif raw_delta is not None:
            add("WARN", "RAW_COUNT_DECREASED", f"Raw count fix sonrasına göre azaldı; delta={raw_delta}")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if fail_count:
        decision = "FAIL_NEWS_B_FIX_1_POST_APPLY_AUDIT_BLOCKED"
        next_step = "REVIEW_NEWS_B_FIX_1_POST_APPLY_FAILURE"
    elif warn_count:
        decision = "WARN_NEWS_B_FIX_1_POST_APPLY_AUDIT_REVIEW_REQUIRED"
        next_step = "NEWS_B_FIX_2_TIMER_ACTIVATION_TARGETED_APPLY_REQUIRES_APPROVAL"
    else:
        decision = "OK_NEWS_B_FIX_1_POST_APPLY_AUDIT_CLEAN"
        next_step = "NEWS_B_FIX_2_TIMER_ACTIVATION_TARGETED_APPLY_REQUIRES_APPROVAL"

    result = {
        "stage": STAGE,
        "generated_at_utc": iso_now(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "readonly_audit": True,
            "real_db_write": False,
            "db_schema_write": False,
            "panel_write": False,
            "runner_code_change": False,
            "matcher_code_change": False,
            "unit_file_write": False,
            "systemd_start": False,
            "systemd_stop": False,
            "systemd_restart": False,
            "systemd_daemon_reload": False,
            "timer_enable": False,
            "timer_start": False,
            "timer_restart": False,
            "boot_update": False,
            "runtime_update": False,
            "external_api_call": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "repo_artifact_write": True,
        },
        "references": {
            "fix_1_artifact": {
                "path": str(FIX_JSON),
                "read_error": fix_err,
                "decision": fix_obj.get("decision") if isinstance(fix_obj, dict) else None,
                "generated_at_utc": fix_obj.get("generated_at_utc") if isinstance(fix_obj, dict) else None,
                "counts": fix_counts,
            },
            "news_b_audit": {
                "path": str(NEWS_B_JSON),
                "read_error": news_b_err,
                "decision": news_b_obj.get("decision") if isinstance(news_b_obj, dict) else None,
            },
            "news_a_snapshot": {
                "path": str(NEWS_A_JSON),
                "read_error": news_a_err,
                "decision": news_a_obj.get("decision") if isinstance(news_a_obj, dict) else None,
            },
        },
        "log_files": {
            "dir": file_info(LOG_DIR),
            "stdout": file_info(LOG_OUT),
            "stderr": file_info(LOG_ERR),
        },
        "systemd": sysd,
        "journal_since_fix": journal,
        "db_current": db,
        "summary": {
            "raw_count": raw,
            "match_count": match,
            "signal_count": signal,
            "score_count": score,
            "freshness_count": freshness,
            "service_active": service_active,
            "timer_active": timer_active,
            "timer_enabled": timer_enabled,
            "journal_status_209_stdout_count": journal.get("status_209_stdout_count"),
            "journal_failed_set_up_stdout_count": journal.get("failed_set_up_stdout_count"),
            "journal_invalidargument_count": journal.get("invalidargument_count"),
            "journal_rc2_count": journal.get("rc2_count"),
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
        "findings": findings,
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_md(result))

    print("OK_NEWS_B_FIX_1_POST_APPLY_AUDIT_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + str(OUT_JSON.relative_to(ROOT)))
    print("REPORT=" + str(OUT_MD.relative_to(ROOT)))
    print("RAW=" + str(raw))
    print("MATCH=" + str(match))
    print("SIGNAL=" + str(signal))
    print("SCORE=" + str(score))
    print("SERVICE_ACTIVE=" + service_active)
    print("TIMER_ACTIVE=" + timer_active)
    print("TIMER_ENABLED=" + timer_enabled)
    print("JOURNAL_209_STDOUT=" + str(journal.get("status_209_stdout_count")))
    print("JOURNAL_FAILED_STDOUT_SETUP=" + str(journal.get("failed_set_up_stdout_count")))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
