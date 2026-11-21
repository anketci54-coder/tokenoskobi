"""Send watcher candidates, one at a time, through the local panel's analysis.

It only calls the panel's advisory analyze endpoint on 127.0.0.1 (the same path as typing an address
into the panel), so every result becomes an immutable packet in the panel's history. It records no human
decision, holds no keys and cannot trade. A token is analysed once; failures are retried a few times.

Run:  python3 -m services.market.candidate_analyzer --state-dir DIR [--once | --report]
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

from services.market.pair_watcher import (CANDIDATE_KEEP_FRACTION, CANDIDATE_MIN_AGE_MIN, Store,
                                          candidate_rows)

SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses(
  token TEXT PRIMARY KEY, analyzed_at REAL, status TEXT, decision TEXT, risk INTEGER,
  quality TEXT, packet_id TEXT, blockers TEXT, warnings TEXT, error TEXT,
  attempts INTEGER DEFAULT 0, next_try REAL, sell_state TEXT, lp_state TEXT);
"""
EXTRA_COLUMNS = ("sell_state", "lp_state")
MAX_ATTEMPTS = 3
RETRY_BASE_SEC = 600.0
PANEL_DOWN_SLEEP_SEC = 60.0

Post = Callable[[str], dict[str, Any]]


class PanelUnreachable(RuntimeError):
    """The local panel is not answering; this is not the token's fault."""


def panel_post(token: str) -> dict[str, Any]:
    port = int(os.getenv("TOKENOSKOBI_PRODUCT_SLICE_02_PORT", "8096"))
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/v1/analyze",
        data=json.dumps({"token_address": token}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read(4_000_000))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP_{exc.code}") from exc
    except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
        raise PanelUnreachable(type(exc).__name__) from exc


def ensure_table(store: Store) -> None:
    store.db.executescript(SCHEMA)
    have = {r["name"] for r in store.db.execute("PRAGMA table_info(analyses)")}
    for column in EXTRA_COLUMNS:
        if column not in have:
            store.db.execute(f"ALTER TABLE analyses ADD COLUMN {column} TEXT")
    store.db.commit()


def pick(store: Store, now: float, min_age_min: float, keep_fraction: float) -> str | None:
    done = {r["token"]: r for r in store.db.execute("SELECT * FROM analyses")}
    for row in sorted(candidate_rows(store, now, min_age_min, keep_fraction),
                      key=lambda r: r["since"], reverse=True):  # newest candidate first
        known = done.get(row["target"])
        if known is None:
            return row["target"]
        if known["status"] == "ERROR" and known["attempts"] < MAX_ATTEMPTS and known["next_try"] <= now:
            return row["target"]
    return None


def _state_label(block: Any, *keys: str) -> str | None:
    """Short, safe text for why a layer did or did not measure (status plus reason or ability)."""
    if not isinstance(block, dict):
        return "MISSING"
    parts = [str(block.get(key))[:40] for key in keys if isinstance(block.get(key), (str, int, float))]
    return ":".join(parts) or "MISSING"


def analyze_one(store: Store, token: str, post: Post, now: float) -> str:
    """Analyse one token. Returns OK, ERROR, or PANEL_DOWN (nothing recorded)."""
    previous = store.db.execute("SELECT attempts FROM analyses WHERE token=?", (token,)).fetchone()
    attempts = (previous["attempts"] if previous else 0) + 1
    try:
        result = post(token)
        decision = result.get("decision") or {}
        packet_id = (result.get("history") or {}).get("packet_id")
        if not decision.get("decision") or not packet_id:
            raise RuntimeError("RESPONSE_MISSING_DECISION")
    except PanelUnreachable:
        return "PANEL_DOWN"
    except Exception as exc:
        store.db.execute(
            "INSERT INTO analyses(token, analyzed_at, status, error, attempts, next_try)"
            " VALUES(?,?,?,?,?,?) ON CONFLICT(token) DO UPDATE SET analyzed_at=excluded.analyzed_at,"
            " status='ERROR', error=excluded.error, attempts=excluded.attempts, next_try=excluded.next_try",
            (token, now, "ERROR", f"{type(exc).__name__}:{str(exc)[:100]}", attempts,
             now + RETRY_BASE_SEC * attempts))
        store.db.commit()
        return "ERROR"
    store.db.execute(
        "INSERT INTO analyses(token, analyzed_at, status, decision, risk, quality, packet_id,"
        " blockers, warnings, attempts, sell_state, lp_state) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"
        " ON CONFLICT(token) DO UPDATE SET analyzed_at=excluded.analyzed_at, status='OK',"
        " decision=excluded.decision, risk=excluded.risk, quality=excluded.quality,"
        " packet_id=excluded.packet_id, blockers=excluded.blockers, warnings=excluded.warnings,"
        " error=NULL, attempts=excluded.attempts, sell_state=excluded.sell_state,"
        " lp_state=excluded.lp_state",
        (token, now, "OK", decision.get("decision"), decision.get("risk_score"),
         decision.get("data_quality"), packet_id, json.dumps(decision.get("blockers") or []),
         json.dumps(decision.get("warnings") or []), attempts,
         _state_label(result.get("swap_behavior"), "status", "reason", "sell_ability"),
         _state_label(result.get("lp_status"), "status", "reason")))
    store.db.commit()
    return "OK"


def step(store: Store, post: Post, now: float, min_age_min: float = CANDIDATE_MIN_AGE_MIN,
         keep_fraction: float = CANDIDATE_KEEP_FRACTION) -> str:
    token = pick(store, now, min_age_min, keep_fraction)
    if token is None:
        return "IDLE"
    return analyze_one(store, token, post, now)


def report(store: Store) -> str:
    db = store.db
    lines = ["Aday analizi raporu", ""]
    rows = db.execute("SELECT status, decision, COUNT(*) AS n FROM analyses GROUP BY status, decision"
                      " ORDER BY n DESC").fetchall()
    for row in rows:
        lines.append(f"  {row['status']} {row['decision'] or ''}: {row['n']}")
    if not rows:
        lines.append("  henüz analiz yok")
    ok_total = db.execute("SELECT COUNT(*) FROM analyses WHERE status='OK'").fetchone()[0]
    if ok_total:
        counts: dict[str, int] = {}
        for row in db.execute("SELECT warnings FROM analyses WHERE status='OK'"):
            for warning in set(json.loads(row["warnings"] or "[]")):
                counts[warning] = counts.get(warning, 0) + 1
        lines += ["", f"En sık uyarılar ({ok_total} analiz içinde):"]
        lines += [f"  {name}: {n} (%{100 * n / ok_total:.0f})"
                  for name, n in sorted(counts.items(), key=lambda i: -i[1])[:8]]
        for title, column in (("Satış davranışı durumları:", "sell_state"), ("LP durumları:", "lp_state")):
            lines += ["", title]
            for row in db.execute(f"SELECT {column} AS v, COUNT(*) AS n FROM analyses WHERE status='OK'"
                                  f" GROUP BY v ORDER BY n DESC LIMIT 6"):
                lines.append(f"  {row['v'] or 'eski kayıt (bilinmiyor)'}: {row['n']}")
    lines += ["", "Son analizler:"]
    latest = db.execute("SELECT * FROM analyses WHERE status='OK' ORDER BY analyzed_at DESC LIMIT 10").fetchall()
    for row in latest:
        blockers = ", ".join(json.loads(row["blockers"] or "[]")[:3]) or "-"
        warnings = ", ".join(json.loads(row["warnings"] or "[]")[:6]) or "-"
        lines.append(f"  {row['token']}  {row['decision']}  risk {row['risk']}  engel: {blockers}")
        lines.append(f"    uyarılar: {warnings}")
    errors = db.execute("SELECT token, error, attempts FROM analyses WHERE status='ERROR' LIMIT 5").fetchall()
    if errors:
        lines += ["", "Hatalar (yeniden denenecek veya vazgeçildi):"]
        lines += [f"  {r['token']}  {r['error']}  deneme {r['attempts']}" for r in errors]
    return "\n".join(lines + (["  yok"] if not latest else []))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aday tokenleri panel analizinden geçirir (danışma amaçlı)")
    parser.add_argument("--state-dir", default=str(Path.home() / ".local/state/tokenoskobi/watcher"))
    parser.add_argument("--interval", type=float, default=60.0, help="iki analiz arası saniye")
    parser.add_argument("--min-age", type=float, default=CANDIDATE_MIN_AGE_MIN)
    parser.add_argument("--keep-fraction", type=float, default=CANDIDATE_KEEP_FRACTION)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(argv)
    store = Store(Path(args.state_dir).expanduser() / "pairs.sqlite")
    with closing(store):
        ensure_table(store)
        if args.report:
            print(report(store))
            return 0
        while True:
            outcome = "IDLE"
            try:
                outcome = step(store, panel_post, time.time(), args.min_age, args.keep_fraction)
                print(time.strftime("%H:%M:%S", time.gmtime()), outcome, flush=True)
            except KeyboardInterrupt:
                return 0
            except Exception as exc:
                print(f"HATA {type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr, flush=True)
            if args.once:
                return 0
            try:
                time.sleep(PANEL_DOWN_SLEEP_SEC if outcome == "PANEL_DOWN" else args.interval)
            except KeyboardInterrupt:
                return 0


if __name__ == "__main__":
    raise SystemExit(main())
