# Tokenoskobi / Coinoskobi Screen Map & Data Ownership Contract v1

Phase: `UI_CONTRACT2_SCREEN_MAP_AND_DATA_OWNERSHIP_NOAPI`  
Timestamp: `20260517_190615`  
Depends on: `/root/tokenoskobi_clean_v1/docs/ui_contracts/LATEST_UI_CONTRACT1_VIEWPORT_FIT_AND_SINGLE_SOURCE_POLICY_NOAPI.md`

## 1. Global kurallar

- Her ekran viewport-fit olacak.
- Body vertical scroll ana ekranlarda yasak.
- Her veri tek canonical owner’dan gelecek.
- Paneller hesap yapmayacak; view model okuyacak.
- Efekt, animasyon, pulse, radar, glow sadece gerçek data/state ile çalışacak.
- Veri yoksa panel susacak veya “beklemede/veri yok” diyecek.
- Ana ekran özet, detaylar drawer/modal/detail tab.

## 2. Canonical data layer sahipliği

### identity_layer
Token, pair, chain, deployer, wallet ve source identity sahibi.

Owned data:
- token_uid
- chain
- token_address
- pair_address
- symbol
- name
- deployer_address
- identity_confidence

### market_layer
Price, liquidity, volume, tx, freshness ve snapshot state sahibi.

Owned data:
- price
- liquidity
- volume
- tx_count
- snapshot_age
- source_freshness
- market_quality

### news_layer
Haber, reliability, importance, token connection ve narrative impact sahibi.

Owned data:
- news_event_uid
- source
- title / translated_title
- importance_score
- source_reliability
- token_connection_score
- risk_signal
- narrative_tag
- freshness

### onchain_layer
Transfer, holder, deployer, liquidity ve wallet relationship sahibi.

Owned data:
- holder_distribution
- transfer_flow
- liquidity_change
- deployer_history
- wallet_cluster_confidence
- smart_money_signal
- contract_risk_signal

### risk_layer
Hard block, risk score, position sizing ve güvenlik sahibi.

Owned data:
- hard_block
- risk_score
- confidence
- liquidity_capacity
- slippage_risk
- mev_risk
- stop_distance
- max_safe_buy
- position_size_suggestion

### lifecycle_layer
Token doğum, klinik, otopsi, morg, revival ve outcome sahibi.

Owned data:
- lifecycle_state
- birth_event
- clinical_watch
- autopsy_status
- morg_status
- revival_signal
- outcome_record

### paper_trade_layer
Paper plan, simulated position, SL/TP ve outcome takip sahibi.

Owned data:
- paper_plan
- paper_position
- entry_plan
- sl_status
- tp_status
- position_state
- execution_simulation
- outcome

### motion_state_layer
Görsel hareket ve living UI truth sahibi.

Owned data:
- motion_state
- motion_reason
- motion_source_uid
- motion_freshness
- motion_intensity
- motion_expiry

Hard rule: source data ve reason yoksa motion yok.

## 3. Screen map

## Ana Panel

Role: Decision and operation center.

Primary content:
- takip edilen token/coin durumu
- buy/sell controls
- SL/TP durumu
- paper/live state
- position state
- risk/decision summary
- data freshness

Detay: Token tıklanınca drawer açılır. Ana grid bozulmaz.

Inputs:
- identity_layer
- market_layer
- risk_layer
- paper_trade_layer
- lifecycle_layer
- motion_state_layer

## Haber Paneli

Role: News reliability, narrative, importance and token impact radar.

Primary content:
- critical news count
- source reliability
- narrative lanes
- token-linked news
- general market flow
- freshness

Detay: Haber tıklanınca source, translation, scoring ve linkage drawer.

Inputs:
- news_layer
- identity_layer
- motion_state_layer

## Onchain Panel

Role: Onchain evidence and flow surface.

Primary content:
- holder distribution summary
- flow direction
- liquidity change summary
- deployer/wallet signal summary
- freshness

Detay: tx/wallet/source evidence drawer.

Inputs:
- onchain_layer
- identity_layer
- market_layer
- motion_state_layer

## Whale Panel

Role: Whale and smart-money event radar.

Motion rule:
- Whale event yoksa radar sweep yok.
- Event size ve confidence pulse intensity belirler.
- Veri eskiyse efekt söner.

Inputs:
- onchain_layer
- identity_layer
- risk_layer
- motion_state_layer

## Risk Panel

Role: Security, MEV, hard block, risk/reward and position sizing.

Primary content:
- hard block
- risk score
- confidence
- max safe buy
- position size suggestion
- slippage / MEV / gas / liquidity warnings

Inputs:
- risk_layer
- market_layer
- onchain_layer
- identity_layer

## Token Yaşam Merkezi

Role: Lifecycle organism.

Viewport rule: 6 departman kartı tek ekranda kalır. Body scroll yok.

Departments:

### Olay Yeri
Summary:
- event count
- last event freshness
- first evidence state

Detail:
- timeline
- first tx
- first liquidity
- first suspicious signal

### Adli
Summary:
- investigation state
- relationship confidence
- evidence count

Detail:
- deployer links
- wallet/source relationships
- confidence reasoning

### Şüpheliler
Summary:
- suspect wallet count
- highest risk actor
- cluster confidence

Detail:
- wallet list
- cluster graph evidence
- bad-wallet memory

### Klinik
Summary:
- clinical state
- recovery chance band
- watch intensity

Detail:
- liquidity trend
- volume trend
- risk treatment plan
- watch conditions

### Otopsi
Summary:
- autopsy status
- failure class
- outcome memory

Detail:
- death cause
- timeline
- risk factors
- lessons learned

### Morg
Summary:
- archived/dead count
- revival watch count
- cold-state status

Detail:
- morg records
- revival signals
- historic outcome

Motion:
- Klinik pulse only if clinical_watch exists.
- Morg cold breath only if morg_status exists.
- Otopsi scan only if autopsy_status is active.
- Olay alarm only if fresh event exists.

## Paper Panel

Role: Paper trade simulator.

Primary content:
- paper plans
- simulated positions
- entry/sl/tp state
- outcome summary
- paper/live separation

Inputs:
- paper_trade_layer
- risk_layer
- market_layer
- identity_layer

## Source Health Panel

Role: Source/fetch/API health.

Primary content:
- source status
- fetch enabled/disabled
- api budget state
- last successful update
- stale/broken source warning

## AI Calibration Panel

Role: Learning, calibration and outcome memory.

Primary content:
- calibration status
- last outcome memory
- confidence drift
- model error classes

## 4. Duplicate data ban

- Main Panel news impact gösterir ama haber skorunu yeniden hesaplamaz.
- Token Yaşam risk özeti gösterir ama risk hesaplamasının sahibi değildir.
- Risk Panel lifecycle state gösterir ama morg/autopsy kayıtlarının sahibi değildir.
- Whale Panel radar oynatır ama motion state’i kendisi uydurmaz.

## 5. Detail pattern

Allowed:
- drawer
- modal
- right-side inspector
- department detail tab inside same viewport

Forbidden:
- body scroll for main screens
- long tables directly in primary screen
- duplicated card copies across panels
- fake placeholder metrics as real

## 6. Next phase

`UI_CONTRACT3_MOTION_STATE_AND_TRUTH_ENGINE_NOAPI`
