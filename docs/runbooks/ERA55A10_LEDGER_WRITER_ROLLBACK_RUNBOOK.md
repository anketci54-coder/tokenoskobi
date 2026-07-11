
# ERA55A10 Ledger Writer Rollback Runbook

## Scope

This runbook covers only the ERA55 P0 disposition-ledger writer and recovery shields. It does not authorize trade, wallet, signing, external API, schema expansion, Option B, service activation, or timer mutation.

## Feature Flags

The remediation code is inert unless explicitly enabled by the service environment:

```text
TOKENOSKOBI_LEDGER_WRITER_ENABLED=1
TOKENOSKOBI_RUNNER_LOCK_ENABLED=1
TOKENOSKOBI_LEDGER_RECOVERY_MAX_ATTEMPTS=3
```

Removing or setting the first two flags to `0` disables the writer/recovery path and the new runner lock without deleting ledger tables.

## Tier 1 — Logical Rollback

Use this first unless the database itself is unreadable.

1. Disable the ledger writer and recovery shields in the systemd environment/drop-in.
2. Run `systemctl daemon-reload`.
3. Restart only `tokenoskobi-news-radar-refresh.service` if an active process must be replaced.
4. Confirm raw ingestion, derived refresh and the pre-A9 hot gateway path still execute.
5. Do not drop or delete `news_disposition_batches_v2` or `news_disposition_ledger_v2`.
6. Mark affected batch UIDs as quarantined in the recovery-state evidence and preserve the output/state files for audit.
7. Restore the pre-activation code HEAD only if disabling the flags is insufficient.
8. Verify database integrity, source-table row counts, timer status and gateway JSON contract.

Tier 1 preserves raw, match, signal and score data.

## Tier 2 — Physical Restore With Delta Recovery

Use only when the live SQLite database is unreadable or integrity checks fail.

1. Stop the news timer and service.
2. Copy the damaged database, WAL/SHM files if present, runtime state and journal evidence to a quarantine directory.
3. Record SHA-256, size and timestamp for every quarantined file.
4. Restore the verified pre-activation database backup.
5. Extract post-backup raw/derived deltas from the quarantined database in read-only mode.
6. Deduplicate delta rows by their canonical primary/unique identifiers before insertion.
7. Replay deltas into a disposable copy first.
8. Prove row-count parity, UID uniqueness, foreign-key integrity and zero duplicate notification risk.
9. Apply the validated delta only after explicit authorization.
10. Re-enable the timer only after natural-cycle verification.

A blind full-database restore without delta recovery is prohibited.

## Duplicate/Notification Guard

Delta replay must not emit historical notifications blindly. Gateway output and ledger batches must be reconciled by canonical UID and batch sequence. Existing downstream output with a newer batch sequence must never be overwritten by an older recovery batch.

## Poison-Batch Handling

Three consecutive recovery failures quarantine the batch. While quarantined:

- raw and derived processing may continue;
- hot publication is blocked;
- a loud recovery/quarantine alert is mandatory;
- operator review is required before retry-counter reset.

## Evidence Required Before Production Activation

- fresh-process recovery pass;
- natural runner recovery-before-raw pass;
- file fsync → atomic replace → parent-directory fsync pass;
- monotonic batch-sequence overwrite protection pass;
- strict single-instance lock pass;
- poison-pill quarantine pass;
- recovery alert pass;
- backward-compatible JSON contract pass;
- production DB and runtime-state guard unchanged during A10 test;
- explicit Red Team production authorization.

## Current Authorization

```text
PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```
