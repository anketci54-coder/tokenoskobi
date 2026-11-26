"""Geçmiş testi (backtest): daha önce verilmiş kararlar, sonradan olanla karşılaştırılır.

Karar analiz anında verildi ve o an sonucu bilmiyordu (ileriye bakma yok). Sonuç, watcher'ın analizden SONRA
kaydettiği likidite çekilmesidir (`pairs.status=PULLED`, `decided_at` = çekilmenin fark edildiği an).
Yalnızca likidite çekilmesi ölçülür; fiyat geçmişi kaydedilmediği için fiyat bu raporda YOK.
Salt okunur: hiçbir şey yazmaz.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from services.market.pair_watcher import wilson

HORIZONS_MIN = (60, 360, 1440)
MIN_SAMPLE = 30
FACTOR_HORIZON_MIN = 360
MIN_GROUP = 10   # bir uyarının "var" ve "yok" gruplarında en az bu kadar ölçülebilir örnek


def outcome_at(row: sqlite3.Row, horizon_min: int, now: float) -> bool | None:
    """True = likidite bu sürede çekildi, False = çekilmedi, None = bilinmiyor (tahmin etmiyoruz).

    Bir analizin o ufukta ölçülebilir olması SONUCA bağlı değildir: izleme penceresi (watch_until) ufku
    kapsamalı ve ufuk geçmiş olmalı. Aksi halde yalnızca çekilenler görülür ve oran şişer (hayatta kalma yanlılığı).
    """
    end = row["analyzed_at"] + horizon_min * 60
    if now < end or row["watch_until"] is None or row["watch_until"] < end:
        return None
    return row["status"] == "PULLED" and row["decided_at"] is not None and row["decided_at"] <= end


def report(db: sqlite3.Connection, now: float | None = None) -> str:
    now = time.time() if now is None else now
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute(
            "SELECT a.decision, a.analyzed_at, a.warnings, p.status, p.decided_at, p.watch_until FROM analyses a"
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
    lines += factors(rows, now)
    return "\n".join(lines)


def factors(rows: list[sqlite3.Row], now: float, horizon: int = FACTOR_HORIZON_MIN) -> list[str]:
    """Uyarı VAR / YOK gruplarında çekilme oranı. Aralıklar çakışıyorsa fark kanıtlanmış sayılmaz."""
    measured = [(set(json.loads(r["warnings"] or "[]")), o) for r in rows
                if (o := outcome_at(r, horizon, now)) is not None]
    lines = ["", f"Uyarıya göre ({horizon // 60} sa, tüm kararlar birlikte): uyarı VAR ↔ YOK, likidite çekilme oranı",
             f"  ölçülebilen analiz: {len(measured)}"]
    names = sorted({w for ws, _ in measured for w in ws})
    shown = 0
    for name in names:
        with_w = [o for ws, o in measured if name in ws]
        without = [o for ws, o in measured if name not in ws]
        if len(with_w) < MIN_GROUP or len(without) < MIN_GROUP:
            continue
        shown += 1
        a, b = sum(with_w), sum(without)
        la, ha = wilson(a, len(with_w))
        lb, hb = wilson(b, len(without))
        verdict = "fark gösterilemedi" if la <= hb and lb <= ha else ("uyarı VARKEN daha çok çekilmiş" if a / len(with_w) > b / len(without) else "uyarı VARKEN daha az çekilmiş")
        lines.append(f"  {name}: var %{100 * a / len(with_w):.0f} ({len(with_w)}) ↔ yok %{100 * b / len(without):.0f} ({len(without)}) · {verdict}")
    if not shown:
        lines.append(f"  her iki grupta da en az {MIN_GROUP} örneği olan uyarı yok")
    lines += combo(measured)
    lines.append("  Not: korelasyon nedensellik değil; eski kayıtlar LP/satış ölçümünden önceydi, o uyarılar karışık olabilir.")
    return lines


def combo(measured: list[tuple[set[str], bool]]) -> list[str]:
    """Birbirine bağlı iki uyarıyı birlikte ayırır: LP yakılmamış x sahip aktif cüzdan."""
    lines = ["", "İki uyarı birlikte (LP yakılmamış × sahip aktif cüzdan):"]
    for lp in (False, True):
        for eoa in (False, True):
            g = [o for ws, o in measured if ("LP_NOT_BURNED" in ws) == lp and ("OWNER_ACTIVE_EOA" in ws) == eoa]
            name = f"LP {'yakılmamış' if lp else 'yakılmış'} · sahip {'aktif cüzdan' if eoa else 'aktif cüzdan değil'}"
            if not g:
                lines.append(f"  {name}: örnek yok")
                continue
            low, high = wilson(sum(g), len(g))
            note = "  (örnek az, yorum yapma)" if len(g) < MIN_SAMPLE else ""
            lines.append(f"  {name}: {len(g)} örnek · çekilen %{100 * sum(g) / len(g):.0f} (aralık %{100 * low:.0f}–%{100 * high:.0f}){note}")
    return lines


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
