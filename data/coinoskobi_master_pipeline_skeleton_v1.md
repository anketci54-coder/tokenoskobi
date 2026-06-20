# Coinoskobi Master Pipeline Skeleton v1

Phase: `COINOSKOBI_MASTER_PIPELINE_SKELETON_PLAN_NOAPI`
Generated: `20260522_095158`
Mode: `PLAN_ONLY_NOAPI`

## Ana hedef

DEX borsalarında yeni gelen token/coin adaylarını, ICO/IDO/drop sinyallerini, haber/narrative akışını, on-chain veriyi, balina hareketlerini, teknik veriyi, risk/MEV kontrollerini ve paper sim sonucunu tek karar omurgasına bağlamak.

## Master akış

```text
External Sources
  -> RAW_INGESTION
  -> STAGING_PARSE
  -> IDENTITY_ENTITY_MATCH
  -> TRUTH_VALIDATION_GATE
  -> CENTER_PROCESSORS
  -> FUSION_SCORE_ENGINE
  -> COMMAND_CENTER_DECISION
  -> PAPER_SIMULATION
  -> OUTCOME_MEMORY_MORGUE_AUTOPSY
  -> DASHBOARD_VIEW_MODEL
```

## Pipeline katmanları

| Layer | Job |
| --- | --- |
| RAW_INGESTION | Dış kaynaklardan ham veriyi source/hash/time ile alır. Karar vermez. |
| STAGING_PARSE | Ham veriyi parse eder, alanları ayırır, kalite hatalarını yazar. |
| IDENTITY_ENTITY_MATCH | Token_uid, pair_uid, chain, contract ve source kimliğini eşler. |
| TRUTH_VALIDATION_GATE | Wrong pair, no pair, source conflict, stale pair, fake/liquidity uyumsuzluğu kontrol eder. |
| CENTER_PROCESSORS | Her merkez kendi sinyalini üretir: news/onchain/wallet/technical/risk/lifecycle/system. |
| FUSION_SCORE_ENGINE | Merkez skorlarını birleştirir ve route üretir. |
| COMMAND_CENTER_DECISION | Watchlist, paper-ready, wait-more-data, blocked, morgue gibi son yönlendirme yapar. |
| PAPER_SIMULATION | Sanal entry/SL/TP/exit/PnL/drawdown ve hata tagleri üretir. |
| OUTCOME_MEMORY_MORGUE_AUTOPSY | Kazanan/kaybeden aday hafızası, morg ve otopsi katmanı. |
| DASHBOARD_VIEW_MODEL | Panelin okuyacağı sade JSON view-model üretir. |

## Merkez görevleri

| Merkez | Rol | Input | Output |
| --- | --- | --- | --- |
| Komuta Merkezi | Son karar, watchlist, paper, açık pozisyon, SL/TP, aksiyon geçmişi. | fusion_score_events, command_decision_events, paper_trade_events | watchlist_view, live_decision_view, paper_summary_view, action_history_view |
| Haber Akış Merkezi | Haber, narrative, ICO/IDO/drop, listing, hack, partnership, launch sinyali. | raw_news_events, raw_launch_events | news_signal_events, launch_signal_events, narrative_signal_events |
| On-Chain Veri Merkezi | Token/pair/liquidity/volume/tx/pool doğrulama. | raw_dex_pair_events, raw_onchain_market_events | identity_signal_events, liquidity_signal_events, activity_signal_events |
| Balina Takip Merkezi | Known wallet, whale tier, smart money, wallet-token ilişkisi. | raw_wallet_events | wallet_signal_events, whale_signal_events, smart_money_signal_events |
| Teknik Analiz Merkezi | OHLC, momentum, volatilite, trend, destek/direnç, giriş/çıkış zamanı. | raw_ohlc_events, market_snapshots | technical_signal_events, volatility_signal_events, entry_timing_events |
| Risk & Güvenlik Merkezi | Contract, honeypot, tax, liquidity lock, deployer, cluster, fake volume, MEV/sandwich. | raw_risk_events, onchain_signal_events, wallet_signal_events | risk_signal_events, mev_sandwich_risk_events, hard_block_events |
| Yaşam Destek Merkezi | Token yaşam döngüsü, klinik, yoğun bakım, morg, otopsi, negatif hafıza. | validation_events, risk_signal_events, paper_trade_events, outcome_events | lifecycle_events, morgue_events, autopsy_events |
| Sistem Kontrol Merkezi | DB, runner, timer, API budget, servis, panel sağlığı. | system_events, validation_runs, runner_logs | system_health_events, api_budget_events, service_state_events |

## MEV / Sandwich Risk Motoru

Motor: `MEV_SANDWICH_RISK_ENGINE_V1`

Inputlar:
- liquidity_depth
- swap_price_impact
- slippage_required
- tx_burst_1m_5m
- buy_sell_imbalance
- gas_spike
- same_block_or_same_window_swap_pattern
- known_bot_wallet_touch
- pool_age
- entry_size_vs_pool_depth

Outputlar:
- MEV_LOW
- MEV_MEDIUM
- MEV_HIGH
- SANDWICH_EXPOSURE_DETECTED
- ENTRY_SIZE_REDUCE
- ENTRY_BLOCKED
- SLIPPAGE_LIMIT_REQUIRED
- PRIVATE_RPC_RECOMMENDED

Hard-block kombinasyonları:
- MEV_HIGH + LOW_LIQUIDITY + HIGH_SLIPPAGE
- SANDWICH_EXPOSURE_DETECTED + POOL_DEPTH_WEAK
- KNOWN_BOT_CLUSTER + ENTRY_SIZE_TOO_LARGE

## Fusion score alanları
- identity_score
- source_score
- liquidity_score
- activity_score
- news_score
- launch_score
- wallet_score
- technical_score
- risk_score
- mev_score
- lifecycle_score

## Route tipleri
- STRONG_WATCH
- ACTIVE_WATCH
- ASYMMETRIC_WATCH
- TINY_REVIEW
- WEAK_REVIEW
- BLOCKED_WITH_REASON
- MORGUE
- PAPER_ELIGIBLE

## Komuta karar tipleri
- NO_ACTION
- WATCH
- WAIT_MORE_DATA
- PAPER_ENTRY_READY
- ENTRY_SIZE_REDUCE
- ENTRY_BLOCKED
- MORGUE_ROUTE
- AUTOPSY_ROUTE

## DB tablo planı

| Table | Purpose | Key Fields |
| --- | --- | --- |
| raw_discovery_events_v1 | DEX/launch/news/wallet/risk ham kaynak olayları. | raw_event_uid, source_group, source_name, chain, content_hash, seen_at, payload_json |
| entity_identity_events_v1 | Token/pair/entity kimlik eşleştirme. | entity_uid, token_uid, pair_uid, chain, contract, pair_address, identity_status |
| center_signal_events_v1 | Merkezlerin standart sinyal çıkışı. | signal_uid, center_key, token_uid, pair_uid, signal_type, score, severity, evidence_json |
| mev_sandwich_risk_events_v1 | MEV/sandwich risk skoru ve entry etkisi. | mev_uid, token_uid, pair_uid, mev_level, slippage_hint, entry_gate, evidence_json |
| fusion_score_events_v1 | Birleşik skor ve route sonucu. | fusion_uid, token_uid, pair_uid, final_score, route, hard_blocks_json, soft_warnings_json |
| command_decision_events_v1 | Komuta Merkezi son karar ve gerekçeleri. | decision_uid, token_uid, pair_uid, decision_type, entry_size_hint, sl_tp_plan_json, reason_json |
| paper_trade_events_v1 | Paper sim entry/exit/PnL/drawdown. | paper_uid, decision_uid, token_uid, pair_uid, entry, exit, pnl, drawdown, exit_reason |
| outcome_memory_events_v1 | Kazanan/kaybeden aday hafızası. | outcome_uid, token_uid, pair_uid, outcome_type, mistake_tags_json, learning_notes_json |
| control_dashboard_view_model_events_v1 | Panelin okuyacağı view-model snapshot. | view_uid, generated_at, panel_scope, view_model_json, source_counts_json |

## Sonraki fazlar
- COINOSKOBI_MASTER_PIPELINE_SCHEMA_DRYRUN_NOAPI
- COINOSKOBI_SIGNAL_EVENT_CONTRACT_DRYRUN_NOAPI
- COINOSKOBI_MEV_SANDWICH_RISK_ENGINE_PLAN_NOAPI
- COINOSKOBI_VIEW_MODEL_BUILDER_DRYRUN_NOAPI
- COINOSKOBI_ONE_TOKEN_PIPELINE_SIM_NOAPI
- COINOSKOBI_PAPER_DECISION_DRYRUN_NOAPI

## Kural

Live trade kapalı. Önce watch-only ve paper sim. Hard-block dışında adaylar silinmez; zayıf adaylar da hafıza ve otopsi için kayıt altında kalır.
