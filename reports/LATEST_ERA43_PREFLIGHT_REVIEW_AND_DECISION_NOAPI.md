# ERA43 PREFLIGHT REVIEW AND DECISION NOAPI

- Created UTC: 2026-07-07T15:39:56.121997+00:00
- Source audit: `/root/tokenoskobi_clean_v1/data/control/era43_preflight_readonly_audit_noapi_v1.json`
- Source decision: `WARN_ERA43_PREFLIGHT_READONLY_AUDIT_NOAPI`
- Review decision: `WARN_ERA43_PREFLIGHT_REVIEW_AND_DECISION_NOAPI`
- Critical: 0
- High: 3
- Medium: 2
- ERA43 real run allowed: `False`
- Next step: `ERA43_VERIFIED_RISK_REVIEW_AND_ACCEPTANCE_PLAN_NOAPI`

## Rule

ERA43 real run cannot proceed while Critical/High findings remain unreviewed or not explicitly risk-accepted.

## High Findings

- `ERA43_GRAPH_STATIC` — ACTIVE_EXECUTION_GRAPH appears static/incomplete — `FIX_NOW_VERIFY`
- `ERA43_GOVERNANCE_INERT` — Governance files exist but active enforcement imports were not found — `FIX_NOW_VERIFY_OR_RISK_ACCEPT`
- `ERA43_PUBLIC_EXPOSURE_REVIEW` — public/ contains internal/action/staging/wallet/debug keyword hits or symlinks — `FIX_NOW_VERIFY`
