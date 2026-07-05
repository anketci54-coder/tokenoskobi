#!/usr/bin/env python3
from pathlib import Path
import argparse, json, subprocess, datetime, os

ROOT = Path(__file__).resolve().parent
GENERATED_REGISTRY = "TOKENOSKOBI_OS_REGISTRY.json"

def sh(cmd):
    try:
        return subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception as e:
        return f"ERROR: {e}"

def load_json(path):
    p = ROOT / path
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(errors="ignore"))
    except Exception as e:
        return {"error": str(e), "path": path}

def file_exists(path):
    return (ROOT / path).exists()

def git_status_short(include_generated_registry=False):
    status = sh(["git", "status", "--short"])
    if include_generated_registry or not status or status.startswith("ERROR"):
        return status
    kept = []
    for line in status.splitlines():
        path = line[3:] if len(line) > 3 else line
        if path == GENERATED_REGISTRY:
            continue
        kept.append(line)
    return "\n".join(kept)

def remote_head_fast():
    remote = sh(["git", "rev-parse", "origin/main"])
    if remote.startswith("ERROR"):
        remote = sh(["git", "ls-remote", "origin", "refs/heads/main"])
        if remote.startswith("ERROR"):
            return "ERROR"
        return remote.split()[0]
    return remote

def inventory_summary(full=False):
    if full:
        return {
            "python_files": len([p for p in ROOT.rglob("*.py") if ".git" not in p.parts]),
            "services_found": len([p for p in ROOT.rglob("*.service") if ".git" not in p.parts]),
            "timers_found": len([p for p in ROOT.rglob("*.timer") if ".git" not in p.parts]),
            "mode": "full_recursive"
        }
    return {
        "python_files": "FASTPATH_SKIPPED_USE_TK_MACHINE",
        "services_found": "FASTPATH_SKIPPED_USE_TK_MACHINE",
        "timers_found": "FASTPATH_SKIPPED_USE_TK_MACHINE",
        "mode": "fastpath"
    }

def collect(full=False):
    runtime = load_json("PROJECT_RUNTIME.json") or {}
    boot = load_json("PROJECT_BOOT.json") if full else None
    history = load_json("PROJECT_HISTORY.json") if full else None

    local_head = sh(["git", "rev-parse", "HEAD"])
    branch = sh(["git", "branch", "--show-current"])
    remote_head = remote_head_fast()
    status = git_status_short(include_generated_registry=False)
    raw_status = git_status_short(include_generated_registry=True)
    registry_generated_dirty = any((line[3:] if len(line) > 3 else line) == GENERATED_REGISTRY for line in raw_status.splitlines()) if raw_status and not raw_status.startswith("ERROR") else False

    graphs = {}
    if full:
        graphs = {
            "active_execution_graph": load_json("ACTIVE_EXECUTION_GRAPH.json"),
            "active_dependency_graph": load_json("ACTIVE_DEPENDENCY_GRAPH.json"),
            "active_core_ranking": load_json("ACTIVE_CORE_RANKING.json"),
            "real_execution_chain": load_json("REAL_EXECUTION_CHAIN.json"),
            "real_code_duplicates": load_json("REAL_CODE_DUPLICATES.json"),
            "mutation_candidates": load_json("MUTATION_CANDIDATES.json"),
            "minimal_active_core_manifest": load_json("MINIMAL_ACTIVE_CORE_MANIFEST.json"),
            "used_by_runtime_index": load_json("USED_BY_RUNTIME_INDEX.json")
        }

    active_work_unit = runtime.get("current_work_unit") or runtime.get("current_state", {}).get("active_work_unit") or {}
    next_safe_step = runtime.get("next_safe_step") or runtime.get("current_state", {}).get("next_safe_step")

    kernel = {
        "kernel": "TOKENOSKOBI_KERNEL_V1",
        "collect_mode": "full" if full else "fastpath",
        "created_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "project": {
            "name": "Tokenoskobi",
            "root": str(ROOT),
            "branch": branch,
            "local_head": local_head,
            "remote_head": remote_head,
            "head_sync": local_head == remote_head,
            "git_clean": status == "",
            "git_status_short": status,
            "generated_registry_dirty_ignored": registry_generated_dirty
        },
        "boot_files": {
            "PROJECT_BOOT.json": file_exists("PROJECT_BOOT.json"),
            "PROJECT_RUNTIME.json": file_exists("PROJECT_RUNTIME.json"),
            "PROJECT_HISTORY.json": file_exists("PROJECT_HISTORY.json")
        },
        "current_state": {
            "active_work_unit": active_work_unit,
            "next_safe_step": next_safe_step,
            "runtime_status": runtime.get("status"),
            "updated_at": runtime.get("updated_at"),
            "last_action": runtime.get("last_action")
        },
        "known_facts": {
            "mirror_mode": "SERVER_WORKSPACE_EQUALS_GITHUB_MAIN",
            "current_priority": "TOKENOSKOBI_KERNEL_V1_AND_CORE_OS_CLEANUP",
            "era33_status": "ARCHITECTURE_DEFINED_VALIDATION_IN_PROGRESS",
            "era33_next": "PHASE3_CONTAMINATION_AUDITOR",
            "core_problem": "repository contains code plus archive/audit/runtime outputs; kernel is being added to make system self-describing"
        },
        "architecture": {
            "constitution_target": "TOKENOSKOBI_OS_CONSTITUTION_V1",
            "planned_layers": [
                "CONSTITUTION",
                "BOOT",
                "CORE",
                "RUNTIME",
                "STATE",
                "CONFIG",
                "PLUGINS",
                "WORKSPACE",
                "ARCHIVE"
            ],
            "future_rule": "new ERA work must be plugin-based and must not rewrite CORE unless CORE_UPGRADE is explicitly opened"
        },
        "inventory_summary": inventory_summary(full=full),
        "graphs": graphs,
        "runtime_json": runtime if full else "FASTPATH_SKIPPED_USE_TK_MACHINE",
        "boot_json": boot if full else "FASTPATH_SKIPPED_USE_TK_MACHINE",
        "history_json": history if full else "FASTPATH_SKIPPED_USE_TK_MACHINE"
    }

    return kernel

def stable_registry_write(k):
    path = ROOT / GENERATED_REGISTRY
    old = load_json(GENERATED_REGISTRY) or {}
    old_norm = dict(old) if isinstance(old, dict) else {}
    new_norm = dict(k)

    old_norm.pop("created_at_utc", None)
    new_norm.pop("created_at_utc", None)

    if old_norm == new_norm and isinstance(old, dict) and old.get("created_at_utc"):
        k["created_at_utc"] = old["created_at_utc"]

    new_text = json.dumps(k, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(errors="ignore") == new_text:
        print("TOKENOSKOBI_OS_REGISTRY_WRITE=UNCHANGED")
        print("OUT=TOKENOSKOBI_OS_REGISTRY.json")
        return

    path.write_text(new_text)
    print("TOKENOSKOBI_OS_REGISTRY_WRITE=PASS")
    print("OUT=TOKENOSKOBI_OS_REGISTRY.json")

def print_human(k):
    p = k["project"]
    c = k["current_state"]
    aw = c.get("active_work_unit") or {}
    print("=" * 80)
    print("TOKENOSKOBI KERNEL V1")
    print("=" * 80)
    print("ROOT        :", p["root"])
    print("BRANCH      :", p["branch"])
    print("LOCAL HEAD  :", p["local_head"])
    print("REMOTE HEAD :", p["remote_head"])
    print("HEAD SYNC   :", "PASS" if p["head_sync"] else "FAIL")
    print("GIT CLEAN   :", "PASS" if p["git_clean"] else "DIRTY")
    print()
    print("WORK UNIT   :", aw.get("id"))
    print("STATUS      :", aw.get("status"))
    print("LAST STEP   :", aw.get("last_completed_step"))
    print("NEXT STEP   :", aw.get("next_step"))
    print("NEXT SAFE   :", c.get("next_safe_step"))
    print()
    print("INVENTORY   :", k["inventory_summary"].get("mode"))
    print("PYTHON      :", k["inventory_summary"].get("python_files"))
    print("SERVICES    :", k["inventory_summary"].get("services_found"))
    print("TIMERS      :", k["inventory_summary"].get("timers_found"))
    print()
    print("PRIORITY    :", k["known_facts"]["current_priority"])
    print("ERA33       :", k["known_facts"]["era33_status"])
    print("ERA33 NEXT  :", k["known_facts"]["era33_next"])
    print("=" * 80)

def print_ai(k):
    p = k["project"]
    c = k["current_state"]
    aw = c.get("active_work_unit") or {}

    print("NEW AI: READ THIS FIRST. THIS IS THE SOURCE OF TRUTH FOR TOKENOSKOBI OS.")
    print("")
    print("TOKENOSKOBI OS KERNEL BOOTSTRAP v1")
    print("=" * 72)
    print("")
    print("ABSOLUTE RULES:")
    print("- Repository/server state is source of truth; AI memory is not.")
    print("- Server workspace and GitHub main must remain mirror-synced.")
    print("- Do not invent roadmap, status, phases, or next steps.")
    print("- If data is missing, say data is missing.")
    print("- Do not open a new ERA unless the user explicitly asks.")
    print("- Do not write code unless the user says Ver/Yap or explicitly asks.")
    print("- All server commands must start with: cd /root/tokenoskobi_clean_v1 || exit 1")
    print("- Prefer one paste-and-run command block.")
    print("")
    print("CURRENT CANONICAL STATE:")
    print(f"- root: {p['root']}")
    print(f"- branch: {p['branch']}")
    print(f"- local_head: {p['local_head']}")
    print(f"- remote_head: {p['remote_head']}")
    print(f"- head_sync: {p['head_sync']}")
    print(f"- git_clean: {p['git_clean']}")
    print(f"- active_work_unit: {aw.get('id')}")
    print(f"- status: {aw.get('status')}")
    print(f"- last_step: {aw.get('last_completed_step')}")
    print(f"- next_step: {aw.get('next_step')}")
    print(f"- next_safe_step: {c.get('next_safe_step')}")
    print("")
    print("CURRENT PRIORITY ORDER:")
    print("1. Harden Tokenoskobi Kernel / Registry.")
    print("2. Build Core Isolation Map.")
    print("3. Build Lifecycle Controller.")
    print("4. Then resume ERA33 Phase3 Contamination Auditor.")
    print("")
    print("ARCHITECTURE DIRECTION:")
    print("- Tokenoskobi is moving to Kernel + Registry + Core Freeze + Plugin architecture.")
    print("- Layers: CONSTITUTION, BOOT, CORE, RUNTIME, STATE, CONFIG, PLUGINS, WORKSPACE, ARCHIVE.")
    print("- New ERA work must become plugin-based.")
    print("- CORE must not change unless CORE_UPGRADE is explicitly opened.")
    print("- Repository must not become a temporary workspace.")
    print("")
    print("IMPORTANT FINDINGS:")
    print("- tk ai uses FASTPATH. Use tk machine for full recursive inventory and graph details.")
    print("- tk registry ignores its own generated file dirtiness while computing git_clean.")
    print("- Real code duplicates: 0 according to REAL_CODE_DUPLICATES.json.")
    print("- Repository bloat is mainly data/docs/backups/audit outputs, not Python code.")
    print("")
    print("KNOWN COMMANDS:")
    print("- tk           => human status")
    print("- tk ai        => this bootstrap")
    print("- tk sync      => local/remote sync check")
    print("- tk registry  => refresh TOKENOSKOBI_OS_REGISTRY.json")
    print("- tk machine   => full JSON machine export")
    print("")
    print("WHAT THE NEXT AI SHOULD DO FIRST:")
    print("- Confirm it understood the current state.")
    print("- Do not propose a new ERA.")
    print("- If asked to continue, continue with Kernel/Registry hardening or Core Isolation, not random audits.")
    print("=" * 72)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human", action="store_true")
    ap.add_argument("--ai", action="store_true")
    ap.add_argument("--machine", action="store_true")
    ap.add_argument("--write-registry", action="store_true")
    args = ap.parse_args()

    full = bool(args.machine or args.write_registry)
    k = collect(full=full)

    if args.write_registry:
        stable_registry_write(k)
        return

    if args.machine:
        print(json.dumps(k, indent=2, ensure_ascii=False))
    elif args.ai:
        print_ai(k)
    else:
        print_human(k)

if __name__ == "__main__":
    main()
