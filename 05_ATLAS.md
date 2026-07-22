# 05 ATLAS - TOKENOSKOBI / COINOSKOBI MASTER SYSTEM MAP

Bu dosya sistemin mimari bağ haritasıdır.

Roadmap yönü gösterir.

Almanac yapılan işleri ve tarihsel kayıtları gösterir.

Atlas parçaların birbirine nasıl bağlandığını, verinin nasıl aktığını ve yetkinin nerede sınırlandığını gösterir.

Atlas içinde kapanış kaydı, audit sonucu, HEAD, timestamp, current gate, next step veya operasyon günlüğü tutulmaz.

---

## 01 MASTER SYSTEM FLOW

```text
TOKEN / PAIR
  -> DATA INTAKE
  -> EVIDENCE RUNTIME
  -> HUNTER / UNKNOWN ANOMALY / PROSECUTOR
  -> TECHNICAL / WHALE / NEWS CONTEXT
  -> PRIORITY / FUSION SUMMARY
  -> RISK ENGINE
  -> COMMAND CENTER
  -> HUMAN REVIEW
```

---

## 02 DATA FLOW

```text
ONCHAIN DATA
  -> READER / PROVIDER LAYER
  -> NORMALIZATION
  -> EVIDENCE RUNTIME
  -> READMODEL
  -> RISK CONTEXT
  -> COMMAND CENTER

NEWS / SOCIAL DATA
  -> COLD RAW PRODUCER
  -> MATCH / SIGNAL / SCORE
  -> TRUST FILTER
  -> HOT INTELLIGENCE INGRESS
  -> BOUNDED REVIEW QUEUE
  -> PANEL CONTEXT
  -> NO DIRECT TRADE AUTHORITY

WHALE DATA
  -> WALLET / ENTITY GRAPH
  -> WHALE RUNTIME
  -> FLOW / EXCHANGE / RELATED-WALLET CONTEXT
  -> RISK CONTEXT
  -> COMMAND CENTER

TECHNICAL DATA
  -> MARKET / PRICE / LIQUIDITY INPUT
  -> TECHNICAL TACTICAL ENGINE
  -> TECHNICAL CONTEXT
  -> RISK CONTEXT
  -> COMMAND CENTER
```

---

## 03 NEWS RUNTIME FLOW

```text
SYSTEMD TIMER
  -> tokenoskobi-news-radar-refresh.service
  -> tools/news_radar_refresh_runner_v1.py
  -> COLD RAW PRODUCER
  -> DERIVED MATCHER / SIGNAL / SCORE REFRESH
  -> NEWS COVERAGE READMODEL
  -> PANEL DISPLAY ADAPTER
  -> HOT INTELLIGENCE INGRESS
  -> BOUNDED REVIEW-ONLY QUEUE
  -> ACTIVE PANEL DATA BRIDGE
  -> HUMAN REVIEW
```

Architecture boundary:

- News supplies context only.
- Hot ingress is admission and review infrastructure.
- Queue capacity is bounded.
- News cannot create trade, wallet, signing or order authority.
- AI execution authority remains zero.

---

## 04 HOT INTELLIGENCE INGRESS FLOW

```text
HOT SOURCE SIGNAL
  -> SOURCE TRUST / RATE POLICY
  -> EVENT NORMALIZATION
  -> ADMISSION GATE
  -> EVENT UID / FINGERPRINT
  -> EVIDENCE FRESHNESS
  -> TOPIC DEDUPLICATION
  -> EVIDENCE POINTER
  -> PROSECUTOR CANDIDATE GATE
  -> BOUNDED REVIEW QUEUE
  -> HUMAN / RISK REVIEW ONLY
```

UID contract:

- event_hash = sha256(normalized_title + normalized_body + event_time_bucket)
- event_uid = sha256(source_uid + event_hash)
- dedupe_key = source_uid + event_hash

Architecture rule:

- Admission is gatekeeper.
- Prosecutor weighs evidence; it does not execute.
- Duplicate and poison events do not create authority.
- Hot ingress never bypasses Risk Engine or human review.

---

## 05 RISK AND DECISION FLOW

```text
TOKEN / PAIR
  -> CONTRACT / DEPLOYER / HOLDER RISK
  -> LIQUIDITY / SLIPPAGE / MEV RISK
  -> WHALE / WALLET RISK
  -> NEWS / SOCIAL TRUST FILTER
  -> TECHNICAL CONTEXT
  -> UNKNOWN ANOMALY
  -> PROSECUTOR EVIDENCE WEIGHING
  -> FUSION SUMMARY
  -> RISK ENGINE
  -> ALLOW / BLOCK / WAIT / REVIEW
  -> COMMAND CENTER
  -> HUMAN DECISION
```

Risk Engine final risk authority katmanıdır.

Teknik skor, haber skoru, balina skoru, Fusion özeti veya AI önerisi Risk Engine'i geçersiz kılamaz.

Hard block bypass edilemez.

---

## 06 AUTHORITY FLOW

```text
AI
  -> PROPOSAL / EXPLANATION ONLY

HUNTER ENGINE
  -> CANDIDATE DISCOVERY ONLY

UNKNOWN ANOMALY ENGINE
  -> SUSPICION CONTEXT ONLY

PROSECUTOR ENGINE
  -> EVIDENCE WEIGHING ONLY

TECHNICAL ENGINE
  -> CONTEXT ONLY

NEWS / SOCIAL
  -> CONTEXT ONLY

WHALE RUNTIME
  -> CONTEXT ONLY

FUSION SUMMARY
  -> COMBINED CONTEXT ONLY

PANEL
  -> DISPLAY / REVIEW ONLY

RISK ENGINE
  -> FINAL RISK AUTHORITY

HUMAN
  -> FINAL USER DECISION
```

```text
AI_AUTHORITY=0
TRADE_AUTHORITY=0
WALLET_AUTHORITY=0
SIGNING_AUTHORITY=0
ORDER_CREATE_AUTHORITY=0
LIVE_TRADE=DISABLED
PAPER_TRADE=ERA_SCOPED_ZERO_REAL_FUNDS_SIMULATION
AUTO_APPLY=0
AUTO_BLOCK=0
```

---


<!-- EXECUTABLE_AUTHORITY_GATE_START -->
### Executable Authority Gate

OPERATION + DECLARED_EFFECTS + TARGET
-> AUTHORITY_STATE
-> RUNTIME_POLICY
-> HUMAN_APPROVAL_WHEN_REQUIRED
-> FAIL_CLOSED_DENY

Rules:

- Missing or unknown operation, effect, target, authority or policy is denied.
- Read-only classification cannot hide a mutating effect.
- Human approval is a required condition where declared; it does not create authority.
- Trade, order, wallet-signing and transaction-broadcast paths remain denied unless every required authority boundary is explicitly satisfied.
<!-- EXECUTABLE_AUTHORITY_GATE_END -->

## 07 CORE CAPABILITY MAP

```text
DATA INTAKE
  -> source acquisition
  -> provider abstraction
  -> normalization

EVIDENCE RUNTIME
  -> evidence identity
  -> freshness
  -> provenance
  -> append-only event context

HUNTER ENGINE
  -> candidate discovery

UNKNOWN ANOMALY ENGINE
  -> abnormal behavior detection

PROSECUTOR ENGINE
  -> evidence weighing
  -> verdict context

PRIORITY ENGINE
  -> attention ordering

WHALE INTELLIGENCE
  -> wallet / entity graph
  -> movement and flow context

NEWS INTELLIGENCE
  -> trusted context
  -> market and adversarial coverage

TECHNICAL TACTICAL ENGINE
  -> technical and market context

MEMORY / LEARNING
  -> outcome memory
  -> opportunity memory
  -> case reasoning

FUSION
  -> combined explanation and summary

RISK ENGINE
  -> final risk gate

COMMAND CENTER
  -> unified review surface

SYSTEM CONTROL
  -> health, authority and operational visibility
```

---

## 08 ENGINE TO PANEL MAP

```text
EVIDENCE RUNTIME
  -> PANEL08 SYSTEM CONTROL
  -> PANEL05 RISK SECURITY

PROSECUTOR ENGINE
  -> PANEL04 ONCHAIN
  -> PANEL05 RISK SECURITY

PRIORITY ENGINE
  -> PANEL01 COMMAND

WHALE INTELLIGENCE
  -> PANEL03 WHALE TRACKING
  -> PANEL05 RISK SECURITY

NEWS INTELLIGENCE
  -> PANEL02 NEWS FLOW
  -> PANEL01 COMMAND

TECHNICAL TACTICAL ENGINE
  -> PANEL07 TECHNICAL ANALYSIS

MEMORY / LEARNING
  -> PANEL01 COMMAND
  -> PANEL08 SYSTEM CONTROL

FUSION
  -> PANEL01 COMMAND

RISK ENGINE
  -> PANEL01 COMMAND
  -> PANEL05 RISK SECURITY

HUNTER ENGINE
  -> PANEL01 COMMAND
  -> PANEL02 NEWS FLOW

EXECUTION ACCOUNTING
  -> PANEL01 COMMAND
  -> PANEL08 SYSTEM CONTROL
```

---

## 09 PANEL MAP

```text
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
```

Panel display ve review yüzeyidir.

Panel tek başına trade, wallet, signing, order veya auto-apply yetkisi üretmez.

---

## 10 V-LINE ARCHITECTURE MAP

### V1 - CANONICAL FOUNDATION

```text
FOUNDATION
  -> DATA INTAKE
  -> EVIDENCE RUNTIME
  -> RISK ENGINE
  -> WHALE INTELLIGENCE
  -> NEWS INTELLIGENCE
  -> TECHNICAL TACTICAL ENGINE
  -> MEMORY / LEARNING
  -> HUNTER ENGINE
  -> UNKNOWN ANOMALY ENGINE
  -> PROSECUTOR ENGINE
  -> FUSION SUMMARY
  -> COMMAND CENTER
  -> READONLY DECISION SURFACE
```

### V2 - CONTROLLED CONTINUATION

```text
V1 SEALED BASE
  -> REAL EVIDENCE BOOTSTRAP
  -> SOURCE TRUST
  -> SHADOW OBSERVATION
  -> REPLAY HARNESS
  -> REAL DATA INTAKE BOUNDARY
  -> WHALE SOURCE TAXONOMY
  -> TIME DRIFT / TTL
  -> OPPORTUNITY ENGINE
  -> ALPHA / OUTCOME MEMORY
  -> CASE REASONING
  -> RUNTIME SHADOW READMODEL
  -> CORE RISK PRE-BINDING
  -> DECISION PIPELINE
  -> CONFLICT RESOLVER
  -> STATE MACHINE
  -> END-TO-END DRY-RUN DECISION CHAIN
```

### V3 - RUNTIME INTELLIGENCE OS

```text
RUNTIME READINESS
  -> OBSERVABILITY
  -> ASYNC LOGGER ISOLATION
  -> SHADOW FEED
  -> MULTI RPC TRUST
  -> WHALE INTELLIGENCE RUNTIME
  -> HYBRID RPC COST GUARD
  -> CHAIN ABSTRACTION
  -> READONLY RPC INTAKE
  -> PROVIDER ABSTRACTION
  -> HOT INTELLIGENCE INGRESS
  -> BOUNDED QUEUE
  -> PANEL BRIDGE
  -> RUNTIME OPTIMIZATION LAYER
```

```text
READ_ONLY_FIRST
SHADOW_FIRST
LIVE_TRADE=DISABLED
WALLET_SIGNING=DISABLED
ORDER_CREATE=DISABLED
```

V4-V8 gelecek yönleri Atlas içinde ayrıntılandırılmaz; yön sahipliği `03_ROADMAP.md` dosyasındadır.

---

## 11 ROOT LOCATION MAP

```text
PROJECT_RUNTIME.json
  -> primary machine-readable current-state authority

PROJECT_BOOT.json
  -> identity, doctrine and startup contract

PROJECT_HISTORY.json
  -> append-only historical machine record

01_INDEX.md
  -> canonical navigation

02_MANIFESTO.md
  -> doctrine and constitutional rules

03_ROADMAP.md
  -> future direction and V-line map

04_ALMANAC.md
  -> completed-work history and evidence ledger

05_ATLAS.md
  -> architecture, flow and authority map

06_PROJECT_MASTER_STATE.md
  -> human-readable current-state summary

07_PROJECT_HANDOFF.md
  -> continuation and new-session handoff

tokenoskobi_kernel.py
  -> root kernel / entrypoint

core/
  -> core system components

config/
  -> policy and configuration

schema/
  -> schema definitions and contracts

runtime/
  -> runtime state and generated runtime surfaces

data/
  -> evidence, control artifacts and readmodels

tools/
  -> runners, utilities and audit tools

plugins/
  -> extension components

deploy/
  -> deployment definitions

maintenance/
  -> controlled maintenance operations

tests/
  -> test and verification assets

public/
  -> public and panel-facing assets

active_panel_8096/current/
  -> current active panel surface

reports/
  -> generated reports and latest review outputs

docs/
  -> supporting documentation

archive/
  -> historical or superseded records; not active authority
```

Root location map görevleri gösterir; root dizin envanteri değildir.

---

## 12 FORBIDDEN AUTHORITY MAP

```text
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
```

---

## 13 MASTER ASCII MAP

```text
                         USER / HUMAN REVIEW
                                  ^
                                  |
                           COMMAND CENTER
                                  ^
                                  |
                            RISK ENGINE
                                  ^
                                  |
                           FUSION SUMMARY
             _____________________|_____________________
            |          |          |          |           |
        EVIDENCE   PROSECUTOR  TECHNICAL    WHALE      NEWS
            |          |          |          |           |
        ONCHAIN    ANOMALY      TACTICAL    ENTITY    TRUSTED
          DATA      CONTEXT      CONTEXT    GRAPH     CONTEXT

AUTHORITY:
AI=0 | TRADE=0 | WALLET=0 | SIGNING=0 | AUTO_APPLY=0
```

---

## 14 ATLAS RULE

Atlas açıklama kitabı değildir.

Atlas operasyon logu değildir.

Atlas audit defteri değildir.

Atlas tarihçe kitabı değildir.

Atlas roadmap değildir.

Atlas root envanteri değildir.

Atlas mimari bağ, veri akışı, konum ve yetki haritasıdır.

Detaylı tarihçe Almanac içindedir.

Yön Roadmap içindedir.

Doktrin Manifesto içindedir.

Güncel durum PROJECT_RUNTIME.json ve 06_PROJECT_MASTER_STATE.md içindedir.

İçerik haritası Index içindedir.

---

## ATLAS ARCHITECTURE INSERTION AND REPLACEMENT CONSTITUTION

Yeni onaylı bir mimari bağ mevcut Atlas bağıyla çakışıyorsa, mevcut bağ kendi akış, bileşen veya konum haritasındaki yerinde yeni bağla değiştirilir.

Değiştirilen eski mimari bağ Atlas içinde ikinci bir kopya olarak tutulmaz; tarihsel kayıt gerekiyorsa Almanac veya PROJECT_HISTORY.json içinde korunur.

Yeni onaylı mimari bağ Atlas içinde mevcut değilse ve hiçbir mevcut bağla çakışmıyorsa, ilgili sistem akışı, bileşen, panel, V-line veya konum haritası altında eklenir.

Yeni mimari bağ sırf yeni olduğu için dosyanın sonuna rastgele eklenmez; Atlas içindeki doğru mimari katmana yerleştirilir.

Atlasın mevcut yazım şekli, başlık düzeni, boşluk yapısı, yazı tipi ve biçimlendirmesi açık kullanıcı onayı olmadan değiştirilmez.

---

## ATLAS YAZIM STANDARDI

Bu eser aşağıdaki canonical rehbere göre geliştirilir:

`docs/design/ATLAS_AUTHORING_GUIDE.md`

<!-- ERA63_PAPER_PATH:BEGIN -->
## PAPER PATH

```text
ASYNC NEWS/WHALE/ONCHAIN/AI CONTEXT -> CACHE
FRESH MARKET DATA -> TECHNICAL/EDGE -> RISK ENGINE -> SIZING -> SIMULATED FILL -> COSTS -> P&L/DRAWDOWN -> OUTCOME MEMORY
```

Paper authority is simulation only. Real wallet, signing, broadcast and capital authority remain zero. Risk Engine has veto.
<!-- ERA63_PAPER_PATH:END -->
