#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_SAFE_APPLY_POST_AUDIT_NOAPI"

PARENT = ROOT / "data/control/hot_intelligence_ingress_gateway_contract_canonical_binding_safe_apply_docs_only_noapi_v1.json"
OUT_JSON = ROOT / "data/control/hot_ingress_binding_safe_apply_post_audit_noapi_v1.json"
OUT_DOC = ROOT / "docs/HOT_INGRESS_BINDING_SAFE_APPLY_POST_AUDIT_NOAPI.md"
OUT_REPORT = ROOT / "reports/LATEST_HOT_INGRESS_BINDING_SAFE_APPLY_POST_AUDIT_NOAPI.md"

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

def main():
    generated = now_iso()
    head = run_cmd(["git", "rev-parse", "HEAD"])["stdout"]
    names = run_cmd(["git", "show", "--name-only", "--format=", "HEAD"])["stdout"].splitlines()

    parent, err = read_json(PARENT)
    findings = []

    def add(level, code, msg):
        findings.append({"level": level, "code": code, "message": msg})

    if err:
        add("FAIL", "PARENT_READ_FAIL", err)
        parent = {}
    else:
        add("OK", "PARENT_READ_OK", "Safe apply artifact okundu.")

    expected_decision = "OK_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_SAFE_APPLY_DOCS_ONLY_DONE"
    if parent.get("decision") == expected_decision:
        add("OK", "PARENT_DECISION_OK", "Safe apply decision OK.")
    else:
        add("FAIL", "PARENT_DECISION_BAD", "Safe apply decision beklenen değil.")

    summary = parent.get("summary", {})
    authority = parent.get("authority", {})
    updated = parent.get("updated_files", [])

    if summary.get("updated_file_count") == 2:
        add("OK", "UPDATED_COUNT_OK", "2 dosya güncellenmiş.")
    else:
        add("FAIL", "UPDATED_COUNT_BAD", "Güncellenen dosya sayısı beklenen değil.")

    expected_updated = {"06_PROJECT_MASTER_STATE.md", "07_PROJECT_HANDOFF.md"}
    got_updated = {x.get("path") for x in updated if x.get("changed") is True}

    if got_updated == expected_updated:
        add("OK", "UPDATED_FILES_OK", "Sadece 06/07 state dosyaları güncellenmiş.")
    else:
        add("FAIL", "UPDATED_FILES_BAD", "Güncellenen dosya seti beklenen değil.")

    if authority.get("index_file_changed") is False and summary.get("index_changed") is False:
        add("OK", "INDEX_UNCHANGED_OK", "01_INDEX değişmemiş.")
    else:
        add("FAIL", "INDEX_CHANGED_BAD", "01_INDEX değişmiş görünüyor.")

    if authority.get("active_control_json_changed") is False and summary.get("active_control_json_changed") is False:
        add("OK", "ACTIVE_CONTROL_UNCHANGED_OK", "ACTIVE control JSON dosyaları değişmemiş.")
    else:
        add("FAIL", "ACTIVE_CONTROL_CHANGED_BAD", "ACTIVE control JSON değişmiş görünüyor.")

    forbidden = {
        "01_INDEX.md",
        "data/control/ACTIVE_EXECUTION_GRAPH.json",
        "data/control/MINIMAL_ACTIVE_CORE_MANIFEST.json",
        "data/control/USED_BY_RUNTIME_INDEX.json",
        "data/control/ACTIVE_CORE_RANKING.json",
    }
    touched_forbidden = sorted(forbidden.intersection(set(names)))

    if touched_forbidden:
        add("FAIL", "FORBIDDEN_FILE_TOUCHED", ",".join(touched_forbidden))
    else:
        add("OK", "FORBIDDEN_FILES_UNTOUCHED", "Index ve ACTIVE control JSON dosyaları commit diff içinde yok.")

    clean_flags = {
        "noapi": authority.get("noapi") is True,
        "real_db_write": authority.get("real_db_write") is False,
        "db_schema_write": authority.get("db_schema_write") is False,
        "runtime_change": authority.get("runtime_change") is False,
        "systemd_change": authority.get("systemd_change") is False,
        "source_connection": authority.get("source_connection") is False,
        "token_or_key_use": authority.get("token_or_key_use") is False,
        "wallet": authority.get("wallet") is False,
        "signing": authority.get("signing") is False,
        "live_trade": authority.get("live_trade") is False,
        "paper_trade": authority.get("paper_trade") is False,
        "ai_trade_authority": authority.get("ai_trade_authority") is False,
    }

    bad_flags = [k for k, ok in clean_flags.items() if not ok]
    if bad_flags:
        add("FAIL", "AUTHORITY_FLAGS_BAD", ",".join(bad_flags))
    else:
        add("OK", "AUTHORITY_FLAGS_OK", "NOAPI ve yetki sınırları temiz.")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if fail_count:
        decision = "FAIL_HOT_INGRESS_BINDING_SAFE_APPLY_POST_AUDIT_BLOCKED"
        next_step = "REVIEW_HOT_INGRESS_BINDING_SAFE_APPLY_FAILURE"
    else:
        decision = "OK_HOT_INGRESS_BINDING_SAFE_APPLY_POST_AUDIT_SEALED"
        next_step = "HOT_INTELLIGENCE_INGRESS_GATEWAY_SOURCE_REGISTRY_MINIMAL_PLAN_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": generated,
        "decision": decision,
        "next_step": next_step,
        "audited_head": head,
        "parent_artifact": str(PARENT.relative_to(ROOT)),
        "parent_artifact_sha256": sha256_file(PARENT),
        "commit_name_only": names,
        "findings": findings,
        "summary": {
            "fail_count": fail_count,
            "warn_count": warn_count,
            "updated_file_count": summary.get("updated_file_count"),
            "index_changed": summary.get("index_changed"),
            "active_control_json_changed": summary.get("active_control_json_changed")
        }
    }

    safe_write_json(OUT_JSON, result)

    md = f"""# HOT Ingress Binding Safe Apply Post Audit NOAPI

- stage: `{STAGE}`
- generated_at_utc: `{generated}`
- decision: `{decision}`
- audited_head: `{head}`
- next_step: `{next_step}`

## Verified

- `06_PROJECT_MASTER_STATE.md` updated.
- `07_PROJECT_HANDOFF.md` updated.
- `01_INDEX.md` unchanged.
- ACTIVE control JSON files unchanged.
- NOAPI / DB / runtime / systemd / source / trade boundary clean.

## Counts

- fail_count: `{fail_count}`
- warn_count: `{warn_count}`
"""
    safe_write(OUT_DOC, md)
    safe_write(OUT_REPORT, md)

    print("OK_HOT_INGRESS_BINDING_SAFE_APPLY_POST_AUDIT_WRITTEN")
    print("DECISION=" + decision)
    print("FAIL_COUNT=" + str(fail_count))
    print("WARN_COUNT=" + str(warn_count))
    print("NEXT_STEP=" + next_step)
    raise SystemExit(0 if fail_count == 0 else 2)

if __name__ == "__main__":
    main()
