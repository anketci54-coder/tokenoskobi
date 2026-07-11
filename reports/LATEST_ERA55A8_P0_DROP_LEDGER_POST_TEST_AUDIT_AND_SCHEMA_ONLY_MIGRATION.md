# ERA55A_8 P0 DROP LEDGER POST-TEST AUDIT AND SCHEMA-ONLY MIGRATION

Result: `OK_REPAIRED_SCHEMA_COMPLETE_TEMP_COPY_AND_PRODUCTION_DDL_ONLY`

Complete disposition test:

```json
{
  "source_candidate_count": 71,
  "normalized_candidate_count": 66,
  "deduplicated_candidate_count": 61,
  "replaced_count": 1,
  "accounted_count": 71,
  "ledger_count": 71,
  "disposition_counts": {
    "ADMITTED": 50,
    "DUPLICATE_REMOVED": 5,
    "INVALID_CANDIDATE": 2,
    "OVERFLOW_TRUNCATED": 10,
    "REPLACED_BY_HIGHER_PRIORITY": 1,
    "UNSAFE_AUTHORITY_FILTERED": 3
  },
  "event_count_loss": 0,
  "uid_loss": 0,
  "duplicate_regression": 0,
  "unledgered_disposition": 0,
  "payload_limit_rejected": true,
  "atomic_rollback_rows": 0,
  "unarchived_delete_rejected": true,
  "archived_delete_allowed": true,
  "integrity_check": "ok",
  "quick_check": "ok",
  "foreign_key_check_rows": 0,
  "source_tables_unchanged": true,
  "ok": true
}
```

Production migration:

```json
{
  "mode": "PRODUCTION_DDL_ONLY_EMPTY_TABLES",
  "backup": {
    "backup_db": "/root/tokenoskobi_backups/era55a8_20260711T102356Z/tokenoskobi_clean_v1.sqlite",
    "sha256": "cf5dbdfdb478a3d34843c22df75e49264a317de42c3bb7af686415dfd0a85e1b",
    "integrity_check": "ok",
    "quick_check": "ok"
  },
  "foreign_keys_migration_connection": 1,
  "foreign_keys_fresh_after_enable": 1,
  "journal_mode_before": "delete",
  "journal_mode_after": "delete",
  "synchronous_before": 2,
  "synchronous_after": 2,
  "integrity_check": "ok",
  "quick_check": "ok",
  "foreign_key_check_rows": 0,
  "batch_rows": 0,
  "ledger_rows": 0,
  "gateway_hash_before": "8d4c1cb568ab194dfb010d66859c45aa29fa044aff1518a656a9f78ecc4fb263",
  "gateway_hash_after": "8d4c1cb568ab194dfb010d66859c45aa29fa044aff1518a656a9f78ecc4fb263",
  "gateway_writer_active": false,
  "runtime_and_gateway_unchanged": true,
  "production_data_rows_mutated": false,
  "ok": true
}
```

Production writer remains inactive. P0 F1 remains open. Next: `ERA55A_9_P0_LEDGER_WRITER_INTEGRATION_TEMP_COPY_TEST`.
