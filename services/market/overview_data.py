"""Genel bakış verisi (salt okunur): panelin /api/v1/overview ucu için.

Yalnızca mevcut SQLite dosyalarını salt okunur açar; hiçbir şey yazmaz, hiçbir şeyi başlatmaz/durdurmaz.
Her blok bağımsızdır: bir tablo yoksa o blok `None` olur ve sayfa "veri yok" der, tahmin edilmez.
"Taze/eski" yalnızca son etkinlik zamanına bakar; servisin çalıştığının KANITI değil, işaretidir.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from services.market.backtest_report import HORIZONS_MIN as BT_HORIZONS, MIN_SAMPLE, outcome_at
from services.market.outcome_tracker import CRASH_PCT, HORIZONS_MIN as OT_HORIZONS, MAX_DELAY_SEC, PULLED_PCT
from services.market.pair_watcher import survival_table, wilson

# (anahtar, ad, tablo, sütun, taze sayılma süresi sn)
ACTIVITY = (
    ("watcher", "Göz · yeni çift gördü", "pairs", "seen_at", 900),
    ("series", "Likidite kaydı", "liq_series", "t", 900),
    ("analyzer", "Beyin · son analiz", "analyses", "analyzed_at", 6 * 3600),
    ("outcomes", "Hafıza · son ölçüm", "outcome_points", "measured_at", 6 * 3600),
)
NEWS_FRESH_SEC = 1800
DECISIONS = ("ALLOW", "REVIEW", "WAIT", "BLOCK")


def _open(path: Path) -> sqlite3.Connection | None:
    if not path.exists():
        return None
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
    db.row_factory = sqlite3.Row
    return db


def _has(db: sqlite3.Connection, table: str) -> bool:
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _state(age: float | None, fresh: float) -> str:
    return "yok" if age is None else ("taze" if age <= fresh else "eski")


def _activity(db: sqlite3.Connection, news: sqlite3.Connection | None, now: float) -> list[dict[str, Any]]:
    items = []
    for key, label, table, column, fresh in ACTIVITY:
        last = db.execute(f"SELECT MAX({column}) FROM {table}").fetchone()[0] if _has(db, table) else None
        age = None if last is None else max(0.0, now - last)
        items.append({"key": key, "label": label, "age_sec": age, "fresh_sec": fresh, "state": _state(age, fresh)})
    last = None
    if news is not None and _has(news, "news_collector_runs"):
        last = news.execute("SELECT MAX(run_at) FROM news_collector_runs").fetchone()[0]
    age = None if last is None else max(0.0, now - last)
    items.append({"key": "news", "label": "Kulak · haber turu", "age_sec": age, "fresh_sec": NEWS_FRESH_SEC,
                  "state": _state(age, NEWS_FRESH_SEC)})
    return items


def _rate(events: int, n: int) -> dict[str, Any]:
    low, high = wilson(events, n) if n else (None, None)
    return {"n": n, "events": events, "low": low, "high": high, "enough": n >= MIN_SAMPLE}


def _outcomes(db: sqlite3.Connection) -> list[dict[str, Any]] | None:
    if not (_has(db, "outcomes") and _has(db, "outcome_points")):
        return None
    rows = db.execute(
        "SELECT o.decision, p.horizon, p.price_change_pct AS price, p.liq_change_pct AS liq FROM outcome_points p"
        " JOIN outcomes o ON o.token=p.token AND o.analyzed_at=p.analyzed_at"
        " WHERE p.status='MEASURED' AND p.measured_at - p.due_at <= ?", (MAX_DELAY_SEC,)).fetchall()
    out = []
    for decision in DECISIONS:
        for horizon in OT_HORIZONS:
            sample = [r for r in rows if r["decision"] == decision and r["horizon"] == horizon]
            out.append({"decision": decision, "horizon": horizon,
                        "pulled": _rate(sum(1 for r in sample if r["liq"] <= PULLED_PCT), len(sample)),
                        "crashed": sum(1 for r in sample if r["price"] <= CRASH_PCT)})
    return out


def _backtest(db: sqlite3.Connection, now: float) -> list[dict[str, Any]] | None:
    if not (_has(db, "analyses") and _has(db, "pairs")):
        return None
    rows = db.execute(
        "SELECT a.decision, a.analyzed_at, p.status, p.decided_at, p.watch_until FROM analyses a"
        " JOIN pairs p ON p.target = a.token AND p.status IN ('KEPT','PULLED') WHERE a.status='OK'").fetchall()
    out = []
    for decision in DECISIONS:
        for horizon in BT_HORIZONS:
            known = [o for o in (outcome_at(r, horizon, now) for r in rows if r["decision"] == decision)
                     if o is not None]
            out.append({"decision": decision, "horizon": horizon, "pulled": _rate(sum(known), len(known))})
    return out


def snapshot(state_dir: Path, news_path: Path | None = None, now: float | None = None) -> dict[str, Any]:
    now = time.time() if now is None else now
    db = _open(state_dir / "pairs.sqlite")
    if db is None:
        return {"available": False, "generated_at": now}
    news = _open(news_path) if news_path else None
    try:
        decisions = {d: 0 for d in DECISIONS}
        recent: list[dict[str, Any]] = []
        if _has(db, "analyses"):
            for row in db.execute("SELECT decision, COUNT(*) AS n FROM analyses WHERE status='OK' GROUP BY decision"):
                if row["decision"] in decisions:
                    decisions[row["decision"]] = row["n"]
            for row in db.execute("SELECT token, decision, risk, warnings, analyzed_at FROM analyses"
                                  " WHERE status='OK' ORDER BY analyzed_at DESC LIMIT 10"):
                try:
                    warnings = [str(w) for w in json.loads(row["warnings"] or "[]")][:6]
                except ValueError:
                    warnings = []
                recent.append({"token": row["token"], "decision": row["decision"], "risk": row["risk"],
                               "warnings": warnings, "analyzed_at": row["analyzed_at"]})
        survival = None
        if _has(db, "pairs"):
            survival = [{"horizon": r["horizon"], **_rate(r["pulled"], r["n"])}
                        for r in survival_table(SimpleNamespace(db=db), now)]
        return {"available": True, "generated_at": now, "activity": _activity(db, news, now),
                "decisions": decisions, "survival": survival, "outcomes": _outcomes(db),
                "backtest": _backtest(db, now), "recent": recent, "min_sample": MIN_SAMPLE}
    finally:
        db.close()
        if news is not None:
            news.close()
