PRAGMA foreign_keys=ON;

CREATE TABLE news_disposition_batches_v2 (
 batch_uid TEXT PRIMARY KEY, policy_version TEXT NOT NULL,
 queue_capacity INTEGER NOT NULL CHECK(queue_capacity>0),
 source_candidate_count INTEGER NOT NULL CHECK(source_candidate_count>=0),
 normalized_candidate_count INTEGER NOT NULL CHECK(normalized_candidate_count>=0),
 deduplicated_candidate_count INTEGER NOT NULL CHECK(deduplicated_candidate_count>=0),
 admitted_count INTEGER NOT NULL CHECK(admitted_count>=0),
 overflow_count INTEGER NOT NULL CHECK(overflow_count>=0),
 duplicate_removed_count INTEGER NOT NULL CHECK(duplicate_removed_count>=0),
 unsafe_filtered_count INTEGER NOT NULL CHECK(unsafe_filtered_count>=0),
 invalid_candidate_count INTEGER NOT NULL CHECK(invalid_candidate_count>=0),
 replaced_count INTEGER NOT NULL CHECK(replaced_count>=0),
 lowest_admitted_priority INTEGER, highest_overflow_priority INTEGER,
 source_snapshot_hash TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('BUILDING','COMMITTED','INCOMPLETE','ARCHIVED')),
 retention_class TEXT NOT NULL DEFAULT 'STANDARD_30D' CHECK(retention_class='STANDARD_30D'),
 retention_expires_at_utc TEXT NOT NULL, archived_at_utc TEXT, archive_location TEXT,
 created_at_utc TEXT NOT NULL, committed_at_utc TEXT, incomplete_reason TEXT,
 CHECK(source_candidate_count=admitted_count+overflow_count+duplicate_removed_count+unsafe_filtered_count+invalid_candidate_count+replaced_count),
 CHECK(normalized_candidate_count=deduplicated_candidate_count+duplicate_removed_count),
 CHECK(deduplicated_candidate_count=admitted_count+overflow_count+replaced_count),
 CHECK((status='ARCHIVED' AND archived_at_utc IS NOT NULL AND archive_location IS NOT NULL) OR status<>'ARCHIVED'));

CREATE TABLE news_disposition_ledger_v2 (
 disposition_uid TEXT PRIMARY KEY, batch_uid TEXT NOT NULL,
 source_index INTEGER NOT NULL CHECK(source_index>=0), source_candidate_uid TEXT NOT NULL,
 hot_uid TEXT, event_uid TEXT, news_uid TEXT, lane TEXT, priority_score INTEGER,
 candidate_rank INTEGER CHECK(candidate_rank IS NULL OR candidate_rank>0),
 disposition TEXT NOT NULL CHECK(disposition IN ('ADMITTED','DUPLICATE_REMOVED','UNSAFE_AUTHORITY_FILTERED','OVERFLOW_TRUNCATED','REPLACED_BY_HIGHER_PRIORITY','INVALID_CANDIDATE')),
 reason_code TEXT NOT NULL CHECK(reason_code IN ('TOP_50_ADMITTED','DUPLICATE_HOT_UID','UNSAFE_AUTHORITY','QUEUE_OVERFLOW','HIGHER_PRIORITY_REPLACEMENT','INVALID_INPUT')),
 lowest_admitted_priority INTEGER, highest_overflow_priority INTEGER,
 source_snapshot_hash TEXT NOT NULL, recorded_at_utc TEXT NOT NULL,
 payload_json TEXT NOT NULL CHECK(length(CAST(payload_json AS BLOB))<=16384),
 FOREIGN KEY(batch_uid) REFERENCES news_disposition_batches_v2(batch_uid) ON DELETE RESTRICT,
 UNIQUE(batch_uid,source_index));

CREATE INDEX idx_news_disposition_ledger_batch_v2 ON news_disposition_ledger_v2(batch_uid,candidate_rank);

CREATE INDEX idx_news_disposition_ledger_hot_uid_v2 ON news_disposition_ledger_v2(hot_uid);

CREATE INDEX idx_news_disposition_ledger_disposition_v2 ON news_disposition_ledger_v2(disposition,reason_code);

CREATE TRIGGER trg_news_disposition_ledger_archive_before_delete_v2 BEFORE DELETE ON news_disposition_ledger_v2 BEGIN
 SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM news_disposition_batches_v2 WHERE batch_uid=OLD.batch_uid AND status='ARCHIVED' AND archived_at_utc IS NOT NULL AND archive_location IS NOT NULL AND datetime(retention_expires_at_utc)<=CURRENT_TIMESTAMP)
 THEN RAISE(ABORT,'LEDGER_DELETE_REQUIRES_EXPIRED_ARCHIVED_BATCH') END; END;

CREATE TRIGGER trg_news_disposition_batch_archive_before_delete_v2 BEFORE DELETE ON news_disposition_batches_v2 BEGIN
 SELECT CASE WHEN OLD.status<>'ARCHIVED' OR OLD.archived_at_utc IS NULL OR OLD.archive_location IS NULL OR datetime(OLD.retention_expires_at_utc)>CURRENT_TIMESTAMP
 THEN RAISE(ABORT,'BATCH_DELETE_REQUIRES_EXPIRED_ARCHIVED_BATCH') END; END;
