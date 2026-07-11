# ERA55A_7 P0 DROP LEDGER DESIGN AND TEMP-COPY TEST

Result: `PASS_P0_LEDGER_DESIGN_TEMP_COPY_VALIDATED_NO_PRODUCTION_MUTATION`

Test mode: `DISPOSABLE_TEMP_COPY`

Production mutation: `false`

## Schema

- Batch table: `news_disposition_batches_v1`
- Ledger table: `news_disposition_ledger_v1`
- Atomicity: `SINGLE_TRANSACTION_FAIL_CLOSED`
- Schema artifact: `data/control/era55a7_p0_disposition_ledger_schema_v1.sql`

## Overflow Simulation

- Source candidates: `70`
- Normalized candidates: `65`
- Deduplicated candidates: `60`
- Admitted: `50`
- Overflow: `10`
- Duplicate removed: `5`
- Unsafe filtered: `3`
- Invalid candidates: `2`

```json
{
  "ADMITTED": 50,
  "DUPLICATE_REMOVED": 5,
  "INVALID_CANDIDATE": 2,
  "OVERFLOW_TRUNCATED": 10,
  "UNSAFE_AUTHORITY_FILTERED": 3
}
```

Every overflow event was written with `reason_code=QUEUE_OVERFLOW`.

## Hard Gates

```json
{
  "event_count_loss": 0,
  "uid_loss": 0,
  "duplicate_regression": 0,
  "unledgered_disposition": 0,
  "overflow_wrong_reason_count": 0,
  "integrity_check": "ok",
  "quick_check": "ok",
  "atomic_rollback_pass": true,
  "constraint_tests_pass": true,
  "production_unchanged": true
}
```

## Atomicity and Constraints

```json
{
  "atomic_rollback": {
    "batch_rows_after_rollback": 0,
    "ledger_rows_after_rollback": 0,
    "pass": true
  },
  "constraint_tests": {
    "duplicate_disposition_uid_rejected": true,
    "missing_batch_foreign_key_rejected": true,
    "pass": true
  }
}
```

## Production Guard

Production DB, runtime-state files and systemd unit hashes were identical before and after the test.

## Decision

- Ledger schema design: `VALIDATED_ON_TEMP_COPY`
- Overflow accounting: `VALIDATED_ON_TEMP_COPY`
- Production implementation: `NOT_AUTHORIZED`
- F1 P0: `OPEN_PENDING_POST_TEST_AUDIT_AND_APPLY_DECISION`
- Optimization apply: `false`
- Next: `ERA55A_8_P0_DROP_LEDGER_POST_TEST_AUDIT_AND_APPLY_DECISION`
