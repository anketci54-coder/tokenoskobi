#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SERVICE="tokenoskobi-era63e-always-on-market.service"
TIMER="tokenoskobi-era63d-market-technical.timer"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

echo "PRECHECK=VERIFIED"

python3 <<'PY_STATE'
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path('/root/tokenoskobi_clean_v1')
state = json.loads((root / 'runtime/era63e/always_on_state_v1.json').read_text(encoding='utf-8'))
health = json.loads((root / 'runtime/era63e/health_v1.json').read_text(encoding='utf-8'))
successes = int(state.get('full_refresh_count') or 0)
failures = int(state.get('refresh_failure_count') or 0)
attempts = successes + failures
rate = failures / attempts if attempts else 1.0
last = state.get('last_refresh_result') or {}
print(f'SERVICE_STATE={state.get("status")}')
print(f'BLOCK_EVENTS={int(state.get("block_event_count") or 0)}')
print(f'REFRESH_SUCCESSES={successes}')
print(f'REFRESH_FAILURES={failures}')
print(f'REFRESH_ATTEMPTS={attempts}')
print(f'REFRESH_FAILURE_RATE={rate:.6f}')
print(f'LAST_REFRESH_REASON={state.get("last_refresh_reason")}')
print(f'LAST_REFRESH_RESULT={json.dumps(last, ensure_ascii=False, sort_keys=True)}')
print(f'LAST_RUNTIME_ERROR={state.get("last_runtime_error")}')
print(f'HEALTH_STATUS={health.get("status")}')
print(f'RPC_ENDPOINT={state.get("rpc_endpoint")}')
authority = state.get('authority') or {}
assert authority.get('observation_runtime') is True
for key in ('paper_runtime', 'paper_position_write', 'real_trade', 'wallet', 'signing', 'real_order', 'broadcast', 'system_may_expand_policy'):
    assert authority.get(key) is False, key
print('AUTHORITY_BOUNDARY=VERIFIED_READ_ONLY')
PY_STATE

systemctl show "$SERVICE" --no-pager \
  --property=ActiveState,SubState,UnitFileState,MainPID,NRestarts,ActiveEnterTimestamp,ExecMainStatus \
  | sed '/^$/d'

python3 <<'PY_PROBE'
from __future__ import annotations

import copy
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import era63d_market_technical_runtime_v1 as module

base = json.loads((ROOT / 'config/era63d_market_technical_runtime_v1.json').read_text(encoding='utf-8'))
config = copy.deepcopy(base)
provider = config['provider']
provider['max_pools'] = 1
provider['min_successful_pools'] = 1
provider['request_timeout_sec'] = min(12, int(provider.get('request_timeout_sec', 12)))
provider['retries'] = 1
provider['minimum_request_interval_sec'] = max(1.1, float(provider.get('minimum_request_interval_sec', 1.1)))

attempt_total = 8
successes = 0
failures = 0
classes: Counter[str] = Counter()
per_pool_errors: Counter[str] = Counter()

def classify(text: str) -> str:
    upper = text.upper()
    if 'HTTP_429' in upper or 'STATUS:429' in upper:
        return 'HTTP_429_RATE_LIMIT'
    if re.search(r'HTTP_5\d\d', upper) or 'STATUS:5' in upper:
        return 'HTTP_5XX_PROVIDER'
    if 'TIMED OUT' in upper or 'TIMEOUT' in upper:
        return 'TIMEOUT'
    if 'TEMPORARY FAILURE' in upper or 'NAME OR SERVICE NOT KNOWN' in upper or 'DNS' in upper:
        return 'DNS_OR_NETWORK'
    if 'OHLCV_INSUFFICIENT' in upper or 'OHLCV_LIST_MISSING' in upper:
        return 'OHLCV_DATA_QUALITY'
    if 'NO_VALID_BSC_POOL_CANDIDATES' in upper:
        return 'DISCOVERY_EMPTY'
    if 'SUCCESSFUL_POOL_COUNT_TOO_LOW' in upper:
        return 'POOL_REFRESH_FAILED'
    return 'OTHER'

print(f'DIRECT_PROBE_ATTEMPTS={attempt_total}')
for index in range(1, attempt_total + 1):
    started = time.monotonic()
    try:
        snapshot = module.run_runtime(config)
        elapsed = time.monotonic() - started
        successes += 1
        errors = snapshot.get('errors') or []
        for row in errors:
            error = str((row or {}).get('error') or '')
            if error:
                per_pool_errors[classify(error)] += 1
        print(
            f'PROBE_{index}=OK:'
            f'elapsed_sec={elapsed:.3f}:'
            f'requests={int(snapshot.get("request_count") or 0)}:'
            f'candidates={int(snapshot.get("candidate_count") or 0)}:'
            f'pools={int(snapshot.get("successful_pool_count") or 0)}:'
            f'isolated_pool_errors={len(errors)}'
        )
    except Exception as exc:
        elapsed = time.monotonic() - started
        failures += 1
        text = f'{type(exc).__name__}:{exc}'
        category = classify(text)
        classes[category] += 1
        print(f'PROBE_{index}=FAIL:elapsed_sec={elapsed:.3f}:class={category}:error={text[:900]}')
    if index < attempt_total:
        time.sleep(5)

rate = failures / attempt_total
print(f'DIRECT_PROBE_SUCCESSES={successes}')
print(f'DIRECT_PROBE_FAILURES={failures}')
print(f'DIRECT_PROBE_FAILURE_RATE={rate:.6f}')
print('DIRECT_PROBE_FAILURE_CLASSES=' + json.dumps(dict(classes), sort_keys=True))
print('ISOLATED_POOL_ERROR_CLASSES=' + json.dumps(dict(per_pool_errors), sort_keys=True))

if classes.get('HTTP_429_RATE_LIMIT', 0):
    decision = 'RATE_LIMIT_CONFIRMED'
elif classes.get('HTTP_5XX_PROVIDER', 0):
    decision = 'PROVIDER_5XX_CONFIRMED'
elif classes.get('TIMEOUT', 0) or classes.get('DNS_OR_NETWORK', 0):
    decision = 'NETWORK_TRANSIENT_CONFIRMED'
elif classes.get('OHLCV_DATA_QUALITY', 0) or classes.get('DISCOVERY_EMPTY', 0) or classes.get('POOL_REFRESH_FAILED', 0):
    decision = 'PROVIDER_DATA_QUALITY_FAILURE_CONFIRMED'
elif failures:
    decision = 'UNCLASSIFIED_REFRESH_FAILURE_CONFIRMED'
else:
    decision = 'CURRENT_PROBES_CLEAN_HISTORICAL_FAILURE_CAUSE_NOT_RECORDED'
print(f'DIAGNOSTIC_DECISION={decision}')
print('CANONICAL_MUTATION=NONE')
print('SERVICE_MUTATION=NONE')
PY_PROBE

echo "SERVICE=ENABLED_ACTIVE_RESTART_ALWAYS"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "WORKTREE=CLEAN"
echo "HEAD=$(git rev-parse HEAD)"
echo "NEXT_SAFE_STEP=REPAIR_REFRESH_RELIABILITY_FROM_DIAGNOSTIC_EVIDENCE"
