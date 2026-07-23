#!/usr/bin/env python3
"""Bridge the ERA63D runtime snapshot into the technical-center panel readmodel."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/root/tokenoskobi_clean_v1")
LATEST = ROOT / "runtime/era63d/latest_real_market_technical_snapshot_v1.json"
PANEL = ROOT / "active_panel_8096/current/data/technical_center_live_readmodel_v1.json"
OUT = ROOT / "data/control/n16d_technical_center_live_producer_result_v1.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        read_json(Path(temporary))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def missing(reason: str):
    return {
        "schema": "tokenoskobi.technical_center.live_readmodel.v2",
        "stage": "ERA63D_REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING",
        "generated_at_utc": now(),
        "producer": "tools/technical_center_live_producer_v1.py",
        "decision": "TECHNICAL_CENTER_DATA_MISSING",
        "data_freshness_sec": 0,
        "source_count": 0,
        "authority": {
            "trade": False,
            "paper_trade_write": False,
            "wallet": False,
            "signing": False,
            "real_order": False,
            "broadcast": False,
            "provider_call_from_browser": False,
            "policy_apply": False,
        },
        "items": [{
            "key": "technical_center",
            "label": "Teknik Analiz Merkezi",
            "status": "DATA_MISSING",
            "live_ta_claim": False,
            "note": reason,
        }],
    }


def main() -> int:
    if not LATEST.exists():
        model = missing("ERA63D runtime snapshot is not available yet.")
    else:
        root_text = str(ROOT)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)
        from tools.era63d_market_technical_runtime_v1 import build_panel
        snapshot = read_json(LATEST)
        model = build_panel(snapshot)
    atomic_write(PANEL, model)
    atomic_write(OUT, model)
    print("FINAL_GATE=PASS_ERA63D_TECHNICAL_CENTER_BRIDGE")
    print(f"DECISION={model['decision']}")
    print(f"SOURCE_COUNT={model['source_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
