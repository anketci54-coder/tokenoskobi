
PRAGMA foreign_keys = ON;

CREATE TABLE state_reader_events (
    event_id TEXT PRIMARY KEY,
    created_utc TEXT NOT NULL,
    source_state_dir TEXT NOT NULL,
    last_successful_phase TEXT NOT NULL,
    next_target_phase TEXT NOT NULL,
    phase31_closed INTEGER NOT NULL CHECK (phase31_closed IN (0,1)),
    data_provenance_locked INTEGER NOT NULL CHECK (data_provenance_locked IN (0,1)),
    fast_path_not_touched INTEGER NOT NULL CHECK (fast_path_not_touched IN (0,1)),
    ai_not_touched INTEGER NOT NULL CHECK (ai_not_touched IN (0,1)),
    secret_scan_clean INTEGER NOT NULL CHECK (secret_scan_clean IN (0,1)),
    sha_validation_ok INTEGER NOT NULL CHECK (sha_validation_ok IN (0,1))
);

CREATE TABLE maintenance_bundle_events (
    bundle_id TEXT PRIMARY KEY,
    created_utc TEXT NOT NULL,
    source_state_event_id TEXT NOT NULL,
    redaction_required INTEGER NOT NULL CHECK (redaction_required IN (0,1)),
    secret_scan_required INTEGER NOT NULL CHECK (secret_scan_required IN (0,1)),
    secret_scan_clean INTEGER NOT NULL CHECK (secret_scan_clean IN (0,1)),
    fast_path_isolated INTEGER NOT NULL CHECK (fast_path_isolated IN (0,1)),
    bundle_for_ai INTEGER NOT NULL CHECK (bundle_for_ai IN (0,1)),
    FOREIGN KEY(source_state_event_id) REFERENCES state_reader_events(event_id)
);

CREATE TABLE ai_proposal_events (
    proposal_id TEXT PRIMARY KEY,
    created_utc TEXT NOT NULL,
    source_bundle_id TEXT NOT NULL,
    proposal_type TEXT NOT NULL,
    target_phase TEXT NOT NULL,
    summary TEXT NOT NULL,
    forbidden_flags_json TEXT NOT NULL,
    approval_required INTEGER NOT NULL CHECK (approval_required IN (0,1)),
    rollback_required INTEGER NOT NULL CHECK (rollback_required IN (0,1)),
    fast_path_waits_for_ai INTEGER NOT NULL CHECK (fast_path_waits_for_ai IN (0,1)),
    fast_path_waits_for_bundle INTEGER NOT NULL CHECK (fast_path_waits_for_bundle IN (0,1)),
    ai_attempts_apply INTEGER NOT NULL CHECK (ai_attempts_apply IN (0,1)),
    FOREIGN KEY(source_bundle_id) REFERENCES maintenance_bundle_events(bundle_id)
);

CREATE TABLE validator_decision_events (
    decision_id TEXT PRIMARY KEY,
    created_utc TEXT NOT NULL,
    proposal_id TEXT NOT NULL,
    validator_decision TEXT NOT NULL CHECK (validator_decision IN ('REJECT','REVIEW_REQUIRED','PLAN_ONLY_ALLOWED','DRYRUN_ALLOWED','APPROVAL_REQUIRED')),
    reject_reasons_json TEXT NOT NULL,
    review_reasons_json TEXT NOT NULL,
    forbidden_flags_seen_json TEXT NOT NULL,
    secret_scan_clean INTEGER NOT NULL CHECK (secret_scan_clean IN (0,1)),
    fast_path_impact_ok INTEGER NOT NULL CHECK (fast_path_impact_ok IN (0,1)),
    rollback_requirement_ok INTEGER NOT NULL CHECK (rollback_requirement_ok IN (0,1)),
    approval_requirement_ok INTEGER NOT NULL CHECK (approval_requirement_ok IN (0,1)),
    FOREIGN KEY(proposal_id) REFERENCES ai_proposal_events(proposal_id)
);

CREATE TABLE approval_queue_events (
    queue_id TEXT PRIMARY KEY,
    created_utc TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    proposal_id TEXT NOT NULL,
    queue_status TEXT NOT NULL CHECK (queue_status IN ('REJECTED','REVIEW_REQUIRED','PLAN_ONLY_ALLOWED','DRYRUN_ALLOWED','PENDING_APPROVAL','APPROVED_FOR_GUARDED_PHASE','EXPIRED','CANCELLED','CLOSED_AFTER_POST_AUDIT')),
    approval_required INTEGER NOT NULL CHECK (approval_required IN (0,1)),
    approval_phrase_required TEXT,
    exact_match_required INTEGER NOT NULL CHECK (exact_match_required IN (0,1)),
    queue_can_execute INTEGER NOT NULL CHECK (queue_can_execute = 0),
    queue_can_apply INTEGER NOT NULL CHECK (queue_can_apply = 0),
    queue_can_store_secret INTEGER NOT NULL CHECK (queue_can_store_secret = 0),
    FOREIGN KEY(decision_id) REFERENCES validator_decision_events(decision_id),
    FOREIGN KEY(proposal_id) REFERENCES ai_proposal_events(proposal_id)
);

CREATE TABLE rollback_registry_events (
    rollback_id TEXT PRIMARY KEY,
    created_utc TEXT NOT NULL,
    queue_id TEXT NOT NULL,
    proposal_id TEXT NOT NULL,
    mutation_class TEXT NOT NULL,
    backup_required INTEGER NOT NULL CHECK (backup_required IN (0,1)),
    rollback_script_required INTEGER NOT NULL CHECK (rollback_script_required IN (0,1)),
    post_audit_required INTEGER NOT NULL CHECK (post_audit_required IN (0,1)),
    pre_hashes_required INTEGER NOT NULL CHECK (pre_hashes_required IN (0,1)),
    rollback_script_must_exist_before_mutation INTEGER NOT NULL CHECK (rollback_script_must_exist_before_mutation IN (0,1)),
    rollback_no_reboot_shutdown_logout INTEGER NOT NULL CHECK (rollback_no_reboot_shutdown_logout IN (0,1)),
    FOREIGN KEY(queue_id) REFERENCES approval_queue_events(queue_id),
    FOREIGN KEY(proposal_id) REFERENCES ai_proposal_events(proposal_id)
);

CREATE INDEX idx_state_reader_next_phase ON state_reader_events(next_target_phase);
CREATE INDEX idx_bundle_state_ref ON maintenance_bundle_events(source_state_event_id);
CREATE INDEX idx_proposal_bundle_ref ON ai_proposal_events(source_bundle_id);
CREATE INDEX idx_validator_proposal ON validator_decision_events(proposal_id);
CREATE INDEX idx_queue_status ON approval_queue_events(queue_status);
CREATE INDEX idx_rollback_proposal ON rollback_registry_events(proposal_id);
