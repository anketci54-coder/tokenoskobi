#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def git(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()

boot = read_json("PROJECT_BOOT.json")
runtime = read_json("PROJECT_RUNTIME.json")

head = git("git rev-parse HEAD")
branch = git("git branch --show-current")
status = git("git status --short")

wu = runtime.get("current_state", {}).get("active_work_unit", {})

report = {
    "continuation_engine_version": "1.0",
    "project": boot.get("project", {}),
    "source_of_truth": boot.get("source_of_truth", {}),
    "git": {
        "branch": branch,
        "head": head,
        "status_clean": status == "",
        "status_summary": status if status else "CLEAN"
    },
    "current_position": {
        "active_work_unit_id": wu.get("id", "UNKNOWN"),
        "active_work_unit_type": wu.get("type", "UNKNOWN"),
        "active_work_unit_status": wu.get("status", "UNKNOWN"),
        "last_completed_step": wu.get("last_completed_step", "UNKNOWN"),
        "next_step": wu.get("next_step", "UNKNOWN")
    },
    "last_action": runtime.get("last_action", {}),
    "next_safe_step": runtime.get("next_safe_step", {}),
    "open_risks": runtime.get("open_risks", []),
    "do_not_do": [
        "Do not start a new work unit if current work unit is not sealed.",
        "Do not rely on chat memory.",
        "Do not use GitHub Remote over local server state.",
        "Do not write code unless explicitly requested.",
        "Do not modify repository without risk analysis."
    ],
    "startup_instruction_for_new_chat": [
        "Read PROJECT_BOOT.json.",
        "Read PROJECT_RUNTIME.json.",
        "Run boot_validator_v1.py if server access exists.",
        "Run boot_workflow_manager_v1.py if server access exists.",
        "Use this continuation report to identify exact current position.",
        "Wait for user approval before any change."
    ]
}

print(json.dumps(report, indent=2, ensure_ascii=False))
