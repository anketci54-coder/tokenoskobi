#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/root/tokenoskobi_clean_v1"
SELF_REL="tools/tokenoskobi_deadline_20260901_live_canary_plan_sync.sh"
cd "$ROOT"

if [[ -f "$ROOT/FETCH_HEAD" ]] && ! git ls-files --error-unmatch FETCH_HEAD >/dev/null 2>&1; then
  rm -f "$ROOT/FETCH_HEAD"
  echo "ROOT_FETCH_HEAD_REMOVED=true"
fi

git fetch origin main >/dev/null
BRANCH="$(git branch --show-current)"
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git rev-parse origin/main)"
[[ "$BRANCH" == "main" ]] || { echo "BLOCKED=BRANCH_NOT_MAIN:$BRANCH"; exit 1; }
[[ "$LOCAL_HEAD" == "$REMOTE_HEAD" ]] || { echo "BLOCKED=LOCAL_REMOTE_DIVERGED:$LOCAL_HEAD:$REMOTE_HEAD"; exit 1; }
[[ -z "$(git status --short)" ]] || { echo "BLOCKED=WORKTREE_NOT_CLEAN"; git status --short; exit 1; }

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/tokenoskobi_deadline_20260901_backup_${TS}.tar.gz"
BACKUP_LIST="$(mktemp)"
trap 'rm -f "$BACKUP_LIST"' EXIT
for path in \
  02_MANIFESTO.md PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json 03_ROADMAP.md 04_ALMANAC.md \
  05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  reports/LATEST_TK_AI_HANDOFF.md data/control/latest_tk_machine_state.json "$SELF_REL"
  do
  [[ -e "$path" ]] && printf '%s\n' "$path" >> "$BACKUP_LIST"
done
tar -czf "$BACKUP" -T "$BACKUP_LIST"
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

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
NOW = datetime.now(timezone.utc).isoformat()
TARGET_DATE = '2026-09-01'
PROGRAM_ID = 'TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE'
NEXT = 'PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION'
STATUS = 'PRODUCT_COMPLETION_DEADLINE_LOCKED_2026_09_01'
HEAD_BEFORE = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def load(rel: str):
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


schedule = [
    {
        'order': 1,
        'window': '2026-07-25/2026-07-27',
        'id': NEXT,
        'deliverable': 'NEWS canlılığı, kesin panel URL/auth, Alchemy hibrit bağlantısı, onchain gecikmesi ve iç/dış güvenlik read-only doğrulaması',
        'completion_gate': 'Tek güncel gerçeklik tablosu ve kullanıcı kabulü',
    },
    {
        'order': 2,
        'window': '2026-07-28/2026-08-05',
        'id': 'PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET',
        'deliverable': 'Canlı BSC token giriş ekranı, gerçek karar paketi, 1m/5m/15m/1h/4h/1d online teknik analiz ve VERI_YETERSIZ davranışı',
        'completion_gate': 'Telefon üzerinden canlı URL kullanıcı kabulü',
    },
    {
        'order': 3,
        'window': '2026-08-06/2026-08-10',
        'id': 'PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING',
        'deliverable': 'İnsan kararı, append-only geçmiş, tekrar açılabilir kanıt paketi ve sonuç takibi',
        'completion_gate': 'Kaydedilen karar geçmişten doğrulanarak açılır',
    },
    {
        'order': 4,
        'window': '2026-08-11/2026-08-17',
        'id': 'PRODUCT_SLICE_04_DEX_WALLET_CEX_GRAPH_AND_PERFORMANCE',
        'deliverable': 'DEX swap yönü, router/pool, metadata/decimals, fiyat ve tam maliyet; başarılı wallet ölçümü; CEX balina akışı; Obsidian tarzı kanıt grafiği',
        'completion_gate': 'En az bir gerçek kapalı döngü ve kanıt grafiği uçtan uca doğrulanır',
    },
    {
        'order': 5,
        'window': '2026-08-18/2026-08-22',
        'id': 'PRODUCT_SLICE_05_HAREKAT_SUBAYI_AI_COUNCIL_SELF_HEALING_AND_OPERATIONAL_INTELLIGENCE',
        'deliverable': 'Chatbot, advisory AI konseyi, arıza teşhis/diff/test önerisi ve DEX-operasyonel teknoloji/saldırı istihbaratı opportunity-cost döngüsü',
        'completion_gate': 'Kullanıcıya gerçek sistem olayı üzerinden açıklama ve onarım önerisi gelir',
    },
    {
        'order': 6,
        'window': '2026-08-23/2026-08-29',
        'id': 'PRODUCT_SLICE_06_LIMITED_PAPER_TRADE',
        'deliverable': 'Gerçek fiyat, gas, fee, slippage ve gecikme kullanan kesintisiz sınırlı paper trade',
        'completion_gate': 'En az 7 günlük sürekli koşu, kapanmış simülasyon döngüleri ve hata/restart testleri',
    },
    {
        'order': 7,
        'window': '2026-08-30/2026-08-31',
        'id': 'PRODUCT_SLICE_07_FINAL_SECURITY_GO_NO_GO',
        'deliverable': 'Signer/wallet izolasyonu, kill switch, exact approvals, backup/recovery ve son go/no-go',
        'completion_gate': 'Kritik/yüksek açık yok; kullanıcı canlı canary aktivasyonunu ayrıca onaylar',
    },
    {
        'order': 8,
        'window': '2026-09-01',
        'id': 'PRODUCT_SLICE_08_LIVE_CANARY_START',
        'deliverable': 'BSC PancakeSwap üzerinde işlem başına 1-2 USD, insan onaylı, izole wallet ile gerçek para canary başlangıcı',
        'completion_gate': 'İlk gerçek işlem; karar, pre-trade snapshot, execution ve outcome kanıtı panelde kayıtlıdır',
    },
]

live_canary = {
    'target_start_date': TARGET_DATE,
    'chain': 'BSC',
    'dex_scope': ['PANCAKESWAP_V2', 'PANCAKESWAP_V3'],
    'trade_notional_usd_min': 1,
    'trade_notional_usd_max': 2,
    'initial_mode': 'HUMAN_APPROVAL_EACH_TRADE',
    'isolated_canary_wallet_required': True,
    'wallet_funding_cap_usd': 'USER_DEFINED_BEFORE_ACTIVATION',
    'max_concurrent_open_positions': 1,
    'exact_amount_approval_required': True,
    'unlimited_token_approval_forbidden': True,
    'risk_engine_veto': True,
    'kill_switch_required': True,
    'automatic_capital_expansion': False,
    'live_trade_current_state': 'DISABLED_UNTIL_FINAL_GO_NO_GO_AND_EXPLICIT_USER_ACTIVATION',
    'real_wallet_signing_order_authority_current_state': 0,
    'loss_accounting': [
        'TOKEN_NOTIONAL_LOSS',
        'GAS_COST',
        'FAILED_TRANSACTION_GAS',
        'SLIPPAGE',
        'DEX_FEE',
        'TOKEN_BUY_SELL_TAX',
        'APPROVAL_TRANSACTION_COST',
    ],
}

learning = {
    'status': 'MANDATORY_NOT_YET_END_TO_END_VERIFIED',
    'principle': 'A loss becomes usable experience only when the complete evidence and outcome loop is captured and replayable.',
    'required_record': [
        'PRE_TRADE_DATA_SNAPSHOT',
        'RISK_AND_DECISION_PACKET',
        'HUMAN_APPROVAL',
        'ROUTE_QUOTE_AND_EXPECTED_COST',
        'SIGNED_OR_SIMULATED_ACTION_ID',
        'EXECUTION_RECEIPT',
        'ACTUAL_GAS_FEE_SLIPPAGE_TAX',
        'POSITION_AND_EXIT_OUTCOME',
        'ERROR_OR_SUCCESS_CLASSIFICATION',
        'LESSON_CANDIDATE',
    ],
    'adaptation_loop': [
        'CAPTURE',
        'CLASSIFY',
        'COMPARE_TO_EXPECTATION',
        'PROPOSE_RULE_OR_MODEL_CHANGE',
        'HISTORICAL_REPLAY',
        'RED_TEAM_AND_REGRESSION_TEST',
        'HUMAN_APPROVAL',
        'CONTROLLED_DEPLOYMENT',
    ],
    'silent_production_self_modification': False,
    'automatic_code_apply_without_human_approval': False,
    'automatic_trade_authority_expansion': False,
}

manifesto_body = f'''## DEADLINE, LIVE CANARY AND LEARNING CONSTITUTION

- Usable product, paper-trade validation and initial bounded live canary target date is `{TARGET_DATE}`; the active date and schedule are owned by `PROJECT_RUNTIME.json`.
- Deadline pressure may remove bloat and nonessential work, but may not fabricate evidence or silently expand wallet, signing, order or capital authority.
- Initial live canary is BSC/PancakeSwap only, transaction notional is bounded to 1-2 USD, one open position, isolated canary wallet and exact-amount approvals.
- Unlimited token approval, automatic capital growth and hidden trade-authority expansion are forbidden.
- A monetary loss is counted as learning only when pre-trade evidence, decision, approval, execution, all costs, exit/outcome and error classification are stored and replayable.
- The learning layer may propose rule, model or code changes; it may not silently modify production code or activate a change without replay, regression/red-team evidence and human approval.
- The target date does not enable live trading today. Current live authority remains disabled until the final go/no-go and explicit user activation.'''
marker_upsert('02_MANIFESTO.md', '<!-- DEADLINE_LIVE_CANARY_LEARNING:BEGIN -->', '<!-- DEADLINE_LIVE_CANARY_LEARNING:END -->', manifesto_body)

boot = load('PROJECT_BOOT.json')
boot['boot_version'] = '3.5'
boot.setdefault('assistant_behavior_rules', {})['respect_runtime_product_deadline_and_schedule'] = True
boot['assistant_behavior_rules']['do_not_replace_delivery_with_new_era_or_engine_bloat'] = True
boot['assistant_behavior_rules']['treat_loss_as_learning_only_with_complete_outcome_evidence'] = True
boot['deadline_delivery_contract'] = {
    'current_deadline_owner': 'PROJECT_RUNTIME.json',
    'runtime_field': 'product_completion_program.delivery_deadline',
    'deadline_must_be_respected': True,
    'scope_reduction_before_deadline_extension': True,
    'new_era_forbidden_while_product_completion_lock_active': True,
    'user_visible_delivery_over_engine_deepening': True,
}
boot['live_canary_learning_contract'] = {
    'current_policy_owner': 'PROJECT_RUNTIME.json',
    'bounded_notional_required': True,
    'isolated_wallet_required': True,
    'exact_approval_required': True,
    'unlimited_approval_forbidden': True,
    'complete_evidence_outcome_loop_required': True,
    'silent_self_modification_forbidden': True,
    'human_approval_for_code_or_authority_change': True,
}
boot['updated_at_utc'] = NOW
atomic_json('PROJECT_BOOT.json', boot)

runtime = load('PROJECT_RUNTIME.json')
runtime['current_stage'] = PROGRAM_ID
runtime['current_status'] = STATUS
runtime['mode'] = 'DEADLINE_DRIVEN_USABLE_PRODUCT_COMPLETION'
runtime['product_completion_lock'] = True
runtime['no_new_era_until_product_completion'] = True
runtime['delivery_deadline'] = TARGET_DATE
runtime['days_from_plan_lock_to_deadline'] = 39
runtime['next_safe_step'] = NEXT
runtime['live_canary_policy'] = live_canary
runtime['learning_system_contract'] = learning
program = runtime.setdefault('product_completion_program', {})
program.update({
    'id': PROGRAM_ID,
    'status': 'ACTIVE_DEADLINE_LOCKED',
    'delivery_deadline': TARGET_DATE,
    'deadline_schedule': schedule,
    'current_step': NEXT,
    'next_safe_step': NEXT,
    'no_new_era_until_complete': True,
    'scope_freeze': True,
    'paper_trade_completion_required_before_live_canary': True,
    'live_canary_start_target': TARGET_DATE,
    'live_canary_policy': live_canary,
    'learning_system_contract': learning,
})
runtime['current_work_unit'] = {
    'id': PROGRAM_ID,
    'type': 'PRODUCT_COMPLETION_PROGRAM',
    'status': 'ACTIVE_DEADLINE_LOCKED',
    'stage': NEXT,
    'delivery_deadline': TARGET_DATE,
    'new_era': False,
    'next_step': NEXT,
}
runtime['last_action'] = 'SEPTEMBER_1_PRODUCT_PAPER_AND_LIVE_CANARY_DEADLINE_PLAN_LOCK'
runtime['last_result'] = 'DEADLINE_AND_1_TO_2_USD_LIVE_CANARY_POLICY_CANONICALLY_LOCKED'
runtime['open_risks'] = [
    'PRODUCT_SURFACE_NOT_DEPLOYED',
    'NEWS_PANEL_ALCHEMY_SECURITY_TRUTH_NOT_REVERIFIED',
    'LEARNING_LOOP_NOT_END_TO_END_VERIFIED',
    'PAPER_RUNTIME_NOT_YET_VALIDATED',
    'LIVE_CANARY_FINAL_GO_NO_GO_PENDING',
]
runtime['updated_at_utc'] = NOW
pointer = runtime.setdefault('canonical_runtime_pointer', {})
pointer['current_stage'] = PROGRAM_ID
pointer['current_status'] = STATUS
pointer['next_safe_step'] = NEXT
pointer['delivery_deadline'] = TARGET_DATE
pointer['product_completion_lock'] = True
pointer['live_canary_target'] = TARGET_DATE
pointer['live_trade_current_state'] = 'DISABLED'
atomic_json('PROJECT_RUNTIME.json', runtime)

roadmap = load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
roadmap['product_completion_program'] = program
roadmap['deadline_schedule'] = schedule
roadmap['live_canary_policy'] = live_canary
roadmap['learning_system_contract'] = learning
direction = roadmap.setdefault('current_direction', {})
direction['current_line'] = PROGRAM_ID
direction['current_stage'] = PROGRAM_ID
direction['current_status'] = STATUS
direction['status'] = 'DEADLINE_LOCKED_PRODUCT_COMPLETION'
direction['delivery_deadline'] = TARGET_DATE
direction['next_safe_step'] = NEXT
direction['product_completion_lock'] = True
direction['era64k_status'] = 'DEFERRED_NOT_NEXT_STEP'
direction['updated_at_utc'] = NOW
roadmap['updated_at_utc'] = NOW
atomic_json('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

roadmap_md = f'''# 03 ROADMAP - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={PROGRAM_ID}
CURRENT_STATUS={STATUS}
PRODUCT_COMPLETION_DEADLINE={TARGET_DATE}
NO_NEW_ERA=true
SCOPE_FREEZE=true
ERA64K_STATUS=DEFERRED_NOT_NEXT_STEP
NEXT_SAFE_STEP={NEXT}

## Kesin teslim hedefi

Tokenoskobi kullanılabilir ürün döngüsü, paper-trade testleri ve ilk bounded gerçek para canary başlangıcı **1 Eylül 2026** hedefiyle kilitlenmiştir. Tarihi kaçırmamak için önce kapsam daraltılır; yeni ERA, alt ERA, mimari gösteri, belge zinciri veya ürünü doğrudan bloke etmeyen engine derinleştirmesi açılmaz.

## Sıkıştırılmış takvim

| Tarih | Tek teslimat |
|---|---|
| 25-27 Temmuz | NEWS, panel URL/auth, Alchemy hibrit bağlantısı, onchain gecikmesi ve iç/dış güvenliğin read-only gerçeklik doğrulaması |
| 28 Temmuz-5 Ağustos | Canlı tek token giriş ekranı, gerçek karar paketi, online timeframe ve kanıtlar |
| 6-10 Ağustos | İnsan onayı, karar geçmişi ve sonuç takibi |
| 11-17 Ağustos | DEX swap yönü, tam maliyet, başarılı wallet, CEX balina ve Obsidian grafiği |
| 18-22 Ağustos | Harekât Subayı chatbotu, AI konseyi, self-healing önerisi ve operasyonel istihbarat |
| 23-29 Ağustos | En az 7 günlük sınırlı paper-trade koşusu ve hata/restart testleri |
| 30-31 Ağustos | Son signer/wallet izolasyonu, kill switch, recovery ve go/no-go |
| 1 Eylül | BSC/PancakeSwap üzerinde işlem başına 1-2 USD gerçek para canary başlangıcı |

## İlk canlı canary sınırı

- BSC ve PancakeSwap V2/V3.
- İşlem başına 1-2 USD.
- Başlangıçta her işlem insan onaylı.
- İzole canary wallet, tek açık pozisyon ve exact-amount approval.
- Unlimited approval ve otomatik sermaye artırımı yok.
- Risk Engine veto ve kill switch zorunlu.
- Live trade bugün açılmaz; 31 Ağustos go/no-go ve açık kullanıcı aktivasyonu sonrası hedef 1 Eylül'dür.

## Öğrenme şartı

Kaybedilen para ancak pre-trade veri snapshotı, karar, insan onayı, quote, receipt, gerçek gas/fee/slippage/tax, exit/outcome ve hata sınıfı kaydedilip replay edilebiliyorsa tecrübeye dönüşür. Sistem bu veriden değişiklik önerir; production kodunu veya trade yetkisini kendiliğinden değiştirmez. Değişiklik replay, regression/red-team ve insan onayından sonra uygulanır.
'''
atomic_text('03_ROADMAP.md', roadmap_md)

almanac_body = f'''## SEPTEMBER 1 PRODUCT, PAPER AND LIVE CANARY DEADLINE DECISION

- Timestamp UTC: `{NOW}`
- Status: `DEADLINE_PLAN_LOCKED`
- Program: `{PROGRAM_ID}`
- Product deadline: `{TARGET_DATE}`
- Paper-trade validation window: `2026-08-23/2026-08-29`
- Final security go/no-go: `2026-08-30/2026-08-31`
- Target live canary start: `{TARGET_DATE}`
- Live canary: `BSC_PANCAKESWAP_1_TO_2_USD_PER_TRADE`
- Initial approval mode: `HUMAN_APPROVAL_EACH_TRADE`
- Isolated wallet: `REQUIRED`
- Unlimited token approvals: `FORBIDDEN`
- Learning loop status: `MANDATORY_NOT_YET_END_TO_END_VERIFIED`
- Current live trade: `DISABLED`
- Current wallet/signing/order authority: `0`
- New ERA opened: `false`
- Next safe step: `{NEXT}`
- Note: The target is binding for delivery planning; this record does not prematurely enable live trading.'''
marker_upsert('04_ALMANAC.md', '<!-- SEPTEMBER_1_DEADLINE_DECISION:BEGIN -->', '<!-- SEPTEMBER_1_DEADLINE_DECISION:END -->', almanac_body)

atlas_body = '''## DEADLINE LIVE CANARY AND LEARNING FLOW

```text
PRODUCT DELIVERY
  -> LIVE TOKEN PANEL
  -> HUMAN DECISION HISTORY
  -> DEX / WALLET / CEX EVIDENCE GRAPH
  -> HAREKAT SUBAYI + OPERATIONAL INTELLIGENCE
  -> 7-DAY PAPER VALIDATION
  -> FINAL SECURITY GO/NO-GO
  -> 1-2 USD LIVE CANARY
```

```text
LIVE CANARY
  -> ISOLATED BSC WALLET
  -> EXACT AMOUNT APPROVAL
  -> ONE OPEN POSITION
  -> PANCAKESWAP V2/V3 ALLOWLIST
  -> RISK ENGINE VETO
  -> HUMAN APPROVAL
  -> SIGN / BROADCAST
  -> RECEIPT + ALL COSTS
  -> KILL SWITCH
```

```text
LEARNING LOOP
  PRE-TRADE SNAPSHOT
  -> DECISION + EXPECTATION
  -> EXECUTION RECEIPT
  -> GAS / FEE / SLIPPAGE / TAX
  -> EXIT AND OUTCOME
  -> EXPECTED VS ACTUAL ERROR
  -> LESSON CANDIDATE
  -> HISTORICAL REPLAY
  -> REGRESSION + CLAUDE REVIEW + GEMINI RED TEAM
  -> HUMAN APPROVAL
  -> CONTROLLED UPDATE
```

- Loss without complete evidence and outcome classification is expense, not learning.
- AI may diagnose and propose; it cannot silently rewrite production or enlarge authority.
- Initial live exposure is bounded by transaction notional, isolated wallet funding and one open position.'''
marker_upsert('05_ATLAS.md', '<!-- DEADLINE_LIVE_CANARY_LEARNING_FLOW:BEGIN -->', '<!-- DEADLINE_LIVE_CANARY_LEARNING_FLOW:END -->', atlas_body)

master_state = f'''# 06 PROJECT MASTER STATE

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={PROGRAM_ID}
CURRENT_STATUS={STATUS}
PRODUCT_COMPLETION_DEADLINE={TARGET_DATE}
PRODUCT_COMPLETION_LOCK=true
NO_NEW_ERA=true
SCOPE_FREEZE=true
NEXT_SAFE_STEP={NEXT}

LAST_VERIFIED_TECHNICAL_STAGE=ERA64J
TECHNICAL_TEST_BASELINE=172/172_VERIFIED
REAL_BSC_EVENT_COUNT=367
REAL_BSC_TRANSACTION_COUNT=277
PRODUCT_SURFACE_DEPLOYED=false
LEARNING_LOOP_END_TO_END_VERIFIED=false

PAPER_TRADE_TARGET_WINDOW=2026-08-23/2026-08-29
FINAL_GO_NO_GO_WINDOW=2026-08-30/2026-08-31
LIVE_CANARY_TARGET_DATE={TARGET_DATE}
LIVE_CANARY_CHAIN=BSC
LIVE_CANARY_DEX=PANCAKESWAP_V2_V3
LIVE_CANARY_TRADE_USD_MIN=1
LIVE_CANARY_TRADE_USD_MAX=2
LIVE_CANARY_INITIAL_MODE=HUMAN_APPROVAL_EACH_TRADE
ISOLATED_CANARY_WALLET_REQUIRED=true
UNLIMITED_TOKEN_APPROVAL=false
MAX_CONCURRENT_OPEN_POSITIONS=1

PAPER_RUNTIME=DISABLED_PENDING_BUILD_AND_VALIDATION
LIVE_TRADE=DISABLED_PENDING_FINAL_GO_NO_GO
REAL_WALLET_AUTHORITY=0
REAL_SIGNING_AUTHORITY=0
REAL_ORDER_AUTHORITY=0
REAL_FINANCIAL_AUTHORITY=0

BLOCKERS=PRODUCT_SURFACE_NOT_DEPLOYED;LIVE_TRUTH_NOT_REVERIFIED;LEARNING_LOOP_NOT_VERIFIED;PAPER_RUNTIME_NOT_VALIDATED;FINAL_GO_NO_GO_PENDING
'''
atomic_text('06_PROJECT_MASTER_STATE.md', master_state)

handoff = f'''# 07 PROJECT HANDOFF

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={PROGRAM_ID}
STATUS={STATUS}
PRODUCT_COMPLETION_DEADLINE={TARGET_DATE}
NO_NEW_ERA=true
SCOPE_FREEZE=true
NEXT_SAFE_STEP={NEXT}

## Kesin yön

1 Eylül 2026 tarihinde kullanılabilir ürün, tamamlanmış paper-trade test hattı ve BSC/PancakeSwap üzerinde işlem başına 1-2 USD bounded gerçek para canary başlangıcı hedeflenmiştir. Yeni ERA, alt ERA veya ürün dışı engine derinleştirmesi yoktur.

## İlk canlı canary

- BSC ve PancakeSwap V2/V3.
- İşlem başına 1-2 USD.
- Başlangıçta her işlem insan onaylı.
- İzole wallet, tek açık pozisyon, exact approval, unlimited approval yasağı.
- Live trade şu anda kapalıdır; 30-31 Ağustos go/no-go ve açık kullanıcı aktivasyonu gerekir.

## Öğrenme gerçeği

Öğrenme sistemi bugün uçtan uca doğrulanmış değildir. Zorunlu akış: pre-trade snapshot -> karar -> onay -> execution/receipt -> gerçek maliyetler -> exit/outcome -> hata sınıfı -> lesson candidate -> replay/test/red-team -> insan onayı -> kontrollü güncelleme. Bu akış kurulmadan kayıp yalnız giderdir; kurulduğunda ölçülebilir tecrübeye dönüşür.

## Yeni pencerenin tek işi

README boot protocolünü eksiksiz uygula ve yalnız `{NEXT}` adımını yürüt. NEWS, panel URL/auth, Alchemy hibrit bağlantısı, onchain gecikmesi ve iç/dış güvenliği güncel read-only kanıtla doğrula. Sonra takvimdeki bir sonraki görünür ürün teslimatına geç.'''
atomic_text('07_PROJECT_HANDOFF.md', handoff)

history = load('PROJECT_HISTORY.json')
event_id = 'TOKENOSKOBI_SEPTEMBER_1_DEADLINE_AND_LIVE_CANARY_PLAN_LOCK_V1'
events = history.setdefault('events', [])
history['events'] = [item for item in events if item.get('event_id') != event_id]
history['events'].append({
    'event_id': event_id,
    'event': 'SEPTEMBER_1_PRODUCT_PAPER_AND_LIVE_CANARY_DEADLINE_PLAN_LOCK',
    'timestamp_utc': NOW,
    'head_before_commit': HEAD_BEFORE,
    'program': PROGRAM_ID,
    'delivery_deadline': TARGET_DATE,
    'deadline_schedule': schedule,
    'live_canary_policy': live_canary,
    'learning_system_contract': learning,
    'new_era_opened': False,
    'current_live_trade': 'DISABLED',
    'current_real_financial_authority': 0,
    'next_safe_step': NEXT,
})
history['updated_at_utc'] = NOW
atomic_json('PROJECT_HISTORY.json', history)

latest = f'''# TOKENOSKOBI LATEST HANDOFF

```text
CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={PROGRAM_ID}
STATUS={STATUS}
PRODUCT_COMPLETION_DEADLINE={TARGET_DATE}
NO_NEW_ERA=true
PAPER_TRADE_TARGET=2026-08-23_TO_2026-08-29
LIVE_CANARY_TARGET={TARGET_DATE}
LIVE_CANARY_NOTIONAL_USD=1_TO_2
CURRENT_LIVE_TRADE=DISABLED
CURRENT_REAL_FINANCIAL_AUTHORITY=0
NEXT_SAFE_STEP={NEXT}
```

Next window must boot from README and execute only the read-only NEWS, panel, Alchemy/hybrid, latency and internal/external security truth verification before product building continues.'''
atomic_text('reports/LATEST_TK_AI_HANDOFF.md', latest)

machine = load('data/control/latest_tk_machine_state.json')
machine['current_stage'] = PROGRAM_ID
machine['current_status'] = STATUS
machine['product_completion_deadline'] = TARGET_DATE
machine['product_completion_lock'] = True
machine['no_new_era'] = True
machine['next_safe_step'] = NEXT
machine['deadline_schedule'] = schedule
machine['live_canary_policy'] = live_canary
machine['learning_system_contract'] = learning
machine['updated_at_utc'] = NOW
atomic_json('data/control/latest_tk_machine_state.json', machine)

print('DEADLINE_PLAN_WRITE=COMPLETED')
PY

python3 <<'PY'
import json
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
TARGET = '2026-09-01'
NEXT = 'PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION'
load = lambda rel: json.loads((ROOT / rel).read_text(encoding='utf-8'))
boot = load('PROJECT_BOOT.json')
runtime = load('PROJECT_RUNTIME.json')
roadmap = load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
history = load('PROJECT_HISTORY.json')
machine = load('data/control/latest_tk_machine_state.json')

assert boot['boot_version'] == '3.5'
assert boot['deadline_delivery_contract']['deadline_must_be_respected'] is True
assert boot['live_canary_learning_contract']['silent_self_modification_forbidden'] is True
assert runtime['delivery_deadline'] == TARGET
assert runtime['current_status'] == 'PRODUCT_COMPLETION_DEADLINE_LOCKED_2026_09_01'
assert runtime['next_safe_step'] == NEXT
assert runtime['product_completion_lock'] is True
assert len(runtime['product_completion_program']['deadline_schedule']) == 8
policy = runtime['live_canary_policy']
assert policy['trade_notional_usd_min'] == 1
assert policy['trade_notional_usd_max'] == 2
assert policy['isolated_canary_wallet_required'] is True
assert policy['unlimited_token_approval_forbidden'] is True
assert policy['live_trade_current_state'].startswith('DISABLED')
assert runtime['learning_system_contract']['silent_production_self_modification'] is False
assert roadmap['current_direction']['delivery_deadline'] == TARGET
assert roadmap['current_direction']['next_safe_step'] == NEXT
assert any(item.get('event_id') == 'TOKENOSKOBI_SEPTEMBER_1_DEADLINE_AND_LIVE_CANARY_PLAN_LOCK_V1' for item in history['events'])
assert machine['product_completion_deadline'] == TARGET

for rel, token in [
    ('02_MANIFESTO.md', '<!-- DEADLINE_LIVE_CANARY_LEARNING:BEGIN -->'),
    ('03_ROADMAP.md', '1 Eylül 2026'),
    ('04_ALMANAC.md', '<!-- SEPTEMBER_1_DEADLINE_DECISION:BEGIN -->'),
    ('05_ATLAS.md', '<!-- DEADLINE_LIVE_CANARY_LEARNING_FLOW:BEGIN -->'),
    ('06_PROJECT_MASTER_STATE.md', 'LIVE_CANARY_TRADE_USD_MAX=2'),
    ('07_PROJECT_HANDOFF.md', '1-2 USD'),
    ('reports/LATEST_TK_AI_HANDOFF.md', 'LIVE_CANARY_NOTIONAL_USD=1_TO_2'),
]:
    assert token in (ROOT / rel).read_text(encoding='utf-8'), rel

authority = runtime['authority']
assert str(authority['live_trade']).upper() == 'DISABLED'
assert str(authority['paper_trade']).upper().startswith('DISABLED')
assert int(authority['real_order_authority']) == 0
assert int(authority['real_signing_authority']) == 0
assert int(authority['real_trade_authority']) == 0
assert int(authority['real_wallet_authority']) == 0
print('DEADLINE_PLAN_VALIDATION=VERIFIED')
print('LIVE_CANARY_1_TO_2_USD_POLICY=VERIFIED')
print('LEARNING_EVIDENCE_LOOP_CONTRACT=VERIFIED')
print('CURRENT_AUTHORITY_BOUNDARIES=UNCHANGED_VERIFIED')
PY

rm -f "$SELF_REL"

git diff --check

git add -A -- \
  02_MANIFESTO.md PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json 03_ROADMAP.md 04_ALMANAC.md \
  05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  data/control/latest_tk_machine_state.json "$SELF_REL"
git add -f reports/LATEST_TK_AI_HANDOFF.md

ALLOWED='^(02_MANIFESTO\.md|PROJECT_BOOT\.json|PROJECT_RUNTIME\.json|PROJECT_HISTORY\.json|data/tokenoskobi_v1_v8_master_era_roadmap\.json|03_ROADMAP\.md|04_ALMANAC\.md|05_ATLAS\.md|06_PROJECT_MASTER_STATE\.md|07_PROJECT_HANDOFF\.md|reports/LATEST_TK_AI_HANDOFF\.md|data/control/latest_tk_machine_state\.json|tools/tokenoskobi_deadline_20260901_live_canary_plan_sync\.sh)$'
while IFS= read -r changed; do
  [[ "$changed" =~ $ALLOWED ]] || { echo "BLOCKED=UNEXPECTED_STAGED_FILE:$changed"; exit 1; }
done < <(git diff --cached --name-only)

[[ -n "$(git diff --cached --name-only)" ]] || { echo "BLOCKED=NO_CANONICAL_CHANGES"; exit 1; }
git diff --cached --stat
git commit -m "Product: lock September 1 delivery and live canary plan"
COMMITTED=1
git push origin main

FINAL_HEAD="$(git rev-parse HEAD)"
REMOTE_FINAL="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
[[ "$FINAL_HEAD" == "$REMOTE_FINAL" ]] || { echo "BLOCKED=REMOTE_VERIFY_FAILED:$FINAL_HEAD:$REMOTE_FINAL"; exit 1; }
[[ -z "$(git status --short)" ]] || { echo "BLOCKED=WORKTREE_NOT_CLEAN_AFTER_PUSH"; git status --short; exit 1; }

trap - ERR
rm -f "$BACKUP_LIST"
trap - EXIT

echo "SEPTEMBER_1_DEADLINE_PLAN=VERIFIED_GITHUB_SEALED"
echo "PRODUCT_COMPLETION_DEADLINE=2026-09-01"
echo "NO_NEW_ERA=true"
echo "LIVE_CANARY_TARGET=2026-09-01"
echo "LIVE_CANARY_CHAIN=BSC"
echo "LIVE_CANARY_DEX=PANCAKESWAP_V2_V3"
echo "LIVE_CANARY_TRADE_USD=1_TO_2"
echo "LEARNING_LOOP=MANDATORY_NOT_YET_END_TO_END_VERIFIED"
echo "CURRENT_PAPER_RUNTIME=DISABLED"
echo "CURRENT_LIVE_TRADE=DISABLED"
echo "CURRENT_REAL_FINANCIAL_AUTHORITY=0"
echo "NEXT_SAFE_STEP=PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$FINAL_HEAD"
