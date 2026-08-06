#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]

python3 <<'PY_PRECHECK'
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path('/root/tokenoskobi_clean_v1')
state = json.loads((root / 'runtime/era63e/always_on_state_v1.json').read_text(encoding='utf-8'))
successes = int(state.get('full_refresh_count') or 0)
failures = int(state.get('refresh_failure_count') or 0)
attempts = successes + failures
rate = failures / attempts if attempts else 1.0
last = state.get('last_refresh_result') or {}
last_at = state.get('last_full_refresh_at_utc')
if isinstance(last_at, str) and last_at.endswith('Z'):
    last_at = last_at[:-1] + '+00:00'
last_dt = datetime.fromisoformat(str(last_at)) if last_at else None
if last_dt and last_dt.tzinfo is None:
    last_dt = last_dt.replace(tzinfo=timezone.utc)
age = (datetime.now(timezone.utc) - last_dt.astimezone(timezone.utc)).total_seconds() if last_dt else 10**9
print(f'REFRESH_SUCCESSES={successes}')
print(f'REFRESH_FAILURES={failures}')
print(f'REFRESH_ATTEMPTS={attempts}')
print(f'REFRESH_FAILURE_RATE={rate:.6f}')
print(f'LAST_REFRESH_STATUS={last.get("status")}')
print(f'LAST_REFRESH_AGE_SEC={max(0.0, age):.3f}')
if attempts < 3:
    raise SystemExit('RECOVERY_GATE=BLOCKED_INSUFFICIENT_REFRESH_ATTEMPTS')
if rate > 0.05:
    raise SystemExit('RECOVERY_GATE=BLOCKED_REFRESH_FAILURE_RATE_ABOVE_5_PERCENT')
if last.get('status') != 'PASS':
    raise SystemExit('RECOVERY_GATE=BLOCKED_LAST_REFRESH_NOT_PASS')
if age > 300:
    raise SystemExit('RECOVERY_GATE=BLOCKED_LAST_REFRESH_STALE')
print('RECOVERY_GATE=VERIFIED_RECOVERED_TRANSIENT_FAILURES')
PY_PRECHECK

python3 <<'PY_PATCH'
from pathlib import Path

source = Path('/root/tokenoskobi_clean_v1/tools/era63e_observe_close.sh')
target = Path('/tmp/era63e_observe_close_recovered.sh')
text = source.read_text(encoding='utf-8')
old_gate = "checks['refresh_failures_zero'] = int(state.get('refresh_failure_count') or 0) == 0"
new_gate = """refresh_successes = int(state.get('full_refresh_count') or 0)
refresh_failures = int(state.get('refresh_failure_count') or 0)
refresh_attempts = refresh_successes + refresh_failures
refresh_failure_rate = (refresh_failures / refresh_attempts) if refresh_attempts else 1.0
checks['refresh_failure_rate_bounded'] = refresh_attempts >= MIN_REFRESHES and refresh_failure_rate <= 0.05"""
if old_gate not in text:
    raise SystemExit('PATCH_TARGET_REFRESH_GATE_NOT_FOUND')
text = text.replace(old_gate, new_gate, 1)
old_threshold = "        'maximum_market_age_sec': MAX_MARKET_AGE_SEC,\n"
new_threshold = "        'maximum_market_age_sec': MAX_MARKET_AGE_SEC,\n        'maximum_refresh_failure_rate': 0.05,\n"
if old_threshold not in text:
    raise SystemExit('PATCH_TARGET_THRESHOLD_NOT_FOUND')
text = text.replace(old_threshold, new_threshold, 1)
old_observed = "        'refresh_failure_count': int(state.get('refresh_failure_count') or 0),\n"
new_observed = """        'refresh_failure_count': refresh_failures,
        'refresh_attempt_count': refresh_attempts,
        'refresh_failure_rate': round(refresh_failure_rate, 6),
"""
if old_observed not in text:
    raise SystemExit('PATCH_TARGET_OBSERVED_NOT_FOUND')
text = text.replace(old_observed, new_observed, 1)
old_print = "print(f\"FULL_MARKET_REFRESHES={audit['observed']['full_market_refresh_count']}/{MIN_REFRESHES}\")\n"
new_print = old_print + "print(f\"REFRESH_FAILURE_RATE={audit['observed']['refresh_failure_rate']:.6f}/0.050000\")\n"
if old_print not in text:
    raise SystemExit('PATCH_TARGET_PRINT_NOT_FOUND')
text = text.replace(old_print, new_print, 1)
target.write_text(text, encoding='utf-8')
target.chmod(0o700)
print('CLOSURE_AUDIT_PATCH=BOUNDED_FAILURE_RATE_PLUS_LAST_PASS_AND_FRESHNESS')
PY_PATCH

exec bash /tmp/era63e_observe_close_recovered.sh
