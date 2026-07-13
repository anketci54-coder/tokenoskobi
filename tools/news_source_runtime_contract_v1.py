#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

EXIT_NO_AUTHORIZED_SOURCES = 78
EXIT_ADAPTER_REQUIRED = 79
ACTIVE_STATUSES = {
    "ACTIVE",
    "ENABLED",
    "LIVE",
    "APPROVED_ACTIVE",
    "ENDPOINT_CONFIRMED_ACTIVE",
}
SUPPORTED_METHODS: set[str] = set()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row[1]) for row in rows}


def valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def resolve(db_path: Path, contract_path: Path) -> dict:
    contract = load_json(contract_path)
    authority = contract.get("authority") or {}
    registry_table = str(authority.get("seed_registry") or "")
    policy_table = str(authority.get("fetch_policy") or "")

    if registry_table != "news_source_registry_v1":
        raise RuntimeError("UNSUPPORTED_SEED_REGISTRY")
    if policy_table != "news_source_fetch_policy_v1":
        raise RuntimeError("UNSUPPORTED_FETCH_POLICY")

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        integrity = str(con.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity != "ok":
            raise RuntimeError(f"DB_INTEGRITY_FAILED:{integrity}")

        registry_columns = table_columns(con, registry_table)
        policy_columns = table_columns(con, policy_table)

        required_registry = {
            "source_uid",
            "source_name",
            "source_url",
            "fetch_method",
            "status",
        }
        required_policy = {
            "source_uid",
            "fetch_enabled",
            "daily_call_budget",
            "requires_approval_for_live_fetch",
        }
        if not required_registry.issubset(registry_columns):
            raise RuntimeError("REGISTRY_SCHEMA_MISMATCH")
        if not required_policy.issubset(policy_columns):
            raise RuntimeError("POLICY_SCHEMA_MISMATCH")

        rows = con.execute(
            f"""
            SELECT
                r.source_uid,
                r.source_name,
                r.source_url,
                r.fetch_method,
                r.status,
                p.fetch_enabled,
                p.daily_call_budget,
                p.requires_approval_for_live_fetch
            FROM {registry_table} AS r
            JOIN {policy_table} AS p
              ON p.source_uid = r.source_uid
            ORDER BY r.source_uid
            """
        ).fetchall()
    finally:
        con.close()

    sources = []
    eligible = []
    for row in rows:
        status = str(row["status"] or "").strip().upper()
        method = str(row["fetch_method"] or "").strip().upper()
        url = str(row["source_url"] or "").strip()
        fetch_enabled = int(row["fetch_enabled"] or 0) == 1
        budget = int(row["daily_call_budget"] or 0)
        approval_required = int(row["requires_approval_for_live_fetch"] or 0) == 1
        runtime_enabled = status in ACTIVE_STATUSES
        endpoint_valid = valid_http_url(url)
        adapter_supported = method in SUPPORTED_METHODS
        is_eligible = all(
            (
                runtime_enabled,
                fetch_enabled,
                budget > 0,
                not approval_required,
                endpoint_valid,
                adapter_supported,
            )
        )
        item = {
            "source_uid": str(row["source_uid"]),
            "source_name": str(row["source_name"] or ""),
            "registry_status": status,
            "fetch_method": method,
            "fetch_enabled": fetch_enabled,
            "daily_call_budget": budget,
            "approval_required": approval_required,
            "endpoint_valid": endpoint_valid,
            "adapter_supported": adapter_supported,
            "runtime_eligible": is_eligible,
        }
        sources.append(item)
        if is_eligible:
            eligible.append(item)

    contract_truth = contract.get("current_truth") or {}
    configured_live = bool(contract_truth.get("live_fetch_authorized"))
    configured_eligible = int(contract_truth.get("runtime_eligible_source_count") or 0)

    if configured_live or configured_eligible != 0:
        raise RuntimeError("CONTRACT_LIVE_TRUTH_NOT_FAIL_CLOSED")

    return {
        "schema": "news_source_runtime_contract_result_v1",
        "mode": "READ_ONLY_POLICY_RESOLUTION",
        "database": str(db_path),
        "contract": str(contract_path),
        "registered_source_count": len(sources),
        "runtime_eligible_source_count": len(eligible),
        "live_fetch_authorized": configured_live,
        "network_call": False,
        "database_write": False,
        "sources": sources,
    }


def main() -> int:
    root = Path(os.getenv("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1"))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db-path",
        default=os.getenv(
            "TOKENOSKOBI_DB_PATH",
            str(root / "data" / "tokenoskobi_clean_v1.sqlite"),
        ),
    )
    parser.add_argument(
        "--contract-path",
        default=os.getenv(
            "TOKENOSKOBI_NEWS_SOURCE_CONTRACT_PATH",
            str(root / "config" / "news_runtime_source_contract_v1.json"),
        ),
    )
    args = parser.parse_args()

    try:
        result = resolve(Path(args.db_path), Path(args.contract_path))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "schema": "news_source_runtime_contract_result_v1",
                    "status": "ERROR_FAIL_CLOSED",
                    "error": f"{type(exc).__name__}:{exc}",
                    "network_call": False,
                    "database_write": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            flush=True,
        )
        return 77

    eligible = int(result["runtime_eligible_source_count"])
    if eligible == 0:
        result["status"] = "SUCCESS_NOOP_FAIL_CLOSED"
        print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
        return EXIT_NO_AUTHORIZED_SOURCES

    result["status"] = "AUTHORIZED_SOURCE_ADAPTER_REQUIRED_FAIL_CLOSED"
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    return EXIT_ADAPTER_REQUIRED


if __name__ == "__main__":
    raise SystemExit(main())
