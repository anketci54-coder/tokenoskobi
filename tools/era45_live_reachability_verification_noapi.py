#!/usr/bin/env python3
import json, re, os, subprocess, datetime
from pathlib import Path

ROOT=Path.cwd()
NOW=datetime.datetime.now(datetime.UTC).isoformat()

OUT=ROOT/"data/control/era45_live_reachability_verification_noapi_v1.json"
MD=ROOT/"reports/LATEST_ERA45_LIVE_REACHABILITY_VERIFICATION_NOAPI.md"

def sh(cmd):
    r=subprocess.run(cmd,shell=True,cwd=ROOT,text=True,capture_output=True)
    return {"cmd":cmd,"rc":r.returncode,"stdout":r.stdout.strip(),"stderr":r.stderr.strip()}

def read(p, limit=1000000):
    f=ROOT/p
    return f.read_text(errors="replace")[:limit] if f.exists() else ""

def load_json(p):
    try:
        return json.loads(read(Path(p),3000000))
    except Exception:
        return {}

def grep(pattern, paths):
    out=[]
    rx=re.compile(pattern,re.I)
    for base in paths:
        b=ROOT/base
        if not b.exists(): continue
        for p in b.rglob("*"):
            if ".git" in p.parts or "archive" in p.parts: continue
            if p.is_file() and p.suffix in [".py",".json",".md",".service",".timer",".sh"]:
                try:
                    for i,l in enumerate(p.read_text(errors="replace").splitlines(),1):
                        if rx.search(l):
                            out.append({"path":str(p.relative_to(ROOT)),"line":i,"text":l[:240]})
                            if len(out)>=500: return out
                except Exception:
                    pass
    return out

def dir_stats(path):
    p=ROOT/path
    total=count=0
    if not p.exists(): return {"path":path,"exists":False,"files":0,"bytes":0}
    for f in p.rglob("*"):
        if ".git" in f.parts or "archive" in f.parts: continue
        if f.is_file():
            try:
                total+=f.stat().st_size; count+=1
            except Exception: pass
    return {"path":path,"exists":True,"files":count,"bytes":total}

runtime=load_json("PROJECT_RUNTIME.json")

services={}
for unit in [
    "tokenoskobi-news-radar-refresh.service",
    "tokenoskobi-news-radar-refresh.timer",
    "tokenoskobi-active-panel-8096.service",
    "coinoskobi-backpressure-refresh-runner.service",
    "coinoskobi-backpressure-refresh-runner.timer",
    "coinoskobi-system-control-status-refresh.service",
    "coinoskobi-system-control-status-refresh.timer"
]:
    services[unit]={
        "is_active":sh(f"systemctl is-active {unit} 2>/dev/null || true")["stdout"],
        "is_enabled":sh(f"systemctl is-enabled {unit} 2>/dev/null || true")["stdout"],
        "cat":sh(f"systemctl cat {unit} 2>/dev/null || true")["stdout"][:5000]
    }

processes={
    "python_tokenoskobi":sh("ps -eo pid,ppid,cmd | grep -E 'python3|python' | grep tokenoskobi | grep -v grep || true")["stdout"],
    "provider_vault":sh("ps -eo pid,ppid,cmd | grep provider_secret_vault_handler_v1 | grep -v grep || true")["stdout"],
    "news_runner":sh("ps -eo pid,ppid,cmd | grep news_radar_refresh_runner_v1 | grep -v grep || true")["stdout"],
    "panel_ports":sh("ss -lntp 2>/dev/null | grep -E ':8096|:8097' || true")["stdout"]
}

sqlite_files=[]
for p in ROOT.rglob("*"):
    if ".git" in p.parts or "archive" in p.parts: continue
    if p.is_file() and (p.name.endswith(".sqlite") or p.name.endswith(".db")):
        item={"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size}
        try:
            import sqlite3
            con=sqlite3.connect(f"file:{p}?mode=ro",uri=True,timeout=2)
            item["journal_mode"]=con.execute("PRAGMA journal_mode").fetchone()[0]
            item["busy_timeout"]=con.execute("PRAGMA busy_timeout").fetchone()[0]
            item["table_count"]=len(con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
            con.close()
        except Exception as e:
            item["error"]=str(e)
        sqlite_files.append(item)

large=[]
for p in ROOT.rglob("*"):
    if ".git" in p.parts or "archive" in p.parts: continue
    if p.is_file():
        try:
            s=p.stat().st_size
            if s>=5*1024*1024:
                large.append({"path":str(p.relative_to(ROOT)),"bytes":s})
        except Exception: pass
large=sorted(large,key=lambda x:x["bytes"],reverse=True)[:100]

public_hits=grep(r"/root/tokenoskobi_clean_v1|sk-or-v1|secret|private|mnemonic|seed_phrase|wallet_seed|provider_url|rpc_url|recommended_action|action_hint|operator_note", [Path("public"),Path("active_panel_8096/current/data")])
shell_hits=grep(r"shell=True|os\.system|subprocess\.run", [Path("tools"),Path("core"),Path("runtime"),Path("scripts")])
write_hits=grep(r"write_text|json\.dump|open\([^)]*['\"]w|INSERT INTO|UPDATE |DELETE FROM|CREATE TABLE|sqlite3\.connect", [Path("tools"),Path("core"),Path("runtime"),Path("scripts")])

# canonical block sync
canonical_block=f"""<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_START -->
# CURRENT CANONICAL STATE

- Updated UTC: {NOW}
- Current work unit: `ERA45_CODEX_FULL_VERIFICATION_AUDIT_NOAPI`
- Last completed step: `ERA45_LIVE_REACHABILITY_VERIFICATION_NOAPI`
- Next safe step: `ERA45_CONSOLIDATED_VERIFICATION_REVIEW_NOAPI`
- Rule: `PROJECT_RUNTIME.json` is the machine-readable source of truth.
- Note: older ERA mentions below this block are historical/archive context unless explicitly marked CURRENT in this block.
<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_END -->
"""
def sync_top_block(path):
    p=ROOT/path
    if not p.exists(): return False
    txt=p.read_text(errors="replace")
    rx=re.compile(r"<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_START -->.*?<!-- TOKENOSKOBI_CURRENT_CANONICAL_STATE_END -->",re.S)
    new=rx.sub(canonical_block.strip(),txt) if rx.search(txt) else canonical_block+"\n"+txt
    if new!=txt:
        p.write_text(new)
        return True
    return False

changed_docs=[p for p in ["06_PROJECT_MASTER_STATE.md","07_PROJECT_HANDOFF.md"] if sync_top_block(p)]

news_active = services.get("tokenoskobi-news-radar-refresh.timer",{}).get("is_active")=="active" or services.get("tokenoskobi-news-radar-refresh.service",{}).get("is_active")=="active"
provider_active = bool(processes["provider_vault"] or ":8097" in processes["panel_ports"])
panel_active = bool(":8096" in processes["panel_ports"] or services.get("tokenoskobi-active-panel-8096.service",{}).get("is_active")=="active")

findings=[]
if news_active:
    findings.append({"severity":"HIGH","id":"NEWS_RUNNER_REACHABLE","title":"News runner/timer appears active","decision":"REVIEW_BEFORE_ERA43_REAL_PLANNING"})
if provider_active:
    findings.append({"severity":"HIGH","id":"PROVIDER_VAULT_REACHABLE","title":"Provider vault appears active/listening","decision":"REVIEW_BEFORE_ERA43_REAL_PLANNING"})
if public_hits:
    findings.append({"severity":"MEDIUM","id":"PUBLIC_KEYWORD_HITS_REMAIN","title":"Public/active panel keyword hits remain","count":len(public_hits),"decision":"REVIEW"})
if large:
    findings.append({"severity":"MEDIUM","id":"NON_ARCHIVE_WATER_POOLING","title":"Large non-archive files remain","count":len(large),"decision":"BACKLOG_CLASSIFY"})
if shell_hits:
    findings.append({"severity":"MEDIUM","id":"SHELL_OR_SUBPROCESS_SURFACE","title":"shell/subprocess surface remains","count":len(shell_hits),"decision":"CLASSIFY_ACTIVE_MANUAL_DORMANT"})

high=[f for f in findings if f["severity"]=="HIGH"]
decision="WARN_ERA45_LIVE_REACHABILITY_VERIFICATION_NOAPI" if high else "PASS_ERA45_LIVE_REACHABILITY_VERIFICATION_NOAPI"
next_step="ERA45_REACHABILITY_RISK_REVIEW_NOAPI" if high else "ERA45_CONSOLIDATED_VERIFICATION_REVIEW_NOAPI"

report={
    "era":"ERA45",
    "phase":"LIVE_REACHABILITY_VERIFICATION_NOAPI",
    "created_at_utc":NOW,
    "decision":decision,
    "next_step":next_step,
    "era43_real_runtime_planning_allowed":False if high else "REVIEW_REQUIRED",
    "services":services,
    "processes":processes,
    "sqlite_files":sqlite_files,
    "public_hits_sample":public_hits[:80],
    "shell_hits_sample":shell_hits[:120],
    "write_hits_sample":write_hits[:160],
    "non_archive_large_files":large,
    "directory_stats":[dir_stats(x) for x in ["data","data/control","public","reports","docs","data/shadow_runtime_lab"]],
    "changed_docs":changed_docs,
    "findings":findings,
    "guards":{"external_api_calls":0,"live_trade":False,"wallet_action":False,"db_schema_change":False,"service_change":False,"nginx_change":False,"cleanup_performed":False}
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")

MD.parent.mkdir(parents=True,exist_ok=True)
lines=[
"# ERA45 LIVE REACHABILITY VERIFICATION NOAPI","",
f"- Created UTC: {NOW}",
f"- Decision: `{decision}`",
f"- Next step: `{next_step}`",
f"- News active: `{news_active}`",
f"- Provider vault active: `{provider_active}`",
f"- Panel active: `{panel_active}`",
f"- High findings: {len(high)}",
"",
"## Findings"
]
if findings:
    for f in findings:
        lines.append(f"- **{f['severity']} `{f['id']}`** — {f['title']} — `{f['decision']}`")
else:
    lines.append("- No high findings.")
MD.write_text("\n".join(lines)+"\n")

# runtime update
rtp=ROOT/"PROJECT_RUNTIME.json"
rt=json.loads(rtp.read_text())
wu={"id":"ERA45_CODEX_FULL_VERIFICATION_AUDIT_NOAPI","type":"CODEX_FULL_VERIFICATION_AUDIT","status":"WORK_UNIT_OPEN","last_completed_step":"ERA45_LIVE_REACHABILITY_VERIFICATION_NOAPI","next_step":next_step}
ns={"name":next_step,"status":"READY"}
rt["current_work_unit"]=wu
rt["next_safe_step"]=ns
rt["last_completed"]="ERA45_LIVE_REACHABILITY_VERIFICATION_NOAPI"
rt["status"]="WORK_UNIT_OPEN"
cs=rt.get("current_state") if isinstance(rt.get("current_state"),dict) else {}
cs["mode"]="ERA45_LIVE_REACHABILITY_VERIFICATION_DONE"
cs["current_problem"]="LIVE_REACHABILITY_RISK_REVIEW_REQUIRED" if high else None
cs["active_work_unit"]=wu
cs["next_safe_step"]=ns
cs["runtime_status"]="WORK_UNIT_OPEN"
cs["updated_at"]=NOW
rt["current_state"]=cs
rtp.write_text(json.dumps(rt,indent=2,ensure_ascii=False)+"\n")

print("DECISION:",decision)
print("NEXT_STEP:",next_step)
print("HIGH:",len(high))
print("NEWS_ACTIVE:",news_active)
print("PROVIDER_ACTIVE:",provider_active)
print("PANEL_ACTIVE:",panel_active)
