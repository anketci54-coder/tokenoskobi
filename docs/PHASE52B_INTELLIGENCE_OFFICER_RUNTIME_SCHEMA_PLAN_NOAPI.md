# PHASE52B_INTELLIGENCE_OFFICER_RUNTIME_SCHEMA_PLAN_NOAPI

## STATUS

PLAN_ONLY

## PURPOSE

Define runtime schema for Intelligence Officer.

No DB apply.
No TempDB.
No Runtime apply.

Schema planning only.

## TABLES

### intelligence_source_v1

source_id TEXT PRIMARY KEY
source_name TEXT
source_class TEXT
trust_tier TEXT
enabled INTEGER
created_utc TEXT

### intelligence_event_v1

event_id TEXT PRIMARY KEY
source_id TEXT
event_family TEXT
event_type TEXT
event_hash TEXT
event_summary TEXT
trust_score REAL
severity TEXT
created_utc TEXT

### intelligence_entity_v1

entity_id TEXT PRIMARY KEY
entity_type TEXT
entity_name TEXT
entity_hash TEXT
created_utc TEXT

### intelligence_event_entity_v1

link_id TEXT PRIMARY KEY
event_id TEXT
entity_id TEXT

### intelligence_candidate_v2

candidate_id TEXT PRIMARY KEY
candidate_type TEXT
candidate_priority TEXT
candidate_confidence REAL
candidate_status TEXT
created_utc TEXT

### intelligence_brief_v2

brief_id TEXT PRIMARY KEY
brief_type TEXT
brief_title TEXT
brief_summary TEXT
generated_utc TEXT

### intelligence_counterintel_v1

counterintel_id TEXT PRIMARY KEY
signal_type TEXT
signal_summary TEXT
confidence REAL
created_utc TEXT

## INDEXES

idx_source_class
idx_source_trust

idx_event_family
idx_event_type
idx_event_hash

idx_entity_type
idx_entity_hash

idx_candidate_type
idx_candidate_priority

idx_brief_type

idx_counterintel_signal

## EVENT_FAMILIES

NEWS_EVENT
SOCIAL_EVENT
SCAM_EVENT
RUG_EVENT
HONEYPOT_EVENT
MEV_EVENT
SANDWICH_EVENT
EXPLOIT_EVENT
LAUNCH_EVENT
ICO_EVENT
IDO_EVENT
AIRDROP_EVENT
COUNTER_INTELLIGENCE_EVENT

## MEMORY_BINDINGS

THREAT_MEMORY_BINDING=true
OPPORTUNITY_MEMORY_BINDING=true
DECISION_MEMORY_BINDING=true
PROSECUTOR_BINDING=true
FUSION_BINDING=true
HAREKAT_SUBAYI_BINDING=true

## AUTHORITY_LOCKS

TRADE_AUTHORITY=0
AI_AUTHORITY=0
AUTO_BLOCK=0
AUTO_APPLY=0
AUTO_POLICY_EDIT=0
RISK_OVERRIDE=0

## HOT_PATH_LOCKS

HOT_PATH_BLOCKS=false
EXECUTION_PATH_TOUCH=false

## NEXT_SAFE_STEP

PHASE52C_INTELLIGENCE_OFFICER_TEMPDB_DRYRUN_NOAPI

## FINAL_GATE

PASS_PHASE52B_INTELLIGENCE_OFFICER_RUNTIME_SCHEMA_PLAN_NOAPI
