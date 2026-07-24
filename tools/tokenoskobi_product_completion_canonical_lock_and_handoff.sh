#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/root/tokenoskobi_clean_v1"
SELF_REL="tools/tokenoskobi_product_completion_canonical_lock_and_handoff.sh"
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

STATUS_BEFORE="$(git status --short)"
[[ -z "$STATUS_BEFORE" ]] || { echo "BLOCKED=WORKTREE_NOT_CLEAN"; printf '%s\n' "$STATUS_BEFORE"; exit 1; }

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/tokenoskobi_product_completion_canonical_backup_${TS}.tar.gz"
BACKUP_LIST="$(mktemp)"
trap 'rm -f "$BACKUP_LIST"' EXIT

for path in \
  README.md \
  01_INDEX.md \
  02_MANIFESTO.md \
  PROJECT_BOOT.json \
  PROJECT_RUNTIME.json \
  PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  03_ROADMAP.md \
  04_ALMANAC.md \
  05_ATLAS.md \
  06_PROJECT_MASTER_STATE.md \
  07_PROJECT_HANDOFF.md \
  reports/LATEST_TK_AI_HANDOFF.md \
  data/control/latest_tk_machine_state.json \
  tools/build_tokenoskobi_product_vertical_slice_v1.sh \
  tools/.tokenoskobi_product_vertical_slice_payload_v1/index.001 \
  tools/.tokenoskobi_product_vertical_slice_payload_v1/index.002 \
  tools/.tokenoskobi_product_vertical_slice_payload_v1/inner.001 \
  tools/.tokenoskobi_product_vertical_slice_payload_v1/inner.002 \
  tools/.tokenoskobi_product_vertical_slice_payload_v1/inner.003 \
  tools/.tokenoskobi_product_vertical_slice_payload_v1/server.001 \
  tools/.tokenoskobi_product_vertical_slice_payload_v1/server.002 \
  tools/.tokenoskobi_product_vertical_slice_payload_v1/server.003 \
  tools/.tokenoskobi_product_vertical_slice_payload_v1/test.001
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

import copy
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
NOW = datetime.now(timezone.utc).isoformat()
NEXT = 'PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION'
PROGRAM_ID = 'TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE'
STATUS = 'PRODUCT_COMPLETION_MODE_ACTIVE_PLAN_LOCKED'
TECHNICAL_BASELINE_HEAD = '43279c41d63250893540553994598a7418dc91ca'
HEAD_BEFORE = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


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
        if lines:
            text = lines[0] + '\n\n' + block + '\n\n' + '\n'.join(lines[1:]).lstrip('\n')
        else:
            text = block + '\n'
    atomic_text(rel, text)


baseline = {
    'stage': 'ERA64J_HISTORICAL_TRANSFER_RECEIPT_AND_COST_ENRICHMENT',
    'status': 'HISTORICAL_TRANSFER_RECEIPT_GAS_COST_ENRICHMENT_VERIFIED',
    'technical_head': TECHNICAL_BASELINE_HEAD,
    'tests': '172/172_VERIFIED',
    'real_data': True,
    'synthetic_data': False,
    'source_event_count': 367,
    'source_transaction_count': 277,
    'receipt_enriched_event_count': 367,
    'gas_cost_enriched_event_count': 367,
    'successful_wallet_classification_ready': False,
    'paper_runtime': 'DISABLED',
    'live_trade': 'DISABLED',
    'real_financial_authority': 0,
}

ordered_steps = [
    {
        'order': 1,
        'id': NEXT,
        'title': 'Canlı Gerçeklik, Panel Erişimi ve Güvenlik Doğrulaması',
        'mode': 'READ_ONLY',
        'purpose': 'NEWS canlılığı, gerçek panel URL/auth yolu, servisler, Alchemy hibrit bağlantısı, onchain gecikmesi ve iç/dış güvenliği güncel kanıtla doğrulamak.',
        'acceptance': [
            'Kesin panel URL ve kimlik doğrulama yolu telefondan açılır ve doğrulanır.',
            'NEWS producer/timer/readmodel zincirinin güncel canlı veya arızalı durumu ölçülür.',
            'Alchemy bağlantısı sır basmadan doğrulanır; public BSC RPC ve piyasa veri fallback zinciri ölçülür.',
            'Onchain olaydan readmodel/panel görünümüne gerçek gecikme ölçülür.',
            'Nginx, TLS, auth, port, firewall, SSH, secret, izin, rate-limit ve servis yüzeyi için iç/dış güvenlik bulgusu çıkarılır.',
            'Bu adım runtime, DB, panel, service, timer veya authority mutation yapmaz.',
        ],
    },
    {
        'order': 2,
        'id': 'PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET',
        'title': 'Tek Token Giriş Ekranı ve Gerçek Karar Paketi',
        'mode': 'BOUNDED_PRODUCT_BUILD',
        'purpose': 'Kullanıcının BSC token adresi girip gerçek, gerekçeli ve kanıt bağlantılı karar paketi görmesini sağlamak.',
        'acceptance': [
            'BSC adresi server-side doğrulanır; geçersiz veya kontrat olmayan adres fail-closed reddedilir.',
            'Onchain, kontrat, holder/deployer, likidite, teknik, NEWS ve mevcut wallet bağlamı tek pakette birleşir.',
            'Online timeframe seti 1m, 5m, 15m, 1h, 4h ve 1d olarak çalışır; yeterli mum yoksa VERI_YETERSIZ gösterilir.',
            'Alchemy WebSocket/HTTP birincil, allowlisted public BSC RPC fallback/cross-check, GeckoTerminal piyasa kaynağı ve local cache hibrit çalışır.',
            'Risk Engine ALLOW, BLOCK, WAIT veya REVIEW kararı ve gerekçelerini üretir; panel trade yetkisi üretmez.',
            'Kullanıcı telefondan canlı URL üzerinde ekranı açar ve kabul eder.',
        ],
    },
    {
        'order': 3,
        'id': 'PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING',
        'title': 'İnsan Onayı, Karar Geçmişi ve Sonuç Takibi',
        'mode': 'BOUNDED_PRODUCT_BUILD',
        'purpose': 'Kararı insan onayıyla kaydetmek, tekrar açmak ve sonucunu izlemek.',
        'acceptance': [
            'İnsan ACCEPT, REJECT, WAIT veya REVIEW seçimi kanıt paketiyle birlikte append-only kaydedilir.',
            'Kayıt trade, wallet, signing veya order authority oluşturmaz.',
            'Geçmiş karar tekrar açılır ve kullanılan kanıt sürümü görülür.',
            'Belirlenen izleme pencerelerinde fiyat, risk ve sonuç değişimi kayda bağlanır.',
            'Panelde karar geçmişi ve sonuç takibi görünür.',
        ],
    },
    {
        'order': 4,
        'id': 'PRODUCT_SLICE_04_DEX_WALLET_CEX_GRAPH_AND_PERFORMANCE',
        'title': 'DEX İşlemi, Başarılı Cüzdan, CEX Balina ve Obsidian Grafiği',
        'mode': 'BOUNDED_PRODUCT_BUILD',
        'purpose': 'Gerçek swap döngülerini, maliyet-tam performansı ve kanıt-temelli wallet/entity ilişkilerini görselleştirmek.',
        'acceptance': [
            'Router, pool, token metadata/decimals, alış-satış yönü, gerçekleşme fiyatı, gas, fee, slippage ve kapalı döngü belirlenir.',
            'Başarılı cüzdan etiketi yalnız yeterli örnek, maliyet-tam PnL ve confidence eşiğiyle verilir.',
            'CEX deposit/withdrawal ilişkileri ve 50 BTC veya eşdeğer balina eşiği izlenir.',
            'Wallet, CEX, DEX, pool, token, transaction, news ve decision düğümleri Obsidian tarzı grafikte gösterilir.',
            'Transfer ilişkisi tek başına ortak sahiplik veya kimlik iddiasına çevrilmez.',
        ],
    },
    {
        'order': 5,
        'id': 'PRODUCT_SLICE_05_HAREKAT_SUBAYI_AI_COUNCIL_SELF_HEALING_AND_OPERATIONAL_INTELLIGENCE',
        'title': 'Harekât Subayı, AI Konseyi, Onarım Önerisi ve Operasyonel İstihbarat',
        'mode': 'ADVISORY_ONLY_PRODUCT_BUILD',
        'purpose': 'Sistemle sürekli temas, çoklu AI incelemesi, arıza teşhisi ve DEX-operasyonel teknoloji/saldırı istihbaratı sağlamak.',
        'acceptance': [
            'Panel veya Telegram chatbot durum, token, risk, neden, uyarı, onay ve reddet komutlarını destekler.',
            'NVIDIA API, ChatGPT/Codex, Claude, Gemini ve GitHub Copilot rolleri advisory-only ve hot-path dışı olarak doğrulanır.',
            'Sorun algılama kök neden, düzeltme diffi, test sonucu, risk ve rollback önerisi üretir; insan onayı olmadan kod uygulamaz.',
            'İstihbarat genel kripto haberini değil DEX operasyonu, yeni saldırı, AI/hardware/software/provider ve güvenlik gelişmelerini filtreler.',
            'Her öneri opportunity cost, uygulanabilirlik, güvenlik etkisi ve APPLY/DEFER/REJECT kararıyla kullanıcıya gelir.',
        ],
    },
    {
        'order': 6,
        'id': 'PRODUCT_SLICE_06_LIMITED_PAPER_TRADE',
        'title': 'Sınırlı Paper Trade',
        'mode': 'ZERO_REAL_FUNDS_SIMULATION_ONLY',
        'purpose': 'Önceki ürün adımları kullanıcı tarafından kabul edildikten sonra sıfır gerçek fonla izlenebilir simülasyon çalıştırmak.',
        'acceptance': [
            'Adım 1-5 kullanıcı kabulü olmadan paper runtime açılmaz.',
            'Risk Engine veto, insan politika zarfı, bounded sizing ve stop/rollback zorunludur.',
            'Wallet, signing, broadcast, live order ve gerçek sermaye yetkileri sıfır kalır.',
            'Simülasyon emri, maliyet modeli, karar kanıtı ve sonuç geçmişi panelde görünür.',
            'Canlı trade ayrı açık insan kararı ve ayrı güvenlik doğrulaması olmadan açılamaz.',
        ],
    },
]

program = {
    'id': PROGRAM_ID,
    'title': 'Tokenoskobi Kullanılabilir Ürün Dikey Dilimi',
    'status': 'ACTIVE_PLAN_LOCKED',
    'opened_by': 'EXPLICIT_USER_DIRECTION',
    'opened_at_utc': NOW,
    'current_step': NEXT,
    'next_safe_step': NEXT,
    'no_new_era_until_complete': True,
    'no_new_alt_era': True,
    'single_active_product_step': True,
    'no_new_canonical_document': True,
    'engine_deepening_only_when_product_blocked': True,
    'user_visible_acceptance_required_for_progress': True,
    'tests_docs_schemas_and_standalone_engines_are_not_product_completion': True,
    'era64k_status': 'DEFERRED_NOT_NEXT_STEP',
    'failed_builder_attempt': {
        'commit': '034b16387ed5e9966db637003cfc3f077abebe8e',
        'result': 'ROLLED_BACK_NO_PRODUCT_DEPLOYED',
        'cleanup_required': True,
    },
    'last_verified_technical_baseline': baseline,
    'ordered_steps': ordered_steps,
    'definition_of_done': [
        'Canlı panel URL telefondan açılır.',
        'Kullanıcı BSC token adresi girer.',
        'Gerçek veri kaynakları birleşik karar paketi üretir.',
        'Eksik veri açıkça VERI_YETERSIZ olarak gösterilir.',
        'Risk kararı ve kanıt bağlantıları görünür.',
        'İnsan kararı kaydedilir ve geçmişten tekrar açılır.',
        'Sonuç takibi çalışır.',
        'Daha sonra sınırlı paper trade aynı akışa bağlanır.',
    ],
    'forbidden_until_core_user_loop_accepted': [
        'NEW_ERA',
        'NEW_ALT_ERA',
        'UNRELATED_ENGINE_DEEPENING',
        'NEW_ARCHITECTURE_EXPANSION',
        'NEW_CANONICAL_DOCUMENT',
        'PAPER_RUNTIME_ENABLEMENT',
        'LIVE_TRADE_ENABLEMENT',
        'WALLET_SIGNING_ORDER_BROADCAST_AUTHORITY',
    ],
}

manifesto_body = '''## PRODUCT COMPLETION AND DEFINITION OF DONE

- Test, schema, doküman, bağımsız engine, plan, commit veya audit tek başına ürün tamamlanması değildir.
- İlerleme; kullanıcının canlı yüzeyde açabildiği, gerçek veriyle çalışan, kanıt gösteren ve kabul ettiği uçtan uca akışla ölçülür.
- `PROJECT_RUNTIME.json` içinde product-completion lock aktifken yeni ERA veya alt ERA açılamaz.
- Yeni mimari veya engine derinleştirmesi yalnız aktif kullanıcı akışını doğrudan bloke eden eksik için yapılabilir.
- Aynı anda yalnız bir görünür ürün adımı yürütülür.
- Veri yoksa veya doğrulanamıyorsa sistem `VERI_YETERSIZ` der; sahte skor, sahte canlılık veya sahte karar üretmez.
- Tek token ekranı, gerçek karar paketi, insan kararı ve geçmiş takibi kullanıcı tarafından kabul edilmeden paper runtime açılamaz.
- Paper trade sıfır gerçek fonlu simülasyondur; live wallet, signing, order ve broadcast yetkisi oluşturmaz.
- Kapanış ölçütü etiket veya test sayısı değil, çalışan ve kullanıcı tarafından kabul edilmiş ürün döngüsüdür.'''
marker_upsert('02_MANIFESTO.md', '<!-- PRODUCT_COMPLETION_CONSTITUTION:BEGIN -->', '<!-- PRODUCT_COMPLETION_CONSTITUTION:END -->', manifesto_body)

boot = read_json('PROJECT_BOOT.json')
boot['boot_version'] = '3.4'
boot.setdefault('assistant_behavior_rules', {})['do_not_open_new_era_while_product_completion_lock_active'] = True
boot['assistant_behavior_rules']['do_not_count_tests_docs_or_standalone_engines_as_product_completion'] = True
boot['assistant_behavior_rules']['require_user_visible_acceptance_for_product_progress'] = True
boot['product_delivery_contract'] = {
    'name': 'USER_VISIBLE_PRODUCT_COMPLETION_CONTRACT',
    'runtime_lock_owner': 'PROJECT_RUNTIME.json',
    'lock_field': 'product_completion_program.no_new_era_until_complete',
    'definition_of_progress': 'USER_VISIBLE_END_TO_END_FLOW_ACCEPTED_BY_USER',
    'single_active_product_step': True,
    'new_era_forbidden_while_locked': True,
    'new_alt_era_forbidden_while_locked': True,
    'new_canonical_document_forbidden_while_locked': True,
    'engine_deepening_rule': 'ONLY_WHEN_DIRECT_BLOCKER_TO_ACTIVE_PRODUCT_STEP',
    'missing_data_rule': 'SHOW_VERI_YETERSIZ_NEVER_FABRICATE',
    'paper_gate': 'CORE_USER_LOOP_ACCEPTED_BEFORE_PAPER_RUNTIME',
    'live_authority_unchanged': True,
    'completion_definition': program['definition_of_done'],
}
boot.setdefault('canonical_workflow_rules', {}).setdefault('delivery_policy', {})['product_completion_precedence'] = 'VISIBLE_WORKING_PRODUCT_OVER_NEW_ENGINE_ERA_OR_DOCUMENT'
boot['current_checkpoint'] = 'TOKENOSKOBI_PRODUCT_COMPLETION_PLAN_LOCKED'
boot['last_action'] = 'TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE_CANONICAL_PLAN_SYNC'
boot['next_safe_step'] = NEXT
boot['open_risks'] = [
    'PRODUCT_SURFACE_NOT_DEPLOYED',
    'NEWS_LIVE_HEALTH_NOT_REVERIFIED',
    'PANEL_URL_AND_AUTH_NOT_REVERIFIED',
    'ALCHEMY_HYBRID_RUNTIME_NOT_REVERIFIED',
    'INTERNAL_EXTERNAL_SECURITY_NOT_REVERIFIED',
    'SUCCESSFUL_WALLET_CLASSIFICATION_NOT_READY',
    'CHATBOT_AI_COUNCIL_SELF_HEALING_NOT_BOUND',
]
boot['updated_at'] = NOW
boot['updated_at_utc'] = NOW
atomic_json('PROJECT_BOOT.json', boot)

runtime = read_json('PROJECT_RUNTIME.json')
runtime['current_version'] = 'V4'
runtime['current_era'] = 'ERA64'
runtime['current_stage'] = PROGRAM_ID
runtime['current_status'] = STATUS
runtime['mode'] = 'USABLE_PRODUCT_VERTICAL_SLICE_CLOSURE'
runtime['product_completion_lock'] = True
runtime['no_new_era_until_product_completion'] = True
runtime['era64_deepening_status'] = 'FROZEN_AFTER_ERA64J_BY_PRODUCT_PRIORITY'
runtime['era64k_status'] = 'DEFERRED_NOT_NEXT_STEP'
runtime['last_verified_technical_baseline'] = baseline
runtime['product_completion_program'] = copy.deepcopy(program)
runtime['current_work_unit'] = {
    'id': PROGRAM_ID,
    'type': 'PRODUCT_COMPLETION_PROGRAM',
    'status': 'ACTIVE_PLAN_LOCKED',
    'stage': NEXT,
    'new_era': False,
    'next_step': NEXT,
}
runtime.setdefault('current_state', {})['project_status'] = 'ACTIVE_PRODUCT_COMPLETION_MODE'
runtime['current_state']['mode'] = 'USABLE_PRODUCT_VERTICAL_SLICE_CLOSURE'
runtime['current_state']['active_work_unit'] = copy.deepcopy(runtime['current_work_unit'])
runtime['last_action'] = 'TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE_CANONICAL_PLAN_SYNC'
runtime['last_result'] = 'PRODUCT_COMPLETION_PLAN_LOCKED_NO_NEW_ERA'
runtime['next_safe_step'] = NEXT
runtime['open_risks'] = copy.deepcopy(boot['open_risks']) + ['PAPER_RUNTIME_DISABLED_UNTIL_PRODUCT_ACCEPTANCE']
runtime['updated_at_utc'] = NOW
pointer = runtime.setdefault('canonical_runtime_pointer', {})
pointer['current_era'] = 'ERA64'
pointer['current_stage'] = PROGRAM_ID
pointer['current_status'] = STATUS
pointer['current_version_line'] = 'V4'
pointer['next_safe_step'] = NEXT
pointer['product_completion_lock'] = True
pointer['new_era_opened'] = False
pointer['era64k_status'] = 'DEFERRED_NOT_NEXT_STEP'
pointer['product_completion_program'] = copy.deepcopy(program)
atomic_json('PROJECT_RUNTIME.json', runtime)

roadmap = read_json('data/tokenoskobi_v1_v8_master_era_roadmap.json')
roadmap['product_completion_program'] = copy.deepcopy(program)
direction = roadmap.setdefault('current_direction', {})
direction['current_version'] = 'V4'
direction['current_era'] = 'ERA64'
direction['current_line'] = PROGRAM_ID
direction['current_stage'] = PROGRAM_ID
direction['current_status'] = STATUS
direction['status'] = 'PRODUCT_COMPLETION_PLAN_LOCKED'
direction['next_safe_step'] = NEXT
direction['product_completion_lock'] = True
direction['new_work_unit_opened'] = True
direction['new_era_opened'] = False
direction['era64_deepening_status'] = 'FROZEN_AFTER_ERA64J_BY_PRODUCT_PRIORITY'
direction['era64k_status'] = 'DEFERRED_NOT_NEXT_STEP'
direction['updated_at_utc'] = NOW
roadmap['deferred_by_product_completion_lock'] = [
    'ERA64K_DEX_SWAP_DIRECTION_TOKEN_METADATA_AND_PRICE_CONTEXT',
    'ANY_NEW_ERA_OR_ALT_ERA',
    'UNRELATED_ARCHITECTURE_OR_ENGINE_EXPANSION',
]
roadmap['updated_at_utc'] = NOW
atomic_json('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

roadmap_md = f'''# 03 ROADMAP - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
ERA64_DEEPENING=FROZEN_AFTER_ERA64J
CURRENT_STAGE={PROGRAM_ID}
CURRENT_STATUS={STATUS}
NO_NEW_ERA=true
ERA64K_STATUS=DEFERRED_NOT_NEXT_STEP
NEXT_SAFE_STEP={NEXT}

## Ürün Tamamlama Kuralı

Test, schema, doküman veya bağımsız motor artık ilerleme ölçüsü değildir. İlerleme yalnız kullanıcının canlı URL üzerinde açtığı ve kabul ettiği uçtan uca ürün akışıyla ölçülür. Aktif ürün adımını doğrudan bloke etmeyen engine derinleştirmesi, mimari genişleme, yeni belge, yeni ERA veya alt ERA yasaktır.

## Son Doğrulanmış Teknik Temel

- ERA64J receipt ve gas-cost zenginleştirmesi doğrulandı.
- 172/172 test geçti.
- 367 gerçek BSC transfer olayı ve 277 gerçek işlem kapsandı.
- Wallet, signing, order, live trade ve gerçek finansal yetki sıfır kaldı.
- Başarılı wallet sınıflandırması henüz hazır değildir.
- İlk kullanılabilir ürün kurulum denemesi hata verdi ve tamamen rollback edildi; canlı ürün yüzeyi kurulmadı.

## Zorunlu Ürün Kapanış Sırası

1. **Canlı gerçeklik, panel erişimi ve güvenlik doğrulaması** — NEWS canlılığı, kesin panel URL/auth, servisler, Alchemy hibrit bağlantısı, onchain gecikmesi ve iç/dış güvenlik read-only doğrulanır.
2. **Tek token giriş ekranı ve gerçek karar paketi** — BSC token adresi; gerçek onchain, kontrat, likidite, teknik, NEWS ve wallet bağlamı; 1m/5m/15m/1h/4h/1d online analiz; Risk Engine kararı; kanıtlar ve `VERI_YETERSIZ` davranışı.
3. **İnsan onayı, karar geçmişi ve sonuç takibi** — ACCEPT/REJECT/WAIT/REVIEW kaydı, tekrar açılabilir kanıt paketi ve zaman içindeki sonuç değişimi.
4. **DEX wallet/CEX balina performansı ve Obsidian grafiği** — Swap yönü, router/pool, metadata, fiyat, tüm maliyetler, kapalı döngü, kanıtlı başarılı wallet, 50 BTC eşdeğer balina ve CEX akışları.
5. **Harekât Subayı, AI konseyi, self-healing önerisi ve operasyonel istihbarat** — Chatbot; NVIDIA, ChatGPT/Codex, Claude, Gemini ve Copilot advisory rolleri; arıza teşhis/diff/test/onay döngüsü; DEX-relevant teknoloji ve saldırı istihbaratı; opportunity-cost kararı.
6. **Sınırlı paper trade** — Yalnız önceki adımlar kullanıcı tarafından kabul edildikten sonra, sıfır gerçek fonla, Risk Engine veto ve insan politika zarfı içinde.

## Ürün Bitti Sayılma Şartı

Canlı URL açılır; BSC token adresi kabul edilir; gerçek karar paketi üretilir; eksik veri açıkça gösterilir; risk kararı ve kanıtları görünür; insan kararı kaydedilir ve geçmişten açılır; sonuç takibi çalışır; sonrasında paper trade aynı akışa bağlanır.
'''
atomic_text('03_ROADMAP.md', roadmap_md)

almanac_body = f'''## TOKENOSKOBI PRODUCT COMPLETION PIVOT DECISION

- Timestamp UTC: `{NOW}`
- Status: `DECISION_RECORDED_PLAN_LOCKED`
- Program: `{PROGRAM_ID}`
- New ERA opened: `false`
- New alt ERA opened: `false`
- ERA64 deepening: `FROZEN_AFTER_ERA64J_BY_PRODUCT_PRIORITY`
- ERA64K: `DEFERRED_NOT_NEXT_STEP`
- Last verified technical baseline: `ERA64J`, `172/172_VERIFIED`, 367 real BSC events, 277 transactions
- Failed product builder attempt: `ROLLED_BACK_NO_PRODUCT_DEPLOYED`
- Broken builder payload cleanup: `INCLUDED_IN_CANONICAL_SYNC`
- Product completion metric: `USER_VISIBLE_END_TO_END_FLOW_ACCEPTED_BY_USER`
- Next safe step: `{NEXT}`
- Authority change: `NONE`
- Paper runtime: `DISABLED`
- Live trade: `DISABLED`
- Real financial authority: `0`
- Note: This record locks the product-completion direction; it does not claim the product is completed.'''
marker_upsert('04_ALMANAC.md', '<!-- PRODUCT_COMPLETION_PIVOT:BEGIN -->', '<!-- PRODUCT_COMPLETION_PIVOT:END -->', almanac_body)

atlas_body = '''## PRODUCT COMPLETION VERTICAL SLICE MAP

```text
USER / PHONE
  -> AUTHENTICATED LIVE PANEL
  -> BSC TOKEN ADDRESS INPUT
  -> SERVER-SIDE ADDRESS / CONTRACT VALIDATION
  -> HYBRID DATA INTAKE
       -> ALCHEMY WEBSOCKET / HTTP
       -> ALLOWLISTED PUBLIC BSC RPC FALLBACK + CROSS-CHECK
       -> GECKOTERMINAL MARKET / OHLCV / LIQUIDITY
       -> LOCAL CACHE / READMODEL
  -> CONTRACT / ONCHAIN / LIQUIDITY / TECHNICAL / NEWS / WALLET CONTEXT
  -> EVIDENCE POINTERS + DATA FRESHNESS
  -> RISK ENGINE: ALLOW / BLOCK / WAIT / REVIEW
  -> TRANSPARENT DECISION PACKET
  -> HUMAN ACCEPT / REJECT / WAIT / REVIEW
  -> APPEND-ONLY DECISION HISTORY
  -> OUTCOME TRACKING
  -> ONLY AFTER USER ACCEPTANCE: ZERO-REAL-FUNDS PAPER TRADE
```

```text
DEX / WALLET / CEX INTELLIGENCE
  -> SWAP CLASSIFICATION -> ROUTER / POOL / TOKEN METADATA
  -> PRICE + GAS + FEE + SLIPPAGE -> CLOSED CYCLES + CONFIDENCE
  -> CEX FLOWS + 50 BTC EQUIVALENT WHALE THRESHOLD
  -> OBSIDIAN-STYLE EVIDENCE GRAPH
  -> NO OWNERSHIP CLAIM WITHOUT EVIDENCE

HAREKAT SUBAYI
  -> CHATBOT STATUS / RISK / WHY / ALERT / APPROVAL
  -> NVIDIA + CHATGPT/CODEX + CLAUDE + GEMINI + COPILOT ADVISORY COUNCIL
  -> CONFLICT + RISK + OPPORTUNITY-COST RESOLUTION
  -> NO TRADE AUTHORITY

SELF-HEALING PROPOSAL LOOP
  -> DETECT -> DIAGNOSE -> PROPOSE PATCH / DIFF -> TEST + RED TEAM
  -> EXPLAIN RISK / ROLLBACK -> HUMAN APPROVAL -> APPLY ONLY AFTER APPROVAL

OPERATIONAL INTELLIGENCE
  -> DEX-RELEVANT ATTACK / PROTOCOL / PROVIDER / AI / HARDWARE / SOFTWARE CHANGE
  -> TOKENOSKOBI IMPACT -> VULNERABILITY / BENEFIT CHECK -> OPPORTUNITY COST
  -> APPLY / DEFER / REJECT RECOMMENDATION
```

- Panel display, review, human-decision and history surface only.
- Browser provider secret, wallet, signing veya order authority alamaz.
- Product progress visible user acceptance gerektirir.
- New ERA, unrelated engine deepening ve paper runtime core user loop kabulüne kadar blokludur.'''
marker_upsert('05_ATLAS.md', '<!-- PRODUCT_COMPLETION_VERTICAL_SLICE:BEGIN -->', '<!-- PRODUCT_COMPLETION_VERTICAL_SLICE:END -->', atlas_body)

master_state = f'''# 06 PROJECT MASTER STATE

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
ERA64_DEEPENING=FROZEN_AFTER_ERA64J_BY_PRODUCT_PRIORITY
CURRENT_STAGE={PROGRAM_ID}
CURRENT_STATUS={STATUS}
PRODUCT_COMPLETION_LOCK=true
NO_NEW_ERA=true
ERA64K_STATUS=DEFERRED_NOT_NEXT_STEP
NEXT_SAFE_STEP={NEXT}

LAST_VERIFIED_TECHNICAL_STAGE=ERA64J_HISTORICAL_TRANSFER_RECEIPT_AND_COST_ENRICHMENT
LAST_VERIFIED_TECHNICAL_HEAD={TECHNICAL_BASELINE_HEAD}
TECHNICAL_TEST_BASELINE=172/172_VERIFIED
REAL_BSC_EVENT_COUNT=367
REAL_BSC_TRANSACTION_COUNT=277
RECEIPT_GAS_COST_ENRICHMENT_COMPLETE=true
SUCCESSFUL_WALLET_CLASSIFICATION_READY=false

PRODUCT_SURFACE_DEPLOYED=false
LAST_PRODUCT_BUILDER_ATTEMPT=ROLLED_BACK_NO_PRODUCT_DEPLOYED
CANONICAL_PRODUCT_PLAN=LOCKED
CURRENT_PRODUCT_STEP=Canlı gerçeklik, panel erişimi ve güvenlik doğrulaması
CURRENT_PRODUCT_STEP_MODE=READ_ONLY
CURRENT_PRODUCT_STEP_ACCEPTANCE=NEWS_PANEL_ALCHEMY_LATENCY_INTERNAL_EXTERNAL_SECURITY_TRUTH

PAPER_RUNTIME=DISABLED
LIVE_TRADE=DISABLED
REAL_WALLET_AUTHORITY=0
REAL_SIGNING_AUTHORITY=0
REAL_ORDER_AUTHORITY=0
REAL_FINANCIAL_AUTHORITY=0

BLOCKERS=PRODUCT_SURFACE_NOT_DEPLOYED;NEWS_LIVE_HEALTH_NOT_REVERIFIED;PANEL_URL_AND_AUTH_NOT_REVERIFIED;ALCHEMY_HYBRID_RUNTIME_NOT_REVERIFIED;INTERNAL_EXTERNAL_SECURITY_NOT_REVERIFIED
'''
atomic_text('06_PROJECT_MASTER_STATE.md', master_state)

handoff = f'''# 07 PROJECT HANDOFF

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={PROGRAM_ID}
STATUS={STATUS}
PRODUCT_COMPLETION_LOCK=true
NO_NEW_ERA=true
ERA64K_STATUS=DEFERRED_NOT_NEXT_STEP
NEXT_SAFE_STEP={NEXT}

## Son Doğrulanmış Teknik Temel

- ERA64J doğrulandı: 172/172 test, 367 gerçek BSC olayı, 277 işlem ve tam receipt/gas-cost coverage.
- Başarılı wallet sınıflandırması hazır değildir.
- Paper runtime ve live trade kapalıdır; gerçek wallet/signing/order/financial authority sıfırdır.
- `034b163` ürün builder denemesi `PAYLOAD_MISSING` ile durdu ve rollback edildi; ürün yüzeyi kurulmadı.

## Yeni Pencerenin Tek Görevi

Önce `README.md` dosyasını okuyup mandatory canonical boot sırasını eksiksiz uygula. Local workspace erişimi varsa local workspace ve local Git, GitHub remote’dan önce doğrulansın. Boot tamamlandıktan sonra yalnız `{NEXT}` yürütülsün.

Bu adım read-only olacaktır ve şunları kanıtlayacaktır: NEWS katmanı canlı mı; panelin kesin canlı URL/auth yolu nedir ve telefondan açılıyor mu; Alchemy ve hibrit fallback zinciri çalışıyor mu; onchain-to-panel gecikmesi nedir; iç/dış güvenlik güncel olarak ne durumdadır.

Yeni ERA, alt ERA, yeni canonical belge, engine derinleştirmesi, paper runtime, live trade veya finansal authority açılmayacaktır. Sonuç tek doğrulanmış tablo olarak kullanıcıya sunulacaktır.'''
atomic_text('07_PROJECT_HANDOFF.md', handoff)

history = read_json('PROJECT_HISTORY.json')
event_id = 'TOKENOSKOBI_PRODUCT_COMPLETION_PIVOT_AND_CANONICAL_PLAN_LOCK_V1'
event = {
    'event_id': event_id,
    'event': 'PRODUCT_COMPLETION_PIVOT_AND_CANONICAL_PLAN_LOCK',
    'timestamp_utc': NOW,
    'head_before_commit': HEAD_BEFORE,
    'program': PROGRAM_ID,
    'status': 'PLAN_LOCKED_NO_NEW_ERA',
    'last_verified_technical_baseline': baseline,
    'failed_product_builder_attempt': 'ROLLED_BACK_NO_PRODUCT_DEPLOYED',
    'new_era_opened': False,
    'era64k_status': 'DEFERRED_NOT_NEXT_STEP',
    'next_safe_step': NEXT,
    'authority_change': False,
    'paper_runtime': 'DISABLED',
    'live_trade': 'DISABLED',
    'real_financial_authority': 0,
    'updated_files': [
        '02_MANIFESTO.md', 'PROJECT_BOOT.json', 'PROJECT_RUNTIME.json', 'PROJECT_HISTORY.json',
        'data/tokenoskobi_v1_v8_master_era_roadmap.json', '03_ROADMAP.md', '04_ALMANAC.md',
        '05_ATLAS.md', '06_PROJECT_MASTER_STATE.md', '07_PROJECT_HANDOFF.md',
        'reports/LATEST_TK_AI_HANDOFF.md', 'data/control/latest_tk_machine_state.json',
    ],
}
events = history.setdefault('events', [])
history['events'] = [item for item in events if item.get('event_id') != event_id]
history['events'].append(event)
history['updated_at_utc'] = NOW
atomic_json('PROJECT_HISTORY.json', history)

latest_handoff = f'''# TOKENOSKOBI LATEST HANDOFF

```text
CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={PROGRAM_ID}
STATUS={STATUS}
NO_NEW_ERA=true
ERA64K_STATUS=DEFERRED_NOT_NEXT_STEP
LAST_VERIFIED_TECHNICAL_BASELINE=ERA64J_172_OF_172
PRODUCT_SURFACE_DEPLOYED=false
NEXT_SAFE_STEP={NEXT}
```

Tokenoskobi is now locked to user-visible product completion. The next window must boot from README and perform only the read-only live NEWS, panel, Alchemy/hybrid, latency and internal/external security truth verification. No financial authority is opened.'''
atomic_text('reports/LATEST_TK_AI_HANDOFF.md', latest_handoff)

machine = read_json('data/control/latest_tk_machine_state.json')
machine['current_version'] = 'V4'
machine['current_era'] = 'ERA64'
machine['current_stage'] = PROGRAM_ID
machine['current_status'] = STATUS
machine['product_completion_lock'] = True
machine['no_new_era'] = True
machine['era64k_status'] = 'DEFERRED_NOT_NEXT_STEP'
machine['next_safe_step'] = NEXT
machine['product_completion_program'] = copy.deepcopy(program)
machine['runtime_product_completion_pointer'] = {
    'authority': 'PROJECT_RUNTIME.json',
    'current_stage': PROGRAM_ID,
    'current_status': STATUS,
    'next_safe_step': NEXT,
}
machine['boot_json'] = copy.deepcopy(boot)
if 'runtime_json' in machine:
    machine['runtime_json'] = copy.deepcopy(runtime)
machine['master_roadmap_current_direction'] = copy.deepcopy(direction)
machine['updated_at_utc'] = NOW
atomic_json('data/control/latest_tk_machine_state.json', machine)

print('CANONICAL_PRODUCT_PLAN_WRITE=COMPLETED')
PY

python3 <<'PY'
import json
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
NEXT = 'PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION'
PROGRAM_ID = 'TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE'
load = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8'))
boot = load('PROJECT_BOOT.json')
runtime = load('PROJECT_RUNTIME.json')
roadmap = load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
history = load('PROJECT_HISTORY.json')
machine = load('data/control/latest_tk_machine_state.json')

assert boot['boot_version'] == '3.4'
assert boot['product_delivery_contract']['new_era_forbidden_while_locked'] is True
assert boot['next_safe_step'] == NEXT
assert runtime['current_stage'] == PROGRAM_ID
assert runtime['current_status'] == 'PRODUCT_COMPLETION_MODE_ACTIVE_PLAN_LOCKED'
assert runtime['product_completion_lock'] is True
assert runtime['no_new_era_until_product_completion'] is True
assert runtime['next_safe_step'] == NEXT
assert runtime['era64k_status'] == 'DEFERRED_NOT_NEXT_STEP'
assert roadmap['current_direction']['current_stage'] == PROGRAM_ID
assert roadmap['current_direction']['next_safe_step'] == NEXT
assert roadmap['product_completion_program']['ordered_steps'][0]['id'] == NEXT
assert len(roadmap['product_completion_program']['ordered_steps']) == 6
assert any(item.get('event_id') == 'TOKENOSKOBI_PRODUCT_COMPLETION_PIVOT_AND_CANONICAL_PLAN_LOCK_V1' for item in history['events'])
assert machine['current_stage'] == PROGRAM_ID
assert machine['next_safe_step'] == NEXT

for rel, token in [
    ('02_MANIFESTO.md', '<!-- PRODUCT_COMPLETION_CONSTITUTION:BEGIN -->'),
    ('03_ROADMAP.md', NEXT), ('04_ALMANAC.md', '<!-- PRODUCT_COMPLETION_PIVOT:BEGIN -->'),
    ('05_ATLAS.md', '<!-- PRODUCT_COMPLETION_VERTICAL_SLICE:BEGIN -->'),
    ('06_PROJECT_MASTER_STATE.md', NEXT), ('07_PROJECT_HANDOFF.md', NEXT),
    ('reports/LATEST_TK_AI_HANDOFF.md', NEXT),
]:
    assert token in (ROOT / rel).read_text(encoding='utf-8'), rel

authority = runtime['authority']
assert str(authority['live_trade']).upper() == 'DISABLED'
assert str(authority['paper_trade']).upper().startswith('DISABLED')
assert int(authority['real_order_authority']) == 0
assert int(authority['real_signing_authority']) == 0
assert int(authority['real_trade_authority']) == 0
assert int(authority['real_wallet_authority']) == 0

for rel in ['PROJECT_BOOT.json', 'PROJECT_RUNTIME.json', 'PROJECT_HISTORY.json',
            'data/tokenoskobi_v1_v8_master_era_roadmap.json',
            'data/control/latest_tk_machine_state.json']:
    json.loads((ROOT / rel).read_text(encoding='utf-8'))

print('CANONICAL_PRODUCT_PLAN_VALIDATION=VERIFIED')
print('AUTHORITY_BOUNDARIES=UNCHANGED_VERIFIED')
print('ORDERED_PRODUCT_STEPS=6_VERIFIED')
PY

rm -rf tools/.tokenoskobi_product_vertical_slice_payload_v1
rm -f tools/build_tokenoskobi_product_vertical_slice_v1.sh
rm -f "$SELF_REL"

git diff --check

git add -A -- \
  02_MANIFESTO.md PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json 03_ROADMAP.md 04_ALMANAC.md \
  05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  data/control/latest_tk_machine_state.json \
  tools/build_tokenoskobi_product_vertical_slice_v1.sh \
  tools/.tokenoskobi_product_vertical_slice_payload_v1 "$SELF_REL"
git add -f reports/LATEST_TK_AI_HANDOFF.md

ALLOWED='^(02_MANIFESTO\.md|PROJECT_BOOT\.json|PROJECT_RUNTIME\.json|PROJECT_HISTORY\.json|data/tokenoskobi_v1_v8_master_era_roadmap\.json|03_ROADMAP\.md|04_ALMANAC\.md|05_ATLAS\.md|06_PROJECT_MASTER_STATE\.md|07_PROJECT_HANDOFF\.md|reports/LATEST_TK_AI_HANDOFF\.md|data/control/latest_tk_machine_state\.json|tools/build_tokenoskobi_product_vertical_slice_v1\.sh|tools/tokenoskobi_product_completion_canonical_lock_and_handoff\.sh|tools/\.tokenoskobi_product_vertical_slice_payload_v1/.*)$'
while IFS= read -r changed; do
  [[ "$changed" =~ $ALLOWED ]] || { echo "BLOCKED=UNEXPECTED_STAGED_FILE:$changed"; exit 1; }
done < <(git diff --cached --name-only)

[[ -n "$(git diff --cached --name-only)" ]] || { echo "BLOCKED=NO_CANONICAL_CHANGES"; exit 1; }

git diff --cached --stat
git commit -m "Product: lock usable vertical slice completion plan"
COMMITTED=1
git push origin main

FINAL_HEAD="$(git rev-parse HEAD)"
REMOTE_FINAL="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
[[ "$FINAL_HEAD" == "$REMOTE_FINAL" ]] || { echo "BLOCKED=REMOTE_VERIFY_FAILED:$FINAL_HEAD:$REMOTE_FINAL"; exit 1; }
[[ -z "$(git status --short)" ]] || { echo "BLOCKED=WORKTREE_NOT_CLEAN_AFTER_PUSH"; git status --short; exit 1; }

trap - ERR
rm -f "$BACKUP_LIST"
trap - EXIT

echo "PRODUCT_COMPLETION_CANONICAL_SYNC=VERIFIED_GITHUB_SEALED"
echo "CURRENT_STAGE=TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE"
echo "CURRENT_STATUS=PRODUCT_COMPLETION_MODE_ACTIVE_PLAN_LOCKED"
echo "NO_NEW_ERA=true"
echo "ERA64K_STATUS=DEFERRED_NOT_NEXT_STEP"
echo "BROKEN_PRODUCT_BUILDER_CLEANUP=COMPLETED"
echo "AUTHORITY_CHANGE=NONE"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REAL_FINANCIAL_AUTHORITY=0"
echo "NEXT_SAFE_STEP=PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$FINAL_HEAD"
