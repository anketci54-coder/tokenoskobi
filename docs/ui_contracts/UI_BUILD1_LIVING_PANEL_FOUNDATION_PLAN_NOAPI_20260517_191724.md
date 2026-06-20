# Living Panel Foundation Plan v1

Phase: `UI_BUILD1_LIVING_PANEL_FOUNDATION_PLAN_NOAPI`  
Timestamp: `20260517_191724`

## 1. Amaç

Bu faz panel değiştirmez. Amaç, yaşayan panel altyapısının ilk uygulama planını kilitlemektir.

Ana kural:

**No panel implementation before data/view-model/motion/fit gates are testable.**

## 2. Foundation objective

- Mevcut çalışan panel ruhunu bozmadan living UI altyapısı kurmak.
- Panel içinde fake animasyon üretmemek.
- Tüm hareketleri `motion_state_layer` üzerinden okumak.
- Her ekranı viewport-fit zorunluluğuna bağlamak.
- Veriyi tek canonical source’dan `view_model` olarak göstermek.
- İlk hedefte aktif 8096’ya dokunmadan preview/dry-run planı hazırlamak.

## 3. Foundation layers

### canonical_data_layer

DB/source reality haritalanacak. Bu fazda DB write yok.

### view_model_layer

Future dir:

`/root/tokenoskobi_clean_v1/data/view_models`

Planlanan view model dosyaları:

- main_panel_vm.json
- token_yasam_vm.json
- haber_panel_vm.json
- whale_panel_vm.json
- risk_panel_vm.json
- paper_panel_vm.json

Kural:

Panel içinde hardcoded production metric yok.

### motion_state_layer

Future dir:

`/root/tokenoskobi_clean_v1/data/motion_states`

Planlanan dosyalar:

- motion_state_snapshot.json
- motion_state_policy.json

Kural:

**No source_uid, no motion.**

### screen_fit_layer

Future dir:

`/root/tokenoskobi_clean_v1/data/screen_fit`

Planlanan dosyalar:

- fit_profile_laptop.json
- fit_profile_desktop.json
- fit_test_result.json

Kural:

Primary body scroll varsa FIT_FAIL.

### visual_component_layer

Future dir:

`/root/tokenoskobi_clean_v1/ui_components`

Reusable components:

- living_badge
- truth_motion_icon
- viewport_shell
- detail_drawer
- radar_canvas
- token_status_row
- trade_control_strip

Kural:

Components only read `view_model` and `motion_state`.

## 4. İlk hedef ekran

İlk hedef:

`Token Yaşam Merkezi`

Sebep:

Logo placement ve department layout son çalışmada stabilize edildi. Living UI foundation testi için en uygun ilk alan.

Source baseline:

`/root/tokenoskobi_clean_v1/accepted_baselines/token_yasam_merkezi_final_panel64_20260515_175146`

Accepted logo preview:

`/root/tokenoskobi_clean_v1/panel_previews/tokenyasam_left_logo_circle_bigger_cleanbg_latest`

Master asset pack:

`/root/tokenoskobi_clean_v1/panel_assets/token_yasam_master_pack_v1`

Constraints:

- Layout rebuild yok.
- Active 8096 yok.
- Haber final 8101 yok.
- Token Yaşam final 8102 yok.
- Sadece ayrı approval sonrası preview.
- Kabul edilen yuvarlak logo placement korunabilir.
- 6 departman kartı summary-only kalır.
- Detaylar drawer/tab içinde açılır.
- Fake department pulse yok.

## 5. İlk motion truth hedefleri

### Klinik

Allowed motion:

`heartbeat pulse`

Required source:

`clinical_watch`

No data:

`static icon`

### Morg

Allowed motion:

`cold slow breath`

Required source:

`morg_status`

No data:

`static icon`

### Otopsi

Allowed motion:

`slow scan`

Required source:

`active autopsy_status`

No data:

`static icon`

### Olay Yeri

Allowed motion:

`short alarm pulse`

Required source:

`fresh event`

No data:

`static icon`

## 6. Koddan önce implementation gate

Panel kodu ancak şu şartlarla başlayabilir:

- Contracts 1-5 exist.
- Target screen source baseline exists.
- View model schema is defined.
- Motion source requirements are defined.
- Fit rules are testable.
- Preview directory is separate.
- No active apply.
- No fake data.
- No yama.
- No product-specific hack.

## 7. Hard stop conditions

- Displayed data için canonical source yoksa dur.
- Fake motion önerisi varsa dur.
- Primary body scroll varsa dur.
- Active 8096 mutation varsa dur.
- Duplicate metric calculation varsa dur.
- Hardcoded production value varsa dur.
- User visual reject varsa dur.

## 8. Future phase sequence

1. UI_BUILD2_FOUNDATION_DRYRUN_NOAPI
2. UI_BUILD3_VIEW_MODEL_SNAPSHOT_DRYRUN_NOAPI
3. UI_BUILD4_MOTION_STATE_SNAPSHOT_DRYRUN_NOAPI
4. UI_BUILD5_TOKEN_YASAM_LIVING_PREVIEW_PLAN_NOAPI
5. UI_BUILD6_TOKEN_YASAM_LIVING_PREVIEW_AFTER_APPROVAL
6. UI_BUILD7_VISUAL_REVIEW_AND_PRODUCT_PASS_AUDIT_NOAPI

## 9. Next phase

`UI_BUILD2_FOUNDATION_DRYRUN_NOAPI`
