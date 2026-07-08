#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import re
import subprocess
import hashlib
import ast

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_B_RUNNER_TIMER_JOURNAL_ARGV_AUDIT_NOAPI"
OUT_JSON = ROOT / "data/control/news_b_runner_timer_journal_argv_audit_noapi_v1.json"
OUT_MD = ROOT / "reports/LATEST_NEWS_B_RUNNER_TIMER_JOURNAL_ARGV_AUDIT_NOAPI.md"

UNIT_SERVICE = "tokenoskobi-news-radar-refresh.service"
UNIT_TIMER = "tokenoskobi-news-radar-refresh.timer"

RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
ORIGINAL = ROOT / "tools/news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.py"
MATCHER = ROOT / "tools/news_token_matcher_v1.py"
NEWS_A_JSON = ROOT / "data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json"

NEWS_LOG_HINTS = [
    ROOT / "logs/news_radar/news_radar_refresh.log",
    ROOT / "logs/news_radar/news_radar_refresh.err.log",
    ROOT / "logs/news_radar",
    ROOT / "data/control",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


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
        return {
            "cmd": args,
            "rc": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
        }
    except Exception as e:
        return {
            "cmd": args,
            "rc": None,
            "stdout": "",
            "stderr": type(e).__name__ + ":" + str(e)[:500],
        }


def read_text(path, max_bytes=600000):
    if not path.exists():
        return None, "MISSING"
    try:
        data = path.read_bytes()
        if len(data) > max_bytes:
            data = data[-max_bytes:]
        return data.decode("utf-8", errors="replace"), None
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:300]


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


def file_info(path):
    info = {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file() if path.exists() else False,
        "is_dir": path.is_dir() if path.exists() else False,
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat() if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() and path.is_file() and path.stat().st_size < 50_000_000 else None,
    }
    return info


def systemd_snapshot():
    service_cat = run_cmd(["systemctl", "cat", UNIT_SERVICE])
    timer_cat = run_cmd(["systemctl", "cat", UNIT_TIMER])
    service_show = run_cmd([
        "systemctl", "show", UNIT_SERVICE,
        "-p", "ActiveState",
        "-p", "SubState",
        "-p", "Result",
        "-p", "ExecMainStatus",
        "-p", "NRestarts",
        "-p", "FragmentPath",
        "-p", "UnitFileState",
        "-p", "ExecStart",
        "-p", "StandardOutput",
        "-p", "StandardError",
        "-p", "WorkingDirectory",
        "-p", "User",
        "-p", "Group",
    ])
    timer_show = run_cmd([
        "systemctl", "show", UNIT_TIMER,
        "-p", "ActiveState",
        "-p", "SubState",
        "-p", "Result",
        "-p", "FragmentPath",
        "-p", "UnitFileState",
        "-p", "NextElapseUSecRealtime",
        "-p", "LastTriggerUSec",
        "-p", "Triggers",
    ])
    return {
        "service_is_active": run_cmd(["systemctl", "is-active", UNIT_SERVICE]),
        "service_is_enabled": run_cmd(["systemctl", "is-enabled", UNIT_SERVICE]),
        "service_show": service_show,
        "service_cat": service_cat,
        "service_status": run_cmd(["systemctl", "status", UNIT_SERVICE, "--no-pager", "-l"], timeout=20),
        "timer_is_active": run_cmd(["systemctl", "is-active", UNIT_TIMER]),
        "timer_is_enabled": run_cmd(["systemctl", "is-enabled", UNIT_TIMER]),
        "timer_show": timer_show,
        "timer_cat": timer_cat,
        "timer_status": run_cmd(["systemctl", "status", UNIT_TIMER, "--no-pager", "-l"], timeout=20),
        "list_timers": run_cmd(["systemctl", "list-timers", "--all", UNIT_TIMER, "--no-pager"], timeout=20),
    }


def parse_unit_text(text):
    parsed = {
        "execstart_lines": [],
        "standard_output_lines": [],
        "standard_error_lines": [],
        "working_directory_lines": [],
        "environment_lines": [],
        "argv_risk_lines": [],
        "referenced_paths": [],
    }
    if not text:
        return parsed

    path_re = re.compile(r"(/[A-Za-z0-9_./:@%+\-]+)")
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("ExecStart="):
            parsed["execstart_lines"].append({"line": i, "text": s})
        if s.startswith("StandardOutput="):
            parsed["standard_output_lines"].append({"line": i, "text": s})
        if s.startswith("StandardError="):
            parsed["standard_error_lines"].append({"line": i, "text": s})
        if s.startswith("WorkingDirectory="):
            parsed["working_directory_lines"].append({"line": i, "text": s})
        if s.startswith("Environment=") or s.startswith("EnvironmentFile="):
            parsed["environment_lines"].append({"line": i, "text": s})
        if any(x in s for x in ["--", "$", "%", "{", "}", "ARGV", "arg", "Argument"]):
            if s.startswith("ExecStart=") or "python" in s.lower() or "news" in s.lower():
                parsed["argv_risk_lines"].append({"line": i, "text": s})
        for p in path_re.findall(s):
            parsed["referenced_paths"].append(p)
    return parsed


def extract_stdio_paths(unit_text):
    rows = []
    if not unit_text:
        return rows
    for line in unit_text.splitlines():
        s = line.strip()
        if not (s.startswith("StandardOutput=") or s.startswith("StandardError=")):
            continue
        key, val = s.split("=", 1)
        val = val.strip()
        entry = {"key": key, "raw_value": val, "path": None, "parent": None, "parent_exists": None, "target_exists": None}
        if val.startswith("append:"):
            p = Path(val.split("append:", 1)[1])
            entry["path"] = str(p)
            entry["parent"] = str(p.parent)
            entry["parent_exists"] = p.parent.exists()
            entry["target_exists"] = p.exists()
        elif val.startswith("file:"):
            p = Path(val.split("file:", 1)[1])
            entry["path"] = str(p)
            entry["parent"] = str(p.parent)
            entry["parent_exists"] = p.parent.exists()
            entry["target_exists"] = p.exists()
        rows.append(entry)
    return rows


def journal_snapshot():
    r = run_cmd([
        "journalctl", "-u", UNIT_SERVICE,
        "-n", "220",
        "--no-pager",
        "--output=short-iso",
    ], timeout=25)
    text = (r.get("stdout") or "") + "\n" + (r.get("stderr") or "")
    low = text.lower()
    interesting = []
    terms = [
        "stdout",
        "stderr",
        "failed",
        "exit-code",
        "status=209",
        "invalidargument",
        "rc=2",
        "status=2",
        "return_rc",
        "postprocess",
        "execmainstatus",
        "no such file or directory",
        "started",
        "finished",
        "succeeded",
    ]
    for ln in text.splitlines():
        l = ln.lower()
        if any(t in l for t in terms):
            interesting.append(ln[-700:])
    return {
        "cmd": r.get("cmd"),
        "rc": r.get("rc"),
        "line_count": len([x for x in text.splitlines() if x.strip()]),
        "status_209_stdout_count": low.count("status=209/stdout"),
        "failed_set_up_stdout_count": low.count("failed to set up standard output"),
        "failed_at_step_stdout_count": low.count("failed at step stdout"),
        "no_such_file_count": low.count("no such file or directory"),
        "invalidargument_count": low.count("invalidargument"),
        "rc2_count": low.count("rc=2") + low.count("status=2"),
        "postprocess_count": low.count("postprocess"),
        "return_rc_count": low.count("return_rc"),
        "traceback_count": low.count("traceback"),
        "failed_count": low.count("failed"),
        "interesting_lines_tail": interesting[-40:],
    }


def runner_static_snapshot():
    files = {
        "runner": RUNNER,
        "original_runner": ORIGINAL,
        "matcher": MATCHER,
    }
    out = {}
    for name, path in files.items():
        text, err = read_text(path)
        item = file_info(path)
        item["parse_error"] = err
        item["contains_subprocess_run"] = "subprocess.run" in text if text else False
        item["contains_original_runner"] = "ORIGINAL_RUNNER" in text if text else False
        item["contains_sys_argv"] = "sys.argv" in text if text else False
        item["contains_postprocess"] = "_postprocess" in text if text else False
        item["postprocess_line_numbers"] = []
        item["return_line_numbers_near_postprocess"] = []
        item["dead_code_suspect"] = False
        item["function_names"] = []
        item["syntax_ok"] = False

        if text:
            lines = text.splitlines()
            for i, ln in enumerate(lines, 1):
                if "_postprocess" in ln:
                    item["postprocess_line_numbers"].append(i)
                if "return " in ln:
                    if any(abs(i - p) <= 6 for p in item["postprocess_line_numbers"]):
                        item["return_line_numbers_near_postprocess"].append(i)
            try:
                tree = ast.parse(text)
                item["syntax_ok"] = True
                item["function_names"] = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == "main":
                        body = list(node.body)
                        for idx, stmt in enumerate(body):
                            if isinstance(stmt, ast.Try):
                                t_body = stmt.body
                                for j, sub in enumerate(t_body[:-1]):
                                    if isinstance(sub, ast.Return):
                                        tail = t_body[j+1:]
                                        tail_src = [ast.get_source_segment(text, x) or "" for x in tail]
                                        if any("_postprocess" in x for x in tail_src):
                                            item["dead_code_suspect"] = True
                            if idx < len(body) - 1 and isinstance(stmt, ast.Return):
                                tail_src = [ast.get_source_segment(text, x) or "" for x in body[idx+1:]]
                                if any("_postprocess" in x for x in tail_src):
                                    item["dead_code_suspect"] = True
            except Exception as e:
                item["syntax_ok"] = False
                item["ast_error"] = type(e).__name__ + ":" + str(e)[:300]
        out[name] = item
    return out


def local_log_snapshot():
    rows = []
    candidates = []
    for p in NEWS_LOG_HINTS:
        if p.is_file():
            candidates.append(p)
        elif p.is_dir():
            for child in sorted(p.glob("*news*"))[:30]:
                if child.is_file():
                    candidates.append(child)
            for child in sorted(p.glob("*radar*"))[:30]:
                if child.is_file():
                    candidates.append(child)
    seen = set()
    for p in candidates:
        if str(p) in seen:
            continue
        seen.add(str(p))
        info = file_info(p)
        text, err = read_text(p, max_bytes=300000)
        low = text.lower() if text else ""
        info.update({
            "read_error": err,
            "postprocess_count": low.count("postprocess"),
            "return_rc_count": low.count("return_rc"),
            "rc2_count": low.count("rc=2") + low.count("status=2"),
            "status_209_stdout_count": low.count("status=209/stdout"),
            "failed_set_up_stdout_count": low.count("failed to set up standard output"),
            "invalidargument_count": low.count("invalidargument"),
            "traceback_count": low.count("traceback"),
            "error_count": low.count("error"),
        })
        rows.append(info)
    return rows


def build_markdown(result):
    lines = []
    lines.append("# NEWS-B Runner / Timer / Journal / ARGV Audit NOAPI")
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
    lines.append("## Service Unit Parsed")
    lines.append("")
    parsed = result["unit_parse"]["service"]
    lines.append("### ExecStart")
    lines.append("```text")
    lines.append("\n".join(x["text"] for x in parsed.get("execstart_lines", [])) or "NONE")
    lines.append("```")
    lines.append("")
    lines.append("### StandardOutput / StandardError")
    lines.append("```text")
    se = []
    se += [x["text"] for x in parsed.get("standard_output_lines", [])]
    se += [x["text"] for x in parsed.get("standard_error_lines", [])]
    lines.append("\n".join(se) or "NONE")
    lines.append("```")
    lines.append("")
    lines.append("### Stdio Path Checks")
    lines.append("")
    lines.append("| Key | Raw | Path | Parent Exists | Target Exists |")
    lines.append("|---|---|---|---:|---:|")
    for r in result["stdio_path_checks"]:
        lines.append(f"| {r.get('key')} | `{r.get('raw_value')}` | `{r.get('path')}` | {r.get('parent_exists')} | {r.get('target_exists')} |")
    lines.append("")
    lines.append("## Systemd Status")
    lines.append("")
    for key in ["service_is_active", "service_is_enabled", "timer_is_active", "timer_is_enabled"]:
        x = result["systemd"].get(key, {})
        lines.append(f"- {key}: rc=`{x.get('rc')}` stdout=`{(x.get('stdout') or '').strip()}` stderr=`{(x.get('stderr') or '').strip()}`")
    lines.append("")
    lines.append("### list-timers")
    lines.append("```text")
    lines.append((result["systemd"].get("list_timers", {}).get("stdout") or result["systemd"].get("list_timers", {}).get("stderr") or "")[:4000])
    lines.append("```")
    lines.append("")
    lines.append("## Journal Summary")
    lines.append("")
    js = result["journal"]
    for k, v in js.items():
        if k != "interesting_lines_tail":
            lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("### Journal Interesting Tail")
    lines.append("```text")
    lines.append("\n".join(js.get("interesting_lines_tail", [])[-40:]) or "NONE")
    lines.append("```")
    lines.append("")
    lines.append("## Runner Static")
    lines.append("")
    lines.append("| File | Exists | Syntax OK | Dead-code suspect | Contains argv | Contains postprocess |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for name, r in result["runner_static"].items():
        lines.append(f"| {name} | {r.get('exists')} | {r.get('syntax_ok')} | {r.get('dead_code_suspect')} | {r.get('contains_sys_argv')} | {r.get('contains_postprocess')} |")
    lines.append("")
    lines.append("## Recommended Next")
    lines.append("")
    lines.append("```text")
    lines.append(result["next_step"])
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    systemd = systemd_snapshot()
    service_cat_text = systemd.get("service_cat", {}).get("stdout") or ""
    timer_cat_text = systemd.get("timer_cat", {}).get("stdout") or ""

    unit_parse = {
        "service": parse_unit_text(service_cat_text),
        "timer": parse_unit_text(timer_cat_text),
    }
    stdio_paths = extract_stdio_paths(service_cat_text)
    journal = journal_snapshot()
    runner_static = runner_static_snapshot()
    local_logs = local_log_snapshot()
    news_a, news_a_err = read_json(NEWS_A_JSON)

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    service_active = (systemd.get("service_is_active", {}).get("stdout") or "").strip()
    service_enabled = (systemd.get("service_is_enabled", {}).get("stdout") or "").strip()
    timer_active = (systemd.get("timer_is_active", {}).get("stdout") or "").strip()
    timer_enabled = (systemd.get("timer_is_enabled", {}).get("stdout") or "").strip()

    if service_cat_text:
        add("OK", "SERVICE_UNIT_READ", "Service unit okundu.")
    else:
        add("FAIL", "SERVICE_UNIT_NOT_READ", "Service unit okunamadı.")

    if timer_cat_text:
        add("OK", "TIMER_UNIT_READ", "Timer unit okundu.")
    else:
        add("WARN", "TIMER_UNIT_NOT_READ", "Timer unit okunamadı.")

    exec_lines = unit_parse["service"].get("execstart_lines", [])
    if exec_lines:
        add("OK", "EXECSTART_FOUND", "ExecStart bulundu.")
    else:
        add("FAIL", "EXECSTART_MISSING", "ExecStart bulunamadı.")

    if str(RUNNER) in service_cat_text or "news_radar_refresh_runner_v1.py" in service_cat_text:
        add("OK", "EXECSTART_RUNNER_BOUND", "ExecStart NEWS runner'a bağlı görünüyor.")
    else:
        add("WARN", "EXECSTART_RUNNER_NOT_CONFIRMED", "ExecStart içinde NEWS runner bağı net değil.")

    for name, p in [("runner", RUNNER), ("original_runner", ORIGINAL), ("matcher", MATCHER)]:
        if p.exists():
            add("OK", f"{name.upper()}_EXISTS", f"{name} dosyası var.")
        else:
            add("FAIL", f"{name.upper()}_MISSING", f"{name} dosyası yok: {p}")

    missing_stdio_parent = [x for x in stdio_paths if x.get("parent_exists") is False]
    if missing_stdio_parent:
        add("FAIL", "STDIO_PARENT_PATH_MISSING", "StandardOutput/StandardError parent path eksik.")
    elif stdio_paths:
        add("OK", "STDIO_PARENT_PATHS_EXIST", "StandardOutput/StandardError parent path mevcut.")
    else:
        add("WARN", "STDIO_PATHS_NOT_DECLARED", "StandardOutput/StandardError path tanımı bulunamadı.")

    if journal.get("status_209_stdout_count", 0) > 0 or journal.get("failed_set_up_stdout_count", 0) > 0:
        add("FAIL", "JOURNAL_STDOUT_209_CONFIRMED", "journal 209/STDOUT ve StandardOutput kurulum hatasını doğruluyor.")
    else:
        add("OK", "JOURNAL_STDOUT_209_NOT_SEEN", "journal tail içinde 209/STDOUT görülmedi.")

    if journal.get("invalidargument_count", 0) > 0:
        add("WARN", "INVALIDARGUMENT_SEEN", f"journal INVALIDARGUMENT count: {journal.get('invalidargument_count')}")
    else:
        add("OK", "INVALIDARGUMENT_NOT_SEEN", "journal tail içinde INVALIDARGUMENT yok.")

    if journal.get("rc2_count", 0) > 0:
        add("WARN", "RC2_OR_STATUS2_SEEN", f"journal rc=2/status=2 count: {journal.get('rc2_count')}")
    else:
        add("OK", "RC2_OR_STATUS2_NOT_SEEN", "journal tail içinde rc=2/status=2 yok.")

    postprocess_logs = journal.get("postprocess_count", 0) + sum(x.get("postprocess_count", 0) for x in local_logs)
    if postprocess_logs > 0:
        add("OK", "POSTPROCESS_TRACE_SEEN", f"postprocess trace/log count: {postprocess_logs}")
    else:
        add("WARN", "POSTPROCESS_TRACE_NOT_SEEN", "postprocess trace görülmedi.")

    if runner_static.get("runner", {}).get("dead_code_suspect"):
        add("WARN", "RUNNER_POSTPROCESS_DEAD_CODE_SUSPECT", "Runner içinde return sonrası _postprocess dead-code adayı.")
    else:
        add("OK", "RUNNER_POSTPROCESS_DEAD_CODE_NOT_CONFIRMED", "AST ile return sonrası _postprocess dead-code kesin doğrulanmadı.")

    if timer_active == "active":
        add("OK", "TIMER_ACTIVE", "Timer active.")
    else:
        add("WARN", "TIMER_NOT_ACTIVE", f"Timer active değil: {timer_active}")

    if timer_enabled == "enabled":
        add("OK", "TIMER_ENABLED", "Timer enabled.")
    else:
        add("WARN", "TIMER_NOT_ENABLED", f"Timer enabled değil: {timer_enabled}")

    if news_a_err:
        add("WARN", "NEWS_A_JSON_NOT_READ", f"NEWS-A JSON okunamadı: {news_a_err}")
    else:
        add("OK", "NEWS_A_JSON_READ", "NEWS-A JSON okundu.")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if any(x["code"] == "JOURNAL_STDOUT_209_CONFIRMED" for x in findings):
        decision = "FAIL_NEWS_B_STDOUT_PATH_ROOT_CAUSE_CONFIRMED"
        next_step = "NEWS_B_FIX_1_SYSTEMD_STDOUT_STDERR_PATH_TARGETED_APPLY_REQUIRES_APPROVAL"
    elif fail_count:
        decision = "FAIL_NEWS_B_RUNNER_TIMER_BLOCKER_FOUND"
        next_step = "REVIEW_NEWS_B_BLOCKERS"
    elif warn_count:
        decision = "WARN_NEWS_B_RUNNER_TIMER_REVIEW_REQUIRED"
        next_step = "NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_NOAPI"
    else:
        decision = "OK_NEWS_B_RUNNER_TIMER_CLEAN_READY_FOR_NEWS_C"
        next_step = "NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": now(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "readonly": True,
            "real_db_write": False,
            "panel_write": False,
            "boot_update": False,
            "runtime_update": False,
            "systemd_start": False,
            "systemd_stop": False,
            "systemd_restart": False,
            "timer_restart": False,
            "unit_file_write": False,
            "external_api_call": False,
            "provider_call": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "repo_artifact_write": True,
        },
        "summary": {
            "service_active": service_active,
            "service_enabled": service_enabled,
            "timer_active": timer_active,
            "timer_enabled": timer_enabled,
            "stdio_path_rows": len(stdio_paths),
            "stdio_missing_parent_count": len(missing_stdio_parent),
            "journal_status_209_stdout_count": journal.get("status_209_stdout_count"),
            "journal_failed_set_up_stdout_count": journal.get("failed_set_up_stdout_count"),
            "journal_invalidargument_count": journal.get("invalidargument_count"),
            "journal_rc2_count": journal.get("rc2_count"),
            "postprocess_trace_count": postprocess_logs,
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
        "systemd": systemd,
        "unit_parse": unit_parse,
        "stdio_path_checks": stdio_paths,
        "journal": journal,
        "runner_static": runner_static,
        "local_logs": local_logs,
        "news_a_reference": {
            "path": str(NEWS_A_JSON),
            "read_error": news_a_err,
            "decision": news_a.get("decision") if isinstance(news_a, dict) else None,
            "summary": news_a.get("summary") if isinstance(news_a, dict) else None,
        },
        "findings": findings,
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_markdown(result))

    print("OK_NEWS_B_RUNNER_TIMER_JOURNAL_ARGV_AUDIT_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + str(OUT_JSON.relative_to(ROOT)))
    print("REPORT=" + str(OUT_MD.relative_to(ROOT)))
    print("SERVICE_ACTIVE=" + service_active)
    print("TIMER_ACTIVE=" + timer_active)
    print("STDIO_MISSING_PARENT_COUNT=" + str(len(missing_stdio_parent)))
    print("JOURNAL_209_STDOUT=" + str(journal.get("status_209_stdout_count")))
    print("JOURNAL_FAILED_STDOUT_SETUP=" + str(journal.get("failed_set_up_stdout_count")))
    print("POSTPROCESS_TRACE_COUNT=" + str(postprocess_logs))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
