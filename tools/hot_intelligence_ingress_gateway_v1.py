#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List
import hashlib
import json
import os

ROOT = Path("/root/tokenoskobi_clean_v1")
DISPLAY = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
OUT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def uid_for(obj: Dict[str, Any], lane: str) -> str:
    raw = "|".join([
        lane,
        str(obj.get("event_uid") or ""),
        str(obj.get("news_uid") or ""),
        str(obj.get("title") or "")
    ])
    return "hot_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

def score_item(item: Dict[str, Any], lane: str) -> int:
    hits = item.get("hits") if isinstance(item.get("hits"), list) else []
    base = len(hits) * 10
    if lane == "ADVERSARIAL_NEWS":
        base += 15
    if item.get("published_at_utc"):
        base += 5
    return base

def normalize_items(display: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for section in display.get("sections") or []:
        sid = section.get("id")
        if sid == "news_market_indicator":
            lane = "MARKET_INDICATOR"
        elif sid == "news_adversarial_intelligence":
            lane = "ADVERSARIAL_NEWS"
        else:
            continue
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            authority = item.get("authority") or {}
            if authority.get("db_write") is not False:
                continue
            if authority.get("hunter_authorized") is not False:
                continue
            if authority.get("trade_signal") is not False:
                continue
            if authority.get("paper_signal") is not False:
                continue
            hot = {
                "hot_uid": uid_for(item, lane),
                "lane": lane,
                "event_uid": item.get("event_uid"),
                "news_uid": item.get("news_uid"),
                "title": item.get("title"),
                "hits": item.get("hits") or [],
                "published_at_utc": item.get("published_at_utc"),
                "source_uid": item.get("source_uid"),
                "priority_score": score_item(item, lane),
                "gateway_decision": "REVIEW_ONLY",
                "authority": {
                    "db_write": False,
                    "hunter_authorized": False,
                    "trade_signal": False,
                    "paper_signal": False,
                    "live_trade": False,
                    "execution_authority": False
                }
            }
            items.append(hot)
    seen = set()
    deduped = []
    for item in sorted(items, key=lambda x: (-int(x.get("priority_score") or 0), str(x.get("hot_uid") or ""))):
        uid = item.get("hot_uid")
        if uid in seen:
            continue
        seen.add(uid)
        deduped.append(item)
    return deduped[:50]

def main() -> int:
    display = read_json(DISPLAY)
    summary = read_json(SUMMARY)
    queue = normalize_items(display)
    payload = {
        "schema_version": "1.0",
        "gateway": "HOT_INTELLIGENCE_INGRESS_GATEWAY_V1",
        "generated_at_utc": utc_now(),
        "mode": "NOAPI_READONLY_REVIEW_GATEWAY",
        "sources": {
            "display_json": str(DISPLAY),
            "summary_json": str(SUMMARY)
        },
        "authority": {
            "db_write": False,
            "db_schema_change": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "execution_authority": False,
            "service_change": False,
            "timer_change": False,
            "network_call": False,
            "external_api_call": False
        },
        "source_health": {
            "display_exists": bool(display),
            "summary_exists": bool(summary),
            "display_source_authority_ok": bool((display.get("health") or {}).get("source_authority_ok")),
            "summary_parse_errors": summary.get("parse_errors", 0),
            "summary_duplicate_event_uids": summary.get("duplicate_event_uids", 0),
            "summary_unsafe_events": summary.get("unsafe_events", 0)
        },
        "hot_queue_count": len(queue),
        "hot_queue": queue
    }
    write_json(OUT, payload)
    print(json.dumps({
        "gateway": payload["gateway"],
        "hot_queue_count": len(queue),
        "display_exists": payload["source_health"]["display_exists"],
        "summary_exists": payload["source_health"]["summary_exists"],
        "execution_authority": False,
        "output": str(OUT)
    }, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
