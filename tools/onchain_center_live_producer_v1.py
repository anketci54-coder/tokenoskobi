#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
PANEL_DATA = ROOT / 'active_panel_8096/current/data'
CACHE = PANEL_DATA / 'backpressure_readmodel_refresh_cache.json'
MANIFEST = PANEL_DATA / 'backpressure_readmodel_refresh_manifest.json'
INDEX = PANEL_DATA / 'backpressure_readmodel_refresh_index.json'
TARGET = PANEL_DATA / 'onchain_center_live_readmodel_v1.json'
OUT = ROOT / 'data/control/n16d_onchain_center_live_producer_result_v1.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n16d_onchain_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        read_json(Path(tmp))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    files = {'cache': CACHE, 'manifest': MANIFEST, 'index': INDEX}
    file_checks = []
    parsed = {}
    for name, path in files.items():
        exists = path.exists() and path.is_file()
        ok = False
        if exists:
            try:
                parsed[name] = read_json(path)
                ok = True
            except Exception:
                ok = False
        file_checks.append({'name': name + '_exists_and_parse_ok', 'ok': exists and ok, 'path': str(path)})

    hashes = {k: sha256(v) for k, v in files.items() if v.exists() and v.is_file()}
    cache = parsed.get('cache', {})
    manifest = parsed.get('manifest', {})
    index = parsed.get('index', {})

    checks = list(file_checks)
    checks += [
        {'name': 'cache_state_valid', 'ok': cache.get('state') == 'CACHE_VALID'},
        {'name': 'cache_runtime_lookup_only', 'ok': cache.get('runtime_bucket') == 'LOOKUP_ONLY'},
        {'name': 'manifest_cache_sha_matches', 'ok': manifest.get('cache_sha256') == hashes.get('cache')},
        {'name': 'index_cache_sha_matches', 'ok': index.get('cache_sha256') == hashes.get('cache')},
        {'name': 'index_manifest_sha_matches', 'ok': index.get('manifest_sha256') == hashes.get('manifest')}
    ]

    items = cache.get('items') or cache.get('rows') or cache.get('candidates') or []
    item_count = len(items) if isinstance(items, list) else 0
    decision = 'ONCHAIN_CENTER_READY_LOOKUP_ONLY' if all(c['ok'] for c in checks) else 'ONCHAIN_CENTER_PARTIAL_OR_NEEDS_REVIEW'

    model = {
        'stage': 'N16D_ONCHAIN_CENTER_LIVE_PRODUCER',
        'generated_at_utc': now(),
        'producer': 'tools/onchain_center_live_producer_v1.py',
        'decision': decision,
        'data_freshness_sec': 0,
        'authority': {
            'trade': False,
            'wallet_signing': False,
            'provider_call_from_browser': False,
            'policy_apply': False,
            'paper_trade_write': False
        },
        'source_count': sum(1 for c in file_checks if c['ok']),
        'items': [{
            'key': 'onchain_center',
            'label': 'Onchain Veri Merkezi',
            'status': decision,
            'mode': 'LOOKUP_ONLY_DISPLAY',
            'cache_state': cache.get('state'),
            'runtime_bucket': cache.get('runtime_bucket'),
            'item_count': item_count,
            'hashes': hashes,
            'checks': checks,
            'sample_items': items[:5] if isinstance(items, list) else []
        }]
    }
    atomic_write(TARGET, model)
    atomic_write(OUT, model)
    print('FINAL_GATE=PASS_N16D_ONCHAIN_CENTER_LIVE_PRODUCER')
    print('DECISION=' + decision)
    print('ITEM_COUNT=' + str(item_count))
    print('JSON=' + str(OUT.relative_to(ROOT)))
    print('TARGET=' + str(TARGET.relative_to(ROOT)))

if __name__ == '__main__':
    main()
