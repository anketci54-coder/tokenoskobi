# ERA53 HOT Ingress Event Normalization Contract Minimal Plan Review Seal NOAPI

- stage: `ERA53_HOT_INGRESS_EVENT_NORMALIZATION_CONTRACT_MINIMAL_PLAN_REVIEW_SEAL_NOAPI`
- generated_at_utc: `2026-07-08T15:24:00Z`
- decision: `OK_ERA53_HOT_INGRESS_EVENT_NORMALIZATION_CONTRACT_MINIMAL_PLAN_REVIEW_SEALED`
- next_step: `ERA53_HOT_INGRESS_TOPIC_DEDUPLICATION_POLICY_MINIMAL_PLAN_NOAPI`

## Purpose

Define the minimal normalized HOT ingress event contract after admission and before deduplication, evidence binding, or runtime use.

## Normalized Event Contract

Required fields include normalized event UID, source identity, observed time, payload hash, topic hash, normalized topic key, event type, admission route, trust score, policy refs, and normalization version.

Optional context fields include canonical chain, chain ID, normalized asset address, raw symbol, entity label, wallet address, DEX protocol, transaction hash, block number, URL hash, language hint, and source confidence.

## Core Rules

- chain names map to canonical chain when present
- hex addresses normalize lowercase
- payload hash and topic hash do not change
- normalized topic key must be deterministic
- unknown type maps to unknown anomaly
- raw payload is not stored in this contract
- credential-like fields remain blocked
- normalization cannot increase admission route

## Hard Blocks

- no Evidence binding created
- no DB record created
- no runtime queue created
- no outbound alarm created
- no trade or wallet action created

## Workflow Rule

Plan-only docs/contract used `PLAN -> REVIEW_SEAL`. Dryrun skipped because no runtime code, DB schema, service, source adapter, or executable logic changed.

## Tree Rule

Existing tree preserved. No directory restructure, move, rename, archive, or new top-level directory.

## Boundary

No API. No source connection. No secret material. No credential use. No DB write. No schema write. No runtime change. No systemd change. No wallet/signing. No paper/live trade. AI authority 0.
