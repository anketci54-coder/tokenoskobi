# CORE CLEAN5D CANONICAL PANEL REFERENCE POLICY PLAN NOAPI

- created_at_utc: `2026-05-11T16:03:05.647794+00:00`
- final_status: **PASS**
- scope: canonical panel/reference policy planı; gerçek dosya işlemi yok.

## Karar
- Aktif referanslı legacy/source path korunacak.
- Cleanup allowed now: `False`
- Dosya silme/taşıma/arşivleme yok.

## Source Problem
- source_path: `/root/tokenoskobi_clean_v1/_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096`
- target_path: `/root/tokenoskobi_clean_v1/archive/unused_phase_outputs_AFTER_APPROVAL/20260511_162447/_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096`
- reference_rows: `48`
- canonical_class_counts: `{'CANONICAL_TOOLS': 3, 'CANONICAL_RUNNER': 2, 'CANONICAL_DATA': 43}`
- old_class_counts: `{'TOOL_CODE_REFERENCE': 3, 'CORE_RUNNER_CRITICAL_REFERENCE': 2, 'DATA_POLICY_OR_STATE_REFERENCE': 43}`

## Canonical Policy Rules
- Aktif referanslı path temizlenmez.
- Runner, systemd, data, tools veya public panel referansı varsa cleanup bloklanır.
- Legacy phase output ancak aktif referans 0 ise arşiv dry-run adayı olabilir.
- Path özel yama yapılmaz; önce genel canonical resolver/manifest policy oluşturulur.
- Gerçek dosya hareketi için önce noapi plan, dry-run, açık onay ve post-audit gerekir.
- Silme yok; yalnızca geri alınabilir arşiv yaklaşımı.

## Future Requirements
- Panel active root tek yerden okunmalı.
- Legacy panel workdir doğrudan referans olmamalı.
- Data/policy dosyalarında path referansı varsa generic path alias/resolver kullanılmalı.
- Reference migration planı path-specific patch değil, tüm panel pathleri için genel manifest yaklaşımı olmalı.
- Her migration sonrası post-audit DB/runner/service/timer/paper-live guard çalışmalı.

## Bu Fazda Yapılmayanlar
- Dosya silme: `False`
- Dosya taşıma: `False`
- Dosya arşivleme: `False`
- DB mutation: `False`
- API call: `0`
- Model training: `False`
- Paper/live: `False`

## Safety
- health_ok: `True`
- runner_compile_ok: `True`
- paper_live_zero: `True`
- db_counts_unchanged: `True`
- db_unchanged: `True`
- runner_unchanged: `True`
- service_unchanged: `True`
- timer_unchanged: `True`

## Outputs
- policy_json: `/root/tokenoskobi_clean_v1/_core_clean5d_canonical_panel_reference_policy_plan_noapi/20260511_190305/core_clean5d_canonical_panel_reference_policy_plan_noapi_canonical_reference_policy.json`
- reference_map_jsonl: `/root/tokenoskobi_clean_v1/_core_clean5d_canonical_panel_reference_policy_plan_noapi/20260511_190305/core_clean5d_canonical_panel_reference_policy_plan_noapi_reference_map.jsonl`
- protected_paths_jsonl: `/root/tokenoskobi_clean_v1/_core_clean5d_canonical_panel_reference_policy_plan_noapi/20260511_190305/core_clean5d_canonical_panel_reference_policy_plan_noapi_protected_paths.jsonl`

## Next
- `NEWS_SOURCE_ENGINE_GENERAL_POLICY_IMPLEMENTATION_PLAN_NOAPI`

## Errors
- none

## Warnings
- none
