#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

SCHEMA_VERSION = "1.0"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_authority(obj: Dict[str, Any], expected_lane: str) -> Dict[str, Any]:
    lane_ok = obj.get("lane") == expected_lane
    db_write = obj.get("db_match_write")
    hunter = obj.get("hunter_authorized")
    trade = obj.get("trade_signal")
    paper = obj.get("paper_signal")

    if not lane_ok:
        db_write = True

    return {
        "db_write": db_write,
        "hunter_authorized": hunter,
        "trade_signal": trade,
        "paper_signal": paper,
        "live_trade": False,
        "execution_authority": False,
    }


def _convert_object(
    obj: Dict[str, Any],
    *,
    expected_lane: str,
    source_path: Path,
    line_number: int,
    raw_line: str,
) -> Dict[str, Any]:
    return {
        "event_uid": obj.get("event_uid"),
        "news_uid": obj.get("news_uid"),
        "title": obj.get("title"),
        "hits": obj.get("hits") if isinstance(obj.get("hits"), list) else [],
        "published_at_utc": obj.get("published_at_utc"),
        "source_uid": obj.get("source_uid"),
        "authority": _safe_authority(obj, expected_lane),
        "_pre_gateway": {
            "source_path": str(source_path),
            "line_number": line_number,
            "expected_lane": expected_lane,
            "observed_lane": obj.get("lane"),
            "raw_line_sha256": sha256_text(raw_line),
        },
    }


def read_lane_observations(
    path: Path,
    *,
    section_id: str,
    expected_lane: str,
) -> Dict[str, Any]:
    items: list[Any] = []
    physical_lines = 0
    nonempty_lines = 0
    blank_lines = 0
    parsed_object_rows = 0
    parsed_nonobject_rows = 0
    parse_error_rows = 0
    unsafe_rows = 0

    with path.open("rb") as handle:
        for line_number, physical in enumerate(handle, start=1):
            physical_lines += 1
            raw_bytes = physical.rstrip(b"\r\n")
            if not raw_bytes.strip():
                blank_lines += 1
                continue
            nonempty_lines += 1

            try:
                raw_line = raw_bytes.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                parse_error_rows += 1
                items.append(
                    "PRE_GATEWAY_UTF8_ERROR|"
                    f"path={path}|line={line_number}|"
                    f"error={type(exc).__name__}|"
                    f"raw_sha256={hashlib.sha256(raw_bytes).hexdigest()}|"
                    f"raw_hex_preview={raw_bytes[:256].hex()}"
                )
                continue

            try:
                value = json.loads(raw_line)
            except Exception as exc:
                parse_error_rows += 1
                items.append(
                    "PRE_GATEWAY_PARSE_ERROR|"
                    f"path={path}|line={line_number}|"
                    f"error={type(exc).__name__}|"
                    f"raw_sha256={sha256_text(raw_line)}|"
                    f"preview={raw_line[:512]}"
                )
                continue

            if not isinstance(value, dict):
                parsed_nonobject_rows += 1
                items.append(
                    "PRE_GATEWAY_NONOBJECT|"
                    f"path={path}|line={line_number}|"
                    f"type={type(value).__name__}|"
                    f"raw_sha256={sha256_text(raw_line)}|"
                    f"preview={raw_line[:512]}"
                )
                continue

            parsed_object_rows += 1
            converted = _convert_object(
                value,
                expected_lane=expected_lane,
                source_path=path,
                line_number=line_number,
                raw_line=raw_line,
            )
            authority = converted["authority"]
            if not all(
                authority.get(key) is False
                for key in (
                    "db_write",
                    "hunter_authorized",
                    "trade_signal",
                    "paper_signal",
                )
            ):
                unsafe_rows += 1
            items.append(converted)

    return {
        "section": {
            "id": section_id,
            "title": section_id,
            "count": nonempty_lines,
            "items": items,
        },
        "stats": {
            "path": str(path),
            "expected_lane": expected_lane,
            "physical_lines": physical_lines,
            "nonempty_lines": nonempty_lines,
            "blank_lines": blank_lines,
            "parsed_object_rows": parsed_object_rows,
            "parsed_nonobject_rows": parsed_nonobject_rows,
            "parse_error_rows": parse_error_rows,
            "unsafe_rows": unsafe_rows,
        },
    }


def build_candidate_display(
    market_path: Path,
    adversarial_path: Path,
) -> Dict[str, Any]:
    lane_specs = (
        (market_path, "news_market_indicator", "MARKET_INDICATOR"),
        (
            adversarial_path,
            "news_adversarial_intelligence",
            "ADVERSARIAL_NEWS",
        ),
    )
    sections: list[Dict[str, Any]] = []
    stats: list[Dict[str, Any]] = []

    for path, section_id, expected_lane in lane_specs:
        lane = read_lane_observations(
            path,
            section_id=section_id,
            expected_lane=expected_lane,
        )
        sections.append(lane["section"])
        stats.append(lane["stats"])

    total_nonempty = sum(int(row["nonempty_lines"]) for row in stats)
    total_parse_errors = sum(int(row["parse_error_rows"]) for row in stats)
    total_nonobjects = sum(int(row["parsed_nonobject_rows"]) for row in stats)
    total_unsafe = sum(int(row["unsafe_rows"]) for row in stats)

    return {
        "schema_version": SCHEMA_VERSION,
        "adapter": "NEWS_PRE_GATEWAY_CANDIDATE_STREAM_V1",
        "authority": {
            "db_write": False,
            "db_schema_change": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "execution_authority": False,
        },
        "health": {
            "source_authority_ok": True,
            "parse_errors": total_parse_errors,
            "nonobject_rows": total_nonobjects,
            "unsafe_rows": total_unsafe,
        },
        "extraction": {
            "lane_stats": stats,
            "source_candidate_count": total_nonempty,
            "physical_nonempty_line_accounting": True,
        },
        "sections": sections,
    }


def write_candidate_display(
    market_path: Path,
    adversarial_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    payload = build_candidate_display(market_path, adversarial_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return payload
