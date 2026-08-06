#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_POST_AUDIT_NOAPI"

DRYRUN_JSON = ROOT / "data/control/hot_intelligence_ingress_gateway_contract_dryrun_noapi_v1.json"
SUMMARY_DOC = ROOT / "docs/HOT_INGRESS_CONTRACT_DRYRUN_SUMMARY_NOAPI.md"
PLAN_JSON = ROOT / "data/control/hot_intelligence_ingress_gateway_plan_noapi_v1.json"

OUT_JSON = ROOT / "data/control/hot_intelligence_ingress_gateway_contract_dryrun_post_audit_noapi_v1.json"
OUT_DOC = ROOT / "docs/HOT_INGRESS_CONTRACT_DRYRUN_POST_AUDIT_NOAPI.md"
OUT_REPORT = ROOT / "reports/LATEST_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_POST_AUDIT_NOAPI.md"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def run_cmd(args):
    p = subprocess.run(args, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"cmd": args, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def read_json(path):
    try:
        txt = path.read_text(encoding="utf-8")
        return json.loads(txt), None
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:300]

def sha256_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def safe_write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    os.replace(tmp, path)

def safe_write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def add(findings, level, code, msg):
    findings.append({"level": level, "code": code, "message": msg})

def build_md(result):
    lines = []
    lines.append("# HOT Ingress Contract Dryrun Post Audit NOAPI")
    lines.append("")
    lines.append(f"- stage: `{STAGE}`")
    lines.append(f"- generated_at_utc: `{result['generated_at_utc']}`")
    lines.append(f"- decision: `{result['decision']}`")
    lines.append(f"- next_step: `{result['next_step']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for k, v in result["summary"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for f in result["findings"]:
        lines.append(f"- `{f['level']}` `{f['code']}`: {f['message']}")
    lines.append("")
    return "\n".join(lines)

def main():
    findings = []
    head = run_cmd(["git", "rev-parse", "HEAD"]).get("stdout", "")
    status_before = run_cmd(["git", "status", "--short"])

    dry, dry_err = read_json(DRYRUN_JSON)
    plan, plan_err = read_json(PLAN_JSON)

    if dry_err:
        add(findings, "FAIL", "DRYRUN_JSON_READ_FAIL", dry_err)
    else:
        add(findings, "OK", "DRYRUN_JSON_READ_OK", "Dryrun JSON okundu.")

    if plan_err:
        add(findings, "WARN", "PLAN_JSON_READ_WARN", plan_err)
    else:
        add(findings, "OK", "PLAN_JSON_READ_OK", "Plan JSON okundu.")

    if SUMMARY_DOC.exists():
        add(findings, "OK", "SUMMARY_DOC_EXISTS", "Summary doc mevcut.")
    else:
        add(findings, "FAIL", "SUMMARY_DOC_MISSING", "Summary doc yok.")

    expected_decision = "OK_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_NOAPI_COMPLETE"
    if isinstance(dry, dict) and dry.get("decision") == expected_decision:
        add(findings, "OK", "DRYRUN_DECISION_OK", "Dryrun decision OK.")
    else:
        add(findings, "FAIL", "DRYRUN_DECISION_BAD", "Dryrun decision beklenen değil.")

    authority = dry.get("authority", {}) if isinstance(dry, dict) else {}
    authority_expected = {
        "noapi": True,
        "synthetic_events_only": True,
        "real_source_read": False,
        "real_db_write": False,
        "db_schema_write": False,
        "runtime_change": False,
        "systemd_change": False,
        "telegram_token_use": False,
        "discord_bot_use": False,
        "x_api_use": False,
        "wallet": False,
        "signing": False,
        "live_trade": False,
        "paper_trade": False,
        "ai_trade_authority": False
    }

    bad_authority = []
    for k, v in authority_expected.items():
        if authority.get(k) != v:
            bad_authority.append({"key": k, "expected": v, "actual": authority.get(k)})

    if bad_authority:
        add(findings, "FAIL", "AUTHORITY_DRIFT_FOUND", "Authority boundary sapması var.")
    else:
        add(findings, "OK", "AUTHORITY_BOUNDARY_OK", "NOAPI/authority boundary temiz.")

    summary = dry.get("summary", {}) if isinstance(dry, dict) else {}
    route_counts = summary.get("route_counts", {}) if isinstance(summary, dict) else {}

    checks = {
        "scenario_count": summary.get("scenario_count") == 8,
        "synthetic_input_event_count": summary.get("synthetic_input_event_count") == 137,
        "critical_candidate_count": summary.get("critical_candidate_count") == 1,
        "critical_alarm_count_zero": summary.get("critical_alarm_count") == 0,
        "outbound_alarm_count_zero": summary.get("outbound_alarm_count") == 0,
        "fail_count_zero": summary.get("fail_count") == 0,
        "warn_count_zero": summary.get("warn_count") == 0,
        "watch_count": route_counts.get("WATCH") == 4,
        "quarantine_count": route_counts.get("QUARANTINE") == 2,
        "candidate_count": route_counts.get("CRITICAL_CANDIDATE") == 1,
        "drop_count": route_counts.get("DROP") == 1
    }

    failed_checks = [k for k, v in checks.items() if not v]
    if failed_checks:
        add(findings, "FAIL", "SUMMARY_CHECKS_FAILED", ",".join(failed_checks))
    else:
        add(findings, "OK", "SUMMARY_CHECKS_OK", "Dryrun summary beklenen değerlerle uyumlu.")

    rules = dry.get("locked_red_team_rules_verified", {}) if isinstance(dry, dict) else {}
    missing_rules = [k for k, v in rules.items() if v is not True]
    if missing_rules:
        add(findings, "FAIL", "RED_TEAM_RULES_NOT_LOCKED", ",".join(missing_rules))
    else:
        add(findings, "OK", "RED_TEAM_RULES_LOCKED", "Red Team kuralları doğrulanmış.")

    scenarios = dry.get("synthetic_scenarios", []) if isinstance(dry, dict) else []
    alarm_bad = [x.get("scenario_id") for x in scenarios if x.get("outbound_alarm") is not False]
    if alarm_bad:
        add(findings, "FAIL", "OUTBOUND_ALARM_FOUND", ",".join(alarm_bad))
    else:
        add(findings, "OK", "NO_OUTBOUND_ALARM", "Hiçbir synthetic senaryo alarm üretmedi.")

    dryrun_checks = dry.get("dryrun_checks", []) if isinstance(dry, dict) else []
    non_ok = [x.get("code") for x in dryrun_checks if x.get("status") != "OK"]
    if non_ok:
        add(findings, "FAIL", "DRYRUN_CHECK_NON_OK", ",".join(non_ok))
    else:
        add(findings, "OK", "DRYRUN_CHECKS_OK", "Tüm dryrun check kayıtları OK.")

    fail_count = sum(1 for f in findings if f["level"] == "FAIL")
    warn_count = sum(1 for f in findings if f["level"] == "WARN")

    if fail_count:
        decision = "FAIL_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_POST_AUDIT_BLOCKED"
        next_step = "REVIEW_HOT_INGRESS_DRYRUN_FAILURE"
    elif warn_count:
        decision = "WARN_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_POST_AUDIT_REVIEW"
        next_step = "REVIEW_HOT_INGRESS_DRYRUN_WARNINGS"
    else:
        decision = "OK_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_POST_AUDIT_SEALED"
        next_step = "HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_PLAN_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": now_iso(),
        "decision": decision,
        "next_step": next_step,
        "head": head,
        "authority": {
            "readonly_post_audit": True,
            "noapi": True,
            "real_db_write": False,
            "db_schema_write": False,
            "runtime_change": False,
            "systemd_change": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "repo_artifact_write": True
        },
        "artifacts": {
            "dryrun_json": str(DRYRUN_JSON),
            "dryrun_json_sha256": sha256_file(DRYRUN_JSON),
            "summary_doc": str(SUMMARY_DOC),
            "summary_doc_sha256": sha256_file(SUMMARY_DOC),
            "plan_json": str(PLAN_JSON),
            "plan_json_sha256": sha256_file(PLAN_JSON)
        },
        "bad_authority": bad_authority,
        "summary_checks": checks,
        "findings": findings,
        "git_status_before": status_before,
        "summary": {
            "scenario_count": summary.get("scenario_count"),
            "synthetic_input_event_count": summary.get("synthetic_input_event_count"),
            "route_counts": route_counts,
            "critical_candidate_count": summary.get("critical_candidate_count"),
            "critical_alarm_count": summary.get("critical_alarm_count"),
            "outbound_alarm_count": summary.get("outbound_alarm_count"),
            "fail_count": fail_count,
            "warn_count": warn_count
        }
    }

    safe_write_json(OUT_JSON, result)
    text = build_md(result)
    safe_write_text(OUT_DOC, text)
    safe_write_text(OUT_REPORT, text)

    print("OK_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_POST_AUDIT_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=data/control/hot_intelligence_ingress_gateway_contract_dryrun_post_audit_noapi_v1.json")
    print("DOC=docs/HOT_INGRESS_CONTRACT_DRYRUN_POST_AUDIT_NOAPI.md")
    print("REPORT=reports/LATEST_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_POST_AUDIT_NOAPI.md")
    print("FAIL_COUNT=" + str(fail_count))
    print("WARN_COUNT=" + str(warn_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
