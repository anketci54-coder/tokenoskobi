#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1
rm -f /tmp/pre_era57_phase9_timer_dependency_check_v1.json
exec timeout 90s env PYTHONDONTWRITEBYTECODE=1 python3 -u tools/phase9_dependency_check_fast_v1.py
