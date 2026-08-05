#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict
import hashlib
import json
import os
import tempfile

ROOT = Path("/root/tokenoskobi_clean_v1")
ACTIVE_DATA = ROOT / "active_panel_8096/current/data"

SOURCES = {
    "news_coverage_readmodel_consumer_summary_v1.json": ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json",
    "news_market_indicator_latest_v1.json": ROOT / "runtime/state/news_market_indicator_latest_v1.json",
    "news_adversarial_latest_v1.json": ROOT / "runtime/state/news_adversarial_latest_v1.json",
    "news_coverage_panel_display_v1.json": ROOT / "runtime/state/news_coverage_panel_display_v1.json",
    "hot_intelligence_ingress_gateway_v1.json": ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json",
    "news_runtime_stabilization_review_v1.json": ROOT / "runtime/state/news_runtime_stabilization_review_v1.json",
    "news_producer_health_watch_and_hot_gateway_review_v1.json": ROOT / "runtime/state/news_producer_health_watch_and_hot_gateway_review_v1.json",
}

OUT = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def atomic_json_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    read_json(src)
    source_bytes = src.read_bytes()
    fd, tmp = tempfile.mkstemp(
        prefix=".news_bridge_",
        suffix=".json",
        dir=str(dst.parent),
    )
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(source_bytes)
            f.flush()
            os.fsync(f.fileno())
        read_json(Path(tmp))
        os.replace(tmp, dst)
        directory_fd = os.open(dst.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def validate_authority(obj: Dict[str, Any]) -> list[str]:
    failures: list[str] = []

    def check_auth(auth: Dict[str, Any], prefix: str) -> None:
        for key in [
            "db_write",
            "db_schema_change",
            "hunter_authorized",
            "trade_signal",
            "paper_signal",
            "live_trade",
            "execution_authority",
            "service_change",
            "timer_change",
            "network_call",
            "external_api_call",
        ]:
            if key in auth and auth.get(key) is not False:
                failures.append(prefix + ":" + key + "_not_false")

    if isinstance(obj.get("authority"), dict):
        check_auth(obj["authority"], "root")
    if isinstance(obj.get("summary"), dict) and isinstance(
        obj["summary"].get("authority"), dict
    ):
        check_auth(obj["summary"]["authority"], "summary")
    if isinstance(obj.get("hot_gateway"), dict) and isinstance(
        obj["hot_gateway"].get("authority"), dict
    ):
        check_auth(obj["hot_gateway"]["authority"], "hot_gateway")
    if isinstance(obj.get("review_state"), dict):
        hg = obj["review_state"].get("hot_gateway") or {}
        if isinstance(hg.get("authority"), dict):
            check_auth(hg["authority"], "review_hot_gateway")
    return failures


def main() -> int:
    started = utc_now()
    ACTIVE_DATA.mkdir(parents=True, exist_ok=True)

    checks = []
    failures = []
    source_hashes: Dict[str, str] = {}
    target_hashes_before: Dict[str, str | None] = {}
    target_hashes_after: Dict[str, str] = {}

    source_objs: Dict[str, Dict[str, Any]] = {}

    for name, src in SOURCES.items():
        checks.append(
            {
                "name": "source_exists:" + name,
                "ok": src.exists() and src.is_file(),
            }
        )
        if not src.exists():
            failures.append("missing_source:" + name)
            continue
        try:
            obj = read_json(src)
            source_objs[name] = obj
            checks.append({"name": "source_parse_ok:" + name, "ok": True})
            auth_failures = validate_authority(obj)
            if auth_failures:
                failures.extend(
                    [
                        "source_authority:" + name + ":" + x
                        for x in auth_failures
                    ]
                )
            source_hashes[name] = sha256(src)
        except Exception as e:
            checks.append(
                {
                    "name": "source_parse_ok:" + name,
                    "ok": False,
                    "error": str(e),
                }
            )
            failures.append("source_parse_failed:" + name)

    display = source_objs.get("news_coverage_panel_display_v1.json", {})
    health = display.get("health") or {}
    if health.get("source_authority_ok") is not True:
        failures.append("display_source_authority_not_ok")
    if health.get("parse_errors") not in (0, None):
        failures.append("display_parse_errors")
    if health.get("duplicate_event_uids") not in (0, None):
        failures.append("display_duplicate_event_uids")
    if health.get("unsafe_events") not in (0, None):
        failures.append("display_unsafe_events")

    summary = source_objs.get(
        "news_coverage_readmodel_consumer_summary_v1.json", {}
    )
    if summary.get("parse_errors") not in (0, None):
        failures.append("summary_parse_errors")
    if summary.get("duplicate_event_uids") not in (0, None):
        failures.append("summary_duplicate_event_uids")
    if summary.get("unsafe_events") not in (0, None):
        failures.append("summary_unsafe_events")

    hot = source_objs.get("hot_intelligence_ingress_gateway_v1.json", {})
    if hot.get("hot_queue_count") is None:
        failures.append("hot_queue_count_missing")

    watch = source_objs.get(
        "news_producer_health_watch_and_hot_gateway_review_v1.json", {}
    )
    if watch.get("blockers"):
        failures.append("watch_blockers_present")

    for name in SOURCES:
        dst = ACTIVE_DATA / name
        target_hashes_before[name] = sha256(dst) if dst.exists() else None

    if not failures:
        for name, src in SOURCES.items():
            atomic_json_copy(src, ACTIVE_DATA / name)

        manifest = {
            "schema_version": "1.0",
            "bridge": "NEWS_ACTIVE_PANEL_DATA_BRIDGE_V1",
            "generated_at_utc": utc_now(),
            "source_dir": str(ROOT / "runtime/state"),
            "target_dir": str(ACTIVE_DATA),
            "files": sorted(SOURCES.keys()),
            "source_hashes": source_hashes,
            "authority": {
                "db_write": False,
                "db_schema_change": False,
                "service_change": False,
                "timer_change": False,
                "panel_html_change": False,
                "panel_data_write": True,
                "network_call": False,
                "external_api_call": False,
                "hunter_authorized": False,
                "trade_signal": False,
                "paper_signal": False,
                "live_trade": False,
                "execution_authority": False,
            },
            "status": "ACTIVE_PANEL_DATA_BRIDGE_APPLIED",
        }
        tmp_manifest = (
            ACTIVE_DATA / "news_active_panel_data_bridge_manifest_v1.json"
        )
        fd, tmp = tempfile.mkstemp(
            prefix=".news_bridge_manifest_",
            suffix=".json",
            dir=str(ACTIVE_DATA),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(
                    manifest,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            read_json(Path(tmp))
            os.replace(tmp, tmp_manifest)
            directory_fd = os.open(ACTIVE_DATA, os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    for name in SOURCES:
        dst = ACTIVE_DATA / name
        if dst.exists():
            target_hashes_after[name] = sha256(dst)

    hash_match = {
        name: target_hashes_after.get(name) == source_hashes.get(name)
        for name in SOURCES.keys()
    }

    if not all(hash_match.values()):
        failures.append("target_hash_mismatch")

    status = {
        "schema_version": "1.0",
        "bridge": "NEWS_ACTIVE_PANEL_DATA_BRIDGE_V1",
        "generated_at_utc": started,
        "finished_at_utc": utc_now(),
        "decision": (
            "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED"
            if not failures
            else "FAIL_NEWS_ACTIVE_PANEL_DATA_BRIDGE"
        ),
        "source_dir": str(ROOT / "runtime/state"),
        "target_dir": str(ACTIVE_DATA),
        "files": sorted(SOURCES.keys()),
        "source_hashes": source_hashes,
        "target_hashes_before": target_hashes_before,
        "target_hashes_after": target_hashes_after,
        "hash_match": hash_match,
        "checks": checks,
        "failures": failures,
        "authority": {
            "db_write": False,
            "db_schema_change": False,
            "service_change": False,
            "timer_change": False,
            "panel_html_change": False,
            "panel_data_write": True,
            "network_call": False,
            "external_api_call": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "execution_authority": False,
        },
        "next": "ACTIVE_PANEL_UI_ROUTE_BINDING_REVIEW_OR_STOP",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "bridge": status["bridge"],
                "decision": status["decision"],
                "target_dir": status["target_dir"],
                "file_count": len(status["files"]),
                "failures": failures,
                "hash_match_all": all(hash_match.values()),
                "output": str(OUT),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
