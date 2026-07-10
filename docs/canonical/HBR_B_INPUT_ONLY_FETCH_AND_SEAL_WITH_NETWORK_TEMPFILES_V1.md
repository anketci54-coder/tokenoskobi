# HBR-B Input Only Fetch and Seal With Network Tempfiles V1

Generated UTC: 2026-07-10T08:51:08.267706+00:00

Decision: OK_HBR_B_INPUT_ONLY_FETCH_AND_SEAL_WITH_NETWORK_TEMPFILES

## Scope

Network allowed. Production DB write forbidden. Outcome/result fields forbidden.

## Sealed input

```text
input_count = 55
in_locked_window_count = 0
outside_locked_window_or_undated_count = 55
skipped_count = 0
input_manifest_sha256 = 98ac79dc325d5f433ca7921978537dce5774484669976a78e9331dcd352e431c
items_jsonl_sha256 = 132e5a2a80debe3f0eb625570639b5a84b8bc4e129934596195a1e3d110bdc5c
Tempfiles
runtime/hbr_blind_replay/hbr_b_input_manifest_v1.json
runtime/hbr_blind_replay/hbr_b_input_only_items_v1.jsonl
runtime/hbr_blind_replay/hbr_b_input_only_skipped_v1.jsonl
Forbidden before prediction seal
outcome_label
price_after
future_return_pct
result
win_loss
success_failure
future_price
post_event_price_change
score_comparison
Next

HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI
