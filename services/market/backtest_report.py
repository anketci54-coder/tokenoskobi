"""Geçmiş testi (backtest): daha önce verilmiş kararlar, sonradan olanla karşılaştırılır.

Karar analiz anında verildi ve o an sonucu bilmiyordu (ileriye bakma yok). Sonuç, watcher'ın analizden SONRA
kaydettiği likidite çekilmesidir (`pairs.status=PULLED`, `decided_at` = çekilmenin fark edildiği an).
Yalnızca likidite çekilmesi ölçülür; fiyat geçmişi kaydedilmediği için fiyat bu raporda YOK.
Salt okunur: hiçbir şey yazmaz.
"""
from __future__ import annotations

import argparse
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from services.market.pair_watcher import wilson

HORIZONS_MIN = (60, 360, 1440)
MIN_SAMPLE = 30


def outcome_at(row: sqlite3.Row, horizon_min: int, now: float) -> bool | None:
    """True = likidite bu sürede çekildi, False = çekilmedi, None = bilinmiyor (tahmin etmiyoruz)."""
    end = row["analyzed_at"] + horizon_min * 60
    if row["status"] == "PULLED" and row["decided_at"] is not None and row["decided_at"] <= end:
        return True
    if now < end:
        return None
    if row["status"] == "PULLED":
        return False           # çekilme pencereden sonra fark edildi
    watched_until = row["watch_until"]
    if watched_until is None or watched_until < end:
        return None            # izleme pencereden önce bitti: görmedik
    return False


def report(db: sqlite3.Connection, now: float | None = None) -> str:
    now = time.time() if now is None else now
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute(
            "SELECT a.decision, a.analyzed_at, p.status, p.decided_at, p.watch_until FROM analyses a"
            " JOIN pairs p ON p.target = a.token AND p.status IN ('KEPT','PULLED')"
            " WHERE a.status='OK'").fetchall()
    except sqlite3.OperationalError:
        return "Geçmiş testi: analiz tablosu bulunamadı."
    lines = ["Geçmiş testi: verilmiş kararlar sonradan nasıl çıktı (yalnızca likidite çekilmesi)", "",
             f"  eşleşen analiz: {len(rows)}"]
    for decision in ("ALLOW", "REVIEW", "WAIT", "BLOCK"):
        lines += ["", f"{decision}:"]
        mine = [r for r in rows if r["decision"] == decision]
        if not mine:
            lines.append("  analiz yok")
            continue
        for horizon in HORIZONS_MIN:
            known = [o for o in (outcome_at(r, horizon, now) for r in mine) if o is not None]
            unknown = len(mine) - len(known)
            if not known:
                lines.append(f"  {horizon // 60:>2} sa: ölçülebilen yok ({unknown} bilinmiyor)")
                continue
            pulled = sum(known)
            low, high = wilson(pulled, len(known))
            note = "  (örnek az, yorum yapma)" if len(known) < MIN_SAMPLE else ""
            lines.append(f"  {horizon // 60:>2} sa: {len(known)} örnek · likidite çekilen %{100 * pulled / len(known):.0f} "
                         f"(aralık %{100 * low:.0f}–%{100 * high:.0f}) · bilinmeyen {unknown}{note}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Geçmiş testi (salt okunur)")
    parser.add_argument("--state-dir", default=str(Path.home() / ".local/state/tokenoskobi/watcher"))
    args = parser.parse_args(argv)
    path = Path(args.state_dir).expanduser() / "pairs.sqlite"
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as db:
        print(report(db))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
