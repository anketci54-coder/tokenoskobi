#!/usr/bin/env python3
import json, os, re, sqlite3, subprocess, datetime
from pathlib import Path

ROOT = Path.cwd()
NOW = datetime.datetime.now(datetime.UTC).isoformat()

OUT_JSON = ROOT / "data/control/era43_preflight_readonly_audit_noapi_v1.json"
OUT_MD = ROOT / "reports/LATEST_ERA43_PREFLIGHT_READONLY_AUDIT_NOAPI.md"

def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

def read(path, limit=200000):
    p = ROOT / path
    if not p.exists() or not p.is_file():
        return ""
    return p.read_text(errors="replace")[:limit]

def load_json(path):
    try:
        return json.loads(read(path, 1000000))
    except Exception:
        return None

def walk_files(base, suffixes=None):
    basep = ROOT / base
    if not basep.exists():
        return []
    out = []
    for p in basep.rglob("*"):
        if ".git" in p.parts:
            continue
        if p.is_file() and (suffixes is None or p.suffix in suffixes):
            out.append(p)
    return sorted(out)

def rel(p):
    return str(p.relative_to(ROOT))

def grep_files(files, patterns, max_hits=500):
    hits = []
    rx = re.compile(patterns)
    for p in files:
        try:
            for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if rx.search(line):
                    hits.append({"path": rel(p), "line": i, "text": line[:260]})
                    if len(hits) >= max_hits:
                        return hits
        except Exception:
            pass
    return hits

def dir_size(path):
    p = ROOT / path
    total = 0
    count = 0
    if not p.exists():
        return {"path": path, "exists": False, "bytes": 0, "files": 0}
    for f in p.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
                count += 1
            except Exception:
                pass
    return {"path": path, "exists": True, "bytes": total, "files": count}

py_files = []
for base in ["tools", "core", "runtime", "scripts"]:
    py_files.extend(walk_files(base, {".py"}))

runtime = load_json("PROJECT_RUNTIME.json") or {}
history = load_json("PROJECT_HISTORY.json") or {}

git_head = run(["git", "rev-parse", "HEAD"])["stdout"].strip()
git_status = run(["git", "status", "--short"])["stdout"].splitlines()

service_cat = run(["systemctl", "cat", "tokenoskobi-news-radar-refresh.service"])
service_text = service_cat["stdout"]

active_exec = load_json("data/control/ACTIVE_EXECUTION_GRAPH.json") or {}
used_index = load_json("data/control/USED_BY_RUNTIME_INDEX.json") or {}

current_work_unit = runtime.get("current_work_unit", {})
current_state = runtime.get("current_state", {})
legacy_work_unit = current_state.get("active_work_unit", {}) if isinstance(current_state, dict) else {}

step01_reachability = {
    "systemd_news_service_present": service_cat["rc"] == 0,
    "systemd_news_service_execstart": [l for l in service_text.splitlines() if "ExecStart=" in l],
    "repo_service_timer_files": [rel(p) for p in ROOT.rglob("*") if p.is_file() and p.suffix in [".service", ".timer"] and ".git" not in p.parts],
    "original_news_runner_references": grep_files(
        [p for p in walk_files(".", {".py", ".json", ".md", ".jsonl"}) if ".git" not in p.parts],
        r"news_radar_refresh_runner_v1\.ORIGINAL_NEWS27A11",
        120
    ),
    "news_social_writer_references": grep_files(
        [p for p in walk_files(".", {".py", ".json", ".md", ".jsonl"}) if ".git" not in p.parts],
        r"news_social_launch_signal_writer_v1",
        120
    )
}

step02_execution_graph_validation = {
    "active_execution_graph_status": active_exec.get("status"),
    "active_execution_graph_node_count": len(active_exec.get("nodes", [])) if isinstance(active_exec.get("nodes"), list) else None,
    "active_execution_graph_edge_count": len(active_exec.get("edges", [])) if isinstance(active_exec.get("edges"), list) else None,
    "used_by_runtime_count": len(used_index.get("used_by_runtime", [])) if isinstance(used_index.get("used_by_runtime"), list) else None,
    "assessment": "WARN_STATIC_OR_INCOMPLETE_GRAPH" if not active_exec.get("edges") else "REVIEW_GRAPH_EDGES_PRESENT"
}

governance_import_hits = grep_files(py_files, r"core\.(authority|approval|policy)|from core import (authority|approval|policy)|import core\.(authority|approval|policy)", 300)
step03_governance_enforcement = {
    "governance_files_exist": {
        "core/authority.py": (ROOT/"core/authority.py").exists(),
        "core/approval.py": (ROOT/"core/approval.py").exists(),
        "core/policy.py": (ROOT/"core/policy.py").exists()
    },
    "active_import_hits": governance_import_hits,
    "assessment": "WARN_GOVERNANCE_DEFINED_BUT_NOT_ENFORCED" if not governance_import_hits else "REVIEW_IMPORTS_FOUND"
}

mutation_hits = grep_files(
    py_files,
    r"write_text|json\.dump|open\([^)]*['\"]w|sqlite3\.connect|INSERT INTO|UPDATE |DELETE FROM|CREATE TABLE|subprocess|os\.system|systemctl|nginx|shell=True",
    800
)
shell_hits = [h for h in mutation_hits if "shell=True" in h["text"]]
step04_mutation_write_inventory = {
    "mutation_pattern_hits_count": len(mutation_hits),
    "mutation_pattern_hits_sample": mutation_hits[:220],
    "shell_true_hits": shell_hits,
    "assessment": "WARN_ACTIVE_MUTATION_POINTS_REQUIRE_REACHABILITY_CLASSIFICATION"
}

public_files = walk_files("public")
public_keywords = grep_files(public_files, r"secret|private|debug|internal|recommend|action|wallet|seed|/root/|staging|preview", 500)
symlinks = []
for p in (ROOT/"public").rglob("*") if (ROOT/"public").exists() else []:
    if p.is_symlink():
        try:
            target = os.readlink(p)
        except Exception:
            target = "UNREADABLE"
        symlinks.append({"path": rel(p), "target": target})
step05_public_exposure_audit = {
    "public_file_count": len(public_files),
    "public_keyword_hits_count": len(public_keywords),
    "public_keyword_hits_sample": public_keywords[:160],
    "public_symlinks": symlinks,
    "assessment": "WARN_PUBLIC_EXPOSURE_REQUIRES_REVIEW" if public_keywords or symlinks else "NO_PUBLIC_KEYWORD_HITS"
}

producer_files = [rel(p) for p in py_files if "producer" in p.name or "runner" in p.name or "writer" in p.name]
consumer_files = [rel(p) for p in py_files if "readmodel" in p.name or "panel" in p.name or "builder" in p.name or "bridge" in p.name]
step06_pipeline_isolation = {
    "producer_candidates": producer_files,
    "consumer_readmodel_candidates": consumer_files,
    "write_targets_in_code": grep_files(py_files, r"active_panel_8096|public/|data/control|reports/|\.secrets|tokenoskobi_clean_v1\.sqlite|sqlite", 500),
    "assessment": "WARN_PIPELINE_ISOLATION_NEEDS_MATRIX_REVIEW"
}

dbs = []
for p in ROOT.rglob("*"):
    if ".git" in p.parts:
        continue
    if p.is_file() and (p.name.endswith(".sqlite") or p.name.endswith(".db")):
        item = {"path": rel(p), "bytes": p.stat().st_size, "tables": [], "journal_mode": None}
        try:
            uri = f"file:{p}?mode=ro"
            con = sqlite3.connect(uri, uri=True, timeout=2)
            item["journal_mode"] = con.execute("PRAGMA journal_mode").fetchone()[0]
            item["tables"] = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 120")]
            con.close()
        except Exception as e:
            item["error"] = str(e)
        dbs.append(item)

largest = []
for p in ROOT.rglob("*"):
    if ".git" in p.parts:
        continue
    if p.is_file():
        try:
            s = p.stat().st_size
            if s >= 1024 * 1024:
                largest.append({"path": rel(p), "bytes": s})
        except Exception:
            pass
largest = sorted(largest, key=lambda x: x["bytes"], reverse=True)[:80]

step07_performance_water_pooling = {
    "directory_sizes": [dir_size(x) for x in ["data", "data/control", "public", "archive", "docs", "reports", "data/shadow_runtime_lab"]],
    "sqlite_databases": dbs,
    "largest_files_top80": largest,
    "assessment": "WARN_WATER_POOLING_CONFIRMED" if largest else "NO_LARGE_FILES_FOUND"
}

canonical_text_markers = {}
for f in ["README.md","PROJECT_RUNTIME.json","PROJECT_HISTORY.json","03_ROADMAP.md","04_ALMANAC.md","05_ATLAS.md","06_PROJECT_MASTER_STATE.md","07_PROJECT_HANDOFF.md","PROJECT_BOOT.json"]:
    txt = read(f, 250000)
    canonical_text_markers[f] = {
        "exists": bool(txt),
        "era_markers_top": re.findall(r"ERA[0-9]+[A-Z]?", txt[:12000])[:30],
        "mentions_era42": "ERA42" in txt[:250000],
        "mentions_era43": "ERA43" in txt[:250000]
    }

runtime_sync_ok = current_work_unit == legacy_work_unit and runtime.get("next_safe_step") == current_state.get("next_safe_step", {})
step08_governance_drift = {
    "runtime_top_level_current_work_unit": current_work_unit,
    "runtime_current_state_active_work_unit": legacy_work_unit,
    "runtime_sync_ok": runtime_sync_ok,
    "canonical_text_markers": canonical_text_markers,
    "assessment": "WARN_CANONICAL_DOCS_CONTAIN_HISTORICAL_OR_STALE_ERA_MARKERS" if any(v["era_markers_top"] for v in canonical_text_markers.values()) else "NO_ERA_MARKERS_FOUND"
}

findings = []

if step02_execution_graph_validation["assessment"].startswith("WARN"):
    findings.append({"severity":"HIGH","id":"ERA43_GRAPH_STATIC","title":"ACTIVE_EXECUTION_GRAPH appears static/incomplete","evidence":"edges empty or missing","fix":"Verify real reachability before ERA43 real run","disposition":"FIX_NOW_VERIFY"})
if step03_governance_enforcement["assessment"].startswith("WARN"):
    findings.append({"severity":"HIGH","id":"ERA43_GOVERNANCE_INERT","title":"Governance files exist but active enforcement imports were not found","evidence":"core authority/approval/policy import scan empty","fix":"Classify as accepted pre-trade limitation or wire enforcement in future ERA","disposition":"FIX_NOW_VERIFY_OR_RISK_ACCEPT"})
if shell_hits:
    findings.append({"severity":"MEDIUM","id":"ERA43_SHELL_TRUE","title":"shell=True remains in active code surface","evidence":shell_hits[:20],"fix":"Classify active/manual/archive; convert active instances later","disposition":"BACKLOG_OR_FIX_IF_REACHABLE"})
if public_keywords or symlinks:
    findings.append({"severity":"HIGH","id":"ERA43_PUBLIC_EXPOSURE_REVIEW","title":"public/ contains internal/action/staging/wallet/debug keyword hits or symlinks","evidence":public_keywords[:20]+symlinks[:10],"fix":"Review public boundary before ERA43 real run","disposition":"FIX_NOW_VERIFY"})
if largest:
    findings.append({"severity":"MEDIUM","id":"ERA43_WATER_POOLING","title":"Large artifacts and water pooling confirmed","evidence":largest[:20],"fix":"Classify active/archive/backlog/delete_candidate; no deletion in preflight","disposition":"BACKLOG_CLASSIFICATION_REQUIRED"})
if not runtime_sync_ok:
    findings.append({"severity":"HIGH","id":"ERA43_RUNTIME_DRIFT","title":"PROJECT_RUNTIME top-level and current_state are not synchronized","evidence":{"top":current_work_unit,"legacy":legacy_work_unit},"fix":"Synchronize runtime state","disposition":"FIX_NOW"})

critical = [f for f in findings if f["severity"] == "CRITICAL"]
high = [f for f in findings if f["severity"] == "HIGH"]

decision = "FAIL_ERA43_PREFLIGHT_READONLY_AUDIT_NOAPI" if critical else ("WARN_ERA43_PREFLIGHT_READONLY_AUDIT_NOAPI" if high else "PASS_ERA43_PREFLIGHT_READONLY_AUDIT_NOAPI")

report = {
    "era": "ERA43",
    "work_unit": "ERA43_PREFLIGHT_READONLY_AUDIT_NOAPI",
    "created_at_utc": NOW,
    "git": {"head": git_head, "status_short": git_status},
    "steps": {
        "STEP01_REACHABILITY_MAP": step01_reachability,
        "STEP02_EXECUTION_GRAPH_VALIDATION": step02_execution_graph_validation,
        "STEP03_GOVERNANCE_ENFORCEMENT": step03_governance_enforcement,
        "STEP04_MUTATION_WRITE_INVENTORY": step04_mutation_write_inventory,
        "STEP05_PUBLIC_EXPOSURE_AUDIT": step05_public_exposure_audit,
        "STEP06_PIPELINE_ISOLATION": step06_pipeline_isolation,
        "STEP07_PERFORMANCE_AND_WATER_POOLING": step07_performance_water_pooling,
        "STEP08_GOVERNANCE_DRIFT_AND_FINAL_GATE": step08_governance_drift
    },
    "findings": findings,
    "decision": decision,
    "next_step": "ERA43_PREFLIGHT_REVIEW_AND_DECISION_NOAPI",
    "guards": {
        "external_api_calls": 0,
        "live_trade": False,
        "wallet_action": False,
        "db_schema_change": False,
        "service_change": False,
        "nginx_change": False,
        "cleanup_performed": False,
        "project_scripts_executed": False
    }
}

OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

md = []
md.append("# ERA43 PREFLIGHT READONLY AUDIT NOAPI")
md.append("")
md.append(f"- Created UTC: {NOW}")
md.append(f"- Decision: `{decision}`")
md.append(f"- Git head: `{git_head}`")
md.append("")
md.append("## Findings")
if findings:
    for f in findings:
        md.append(f"- **{f['severity']} {f['id']}** — {f['title']} — `{f['disposition']}`")
else:
    md.append("- No findings.")
md.append("")
md.append("## Step Decisions")
for k, v in report["steps"].items():
    md.append(f"- `{k}`: `{v.get('assessment','RECORDED')}`")
md.append("")
md.append("## ERA43 Gate")
md.append("- ERA43 real run should wait for review of HIGH findings or explicit risk acceptance.")
md.append("- This audit did not modify DB/schema/services/nginx/wallet/trade.")
OUT_MD.write_text("\n".join(md) + "\n")

rtp = ROOT / "PROJECT_RUNTIME.json"
rt = load_json("PROJECT_RUNTIME.json") or {}
wu = {
    "id": "ERA43_PREFLIGHT_READONLY_AUDIT_NOAPI",
    "type": "READONLY_PREFLIGHT_AUDIT",
    "status": "WORK_UNIT_OPEN",
    "last_completed_step": "STEP08_GOVERNANCE_DRIFT_AND_FINAL_GATE",
    "next_step": "ERA43_PREFLIGHT_REVIEW_AND_DECISION_NOAPI"
}
ns = {"name": "ERA43_PREFLIGHT_REVIEW_AND_DECISION_NOAPI", "status": "READY"}
rt["current_work_unit"] = wu
rt["next_safe_step"] = ns
cs = rt.get("current_state") if isinstance(rt.get("current_state"), dict) else {}
cs["active_work_unit"] = wu
cs["next_safe_step"] = ns
cs["runtime_status"] = "WORK_UNIT_OPEN"
cs["updated_at"] = NOW
rt["current_state"] = cs
rt["last_completed"] = "ERA43_PREFLIGHT_READONLY_AUDIT_NOAPI_STEP08"
rt["status"] = "WORK_UNIT_OPEN"
rtp.write_text(json.dumps(rt, indent=2, ensure_ascii=False) + "\n")

print("DECISION:", decision)
print("FINDINGS:", len(findings))
print("JSON:", OUT_JSON)
print("MD:", OUT_MD)
