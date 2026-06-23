# V2_02_CMP_V1_MESSAGE_PROTOCOL_PLAN_NOAPI

UTC: 2026-06-23T17:51:10Z

## Amaç

V2 sistem orduları arasında kullanılacak CMP_V1 mesaj protokolünü planlamak.

CMP_V1 sistemin sinir ağıdır.

Bu adım NOAPI / plan-only çalışır.

Bu adım aktif runtime değildir.

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

V2_01_GRAY_AREA_PARAM_REGISTRY_PUSHED_VERIFIED=true

V1_STATUS=CLOSED_VERIFIED_GITHUB_SEALED

PROJECT_STATUS=TOKENOSKOBI_V1_FINAL_CLOSED

V1_BASELINE_IS_REFERENCE_ONLY=true

V2_MUST_NOT_MUTATE_V1_BASELINE=true

## Red Team Uyarısı ve Cevap

Uyarı:

CMP_V1 üzerinde çok fazla opsiyonel alan ve nested yapı olursa her ordu mesajı farklı parse eder.

Bu deterministik yapıyı bozar.

Nested JSON hot path CPU yükünü artırır.

Cevap:

CMP_FLAT_HEADER_REQUIRED=true

CMP_FIXED_HEADER_ORDER_REQUIRED=true

CMP_OPTIONAL_HEADER_FIELDS_FORBIDDEN=true

CMP_NESTED_HOT_PATH_HEADER_FORBIDDEN=true

CMP_PAYLOAD_TYPE_REQUIRED=true

CMP_PAYLOAD_SIZE_BYTES_REQUIRED=true

CMP_UNKNOWN_FIELD_POLICY=REJECT_MESSAGE

CMP_MISSING_FIELD_POLICY=REJECT_MESSAGE

CMP_FAIL_CLOSED_ON_PROTOCOL_VIOLATION=true

## CMP_V1 Ana Kural

Mesaj önce header ile tanınır.

Payload ancak header validation geçerse okunur.

Header flat ve sabit sıralıdır.

Header içinde nested obje yoktur.

Hot path üzerinde dosya okuma yoktur.

Hot path üzerinde registry JSON parse yoktur.

Runtime registry parametrelerini RAM snapshot üzerinden okur.

## Header Zorunlu Alanları

cmp_version

message_id

message_type

payload_type

payload_size_bytes

created_at_utc

expires_at_utc

ttl_sec

source_army

target_army

source_component

target_component

priority_class

cost_quota_units

context_version

market_regime

registry_version

registry_sha

idempotency_key

correlation_id

source_trust_score

evidence_count

risk_flag_bitmap

live_execution_forbidden

## PayloadType Allowlist

HUNTER_ALERT_V1

PROSECUTOR_EVIDENCE_REQUEST_V1

RISK_DECISION_READONLY_V1

SIMULATED_DECISION_V1

REVIEW_QUEUE_ITEM_V1

MARKET_CONTEXT_V1

KILL_SWITCH_STATE_V1

OUTCOME_MEMORY_EVENT_V1

## MessageType Allowlist

ALERT

EVIDENCE_REQUEST

READONLY_DECISION

SIMULATED_DECISION

REVIEW_REQUEST

CONTEXT_UPDATE

KILL_SWITCH_STATE

OUTCOME_EVENT

## Army Allowlist

HUNTER_ARMY

PROSECUTOR_ARMY

COMMAND_ARMY

CONTEXT_ARMY

LEARNING_ARMY

REVIEW_ARMY

KILL_SWITCH_ARMY

## Validation Sırası

1. CHECK_MESSAGE_SIZE_LIMIT

2. CHECK_HEADER_REQUIRED_FIELDS

3. CHECK_NO_UNKNOWN_HEADER_FIELDS

4. CHECK_CMP_VERSION

5. CHECK_MESSAGE_TYPE_ALLOWLIST

6. CHECK_PAYLOAD_TYPE_ALLOWLIST

7. CHECK_PAYLOAD_SIZE_BYTES

8. CHECK_TTL_NOT_EXPIRED

9. CHECK_COST_QUOTA

10. CHECK_CONTEXT_VERSION_PRESENT

11. CHECK_REGISTRY_SHA_PRESENT

12. CHECK_IDEMPOTENCY_KEY

13. CHECK_SOURCE_TRUST

14. CHECK_LIVE_EXECUTION_FORBIDDEN

15. CHECK_KILL_SWITCH_STATE

16. CHECK_PAYLOAD_FLAT_CONTRACT

17. ROUTE_OR_REJECT

## Güvenlik Guardları

CMP_TTL_REQUIRED=true

CMP_COST_QUOTA_REQUIRED=true

CMP_CONTEXT_VERSION_REQUIRED=true

CMP_REGISTRY_SHA_REQUIRED=true

CMP_IDEMPOTENCY_REQUIRED=true

CMP_SOURCE_TRUST_REQUIRED=true

CMP_EVIDENCE_REFS_REQUIRED_FOR_DECISION=true

CMP_KILL_SWITCH_AWARENESS_REQUIRED=true

CMP_REPLAY_PROTECTION_REQUIRED=true

CMP_DEDUP_REQUIRED=true

CMP_FAIL_CLOSED_ON_VALIDATION_ERROR=true

CMP_POISON_MESSAGE_QUARANTINE_REQUIRED=true

## Yetki Kilitleri

TRADE_AUTHORITY=0

WALLET_AUTHORITY=0

LIVE_TRADE=0

AUTO_APPLY=0

AUTO_PATCH=0

HARD_BLOCK_BYPASS=0

MESSAGE_BUS_LIVE_EXECUTION_FORBIDDEN=true

RISK_DECISION_READONLY_ONLY=true

LIVE_EXECUTE_PAYLOAD_FORBIDDEN=true

WALLET_PAYLOAD_FORBIDDEN=true

SECRET_PAYLOAD_FORBIDDEN=true

## Manifesto Bağlantısı

Şimşek kadar hızlı:

Header flat ve sabittir.

Runtime payload_size_bytes üzerinden memory ayırır.

Payload, header geçmeden decode edilmez.

Balyoz kadar güçlü:

Mesaj kanıt, kaynak güveni, context version ve risk bitmap taşır.

Kale kadar güvenli:

TTL, quota, idempotency, registry SHA ve kill switch awareness zorunludur.

Karınca kadar ekonomik:

Her mesaj cost_quota_units taşır.

Prosecutor sonsuz validation döngüsüne sokulamaz.

## CMP Sözleşme Dosyası

CMP_CONTRACT=data/protocol/cmp_v1_message_protocol_contract_plan_noapi.json

CMP_CONTRACT_SHA=a45ca3040b296c4f05802bc11cd8f972951e4b80a1e801212446a23d1154cc34

## Koruma

CURRENT_HEAD=ac5b445

REMOTE_HEAD=ac5b445

AHEAD_BEHIND=0 0

V2_00_SHA=e64dc5976565f4f1d16906898f25df4bc729ff5062bade52612c5d7073ae8096

V2_00_5_SHA=92704116346b96f19d5ed77148e22b66861117f3185d30177056db43ff3ccb71

V2_01_SHA=6a5c96b1dd527818b7b9a980e2796b28c590425d3c332c97187b71fabb9070f6

REGISTRY_CONTRACT_SHA=b8df6b150a2349cdd618f0480168dc8e4f96ef5fa5908a1ba30e847b6c16fe69

DB_SHA=ad60d581491833c59d78c24d8b44d5280af3efd8cad4667c7b104e46b68f1ee5

PANEL_SHA=d15c147cb81f46b3bb3828a92ea861cf6d9b6807d16932f7d6e9c8a8fb878ca9

DB_SHA_CHANGED=false

PANEL_SHA_CHANGED=false

PROTECTED_DIFF_EMPTY=true

DB_INTEGRITY=ok

DB_QUICK=ok

DB_FK_COUNT=0

## Sonraki Güvenli Adım

COMMIT_PUSH_V2_02_CMP_V1_MESSAGE_PROTOCOL_PLAN

## Karar

CMP_V1_MESSAGE_PROTOCOL_PLAN_ACCEPTED_READY_FOR_COMMIT_PUSH

## Final Gate

PASS_V2_02_CMP_V1_MESSAGE_PROTOCOL_PLAN_NOAPI
