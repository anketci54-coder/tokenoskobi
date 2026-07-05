#!/usr/bin/env python3
from pathlib import Path
import argparse, json, subprocess, datetime, os

ROOT = Path(__file__).resolve().parent

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

def git_status_short():
    return sh(["git", "status", "--short"])

def collect():
    runtime = load_json("PROJECT_RUNTIME.json") or {}
    boot = load_json("PROJECT_BOOT.json") or {}
    history = load_json("PROJECT_HISTORY.json") or {}

    local_head = sh(["git", "rev-parse", "HEAD"])
    branch = sh(["git", "branch", "--show-current"])
    remote_head = sh(["git", "ls-remote", "origin", "refs/heads/main"]).split()[0] if "ERROR" not in sh(["git", "ls-remote", "origin", "refs/heads/main"]) else "ERROR"

    status = git_status_short()

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
    next_safe_step = runtime.get("next_safe_step")

    python_files = len([p for p in ROOT.rglob("*.py") if ".git" not in p.parts])
    services = len([p for p in ROOT.rglob("*.service") if ".git" not in p.parts])
    timers = len([p for p in ROOT.rglob("*.timer") if ".git" not in p.parts])

    kernel = {
        "kernel": "TOKENOSKOBI_KERNEL_V1",
        "created_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "project": {
            "name": "Tokenoskobi",
            "root": str(ROOT),
            "branch": branch,
            "local_head": local_head,
            "remote_head": remote_head,
            "head_sync": local_head == remote_head,
            "git_clean": status == "",
            "git_status_short": status
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
        "inventory_summary": {
            "python_files": python_files,
            "services_found": services,
            "timers_found": timers
        },
        "graphs": graphs,
        "runtime_json": runtime,
        "boot_json": boot,
        "history_json": history
    }

    return kernel

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
    print("PYTHON      :", k["inventory_summary"]["python_files"])
    print("SERVICES    :", k["inventory_summary"]["services_found"])
    print("TIMERS      :", k["inventory_summary"]["timers_found"])
    print()
    print("PRIORITY    :", k["known_facts"]["current_priority"])
    print("ERA33       :", k["known_facts"]["era33_status"])
    print("ERA33 NEXT  :", k["known_facts"]["era33_next"])
    print("=" * 80)

def print_ai(k):
    p = k["project"]
    c = k["current_state"]
    aw = c.get("active_work_unit") or {}
    print("TOKENOSKOBI OS KERNEL EXPORT")
    print("")
    print("SOURCE OF TRUTH:")
    print("- Server workspace and GitHub main must be mirror-synced.")
    print("- Repository state overrides AI memory.")
    print("- Do not invent roadmap or status. Use kernel data only.")
    print("")
    print("CURRENT:")
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
    print("ARCHITECTURE:")
    print("- Tokenoskobi is moving to Kernel + Registry + Core Freeze + Plugin architecture.")
    print("- Planned layers: CONSTITUTION, BOOT, CORE, RUNTIME, STATE, CONFIG, PLUGINS, WORKSPACE, ARCHIVE.")
    print("- New ERA work must become plugin-based.")
    print("- CORE must not be changed unless CORE_UPGRADE is explicitly opened.")
    print("- Repository and server must stay mirror-synced.")
    print("")
    print("CURRENT PRIORITY:")
    print(f"- {k['known_facts']['current_priority']}")
    print("- Next practical work: finish kernel/registry, then core isolation, then lifecycle controller, then resume ERA33 Phase3.")
    print("")
    print("IMPORTANT FINDINGS:")
    print(f"- python_files: {k['inventory_summary']['python_files']}")
    print(f"- services_found: {k['inventory_summary']['services_found']}")
    print(f"- timers_found: {k['inventory_summary']['timers_found']}")
    print("- Real code duplicates: see REAL_CODE_DUPLICATES.json; last known duplicate groups = 0.")
    print("- Repository bloat is mainly data/docs/backups/audit outputs, not Python code.")
    print("")
    print("RULES FOR NEXT AI:")
    print("- Do not open a new ERA until user explicitly asks.")
    print("- Do not write code unless user asks or says 'Ver/Yap'.")
    print("- Prefer one paste-and-run block.")
    print("- Start every server command with: cd /root/tokenoskobi_clean_v1 || exit 1")
    print("- If data is missing, say data is missing.")
    print("- Next safe technical direction: TOKENOSKOBI_KERNEL_V1 hardening + TOKENOSKOBI_OS_REGISTRY.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human", action="store_true")
    ap.add_argument("--ai", action="store_true")
    ap.add_argument("--machine", action="store_true")
    ap.add_argument("--write-registry", action="store_true")
    args = ap.parse_args()

    k = collect()

    if args.write_registry:
        (ROOT / "TOKENOSKOBI_OS_REGISTRY.json").write_text(json.dumps(k, indent=2, ensure_ascii=False) + "\n")
        print("TOKENOSKOBI_OS_REGISTRY_WRITE=PASS")
        print("OUT=TOKENOSKOBI_OS_REGISTRY.json")
        return

    if args.machine:
        print(json.dumps(k, indent=2, ensure_ascii=False))
    elif args.ai:
        print_ai(k)
    else:
        print_human(k)

if __name__ == "__main__":
    main()
