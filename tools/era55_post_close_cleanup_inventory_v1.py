#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1').resolve()
TOOLS = ROOT / 'tools'
OUTPUT = ROOT / 'data/control/era55_post_close_cleanup_inventory_v1.json'
SERVICE = 'tokenoskobi-news-radar-refresh.service'
TIMER = 'tokenoskobi-news-radar-refresh.timer'

HISTORICAL_NAME_MARKERS = (
    '.PRE_', '.ORIGINAL_', '.BACKUP_', '.bak', '.old', '.orig',
)
MANUAL_MARKERS = (
    'audit', 'probe', 'dryrun', 'review', 'decision', 'repair',
    'closure', 'seal', 'apply', 'preflight', 'postcheck',
)


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=ROOT, text=True, capture_output=True,
        check=False, timeout=60,
    )


def unit_text(unit: str) -> str:
    result = run(['systemctl', 'cat', unit, '--no-pager'])
    return result.stdout if result.returncode == 0 else ''


def python_files() -> list[Path]:
    return sorted(
        p for p in TOOLS.rglob('*.py')
        if '/archive/' not in p.as_posix()
    )


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def quoted_paths(text: str) -> set[str]:
    found = set()
    for match in re.findall(r'(?:/root/tokenoskobi_clean_v1/)?tools/[A-Za-z0-9_.\-/]+\.py', text):
        value = match
        if value.startswith('/root/tokenoskobi_clean_v1/'):
            value = value.removeprefix('/root/tokenoskobi_clean_v1/')
        found.add(value)
    return found


def imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
    except (SyntaxError, OSError):
        return set()
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return result


def main() -> int:
    files = python_files()
    service_text = unit_text(SERVICE)
    timer_text = unit_text(TIMER)
    unit_refs = quoted_paths(service_text + '\n' + timer_text)

    all_text: dict[str, str] = {}
    for path in files:
        try:
            all_text[relative(path)] = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            all_text[relative(path)] = ''

    rows: list[dict[str, Any]] = []
    for path in files:
        rel = relative(path)
        basename = path.name
        references = sorted(
            source for source, text in all_text.items()
            if source != rel and (rel in text or basename in text)
        )
        imported_by = sorted(
            source for source, text in all_text.items()
            if source != rel and path.stem in imports(ROOT / source)
        )
        unit_active = rel in unit_refs
        historical_name = any(marker.lower() in basename.lower() for marker in HISTORICAL_NAME_MARKERS)
        manual_name = any(marker in basename.lower() for marker in MANUAL_MARKERS)

        if unit_active:
            classification = 'ACTIVE_RUNTIME'
        elif historical_name:
            classification = 'ARCHIVE_CANDIDATE'
        elif imported_by:
            classification = 'ACTIVE_LIBRARY'
        elif references:
            classification = 'REFERENCED_MANUAL_OR_HISTORICAL'
        elif manual_name:
            classification = 'MANUAL_ONLY'
        else:
            classification = 'UNRESOLVED_REVIEW_REQUIRED'

        rows.append({
            'path': rel,
            'classification': classification,
            'unit_active': unit_active,
            'references': references,
            'imported_by': imported_by,
            'historical_name': historical_name,
            'manual_name': manual_name,
            'size_bytes': path.stat().st_size,
        })

    summary: dict[str, int] = {}
    for row in rows:
        summary[row['classification']] = summary.get(row['classification'], 0) + 1

    payload = {
        'schema': 'era55_post_close_cleanup_inventory_v1',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'mode': 'READ_ONLY_CLASSIFICATION',
        'production_mutation': False,
        'service': SERVICE,
        'timer': TIMER,
        'service_unit_found': bool(service_text),
        'timer_unit_found': bool(timer_text),
        'unit_python_references': sorted(unit_refs),
        'summary': summary,
        'archive_candidates': [r for r in rows if r['classification'] == 'ARCHIVE_CANDIDATE'],
        'active_runtime': [r for r in rows if r['classification'] == 'ACTIVE_RUNTIME'],
        'manual_only': [r for r in rows if r['classification'] == 'MANUAL_ONLY'],
        'unresolved': [r for r in rows if r['classification'] == 'UNRESOLVED_REVIEW_REQUIRED'],
        'all_rows': rows,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print('CLEANUP_INVENTORY=OK')
    print('PRODUCTION_MUTATION=false')
    print('SERVICE_UNIT_FOUND=' + str(bool(service_text)).lower())
    print('TIMER_UNIT_FOUND=' + str(bool(timer_text)).lower())
    print('ACTIVE_RUNTIME_COUNT=' + str(summary.get('ACTIVE_RUNTIME', 0)))
    print('ARCHIVE_CANDIDATE_COUNT=' + str(summary.get('ARCHIVE_CANDIDATE', 0)))
    print('MANUAL_ONLY_COUNT=' + str(summary.get('MANUAL_ONLY', 0)))
    print('UNRESOLVED_COUNT=' + str(summary.get('UNRESOLVED_REVIEW_REQUIRED', 0)))
    print('OUTPUT=' + relative(OUTPUT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
