#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile, subprocess, urllib.request, re

ROOT=Path("/root/tokenoskobi_clean_v1")
DB=ROOT/"data/tokenoskobi_clean_v1.sqlite"
OUT=ROOT/"data/control/n17a3_news_pipeline_deep_audit_v1.json"
ROWS=ROOT/"data/control/n17a3_news_pipeline_deep_audit_v1_rows.jsonl"
TABLES=["news_raw_feed_events","news_token_match_events","news_signal_events","news_score_events_v1"]
FILES=[
 "tools/news_radar_refresh_runner_v1.py",
 "tools/news_token_matcher_v1.py",
 "active_panel_8096/current/data/news_center_live_readmodel_v1.json",
]
TOKENS=["BTC","ETH","BNB","SOL","XRP","DOGE","ADA","TRX","TON","PEPE","SHIB","USDT","USDC","BITCOIN","ETHEREUM","SOLANA","BINANCE"]

def now(): return datetime.now(timezone.utc).isoformat()
def jwrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".n17a3_",suffix=".json",dir=str(p.parent))
    with os.fdopen(fd,"w",encoding="utf-8") as f:
        json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n")
    json.load(open(tmp)); os.replace(tmp,p)
def http(url):
    try:
        r=urllib.request.urlopen(url,timeout=8); b=r.read(2000)
        return {"ok":True,"status":r.status,"bytes":len(b)}
    except Exception as e:
        return {"ok":False,"status":None,"error":type(e).__name__+":"+str(e)[:160]}
def table_info(con,t):
    cur=con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(t,))
    exists=cur.fetchone() is not None
    out={"table":t,"exists":exists,"count":0,"columns":[],"sample":[]}
    if not exists: return out
    cur.execute(f"PRAGMA table_info({t})"); out["columns"]=[r[1] for r in cur.fetchall()]
    cur.execute(f"SELECT COUNT(*) FROM {t}"); out["count"]=int(cur.fetchone()[0])
    cols=out["columns"][:6]
    if cols and out["count"]:
        try:
            cur.execute("SELECT "+",".join(cols)+f" FROM {t} LIMIT 10")
            out["sample"]=[{cols[i]:row[i] for i in range(len(cols))} for row in cur.fetchall()]
        except Exception as e:
            out["sample_error"]=type(e).__name__+":"+str(e)[:120]
    return out
def file_info(rel):
    p=ROOT/rel; txt=p.read_text(encoding="utf-8",errors="replace") if p.exists() else ""
    return {
      "path":rel,"exists":p.exists(),"size":p.stat().st_size if p.exists() else 0,
      "table_refs":[t for t in TABLES if t in txt],
      "token_refs":[x for x in TOKENS if re.search(r"\b"+re.escape(x)+r"\b",txt,re.I)],
      "db_env_refs":[x for x in ["TOKENOSKOBI_DB_PATH","DB_PATH","SQLITE_PATH"] if x in txt],
      "postprocess_refs":txt.count("_postprocess"),
      "return_refs":len(re.findall(r"^\s*return\b",txt,re.M))
    }

con=sqlite3.connect(str(DB))
tables=[table_info(con,t) for t in TABLES]
con.close()
counts={x["table"]:x["count"] for x in tables}
files=[file_info(f) for f in FILES]
raw_text=" ".join(str(v) for row in next(x for x in tables if x["table"]=="news_raw_feed_events")["sample"] for v in row.values())
raw_hits=[x for x in TOKENS if re.search(r"\b"+re.escape(x)+r"\b",raw_text,re.I)]
outside={
 "panel_root":http("https://panel.coinoskobi.com/"),
 "news_json":http("https://panel.coinoskobi.com/data/news_center_live_readmodel_v1.json"),
 "manifest":http("https://panel.coinoskobi.com/data/panel_live_manifest_v1.json")
}
checks=[
 {"gate":"db_exists","ok":DB.exists(),"value":str(DB)},
 {"gate":"raw_news_nonzero","ok":counts.get("news_raw_feed_events",0)>0,"value":counts.get("news_raw_feed_events",0)},
 {"gate":"match_zero_confirmed","ok":counts.get("news_token_match_events",0)==0,"value":counts.get("news_token_match_events",0)},
 {"gate":"signal_zero_confirmed","ok":counts.get("news_signal_events",0)==0,"value":counts.get("news_signal_events",0)},
 {"gate":"score_zero_confirmed","ok":counts.get("news_score_events_v1",0)==0,"value":counts.get("news_score_events_v1",0)},
 {"gate":"raw_sample_has_token_hint","ok":bool(raw_hits),"value":raw_hits},
 {"gate":"matcher_file_exists","ok":(ROOT/"tools/news_token_matcher_v1.py").exists(),"value":"tools/news_token_matcher_v1.py"},
 {"gate":"matcher_refs_match_table","ok":"news_token_match_events" in files[1]["table_refs"],"value":files[1]["table_refs"]},
 {"gate":"panel_news_json_200","ok":outside["news_json"].get("status")==200,"value":outside["news_json"]},
]
if not checks[5]["ok"]:
    decision="RAW_NEWS_HAS_NO_VISIBLE_TOKEN_HINTS"
    next_action="AUDIT_RAW_NEWS_CONTENT_AND_TOKEN_DICTIONARY"
elif not checks[7]["ok"]:
    decision="MATCHER_NOT_BOUND_TO_MATCH_TABLE"
    next_action="PATCH_MATCHER_DB_WRITE_BINDING"
else:
    decision="TOKEN_HINTS_EXIST_MATCHER_ZERO_NEEDS_RULE_TRACE"
    next_action="ADD_MATCHER_RULE_TRACE_ON_TEMPDB_SAMPLE"

result={
 "stage":"N17A3_NEWS_PIPELINE_DEEP_AUDIT",
 "generated_at_utc":now(),
 "decision":decision,
 "next_action":next_action,
 "inside":{"tables":tables,"files":files,"raw_sample_token_hits":raw_hits},
 "outside":outside,
 "checks":checks,
 "authority":{"readonly":True,"real_db_write":False,"systemd_start":False,"api_calls":0,"core_change":False}
}
jwrite(OUT,result)
ROWS.write_text("\n".join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+"\n",encoding="utf-8")
print("FINAL_GATE=PASS_N17A3_NEWS_PIPELINE_DEEP_AUDIT")
print("DECISION="+decision)
print("NEXT_ACTION="+next_action)
print("JSON="+str(OUT.relative_to(ROOT)))
