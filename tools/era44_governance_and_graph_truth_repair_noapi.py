#!/usr/bin/env python3
import json, re, datetime
from pathlib import Path

ROOT = Path.cwd()
NOW = datetime.datetime.now(datetime.UTC).isoformat()

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
GRAPH = ROOT / "data/control/ACTIVE_EXECUTION_GRAPH.json"
USED = ROOT / "data/control/USED_BY_RUNTIME_INDEX.json"
OUT = ROOT / "data/control/era44_governance_and_graph_truth_repair_noapi_v1.json"
MD = ROOT / "reports/LATEST_ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI.md"

rt = json.loads(RUNTIME.read_text())

current_wu = {
    "id": "ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI",
    "type": "PUBLIC_EXPOSURE_BOUNDARY_FIX",
    "status": "WORK_UNIT_OPEN",
    "last_completed_step": "ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI",
    "next_step": "ERA44_GOVERNANCE_AND_GRAPH_TRUTH_POST_REPAIR_AUDIT_NOAPI"
}
next_safe = {
    "name": "ERA44_GOVERNANCE_AND_GRAPH_TRUTH_POST_REPAIR_AUDIT_NOAPI",
    "status": "READY"
}

# PROJECT_RUNTIME sync
rt["current_work_unit"] = current_wu
rt["next_safe_step"] = next_safe
rt["last_completed"] = "ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI"
rt["status"] = "WORK_UNIT_OPEN"
cs = rt.get("current_state") if isinstance(rt.get("current_state"), dict) else {}
cs["project_status"] = "ACTIVE"
cs["mode"] = "ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_ACTIVE"
cs["current_problem"] = "GOVERNANCE_DRIFT_AND_STATIC_EXECUTION_GRAPH"
cs["active_work_unit"] = current_wu
cs["next_safe_step"] = next_safe
cs["runtime_status"] = "WORK_UNIT_OPEN"
cs["updated_at"] = NOW
rt["current_state"] = cs
RUNTIME.write_text(json.dumps(rt, indent=2, ensure_ascii=False) + "\n")

canonical_block = f"""<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_START -->
# CURRENT CANONICAL STATE

- Updated UTC: {NOW}
- Current work unit: `ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI`
- Last completed step: `ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI`
- Next safe step: `ERA44_GOVERNANCE_AND_GRAPH_TRUTH_POST_REPAIR_AUDIT_NOAPI`
- Rule: `PROJECT_RUNTIME.json` is the machine-readable source of truth.
- Note: older ERA mentions below this block are historical/archive context unless explicitly marked CURRENT in this block.
<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_END -->
"""

def replace_block(text):
    rx = re.compile(
        r"<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_START -->.*?<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_END -->",
        re.S
    )
    if rx.search(text):
        return rx.sub(canonical_block.strip(), text)
    return canonical_block + "\n" + text

def neutralize_current_markers(text):
    lines = []
    for line in text.splitlines():
        if re.match(r"^\s*CURRENT_ERA\s*=", line):
            lines.append("CURRENT_ERA=ERA44")
        elif re.match(r"^\s*CURRENT_WORK_UNIT\s*=", line):
            lines.append("CURRENT_WORK_UNIT=ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI")
        elif re.match(r"^\s*NEXT_SAFE_STEP\s*=", line):
            lines.append("NEXT_SAFE_STEP=ERA44_GOVERNANCE_AND_GRAPH_TRUTH_POST_REPAIR_AUDIT_NOAPI")
        elif re.match(r"^\s*LAST_COMPLETED\s*=", line):
            lines.append("LAST_COMPLETED=ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI")
        else:
            lines.append(line)
    return "\n".join(lines) + "\n"

changed_docs = []
for p in [MASTER, HANDOFF]:
    if p.exists():
        old = p.read_text(errors="replace")
        new = neutralize_current_markers(replace_block(old))
        if new != old:
            p.write_text(new)
            changed_docs.append(str(p.relative_to(ROOT)))

# Mark static graph honestly, do not invent runtime edges
graph_status = "MISSING"
if GRAPH.exists():
    g = json.loads(GRAPH.read_text())
    graph_status = g.get("status")
    g["status"] = "STATIC_INVENTORY_NOT_RUNTIME_PROOF"
    g["runtime_proof_reliable"] = False
    g["truth_warning"] = "This file is a static/generated inventory and MUST NOT be used as proof of real runtime reachability."
    g["updated_at"] = NOW
    g.setdefault("edges", g.get("edges", []))
    GRAPH.write_text(json.dumps(g, indent=2, ensure_ascii=False) + "\n")

used_status = "MISSING"
if USED.exists():
    u = json.loads(USED.read_text())
    used_status = u.get("status")
    u["status"] = "STATIC_INDEX_NOT_RUNTIME_PROOF"
    u["runtime_proof_reliable"] = False
    u["truth_warning"] = "This file lists suspected/known references only. It is not proof that a component is executed by runtime."
    u["updated_at"] = NOW
    USED.write_text(json.dumps(u, indent=2, ensure_ascii=False) + "\n")

report = {
    "era": "ERA44",
    "phase": "GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI",
    "created_at_utc": NOW,
    "actions": [
        "PROJECT_RUNTIME synchronized to ERA44 governance/graph truth repair state",
        "06_PROJECT_MASTER_STATE.md and 07_PROJECT_HANDOFF.md received current canonical state block",
        "CURRENT_* marker lines were normalized where present",
        "ACTIVE_EXECUTION_GRAPH marked as STATIC_INVENTORY_NOT_RUNTIME_PROOF",
        "USED_BY_RUNTIME_INDEX marked as STATIC_INDEX_NOT_RUNTIME_PROOF"
    ],
    "changed_docs": changed_docs,
    "previous_graph_status": graph_status,
    "previous_used_by_runtime_status": used_status,
    "decision": "PASS_ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI",
    "next_step": "ERA44_GOVERNANCE_AND_GRAPH_TRUTH_POST_REPAIR_AUDIT_NOAPI",
    "guards": {
        "external_api_calls": 0,
        "live_trade": False,
        "wallet_action": False,
        "db_schema_change": False,
        "service_change": False,
        "nginx_change": False,
        "cleanup_performed": False,
        "runtime_edges_invented": False
    }
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

MD.parent.mkdir(parents=True, exist_ok=True)
MD.write_text(
    "# ERA44 GOVERNANCE AND GRAPH TRUTH REPAIR NOAPI\n\n"
    f"- Created UTC: {NOW}\n"
    "- Decision: `PASS_ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI`\n"
    "- Next step: `ERA44_GOVERNANCE_AND_GRAPH_TRUTH_POST_REPAIR_AUDIT_NOAPI`\n"
    "- Runtime edges invented: `False`\n"
    "- Service/DB/schema/nginx mutation: `False`\n\n"
    "## Scope\n\n"
    "This repair does not claim that runtime reachability is proven. It explicitly marks generated graph/index files as static inventory, not runtime proof.\n"
)

print("DECISION: PASS_ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI")
print("NEXT_STEP: ERA44_GOVERNANCE_AND_GRAPH_TRUTH_POST_REPAIR_AUDIT_NOAPI")
print("CHANGED_DOCS:", changed_docs)
