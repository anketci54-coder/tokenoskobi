#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
PANEL_DATA = ROOT / 'active_panel_8096/current/data'
MANIFEST = PANEL_DATA / 'panel_live_manifest_v1.json'
OUT = ROOT / 'data/control/n16b_panel_live_readmodel_builder_result_v1.json'
ROWS = ROOT / 'data/control/n16b_panel_live_readmodel_builder_result_v1_rows.jsonl'


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n16b_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        read_json(Path(tmp))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def stat_source(rel):
    path = PANEL_DATA / rel.replace('data/', '', 1) if rel.startswith('data/') else ROOT / rel
    exists = path.exists() and path.is_file()
    parsed = False
    keys = []
    if exists:
        try:
            obj = read_json(path)
            parsed = True
            if isinstance(obj, dict):
                keys = sorted(list(obj.keys()))[:20]
        except Exception:
            parsed = False
    return {
        'source': rel,
        'absolute_path': str(path),
        'exists': exists,
        'json_parse_ok': parsed,
        'keys_head': keys
    }


def center_readmodel(center):
    source_stats = [stat_source(s) for s in center.get('source_files', [])]
    source_count = sum(1 for s in source_stats if s['exists'] and s['json_parse_ok'])
    missing = [s['source'] for s in source_stats if not s['exists']]
    parse_fail = [s['source'] for s in source_stats if s['exists'] and not s['json_parse_ok']]
    status = center.get('status', 'DATA_MISSING')
    if missing or parse_fail:
        if status not in ('DATA_MISSING', 'SEALED_INACTIVE'):
            status = 'PARTIAL_READY_WITH_MISSING_SOURCE'
    item = {
        'key': center.get('key'),
        'label': center.get('label'),
        'status': status,
        'source_count': source_count,
        'source_stats': source_stats,
        'missing_sources': missing,
        'parse_failed_sources': parse_fail,
        'stale_behavior': center.get('stale_behavior'),
        'authority': center.get('authority', 'display_only')
    }
    return {
        'stage': 'N16B_CENTER_LIVE_READMODEL',
        'generated_at_utc': now(),
        'producer': 'tools/panel_live_readmodel_builder_v1.py',
        'decision': status,
        'data_freshness_sec': 0,
        'authority': {
            'trade': False,
            'wallet_signing': False,
            'provider_call_from_browser': False,
            'policy_apply': False,
            'paper_trade_write': False
        },
        'source_count': source_count,
        'items': [item]
    }


def main():
    if not MANIFEST.exists():
        raise SystemExit('FAIL: missing manifest ' + str(MANIFEST))
    manifest = read_json(MANIFEST)
    centers = manifest.get('centers', [])
    rows = []
    written = []
    for center in centers:
        rm = center_readmodel(center)
        rel_target = center.get('target_readmodel')
        if not rel_target:
            raise SystemExit('FAIL: missing target_readmodel for ' + str(center.get('key')))
        target = PANEL_DATA / rel_target.replace('data/', '', 1)
        atomic_write(target, rm)
        written.append(str(target.relative_to(ROOT)))
        rows.append({'center': center.get('key'), 'target': str(target.relative_to(ROOT)), 'decision': rm['decision'], 'source_count': rm['source_count']})

    summary = {
        'stage': 'N16B_NOAPI_PANEL_LIVE_READMODEL_BUILDER',
        'generated_at_utc': now(),
        'producer': 'tools/panel_live_readmodel_builder_v1.py',
        'decision': 'PANEL_LIVE_READMODELS_BUILT',
        'manifest': str(MANIFEST.relative_to(ROOT)),
        'written_files': written,
        'center_count': len(centers),
        'authority': {
            'api_calls': 0,
            'provider_call': False,
            'wallet': False,
            'signing': False,
            'paper_trade': False,
            'live_trade': False,
            'policy_apply': False,
            'db_write': False,
            'core_change': False
        },
        'next_step': 'N16C_PANEL_INDEX_BIND_TO_LIVE_MANIFEST'
    }
    atomic_write(PANEL_DATA / 'panel_live_status_v1.json', summary)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    ROWS.write_text('\n'.join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + '\n', encoding='utf-8')
    print('FINAL_GATE=PASS_N16B_NOAPI_PANEL_LIVE_READMODEL_BUILDER')
    print('DECISION=' + summary['decision'])
    print('CENTER_COUNT=' + str(len(centers)))
    print('JSON=' + str(OUT.relative_to(ROOT)))

if __name__ == '__main__':
    main()
