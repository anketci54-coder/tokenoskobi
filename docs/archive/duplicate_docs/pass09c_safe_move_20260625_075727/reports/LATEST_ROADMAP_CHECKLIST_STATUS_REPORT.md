# ROADMAP / CHECKLIST / STATUS REPORT

Generated: `2026-05-20 13:44:00`

## Executive Status

- Current build state: **icon + route + graph + binding backbone hazır**
- Circle mask style config: **written, not active-panel-bound**
- Active 8096 panel: **not mutated in style apply phase**
- DB: **unchanged**
- Domain: `www.coinoskobi.com` / secondary `coinoskobi.xyz`
- SSL: **not configured yet**

## Current Technical Snapshot

- project: `Tokenoskobi / Coinoskobi`
- timestamp: `2026-05-20 13:44:00`
- domain_primary: `www.coinoskobi.com`
- domain_secondary: `coinoskobi.xyz`
- ssl_status: `NOT_CONFIGURED`
- active_panel_8096_changed_today_by_this_phase: `False`
- style_status: `ACTIVE_STYLE_FILE_NOT_PANEL_BOUND`
- style_targets: `8`
- icon_registry: `77 icons`
- subject_graph: `77 nodes / 144 edges / 10 pipelines`
- route_map: `2 shell routes / 77 node routes / 8 center routes / 10 pipeline routes`
- icon_binding: `8 left nav / 77 node route / 65 module / 8 center workspace / 10 pipeline`

## Preview URLs

- bound_preview: `http://159.195.74.132:8105/`
- fit_candidate_rejected: `http://159.195.74.132:8106/`
- circle_mask_accepted: `http://159.195.74.132:8108/?v=3`

## Checklist

| Step | Status | Report |
|---|---|---|
| Icon asset inventory | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_ICON_PANEL_ASSET_INVENTORY_NOAPI.md` |
| Normalize 77 icon assets | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_ICON_PANEL_ASSET_NORMALIZE_POST_AUDIT_V2_NOAPI.md` |
| Export 384/128 icon sizes | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_ICON_PANEL_ASSET_EXPORT_384_128_POST_AUDIT_NOAPI.md` |
| Icon registry v1 | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_ICON_REGISTRY_POST_AUDIT_NOAPI.md` |
| Subject graph + pipelines | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_SUBJECT_GRAPH_PIPELINE_POST_AUDIT_NOAPI.md` |
| Panel route map + domain host | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_PANEL_ROUTE_MAP_POST_AUDIT_NOAPI.md` |
| Panel icon binding | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_PANEL_ICON_BINDING_POST_AUDIT_NOAPI.md` |
| Bound preview build | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_PANEL_BOUND_PREVIEW_BUILD_AFTER_APPROVAL.md` |
| Icon visual fit audit | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_PANEL_BOUND_ICON_VISUAL_FIT_AUDIT_NOAPI.md` |
| Reject fit_v1 candidate icons | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_PANEL_BOUND_ICON_VISUAL_FIT_CANDIDATE_REJECT_HOLD_NOAPI.md` |
| Accept circle_mask_v1 visual decision | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_PANEL_ICON_CARD_MASK_STYLE_VISUAL_DECISION_NOAPI.md` |
| Circle mask apply plan | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_PANEL_ICON_CARD_MASK_STYLE_APPLY_PLAN_NOAPI.md` |
| Circle mask style file real apply | `PASS` | `/root/tokenoskobi_clean_v1/reports/LATEST_PANEL_ICON_CARD_MASK_STYLE_APPLY_REAL_AFTER_EXPLICIT_APPROVAL.md` |

## Roadmap Next

1. `PANEL_ICON_CARD_MASK_STYLE_POST_AUDIT_NOAPI`
2. `PANEL_STYLE_AWARE_BOUND_PREVIEW_PLAN_NOAPI`
3. `PANEL_STYLE_AWARE_BOUND_PREVIEW_BUILD_AFTER_APPROVAL`
4. `MOBILE_COMPACT_UI_PLAN_NOAPI`
5. `ACTIVE_8096_STYLE_BINDING_APPLY_PLAN_NOAPI`
6. `DNS_PROPAGATION_CHECK_NOAPI after manual DNS A records`
7. `NGINX_DOMAIN_PROXY_PLAN_NOAPI`
8. `LETSENCRYPT_SSL_PLAN_NOAPI after DNS is live`

## Immediate Recommendation

1. Önce `PANEL_ICON_CARD_MASK_STYLE_POST_AUDIT_NOAPI` çalıştır.
2. Sonra style-aware preview üret; circle mask gerçekten yeni bound preview içinde görünsün.
3. Aktif 8096 için hâlâ ayrı apply plan + açık onay kullan.
4. Domain tarafında DNS A kayıtları elle girildikten sonra propagation check yap.
