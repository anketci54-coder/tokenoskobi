<!-- CANONICAL_ACTIVE_STATE_CURRENT_START -->
## CANONICAL ACTIVE STATE — ERA20 SEALED

STATE_SYNC_UTC=20260701T101455Z

CURRENT_CANONICAL_HEAD=2c2a9defd2222e3f47a6f8059aa9e4d09cb8a23f
CURRENT_ERA=ERA20
ERA20_STATUS=CLOSED_VERIFIED_GITHUB_SEALED
LAST_COMPLETED=CANONICAL_BOOTSTRAP_AND_DOCUMENTATION_CONSTITUTION_REFACTOR
NEXT_SAFE_STEP=SHADOW_AUDIT_READONLY

PROJECT_MODE=CANONICAL_V1_CERTIFICATION_SEALED
V1_STATUS=CLOSED_VERIFIED_GITHUB_SEALED
V2_STATUS=HISTORICAL_CONTROLLED_CONTINUATION
RUNTIME_SLICE_STATUS=HISTORICAL_UNDER_ERA_CHAIN

LIVE_TRADE=false
PAPER_TRADE=false
WALLET=false
SIGNING=false
REAL_ORDER=false
ORDER_CREATE=false
AI_AUTHORITY=0
TRADE_AUTHORITY=0

CANONICAL_RULE=TOP_ACTIVE_STATE_OVERRIDES_HISTORICAL_ENTRIES
HISTORICAL_ENTRIES_REMAIN_FOR_AUDIT_TRAIL=true
<!-- CANONICAL_ACTIVE_STATE_CURRENT_END -->


# 05 ATLAS - TOKENOSKOBI / COINOSKOBI MASTER SYSTEM MAP

Bu dosya sistemin mimari bağ haritasıdır.

Roadmap yönü gösterir.

Almanac yapılan işleri ve kayıt dosyalarını gösterir.

Atlas parçaların birbirine nasıl bağlandığını gösterir.

---

## 01 SYSTEM FLOW

```text
TOKEN / PAIR
  -> DATA INTAKE
  -> EVIDENCE RUNTIME
  -> RISK ENGINE
  -> TECHNICAL / WHALE / NEWS CONTEXT
  -> FUSION SUMMARY
  -> COMMAND CENTER
  -> HUMAN REVIEW
02 DATA FLOW
ONCHAIN DATA
  -> READER / PROVIDER LAYER
  -> EVIDENCE RUNTIME
  -> READMODEL
  -> RISK CONTEXT
  -> COMMAND CENTER

NEWS / SOCIAL DATA
  -> BACKGROUND INTELLIGENCE
  -> TRUST FILTER
  -> CONTEXT ONLY
  -> NO DIRECT TRADE AUTHORITY

WHALE DATA
  -> WALLET / ENTITY GRAPH
  -> WHALE RUNTIME
  -> RISK CONTEXT
  -> COMMAND CENTER
03 RISK FLOW
TOKEN / PAIR
  -> CONTRACT / DEPLOYER / HOLDER RISK
  -> LIQUIDITY / SLIPPAGE / MEV RISK
  -> WHALE / WALLET RISK
  -> NEWS / SOCIAL TRUST FILTER
  -> RISK ENGINE
  -> ALLOW / BLOCK / WAIT / REVIEW

Risk Engine final risk authority katmanıdır.

Teknik skor, haber skoru, balina skoru veya AI önerisi Risk Engine'i geçersiz kılamaz.

04 AUTHORITY FLOW
AI
  -> PROPOSAL ONLY

TECHNICAL ENGINE
  -> CONTEXT ONLY

NEWS / SOCIAL
  -> CONTEXT ONLY

WHALE RUNTIME
  -> CONTEXT ONLY

PANEL
  -> DISPLAY / REVIEW ONLY

RISK ENGINE
  -> FINAL RISK AUTHORITY

HUMAN
  -> FINAL USER DECISION
AI_AUTHORITY=0
TRADE_AUTHORITY=0
WALLET_AUTHORITY=0
SIGNING_AUTHORITY=0
ORDER_CREATE_AUTHORITY=0
LIVE_TRADE=DISABLED
PAPER_TRADE=DISABLED
AUTO_APPLY=0
AUTO_BLOCK=0
05 PASS TO ENGINE MAP
PASS13 Evidence Dictionary
  -> ENGINE01 Evidence Runtime

PASS14 Deployer Intelligence
  -> ENGINE02 Prosecutor Engine

PASS15 Contract DNA
  -> ENGINE02 Prosecutor Engine

PASS16 Market Regime
  -> ENGINE03 Priority Engine

PASS17 Wallet Cluster
  -> ENGINE04 Whale Runtime

PASS18 Technical Signal
  -> ENGINE05 Technical Tactical Engine

PASS19 Learning Feedback
  -> ENGINE06 Memory Learning

PASS20 Decision Intelligence
  -> ENGINE07 Risk Engine

PASS21 Execution Realism
  -> ENGINE08 Execution Layer

PASS22 Position Sizing
  -> ENGINE07 Risk Engine

PASS23 Portfolio Risk
  -> ENGINE07 Risk Engine

PASS24 Launch Intelligence
  -> ENGINE09 Hunter Engine

PASS25 Historical Launch
  -> ENGINE09 Hunter Engine

PASS26 Launch Outcome
  -> ENGINE09 Hunter Engine

PASS27 Execution Accounting
  -> ENGINE10 Execution Accounting
06 PHASE TO ENGINE MAP
PHASE00–PHASE12
  -> FOUNDATION / LEGACY BASE

PHASE13–PHASE16
  -> SYSTEM CONTROL / RUNTIME PREPARATION

PHASE17–PHASE19
  -> DATA INTAKE / PROVIDER / SNAPSHOT

PHASE20–PHASE21
  -> ENGINE04 Whale Runtime

PHASE22–PHASE23
  -> ENGINE07 Risk Engine
  -> ENGINE06 Memory Learning

PHASE24–PHASE27
  -> ENGINE09 Hunter Engine
  -> ENGINE10 Execution Accounting

PHASE28–PHASE33
  -> PANEL / SYSTEM CONTROL / AUTHORITY STRUCTURE

PHASE35–PHASE39
  -> ADVANCED MARKET INTELLIGENCE
  -> ENGINE06 Memory Learning
  -> ENGINE09 Hunter Engine

PHASE40
  -> ENGINE05 Technical Tactical Engine

PHASE41
  -> COMMAND CENTER BINDING
  -> PROVIDER POLICY
  -> CANONICAL CROSSWALK

PHASE42
  -> Unknown Anomaly Engine

PHASE43
  -> ENGINE02 Prosecutor Engine

PHASE44
  -> Intelligence Fusion

PHASE45
  -> AI Operations Officer

PHASE46
  -> Training Export / GPU Orchestration

PHASE47
  -> Token Lifecycle Intelligence

PHASE48
  -> Threat Memory / Outcome Intelligence

PHASE49
  -> Scalability / Ray Batch

PHASE50
  -> Ray Decision Memory

PHASE51
  -> Background Intelligence Officer

PHASE52
  -> Intelligence Officer Runtime

PHASE53
  -> Consumer / Readmodel Contract

PHASE54
  -> Readonly Decision Surface

PHASE56–PHASE60Z
  -> V1 Closure Path
07 ENGINE TO PANEL MAP
ENGINE01 Evidence Runtime
  -> PANEL08 System Control
  -> PANEL05 Risk Security

ENGINE02 Prosecutor Engine
  -> PANEL04 Onchain
  -> PANEL05 Risk Security

ENGINE03 Priority Engine
  -> PANEL01 Command

ENGINE04 Whale Runtime
  -> PANEL03 Whale Tracking

ENGINE05 Technical Tactical Engine
  -> PANEL07 Technical Analysis

ENGINE06 Memory Learning
  -> PANEL01 Command
  -> PANEL08 System Control

ENGINE07 Risk Engine
  -> PANEL01 Command
  -> PANEL05 Risk Security

ENGINE08 Execution Layer
  -> PANEL01 Command

ENGINE09 Hunter Engine
  -> PANEL01 Command
  -> PANEL02 News Flow

ENGINE10 Execution Accounting
  -> PANEL01 Command
  -> PANEL08 System Control
08 PANEL MAP
PANEL01
  -> Komuta ve Karar Merkezi

PANEL02
  -> Haber Akış Merkezi

PANEL03
  -> Balina Takip Merkezi

PANEL04
  -> Onchain Veri Merkezi

PANEL05
  -> Risk Güvenlik Merkezi

PANEL06
  -> Yaşam Destek Merkezi

PANEL07
  -> Teknik Analiz Merkezi

PANEL08
  -> Sistem Kontrol Merkezi
09 V1 ARCHITECTURE
V1
  -> FOUNDATION
  -> DATA INTAKE
  -> EVIDENCE RUNTIME
  -> RISK ENGINE
  -> WHALE RUNTIME
  -> TECHNICAL TACTICAL ENGINE
  -> MEMORY LEARNING
  -> HUNTER ENGINE
  -> PROSECUTOR ENGINE
  -> FUSION SUMMARY
  -> COMMAND CENTER
  -> READONLY DECISION SURFACE
  -> FINAL CLOSURE
V1_STATUS=CLOSED_VERIFIED_GITHUB_SEALED
10 V2 ARCHITECTURE
V2
  -> CONTROLLED CONTINUATION ON V1 SEALED BASE
  -> REAL EVIDENCE BOOTSTRAP
  -> SOURCE TRUST
  -> SHADOW OBSERVATION
  -> REPLAY HARNESS
  -> REAL DATA INTAKE BOUNDARY
  -> WHALE SOURCE TAXONOMY
  -> TIME DRIFT / TTL
  -> DEX TECHNICAL PATTERN GUARD
  -> OPPORTUNITY ENGINE
  -> ALPHA MEMORY
  -> CASE REASONING
  -> RUNTIME SHADOW READMODEL
  -> CORE RISK PRE-BINDING
  -> DECISION PIPELINE
  -> CONFLICT RESOLVER
  -> DECISION OUTPUT BINDING
  -> STATE MACHINE
  -> RUNTIME BOUNDARY
  -> END-TO-END DRY-RUN DECISION CHAIN
  -> V2 FINAL CLOSURE
NEW_REPO=false
NEW_DB=false
BREAKS_V1=false
LIVE_TRADE=DISABLED
AI_AUTHORITY=0
WALLET_SIGNING=DISABLED
11 V3 RUNTIME ARCHITECTURE
V3
  -> RUNTIME READINESS
  -> OBSERVABILITY
  -> ASYNC LOGGER ISOLATION
  -> SHADOW FEED
  -> MULTI RPC TRUST
  -> WARM-UP LOGIC
  -> CHAOS READINESS
  -> WHALE INTELLIGENCE RUNTIME
  -> HYBRID RPC COST GUARD
  -> CHAIN ABSTRACTION
  -> READONLY RPC INTAKE
  -> PROVIDER ABSTRACTION
READ_ONLY_FIRST
SHADOW_FIRST
LIVE_TRADE=DISABLED
WALLET_SIGNING=DISABLED
ORDER_CREATE=DISABLED
DB_WRITE_AUTHORITY=DISABLED
12 DECISION FLOW
EVIDENCE
  -> RISK
  -> TECHNICAL CONTEXT
  -> WHALE CONTEXT
  -> NEWS CONTEXT
  -> FUSION SUMMARY
  -> COMMAND CENTER
  -> HUMAN REVIEW
13 DATA LOCATION MAP
OKU.md
  -> startup guide

01_INDEX.md
  -> content map

02_MANIFESTO.md
  -> doctrine

03_ROADMAP.md
  -> direction map

04_ALMANAC.md
  -> work history and file ledger

05_ATLAS.md
  -> architecture binding map

06_PROJECT_MASTER_STATE.md
  -> current canonical state

07_PROJECT_HANDOFF.md
  -> technical continuation state

docs/v2/
  -> V2 controlled continuation records

docs/v3/
  -> V3 planning records

docs/runtime/
  -> V3 runtime implementation records

docs/phases/
  -> phase documentation records

data/
  -> audit, json and jsonl evidence records

tools/
  -> runtime and utility modules
14 FORBIDDEN AUTHORITY MAP
AI cannot trade.
AI cannot override risk.
AI cannot use wallet.
AI cannot sign.
AI cannot create order.
AI cannot auto-apply.
AI cannot auto-block.

Panel cannot trade.
News cannot trade.
Whale signal cannot trade.
Technical signal cannot trade.
Fusion summary cannot trade.

Risk block cannot be bypassed.
Hard block cannot be bypassed.
15 MASTER ASCII MAP
                         USER / HUMAN REVIEW
                                  ^
                                  |
                           COMMAND CENTER
                                  ^
                                  |
                           FUSION SUMMARY
             _____________________|_____________________
            |          |          |          |           |
        EVIDENCE     RISK     TECHNICAL    WHALE      NEWS
            |          |          |          |           |
        ONCHAIN     GUARDS     TACTICAL    ENTITY    TRUSTED
          DATA       GATES      CONTEXT    GRAPH     CONTEXT

AUTHORITY:
AI=0 | TRADE=0 | WALLET=0 | SIGNING=0 | AUTO_APPLY=0
16 ATLAS RULE

Atlas açıklama kitabı değildir.

Atlas operasyon logu değildir.

Atlas audit defteri değildir.

Atlas dosya listesi değildir.

Atlas mimari bağ haritasıdır.

Detay Almanac içindedir.

Yön Roadmap içindedir.

Doktrin Manifesto içindedir.

İçerik haritası Index içindedir.
## ERA15 → ERA16 ARCHITECTURE TRANSITION
ERA15 closed the V3 runtime implementation line.

Runtime outputs now feed ERA16 architecture:
- Constitution Engine
- Intelligence Fabric
- Intelligence Graph
- Historical Archive
- Replay Laboratory
- Whale Intelligence
- News Intelligence
- AI Commander
- AI General Staff
- AI Security Officer
- Memory System
- Data Quality Engine
- Confidence Engine

Runtime remains read-only unless separately approved and sealed.

## ERA16 PHASE63 ARCHITECTURE BINDING
PHASE63 binds the Constitution layer to distributed guardian governance.

Architecture links:
- Constitution Engine -> Distributed Guardian
- Distributed Guardian -> Local Runtime Gate
- Guardian Failure -> Fail Closed
- Silent Failure -> Global Observe Only
- Kill Switch -> Global Fail Closed
- Constitution Update -> Two Phase Commit
- Audit Ledger -> Append Only Hash Chain
- AI Authority -> 0

4G Gate remains active:
Speed never down.
Power never down.
Security never down.
Economy never down.


================================================================================
ERA16 FINAL CANONICAL CLOSURE
Timestamp: 2026-06-29T17:04:05Z

ERA16_STATUS=CLOSED_VERIFIED_READY_FOR_GITHUB_SEAL

CANONICAL_PHASE=PHASE62

PHASE62 IMPLEMENTATION MODULES
- Constitution Engine
- Conflict Resolver
- Distributed Guardian
- Runtime Integration
- Intelligence Fabric
- Event Ledger
- Decision Pipeline
- Execution Governance

CANONICAL MAPPING
PHASE63 -> PHASE62/GUARDIAN_MODULE
PHASE64 -> PHASE62/RUNTIME_INTEGRATION_MODULE
PHASE65 -> PHASE62/INTELLIGENCE_FABRIC_MODULE
PHASE66 -> PHASE62/DECISION_PIPELINE_MODULE
PHASE67 -> PHASE62/EXECUTION_GOVERNANCE_MODULE

PHASE ENUMERATION FROZEN
NEXT_ERA=ERA17
================================================================================

================================================================================
ERA17+ WORKFLOW TERMINOLOGY LOCK
Timestamp: 2026-06-29T18:41:46Z
Base HEAD: ecddc11273192bf2e41384b87bdc7a340bbbae9f

DECISION
PASS terminology is not used for ERA17+ workflow units.

REASON
PASS was already used historically in Canonical V1 construction and audits
(PASS0-PASS27 and sub-pass variants). Reusing PASS inside ERA17+ would create
naming ambiguity.

NEW STANDARD
ERA17+ workflow unit = GATE

CANONICAL MEANING
PASS = Legacy construction/audit workflow term.
GATE = ERA17+ certification workflow term.

ERA17+ STRUCTURE
ERA
  GATE01
  GATE02
  GATE03
  FINAL_AUDIT
  GITHUB_SEAL
  ERA_CLOSED

RULES
- No new PHASE identifiers after ERA16 closure.
- No new PASS identifiers after ERA16 closure.
- ERA17+ uses GATE only.
- GATE count is not fixed; minimum necessary gates only.
- Canonical V1 remains the active architecture.
- ERA20 remains the maximum planned ERA boundary for Canonical V1 certification.
================================================================================

================================================================================
ERA18 CLOSURE UPDATE
Timestamp: 2026-06-29T19:58:29Z
HEAD: 3bf2a540d97f32eac652928d46daf115f1a03983

ERA18_STATUS=CLOSED_VERIFIED_GITHUB_SEALED

CURRENT_ERA=ERA19
CURRENT_GATE=GATE01

LAST_COMPLETED=ERA18_GITHUB_SEAL

NEXT_SAFE_STEP=ERA19_GATE01_RUNTIME_CERTIFICATION_PLAN_NOAPI

ERA18 SUMMARY

GATE02
Paper Execution Engine
PASS

GATE03
Paper Risk Engine
PASS

GATE04
Final Audit + GitHub Seal
PASS

CONSTITUTION

Paper/Live Provider Split
Logical Time Only
Rolling Checksum
Replay Certification
Replay Diff
Paper-Live Boundary
Penalty Factor
Delta Ledger
Kill Switch

HEAD
3bf2a540d97f32eac652928d46daf115f1a03983

================================================================================

================================================================================
ERA19 CLOSURE UPDATE
Timestamp: 2026-06-30T05:39:27Z
HEAD: d635900bd363ba9d8437a65181382b3b2568d6db

ERA19_STATUS=CLOSED_VERIFIED_GITHUB_SEALED

CURRENT_ERA=ERA20
CURRENT_GATE=GATE01

LAST_COMPLETED=ERA19_GITHUB_SEAL

NEXT_SAFE_STEP=ERA20_GATE01_LIVE_READINESS_DOCTRINE_PLAN_NOAPI

ERA19 SUMMARY

GATE01
Runtime Activation and Resilience
PASS

GATE02
Long Run Stability
PASS

GATE03
Paper Performance
PASS

GATE04
Replay Certification
PASS

GATE05
Shadow Market
PASS

GATE06
Drift Monitor
PASS

GATE07
War Game
PASS

GATE08
Runtime Certification
PASS

GATE09
Final Runtime Audit
PASS_READY_FOR_GITHUB_SEAL

CERTIFIED
Paper Runtime
Event-Driven Runtime
Logical Time Only
Triple Ledger
GSN Chain
Append-Only + WAL + Immutable Seal
Replay Proof
Shadow Market
Drift Monitor
War Game Resilience
Live Boundary Disabled

LIVE SAFETY
LIVE_TRADE=false
WALLET=false
SIGNING=false
REAL_ORDER=false
ORDER_CREATE=false

HEAD
d635900bd363ba9d8437a65181382b3b2568d6db

================================================================================

