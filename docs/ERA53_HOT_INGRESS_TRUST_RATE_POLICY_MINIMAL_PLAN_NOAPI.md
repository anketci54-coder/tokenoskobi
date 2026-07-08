# ERA53 HOT Ingress Trust Rate Policy Minimal Plan NOAPI

- stage: `ERA53_HOT_INGRESS_TRUST_RATE_POLICY_MINIMAL_PLAN_NOAPI`
- generated_at_utc: `2026-07-08T14:52:00Z`
- decision: `OK_ERA53_HOT_INGRESS_TRUST_RATE_POLICY_MINIMAL_PLAN_NOAPI_DOCUMENTED`
- next_step: `ERA53_HOT_INGRESS_TRUST_RATE_POLICY_MINIMAL_DRYRUN_NOAPI`

## Purpose

Define the minimum trust score and rate limit policy for HOT ingress source registry entries before any real source adapter exists.

## Trust Score Policy

- score range: `0-100`
- social sources start low
- news/RSS starts medium
- onchain/DEX/mempool starts high
- manual synthetic test source is system-only

## Rate Policy

- per-source event cap required
- duplicate wave rule required
- burst quarantine rule required
- outbound alarm remains blocked
- critical alarm requires Evidence and Prosecutor confirmation later

## Tree Rule

Existing tree preserved. No directory restructure, move, rename, archive, or new top-level directory.

## Boundary

No API. No source connection. No secret material. No credential use. No DB write. No schema write. No runtime change. No systemd change. No wallet/signing. No paper/live trade. AI authority 0.
