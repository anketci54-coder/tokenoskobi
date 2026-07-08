# Gemini Red Team Prompt — NEWS Seal + Cengizhan Doctrine Boundary

Red Team task: evaluate whether Tokenoskobi can seal the current COLD NEWS recovery while explicitly preserving the Cengizhan/HOT intelligence doctrine for the next architecture stage.

## Core Doctrine

`COLD NEWS REFRESH` is not the final war intelligence system. It is the fallback/backfill patrol.

`HOT_INTELLIGENCE_INGRESS_GATEWAY` is the future Cengizhan model:

- Always-on or near-real-time intelligence ingress.
- Telegram / Discord / X / crypto news / onchain watcher.
- Ingress relevance filter.
- Source trust scoring.
- Adversarial tactic classifier.
- Conflict resolution: onchain vs social vs news disagreement.
- Priority router: CRITICAL / WATCH / INFO / DROP.
- Hunter / Prosecutor / Risk / Panel / Telegram alarm integration.

## Current Recovery Evidence

- `producer_resurrected` = `OK`
  - OK_NEWS_B_FIX_2_TIMER_ACTIVATED
  - OK_NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_CLEAN
  - timer_active=active
  - timer_enabled=enabled
- `stdout_209_root_cause_closed` = `OK`
  - NEWS-B root cause: FAIL_NEWS_B_STDOUT_PATH_ROOT_CAUSE_CONFIRMED
  - Fix1: OK_NEWS_B_FIX_1_STDOUT_STDERR_PATH_CLEARED
  - Fix1 post: OK_NEWS_B_FIX_1_POST_APPLY_AUDIT_CLEAN
- `downstream_47_chain_verified` = `OK`
  - raw=269
  - match=47
  - signal=47
  - score=47
  - match_signal_mismatch_total=0
  - signal_score_mismatch_total=0
  - raw_link_missing_total=0
  - full_duplicate_group_total=0
  - canonical_duplicate_group_total=0
- `trade_authority_absent` = `OK`
  - trade_signal_nonzero=0
  - paper_signal_nonzero=0
- `freshness_and_panel_known_issue` = `WARN`
  - WARN_NEWS_D_PANEL_READMODEL_FRESHNESS_REVIEW_REQUIRED
  - raw_count=270
  - match_count=47
  - signal_count=47
  - score_count=47
  - raw_newer_than_downstream=True
  - strong_panel_readmodel_count_matches=0
  - freshness_max_ts=2026-07-06T06:44:10.294353+00:00
  - raw_max_ts=2026-07-08T12:48:10.036095+00:00
- `cold_hot_doctrine_split` = `OK`
  - 20min timer is cold backfill/fallback only.
  - HOT_INTELLIGENCE_INGRESS_GATEWAY is deferred until after NEWS-F seal.
  - CENGIZHAN_INTELLIGENCE_DOCTRINE must be preserved as future architecture doctrine.

## Known Warnings

- `PANEL_READMODEL_COUNT_MATCH_NOT_FOUND`: DB sayılarıyla güçlü JSON/readmodel count eşleşmesi bulunamadı.
- `RAW_NEWER_THAN_DOWNSTREAM`: Raw haberler downstream match/signal/score zamanından daha yeni; downstream freshness/staleness takip edilmeli.
- `FRESHNESS_HEARTBEAT_STALER_THAN_RAW`: freshness heartbeat raw max timestamp'ten daha eski.
- `RAW_NEWER_THAN_DOWNSTREAM_CONFIRMED`: Raw producer yeni haber alıyor; downstream 47/47/47 zinciri yeni raw haberleri henüz işlemiyor.
- `PANEL_READMODEL_STRONG_COUNT_MATCH_ZERO`: DB sayılarıyla güçlü panel/readmodel JSON count eşleşmesi bulunmadı.

## Red Team Questions

1. Are we incorrectly presenting a 20-minute timer as final intelligence? If yes, block seal wording.
2. Are the NEWS-D warnings acceptable as known issues for a cold producer seal?
3. Is any claim stronger than evidence supports?
4. Should NEWS-F wording say `COLD NEWS PRODUCER OPERATIONAL` rather than `NEWS FULLY COMPLETE`?
5. Should HOT Gateway be opened only after NEWS-F, with CENGIZHAN_INTELLIGENCE_DOCTRINE as doctrine input?

## Expected Output

Return one of:

- `OK_SEAL_COLD_NEWS_WITH_WARNINGS_THEN_OPEN_HOT_GATEWAY_PLAN`
- `WARN_FIX_SEAL_WORDING_BEFORE_GITHUB_SEAL`
- `BLOCK_SEAL_DUE_TO_HIDDEN_FAILURE`

No praise. Give direct risk verdict.
