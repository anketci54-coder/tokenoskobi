#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict
import hashlib
import html
import json
import os
import shutil
import tempfile

ROOT = Path("/root/tokenoskobi_clean_v1")
ACTIVE = ROOT / "active_panel_8096/current"
ACTIVE_DATA = ACTIVE / "data"
INDEX = ACTIVE / "index.html"
NEWS_PAGE = ACTIVE / "news_coverage.html"
OUT = ROOT / "runtime/state/news_active_panel_ui_route_binding_v1.json"
BACKUP_DIR = ROOT / "data/backups/active_panel_ui_news_binding"

MARKER_BEGIN = "<!-- TOKENOSKOBI_NEWS_UI_LINK_BEGIN -->"
MARKER_END = "<!-- TOKENOSKOBI_NEWS_UI_LINK_END -->"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".ui_bind_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".ui_bind_", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        json.loads(Path(tmp).read_text(encoding="utf-8"))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def load_sources() -> Dict[str, Any]:
    required = {
        "summary": ACTIVE_DATA / "news_coverage_readmodel_consumer_summary_v1.json",
        "market": ACTIVE_DATA / "news_market_indicator_latest_v1.json",
        "adversarial": ACTIVE_DATA / "news_adversarial_latest_v1.json",
        "display": ACTIVE_DATA / "news_coverage_panel_display_v1.json",
        "hot": ACTIVE_DATA / "hot_intelligence_ingress_gateway_v1.json",
        "watch": ACTIVE_DATA / "news_producer_health_watch_and_hot_gateway_review_v1.json",
        "stabilization": ACTIVE_DATA / "news_runtime_stabilization_review_v1.json",
        "manifest": ACTIVE_DATA / "news_active_panel_data_bridge_manifest_v1.json",
    }
    out: Dict[str, Any] = {}
    missing = []
    for k, p in required.items():
        if not p.exists():
            missing.append(str(p))
        else:
            out[k] = read_json(p)
    if missing:
        raise RuntimeError("missing active panel data: " + ", ".join(missing))
    return out

def render_news_page(sources: Dict[str, Any]) -> str:
    summary = sources["summary"]
    hot = sources["hot"]
    watch = sources["watch"]
    display = sources["display"]

    market_count = summary.get("market_indicator_count")
    adversarial_count = summary.get("adversarial_count")
    hot_count = hot.get("hot_queue_count")
    raw = ((watch.get("integration") or {}).get("producer") or {}).get("raw_count")
    match = ((watch.get("integration") or {}).get("downstream_db") or {}).get("match_count")
    signal = ((watch.get("integration") or {}).get("downstream_db") or {}).get("signal_count")
    score = ((watch.get("integration") or {}).get("downstream_db") or {}).get("score_count")
    timer_active = ((watch.get("integration") or {}).get("producer") or {}).get("timer_active")
    timer_enabled = ((watch.get("integration") or {}).get("producer") or {}).get("timer_enabled")
    warnings = watch.get("warnings") or []
    sections = display.get("sections") or []

    section_cards = []
    for section in sections:
        title = html.escape(str(section.get("title") or section.get("id") or "section"))
        count = html.escape(str(section.get("count") if section.get("count") is not None else ""))
        items = section.get("items") or []
        lis = []
        for item in items[:12]:
            ititle = html.escape(str(item.get("title") or ""))
            lane = html.escape(str(item.get("lane") or ""))
            hits = ", ".join(str(x) for x in (item.get("hits") or [])[:6])
            hits = html.escape(hits)
            lis.append(f"<li><b>{ititle}</b><br><span>{lane} · {hits}</span></li>")
        section_cards.append(f"""
        <section class="card">
          <h2>{title} <small>{count}</small></h2>
          <ul>{''.join(lis) if lis else '<li>Veri yok</li>'}</ul>
        </section>
        """)

    warnings_html = "".join(f"<li>{html.escape(str(w))}</li>" for w in warnings) or "<li>Bloklayıcı uyarı yok</li>"

    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Tokenoskobi NEWS Intelligence</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin:0; font-family:Arial,Helvetica,sans-serif; background:#07111f; color:#eaf2ff; }}
    header {{ padding:22px 18px; background:#0d1b2f; border-bottom:1px solid #213552; }}
    h1 {{ margin:0 0 6px; font-size:24px; }}
    .sub {{ color:#9fb4d1; font-size:13px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; padding:16px; }}
    .metric,.card {{ background:#101f35; border:1px solid #263a59; border-radius:14px; padding:14px; }}
    .metric b {{ display:block; font-size:26px; margin-bottom:4px; }}
    .metric span,.card span,small {{ color:#9fb4d1; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; padding:0 16px 18px; }}
    ul {{ margin:8px 0 0; padding-left:18px; }}
    li {{ margin:9px 0; line-height:1.35; }}
    a {{ color:#8fc7ff; }}
    footer {{ color:#7087a8; font-size:12px; padding:16px; border-top:1px solid #213552; }}
  </style>
</head>
<body>
<header>
  <h1>NEWS Intelligence</h1>
  <div class="sub">Read-only panel view · DB/trade/live authority yok · generated {html.escape(utc_now())}</div>
</header>

<div class="grid">
  <div class="metric"><b>{html.escape(str(raw))}</b><span>Raw haber</span></div>
  <div class="metric"><b>{html.escape(str(match))}</b><span>DB match</span></div>
  <div class="metric"><b>{html.escape(str(signal))}</b><span>DB signal</span></div>
  <div class="metric"><b>{html.escape(str(score))}</b><span>DB score</span></div>
  <div class="metric"><b>{html.escape(str(market_count))}</b><span>Market JSONL</span></div>
  <div class="metric"><b>{html.escape(str(adversarial_count))}</b><span>Adversarial JSONL</span></div>
  <div class="metric"><b>{html.escape(str(hot_count))}</b><span>Hot queue</span></div>
  <div class="metric"><b>{html.escape(str(timer_active))}/{html.escape(str(timer_enabled))}</b><span>Timer</span></div>
</div>

<div class="cards">
  {''.join(section_cards)}
  <section class="card">
    <h2>Health</h2>
    <ul>{warnings_html}</ul>
  </section>
</div>

<footer>
  Data source: <code>active_panel_8096/current/data/*.json</code> · Static route: <code>/news_coverage.html</code>
</footer>
</body>
</html>
"""

def update_index() -> Dict[str, Any]:
    ACTIVE.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backup = None
    before_sha = None
    index_created = False

    snippet = f"""{MARKER_BEGIN}
<a href="news_coverage.html" style="display:inline-block;margin:8px 8px 8px 0;padding:10px 14px;border-radius:12px;background:#10233b;color:#eaf2ff;text-decoration:none;border:1px solid #29486f;">NEWS Intelligence</a>
{MARKER_END}"""

    if INDEX.exists():
        before_sha = sha256(INDEX)
        backup = BACKUP_DIR / ("index_before_news_ui_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".html")
        shutil.copy2(INDEX, backup)
        text = INDEX.read_text(encoding="utf-8", errors="replace")
        if MARKER_BEGIN in text and MARKER_END in text:
            start = text.index(MARKER_BEGIN)
            end = text.index(MARKER_END) + len(MARKER_END)
            new_text = text[:start] + snippet + text[end:]
        elif "</body>" in text.lower():
            idx = text.lower().rfind("</body>")
            new_text = text[:idx] + "\n" + snippet + "\n" + text[idx:]
        else:
            new_text = text + "\n" + snippet + "\n"
    else:
        index_created = True
        new_text = f"""<!doctype html>
<html lang="tr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tokenoskobi Panel</title></head>
<body style="font-family:Arial,Helvetica,sans-serif;background:#07111f;color:#eaf2ff;padding:20px;">
<h1>Tokenoskobi Panel</h1>
{snippet}
</body>
</html>
"""

    atomic_write_text(INDEX, new_text)
    return {
        "index_exists_after": INDEX.exists(),
        "index_created": index_created,
        "index_backup": str(backup) if backup else None,
        "index_sha_before": before_sha,
        "index_sha_after": sha256(INDEX),
        "marker_present": MARKER_BEGIN in INDEX.read_text(encoding="utf-8", errors="replace"),
    }

def main() -> int:
    failures: list[str] = []
    sources = load_sources()

    page = render_news_page(sources)
    atomic_write_text(NEWS_PAGE, page)

    index_result = update_index()

    page_text = NEWS_PAGE.read_text(encoding="utf-8", errors="replace")
    if "NEWS Intelligence" not in page_text:
        failures.append("news_page_marker_missing")
    if "active_panel_8096/current/data" not in page_text:
        failures.append("news_page_source_note_missing")
    if not index_result.get("marker_present"):
        failures.append("index_marker_missing")

    status = {
        "schema_version": "1.0",
        "stage": "NEWS_ACTIVE_PANEL_UI_ROUTE_BINDING_V1",
        "generated_at_utc": utc_now(),
        "decision": "OK_NEWS_ACTIVE_PANEL_UI_ROUTE_BOUND" if not failures else "FAIL_NEWS_ACTIVE_PANEL_UI_ROUTE_BINDING",
        "active_panel_dir": str(ACTIVE),
        "news_page": str(NEWS_PAGE),
        "news_page_exists": NEWS_PAGE.exists(),
        "news_page_sha256": sha256(NEWS_PAGE) if NEWS_PAGE.exists() else None,
        "index": str(INDEX),
        "index_result": index_result,
        "route": "/news_coverage.html",
        "authority": {
            "db_write": False,
            "db_schema_change": False,
            "service_change": False,
            "timer_change": False,
            "panel_data_write": False,
            "panel_html_change": True,
            "network_call": False,
            "external_api_call": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "execution_authority": False
        },
        "source_summary": {
            "summary_market": sources["summary"].get("market_indicator_count"),
            "summary_adversarial": sources["summary"].get("adversarial_count"),
            "hot_queue_count": sources["hot"].get("hot_queue_count"),
            "watch_warnings": sources["watch"].get("warnings"),
        },
        "failures": failures,
        "next": "LOCALHOST_PANEL_STATIC_SERVE_PROBE_SINGLE_BLOCK"
    }
    atomic_write_json(OUT, status)

    print(json.dumps({
        "decision": status["decision"],
        "route": status["route"],
        "news_page": status["news_page"],
        "index": status["index"],
        "index_marker": status["index_result"]["marker_present"],
        "failures": failures,
        "output": str(OUT)
    }, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 2

if __name__ == "__main__":
    raise SystemExit(main())
