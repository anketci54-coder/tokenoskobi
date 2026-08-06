#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_CONTRACT_DRYRUN_NOAPI"

PLAN = ROOT / "data/control/hot_ingress_source_registry_minimal_plan_noapi_v1.json"
OUT_JSON = ROOT / "data/control/hot_ingress_source_registry_minimal_contract_dryrun_noapi_v1.json"
OUT_DOC = ROOT / "docs/HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_CONTRACT_DRYRUN_NOAPI.md"
OUT_REPORT = ROOT / "reports/LATEST_HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_CONTRACT_DRYRUN_NOAPI.md"

ALLOWED_TYPES = {"telegram", "discord", "x", "news", "rss", "onchain", "dex", "mempool", "manual_synthetic"}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def run_cmd(args):
    p = subprocess.run(args, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
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

def safe_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def safe_write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    os.replace(tmp, path)

def validate(entry):
    if not entry.get("source_uid"):
        return "REJECT", "source_uid_required"
    if entry.get("source_type") not in ALLOWED_TYPES:
        return "REJECT", "source_type_not_allowed"
    if entry.get("credential_like_field_present") is True:
        return "REJECT", "credential_like_field_forbidden"
    if not entry.get("rate_limit_policy_ref"):
        return "REJECT", "rate_limit_policy_required"
    if not entry.get("trust_policy_ref"):
        return "REJECT", "trust_policy_required"
    return "ACCEPT", "ok"

def route_cap(source_type):
    if source_type in {"telegram", "discord", "x"}:
        return "WATCH"
    if source_type in {"news", "rss"}:
        return "INFO"
    if source_type in {"onchain", "dex", "mempool"}:
        return "CRITICAL_CANDIDATE"
    if source_type == "manual_synthetic":
        return "WATCH"
    return "DROP"

def main():
    generated = now_iso()
    head = run_cmd(["git", "rev-parse", "HEAD"])["stdout"]
    plan, plan_err = read_json(PLAN)

    entries = [
        {
            "case_id": "SRC01_VALID_TELEGRAM_LOW_TRUST",
            "source_uid": "src_telegram_alpha",
            "source_type": "telegram",
            "trust_score_initial": 35,
            "trust_score_current": 35,
            "trust_policy_ref": "dynamic_trust_score_policy_v1",
            "rate_limit_policy_ref": "source_rate_limit_policy_v1",
            "dedupe_policy_ref": "fuzzy_duplicate_policy_v1",
            "expected_result": "ACCEPT",
            "expected_route_cap": "WATCH"
        },
        {
            "case_id": "SRC02_VALID_ONCHAIN_HIGH_TRUST",
            "source_uid": "src_onchain_alpha",
            "source_type": "onchain",
            "trust_score_initial": 90,
            "trust_score_current": 90,
            "trust_policy_ref": "dynamic_trust_score_policy_v1",
            "rate_limit_policy_ref": "source_rate_limit_policy_v1",
            "dedupe_policy_ref": "fuzzy_duplicate_policy_v1",
            "expected_result": "ACCEPT",
            "expected_route_cap": "CRITICAL_CANDIDATE"
        },
        {
            "case_id": "SRC03_MISSING_SOURCE_UID",
            "source_uid": None,
            "source_type": "rss",
            "trust_policy_ref": "dynamic_trust_score_policy_v1",
            "rate_limit_policy_ref": "source_rate_limit_policy_v1",
            "expected_result": "REJECT"
        },
        {
            "case_id": "SRC04_UNKNOWN_SOURCE_TYPE",
            "source_uid": "src_unknown_alpha",
            "source_type": "forum_unknown",
            "trust_policy_ref": "dynamic_trust_score_policy_v1",
            "rate_limit_policy_ref": "source_rate_limit_policy_v1",
            "expected_result": "REJECT"
        },
        {
            "case_id": "SRC05_CREDENTIAL_LIKE_FIELD",
            "source_uid": "src_bad_field_alpha",
            "source_type": "news",
            "credential_like_field_present": True,
            "trust_policy_ref": "dynamic_trust_score_policy_v1",
            "rate_limit_policy_ref": "source_rate_limit_policy_v1",
            "expected_result": "REJECT"
        },
        {
            "case_id": "SRC06_MISSING_RATE_LIMIT_POLICY",
            "source_uid": "src_missing_rate_limit",
            "source_type": "dex",
            "trust_policy_ref": "dynamic_trust_score_policy_v1",
            "rate_limit_policy_ref": None,
            "expected_result": "REJECT"
        },
        {
            "case_id": "SRC07_MISSING_TRUST_POLICY",
            "source_uid": "src_missing_trust_policy",
            "source_type": "mempool",
            "trust_policy_ref": None,
            "rate_limit_policy_ref": "source_rate_limit_policy_v1",
            "expected_result": "REJECT"
        },
        {
            "case_id": "SRC08_VALID_RSS_INFO_CAP",
            "source_uid": "src_rss_alpha",
            "source_type": "rss",
            "trust_score_initial": 55,
            "trust_score_current": 55,
            "trust_policy_ref": "dynamic_trust_score_policy_v1",
            "rate_limit_policy_ref": "source_rate_limit_policy_v1",
            "dedupe_policy_ref": "fuzzy_duplicate_policy_v1",
            "expected_result": "ACCEPT",
            "expected_route_cap": "INFO"
        },
        {
            "case_id": "SRC09_VALID_MANUAL_SYNTHETIC",
            "source_uid": "src_manual_synthetic_alpha",
            "source_type": "manual_synthetic",
            "trust_score_initial": 100,
            "trust_score_current": 100,
            "trust_policy_ref": "dynamic_trust_score_policy_v1",
            "rate_limit_policy_ref": "source_rate_limit_policy_v1",
            "dedupe_policy_ref": "fuzzy_duplicate_policy_v1",
            "expected_result": "ACCEPT",
            "expected_route_cap": "WATCH"
        }
    ]

    findings = []

    if plan_err:
        findings.append({"level": "FAIL", "code": "PLAN_READ_FAIL", "message": plan_err})
    else:
        findings.append({"level": "OK", "code": "PLAN_READ_OK", "message": "Parent plan okundu."})

    results = []
    for e in entries:
        actual_result, reason = validate(e)
        actual_route_cap = route_cap(e.get("source_type")) if actual_result == "ACCEPT" else None
        ok = actual_result == e.get("expected_result")
        if ok and actual_result == "ACCEPT":
            ok = actual_route_cap == e.get("expected_route_cap")
        results.append({
            "case_id": e["case_id"],
            "source_type": e.get("source_type"),
            "expected_result": e.get("expected_result"),
            "actual_result": actual_result,
            "expected_route_cap": e.get("expected_route_cap"),
            "actual_route_cap": actual_route_cap,
            "reason": reason,
            "status": "OK" if ok else "FAIL"
        })

    if all(r["status"] == "OK" for r in results):
        findings.append({"level": "OK", "code": "SYNTHETIC_TESTS_OK", "message": "Tüm synthetic source registry testleri OK."})
    else:
        findings.append({"level": "FAIL", "code": "SYNTHETIC_TESTS_FAIL", "message": "Synthetic testlerde hata var."})

    authority = {
        "dryrun_only": True,
        "synthetic_registry_entries_only": True,
        "noapi": True,
        "source_connection": False,
        "credential_material": False,
        "credential_use": False,
        "real_db_write": False,
        "db_schema_write": False,
        "runtime_change": False,
        "systemd_change": False,
        "wallet": False,
        "signing": False,
        "live_trade": False,
        "paper_trade": False,
        "ai_trade_authority": False,
        "repo_artifact_write": True
    }

    bad_authority = [k for k, v in authority.items() if k != "repo_artifact_write" and k not in {"dryrun_only", "synthetic_registry_entries_only", "noapi"} and v is not False]
    if bad_authority:
        findings.append({"level": "FAIL", "code": "AUTHORITY_DRIFT", "message": ",".join(bad_authority)})
    else:
        findings.append({"level": "OK", "code": "AUTHORITY_BOUNDARY_OK", "message": "NOAPI boundary temiz."})

    fail_count = sum(1 for f in findings if f["level"] == "FAIL") + sum(1 for r in results if r["status"] == "FAIL")
    warn_count = sum(1 for f in findings if f["level"] == "WARN")

    if fail_count:
        decision = "FAIL_HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_CONTRACT_DRYRUN_BLOCKED"
        next_step = "REVIEW_HOT_INGRESS_SOURCE_REGISTRY_DRYRUN_FAILURE"
    else:
        decision = "OK_HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_CONTRACT_DRYRUN_NOAPI_COMPLETE"
        next_step = "HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_CONTRACT_POST_AUDIT_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": generated,
        "decision": decision,
        "next_step": next_step,
        "head": head,
        "parent_plan": {
            "path": str(PLAN.relative_to(ROOT)),
            "sha256": sha256_file(PLAN)
        },
        "authority": authority,
        "allowed_source_types": sorted(ALLOWED_TYPES),
        "synthetic_results": results,
        "route_caps": {
            "social_fast": "WATCH",
            "news_slow": "INFO",
            "chain_observation": "CRITICAL_CANDIDATE",
            "manual_test": "WATCH"
        },
        "findings": findings,
        "summary": {
            "synthetic_entry_count": len(entries),
            "accepted_count": sum(1 for r in results if r["actual_result"] == "ACCEPT"),
            "rejected_count": sum(1 for r in results if r["actual_result"] == "REJECT"),
            "outbound_alarm_count": 0,
            "fail_count": fail_count,
            "warn_count": warn_count
        }
    }

    safe_write_json(OUT_JSON, result)

    md = f"""# HOT Ingress Source Registry Minimal Contract Dryrun NOAPI

- stage: `{STAGE}`
- generated_at_utc: `{generated}`
- decision: `{decision}`
- next_step: `{next_step}`

## Result

- synthetic_entry_count: `{len(entries)}`
- accepted_count: `{result['summary']['accepted_count']}`
- rejected_count: `{result['summary']['rejected_count']}`
- outbound_alarm_count: `0`
- fail_count: `{fail_count}`
- warn_count: `{warn_count}`

## Boundary

No API. No real source connection. No credential use. No DB write. No schema write. No runtime change. No systemd change. No wallet/signing. No paper/live trade. AI authority 0.
"""
    safe_write(OUT_DOC, md)
    safe_write(OUT_REPORT, md)

    print("OK_HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_CONTRACT_DRYRUN_WRITTEN")
    print("DECISION=" + decision)
    print("FAIL_COUNT=" + str(fail_count))
    print("WARN_COUNT=" + str(warn_count))
    print("NEXT_STEP=" + next_step)
    raise SystemExit(0 if fail_count == 0 else 2)

if __name__ == "__main__":
    main()
