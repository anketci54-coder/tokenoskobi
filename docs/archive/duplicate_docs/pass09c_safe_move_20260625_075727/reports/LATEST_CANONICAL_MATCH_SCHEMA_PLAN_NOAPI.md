# CANONICAL_MATCH_SCHEMA_PLAN_NOAPI

STATUS=PASS

PURPOSE=

Define canonical output contract for Hunter Runtime.

---

## CANONICAL_TABLE

news_token_match_events

---

## INPUT

news_raw_feed_events

---

## PRODUCER

hunter_runtime

---

## REQUIRED_FIELDS

match_uid

news_uid

source_uid

token_uid

pair_uid

symbol

chain

match_type

match_confidence

match_score

match_reasons

evidence_text

created_at

---

## MATCH_TYPES

NO_REAL_ENTITY_MATCH

TOKEN_MATCH

PAIR_MATCH

CONTRACT_MATCH

NARRATIVE_MATCH

---

## CONFIDENCE

NONE

LOW

MEDIUM

HIGH

---

## CONSUMERS

priority_runtime

prosecutor_runtime

phase41_binding

---

## SAFETY

NOAPI=True

PLAN_ONLY=True

NO_DB_WRITE=True

NO_PANEL_WRITE=True

---

## RESULT

CANONICAL_MATCH_CONTRACT_DEFINED=True

