# HOT Ingress Contract Dryrun Post Audit NOAPI

- stage: `HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_POST_AUDIT_NOAPI`
- generated_at_utc: `2026-07-08T13:46:52.168859+00:00`
- decision: `OK_HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_POST_AUDIT_SEALED`
- next_step: `HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_CANONICAL_BINDING_PLAN_NOAPI`

## Summary

- scenario_count: `8`
- synthetic_input_event_count: `137`
- route_counts: `{'CRITICAL_CANDIDATE': 1, 'DROP': 1, 'QUARANTINE': 2, 'WATCH': 4}`
- critical_candidate_count: `1`
- critical_alarm_count: `0`
- outbound_alarm_count: `0`
- fail_count: `0`
- warn_count: `0`

## Findings

- `OK` `DRYRUN_JSON_READ_OK`: Dryrun JSON okundu.
- `OK` `PLAN_JSON_READ_OK`: Plan JSON okundu.
- `OK` `SUMMARY_DOC_EXISTS`: Summary doc mevcut.
- `OK` `DRYRUN_DECISION_OK`: Dryrun decision OK.
- `OK` `AUTHORITY_BOUNDARY_OK`: NOAPI/authority boundary temiz.
- `OK` `SUMMARY_CHECKS_OK`: Dryrun summary beklenen değerlerle uyumlu.
- `OK` `RED_TEAM_RULES_LOCKED`: Red Team kuralları doğrulanmış.
- `OK` `NO_OUTBOUND_ALARM`: Hiçbir synthetic senaryo alarm üretmedi.
- `OK` `DRYRUN_CHECKS_OK`: Tüm dryrun check kayıtları OK.
