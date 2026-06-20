# Mobile Pageflow Icon Truth Fix Apply Plan

FINAL_DECISION=PASS_MOBILE_PAGEFLOW_ICON_TRUTH_FIX_APPLY_PLAN_READY_NOAPI
FINAL_OK=True

## Amaç

Aktif `/mobile_pageflow/` route içinde, preview'de kabul edilen ikon doğruluk fix'ini kullanmak.

## Yazılacak yerler

- Sadece aktif mobile route:
  - `/root/tokenoskobi_clean_v1/active_panel_8096/current/mobile_pageflow/index.html`
  - `/root/tokenoskobi_clean_v1/active_panel_8096/current/mobile_pageflow/data/`

## Yazılmayacak yerler

- Root desktop index korunacak.
- Aktif production data korunacak.
- Risk data korunacak.
- DB korunacak.
- Nginx/service/timer değişmeyecek.
- API/fetch yok.

## Kaynak

`/root/tokenoskobi_clean_v1/panel_previews/mobile_pageflow_icon_truth_fix_preview_8143_20260524_110453`

## Kritik ikon kuralları

- Rug / Honeypot: yanlış ikon gösterme, gerekirse R/H badge.
- Kilit Kontrol: yanlış ikon gösterme, gerekirse KK badge.
- TX Akış: yanlış ikon gösterme, gerekirse TX badge.
- Kontrat Risk: yanlış ikon gösterme, gerekirse KR badge.
- Slippage: yanlış ikon gösterme, gerekirse SL badge.
- Aynı ikon farklı kartlarda tekrar kullanılırsa badge'e düşür.

## Çöp kontrolü

Silme yok. Sadece aday listesi üretildi:

`/root/tokenoskobi_clean_v1/_COINOSKOBI_ACTIVE_8096_MOBILE_PAGEFLOW_ICON_TRUTH_FIX_APPLY_PLAN_NOAPI/20260524_142947/preview_cleanup_candidates_list_no_delete.txt`

CLEANUP_CANDIDATE_COUNT=29

## Real apply için gerekli onay

`COINOSKOBI ACTIVE 8096 MOBILE PAGEFLOW ICON TRUTH FIX APPLY REAL için onay veriyorum`
