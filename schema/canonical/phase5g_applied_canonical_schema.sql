/* PHASE5E2 CANONICAL TEMP DB DRYRUN REPAIR SQL */
/* DO NOT APPLY TO LIVE DB */
/* Duplicate table definitions are canonicalized by latest phase, then widest definition. */

/* CANONICAL_TABLE=cascading_execution_filter_eval_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS cascading_execution_filter_eval_events_v1 (
  eval_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  route_type TEXT NOT NULL,
  current_stage_no INTEGER NOT NULL,
  current_stage_id TEXT NOT NULL,
  stage_result TEXT NOT NULL,
  stop_reason TEXT,
  rpc_calls_used INTEGER NOT NULL,
  eth_call_used INTEGER NOT NULL,
  router_quote_used INTEGER NOT NULL,
  execution_permission TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=cascading_execution_filter_policy_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS cascading_execution_filter_policy_v1 (
  policy_uid TEXT PRIMARY KEY,
  policy_version TEXT NOT NULL,
  chain TEXT NOT NULL,
  stage_no INTEGER NOT NULL,
  stage_id TEXT NOT NULL,
  cost_tier TEXT NOT NULL,
  future_rpc_required TEXT NOT NULL,
  stop_if_fail INTEGER NOT NULL,
  fail_action TEXT NOT NULL,
  fields_json TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=command_decision_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS command_decision_time_series_v1 (
  decision_series_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT,
  decision_label TEXT NOT NULL,
  decision_status TEXT NOT NULL,
  hard_block_reason TEXT,
  linked_risk_event_uid TEXT,
  linked_safety_event_uid TEXT,
  reason_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=data_quality_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS data_quality_time_series_v1 (
  quality_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  source_family TEXT NOT NULL,
  source_uid TEXT,
  token_uid TEXT,
  pair_uid TEXT,
  quality_label TEXT NOT NULL,
  stale_data INTEGER NOT NULL,
  missing_required_fields INTEGER NOT NULL,
  parse_error INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=deployer_receipt_evidence_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS deployer_receipt_evidence_events_v1 (
  event_uid TEXT PRIMARY KEY,
  token_uid TEXT,
  chain TEXT NOT NULL,
  tx_hash TEXT,
  receipt_found INTEGER NOT NULL,
  token_log_match INTEGER NOT NULL,
  creation_proof INTEGER NOT NULL,
  zero_mint_unproven INTEGER NOT NULL,
  interpretation_label TEXT NOT NULL,
  source_object_uid TEXT,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=evidence_event_ledger_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS evidence_event_ledger_v1 (
  event_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  source_phase TEXT NOT NULL,
  chain TEXT,
  token_uid TEXT,
  pair_uid TEXT,
  event_family TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_status TEXT NOT NULL,
  confidence TEXT NOT NULL,
  evidence_hash TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=evidence_object_store_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS evidence_object_store_v1 (
  object_uid TEXT PRIMARY KEY,
  object_kind TEXT NOT NULL,
  source_phase TEXT NOT NULL,
  chain TEXT,
  token_uid TEXT,
  pair_uid TEXT,
  object_hash TEXT NOT NULL,
  object_summary_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=execution_preflight_audit_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS execution_preflight_audit_events_v1 (
  preflight_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  route_type TEXT NOT NULL,
  paper_allowed INTEGER NOT NULL,
  live_allowed INTEGER NOT NULL,
  failed_required_fields_json TEXT NOT NULL,
  passed_gate_list_json TEXT NOT NULL,
  blocked_reason_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=execution_rpc_budget_guard_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS execution_rpc_budget_guard_events_v1 (
  budget_event_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  guard_id TEXT NOT NULL,
  guard_result TEXT NOT NULL,
  blocked_expensive_call INTEGER NOT NULL,
  saved_call_type TEXT,
  reason_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=execution_safety_gate_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS execution_safety_gate_events_v1 (
  safety_event_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  route_type TEXT NOT NULL,
  minimum_pool_liquidity_usd REAL,
  buy_price_impact_pct REAL,
  sell_price_impact_pct REAL,
  expected_slippage_pct REAL,
  max_position_size_usd REAL,
  exit_liquidity_usd REAL,
  sell_route_status TEXT NOT NULL,
  tax_buy_pct REAL,
  tax_sell_pct REAL,
  mev_status TEXT NOT NULL,
  gas_cost_sanity TEXT NOT NULL,
  protected_route_status TEXT NOT NULL,
  execution_permission TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=execution_safety_gate_events_v2 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS execution_safety_gate_events_v2 (
  safety_event_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  route_type TEXT NOT NULL,
  policy_uid TEXT,
  hard_block INTEGER NOT NULL,
  sell_route_status TEXT NOT NULL,
  minimum_pool_liquidity_usd REAL,
  exit_liquidity_usd REAL,
  buy_price_impact_pct REAL,
  sell_price_impact_pct REAL,
  expected_slippage_pct REAL,
  max_position_size_usd REAL,
  tax_buy_pct REAL,
  tax_sell_pct REAL,
  mev_status TEXT NOT NULL,
  sandwich_exposure_status TEXT NOT NULL,
  gas_cost_sanity TEXT NOT NULL,
  protected_route_status TEXT NOT NULL,
  execution_permission TEXT NOT NULL,
  failed_gate_list_json TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=execution_safety_policy_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS execution_safety_policy_v1 (
  policy_uid TEXT PRIMARY KEY,
  policy_version TEXT NOT NULL,
  chain TEXT NOT NULL,
  route_type TEXT NOT NULL,
  min_pool_liquidity_usd REAL NOT NULL,
  max_buy_impact_pct REAL NOT NULL,
  max_sell_impact_pct REAL NOT NULL,
  max_expected_slippage_pct REAL NOT NULL,
  max_buy_tax_pct REAL NOT NULL,
  max_sell_tax_pct REAL NOT NULL,
  exit_depth_multiplier REAL NOT NULL,
  mev_required_status TEXT NOT NULL,
  protected_route_required INTEGER NOT NULL,
  live_allowed INTEGER NOT NULL,
  paper_allowed INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=execution_safety_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS execution_safety_time_series_v1 (
  exec_series_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT,
  route_type TEXT NOT NULL,
  buy_price_impact_pct REAL,
  sell_price_impact_pct REAL,
  expected_slippage_pct REAL,
  max_position_size_usd REAL,
  sell_route_status TEXT NOT NULL,
  tax_buy_pct REAL,
  tax_sell_pct REAL,
  mev_status TEXT NOT NULL,
  protected_route_status TEXT NOT NULL,
  execution_permission TEXT NOT NULL,
  source_event_uid TEXT,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=holder_distribution_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS holder_distribution_time_series_v1 (
  holder_series_uid TEXT PRIMARY KEY,
  token_uid TEXT,
  chain TEXT NOT NULL,
  event_ts_utc TEXT NOT NULL,
  holder_count INTEGER,
  top1_pct REAL,
  top5_pct REAL,
  top10_pct REAL,
  new_holder_count INTEGER,
  exiting_holder_count INTEGER,
  distribution_quality TEXT NOT NULL,
  source_event_uid TEXT,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=initial_holder_evidence_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS initial_holder_evidence_events_v1 (
  event_uid TEXT PRIMARY KEY,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  holder_group_key TEXT,
  scan_window_json TEXT NOT NULL,
  transfer_mint_summary_json TEXT NOT NULL,
  risk_interpretation TEXT NOT NULL,
  source_object_uid TEXT,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=liquidity_depth_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS liquidity_depth_time_series_v1 (
  depth_uid TEXT PRIMARY KEY,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  event_ts_utc TEXT NOT NULL,
  liquidity_usd REAL,
  base_reserve REAL,
  quote_reserve REAL,
  exit_liquidity_usd REAL,
  depth_quality TEXT NOT NULL,
  source_event_uid TEXT,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=market_ohlcv_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS market_ohlcv_time_series_v1 (
  candle_uid TEXT PRIMARY KEY,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  open_ts_utc TEXT NOT NULL,
  close_ts_utc TEXT NOT NULL,
  open_price_usd REAL,
  high_price_usd REAL,
  low_price_usd REAL,
  close_price_usd REAL,
  volume_usd REAL,
  tx_count INTEGER,
  buy_count INTEGER,
  sell_count INTEGER,
  source_quality TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=micro_route_size_plan_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS micro_route_size_plan_events_v1 (
  size_plan_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  route_type TEXT NOT NULL,
  requested_size_usd REAL,
  max_safe_size_usd REAL,
  size_decision TEXT NOT NULL,
  linked_safety_event_uid TEXT,
  reason_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=model_feedback_candidate_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS model_feedback_candidate_events_v1 (
  feedback_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  candidate_source TEXT NOT NULL,
  linked_replay_case_uid TEXT,
  linked_lesson_uid TEXT,
  candidate_label TEXT NOT NULL,
  candidate_quality TEXT NOT NULL,
  approved_for_training INTEGER NOT NULL,
  approval_required INTEGER NOT NULL,
  evidence_hash TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=negative_memory_guard_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS negative_memory_guard_events_v1 (
  negative_guard_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT,
  negative_label TEXT NOT NULL,
  preserve_reason TEXT NOT NULL,
  deletion_allowed INTEGER NOT NULL,
  archive_allowed INTEGER NOT NULL,
  training_value_label TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=news_impact_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS news_impact_events_v1 (
  news_event_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  source_uid TEXT,
  token_uid TEXT,
  match_confidence TEXT NOT NULL,
  impact_label TEXT NOT NULL,
  impact_score REAL,
  narrative_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=news_narrative_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS news_narrative_time_series_v1 (
  narrative_series_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  source_uid TEXT,
  match_confidence TEXT NOT NULL,
  impact_label TEXT NOT NULL,
  impact_score REAL,
  decay_window TEXT,
  source_event_uid TEXT,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=outcome_lesson_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS outcome_lesson_events_v1 (
  lesson_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT,
  linked_outcome_uid TEXT,
  lesson_id TEXT NOT NULL,
  lesson_family TEXT NOT NULL,
  severity TEXT NOT NULL,
  training_candidate INTEGER NOT NULL,
  requires_replay INTEGER NOT NULL,
  evidence_hash TEXT NOT NULL,
  lesson_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=outcome_memory_events_v2 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS outcome_memory_events_v2 (
  outcome_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  linked_decision_uid TEXT,
  linked_preflight_uid TEXT,
  linked_paper_decision_uid TEXT,
  outcome_label TEXT NOT NULL,
  outcome_window TEXT NOT NULL,
  pnl_pct REAL,
  max_runup_pct REAL,
  max_drawdown_pct REAL,
  liquidity_change_pct REAL,
  evidence_hash TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=outcome_observation_window_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS outcome_observation_window_events_v1 (
  observation_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  linked_decision_uid TEXT,
  window_label TEXT NOT NULL,
  window_start_ts_utc TEXT NOT NULL,
  window_end_ts_utc TEXT NOT NULL,
  price_change_pct REAL,
  max_runup_pct REAL,
  max_drawdown_pct REAL,
  volume_change_pct REAL,
  liquidity_change_pct REAL,
  observation_quality TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=paper_observation_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS paper_observation_time_series_v1 (
  observation_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  paper_decision_uid TEXT,
  window_label TEXT NOT NULL,
  price_change_pct REAL,
  max_runup_pct REAL,
  max_drawdown_pct REAL,
  liquidity_change_pct REAL,
  observation_quality TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=paper_route_decision_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS paper_route_decision_events_v1 (
  paper_decision_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  linked_safety_event_uid TEXT,
  decision_label TEXT NOT NULL,
  decision_status TEXT NOT NULL,
  max_paper_size_usd REAL,
  reason_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=replay_case_registry_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS replay_case_registry_v1 (
  replay_case_uid TEXT PRIMARY KEY,
  created_at_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT,
  case_family TEXT NOT NULL,
  case_label TEXT NOT NULL,
  linked_outcome_uid TEXT,
  linked_lesson_uid TEXT,
  evidence_bundle_hash TEXT NOT NULL,
  replay_status TEXT NOT NULL,
  training_allowed INTEGER NOT NULL,
  payload_json TEXT NOT NULL
);

/* CANONICAL_TABLE=risk_gate_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS risk_gate_events_v1 (
  risk_event_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  risk_family TEXT NOT NULL,
  risk_label TEXT NOT NULL,
  risk_status TEXT NOT NULL,
  hard_block INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=risk_state_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS risk_state_time_series_v1 (
  risk_state_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT,
  risk_family TEXT NOT NULL,
  risk_status TEXT NOT NULL,
  hard_block INTEGER NOT NULL,
  wait_more_data INTEGER NOT NULL,
  clearance_status TEXT NOT NULL,
  source_event_uid TEXT,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=route_performance_memory_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS route_performance_memory_events_v1 (
  route_memory_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  route_type TEXT NOT NULL,
  linked_safety_event_uid TEXT,
  linked_filter_eval_uid TEXT,
  linked_outcome_uid TEXT,
  route_result TEXT NOT NULL,
  pnl_pct REAL,
  slippage_realized_pct REAL,
  gas_cost_usd REAL,
  lesson_candidate INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=technical_signal_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS technical_signal_events_v1 (
  signal_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  timeframe TEXT NOT NULL,
  signal_family TEXT NOT NULL,
  signal_label TEXT NOT NULL,
  signal_strength REAL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=token_lifecycle_autopsy_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS token_lifecycle_autopsy_events_v1 (
  autopsy_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  lifecycle_label TEXT NOT NULL,
  autopsy_reason TEXT NOT NULL,
  death_or_revival_signal TEXT,
  linked_risk_event_uid TEXT,
  linked_outcome_uid TEXT,
  preserve_record INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=token_time_series_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS token_time_series_events_v1 (
  series_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT,
  series_family TEXT NOT NULL,
  series_metric TEXT NOT NULL,
  numeric_value REAL,
  text_value TEXT,
  quality_label TEXT NOT NULL,
  source_event_uid TEXT,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=transaction_activity_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS transaction_activity_time_series_v1 (
  activity_uid TEXT PRIMARY KEY,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  window_label TEXT NOT NULL,
  window_start_ts_utc TEXT NOT NULL,
  window_end_ts_utc TEXT NOT NULL,
  tx_count INTEGER,
  buy_count INTEGER,
  sell_count INTEGER,
  volume_usd REAL,
  unique_wallet_count INTEGER,
  activity_quality TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=wallet_whale_flow_time_series_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS wallet_whale_flow_time_series_v1 (
  flow_series_uid TEXT PRIMARY KEY,
  token_uid TEXT,
  pair_uid TEXT,
  chain TEXT NOT NULL,
  event_ts_utc TEXT NOT NULL,
  wallet_cluster_uid TEXT,
  flow_direction TEXT NOT NULL,
  flow_value_usd REAL,
  flow_token_amount REAL,
  confidence TEXT NOT NULL,
  source_event_uid TEXT,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_TABLE=whale_flow_events_v1 SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql */
CREATE TABLE IF NOT EXISTS whale_flow_events_v1 (
  whale_event_uid TEXT PRIMARY KEY,
  event_ts_utc TEXT NOT NULL,
  chain TEXT,
  token_uid TEXT,
  wallet_cluster_uid TEXT,
  flow_direction TEXT NOT NULL,
  flow_value_usd REAL,
  confidence TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

/* CANONICAL_INDEXES */
/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_deployer_receipt_evidence_events_v1_chain ON deployer_receipt_evidence_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_deployer_receipt_evidence_events_v1_created_at_utc ON deployer_receipt_evidence_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_deployer_receipt_evidence_events_v1_token_uid ON deployer_receipt_evidence_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_evidence_event_ledger_v1_chain ON evidence_event_ledger_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_evidence_event_ledger_v1_created_at_utc ON evidence_event_ledger_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_evidence_event_ledger_v1_event_ts_utc ON evidence_event_ledger_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_evidence_event_ledger_v1_pair_uid ON evidence_event_ledger_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_evidence_event_ledger_v1_token_uid ON evidence_event_ledger_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_evidence_object_store_v1_chain ON evidence_object_store_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_evidence_object_store_v1_created_at_utc ON evidence_object_store_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_evidence_object_store_v1_pair_uid ON evidence_object_store_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_evidence_object_store_v1_token_uid ON evidence_object_store_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v1_created_at_utc ON execution_safety_gate_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v1_event_ts_utc ON execution_safety_gate_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v1_pair_uid ON execution_safety_gate_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v1_token_uid ON execution_safety_gate_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_initial_holder_evidence_events_v1_chain ON initial_holder_evidence_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_initial_holder_evidence_events_v1_created_at_utc ON initial_holder_evidence_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_initial_holder_evidence_events_v1_pair_uid ON initial_holder_evidence_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_initial_holder_evidence_events_v1_token_uid ON initial_holder_evidence_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_news_impact_events_v1_created_at_utc ON news_impact_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_news_impact_events_v1_event_ts_utc ON news_impact_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_news_impact_events_v1_token_uid ON news_impact_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_memory_events_v2_created_at_utc ON outcome_memory_events_v2(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_memory_events_v2_event_ts_utc ON outcome_memory_events_v2(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_memory_events_v2_pair_uid ON outcome_memory_events_v2(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_memory_events_v2_token_uid ON outcome_memory_events_v2(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_paper_route_decision_events_v1_created_at_utc ON paper_route_decision_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_paper_route_decision_events_v1_event_ts_utc ON paper_route_decision_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_paper_route_decision_events_v1_pair_uid ON paper_route_decision_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_paper_route_decision_events_v1_token_uid ON paper_route_decision_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_risk_gate_events_v1_created_at_utc ON risk_gate_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_risk_gate_events_v1_event_ts_utc ON risk_gate_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_risk_gate_events_v1_pair_uid ON risk_gate_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_risk_gate_events_v1_token_uid ON risk_gate_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_technical_signal_events_v1_created_at_utc ON technical_signal_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_technical_signal_events_v1_event_ts_utc ON technical_signal_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_technical_signal_events_v1_pair_uid ON technical_signal_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_technical_signal_events_v1_token_uid ON technical_signal_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_time_series_events_v1_chain ON token_time_series_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_time_series_events_v1_created_at_utc ON token_time_series_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_time_series_events_v1_event_ts_utc ON token_time_series_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_time_series_events_v1_pair_uid ON token_time_series_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_time_series_events_v1_token_uid ON token_time_series_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_whale_flow_events_v1_chain ON whale_flow_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_whale_flow_events_v1_created_at_utc ON whale_flow_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_whale_flow_events_v1_event_ts_utc ON whale_flow_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_whale_flow_events_v1_token_uid ON whale_flow_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_command_decision_time_series_v1_chain ON command_decision_time_series_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_command_decision_time_series_v1_created_at_utc ON command_decision_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_command_decision_time_series_v1_event_ts_utc ON command_decision_time_series_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_command_decision_time_series_v1_pair_uid ON command_decision_time_series_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_command_decision_time_series_v1_token_uid ON command_decision_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_data_quality_time_series_v1_created_at_utc ON data_quality_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_data_quality_time_series_v1_event_ts_utc ON data_quality_time_series_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_data_quality_time_series_v1_pair_uid ON data_quality_time_series_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_data_quality_time_series_v1_token_uid ON data_quality_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_time_series_v1_chain ON execution_safety_time_series_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_time_series_v1_created_at_utc ON execution_safety_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_time_series_v1_event_ts_utc ON execution_safety_time_series_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_time_series_v1_pair_uid ON execution_safety_time_series_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_time_series_v1_token_uid ON execution_safety_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_holder_distribution_time_series_v1_chain ON holder_distribution_time_series_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_holder_distribution_time_series_v1_created_at_utc ON holder_distribution_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_holder_distribution_time_series_v1_event_ts_utc ON holder_distribution_time_series_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_holder_distribution_time_series_v1_token_uid ON holder_distribution_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_liquidity_depth_time_series_v1_chain ON liquidity_depth_time_series_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_liquidity_depth_time_series_v1_created_at_utc ON liquidity_depth_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_liquidity_depth_time_series_v1_event_ts_utc ON liquidity_depth_time_series_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_liquidity_depth_time_series_v1_pair_uid ON liquidity_depth_time_series_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_liquidity_depth_time_series_v1_token_uid ON liquidity_depth_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_market_ohlcv_time_series_v1_chain ON market_ohlcv_time_series_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_market_ohlcv_time_series_v1_created_at_utc ON market_ohlcv_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_market_ohlcv_time_series_v1_pair_uid ON market_ohlcv_time_series_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_market_ohlcv_time_series_v1_timeframe ON market_ohlcv_time_series_v1(timeframe);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_market_ohlcv_time_series_v1_token_uid ON market_ohlcv_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_news_narrative_time_series_v1_created_at_utc ON news_narrative_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_news_narrative_time_series_v1_event_ts_utc ON news_narrative_time_series_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_news_narrative_time_series_v1_token_uid ON news_narrative_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_paper_observation_time_series_v1_created_at_utc ON paper_observation_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_paper_observation_time_series_v1_event_ts_utc ON paper_observation_time_series_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_paper_observation_time_series_v1_pair_uid ON paper_observation_time_series_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_paper_observation_time_series_v1_token_uid ON paper_observation_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_paper_observation_time_series_v1_window_label ON paper_observation_time_series_v1(window_label);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_risk_state_time_series_v1_chain ON risk_state_time_series_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_risk_state_time_series_v1_created_at_utc ON risk_state_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_risk_state_time_series_v1_event_ts_utc ON risk_state_time_series_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_risk_state_time_series_v1_pair_uid ON risk_state_time_series_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_risk_state_time_series_v1_token_uid ON risk_state_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_transaction_activity_time_series_v1_chain ON transaction_activity_time_series_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_transaction_activity_time_series_v1_created_at_utc ON transaction_activity_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_transaction_activity_time_series_v1_pair_uid ON transaction_activity_time_series_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_transaction_activity_time_series_v1_token_uid ON transaction_activity_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_transaction_activity_time_series_v1_window_label ON transaction_activity_time_series_v1(window_label);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_wallet_whale_flow_time_series_v1_chain ON wallet_whale_flow_time_series_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_wallet_whale_flow_time_series_v1_created_at_utc ON wallet_whale_flow_time_series_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_wallet_whale_flow_time_series_v1_event_ts_utc ON wallet_whale_flow_time_series_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_wallet_whale_flow_time_series_v1_pair_uid ON wallet_whale_flow_time_series_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5B_TIME_SERIES_SCHEMA_GAP_PLAN_NOAPI/20260531_233313/phase5b_future_time_series_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_wallet_whale_flow_time_series_v1_token_uid ON wallet_whale_flow_time_series_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_preflight_audit_events_v1_chain ON execution_preflight_audit_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_preflight_audit_events_v1_created_at_utc ON execution_preflight_audit_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_preflight_audit_events_v1_event_ts_utc ON execution_preflight_audit_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_preflight_audit_events_v1_pair_uid ON execution_preflight_audit_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_preflight_audit_events_v1_route_type ON execution_preflight_audit_events_v1(route_type);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_preflight_audit_events_v1_token_uid ON execution_preflight_audit_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v2_chain ON execution_safety_gate_events_v2(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v2_created_at_utc ON execution_safety_gate_events_v2(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v2_event_ts_utc ON execution_safety_gate_events_v2(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v2_pair_uid ON execution_safety_gate_events_v2(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v2_policy_uid ON execution_safety_gate_events_v2(policy_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v2_route_type ON execution_safety_gate_events_v2(route_type);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_gate_events_v2_token_uid ON execution_safety_gate_events_v2(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_policy_v1_chain ON execution_safety_policy_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_policy_v1_created_at_utc ON execution_safety_policy_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_policy_v1_policy_uid ON execution_safety_policy_v1(policy_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_safety_policy_v1_route_type ON execution_safety_policy_v1(route_type);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_micro_route_size_plan_events_v1_chain ON micro_route_size_plan_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_micro_route_size_plan_events_v1_created_at_utc ON micro_route_size_plan_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_micro_route_size_plan_events_v1_event_ts_utc ON micro_route_size_plan_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_micro_route_size_plan_events_v1_pair_uid ON micro_route_size_plan_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_micro_route_size_plan_events_v1_route_type ON micro_route_size_plan_events_v1(route_type);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C_EXECUTION_SAFETY_AND_MICRO_ROUTE_PLAN_NOAPI/20260531_233621/phase5c_future_execution_safety_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_micro_route_size_plan_events_v1_token_uid ON micro_route_size_plan_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_cascading_execution_filter_eval_events_v1_chain ON cascading_execution_filter_eval_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_cascading_execution_filter_eval_events_v1_created_at_utc ON cascading_execution_filter_eval_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_cascading_execution_filter_eval_events_v1_event_ts_utc ON cascading_execution_filter_eval_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_cascading_execution_filter_eval_events_v1_pair_uid ON cascading_execution_filter_eval_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_cascading_execution_filter_eval_events_v1_token_uid ON cascading_execution_filter_eval_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_cascading_execution_filter_policy_v1_chain ON cascading_execution_filter_policy_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_cascading_execution_filter_policy_v1_created_at_utc ON cascading_execution_filter_policy_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_cascading_execution_filter_policy_v1_stage_id ON cascading_execution_filter_policy_v1(stage_id);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_rpc_budget_guard_events_v1_chain ON execution_rpc_budget_guard_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_rpc_budget_guard_events_v1_created_at_utc ON execution_rpc_budget_guard_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_rpc_budget_guard_events_v1_event_ts_utc ON execution_rpc_budget_guard_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_rpc_budget_guard_events_v1_guard_id ON execution_rpc_budget_guard_events_v1(guard_id);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_rpc_budget_guard_events_v1_pair_uid ON execution_rpc_budget_guard_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5C2_CASCADING_EXECUTION_FILTER_PLAN_NOAPI/20260531_235701/phase5c2_future_cascading_filter_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_execution_rpc_budget_guard_events_v1_token_uid ON execution_rpc_budget_guard_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_model_feedback_candidate_events_v1_created_at_utc ON model_feedback_candidate_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_model_feedback_candidate_events_v1_event_ts_utc ON model_feedback_candidate_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_negative_memory_guard_events_v1_chain ON negative_memory_guard_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_negative_memory_guard_events_v1_created_at_utc ON negative_memory_guard_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_negative_memory_guard_events_v1_event_ts_utc ON negative_memory_guard_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_negative_memory_guard_events_v1_pair_uid ON negative_memory_guard_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_negative_memory_guard_events_v1_token_uid ON negative_memory_guard_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_lesson_events_v1_chain ON outcome_lesson_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_lesson_events_v1_created_at_utc ON outcome_lesson_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_lesson_events_v1_event_ts_utc ON outcome_lesson_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_lesson_events_v1_lesson_id ON outcome_lesson_events_v1(lesson_id);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_lesson_events_v1_linked_outcome_uid ON outcome_lesson_events_v1(linked_outcome_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_lesson_events_v1_pair_uid ON outcome_lesson_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_lesson_events_v1_token_uid ON outcome_lesson_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_memory_events_v2_chain ON outcome_memory_events_v2(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_memory_events_v2_linked_decision_uid ON outcome_memory_events_v2(linked_decision_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_observation_window_events_v1_chain ON outcome_observation_window_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_observation_window_events_v1_created_at_utc ON outcome_observation_window_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_observation_window_events_v1_event_ts_utc ON outcome_observation_window_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_observation_window_events_v1_linked_decision_uid ON outcome_observation_window_events_v1(linked_decision_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_observation_window_events_v1_pair_uid ON outcome_observation_window_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_outcome_observation_window_events_v1_token_uid ON outcome_observation_window_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_replay_case_registry_v1_case_family ON replay_case_registry_v1(case_family);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_replay_case_registry_v1_chain ON replay_case_registry_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_replay_case_registry_v1_created_at_utc ON replay_case_registry_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_replay_case_registry_v1_linked_outcome_uid ON replay_case_registry_v1(linked_outcome_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_replay_case_registry_v1_pair_uid ON replay_case_registry_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_replay_case_registry_v1_token_uid ON replay_case_registry_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_route_performance_memory_events_v1_chain ON route_performance_memory_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_route_performance_memory_events_v1_created_at_utc ON route_performance_memory_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_route_performance_memory_events_v1_event_ts_utc ON route_performance_memory_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_route_performance_memory_events_v1_linked_outcome_uid ON route_performance_memory_events_v1(linked_outcome_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_route_performance_memory_events_v1_pair_uid ON route_performance_memory_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_route_performance_memory_events_v1_route_type ON route_performance_memory_events_v1(route_type);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_route_performance_memory_events_v1_token_uid ON route_performance_memory_events_v1(token_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_lifecycle_autopsy_events_v1_chain ON token_lifecycle_autopsy_events_v1(chain);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_lifecycle_autopsy_events_v1_created_at_utc ON token_lifecycle_autopsy_events_v1(created_at_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_lifecycle_autopsy_events_v1_event_ts_utc ON token_lifecycle_autopsy_events_v1(event_ts_utc);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_lifecycle_autopsy_events_v1_lifecycle_label ON token_lifecycle_autopsy_events_v1(lifecycle_label);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_lifecycle_autopsy_events_v1_linked_outcome_uid ON token_lifecycle_autopsy_events_v1(linked_outcome_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_lifecycle_autopsy_events_v1_pair_uid ON token_lifecycle_autopsy_events_v1(pair_uid);

/* INDEX_SOURCE=/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql */
CREATE INDEX IF NOT EXISTS idx_token_lifecycle_autopsy_events_v1_token_uid ON token_lifecycle_autopsy_events_v1(token_uid);
