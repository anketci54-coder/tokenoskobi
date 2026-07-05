#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-panel.coinoskobi.xyz}"
ROOT="/root/tokenoskobi_clean_v1"
AVAILABLE="/etc/nginx/sites-available/${DOMAIN}.conf"
ENABLED="/etc/nginx/sites-enabled/${DOMAIN}.conf"
OUT="$ROOT/data/control/n15_panel_domain_rollback_${DOMAIN//./_}.json"

cd "$ROOT"

rm -f "$ENABLED"
if [ -f "$AVAILABLE" ]; then
  mv "$AVAILABLE" "${AVAILABLE}.disabled_$(date -u +%Y%m%dT%H%M%SZ)"
fi

nginx -t
systemctl reload nginx

python3 - <<PY
import json, pathlib, datetime
out = pathlib.Path('$OUT')
out.parent.mkdir(parents=True, exist_ok=True)
result = {
  'stage': 'N15_PANEL_DOMAIN_ROLLBACK',
  'domain': '$DOMAIN',
  'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'decision': 'DOMAIN_SITE_DISABLED_AND_NGINX_RELOADED',
  'safety': {'core_change': False, 'runtime_logic_change': False, 'wallet': False, 'signing': False, 'live_trade': False, 'provider_call': False, 'api_call': False}
}
out.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
print('FINAL_GATE=PASS_N15_PANEL_DOMAIN_ROLLBACK')
print('DECISION=' + result['decision'])
print('JSON=' + str(out.relative_to(pathlib.Path('$ROOT'))))
PY
