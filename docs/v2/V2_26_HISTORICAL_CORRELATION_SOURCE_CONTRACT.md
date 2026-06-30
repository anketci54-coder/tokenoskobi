# V2_26 Historical Correlation Source Contract

TASK=V2_26_HISTORICAL_CORRELATION_SOURCE_CONTRACT_PLAN_NOAPI
MODE=PLAN_ONLY_NOAPI
STAMP_UTC=2026-06-26T07:18:57.724956+00:00
PARENT_HEAD=413626301d297abcb19993a9ea4c76b31553864e

## Purpose

V2_26 defines the source contract for historical news, market, onchain, social, DEX and launch data.

This phase does not fetch data.
This phase does not write DB.
This phase does not touch panel, service, timer, wallet or live trade.

## Core Locks

HISTORICAL_DATA_IS_ARCHIVE_ONLY=true
HISTORICAL_DATA_IS_NOT_LIVE_DECISION_DATA=true
OUTCOME_LEAKAGE_FORBIDDEN=true
DATE_RANGE_REQUIRED=true
SOURCE_TIMESTAMP_REQUIRED=true
EVENT_TIMESTAMP_REQUIRED=true
DISCOVERED_TIME_REQUIRED=true
VISIBLE_DATA_UNTIL_REQUIRED=true
MARKET_CONTEXT_REQUIRED=true
ONCHAIN_CONTEXT_REQUIRED=true
LIQUIDITY_CONTEXT_REQUIRED=true
WHALE_CONTEXT_REQUIRED=true
SOURCE_CONTRACT_REQUIRED=true
EVENT_CONTRACT_REQUIRED=true
EVENT_TIME_AND_DISCOVERED_TIME_SEPARATED=true
L6_OUTCOME_NOT_VISIBLE_BEFORE_DECISION=true
API_FETCH_FORBIDDEN_IN_V2_26=true
DB_WRITE_FORBIDDEN_IN_V2_26=true

## Source Classes

- NEWS_SOURCE
- MARKET_SOURCE
- EXCHANGE_ANNOUNCEMENT_SOURCE
- DEX_SOURCE
- ONCHAIN_SOURCE
- SOCIAL_SOURCE
- LAUNCH_SOURCE

## Mandatory Source Fields

- source_id
- source_class
- source_name
- source_url_or_identifier
- access_method
- api_required
- archive_available
- date_range_supported
- timestamp_precision
- rate_limit_risk
- cost_risk
- terms_risk
- data_completeness
- trust_level
- manipulation_risk
- echo_chamber_risk
- outcome_leakage_risk
- allowed_usage
- forbidden_usage

## Historical Event Contract

Required event fields:

- historical_event_id
- token_uid
- chain
- contract_address
- event_type
- event_time
- source_time
- discovered_time
- source_class
- source_id
- raw_event_ref
- visible_data_until
- outcome_hidden_until
- market_regime_ref
- onchain_context_ref
- liquidity_context_ref
- whale_context_ref

## Time Separation Rule

event_time:
The time the event actually happened or was published.

discovered_time:
The time Tokenoskobi could have seen the event.

visible_data_until:
The blind model cannot see anything after this time.

outcome_hidden_until:
Actual result remains hidden until the blind decision is frozen.

## Outcome Leakage Guards

POST_EVENT_PRICE_NOT_VISIBLE_BEFORE_DECISION=true
POST_EVENT_VOLUME_NOT_VISIBLE_BEFORE_DECISION=true
POST_EVENT_LIQUIDITY_NOT_VISIBLE_BEFORE_DECISION=true
RUG_OUTCOME_NOT_VISIBLE_BEFORE_DECISION=true
PUMP_DUMP_OUTCOME_NOT_VISIBLE_BEFORE_DECISION=true
FUTURE_ONCHAIN_EVENTS_NOT_VISIBLE_BEFORE_DECISION=true
FUTURE_WHALE_FLOW_NOT_VISIBLE_BEFORE_DECISION=true
L6_OUTCOME_ONLY_AFTER_DECISION_FREEZE=true

## Evidence Levels

L0 = name or rumor only
L1 = source page exists
L2 = timestamp exists
L3 = token / contract match exists
L4 = official or independent confirmation exists
L5 = market / onchain context matches
L6 = outcome verified after decision freeze

L6 outcome must not be visible before blind decision.

## Final Doctrine

Historical data is cold-path archive data.
Historical data can train, audit and validate.
Historical data cannot directly drive live decisions.
