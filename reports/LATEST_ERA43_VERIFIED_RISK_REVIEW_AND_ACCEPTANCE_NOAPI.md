# ERA43 VERIFIED RISK REVIEW AND ACCEPTANCE NOAPI

- Created UTC: 2026-07-07T16:00:25.704598+00:00
- Source decision: `WARN_ERA43_PREFLIGHT_READONLY_AUDIT_NOAPI`
- High findings: 3
- Medium findings: 2
- Final decision: `WARN_ERA43_RISK_REVIEW_PUBLIC_EXPOSURE_FIX_REQUIRED`
- Next step: `ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI`
- ERA43 real run allowed: `False`

## High Decisions
- `ERA43_GRAPH_STATIC` — `ACCEPTED_RISK_READONLY_ONLY` — Do not use generated execution graph as runtime proof until graph quality is repaired.
- `ERA43_GOVERNANCE_INERT` — `ACCEPTED_RISK_READONLY_ONLY` — Governance is not enforced in active runtime yet, but trade/wallet authority remains locked.
- `ERA43_PUBLIC_EXPOSURE_REVIEW` — `MUST_FIX_BEFORE_REAL_RUN` — Public exposure review must be handled before any ERA43 real run.

## Medium Findings
Medium findings are backlog unless later promoted by evidence.
- `ERA43_SHELL_TRUE` — shell=True remains in active code surface
- `ERA43_WATER_POOLING` — Large artifacts and water pooling confirmed
