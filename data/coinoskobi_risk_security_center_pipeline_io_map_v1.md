# Coinoskobi Risk & Güvenlik Merkezi Pipeline I/O Map v1

Phase: `COINOSKOBI_RISK_SECURITY_CENTER_PIPELINE_IO_MAP_PLAN_NOAPI`
Generated: `20260522_112817`

## Amaç

Risk & Güvenlik Merkezi, sisteme giren her token/pair adayının karar motoruna gitmeden önce geçtiği ana risk kavşağıdır.

Bu merkez sadece MEV kutusu değildir. Kimlik, likidite, piyasa aktivitesi, cüzdan, haber, teknik, kontrat, MEV/mempool, yaşam/morg/otopsi ve outcome memory hatlarının tamamını toplar.

## Inbound Lines

| Line | Source | Risk Center Use | Risk Output |
| --- | --- | --- | --- |
| Raw Discovery | raw_discovery_events_v1 | Aday token/pair kaynagini ve ilk gorulme anini risk merkezine tasir. | SOURCE_CONFIDENCE, NEW_PAIR_CONTEXT |
| Entity Identity | entity_identity_events_v1 | Token, pair, chain, adres, sembol ve kimlik kalitesini dogrular. | IDENTITY_RISK, ADDRESS_CONFIDENCE |
| Liquidity & Volume | future_liquidity_snapshot, market_snapshot | Pool derinligi, hacim ve exit satilabilirligini olcer. | LIQUIDITY_RISK, EXIT_RISK |
| Market Activity | future_swap_activity, center_signal_events_v1 | Tx burst, buy/sell imbalance, pool age ve aktivite sagligini olcer. | ACTIVITY_RISK, BURST_RISK |
| Wallet / Whale | future_wallet_cluster, future_whale_signal | Deployer, balina, smart money, bot wallet ve cluster temasini olcer. | WALLET_RISK, BOT_WALLET_RISK |
| News / Social | future_news_events, future_social_events | Haber, narrative, hype, negatif olay ve sosyal manipülasyon riskini olcer. | NARRATIVE_RISK, SOCIAL_MANIPULATION_RISK |
| Technical Context | future_ohlc, future_ta_signal | Volatilite, momentum, trend ve teknik giris riskini olcer. | TECHNICAL_RISK, VOLATILITY_RISK |
| Contract Risk | future_contract_security_scan | Honeypot, sell tax, blacklist, mint, pause, proxy, ownership ve upgrade riskini olcer. | CONTRACT_RISK, HONEYPOT_RISK, TAX_RISK |
| MEV / Mempool | mev_sandwich_risk_events_v1, future_mempool_observer | Slippage, price impact, pending tx, sandwich exposure ve protected route ihtiyacini olcer. | MEV_RISK, SANDWICH_RISK, PROTECTED_ROUTE_REQUIRED |
| Lifecycle / Morg / Otopsi | outcome_memory_events_v1, future_morg_autopsy | Gecmis hatalar, olum sinyalleri, missed run ve false positive hafizasini tasir. | MEMORY_RISK, AUTOPSY_WARNING |
| Paper / Outcome Memory | paper_trade_events_v1, outcome_memory_events_v1 | Paper sonucunu ve risk kararinin gerceklesme kalitesini geri besler. | RISK_CALIBRATION, SIZE_POLICY_LEARNING |

## Internal Risk Layers

| Layer | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| Identity Risk Gate | Token/pair kimligi zayifsa tum karar zincirine risk penalty veya block uretir. | raw_discovery, entity_identity | IDENTITY_RISK, SOURCE_CONFIDENCE |
| Liquidity & Exit Risk | Giris kadar cikisin da yapilabilir olup olmadigini olcer. | liquidity_volume, market_activity | LIQUIDITY_RISK, EXIT_RISK |
| Contract Security | Honeypot, tax, blacklist, mint, pause, owner/proxy risklerini karar kapisina baglar. | contract_risk, entity_identity | CONTRACT_BLOCK, CONTRACT_WARNING |
| MEV Shield v1/v2 | Sandwich/slippage/price impact/private route riskini olcer. | mev_mempool, liquidity_volume, market_activity | MEV_ALLOW, MEV_REDUCE_SIZE, MEV_BLOCK, PROTECTED_ROUTE_REQUIRED |
| Wallet Pressure | Bot wallet, deployer, balina ve holder baskisini risk merkezine tasir. | wallet_whale, market_activity | WALLET_WARNING, BOT_CLUSTER_WARNING |
| Lifecycle Memory Gate | Morg/otopsi/paper/outcome hafizasiyla risk kararlarini kalibre eder. | lifecycle_memory, paper_outcome | MEMORY_WARNING, AUTOPSY_ROUTE, MORGUE_ROUTE |
| Security Score Fusion | Butun riskleri tek security_score ve risk_level altinda birlestirir. | all_risk_outputs | LOW, MEDIUM, HIGH, CRITICAL |
| Command Gate | Komuta motoruna nihai risk kararini gonderir. | risk_fusion | ALLOW, REDUCE_SIZE, PAPER_ONLY, BLOCK, MORGUE, AUTOPSY |

## Outbound Lines

| Line | Target Table | Purpose | Decision Effect |
| --- | --- | --- | --- |
| center_signal_events | center_signal_events_v1 | Risk merkezinin ana sinyalini center_signal olarak yazar. | Risk panel ve fusion skor icin ana sinyal. |
| mev_sandwich_risk_events | mev_sandwich_risk_events_v1 | MEV/sandwich ozel risk sonucunu yazar. | MEV gate ALLOW/REDUCE_SIZE/BLOCK. |
| fusion_score_events | fusion_score_events_v1 | Security score, hard block ve soft warning etkisini fusion skoruna tasir. | Genel skor ve route etkisi. |
| command_decision_events | command_decision_events_v1 | Risk merkezi kararini komuta motoruna kapı olarak aktarir. | ALLOW / REDUCE_SIZE / PAPER_ONLY / BLOCK / MORGUE. |
| paper_trade_events | paper_trade_events_v1 | Paper eligibility, sermaye kucultme veya paper iptal durumunu yazar. | Paper plan ve risk limitleri. |
| outcome_memory_events | outcome_memory_events_v1 | Risk kararinin sonucunu hafizaya tasir. | Gelecek risk kalibrasyonu. |
| control_dashboard_view_model_events | control_dashboard_view_model_events_v1 | Panelde risk kutulari, blok sebepleri, uyarilar ve onerilen aksiyonlari gosterir. | Risk & Güvenlik Merkezi UI. |

## Risk Levels

| Level | Score Range | Meaning | Command Gate | Paper Policy |
| --- | --- | --- | --- | --- |
| LOW | 0-24 | Izlenebilir risk. | ALLOW | Normal paper izleme. |
| MEDIUM | 25-49 | Risk var, pozisyon kucultulmeli veya slipaj sinirlanmali. | REDUCE_SIZE | Kucuk paper, dynamic slippage cap. |
| HIGH | 50-74 | Paper-only veya protected route gerekli. | PAPER_ONLY | Canli yok, sadece paper/lab. |
| CRITICAL | 75-100 or hard block | Entry blocked, morg/otopsi rotasi. | BLOCK | Paper bile iptal edilebilir veya sadece observation. |

## Safe Lane

- Read-only diagnostics
- Risk scoring
- Dynamic slippage recommendation
- Protected route recommendation
- Entry size reduction
- Paper/lab simulation
- Outcome memory learning

## Forbidden Live Actions

- honeypot bot tuzagi
- Salmonella veya ters arbitraj yem islemi
- frontrun counter-attack execution
- bot cüzdani kilitleme veya fon sıkıştırma
- canli JIT liquidity execution
- canli exploit/manipulative MEV stratejisi

## Next

`COINOSKOBI_MEV_MEMPOOL_PROTECTION_LAYER_PLAN_NOAPI`
