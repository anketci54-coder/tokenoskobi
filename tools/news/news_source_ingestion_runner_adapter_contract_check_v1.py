#!/usr/bin/env python3
"""
Contract check for NEWS_SOURCE_INGESTION_RUNNER_ADAPTER_V1.
This file must not call API, fetch, timer, paper/live or mutate DB.
"""

import json
import sys
from pathlib import Path

BASE = Path("/root/tokenoskobi_clean_v1")
sys.path.insert(0, str(BASE / "app"))
sys.path.insert(0, str(BASE / "tools"))

from news_source_ingestion_runner_adapter_v1 import simulate_adapter_batch

def main():
    rows = [
        {
            "source_id": "DRYRUN_SOURCE",
            "source_name": "Dryrun Source",
            "endpoint_or_origin": "LOCAL_CONTRACT_CHECK",
            "raw_title": "Adapter contract accepted sample",
            "raw_url": "https://dryrun.local/adapter/accepted",
            "published_at": "2026-05-12T12:00:00Z",
            "source_payload": {"dryrun": True}
        },
        {
            "source_id": "",
            "source_name": "Dryrun Source",
            "endpoint_or_origin": "LOCAL_CONTRACT_CHECK",
            "raw_title": "Adapter contract missing source sample",
            "raw_url": "https://dryrun.local/adapter/missing-source",
            "published_at": "2026-05-12T12:05:00Z",
            "source_payload": {"dryrun": True}
        },
        {
            "source_id": "DRYRUN_SOURCE",
            "source_name": "Dryrun Source",
            "endpoint_or_origin": "LOCAL_CONTRACT_CHECK",
            "raw_title": "",
            "raw_url": "",
            "published_at": "2026-05-12T12:10:00Z",
            "source_payload": {"dryrun": True}
        },
    ]

    result = simulate_adapter_batch(rows, known_sources={"DRYRUN_SOURCE"}, existing_hashes=set())

    ok = (
        result["input_rows"] == 3
        and result["accepted_dryrun_only"] == 1
        and result["rejected"] == 2
        and result["db_insert_attempted"] is False
        and result["api_calls"] == 0
        and result["external_network_calls"] == 0
    )

    print(json.dumps({
        "ok": ok,
        "result": result,
        "db_mutation": False,
        "api_calls": 0,
        "external_network_calls": 0,
        "fetch_attempted": False,
        "paper_live": False
    }, ensure_ascii=False, indent=2))

    raise SystemExit(0 if ok else 1)

if __name__ == "__main__":
    main()
