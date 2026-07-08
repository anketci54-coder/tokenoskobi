#!/usr/bin/env python3
import json, time, datetime, subprocess, os, re, sqlite3
from pathlib import Path

ROOT=Path.cwd()
NOW=datetime.datetime.now(datetime.UTC).isoformat()
OUT=ROOT/"data/control/era45_reachability_fix_and_speed_baseline_noapi_v1.json"
MD=ROOT/"reports/LATEST_ERA45_REACHABILITY_FIX_AND_SPEED_BASELINE_NOAPI.md"

def tcall(name, fn):
    t0=time.perf_counter()
    try:
        val=fn()
        ok=True
        err=None
    except Exception as e:
        val=None
        ok=False
        err=str(e)
    dt=(time.perf_counter()-t0)*1000
    return {"name":name,"ok":ok,"ms":round(dt,3),"value":val,"error":err}

def sh(cmd):
    r=subprocess.run(cmd,shell=True,cwd=ROOT,text=True,capture_output=True)
    return {"cmd":cmd,"rc":r.returncode,"stdout":r.stdout.strip(),"stderr":r.stderr.strip()}

def files_under(paths, suffixes=None, exclude_archive=True):
    out=[]
    for base in paths:
        b=ROOT/base
        if not b.exists():
            continue
        for p in b.rglob("*"):
            if ".git" in p.parts:
                continue
            if exclude_archive and "archive" in p.parts:
                continue
            if p.is_file() and (suffixes is None or p.suffix.lower() in suffixes):
                out.append(p)
    return out

def scan_regex(paths, pattern, suffixes=None, max_hits=500):
    rx=re.compile(pattern,re.I)
    hits=[]
    count=0
    for p in files_under(paths,suffixes):
        count+=1
        try:
            for i,l in enumerate(p.read_text(errors="replace").splitlines(),1):
                if rx.search(l):
                    hits.append({"path":str(p.relative_to(ROOT)),"line":i,"text":l[:220]})
                    if len(hits)>=max_hits:
                        return {"files_scanned":count,"hits":hits}
        except Exception:
            pass
    return {"files_scanned":count,"hits":hits}

def parse_json_surface():
    files=files_under([Path("data/control"),Path("public"),Path("active_panel_8096/current/data")],{".json"})
    ok=fail=0
    total_bytes=0
    for p in files:
        total_bytes+=p.stat().st_size
        try:
            json.loads(p.read_text(errors="replace"))
            ok+=1
        except Exception:
            fail+=1
    return {"json_files":len(files),"ok":ok,"fail":fail,"bytes":total_bytes}

def compile_active_tools():
    candidates=[
        "tools/news_radar_refresh_runner_v1.py",
        "tools/provider_secret_vault_handler_v1.py",
        "tools/panel_public_readmodel_bridge_v1.py",
        "tools/panel_live_readmodel_builder_v1.py",
        "tools/system_center_live_producer_v1.py",
        "tools/onchain_center_live_producer_v1.py",
        "tools/risk_center_live_producer_v1.py",
        "tools/command_center_live_producer_v1.py",
        "tools/news_token_matcher_v1.py",
        "tools/era_close.py"
    ]
    res=[]
    for f in candidates:
        p=ROOT/f
        if p.exists():
            r=subprocess.run(["python3","-m","py_compile",f],cwd=ROOT,text=True,capture_output=True)
            res.append({"path":f,"rc":r.returncode,"stderr":r.stderr[-500:]})
    return res

def sqlite_readonly():
    arr=[]
    for p in files_under([Path(".")],None):
        if p.name.endswith(".sqlite") or p.name.endswith(".db"):
            item={"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size}
            try:
                con=sqlite3.connect(f"file:{p}?mode=ro",uri=True,timeout=2)
                t0=time.perf_counter()
                item["journal_mode"]=con.execute("PRAGMA journal_mode").fetchone()[0]
                item["busy_timeout"]=con.execute("PRAGMA busy_timeout").fetchone()[0]
                tables=con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                item["table_count"]=len(tables)
                item["metadata_ms"]=round((time.perf_counter()-t0)*1000,3)
                con.close()
            except Exception as e:
                item["error"]=str(e)
            arr.append(item)
    return arr

def large_non_archive():
    arr=[]
    for p in files_under([Path(".")],None):
        try:
            s=p.stat().st_size
            if s>=5*1024*1024:
                arr.append({"path":str(p.relative_to(ROOT)),"bytes":s})
        except Exception:
            pass
    return sorted(arr,key=lambda x:x["bytes"],reverse=True)[:80]

def dir_stats(path):
    p=ROOT/path
    total=count=0
    if not p.exists():
        return {"path":path,"exists":False,"files":0,"bytes":0}
    for f in p.rglob("*"):
        if ".git" in f.parts or "archive" in f.parts:
            continue
        if f.is_file():
            try:
                count+=1
                total+=f.stat().st_size
            except Exception:
                pass
    return {"path":path,"exists":True,"files":count,"bytes":total}

checks={
 "news_service_active":sh("systemctl is-active tokenoskobi-news-radar-refresh.service 2>/dev/null || true"),
 "news_timer_active":sh("systemctl is-active tokenoskobi-news-radar-refresh.timer 2>/dev/null || true"),
 "news_process":sh("ps -eo pid,ppid,cmd | grep news_radar_refresh_runner_v1 | grep -v grep || true"),
 "provider_process":sh("ps -eo pid,ppid,cmd | grep provider_secret_vault_handler_v1 | grep -v grep || true"),
 "provider_port":sh("ss -lntp 2>/dev/null | grep ':8097' || true"),
 "panel_port":sh("ss -lntp 2>/dev/null | grep ':8096' || true"),
 "git_status":sh("git status --short"),
 "git_head":sh("git rev-parse HEAD")
}

news_active=checks["news_service_active"]["stdout"]=="active" or checks["news_timer_active"]["stdout"]=="active" or bool(checks["news_process"]["stdout"])
provider_active=bool(checks["provider_process"]["stdout"]) or bool(checks["provider_port"]["stdout"])

bench=[
    tcall("compile_active_tools", compile_active_tools),
    tcall("parse_json_surface", parse_json_surface),
    tcall("sqlite_readonly_metadata", sqlite_readonly),
    tcall("scan_public_leakage_keywords", lambda: scan_regex([Path("public"),Path("active_panel_8096/current/data")], r"/root/tokenoskobi_clean_v1|sk-or-v1|secret|private|mnemonic|seed_phrase|wallet_seed|provider_url|rpc_url|recommended_action|action_hint|operator_note", {".json",".html",".txt",".md"})),
    tcall("scan_shell_subprocess_surface", lambda: scan_regex([Path("tools"),Path("core"),Path("runtime"),Path("scripts")], r"shell=True|os\\.system|subprocess\\.run", {".py",".sh"})),
    tcall("scan_write_mutation_surface", lambda: scan_regex([Path("tools"),Path("core"),Path("runtime"),Path("scripts")], r"write_text|json\\.dump|open\\([^)]*['\\\"]w|INSERT INTO|UPDATE |DELETE FROM|CREATE TABLE|sqlite3\\.connect", {".py",".sh"})),
    tcall("large_non_archive_files", large_non_archive),
]

findings=[]
if news_active:
    findings.append({"severity":"HIGH","id":"NEWS_RUNNER_ACTIVE","decision":"ERA43_REAL_PLANNING_BLOCKED_UNTIL_GATE_OR_DISABLE"})
if provider_active:
    findings.append({"severity":"HIGH","id":"PROVIDER_VAULT_ACTIVE","decision":"ERA43_REAL_PLANNING_BLOCKED_UNTIL_GATE_OR_DISABLE"})

large=bench[-1]["value"] or []
if large:
    findings.append({"severity":"MEDIUM","id":"WATER_POOLING_NON_ARCHIVE","decision":"BACKLOG_CLASSIFY","count":len(large)})

high=[f for f in findings if f["severity"]=="HIGH"]
decision="WARN_ERA45_REACHABILITY_FIX_AND_SPEED_BASELINE_BLOCKERS_REMAIN" if high else "PASS_ERA45_REACHABILITY_FIX_AND_SPEED_BASELINE_NO_ACTIVE_BLOCKERS"
next_step="ERA45_REACHABILITY_FIX_OR_GATE_REQUIRED_NOAPI" if high else "ERA45_CONSOLIDATED_VERIFICATION_REVIEW_NOAPI"

report={
 "era":"ERA45",
 "phase":"REACHABILITY_FIX_AND_SPEED_BASELINE_NOAPI",
 "created_at_utc":NOW,
 "decision":decision,
 "next_step":next_step,
 "news_active":news_active,
 "provider_active":provider_active,
 "checks":checks,
 "benchmarks":bench,
 "directory_stats":[dir_stats(x) for x in ["data","data/control","public","reports","docs","data/shadow_runtime_lab"]],
 "findings":findings,
 "era43_real_runtime_planning_allowed":False if high else "REVIEW_REQUIRED",
 "guards":{"external_api_calls":0,"live_trade":False,"wallet_action":False,"db_schema_change":False,"service_change":False,"nginx_change":False,"cleanup_performed":False}
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")

lines=[
"# ERA45 REACHABILITY FIX AND SPEED BASELINE NOAPI","",
f"- Created UTC: {NOW}",
f"- Decision: `{decision}`",
f"- Next step: `{next_step}`",
f"- News active: `{news_active}`",
f"- Provider active: `{provider_active}`",
f"- High findings: {len(high)}",
"",
"## Speed Baseline"
]
for b in bench:
    lines.append(f"- `{b['name']}`: `{b['ms']} ms`, ok=`{b['ok']}`")
lines += ["","## Findings"]
if findings:
    for f in findings:
        lines.append(f"- **{f['severity']} `{f['id']}`** — `{f['decision']}`")
else:
    lines.append("- No high reachability blockers.")
MD.parent.mkdir(parents=True,exist_ok=True)
MD.write_text("\n".join(lines)+"\n")

rtp=ROOT/"PROJECT_RUNTIME.json"
rt=json.loads(rtp.read_text())
wu={"id":"ERA45_CODEX_FULL_VERIFICATION_AUDIT_NOAPI","type":"CODEX_FULL_VERIFICATION_AUDIT","status":"WORK_UNIT_OPEN","last_completed_step":"ERA45_REACHABILITY_FIX_AND_SPEED_BASELINE_NOAPI","next_step":next_step}
ns={"name":next_step,"status":"READY"}
rt["current_work_unit"]=wu
rt["next_safe_step"]=ns
rt["last_completed"]="ERA45_REACHABILITY_FIX_AND_SPEED_BASELINE_NOAPI"
rt["status"]="WORK_UNIT_OPEN"
cs=rt.get("current_state") if isinstance(rt.get("current_state"),dict) else {}
cs["mode"]="ERA45_REACHABILITY_FIX_AND_SPEED_BASELINE_DONE"
cs["current_problem"]="REACHABILITY_BLOCKERS_REMAIN" if high else None
cs["active_work_unit"]=wu
cs["next_safe_step"]=ns
cs["runtime_status"]="WORK_UNIT_OPEN"
cs["updated_at"]=NOW
rt["current_state"]=cs
rtp.write_text(json.dumps(rt,indent=2,ensure_ascii=False)+"\n")

print("DECISION:",decision)
print("NEXT_STEP:",next_step)
print("NEWS_ACTIVE:",news_active)
print("PROVIDER_ACTIVE:",provider_active)
print("HIGH:",len(high))
for b in bench:
    print("BENCH:",b["name"],b["ms"],"ms", "OK" if b["ok"] else "FAIL")
