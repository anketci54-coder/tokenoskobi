#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE_HEAD=${PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD:-}
BRANCH=agent/product-slice-02-target-orientation-fix1
BASE_PATH=tools/tokenoskobi_product_slice_02_target_orientation_fix1.sh
TEMP=/root/tokenoskobi_product_slice_02_target_orientation_fix2_patched.sh

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

def rep(old,new,label):
    global s
    if s.count(old)!=1:
        raise SystemExit('BLOCKED=FIX2_PATCH_ANCHOR_'+label)
    s=s.replace(old,new,1)

rep(
"    base_price=num(a.get('base_token_price_usd'));quote_price=num(a.get('quote_token_price_usd'))\n    target_price=base_price if side=='base' else quote_price if side=='quote' else None",
"    base_price=num(a.get('base_token_price_usd'));quote_price=num(a.get('quote_token_price_usd'));base_change=num((a.get('price_change_percentage') or {}).get('h24'))\n    target_price=base_price if side=='base' else quote_price if side=='quote' else None\n    target_change=base_change if side=='base' else ((1/(1+base_change/100)-1)*100 if side=='quote' and base_change is not None and base_change>-100 else None)",
'QUOTE_CHANGE_CALC')
rep(
"      'change_24h_pct':num((a.get('price_change_percentage') or {}).get('h24')),",
"      'change_24h_pct':target_change,",
'QUOTE_CHANGE_FIELD')
rep(
"  r=m.oriented_pool(item(),QUOTE);self.assertEqual(r['target_side'],'quote');self.assertEqual(r['price_usd'],1.001);self.assertTrue(r['orientation_verified'])",
"  r=m.oriented_pool(item(),QUOTE);self.assertEqual(r['target_side'],'quote');self.assertEqual(r['price_usd'],1.001);self.assertTrue(r['orientation_verified']);self.assertAlmostEqual(r['change_24h_pct'],(1/(1+0.012)-1)*100,places=8)",
'QUOTE_CHANGE_TEST')
rep(
" def test_decide_blocks_wrong_target(self):",
" def test_tech_rejects_meta_without_target(self):\n  old=m.request\n  def fake(url,body=None):return {'data':{'attributes':{'ohlcv_list':[[3,1,1,1,1,1],[2,1,1,1,1,1],[1,1,1,1,1,1]]}},'meta':{'base':{'address':QUOTE},'quote':{'address':'0x'+'d'*40}}}\n  m.request=fake\n  try:r=m.tech(POOL,BASE)\n  finally:m.request=old\n  self.assertTrue(all(v['status']=='VERI_YETERSIZ' and 'TARGET_TOKEN_NOT_IN_OHLCV_META' in v['error'] for v in r.values()))\n def test_decide_blocks_wrong_target(self):",
'META_MISMATCH_TEST')
rep(
"EXPECTED_STATUS=$' M tests/test_product_slice_02.py\\n M tools/tokenoskobi_product_slice_02_server.py'",
"EXTERNAL_PANEL=$(curl -sS --connect-timeout 5 --max-time 20 -o /dev/null -w '%{http_code}' https://panel.coinoskobi.xyz/panel/panel_v2/ 2>/dev/null || true)\nEXTERNAL_API=$(curl -sS --connect-timeout 5 --max-time 30 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' --data '{\"token_address\":\"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c\"}' https://panel.coinoskobi.xyz/api/v1/analyze 2>/dev/null || true)\nEXTERNAL_HEALTH=$(curl -sS --connect-timeout 5 --max-time 20 -o /dev/null -w '%{http_code}' https://panel.coinoskobi.xyz/healthz 2>/dev/null || true)\n[[ \"$EXTERNAL_PANEL\" == 401 ]] || fail EXTERNAL_PANEL_NOT_401\n[[ \"$EXTERNAL_API\" == 401 ]] || fail EXTERNAL_API_NOT_401\n[[ \"$EXTERNAL_HEALTH\" == 200 ]] || fail EXTERNAL_HEALTH_NOT_200\n\nEXPECTED_STATUS=$' M tests/test_product_slice_02.py\\n M tools/tokenoskobi_product_slice_02_server.py'",
'EXTERNAL_GATES')
rep(
"printf 'LOCAL_HEALTH_HTTP=200\\n'",
"printf 'LOCAL_HEALTH_HTTP=200\\n'\nprintf 'EXTERNAL_PANEL_UNAUTH_HTTP=401\\n'\nprintf 'EXTERNAL_API_UNAUTH_HTTP=401\\n'\nprintf 'EXTERNAL_HEALTH_HTTP=200\\n'",
'EXTERNAL_OUTPUT')
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
  printf 'TARGET_ORIENTATION_FIX2_RESULT=FAILED\n'
  printf 'INNER_RC=%s\n' "$RC"
  exit "$RC"
fi
printf 'TARGET_ORIENTATION_FIX2_RESULT=SUCCESS\n'
