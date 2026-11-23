"""Measure what happened to analysed pairs, so decision rules can be judged with numbers.

For each fresh analysis it takes a baseline of the pair's reserves, then re-reads them 1, 6 and 24 hours
later. Price change is the change of the quote-per-token reserve ratio; liquidity change is the change of
the quote reserve. Everything is grouped by the decision that was given (ALLOW / REVIEW / WAIT / BLOCK).

Read-only on chain and advisory only. A baseline that cannot be read, or a late measurement, is never
guessed: the row is marked and left out of the statistics.

Run:  python3 -m services.market.outcome_tracker --report
"""
from __future__ import annotations

import argparse
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from statistics import median
from typing import Any, Callable

from services.market.pair_watcher import QUOTES, RESERVES_CALL, Store, _reserves, wilson

HORIZONS_MIN = (60, 360, 1440)
FRESH_SEC = 900.0           # a baseline must be taken within this long after the analysis
MAX_DELAY_SEC = 1800.0      # a measurement later than this after its due time is not used in statistics
RETRY_SEC = 300.0
MAX_ERRORS = 5
PULLED_PCT = -50.0          # liquidity change at or below this counts as pulled
CRASH_PCT = -50.0           # price change at or below this counts as a crash
MIN_SAMPLE = 30

SCHEMA = """
CREATE TABLE IF NOT EXISTS outcomes(
  token TEXT, analyzed_at REAL, decision TEXT, risk INTEGER, pair TEXT, quote TEXT, status TEXT,
  t0_at REAL, t0_quote REAL, t0_ratio REAL, PRIMARY KEY(token, analyzed_at));
CREATE TABLE IF NOT EXISTS outcome_points(
  token TEXT, analyzed_at REAL, horizon INTEGER, due_at REAL, status TEXT, measured_at REAL,
  price_change_pct REAL, liq_change_pct REAL, errors INTEGER DEFAULT 0,
  PRIMARY KEY(token, analyzed_at, horizon));
"""

Rpc = Callable[[str, list[Any]], Any]


def ensure_tables(store: Store) -> None:
    store.db.executescript(SCHEMA)
    store.db.commit()


def read_pair(rpc: Rpc, row: sqlite3.Row) -> tuple[float, float]:
    """(quote_reserve, token_reserve) in raw units. Raises on anything unreadable."""
    reserves = _reserves(rpc("eth_call", [{"to": row["pair"], "data": RESERVES_CALL}, "latest"]))
    if reserves is None:
        raise RuntimeError("RESERVES_UNREADABLE")
    quote_first = row["token0"] == row["quote"]
    return (float(reserves[0]), float(reserves[1])) if quote_first else (float(reserves[1]), float(reserves[0]))


def register(store: Store, rpc: Rpc, now: float) -> int:
    """Give every new analysis a baseline (or a reason why it has none)."""
    db = store.db
    rows = db.execute(
        "SELECT a.token, a.analyzed_at, a.decision, a.risk FROM analyses a WHERE a.status='OK'"
        " AND NOT EXISTS (SELECT 1 FROM outcomes o WHERE o.token=a.token AND o.analyzed_at=a.analyzed_at)").fetchall()
    added = 0
    for item in rows:
        pair = db.execute("SELECT * FROM pairs WHERE target=? ORDER BY seen_at DESC LIMIT 1", (item["token"],)).fetchone()
        base = (item["token"], item["analyzed_at"], item["decision"], item["risk"])
        if pair is None or pair["quote"] not in QUOTES:
            status, t0 = "NO_PAIR", None
        elif now - item["analyzed_at"] > FRESH_SEC:
            status, t0 = "SKIPPED_LATE", None
        else:
            try:
                quote_reserve, token_reserve = read_pair(rpc, pair)
            except Exception:
                continue  # try again next step, until the freshness window closes
            if quote_reserve <= 0 or token_reserve <= 0:
                status, t0 = "NO_BASELINE", None
            else:
                status, t0 = "TRACKING", (now, quote_reserve, quote_reserve / token_reserve)
        with db:
            db.execute("INSERT OR IGNORE INTO outcomes(token, analyzed_at, decision, risk, pair, quote, status,"
                       " t0_at, t0_quote, t0_ratio) VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (*base, pair["pair"] if pair else None, pair["quote"] if pair else None, status,
                        t0[0] if t0 else None, t0[1] if t0 else None, t0[2] if t0 else None))
            if t0:
                for horizon in HORIZONS_MIN:
                    db.execute("INSERT OR IGNORE INTO outcome_points(token, analyzed_at, horizon, due_at, status)"
                               " VALUES(?,?,?,?,'PENDING')", (item["token"], item["analyzed_at"], horizon,
                                                              now + horizon * 60))
        added += 1
    return added


def measure(store: Store, rpc: Rpc, now: float, limit: int = 100) -> dict[str, int]:
    db = store.db
    counts = {"MEASURED": 0, "ERRORS": 0, "FAILED": 0}
    due = db.execute(
        "SELECT p.*, o.pair, o.quote, o.t0_quote, o.t0_ratio, pr.token0 FROM outcome_points p"
        " JOIN outcomes o ON o.token=p.token AND o.analyzed_at=p.analyzed_at"
        " JOIN pairs pr ON pr.pair=o.pair WHERE p.status='PENDING' AND p.due_at <= ? ORDER BY p.due_at LIMIT ?",
        (now, limit)).fetchall()
    for point in due:
        try:
            quote_reserve, token_reserve = read_pair(rpc, point)
        except Exception:
            errors = point["errors"] + 1
            counts["ERRORS"] += 1
            with db:
                if errors >= MAX_ERRORS:
                    db.execute("UPDATE outcome_points SET status='FAILED', errors=? WHERE token=? AND analyzed_at=?"
                               " AND horizon=?", (errors, point["token"], point["analyzed_at"], point["horizon"]))
                    counts["FAILED"] += 1
                else:
                    db.execute("UPDATE outcome_points SET errors=?, due_at=? WHERE token=? AND analyzed_at=?"
                               " AND horizon=?", (errors, now + RETRY_SEC, point["token"], point["analyzed_at"],
                                                  point["horizon"]))
            continue
        liq = (quote_reserve / point["t0_quote"] - 1) * 100
        # With nothing left on one side there is no price; a fully drained pool is a total loss.
        price = (quote_reserve / token_reserve / point["t0_ratio"] - 1) * 100 if token_reserve > 0 and quote_reserve > 0 else -100.0
        with db:
            db.execute("UPDATE outcome_points SET status='MEASURED', measured_at=?, price_change_pct=?,"
                       " liq_change_pct=? WHERE token=? AND analyzed_at=? AND horizon=?",
                       (now, price, liq, point["token"], point["analyzed_at"], point["horizon"]))
        counts["MEASURED"] += 1
    return counts


def step(store: Store, rpc: Rpc, now: float | None = None) -> dict[str, Any]:
    now = time.time() if now is None else now
    ensure_tables(store)
    return {"registered": register(store, rpc, now), **measure(store, rpc, now)}


def report(store: Store) -> str:
    ensure_tables(store)
    db = store.db
    lines = ["Karar sonuçları (baz: analizden hemen sonraki havuz durumu)", ""]
    totals = db.execute("SELECT status, COUNT(*) AS n FROM outcomes GROUP BY status").fetchall()
    lines.append("  kayıtlar: " + (", ".join(f"{r['status']} {r['n']}" for r in totals) or "henüz yok"))
    rows = db.execute(
        "SELECT o.decision, p.horizon, p.price_change_pct AS price, p.liq_change_pct AS liq FROM outcome_points p"
        " JOIN outcomes o ON o.token=p.token AND o.analyzed_at=p.analyzed_at"
        " WHERE p.status='MEASURED' AND p.measured_at - p.due_at <= ?", (MAX_DELAY_SEC,)).fetchall()
    for decision in ("ALLOW", "REVIEW", "WAIT", "BLOCK"):
        lines += ["", f"{decision}:"]
        any_row = False
        for horizon in HORIZONS_MIN:
            sample = [r for r in rows if r["decision"] == decision and r["horizon"] == horizon]
            if not sample:
                continue
            any_row = True
            n = len(sample)
            pulled = sum(1 for r in sample if r["liq"] <= PULLED_PCT)
            crashed = sum(1 for r in sample if r["price"] <= CRASH_PCT)
            low, high = wilson(pulled, n)
            note = "  (örnek az, yorum yapma)" if n < MIN_SAMPLE else ""
            lines.append(f"  {horizon // 60:>2} sa: {n} örnek · likidite çekilen %{100 * pulled / n:.0f} "
                         f"(aralık %{100 * low:.0f}–%{100 * high:.0f}) · fiyat ≥%50 düşen {crashed}/{n} · "
                         f"ortanca fiyat değişimi %{median(r['price'] for r in sample):.0f}{note}")
        if not any_row:
            lines.append("  henüz ölçüm yok")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Karar sonuçlarını raporlar (salt okunur)")
    parser.add_argument("--state-dir", default=str(Path.home() / ".local/state/tokenoskobi/watcher"))
    args = parser.parse_args(argv)
    with closing(Store(Path(args.state_dir).expanduser() / "pairs.sqlite")) as store:
        print(report(store))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
