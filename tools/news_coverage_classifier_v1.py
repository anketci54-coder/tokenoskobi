#!/usr/bin/env python3
# TOKENOSKOBI NEWS COVERAGE CLASSIFIER V1
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from typing import Any, Dict, Iterable, List

DEFAULT_MARKET_ASSETS = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "LINK", "TRX", "USDT", "USDC"]
DEFAULT_ADVERSARIAL_TERMS = ["approval", "bridge", "contract", "defi", "dex", "exploit", "launch", "perpetual", "phishing", "stablecoin", "token", "tokenized", "wallet", "rug", "honeypot", "airdrop", "liquidity"]

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def stable_hash(*parts: Any) -> str:
    raw = "||".join("" if x is None else str(x).strip().lower() for x in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if path.exists():
            obj = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(obj, dict):
                return obj
    except Exception:
        pass
    return default

def text_of(row: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("title", "description", "summary", "url", "source_uid", "published_at_utc"):
        value = row.get(key)
        if value not in (None, ""):
            parts.append(str(value))
    return " ".join(parts)

def word_hit(text: str, term: str) -> bool:
    term = str(term or "").strip()
    if not term:
        return False
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", text, re.I) is not None

def existing_event_uids(path: Path) -> set:
    out = set()
    if not path.exists():
        return out
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    uid = str(obj.get("event_uid") or "").strip()
                    if uid:
                        out.add(uid)
                except Exception:
                    continue
    except Exception:
        return out
    return out

def append_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> int:
    rows = list(records)
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(path.suffix + ".lock")
    fd = None
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        fd = None
        with path.open("a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return len(rows)
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass
        try:
            if lock.exists():
                lock.unlink()
        except Exception:
            pass

def classify_and_append_news_coverage_v1(
    candidates: List[Dict[str, Any]],
    market_path: str = "/root/tokenoskobi_clean_v1/runtime/state/news_market_indicator_events_v1.jsonl",
    adversarial_path: str = "/root/tokenoskobi_clean_v1/runtime/state/news_adversarial_events_v1.jsonl",
    config_dir: str = "/root/tokenoskobi_clean_v1/data/config",
) -> Dict[str, Any]:
    # Market/adversarial readmodels only. No DB match writes. No Hunter authority.
    cfg_dir = Path(config_dir)
    market_cfg = load_json(cfg_dir / "news_market_indicator_assets_v1.json", {"assets": DEFAULT_MARKET_ASSETS})
    adv_cfg = load_json(cfg_dir / "news_adversarial_terms_v1.json", {"terms": DEFAULT_ADVERSARIAL_TERMS})

    assets = [str(x).upper().strip() for x in market_cfg.get("assets", DEFAULT_MARKET_ASSETS) if str(x).strip()]
    terms = [str(x).lower().strip() for x in adv_cfg.get("terms", DEFAULT_ADVERSARIAL_TERMS) if str(x).strip()]

    market_file = Path(market_path)
    adversarial_file = Path(adversarial_path)
    existing_market = existing_event_uids(market_file)
    existing_adv = existing_event_uids(adversarial_file)

    market_events: List[Dict[str, Any]] = []
    adversarial_events: List[Dict[str, Any]] = []
    market_rows = 0
    adversarial_rows = 0

    for row in candidates or []:
        d = dict(row)
        news_uid = str(d.get("news_uid") or "").strip()
        raw_hash = str(d.get("raw_hash") or "").strip()
        title = str(d.get("title") or "").strip()
        published = str(d.get("published_at_utc") or "").strip()
        fetched = str(d.get("fetched_at_utc") or "").strip()
        source = str(d.get("source_uid") or "").strip()
        text = text_of(d)

        market_hits = [asset for asset in assets if word_hit(text, asset)]
        adv_hits = [term for term in terms if word_hit(text, term)]

        if market_hits:
            market_rows += 1
            event_uid = "market_news_" + stable_hash(news_uid, raw_hash, "market", ",".join(market_hits))[:24]
            if event_uid not in existing_market:
                market_events.append({
                    "event_uid": event_uid,
                    "lane": "MARKET_INDICATOR",
                    "news_uid": news_uid,
                    "raw_hash": raw_hash,
                    "source_uid": source,
                    "published_at_utc": published,
                    "fetched_at_utc": fetched,
                    "title": title,
                    "hits": market_hits,
                    "hunter_authorized": False,
                    "db_match_write": False,
                    "trade_signal": False,
                    "paper_signal": False,
                    "created_at_utc": now_utc()
                })
                existing_market.add(event_uid)

        if adv_hits:
            adversarial_rows += 1
            event_uid = "adversarial_news_" + stable_hash(news_uid, raw_hash, "adversarial", ",".join(adv_hits))[:24]
            if event_uid not in existing_adv:
                adversarial_events.append({
                    "event_uid": event_uid,
                    "lane": "ADVERSARIAL_NEWS",
                    "news_uid": news_uid,
                    "raw_hash": raw_hash,
                    "source_uid": source,
                    "published_at_utc": published,
                    "fetched_at_utc": fetched,
                    "title": title,
                    "hits": adv_hits,
                    "entity_binding_status": "UNBOUND_NO_EXPLICIT_TOKEN_PAIR_EVIDENCE",
                    "hunter_authorized": False,
                    "db_match_write": False,
                    "trade_signal": False,
                    "paper_signal": False,
                    "created_at_utc": now_utc()
                })
                existing_adv.add(event_uid)

    market_written = append_jsonl(market_file, market_events)
    adversarial_written = append_jsonl(adversarial_file, adversarial_events)

    return {
        "schema_version": "1.0",
        "classifier": "NEWS_COVERAGE_CLASSIFIER_V1",
        "input_candidates": len(candidates or []),
        "market_indicator_rows": market_rows,
        "adversarial_rows": adversarial_rows,
        "market_indicator_events": market_written,
        "adversarial_events": adversarial_written,
        "market_path": str(market_file),
        "adversarial_path": str(adversarial_file),
        "hunter_authorized": False,
        "db_match_write": False,
        "trade_signal": False,
        "paper_signal": False
    }
