# UI_BUILD3_VIEW_MODEL_SNAPSHOT_DRYRUN_NOAPI

Timestamp: `20260517_192720`

## Final

- FINAL_STATUS=PASS
- FINAL_GATE=UI_BUILD3_VIEW_MODEL_SNAPSHOT_DRYRUN_READY
- DB_UNCHANGED=True

## Scope

Dry-run only.

No view model directory was created.  
No view model production file was written.  
The Token Yaşam VM draft exists only inside this phase JSON/report.

## Token Yaşam VM dry-run

Screen:

`token_yasam`

Departments:

1. Olay Yeri İnceleme
2. Adli Soruşturma
3. Şüpheliler / Arananlar
4. Klinik / Yoğun Bakım
5. Otopsi
6. Morg

## Global VM rules

- Six department cards stay summary-only.
- Every department has `detail_ref`.
- Every department has `motion_state_ref`.
- Motion is read-only from `motion_state_layer`.
- No source_uid means no motion.
- Primary body scroll is not allowed.
- Heavy data opens only in drawer/tab/detail surface.

## DB read summary

- integrity_check=ok
- quick_check=ok
- foreign_key_check_count=0
- known_table_count=38
- nonzero_known_table_count=12
- total_known_count=371

## Department source status

### Olay Yeri İnceleme

- data_status: `partial_source_available`
- existing_tables: `tokens, pairs, pair_birth_events, liquidity_birth_events, opening_price_events, opening_baseline_events`
- nonzero_tables: `tokens, pairs`
- detail_ref: `token_yasam.olay_yeri.detail`
- motion_state_ref: `motion.token_yasam.olay_yeri`

### Adli Soruşturma

- data_status: `partial_source_available`
- existing_tables: `tokens, pairs, source_gate_decisions, pair_verification_events, source_conflict_events, alias_conflict_events`
- nonzero_tables: `tokens, pairs, source_gate_decisions, pair_verification_events`
- detail_ref: `token_yasam.adli.detail`
- motion_state_ref: `motion.token_yasam.adli`

### Şüpheliler / Arananlar

- data_status: `partial_source_available`
- existing_tables: `tokens, pairs, tx_flow_events, buyer_seller_balance_events, holder_growth_events`
- nonzero_tables: `tokens, pairs`
- detail_ref: `token_yasam.supheliler.detail`
- motion_state_ref: `motion.token_yasam.supheliler`

### Klinik / Yoğun Bakım

- data_status: `partial_source_available`
- existing_tables: `tokens, pairs, life_signal_events, liquidity_alive_events, organic_volume_events, snapshot_strength_events, life_gate_decisions`
- nonzero_tables: `tokens, pairs`
- detail_ref: `token_yasam.klinik.detail`
- motion_state_ref: `motion.token_yasam.klinik`

### Otopsi

- data_status: `partial_source_available`
- existing_tables: `tokens, pairs, autopsy_evidence_events, rug_evidence_events, early_death_events, fast_decay_events`
- nonzero_tables: `tokens, pairs`
- detail_ref: `token_yasam.otopsi.detail`
- motion_state_ref: `motion.token_yasam.otopsi`

### Morg

- data_status: `partial_source_available`
- existing_tables: `tokens, pairs, morgue_route_decisions, stillborn_events, no_pair_memory`
- nonzero_tables: `tokens, pairs`
- detail_ref: `token_yasam.morg.detail`
- motion_state_ref: `motion.token_yasam.morg`

## Next phase

`UI_BUILD4_MOTION_STATE_SNAPSHOT_DRYRUN_NOAPI`
