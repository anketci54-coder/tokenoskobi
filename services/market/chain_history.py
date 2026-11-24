"""Zincir geçmişi doğrulaması (salt okunur).

Soru: havuzun geçmiş `Sync` olaylarından geri kurduğumuz likidite, watcher'ın kendi kaydettiğiyle tutuyor mu?
Tutmuyorsa geçmişten test yapmak yanıltır. Hiçbir şey yazmaz, durum değiştirmez.
Olay bulunamayan havuz "çekilmedi" sayılmaz: "veri yok" denir (sunucu eski kayıtları tutmayabilir).
"""
from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

from services.market.pair_watcher import Store, pick_public_rpc

SYNC_TOPIC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
SPAN_BLOCKS = 5000            # bir istekte istenen blok aralığı (publicnode'da çalıştığı görüldü)
WINDOW_BLOCKS = 20000         # doğum bloğundan sonra bakılan pencere
MAX_AGE_BLOCKS = 250000       # bundan eski havuza bakılmaz (sunucu geçmişi sınırlı; 300 bin çalıştı, 800 bin çalışmadı)
HEAD_MARGIN = 50              # kamu RPC birden çok sunucuya dağılır; biri birkaç blok geride olabilir
TOLERANCE = 0.95              # zincir zirvesi, watcher'ın kaydettiği zirvenin bunun altına düşerse "tutmuyor"

Rpc = Callable[[str, list[Any]], Any]


def parse_sync(log: dict[str, Any]) -> tuple[int, int, int]:
    """(block, reserve0, reserve1)."""
    data = log["data"]
    if not isinstance(data, str) or len(data) != 2 + 64 * 2:
        raise ValueError("BAD_SYNC_DATA")
    return int(log["blockNumber"], 16), int(data[2:66], 16), int(data[66:130], 16)


def fetch_sync(rpc: Rpc, pair: str, from_block: int, to_block: int, span: int = SPAN_BLOCKS) -> list[tuple[int, int, int]]:
    events: list[tuple[int, int, int]] = []
    start = from_block
    while start <= to_block:
        end = min(to_block, start + span - 1)
        logs = rpc("eth_getLogs", [{"address": pair, "topics": [SYNC_TOPIC],
                                    "fromBlock": hex(start), "toBlock": hex(end)}])
        if not isinstance(logs, list):
            raise RuntimeError("LOGS_UNREADABLE")
        events += [parse_sync(entry) for entry in logs]
        start = end + 1
    return sorted(events)


def curve(events: list[tuple[int, int, int]], quote_is_token0: bool) -> list[tuple[int, float]]:
    """(blok, teminat tarafı rezerv, ondalıklı) — watcher'ın liq değeriyle aynı birim (1e18'e bölünmüş)."""
    return [(block, (r0 if quote_is_token0 else r1) / 1e18) for block, r0, r1 in events]


def check(store: Store, rpc: Rpc, limit: int = 10) -> str:
    head = int(rpc("eth_blockNumber", []), 16)
    rows = store.db.execute(
        "SELECT pair, block, token0, quote, peak FROM pairs WHERE status IN ('KEPT','PULLED')"
        " AND peak > 0 AND block >= ? ORDER BY block DESC LIMIT ?", (head - MAX_AGE_BLOCKS, limit)).fetchall()
    lines = ["Zincir geçmişi doğrulaması (salt okunur)", "",
             f"  bakılan havuz: {len(rows)} (yaşı ≤ {MAX_AGE_BLOCKS} blok)"]
    matched = mismatched = nodata = unreadable = 0
    for row in rows:
        short = row["pair"][:8] + "…" + row["pair"][-4:]
        try:
            events = fetch_sync(rpc, row["pair"], row["block"], min(head - HEAD_MARGIN, row["block"] + WINDOW_BLOCKS))
        except Exception as exc:
            unreadable += 1
            lines.append(f"  {short}: okunamadı ({str(exc)[:60]})")
            continue
        if not events:
            nodata += 1
            lines.append(f"  {short}: veri yok (olay bulunamadı; 'çekilmedi' DEĞİL)")
            continue
        chain_peak = max(liq for _, liq in curve(events, row["token0"] == row["quote"]))
        ok = chain_peak >= row["peak"] * TOLERANCE
        matched += ok
        mismatched += not ok
        lines.append(f"  {short}: {len(events)} olay · zincir zirvesi {chain_peak:.2f} · watcher zirvesi {row['peak']:.2f}"
                     f" · {'TUTUYOR' if ok else 'TUTMUYOR'}")
    lines += ["", f"Özet: tutan {matched} · tutmayan {mismatched} · veri yok {nodata} · okunamadı {unreadable}",
              "Not: zincir zirvesi, 5 dakikalık örnekleme arasındaki tepeleri de görür; watcher zirvesinden DÜŞÜK olmamalı."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Zincir geçmişi doğrulaması (salt okunur)")
    parser.add_argument("--state-dir", default=str(Path.home() / ".local/state/tokenoskobi/watcher"))
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    from services.market import tokenoskobi_product_slice_02_server as market
    url = pick_public_rpc(market.CFG["rpc"], market.rpc)
    with closing(Store(Path(args.state_dir).expanduser() / "pairs.sqlite")) as store:
        print(check(store, lambda method, params: market.rpc(url, method, params), args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
