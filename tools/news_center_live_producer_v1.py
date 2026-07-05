#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, tempfile

ROOT=Path("/root/tokenoskobi_clean_v1")
PANEL=ROOT/"active_panel_8096/current/data"
TARGET=PANEL/"news_center_live_readmodel_v1.json"
OUT=ROOT/"data/control/n16d_news_center_live_producer_result_v1.json"
MARKER=ROOT/"data/control/n12_news_sealed_inactive_runtime_marker_v1.json"

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding="utf-8") as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".n16d_news_",suffix=".json",dir=str(p.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n")
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

exists=MARKER.exists()
parsed=False; marker={}
if exists:
    try: marker=read_json(MARKER); parsed=True
    except Exception: parsed=False

decision="NEWS_CENTER_SEALED_INACTIVE" if exists and parsed else "NEWS_CENTER_DATA_MISSING"
model={
 "stage":"N16D_NEWS_CENTER_LIVE_PRODUCER",
 "generated_at_utc":now(),
 "producer":"tools/news_center_live_producer_v1.py",
 "decision":decision,
 "data_freshness_sec":0,
 "authority":{"trade":False,"wallet_signing":False,"provider_call_from_browser":False,"policy_apply":False,"paper_trade_write":False},
 "source_count":1 if exists and parsed else 0,
 "items":[{
   "key":"news_center","label":"Haber Akış Merkezi","status":decision,
   "source_marker_exists":exists,"source_marker_parse_ok":parsed,
   "live_news_claim":False,
   "note":"News runtime sealed inactive. Panel shows inactive truth, not fake live news."
 }]
}
awrite(TARGET,model); awrite(OUT,model)
print("FINAL_GATE=PASS_N16D_NEWS_CENTER_LIVE_PRODUCER")
print("DECISION="+decision)
print("JSON="+str(OUT.relative_to(ROOT)))
