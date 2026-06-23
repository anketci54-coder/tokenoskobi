# TOKENOSKOBI CLEAN V1 — 14 FAZLIK ROADMAP

## FAZ 0 — Ana Prensip / Güvenlik Kilidi
[x] Canlı trade kapalı.
[x] Paper/live ayrı tutuluyor.
[x] Registry/quality dosyalarına kontrolsüz yazma yok.
[x] Stale/veri bozuk kaynaklar genişletilmiyor.
[x] Riskli token otomatik çöpe atılmıyor; riskine göre rota değiştiriliyor.
[x] Öncelik: mimariyi gözden geçir, gerekirse revize et, sonra devam et.

## FAZ 1 — Architecture Review / Yol Haritası
[x] Mevcut tüm modülleri haritala.
[x] Death Core / Life Core / Moonshot Core ayrımını başlat.
[x] Eski patch karmaşasını frozen/reference olarak ayır.
[x] Lab / Paper / Live / Moonshot Basket yollarını hedef mimaride ayır.
[x] Tek kimlik standardını belirle: chain + token_address + pair_address + deployer_address.
[x] Kalıcı quality gate gereksinimini belirle.

## FAZ 2 — Clean V1 Root + Eski Sistemi Freeze
[ ] Eski sistemi frozen/reference kabul et.
[ ] Yeni clean root oluştur.
[ ] Config/core/data/reports/backups/logs/scripts/tests/docs yapısını oluştur.
[ ] Eski scriptleri yeni sisteme taşıma.

## FAZ 3 — Forensic Warehouse / Veri Omurgası
[ ] Token doğum kaydı.
[ ] İlk pair kaydı.
[ ] İlk likidite kaydı.
[ ] İlk tx/hacim/fiyat kaydı.
[ ] Deployer geçmişi.
[ ] Holder dağılımı.
[ ] Wallet hareketleri.
[ ] Liquidity değişimleri.
[ ] Tax/honeypot/sellability kontrolleri.
[ ] Outcome labels.
[ ] Time-series snapshots.
[ ] Token biography.

## FAZ 4 — Identity + Quality Gate
[ ] UID guard.
[ ] Pair quality gate.
[ ] Stale pair gate.
[ ] Alias confusion gate.
[ ] Duplicate control.

## FAZ 5 — Death Core
[x] Hard risk hafızası başladı.
[x] Stale pair yakalandı.
[x] Pair conflict mantığı başladı.
[x] Sahte/ölü Batch-0 genişletilmedi.
[ ] Honeypot/sell simulation.
[ ] Deployer rug history.
[ ] Fake/pulled liquidity alarm.
[ ] Dead token label.
[ ] Rug autopsy.
[ ] Death Pattern Library.

## FAZ 6 — Life Core
[x] 2/3/4 nokta snapshot testleri yapıldı.
[x] Safu Scanner HOLD mantığı görüldü.
[x] Güçlü aday seçici çalıştı.
[ ] 15m/1h/4h/24h yaşam kontrolü.
[ ] Liquidity retention.
[ ] Tx continuity.
[ ] Organic/bot volume.
[ ] Holder growth.
[ ] Whale exit.
[ ] Alive Score.

## FAZ 7 — Moonshot Core
[ ] Narrative Score.
[ ] Founder Score.
[ ] Community Organic Score.
[ ] Whale Accumulation Score.
[ ] Tokenomics Safety Score.
[ ] CEX Potential Score.
[ ] Sector Timing Score.
[ ] Survival Score.
[ ] Scam/Rug Risk Score.
[ ] Asymmetry Score.
[ ] Moonshot Probability Band.

## FAZ 8 — Risk Budget / Position Sizing
[ ] Risk level.
[ ] Opportunity level.
[ ] Risk/opportunity ratio.
[ ] REJECT / WATCH_ONLY / PAPER_TEST / MICRO_OBSERVE / MOONSHOT_BASKET / SHORT_TRADE.
[ ] Size down as risk rises.
[ ] Hard fail zero permission.

## FAZ 9 — Sandwich Shield
[ ] Public mempool block.
[ ] Private RPC / MEV protection.
[ ] Dynamic slippage.
[ ] Price impact limit.
[ ] Trade size/liquidity ratio.
[ ] Pre-trade simulation.
[ ] Min received.
[ ] Short deadline.
[ ] Gas anomaly.
[ ] Mempool exposure score.
[ ] Post-trade sandwich detector.
[ ] Low liquidity live block.
[ ] Chain-specific route.
[ ] Fail-safe no live if MEV protection inactive.

## FAZ 10 — Trade Wallet / Moonshot Wallet Ayrımı
[ ] Trade wallet.
[ ] Moonshot wallet.
[ ] Separate limits.
[ ] Stop/profit-lock.
[ ] Trade değil, moonshot watch kararı.

## FAZ 11 — News / Narrative Core
[ ] X/Twitter.
[ ] Telegram/Discord.
[ ] Website/docs/whitepaper/GitHub.
[ ] Sector trends.
[ ] Organic vs influencer pump.

## FAZ 12 — Pilot 3-5 Token Test
[ ] 3-5 token.
[ ] Base + BNB.
[ ] Clean identity.
[ ] UID guard.
[ ] Local snapshot.
[ ] Validation PASS.
[ ] Report.

## FAZ 13 — Base + BNB Küçük Musluk
[ ] DexScreener capped refresh.
[ ] Alchemy closed.
[ ] JSON-RPC closed.
[ ] 5 token.
[ ] 10 token.
[ ] 25 token.
[ ] Validation after every batch.

## FAZ 14 — AI Training Dataset
[ ] 30 days clean data.
[ ] 60 days clean data.
[ ] 90 days clean data.
[ ] Labels: dead, alive, rug, fake, x2, x5, x10, x50, whale accumulation, short pump, long watch.
[ ] Death prediction.
[ ] Survival prediction.
[ ] Pump-risk prediction.
[ ] Moonshot model.

================================================================
POST AUDIT ROADMAP
================================================================

PHASE_A
Canonical Producer Mapping

PHASE_B
Consumer Mapping

PHASE_C
Runtime Consolidation

PHASE_D
News Intelligence Reactivation

PHASE_E
Wallet Intelligence Consolidation

PHASE_F
Technical Tactical Consolidation

PHASE_G
Shadow Validation

PHASE_H
Production Readiness


================================================================
