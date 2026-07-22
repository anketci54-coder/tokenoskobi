#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import tempfile

from core.authority import evaluate_authority

ROOT = Path('/root/tokenoskobi_clean_v1')
PANEL_DATA = ROOT / 'active_panel_8096/current/data'
TARGET = PANEL_DATA / 'system_center_live_readmodel_v1.json'
OUT = ROOT / 'data/control/n16d_system_center_live_producer_result_v1.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def run(cmd):
    """Run a fixed argv command without a shell."""
    p = subprocess.run(
        cmd,
        shell=False,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        'cmd': list(cmd),
        'rc': p.returncode,
        'stdout': p.stdout[-4000:],
        'stderr': p.stderr[-2000:],
    }


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n16d_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        read_json(Path(tmp))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def file_ok(rel):
    p = PANEL_DATA / rel
    return p.exists() and p.is_file()


def enforce_publish_authority():
    decision = evaluate_authority({
        'operation_id': 'system-center-live-producer:publish',
        'operation_type': 'dashboard_active_mutation',
        'effects': {
            'writes_file': True,
            'mutates_dashboard_active': True,
        },
        'target': {
            'hot_path': True,
            'paths': [str(TARGET), str(OUT)],
        },
    })
    if decision.get('decision') != 'ALLOW':
        print('[AUTHORITY_DENIED] ' + json.dumps(decision, sort_keys=True), flush=True)
        return False
    return True


def main():
    # Fail closed before any active panel or control-artifact write.
    if not enforce_publish_authority():
        return 76

    sync = run(['tk', 'sync'])
    panel = run(['systemctl', 'is-active', 'tokenoskobi-active-panel-8096.service'])
    nginx = run(['systemctl', 'is-active', 'nginx'])
    https = run([
        'curl', '-ksS', '-o', '/tmp/n16d_panel_https.html', '-w', '%{http_code}',
        '--max-time', '8', 'https://panel.coinoskobi.com/'
    ])
    bridge = run([
        'curl', '-ksS', '-o', '/tmp/n16d_panel_bridge.json', '-w', '%{http_code}',
        '--max-time', '8',
        'https://panel.coinoskobi.com/data/backpressure_readmodel_refresh_cache.json'
    ])

    local_remote_synced = 'LOCAL :' in sync['stdout'] and 'REMOTE:' in sync['stdout'] and sync['rc'] == 0
    panel_active = panel['stdout'].strip() == 'active'
    nginx_active = nginx['stdout'].strip() == 'active'
    https_ok = https['stdout'].strip() == '200'
    bridge_ok = bridge['stdout'].strip() == '200'
    manifest_ok = file_ok('panel_live_manifest_v1.json')
    live_status_ok = file_ok('panel_live_status_v1.json')

    checks = [
        {'name': 'git_sync_command_ok', 'ok': sync['rc'] == 0},
        {'name': 'local_remote_sync_seen', 'ok': local_remote_synced},
        {'name': 'panel_service_active', 'ok': panel_active},
        {'name': 'nginx_active', 'ok': nginx_active},
        {'name': 'https_panel_root_200', 'ok': https_ok},
        {'name': 'https_bridge_json_200', 'ok': bridge_ok},
        {'name': 'panel_live_manifest_exists', 'ok': manifest_ok},
        {'name': 'panel_live_status_exists', 'ok': live_status_ok}
    ]
    decision = 'SYSTEM_CENTER_READY' if all(c['ok'] for c in checks) else 'SYSTEM_CENTER_PARTIAL_OR_NEEDS_REVIEW'

    model = {
        'stage': 'N16D_SYSTEM_CENTER_LIVE_PRODUCER',
        'generated_at_utc': now(),
        'producer': 'tools/system_center_live_producer_v1.py',
        'decision': decision,
        'data_freshness_sec': 0,
        'authority': {
            'trade': False,
            'wallet_signing': False,
            'provider_call_from_browser': False,
            'policy_apply': False,
            'paper_trade_write': False
        },
        'source_count': len(checks),
        'items': [{
            'key': 'system_center',
            'label': 'Sistem Kontrol Merkezi',
            'status': decision,
            'checks': checks,
            'commands': {
                'sync': {'rc': sync['rc'], 'stdout': sync['stdout']},
                'panel': {'rc': panel['rc'], 'stdout': panel['stdout']},
                'nginx': {'rc': nginx['rc'], 'stdout': nginx['stdout']},
                'https_code': https['stdout'].strip(),
                'bridge_code': bridge['stdout'].strip()
            }
        }]
    }
    atomic_write(TARGET, model)
    atomic_write(OUT, model)
    print('FINAL_GATE=PASS_N16D_SYSTEM_CENTER_LIVE_PRODUCER')
    print('DECISION=' + decision)
    print('JSON=' + str(OUT.relative_to(ROOT)))
    print('TARGET=' + str(TARGET.relative_to(ROOT)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
