#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "general_systemd_dependency_check_v1"
HISTORICAL_PREFIXES = (
    "archive/",
    "docs/archive/",
    "reports/",
    "data/control/",
    "data/phase",
)
ACTIVE_PREFIXES = (
    "tools/",
    "core/",
    "runtime/",
    "config/",
    "active_panel_8096/",
    "systemd/",
    "systemd_drafts/",
    ".github/workflows/",
)
CANONICAL_FILES = {
    "PROJECT_RUNTIME.json",
    "PROJECT_HISTORY.json",
    "PROJECT_BOOT.json",
    "01_INDEX.md",
    "02_MANIFESTO.md",
    "03_ROADMAP.md",
    "04_ALMANAC.md",
    "05_ATLAS.md",
    "06_PROJECT_MASTER_STATE.md",
    "07_PROJECT_HANDOFF.md",
    "README.md",
}


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def systemctl_show(unit: str, properties: list[str]) -> dict[str, str]:
    argv = ["systemctl", "show", unit, "--no-pager"]
    for prop in properties:
        argv.extend(["-p", prop])
    result = run(argv)
    if result.returncode != 0:
        raise RuntimeError(
            f"SYSTEMCTL_SHOW_FAILED:{unit}:{result.stderr.strip()}"
        )
    return {
        line.split("=", 1)[0]: line.split("=", 1)[1]
        for line in result.stdout.splitlines()
        if "=" in line
    }


def unit_record(unit: str) -> dict[str, Any]:
    props = systemctl_show(
        unit,
        [
            "Id",
            "Names",
            "Description",
            "LoadState",
            "ActiveState",
            "SubState",
            "UnitFileState",
            "Result",
            "FragmentPath",
            "DropInPaths",
            "ExecStart",
            "Environment",
            "EnvironmentFiles",
            "Triggers",
            "TriggeredBy",
            "Requires",
            "Requisite",
            "Wants",
            "WantedBy",
            "Before",
            "After",
            "PartOf",
            "Upholds",
            "ConsistsOf",
            "OnCalendar",
            "OnBootUSec",
            "OnUnitActiveUSec",
            "OnUnitInactiveUSec",
            "LastTriggerUSec",
            "NextElapseUSecRealtime",
        ],
    )
    fragment_text = props.get("FragmentPath") or ""
    fragment = Path(fragment_text) if fragment_text else None
    dropins = [
        Path(item)
        for item in (props.get("DropInPaths") or "").split()
        if item
    ]
    cat = run(["systemctl", "cat", unit, "--no-pager"])
    reverse = run(
        [
            "systemctl",
            "list-dependencies",
            "--reverse",
            "--all",
            "--plain",
            "--no-pager",
            unit,
        ]
    )
    forward = run(
        [
            "systemctl",
            "list-dependencies",
            "--all",
            "--plain",
            "--no-pager",
            unit,
        ]
    )
    return {
        "unit": unit,
        "properties": props,
        "fragment": {
            "path": str(fragment) if fragment else None,
            "exists": bool(fragment and fragment.is_file()),
            "sha256": (
                sha256(fragment)
                if fragment and fragment.is_file()
                else None
            ),
        },
        "dropins": [
            {
                "path": str(path),
                "exists": path.is_file(),
                "sha256": sha256(path) if path.is_file() else None,
            }
            for path in dropins
        ],
        "cat_returncode": cat.returncode,
        "cat": cat.stdout,
        "reverse_dependencies_returncode": reverse.returncode,
        "reverse_dependencies": reverse.stdout.splitlines(),
        "forward_dependencies_returncode": forward.returncode,
        "forward_dependencies": forward.stdout.splitlines(),
    }


def git_grep(root: Path, patterns: list[str]) -> list[dict[str, Any]]:
    rows: dict[tuple[str, int, str], dict[str, Any]] = {}
    for pattern in patterns:
        result = run(
            ["git", "grep", "-n", "-I", "-F", "--", pattern],
            cwd=root,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(
                f"GIT_GREP_FAILED:{pattern}:{result.stderr.strip()}"
            )
        for line in result.stdout.splitlines():
            match = re.match(r"^([^:]+):(\d+):(.*)$", line)
            if not match:
                continue
            path = match.group(1)
            line_number = int(match.group(2))
            text = match.group(3).strip()
            if path.startswith(HISTORICAL_PREFIXES):
                category = "HISTORICAL_REFERENCE"
            elif path in CANONICAL_FILES:
                category = "CANONICAL_REFERENCE"
            elif path.startswith(ACTIVE_PREFIXES):
                category = "ACTIVE_CODE_REFERENCE"
            else:
                category = "OTHER_REFERENCE"
            key = (path, line_number, text)
            rows[key] = {
                "path": path,
                "line": line_number,
                "text": text[:1000],
                "category": category,
                "matched_pattern": pattern,
            }
    return sorted(
        rows.values(),
        key=lambda item: (item["path"], item["line"]),
    )


def filesystem_references(patterns: list[str]) -> list[dict[str, str]]:
    roots = [
        Path("/etc/systemd/system"),
        Path("/etc/cron.d"),
        Path("/etc/cron.daily"),
        Path("/etc/cron.hourly"),
        Path("/etc/cron.weekly"),
        Path("/etc/cron.monthly"),
    ]
    found: dict[tuple[str, str], dict[str, str]] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            try:
                if path.is_symlink():
                    target = os.readlink(path)
                    for pattern in patterns:
                        if pattern in target or pattern in str(path):
                            found[(str(path), target)] = {
                                "path": str(path),
                                "kind": "symlink",
                                "match": pattern,
                                "target_or_line": target,
                            }
                    continue
                if not path.is_file() or path.stat().st_size > 2_000_000:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError):
                continue
            for pattern in patterns:
                for line in text.splitlines():
                    if pattern in line:
                        found[(str(path), line.strip())] = {
                            "path": str(path),
                            "kind": "text",
                            "match": pattern,
                            "target_or_line": line.strip()[:1000],
                        }
    return sorted(found.values(), key=lambda item: item["path"])


def journal_record(unit: str, since: str) -> dict[str, Any]:
    result = run(
        [
            "journalctl",
            "-u",
            unit,
            "--since",
            since,
            "--no-pager",
            "-o",
            "short-iso",
            "-n",
            "300",
        ],
        timeout=90,
    )
    lines = result.stdout.splitlines()
    return {
        "returncode": result.returncode,
        "since": since,
        "line_count": len(lines),
        "tail": lines[-100:],
        "stderr": result.stderr[-2000:],
    }


def active_dependency_names(lines: list[str], ignored: set[str]) -> list[str]:
    result = []
    for line in lines:
        text = line.strip()
        text = re.sub(r"^[●○*+\-\s]+", "", text)
        if not text or text in ignored:
            continue
        if text.endswith((".service", ".timer", ".target", ".socket", ".path")):
            result.append(text)
    return sorted(set(result))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=os.getenv(
            "TOKENOSKOBI_ROOT",
            "/root/tokenoskobi_clean_v1",
        ),
    )
    parser.add_argument("--timer", required=True)
    parser.add_argument("--service", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--config")
    parser.add_argument("--output-path")
    parser.add_argument("--since", default="30 days ago")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    script_rel = args.script.lstrip("/")
    if str(root) + "/" in args.script:
        script_rel = str(Path(args.script).resolve().relative_to(root))
    script_path = root / script_rel
    if not script_path.is_file():
        raise SystemExit(f"SCRIPT_MISSING:{script_path}")

    config_path = None
    config = None
    if args.config:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = root / config_path
        if not config_path.is_file():
            raise SystemExit(f"CONFIG_MISSING:{config_path}")
        config = load_json(config_path)

    runtime = load_json(root / "PROJECT_RUNTIME.json")
    timer = unit_record(args.timer)
    service = unit_record(args.service)

    patterns = [
        args.timer,
        args.service,
        script_rel,
        str(script_path),
    ]
    output_paths = re.findall(
        r"(?:BASE\s*/\s*)?[\"']([^\"']*(?:LATEST|STATUS)[^\"']*)[\"']",
        script_path.read_text(encoding="utf-8", errors="replace"),
    )
    patterns.extend(output_paths)

    repo_references = git_grep(root, patterns)
    filesystem_refs = filesystem_references(patterns)

    self_paths = {
        script_rel,
        "tools/general_systemd_dependency_check_v1.py",
    }
    active_repo_consumers = sorted(
        {
            row["path"]
            for row in repo_references
            if row["category"] == "ACTIVE_CODE_REFERENCE"
            and row["path"] not in self_paths
        }
    )
    canonical_references = sorted(
        {
            row["path"]
            for row in repo_references
            if row["category"] == "CANONICAL_REFERENCE"
        }
    )

    ignored_units = {args.timer, args.service}
    reverse_consumers = active_dependency_names(
        timer["reverse_dependencies"] + service["reverse_dependencies"],
        ignored_units,
    )

    service_exec = service["properties"].get("ExecStart", "")
    timer_triggers = timer["properties"].get("Triggers", "")
    service_triggered_by = service["properties"].get("TriggeredBy", "")

    binding_ok = (
        str(script_path) in service_exec
        and args.service in timer_triggers
        and args.timer in service_triggered_by
    )

    script_text = script_path.read_text(encoding="utf-8", errors="replace")
    script_declares_inert = all(
        token in script_text
        for token in (
            "runtime_enabled\": False",
            "api_calls\": 0",
            "rpc_calls\": 0",
            "fetch_calls\": 0",
            "paper_allowed\": False",
            "live_allowed\": False",
            "INERT_INSTALL_ONLY_NO_RUNTIME_LOOP",
        )
    )

    config_inert = True
    config_flags: dict[str, Any] = {}
    if isinstance(config, dict):
        for key in (
            "runtime_enabled",
            "api_rpc_fetch_enabled",
            "live_allowed",
            "paper_allowed",
            "panel_apply_allowed",
        ):
            config_flags[key] = config.get(key)
        config_inert = all(value is False for value in config_flags.values())

    active_filesystem_consumers = sorted(
        {
            item["path"]
            for item in filesystem_refs
            if item["path"]
            not in {
                timer["fragment"]["path"],
                service["fragment"]["path"],
            }
            and not item["path"].startswith(
                "/etc/systemd/system/"
                + args.timer
            )
        }
    )

    timer_enabled = timer["properties"].get("UnitFileState") == "enabled"
    timer_active = timer["properties"].get("ActiveState") == "active"

    blocking_reasons = []
    if not binding_ok:
        blocking_reasons.append("SYSTEMD_BINDING_NOT_PROVEN")
    if not script_declares_inert:
        blocking_reasons.append("SCRIPT_NOT_PROVEN_INERT")
    if not config_inert:
        blocking_reasons.append("CONFIG_NOT_PROVEN_INERT")
    if active_repo_consumers:
        blocking_reasons.append("ACTIVE_REPO_CONSUMERS_PRESENT")
    if reverse_consumers:
        blocking_reasons.append("EXTERNAL_SYSTEMD_CONSUMERS_PRESENT")
    if active_filesystem_consumers:
        blocking_reasons.append("EXTERNAL_FILESYSTEM_CONSUMERS_PRESENT")

    if blocking_reasons:
        decision = "REVIEW_REQUIRED"
    elif timer_enabled or timer_active:
        decision = "SAFE_TO_DISABLE_AND_STOP"
    else:
        decision = "ALREADY_INACTIVE_NO_ACTION"

    now = datetime.now(timezone.utc).isoformat()
    result = {
        "schema": SCHEMA,
        "timestamp_utc": now,
        "mode": "READ_ONLY_DEPENDENCY_CHECK",
        "target": {
            "timer": args.timer,
            "service": args.service,
            "script": script_rel,
            "config": (
                str(config_path.relative_to(root))
                if config_path
                else None
            ),
        },
        "decision": decision,
        "blocking_reasons": blocking_reasons,
        "checks": {
            "systemd_binding_proven": binding_ok,
            "script_declares_inert": script_declares_inert,
            "config_inert": config_inert,
            "config_flags": config_flags,
            "timer_enabled": timer_enabled,
            "timer_active": timer_active,
            "active_repo_consumer_count": len(active_repo_consumers),
            "external_systemd_consumer_count": len(reverse_consumers),
            "external_filesystem_consumer_count": len(
                active_filesystem_consumers
            ),
            "production_mutation": False,
            "systemd_mutation": False,
            "database_mutation": False,
            "network_call": False,
            "era57_opened": False,
        },
        "active_repo_consumers": active_repo_consumers,
        "canonical_references": canonical_references,
        "external_systemd_consumers": reverse_consumers,
        "external_filesystem_consumers": active_filesystem_consumers,
        "repo_references": repo_references,
        "filesystem_references": filesystem_refs,
        "timer": timer,
        "service": service,
        "journal": {
            args.timer: journal_record(args.timer, args.since),
            args.service: journal_record(args.service, args.since),
        },
        "canonical_runtime_snapshot": {
            "current_era": (
                runtime.get("canonical_runtime_pointer", {}).get("current_era")
            ),
            "next_safe_step": (
                runtime.get("canonical_runtime_pointer", {}).get(
                    "next_safe_step"
                )
            ),
            "era57_opened": (
                runtime.get("canonical_runtime_pointer", {}).get(
                    "era57_opened"
                )
            ),
            "production_mutation": (
                runtime.get("canonical_runtime_pointer", {}).get(
                    "production_mutation"
                )
            ),
        },
    }

    output_path = Path(
        args.output_path
        or (
            Path(tempfile.gettempdir())
            / "general_systemd_dependency_check_v1.json"
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    print(f"DECISION={decision}")
    print(f"SYSTEMD_BINDING_PROVEN={str(binding_ok).lower()}")
    print(f"SCRIPT_DECLARES_INERT={str(script_declares_inert).lower()}")
    print(f"CONFIG_INERT={str(config_inert).lower()}")
    print(f"ACTIVE_REPO_CONSUMERS={len(active_repo_consumers)}")
    print(f"EXTERNAL_SYSTEMD_CONSUMERS={len(reverse_consumers)}")
    print(
        "EXTERNAL_FILESYSTEM_CONSUMERS="
        + str(len(active_filesystem_consumers))
    )
    print(f"TIMER_ENABLED={str(timer_enabled).lower()}")
    print(f"TIMER_ACTIVE={str(timer_active).lower()}")
    print("PRODUCTION_MUTATION=false")
    print("SYSTEMD_MUTATION=false")
    print("ERA57_OPENED=false")
    print(f"OUTPUT={output_path}")
    return 0 if decision != "REVIEW_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
