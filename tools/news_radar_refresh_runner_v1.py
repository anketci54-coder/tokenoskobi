#!/usr/bin/env python3
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path('/root/tokenoskobi_clean_v1')
ORIGINAL = ROOT / 'tools' / 'news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py'
HELPER = ROOT / 'tools' / 'news_derived_layer_refresher_v1.py'
HOT = ROOT / 'tools' / 'post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.py'
DB = ROOT / 'data' / 'tokenoskobi_clean_v1.sqlite'

def run_hot():
    return subprocess.run(
        [sys.executable, str(HOT), '--runtime-refresh'],
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
    ).returncode

def main():
    if '--hot-only' in sys.argv[1:]:
        return run_hot()

    raw = subprocess.run([sys.executable, str(ORIGINAL)] + sys.argv[1:])
    if raw.returncode != 0:
        return raw.returncode

    derived = subprocess.run([
        sys.executable,
        str(HELPER),
        '--db-path',
        str(DB),
        '--write',
        '--stage',
        'NEWS_SYSTEMD_TIMER_DERIVED_REFRESH',
    ])
    if derived.returncode != 0:
        return derived.returncode

    return run_hot()

if __name__ == '__main__':
    raise SystemExit(main())
