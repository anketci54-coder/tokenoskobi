# ERA60 Schema Hardening Backlog Plan NOAPI V1

Generated UTC: 2026-07-10T07:49:20.379322+00:00

Decision: OK_ERA60_SCHEMA_HARDENING_BACKLOG_PLAN_NOAPI

## Purpose

ERA60 is a backlog plan only in this step. No DB schema change, no DB write, no service/timer change.

## Backlog

1. Event hash backlog
2. Quarantine backlog
3. Conflict resolution backlog
4. Historical blind replay gate

## Blind replay rule

```text
1) Input-only historical data fetch
2) Input manifest SHA seal
3) Prediction run without outcome/results
4) Outcome/result fetch after prediction seal
5) Score comparison last
Policy verifier

NEWS runtime policy verifier remains active and must pass before blind replay.

Next

HISTORICAL_BLIND_REPLAY_PLAN_NOAPI
