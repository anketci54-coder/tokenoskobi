#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path('/root/tokenoskobi_clean_v1')
ORIGINAL = ROOT / 'tools' / 'news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py'
HELPER = ROOT / 'tools' / 'news_derived_layer_refresher_v1.py'
DB = ROOT / 'data' / 'tokenoskobi_clean_v1.sqlite'

def main():
    raw = subprocess.run([sys.executable, str(ORIGINAL)])
    if raw.returncode != 0:
        return raw.returncode
    derived = subprocess.run([sys.executable, str(HELPER), '--db-path', str(DB), '--write', '--stage', 'NEWS_SYSTEMD_TIMER_DERIVED_REFRESH'])
    return derived.returncode

if __name__ == '__main__':
    raise SystemExit(main())
