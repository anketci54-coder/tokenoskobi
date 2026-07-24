#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/root/tokenoskobi_clean_v1"
SELF_REL="tools/tokenoskobi_dynamic_position_sizing_policy_sync.sh"
cd "$ROOT"

git fetch origin main >/dev/null
BRANCH="$(git branch --show-current)"
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git rev-parse origin/main)"
[[ "$BRANCH" == "main" ]] || { echo "BLOCKED=BRANCH_NOT_MAIN:$BRANCH"; exit 1; }
[[ "$LOCAL_HEAD" == "$REMOTE_HEAD" ]] || { echo "BLOCKED=LOCAL_REMOTE_DIVERGED:$LOCAL_HEAD:$REMOTE_HEAD"; exit 1; }
[[ -z "$(git status --short)" ]] || { echo "BLOCKED=WORKTREE_NOT_CLEAN"; git status --short; exit 1; }

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/tokenoskobi_dynamic_position_sizing_backup_${TS}.tar.gz"
tar -czf "$BACKUP" \
  02_MANIFESTO.md 03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md \
  06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json \
  reports/LATEST_TK_AI_HANDOFF.md "$SELF_REL"
echo "BACKUP=$BACKUP"

COMMITTED=0
rollback() {
  rc=$?
  if [[ $rc -ne 0 && $COMMITTED -eq 0 ]]; then
    tar -xzf "$BACKUP" -C "$ROOT"
    git reset --quiet
    echo "ROLLBACK=COMPLETED"
  elif [[ $rc -ne 0 ]]; then
    echo "ROLLBACK=SKIPPED_AFTER_LOCAL_COMMIT"
  fi
  exit $rc
}
trap rollback ERR

python3 <<'PY'
from __future__ import annotations

import copy
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
NOW = datetime.now(timezone.utc).isoformat()
NEXT = 'PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION'
POLICY_ID = 'DYNAMIC_WALLET_OPPORTUNITY_RISK_BASED_POSITION_SIZING'


def read_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))


def atomic_text(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(text)
            if not text.endswith('\n'):
                handle.write('\n')
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_json(rel: str, value) -> None:
    atomic_text(rel, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def marker_upsert(rel: str, begin: str, end: str, body: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    block = f'{begin}\n{body.strip()}\n{end}'
    if begin in text and end in text:
        start = text.index(begin)
        finish = text.index(end, start) + len(end)
        text = text[:start] + block + text[finish:]
    else:
        lines = text.splitlines()
        text = (lines[0] + '\n\n' + block + '\n\n' + '\n'.join(lines[1:]).lstrip('\n')) if lines else block
    atomic_text(rel, text)


def replace_current_policy_tokens(value):
    if isinstance(value, dict):
        return {k: replace_current_policy_tokens(v) for k, v in value.items()}
    if isinstance(value, list):
        return [replace_current_policy_tokens(v) for v in value]
    if isinstance(value, str):
        replacements = {
            '1_TO_2': 'DYNAMIC_WALLET_OPPORTUNITY_RISK_BASED',
            '1-2_USD': 'DYNAMIC_WALLET_OPPORTUNITY_RISK_BASED',
            'FIXED_1_TO_2_USD': 'DYNAMIC_WALLET_OPPORTUNITY_RISK_BASED',
        }
        return replacements.get(value, value)
    return value


policy = {
    'id': POLICY_ID,
    'status': 'LOCKED_PLAN_ONLY_AUTHORITY_UNCHANGED',
    'fixed_usd_cap': False,
    'permanent_1_to_2_usd_cap': False,
    'initial_probe': {
        'optional': True,
        'usd_range': '1_TO_2',
        'role': 'OPTIONAL_EARLY_CANARY_PROBE_ONLY_NOT_A_SYSTEM_LIMIT',
        'automatic_extension': False,
    },
    'position_size_owner': 'POSITION_SIZING_ENGINE_INSIDE_HUMAN_DEFINED_POLICY_ENVELOPE',
    'primary_inputs': [
        'AVAILABLE_CANARY_WALLET_BALANCE',
        'OPPORTUNITY_QUALITY_AND_CONFIDENCE',
        'RISK_ENGINE_DECISION',
        'LIQUIDITY_DEPTH',
        'EXPECTED_PRICE_IMPACT',
        'EXPECTED_SLIPPAGE',
        'GAS_AND_TOTAL_EXECUTION_COST_RATIO',
        'TOKEN_TAX_OR_TRANSFER_RESTRICTION',
        'OPEN_EXPOSURE',
        'DAILY_REMAINING_RISK_BUDGET',
        'CURRENT_DRAWDOWN',
        'LEARNING_AND_VALIDATION_STAGE',
    ],
    'hard_bounds': [
        'CANNOT_EXCEED_AVAILABLE_CANARY_WALLET_BALANCE',
        'CANNOT_EXCEED_HUMAN_DEFINED_MAX_PER_TRADE',
        'CANNOT_EXCEED_HUMAN_DEFINED_DAILY_LOSS_BUDGET',
        'CANNOT_EXCEED_LIQUIDITY_AND_PRICE_IMPACT_LIMIT',
        'CANNOT_BYPASS_RISK_ENGINE_VETO',
        'CANNOT_AUTO_INCREASE_AFTER_SINGLE_WIN',
        'CANNOT_USE_CORE_OR_RESERVE_WALLET_BALANCE',
    ],
    'scaling_rule': 'SIZE_MAY_INCREASE_OR_DECREASE_FROM_MEASURED_WALLET_CAPACITY_OPPORTUNITY_QUALITY_LIQUIDITY_COST_AND_OUTCOME_EVIDENCE',
    'human_controls': [
        'MAX_PER_TRADE',
        'MAX_DAILY_LOSS',
        'MAX_TOTAL_OPEN_EXPOSURE',
        'CANARY_WALLET_FUNDING',
        'POLICY_ENVELOPE_AND_VETO',
    ],
    'authority_note': 'THIS_POLICY_DOES_NOT_ENABLE_PAPER_OR_LIVE_TRADE_WALLET_SIGNING_OR_ORDER_AUTHORITY',
    'recorded_at_utc': NOW,
}

manifesto_body = '''## DYNAMIC POSITION SIZING CONSTITUTION

- Tokenoskobi kalıcı olarak 1–2 USD işlem büyüklüğüyle sınırlandırılamaz.
- 1–2 USD yalnız ilk canlı doğrulamalarda kullanılabilecek isteğe bağlı küçük canary probe değeridir; sistem tavanı değildir.
- İşlem büyüklüğü, insanın tanımladığı politika zarfı içinde kullanılabilir canary wallet bakiyesi, fırsat kalitesi, Risk Engine kararı, likidite, fiyat etkisi, slippage, gas/toplam maliyet, açık risk, günlük kalan risk bütçesi, drawdown ve ölçülmüş öğrenme kanıtıyla dinamik belirlenir.
- Wallet bakiyesinin tamamı işlem sermayesi kabul edilemez; yalnız insan tarafından canary wallet’a ayrılmış bakiye kullanılabilir.
- Tek kazanç otomatik büyütme yetkisi üretmez. Ölçek büyümesi ancak yeterli kapanmış işlem, maliyet-tam sonuç ve risk sınırlarıyla yapılır.
- Risk Engine veto, insanın maksimum işlem/günlük zarar/toplam açık risk sınırları ve likidite-price-impact limitleri aşılmaz.
- Bu politika tek başına paper veya live trade, wallet, signing, order ya da broadcast yetkisi açmaz.'''
marker_upsert('02_MANIFESTO.md', '<!-- DYNAMIC_POSITION_SIZING_CONSTITUTION:BEGIN -->', '<!-- DYNAMIC_POSITION_SIZING_CONSTITUTION:END -->', manifesto_body)

boot = replace_current_policy_tokens(read_json('PROJECT_BOOT.json'))
boot['boot_version'] = '3.6'
boot['dynamic_position_sizing_contract'] = copy.deepcopy(policy)
boot.setdefault('assistant_behavior_rules', {})['do_not_treat_1_to_2_usd_as_permanent_system_cap'] = True
boot['assistant_behavior_rules']['position_size_must_follow_wallet_opportunity_risk_liquidity_and_human_policy'] = True
boot['last_action'] = 'DYNAMIC_POSITION_SIZING_POLICY_CORRECTION_SYNC'
boot['next_safe_step'] = NEXT
boot['updated_at'] = NOW
boot['updated_at_utc'] = NOW
atomic_json('PROJECT_BOOT.json', boot)

runtime = replace_current_policy_tokens(read_json('PROJECT_RUNTIME.json'))
runtime['dynamic_position_sizing_policy'] = copy.deepcopy(policy)
runtime['live_canary_trade_size_policy'] = POLICY_ID
runtime['live_canary_fixed_trade_usd'] = False
runtime['live_canary_initial_probe_usd'] = 'OPTIONAL_1_TO_2_NOT_PERMANENT_CAP'
runtime['last_action'] = 'DYNAMIC_POSITION_SIZING_POLICY_CORRECTION_SYNC'
runtime['last_result'] = 'FIXED_1_TO_2_USD_CAP_REMOVED_DYNAMIC_POLICY_LOCKED'
runtime['next_safe_step'] = NEXT
runtime['updated_at_utc'] = NOW
pointer = runtime.setdefault('canonical_runtime_pointer', {})
pointer['dynamic_position_sizing_policy'] = copy.deepcopy(policy)
pointer['live_canary_fixed_trade_usd'] = False
pointer['next_safe_step'] = NEXT
atomic_json('PROJECT_RUNTIME.json', runtime)

roadmap = replace_current_policy_tokens(read_json('data/tokenoskobi_v1_v8_master_era_roadmap.json'))
roadmap['dynamic_position_sizing_policy'] = copy.deepcopy(policy)
roadmap['live_canary_trade_size_policy'] = POLICY_ID
roadmap.setdefault('current_direction', {})['live_canary_trade_size_policy'] = POLICY_ID
roadmap['current_direction']['fixed_usd_cap'] = False
roadmap['current_direction']['next_safe_step'] = NEXT
roadmap['current_direction']['updated_at_utc'] = NOW
roadmap['updated_at_utc'] = NOW
atomic_json('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

roadmap_body = '''## Dinamik İşlem Büyüklüğü Düzeltmesi

`LIVE_CANARY_TRADE_USD=1_TO_2` kalıcı sistem sınırı değildir ve bu anlamıyla yürürlükten kaldırılmıştır.

```text
POSITION_SIZE
  = human policy envelope içinde
    kullanılabilir canary wallet bakiyesi
    + fırsat kalitesi ve confidence
    + Risk Engine kararı
    + likidite / price impact / slippage
    + gas, fee, tax ve toplam maliyet oranı
    + açık risk / günlük kalan risk bütçesi / drawdown
    + ölçülmüş kapanmış işlem ve öğrenme kanıtı
```

- 1–2 USD yalnız isteğe bağlı ilk canary probe olabilir.
- Sistem fırsat ve cüzdan koşullarına göre daha düşük veya daha yüksek pozisyon önerebilir.
- Nihai üst sınırlar kullanıcı tarafından belirlenen işlem başı maksimum, günlük zarar ve toplam açık risk zarfıdır.
- Risk Engine veto aşılamaz.
- Bu düzeltme şu anda live authority açmaz; mevcut ürün tamamlama ve 1 Eylül hedef sırası değişmez.'''
marker_upsert('03_ROADMAP.md', '<!-- DYNAMIC_POSITION_SIZING_ROADMAP:BEGIN -->', '<!-- DYNAMIC_POSITION_SIZING_ROADMAP:END -->', roadmap_body)

almanac_body = f'''## DYNAMIC POSITION SIZING POLICY CORRECTION

- Timestamp UTC: `{NOW}`
- Status: `CORRECTION_RECORDED_AND_POLICY_LOCKED`
- Previous wording: `1_TO_2_USD_LIVE_CANARY`
- Correct interpretation: `OPTIONAL_INITIAL_PROBE_ONLY`
- Permanent fixed USD cap: `false`
- New policy: `{POLICY_ID}`
- Position basis: `CANARY_WALLET_BALANCE + OPPORTUNITY + RISK + LIQUIDITY + COST + DRAWDOWN + LEARNING_EVIDENCE`
- Human policy controls: `MAX_PER_TRADE + MAX_DAILY_LOSS + MAX_TOTAL_OPEN_EXPOSURE + CANARY_WALLET_FUNDING`
- Authority change: `NONE`
- Paper runtime: `DISABLED`
- Live trade: `DISABLED`
- Real financial authority: `0`
- Next safe step: `{NEXT}`'''
marker_upsert('04_ALMANAC.md', '<!-- DYNAMIC_POSITION_SIZING_CORRECTION:BEGIN -->', '<!-- DYNAMIC_POSITION_SIZING_CORRECTION:END -->', almanac_body)

atlas_body = '''## DYNAMIC POSITION SIZING FLOW

```text
CANARY WALLET AVAILABLE BALANCE
  + OPPORTUNITY QUALITY / CONFIDENCE
  + RISK ENGINE ALLOW / WAIT / BLOCK / REVIEW
  + LIQUIDITY DEPTH / PRICE IMPACT / SLIPPAGE
  + GAS / FEE / TAX / TOTAL COST RATIO
  + OPEN EXPOSURE / DAILY REMAINING RISK / DRAWDOWN
  + CLOSED-TRADE LEARNING EVIDENCE
  -> POSITION SIZING ENGINE
  -> HUMAN POLICY ENVELOPE
       -> MAX PER TRADE
       -> MAX DAILY LOSS
       -> MAX TOTAL OPEN EXPOSURE
  -> HUMAN APPROVAL / VETO
```

- 1–2 USD is an optional initial probe, not a permanent cap.
- Core/reserve wallet balance is never treated as available trade capital.
- A single win cannot auto-scale capital.
- Risk Engine veto and liquidity/cost limits are absolute.
- No paper/live/wallet/signing/order authority is created by sizing logic.'''
marker_upsert('05_ATLAS.md', '<!-- DYNAMIC_POSITION_SIZING_FLOW:BEGIN -->', '<!-- DYNAMIC_POSITION_SIZING_FLOW:END -->', atlas_body)

master = (ROOT / '06_PROJECT_MASTER_STATE.md').read_text(encoding='utf-8')
for old in ['LIVE_CANARY_TRADE_USD=1_TO_2', 'LIVE_CANARY_TRADE_USD=DYNAMIC_WALLET_OPPORTUNITY_RISK_BASED']:
    master = master.replace(old, 'LIVE_CANARY_TRADE_SIZE_POLICY=DYNAMIC_WALLET_OPPORTUNITY_RISK_BASED')
if 'LIVE_CANARY_FIXED_USD_CAP=false' not in master:
    master += '\nLIVE_CANARY_FIXED_USD_CAP=false\nLIVE_CANARY_INITIAL_1_TO_2_USD=OPTIONAL_PROBE_ONLY\nPOSITION_SIZE_BASIS=CANARY_WALLET_BALANCE_OPPORTUNITY_RISK_LIQUIDITY_COST_DRAWDOWN_LEARNING\n'
atomic_text('06_PROJECT_MASTER_STATE.md', master)

handoff = (ROOT / '07_PROJECT_HANDOFF.md').read_text(encoding='utf-8')
handoff = handoff.replace('LIVE_CANARY_TRADE_USD=1_TO_2', 'LIVE_CANARY_TRADE_SIZE_POLICY=DYNAMIC_WALLET_OPPORTUNITY_RISK_BASED')
handoff += '''

## İşlem Büyüklüğü Düzeltmesi

1–2 USD kalıcı sistem sınırı değildir. Yalnız isteğe bağlı ilk canary probe olabilir. Gerçek işlem büyüklüğü canary wallet bakiyesi, fırsat kalitesi, risk, likidite, slippage, fiyat etkisi, toplam maliyet, drawdown ve kapanmış işlem öğrenme kanıtına göre dinamik belirlenir. Kullanıcı maksimum işlem, günlük zarar ve toplam açık risk sınırlarını belirler. Bu kayıt mevcut authority durumunu değiştirmez.
'''
atomic_text('07_PROJECT_HANDOFF.md', handoff)

history = read_json('PROJECT_HISTORY.json')
event_id = 'DYNAMIC_POSITION_SIZING_POLICY_CORRECTION_V1'
history['events'] = [item for item in history.setdefault('events', []) if item.get('event_id') != event_id]
history['events'].append({
    'event_id': event_id,
    'event': 'FIXED_1_TO_2_USD_CAP_REMOVED',
    'timestamp_utc': NOW,
    'status': 'DYNAMIC_POSITION_SIZING_POLICY_LOCKED',
    'previous_policy': '1_TO_2_USD_WAS_RECORDED_AS_LIVE_CANARY_SIZE',
    'corrected_policy': POLICY_ID,
    'initial_1_to_2_usd_role': 'OPTIONAL_EARLY_PROBE_ONLY',
    'position_basis': policy['primary_inputs'],
    'authority_change': False,
    'paper_runtime': 'DISABLED',
    'live_trade': 'DISABLED',
    'real_financial_authority': 0,
    'next_safe_step': NEXT,
})
history['updated_at_utc'] = NOW
atomic_json('PROJECT_HISTORY.json', history)

latest = (ROOT / 'reports/LATEST_TK_AI_HANDOFF.md').read_text(encoding='utf-8')
latest = latest.replace('LIVE_CANARY_TRADE_USD=1_TO_2', 'LIVE_CANARY_TRADE_SIZE_POLICY=DYNAMIC_WALLET_OPPORTUNITY_RISK_BASED')
latest += '''

POSITION_SIZING_CORRECTION=1_TO_2_USD_IS_OPTIONAL_INITIAL_PROBE_NOT_PERMANENT_CAP
POSITION_SIZE_INPUTS=CANARY_WALLET_BALANCE_OPPORTUNITY_RISK_LIQUIDITY_COST_DRAWDOWN_LEARNING
CURRENT_AUTHORITY_CHANGE=NONE
'''
atomic_text('reports/LATEST_TK_AI_HANDOFF.md', latest)

machine = replace_current_policy_tokens(read_json('data/control/latest_tk_machine_state.json'))
machine['dynamic_position_sizing_policy'] = copy.deepcopy(policy)
machine['live_canary_trade_size_policy'] = POLICY_ID
machine['live_canary_fixed_trade_usd'] = False
machine['live_canary_initial_probe_usd'] = 'OPTIONAL_1_TO_2_NOT_PERMANENT_CAP'
machine['next_safe_step'] = NEXT
machine['updated_at_utc'] = NOW
if 'boot_json' in machine:
    machine['boot_json'] = copy.deepcopy(boot)
if 'runtime_json' in machine:
    machine['runtime_json'] = copy.deepcopy(runtime)
atomic_json('data/control/latest_tk_machine_state.json', machine)

print('DYNAMIC_POSITION_SIZING_POLICY_WRITE=COMPLETED')
PY

python3 <<'PY'
import json
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
POLICY_ID = 'DYNAMIC_WALLET_OPPORTUNITY_RISK_BASED_POSITION_SIZING'
NEXT = 'PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION'
load = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8'))
boot = load('PROJECT_BOOT.json')
runtime = load('PROJECT_RUNTIME.json')
roadmap = load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
history = load('PROJECT_HISTORY.json')
machine = load('data/control/latest_tk_machine_state.json')

assert boot['dynamic_position_sizing_contract']['id'] == POLICY_ID
assert runtime['dynamic_position_sizing_policy']['fixed_usd_cap'] is False
assert runtime['live_canary_fixed_trade_usd'] is False
assert runtime['live_canary_initial_probe_usd'] == 'OPTIONAL_1_TO_2_NOT_PERMANENT_CAP'
assert roadmap['dynamic_position_sizing_policy']['id'] == POLICY_ID
assert roadmap['current_direction']['fixed_usd_cap'] is False
assert machine['live_canary_fixed_trade_usd'] is False
assert any(item.get('event_id') == 'DYNAMIC_POSITION_SIZING_POLICY_CORRECTION_V1' for item in history['events'])
assert runtime['next_safe_step'] == NEXT

authority = runtime['authority']
assert str(authority['live_trade']).upper() == 'DISABLED'
assert str(authority['paper_trade']).upper().startswith('DISABLED')
assert int(authority['real_order_authority']) == 0
assert int(authority['real_signing_authority']) == 0
assert int(authority['real_trade_authority']) == 0
assert int(authority['real_wallet_authority']) == 0

for rel, token in [
    ('02_MANIFESTO.md', '<!-- DYNAMIC_POSITION_SIZING_CONSTITUTION:BEGIN -->'),
    ('03_ROADMAP.md', '<!-- DYNAMIC_POSITION_SIZING_ROADMAP:BEGIN -->'),
    ('04_ALMANAC.md', '<!-- DYNAMIC_POSITION_SIZING_CORRECTION:BEGIN -->'),
    ('05_ATLAS.md', '<!-- DYNAMIC_POSITION_SIZING_FLOW:BEGIN -->'),
    ('06_PROJECT_MASTER_STATE.md', 'LIVE_CANARY_FIXED_USD_CAP=false'),
    ('07_PROJECT_HANDOFF.md', '1–2 USD kalıcı sistem sınırı değildir'),
    ('reports/LATEST_TK_AI_HANDOFF.md', 'POSITION_SIZING_CORRECTION='),
]:
    assert token in (ROOT / rel).read_text(encoding='utf-8'), rel

print('DYNAMIC_POSITION_SIZING_POLICY=VERIFIED')
print('FIXED_1_TO_2_USD_CAP=REMOVED_VERIFIED')
print('OPTIONAL_INITIAL_1_TO_2_USD_PROBE=PRESERVED')
print('CURRENT_AUTHORITY_BOUNDARIES=UNCHANGED_VERIFIED')
PY

rm -f "$SELF_REL"

git diff --check
git add -A -- \
  02_MANIFESTO.md 03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md \
  06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json "$SELF_REL"
git add -f reports/LATEST_TK_AI_HANDOFF.md

git diff --cached --stat
git commit -m "Product: replace fixed canary size with dynamic sizing"
COMMITTED=1
git push origin main

FINAL_HEAD="$(git rev-parse HEAD)"
REMOTE_FINAL="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
[[ "$FINAL_HEAD" == "$REMOTE_FINAL" ]] || { echo "BLOCKED=REMOTE_VERIFY_FAILED:$FINAL_HEAD:$REMOTE_FINAL"; exit 1; }
[[ -z "$(git status --short)" ]] || { echo "BLOCKED=WORKTREE_NOT_CLEAN_AFTER_PUSH"; git status --short; exit 1; }

trap - ERR

echo "DYNAMIC_POSITION_SIZING_POLICY=VERIFIED_GITHUB_SEALED"
echo "FIXED_1_TO_2_USD_CAP=REMOVED"
echo "INITIAL_1_TO_2_USD=OPTIONAL_CANARY_PROBE_ONLY"
echo "POSITION_SIZE_BASIS=CANARY_WALLET_BALANCE_OPPORTUNITY_RISK_LIQUIDITY_COST_DRAWDOWN_LEARNING"
echo "HUMAN_CONTROLS=MAX_PER_TRADE_MAX_DAILY_LOSS_MAX_TOTAL_OPEN_EXPOSURE_CANARY_WALLET_FUNDING"
echo "AUTHORITY_CHANGE=NONE"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REAL_FINANCIAL_AUTHORITY=0"
echo "NEXT_SAFE_STEP=PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$FINAL_HEAD"
