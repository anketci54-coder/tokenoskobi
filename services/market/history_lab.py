"""Geçmiş laboratuvarı: eşikleri (aday yaşı, likidite koruma oranı) zincir geçmişiyle geriye dönük dener.

Veri: havuzların geçmiş `Sync` olayları (zincirden). Sadece LİKİDİTE; fiyat yok.
Evren: eleği geçmiş (KEPT/PULLED) ve penceresi tam okunabilmiş her havuz. Evren sonuca bakılarak SEÇİLMEZ.
Yazdığı tek yer: `hist_fetch` ve `hist_events` tabloları (pairs.sqlite içinde, watcher'a dokunmaz).
Olay bulunamayan/okunamayan havuz evrenden çıkarılır ve raporda sayılır; "çekilmedi" sayılmaz.
"""
from __future__ import annotations

import argparse
import time
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

from services.market.chain_history import HEAD_MARGIN, MAX_AGE_BLOCKS, SPAN_BLOCKS, SYNC_TOPIC
from services.market.pair_watcher import PULL_FRACTION, Store, pick_public_rpc, wilson

AGES_MIN = (30, 60, 120)
KEEPS = (0.8, 0.9, 0.95)
HORIZON_MIN = 360
WINDOW_MIN = max(AGES_MIN) + HORIZON_MIN + 20   # her havuz için doğumdan sonra okunan süre
MAX_ATTEMPTS = 3
MIN_SAMPLE = 30
PAUSE_SEC = 0.25

SCHEMA = """
CREATE TABLE IF NOT EXISTS hist_fetch(
  pair TEXT PRIMARY KEY, status TEXT, events INTEGER, to_block INTEGER, attempts INTEGER DEFAULT 0, error TEXT);
CREATE TABLE IF NOT EXISTS hist_events(pair TEXT, block INTEGER, liq REAL, PRIMARY KEY(pair, block)) WITHOUT ROWID;
"""

Rpc = Callable[[str, list[Any]], Any]


def ensure_tables(store: Store) -> None:
    store.db.executescript(SCHEMA)
    store.db.commit()


def seconds_per_block(rpc: Rpc, head: int, lookback: int = 100000) -> float:
    def stamp(number: int) -> int:
        return int(rpc("eth_getBlockByNumber", [hex(number), False])["timestamp"], 16)
    return (stamp(head) - stamp(head - lookback)) / lookback


def fetch_curve(rpc: Rpc, pair: str, from_block: int, to_block: int, quote_is_token0: bool,
                span: int = SPAN_BLOCKS) -> list[tuple[int, float]]:
    """(blok, teminat rezervi) — blok başına SON olay (durum o bloğun sonundaki). Hata verirse fırlatır."""
    raw: list[tuple[int, int, float]] = []
    start = from_block
    while start <= to_block:
        end = min(to_block, start + span - 1)
        logs = rpc("eth_getLogs", [{"address": pair, "topics": [SYNC_TOPIC],
                                    "fromBlock": hex(start), "toBlock": hex(end)}])
        if not isinstance(logs, list):
            raise RuntimeError("LOGS_UNREADABLE")
        for log in logs:
            data = log["data"]
            if not isinstance(data, str) or len(data) != 2 + 64 * 2:
                raise ValueError("BAD_SYNC_DATA")
            reserve = int(data[2:66], 16) if quote_is_token0 else int(data[66:130], 16)
            raw.append((int(log["blockNumber"], 16), int(log["logIndex"], 16), reserve / 1e18))
        start = end + 1
    last: dict[int, float] = {}
    for block, _, liq in sorted(raw):
        last[block] = liq
    return sorted(last.items())


def fetch(store: Store, rpc: Rpc, limit: int, pause: float = PAUSE_SEC) -> dict[str, int]:
    """Henüz çekilmemiş (veya hatalı ve deneme hakkı olan) havuzların geçmişini çeker. Devam ettirilebilir."""
    ensure_tables(store)
    head = int(rpc("eth_blockNumber", []), 16)
    window = int(WINDOW_MIN * 60 / seconds_per_block(rpc, head))
    rows = store.db.execute(
        "SELECT p.pair, p.block, p.token0, p.quote FROM pairs p LEFT JOIN hist_fetch h ON h.pair = p.pair"
        " WHERE p.status IN ('KEPT','PULLED') AND p.block >= ? AND p.block + ? <= ?"
        " AND (h.pair IS NULL OR (h.status = 'ERROR' AND h.attempts < ?)) ORDER BY p.block DESC LIMIT ?",
        (head - MAX_AGE_BLOCKS, window, head - HEAD_MARGIN, MAX_ATTEMPTS, limit)).fetchall()
    counts = {"OK": 0, "NO_DATA": 0, "ERROR": 0}
    for row in rows:
        to_block = row["block"] + window
        try:
            curve = fetch_curve(rpc, row["pair"], row["block"], to_block, row["token0"] == row["quote"])
            status, error = ("OK", None) if curve else ("NO_DATA", None)
        except Exception as exc:
            curve, status, error = [], "ERROR", f"{type(exc).__name__}:{str(exc)[:100]}"
        with store.db:
            if curve:
                store.db.executemany("INSERT OR REPLACE INTO hist_events(pair, block, liq) VALUES(?,?,?)",
                                     [(row["pair"], b, liq) for b, liq in curve])
            store.db.execute(
                "INSERT INTO hist_fetch(pair, status, events, to_block, attempts, error) VALUES(?,?,?,?,1,?)"
                " ON CONFLICT(pair) DO UPDATE SET status=excluded.status, events=excluded.events,"
                " to_block=excluded.to_block, attempts=hist_fetch.attempts + 1, error=excluded.error",
                (row["pair"], status, len(curve), to_block, error))
        counts[status] += 1
        time.sleep(pause)
    return counts


def simulate(curve: list[tuple[int, float]], birth: int, blocks_per_min: float,
             age_min: int, keep: float, horizon_min: int = HORIZON_MIN) -> dict[str, bool]:
    """Bir havuz için: aday olur muydu, adaysa çekildi mi, ayakta mı kaldı?"""
    age_block = birth + int(age_min * blocks_per_min)
    end_block = age_block + int(horizon_min * blocks_per_min)
    peak = 0.0
    pull_block: int | None = None
    peak_at_age = 0.0
    state_at_age: float | None = None
    for block, liq in curve:
        peak = max(peak, liq)
        if pull_block is None and liq < peak * PULL_FRACTION:
            pull_block = block
        if block <= age_block:
            peak_at_age, state_at_age = peak, liq
    survived = pull_block is None or pull_block > end_block
    candidate = (state_at_age is not None and peak_at_age > 0 and state_at_age >= peak_at_age * keep
                 and (pull_block is None or pull_block > age_block))
    return {"candidate": candidate, "survived": survived,
            "pulled": candidate and not survived}


def report(store: Store, blocks_per_min: float) -> str:
    ensure_tables(store)
    db = store.db
    status = {r["status"]: r["n"] for r in db.execute("SELECT status, COUNT(*) AS n FROM hist_fetch GROUP BY status")}
    lines = ["Geçmiş laboratuvarı (yalnızca likidite; fiyat yok)", "",
             "  çekilen: " + (", ".join(f"{k} {v}" for k, v in sorted(status.items())) or "henüz yok")]
    pairs = db.execute("SELECT p.pair, p.block FROM pairs p JOIN hist_fetch h ON h.pair = p.pair WHERE h.status='OK'").fetchall()
    if not pairs:
        return "\n".join(lines + ["", "  Önce: python3 -m services.market.history_lab --fetch --limit 100"])
    curves: dict[str, list[tuple[int, float]]] = {}
    for row in db.execute("SELECT pair, block, liq FROM hist_events ORDER BY pair, block"):
        curves.setdefault(row["pair"], []).append((row["block"], row["liq"]))
    lines += [f"  evren: {len(pairs)} havuz (sonuca bakılarak seçilmedi; olayı olmayan/okunamayan dışarıda)", "",
              f"Aday olmak için şart ↔ sonuç ({HORIZON_MIN // 60} saat içinde likidite çekilmesi)",
              "  yaş   koruma  aday(%evren)  çekilen%(aralık)             ayakta kalanlardan kaçı aday sayıldı"]
    for age in AGES_MIN:
        results = {keep: [simulate(curves[p["pair"]], p["block"], blocks_per_min, age, keep) for p in pairs]
                   for keep in KEEPS}
        survivors = sum(r["survived"] for r in results[KEEPS[0]])
        lines.append(f"  -- yaş {age} dk: {survivors} / {len(pairs)} havuz {HORIZON_MIN // 60} saat sonunda hâlâ ayakta (çekilmemiş)")
        for keep in KEEPS:
            res = results[keep]
            cands = [r for r in res if r["candidate"]]
            pulled = sum(r["pulled"] for r in cands)
            kept_alive = sum(r["candidate"] and r["survived"] for r in res)
            if cands:
                low, high = wilson(pulled, len(cands))
                share = f"%{100 * pulled / len(cands):.0f} (%{100 * low:.0f}–%{100 * high:.0f})"
            else:
                share = "aday yok"
            note = "  (örnek az)" if len(cands) < MIN_SAMPLE else ""
            recall = f"{kept_alive}/{survivors} (%{100 * kept_alive / survivors:.0f})" if survivors else "-"
            lines.append(f"  {age:>3} dk  %{int(keep * 100):<5}  {len(cands):>4} (%{100 * len(cands) / len(res):.0f})"
                         f"    {share:<26} {recall}{note}")
    lines += ["", "Okuma: 'çekilen%' ne kadar düşükse şart o kadar güvenli; 'ayakta kalanların kaçı aday' ne kadar yüksekse",
              "şart o kadar az fırsat kaçırıyor. İkisi birlikte okunur. Fiyat ölçülmedi; likidite çekilmesi ≠ fiyat çöküşü."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Geçmiş laboratuvarı")
    parser.add_argument("--state-dir", default=str(Path.home() / ".local/state/tokenoskobi/watcher"))
    parser.add_argument("--fetch", action="store_true", help="geçmişi zincirden çek (yalnızca yeni tablolara yazar)")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args(argv)
    from services.market import tokenoskobi_product_slice_02_server as market
    url = pick_public_rpc(market.CFG["rpc"], market.rpc)

    def rpc(method: str, params: list[Any]) -> Any:
        return market.rpc(url, method, params)

    with closing(Store(Path(args.state_dir).expanduser() / "pairs.sqlite")) as store:
        if args.fetch:
            print("çekim sonucu:", fetch(store, rpc, args.limit))
        head = int(rpc("eth_blockNumber", []), 16)
        print(report(store, 60 / seconds_per_block(rpc, head)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
