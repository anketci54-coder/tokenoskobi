#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
PANEL_DATA = ROOT / 'active_panel_8096/current/data'
SYSTEM = PANEL_DATA / 'system_center_live_readmodel_v1.json'
ONCHAIN = PANEL_DATA / 'onchain_center_live_readmodel_v1.json'
RISK = PANEL_DATA / 'risk_center_live_readmodel_v1.json'
BRIDGE_STATUS = PANEL_DATA / 'panel_public_bridge_status_v1.json'
TARGET = PANEL_DATA / 'command_center_live_readmodel_v1.json'
OUT = ROOT / 'data/control/n16d_command_center_live_producer_result_v1.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n16d_command_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        read_json(Path(tmp))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load(name, path):
    exists = path.exists() and path.is_file()
    parsed = False
    obj = {}
    if exists:
        try:
            obj = read_json(path)
            parsed = True
        except Exception:
            parsed = False
    return {'name': name, 'path': str(path), 'exists': exists, 'json_parse_ok': parsed, 'decision': obj.get('decision') if isinstance(obj, dict) else None, 'object': obj if parsed else {}}


def main():
    sources = [
        load('system_center', SYSTEM),
        load('onchain_center', ONCHAIN),
        load('risk_center', RISK),
        load('panel_public_bridge_status', BRIDGE_STATUS),
    ]
    checks = [
        {'name': s['name'] + '_exists_parse_ok', 'ok': s['exists'] and s['json_parse_ok'], 'decision': s['decision']} for s in sources
    ]
    system_ok = sources[0]['decision'] == 'SYSTEM_CENTER_READY'
    onchain_ok = sources[1]['decision'] == 'ONCHAIN_CENTER_READY_LOOKUP_ONLY'
    risk_ok = sources[2]['decision'] == 'RISK_CENTER_READY_PREVIEW_PLUS_LOOKUP_ONLY'
    bridge_ok = sources[3]['decision'] == 'PANEL_PUBLIC_BRIDGE_APPLIED'
    checks += [
        {'name': 'system_center_ready', 'ok': system_ok},
        {'name': 'onchain_center_lookup_ready', 'ok': onchain_ok},
        {'name': 'risk_center_preview_lookup_ready', 'ok': risk_ok},
        {'name': 'public_bridge_applied', 'ok': bridge_ok}
    ]
    ready_count = sum(1 for c in checks if c['ok'])
    decision = 'COMMAND_CENTER_READY_DISPLAY_ONLY' if all(c['ok'] for c in checks) else 'COMMAND_CENTER_PARTIAL_OR_NEEDS_REVIEW'
    severity = 'GREEN' if decision == 'COMMAND_CENTER_READY_DISPLAY_ONLY' else 'YELLOW'

    model = {
        'stage': 'N16D_COMMAND_CENTER_LIVE_PRODUCER',
        'generated_at_utc': now(),
        'producer': 'tools/command_center_live_producer_v1.py',
        'decision': decision,
        'severity': severity,
        'data_freshness_sec': 0,
        'authority': {
            'trade': False,
            'wallet_signing': False,
            'provider_call_from_browser': False,
            'policy_apply': False,
            'paper_trade_write': False
        },
        'source_count': sum(1 for s in sources if s['exists'] and s['json_parse_ok']),
        'items': [{
            'key': 'command_center',
            'label': 'Komuta Merkezi',
            'status': decision,
            'severity': severity,
            'ready_count': ready_count,
            'total_checks': len(checks),
            'checks': checks,
            'source_decisions': {s['name']: s['decision'] for s in sources},
            'summary': 'System, Onchain, Risk and Public Bridge are aggregated into command view. Display-only; no trade/wallet/provider authority.'
        }]
    }
    atomic_write(TARGET, model)
    atomic_write(OUT, model)
    print('FINAL_GATE=PASS_N16D_COMMAND_CENTER_LIVE_PRODUCER')
    print('DECISION=' + decision)
    print('SEVERITY=' + severity)
    print('JSON=' + str(OUT.relative_to(ROOT)))
    print('TARGET=' + str(TARGET.relative_to(ROOT)))

if __name__ == '__main__':
    main()
