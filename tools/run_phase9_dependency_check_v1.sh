#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/root/tokenoskobi_clean_v1"
OUT="/tmp/pre_era57_phase9_timer_dependency_check_v1.json"
LOG="/tmp/pre_era57_phase9_timer_dependency_check_v1.log"

cd "$ROOT"
rm -f "$OUT" "$LOG"

set +e
PYTHONDONTWRITEBYTECODE=1 python3 tools/general_systemd_dependency_check_v1.py --timer tokenoskobi-phase9-observation-runtime.timer --service tokenoskobi-phase9-observation-runtime.service --script tools/phase9_commercial_observation_runtime.py --config data/phase9_commercial_observation_config.json --output-path "$OUT" --since "30 days ago" >"$LOG" 2>&1
RC=$?
set -e

cat "$LOG"
echo "CHECKER_RC=$RC"

if [[ -f "$OUT" ]]; then
  python3 - <<'PY'
import json
from pathlib import Path

path = Path('/tmp/pre_era57_phase9_timer_dependency_check_v1.json')
data = json.loads(path.read_text(encoding='utf-8'))
checks = data['checks']
print('DECISION=' + str(data['decision']))
print('BLOCKING_REASONS=' + ','.join(data.get('blocking_reasons') or []))
print('SYSTEMD_BINDING_PROVEN=' + str(checks['systemd_binding_proven']).lower())
print('SCRIPT_DECLARES_INERT=' + str(checks['script_declares_inert']).lower())
print('CONFIG_INERT=' + str(checks['config_inert']).lower())
print('ACTIVE_REPO_CONSUMERS=' + str(checks['active_repo_consumer_count']))
print('EXTERNAL_SYSTEMD_CONSUMERS=' + str(checks['external_systemd_consumer_count']))
print('EXTERNAL_FILESYSTEM_CONSUMERS=' + str(checks['external_filesystem_consumer_count']))
print('TIMER_ENABLED=' + str(checks['timer_enabled']).lower())
print('TIMER_ACTIVE=' + str(checks['timer_active']).lower())
PY
else
  echo "RESULT_JSON_MISSING=true"
fi

echo "PHASE9_TIMER_ACTIVE=$(systemctl show tokenoskobi-phase9-observation-runtime.timer -p ActiveState --value)"
echo "PHASE9_TIMER_ENABLED=$(systemctl show tokenoskobi-phase9-observation-runtime.timer -p UnitFileState --value)"
echo "PRODUCTION_MUTATION=false"
echo "SYSTEMD_MUTATION=false"
echo "ERA57_OPENED=false"

exit "$RC"
