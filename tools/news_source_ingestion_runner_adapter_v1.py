#!/usr/bin/env python3
"""
NEWS_SOURCE_INGESTION_RUNNER_ADAPTER_V1

Generic adapter contract for news raw ingestion.
Safety default:
- no API call
- no fetch
- no timer
- no paper/live
- dry-run by default
- real DB write only when caller explicitly passes real_write=True and external safety guard allows it
"""

import hashlib
import json
from datetime import datetime, timezone

def _stable_hash(*parts):
    joined = "||".join("" if p is None else str(p).strip().lower() for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()

def normalize_news_event(row):
    source_id = str(row.get("source_id") or "").strip()
    source_name = str(row.get("source_name") or "").strip()
    title = str(row.get("raw_title") or row.get("title") or "").strip()
    url = str(row.get("raw_url") or row.get("url") or "").strip()
    published_at = str(row.get("published_at") or "").strip()
    fetched_at = str(row.get("fetched_at") or datetime.now(timezone.utc).isoformat()).strip()
    origin = str(row.get("endpoint_or_origin") or row.get("origin") or "").strip()
    payload = row.get("source_payload") or {}

    payload_hash = row.get("raw_payload_hash") or _stable_hash(
        json.dumps(payload, sort_keys=True, ensure_ascii=False)
    )

    return {
        "source_id": source_id,
        "source_name": source_name,
        "endpoint_or_origin": origin,
        "raw_title": title,
        "raw_url": url,
        "published_at": published_at,
        "fetched_at": fetched_at,
        "raw_payload_hash": payload_hash,
        "source_payload": payload,
        "title_hash": _stable_hash(title),
        "url_hash": _stable_hash(url),
        "event_hash": _stable_hash(source_id, source_name, title, url, published_at),
    }

def validate_news_event(ev, known_sources=None, existing_hashes=None, batch_hashes=None):
    known_sources = known_sources or set()
    existing_hashes = existing_hashes or set()
    batch_hashes = batch_hashes or set()

    reject = []

    if not ev.get("source_id"):
        reject.append("missing_source_id")

    if ev.get("source_id") and known_sources and ev["source_id"] not in known_sources:
        reject.append("source_not_registered")

    if not ev.get("raw_title") and not ev.get("raw_url"):
        reject.append("missing_title_and_url")

    if not ev.get("published_at"):
        reject.append("bad_timestamp")

    if (
        ev.get("event_hash") in existing_hashes
        or ev.get("title_hash") in existing_hashes
        or ev.get("url_hash") in existing_hashes
        or ev.get("raw_payload_hash") in existing_hashes
    ):
        reject.append("duplicate_existing_hash")

    if ev.get("event_hash") in batch_hashes:
        reject.append("duplicate_batch_hash")

    if reject:
        return "REJECT", reject

    return "ACCEPT", []

def simulate_adapter_batch(rows, known_sources=None, existing_hashes=None):
    known_sources = known_sources or set()
    existing_hashes = existing_hashes or set()
    batch_hashes = set()

    accepted = []
    rejected = []
    normalized = []

    for row in rows:
        ev = normalize_news_event(row)
        decision, reasons = validate_news_event(
            ev,
            known_sources=known_sources,
            existing_hashes=existing_hashes,
            batch_hashes=batch_hashes,
        )

        item = {
            "decision": decision if decision == "REJECT" else "ACCEPT_DRYRUN_ONLY",
            "reject_reasons": reasons,
            "normalized": ev,
        }

        normalized.append(item)

        if decision == "ACCEPT":
            accepted.append(item)
        else:
            rejected.append(item)

        batch_hashes.add(ev["event_hash"])

    reject_counts = {}
    for item in rejected:
        for reason in item["reject_reasons"]:
            reject_counts[reason] = reject_counts.get(reason, 0) + 1

    return {
        "input_rows": len(rows),
        "normalized_rows": len(normalized),
        "accepted_dryrun_only": len(accepted),
        "rejected": len(rejected),
        "reject_counts": reject_counts,
        "normalized_preview": normalized,
        "db_insert_attempted": False,
        "db_inserted_rows": 0,
        "fetch_attempted": False,
        "api_calls": 0,
        "external_network_calls": 0,
    }
