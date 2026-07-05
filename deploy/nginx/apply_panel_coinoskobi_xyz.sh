#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-panel.coinoskobi.xyz}"
ROOT="/root/tokenoskobi_clean_v1"
TEMPLATE="$ROOT/deploy/nginx/coinoskobi_panel_8096_proxy.conf.template"
AVAILABLE="/etc/nginx/sites-available/${DOMAIN}.conf"
ENABLED="/etc/nginx/sites-enabled/${DOMAIN}.conf"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$ROOT/data/control/n15_nginx_panel_publish_apply_${DOMAIN//./_}.json"

cd "$ROOT"

git rev-parse HEAD >/tmp/n15_head.txt
systemctl is-active --quiet tokenoskobi-active-panel-8096.service
curl -fsS --max-time 3 http://127.0.0.1:8096/ >/tmp/n15_panel_root.html
curl -fsS --max-time 3 http://127.0.0.1:8096/data/backpressure_readmodel_refresh_cache.json >/tmp/n15_bridge_cache.json

test -f "$TEMPLATE"

tmp="/tmp/${DOMAIN}.conf.${STAMP}"
sed "s/DOMAIN_NAME/${DOMAIN}/g" "$TEMPLATE" > "$tmp"

if [ -f "$AVAILABLE" ]; then
  cp "$AVAILABLE" "${AVAILABLE}.bak_${STAMP}"
fi
cp "$tmp" "$AVAILABLE"
ln -sfn "$AVAILABLE" "$ENABLED"

nginx -t
systemctl reload nginx

HTTP_CODE="$(curl -sS -o /tmp/n15_domain_root.html -w '%{http_code}' --max-time 8 "http://${DOMAIN}/" || true)"
BRIDGE_CODE="$(curl -sS -o /tmp/n15_domain_bridge.json -w '%{http_code}' --max-time 8 "http://${DOMAIN}/data/backpressure_readmodel_refresh_cache.json" || true)"

python3 - <<PY
import json, pathlib, datetime
out = pathlib.Path('$OUT')
out.parent.mkdir(parents=True, exist_ok=True)
result = {
  'stage': 'N15_NGINX_PANEL_PUBLISH_APPLY',
  'domain': '$DOMAIN',
  'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'local_head': pathlib.Path('/tmp/n15_head.txt').read_text().strip(),
  'panel_local_root_ok': pathlib.Path('/tmp/n15_panel_root.html').exists(),
  'panel_local_bridge_ok': pathlib.Path('/tmp/n15_bridge_cache.json').exists(),
  'nginx_available': '$AVAILABLE',
  'nginx_enabled': '$ENABLED',
  'http_root_code': '$HTTP_CODE',
  'http_bridge_code': '$BRIDGE_CODE',
  'decision': 'DOMAIN_PANEL_HTTP_READY' if '$HTTP_CODE' == '200' and '$BRIDGE_CODE' == '200' else 'DOMAIN_PANEL_HTTP_NEEDS_DNS_OR_NGINX_REVIEW',
  'next_step': 'ISSUE_SSL_WITH_CERTBOT_AFTER_HTTP_200',
  'safety': {
    'core_change': False,
    'runtime_logic_change': False,
    'wallet': False,
    'signing': False,
    'live_trade': False,
    'provider_call': False,
    'api_call': False,
    'nginx_reload': True
  }
}
out.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
print('FINAL_GATE=PASS_N15_NGINX_PANEL_PUBLISH_APPLY')
print('DECISION=' + result['decision'])
print('DOMAIN=' + result['domain'])
print('HTTP_ROOT_CODE=' + result['http_root_code'])
print('HTTP_BRIDGE_CODE=' + result['http_bridge_code'])
print('JSON=' + str(out.relative_to(pathlib.Path('$ROOT'))))
PY
