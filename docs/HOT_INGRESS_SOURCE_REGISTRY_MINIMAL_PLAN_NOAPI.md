# HOT Ingress Source Registry Minimal Plan NOAPI

- stage: `HOT_INTELLIGENCE_INGRESS_GATEWAY_SOURCE_REGISTRY_MINIMAL_PLAN_NOAPI`
- generated_at_utc: `2026-07-08T14:23:00Z`
- decision: `OK_HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_PLAN_NOAPI_DOCUMENTED`
- next_step: `HOT_INGRESS_SOURCE_REGISTRY_MINIMAL_CONTRACT_DRYRUN_NOAPI`

## Purpose

Define the minimum source registry contract for HOT ingress without connecting to any real source.

## Boundary

Plan only. No source connection. No secret material. No database mutation. No runtime change. No service change. No wallet/signing path. No paper/live trade. AI authority remains zero.

## Allowed Source Types For Plan

- telegram
- discord
- x
- news
- rss
- onchain
- dex
- mempool
- manual_synthetic

## Minimum Registry Fields

- source_uid
- source_type
- source_label_hash
- source_location_hash
- trust_score_initial
- trust_score_current
- trust_policy_ref
- rate_limit_policy_ref
- dedupe_policy_ref
- allowed_routes
- status
- evidence_required_before_alarm
- created_at_utc
- last_review_at_utc
- notes_hash

## Next Step

Run synthetic contract dryrun for the registry rules.
