# Coinoskobi XYZ Panel Staging Binding Plan

FINAL_DECISION=PASS_XYZ_PANEL_STAGING_BINDING_PLAN_READY_NOAPI
FINAL_OK=True
VALIDATION_ERROR_COUNT=0
VALIDATION_ERRORS=NONE

## Domain ayrımı

- `www.coinoskobi.xyz` = staging / panel / iç kontrol kapısı
- `www.coinoskobi.com` = public marka / ileride müşteri production alanı

## Planlanan route yapısı

- `/` = roadmap/status landing
- `/roadmap/` = roadmap/status landing
- `/panel/` = 127.0.0.1:8096 desktop panel reverse proxy
- `/mobile/` = 127.0.0.1:8096/mobile_pageflow/ reverse proxy

## Güvenlik şartı

- `/panel/` ve `/mobile/` auth olmadan açılmamalı.
- İlk real fazda basic auth önerilir.
- API key, secret, DB dump, admin action açıkta kalmamalı.
- Live trade / paper write açılmamalı.

## Bu fazda yapılanlar

- Nginx yazılmadı.
- SSL değişmedi.
- Domain değişmedi.
- Aktif panel değişmedi.
- DB değişmedi.
- API/fetch yok.

## Plan dosyaları

ROUTE_PLAN=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_PANEL_STAGING_BINDING_PLAN_NOAPI/20260524_154641/xyz_panel_route_plan.json
AUTH_POLICY=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_PANEL_STAGING_BINDING_PLAN_NOAPI/20260524_154641/xyz_panel_auth_policy.json
NGINX_CANDIDATE=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_PANEL_STAGING_BINDING_PLAN_NOAPI/20260524_154641/nginx_www_coinoskobi_xyz_panel_staging_candidate.conf
REAL_DRAFT=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_PANEL_STAGING_BINDING_PLAN_NOAPI/20260524_154641/REAL_XYZ_PANEL_STAGING_BINDING_DRAFT_REFUSES_EXECUTION.sh

## Real apply için gerekli onay

COINOSKOBI XYZ PANEL STAGING BINDING REAL için onay veriyorum
