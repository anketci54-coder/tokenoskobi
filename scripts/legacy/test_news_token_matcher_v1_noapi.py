#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3
import sys
from collections import Counter

ROOT = "/root/tokenoskobi_clean_v1"
sys.path.insert(0, ROOT + "/tools")

from news_token_matcher_v1 import match_many, REAL_REASONS

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def read_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def pick(row, *names):
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return ""

def table_exists(cur, table):
    return cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone() is not None

def load_tokens(db_path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    out = []

    for r in cur.execute("SELECT * FROM token_score_100_events ORDER BY score_total DESC").fetchall():
        d = dict(r)
        token_uid = pick(d, "token_uid")
        pair_uid = pick(d, "pair_uid")
        chain = pick(d, "chain")
        symbol = ""
        name = ""
        token_address = ""
        pair_address = ""

        if token_uid and table_exists(cur, "tokens"):
            tr = cur.execute("SELECT * FROM tokens WHERE token_uid=? LIMIT 1", (token_uid,)).fetchone()
            if tr:
                td = dict(tr)
                symbol = pick(td, "symbol", "token_symbol", "ticker", "name")
                name = pick(td, "name", "token_name", "display_name") or symbol
                token_address = pick(td, "token_address", "address", "contract_address")
                chain = chain or pick(td, "chain", "network")

        if pair_uid and table_exists(cur, "pairs"):
            pr = cur.execute("SELECT * FROM pairs WHERE pair_uid=? LIMIT 1", (pair_uid,)).fetchone()
            if pr:
                pd = dict(pr)
                symbol = symbol or pick(pd, "symbol", "base_symbol", "token_symbol", "name")
                name = name or pick(pd, "name", "pair_name", "token_name") or symbol
                pair_address = pick(pd, "pair_address", "address", "pool_address")
                chain = chain or pick(pd, "chain", "network")

        out.append({
            "token_uid": token_uid,
            "pair_uid": pair_uid,
            "symbol": symbol,
            "name": name,
            "chain": chain,
            "token_address": token_address,
            "pair_address": pair_address,
        })

    con.close()
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--news12-json", required=True)
    ap.add_argument("--out-json", required=True)
    args = ap.parse_args()

    news12 = read_json(args.news12_json)
    raw = read_jsonl(news12["outputs"]["raw_jsonl"])
    old = read_jsonl(news12["outputs"]["match_jsonl"])
    new = match_many(raw, load_tokens(args.db))

    def baseline_low(row):
        reasons = row.get("match_reasons") or []
        return (
            row.get("match_confidence") == "LOW"
            and "TRACKED_TOKEN_PAIR_PRESENT" in reasons
            and not any(x in reasons for x in REAL_REASONS)
        )

    old_low = sum(1 for r in old if baseline_low(r))
    new_low = sum(1 for r in new if baseline_low(r))
    none_attached = sum(
        1 for r in new
        if r.get("match_confidence") == "NONE"
        and (r.get("token_uid") or r.get("pair_uid") or r.get("symbol"))
    )

    result = {
        "raw_rows": len(raw),
        "old_rows": len(old),
        "new_rows": len(new),
        "old_confidence_counts": dict(Counter(r.get("match_confidence") for r in old)),
        "new_confidence_counts": dict(Counter(r.get("match_confidence") for r in new)),
        "old_baseline_only_low_count": old_low,
        "new_baseline_only_low_count": new_low,
        "none_attached_count": none_attached,
        "write_allowed_count": sum(1 for r in new if r.get("write_allowed")),
        "trade_signal_count": sum(1 for r in new if r.get("trade_signal")),
        "paper_signal_count": sum(1 for r in new if r.get("paper_signal")),
    }

    result["ok"] = (
        len(raw) == len(new)
        and old_low > 0
        and new_low == 0
        and none_attached == 0
        and result["trade_signal_count"] == 0
        and result["paper_signal_count"] == 0
    )

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
