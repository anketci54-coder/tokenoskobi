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
STAB = ROOT / "runtime/state/news_runtime_stabilization_review_v1.json"
MARKET_EVENTS = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADV_EVENTS = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
OUT = ROOT / "runtime/state/news_producer_health_watch_and_hot_gateway_review_v1.json"

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

def max_col(con: sqlite3.Connection, table: str, candidates: list[str]) -> Any:
    if not table_exists(con, table):
        return None
    cols = [r[1] for r in con.execute("PRAGMA table_info(" + table + ")").fetchall()]
    for c in candidates:
        if c in cols:
            try:
                return con.execute("SELECT MAX(" + c + ") FROM " + table).fetchone()[0]
            except Exception:
                return None
    return None

def db_snapshot() -> Dict[str, Any]:
    out: Dict[str, Any] = {"exists": DB.exists(), "journal_mode": None, "counts": {}, "max_times": {}}
    if not DB.exists():
        return out
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    out["journal_mode"] = con.execute("PRAGMA journal_mode").fetchone()[0]
    for table in ["news_raw_feed_events", "news_token_match_events", "news_signal_events", "news_score_events_v1", "news_runtime_freshness_v1"]:
        out["counts"][table] = table_count(con, table)
        out["max_times"][table] = max_col(con, table, ["created_at_utc", "created_at", "timestamp_utc", "updated_at_utc", "published_at_utc", "seen_at_utc"])
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
    stab = read_json(STAB)
    market = jsonl_audit(MARKET_EVENTS)
    adv = jsonl_audit(ADV_EVENTS)
    db = db_snapshot()

    service_active = sh(["systemctl", "is-active", SERVICE])
    service_enabled = sh(["systemctl", "is-enabled", SERVICE])
    timer_active = sh(["systemctl", "is-active", TIMER])
    timer_enabled = sh(["systemctl", "is-enabled", TIMER])
    timer_list = sh(["systemctl", "list-timers", TIMER, "--no-pager", "--all"])
    journal = sh(["journalctl", "-u", SERVICE, "-n", "80", "--no-pager", "--output", "short-iso"])

    warnings: list[str] = []
    blockers: list[str] = []

    raw = db.get("counts", {}).get("news_raw_feed_events")
    match = db.get("counts", {}).get("news_token_match_events")
    signal = db.get("counts", {}).get("news_signal_events")
    score = db.get("counts", {}).get("news_score_events_v1")

    if timer_active.get("stdout") != "active":
        blockers.append("timer_not_active")
    if timer_enabled.get("stdout") != "enabled":
        blockers.append("timer_not_enabled")
    if market["parse_errors"] or adv["parse_errors"]:
        blockers.append("jsonl_parse_errors")
    if market["duplicate_event_uid_count"] or adv["duplicate_event_uid_count"]:
        blockers.append("jsonl_duplicate_event_uids")
    if market["unsafe_events"] or adv["unsafe_events"]:
        blockers.append("jsonl_unsafe_events")
    if summary.get("market_indicator_count") != market["line_count"]:
        blockers.append("summary_market_not_equal_jsonl")
    if summary.get("adversarial_count") != adv["line_count"]:
        blockers.append("summary_adversarial_not_equal_jsonl")
    if not hot or hot.get("hot_queue_count") is None:
        blockers.append("hot_gateway_state_missing")
    if raw is not None and match is not None and raw > match:
        warnings.append("raw_count_greater_than_match_downstream_review_needed")
    if db.get("journal_mode") != "wal":
        warnings.append("sqlite_journal_mode_not_wal")

    hot_auth = hot.get("authority") or {}
    if hot_auth.get("execution_authority") is not False:
        blockers.append("hot_execution_authority_not_false")
    if hot_auth.get("db_write") is not False:
        blockers.append("hot_db_write_not_false")
    if hot_auth.get("live_trade") is not False:
        blockers.append("hot_live_trade_not_false")

    integration = {
        "producer": {
            "timer_active": timer_active.get("stdout"),
            "timer_enabled": timer_enabled.get("stdout"),
            "service_active": service_active.get("stdout"),
            "service_enabled": service_enabled.get("stdout"),
            "raw_count": raw,
            "freshness_count": db.get("counts", {}).get("news_runtime_freshness_v1")
        },
        "downstream_db": {
            "match_count": match,
            "signal_count": signal,
            "score_count": score,
            "raw_to_match_gap": (raw - match) if isinstance(raw, int) and isinstance(match, int) else None
        },
        "coverage_lanes": {
            "market_jsonl": market["line_count"],
            "adversarial_jsonl": adv["line_count"],
            "summary_market": summary.get("market_indicator_count"),
            "summary_adversarial": summary.get("adversarial_count")
        },
        "display": {
            "exists": bool(display),
            "sections": [s.get("id") for s in (display.get("sections") or [])],
            "source_authority_ok": (display.get("health") or {}).get("source_authority_ok")
        },
        "hot_gateway": {
            "exists": bool(hot),
            "hot_queue_count": hot.get("hot_queue_count"),
            "source_health": hot.get("source_health"),
            "authority": hot.get("authority")
        }
    }

    decision = "OK_PRODUCER_HEALTH_WATCH_AND_HOT_GATEWAY_REVIEW" if not blockers else "BLOCKED_PRODUCER_HEALTH_WATCH_AND_HOT_GATEWAY_REVIEW"

    payload = {
        "schema_version": "1.0",
        "review": "NEWS_PRODUCER_HEALTH_WATCH_AND_HOT_GATEWAY_REVIEW_V1",
        "generated_at_utc": utc_now(),
        "decision": decision,
        "mode": "NOAPI_READONLY_HEALTH_WATCH_AND_INTEGRATION_REVIEW",
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
        "integration": integration,
        "db": db,
        "jsonl": {
            "market": market,
            "adversarial": adv
        },
        "previous_stabilization": {
            "exists": bool(stab),
            "warnings": stab.get("warnings"),
            "systemd": stab.get("systemd")
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
            "tail": journal["stdout"].splitlines()[-25:],
            "stderr": journal["stderr"]
        },
        "blockers": blockers,
        "warnings": warnings,
        "next_recommendation": "Choose active panel binding only after explicit approval, or keep read-only producer watch running as manual review."
    }
    write_json(OUT, payload)
    print(json.dumps({
        "decision": decision,
        "raw": raw,
        "match": match,
        "signal": signal,
        "score": score,
        "market_jsonl": market["line_count"],
        "adversarial_jsonl": adv["line_count"],
        "summary_market": summary.get("market_indicator_count"),
        "summary_adversarial": summary.get("adversarial_count"),
        "hot_queue_count": hot.get("hot_queue_count"),
        "timer_active": timer_active.get("stdout"),
        "timer_enabled": timer_enabled.get("stdout"),
        "blockers": blockers,
        "warnings": warnings,
        "output": str(OUT)
    }, ensure_ascii=False, sort_keys=True))
    return 0 if not blockers else 2

if __name__ == "__main__":
    raise SystemExit(main())
