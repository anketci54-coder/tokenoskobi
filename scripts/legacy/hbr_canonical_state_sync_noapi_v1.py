#!/usr/bin/env python3
import json
from pathlib import Path

root = Path("/root/tokenoskobi_clean_v1")

runtime = json.loads(
    (root / "PROJECT_RUNTIME.json").read_text(encoding="utf-8")
)

artifact = json.loads(
    (
        root
        / "data/control/hbr_canonical_state_sync_noapi_v1.json"
    ).read_text(encoding="utf-8")
)

checks = {
    "runtime_last_completed": (
        runtime.get("last_completed")
        == "HBR_CANONICAL_STATE_SYNC_NOAPI"
    ),
    "runtime_next": (
        runtime.get("next_safe_step", {}).get("name")
        == "HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI"
    ),
    "artifact_decision": (
        artifact.get("decision")
        == "OK_HBR_CANONICAL_STATE_SYNC_NOAPI"
    ),
    "collision_unknown": (
        artifact.get("result", {}).get("collision_result")
        == "UNKNOWN_UNTIL_HBR_C"
    ),
}

ok = all(checks.values())

print(
    json.dumps(
        {
            "decision": (
                "OK_HBR_CANONICAL_STATE_SYNC_VERIFY_NOAPI"
                if ok
                else "FAIL_HBR_CANONICAL_STATE_SYNC_VERIFY_NOAPI"
            ),
            "checks": checks,
        },
        indent=2,
    )
)

raise SystemExit(0 if ok else 1)
