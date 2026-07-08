#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


READ_TARGETS = (
    "PROJECT_RUNTIME.json",
    "PROJECT_BOOT.json",
    "data/control/latest_tk_machine_state.json",
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path), "data": None, "error": "missing"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {"exists": True, "path": str(path), "data": data, "error": None}
    except Exception as exc:
        return {"exists": True, "path": str(path), "data": None, "error": str(exc)}


def build_readonly_snapshot(root: Path) -> dict[str, Any]:
    root = root.resolve()
    loaded = {name: _load_json(root / name) for name in READ_TARGETS}
    runtime = loaded["PROJECT_RUNTIME.json"].get("data") or {}
    current_state = runtime.get("current_state") or {}
    workflow_rules = runtime.get("canonical_workflow_rules") or {}
    next_safe_step = (current_state.get("next_safe_step") or runtime.get("next_safe_step") or {}).get("name")
    active_work_unit = (current_state.get("active_work_unit") or runtime.get("current_work_unit") or {}).get("id")

    return {
        "scaffold_name": "discipline_layer_readonly_scaffold_v1",
        "read_only": True,
        "runtime_mutation_attempted": False,
        "db_write_attempted": False,
        "panel_write_attempted": False,
        "service_timer_mutation_attempted": False,
        "api_access_attempted": False,
        "provider_access_attempted": False,
        "wallet_access_attempted": False,
        "trade_authority": 0,
        "active_work_unit": active_work_unit,
        "next_safe_step": next_safe_step,
        "workflow_rules_name": workflow_rules.get("name"),
        "workflow_rules_status": workflow_rules.get("status"),
        "loaded": {
            name: {
                "exists": value.get("exists"),
                "path": value.get("path"),
                "error": value.get("error"),
            }
            for name, value in loaded.items()
        },
        "discipline_scope": {
            "allowed": [
                "read canonical machine state",
                "produce read-only snapshot",
                "report boundary state",
            ],
            "forbidden": [
                "runtime mutation",
                "database write",
                "panel write",
                "service or timer mutation",
                "api call",
                "provider call",
                "wallet access",
                "trade action",
            ],
        },
    }


def main() -> None:
    print(json.dumps(build_readonly_snapshot(Path.cwd()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
