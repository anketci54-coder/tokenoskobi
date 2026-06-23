# V2_01_GRAY_AREA_PARAM_REGISTRY_PLAN_NOAPI

UTC: 2026-06-23T17:44:25Z

## Amaç

V2 canlı parametrelerinin anayasal kayıt defterini planlamak.

Bu adım NOAPI / plan-only çalışır.

Bu adım aktif runtime registry değildir.

Bu adım DB yazmaz.

Bu adım panel yazmaz.

Bu adım runtime açmaz.

Bu adım provider/API çağırmaz.

Bu adım AI çağırmaz.

Bu adım trade/wallet açmaz.

Bu adım commit/push yapmaz.

## Ön Şartlar

V2_00_CHARTER_PUSHED_VERIFIED=true

V2_00_5_V1_FROZEN_BASELINE_PUSHED_VERIFIED=true

V1_STATUS=CLOSED_VERIFIED_GITHUB_SEALED

PROJECT_STATUS=TOKENOSKOBI_V1_FINAL_CLOSED

V1_BASELINE_IS_REFERENCE_ONLY=true

V1_PHYSICAL_LOCK_NOT_APPLIED=true

V2_MUST_NOT_MUTATE_V1_BASELINE=true

## Registry Ana Kuralı

Gray Area Param Registry sistemin refleks eşiklerini tanımlar.

Registry kara kutu değildir.

Her parametre sebep, sınır, risk ve yetki bilgisi taşır.

Registry hot path üzerinde dosya okumaz.

Runtime her mesajda JSON parse etmez.

Runtime başlangıçta veya açık güvenli reload ile registry'yi RAM'e alır.

Hot path sadece read-only RAM snapshot okur.

## Red Team Uyarısı ve Cevap

Uyarı:

Tek JSON dosyası her işlemde parse edilirse Şimşek Kadar Hızlı ilkesi bozulur.

Cevap:

HOT_PATH_FILE_IO_FORBIDDEN=true

PER_MESSAGE_JSON_PARSE_FORBIDDEN=true

REGISTRY_LOAD_POLICY=LOAD_ON_START_OR_EXPLICIT_SAFE_RELOAD_ONLY

HOT_PATH_ACCESS_POLICY=READ_ONLY_RAM_SNAPSHOT

REGISTRY_MEMORY_SHAPE=FLAT_KEY_VALUE_MAP

MMAP_FUTURE_ALLOWED=true

## Mimari Kural

Registry source-of-truth olabilir.

Runtime hot path source-of-truth değildir.

Hot path registry dosyasına gitmez.

Hot path sadece immutable in-memory snapshot okur.

Parametre değişimi runtime ortasında gizlice uygulanmaz.

Parametre reload sadece explicit safe reload ile olur.

Registry SHA ve version olmadan aktif sayılmaz.

## Registry Aileleri

SPEED_LIMITS

BUDGET_LIMITS

TTL_FRESHNESS

SOURCE_TRUST

DATA_QUALITY

UNCERTAINTY_LIFETIME

ANALYSIS_COST_LIMITER

ALPHA_PRIORITY_BYPASS

CONTEXTUAL_RESET

REVIEW_QUEUE_LIMITER

CMP_V1_MESSAGE_PROTOCOL

OUTCOME_MEMORY_TIME_DECAY

KILL_SWITCH

AUTHORITY_LOCKS

## Planlanan Parametre Alanları

param_key

family

value_type

default_value

min_value

max_value

unit

runtime_scope

hot_path_allowed

reload_policy

authority_level

reason

risk_if_too_low

risk_if_too_high

evidence_required_for_change

owner

created_in_phase

active

version

## Kritik Parametreler

speed.max_hot_path_ms

speed.max_candidate_route_ms

budget.max_free_calls_per_cycle

budget.max_paid_calls_per_cycle

budget.alpha_priority_paid_call_ceiling

ttl.default_market_data_sec

ttl.new_launch_data_sec

ttl.high_volatility_sec

ttl.risk_sellability_sec

trust.min_source_trust_for_decision

quality.min_evidence_count_for_decision

uncertainty.max_suspicion_age_sec

uncertainty.latent_uncertainty_expiry_sec

analysis.max_deep_scan_cost_units

alpha.shadow_signal_bypass_threshold

alpha.bypass_requires_ledger

context.market_regime_version_required

context.reset_on_regime_change

review.max_queue_items

review.min_intersection_score

cmp.message_ttl_sec

cmp.max_cost_quota_per_message

cmp.context_version_required

cmp.idempotency_required

outcome.time_decay_half_life_days

kill_switch.message_bus_hard_stop_required

authority.live_execution_forbidden

## Manifesto Bağlantısı

Şimşek kadar hızlı:

Hot path dosya okumaz.

Hot path JSON parse etmez.

Hot path read-only RAM snapshot okur.

Balyoz kadar güçlü:

Karar eşikleri explicit, versioned ve kanıt bağlıdır.

Kale kadar güvenli:

Parametre değişimi review, audit, commit ve rollback gerektirir.

Karınca kadar ekonomik:

Bütçe, quota, dedup, cache ve paid-call gerekçesi registry içinde görünürdür.

## Yetki Kilitleri

TRADE_AUTHORITY=0

WALLET_AUTHORITY=0

LIVE_TRADE=0

AUTO_APPLY=0

AUTO_PATCH=0

HARD_BLOCK_BYPASS=0

PARAM_CHANGE_REQUIRES_HUMAN_REVIEW=true

MESSAGE_BUS_LIVE_EXECUTION_FORBIDDEN=true

## Registry Mutasyon Kuralları

PARAM_CHANGE_REQUIRES_REVIEW=true

PARAM_CHANGE_REQUIRES_AUDIT=true

PARAM_CHANGE_REQUIRES_COMMIT=true

PARAM_CHANGE_REQUIRES_ROLLBACK_PLAN=true

PARAM_CHANGE_CANNOT_MUTATE_V1_BASELINE=true

PARAM_CHANGE_CANNOT_ENABLE_TRADE=true

PARAM_CHANGE_CANNOT_ENABLE_WALLET=true

PARAM_CHANGE_CANNOT_BYPASS_HARD_BLOCK=true

## Koruma

CURRENT_HEAD=c42ca3c

REMOTE_HEAD=c42ca3c

AHEAD_BEHIND=0 0

V2_00_SHA=e64dc5976565f4f1d16906898f25df4bc729ff5062bade52612c5d7073ae8096

V2_00_5_SHA=92704116346b96f19d5ed77148e22b66861117f3185d30177056db43ff3ccb71

REGISTRY_CONTRACT_SHA=a9e05962cbb5ac83a6d6e62b4b2a2a1b7480f14dce7e540da238b2c4af3a84d6

DB_SHA=ad60d581491833c59d78c24d8b44d5280af3efd8cad4667c7b104e46b68f1ee5

PANEL_SHA=d15c147cb81f46b3bb3828a92ea861cf6d9b6807d16932f7d6e9c8a8fb878ca9

DB_SHA_CHANGED=false

PANEL_SHA_CHANGED=false

PROTECTED_DIFF_EMPTY=true

DB_INTEGRITY=ok

DB_QUICK=ok

DB_FK_COUNT=0

## Sonraki Güvenli Adım

COMMIT_PUSH_V2_01_GRAY_AREA_PARAM_REGISTRY_PLAN

## Karar

GRAY_AREA_PARAM_REGISTRY_PLAN_ACCEPTED_READY_FOR_COMMIT_PUSH

## Final Gate

PASS_V2_01_GRAY_AREA_PARAM_REGISTRY_PLAN_NOAPI


## Red Team Pre-Commit Hard Bound Fix

REGISTRY_POISONING_SURFACE=true

RISK=Parametre sınır ihlali hot path kilitleyebilir veya güvenlik refleksini bozabilir.

FIX=HARD_MIN_MAX_DEFAULT_AND_LOADER_VALIDATION

PARAM_BOUNDS_ENFORCED_ON_LOAD=true

MISSING_MIN_MAX_BLOCKS_REGISTRY_ACTIVATION=true

OUT_OF_BOUNDS_VALUE_BLOCKS_REGISTRY_ACTIVATION=true

FAIL_CLOSED_ON_BOUNDS_VIOLATION=true

HOT_PATH_USES_VALIDATED_RAM_SNAPSHOT_ONLY=true

LAST_GOOD_SNAPSHOT_REQUIRED=true

ROLLBACK_REQUIRED=true

ALL_PLANNED_PARAMS_HAVE_BOUNDS=true

PLANNED_PARAM_COUNT=27

UPDATED_REGISTRY_CONTRACT_SHA=b8df6b150a2349cdd618f0480168dc8e4f96ef5fa5908a1ba30e847b6c16fe69
