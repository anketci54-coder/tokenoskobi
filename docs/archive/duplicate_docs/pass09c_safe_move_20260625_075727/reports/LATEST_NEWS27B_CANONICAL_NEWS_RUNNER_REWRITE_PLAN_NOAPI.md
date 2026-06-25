# NEWS27B CANONICAL NEWS RUNNER REWRITE PLAN NOAPI

- created_at_utc: `2026-05-10T18:59:08.164818+00:00`
- final_status: **PASS**
- runner_compile_ok: `True`
- data_mapping_ok: `True`
- html_marker_still_missing: `True`
- literal_marker_bug_confirmed: `True`
- news_count: `33`
- lane_counts: `{'risk_top': 3, 'risk_watch': 8, 'general_info': 22}`
- display_counts: `{'Kritik Risk': 3, 'Risk İzle': 8, 'Bilgi': 22}`
- db_unchanged: `True`
- runner_unchanged: `True`
- preview_unchanged: `True`
- paper_live_zero: `True`
- next_phase: `NEWS27C_CANONICAL_NEWS_RUNNER_REWRITE_DRYRUN_NOAPI`
- real_rewrite_approval_sentence: `NEWS27E canonical news runner rewrite real için onay veriyorum`

## Decision
- Küçük regex/marker yama zinciri durduruldu.
- Sonraki canlı değişiklik ancak tek parça canonical runner rewrite olarak yapılacak.
- Önce temp dry-run zorunlu.

## Plan Steps
- 1 `FREEZE_PATCH_CHAIN` write_now=`False`
- 2 `READ_CURRENT_WRAPPER_AND_ORIGINAL` write_now=`False`
- 3 `DESIGN_CANONICAL_RUNNER` write_now=`False`
- 4 `TEMP_CANONICAL_RUNNER_DRYRUN` write_now=`False`
- 5 `VALIDATE_TEMP_OUTPUT` write_now=`False`
- 6 `REAL_REWRITE_REQUIRES_EXPLICIT_APPROVAL` write_now=`False`
- 7 `POST_REAL_AUDIT` write_now=`False`
- 8 `PHASE_OUTPUT_CLEANUP_PLAN_LATER` write_now=`False`

## Errors
- none

## Warnings
- none
