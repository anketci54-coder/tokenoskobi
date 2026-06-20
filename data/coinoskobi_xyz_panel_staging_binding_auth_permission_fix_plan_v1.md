# Coinoskobi XYZ Auth Permission Fix Plan

FINAL_DECISION=PASS_AUTH_PERMISSION_FIX_PLAN_READY_NOAPI
FINAL_OK=True
VALIDATION_ERROR_COUNT=0
VALIDATION_ERRORS=NONE

## Teşhis

Nginx auth dosyasını okuyamadığı için `/panel/` ve `/mobile/` authenticated istekleri 500 dönüyor.

AUTH_FILE=/etc/nginx/.htpasswd_coinoskobi_xyz_panel
AUTH_OWNER=root
AUTH_GROUP=root
AUTH_MODE=0o640

NGINX_WORKER_USER=www-data
NGINX_WORKER_GROUP=www-data
WORKER_CAN_READ_AUTH_FILE=True

## Planlanan minimum fix

STRATEGY=chgrp_worker_group_and_chmod_640
COMMANDS=chgrp www-data /etc/nginx/.htpasswd_coinoskobi_xyz_panel && chmod 640 /etc/nginx/.htpasswd_coinoskobi_xyz_panel

## Bu fazda yapılanlar

- chmod yok
- chown yok
- chgrp yok
- Nginx write/reload yok
- DB write yok
- aktif panel write yok
- API/fetch yok

## Real için gerekli onay

COINOSKOBI XYZ AUTH PERMISSION FIX REAL için onay veriyorum
