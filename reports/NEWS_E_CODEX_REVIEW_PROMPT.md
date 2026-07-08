# Codex Review Prompt — NEWS Operational Seal Prep

You are reviewing the Tokenoskobi NEWS recovery sequence. Do not propose a rewrite. Verify whether the current artifacts support an operational seal with known warnings.

## Scope

- Repository path: `/root/tokenoskobi_clean_v1`
- Current stage: `NEWS_E_REVIEW_PROMPT_AND_SEAL_PREP_NOAPI`
- Next intended stage: `NEWS_F_FINAL_OPERATIONAL_SEAL_WITH_KNOWN_WARNINGS`
- Do not recommend live trading, paper trading, wallet/signing, or API expansion.
- Do not convert the 20-minute timer into the final intelligence architecture.

## Artifact Chain

- `news_a`: `WARN_NEWS_A_CURRENT_TRUTH_CAPTURED_REVIEW_REQUIRED` — `/root/tokenoskobi_clean_v1/data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json`
- `news_b`: `FAIL_NEWS_B_STDOUT_PATH_ROOT_CAUSE_CONFIRMED` — `/root/tokenoskobi_clean_v1/data/control/news_b_runner_timer_journal_argv_audit_noapi_v1.json`
- `news_b_fix1`: `OK_NEWS_B_FIX_1_STDOUT_STDERR_PATH_CLEARED` — `/root/tokenoskobi_clean_v1/data/control/news_b_fix_1_systemd_stdout_stderr_path_targeted_apply_v1.json`
- `news_b_fix1_post`: `OK_NEWS_B_FIX_1_POST_APPLY_AUDIT_CLEAN` — `/root/tokenoskobi_clean_v1/data/control/news_b_fix_1_post_apply_audit_noapi_v1.json`
- `news_b_fix2`: `OK_NEWS_B_FIX_2_TIMER_ACTIVATED` — `/root/tokenoskobi_clean_v1/data/control/news_b_fix_2_timer_activation_targeted_apply_v1.json`
- `news_b_fix2_post`: `OK_NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_CLEAN` — `/root/tokenoskobi_clean_v1/data/control/news_b_fix_2_post_activation_audit_noapi_v1.json`
- `news_c`: `OK_NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_CLEAN` — `/root/tokenoskobi_clean_v1/data/control/news_c_downstream_checksum_fingerprint_noapi_v1.json`
- `news_d`: `WARN_NEWS_D_PANEL_READMODEL_FRESHNESS_REVIEW_REQUIRED` — `/root/tokenoskobi_clean_v1/data/control/news_d_panel_readmodel_freshness_noapi_v1.json`

## Seal Matrix

- `producer_resurrected`: `OK`
  - OK_NEWS_B_FIX_2_TIMER_ACTIVATED
  - OK_NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_CLEAN
  - timer_active=active
  - timer_enabled=enabled
- `stdout_209_root_cause_closed`: `OK`
  - NEWS-B root cause: FAIL_NEWS_B_STDOUT_PATH_ROOT_CAUSE_CONFIRMED
  - Fix1: OK_NEWS_B_FIX_1_STDOUT_STDERR_PATH_CLEARED
  - Fix1 post: OK_NEWS_B_FIX_1_POST_APPLY_AUDIT_CLEAN
- `downstream_47_chain_verified`: `OK`
  - raw=269
  - match=47
  - signal=47
  - score=47
  - match_signal_mismatch_total=0
  - signal_score_mismatch_total=0
  - raw_link_missing_total=0
  - full_duplicate_group_total=0
  - canonical_duplicate_group_total=0
- `trade_authority_absent`: `OK`
  - trade_signal_nonzero=0
  - paper_signal_nonzero=0
- `freshness_and_panel_known_issue`: `WARN`
  - WARN_NEWS_D_PANEL_READMODEL_FRESHNESS_REVIEW_REQUIRED
  - raw_count=270
  - match_count=47
  - signal_count=47
  - score_count=47
  - raw_newer_than_downstream=True
  - strong_panel_readmodel_count_matches=0
  - freshness_max_ts=2026-07-06T06:44:10.294353+00:00
  - raw_max_ts=2026-07-08T12:48:10.036095+00:00
- `cold_hot_doctrine_split`: `OK`
  - 20min timer is cold backfill/fallback only.
  - HOT_INTELLIGENCE_INGRESS_GATEWAY is deferred until after NEWS-F seal.
  - CENGIZHAN_INTELLIGENCE_DOCTRINE must be preserved as future architecture doctrine.

## Known Warnings

- `PANEL_READMODEL_COUNT_MATCH_NOT_FOUND`: DB sayılarıyla güçlü JSON/readmodel count eşleşmesi bulunamadı.
- `RAW_NEWER_THAN_DOWNSTREAM`: Raw haberler downstream match/signal/score zamanından daha yeni; downstream freshness/staleness takip edilmeli.
- `FRESHNESS_HEARTBEAT_STALER_THAN_RAW`: freshness heartbeat raw max timestamp'ten daha eski.
- `RAW_NEWER_THAN_DOWNSTREAM_CONFIRMED`: Raw producer yeni haber alıyor; downstream 47/47/47 zinciri yeni raw haberleri henüz işlemiyor.
- `PANEL_READMODEL_STRONG_COUNT_MATCH_ZERO`: DB sayılarıyla güçlü panel/readmodel JSON count eşleşmesi bulunmadı.

## Review Questions

1. Is the 209/STDOUT root cause adequately identified and closed?
2. Is the timer active/enabled evidence sufficient for COLD NEWS producer operational status?
3. Is the 47/47/47 downstream chain verified without broken references or duplicate rows?
4. Are the NEWS-D warnings correctly classified as known issues rather than hidden failures?
5. Is it safe to create NEWS-F as an operational seal with known warnings, without claiming panel/freshness fully clean?
6. Confirm that HOT_INTELLIGENCE_INGRESS_GATEWAY should remain a post-NEWS-F architecture plan, not part of this seal.

## Expected Output

Return one of:

- `OK_FOR_NEWS_F_SEAL_WITH_KNOWN_WARNINGS`
- `WARN_REVIEW_BEFORE_NEWS_F`
- `BLOCK_NEWS_F_SEAL`

Include concrete artifact references and exact reasons.
