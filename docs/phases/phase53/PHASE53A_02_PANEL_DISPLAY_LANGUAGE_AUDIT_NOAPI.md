# PHASE53A_02_PANEL_DISPLAY_LANGUAGE_AUDIT_NOAPI

FINAL_GATE=PASS_PHASE53A_02_PANEL_DISPLAY_LANGUAGE_AUDIT_NOAPI
DECISION=PANEL_DISPLAY_LANGUAGE_FINDINGS_READY_FOR_READONLY_REWRITE_PLAN

MODE=READONLY_PANEL_AUDIT_NOAPI
SCAN_TARGET=active_panel_8096/current

DB_WRITE=false
PANEL_WRITE=false
RUNTIME_CHANGE=false
SERVICE_CHANGE=false
PROVIDER_FETCH=false
TRADE_AUTHORITY=0
WALLET_AUTHORITY=0
LIVE_TRADE=0
PAPER_TRADE=0
AUTO_APPLY=0
HARD_BLOCK_BYPASS=0

## Red Team Question

Mevcut panel kaynaklarında BUY, SELL, TRADE, SWAP veya EXECUTE fiillerini içeren en büyük yüzey veya bileşen hangisidir?

## Answer

LARGEST_SURFACE_PATH=`active_panel_8096/current/index.html`
LARGEST_SURFACE_TOTAL_HITS=19
LARGEST_SURFACE_UNSAFE_HITS=4

## Metrics

SCANNED_TEXT_FILE_COUNT=15
PANEL_ACTION_TERM_HIT_COUNT=82
UNSAFE_ACTION_LANGUAGE_HIT_COUNT=25
REVIEW_SAFE_CONTEXT_HIT_COUNT=57
ACTION_TERM_COUNT=16

## Term Summary

| Term | Total | Unsafe | Review/Safe Context | Safe Replacement |
|---|---:|---:|---:|---|
| WALLET | 14 | 10 | 4 | WALLET_RISK_CONTEXT |
| TRADE | 22 | 6 | 16 | MARKET_RISK_CONTEXT |
| EXECUTE | 9 | 3 | 6 | READONLY_REVIEW |
| POSITION | 21 | 2 | 19 | EXPOSURE_CONTEXT |
| ENTRY | 11 | 2 | 9 | ENTRY_CONDITION_OBSERVED |
| APPLY | 5 | 2 | 3 | READONLY_PROPOSAL_CONTEXT |

## Largest File Surfaces

| Path | Total Hits | Unsafe Hits | Review Hits |
|---|---:|---:|---:|
| `active_panel_8096/current/index.html` | 19 | 4 | 15 |
| `active_panel_8096/current/data/production_v2_control_center_data.json` | 11 | 4 | 7 |
| `active_panel_8096/current/data/risk_security_preview_data.json` | 14 | 3 | 11 |
| `active_panel_8096/current/mobile_pageflow/index.html` | 6 | 3 | 3 |
| `active_panel_8096/current/panel_v2/data/panel_v2_model.json` | 4 | 3 | 1 |
| `active_panel_8096/current/mobile_pageflow/data/mobile_strict_pageflow_selector_model.json` | 4 | 3 | 1 |
| `active_panel_8096/current/panel_v2/assets/panel_v2.css` | 14 | 2 | 12 |
| `active_panel_8096/current/panel_v2/index.html` | 4 | 2 | 2 |
| `active_panel_8096/current/data/system_control_status_readmodel_view.json` | 2 | 1 | 1 |
| `active_panel_8096/current/data/phase41_command_center_binding_v1.json` | 4 | 0 | 4 |

## Unsafe Action-Language Findings

| Location | Term | Gap Class | Severity | Safe Replacement | Context |
|---|---|---|---|---|---|
| `active_panel_8096/current/data/production_v2_control_center_data.json`:22 | TRADE | SEMANTIC_ACTION_LEAK | HIGH | MARKET_RISK_CONTEXT | ezi" }, { "key": "paper_trade_ozeti", "label": "Paper Trade Özeti", "icon": "panel_assets/icons_panel_384/komuta_merkezi/paper_trade_ozeti_ |
| `active_panel_8096/current/data/production_v2_control_center_data.json`:500 | EXECUTE | AUTHORITY_LEAK | CRITICAL | READONLY_REVIEW | "center_key": "sistem", "panel_label": "Sistem Kontrol", "sub_panel": "Execution Locks", "cards": [ "live_auto_lock" ], "purpose": "Live |
| `active_panel_8096/current/data/production_v2_control_center_data.json`:183 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | balina_takip_merkezi", "label": "Balina Takip Merkezi", "description": "Whale wallet, akıllı para, büyük transfer ve borsa akışı", "icon": "panel_assets/icons_panel_384 |
| `active_panel_8096/current/data/production_v2_control_center_data.json`:189 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | "modules": [ { "key": "whale_wallet_i_zleme", "label": "Whale Wallet İzleme", "icon": "panel_assets/icons_panel_384/balina_takip_merkezi/whale_walle |
| `active_panel_8096/current/data/risk_security_preview_data.json`:93 | EXECUTE | AUTHORITY_LEAK | CRITICAL | READONLY_REVIEW | "center_key": "sistem", "panel_label": "Sistem Kontrol", "sub_panel": "Execution Locks", "cards": [ "live_auto_lock" ], "purpose": "Live/auto ki |
| `active_panel_8096/current/data/risk_security_preview_data.json`:353 | ENTRY | SEMANTIC_ACTION_LEAK | HIGH | ENTRY_CONDITION_OBSERVED | e": "Outcome Memory Hazırlığı", "status": "STUB_READY", "details": "Planlanan entry/slippage/SL/TP ileride paper/outcome sonucu ile karşılaştırılacak." }, { "c |
| `active_panel_8096/current/data/risk_security_preview_data.json`:546 | ENTRY | SEMANTIC_ACTION_LEAK | HIGH | ENTRY_CONDITION_OBSERVED | e": "Outcome Memory Hazırlığı", "status": "STUB_READY", "details": "Planlanan entry/slippage/SL/TP ileride paper/outcome sonucu ile karşılaştırılacak." }, "morg_auto |
| `active_panel_8096/current/data/system_control_status_readmodel_view.json`:133 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | t_trade": true }, "scope_warning": "Bu panel yalnızca status readmodel aynasıdır; OS, wallet veya API-key genel güvenlik garantisi değildir.", "single_manual_refresh_real": true, |
| `active_panel_8096/current/index.html`:757 | TRADE | SEMANTIC_ACTION_LEAK | HIGH | MARKET_RISK_CONTEXT | if bağlantı kuruldu. Veri tabloları şu an boş başlangıç durumunda. Panel sadece gösterir; trade, provider fetch, paper/live ve wallet/signing yetkisi yoktur."; box.appendChild(note... |
| `active_panel_8096/current/index.html`:757 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | u an boş başlangıç durumunda. Panel sadece gösterir; trade, provider fetch, paper/live ve wallet/signing yetkisi yoktur."; box.appendChild(note); } fetch(DATA_URL, {cache: "no-s |
| `active_panel_8096/current/index.html`:904 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | v> <div class="phase12-status-note">Bu panel yalnızca status readmodel aynasıdır; OS, wallet veya API-key genel güvenlik garantisi değildir.</div> </div> </section> <style id="phas |
| `active_panel_8096/current/index.html`:1053 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | iv class="psv-note">Secret panelde gösterilmez, log’a yazılmaz, AI görmez. Canlı işlem ve wallet signing bağlı değildir.</div> <div class="psv-mini">Kaydet/Test auth’lu .xyz panel ... |
| `active_panel_8096/current/mobile_pageflow/data/mobile_strict_pageflow_selector_model.json`:35 | TRADE | SEMANTIC_ACTION_LEAK | HIGH | MARKET_RISK_CONTEXT | "CK" }, { "key": "paper_trade_ozeti", "title": "Paper Trade Özeti", "status": "Normal", "icon": "panel_assets/icons_panel_384/kom |
| `active_panel_8096/current/mobile_pageflow/data/mobile_strict_pageflow_selector_model.json`:218 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | balina_takip_merkezi", "title": "Balina Takip Merkezi", "description": "Whale wallet, akıllı para, büyük transfer ve borsa akışı", "icon": "panel_assets/icons_panel_384 |
| `active_panel_8096/current/mobile_pageflow/data/mobile_strict_pageflow_selector_model.json`:225 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | "modules": [ { "key": "whale_wallet_i_zleme", "title": "Whale Wallet İzleme", "status": "Normal", "icon": "panel_assets/icons_panel_384/ba |
| `active_panel_8096/current/mobile_pageflow/index.html`:1223 | TRADE | SEMANTIC_ACTION_LEAK | HIGH | MARKET_RISK_CONTEXT | eti_384.jpg" alt=""></div> <div class="module-title" data-measure-title="1">Paper Trade Özeti</div> <div class="module-status" data-measure-status="1">● Normal</div> |
| `active_panel_8096/current/mobile_pageflow/index.html`:1498 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | <div class="center-head-text"> <h1>Balina Takip Merkezi</h1> <p>Whale wallet, akıllı para, büyük transfer ve borsa akışı</p> </div> </header> <se |
| `active_panel_8096/current/mobile_pageflow/index.html`:1534 | WALLET | SEMANTIC_ACTION_LEAK | HIGH | WALLET_RISK_CONTEXT | eme_384.jpg" alt=""></div> <div class="module-title" data-measure-title="1">Whale Wallet İzleme</div> <div class="module-status" data-measure-status="1">● Normal</div> |
| `active_panel_8096/current/panel_v2/assets/panel_v2.css`:50 | POSITION | SEMANTIC_ACTION_LEAK | HIGH | EXPOSURE_CONTEXT | color:var(--green)}.metric .amber{color:var(--amber)}.metric .red{color:var(--red)}.spark{position:absolute;right:8px;bottom:8px;width:78px;height:18px;border-bottom:1px solid rgba... |
| `active_panel_8096/current/panel_v2/assets/panel_v2.css`:51 | POSITION | SEMANTIC_ACTION_LEAK | HIGH | EXPOSURE_CONTEXT | 8px;bottom:8px;width:78px;height:18px;border-bottom:1px solid rgba(81,255,145,.32)} .core{position:relative;border:1px solid rgba(32,233,255,.42);background:rgba(2,11,18,.72);clip-... |
| `active_panel_8096/current/panel_v2/data/panel_v2_model.json`:143 | TRADE | SEMANTIC_ACTION_LEAK | HIGH | MARKET_RISK_CONTEXT | cy": "Kapalı" } ], "alerts": [ { "level": "Yüksek", "text": "Live trade kilidi kapalı tutuluyor.", "time": "Şimdi" }, { "level": "Orta", |
| `active_panel_8096/current/panel_v2/data/panel_v2_model.json`:135 | EXECUTE | AUTHORITY_LEAK | CRITICAL | READONLY_REVIEW | come Memory", "status": "Normal", "latency": "OK" }, { "name": "Execution Gate", "status": "Normal", "latency": "Kapalı" } ], "alerts": [ { |
| `active_panel_8096/current/panel_v2/data/panel_v2_model.json`:159 | APPLY | SEMANTIC_ACTION_LEAK | HIGH | READONLY_PROPOSAL_CONTEXT | "time": "Plan" } ], "decision_queue": [ { "item": "Panel V2 route apply", "status": "Beklemede" }, { "item": "Data binding post-audit", |
| `active_panel_8096/current/panel_v2/index.html`:73 | TRADE | SEMANTIC_ACTION_LEAK | HIGH | MARKET_RISK_CONTEXT | rpanel"><h2>KRİTİK UYARILAR</h2><div class="alert high"><div><b>Yüksek</b><br><small>Live trade kilidi kapalı tutuluyor.</small></div><small>Şimdi</small></div><div class="alert ">... |
| `active_panel_8096/current/panel_v2/index.html`:75 | APPLY | SEMANTIC_ACTION_LEAK | HIGH | READONLY_PROPOSAL_CONTEXT | <section class="rpanel"><h2>KARAR KUYRUĞU</h2><div class="queue"><span>Panel V2 route apply</span><em>Beklemede</em></div><div class="queue"><span>Data binding post-audit</span><em... |

## READONLY_DISPLAY Rewrite Plan

| Risk Term | Safe Display Language | Reason |
|---|---|---|
| BUY | ENTRY_CONDITION_OBSERVED | Remove direct purchase call-to-action. |
| SELL | EXIT_CONDITION_OBSERVED | Remove direct sale call-to-action. |
| TRADE | MARKET_RISK_CONTEXT | Keep system as risk observer, not trading system. |
| SWAP | ROUTE_RISK_CONTEXT | Convert action verb into route observation. |
| EXECUTE | READONLY_REVIEW | No execution semantics in Consumer Binding. |
| APPROVE | EVIDENCE_REVIEW_ACKNOWLEDGE | Approval may only mean evidence review acknowledgement. |
| CONFIRM | EVIDENCE_REVIEW_ACKNOWLEDGE | Confirmation may not imply trade or wallet confirmation. |
| WALLET CONNECT | WALLET_SURFACE_OBSERVATION | No wallet-connect action surface in read-only panel. |
| AUTO APPLY | PROPOSAL_REVIEW_ONLY | Auto-apply is forbidden. |
| OVERRIDE | POLICY_BLOCKED | Hard-Block and policy blocks are non-overridable. |
| HARD_BLOCK display | READONLY_OBSERVATION_BLOCKED | Must not render as Trade Failed or Execution Failed. |

## Negative Action Test

- RISK_STATE=HARD_BLOCK must not render as Trade Failed, Execution Failed, Order Blocked, Buy Blocked, or Sell Blocked.
- Safe render target: ReadOnly Observation Blocked / Risk Observation Restricted / Policy Blocked / Evidence Review Required.
- Consumer Binding must not render Buy, Sell, Execute, Approve Trade, Confirm Trade, Wallet Connect.
- High confidence must not render Permission Granted, Trade Ready, or Execute.

## Protected State

DB_SHA_CHANGED=false
PANEL_SHA_CHANGED=false
PROTECTED_DIFF_EMPTY=true

AUDIT_CHECK_COUNT=39
AUDIT_FAIL_COUNT=0
REVIEW_FINDING_COUNT=2

NEXT_SAFE_STEP=PHASE53A_02_PANEL_READONLY_DISPLAY_LANGUAGE_REWRITE_PLAN_NOAPI
