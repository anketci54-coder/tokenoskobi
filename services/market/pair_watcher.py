"""New-pair watcher for the Pancake V2 factory: discovery, cheap triage, reasoned drops.

Read-only on chain (eth_blockNumber / eth_getLogs / eth_getCode / eth_call /
eth_getStorageAt). It writes only its own SQLite file and never trades, signs or
touches the analysis ledger. Every drop carries a reason code; anything it cannot
check is retried and finally dropped as CHECK_FAILED, never treated as safe.

Run:  python3 -m services.market.pair_watcher --state-dir DIR [--once | --report]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from services.market.dex_policy import DEPLOYMENTS
from services.market.swap_behavior import RESERVES_CALL
from services.market.token_controls import OWNER_SELECTORS, collect_controls, keccak256

FACTORY_V2 = DEPLOYMENTS["v2"][0]
PAIR_CREATED_TOPIC = "0x" + keccak256(b"PairCreated(address,address,address,uint256)").hex()
WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
USDT = "0x55d398326f99059ff775485246999027b3197955"
QUOTES = {WBNB: "WBNB", USDT: "USDT"}
# Both quote tokens use 18 decimals on BSC, so reserves are divided by 1e18.
MIN_LIQUIDITY = {WBNB: 5.0, USDT: 3000.0}
LOOKBACK_BLOCKS = 200
MAX_SPAN = 2000
CHECK_DELAY_SEC = 300.0
RETRY_SEC = 300.0
ERROR_RETRY_SEC = 60.0
MAX_LIQUIDITY_ATTEMPTS = 3
MAX_ERRORS = 5
CHECKS_PER_LOOP = 50
RETAIN_DROPPED_DAYS = 7
PRUNE_EVERY_SEC = 3600.0
WATCH_INTERVAL_SEC = 300.0
WATCH_HOURS = 24
PULL_FRACTION = 0.5  # liquidity below half of its peak = pulled
WATCHES_PER_LOOP = 100
HORIZONS_MIN = (10, 30, 60, 180)
CANDIDATE_MIN_AGE_MIN = 60  # tunable guess; pick from the survival table, not from this number
CANDIDATE_KEEP_FRACTION = 0.9

SCHEMA = """
CREATE TABLE IF NOT EXISTS pairs(
  pair TEXT PRIMARY KEY, target TEXT, quote TEXT, token0 TEXT, token1 TEXT,
  block INTEGER, seen_at REAL, status TEXT, reason TEXT, detail TEXT,
  attempts INTEGER DEFAULT 0, errors INTEGER DEFAULT 0, due_at REAL,
  decided_at REAL, controls TEXT,
  peak REAL, last_liq REAL, watch_due REAL, watch_until REAL,
  kept_at REAL, backfilled REAL);
CREATE INDEX IF NOT EXISTS pairs_due ON pairs(status, due_at);
CREATE TABLE IF NOT EXISTS cursor(id INTEGER PRIMARY KEY CHECK(id = 1), block INTEGER);
CREATE TABLE IF NOT EXISTS drop_stats(day TEXT, reason TEXT, count INTEGER,
  PRIMARY KEY(day, reason));
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value REAL);
"""


def _addr(word: str) -> str:
    return "0x" + word[-40:].lower()


def parse_pair_created(log: Any) -> dict[str, Any] | None:
    try:
        topics, data = log["topics"], log["data"]
        if len(topics) != 3 or topics[0].lower() != PAIR_CREATED_TOPIC:
            return None
        if not isinstance(data, str) or len(data) < 2 + 64:
            return None
        return {"token0": _addr(topics[1]), "token1": _addr(topics[2]),
                "pair": _addr(data[2:66]), "block": int(log["blockNumber"], 16)}
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def classify_new_pair(token0: str, token1: str) -> tuple[str | None, str | None, str | None]:
    """(target, quote, drop_reason). No network: the cheapest possible filter."""
    q0, q1 = token0 in QUOTES, token1 in QUOTES
    if q0 and q1:
        return None, None, "BOTH_QUOTE_TOKENS"
    if not q0 and not q1:
        return None, None, "NO_ALLOWED_QUOTE"
    return (token1, token0, None) if q0 else (token0, token1, None)


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)
        have = {r["name"] for r in self.db.execute("PRAGMA table_info(pairs)")}
        for col in ("peak", "last_liq", "watch_due", "watch_until", "kept_at", "backfilled"):
            if col not in have:
                self.db.execute(f"ALTER TABLE pairs ADD COLUMN {col} REAL")
        self.db.commit()
        self.backfill_watch(time.time())

    def backfill_watch(self, now: float) -> int:
        """Put KEPT pairs that predate the watch columns under watch.

        Their first liquidity (written in `detail` when they were kept) becomes the peak. Rows whose
        window already ended get one last check and then stop.
        """
        with self.db:
            return self.db.execute(
                "UPDATE pairs SET peak = CAST(substr(detail, 1, instr(detail, ' ') - 1) AS REAL),"
                " last_liq = CAST(substr(detail, 1, instr(detail, ' ') - 1) AS REAL),"
                " watch_due = ?, watch_until = decided_at + ?, kept_at = decided_at, backfilled = 1"
                " WHERE status = 'KEPT' AND watch_due IS NULL AND watch_until IS NULL"
                " AND peak IS NULL AND instr(detail, ' ') > 1",
                (now, WATCH_HOURS * 3600)).rowcount

    def close(self) -> None:
        self.db.close()

    def cursor(self) -> int | None:
        row = self.db.execute("SELECT block FROM cursor WHERE id = 1").fetchone()
        return row["block"] if row else None

    def add(self, row: dict[str, Any], to_block: int) -> None:
        """Insert a batch of discovered pairs and advance the cursor atomically."""
        with self.db:
            for item in row["items"]:
                self.db.execute(
                    "INSERT OR IGNORE INTO pairs(pair, target, quote, token0, token1, block, seen_at,"
                    " status, reason, detail, due_at, decided_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (item["pair"], item["target"], item["quote"], item["token0"], item["token1"],
                     item["block"], row["now"], item["status"], item["reason"], item["detail"],
                     item["due_at"], row["now"] if item["status"] == "DROPPED" else None))
            self.db.execute("INSERT INTO cursor(id, block) VALUES(1, ?) "
                            "ON CONFLICT(id) DO UPDATE SET block = excluded.block", (to_block,))

    def due(self, now: float, limit: int) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM pairs WHERE status = 'NEW' AND due_at <= ? ORDER BY due_at LIMIT ?",
            (now, limit)).fetchall()

    def decide(self, pair: str, status: str, reason: str, detail: str, now: float,
               controls: dict[str, Any] | None = None, liquidity: float | None = None) -> None:
        watch = status == "KEPT" and liquidity is not None
        with self.db:
            self.db.execute(
                "UPDATE pairs SET status=?, reason=?, detail=?, decided_at=?, controls=?, due_at=NULL,"
                " peak=?, last_liq=?, watch_due=?, watch_until=?, kept_at=? WHERE pair=?",
                (status, reason, detail, now, json.dumps(controls) if controls else None,
                 liquidity if watch else None, liquidity if watch else None,
                 now + WATCH_INTERVAL_SEC if watch else None,
                 now + WATCH_HOURS * 3600 if watch else None, now if watch else None, pair))

    def watch_rows(self, now: float, limit: int) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM pairs WHERE status='KEPT' AND watch_due IS NOT NULL AND watch_due <= ?"
            " ORDER BY watch_due LIMIT ?", (now, limit)).fetchall()

    def watch_update(self, pair: str, *, peak: float, liq: float, due: float | None) -> None:
        with self.db:
            self.db.execute("UPDATE pairs SET peak=?, last_liq=?, watch_due=? WHERE pair=?",
                            (peak, liq, due, pair))

    def watch_delay(self, pair: str, due: float) -> None:
        with self.db:
            self.db.execute("UPDATE pairs SET watch_due=? WHERE pair=?", (due, pair))

    def mark_pulled(self, pair: str, detail: str, now: float, peak: float, liq: float) -> None:
        with self.db:
            self.db.execute(
                "UPDATE pairs SET status='PULLED', reason='LIQUIDITY_PULLED', detail=?, decided_at=?,"
                " peak=?, last_liq=?, watch_due=NULL WHERE pair=?", (detail, now, peak, liq, pair))

    def reschedule(self, pair: str, due_at: float, *, attempts: int, errors: int) -> None:
        with self.db:
            self.db.execute("UPDATE pairs SET due_at=?, attempts=?, errors=? WHERE pair=?",
                            (due_at, attempts, errors, pair))

    def prune(self, now: float, retain_days: int = RETAIN_DROPPED_DAYS) -> int:
        """Fold old dropped rows into daily counts, then delete them."""
        cutoff = now - retain_days * 86400
        rows = self.db.execute(
            "SELECT reason, strftime('%Y-%m-%d', decided_at, 'unixepoch') AS day, COUNT(*) AS n"
            " FROM pairs WHERE status='DROPPED' AND decided_at < ? GROUP BY reason, day",
            (cutoff,)).fetchall()
        with self.db:
            for row in rows:
                self.db.execute(
                    "INSERT INTO drop_stats(day, reason, count) VALUES(?,?,?) "
                    "ON CONFLICT(day, reason) DO UPDATE SET count = count + excluded.count",
                    (row["day"], row["reason"], row["n"]))
            deleted = self.db.execute(
                "DELETE FROM pairs WHERE status='DROPPED' AND decided_at < ?", (cutoff,)).rowcount
        return deleted

    def meta(self, key: str) -> float | None:
        row = self.db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_meta(self, key: str, value: float) -> None:
        with self.db:
            self.db.execute("INSERT INTO meta(key, value) VALUES(?,?) "
                            "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))


Rpc = Callable[[str, list[Any]], Any]


def scan(store: Store, rpc: Rpc, now: float) -> int:
    """Read new PairCreated logs after the cursor. Returns how many pairs were recorded."""
    latest = int(rpc("eth_blockNumber", []), 16)
    cursor = store.cursor()
    if cursor is None:
        cursor = max(0, latest - LOOKBACK_BLOCKS)
    if cursor >= latest:
        return 0
    start, end = cursor + 1, min(latest, cursor + MAX_SPAN)
    logs = rpc("eth_getLogs", [{"address": FACTORY_V2, "topics": [PAIR_CREATED_TOPIC],
                                "fromBlock": hex(start), "toBlock": hex(end)}])
    if not isinstance(logs, list):
        raise RuntimeError("GETLOGS_BAD_RESULT")
    items = []
    for log in logs:
        parsed = parse_pair_created(log)
        if not parsed:
            continue
        target, quote, reason = classify_new_pair(parsed["token0"], parsed["token1"])
        items.append({**parsed, "target": target, "quote": quote,
                      "status": "DROPPED" if reason else "NEW", "reason": reason,
                      "detail": None, "due_at": None if reason else now + CHECK_DELAY_SEC})
    store.add({"items": items, "now": now}, end)
    return len(items)


def _reserves(raw: Any) -> tuple[int, int] | None:
    if not isinstance(raw, str) or len(raw) != 2 + 64 * 3:
        return None
    return int(raw[2:66], 16), int(raw[66:130], 16)


def check_pair(row: sqlite3.Row, rpc: Rpc) -> tuple[str, str, str, dict[str, Any] | None, float | None]:
    """(outcome, reason, detail, controls, liquidity). outcome: DROP | KEEP | WAIT. May raise."""
    target, pair, quote = row["target"], row["pair"], row["quote"]
    code = rpc("eth_getCode", [target, "latest"])
    if not isinstance(code, str):
        raise RuntimeError("GETCODE_BAD_RESULT")
    if code in ("0x", "0x0", ""):
        return "DROP", "NO_CODE", "no contract code at target", None, None
    reserves = _reserves(rpc("eth_call", [{"to": pair, "data": RESERVES_CALL}, "latest"]))
    if reserves is None:
        raise RuntimeError("RESERVES_UNREADABLE")
    quote_reserve = reserves[0] if row["token0"] == quote else reserves[1]
    liquidity = quote_reserve / 1e18
    symbol = QUOTES[quote]
    if liquidity <= 0:
        return "WAIT", "NO_LIQUIDITY_YET", f"0 {symbol}", None, None
    if liquidity < MIN_LIQUIDITY[quote]:
        return "DROP", "LIQUIDITY_TOO_LOW", f"{liquidity:.4f} {symbol} < {MIN_LIQUIDITY[quote]:g}", None, liquidity

    def call(data: str) -> Any:
        return rpc("eth_call", [{"to": target, "data": data}, "latest"])

    try:
        owner_raw = call(OWNER_SELECTORS["owner()"])
    except Exception:
        owner_raw = None
    controls = collect_controls(
        code, owner_raw, call,
        lambda address: rpc("eth_getCode", [address, "latest"]),
        lambda slot: rpc("eth_getStorageAt", [target, slot, "latest"]))
    if (controls["owner"]["status"] == "OWNER_ACTIVE_EOA"
            and "MINT_SELECTOR_PRESENT" in controls["selector_hints"]):
        return "DROP", "MINT_UNDER_SINGLE_KEY", f"{liquidity:.4f} {symbol}", controls, liquidity
    return "KEEP", "LIQUIDITY_OK", f"{liquidity:.4f} {symbol}", controls, liquidity


def check_due(store: Store, rpc: Rpc, now: float, limit: int = CHECKS_PER_LOOP) -> dict[str, int]:
    counts = {"KEPT": 0, "DROPPED": 0, "WAITING": 0, "ERRORS": 0}
    for row in store.due(now, limit):
        try:
            outcome, reason, detail, controls, liquidity = check_pair(row, rpc)
        except Exception as exc:
            errors = row["errors"] + 1
            counts["ERRORS"] += 1
            if errors >= MAX_ERRORS:
                store.decide(row["pair"], "DROPPED", "CHECK_FAILED",
                             f"{type(exc).__name__}:{str(exc)[:80]}", now)
                counts["DROPPED"] += 1
            else:
                store.reschedule(row["pair"], now + ERROR_RETRY_SEC,
                                 attempts=row["attempts"], errors=errors)
            continue
        if outcome == "WAIT":
            attempts = row["attempts"] + 1
            if attempts >= MAX_LIQUIDITY_ATTEMPTS:
                store.decide(row["pair"], "DROPPED", "NO_LIQUIDITY_ADDED", detail, now)
                counts["DROPPED"] += 1
            else:
                store.reschedule(row["pair"], now + RETRY_SEC, attempts=attempts, errors=row["errors"])
                counts["WAITING"] += 1
        elif outcome == "DROP":
            store.decide(row["pair"], "DROPPED", reason, detail, now, controls)
            counts["DROPPED"] += 1
        else:
            store.decide(row["pair"], "KEPT", reason, detail, now, controls, liquidity)
            counts["KEPT"] += 1
    return counts


def check_watch(store: Store, rpc: Rpc, now: float, limit: int = WATCHES_PER_LOOP) -> dict[str, int]:
    """Re-read liquidity of KEPT pairs; a drop below half of the peak marks the pair PULLED."""
    counts = {"WATCHED": 0, "PULLED": 0, "WATCH_ERRORS": 0}
    for row in store.watch_rows(now, limit):
        try:
            reserves = _reserves(rpc("eth_call", [{"to": row["pair"], "data": RESERVES_CALL}, "latest"]))
            if reserves is None:
                raise RuntimeError("RESERVES_UNREADABLE")
        except Exception:
            # Unreadable is not "fine" and not "pulled": try again soon, never change the status.
            counts["WATCH_ERRORS"] += 1
            store.watch_delay(row["pair"], now + ERROR_RETRY_SEC)
            continue
        quote_reserve = reserves[0] if row["token0"] == row["quote"] else reserves[1]
        liq = quote_reserve / 1e18
        peak = max(row["peak"] or 0.0, liq)
        symbol = QUOTES[row["quote"]]
        if peak > 0 and liq < peak * PULL_FRACTION:
            store.mark_pulled(row["pair"], f"{peak:.4f} -> {liq:.4f} {symbol}", now, peak, liq)
            counts["PULLED"] += 1
            continue
        ended = row["watch_until"] is not None and now >= row["watch_until"]
        store.watch_update(row["pair"], peak=peak, liq=liq, due=None if ended else now + WATCH_INTERVAL_SEC)
        counts["WATCHED"] += 1
    return counts


def run_once(store: Store, rpc: Rpc, now: float | None = None) -> dict[str, Any]:
    now = time.time() if now is None else now
    found = scan(store, rpc, now)
    checked = check_due(store, rpc, now)
    checked.update(check_watch(store, rpc, now))
    pruned = 0
    last = store.meta("last_prune")
    if last is None or now - last >= PRUNE_EVERY_SEC:
        pruned = store.prune(now)
        store.set_meta("last_prune", now)
    return {"found": found, **checked, "pruned": pruned}


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion (n > 0)."""
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def survival_table(store: Store, now: float) -> list[dict[str, Any]]:
    """P(liquidity pulled within H minutes of being kept), live-watched pairs only.

    The cohort for horizon H is every pair that has been watched for at least H minutes (kept at
    least H minutes ago, or watched to the end of its window). Counting only pairs whose outcome is
    already known would over-count pulls, because pulls become known sooner than survivals.
    Detection time is the first 5-minute check that saw the pull, so times are upper bounds.
    """
    rows = store.db.execute(
        "SELECT status, kept_at, decided_at, watch_until FROM pairs WHERE kept_at IS NOT NULL"
        " AND backfilled IS NULL AND status IN ('KEPT', 'PULLED')").fetchall()
    table = []
    for horizon in HORIZONS_MIN:
        cohort = events = 0
        for row in rows:
            end = now
            if row["status"] == "KEPT" and row["watch_until"] is not None:
                end = min(now, row["watch_until"])
            if (end - row["kept_at"]) / 60.0 < horizon:
                continue  # not watched for the full horizon yet
            cohort += 1
            if row["status"] == "PULLED" and (row["decided_at"] - row["kept_at"]) / 60.0 <= horizon:
                events += 1
        table.append({"horizon": horizon, "n": cohort, "pulled": events,
                      "ci": wilson(events, cohort) if cohort else None})
    return table


def candidate_rows(store: Store, now: float, min_age_min: float = CANDIDATE_MIN_AGE_MIN,
                   keep_fraction: float = CANDIDATE_KEEP_FRACTION) -> list[sqlite3.Row]:
    """KEPT pairs that lived long enough and still hold most of their peak liquidity, oldest first."""
    return store.db.execute(
        "SELECT target, quote, detail, last_liq, peak, COALESCE(kept_at, decided_at) AS since FROM pairs"
        " WHERE status='KEPT' AND peak > 0 AND last_liq >= peak * ? AND ? - COALESCE(kept_at, decided_at) >= ?"
        " ORDER BY since", (keep_fraction, now, min_age_min * 60)).fetchall()


def report(store: Store, now: float | None = None, min_age_min: float = CANDIDATE_MIN_AGE_MIN,
           keep_fraction: float = CANDIDATE_KEEP_FRACTION) -> str:
    db = store.db
    now = time.time() if now is None else now
    lines = ["Havuz yakalayıcı raporu", ""]
    for row in db.execute("SELECT status, COUNT(*) AS n FROM pairs GROUP BY status ORDER BY status"):
        lines.append(f"  {row['status']}: {row['n']}")
    lines += ["", "Elenme nedenleri (kayıtlı + özetlenmiş):"]
    totals: dict[str, int] = {}
    for row in db.execute("SELECT reason, COUNT(*) AS n FROM pairs WHERE status='DROPPED' GROUP BY reason"):
        totals[row["reason"]] = totals.get(row["reason"], 0) + row["n"]
    for row in db.execute("SELECT reason, SUM(count) AS n FROM drop_stats GROUP BY reason"):
        totals[row["reason"]] = totals.get(row["reason"], 0) + row["n"]
    lines += [f"  {reason}: {count}" for reason, count in sorted(totals.items(), key=lambda i: -i[1])] or ["  yok"]
    kept_n = db.execute("SELECT COUNT(*) FROM pairs WHERE status='KEPT'").fetchone()[0]
    pulled_n = db.execute("SELECT COUNT(*) FROM pairs WHERE status='PULLED'").fetchone()[0]
    lines += ["", "Eleği geçenlerin akıbeti:"]
    if kept_n + pulled_n:
        share = 100.0 * pulled_n / (kept_n + pulled_n)
        lines.append(f"  eleği geçen: {kept_n + pulled_n} · likiditesi çekilen: {pulled_n} (%{share:.1f}) · hâlâ ayakta: {kept_n}")
        gaps = sorted((r["g"] for r in db.execute(
            "SELECT (decided_at - kept_at) / 60.0 AS g FROM pairs WHERE status='PULLED'"
            " AND kept_at IS NOT NULL AND backfilled IS NULL")))
        if gaps:
            lines.append(f"  çekilme süresi (dk, canlı izlenenler): en kısa {gaps[0]:.0f} · ortanca "
                         f"{gaps[len(gaps) // 2]:.0f} · en uzun {gaps[-1]:.0f} ({len(gaps)} kayıt)")
        old = db.execute("SELECT COUNT(*) FROM pairs WHERE status='PULLED' AND backfilled = 1").fetchone()[0]
        if old:
            lines.append(f"  not: {old} kaydın çekilme zamanı bilinmiyor (izleme sonradan başladı); süreye katılmadı")
    else:
        lines.append("  yok")
    lines += ["", "Çekilme olasılığı (canlı izlenenler; %95 güven aralığı; örnek azsa geniş çıkar):"]
    for row in survival_table(store, now):
        if row["n"] == 0:
            lines.append(f"  {row['horizon']} dk içinde: henüz örnek yok")
        else:
            low, high = row["ci"]
            lines.append(f"  {row['horizon']} dk içinde: %{100 * row['pulled'] / row['n']:.1f} "
                         f"(aralık %{100 * low:.1f}–%{100 * high:.1f}; {row['pulled']}/{row['n']} örnek)")
    lines += ["", f"Adaylar (≥{min_age_min:g} dk ayakta ve likidite ≥ zirvenin %{100 * keep_fraction:.0f}'i):"]
    candidates = candidate_rows(store, now, min_age_min, keep_fraction)
    lines.append(f"  toplam {len(candidates)} aday")
    for row in candidates[:10]:
        lines.append(f"  {row['target']}  {(now - row['since']) / 60:.0f} dk  "
                     f"{row['last_liq']:.2f}/{row['peak']:.2f} {QUOTES.get(row['quote'], '?')} (şimdiki/zirve)")
    lines += ["", "Likiditesi çekilenler (PULLED):"]
    pulled = db.execute("SELECT target, detail, decided_at FROM pairs WHERE status='PULLED' "
                        "ORDER BY decided_at DESC LIMIT 10").fetchall()
    for row in pulled:
        when = datetime.fromtimestamp(row["decided_at"], timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"  {row['target']}  {row['detail']}  ({when} UTC)")
    lines += ["  yok"] if not pulled else []
    lines += ["", "Son kalanlar (KEPT):"]
    kept = db.execute("SELECT target, quote, detail, decided_at FROM pairs WHERE status='KEPT' "
                      "ORDER BY decided_at DESC LIMIT 10").fetchall()
    for row in kept:
        when = datetime.fromtimestamp(row["decided_at"], timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"  {row['target']}  {row['detail']}  ({when} UTC)")
    return "\n".join(lines + (["  yok"] if not kept else []))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pancake V2 yeni havuz yakalayıcı (salt okunur)")
    parser.add_argument("--state-dir", default=str(Path.home() / ".local/state/tokenoskobi/watcher"))
    parser.add_argument("--interval", type=float, default=15.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--min-age", type=float, default=CANDIDATE_MIN_AGE_MIN,
                        help="aday için en az dakika (yalnızca rapor)")
    parser.add_argument("--keep-fraction", type=float, default=CANDIDATE_KEEP_FRACTION,
                        help="aday için zirveye göre en az likidite oranı (yalnızca rapor)")
    args = parser.parse_args(argv)
    store = Store(Path(args.state_dir).expanduser() / "pairs.sqlite")
    with closing(store):
        if args.report:
            print(report(store, min_age_min=args.min_age, keep_fraction=args.keep_fraction))
            return 0
        from services.market import tokenoskobi_product_slice_02_server as market

        url: str | None = None
        while True:
            try:
                if url is None:
                    selected = market.providers().get("selected")
                    if not selected:
                        raise RuntimeError("NO_RPC")
                    url = selected["url"]
                summary = run_once(store, lambda method, params: market.rpc(url, method, params))
                print(datetime.now(timezone.utc).strftime("%H:%M:%S"), json.dumps(summary), flush=True)
            except KeyboardInterrupt:
                return 0
            except Exception as exc:
                url = None  # pick a working RPC again next round
                print(f"HATA {type(exc).__name__}: {str(exc)[:120]}", file=sys.stderr, flush=True)
            if args.once:
                return 0
            try:
                time.sleep(args.interval)
            except KeyboardInterrupt:
                return 0


if __name__ == "__main__":
    raise SystemExit(main())
