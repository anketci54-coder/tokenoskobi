#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE_HEAD=${PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD:-}
BRANCH=agent/product-slice-02-target-orientation-fix1
BASE_PATH=tools/tokenoskobi_product_slice_02_target_orientation_fix2.sh
TEMP=/root/tokenoskobi_product_slice_02_target_orientation_fix3_patched.sh

fail(){ printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
[[ "$SOURCE_HEAD" =~ ^[0-9a-f]{40}$ ]] || fail SOURCE_HEAD_MISSING_OR_INVALID
[[ "$(git rev-parse "origin/$BRANCH")" == "$SOURCE_HEAD" ]] || fail SOURCE_HEAD_NOT_CURRENT_BRANCH_HEAD
[[ "$(git merge-base d1d5078a7fb9bab7108755bf63806cb27f697007 "$SOURCE_HEAD")" == d1d5078a7fb9bab7108755bf63806cb27f697007 ]] || fail SOURCE_HEAD_BASE_INVALID

git show "$SOURCE_HEAD:$BASE_PATH" > "$TEMP"

TEMP="$TEMP" python3 - <<'PY'
from pathlib import Path
import os

p=Path(os.environ['TEMP'])
s=p.read_text(encoding='utf-8')
anchor="p.write_text(s,encoding='utf-8')"
if s.count(anchor)!=1:
    raise SystemExit('BLOCKED=FIX3_PATCH_ANCHOR_WRITE')

start_prod="curl -sS --connect-timeout 5 --max-time 180 -H 'Content-Type: application/json' --data '{\"token_address\":\"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c\"}' http://127.0.0.1:8096/api/v1/analyze > \"$BACKUP/production_wbnb.json\"\n"
end_prod="\nEXPECTED_STATUS=$' M tests/test_product_slice_02.py\\n M tools/tokenoskobi_product_slice_02_server.py'"

new_prod=r'''PRODUCTION_RESULT="$BACKUP/production_wbnb.json"
PRODUCTION_VALIDATION="$BACKUP/production_validation.txt"
PRODUCTION_OK=0

for ATTEMPT in 1 2 3 4 5 6; do
  TMP_RESULT="${PRODUCTION_RESULT}.tmp"
  HTTP_CODE=$(curl -sS --connect-timeout 5 --max-time 180 -o "$TMP_RESULT" -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"}' http://127.0.0.1:8096/api/v1/analyze 2>/dev/null || true)
  printf 'PRODUCTION_SEMANTIC_ATTEMPT=%s HTTP=%s\n' "$ATTEMPT" "$HTTP_CODE"

  if [[ "$HTTP_CODE" == 200 ]]; then
    mv "$TMP_RESULT" "$PRODUCTION_RESULT"
    set +e
    RESULT="$PRODUCTION_RESULT" WBNB="$WBNB" python3 - <<'PYPROD' > "$PRODUCTION_VALIDATION" 2>&1
import json,os
path=os.environ['RESULT']
token=os.environ['WBNB']
try:
    with open(path,encoding='utf-8') as handle:
        x=json.load(handle)
except Exception as exc:
    print('PRODUCTION_PACKET_PARSE_ERROR='+type(exc).__name__+':'+str(exc)[:160])
    raise SystemExit(2)

m=x.get('market') or {}
p=m.get('selected_pool')
t=x.get('technical_timeframes') or {}
d=x.get('decision') or {}
a=x.get('authority') or {}

if not isinstance(p,dict):
    print('PRODUCTION_NOT_READY=SELECTED_POOL_NONE')
    print('MARKET_ERRORS='+json.dumps(m.get('errors') or [],ensure_ascii=False))
    print('DECISION='+json.dumps(d,ensure_ascii=False))
    raise SystemExit(3)

try:
    price=float((m.get('token') or {}).get('price_usd'))
    pool_price=float(p.get('price_usd'))
except Exception as exc:
    print('PRODUCTION_NOT_READY=TARGET_PRICE_MISSING')
    print('DETAIL='+type(exc).__name__+':'+str(exc)[:120])
    print('MARKET_ERRORS='+json.dumps(m.get('errors') or [],ensure_ascii=False))
    raise SystemExit(4)

if m.get('target_orientation_verified') is not True:
    print('PRODUCTION_NOT_READY=MARKET_ORIENTATION_UNVERIFIED')
    raise SystemExit(5)
if p.get('orientation_verified') is not True or p.get('target_token_address')!=token:
    print('PRODUCTION_NOT_READY=POOL_TARGET_MISMATCH')
    print('POOL='+json.dumps(p,ensure_ascii=False))
    raise SystemExit(6)
if not (price>100 and pool_price>100 and 0.75 <= pool_price/price <= 1.25):
    print('PRODUCTION_NOT_READY=TARGET_PRICE_RATIO_INVALID')
    print('TOKEN_PRICE_USD='+str(price))
    print('POOL_TARGET_PRICE_USD='+str(pool_price))
    raise SystemExit(7)

ok=[v for v in t.values() if v.get('status')=='OK']
if len(ok)<4:
    print('PRODUCTION_NOT_READY=TECHNICAL_OK_BELOW_4')
    print('TECHNICAL='+json.dumps(t,ensure_ascii=False))
    raise SystemExit(8)
if not all(v.get('target_token_address')==token and float(v.get('last'))>100 for v in ok):
    print('PRODUCTION_NOT_READY=TECHNICAL_TARGET_OR_PRICE_MISMATCH')
    print('TECHNICAL='+json.dumps(t,ensure_ascii=False))
    raise SystemExit(9)
if 'TARGET_ASSET_ORIENTATION_UNVERIFIED' in (d.get('blockers') or []):
    print('PRODUCTION_NOT_READY=ORIENTATION_BLOCKER_PRESENT')
    raise SystemExit(10)
if 'TECHNICAL_TARGET_MISMATCH' in (d.get('blockers') or []):
    print('PRODUCTION_NOT_READY=TECHNICAL_TARGET_BLOCKER_PRESENT')
    raise SystemExit(11)
if not all(a.get(k) is False for k in ('paper','live','wallet','signing','order','broadcast')):
    print('PRODUCTION_NOT_READY=AUTHORITY_NOT_ZERO')
    raise SystemExit(12)

print('PRODUCTION_TARGET_ORIENTATION=PASS')
print('PRODUCTION_TARGET_SIDE='+str(p.get('target_side')))
print('PRODUCTION_TOKEN_PRICE_USD='+str(price))
print('PRODUCTION_POOL_TARGET_PRICE_USD='+str(pool_price))
print('PRODUCTION_TECH_OK='+str(len(ok)))
print('PRODUCTION_DECISION='+str(d.get('decision')))
PYPROD
    VALIDATE_RC=$?
    set -e
    cat "$PRODUCTION_VALIDATION"
    if [[ "$VALIDATE_RC" -eq 0 ]]; then
      PRODUCTION_OK=1
      break
    fi
  else
    rm -f "$TMP_RESULT"
  fi

  sleep $((ATTEMPT * 5))
done

[[ "$PRODUCTION_OK" -eq 1 ]] || fail PRODUCTION_SEMANTIC_READINESS_TIMEOUT
'''

injection=(
    "\nstart_prod="+repr(start_prod)+"\n"
    "end_prod="+repr(end_prod)+"\n"
    "new_prod="+repr(new_prod)+"\n"
    "if s.count(start_prod)!=1 or s.count(end_prod)!=1:\n"
    "    raise SystemExit('BLOCKED=FIX3_PATCH_ANCHOR_PRODUCTION')\n"
    "a=s.index(start_prod)\n"
    "b=s.index(end_prod,a)\n"
    "s=s[:a]+new_prod+s[b:]\n\n"
)
s=s.replace(anchor,injection+anchor,1)
p.write_text(s,encoding='utf-8')
PY

chmod 0700 "$TEMP"
bash -n "$TEMP"

set +e
PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD="$SOURCE_HEAD" \
bash "$TEMP"
RC=$?
set -e
rm -f "$TEMP"

if [[ "$RC" -ne 0 ]]; then
  printf 'TARGET_ORIENTATION_FIX3_RESULT=FAILED\n'
  printf 'INNER_RC=%s\n' "$RC"
  exit "$RC"
fi

printf 'TARGET_ORIENTATION_FIX3_RESULT=SUCCESS\n'
