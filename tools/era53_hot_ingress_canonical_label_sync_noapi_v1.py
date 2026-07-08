#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, subprocess, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "ERA53_HOT_INTELLIGENCE_INGRESS_GATEWAY_CANONICAL_LABEL_SYNC_NOAPI"

FILES_TO_UPDATE = [
    ROOT / "06_PROJECT_MASTER_STATE.md",
    ROOT / "07_PROJECT_HANDOFF.md",
]

OUT_JSON = ROOT / "data/control/era53_hot_ingress_canonical_label_sync_noapi_v1.json"
OUT_DOC = ROOT / "docs/ERA53_HOT_INGRESS_CANONICAL_LABEL_SYNC_NOAPI.md"
OUT_REPORT = ROOT / "reports/LATEST_ERA53_HOT_INGRESS_CANONICAL_LABEL_SYNC_NOAPI.md"

START = "<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_START -->"
END = "<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_END -->"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def run_cmd(args):
    p = subprocess.run(args, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.strip()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def safe_write_json(path, obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    json.loads(text)
    safe_write(path, text)

def replace_block(path, new_block):
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise RuntimeError("marker_missing:" + str(path))
    before, rest = text.split(START, 1)
    old_body, after = rest.split(END, 1)
    old_block = START + old_body + END
    new_text = before + new_block + after
    changed = new_text != text
    if changed:
        safe_write(path, new_text)
    return {
        "path": str(path.relative_to(ROOT)),
        "changed": changed,
        "old_block_sha256": hashlib.sha256(old_block.encode("utf-8")).hexdigest(),
        "new_block_sha256": hashlib.sha256(new_block.encode("utf-8")).hexdigest(),
        "file_sha256_after": sha256_file(path)
    }

def main():
    generated = now_iso()
    head_before = run_cmd(["git", "rev-parse", "HEAD"])

    new_block = f"""{START}
# CURRENT CANONICAL STATE

- Updated UTC: {generated}
- Current ERA: `ERA53`
- ERA52 status: `CLOSED_VERIFIED`
- ERA53 line: `HOT_INTELLIGENCE_INGRESS_GATEWAY`
- Last completed: `HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_CONTRACT_POST_AUDIT_NOAPI`
- Current focus: `ERA53_HOT_INGRESS_TRUST_RATE_POLICY_MINIMAL_PLAN_NOAPI`
- Runtime authority: `PROJECT_RUNTIME.json`
- Canonical source of truth: local server + GitHub main seal.
- HOT ingress status: contract, source registry plan, source registry dryrun, and source registry post-audit completed.
- HOT ingress boundary: planned canonical architecture only; no live source adapter yet.
- Tree/directory rule: existing tree preserved; no directory restructure, no move, no archive, no rename.
- Deferred active control files: `ACTIVE_EXECUTION_GRAPH.json`, `MINIMAL_ACTIVE_CORE_MANIFEST.json`, `USED_BY_RUNTIME_INDEX.json`, `ACTIVE_CORE_RANKING.json`.
- NOAPI boundary: no API, no DB write, no schema change, no runtime change, no systemd change, no source token/key, no wallet/signing, no paper/live trade, AI authority 0.
- Workflow preference: GitHub first when possible; otherwise single paste-and-run command block.
- Next safe step: `ERA53_HOT_INGRESS_TRUST_RATE_POLICY_MINIMAL_PLAN_NOAPI`
{END}"""

    updates = [replace_block(p, new_block) for p in FILES_TO_UPDATE]

    result = {
        "stage": STAGE,
        "generated_at_utc": generated,
        "decision": "OK_ERA53_HOT_INTELLIGENCE_INGRESS_GATEWAY_CANONICAL_LABEL_SYNCED",
        "next_step": "ERA53_HOT_INGRESS_TRUST_RATE_POLICY_MINIMAL_PLAN_NOAPI",
        "head_before": head_before,
        "current_era": "ERA53",
        "previous_era": "ERA52",
        "era52_status": "CLOSED_VERIFIED",
        "era53_line": "HOT_INTELLIGENCE_INGRESS_GATEWAY",
        "tree_directory_policy": {
            "tree_restructure": False,
            "directory_move": False,
            "directory_rename": False,
            "new_top_level_directory": False,
            "existing_tree_preserved": True
        },
        "authority": {
            "label_sync_only": True,
            "noapi": True,
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
        "updated_files": updates,
        "summary": {
            "updated_file_count": sum(1 for x in updates if x["changed"]),
            "fail_count": 0,
            "warn_count": 0
        }
    }

    safe_write_json(OUT_JSON, result)

    md = f"""# ERA53 HOT Ingress Canonical Label Sync NOAPI

- stage: `{STAGE}`
- generated_at_utc: `{generated}`
- decision: `{result['decision']}`
- current_era: `ERA53`
- previous_era: `ERA52`
- era53_line: `HOT_INTELLIGENCE_INGRESS_GATEWAY`
- next_step: `{result['next_step']}`

## Tree Rule

Existing tree preserved. No directory restructure, move, rename, archive, or new top-level directory.

## Boundary

No API. No DB write. No schema change. No runtime change. No systemd change. No source token/key. No wallet/signing. No paper/live trade. AI authority 0.
"""
    safe_write(OUT_DOC, md)
    safe_write(OUT_REPORT, md)

    print("OK_ERA53_HOT_INGRESS_CANONICAL_LABEL_SYNC_WRITTEN")
    print("DECISION=" + result["decision"])
    print("CURRENT_ERA=ERA53")
    print("NEXT_STEP=" + result["next_step"])

if __name__ == "__main__":
    main()
