#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, tempfile

ROOT=Path("/root/tokenoskobi_clean_v1")
PANEL=ROOT/"active_panel_8096/current/data"
TARGET=PANEL/"lifecycle_center_live_readmodel_v1.json"
OUT=ROOT/"data/control/n16d_lifecycle_center_live_producer_result_v1.json"

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding="utf-8") as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".n16d_lifecycle_",suffix=".json",dir=str(p.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n")
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

model={
 "stage":"N16D_LIFECYCLE_CENTER_LIVE_PRODUCER",
 "generated_at_utc":now(),
 "producer":"tools/lifecycle_center_live_producer_v1.py",
 "decision":"LIFECYCLE_CENTER_DATA_MISSING",
 "data_freshness_sec":0,
 "authority":{"trade":False,"wallet_signing":False,"provider_call_from_browser":False,"policy_apply":False,"paper_trade_write":False},
 "source_count":0,
 "items":[{
   "key":"lifecycle_center","label":"Yaşam Destek Merkezi","status":"DATA_MISSING",
   "live_lifecycle_claim":False,
   "note":"Lifecycle runtime source is not active yet. Panel must show DATA_MISSING."
 }]
}
awrite(TARGET,model); awrite(OUT,model)
print("FINAL_GATE=PASS_N16D_LIFECYCLE_CENTER_LIVE_PRODUCER")
print("DECISION=LIFECYCLE_CENTER_DATA_MISSING")
print("JSON="+str(OUT.relative_to(ROOT)))
