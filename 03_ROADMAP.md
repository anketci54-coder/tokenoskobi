<!-- CANONICAL_WORKFLOW_RULES_LOCK_START -->
## CANONICAL WORKFLOW RULES LOCK

Updated UTC: `2026-07-08T10:38:42.760735Z`

These rules are mandatory for every new ChatGPT window.

### Startup

Read in this order:

1. `PROJECT_RUNTIME.json`
2. `PROJECT_BOOT.json`
3. `06_PROJECT_MASTER_STATE.md`
4. `07_PROJECT_HANDOFF.md`
5. `02_MANIFESTO.md`
6. `03_ROADMAP.md`

### ERA Rule

- `ERA` means main software/module milestone only.
- Do not create a new ERA for plan, test, audit, risk decision, Go/No-Go, seal, documentation cleanup, or state normalization.
- Use A/B/C/D/E/F under the same ERA.
- Use A_1/A_2 only when the same sub-area truly needs another layer.
- Example: `ERA52A`, `ERA52B`, `ERA52B_1`, `ERA52C`.

### Current Consolidation

- `ERA47_DISCIPLINE_PREFLIGHT_CHAIN_NOAPI` is the parent chain.
- Old `ERA48` is historical alias for `ERA47B`.
- Old `ERA49` is historical alias for `ERA47C`.
- Old `ERA50` is historical alias for `ERA47D`.
- Old `ERA51` is historical alias for `ERA47E`.
- These old labels are not active work lanes.

### Word Rule

- Do not use `PASS` in new labels or command outputs.
- Use: `OK`, `WARN`, `FAIL`, `BLOCKED`, `CLOSED`, `SEALED`, `VERIFIED`.

### Deadline Rule

- Prefer small working code over repeated decision documents.
- Reduce documents.
- Reduce labels.
- Avoid repeated gate chains.
- `ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI` must deliver minimal read-only scaffold, not another planning chain.

### Safety Rule

- `PROJECT_RUNTIME.json` is source of truth.
- Human approval required.
- AI trade authority is zero.
- Live trade locked.
- Paper trade locked until explicit phase.
- No Runtime, DB, panel, service, timer, deploy mutation unless explicitly in scope.
<!-- CANONICAL_WORKFLOW_RULES_LOCK_END -->

<!-- ERA47_PREFLIGHT_CHAIN_CANONICAL_VIEW_START -->
## CURRENT CANONICAL ROADMAP VIEW — 2026-07-08T10:34:05.417432Z

`ERA47_DISCIPLINE_PREFLIGHT_CHAIN_NOAPI` is the single parent for the previous preflight work.

Canonical mapping:

- `ERA47A` = plan validation
- `ERA47B` = reachability classification
- `ERA47C` = false-positive / active surface review
- `ERA47D` = active runtime risk decision
- `ERA47E` = implementation Go/No-Go

Old labels are historical aliases:

- old `ERA48` -> `ERA47B`
- old `ERA49` -> `ERA47C`
- old `ERA50` -> `ERA47D`
- old `ERA51` -> `ERA47E`

Current execution rule:

- Do not open new micro ERA records.
- Use A/B/C/D under the same ERA.
- Use A_1/A_2 only when the same sub-area truly needs it.
- Next real software step: `ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI`.
- ERA52 must deliver minimal read-only scaffold, not another documentation chain.
<!-- ERA47_PREFLIGHT_CHAIN_CANONICAL_VIEW_END -->

# 03 ROADMAP - TOKENOSKOBI / COINOSKOBI MASTER ROADMAP

Bu dosya projenin yön haritasıdır.

Roadmap yalnızca ana yönü gösterir.

Detaylı tarihçe Almanac içindedir.

Mimari bağ haritası Atlas içindedir.

Anlık durum PROJECT_RUNTIME.json ve 06_PROJECT_MASTER_STATE.md içindedir.

Roadmap içinde alt basamak, audit, JSON içeriği, HEAD, timestamp, GitHub logu, dosya listesi veya operasyon dökümü tutulmaz.

---

## ROADMAP DOCTRINE

- Read-only first
- Shadow-first
- Evidence-first
- Risk-first
- Human final authority
- Runtime does not grant trade authority
- Runtime does not grant wallet authority
- Runtime does not grant signing authority
- Runtime does not create real orders

---

## V1-V8 MASTER ROADMAP

Canonical V-line haritası:

- V1 = PHASE0-PHASE60 closed
- V2 = V2_00-V2_60 closed
- V3 = ERA21-ERA60 active
- V4 = ERA61-ERA80 planned
- V5 = ERA81-ERA100 planned
- V6 = ERA101-ERA120 planned
- V7 = ERA121-ERA140 planned
- V8 = ERA141-ERA160 planned

Rolling roadmap policy:

- Current V = high detail
- Next V = medium detail
- Future V = strategic detail
- When a V closes, next V is expanded
- Closed ERA/V is immutable

Full detailed V1-V8 roadmap source:

`data/tokenoskobi_v1_v8_master_era_roadmap.json`

---

## V1 - CANONICAL FOUNDATION

Amaç:

- Güvenli token radar omurgası
- Onchain evidence backbone
- Risk gate
- Whale intelligence
- News intelligence
- Unknown anomaly
- Prosecutor evidence weighing
- Fusion summary
- Readonly decision surface
- V1 final closure

Durum:

V1 closed.

---

## V2 - CONTROLLED CONTINUATION

Amaç:

- V1 sealed base üzerinde kontrollü devam
- Real evidence bootstrap
- Source trust
- Shadow observation
- Replay harness
- Real data intake boundary
- Whale source taxonomy
- Time drift / TTL
- Opportunity engine
- Decision pipeline
- Conflict resolver
- State machine
- End-to-end dry-run decision chain

Durum:

V2 closed.

---

## V3 - RUNTIME CONTINUATION

Amaç:

- Runtime readiness
- Observability
- Async logger isolation
- Shadow feed
- Multi RPC trust
- Whale intelligence runtime
- Hybrid RPC cost guard
- Chain abstraction
- Read-only provider / RPC intake
- Runtime certification path
- Engineering decision framework
- Adaptive intelligence
- Predictive intelligence
- AI orchestration and veto gate
- Continuous evolution and modular health layer

Durum:

V3 active.

Current state source:

`PROJECT_RUNTIME.json`

Detailed roadmap source:

`data/tokenoskobi_v1_v8_master_era_roadmap.json`

---

## V4 - PRODUCTIZATION AND LIVE READINESS

Amaç:

- Production hardening
- Live-readiness gates
- Controlled micro-live readiness
- Risk and execution boundary certification
- Manual approval discipline
- Provider cost discipline

Durum:

Planned.

---

## V5 - SCALE AND MULTI-CHAIN EXPANSION

Amaç:

- Multi-chain runtime expansion
- DEX route intelligence
- Whale graph expansion
- News / adversarial intelligence expansion
- Scalable readmodel and async deep analysis

Durum:

Planned.

---

## V6 - ADVERSARIAL INTELLIGENCE AND RED TEAM SYSTEM

Amaç:

- Attack doctrine tracking
- Rug / honeypot / manipulation intelligence
- MEV and liquidity deception analysis
- Internal safety watchdog
- External threat defense architecture

Durum:

Planned.

---

## V7 - AUTONOMY BOUNDARY AND GOVERNANCE

Amaç:

- Authority boundary hardening
- Human approval integrity
- Auditability
- Recovery and kill-switch discipline
- No unauthorized live execution

Durum:

Planned.

---

## V8 - FULL INTELLIGENCE OPERATING SYSTEM

Amaç:

- Full evidence-driven operating system
- Continuous learning
- Opportunity memory
- Outcome memory
- Risk-first decision support
- Manual decision cockpit

Durum:

Planned.

---

## LONG TERM TARGET

- Güvenli radar
- Kaliteli aday keşfi
- Sert risk kapısı
- Shadow / paper outcome memory
- Bounded provider maliyeti
- Çok zincirli read-only runtime
- Whale intelligence graph
- News intelligence
- Unknown anomaly detection
- Prosecutor evidence weighing
- Fusion summary
- Panel destekli manuel karar
- Ayrı onaylı micro-live readiness

Final doktrin:

Önce kanıt. Sonra risk. Sonra fırsat. En son karar.

---

## UPDATE RULE

Her V / ERA kapanışında:

- Roadmap yalnızca ana yön veya V-line durumu değiştiyse güncellenir.
- Almanac detaylı tarihçe için güncellenir.
- Atlas yalnızca yeni mimari bağlantı varsa güncellenir.
- Project Master State güncel durum için güncellenir.
- Handoff gerekiyorsa güncellenir.
- Index sadece canonical içerik haritası değişirse güncellenir.
- Manifesto sadece doktrin değişirse güncellenir.

Roadmap içinde tutulmayacak içerikler:

- Alt basamak kayıtları
- Audit dökümleri
- JSON içerikleri
- HEAD dump
- Timestamp
- GitHub logu
- Dosya adı listeleri
- Uzun key/value state yığınları
- Operasyon dökümleri
- Current next work unit
- Closure marker

Bu içerikler Almanac, PROJECT_RUNTIME.json, 06_PROJECT_MASTER_STATE.md veya ilgili canonical kaynak dosyada tutulur.

## ERA42 Final Close — 2026-07-07T10:34:59.172133+00:00
- Status: CLOSED
- Final gate: PASS_ERA42_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI
- Next: ERA43_NEWS_SHADOW_REALTIME_READONLY_REAL_RUN_PLAN_NOAPI
- Health: root/database size check recorded.


## ERA44 Final Close — 2026-07-08T05:04:37.765358+00:00
- Status: CLOSED
- Final gate: PASS_ERA44_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI
- Next: ERA45_CODEX_FULL_VERIFICATION_AUDIT_NOAPI
- Health: root/database size check recorded.


## ERA44 Final Close — 2026-07-08T05:05:45.104744+00:00
- Status: CLOSED
- Final gate: PASS_ERA44_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI
- Next: ERA45_CODEX_FULL_VERIFICATION_AUDIT_NOAPI
- Health: root/database size check recorded.


## ERA44 Final Close — 2026-07-08T05:08:46.042076+00:00
- Status: CLOSED
- Final gate: PASS_ERA44_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI
- Next: ERA45_CODEX_FULL_VERIFICATION_AUDIT_NOAPI
- Health: root/database size check recorded.

## CURRENT ROADMAP UPDATE — 2026-07-08T09:33:39.212698Z
- `ERA46_ENGINE_INTERFACE_CONTRACT_NOAPI` closed.
- `ERA46_DISCIPLINE_LAYER_PLAN_NOAPI` closed as plan-only.
- Next: `ERA47_DISCIPLINE_LAYER_VALIDATION_NOAPI`.
- Implementation remains blocked until validation.

## CURRENT ROADMAP UPDATE — 2026-07-08T10:03:11.060911Z
- `ERA48_REACHABILITY_CLASSIFICATION_NOAPI` closed.
- Decision: `WARN_ACTIVE_RED_REQUIRES_REVIEW`.
- Next: `ERA49_ACTIVE_SURFACE_REVIEW_NOAPI`.
- Implementation remains blocked until active RED/UNKNOWN findings are reviewed.

## CURRENT ROADMAP UPDATE — 2026-07-08T10:11:02.446239Z
- `ERA50_ACTIVE_RUNTIME_RISK_DECISION_NOAPI` closed.
- Decision: `PASS_RISK_DECIDED_NO_DISCIPLINE_BLOCKER`.
- Next: `ERA51_DISCIPLINE_IMPLEMENTATION_GO_NOGO_NOAPI`.
- ERA50 does not authorize implementation; separate Go/No-Go review required.

