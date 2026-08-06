#!/usr/bin/env python3
# TOKENOSKOBI NEWS COVERAGE PANEL DISPLAY ADAPTER V1
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List
import json
import os
import html

ROOT = Path("/root/tokenoskobi_clean_v1")
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
DISPLAY_JSON = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
DISPLAY_HTML = ROOT / "runtime/state/news_coverage_panel_display_v1.html"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def read_summary() -> Dict[str, Any]:
    if not SUMMARY.exists():
        return {}
    return json.loads(SUMMARY.read_text(encoding="utf-8"))

def safe_items(items: Any, max_items: int = 25) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    for obj in items[:max_items]:
        if not isinstance(obj, dict):
            continue
        out.append({
            "event_uid": obj.get("event_uid"),
            "news_uid": obj.get("news_uid"),
            "title": obj.get("title"),
            "hits": obj.get("hits") or [],
            "published_at_utc": obj.get("published_at_utc"),
            "source_uid": obj.get("source_uid"),
            "lane": obj.get("lane"),
            "authority": {
                "db_write": False,
                "hunter_authorized": False,
                "trade_signal": False,
                "paper_signal": False,
                "live_trade": False
            }
        })
    return out

def build_display_payload() -> Dict[str, Any]:
    summary = read_summary()
    auth = summary.get("authority") or {}

    payload = {
        "schema_version": "1.0",
        "adapter": "NEWS_COVERAGE_PANEL_DISPLAY_ADAPTER_V1",
        "generated_at_utc": utc_now(),
        "source": str(SUMMARY),
        "authority": {
            "db_write": False,
            "db_schema_change": False,
            "news_token_match_events_write": False,
            "news_signal_events_write": False,
            "news_score_events_v1_write": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "service_change": False,
            "timer_change": False,
            "active_panel_mutation": False
        },
        "health": {
            "summary_exists": bool(summary),
            "parse_errors": summary.get("parse_errors", 0),
            "duplicate_event_uids": summary.get("duplicate_event_uids", 0),
            "unsafe_events": summary.get("unsafe_events", 0),
            "source_authority_ok": (
                auth.get("db_write") is False and
                auth.get("hunter_authorized") is False and
                auth.get("trade_signal") is False and
                auth.get("paper_signal") is False and
                auth.get("live_trade") is False
            )
        },
        "sections": [
            {
                "id": "news_market_indicator",
                "title": "NEWS Market Indicators",
                "count": summary.get("market_indicator_count", 0),
                "top_hits": summary.get("top_market_hits") or {},
                "items": safe_items(summary.get("latest_market"), 25)
            },
            {
                "id": "news_adversarial_intelligence",
                "title": "NEWS Adversarial Intelligence",
                "count": summary.get("adversarial_count", 0),
                "top_hits": summary.get("top_adversarial_hits") or {},
                "items": safe_items(summary.get("latest_adversarial"), 25)
            },
            {
                "id": "news_coverage_health",
                "title": "NEWS Coverage Health",
                "count": 1,
                "top_hits": {},
                "items": [{
                    "parse_errors": summary.get("parse_errors", 0),
                    "duplicate_event_uids": summary.get("duplicate_event_uids", 0),
                    "unsafe_events": summary.get("unsafe_events", 0),
                    "lane_health": summary.get("lane_health") or {},
                    "authority": {
                        "db_write": False,
                        "hunter_authorized": False,
                        "trade_signal": False,
                        "paper_signal": False,
                        "live_trade": False
                    }
                }]
            }
        ]
    }
    return payload

def render_html(payload: Dict[str, Any]) -> str:
    def e(x: Any) -> str:
        return html.escape("" if x is None else str(x))

    parts: List[str] = []
    parts.append("<!doctype html><html lang='tr'><head><meta charset='utf-8'>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    parts.append("<title>Tokenoskobi NEWS Coverage Display</title>")
    parts.append("<style>")
    parts.append("body{margin:0;background:#08111f;color:#e9f1ff;font-family:Arial,Helvetica,sans-serif}")
    parts.append(".wrap{max-width:1180px;margin:0 auto;padding:18px}")
    parts.append(".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}")
    parts.append(".card{background:#101a2d;border:1px solid #243653;border-radius:16px;padding:14px}")
    parts.append(".item{border-top:1px solid #243653;padding:10px 0}")
    parts.append(".pill{display:inline-block;background:#172b52;border-radius:999px;padding:4px 8px;margin:2px;font-size:12px}")
    parts.append(".muted{color:#9fb1ca;font-size:12px}")
    parts.append("</style></head><body><div class='wrap'>")
    parts.append("<h1>Tokenoskobi NEWS Coverage Display</h1>")
    parts.append("<p class='muted'>Read-only intelligence display. Hunter/trade/paper/live authority: false.</p>")
    parts.append("<p class='muted'>Generated: " + e(payload.get("generated_at_utc")) + "</p>")
    parts.append("<div class='grid'>")

    for sec in payload.get("sections", []):
        parts.append("<section class='card'>")
        parts.append("<h2>" + e(sec.get("title")) + " (" + e(sec.get("count")) + ")</h2>")
        if sec.get("top_hits"):
            parts.append("<div>")
            for k, v in list((sec.get("top_hits") or {}).items())[:12]:
                parts.append("<span class='pill'>" + e(k) + ": " + e(v) + "</span>")
            parts.append("</div>")
        for item in sec.get("items", [])[:25]:
            parts.append("<div class='item'>")
            if item.get("title"):
                parts.append("<strong>" + e(item.get("title")) + "</strong>")
            if item.get("published_at_utc"):
                parts.append("<div class='muted'>" + e(item.get("published_at_utc")) + "</div>")
            if item.get("hits"):
                parts.append("<div>")
                for h in item.get("hits") or []:
                    parts.append("<span class='pill'>" + e(h) + "</span>")
                parts.append("</div>")
            if "parse_errors" in item:
                parts.append("<div class='muted'>parse_errors=" + e(item.get("parse_errors")) + " duplicate_event_uids=" + e(item.get("duplicate_event_uids")) + " unsafe_events=" + e(item.get("unsafe_events")) + "</div>")
            parts.append("</div>")
        parts.append("</section>")

    parts.append("</div></div></body></html>\n")
    return "".join(parts)

def main() -> int:
    payload = build_display_payload()
    atomic_write_json(DISPLAY_JSON, payload)
    atomic_write_text(DISPLAY_HTML, render_html(payload))
    print(json.dumps({
        "adapter": payload["adapter"],
        "summary_exists": payload["health"]["summary_exists"],
        "source_authority_ok": payload["health"]["source_authority_ok"],
        "market_count": payload["sections"][0]["count"],
        "adversarial_count": payload["sections"][1]["count"],
        "parse_errors": payload["health"]["parse_errors"],
        "duplicate_event_uids": payload["health"]["duplicate_event_uids"],
        "unsafe_events": payload["health"]["unsafe_events"],
        "display_json": str(DISPLAY_JSON),
        "display_html": str(DISPLAY_HTML)
    }, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
