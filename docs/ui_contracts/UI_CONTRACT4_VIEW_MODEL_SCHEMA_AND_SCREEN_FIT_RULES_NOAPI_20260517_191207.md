# Tokenoskobi / Coinoskobi View Model Schema & Screen Fit Rules v1

Phase: `UI_CONTRACT4_VIEW_MODEL_SCHEMA_AND_SCREEN_FIT_RULES_NOAPI`  
Timestamp: `20260517_191207`  
Depends on:
- `/root/tokenoskobi_clean_v1/docs/ui_contracts/LATEST_UI_CONTRACT1_VIEWPORT_FIT_AND_SINGLE_SOURCE_POLICY_NOAPI.md`
- `/root/tokenoskobi_clean_v1/docs/ui_contracts/LATEST_UI_CONTRACT2_SCREEN_MAP_AND_DATA_OWNERSHIP_NOAPI.md`
- `/root/tokenoskobi_clean_v1/docs/ui_contracts/LATEST_UI_CONTRACT3_MOTION_STATE_AND_TRUTH_ENGINE_NOAPI.md`

## 1. Ana kural

Screen sadece `view_model` render eder.

Screen şunları yapmaz:

- hesap yapmaz
- veri kopyalamaz
- fake metric üretmez
- motion uydurmaz
- canonical source dışında karar vermez

## 2. Viewport fit baseline

### Body

- height: 100vh
- overflow: hidden
- ana ekranlarda vertical body scroll yasak

### Screen shell

- height: 100vh
- grid/flex layout
- header / content / footer veya sidebar / main alanları tek ekrana oturur

### Detail surfaces

Lokal scroll sadece şuralarda olabilir:

- drawer
- modal
- right inspector
- detail tab

## 3. Breakpoints

### compact_laptop

- width: 1280-1365
- height: 720-800
- density: compact

Kurallar:
- compact font
- dense spacing
- summary-first rendering
- large decorative empty areas yok
- detail drawer preferred

### standard_laptop

- width: 1366-1536
- height: 768-900
- density: balanced

Kurallar:
- primary target layout
- tüm ana paneller fit geçmeli
- Token Yaşam 6-card grid fit geçmeli
- Ana Panel token/action grid fit geçmeli

### desktop

- width: 1537+
- height: 900+
- density: expanded

Kurallar:
- büyük radar/icon surface kullanılabilir
- daha geniş spacing olabilir
- yine body scroll yok
- detail drawer daha geniş olabilir

## 4. Global view model schema

Her ekran view model alanları:

- screen_id
- generated_at
- freshness_seconds
- data_status: ok / partial / stale / missing / blocked
- source_refs
- summary
- cards
- actions
- motion_states
- detail_refs
- fit_profile
- warnings
- empty_state

## 5. Main Panel VM

Canonical inputs:

- identity_layer
- market_layer
- risk_layer
- paper_trade_layer
- lifecycle_layer
- motion_state_layer

Tracked token fields:

- token_uid
- symbol
- chain
- price
- price_change
- liquidity
- risk_score
- decision_state
- position_state
- sl_status
- tp_status
- freshness_seconds
- motion_state_ref

Trade controls:

- buy_enabled
- sell_enabled
- buy_disabled_reason
- sell_disabled_reason
- max_safe_buy
- position_size_suggestion
- paper_live_mode

Fit rules:

- Token list scroll değil pagination/compact rows kullanır.
- Buy/Sell/SL/TP görünür kalır.
- Detay drawer açılınca main grid ezilmez.
- Ana ekranda raw tx/news/autopsy listesi basılmaz.

## 6. Token Yaşam VM

Canonical inputs:

- lifecycle_layer
- identity_layer
- market_layer
- risk_layer
- onchain_layer
- motion_state_layer

Departman fields:

### Olay Yeri

- event_count
- last_event_freshness
- first_evidence_state
- motion_state_ref
- detail_ref

### Adli

- investigation_state
- relationship_confidence
- evidence_count
- motion_state_ref
- detail_ref

### Şüpheliler

- suspect_wallet_count
- highest_risk_actor
- cluster_confidence
- motion_state_ref
- detail_ref

### Klinik

- clinical_state
- recovery_chance_band
- watch_intensity
- motion_state_ref
- detail_ref

### Otopsi

- autopsy_status
- failure_class
- outcome_memory_state
- motion_state_ref
- detail_ref

### Morg

- morg_status
- archived_dead_count
- revival_watch_count
- cold_state_status
- motion_state_ref
- detail_ref

Fit rules:

- 6 departman kartı tek ekranda kalır.
- Kartlar sadece özet gösterir.
- Detaylar drawer/tab ile açılır.
- Klinik/Otopsi/Morg detayları ana karta yığılmaz.
- motion_state_ref yoksa ikon statik kalır.

## 7. Haber Panel VM

Canonical inputs:

- news_layer
- identity_layer
- motion_state_layer

News card fields:

- news_event_uid
- title
- translated_title
- importance_score
- source_reliability
- token_connection_score
- freshness_seconds
- motion_state_ref
- detail_ref

Fit rules:

- Top news lanes fit screen.
- Full article detail drawer’da açılır.
- Rumor critical gibi gösterilmez.
- Token-specific alarm için token_connection_score gerekir.

## 8. Whale Panel VM

Canonical inputs:

- onchain_layer
- identity_layer
- risk_layer
- motion_state_layer

Radar fields:

- radar_state
- active_event_count
- largest_event
- freshness_seconds
- motion_state_refs

Top event fields:

- event_uid
- wallet
- amount
- direction
- chain
- confidence
- risk_score
- freshness_seconds
- detail_ref

Fit rules:

- Radar sadece fresh whale event ile hareket eder.
- Event yoksa radar silent state.
- Wallet history drawer’da açılır.
- Top events sınırlı sayıda gösterilir.

## 9. Risk Panel VM

Canonical inputs:

- risk_layer
- market_layer
- onchain_layer
- identity_layer
- motion_state_layer

Risk card fields:

- hard_block
- risk_score
- confidence
- max_safe_buy
- position_size_suggestion
- liquidity_capacity
- slippage_risk
- mev_risk
- gas_risk
- detail_ref

Fit rules:

- Risk summary cards fit screen.
- Formula/calculation detail drawer’da açılır.
- Hard block varsa buy animation yok.
- Risk verisi yoksa unknown/silent.

## 10. Paper Panel VM

Canonical inputs:

- paper_trade_layer
- risk_layer
- market_layer
- identity_layer
- motion_state_layer

Paper plan fields:

- plan_uid
- token_uid
- entry_plan
- sl_status
- tp_status
- position_state
- outcome_state
- paper_live_mode
- detail_ref

Fit rules:

- Active paper plans fit screen.
- Execution/outcome detail drawer’da açılır.
- Paper/live ayrımı her zaman görünür.
- Gerçek live trade izinsiz görünmez/çalışmaz.

## 11. Detail model rules

Primary cards heavy data taşımaz. `detail_ref` taşır.

Allowed detail surfaces:

- drawer
- modal
- right inspector
- department detail tab

Forbidden:

- primary screen long raw table
- primary screen full log dump
- primary screen repeated same metric
- detail component içinde motion state üretmek

## 12. FIT_PASS requirements

- body scrollHeight <= viewport height for primary screen
- critical controls visible without scroll
- sidebar visible without scroll
- main content not clipped
- detail surfaces local-scroll only
- laptop and desktop fit profiles both pass

## 13. DATA_PASS requirements

- all view model fields map to canonical layer
- no duplicate calculation in panel
- no hardcoded production metrics
- missing data returns explicit empty_state
- motion_states are read-only references

## 14. PRODUCT_PASS requirements

- screen looks premium
- density feels intentional
- motion does not distract
- icons and text are balanced
- user can understand state quickly
- no cheap/fake effect

## 15. Next phase

`UI_CONTRACT5_PANEL_IMPLEMENTATION_GATES_NOAPI`
