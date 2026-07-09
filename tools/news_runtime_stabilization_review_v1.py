#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict
import json
import os
import sqlite3
import subprocess

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
DISPLAY = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
MARKET_EVENTS = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADV_EVENTS = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
OUT = ROOT / "runtime/state/news_runtime_stabilization_review_v1.json"

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sh(cmd: list[str]) -> Dict[str, Any]:
    try:
        r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=20)
        return {"rc": r.returncode, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
    except Exception as e:
        return {"rc": 99, "stdout": "", "stderr": str(e)}

def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None

def table_count(con: sqlite3.Connection, table: str) -> int | None:
    if not table_exists(con, table):
        return None
    return int(con.execute("SELECT COUNT(*) FROM " + table).fetchone()[0])

def db_snapshot() -> Dict[str, Any]:
    out: Dict[str, Any] = {"exists": DB.exists(), "journal_mode": None, "counts": {}}
    if not DB.exists():
        return out
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    out["journal_mode"] = con.execute("PRAGMA journal_mode").fetchone()[0]
    for table in ["news_raw_feed_events", "news_token_match_events", "news_signal_events", "news_score_events_v1", "news_runtime_freshness_v1"]:
        out["counts"][table] = table_count(con, table)
    con.close()
    return out

def jsonl_audit(path: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {"exists": path.exists(), "line_count": 0, "parse_errors": 0, "duplicate_event_uid_count": 0, "unsafe_events": 0}
    if not path.exists():
        return out
    uids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out["line_count"] += 1
        try:
            obj = json.loads(line)
            uid = str(obj.get("event_uid") or "")
            if uid:
                uids.append(uid)
            if obj.get("hunter_authorized") is not False or obj.get("trade_signal") is not False or obj.get("paper_signal") is not False:
                out["unsafe_events"] += 1
        except Exception:
            out["parse_errors"] += 1
    out["duplicate_event_uid_count"] = len(uids) - len(set(uids))
    return out

def main() -> int:
    summary = read_json(SUMMARY)
    display = read_json(DISPLAY)
    hot = read_json(HOT)
    market = jsonl_audit(MARKET_EVENTS)
    adv = jsonl_audit(ADV_EVENTS)
    service_active = sh(["systemctl", "is-active", SERVICE])
    service_enabled = sh(["systemctl", "is-enabled", SERVICE])
    timer_active = sh(["systemctl", "is-active", TIMER])
    timer_enabled = sh(["systemctl", "is-enabled", TIMER])
    timer_list = sh(["systemctl", "list-timers", TIMER, "--no-pager", "--all"])
    journal = sh(["journalctl", "-u", SERVICE, "-n", "60", "--no-pager", "--output", "short-iso"])

    warnings = []
    if summary.get("market_indicator_count") != market["line_count"]:
        warnings.append("summary_market_count_lags_jsonl")
    if summary.get("adversarial_count") != adv["line_count"]:
        warnings.append("summary_adversarial_count_lags_jsonl")
    if timer_active["stdout"] != "active":
        warnings.append("timer_not_active")
    if timer_enabled["stdout"] != "enabled":
        warnings.append("timer_not_enabled")
    if summary.get("parse_errors") not in (None, 0):
        warnings.append("summary_parse_errors_nonzero")
    if summary.get("duplicate_event_uids") not in (None, 0):
        warnings.append("summary_duplicate_event_uids_nonzero")
    if summary.get("unsafe_events") not in (None, 0):
        warnings.append("summary_unsafe_events_nonzero")
    if market["parse_errors"] != 0 or adv["parse_errors"] != 0:
        warnings.append("jsonl_parse_errors_nonzero")
    if market["duplicate_event_uid_count"] != 0 or adv["duplicate_event_uid_count"] != 0:
        warnings.append("jsonl_duplicate_event_uids_nonzero")
    if market["unsafe_events"] != 0 or adv["unsafe_events"] != 0:
        warnings.append("jsonl_unsafe_events_nonzero")

    payload = {
        "schema_version": "1.0",
        "review": "NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW_V1",
        "generated_at_utc": utc_now(),
        "mode": "NOAPI_READONLY_PRODUCER_REVIEW",
        "authority": {
            "db_write": False,
            "db_schema_change": False,
            "service_change": False,
            "timer_change": False,
            "panel_change": False,
            "network_call": False,
            "external_api_call": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "execution_authority": False
        },
        "db": db_snapshot(),
        "jsonl": {
            "market": market,
            "adversarial": adv
        },
        "summary": {
            "exists": bool(summary),
            "market_indicator_count": summary.get("market_indicator_count"),
            "adversarial_count": summary.get("adversarial_count"),
            "parse_errors": summary.get("parse_errors"),
            "duplicate_event_uids": summary.get("duplicate_event_uids"),
            "unsafe_events": summary.get("unsafe_events"),
            "authority": summary.get("authority")
        },
        "display": {
            "exists": bool(display),
            "sections": [s.get("id") for s in (display.get("sections") or [])],
            "health": display.get("health"),
            "authority": display.get("authority")
        },
        "hot_gateway": {
            "exists": bool(hot),
            "hot_queue_count": hot.get("hot_queue_count"),
            "source_health": hot.get("source_health"),
            "authority": hot.get("authority")
        },
        "systemd": {
            "service": SERVICE,
            "service_active": service_active,
            "service_enabled": service_enabled,
            "timer": TIMER,
            "timer_active": timer_active,
            "timer_enabled": timer_enabled,
            "timer_list": timer_list
        },
        "journal_tail": {
            "rc": journal["rc"],
            "tail": journal["stdout"].splitlines()[-20:],
            "stderr": journal["stderr"]
        },
        "warnings": warnings,
        "next_recommendation": "Keep producer under observation; refresh consumer/display/hot chain when JSONL counts drift."
    }
    write_json(OUT, payload)
    print(json.dumps({
        "review": payload["review"],
        "market_jsonl": market["line_count"],
        "adversarial_jsonl": adv["line_count"],
        "summary_market": summary.get("market_indicator_count"),
        "summary_adversarial": summary.get("adversarial_count"),
        "hot_queue_count": hot.get("hot_queue_count"),
        "timer_active": timer_active["stdout"],
        "timer_enabled": timer_enabled["stdout"],
        "warnings": warnings,
        "output": str(OUT)
    }, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
