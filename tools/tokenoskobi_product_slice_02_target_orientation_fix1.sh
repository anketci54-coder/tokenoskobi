#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

ROOT=/root/tokenoskobi_clean_v1
EXPECTED_MAIN=d1d5078a7fb9bab7108755bf63806cb27f697007
BRANCH=agent/product-slice-02-target-orientation-fix1
SOURCE_HEAD=${PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD:-}
SERVICE=tokenoskobi-product-slice-02.service
SERVER=tools/tokenoskobi_product_slice_02_server.py
TEST=tests/test_product_slice_02.py
WBNB=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c
SHADOW_PORT=18096
BACKUP=''
MODIFIED=0
SHADOW_PID=''

fail(){ printf 'BLOCKED=%s\n' "$1" >&2; return 1; }

cleanup_shadow(){
  set +e
  if [[ -n "$SHADOW_PID" ]] && kill -0 "$SHADOW_PID" 2>/dev/null; then
    kill "$SHADOW_PID" 2>/dev/null || true
    wait "$SHADOW_PID" 2>/dev/null || true
  fi
  SHADOW_PID=''
}

wait_http(){
  local url=$1
  local expected=$2
  local i code
  for i in $(seq 1 30); do
    code=$(curl -sS --connect-timeout 2 --max-time 5 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || true)
    [[ "$code" == "$expected" ]] && return 0
    sleep 1
  done
  return 1
}

rollback(){
  local rc=$?
  trap - ERR INT TERM
  set +e
  cleanup_shadow
  if [[ "$MODIFIED" -eq 1 && -n "$BACKUP" ]]; then
    cp "$BACKUP/server.py" "$ROOT/$SERVER" 2>/dev/null || true
    cp "$BACKUP/test.py" "$ROOT/$TEST" 2>/dev/null || true
    chmod 0755 "$ROOT/$SERVER" 2>/dev/null || true
    chmod 0644 "$ROOT/$TEST" 2>/dev/null || true
    python3 -m py_compile "$ROOT/$SERVER" "$ROOT/$TEST" >/dev/null 2>&1 || true
    systemctl restart "$SERVICE" >/dev/null 2>&1 || true
    wait_http http://127.0.0.1:8096/healthz 200 >/dev/null 2>&1 || true
  fi
  printf 'TARGET_ORIENTATION_FIX1_RESULT=FAILED\n'
  printf 'FAILED_RC=%s\n' "$rc"
  printf 'ROLLBACK_ATTEMPTED=%s\n' "$MODIFIED"
  printf 'LIVE_TRADE=DISABLED\n'
  printf 'REAL_FINANCIAL_AUTHORITY=0\n'
  exit "$rc"
}
trap rollback ERR INT TERM

[[ "${PRODUCT_SLICE_02_ORIENTATION_CONFIRM:-}" == YES ]] || fail CONFIRMATION_MISSING
[[ "$SOURCE_HEAD" =~ ^[0-9a-f]{40}$ ]] || fail SOURCE_HEAD_MISSING_OR_INVALID
[[ "$(git branch --show-current)" == main ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$EXPECTED_MAIN" ]] || fail MAIN_HEAD_CHANGED
[[ "$(git rev-parse origin/main)" == "$EXPECTED_MAIN" ]] || fail ORIGIN_MAIN_CHANGED
[[ "$(git rev-parse "origin/$BRANCH")" == "$SOURCE_HEAD" ]] || fail FIX_BRANCH_HEAD_CHANGED
[[ "$(git merge-base "$EXPECTED_MAIN" "$SOURCE_HEAD")" == "$EXPECTED_MAIN" ]] || fail FIX_BRANCH_BASE_INVALID
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN
[[ "$(git hash-object "$SERVER")" == 73b68c3d0bc18abf27966661791cf8369c8ff1cd ]] || fail SERVER_BLOB_CHANGED
[[ "$(git hash-object "$TEST")" == 5a1ba0ca7c03250dc17d362e5f0862d0627b9ac5 ]] || fail TEST_BLOB_CHANGED
systemctl is-active --quiet "$SERVICE" || fail SERVICE_NOT_ACTIVE
[[ "$(curl -sS --connect-timeout 5 --max-time 15 -o /dev/null -w '%{http_code}' http://127.0.0.1:8096/healthz 2>/dev/null || true)" == 200 ]] || fail LOCAL_HEALTH_NOT_200

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP=/root/tokenoskobi_product_slice_02_orientation_fix1_${STAMP}
mkdir -p "$BACKUP"
cp "$SERVER" "$BACKUP/server.py"
cp "$TEST" "$BACKUP/test.py"

PATCHED_SERVER="$BACKUP/server_patched.py"
PATCHED_TEST="$BACKUP/test_patched.py"
cp "$SERVER" "$PATCHED_SERVER"

PATCHED_SERVER="$PATCHED_SERVER" python3 - <<'PY'
from pathlib import Path
import os

p=Path(os.environ['PATCHED_SERVER'])
s=p.read_text(encoding='utf-8')

def replace_between(text,start,end,new,label):
    if text.count(start)!=1 or text.count(end)<1:
        raise SystemExit('BLOCKED=PATCH_ANCHOR_'+label)
    a=text.index(start)
    b=text.index(end,a)
    return text[:a]+new+text[b:]

market_tech='''def relationship_address(item,key):
    rel=((item.get('relationships') or {}).get(key) or {}).get('data') or {}
    rid=str(rel.get('id') or '')
    candidate=rid.rsplit('_',1)[-1].lower()
    return candidate if ADDR.fullmatch(candidate) else None


def oriented_pool(item,token):
    token=token.lower();a=item.get('attributes',{});base=relationship_address(item,'base_token');quote=relationship_address(item,'quote_token')
    side='base' if token==base else 'quote' if token==quote else None
    base_price=num(a.get('base_token_price_usd'));quote_price=num(a.get('quote_token_price_usd'))
    target_price=base_price if side=='base' else quote_price if side=='quote' else None
    return {
      'address':a.get('address') or item.get('id','').split('_')[-1],
      'name':a.get('name'),
      'reserve_usd':num(a.get('reserve_in_usd')),
      'price_usd':target_price,
      'base_token_price_usd':base_price,
      'quote_token_price_usd':quote_price,
      'base_token_address':base,
      'quote_token_address':quote,
      'target_token_address':token if side else None,
      'target_side':side,
      'orientation_verified':bool(side),
      'volume_24h_usd':num((a.get('volume_usd') or {}).get('h24')),
      'change_24h_pct':num((a.get('price_change_percentage') or {}).get('h24')),
    }


def market(token):
    base='https://api.geckoterminal.com/api/v2';out={'available':False,'token':{},'pools':[],'selected_pool':None,'target_orientation_verified':False,'errors':[]}
    try:
        a=request(f'{base}/networks/bsc/tokens/{token}')['data']['attributes'];out['token']={'name':a.get('name'),'symbol':a.get('symbol'),'price_usd':num(a.get('price_usd')),'market_cap_usd':num(a.get('market_cap_usd')),'fdv_usd':num(a.get('fdv_usd'))};out['available']=True
    except Exception as e:out['errors'].append('TOKEN:'+type(e).__name__)
    try:
        rows=[oriented_pool(item,token) for item in request(f'{base}/networks/bsc/tokens/{token}/pools?page=1').get('data',[])]
        rows.sort(key=lambda x:(1 if x.get('orientation_verified') else 0,x.get('reserve_usd') or 0),reverse=True)
        oriented=[x for x in rows if x.get('orientation_verified')]
        out['pools']=rows[:8];out['selected_pool']=oriented[0] if oriented else None;out['target_orientation_verified']=bool(oriented);out['available']=out['available'] or bool(rows)
        if rows and not oriented:out['errors'].append('TARGET_ASSET_ORIENTATION_UNVERIFIED')
    except Exception as e:out['errors'].append('POOLS:'+type(e).__name__)
    return out


def tech(pool,token):
    specs={'1m':('minute',1),'5m':('minute',5),'15m':('minute',15),'1h':('hour',1),'4h':('hour',4),'1d':('day',1)};out={};base='https://api.geckoterminal.com/api/v2';token=token.lower()
    if not pool:return {k:{'status':'VERI_YETERSIZ','target_token_address':token} for k in specs}
    for k,(tf,agg) in specs.items():
        try:
            selector=urllib.parse.quote(token,safe='')
            u=f'{base}/networks/bsc/pools/{pool}/ohlcv/{tf}?aggregate={agg}&limit=100&currency=usd&token={selector}'
            payload=request(u);meta=payload.get('meta') or {};base_addr=str((meta.get('base') or {}).get('address') or '').lower();quote_addr=str((meta.get('quote') or {}).get('address') or '').lower()
            if token not in {base_addr,quote_addr}:raise ValueError('TARGET_TOKEN_NOT_IN_OHLCV_META')
            side='base' if token==base_addr else 'quote'
            rows=payload['data']['attributes']['ohlcv_list'];cl=[num(x[4]) for x in rows if len(x)>=6 and num(x[4]) is not None];cl=list(reversed(cl))
            if len(cl)<3:out[k]={'status':'VERI_YETERSIZ','bars':len(cl),'target_token_address':token,'target_side':side};continue
            ch=(cl[-1]/cl[0]-1)*100 if cl[0] else None;fast=sum(cl[-5:])/min(5,len(cl));slow=sum(cl[-20:])/min(20,len(cl));trend='UP' if fast>slow*1.002 else 'DOWN' if fast<slow*.998 else 'FLAT';out[k]={'status':'OK','bars':len(cl),'last':cl[-1],'change_pct':round(ch,4) if ch is not None else None,'trend':trend,'target_token_address':token,'target_side':side}
        except Exception as e:out[k]={'status':'VERI_YETERSIZ','error':type(e).__name__+':'+str(e)[:80],'target_token_address':token}
    return out


'''
s=replace_between(s,'def market(token):\n','def news(token,meta):\n',market_tech,'MARKET_TECH')

decide='''def decide(c,m,t,n,p):
    block=[];warn=[];ev=[];score=50;selected=m.get('selected_pool') or {};target=selected.get('target_token_address');orientation=bool(m.get('target_orientation_verified') and selected.get('orientation_verified') and target)
    if c.get('code_exists') is False:block.append('CONTRACT_CODE_MISSING');score=100
    elif c.get('code_exists') is True:ev.append('CONTRACT_CODE_PRESENT');score-=10
    else:warn.append('CONTRACT_CODE_UNVERIFIED');score+=20
    if not orientation:block.append('TARGET_ASSET_ORIENTATION_UNVERIFIED');score=100
    liq=num(selected.get('reserve_usd'))
    if liq is None:warn.append('LIQUIDITY_UNVERIFIED');score+=20
    elif liq<5000:block.append('LIQUIDITY_BELOW_5000_USD');score+=35
    elif liq<50000:warn.append('LOW_LIQUIDITY');score+=15
    else:ev.append('LIQUIDITY_AT_LEAST_50000_USD');score-=15
    wrong=sum(1 for x in t.values() if x.get('status')=='OK' and x.get('target_token_address')!=target)
    ok=sum(1 for x in t.values() if x.get('status')=='OK' and x.get('target_token_address')==target)
    if wrong:block.append('TECHNICAL_TARGET_MISMATCH');score=100
    if ok<2:warn.append('TECHNICAL_DATA_INSUFFICIENT');score+=15
    elif ok>=4 and orientation and not wrong:ev.append('MULTI_TIMEFRAME_AVAILABLE');score-=5
    if p['public_rpc_ok']:ev.append('PUBLIC_RPC_FALLBACK_AVAILABLE')
    else:block.append('NO_BSC_RPC');score+=40
    if not p['hybrid_ready']:warn.append('ALCHEMY_HYBRID_NOT_READY');score+=5
    if not n['fresh']:warn.append('NEWS_STALE_OR_UNAVAILABLE');score+=5
    score=max(0,min(100,score));decision='BLOCK' if block else 'REVIEW' if len(warn)>=3 or score>=65 else 'WAIT' if score>=45 else 'ALLOW';quality='SUFFICIENT' if c.get('code_exists') is True and liq is not None and orientation and not wrong and ok>=2 else 'VERI_YETERSIZ'
    return {'decision':decision,'risk_score':score,'data_quality':quality,'blockers':block,'warnings':warn,'evidence':ev,'authority':'ADVISORY_ONLY'}


'''
s=replace_between(s,'def decide(c,m,t,n,p):\n','def analyze(token):\n',decide,'DECIDE')

analyze='''def analyze(token):
    token=token.lower();p=providers();c=contract(token,p);m=market(token);meta=c['metadata'];meta['name']=meta.get('name') or m['token'].get('name');meta['symbol']=meta.get('symbol') or m['token'].get('symbol');t=tech((m.get('selected_pool') or {}).get('address'),token);n=news(token,meta);d=decide(c,m,t,n,p);safe_p={k:v for k,v in p.items() if k!='selected'};safe_p['selected']={k:v for k,v in (p.get('selected') or {}).items() if k!='url'} or None
    return {'schema':'tokenoskobi.product_slice_02.packet.v1','generated_at_utc':now(),'chain':'BSC','token_address':token,'provider':safe_p,'contract':c,'market':m,'technical_timeframes':t,'news':n,'decision':d,'authority':{'paper':False,'live':False,'wallet':False,'signing':False,'order':False,'broadcast':False,'human_action_required':True}}


'''
s=replace_between(s,'def analyze(token):\n','HTML=',analyze,'ANALYZE')
p.write_text(s,encoding='utf-8')
PY

cat > "$PATCHED_TEST" <<'PYTEST'
import importlib.util,unittest
from pathlib import Path
p=Path('/root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_02_server.py');s=importlib.util.spec_from_file_location('m',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

BASE='0x'+'a'*40
QUOTE='0x'+'b'*40
POOL='0x'+'c'*40

def item():
 return {'id':'bsc_'+POOL,'attributes':{'address':POOL,'name':'BASE / QUOTE','reserve_in_usd':'1000000','base_token_price_usd':'571.05','quote_token_price_usd':'1.001','volume_usd':{'h24':'1000'},'price_change_percentage':{'h24':'1.2'}},'relationships':{'base_token':{'data':{'id':'bsc_'+BASE}},'quote_token':{'data':{'id':'bsc_'+QUOTE}}}}

class T(unittest.TestCase):
 def test_address(self):self.assertTrue(m.ADDR.fullmatch('0x'+'a'*40));self.assertFalse(m.ADDR.fullmatch('0x12'))
 def test_uint(self):self.assertEqual(m.uint('0x12'),18)
 def test_text(self):self.assertEqual(m.text('0x'+b'TKN'.ljust(32,b'\0').hex()),'TKN')
 def test_pool_base_orientation(self):
  r=m.oriented_pool(item(),BASE);self.assertEqual(r['target_side'],'base');self.assertEqual(r['price_usd'],571.05);self.assertTrue(r['orientation_verified'])
 def test_pool_quote_orientation(self):
  r=m.oriented_pool(item(),QUOTE);self.assertEqual(r['target_side'],'quote');self.assertEqual(r['price_usd'],1.001);self.assertTrue(r['orientation_verified'])
 def test_pool_unknown_orientation(self):
  r=m.oriented_pool(item(),'0x'+'d'*40);self.assertIsNone(r['target_side']);self.assertIsNone(r['price_usd']);self.assertFalse(r['orientation_verified'])
 def test_tech_uses_target_token_selector(self):
  seen=[];old=m.request
  def fake(url,body=None):
   seen.append(url);return {'data':{'attributes':{'ohlcv_list':[[3,570,580,560,575,100],[2,568,578,558,572,90],[1,565,575,555,570,80]]}},'meta':{'base':{'address':BASE},'quote':{'address':QUOTE}}}
  m.request=fake
  try:r=m.tech(POOL,BASE)
  finally:m.request=old
  self.assertEqual(len(seen),6);self.assertTrue(all('token='+BASE in u for u in seen));self.assertTrue(all(v['status']=='OK' and v['target_token_address']==BASE for v in r.values()))
 def test_decide_blocks_wrong_target(self):
  market={'selected_pool':{'reserve_usd':100000,'target_token_address':BASE,'orientation_verified':True},'target_orientation_verified':True}
  tech={'1m':{'status':'OK','target_token_address':QUOTE}}
  d=m.decide({'code_exists':True},market,tech,{'fresh':True},{'public_rpc_ok':1,'hybrid_ready':True});self.assertEqual(d['decision'],'BLOCK');self.assertIn('TECHNICAL_TARGET_MISMATCH',d['blockers'])
 def test_block(self):self.assertEqual(m.decide({'code_exists':False},{'selected_pool':None},{},{'fresh':False},{'public_rpc_ok':1,'hybrid_ready':False})['decision'],'BLOCK')
 def test_authority(self):self.assertTrue(all(v is False for v in m.CFG['authority'].values()))

if __name__=='__main__':unittest.main()
PYTEST

python3 -m py_compile "$PATCHED_SERVER" "$PATCHED_TEST"

cp "$PATCHED_SERVER" "$SERVER"
cp "$PATCHED_TEST" "$TEST"
chmod 0755 "$SERVER"
chmod 0644 "$TEST"
MODIFIED=1

python3 -m py_compile "$SERVER" "$TEST"
python3 -m unittest -v "$TEST"
git diff --check

SHADOW="$BACKUP/server_shadow.py"
cp "$SERVER" "$SHADOW"
SHADOW="$SHADOW" SHADOW_PORT="$SHADOW_PORT" python3 - <<'PY'
from pathlib import Path
import os
p=Path(os.environ['SHADOW']);s=p.read_text(encoding='utf-8')
old="CFG=json.loads((ROOT/'config/product_slice_02_v1.json').read_text())"
new=old+";CFG=dict(CFG);CFG['port']="+os.environ['SHADOW_PORT']
if s.count(old)!=1:raise SystemExit('BLOCKED=SHADOW_CONFIG_ANCHOR')
p.write_text(s.replace(old,new,1),encoding='utf-8')
PY
python3 "$SHADOW" >"$BACKUP/shadow.log" 2>&1 &
SHADOW_PID=$!
wait_http "http://127.0.0.1:${SHADOW_PORT}/healthz" 200 || fail SHADOW_NOT_READY

curl -sS --connect-timeout 5 --max-time 180 -H 'Content-Type: application/json' --data '{"token_address":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"}' "http://127.0.0.1:${SHADOW_PORT}/api/v1/analyze" > "$BACKUP/shadow_wbnb.json"
RESULT="$BACKUP/shadow_wbnb.json" WBNB="$WBNB" python3 - <<'PY'
import json,os
x=json.load(open(os.environ['RESULT']))
token=os.environ['WBNB'];m=x['market'];p=m['selected_pool'];t=x['technical_timeframes'];price=float(m['token']['price_usd']);pool_price=float(p['price_usd'])
assert m['target_orientation_verified'] is True
assert p['orientation_verified'] is True and p['target_token_address']==token and p['target_side'] in ('base','quote')
assert price>100 and pool_price>100 and 0.75 <= pool_price/price <= 1.25
ok=[v for v in t.values() if v.get('status')=='OK']
assert len(ok)>=4
assert all(v.get('target_token_address')==token and float(v['last'])>100 for v in ok)
assert 'TARGET_ASSET_ORIENTATION_UNVERIFIED' not in x['decision']['blockers']
assert 'TECHNICAL_TARGET_MISMATCH' not in x['decision']['blockers']
assert 'MULTI_TIMEFRAME_AVAILABLE' in x['decision']['evidence']
assert all(x['authority'][k] is False for k in ('paper','live','wallet','signing','order','broadcast'))
print('SHADOW_TARGET_ORIENTATION=PASS')
print('SHADOW_TARGET_SIDE='+p['target_side'])
print('SHADOW_TOKEN_PRICE_USD='+str(price))
print('SHADOW_POOL_TARGET_PRICE_USD='+str(pool_price))
print('SHADOW_TECH_OK='+str(len(ok)))
print('SHADOW_DECISION='+x['decision']['decision'])
PY
cleanup_shadow

OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value)
systemctl restart "$SERVICE"
wait_http http://127.0.0.1:8096/healthz 200 || fail PRODUCTION_NOT_READY
NEW_PID=$(systemctl show "$SERVICE" -p MainPID --value)
[[ "$NEW_PID" =~ ^[1-9][0-9]*$ && "$NEW_PID" != "$OLD_PID" ]] || fail PRODUCTION_PID_NOT_CHANGED

curl -sS --connect-timeout 5 --max-time 180 -H 'Content-Type: application/json' --data '{"token_address":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"}' http://127.0.0.1:8096/api/v1/analyze > "$BACKUP/production_wbnb.json"
RESULT="$BACKUP/production_wbnb.json" WBNB="$WBNB" python3 - <<'PY'
import json,os
x=json.load(open(os.environ['RESULT']))
token=os.environ['WBNB'];m=x['market'];p=m['selected_pool'];t=x['technical_timeframes'];price=float(m['token']['price_usd']);pool_price=float(p['price_usd'])
assert m['target_orientation_verified'] is True
assert p['orientation_verified'] is True and p['target_token_address']==token
assert price>100 and pool_price>100 and 0.75 <= pool_price/price <= 1.25
ok=[v for v in t.values() if v.get('status')=='OK']
assert len(ok)>=4 and all(v.get('target_token_address')==token and float(v['last'])>100 for v in ok)
assert 'TARGET_ASSET_ORIENTATION_UNVERIFIED' not in x['decision']['blockers']
assert 'TECHNICAL_TARGET_MISMATCH' not in x['decision']['blockers']
assert all(x['authority'][k] is False for k in ('paper','live','wallet','signing','order','broadcast'))
print('PRODUCTION_TARGET_ORIENTATION=PASS')
print('PRODUCTION_TARGET_SIDE='+p['target_side'])
print('PRODUCTION_TOKEN_PRICE_USD='+str(price))
print('PRODUCTION_POOL_TARGET_PRICE_USD='+str(pool_price))
print('PRODUCTION_TECH_OK='+str(len(ok)))
print('PRODUCTION_DECISION='+x['decision']['decision'])
PY

EXPECTED_STATUS=$' M tests/test_product_slice_02.py\n M tools/tokenoskobi_product_slice_02_server.py'
ACTUAL_STATUS=$(git status --short --untracked-files=all)
[[ "$ACTUAL_STATUS" == "$EXPECTED_STATUS" ]] || {
  printf 'EXPECTED_STATUS_BEGIN\n%s\nEXPECTED_STATUS_END\n' "$EXPECTED_STATUS"
  printf 'ACTUAL_STATUS_BEGIN\n%s\nACTUAL_STATUS_END\n' "$ACTUAL_STATUS"
  fail FINAL_WORKTREE_SCOPE_CHANGED
}

trap - ERR INT TERM
printf 'TARGET_ORIENTATION_FIX1_RESULT=SUCCESS\n'
printf 'OLD_PID=%s\n' "$OLD_PID"
printf 'NEW_PID=%s\n' "$NEW_PID"
printf 'SERVICE_ACTIVE=%s\n' "$(systemctl is-active "$SERVICE")"
printf 'PORT_8096=LOOPBACK_ONLY\n'
printf 'LOCAL_HEALTH_HTTP=200\n'
printf 'PHONE_UI_PREVIOUSLY_VERIFIED=true\n'
printf 'PHONE_DECISION_CORRECTNESS=RETEST_REQUIRED\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'
printf 'BACKUP_DIR=%s\n' "$BACKUP"
printf 'NEXT_SAFE_STEP=PHONE_AUTHENTICATED_WBNB_AND_NON_QUOTE_TOKEN_RETEST\n'
