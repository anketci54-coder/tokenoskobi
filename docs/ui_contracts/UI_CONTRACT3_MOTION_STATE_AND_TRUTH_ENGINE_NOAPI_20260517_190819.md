# Tokenoskobi / Coinoskobi Motion State & Truth Engine Contract v1

Phase: `UI_CONTRACT3_MOTION_STATE_AND_TRUTH_ENGINE_NOAPI`  
Timestamp: `20260517_190819`  
Depends on:
- `/root/tokenoskobi_clean_v1/docs/ui_contracts/LATEST_UI_CONTRACT1_VIEWPORT_FIT_AND_SINGLE_SOURCE_POLICY_NOAPI.md`
- `/root/tokenoskobi_clean_v1/docs/ui_contracts/LATEST_UI_CONTRACT2_SCREEN_MAP_AND_DATA_OWNERSHIP_NOAPI.md`

## 1. Ana kural

**Veriye göre konuş, veri yoksa konuşma.**

Motion varsa gerçek source data ve reason olmak zorunda.

Panel, CSS veya JS kendi başına şunları uyduramaz:

- critical
- active
- whale
- morg
- clinical
- news impact
- risk pulse
- buy/sell encouragement

## 2. Motion state schema

Her hareket şu alanlara sahip olmak zorunda:

- motion_uid
- target_scope
- target_id
- state
- intensity
- reason
- source_layer
- source_uid
- freshness_seconds
- expires_at
- visual_policy
- fallback_behavior

## 3. Global motion yasaları

- source_uid yoksa motion yok.
- reason yoksa motion yok.
- Eksik veri silent/waiting state üretir.
- Stale veri söner; flash etmeye devam etmez.
- Fake/demo/mock veri production motion tetikleyemez.
- Motion tek yerde hesaplanır: motion_state_layer.
- Panel motion uydurmaz, sadece okur.
- Her motion expiry taşır.
- Intensity source data’dan deterministik gelir.
- TECH_PASS, TRUTH_PASS değildir.

## 4. State tanımları

### silent
Veri yok veya olay yok.

Allowed:
- static card
- dim badge
- no pulse
- no radar movement

Forbidden:
- glow
- pulse
- sweep
- flash
- alarm

### calm
Taze veri var ama eşik aşımı yok.

Allowed:
- çok hafif breathing background
- stable icon

Forbidden:
- alarm flash
- critical glow

### watch
Düşük/orta dikkat durumu.

Allowed:
- soft pulse
- düşük glow
- slow scan

Forbidden:
- panic alarm
- red critical flash

### active
Taze anlamlı event var.

Allowed:
- medium pulse
- radar ripple
- badge attention

Forbidden:
- critical styling without critical threshold

### critical
Kritik eşik taze kanıtla aşıldı.

Allowed:
- strong pulse
- red/amber glow
- short flash burst
- alert badge

Forbidden:
- expiry olmadan sonsuz flash

### dead
Lifecycle dead / morg state var.

Allowed:
- cold low-frequency breath
- blue/cyan dim glow
- slow fade

Forbidden:
- revival source olmadan green revival motion

### revival
Gerçek revival signal var.

Allowed:
- green/cyan rising pulse
- controlled wake animation

Forbidden:
- old/dead data’dan revival efekti

### stale
Veri var ama tazelik süresi dolmuş.

Allowed:
- fade/dim
- stale badge

Forbidden:
- active pulse
- critical flash

### blocked
Hard block veya safety stop var.

Allowed:
- lock overlay
- no trade motion
- red static warning

Forbidden:
- buy/sell encouragement animation

## 5. Modül motion kontratları

## Whale Radar

Required source data:
- fresh whale event
- amount / flow magnitude
- wallet confidence
- direction
- freshness

Rules:
- Whale event yoksa radar silent.
- Event size ripple radius belirler.
- Wallet confidence opacity belirler.
- Risk score color temperature belirler.
- Freshness decay intensity azaltır.
- Expired event sweep’i kaldırır.

Forbidden:
- Whale event olmadan rotating radar.
- Fake whale icon movement.
- Mock data’dan glow.

## Haber Badge / Wave

Required source data:
- news_event_uid
- importance_score
- source_reliability
- token_connection_score
- freshness

Rules:
- Critical verified news badge pulse üretir.
- Rumor/low reliability critical olamaz.
- Token-linked news token kartına impact marker verebilir.
- General market flow token-specific alarm üretmez.

Forbidden:
- Rumor as fact.
- Unverified source’dan critical pulse.
- token_connection_score olmadan token alarm.

## Token Yaşam - Olay Yeri

Required:
- fresh event
- event type
- first evidence state
- freshness

Rules:
- Fresh event short alarm pulse.
- No event silent/calm.
- Stale event dim.

## Token Yaşam - Adli

Required:
- relationship confidence
- evidence count
- investigation state

Rules:
- Evidence reviewed -> slow scan.
- High confidence bad link -> amber/red glow.
- No evidence -> no scan.

## Token Yaşam - Şüpheliler

Required:
- suspect wallet count
- cluster confidence
- highest risk actor

Rules:
- Fresh suspect activity -> pulse.
- High cluster confidence -> stronger border glow.
- No suspect data -> silent.

## Token Yaşam - Klinik

Required:
- clinical_watch
- recovery chance band
- liquidity/volume trend
- watch intensity

Rules:
- clinical_watch exists -> heartbeat-style low pulse.
- Improving trend -> cyan/green recovery pulse.
- Worsening trend -> amber/red weak pulse.
- No clinical_watch -> no heartbeat.

Forbidden:
- Constant heartbeat for every token.
- Recovery effect without recovery source.

## Token Yaşam - Otopsi

Required:
- autopsy_status
- failure class
- outcome memory

Rules:
- Active autopsy -> slow purple scan.
- Completed autopsy -> static result badge.
- No autopsy_status -> no scan.

## Token Yaşam - Morg

Required:
- morg_status
- dead/archive count
- revival_watch_count
- historic outcome

Rules:
- morg_status exists -> cold blue/cyan slow breath.
- revival_signal exists -> separate revival pulse.
- no morg_status -> no morg breath.

Forbidden:
- revival pulse without revival_signal.
- morg animation from fake archive count.

## Risk Panel

Required:
- hard_block
- risk_score
- confidence
- MEV/slippage/liquidity warnings

Rules:
- hard_block -> static lock, no buy encouragement.
- high risk -> amber/red warning pulse with expiry.
- low risk without event -> calm.

## Main Panel Trade Controls

Required:
- position_state
- sl_status
- tp_status
- entry_plan
- hard_block

Rules:
- hard_block disables buy/sell motion.
- SL danger -> red controlled pulse.
- TP approaching -> green/cyan controlled pulse.
- No active position -> no SL/TP animation.

## 6. Freshness policy

- news active window: 1800s, stale after 7200s
- whale active window: 900s, stale after 1800s
- onchain active window: 600s, stale after 1800s
- risk active window: 900s, stale after 3600s
- lifecycle active window: 3600s, stale after 86400s
- paper_trade active window: 300s, stale after 900s

## 7. TRUTH_PASS requirements

- Every moving visual has source_layer.
- Every moving visual has source_uid.
- Every moving visual has reason.
- Every moving visual has freshness_seconds.
- Every moving visual has expiry.
- No fake/mock source can set production motion.
- Motion intensity can be traced to source data.
- If source data disappears, motion becomes silent/stale.

## 8. PRODUCT_PASS requirements

- Motion feels premium, not toy-like.
- Motion does not distract from decision making.
- Motion matches data severity.
- No constant meaningless animation.
- User visually understands why a module is alive.
- Viewport-fit remains intact.

## 9. Next phase

`UI_CONTRACT4_VIEW_MODEL_SCHEMA_AND_SCREEN_FIT_RULES_NOAPI`
