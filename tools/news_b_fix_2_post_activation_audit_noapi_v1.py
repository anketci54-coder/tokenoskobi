#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import os
import sqlite3
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_NOAPI"
OUT_JSON = ROOT / "data/control/news_b_fix_2_post_activation_audit_noapi_v1.json"
OUT_MD = ROOT / "reports/LATEST_NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_NOAPI.md"

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

FIX2_JSON = ROOT / "data/control/news_b_fix_2_timer_activation_targeted_apply_v1.json"
FIX1_POST_JSON = ROOT / "data/control/news_b_fix_1_post_apply_audit_noapi_v1.json"
NEWS_A_JSON = ROOT / "data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json"
NEWS_B_JSON = ROOT / "data/control/news_b_runner_timer_journal_argv_audit_noapi_v1.json"

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
    ], timeout=45)
    text = (r.get("stdout") or "") + "\n" + (r.get("stderr") or "")
    low = text.lower()
    lines = [x for x in text.splitlines() if x.strip()]
    interesting = []
    for ln in lines:
        l = ln.lower()
        if any(t in l for t in [
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
        ]):
            interesting.append(ln[-800:])
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
        "started_timer_count": low.count("started tokenoskobi-news-radar-refresh.timer"),
        "started_service_count": low.count("starting tokenoskobi-news-radar-refresh.service") + low.count("started tokenoskobi-news-radar-refresh.service"),
        "finished_service_count": low.count("finished tokenoskobi-news-radar-refresh.service"),
        "deactivated_successfully_count": low.count("deactivated successfully"),
        "interesting_lines_tail": interesting[-120:],
    }


def extract_counts(db_obj):
    t = db_obj.get("tables", {}) if isinstance(db_obj, dict) else {}
    return {
        "raw": t.get("news_raw_feed_events", {}).get("count"),
        "match": t.get("news_token_match_events", {}).get("count"),
        "signal": t.get("news_signal_events", {}).get("count"),
        "score": t.get("news_score_events_v1", {}).get("count"),
        "freshness": t.get("news_runtime_freshness_v1", {}).get("count"),
    }


def timer_schedule_present(list_text):
    text = list_text or ""
    return TIMER in text and SERVICE in text and "0 timers listed" not in text


def build_md(result):
    lines = []
    lines.append("# NEWS-B FIX 2 Post Activation Audit NOAPI")
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
    lines.append("| Table | Count | Max TS |")
    lines.append("|---|---:|---|")
    for t, r in result["db_current"].get("tables", {}).items():
        lines.append(f"| {t} | {r.get('count')} | {r.get('max_ts')} |")
    lines.append("")
    lines.append("## Timer Status")
    lines.append("")
    lines.append("```text")
    lines.append(result["systemd"].get("timer_status", {}).get("stdout", ""))
    lines.append("```")
    lines.append("")
    lines.append("## Service Status")
    lines.append("")
    lines.append("```text")
    lines.append(result["systemd"].get("service_status", {}).get("stdout", ""))
    lines.append("```")
    lines.append("")
    lines.append("## list-timers")
    lines.append("")
    lines.append("```text")
    lines.append(result["systemd"].get("list_timers", {}).get("stdout", ""))
    lines.append("```")
    lines.append("")
    lines.append("## Journal Since Timer Activation")
    lines.append("")
    for k, v in result["journal_since_activation"].items():
        if k != "interesting_lines_tail":
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("```text")
    lines.append("\n".join(result["journal_since_activation"].get("interesting_lines_tail", [])[-120:]) or "NONE")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    fix2, fix2_err = read_json(FIX2_JSON)
    fix1_post, fix1_post_err = read_json(FIX1_POST_JSON)
    news_a, news_a_err = read_json(NEWS_A_JSON)
    news_b, news_b_err = read_json(NEWS_B_JSON)

    fix2_generated = parse_dt(fix2.get("generated_at_utc")) if isinstance(fix2, dict) else None
    since_dt = (fix2_generated - timedelta(seconds=30)) if fix2_generated else (utc_now() - timedelta(hours=2))

    sysd = systemd_snapshot()
    db = db_counts()
    counts = extract_counts(db)
    journal = journal_since(since_dt)

    service_active = (sysd.get("service_is_active", {}).get("stdout") or "").strip()
    service_enabled = (sysd.get("service_is_enabled", {}).get("stdout") or "").strip()
    timer_active = (sysd.get("timer_is_active", {}).get("stdout") or "").strip()
    timer_enabled = (sysd.get("timer_is_enabled", {}).get("stdout") or "").strip()
    service_show = sysd.get("service_show", {}).get("stdout") or ""
    timer_show = sysd.get("timer_show", {}).get("stdout") or ""
    list_text = sysd.get("list_timers", {}).get("stdout") or ""

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    if fix2_err:
        add("WARN", "FIX2_ARTIFACT_NOT_READ", f"Fix2 artifact okunamadı: {fix2_err}")
    else:
        add("OK", "FIX2_ARTIFACT_READ", "Fix2 artifact okundu.")

    if fix1_post_err:
        add("WARN", "FIX1_POST_ARTIFACT_NOT_READ", f"Fix1 post-audit okunamadı: {fix1_post_err}")
    else:
        add("OK", "FIX1_POST_ARTIFACT_READ", "Fix1 post-audit artifact okundu.")

    if timer_active == "active":
        add("OK", "TIMER_ACTIVE_CONFIRMED", "Timer active.")
    else:
        add("FAIL", "TIMER_NOT_ACTIVE", f"Timer active değil: {timer_active}")

    if timer_enabled == "enabled":
        add("OK", "TIMER_ENABLED_CONFIRMED", "Timer enabled.")
    else:
        add("FAIL", "TIMER_NOT_ENABLED", f"Timer enabled değil: {timer_enabled}")

    if "ActiveState=active" in timer_show and "SubState=waiting" in timer_show:
        add("OK", "TIMER_WAITING_CONFIRMED", "Timer active/waiting.")
    else:
        add("WARN", "TIMER_WAITING_NOT_CONFIRMED", "Timer active/waiting net değil.")

    if "Triggers=" in timer_show and SERVICE in timer_show:
        add("OK", "TIMER_TRIGGER_SERVICE_CONFIRMED", "Timer service trigger bağı mevcut.")
    else:
        add("FAIL", "TIMER_TRIGGER_SERVICE_MISSING", "Timer service trigger bağı yok.")

    if timer_schedule_present(list_text):
        add("OK", "LIST_TIMERS_SCHEDULE_CONFIRMED", "list-timers schedule gösteriyor.")
    else:
        add("FAIL", "LIST_TIMERS_SCHEDULE_MISSING", "list-timers schedule göstermiyor.")

    if "Result=success" in service_show and "ExecMainStatus=0" in service_show:
        add("OK", "SERVICE_LAST_RESULT_CLEAN", "Service last result success/0.")
    else:
        add("WARN", "SERVICE_LAST_RESULT_REVIEW", "Service last result success/0 net değil.")

    if service_active in {"inactive", "active"}:
        add("OK", "SERVICE_STATE_ACCEPTABLE", f"Service state kabul edilebilir: {service_active}")
    else:
        add("WARN", "SERVICE_STATE_REVIEW", f"Service state review gerekir: {service_active}")

    if journal.get("status_209_stdout_count", 0) == 0 and journal.get("failed_set_up_stdout_count", 0) == 0:
        add("OK", "STDOUT_209_ABSENT_AFTER_ACTIVATION", "Timer activation sonrası 209/STDOUT yok.")
    else:
        add("FAIL", "STDOUT_209_PRESENT_AFTER_ACTIVATION", "Timer activation sonrası 209/STDOUT görüldü.")

    if journal.get("invalidargument_count", 0) == 0:
        add("OK", "INVALIDARGUMENT_ABSENT_AFTER_ACTIVATION", "Timer activation sonrası INVALIDARGUMENT yok.")
    else:
        add("WARN", "INVALIDARGUMENT_PRESENT_AFTER_ACTIVATION", "Timer activation sonrası INVALIDARGUMENT görüldü.")

    if journal.get("rc2_count", 0) == 0:
        add("OK", "RC2_ABSENT_AFTER_ACTIVATION", "Timer activation sonrası rc2/status2 yok.")
    else:
        add("WARN", "RC2_PRESENT_AFTER_ACTIVATION", "Timer activation sonrası rc2/status2 görüldü.")

    if counts.get("raw") is not None and counts.get("raw") >= 269 and counts.get("match") == 47 and counts.get("signal") == 47 and counts.get("score") == 47:
        add("OK", "DB_CHAIN_PRESERVED", f"DB chain korunuyor: {counts.get('raw')}/{counts.get('match')}/{counts.get('signal')}/{counts.get('score')}")
    else:
        add("FAIL", "DB_CHAIN_NOT_PRESERVED", f"DB chain beklenen değil: {counts}")

    first_fire_seen = journal.get("finished_service_count", 0) > 0 or journal.get("deactivated_successfully_count", 0) > 0
    if first_fire_seen:
        add("OK", "TIMER_SERVICE_FIRE_SEEN", "Timer activation penceresinde service run izi var.")
    else:
        add("OK", "TIMER_WAITING_FIRST_FIRE", "Timer schedule aktif; bu audit anında yeni service tetiklemesi henüz beklemede olabilir.")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if fail_count:
        decision = "FAIL_NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_BLOCKED"
        next_step = "REVIEW_NEWS_B_FIX_2_POST_ACTIVATION_FAILURE"
    elif warn_count:
        decision = "WARN_NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_REVIEW_REQUIRED"
        next_step = "NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_NOAPI"
    else:
        decision = "OK_NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_CLEAN"
        next_step = "NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": iso_now(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "readonly_audit": True,
            "timer_enable": False,
            "timer_start": False,
            "timer_restart": False,
            "service_start": False,
            "service_stop": False,
            "systemd_daemon_reload": False,
            "unit_file_write": False,
            "real_db_write": False,
            "db_schema_write": False,
            "panel_write": False,
            "runner_code_change": False,
            "matcher_code_change": False,
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
            "fix2_activation": {
                "path": str(FIX2_JSON),
                "read_error": fix2_err,
                "decision": fix2.get("decision") if isinstance(fix2, dict) else None,
                "generated_at_utc": fix2.get("generated_at_utc") if isinstance(fix2, dict) else None,
            },
            "fix1_post_audit": {
                "path": str(FIX1_POST_JSON),
                "read_error": fix1_post_err,
                "decision": fix1_post.get("decision") if isinstance(fix1_post, dict) else None,
            },
            "news_a_snapshot": {
                "path": str(NEWS_A_JSON),
                "read_error": news_a_err,
                "decision": news_a.get("decision") if isinstance(news_a, dict) else None,
            },
            "news_b_audit": {
                "path": str(NEWS_B_JSON),
                "read_error": news_b_err,
                "decision": news_b.get("decision") if isinstance(news_b, dict) else None,
            },
        },
        "systemd": sysd,
        "db_current": db,
        "journal_since_activation": journal,
        "summary": {
            "service_active": service_active,
            "service_enabled": service_enabled,
            "timer_active": timer_active,
            "timer_enabled": timer_enabled,
            "list_timers_has_schedule": timer_schedule_present(list_text),
            "journal_status_209_stdout_count": journal.get("status_209_stdout_count"),
            "journal_failed_set_up_stdout_count": journal.get("failed_set_up_stdout_count"),
            "journal_invalidargument_count": journal.get("invalidargument_count"),
            "journal_rc2_count": journal.get("rc2_count"),
            "first_fire_seen": first_fire_seen,
            "raw_count": counts.get("raw"),
            "match_count": counts.get("match"),
            "signal_count": counts.get("signal"),
            "score_count": counts.get("score"),
            "freshness_count": counts.get("freshness"),
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
        "findings": findings,
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_md(result))

    print("OK_NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + str(OUT_JSON.relative_to(ROOT)))
    print("REPORT=" + str(OUT_MD.relative_to(ROOT)))
    print("TIMER_ACTIVE=" + timer_active)
    print("TIMER_ENABLED=" + timer_enabled)
    print("LIST_TIMERS_HAS_SCHEDULE=" + str(timer_schedule_present(list_text)))
    print("JOURNAL_209_STDOUT=" + str(journal.get("status_209_stdout_count")))
    print("JOURNAL_FAILED_STDOUT_SETUP=" + str(journal.get("failed_set_up_stdout_count")))
    print("JOURNAL_INVALIDARGUMENT=" + str(journal.get("invalidargument_count")))
    print("FIRST_FIRE_SEEN=" + str(first_fire_seen))
    print("RAW=" + str(counts.get("raw")))
    print("MATCH=" + str(counts.get("match")))
    print("SIGNAL=" + str(counts.get("signal")))
    print("SCORE=" + str(counts.get("score")))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
