# Coinoskobi .COM Public Site Plan

FINAL_DECISION=PASS_COM_PUBLIC_SITE_PLAN_READY_NOAPI
FINAL_OK=True
VALIDATION_ERROR_COUNT=0
VALIDATION_ERRORS=NONE

## Domain policy

.xyz = staging / roadmap / auth protected panel
.com = public brand / customer-facing marketing site

## Public pages

- / : Ana Sayfa
- /platform/ : Ürün / Panel Tanıtımı
- /roadmap/ : Public roadmap
- /risk/ : Güvenlik / Risk Yaklaşımı
- /contact/ : İletişim / Bekleme listesi

## Public copy rules

- Public sitede server path gösterme: /root/tokenoskobi_clean_v1, /var/www, SQLite path yok.
- Public sitede auth kullanıcı adı/şifre yok.
- Public sitede private panel URL doğrudan öne çıkarılmaz; sadece 'korumalı demo/panel' ifadesi kullanılır.
- Getiri vaadi yok; risk kontrollü, data-first, simulation-first anlatım.
- Live trade/paper trade açık gibi gösterme; mevcut durum neyse onu yaz.
- .xyz staging/internal; .com public marka olarak ayrılır.

## Next phases

1. COINOSKOBI_COM_PUBLIC_SITE_PREVIEW_NOAPI
2. COINOSKOBI_COM_DOMAIN_SSL_NGINX_PREFLIGHT_NOAPI
3. COINOSKOBI_COM_PUBLIC_SITE_APPLY_PLAN_NOAPI
4. COINOSKOBI_COM_PUBLIC_SITE_APPLY_REAL_AFTER_EXPLICIT_APPROVAL

## Read-only findings

NGINX_T_OK=True
NGINX_COM_HIT_COUNT=1
NGINX_XYZ_HIT_COUNT=13
COM_WWW_CERT_DIR_EXISTS=False
COM_ROOT_CERT_DIR_EXISTS=False

## Safety

ACTIVE_INDEX_UNCHANGED=True
ACTIVE_DATA_UNCHANGED=True
ACTIVE_RISK_DATA_UNCHANGED=True
ACTIVE_MOBILE_INDEX_UNCHANGED=True
LIVE_DB_UNCHANGED=True
NGINX_XYZ_UNCHANGED=True
AUTH_FILE_UNCHANGED=True

NO_COM_NGINX_WRITE=True
NO_DNS_CHANGE=True
NO_SSL_CHANGE=True
NO_XYZ_CHANGE=True
NO_ACTIVE_PANEL_WRITE=True
NO_DB_WRITE=True
NO_API_FETCH=True
LIVE_TRADE=0
PAPER_TRADE_EXECUTION=0
AUTH_PASSWORD_PRINTED=False
