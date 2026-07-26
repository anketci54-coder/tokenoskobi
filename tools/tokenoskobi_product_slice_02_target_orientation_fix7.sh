#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE_HEAD=${PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD:-}
BRANCH=agent/product-slice-02-target-orientation-fix1
BASE_PATH=tools/tokenoskobi_product_slice_02_target_orientation_fix6.sh
EXPECTED_FIX6_BLOB=b2da096cc56c332ba93f20040c32b6f3b733cb6c
TEMP=/root/tokenoskobi_product_slice_02_target_orientation_fix7_patched.sh

fail(){ printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
[[ "$SOURCE_HEAD" =~ ^[0-9a-f]{40}$ ]] || fail SOURCE_HEAD_MISSING_OR_INVALID
[[ "$(git rev-parse "origin/$BRANCH")" == "$SOURCE_HEAD" ]] || fail SOURCE_HEAD_NOT_CURRENT_BRANCH_HEAD
[[ "$(git merge-base d1d5078a7fb9bab7108755bf63806cb27f697007 "$SOURCE_HEAD")" == d1d5078a7fb9bab7108755bf63806cb27f697007 ]] || fail SOURCE_HEAD_BASE_INVALID

git show "$SOURCE_HEAD:$BASE_PATH" > "$TEMP"
[[ "$(git hash-object "$TEMP")" == "$EXPECTED_FIX6_BLOB" ]] || fail FIX6_BASE_BLOB_CHANGED

TEMP="$TEMP" python3 - <<'PY'
from pathlib import Path
import os

p=Path(os.environ['TEMP'])
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    if s.count(old)!=1:
        raise SystemExit('BLOCKED=FIX7_PATCH_ANCHOR_'+label)
    s=s.replace(old,new,1)

rep(
"        a=request(f'{base}/networks/bsc/tokens/{token}')['data']['attributes'];out['token']={'name':a.get('name'),'symbol':a.get('symbol'),'price_usd':num(a.get('price_usd')),'market_cap_usd':num(a.get('market_cap_usd')),'fdv_usd':num(a.get('fdv_usd'))};out['available']=True",
"        a=request(f'{base}/networks/bsc/tokens/{token}')['data']['attributes'];out['token']={'name':a.get('name'),'symbol':a.get('symbol'),'price_usd':num(a.get('price_usd')),'market_cap_usd':num(a.get('market_cap_usd')),'fdv_usd':num(a.get('fdv_usd')),'price_source':'TOKEN_ENDPOINT'};out['available']=True",
'TOKEN_PRICE_SOURCE',
)

rep(
"        out['pools']=rows[:8];out['selected_pool']=oriented[0] if oriented else None;out['target_orientation_verified']=bool(oriented);out['available']=out['available'] or bool(rows)\n        if rows and not oriented:out['errors'].append('TARGET_ASSET_ORIENTATION_UNVERIFIED')",
"        out['pools']=rows[:8];out['selected_pool']=oriented[0] if oriented else None;out['target_orientation_verified']=bool(oriented);out['available']=out['available'] or bool(rows)\n        selected=out.get('selected_pool') or {};token_row=out.setdefault('token',{})\n        if selected.get('orientation_verified') and token_row.get('price_usd') is None and selected.get('price_usd') is not None:\n            token_row['price_usd']=selected['price_usd'];token_row['price_source']='SELECTED_POOL_ORIENTED_FALLBACK'\n        if rows and not oriented:out['errors'].append('TARGET_ASSET_ORIENTATION_UNVERIFIED')",
'ORIENTED_PRICE_FALLBACK',
)

rep(
" def test_pool_base_orientation(self):",
" def test_market_price_fallback_from_oriented_pool(self):\n  old=m.request\n  def fake(url,body=None):\n   if url.endswith('/'+BASE):raise RuntimeError('TOKEN_ENDPOINT_DOWN')\n   if '/pools?' in url:return {'data':[item()]}\n   raise AssertionError(url)\n  m.request=fake\n  try:r=m.market(BASE)\n  finally:m.request=old\n  self.assertEqual(r['token']['price_usd'],571.05);self.assertEqual(r['token']['price_source'],'SELECTED_POOL_ORIENTED_FALLBACK');self.assertTrue(r['target_orientation_verified'])\n def test_pool_base_orientation(self):",
'FALLBACK_TEST',
)

rep(
"x=json.load(open(os.environ['RESULT']));token=os.environ['WBNB'];m=x['market'];p=m['selected_pool'];t=x['technical_timeframes'];price=float(m['token']['price_usd']);pool_price=float(p['price_usd']);ok=[v for v in t.values() if v.get('status')=='OK']",
"x=json.load(open(os.environ['RESULT']));token=os.environ['WBNB'];m=x['market'];p=m['selected_pool'];t=x['technical_timeframes'];price=float(m['token']['price_usd']);pool_price=float(p['price_usd']);ok=[v for v in t.values() if v.get('status')=='OK'];assert m['token'].get('price_source') in ('TOKEN_ENDPOINT','SELECTED_POOL_ORIENTED_FALLBACK')",
'VALIDATION_PRICE_SOURCE_FIRST',
)

rep(
"x=json.load(open(os.environ['RESULT']));token=os.environ['WBNB'];m=x['market'];p=m['selected_pool'];t=x['technical_timeframes'];price=float(m['token']['price_usd']);pool_price=float(p['price_usd']);ok=[v for v in t.values() if v.get('status')=='OK']",
"x=json.load(open(os.environ['RESULT']));token=os.environ['WBNB'];m=x['market'];p=m['selected_pool'];t=x['technical_timeframes'];price=float(m['token']['price_usd']);pool_price=float(p['price_usd']);ok=[v for v in t.values() if v.get('status')=='OK'];assert m['token'].get('price_source') in ('TOKEN_ENDPOINT','SELECTED_POOL_ORIENTED_FALLBACK')",
'VALIDATION_PRICE_SOURCE_SECOND',
)

rep(
"print('SHADOW_TARGET_ORIENTATION=PASS');print('SHADOW_TARGET_SIDE='+p['target_side']);print('SHADOW_TOKEN_PRICE_USD='+str(price));print('SHADOW_POOL_TARGET_PRICE_USD='+str(pool_price));print('SHADOW_TECH_OK='+str(len(ok)));print('SHADOW_DECISION='+x['decision']['decision'])",
"print('SHADOW_TARGET_ORIENTATION=PASS');print('SHADOW_TARGET_SIDE='+p['target_side']);print('SHADOW_TOKEN_PRICE_USD='+str(price));print('SHADOW_POOL_TARGET_PRICE_USD='+str(pool_price));print('SHADOW_PRICE_SOURCE='+str(m['token'].get('price_source')));print('SHADOW_TECH_OK='+str(len(ok)));print('SHADOW_DECISION='+x['decision']['decision'])",
'SHADOW_PRICE_SOURCE_OUTPUT',
)

rep(
"print('PRODUCTION_TARGET_ORIENTATION=PASS');print('PRODUCTION_TARGET_SIDE='+p['target_side']);print('PRODUCTION_TOKEN_PRICE_USD='+str(price));print('PRODUCTION_POOL_TARGET_PRICE_USD='+str(pool_price));print('PRODUCTION_TECH_OK='+str(len(ok)));print('PRODUCTION_DECISION='+x['decision']['decision'])",
"print('PRODUCTION_TARGET_ORIENTATION=PASS');print('PRODUCTION_TARGET_SIDE='+p['target_side']);print('PRODUCTION_TOKEN_PRICE_USD='+str(price));print('PRODUCTION_POOL_TARGET_PRICE_USD='+str(pool_price));print('PRODUCTION_PRICE_SOURCE='+str(m['token'].get('price_source')));print('PRODUCTION_TECH_OK='+str(len(ok)));print('PRODUCTION_DECISION='+x['decision']['decision'])",
'PRODUCTION_PRICE_SOURCE_OUTPUT',
)

rep(
"printf 'TARGET_ORIENTATION_FIX6_RESULT=SUCCESS\\n'",
"printf 'TARGET_ORIENTATION_FIX7_RESULT=SUCCESS\\n'",
'SUCCESS_MARKER',
)
rep(
"printf 'BACKUP_DIR=%s\\n' \"$BACKUP\"",
"printf 'PRICE_FALLBACK=SELECTED_POOL_ORIENTED_ONLY\\n'\nprintf 'BACKUP_DIR=%s\\n' \"$BACKUP\"",
'FALLBACK_OUTPUT',
)

p.write_text(s,encoding='utf-8')
PY

chmod 0700 "$TEMP"
bash -n "$TEMP"

set +e
PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD="$SOURCE_HEAD" \
PRODUCT_SLICE_02_ORIENTATION_CONFIRM=YES \
bash "$TEMP"
RC=$?
set -e
rm -f "$TEMP"

if [[ "$RC" -ne 0 ]]; then
  printf 'TARGET_ORIENTATION_FIX7_RESULT=FAILED\n'
  printf 'INNER_RC=%s\n' "$RC"
  exit "$RC"
fi

printf 'TARGET_ORIENTATION_FIX7_WRAPPER=SUCCESS\n'
