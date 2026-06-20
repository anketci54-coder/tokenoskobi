# Coinoskobi Risk Security Active Panel Apply Plan v1

Phase: `COINOSKOBI_RISK_SECURITY_ACTIVE_PANEL_APPLY_PLAN_NOAPI`
Generated: `20260522_142444`

## Decision

This is a plan-only phase. It does not write active 8096.

## Source preview

- Preview review JSON: `/root/tokenoskobi_clean_v1/data/coinoskobi_risk_security_panel_integration_preview_review_noapi.json`
- Preview payload: `/root/tokenoskobi_clean_v1/panel_previews/risk_security_panel_integration_preview_8142_20260522_132635/risk_security_preview_data.json`
- Preview index: `/root/tokenoskobi_clean_v1/panel_previews/risk_security_panel_integration_preview_8142_20260522_132635/index.html`
- Preview root: `/root/tokenoskobi_clean_v1/panel_previews/risk_security_panel_integration_preview_8142_20260522_132635`

## Active target

- Active index: `/root/tokenoskobi_clean_v1/active_panel_8096/current/index.html`
- Active data: `/root/tokenoskobi_clean_v1/active_panel_8096/current/data/production_v2_control_center_data.json`
- Active data dir: `/root/tokenoskobi_clean_v1/active_panel_8096/current/data`

## Apply strategy

- Keep active 8096 production shell.
- Do not create a 9th center.
- Do not overwrite full app blindly.
- Mount cards under existing 8-center structure.
- Risk cards go under Risk & Güvenlik.
- Execution plan cards go under Komuta.
- Outcome/Morg route cards go under Yaşam Destek.
- Lock state card goes under Sistem Kontrol.

## Planned files

1. Copy preview data to active data namespace:
   `/root/tokenoskobi_clean_v1/active_panel_8096/current/data/risk_security_preview_data.json`

2. Augment active data:
   `/root/tokenoskobi_clean_v1/active_panel_8096/current/data/production_v2_control_center_data.json`

3. Enable/mount panel sections in active shell:
   `/root/tokenoskobi_clean_v1/active_panel_8096/current/index.html`

## Safety

- DB write: `0`
- API/fetch: `0`
- Nginx/service/timer: `0`
- Live trade: `0`
- Paper execution: `0`
- Auto execution: `0`

## Required approval for real apply

`COINOSKOBI RISK SECURITY ACTIVE PANEL APPLY REAL için onay veriyorum`
