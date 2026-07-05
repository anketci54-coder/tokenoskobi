#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
PANEL_DATA = ROOT / 'active_panel_8096/current/data'
RISK_PREVIEW = PANEL_DATA / 'risk_security_preview_data.json'
ONCHAIN = PANEL_DATA / 'onchain_center_live_readmodel_v1.json'
BRIDGE = PANEL_DATA / 'backpressure_readmodel_refresh_cache.json'
TARGET = PANEL_DATA / 'risk_center_live_readmodel_v1.json'
OUT = ROOT / 'data/control/n16d_risk_center_live_producer_result_v1.json'


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
    fd, tmp = tempfile.mkstemp(prefix='.n16d_risk_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        read_json(Path(tmp))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_source(name, path):
    exists = path.exists() and path.is_file()
    parsed = False
    obj = {}
    if exists:
        try:
            obj = read_json(path)
            parsed = True
        except Exception:
            parsed = False
    return {
        'name': name,
        'path': str(path),
        'exists': exists,
        'json_parse_ok': parsed,
        'sha256': sha256(path) if exists else None,
        'object': obj if parsed else {}
    }


def main():
    risk = load_source('risk_preview', RISK_PREVIEW)
    onchain = load_source('onchain_live_readmodel', ONCHAIN)
    bridge = load_source('bridge_cache', BRIDGE)

    onchain_decision = onchain['object'].get('decision')
    bridge_state = bridge['object'].get('state')
    bridge_bucket = bridge['object'].get('runtime_bucket')
    risk_preview_parse_ok = risk['json_parse_ok']

    checks = [
        {'name': 'risk_preview_exists_parse_ok', 'ok': risk_preview_parse_ok},
        {'name': 'onchain_readmodel_exists_parse_ok', 'ok': onchain['json_parse_ok']},
        {'name': 'bridge_cache_exists_parse_ok', 'ok': bridge['json_parse_ok']},
        {'name': 'onchain_decision_ready_or_lookup', 'ok': onchain_decision in ('ONCHAIN_CENTER_READY_LOOKUP_ONLY', 'ONCHAIN_CENTER_PARTIAL_OR_NEEDS_REVIEW')},
        {'name': 'bridge_cache_valid', 'ok': bridge_state == 'CACHE_VALID'},
        {'name': 'bridge_lookup_only', 'ok': bridge_bucket == 'LOOKUP_ONLY'}
    ]

    decision = 'RISK_CENTER_READY_PREVIEW_PLUS_LOOKUP_ONLY' if all(c['ok'] for c in checks) else 'RISK_CENTER_PARTIAL_OR_NEEDS_REVIEW'

    model = {
        'stage': 'N16D_RISK_CENTER_LIVE_PRODUCER',
        'generated_at_utc': now(),
        'producer': 'tools/risk_center_live_producer_v1.py',
        'decision': decision,
        'data_freshness_sec': 0,
        'authority': {
            'trade': False,
            'wallet_signing': False,
            'provider_call_from_browser': False,
            'policy_apply': False,
            'paper_trade_write': False
        },
        'source_count': sum(1 for s in (risk, onchain, bridge) if s['exists'] and s['json_parse_ok']),
        'items': [{
            'key': 'risk_center',
            'label': 'Risk Güvenlik Merkezi',
            'status': decision,
            'risk_mode': 'PREVIEW_PLUS_LOOKUP_ONLY_EVIDENCE',
            'live_risk_claim': False,
            'preview_available': risk_preview_parse_ok,
            'onchain_decision': onchain_decision,
            'bridge_state': bridge_state,
            'bridge_runtime_bucket': bridge_bucket,
            'checks': checks,
            'source_hashes': {
                'risk_preview': risk['sha256'],
                'onchain_live_readmodel': onchain['sha256'],
                'bridge_cache': bridge['sha256']
            },
            'note': 'Risk center separates old preview content from lookup-only bridge/onchain evidence. It does not claim live risk scoring yet.'
        }]
    }

    atomic_write(TARGET, model)
    atomic_write(OUT, model)
    print('FINAL_GATE=PASS_N16D_RISK_CENTER_LIVE_PRODUCER')
    print('DECISION=' + decision)
    print('JSON=' + str(OUT.relative_to(ROOT)))
    print('TARGET=' + str(TARGET.relative_to(ROOT)))

if __name__ == '__main__':
    main()
