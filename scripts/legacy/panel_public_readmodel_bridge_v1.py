#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
SRC = ROOT / 'public/backpressure_readmodel_refresh_staging_v1'
DST = ROOT / 'active_panel_8096/current/data'
OUT = ROOT / 'data/control/n14a_panel_public_bridge_apply_result_v1.json'
ROWS = ROOT / 'data/control/n14a_panel_public_bridge_apply_result_v1_rows.jsonl'
FILES = [
    'backpressure_readmodel_refresh_cache.json',
    'backpressure_readmodel_refresh_manifest.json',
    'backpressure_readmodel_refresh_index.json',
]

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def read_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def atomic_json_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.bridge_', suffix='.json', dir=str(path.parent))
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
    started = datetime.now(timezone.utc).isoformat()
    checks = []
    sources = {name: SRC / name for name in FILES}
    targets = {name: DST / name for name in FILES}

    for name, path in sources.items():
        checks.append({'name': 'source_exists:' + name, 'ok': path.exists() and path.is_file()})
        if not path.exists():
            raise SystemExit('FAIL: missing source ' + str(path))
        try:
            read_json(path)
            checks.append({'name': 'source_parse_ok:' + name, 'ok': True})
        except Exception:
            checks.append({'name': 'source_parse_ok:' + name, 'ok': False})
            raise

    cache_sha = sha256(sources['backpressure_readmodel_refresh_cache.json'])
    manifest_sha = sha256(sources['backpressure_readmodel_refresh_manifest.json'])
    index_sha = sha256(sources['backpressure_readmodel_refresh_index.json'])
    cache = read_json(sources['backpressure_readmodel_refresh_cache.json'])
    manifest = read_json(sources['backpressure_readmodel_refresh_manifest.json'])
    index = read_json(sources['backpressure_readmodel_refresh_index.json'])

    validation = {
        'cache_state_valid': cache.get('state') == 'CACHE_VALID',
        'cache_runtime_lookup_only': cache.get('runtime_bucket') == 'LOOKUP_ONLY',
        'manifest_cache_sha_matches': manifest.get('cache_sha256') == cache_sha,
        'index_cache_sha_matches': index.get('cache_sha256') == cache_sha,
        'index_manifest_sha_matches': index.get('manifest_sha256') == manifest_sha,
    }
    for k, v in validation.items():
        checks.append({'name': k, 'ok': bool(v)})
    if not all(validation.values()):
        raise SystemExit('FAIL: source validation failed')

    for name in FILES:
        atomic_json_write(targets[name], read_json(sources[name]))

    target_hashes = {name: sha256(targets[name]) for name in FILES}
    source_hashes = {name: sha256(sources[name]) for name in FILES}
    hash_match = {name: target_hashes[name] == source_hashes[name] for name in FILES}
    for name, ok in hash_match.items():
        checks.append({'name': 'target_hash_match:' + name, 'ok': bool(ok)})

    status = {
        'stage': 'N14A_PANEL_PUBLIC_BRIDGE_SCRIPT_APPLY_NOAPI',
        'created_at_utc': started,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'decision': 'PANEL_PUBLIC_BRIDGE_APPLIED' if all(x['ok'] for x in checks) else 'PANEL_PUBLIC_BRIDGE_FAILED',
        'source_dir': str(SRC),
        'target_dir': str(DST),
        'source_hashes': source_hashes,
        'target_hashes': target_hashes,
        'hash_match': hash_match,
        'validation': validation,
        'authority': {
            'api_calls': 0,
            'provider_call': False,
            'wallet': False,
            'signing': False,
            'paper_trade': False,
            'live_trade': False,
            'policy_apply': False,
            'db_write': False,
            'core_change': False,
            'panel_html_change': False
        },
        'next_step': 'N14B_LOCALHOST_PANEL_STATIC_SERVE_PROBE'
    }
    atomic_json_write(DST / 'panel_public_bridge_status_v1.json', status)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    ROWS.write_text('\n'.join(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in checks) + '\n', encoding='utf-8')

    print('FINAL_GATE=PASS_N14A_PANEL_PUBLIC_BRIDGE_SCRIPT_APPLY_NOAPI')
    print('DECISION=' + status['decision'])
    print('TARGET_DIR=' + str(DST))
    print('JSON=' + str(OUT.relative_to(ROOT)))
    print('ROWS=' + str(ROWS.relative_to(ROOT)))

if __name__ == '__main__':
    main()
