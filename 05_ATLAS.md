# 05 ATLAS - Tokenoskobi / Coinoskobi Master System Map

Bu dosya sistemin muhendislik haritasidir.
Almanac tarih kitabidir; Atlas baglanti haritasidir.

## 01 SYSTEM FLOW

RAW SOURCES
  -> DATA ACQUISITION
  -> ONCHAIN DATA ENGINE
  -> EVIDENCE RUNTIME
  -> RISK ENGINE
  -> TECHNICAL TACTICAL ENGINE
  -> OPPORTUNITY / HUNTER ENGINE
  -> SHADOW / PAPER SIMULATION
  -> LEARNING MEMORY
  -> COMMAND CENTER

## 02 DATA FLOW

RAW
  -> STAGING
  -> VALIDATED
  -> CANONICAL
  -> READMODEL
  -> PANEL

Kurallar:
- RAW veri dogrudan trade karari uretmez.
- VALIDATED olmadan canonical sayilmaz.
- READMODEL panel icin kullanilir.
- PANEL sadece karar destek kokpitidir.

## 03 RISK FLOW

TOKEN / PAIR
  -> SELLABILITY CHECK
  -> LIQUIDITY CHECK
  -> CONTRACT / DEPLOYER / HOLDER RISK
  -> HONEYPOT / RWD / TRAP CHECK
  -> RISK ENGINE
  -> ALLOW / BLOCK / WAIT / REVIEW

Risk Gate ustundur.
Teknik skor, haber skoru, balina skoru veya AI onerisi Risk Gate'i gecemez.

## 04 AUTHORITY FLOW

AI -> PROPOSAL ONLY
TECHNICAL SCORE -> NO TRADE AUTHORITY
NEWS / SOCIAL -> NO TRADE AUTHORITY
WHALE SIGNAL -> NO TRADE AUTHORITY
RISK ENGINE -> FINAL RISK AUTHORITY

AI_AUTHORITY=0
TECHNICAL_TRADE_AUTHORITY=0
NEWS_SOCIAL_TRADE_AUTHORITY=0
WHALE_TRADE_AUTHORITY=0
PANEL_TRADE_AUTHORITY=0
FINAL_RISK_AUTHORITY=RISK_ENGINE
LIVE_TRADE=DISABLED
WALLET_SIGNING=DISABLED

## 05 LEARNING FLOW

SHADOW RESULT
  -> OUTCOME MEMORY
  -> FALSE POSITIVE / FALSE NEGATIVE MEMORY
  -> AVOIDED LOSS MEMORY
  -> MISSED OPPORTUNITY MEMORY
  -> CALIBRATION LEDGER
  -> FUTURE SCORE ADJUSTMENT

Learning sistemi trade yetkisi vermez.
Sadece skorlama, kalibrasyon ve review uretir.

## 06 SHADOW FLOW

CANDIDATE
  -> ENTRY PLAN
  -> SL / TP / EXIT PLAN
  -> GAS / SLIPPAGE / MEV / EXIT COST
  -> SHADOW PAPER RESULT
  -> OUTCOME LEDGER

Shadow/Paper live trade degildir.
Canli emir, wallet signing veya para hareketi yoktur.

## 07 ENGINE TO PHASE MAP

ENGINE01 Evidence Runtime
  -> PASS13
  -> PHASE5 evidence backbone input

ENGINE02 Prosecutor Engine
  -> PASS14
  -> PASS15

ENGINE03 Priority Engine
  -> PASS16

ENGINE04 Whale Runtime
  -> PASS17
  -> PHASE20 whale / wallet direction

ENGINE05 Technical Tactical Engine
  -> PASS18
  -> PHASE40

ENGINE06 Memory Learning
  -> PASS19
  -> PHASE36
  -> PHASE41 outcome memory

ENGINE07 Risk Engine
  -> PASS20
  -> PASS22
  -> PASS23
  -> PHASE22
  -> PHASE40 RWD/TPI
  -> PHASE41 command binding

ENGINE08 Execution Layer
  -> PASS21
  -> Phase23 risk math / execution realism

ENGINE09 Hunter Engine
  -> PASS24
  -> PASS25
  -> PASS26
  -> Phase40F news/social/launch direction

ENGINE10 Execution Accounting
  -> PASS27
  -> Phase41 paper/outcome/accounting direction

## 08 PHASE TO PASS MAP

PHASE00-08
  -> Legacy foundation

PHASE17
  -> Reader runtime / envelope / bridge

PHASE18
  -> Provider pool / budget / cache guard

PHASE19
  -> Mass intake / fast snapshot

PHASE20
  -> Whale entity intelligence
  -> PASS17 / Whale Runtime

PHASE21
  -> Known wallet registry baseline
  -> Whale Runtime support

PHASE22
  -> Risk readmodel / hard block / slippage
  -> Risk Engine

PHASE23
  -> Risk math / outcome memory planning
  -> Execution Layer and Risk Engine

PHASE31-32
  -> System control / maintenance / AI proposal boundaries

PHASE35-36
  -> Fast path compact state / learning calibration

PHASE37-39
  -> Opportunity Radar / Cost Risk / Shadow Simulation

PHASE40
  -> Technical Tactical Adaptive Learning Engine

PHASE41
  -> Command center binding / simulation drift / provider policy / paper memory

## 09 PASS TO PANEL MAP

PASS13 Evidence Dictionary
  -> PANEL08 System Control
  -> PANEL05 Risk Security

PASS14 Deployer Intelligence
  -> PANEL04 Onchain
  -> PANEL05 Risk Security

PASS15 Contract DNA
  -> PANEL04 Onchain
  -> PANEL05 Risk Security

PASS16 Market Regime
  -> PANEL01 Command
  -> PANEL07 Technical

PASS17 Wallet Cluster
  -> PANEL03 Whale Tracking

PASS18 Technical Signal
  -> PANEL07 Technical Analysis

PASS19 Learning Feedback
  -> PANEL08 System Control
  -> PANEL01 Command

PASS20 Decision Intelligence
  -> PANEL01 Command
  -> PANEL05 Risk Security

PASS21 Execution Realism
  -> PANEL01 Command

PASS22 Position Sizing
  -> PANEL05 Risk Security
  -> PANEL01 Command

PASS23 Portfolio Risk
  -> PANEL05 Risk Security

PASS24 Launch Intelligence
  -> PANEL02 News Flow
  -> PANEL01 Command

PASS25 Historical Launch
  -> PANEL02 News Flow
  -> PANEL08 System Control

PASS26 Launch Outcome
  -> PANEL02 News Flow
  -> PANEL01 Command

PASS27 Execution Accounting
  -> PANEL01 Command
  -> PANEL08 System Control

## 10 ENGINE TO PANEL MAP

ENGINE01 Evidence Runtime
  -> PANEL08 System Control

ENGINE02 Prosecutor Engine
  -> PANEL05 Risk Security
  -> PANEL04 Onchain

ENGINE03 Priority Engine
  -> PANEL01 Command

ENGINE04 Whale Runtime
  -> PANEL03 Whale Tracking

ENGINE05 Technical Tactical Engine
  -> PANEL07 Technical Analysis

ENGINE06 Memory Learning
  -> PANEL08 System Control
  -> PANEL01 Command

ENGINE07 Risk Engine
  -> PANEL05 Risk Security
  -> PANEL01 Command

ENGINE08 Execution Layer
  -> PANEL01 Command

ENGINE09 Hunter Engine
  -> PANEL02 News Flow
  -> PANEL01 Command

ENGINE10 Execution Accounting
  -> PANEL01 Command
  -> PANEL08 System Control

## 11 PANEL ARCHITECTURE

PANEL01 Komuta ve Karar Merkezi
  Role: final cockpit / decision support
  Shows: token, entry, SL, TP, Vur-Kac, Atis Poligonu, approval

PANEL02 Haber Akis Merkezi
  Role: news/social/launch context
  Shows: X, Telegram, Discord, listing, launch, narrative

PANEL03 Balina Takip Merkezi
  Role: smart money and wallet intelligence
  Shows: known wallets, CEX flow, clusters, holder risk

PANEL04 Onchain Veri Merkezi
  Role: token/pair/contract/LP truth
  Shows: pair, LP, holder, deployer, contract, source lineage

PANEL05 Risk Guvenlik Merkezi
  Role: hard safety gate
  Shows: honeypot, sellability, liquidity, RWD, hard block

PANEL06 Yasam Destek Merkezi
  Role: token lifecycle and quarantine
  Shows: clinical state, morg, deep scan, quarantine

PANEL07 Teknik Analiz Merkezi
  Role: technical/tactical radar
  Shows: ARI, TPI, EPI, CLHS, CESS, CPEI, CFBD, RWD

PANEL08 Sistem Kontrol Merkezi
  Role: factory manager
  Shows: phase status, audit, rollback, policy, maintenance

## 12 MASTER ASCII MAP

                    +----------------------+
                    |   PANEL01 COMMAND    |
                    +----------^-----------+
                               |
                    +----------+-----------+
                    |   LEARNING MEMORY    |
                    +----------^-----------+
                               |
                    +----------+-----------+
                    |  SHADOW / PAPER SIM  |
                    +----------^-----------+
                               |
      +------------------------+------------------------+
      |                                                 |
+-----+------+                                  +-------+------+
| TECHNICAL  |                                  |   HUNTER     |
| ENGINE05   |                                  |   ENGINE09   |
+-----^------+                                  +-------^------+
      |                                                 |
      +------------------------+------------------------+
                               |
                    +----------+-----------+
                    |    RISK ENGINE07     |
                    +----------^-----------+
                               |
                    +----------+-----------+
                    |  EVIDENCE RUNTIME    |
                    +----------^-----------+
                               |
                    +----------+-----------+
                    |  ONCHAIN / PROVIDER  |
                    +----------^-----------+
                               |
                    +----------+-----------+
                    |     RAW SOURCES      |
                    +----------------------+

## 13 FUTURE VISUAL ATLAS

Visual Atlas hedefi:
- Da Vinci teknik defteri hissi
- hafif renkli flow cizgileri
- engine halkalari
- panel merkezleri
- risk authority kirmizi omurga
- AI authority zero muhuru
- command center ana dugum
- phase/pass/engine/panel capraz harita

Bu dosya metinsel master atlas olarak kilitlenir.
Gorsel versiyon ayrica uretilecek.
