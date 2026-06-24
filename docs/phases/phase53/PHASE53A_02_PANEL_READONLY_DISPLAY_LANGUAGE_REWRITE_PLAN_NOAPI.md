# PHASE53A_02_PANEL_READONLY_DISPLAY_LANGUAGE_REWRITE_PLAN_NOAPI

FINAL_GATE=PASS_PHASE53A_02_PANEL_READONLY_DISPLAY_LANGUAGE_REWRITE_PLAN_NOAPI
DECISION=READONLY_REWRITE_PLAN_ACCEPTED_READY_FOR_READMODEL_FIELD_AUTHORITY_AUDIT

MODE=REWRITE_PLAN_NOAPI
PATCH_ALLOWED_NOW=false
REQUIRES_EXPLICIT_APPROVAL=true

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

## Three-Class Protocol

| Class | Count |
|---|---:|
| REWRITE_REQUIRED | 18 |
| SAFE_CONTEXT_KEEP | 43 |
| FALSE_POSITIVE_IGNORE | 21 |

## Metrics

TOTAL_HIT_COUNT=82
REWRITE_REQUIRED_COUNT=18
SAFE_CONTEXT_KEEP_COUNT=43
FALSE_POSITIVE_IGNORE_COUNT=21
REWRITE_AUDIT_LOG_COUNT=18
LARGEST_REWRITE_SURFACE_PATH=`active_panel_8096/current/data/production_v2_control_center_data.json`
LARGEST_REWRITE_SURFACE_REWRITE_COUNT=4

## Term Rewrite Dictionary

| Unsafe Term | Safe ReadOnly Display | Class Rule | Reason |
|---|---|---|---|
| Trade | Market Risk Context | REWRITE_REQUIRED_IF_UI_LABEL | Gözlemci kimliğiyle uyumlu. |
| Paper Trade | Simulation Outcome Memory | REWRITE_REQUIRED | Eylem değil, simülasyon sonucu. |
| Wallet | Wallet Risk Context | REWRITE_REQUIRED_IF_UI_LABEL | Sadece risk odaklı izleme. |
| Execute | Readonly Review | REWRITE_REQUIRED | İcra değil, inceleme. |
| Execution | Runtime Boundary Status | REWRITE_REQUIRED | İcra yüzeyi değil, sınır durumu. |
| Position | Exposure Context | REWRITE_REQUIRED_IF_UI_LABEL | Konum/pozisyon değil, maruziyet. |
| Entry | Entry Condition Observed | REWRITE_REQUIRED_IF_UI_LABEL | Giriş emri değil, koşul gözlemi. |
| Exit | Exit Condition Observed | REWRITE_REQUIRED_IF_UI_LABEL | Çıkış emri değil, koşul gözlemi. |
| Apply | Readonly Proposal Context | REWRITE_REQUIRED_IF_UI_LABEL | Uygulama değil, teklif bağlamı. |
| Approve | Evidence Review Acknowledge | REWRITE_REQUIRED | Onay sadece kanıt inceleme onayı olabilir. |
| Confirm | Evidence Review Acknowledge | REWRITE_REQUIRED | Teyit trade/wallet teyidi olamaz. |
| Swap | Route Risk Context | REWRITE_REQUIRED | Swap eylem değil, rota riski bağlamı. |
| Override | Policy Blocked | REWRITE_REQUIRED | Override yasaktır; policy blocked olarak gösterilir. |

## Phrase Rewrite Dictionary

| Unsafe Phrase | Safe Phrase | Class | Reason |
|---|---|---|---|
| Paper Trade Özeti | Simulation Outcome Memory | REWRITE_REQUIRED | Paper trade evokes execution. Rewrite as simulation outcome memory. |
| Paper Trade Ozeti | Simulation Outcome Memory | REWRITE_REQUIRED | Paper trade evokes execution. Rewrite as simulation outcome memory. |
| Execution Locks | Runtime Boundary Status | REWRITE_REQUIRED | Execution wording implies controllable action surface. Rewrite as boundary status. |
| Whale Wallet İzleme | Whale Entity Risk Context | REWRITE_REQUIRED | Wallet wording can imply wallet surface. Rewrite as entity risk context. |
| Whale Wallet Izleme | Whale Entity Risk Context | REWRITE_REQUIRED | Wallet wording can imply wallet surface. Rewrite as entity risk context. |
| entry/slippage/SL/TP | Entry Condition / Slippage / SL-TP Observation | REWRITE_REQUIRED | Entry wording must be observational. |
| Live/auto kilidi | Runtime Boundary Status | REWRITE_REQUIRED | Auto/live wording must remain boundary status only. |

## Rewrite Surface Rank

| Path | Rewrite Required | Safe Context Keep | False Positive Ignore | Total |
|---|---:|---:|---:|---:|
| `active_panel_8096/current/data/production_v2_control_center_data.json` | 4 | 7 | 0 | 11 |
| `active_panel_8096/current/data/risk_security_preview_data.json` | 3 | 11 | 0 | 14 |
| `active_panel_8096/current/mobile_pageflow/index.html` | 3 | 1 | 2 | 6 |
| `active_panel_8096/current/panel_v2/data/panel_v2_model.json` | 3 | 1 | 0 | 4 |
| `active_panel_8096/current/mobile_pageflow/data/mobile_strict_pageflow_selector_model.json` | 3 | 1 | 0 | 4 |
| `active_panel_8096/current/panel_v2/index.html` | 2 | 2 | 0 | 4 |
| `active_panel_8096/current/index.html` | 0 | 14 | 5 | 19 |
| `active_panel_8096/current/panel_v2/assets/panel_v2.css` | 0 | 0 | 14 | 14 |
| `active_panel_8096/current/data/phase41_command_center_binding_v1.json` | 0 | 4 | 0 | 4 |
| `active_panel_8096/current/data/system_control_status_readmodel_view.json` | 0 | 2 | 0 | 2 |

## Rewrite Audit Log

Every REWRITE_REQUIRED item is locked as PATCH_ALLOWED_NOW=false.

| Plan ID | Location | Term | Safe Replacement | Patch Allowed Now | Requires Approval | Security Reason |
|---|---|---|---|---|---|---|
| PH53A02-RW-0005 | `active_panel_8096/current/data/production_v2_control_center_data.json`:22 | TRADE | MARKET_RISK_CONTEXT | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0009 | `active_panel_8096/current/data/production_v2_control_center_data.json`:500 | EXECUTE | READONLY_REVIEW | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0011 | `active_panel_8096/current/data/production_v2_control_center_data.json`:183 | WALLET | WALLET_RISK_CONTEXT | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0012 | `active_panel_8096/current/data/production_v2_control_center_data.json`:189 | WALLET | WALLET_RISK_CONTEXT | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0020 | `active_panel_8096/current/data/risk_security_preview_data.json`:93 | EXECUTE | READONLY_REVIEW | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0026 | `active_panel_8096/current/data/risk_security_preview_data.json`:353 | ENTRY | ENTRY_CONDITION_OBSERVED | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0029 | `active_panel_8096/current/data/risk_security_preview_data.json`:546 | ENTRY | ENTRY_CONDITION_OBSERVED | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0051 | `active_panel_8096/current/mobile_pageflow/data/mobile_strict_pageflow_selector_model.json`:35 | TRADE | MARKET_RISK_CONTEXT | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0052 | `active_panel_8096/current/mobile_pageflow/data/mobile_strict_pageflow_selector_model.json`:218 | WALLET | WALLET_RISK_CONTEXT | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0053 | `active_panel_8096/current/mobile_pageflow/data/mobile_strict_pageflow_selector_model.json`:225 | WALLET | WALLET_RISK_CONTEXT | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0055 | `active_panel_8096/current/mobile_pageflow/index.html`:1223 | TRADE | MARKET_RISK_CONTEXT | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0056 | `active_panel_8096/current/mobile_pageflow/index.html`:1498 | WALLET | WALLET_RISK_CONTEXT | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0057 | `active_panel_8096/current/mobile_pageflow/index.html`:1534 | WALLET | WALLET_RISK_CONTEXT | false | true | Explicit action-like UI phrase must be rewritten. |
| PH53A02-RW-0076 | `active_panel_8096/current/panel_v2/data/panel_v2_model.json`:143 | TRADE | MARKET_RISK_CONTEXT | false | true | Unsafe action-language hit from panel audit. |
| PH53A02-RW-0077 | `active_panel_8096/current/panel_v2/data/panel_v2_model.json`:135 | EXECUTE | READONLY_REVIEW | false | true | Unsafe action-language hit from panel audit. |
| PH53A02-RW-0078 | `active_panel_8096/current/panel_v2/data/panel_v2_model.json`:159 | APPLY | READONLY_PROPOSAL_CONTEXT | false | true | Unsafe action-language hit from panel audit. |
| PH53A02-RW-0080 | `active_panel_8096/current/panel_v2/index.html`:73 | TRADE | MARKET_RISK_CONTEXT | false | true | Unsafe action-language hit from panel audit. |
| PH53A02-RW-0082 | `active_panel_8096/current/panel_v2/index.html`:75 | APPLY | READONLY_PROPOSAL_CONTEXT | false | true | Unsafe action-language hit from panel audit. |

## Red Team Rule

- REWRITE_REQUIRED: plan only, no patch.
- SAFE_CONTEXT_KEEP: preserve doctrine defense text.
- FALSE_POSITIVE_IGNORE: do not touch CSS or technical false positives.

## Protected State

DB_SHA_CHANGED=false
PANEL_SHA_CHANGED=false
PROTECTED_DIFF_EMPTY=true

AUDIT_CHECK_COUNT=48
AUDIT_FAIL_COUNT=0
REVIEW_FINDING_COUNT=3

NEXT_SAFE_STEP=PHASE53A_02_READMODEL_FIELD_AUTHORITY_AUDIT_NOAPI
