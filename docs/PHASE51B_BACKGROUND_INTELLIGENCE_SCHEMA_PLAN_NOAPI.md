# PHASE51B_BACKGROUND_INTELLIGENCE_SCHEMA_PLAN_NOAPI

## STATUS

PLAN_ONLY

## PURPOSE

Define the canonical schema for the Background Intelligence Officer.

This schema stores intelligence candidates only.

No trade authority.
No policy authority.
No risk override authority.

## TABLES

### intelligence_case_v1

case_id TEXT PRIMARY KEY
source_class TEXT
source_name TEXT
source_url_hash TEXT
event_type TEXT
event_subtype TEXT
trust_tier TEXT
confidence REAL
severity TEXT
summary TEXT
created_utc TEXT

### intelligence_evidence_v1

evidence_id TEXT PRIMARY KEY
case_id TEXT
evidence_type TEXT
evidence_hash TEXT
evidence_ref TEXT
created_utc TEXT

### intelligence_pattern_v1

pattern_id TEXT PRIMARY KEY
pattern_family TEXT
pattern_name TEXT
pattern_version TEXT
pattern_summary TEXT
first_seen_utc TEXT

### intelligence_candidate_v1

candidate_id TEXT PRIMARY KEY
candidate_type TEXT

candidate_type_enum:
- threat_memory
- opportunity_memory
- prosecutor_review
- fusion_context
- harekat_subayi
- launch_radar
- mev_pattern
- scam_pattern
- exploit_pattern

candidate_confidence REAL
candidate_priority TEXT
candidate_status TEXT

### intelligence_brief_v1

brief_id TEXT PRIMARY KEY
brief_type TEXT
brief_title TEXT
brief_summary TEXT
generated_utc TEXT

## TRUST TIERS

TIER_0_UNTRUSTED
TIER_1_LOW
TIER_2_MEDIUM
TIER_3_HIGH
TIER_4_VERIFIED

## EVENT FAMILIES

NEWS_EVENT
SOCIAL_EVENT
LAUNCH_EVENT
ICO_EVENT
IDO_EVENT
AIRDROP_EVENT
SCAM_EVENT
RUG_EVENT
HONEYPOT_EVENT
MEV_EVENT
SANDWICH_EVENT
EXPLOIT_EVENT
DEX_EVENT
COUNTER_INTELLIGENCE_EVENT

## AUTHORITY LOCKS

TRADE_AUTHORITY=0
AI_AUTHORITY=0
AUTO_BLOCK=0
AUTO_APPLY=0
RISK_OVERRIDE=0

## MEMORY BINDINGS

THREAT_MEMORY_BINDING=true
OPPORTUNITY_MEMORY_BINDING=true
DECISION_MEMORY_BINDING=true
PROSECUTOR_BINDING=true
FUSION_BINDING=true

## CONSTITUTIONAL_GATE_V1

SPEED_NEVER_DOWN=true
SECURITY_NEVER_DOWN=true
POWER_NEVER_DOWN=true
DENGE_DENGE_DENGE=true

## NEXT_SAFE_STEP

PHASE51C_BACKGROUND_INTELLIGENCE_TEMPDB_DRYRUN_NOAPI

## FINAL_GATE

PASS_PHASE51B_BACKGROUND_INTELLIGENCE_SCHEMA_PLAN_NOAPI
