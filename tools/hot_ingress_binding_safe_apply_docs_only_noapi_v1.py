#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_SAFE_APPLY_DOCS_ONLY_NOAPI"

FILES_TO_UPDATE = [
    ROOT / "06_PROJECT_MASTER_STATE.md",
    ROOT / "07_PROJECT_HANDOFF.md",
]

INDEX_FILE = ROOT / "01_INDEX.md"

OUT_JSON = ROOT / "data/control/hot_intelligence_ingress_gateway_contract_canonical_binding_safe_apply_docs_only_noapi_v1.json"
OUT_DOC = ROOT / "docs/HOT_INGRESS_BINDING_SAFE_APPLY_DOCS_ONLY_NOAPI.md"
OUT_REPORT = ROOT / "reports/LATEST_HOT_INGRESS_BINDING_SAFE_APPLY_DOCS_ONLY_NOAPI.md"

START = "<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_START -->"
END = "<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_END -->"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def run_cmd(args):
    p = subprocess.run(args, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"cmd": args, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

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
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def safe_write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    os.replace(tmp, path)

def replace_block(path, new_block):
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise RuntimeError(f"marker_missing:{path}")
    before, rest = text.split(START, 1)
    old_body, after = rest.split(END, 1)
    old_block = START + old_body + END
    new_text = before + new_block + after
    if new_text == text:
        changed = False
    else:
        safe_write(path, new_text)
        changed = True
    return {
        "path": str(path.relative_to(ROOT)),
        "changed": changed,
        "old_block_sha256": hashlib.sha256(old_block.encode("utf-8")).hexdigest(),
        "new_block_sha256": hashlib.sha256(new_block.encode("utf-8")).hexdigest(),
        "file_sha256_after": sha256_file(path)
    }

def main():
    generated = now_iso()
    head_before = run_cmd(["git", "rev-parse", "HEAD"])["stdout"]

    new_block = f"""{START}
# CURRENT CANONICAL STATE

- Updated UTC: {generated}
- Last completed: `HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_REVIEW_NOAPI`
- Current focus: `HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_SAFE_APPLY_DOCS_ONLY_NOAPI`
- Runtime authority: `PROJECT_RUNTIME.json`
- Canonical source of truth: local server + GitHub main seal.
- HOT ingress status: contract plan, synthetic dryrun, post-audit, binding plan, binding dryrun, and binding review completed.
- HOT ingress boundary: planned canonical architecture only.
- Safe apply scope: `06_PROJECT_MASTER_STATE.md` and `07_PROJECT_HANDOFF.md`.
- Index decision: `01_INDEX.md` unchanged because it is navigation-only and already points to 06/07.
- Deferred active control files: `ACTIVE_EXECUTION_GRAPH.json`, `MINIMAL_ACTIVE_CORE_MANIFEST.json`, `USED_BY_RUNTIME_INDEX.json`, `ACTIVE_CORE_RANKING.json`.
- NOAPI boundary: no API, no DB write, no schema change, no runtime change, no systemd change, no source token/key, no wallet/signing, no paper/live trade, AI authority 0.
- Workflow preference: GitHub first when possible; otherwise single paste-and-run command block.
- Next safe step: `HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_SAFE_APPLY_POST_AUDIT_NOAPI`
{END}"""

    updates = []
    for p in FILES_TO_UPDATE:
        updates.append(replace_block(p, new_block))

    result = {
        "stage": STAGE,
        "generated_at_utc": generated,
        "decision": "OK_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_SAFE_APPLY_DOCS_ONLY_DONE",
        "next_step": "HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_SAFE_APPLY_POST_AUDIT_NOAPI",
        "head_before": head_before,
        "authority": {
            "docs_only_apply": True,
            "noapi": True,
            "index_file_changed": False,
            "active_control_json_changed": False,
            "real_db_write": False,
            "db_schema_write": False,
            "runtime_change": False,
            "systemd_change": False,
            "source_connection": False,
            "token_or_key_use": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "ai_trade_authority": False,
            "repo_artifact_write": True
        },
        "index_decision": {
            "path": "01_INDEX.md",
            "changed": False,
            "reason": "01_INDEX.md constitution says navigation only; HOT binding is recorded in 06/07 which index already points to.",
            "sha256": sha256_file(INDEX_FILE)
        },
        "updated_files": updates,
        "deferred_files": [
            "data/control/ACTIVE_EXECUTION_GRAPH.json",
            "data/control/MINIMAL_ACTIVE_CORE_MANIFEST.json",
            "data/control/USED_BY_RUNTIME_INDEX.json",
            "data/control/ACTIVE_CORE_RANKING.json"
        ],
        "summary": {
            "updated_file_count": sum(1 for x in updates if x["changed"]),
            "index_changed": False,
            "active_control_json_changed": False,
            "fail_count": 0,
            "warn_count": 0
        }
    }

    safe_write_json(OUT_JSON, result)

    md = f"""# HOT Ingress Binding Safe Apply Docs Only NOAPI

- stage: `{STAGE}`
- generated_at_utc: `{generated}`
- decision: `{result['decision']}`
- next_step: `{result['next_step']}`

## Updated

- `06_PROJECT_MASTER_STATE.md`
- `07_PROJECT_HANDOFF.md`

## Not Changed

- `01_INDEX.md` stayed unchanged because it is navigation-only.
- ACTIVE control JSON files deferred.

## Boundary

No API. No DB write. No schema change. No runtime change. No systemd change. No source token/key. No wallet/signing. No paper/live trade. AI authority 0.
"""
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    safe_write(OUT_DOC, md)
    safe_write(OUT_REPORT, md)

    print("OK_HOT_INGRESS_BINDING_SAFE_APPLY_DOCS_ONLY_WRITTEN")
    print("DECISION=" + result["decision"])
    print("UPDATED_FILE_COUNT=" + str(result["summary"]["updated_file_count"]))
    print("INDEX_CHANGED=false")
    print("ACTIVE_CONTROL_JSON_CHANGED=false")
    print("NEXT_STEP=" + result["next_step"])

if __name__ == "__main__":
    main()
