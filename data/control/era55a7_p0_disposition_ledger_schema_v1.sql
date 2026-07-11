PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS news_disposition_batches_v1 (
    batch_uid TEXT PRIMARY KEY,
    policy_version TEXT NOT NULL,
    queue_capacity INTEGER NOT NULL CHECK(queue_capacity > 0),
    source_candidate_count INTEGER NOT NULL CHECK(source_candidate_count >= 0),
    normalized_candidate_count INTEGER NOT NULL CHECK(normalized_candidate_count >= 0),
    deduplicated_candidate_count INTEGER NOT NULL CHECK(deduplicated_candidate_count >= 0),
    admitted_count INTEGER NOT NULL CHECK(admitted_count >= 0),
    overflow_count INTEGER NOT NULL CHECK(overflow_count >= 0),
    duplicate_removed_count INTEGER NOT NULL CHECK(duplicate_removed_count >= 0),
    unsafe_filtered_count INTEGER NOT NULL CHECK(unsafe_filtered_count >= 0),
    invalid_candidate_count INTEGER NOT NULL CHECK(invalid_candidate_count >= 0),
    lowest_admitted_priority INTEGER,
    highest_overflow_priority INTEGER,
    source_snapshot_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('BUILDING','COMMITTED','INCOMPLETE')),
    created_at_utc TEXT NOT NULL,
    committed_at_utc TEXT,
    incomplete_reason TEXT,
    CHECK(
        source_candidate_count = admitted_count + overflow_count
        + duplicate_removed_count + unsafe_filtered_count + invalid_candidate_count
    ),
    CHECK(deduplicated_candidate_count = admitted_count + overflow_count)
);

CREATE TABLE IF NOT EXISTS news_disposition_ledger_v1 (
    disposition_uid TEXT PRIMARY KEY,
    batch_uid TEXT NOT NULL,
    source_index INTEGER NOT NULL CHECK(source_index >= 0),
    source_candidate_uid TEXT NOT NULL,
    hot_uid TEXT,
    event_uid TEXT,
    news_uid TEXT,
    lane TEXT,
    priority_score INTEGER,
    candidate_rank INTEGER CHECK(candidate_rank IS NULL OR candidate_rank > 0),
    disposition TEXT NOT NULL CHECK(disposition IN (
        'ADMITTED',
        'DUPLICATE_REMOVED',
        'UNSAFE_AUTHORITY_FILTERED',
        'OVERFLOW_TRUNCATED',
        'REPLACED_BY_HIGHER_PRIORITY',
        'INVALID_CANDIDATE'
    )),
    reason_code TEXT NOT NULL CHECK(reason_code IN (
        'TOP_50_ADMITTED',
        'DUPLICATE_HOT_UID',
        'UNSAFE_AUTHORITY',
        'QUEUE_OVERFLOW',
        'HIGHER_PRIORITY_REPLACEMENT',
        'INVALID_INPUT'
    )),
    lowest_admitted_priority INTEGER,
    highest_overflow_priority INTEGER,
    source_snapshot_hash TEXT NOT NULL,
    recorded_at_utc TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(batch_uid) REFERENCES news_disposition_batches_v1(batch_uid) ON DELETE RESTRICT,
    UNIQUE(batch_uid, source_index)
);

CREATE INDEX IF NOT EXISTS idx_news_disposition_ledger_batch_v1
ON news_disposition_ledger_v1(batch_uid, candidate_rank);

CREATE INDEX IF NOT EXISTS idx_news_disposition_ledger_hot_uid_v1
ON news_disposition_ledger_v1(hot_uid);

CREATE INDEX IF NOT EXISTS idx_news_disposition_ledger_disposition_v1
ON news_disposition_ledger_v1(disposition, reason_code);
