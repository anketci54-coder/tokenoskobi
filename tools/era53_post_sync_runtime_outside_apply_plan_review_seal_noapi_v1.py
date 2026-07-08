#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "ERA53_POST_SYNC_RUNTIME_OUTSIDE_APPLY_PLAN_REVIEW_SEAL_NOAPI"

OUT_JSON = ROOT / "data/control/era53_post_sync_runtime_outside_apply_plan_review_seal_noapi_v1.json"
OUT_DOC = ROOT / "docs/ERA53_POST_SYNC_RUNTIME_OUTSIDE_APPLY_PLAN_REVIEW_SEAL_NOAPI.md"
OUT_REPORT = ROOT / "reports/LATEST_ERA53_POST_SYNC_RUNTIME_OUTSIDE_APPLY_PLAN_REVIEW_SEAL_NOAPI.md"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def run_cmd(args):
    p = subprocess.run(args, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()

def safe_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def safe_write_json(path, obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    json.loads(text)
    safe_write(path, text)

def main():
    generated = now_iso()
    head_before = run_cmd(["git", "rev-parse", "HEAD"])

    result = {
        "stage": STAGE,
        "generated_at_utc": generated,
        "decision": "OK_ERA53_POST_SYNC_RUNTIME_OUTSIDE_APPLY_PLAN_REVIEW_SEALED",
        "next_step": "ERA53_POST_SYNC_RUNTIME_OUTSIDE_APPLY_DOCS_ONLY_NOAPI",
        "head_before": head_before,
        "current_era": "ERA53",
        "user_approval_received": True,
        "purpose": "Define the controlled runtime-outside apply path after ERA53 HOT ingress minimal contract consolidation.",
        "apply_scope": {
            "allowed": [
                "docs_only_canonical_references",
                "data_control_planning_artifacts",
                "non_runtime_index_references",
                "canonical_state_notes"
            ],
            "not_allowed": [
                "runtime_imports",
                "database_writes",
                "schema_changes",
                "systemd_changes",
                "source_adapters",
                "queues",
                "outbound_alarms",
                "wallet_or_signing",
                "paper_or_live_trade"
            ]
        },
        "active_control_files": {
            "ACTIVE_EXECUTION_GRAPH.json": "DEFERRED",
            "MINIMAL_ACTIVE_CORE_MANIFEST.json": "DEFERRED",
            "USED_BY_RUNTIME_INDEX.json": "DEFERRED",
            "ACTIVE_CORE_RANKING.json": "DEFERRED"
        },
        "workflow_policy": {
            "this_step": "PLAN_TO_REVIEW_SEAL",
            "next_docs_only_apply": "SERVER_MARKER_OR_DOCS_WRITE_THEN_GITHUB_SEAL",
            "runtime_or_db_or_service_change": "PLAN_TO_DRYRUN_TO_POST_AUDIT"
        },
        "authority": {
            "plan_review_seal_only": True,
            "noapi": True,
            "real_db_write": False,
            "db_schema_write": False,
            "runtime_change": False,
            "runtime_import": False,
            "systemd_change": False,
            "source_adapter_created": False,
            "queue_created": False,
            "outbound_alarm_created": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "ai_trade_authority": False,
            "tree_restructure": False,
            "repo_artifact_write": True
        },
        "review_result": {
            "user_approval_recorded": True,
            "apply_scope_defined": True,
            "docs_only_boundary_defined": True,
            "active_control_files_deferred": True,
            "boundary_clean": True
        },
        "summary": {
            "sealed": True,
            "fail_count": 0,
            "warn_count": 0
        }
    }

    safe_write_json(OUT_JSON, result)

    md = f"""# ERA53 Post Sync Runtime Outside Apply Plan Review Seal NOAPI

- stage: `{STAGE}`
- generated_at_utc: `{generated}`
- decision: `{result['decision']}`
- current_era: `ERA53`
- user_approval_received: `true`
- next_step: `{result['next_step']}`

## Scope

Allowed: docs-only canonical references, data/control planning artifacts, non-runtime index references, canonical state notes.

Deferred active control files:

- `ACTIVE_EXECUTION_GRAPH.json`
- `MINIMAL_ACTIVE_CORE_MANIFEST.json`
- `USED_BY_RUNTIME_INDEX.json`
- `ACTIVE_CORE_RANKING.json`

## Workflow Rule

- plan-only docs/contract: `PLAN_TO_REVIEW_SEAL`
- runtime/DB/service/code: `PLAN_TO_DRYRUN_TO_POST_AUDIT`

## Boundary

NOAPI. No DB/schema/runtime/systemd/source-adapter/queue/alarm/wallet/trade change. AI authority 0.

## Tree Rule

Existing tree preserved. No directory restructure, move, rename, archive, or new top-level directory.
"""
    safe_write(OUT_DOC, md)
    safe_write(OUT_REPORT, md)

    print("OK_ERA53_POST_SYNC_RUNTIME_OUTSIDE_APPLY_PLAN_REVIEW_SEAL_WRITTEN")
    print("DECISION=" + result["decision"])
    print("NEXT_STEP=" + result["next_step"])

if __name__ == "__main__":
    main()
