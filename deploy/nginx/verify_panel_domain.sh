#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-panel.coinoskobi.xyz}"
ROOT="/root/tokenoskobi_clean_v1"
OUT="$ROOT/data/control/n15_panel_domain_verify_${DOMAIN//./_}.json"

cd "$ROOT"

LOCAL_ROOT_CODE="$(curl -sS -o /tmp/n15_verify_local_root.html -w '%{http_code}' --max-time 5 http://127.0.0.1:8096/ || true)"
LOCAL_BRIDGE_CODE="$(curl -sS -o /tmp/n15_verify_local_bridge.json -w '%{http_code}' --max-time 5 http://127.0.0.1:8096/data/backpressure_readmodel_refresh_cache.json || true)"
HTTP_ROOT_CODE="$(curl -sS -o /tmp/n15_verify_http_root.html -w '%{http_code}' --max-time 8 http://${DOMAIN}/ || true)"
HTTP_BRIDGE_CODE="$(curl -sS -o /tmp/n15_verify_http_bridge.json -w '%{http_code}' --max-time 8 http://${DOMAIN}/data/backpressure_readmodel_refresh_cache.json || true)"
HTTPS_ROOT_CODE="$(curl -k -sS -o /tmp/n15_verify_https_root.html -w '%{http_code}' --max-time 8 https://${DOMAIN}/ || true)"
HTTPS_BRIDGE_CODE="$(curl -k -sS -o /tmp/n15_verify_https_bridge.json -w '%{http_code}' --max-time 8 https://${DOMAIN}/data/backpressure_readmodel_refresh_cache.json || true)"

python3 - <<PY
import json, pathlib, datetime
out = pathlib.Path('$OUT')
out.parent.mkdir(parents=True, exist_ok=True)
result = {
  'stage': 'N15_PANEL_DOMAIN_VERIFY',
  'domain': '$DOMAIN',
  'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'codes': {
    'local_root': '$LOCAL_ROOT_CODE',
    'local_bridge': '$LOCAL_BRIDGE_CODE',
    'http_root': '$HTTP_ROOT_CODE',
    'http_bridge': '$HTTP_BRIDGE_CODE',
    'https_root': '$HTTPS_ROOT_CODE',
    'https_bridge': '$HTTPS_BRIDGE_CODE'
  },
  'http_ready': '$HTTP_ROOT_CODE' == '200' and '$HTTP_BRIDGE_CODE' == '200',
  'https_ready': '$HTTPS_ROOT_CODE' == '200' and '$HTTPS_BRIDGE_CODE' == '200',
  'decision': 'HTTPS_PANEL_READY' if '$HTTPS_ROOT_CODE' == '200' and '$HTTPS_BRIDGE_CODE' == '200' else ('HTTP_PANEL_READY_SSL_PENDING' if '$HTTP_ROOT_CODE' == '200' and '$HTTP_BRIDGE_CODE' == '200' else 'DOMAIN_PANEL_NOT_READY'),
  'safety': {'core_change': False, 'runtime_logic_change': False, 'wallet': False, 'signing': False, 'live_trade': False, 'provider_call': False, 'api_call': False}
}
out.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
print('FINAL_GATE=PASS_N15_PANEL_DOMAIN_VERIFY')
print('DECISION=' + result['decision'])
print('JSON=' + str(out.relative_to(pathlib.Path('$ROOT'))))
PY
