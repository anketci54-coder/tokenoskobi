# Coinoskobi Preview Cleanup Archive Plan

FINAL_DECISION=PASS_PREVIEW_CLEANUP_ARCHIVE_PLAN_READY_NOAPI
FINAL_OK=True
VALIDATION_ERROR_COUNT=0
VALIDATION_ERRORS=NONE

## Amaç

Sunucudaki eski preview klasörlerini silmeden, önce arşiv adayı olarak listelemek.

## Bu faz ne yaptı?

- Silme yok.
- Taşıma yok.
- Archive yazımı yok.
- Aktif panele yazım yok.
- DB yazımı yok.
- API/fetch yok.
- Nginx/domain/SSL yok.

## Sayılar

KEEP_COUNT=107
ARCHIVE_CANDIDATE_COUNT=32
DELETE_CANDIDATE_COUNT=0

KEEP_SIZE_BYTES=1701178204
ARCHIVE_CANDIDATE_SIZE_BYTES=21844437

## Dosyalar

KEEP_LIST=/root/tokenoskobi_clean_v1/_COINOSKOBI_PREVIEW_CLEANUP_ARCHIVE_PLAN_NOAPI/20260524_153029/keep_preview_targets.txt
ARCHIVE_CANDIDATES=/root/tokenoskobi_clean_v1/_COINOSKOBI_PREVIEW_CLEANUP_ARCHIVE_PLAN_NOAPI/20260524_153029/archive_candidates_no_action.txt
DELETE_CANDIDATES=/root/tokenoskobi_clean_v1/_COINOSKOBI_PREVIEW_CLEANUP_ARCHIVE_PLAN_NOAPI/20260524_153029/delete_candidates_no_action.txt

## Real archive için gerekli onay

COINOSKOBI PREVIEW CLEANUP ARCHIVE REAL için onay veriyorum

## Sonraki adımlar

1. Aday listeyi kontrol et.
2. Kabul edilirse real archive fazı.
3. Sonra staging binding plan.
