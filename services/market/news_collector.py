"""Read-only news collector: public RSS/Atom feeds -> local SQLite the panel already reads.

It only downloads feeds. It never trusts feed text as instructions, never follows links and has no
trading authority. Each run records a heartbeat (how many sources answered), which is what lets the
panel tell "scanned, nothing about this token" apart from "never scanned".

Run:  python3 -m services.market.news_collector [--once | --report]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from contextlib import closing
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable

from core.platform.paths import get_root

ROOT = get_root()
CONFIG = ROOT / "config/news_feeds_v1.json"
NEWS_DB = ROOT / "data/tokenoskobi_news.sqlite"
MAX_BYTES = 2_000_000
MAX_ITEMS_PER_FEED = 60
RETAIN_DAYS = 14

SCHEMA = """
CREATE TABLE IF NOT EXISTS news_raw_feed_events(
  id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT, guid TEXT, title TEXT, summary TEXT,
  link TEXT, published_at_utc TEXT, fetched_at_utc TEXT, UNIQUE(source_id, guid));
CREATE TABLE IF NOT EXISTS news_collector_runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_at REAL, sources_total INTEGER, sources_ok INTEGER,
  min_ok INTEGER, items_new INTEGER, detail TEXT);
"""

Fetch = Callable[[str], bytes]


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "tokenoskobi-news/1 (read-only)"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("FEED_TOO_LARGE")
    return data


def _text(element: ET.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _iso(value: str) -> str | None:
    """Return a timezone-aware UTC ISO time, or None. A date without a zone is not trusted."""
    value = value.strip()
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)  # RFC 822 (RSS)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))  # ISO 8601 (Atom)
        except ValueError:
            return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc).isoformat()


def parse_feed(data: bytes) -> list[dict[str, str | None]]:
    """Parse RSS 2.0 or Atom. Raises ValueError on anything that is not a clean feed."""
    if b"<!doctype" in data[:100000].lower() or b"<!entity" in data.lower():
        raise ValueError("DTD_OR_ENTITY_REJECTED")  # blocks entity-expansion tricks
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError("FEED_NOT_XML") from exc
    items: list[dict[str, str | None]] = []
    tag = root.tag.split("}")[-1].lower()
    if tag == "rss":
        for item in root.iter("item"):
            items.append({
                "guid": _text(item.find("guid")) or _text(item.find("link")) or _text(item.find("title")),
                "title": _text(item.find("title")), "summary": _text(item.find("description")),
                "link": _text(item.find("link")), "published": _iso(_text(item.find("pubDate")))})
    elif tag == "feed":
        for entry in root.iter():
            if entry.tag.split("}")[-1] != "entry":
                continue
            def child(name: str) -> ET.Element | None:
                return next((c for c in entry if c.tag.split("}")[-1] == name), None)
            link = child("link")
            items.append({
                "guid": _text(child("id")) or (link.get("href") if link is not None else "") or _text(child("title")),
                "title": _text(child("title")), "summary": _text(child("summary")) or _text(child("content")),
                "link": (link.get("href") or "") if link is not None else "",
                "published": _iso(_text(child("published")) or _text(child("updated")))})
    else:
        raise ValueError("FEED_FORMAT_UNKNOWN")
    items = [item for item in items if item["guid"] and item["title"]]
    if not items:
        raise ValueError("FEED_EMPTY")
    return items[:MAX_ITEMS_PER_FEED]


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    return db


def run_once(db: sqlite3.Connection, config: dict[str, Any], get: Fetch, now: float | None = None) -> dict[str, Any]:
    now = time.time() if now is None else now
    stamp = datetime.fromtimestamp(now, timezone.utc).isoformat()
    feeds = [f for f in config.get("feeds", []) if f.get("source_id") and f.get("url")]
    status: dict[str, str] = {}
    new_items = 0
    for feed in feeds:
        try:
            items = parse_feed(get(feed["url"]))
        except Exception as exc:
            status[feed["source_id"]] = f"FAIL {type(exc).__name__}:{str(exc)[:60]}"
            continue
        with db:
            for item in items:
                cursor = db.execute(
                    "INSERT OR IGNORE INTO news_raw_feed_events(source_id, guid, title, summary, link,"
                    " published_at_utc, fetched_at_utc) VALUES(?,?,?,?,?,?,?)",
                    (feed["source_id"], item["guid"], item["title"], (item["summary"] or "")[:2000],
                     item["link"], item["published"], stamp))
                new_items += cursor.rowcount
        status[feed["source_id"]] = f"OK {len(items)}"
    ok = sum(1 for value in status.values() if value.startswith("OK"))
    min_ok = int(config.get("min_sources_ok", 2))
    with db:
        db.execute("INSERT INTO news_collector_runs(run_at, sources_total, sources_ok, min_ok, items_new, detail)"
                   " VALUES(?,?,?,?,?,?)", (now, len(feeds), ok, min_ok, new_items, json.dumps(status)))
        db.execute("DELETE FROM news_raw_feed_events WHERE fetched_at_utc < ?",
                   (datetime.fromtimestamp(now - RETAIN_DAYS * 86400, timezone.utc).isoformat(),))
        db.execute("DELETE FROM news_collector_runs WHERE run_at < ?", (now - RETAIN_DAYS * 86400,))
    return {"sources_total": len(feeds), "sources_ok": ok, "items_new": new_items, "status": status}


def report(db: sqlite3.Connection) -> str:
    run = db.execute("SELECT * FROM news_collector_runs ORDER BY run_at DESC LIMIT 1").fetchone()
    if run is None:
        return "Haber toplayıcı: henüz çalışmadı."
    when = datetime.fromtimestamp(run["run_at"], timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"Haber toplayıcı raporu (son tarama {when} UTC)",
             f"  kaynak: {run['sources_ok']}/{run['sources_total']} açıldı (en az {run['min_ok']} gerekir) · yeni haber: {run['items_new']}"]
    lines += [f"  {name}: {value}" for name, value in json.loads(run["detail"] or "{}").items()]
    total = db.execute("SELECT COUNT(*) FROM news_raw_feed_events").fetchone()[0]
    lines.append(f"  kayıtlı haber: {total}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Haber toplayıcı (salt okunur, danışma amaçlı)")
    parser.add_argument("--interval", type=float, default=600.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(argv)
    with closing(connect(NEWS_DB)) as db:
        if args.report:
            print(report(db))
            return 0
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        while True:
            try:
                result = run_once(db, config, fetch)
                print(time.strftime("%H:%M:%S", time.gmtime()),
                      json.dumps({k: v for k, v in result.items() if k != "status"}), flush=True)
            except KeyboardInterrupt:
                return 0
            except Exception as exc:
                print(f"HATA {type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr, flush=True)
            if args.once:
                return 0
            try:
                time.sleep(args.interval)
            except KeyboardInterrupt:
                return 0


if __name__ == "__main__":
    raise SystemExit(main())
