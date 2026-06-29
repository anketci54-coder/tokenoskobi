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

docs/canonical/PROJECT_MASTER_STATE.md
  -> current canonical state

docs/canonical/PROJECT_HANDOFF.md
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
