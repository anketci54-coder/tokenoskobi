#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import os
import re
import sqlite3
import subprocess
import time
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_B_FIX_2_TIMER_ACTIVATION_TARGETED_APPLY"
OUT_JSON = ROOT / "data/control/news_b_fix_2_timer_activation_targeted_apply_v1.json"
OUT_MD = ROOT / "reports/LATEST_NEWS_B_FIX_2_TIMER_ACTIVATION_TARGETED_APPLY.md"

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

FIX1_AUDIT_JSON = ROOT / "data/control/news_b_fix_1_post_apply_audit_noapi_v1.json"
FIX1_APPLY_JSON = ROOT / "data/control/news_b_fix_1_systemd_stdout_stderr_path_targeted_apply_v1.json"
NEWS_B_JSON = ROOT / "data/control/news_b_runner_timer_journal_argv_audit_noapi_v1.json"
NEWS_A_JSON = ROOT / "data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json"

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
        "service_status": run_cmd(["systemctl", "status", SERVICE, "--no-pager", "-l"], timeout=30),
        "timer_is_active": run_cmd(["systemctl", "is-active", TIMER]),
        "timer_is_enabled": run_cmd(["systemctl", "is-enabled", TIMER]),
        "timer_show": run_cmd([
            "systemctl", "show", TIMER,
            "-p", "ActiveState",
            "-p", "SubState",
            "-p", "Result",
            "-p", "NextElapseUSecRealtime",
            "-p", "LastTriggerUSec",
            "-p", "Triggers",
            "-p", "UnitFileState",
        ]),
        "timer_status": run_cmd(["systemctl", "status", TIMER, "--no-pager", "-l"], timeout=30),
        "timer_cat": run_cmd(["systemctl", "cat", TIMER], timeout=20),
        "list_timers": run_cmd(["systemctl", "list-timers", "--all", TIMER, "--no-pager"], timeout=20),
    }


def parse_timer_unit(cat_text):
    out = {
        "on_boot_sec": [],
        "on_unit_active_sec": [],
        "on_active_sec": [],
        "accuracy_sec": [],
        "unit": [],
        "wanted_by": [],
        "raw_timer_lines": [],
    }
    for line in (cat_text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out["raw_timer_lines"].append(s)
        if s.startswith("OnBootSec="):
            out["on_boot_sec"].append(s.split("=", 1)[1])
        elif s.startswith("OnUnitActiveSec="):
            out["on_unit_active_sec"].append(s.split("=", 1)[1])
        elif s.startswith("OnActiveSec="):
            out["on_active_sec"].append(s.split("=", 1)[1])
        elif s.startswith("AccuracySec="):
            out["accuracy_sec"].append(s.split("=", 1)[1])
        elif s.startswith("Unit="):
            out["unit"].append(s.split("=", 1)[1])
        elif s.startswith("WantedBy="):
            out["wanted_by"].append(s.split("=", 1)[1])
    return out


def journal_since(since_dt):
    since_arg = since_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    r = run_cmd([
        "journalctl",
        "-u",
        SERVICE,
        "-u",
        TIMER,
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
        "started",
        "finished",
        "deactivated",
        "failed",
        "stdout",
        "stderr",
        "invalidargument",
        "traceback",
        "error",
        "status=",
        "no such file",
        "trigger",
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
        "started_count": low.count("started"),
        "finished_count": low.count("finished"),
        "deactivated_successfully_count": low.count("deactivated successfully"),
        "interesting_lines_tail": interesting[-100:],
    }


def list_timer_has_schedule(list_text):
    text = list_text or ""
    if "0 timers listed" in text:
        return False
    return TIMER in text and SERVICE in text


def extract_counts(db_obj):
    t = db_obj.get("tables", {}) if isinstance(db_obj, dict) else {}
    return {
        "raw": t.get("news_raw_feed_events", {}).get("count"),
        "match": t.get("news_token_match_events", {}).get("count"),
        "signal": t.get("news_signal_events", {}).get("count"),
        "score": t.get("news_score_events_v1", {}).get("count"),
        "freshness": t.get("news_runtime_freshness_v1", {}).get("count"),
    }


def build_md(result):
    lines = []
    lines.append("# NEWS-B FIX 2 Timer Activation Targeted Apply")
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
    lines.append("## Timer Unit Parsed")
    lines.append("")
    for k, v in result["timer_unit_parsed"].items():
        if k != "raw_timer_lines":
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("```text")
    lines.append("\n".join(result["timer_unit_parsed"].get("raw_timer_lines", [])))
    lines.append("```")
    lines.append("")
    lines.append("## Apply")
    lines.append("")
    for k, v in result["apply"].items():
        lines.append(f"- {k}: rc=`{v.get('rc')}` stdout=`{v.get('stdout')}` stderr=`{v.get('stderr')}`")
    lines.append("")
    lines.append("## list-timers After")
    lines.append("")
    lines.append("```text")
    lines.append(result["after_systemd"].get("list_timers", {}).get("stdout", ""))
    lines.append("```")
    lines.append("")
    lines.append("## service_show After")
    lines.append("")
    lines.append("```text")
    lines.append(result["after_systemd"].get("service_show", {}).get("stdout", ""))
    lines.append("```")
    lines.append("")
    lines.append("## timer_show After")
    lines.append("")
    lines.append("```text")
    lines.append(result["after_systemd"].get("timer_show", {}).get("stdout", ""))
    lines.append("```")
    lines.append("")
    lines.append("## DB Counts")
    lines.append("")
    lines.append("| Table | Before | After |")
    lines.append("|---|---:|---:|")
    before_counts = extract_counts(result["before_db"])
    after_counts = extract_counts(result["after_db"])
    labels = {
        "raw": "news_raw_feed_events",
        "match": "news_token_match_events",
        "signal": "news_signal_events",
        "score": "news_score_events_v1",
        "freshness": "news_runtime_freshness_v1",
    }
    for k, label in labels.items():
        lines.append(f"| {label} | {before_counts.get(k)} | {after_counts.get(k)} |")
    lines.append("")
    lines.append("## Journal Since Activation")
    lines.append("")
    for k, v in result["journal_since_activation"].items():
        if k != "interesting_lines_tail":
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("```text")
    lines.append("\n".join(result["journal_since_activation"].get("interesting_lines_tail", [])[-100:]) or "NONE")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    started_at = utc_now()

    fix1_audit, fix1_audit_err = read_json(FIX1_AUDIT_JSON)
    fix1_apply, fix1_apply_err = read_json(FIX1_APPLY_JSON)
    news_b, news_b_err = read_json(NEWS_B_JSON)
    news_a, news_a_err = read_json(NEWS_A_JSON)

    before_systemd = systemd_snapshot()
    before_db = db_counts()
    timer_cat_text = before_systemd.get("timer_cat", {}).get("stdout") or ""
    timer_unit_parsed = parse_timer_unit(timer_cat_text)

    apply = {}
    apply["daemon_reload"] = run_cmd(["systemctl", "daemon-reload"], timeout=30)
    apply["reset_failed_service"] = run_cmd(["systemctl", "reset-failed", SERVICE], timeout=20)
    apply["enable_now_timer"] = run_cmd(["systemctl", "enable", "--now", TIMER], timeout=60)

    time.sleep(5)

    after_systemd = systemd_snapshot()
    after_db = db_counts()
    journal = journal_since(started_at - timedelta(seconds=10))

    before_counts = extract_counts(before_db)
    after_counts = extract_counts(after_db)

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    if fix1_audit_err:
        add("WARN", "FIX1_POST_AUDIT_REFERENCE_MISSING", f"Fix1 post-audit okunamadı: {fix1_audit_err}")
    else:
        add("OK", "FIX1_POST_AUDIT_REFERENCE_READ", "Fix1 post-audit artifact okundu.")

    if apply["enable_now_timer"].get("rc") == 0:
        add("OK", "TIMER_ENABLE_NOW_RC_ZERO", "systemctl enable --now timer rc=0.")
    else:
        add("FAIL", "TIMER_ENABLE_NOW_FAILED", f"systemctl enable --now rc={apply['enable_now_timer'].get('rc')}")

    timer_active = (after_systemd.get("timer_is_active", {}).get("stdout") or "").strip()
    timer_enabled = (after_systemd.get("timer_is_enabled", {}).get("stdout") or "").strip()

    if timer_active == "active":
        add("OK", "TIMER_ACTIVE_AFTER_ENABLE", "Timer active.")
    else:
        add("FAIL", "TIMER_NOT_ACTIVE_AFTER_ENABLE", f"Timer active değil: {timer_active}")

    if timer_enabled == "enabled":
        add("OK", "TIMER_ENABLED_AFTER_ENABLE", "Timer enabled.")
    else:
        add("FAIL", "TIMER_NOT_ENABLED_AFTER_ENABLE", f"Timer enabled değil: {timer_enabled}")

    list_text = after_systemd.get("list_timers", {}).get("stdout") or ""
    if list_timer_has_schedule(list_text):
        add("OK", "LIST_TIMERS_HAS_NEXT_SCHEDULE", "list-timers içinde NEWS timer schedule görünüyor.")
    else:
        add("WARN", "LIST_TIMERS_SCHEDULE_NOT_CONFIRMED", "list-timers içinde NEWS timer schedule net görünmüyor.")

    timer_show_text = after_systemd.get("timer_show", {}).get("stdout") or ""
    if "Triggers=" in timer_show_text and SERVICE in timer_show_text:
        add("OK", "TIMER_TRIGGERS_SERVICE", "Timer service'i trigger ediyor.")
    else:
        add("WARN", "TIMER_TRIGGER_SERVICE_NOT_CONFIRMED", "Timer→service trigger bağı net doğrulanmadı.")

    service_show_text = after_systemd.get("service_show", {}).get("stdout") or ""
    if "Result=success" in service_show_text and "ExecMainStatus=0" in service_show_text:
        add("OK", "SERVICE_LAST_RESULT_STILL_CLEAN", "Service last result success/0.")
    else:
        add("WARN", "SERVICE_LAST_RESULT_REVIEW", "Service last result success/0 net değil.")

    if journal.get("status_209_stdout_count", 0) == 0 and journal.get("failed_set_up_stdout_count", 0) == 0:
        add("OK", "STDOUT_209_NOT_REAPPEARED", "Timer activation sonrası 209/STDOUT yok.")
    else:
        add("FAIL", "STDOUT_209_REAPPEARED", "Timer activation sonrası 209/STDOUT tekrar görüldü.")

    if journal.get("invalidargument_count", 0) == 0:
        add("OK", "INVALIDARGUMENT_NOT_SEEN", "Timer activation sonrası INVALIDARGUMENT yok.")
    else:
        add("WARN", "INVALIDARGUMENT_SEEN", "Timer activation sonrası INVALIDARGUMENT görüldü.")

    if after_counts.get("match") == 47 and after_counts.get("signal") == 47 and after_counts.get("score") == 47:
        add("OK", "DOWNSTREAM_47_CHAIN_PRESERVED", f"Downstream korunuyor: {after_counts.get('match')}/{after_counts.get('signal')}/{after_counts.get('score')}")
    else:
        add("FAIL", "DOWNSTREAM_47_CHAIN_NOT_PRESERVED", f"Downstream beklenen değil: {after_counts}")

    if isinstance(after_counts.get("raw"), int) and isinstance(before_counts.get("raw"), int) and after_counts.get("raw") >= before_counts.get("raw"):
        add("OK", "RAW_COUNT_NOT_DECREASING", f"Raw count azalmadı: {before_counts.get('raw')} -> {after_counts.get('raw')}")
    else:
        add("WARN", "RAW_COUNT_DECREASE_OR_UNKNOWN", f"Raw count review: before={before_counts.get('raw')} after={after_counts.get('raw')}")

    if timer_unit_parsed.get("on_boot_sec") or timer_unit_parsed.get("on_unit_active_sec") or timer_unit_parsed.get("on_active_sec"):
        add("OK", "TIMER_INTERVAL_PRESENT", "Timer interval alanı mevcut.")
    else:
        add("WARN", "TIMER_INTERVAL_NOT_FOUND", "Timer interval alanı bulunamadı.")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if fail_count:
        decision = "FAIL_NEWS_B_FIX_2_TIMER_ACTIVATION_BLOCKED"
        next_step = "REVIEW_NEWS_B_FIX_2_TIMER_FAILURE"
    elif warn_count:
        decision = "WARN_NEWS_B_FIX_2_TIMER_ACTIVATED_REVIEW_REQUIRED"
        next_step = "NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_NOAPI"
    else:
        decision = "OK_NEWS_B_FIX_2_TIMER_ACTIVATED"
        next_step = "NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": iso_now(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "targeted_systemd_timer_apply": True,
            "timer_enable": True,
            "timer_start": True,
            "service_start_direct": False,
            "systemd_daemon_reload": True,
            "systemd_reset_failed_service": True,
            "unit_file_write": False,
            "real_db_write_by_this_script": False,
            "db_schema_write": False,
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
        "references": {
            "fix1_post_audit": {
                "path": str(FIX1_AUDIT_JSON),
                "read_error": fix1_audit_err,
                "decision": fix1_audit.get("decision") if isinstance(fix1_audit, dict) else None,
            },
            "fix1_apply": {
                "path": str(FIX1_APPLY_JSON),
                "read_error": fix1_apply_err,
                "decision": fix1_apply.get("decision") if isinstance(fix1_apply, dict) else None,
            },
            "news_b_audit": {
                "path": str(NEWS_B_JSON),
                "read_error": news_b_err,
                "decision": news_b.get("decision") if isinstance(news_b, dict) else None,
            },
            "news_a_snapshot": {
                "path": str(NEWS_A_JSON),
                "read_error": news_a_err,
                "decision": news_a.get("decision") if isinstance(news_a, dict) else None,
            },
        },
        "timer_unit_parsed": timer_unit_parsed,
        "before_systemd": before_systemd,
        "after_systemd": after_systemd,
        "before_db": before_db,
        "after_db": after_db,
        "apply": apply,
        "journal_since_activation": journal,
        "summary": {
            "timer_active_after": timer_active,
            "timer_enabled_after": timer_enabled,
            "list_timers_has_schedule": list_timer_has_schedule(list_text),
            "journal_status_209_stdout_count": journal.get("status_209_stdout_count"),
            "journal_failed_set_up_stdout_count": journal.get("failed_set_up_stdout_count"),
            "journal_invalidargument_count": journal.get("invalidargument_count"),
            "journal_rc2_count": journal.get("rc2_count"),
            "raw_count_before": before_counts.get("raw"),
            "raw_count_after": after_counts.get("raw"),
            "match_count_after": after_counts.get("match"),
            "signal_count_after": after_counts.get("signal"),
            "score_count_after": after_counts.get("score"),
            "freshness_count_after": after_counts.get("freshness"),
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
        "findings": findings,
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_md(result))

    print("OK_NEWS_B_FIX_2_TIMER_ACTIVATION_TARGETED_APPLY_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + str(OUT_JSON.relative_to(ROOT)))
    print("REPORT=" + str(OUT_MD.relative_to(ROOT)))
    print("TIMER_ACTIVE_AFTER=" + timer_active)
    print("TIMER_ENABLED_AFTER=" + timer_enabled)
    print("LIST_TIMERS_HAS_SCHEDULE=" + str(list_timer_has_schedule(list_text)))
    print("JOURNAL_209_STDOUT=" + str(journal.get("status_209_stdout_count")))
    print("JOURNAL_FAILED_STDOUT_SETUP=" + str(journal.get("failed_set_up_stdout_count")))
    print("RAW_AFTER=" + str(after_counts.get("raw")))
    print("MATCH_AFTER=" + str(after_counts.get("match")))
    print("SIGNAL_AFTER=" + str(after_counts.get("signal")))
    print("SCORE_AFTER=" + str(after_counts.get("score")))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
