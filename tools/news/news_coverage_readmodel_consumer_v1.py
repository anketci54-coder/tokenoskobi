#!/usr/bin/env python3
# TOKENOSKOBI NEWS COVERAGE READMODEL CONSUMER V1
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json
import os
from typing import Any, Dict, List, Tuple

ROOT = Path("/root/tokenoskobi_clean_v1")
MARKET_EVENTS = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL_EVENTS = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
MARKET_LATEST = ROOT / "runtime/state/news_market_indicator_latest_v1.json"
ADVERSARIAL_LATEST = ROOT / "runtime/state/news_adversarial_latest_v1.json"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def read_lane(path: Path, expected_lane: str, max_events: int = 100) -> Dict[str, Any]:
    events: List[Dict[str, Any]] = []
    parse_errors = 0
    unsafe_events = 0
    duplicate_event_uids = 0
    seen = set()
    top_hits = Counter()

    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "expected_lane": expected_lane,
            "events": [],
            "count": 0,
            "parse_errors": 0,
            "duplicate_event_uids": 0,
            "unsafe_events": 0,
            "top_hits": {},
            "warnings": ["missing_file"]
        }

    raw_events: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                parse_errors += 1
                continue

            uid = str(obj.get("event_uid") or "").strip()
            if uid:
                if uid in seen:
                    duplicate_event_uids += 1
                    continue
                seen.add(uid)

            if (
                obj.get("lane") != expected_lane or
                obj.get("hunter_authorized") is not False or
                obj.get("db_match_write") is not False or
                obj.get("trade_signal") is not False or
                obj.get("paper_signal") is not False
            ):
                unsafe_events += 1
                continue

            for h in obj.get("hits") or []:
                top_hits[str(h)] += 1

            raw_events.append({
                "event_uid": obj.get("event_uid"),
                "lane": obj.get("lane"),
                "news_uid": obj.get("news_uid"),
                "title": obj.get("title"),
                "hits": obj.get("hits") or [],
                "published_at_utc": obj.get("published_at_utc"),
                "fetched_at_utc": obj.get("fetched_at_utc"),
                "source_uid": obj.get("source_uid"),
                "hunter_authorized": False,
                "db_match_write": False,
                "trade_signal": False,
                "paper_signal": False
            })

    events = raw_events[-max_events:]

    return {
        "path": str(path),
        "exists": True,
        "expected_lane": expected_lane,
        "events": events,
        "count": len(raw_events),
        "returned_count": len(events),
        "parse_errors": parse_errors,
        "duplicate_event_uids": duplicate_event_uids,
        "unsafe_events": unsafe_events,
        "top_hits": dict(top_hits.most_common(50)),
        "warnings": []
    }

def build_summary(max_events_per_lane: int = 100) -> Dict[str, Any]:
    market = read_lane(MARKET_EVENTS, "MARKET_INDICATOR", max_events_per_lane)
    adversarial = read_lane(ADVERSARIAL_EVENTS, "ADVERSARIAL_NEWS", max_events_per_lane)

    payload = {
        "schema_version": "1.0",
        "consumer": "NEWS_COVERAGE_READMODEL_CONSUMER_V1",
        "generated_at_utc": utc_now(),
        "authority": {
            "db_write": False,
            "news_token_match_events_write": False,
            "news_signal_events_write": False,
            "news_score_events_v1_write": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "panel_change": False,
            "service_timer_change": False
        },
        "inputs": {
            "market_indicator_jsonl": str(MARKET_EVENTS),
            "adversarial_jsonl": str(ADVERSARIAL_EVENTS)
        },
        "market_indicator_count": market["count"],
        "adversarial_count": adversarial["count"],
        "latest_market": list(reversed(market["events"]))[:25],
        "latest_adversarial": list(reversed(adversarial["events"]))[:25],
        "top_market_hits": market["top_hits"],
        "top_adversarial_hits": adversarial["top_hits"],
        "parse_errors": market["parse_errors"] + adversarial["parse_errors"],
        "duplicate_event_uids": market["duplicate_event_uids"] + adversarial["duplicate_event_uids"],
        "unsafe_events": market["unsafe_events"] + adversarial["unsafe_events"],
        "lane_health": {
            "market": {
                "exists": market["exists"],
                "count": market["count"],
                "returned_count": market["returned_count"],
                "parse_errors": market["parse_errors"],
                "duplicate_event_uids": market["duplicate_event_uids"],
                "unsafe_events": market["unsafe_events"],
                "warnings": market["warnings"]
            },
            "adversarial": {
                "exists": adversarial["exists"],
                "count": adversarial["count"],
                "returned_count": adversarial["returned_count"],
                "parse_errors": adversarial["parse_errors"],
                "duplicate_event_uids": adversarial["duplicate_event_uids"],
                "unsafe_events": adversarial["unsafe_events"],
                "warnings": adversarial["warnings"]
            }
        }
    }

    atomic_write_json(SUMMARY, payload)
    atomic_write_json(MARKET_LATEST, {
        "schema_version": "1.0",
        "generated_at_utc": payload["generated_at_utc"],
        "lane": "MARKET_INDICATOR",
        "count": market["count"],
        "top_hits": market["top_hits"],
        "latest": payload["latest_market"],
        "authority": payload["authority"]
    })
    atomic_write_json(ADVERSARIAL_LATEST, {
        "schema_version": "1.0",
        "generated_at_utc": payload["generated_at_utc"],
        "lane": "ADVERSARIAL_NEWS",
        "count": adversarial["count"],
        "top_hits": adversarial["top_hits"],
        "latest": payload["latest_adversarial"],
        "authority": payload["authority"]
    })
    return payload

def main() -> int:
    payload = build_summary(100)
    print(json.dumps({
        "consumer": payload["consumer"],
        "market_indicator_count": payload["market_indicator_count"],
        "adversarial_count": payload["adversarial_count"],
        "parse_errors": payload["parse_errors"],
        "duplicate_event_uids": payload["duplicate_event_uids"],
        "unsafe_events": payload["unsafe_events"],
        "summary": str(SUMMARY),
        "market_latest": str(MARKET_LATEST),
        "adversarial_latest": str(ADVERSARIAL_LATEST)
    }, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
