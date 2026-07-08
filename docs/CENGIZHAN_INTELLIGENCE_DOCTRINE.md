# CENGIZHAN INTELLIGENCE DOCTRINE

- generated_at_utc: `2026-07-08T13:04:26.805247+00:00`
- source_stage: `NEWS_F_FINAL_OPERATIONAL_SEAL_WITH_KNOWN_WARNINGS`
- current_news_seal: `COLD_NEWS_PRODUCER_OPERATIONAL_WITH_KNOWN_WARNINGS`
- hot_gateway_status: `DEFERRED_AFTER_NEWS_F`

## Doctrine

1. Ordu uyumaz.
2. Haber beklenmez; haber avlanır.
3. Her haber komutaya gitmez.
4. Alakasız haber kapıda öldürülür.
5. Kritik haber hızlı ulakla taşınır.
6. Psikolojik harp ayrı risk sınıfıdır.
7. Tuzak, sahte panik, manipülasyon ve aldatma erken sezilir.
8. Lojistik yoksa istihbarat yoktur.
9. Teknoloji, hız ve disiplin aynı zincirde çalışır.
10. 20 dakikalık timer sadece cold backfill/fallback hattıdır; ana istihbarat mimarisi değildir.

## Cold / Hot Split

### COLD NEWS REFRESH

- Current state: `OPERATIONAL_WITH_KNOWN_WARNINGS`
- Purpose: missed-news backfill, audit trail, low-cost periodic scan.
- Timer: `20min`
- Not final war intelligence.

### HOT_INTELLIGENCE_INGRESS_GATEWAY

- Status: `NEXT_SAFE_STEP_AFTER_NEWS_F`
- Sources: Telegram, Discord, X, fast crypto news, onchain watcher, wallet watcher, mempool/DEX signals.
- Gate: relevance filter, source trust, duplicate filter, adversarial tactic classifier.
- Router: CRITICAL / WATCH / INFO / DROP.
- Conflict layer: onchain vs social vs news conflict resolution.
- Consumers: Hunter, Prosecutor, Risk, Whale, Panel, Telegram alarm.

## Forbidden Claims

- NEWS fully clean
- panel fully verified
- freshness fully current
- real-time intelligence implemented
- hot intelligence gateway implemented
- trade or paper authority enabled
