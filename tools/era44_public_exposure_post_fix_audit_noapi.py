#!/usr/bin/env python3
import json, re, datetime, subprocess
from pathlib import Path

ROOT=Path.cwd()
NOW=datetime.datetime.now(datetime.UTC).isoformat()

OUT_JSON=ROOT/"data/control/era44_public_exposure_post_fix_audit_noapi_v1.json"
OUT_MD=ROOT/"reports/LATEST_ERA44_PUBLIC_EXPOSURE_POST_FIX_AUDIT_NOAPI.md"

def read(p, limit=500000):
    f=ROOT/p
    if not f.exists():
        return ""
    return f.read_text(errors="replace")[:limit]

def load_json(p):
    try:
        return json.loads(read(Path(p), 2000000))
    except Exception:
        return None

def sh(cmd):
    r=subprocess.run(cmd,cwd=ROOT,shell=True,text=True,capture_output=True)
    return r.stdout.strip()

runtime=load_json("PROJECT_RUNTIME.json") or {}
graph=load_json("data/control/ACTIVE_EXECUTION_GRAPH.json") or {}
used=load_json("data/control/USED_BY_RUNTIME_INDEX.json") or {}

public_hits=[]
rx=re.compile(r"/root/tokenoskobi_clean_v1|localhost|systemctl|nginx|sk-or-v1|secret|private|mnemonic|seed_phrase|wallet_seed|provider_url|rpc_url|recommended_action|action_hint|operator_note",re.I)

for base in [ROOT/"public", ROOT/"active_panel_8096/current/data"]:
    if base.exists():
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in [".json",".html",".txt",".md"]:
                txt=p.read_text(errors="replace")[:300000]
                for i,line in enumerate(txt.splitlines(),1):
                    if rx.search(line) and "[REDACTED_PUBLIC_BOUNDARY]" not in line:
                        public_hits.append({"path":str(p.relative_to(ROOT)),"line":i,"text":line[:220]})
                        if len(public_hits)>=200:
                            break

canonical_files=["PROJECT_RUNTIME.json","PROJECT_HISTORY.json","03_ROADMAP.md","04_ALMANAC.md","05_ATLAS.md","06_PROJECT_MASTER_STATE.md","07_PROJECT_HANDOFF.md","README.md","PROJECT_BOOT.json"]
canonical={}
for f in canonical_files:
    txt=read(Path(f),600000)
    canonical[f]={
        "exists":bool(txt),
        "era20_mentions":len(re.findall(r"ERA20",txt)),
        "era23_mentions":len(re.findall(r"ERA23",txt)),
        "era42_mentions":len(re.findall(r"ERA42",txt)),
        "era43_mentions":len(re.findall(r"ERA43",txt)),
        "era44_mentions":len(re.findall(r"ERA44",txt)),
        "current_era_like_lines":[
            line[:240] for line in txt.splitlines()
            if re.search(r"CURRENT_ERA|NEXT_SAFE_STEP|LAST_COMPLETED|WORK_UNIT|ERA44|ERA43",line)
        ][:60]
    }

current_work_unit=runtime.get("current_work_unit",{})
current_state=runtime.get("current_state",{}) if isinstance(runtime.get("current_state"),dict) else {}
runtime_sync_ok=(current_work_unit==current_state.get("active_work_unit") and runtime.get("next_safe_step")==current_state.get("next_safe_step"))

graph_edges=graph.get("edges")
graph_status=graph.get("status")
graph_producer=graph.get("producer")
graph_reliable=bool(graph_edges) and graph_status not in ("MINIMAL_STATIC_GRAPH","STATIC","STATIC_INVENTORY")

findings=[]
if public_hits:
    findings.append({
        "severity":"HIGH",
        "id":"ERA44_PUBLIC_EXPOSURE_REMAINING_HITS",
        "title":"Public exposure keyword hits remain after fix",
        "evidence":public_hits[:50],
        "decision":"MUST_REVIEW"
    })

if not runtime_sync_ok:
    findings.append({
        "severity":"HIGH",
        "id":"ERA44_RUNTIME_SYNC_DRIFT",
        "title":"PROJECT_RUNTIME top-level and current_state are not synchronized",
        "evidence":{"top":current_work_unit,"current_state":current_state.get("active_work_unit")},
        "decision":"MUST_FIX"
    })

if canonical["06_PROJECT_MASTER_STATE.md"]["era20_mentions"] or canonical["06_PROJECT_MASTER_STATE.md"]["era23_mentions"]:
    findings.append({
        "severity":"HIGH",
        "id":"ERA44_MASTER_STATE_STALE_ERA_MARKERS",
        "title":"06_PROJECT_MASTER_STATE.md contains stale ERA20/ERA23 markers",
        "evidence":canonical["06_PROJECT_MASTER_STATE.md"]["current_era_like_lines"][:40],
        "decision":"MUST_FIX_OR_MARK_ARCHIVAL"
    })

if not graph_reliable:
    findings.append({
        "severity":"HIGH",
        "id":"ERA44_EXECUTION_GRAPH_NOT_RUNTIME_PROOF",
        "title":"ACTIVE_EXECUTION_GRAPH is static/minimal and cannot be used as runtime proof",
        "evidence":{"producer":graph_producer,"status":graph_status,"edge_count":len(graph_edges) if isinstance(graph_edges,list) else None},
        "decision":"MUST_MARK_AS_STATIC_OR_REPAIR"
    })

critical=[f for f in findings if f["severity"]=="CRITICAL"]
high=[f for f in findings if f["severity"]=="HIGH"]

decision="FAIL_ERA44_PUBLIC_EXPOSURE_POST_FIX_AUDIT_NOAPI" if critical else ("WARN_ERA44_PUBLIC_EXPOSURE_POST_FIX_AUDIT_NOAPI" if high else "PASS_ERA44_PUBLIC_EXPOSURE_POST_FIX_AUDIT_NOAPI")
next_step="ERA44_GOVERNANCE_AND_GRAPH_TRUTH_REPAIR_NOAPI" if high else "ERA43_REAL_RUN_PLAN_NOAPI"

report={
    "era":"ERA44",
    "phase":"PUBLIC_EXPOSURE_BOUNDARY_POST_FIX_AUDIT_NOAPI",
    "created_at_utc":NOW,
    "public_exposure_remaining_hits":public_hits,
    "public_exposure_status":"WARN_REMAINING_HITS" if public_hits else "PASS_NO_UNREDACTED_PUBLIC_KEYWORD_HITS_FOUND",
    "runtime_sync_ok":runtime_sync_ok,
    "current_work_unit":current_work_unit,
    "next_safe_step":runtime.get("next_safe_step"),
    "canonical_scan":canonical,
    "execution_graph": {
        "producer":graph_producer,
        "status":graph_status,
        "edge_count":len(graph_edges) if isinstance(graph_edges,list) else None,
        "runtime_proof_reliable":graph_reliable
    },
    "used_by_runtime_index_count": len(used.get("used_by_runtime",[])) if isinstance(used.get("used_by_runtime"),list) else None,
    "findings":findings,
    "decision":decision,
    "next_step":next_step,
    "era43_real_run_allowed": next_step=="ERA43_REAL_RUN_PLAN_NOAPI",
    "guards":{
        "external_api_calls":0,
        "live_trade":False,
        "wallet_action":False,
        "db_schema_change":False,
        "service_change":False,
        "nginx_change":False,
        "cleanup_performed":False,
        "project_scripts_executed":False
    }
}

OUT_JSON.parent.mkdir(parents=True,exist_ok=True)
OUT_JSON.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")

OUT_MD.parent.mkdir(parents=True,exist_ok=True)
lines=[
"# ERA44 PUBLIC EXPOSURE POST FIX AUDIT NOAPI",
"",
f"- Created UTC: {NOW}",
f"- Decision: `{decision}`",
f"- Public exposure status: `{report['public_exposure_status']}`",
f"- Runtime sync OK: `{runtime_sync_ok}`",
f"- Execution graph runtime proof reliable: `{graph_reliable}`",
f"- Next step: `{next_step}`",
f"- ERA43 real run allowed: `{report['era43_real_run_allowed']}`",
"",
"## Findings"
]
if findings:
    for f in findings:
        lines.append(f"- **{f['severity']} `{f['id']}`** — {f['title']} — `{f['decision']}`")
else:
    lines.append("- No findings.")
OUT_MD.write_text("\n".join(lines)+"\n")

rtp=ROOT/"PROJECT_RUNTIME.json"
rt=json.loads(rtp.read_text())
wu={
 "id":"ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI",
 "type":"PUBLIC_EXPOSURE_BOUNDARY_FIX",
 "status":"WORK_UNIT_OPEN",
 "last_completed_step":"ERA44_PUBLIC_EXPOSURE_BOUNDARY_POST_FIX_AUDIT_NOAPI",
 "next_step":next_step
}
ns={"name":next_step,"status":"READY"}
rt["current_work_unit"]=wu
rt["next_safe_step"]=ns
cs=rt.get("current_state") if isinstance(rt.get("current_state"),dict) else {}
cs["active_work_unit"]=wu
cs["next_safe_step"]=ns
cs["runtime_status"]="WORK_UNIT_OPEN"
cs["updated_at"]=NOW
rt["current_state"]=cs
rt["last_completed"]="ERA44_PUBLIC_EXPOSURE_BOUNDARY_POST_FIX_AUDIT_NOAPI"
rt["status"]="WORK_UNIT_OPEN"
rtp.write_text(json.dumps(rt,indent=2,ensure_ascii=False)+"\n")

print("DECISION:",decision)
print("PUBLIC_HITS:",len(public_hits))
print("FINDINGS:",len(findings))
print("NEXT_STEP:",next_step)
