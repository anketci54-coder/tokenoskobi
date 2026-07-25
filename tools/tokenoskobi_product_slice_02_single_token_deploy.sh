#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

ROOT=/root/tokenoskobi_clean_v1
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/tokenoskobi_product_slice_02_backup_${STAMP}.tar.gz"
RUNNER="tools/tokenoskobi_product_slice_02_single_token_deploy.sh"
SERVICE="tokenoskobi-product-slice-02.service"
OLD_SERVICE="tokenoskobi-active-panel-8096.service"
COMMITTED=0
OLD_ACTIVE=0
OLD_ENABLED=0

FILES=(
  config/product_slice_02_v1.json
  tools/tokenoskobi_product_slice_02_server.py
  tests/test_product_slice_02.py
  systemd_drafts/tokenoskobi-product-slice-02.service
  data/control/product_slice_02_single_token_decision_packet_v1.json
  data/control/product_slice_02_smoke_analysis_v1.json
  reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md
  03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md
  06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md
  PROJECT_RUNTIME.json PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  reports/LATEST_TK_AI_HANDOFF.md
)

rollback() {
  rc=$?
  trap - ERR
  echo "PRODUCT_SLICE_02_FAILED_RC=$rc"
  if [[ "$COMMITTED" -eq 0 ]]; then
    systemctl disable --now "$SERVICE" >/dev/null 2>&1 || true
    rm -f "/etc/systemd/system/$SERVICE"
    systemctl daemon-reload >/dev/null 2>&1 || true
    if [[ "$OLD_ENABLED" -eq 1 ]]; then systemctl enable "$OLD_SERVICE" >/dev/null 2>&1 || true; fi
    if [[ "$OLD_ACTIVE" -eq 1 ]]; then systemctl start "$OLD_SERVICE" >/dev/null 2>&1 || true; fi
    [[ -f "$BACKUP" ]] && tar -xzf "$BACKUP" -C "$ROOT"
    git reset --quiet >/dev/null 2>&1 || true
    git checkout -- . >/dev/null 2>&1 || true
    echo "ROLLBACK=COMPLETED"
  else
    echo "ROLLBACK=NOT_APPLIED_AFTER_COMMIT"
  fi
  exit "$rc"
}
trap rollback ERR

[[ "$(git branch --show-current)" == main ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]

python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('PROJECT_RUNTIME.json').read_text())
assert r.get('next_safe_step')=='PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET',r.get('next_safe_step')
assert r.get('no_new_era_until_product_completion') is True
print('PRODUCT_SLICE_02_PRECHECK=VERIFIED')
PY

if systemctl is-active --quiet "$OLD_SERVICE" 2>/dev/null; then OLD_ACTIVE=1; fi
if systemctl is-enabled --quiet "$OLD_SERVICE" 2>/dev/null; then OLD_ENABLED=1; fi
existing=()
for f in "${FILES[@]}" "$RUNNER"; do [[ -e "$f" ]] && existing+=("$f"); done
if [[ ${#existing[@]} -gt 0 ]]; then tar -czf "$BACKUP" -C "$ROOT" "${existing[@]}"; else tar -czf "$BACKUP" --files-from /dev/null; fi
echo "BACKUP=$BACKUP"
mkdir -p config tools tests systemd_drafts data/control reports

cat > config/product_slice_02_v1.json <<'EOF'
{
  "schema":"tokenoskobi.product_slice_02.config.v1",
  "host":"127.0.0.1",
  "port":8096,
  "chain_id":56,
  "timeout_sec":8,
  "news_stale_sec":21600,
  "rpc":[
    "https://bsc-dataseed.bnbchain.org",
    "https://bsc-dataseed-public.bnbchain.org",
    "https://bsc-dataseed.nariox.org",
    "https://bsc-dataseed.defibit.io"
  ],
  "authority":{"paper":false,"live":false,"wallet":false,"signing":false,"order":false,"broadcast":false}
}
EOF

cat > tools/tokenoskobi_product_slice_02_server.py <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,math,os,re,sqlite3,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
CFG=json.loads((ROOT/'config/product_slice_02_v1.json').read_text())
ADDR=re.compile(r'^0x[a-fA-F0-9]{40}$')
SEL={'name':'0x06fdde03','symbol':'0x95d89b41','decimals':'0x313ce567','supply':'0x18160ddd','owner':'0x8da5cb5b'}
DBS=[ROOT/'data/tokenoskobi_clean_v1.sqlite',ROOT/'data/tokenoskobi_v1.sqlite',ROOT/'data/tokenoskobi.sqlite',ROOT/'tokenoskobi.sqlite']
TABLES=('news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1')

def now(): return datetime.now(timezone.utc).isoformat()
def num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:return None

def request(url,body=None):
    h={'Accept':'application/json','User-Agent':'Tokenoskobi-Slice02/1'}; data=None; method='GET'
    if body is not None:
        data=json.dumps(body).encode();h['Content-Type']='application/json';method='POST'
    q=urllib.request.Request(url,data=data,headers=h,method=method)
    with urllib.request.urlopen(q,timeout=CFG['timeout_sec']) as r:return json.loads(r.read(2000000))

def rpc(url,method,params):
    x=request(url,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
    if x.get('error'):raise RuntimeError(str(x['error'])[:160])
    return x['result']

def alchemy():
    p=ROOT/'.secrets/alchemy_bnb.env'
    if p.exists():
        for line in p.read_text(errors='ignore').splitlines():
            if line.startswith('BSC_ALCHEMY_URL='):return line.split('=',1)[1].strip().strip('"').strip("'")
    return os.getenv('BSC_ALCHEMY_URL')

def providers():
    rows=[]; selected=None; urls=[]
    a=alchemy()
    if a:urls.append(('alchemy',a))
    urls += [(f'public_{i+1}',u) for i,u in enumerate(CFG['rpc'])]
    for name,url in urls:
        t=time.monotonic()
        try:
            chain=int(rpc(url,'eth_chainId',[]),16);block=int(rpc(url,'eth_blockNumber',[]),16)
            ok=chain==56;row={'name':name,'ok':ok,'block':block,'latency_ms':round((time.monotonic()-t)*1000,1)}
            if ok and selected is None:selected={'name':name,'url':url,'block':block}
        except Exception as e:row={'name':name,'ok':False,'error':type(e).__name__+':'+str(e)[:120]}
        rows.append(row)
    ao=any(x.get('name')=='alchemy' and x.get('ok') for x in rows);po=sum(1 for x in rows if x.get('name','').startswith('public_') and x.get('ok'))
    return {'rows':rows,'selected':selected,'alchemy_http_ok':ao,'public_rpc_ok':po,'hybrid_ready':bool(ao and po)}

def text(raw):
    if not raw or raw=='0x':return None
    try:b=bytes.fromhex(raw[2:])
    except Exception:return None
    if len(b)==32:return b.rstrip(b'\0').decode(errors='ignore').strip() or None
    if len(b)>=64:
        try:
            o=int.from_bytes(b[:32],'big');n=int.from_bytes(b[o:o+32],'big');return b[o+32:o+32+n].decode(errors='ignore').strip() or None
        except Exception:return None
    return None

def uint(raw):
    try:return int(raw,16) if raw and raw!='0x' else None
    except Exception:return None

def address(raw):
    if not raw or raw=='0x':return None
    v='0x'+raw.replace('0x','')[-40:].lower()
    return None if v=='0x'+'0'*40 else v

def contract(token,p):
    s=p.get('selected');out={'code_exists':None,'metadata':{},'errors':[]}
    if not s:out['errors'].append('NO_RPC');return out
    try:
        c=rpc(s['url'],'eth_getCode',[token,'latest']);out['code_exists']=c not in ('0x','0x0','')
    except Exception as e:out['errors'].append('CODE:'+str(e)[:100])
    raw={}
    for k,v in SEL.items():
        try:raw[k]=rpc(s['url'],'eth_call',[{'to':token,'data':v},'latest'])
        except Exception:raw[k]=None
    d=uint(raw['decimals']);sr=uint(raw['supply'])
    out['metadata']={'name':text(raw['name']),'symbol':text(raw['symbol']),'decimals':d,'total_supply':sr/(10**d) if sr is not None and d is not None and 0<=d<=36 else None,'owner':address(raw['owner'])}
    return out

def market(token):
    base='https://api.geckoterminal.com/api/v2';out={'available':False,'token':{},'pools':[],'selected_pool':None,'errors':[]}
    try:
        a=request(f'{base}/networks/bsc/tokens/{token}')['data']['attributes'];out['token']={'name':a.get('name'),'symbol':a.get('symbol'),'price_usd':num(a.get('price_usd')),'market_cap_usd':num(a.get('market_cap_usd')),'fdv_usd':num(a.get('fdv_usd'))};out['available']=True
    except Exception as e:out['errors'].append('TOKEN:'+type(e).__name__)
    try:
        rows=[]
        for item in request(f'{base}/networks/bsc/tokens/{token}/pools?page=1').get('data',[]):
            a=item.get('attributes',{});rows.append({'address':a.get('address') or item.get('id','').split('_')[-1],'name':a.get('name'),'reserve_usd':num(a.get('reserve_in_usd')),'price_usd':num(a.get('base_token_price_usd')),'volume_24h_usd':num((a.get('volume_usd') or {}).get('h24')),'change_24h_pct':num((a.get('price_change_percentage') or {}).get('h24'))})
        rows.sort(key=lambda x:x.get('reserve_usd') or 0,reverse=True);out['pools']=rows[:8];out['selected_pool']=rows[0] if rows else None;out['available']=out['available'] or bool(rows)
    except Exception as e:out['errors'].append('POOLS:'+type(e).__name__)
    return out

def tech(pool):
    specs={'1m':('minute',1),'5m':('minute',5),'15m':('minute',15),'1h':('hour',1),'4h':('hour',4),'1d':('day',1)};out={};base='https://api.geckoterminal.com/api/v2'
    if not pool:return {k:{'status':'VERI_YETERSIZ'} for k in specs}
    for k,(tf,agg) in specs.items():
        try:
            u=f'{base}/networks/bsc/pools/{pool}/ohlcv/{tf}?aggregate={agg}&limit=100&currency=usd';rows=request(u)['data']['attributes']['ohlcv_list'];cl=[num(x[4]) for x in rows if len(x)>=6 and num(x[4]) is not None];cl=list(reversed(cl))
            if len(cl)<3:out[k]={'status':'VERI_YETERSIZ','bars':len(cl)};continue
            ch=(cl[-1]/cl[0]-1)*100 if cl[0] else None;fast=sum(cl[-5:])/min(5,len(cl));slow=sum(cl[-20:])/min(20,len(cl));trend='UP' if fast>slow*1.002 else 'DOWN' if fast<slow*.998 else 'FLAT';out[k]={'status':'OK','bars':len(cl),'last':cl[-1],'change_pct':round(ch,4) if ch is not None else None,'trend':trend}
        except Exception as e:out[k]={'status':'VERI_YETERSIZ','error':type(e).__name__}
    return out

def news(token,meta):
    terms={token.lower()};terms|={str(meta.get(k)).lower() for k in ('name','symbol') if meta.get(k)};db=next((x for x in DBS if x.exists()),None);out={'database':str(db.relative_to(ROOT)) if db else None,'fresh':False,'matches':[],'latest':None}
    if not db:return out
    latest=0
    try:
        c=sqlite3.connect(f'file:{db}?mode=ro',uri=True);c.execute('PRAGMA query_only=ON')
        for table in TABLES:
            if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone():continue
            cols=[x[1] for x in c.execute(f'PRAGMA table_info("{table}")')]
            for row in c.execute(f'SELECT * FROM "{table}" ORDER BY rowid DESC LIMIT 100'):
                rec={cols[i]:row[i] if isinstance(row[i],(str,int,float,type(None))) else str(row[i]) for i in range(len(cols))};blob=json.dumps(rec,ensure_ascii=False).lower()
                if any(t in blob for t in terms) and len(out['matches'])<20:out['matches'].append({'table':table,'record':rec})
                for v in rec.values():
                    if isinstance(v,str):
                        try:
                            ts=datetime.fromisoformat(v.replace('Z','+00:00')).timestamp()
                            if ts>latest:latest=ts;out['latest']=datetime.fromtimestamp(ts,timezone.utc).isoformat()
                        except Exception:pass
        c.close()
    except Exception as e:out['error']=type(e).__name__+':'+str(e)[:120]
    if latest:out['age_sec']=round(time.time()-latest,1);out['fresh']=out['age_sec']<=CFG['news_stale_sec']
    return out

def decide(c,m,t,n,p):
    block=[];warn=[];ev=[];score=50
    if c.get('code_exists') is False:block.append('CONTRACT_CODE_MISSING');score=100
    elif c.get('code_exists') is True:ev.append('CONTRACT_CODE_PRESENT');score-=10
    else:warn.append('CONTRACT_CODE_UNVERIFIED');score+=20
    liq=num((m.get('selected_pool') or {}).get('reserve_usd'))
    if liq is None:warn.append('LIQUIDITY_UNVERIFIED');score+=20
    elif liq<5000:block.append('LIQUIDITY_BELOW_5000_USD');score+=35
    elif liq<50000:warn.append('LOW_LIQUIDITY');score+=15
    else:ev.append('LIQUIDITY_AT_LEAST_50000_USD');score-=15
    ok=sum(1 for x in t.values() if x.get('status')=='OK')
    if ok<2:warn.append('TECHNICAL_DATA_INSUFFICIENT');score+=15
    elif ok>=4:ev.append('MULTI_TIMEFRAME_AVAILABLE');score-=5
    if p['public_rpc_ok']:ev.append('PUBLIC_RPC_FALLBACK_AVAILABLE')
    else:block.append('NO_BSC_RPC');score+=40
    if not p['hybrid_ready']:warn.append('ALCHEMY_HYBRID_NOT_READY');score+=5
    if not n['fresh']:warn.append('NEWS_STALE_OR_UNAVAILABLE');score+=5
    score=max(0,min(100,score));decision='BLOCK' if block else 'REVIEW' if len(warn)>=3 or score>=65 else 'WAIT' if score>=45 else 'ALLOW';quality='SUFFICIENT' if c.get('code_exists') is True and liq is not None and ok>=2 else 'VERI_YETERSIZ'
    return {'decision':decision,'risk_score':score,'data_quality':quality,'blockers':block,'warnings':warn,'evidence':ev,'authority':'ADVISORY_ONLY'}

def analyze(token):
    token=token.lower();p=providers();c=contract(token,p);m=market(token);meta=c['metadata'];meta['name']=meta.get('name') or m['token'].get('name');meta['symbol']=meta.get('symbol') or m['token'].get('symbol');t=tech((m.get('selected_pool') or {}).get('address'));n=news(token,meta);d=decide(c,m,t,n,p);safe_p={k:v for k,v in p.items() if k!='selected'};safe_p['selected']={k:v for k,v in (p.get('selected') or {}).items() if k!='url'} or None
    return {'schema':'tokenoskobi.product_slice_02.packet.v1','generated_at_utc':now(),'chain':'BSC','token_address':token,'provider':safe_p,'contract':c,'market':m,'technical_timeframes':t,'news':n,'decision':d,'authority':{'paper':False,'live':False,'wallet':False,'signing':False,'order':False,'broadcast':False,'human_action_required':True}}

HTML='''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tokenoskobi</title><style>body{margin:0;background:#091019;color:#e8eef5;font-family:system-ui}.w{max-width:1100px;margin:auto;padding:18px}.box{background:#111b27;border:1px solid #2a3b4e;border-radius:15px;padding:18px;margin:12px 0}input,button{padding:14px;border-radius:10px;border:1px solid #3b5068;background:#0b131c;color:white;font-size:16px}input{width:min(720px,70%)}button{background:#dbeaff;color:#06101a;font-weight:800}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.card{background:#0b131c;border-radius:12px;padding:13px}.ALLOW{color:#75eca2}.WAIT{color:#ffd173}.REVIEW{color:#ffa56d}.BLOCK{color:#ff7784}pre{white-space:pre-wrap;word-break:break-word}@media(max-width:700px){.grid{grid-template-columns:1fr}input{width:100%;margin-bottom:8px}}</style></head><body><main class="w"><h2>TOKENOSKOBİ — Tek Token Karar Paketi</h2><div class="box">BSC token adresi: <input id="a" placeholder="0x…"><button onclick="go()">Analiz Et</button><p id="s"></p></div><div id="r"></div></main><script>const e=x=>String(x??'—').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));async function go(){s.textContent='Gerçek veriler toplanıyor…';r.innerHTML='';try{let z=await fetch('/api/v1/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token_address:a.value.trim()})}),d=await z.json();if(!z.ok)throw Error(d.error);let q=d.decision,m=d.contract.metadata,p=d.market.selected_pool||{};r.innerHTML=`<div class="grid"><div class="card"><b>Karar</b><h1 class="${e(q.decision)}">${e(q.decision)}</h1>${e(q.data_quality)}</div><div class="card"><b>Risk</b><h1>${e(q.risk_score)}/100</h1></div><div class="card"><b>Token</b><h1>${e(m.symbol)}</h1>${e(m.name)}</div></div><div class="box"><b>Fiyat / Likidite</b><p>${e(d.market.token.price_usd)} USD / ${e(p.reserve_usd)} USD</p><b>Uyarılar</b><p>${e(q.warnings.join(' • '))}</p><b>Kanıt</b><p>${e(q.evidence.join(' • '))}</p></div><details class="box"><summary>Ham paket</summary><pre>${e(JSON.stringify(d,null,2))}</pre></details>`;s.textContent='Karar paketi üretildi';}catch(x){s.textContent=x.message}}</script></body></html>'''

class H(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def sendj(self,code,obj,typ='application/json; charset=utf-8'):
        b=(json.dumps(obj,ensure_ascii=False) if not isinstance(obj,str) else obj).encode();self.send_response(code);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.send_header('X-Frame-Options','DENY');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b)
    def do_GET(self):
        p=urllib.parse.urlsplit(self.path).path
        if p=='/healthz':return self.sendj(200,{'ok':True,'authority':'READ_ONLY_ADVISORY'})
        if p in ('/','/panel','/panel/','/panel/panel_v2','/panel/panel_v2/'):return self.sendj(200,HTML,'text/html; charset=utf-8')
        self.sendj(404,{'error':'NOT_FOUND'})
    def do_POST(self):
        if urllib.parse.urlsplit(self.path).path!='/api/v1/analyze':return self.sendj(404,{'error':'NOT_FOUND'})
        try:
            n=int(self.headers.get('Content-Length','0'));assert 0<n<=4096;d=json.loads(self.rfile.read(n));a=d.get('token_address','')
            if not ADDR.fullmatch(a):return self.sendj(400,{'error':'INVALID_BSC_TOKEN_ADDRESS'})
            self.sendj(200,analyze(a))
        except Exception as e:self.sendj(500,{'error':'ANALYSIS_FAILED','detail':type(e).__name__+':'+str(e)[:140]})

a=CFG['authority']
if __name__=='__main__':
    assert CFG['host']=='127.0.0.1' and all(a[k] is False for k in ('paper','live','wallet','signing','order','broadcast'))
    ThreadingHTTPServer((CFG['host'],CFG['port']),H).serve_forever()
PY
chmod 0755 tools/tokenoskobi_product_slice_02_server.py

cat > tests/test_product_slice_02.py <<'PY'
import importlib.util,unittest
from pathlib import Path
p=Path('/root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_02_server.py');s=importlib.util.spec_from_file_location('m',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class T(unittest.TestCase):
 def test_address(self):self.assertTrue(m.ADDR.fullmatch('0x'+'a'*40));self.assertFalse(m.ADDR.fullmatch('0x12'))
 def test_uint(self):self.assertEqual(m.uint('0x12'),18)
 def test_text(self):self.assertEqual(m.text('0x'+b'TKN'.ljust(32,b'\0').hex()),'TKN')
 def test_block(self):self.assertEqual(m.decide({'code_exists':False},{'selected_pool':None},{},{'fresh':False},{'public_rpc_ok':1,'hybrid_ready':False})['decision'],'BLOCK')
 def test_authority(self):self.assertTrue(all(v is False for v in m.CFG['authority'].values()))
if __name__=='__main__':unittest.main()
PY

cat > systemd_drafts/tokenoskobi-product-slice-02.service <<'EOF'
[Unit]
Description=Tokenoskobi Product Slice 02 Read-Only Decision Packet
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=root
WorkingDirectory=/root/tokenoskobi_clean_v1
ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_02_server.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadOnlyPaths=/root/tokenoskobi_clean_v1
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
CapabilityBoundingSet=
[Install]
WantedBy=multi-user.target
EOF

python3 -m py_compile tools/tokenoskobi_product_slice_02_server.py tests/test_product_slice_02.py
python3 -m unittest -v tests/test_product_slice_02.py
cp systemd_drafts/tokenoskobi-product-slice-02.service "/etc/systemd/system/$SERVICE"
systemctl daemon-reload
systemctl disable --now "$OLD_SERVICE" >/dev/null 2>&1 || true
systemctl enable --now "$SERVICE"
sleep 3
systemctl is-active --quiet "$SERVICE"
curl -fsS --max-time 5 http://127.0.0.1:8096/healthz >/tmp/s02_health.json
curl -fsS --max-time 5 http://127.0.0.1:8096/panel/panel_v2/ >/tmp/s02_panel.html
grep -q 'Tek Token Karar Paketi' /tmp/s02_panel.html
LISTEN="$(ss -ltnp 'sport = :8096' | tail -n +2 | head -n1)"
echo "$LISTEN" | grep -q '127.0.0.1:8096'
! echo "$LISTEN" | grep -Eq '0\.0\.0\.0:8096|\[::\]:8096'

SMOKE=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c
CODE="$(curl -sS --max-time 90 -o /tmp/s02_smoke.json -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' http://127.0.0.1:8096/api/v1/analyze || true)"
[[ "$CODE" == 200 ]]
cp /tmp/s02_smoke.json data/control/product_slice_02_smoke_analysis_v1.json
EXT="$(curl -k -sS --max-time 12 -o /tmp/s02_ext.html -w '%{http_code}' https://panel.coinoskobi.xyz/panel/panel_v2/ || true)"
case "$EXT" in 200|401|403);;*) echo "BLOCKED=EXTERNAL_HTTP_$EXT";exit 1;;esac

python3 - "$EXT" "$LISTEN" <<'PY'
import json,re,sys
from datetime import datetime,timezone
from pathlib import Path
root=Path('/root/tokenoskobi_clean_v1');ext,listen=sys.argv[1:3];now=datetime.now(timezone.utc).isoformat();sm=json.loads((root/'data/control/product_slice_02_smoke_analysis_v1.json').read_text());p=sm['provider'];d=sm['decision'];n=sm['news'];remaining=[]
if ext=='200':remaining.append('PANEL_AUTH_NOT_PROVEN')
if not p['alchemy_http_ok']:remaining.append('ALCHEMY_HTTP_NOT_WORKING')
if not p['hybrid_ready']:remaining.append('HYBRID_RPC_NOT_READY')
if not n['fresh']:remaining.append('NEWS_NOT_FRESH_WITHIN_6H')
remaining+=['UFW_FAIL2BAN_SSH_HARDENING_PENDING_ACCESS_SAFE_APPLY','NGINX_RATE_LIMIT_NOT_PROVEN']
a={'schema':'tokenoskobi.product_slice_02.deployment.v1','stage':'PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET','status':'DEPLOYED_VERIFIED_WITH_REMAINING_BLOCKERS','generated_at_utc':now,'visible_product':{'external_url':'https://panel.coinoskobi.xyz/panel/panel_v2/','external_http_code':ext,'single_token_input':True,'real_decision_packet':True,'timeframes':['1m','5m','15m','1h','4h','1d'],'explicit_insufficient_data':True},'security':{'listen':listen,'loopback_only':True,'external_8096_binding_fixed':True,'remaining_blockers':remaining},'smoke':{'token_address':sm['token_address'],'decision':d['decision'],'data_quality':d['data_quality'],'risk_score':d['risk_score'],'public_rpc_ok':p['public_rpc_ok'],'alchemy_http_ok':p['alchemy_http_ok'],'hybrid_ready':p['hybrid_ready'],'news_fresh':n['fresh']},'authority':{'paper_runtime':'DISABLED','live_trade':'DISABLED','wallet_authority':0,'signing_authority':0,'order_create_authority':0,'real_financial_authority':0},'next_safe_step':'PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING'}
(root/'data/control/product_slice_02_single_token_decision_packet_v1.json').write_text(json.dumps(a,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
(root/'reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md').write_text(f"# PRODUCT SLICE 02\n\n- Status: `{a['status']}`\n- URL: `{a['visible_product']['external_url']}`\n- 8096 loopback-only: `true`\n- Smoke: `{d['decision']}` / `{d['data_quality']}`\n- Public RPC / Alchemy / Hybrid: `{p['public_rpc_ok']}` / `{p['alchemy_http_ok']}` / `{p['hybrid_ready']}`\n- NEWS fresh: `{n['fresh']}`\n- Authority: `DISABLED / 0`\n- Next: `{a['next_safe_step']}`\n")

def load(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
rp=root/'PROJECT_RUNTIME.json';r=load(rp);r['current_stage']=a['stage'];r['current_status']=a['status'];r['next_safe_step']=a['next_safe_step'];r['last_result']=a['status'];r['product_slice_02']=a;r['updated_at_utc']=now;dump(rp,r)
hp=root/'PROJECT_HISTORY.json';h=load(hp);h.setdefault('events',[]).append({'event':'PRODUCT_SLICE_02_DEPLOYED','event_id':'PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET_V1','timestamp_utc':now,'status':a['status'],'artifact':'data/control/product_slice_02_single_token_decision_packet_v1.json','authority_change':False,'next_safe_step':a['next_safe_step']});dump(hp,h)
mp=root/'data/tokenoskobi_v1_v8_master_era_roadmap.json';m=load(mp);m['current_stage']=a['stage'];m['current_status']=a['status'];m['next_safe_step']=a['next_safe_step'];m['product_slice_02']=a;m['updated_at_utc']=now;dump(mp,m)
sp=root/'data/control/latest_tk_machine_state.json';s=load(sp);c=s.setdefault('canonical_runtime_pointer',{});c['current_stage']=a['stage'];c['current_status']=a['status'];c['next_safe_step']=a['next_safe_step'];c['product_slice_02']=a;s['updated_at_utc']=now;dump(sp,s)
section=f'''<!-- PRODUCT_SLICE_02:BEGIN -->\n## Product Slice 02 — Tek Token Karar Paketi\n\n- Status: `{a['status']}`\n- URL: `{a['visible_product']['external_url']}`\n- Tek token gerçek karar paketi: `true`\n- 8096: `LOOPBACK_ONLY`\n- Smoke: `{d['decision']}` / `{d['data_quality']}`\n- Public RPC / Alchemy / Hybrid: `{p['public_rpc_ok']}` / `{p['alchemy_http_ok']}` / `{p['hybrid_ready']}`\n- NEWS fresh: `{n['fresh']}`\n- Authority: `PAPER_DISABLED; LIVE_DISABLED; REAL_FINANCIAL_AUTHORITY_0`\n- Next: `{a['next_safe_step']}`\n<!-- PRODUCT_SLICE_02:END -->'''
for name in ('03_ROADMAP.md','04_ALMANAC.md','05_ATLAS.md','06_PROJECT_MASTER_STATE.md','07_PROJECT_HANDOFF.md','reports/LATEST_TK_AI_HANDOFF.md'):
 pth=root/name;old=pth.read_text();pat=re.compile(r'<!-- PRODUCT_SLICE_02:BEGIN -->.*?<!-- PRODUCT_SLICE_02:END -->',re.S);new=pat.sub(section,old) if pat.search(old) else old.splitlines()[0]+'\n\n'+section+'\n\n'+'\n'.join(old.splitlines()[1:])+'\n';pth.write_text(new)
print('PRODUCT_SLICE_02_CANONICAL_UPDATE=VERIFIED')
PY

python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('PROJECT_RUNTIME.json').read_text());a=json.loads(Path('data/control/product_slice_02_single_token_decision_packet_v1.json').read_text());s=json.loads(Path('data/control/product_slice_02_smoke_analysis_v1.json').read_text())
assert r['next_safe_step']=='PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING'
assert a['security']['loopback_only'] is True
assert all(v in (0,'DISABLED') for v in a['authority'].values())
assert all(s['authority'][k] is False for k in ('paper','live','wallet','signing','order','broadcast'))
print('PRODUCT_SLICE_02_VALIDATION=VERIFIED')
PY

rm -f tools/.tokenoskobi_product_slice_02_deploy_payload.zlib "$RUNNER"
git add config/product_slice_02_v1.json tools/tokenoskobi_product_slice_02_server.py tests/test_product_slice_02.py systemd_drafts/tokenoskobi-product-slice-02.service data/control/product_slice_02_single_token_decision_packet_v1.json data/control/product_slice_02_smoke_analysis_v1.json 03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md PROJECT_RUNTIME.json PROJECT_HISTORY.json data/tokenoskobi_v1_v8_master_era_roadmap.json data/control/latest_tk_machine_state.json
git add -f reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md reports/LATEST_TK_AI_HANDOFF.md
git add -A tools/.tokenoskobi_product_slice_02_deploy_payload.zlib "$RUNNER"
git diff --cached --check
git commit -m "Product: deploy single-token decision packet"
COMMITTED=1
git push origin main
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
python3 - <<'PY'
import json
from pathlib import Path
a=json.loads(Path('data/control/product_slice_02_single_token_decision_packet_v1.json').read_text())
print('PRODUCT_SLICE_02=DEPLOYED_VERIFIED_GITHUB_SEALED')
print('EXTERNAL_URL='+a['visible_product']['external_url'])
print('EXTERNAL_HTTP_CODE='+a['visible_product']['external_http_code'])
print('PANEL_8096_LOOPBACK_ONLY=true')
print('SINGLE_TOKEN_INPUT=true')
print('REAL_DECISION_PACKET=true')
print('SMOKE_DECISION='+a['smoke']['decision'])
print('SMOKE_DATA_QUALITY='+a['smoke']['data_quality'])
print('PUBLIC_RPC_OK='+str(a['smoke']['public_rpc_ok']))
print('ALCHEMY_HTTP_OK='+str(a['smoke']['alchemy_http_ok']).lower())
print('HYBRID_READY='+str(a['smoke']['hybrid_ready']).lower())
print('NEWS_FRESH='+str(a['smoke']['news_fresh']).lower())
print('PAPER_RUNTIME=DISABLED')
print('LIVE_TRADE=DISABLED')
print('REAL_FINANCIAL_AUTHORITY=0')
print('NEXT_SAFE_STEP='+a['next_safe_step'])
PY
echo REMOTE_VERIFY=VERIFIED
echo WORKTREE=CLEAN
echo HEAD="$(git rev-parse HEAD)"
