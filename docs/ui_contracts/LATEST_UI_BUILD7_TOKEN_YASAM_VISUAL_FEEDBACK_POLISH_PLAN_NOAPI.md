# UI_BUILD7_TOKEN_YASAM_VISUAL_FEEDBACK_POLISH_PLAN_NOAPI

Timestamp: `20260517_204546`

## Final

- FINAL_STATUS=PASS
- FINAL_GATE=UI_BUILD7_TOKEN_YASAM_VISUAL_FEEDBACK_POLISH_PLAN_READY
- DB_UNCHANGED=True

## Scope

Plan only.

No preview generated.  
No panel mutation.  
No DB/API/fetch/paper/live.  
No image generation.  
No yama.  
No product-specific hack.

## Source preview

`http://159.195.74.132:8104/?v=tokenyasam_living_preview_20260517_201554#token-yasam`

Preview dir:

`/root/tokenoskobi_clean_v1/panel_previews/tokenyasam_living_preview_20260517_201554`

## User visual feedback

### Accepted

- Sol logo konumu tamam.
- 6 departman genel düzeni korunabilir.
- Morg geri geldi.
- Fake motion yok.

### Must fix

1. Logo ortasından geçen nabız şekli kırmızı değil.
2. Sol menüde Ana Panel ile başlayan liste altta kaldı.
3. Olay Yeri İnceleme, Adli Soruşturma ve Şüpheliler ikonları net değil.
4. Scroll ile hafif alta geçme eğilimi var.

## Product gate

PRODUCT_PASS remains false.

Reason:

User visual feedback requires polish before acceptance.

## Build8 preview plan

Next preview must:

- preserve accepted logo position
- make heartbeat/pulse line red/canlı
- move left nav upward
- sharpen Olay/Adli/Şüpheliler icons from existing assets
- tighten vertical spacing to avoid scroll tendency
- keep 6 cards summary-only
- keep detail_ref behavior
- keep no source_uid = no motion
- use 8104 preview only
- not touch 8096 / 8101 / 8102

## Required next approval sentence

`UI_BUILD8_TOKEN_YASAM_VISUAL_POLISH_PREVIEW_AFTER_APPROVAL için onay veriyorum`

## Next phase

`UI_BUILD8_TOKEN_YASAM_VISUAL_POLISH_PREVIEW_AFTER_APPROVAL`
