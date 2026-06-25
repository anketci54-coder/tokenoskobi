# TOKENOSKOBI V1 ROADMAP RELOCK NOAPI

- created_at_utc: `2026-05-09T17:25:58.790798+00:00`
- root: `/root/tokenoskobi_clean_v1`
- db: `/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite`
- final_status: **PASS**

## Safety
- api_calls: `0`
- external_network_calls: `0`
- db_mutation: `False`
- schema_apply: `False`
- paper_position_write: `False`
- paper_execution_write: `False`
- live_trade: `False`
- telegram: `False`
- panel_mutation: `False`
- morgue_autopsy_move: `False`
- token_specific_logic: `False`
- patch_existing_files: `False`
- scope: `roadmap relock and backbone decision manifest only; read-only DB; no token-specific rules; no patch`

## DB Health Snapshot
- db_sha256: `96a9d40e52cb4777536990c231b028be2ad056163d60c430095bda462f8fd5f2`
- integrity_check: `ok`
- quick_check: `ok`
- foreign_key_error_count: `0`
- tokens: `19`
- pairs: `19`
- liquidity_snapshots: `45`
- market_snapshots: `45`
- paper_trade_plans: `2`
- paper_trade_positions: `0`
- paper_trade_executions: `0`
- paper_trade_outcomes: `0`
- paper_trade_costs: `0`

## Backbone Principles
- Tokenoskobi is a token intelligence system first, not a trading bot first.
- No live trade, no paper position, no execution, no Telegram automation until explicit phase approval.
- No token/coin-specific hardcoded logic in backbone phases.
- No patch/yama to existing engine, panel, or core files in roadmap/design phases.
- Generated reports are not token data sources.
- Old/stale pair data is identity seed only, never direct truth.
- Current pair verification is required before any active observation or simulation.
- Birth/opening price must not be invented; if missing, mark unknown.
- Risky tokens are not blindly discarded; they are routed to Death, Watch, Moonshot Memory, or blocked buckets.
- Paper/live routes are separate from intelligence/warehouse routes.

## Completed
- ✅ **Clean V1 DB health check** — `DONE`
- ✅ **Post archive and DB status check** — `DONE`
- ✅ **Panel path and N3 badge locator** — `DONE`
- ✅ **Generic paper position open gate review** — `DONE`
- ✅ **Generic schema gap decision** — `DONE`

## Parked / Locked
- ⏸️ **Paper position open** — `PARKED` — Evidence chain missing: TP1, sell_status, impact, MEV, execution risk, explicit approval
- ⏸️ **Live or micro-live** — `LOCKED` — Needs MEV shield, dynamic sizing, fresh data, sell confirmation, explicit approval
- ⏸️ **AI training** — `WAIT` — Needs 30-90 days clean labeled forensic warehouse data

## Roadmap Order

### 1. `FW1_FORENSIC_WAREHOUSE_BACKBONE_DESIGN_NOAPI`
- module: `Forensic Warehouse`
- mode: `NOAPI_READONLY_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define generic warehouse backbone for token birth, pair birth, liquidity, price, snapshots, deployer, holder, wallet, risk, death/life/moonshot labels.

### 2. `SG1_SOURCE_GATE_DESIGN_NOAPI`
- module: `Source Gate`
- mode: `NOAPI_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define source trust, stale pair block, wrong pair block, no-pair memory, alias confusion protection, current pair verification gate.

### 3. `BIRTH1_TOKEN_PAIR_BIRTH_PIPELINE_DESIGN_NOAPI`
- module: `Birth / Opening Baseline`
- mode: `NOAPI_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define token_birth_time, pair_birth_time, liquidity_birth_time, first_seen_local_time, first_trusted_price_time, and no invented opening price rule.

### 4. `PIPE1_TWO_SOURCE_PRESSURE_TEST_PLAN_NOAPI`
- module: `Two Source Pipe Test`
- mode: `NOAPI_PLAN_FIRST`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Plan short pressure test for DexScreener + GeckoTerminal without live DB mutation; check leaks, mismatches, 404/429 handling, stale data, pair mismatch.

### 5. `DEATH1_DEATH_CORE_DESIGN_NOAPI`
- module: `Death Core`
- mode: `NOAPI_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define STILLBORN, EARLY_DEATH, FAST_DECAY, RUG, SLOW_DEATH, MORGUE_CANDIDATE and autopsy reasons.

### 6. `LIFE1_LIFE_CORE_DESIGN_NOAPI`
- module: `Life Core`
- mode: `NOAPI_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define life signals: liquidity alive, tx flow, holder growth, organic volume, buyer/seller balance, snapshot strengthening.

### 7. `MOON1_MOONSHOT_CORE_DESIGN_NOAPI`
- module: `Moonshot Core`
- mode: `NOAPI_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define asymmetric watch, moonshot memory, tiny basket candidate, high-risk tiny route without auto-trade.

### 8. `NEWS1_NARRATIVE_CORE_DESIGN_NOAPI`
- module: `News / Narrative Core`
- mode: `NOAPI_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define event/news/trend/narrative flow and how narrative strengthens but never alone creates buy signal.

### 9. `WHALE1_WALLET_MOVEMENT_CORE_DESIGN_NOAPI`
- module: `Whale Wallet Core`
- mode: `NOAPI_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define whale buys/sells, deployer wallet, LP wallet, smart money, wallet cluster behavior as evidence layer.

### 10. `RISK1_DYNAMIC_POSITION_SIZING_DESIGN_NOAPI`
- module: `Risk Budget / Position Sizing`
- mode: `NOAPI_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define dynamic sizing, no fixed liquidity percentage, staged entry/exit, risk cap, slippage/impact limits.

### 11. `MEV1_SANDWICH_SHIELD_DESIGN_NOAPI`
- module: `Sandwich / MEV Shield`
- mode: `NOAPI_PLAN`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Define private RPC/MEV protection, slippage cap, price impact limit, pre-trade simulation, min received, gas anomaly, sandwich detector.

### 12. `PAPER1_GENERIC_PAPER_SIMULATION_REBUILD_PLAN`
- module: `Paper Simulation`
- mode: `LOCKED_UNTIL_FOUNDATION_READY`
- write_allowed: `False`
- token_specific_logic: `False`
- goal: Return to paper only after warehouse/source/death/life/moonshot/risk/MEV foundations are designed.

## Decision
- current_state: `BACKBONE_RELOCKED_PAPER_PARKED`
- next_phase: `FW1_FORENSIC_WAREHOUSE_BACKBONE_DESIGN_NOAPI`

### Do Not Continue With
- P4D/P4E endless paper dry-runs
- token-specific quick fixes
- patch/yama to current engine or panel
- live or paper position writes
- API pressure test before pipe design

### Continue With
- Forensic Warehouse backbone design
- Source Gate design
- Birth/opening baseline design
- Two-source pipe pressure test plan: DexScreener + GeckoTerminal

## Errors
- none

## Warnings
- none

## Outputs
- json: `/root/tokenoskobi_clean_v1/data/tokenoskobi_v1_roadmap_relock_noapi.json`
- report: `/root/tokenoskobi_clean_v1/reports/LATEST_TOKENOSKOBI_V1_ROADMAP_RELOCK_NOAPI.md`
