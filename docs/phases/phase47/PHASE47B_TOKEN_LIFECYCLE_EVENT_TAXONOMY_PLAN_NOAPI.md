# PHASE47B_TOKEN_LIFECYCLE_EVENT_TAXONOMY_PLAN_NOAPI

## STATUS
PLAN_ONLY

## CORE RULE
Before schema design, define lifecycle event taxonomy.

NO_ASSUMED_TIME_BUCKETS=true
NO_FIXED_SCORE_WEIGHTS=true
MARKET_DETERMINES_TIME_WINDOWS=true
MARKET_DETERMINES_WEIGHTS=true

## HARD LOCKS
DB_WRITE=false
SCHEMA_APPLY=false
TEMPDB=false
RUNTIME_CHANGE=false
API_CALL=false
PANEL_WRITE=false
SERVICE_RESTART=false
GIT_PUSH=false
TRADE_AUTHORITY=false
AI_AUTHORITY=false

## PURPOSE
Define token lifecycle event classes before creating tables.

## LIFECYCLE STAGES
- BIRTH
- CHILDHOOD
- YOUTH
- MATURITY
- AGING
- DEATH
- REVIVAL

## EVENT TAXONOMY

### birth_events
- deploy_event
- first_liquidity_event
- first_trade_event
- first_holder_event
- initial_tax_state_event
- initial_contract_state_event

### market_events
- price_move_event
- volume_spike_event
- liquidity_change_event
- holder_distribution_event
- whale_entry_event
- whale_exit_event

### attack_events
- rug_pull_event
- honeypot_event
- liquidity_drain_event
- hidden_tax_event
- tax_mutation_event
- owner_abuse_event
- proxy_trap_event
- hidden_mint_event

### mev_events
- mev_pressure_event
- sandwich_attack_event
- front_run_event
- back_run_event
- arbitrage_pressure_event

### manipulation_events
- fake_volume_event
- wash_trading_event
- fake_holder_event
- social_hype_event
- coordinated_wallet_event

### death_events
- hard_death_event
- slow_death_event
- abandoned_event
- sellability_failure_event
- liquidity_zero_event

### revival_events
- liquidity_return_event
- volume_return_event
- holder_return_event
- whale_return_event
- narrative_return_event

## HOT PATH RULE
Taxonomy is cold/warm path.
HOT PATH only reads precomputed lifecycle_fast_readmodel_v1.

## NEXT_SAFE_STEP
PHASE47C_TOKEN_LIFECYCLE_SCHEMA_PLAN_NOAPI

## FINAL_GATE
PASS_PHASE47B_TOKEN_LIFECYCLE_EVENT_TAXONOMY_PLAN_NOAPI
