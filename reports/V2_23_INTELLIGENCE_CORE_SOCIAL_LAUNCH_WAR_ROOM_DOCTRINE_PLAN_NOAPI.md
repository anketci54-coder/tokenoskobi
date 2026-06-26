# V2_23 Intelligence Core / Social Launch / War Room Doctrine

TASK=V2_23_INTELLIGENCE_CORE_SOCIAL_LAUNCH_WAR_ROOM_DOCTRINE_PLAN_NOAPI
MODE=PLAN_ONLY_DOCTRINE_MANIFEST_NOAPI
STAMP_UTC=2026-06-26T05:11:32.001709+00:00
CANONICAL_PARENT=de00c380849b808d0f3536d278191e6abf318c55

## Core Thesis

Tokenoskobi is a living market intelligence organism.
Intelligence is the primary strength.
Panel final design is deferred.
User sees results first, engines later as audit evidence.

## Locked Flags

INTELLIGENCE_CORE_IS_PRIMARY=true
SOCIAL_RADAR_REQUIRED=true
TELEGRAM_DISCORD_WATCH_REQUIRED=true
LAUNCH_INTELLIGENCE_REQUIRED=true
AIRDROP_ICO_IDO_RESEARCH_REQUIRED=true
MARKET_SOURCE_VERIFICATION_REQUIRED=true
WHALE_NETWORK_INTELLIGENCE_REQUIRED=true
ONCHAIN_CONFIRMATION_REQUIRED=true
TEAM_WEBSITE_FORENSICS_REQUIRED=true

ECHO_CHAMBER_PREVENTION_REQUIRED=true
NORMALIZED_INDEPENDENCE_FACTOR_REQUIRED=true
HARD_BLOCK_BEFORE_SCORE=true
EXPLAINABLE_SCORE_REQUIRED=true

ATIS_POLIGONU_IS_SIMULATION_ONLY=true
WAR_ROOM_IS_REAL_ACTION_ARCHITECTURE=true
VUR_KAC_IS_WAR_ROOM_TACTICAL_MODE=true

PANEL_FINAL_DESIGN_DEFERRED=true
CHAT_FIRST_RESULT_PANEL_DIRECTION=true
DETAILS_ARE_AUDIT_NOT_MAIN_UI=true

TRADE_AUTHORITY=0
WALLET_AUTHORITY=0
LIVE_TRADE=0
AUTO_PATCH=0
HUMAN_APPROVAL_REQUIRED=1

## Intelligence Core

News Intelligence
Social Radar
Telegram Watcher
Discord Watcher
X/Twitter Watch
Launch Intelligence
Airdrop / ICO / IDO Research
Market Source Verification
CoinGecko / CoinMarketCap / Coinbase verification
Whale Wallet Network Intelligence
Onchain Confirmation
Team Verification
Website Forensics
Source Trust Engine
Rumor Verification Engine
Narrative Early Warning

## Atis Poligonu

Atis Poligonu is simulation only.
No real money.
No live order.
No wallet signing.

Scope:
paper trade
simulation
missed opportunity analysis
entry exit replay
SL TP hypothesis testing
strategy learning

## Savas Alani

Savas Alani is real action architecture.
Current authority is zero.

TRADE_AUTHORITY=0
WALLET_AUTHORITY=0
LIVE_TRADE=0

## Vur-Kac

Vur-Kac is a War Room tactical mode.
While live authority is zero, it may only be rehearsed in Atis Poligonu.

Required:
hard_block_absent
net_potential_positive
exit_safety_sufficient
mev_sandwich_risk_bounded
sl_tp_defined
kill_switch_available

## Echo Chamber Prevention

IndependenceFactor =
min(1.0, 0.40 + (log2(independent_source_count + 1) / log2(6)) * 0.60 * min(1.0, diversity_score))

0.40 <= IndependenceFactor <= 1.00

DiversityScore = min(1.0, unique_platform_count / 5)

Ten Telegram channels repeating the same message are not ten independent confirmations.

## Hard Block First

Hard block runs before scoring.

Hard blocks:
HONEYPOT
SELL_DISABLED
BLACKLIST_TRAP
UNLIMITED_MINT_ACTIVE
FAKE_CONTRACT_MISMATCH
CONFIRMED_SCAM_DEPLOYER
LP_OWNER_WITHDRAWABLE_CRITICAL
PROXY_UPGRADE_TRAP_CRITICAL

If hard block exists:
Decision=RED
FinalScore=0

## Final Score

PositiveScore =
SourceScore * 0.15 +
TeamScore * 0.15 +
OnchainScore * 0.20 +
LiquidityScore * 0.15 +
WhaleScore * 0.15 +
SimulationScore * 0.20

FinalScore = clamp(PositiveScore - RiskPenalty, 0, 100)

Decision:
85-100 UYGUN
70-84 POLIGONA_GONDER
55-69 IZLE
40-54 ZAYIF_BEKLE
0-39 RED

## Vur-Kac Score

VurKacScore =
LiquidityMomentum * 0.25 +
SwapPressure * 0.20 +
ExitSafety * 0.25 +
MEVRiskInverse * 0.15 +
NetPotential * 0.15

VurKac=YES only if:
HardBlock=false
ExitSafety sufficient
NetPotential > 0
VurKacScore >= 70

## V2_24 Requirement

No scoring DB write before Decision Audit Log Contract.

Minimum audit fields:
decision_id
token_uid
chain
contract_address
decision_time
decision_type
final_score
source_score
team_score
onchain_score
liquidity_score
whale_score
simulation_score
risk_penalty
hard_block_triggered
hard_block_reasons
source_count
independent_source_count
unique_platform_count
diversity_score
independence_factor
evidence_level
echo_chamber_flag
vur_kac_score
vur_kac_decision
poligon_decision
short_reason
audit_json
created_at

## Final Doctrine

Intelligence sees first.
Onchain confirms.
Risk gates eliminate.
Atis Poligonu rehearses.
Savas Alani acts only with authority.
Vur-Kac is a War Room tactical mode.
Panel design is deferred.
Details are audit, not main UI.
