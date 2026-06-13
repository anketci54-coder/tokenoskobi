#!/usr/bin/env python3
"""
PHASE9 commercial observation runtime skeleton.

This file is installed by PHASE9C, but it is NOT enabled, NOT scheduled,
NOT connected to paper/live trading, and NOT allowed to call RPC/API in this install.

Default mode: inert self-audit only.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("/root/tokenoskobi_clean_v1")
CONFIG = BASE / "data/phase9_commercial_observation_config.json"
DB = BASE / "data/tokenoskobi_clean_v1.sqlite"
STATUS = BASE / "reports/LATEST_PHASE9_OBSERVATION_RUNTIME_STATUS.md"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_config():
    with CONFIG.open("r", encoding="utf-8") as f:
        return json.load(f)

def db_read_health():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    quick = con.execute("PRAGMA quick_check").fetchone()[0]
    fk = len(con.execute("PRAGMA foreign_key_check").fetchall())
    target_count = con.execute("SELECT COUNT(*) FROM state_aggregated_token_readmodel_v1").fetchone()[0]
    con.close()
    return {"integrity": integrity, "quick": quick, "fk": fk, "target_count": target_count}

def main():
    cfg = load_config()

    result = {
        "runtime_name": "phase9_commercial_observation_runtime",
        "timestamp_utc": now_iso(),
        "runtime_enabled": False,
        "watch_only": True,
        "api_calls": 0,
        "rpc_calls": 0,
        "fetch_calls": 0,
        "paper_allowed": False,
        "live_allowed": False,
        "panel_apply_allowed": False,
        "trade_permission": False,
        "config_guardrails": cfg.get("guardrails", {}),
        "db_health_read_only": db_read_health(),
        "decision": "INERT_INSTALL_ONLY_NO_RUNTIME_LOOP",
    }

    lines = [
        "# PHASE9 Observation Runtime Status",
        "",
        "- Runtime installed: `True`",
        "- Runtime enabled: `False`",
        "- Runtime loop executed: `False`",
        "- API/RPC/FETCH calls: `0`",
        "- Paper/live: `False`",
        "- Panel apply: `False`",
        "- Decision: `INERT_INSTALL_ONLY_NO_RUNTIME_LOOP`",
        "",
        "```json",
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
