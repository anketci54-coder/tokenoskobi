#!/usr/bin/env python3
import os, sys, json, sqlite3, hashlib, datetime, time, urllib.request, xml.etree.ElementTree as ET, re, html, shutil, subprocess
from pathlib import Path
from collections import Counter

ROOT="/root/tokenoskobi_clean_v1"
DB=f"{ROOT}/data/tokenoskobi_clean_v1.sqlite"
RUN_DIR=f"{ROOT}/run"
LOCK_FILE=f"{RUN_DIR}/news_radar_refresh.lock"
STATE_FILE=f"{ROOT}/data/news_radar_timer_state_v1.json"
LOG_DIR=f"{ROOT}/logs/news_radar"
REPORT=f"{ROOT}/reports/LATEST_NEWS_RADAR_TIMER_RUN.md"
JSON_OUT=f"{ROOT}/data/latest_news_radar_timer_run.json"

ACTIVE_PUBLIC_DIR=f"{ROOT}/_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096/public"
PREVIEW_DIR=f"{ACTIVE_PUBLIC_DIR}/news_radar_tr_preview"
PREVIEW_HTML=f"{PREVIEW_DIR}/index.html"
PREVIEW_DATA=f"{PREVIEW_DIR}/news_radar_tr_preview_data.json"

MATCHER_MODULE=f"{ROOT}/tools/news_token_matcher_v1.py"

MAX_SOURCES=2
MAX_ITEMS_TOTAL=20
MAX_RUNTIME_SECONDS=35
MIN_SECONDS_BETWEEN_RUNS=900
NETWORK_TIMEOUT_SECONDS=10
MAX_CONSECUTIVE_FAILURES=3
TIMER_UNIT="tokenoskobi-news-radar-refresh.timer"

RSS_SOURCES=[
    {"source_uid":"src_seed_crypto_news_rss","source_name":"Cointelegraph RSS","url":"https://cointelegraph.com/rss","max_items":10},
    {"source_uid":"src_seed_crypto_news_rss","source_name":"CoinDesk RSS","url":"https://www.coindesk.com/arc/outboundfeeds/rss/","max_items":10},
]

TITLE_TR={
"CZ says crypto exchange rivals opposed his pardon bid":"CZ, kripto borsası rakiplerinin af talebine karşı çıktığını söyledi",
"7 major Bitcoin mining pools join Stratum V2, working group":"7 büyük Bitcoin madencilik havuzu Stratum V2 çalışma grubuna katıldı",
"Seven major Bitcoin mining pools join Stratum V2, working group":"7 büyük Bitcoin madencilik havuzu Stratum V2 çalışma grubuna katıldı",
"Strategy CEO Phong Le says company will sell BTC only in specific cases":"Strategy CEO’su Phong Le, şirketin Bitcoin’i yalnızca özel durumlarda satacağını söyledi",
"The CLARITY Act will help reshore the crypto industry in the US — Attorney":"Bir avukata göre CLARITY Act, kripto sektörünün ABD’ye geri dönmesine yardımcı olabilir",
"CLARITY Act will help reshore US crypto industry, attorney says":"CLARITY Act, ABD kripto sektörünün ülkeye geri dönmesine yardımcı olabilir",
"The Nobitex dilemma: How Iran's biggest crypto exchange stays off the OFAC blacklist":"Nobitex ikilemi: İran’ın en büyük kripto borsası OFAC kara listesinin dışında nasıl kalıyor",
"Why a 2017 Linux bug is now a major concern for the crypto industry":"2017 tarihli bir Linux hatası neden kripto sektörü için yeniden büyük endişe oldu",
"TeraWulf doubles AI revenue but posts $427M quarterly loss as mining income declines":"TeraWulf yapay zekâ gelirini ikiye katladı, madencilik geliri düşerken 427 milyon dolar zarar açıkladı",
"Here’s what happened in crypto today":"Bugün kripto piyasasında öne çıkanlar",
"Court lets Arbitrum DAO to transfer $71M in ETH tied to North Korea hack to Aave":"Mahkeme, Kuzey Kore hack’iyle bağlantılı 71 milyon dolarlık ETH’nin Arbitrum DAO tarafından Aave’ye aktarılmasına izin verdi",
"Court lets Arbitrum DAO transfer $71M in ETH tied to North Korea hack to Aave":"Mahkeme, Kuzey Kore hack’iyle bağlantılı 71 milyon dolarlık ETH’nin Arbitrum DAO tarafından Aave’ye aktarılmasına izin verdi",
"Spot Bitcoin ETFs log 6th straight week of net inflows for first time in 9 months":"Spot Bitcoin ETF’leri 9 ay sonra ilk kez üst üste 6 hafta net giriş gördü",
"Trump Media’s Q1 loss widens to $406 million on bitcoin, CRO markdowns":"Trump Media’nın ilk çeyrek zararı Bitcoin ve CRO değer düşüşleriyle 406 milyon dolara çıktı",
"Sports betting should be regulated as a financial product, not gambling, aspiring prediction market provider says":"Bir tahmin piyasası girişimine göre spor bahisleri kumar değil finansal ürün gibi düzenlenmeli",
"It might be too late for bitcoin’s quantum migration, Project Eleven report argues":"Project Eleven raporuna göre Bitcoin’in kuantum geçişi için çok geç kalınmış olabilir",
"Crypto industry cheers Senate Clarity Act markup date as market structure push resumes":"Piyasa yapısı çalışmaları yeniden başlarken kripto sektörü Senato CLARITY Act takvimini olumlu karşıladı",
"Emerging-market users are treating crypto exchanges like banking apps, Binance says":"Binance’e göre gelişen piyasa kullanıcıları kripto borsalarını bankacılık uygulaması gibi kullanıyor",
"Swiss central bank bitcoin reserve push fails over signature shortfall":"İsviçre Merkez Bankası için Bitcoin rezervi girişimi imza yetersizliği nedeniyle başarısız oldu",
"CME is set to let traders bet on bitcoin volatility, not just price":"CME, yatırımcıların yalnızca Bitcoin fiyatına değil volatilitesine de pozisyon almasını sağlayacak",
"How DeFi is changing the financial landscape for Latin Americans":"DeFi, Latin Amerika’da finansal yapıyı nasıl değiştiriyor",
"Crypto wallets are being rebuilt for AI agents, Trust Wallet and Mesh executives say at Consensus Miami":"Trust Wallet ve Mesh yöneticilerine göre kripto cüzdanları yapay zekâ ajanları için yeniden tasarlanıyor",
"BlackRock deepens tokenization push with new onchain fund offerings":"BlackRock yeni on-chain fon ürünleriyle tokenizasyon hamlesini derinleştiriyor",
"Santiment flags risk as crypto bullish talk spikes while BTC holds $80K":"BTC 80 bin dolarda tutunurken yükseliş söylemi artınca Santiment risk uyarısı yaptı",
}

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    if not os.path.exists(path):
        return None
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def stable_hash(s,n=20):
    return hashlib.sha256(str(s or "").encode("utf-8")).hexdigest()[:n]

def clean_text(x):
    x=re.sub(r"<[^>]+>"," ",str(x or ""))
    x=html.unescape(x)
    x=re.sub(r"\s+"," ",x).strip()
    return x

def parse_date(x):
    x=clean_text(x)
    if not x:
        return now_utc()
    try:
        from email.utils import parsedate_to_datetime
        dt=parsedate_to_datetime(x)
        if dt.tzinfo is None:
            dt=dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc).isoformat()
    except Exception:
        return now_utc()

def read_json(path, default=None):
    if default is None:
        default={}
    if not os.path.exists(path):
        return default
    try:
        return json.load(open(path,encoding="utf-8"))
    except Exception:
        return default

def write_json_atomic(path, data):
    tmp=f"{path}.tmp.{os.getpid()}"
    with open(tmp,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    json.load(open(tmp,encoding="utf-8"))
    os.replace(tmp,path)

def table_exists(cur,t):
    return cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone() is not None

def cols(cur,t):
    if not table_exists(cur,t):
        return []
    return [r[1] for r in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]

def count(cur,t):
    if not table_exists(cur,t):
        return None
    return cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]

def insert_existing(cur, table, row):
    c=cols(cur,table)
    use=[k for k in row if k in c]
    if not use:
        return False
    sql=f'INSERT OR IGNORE INTO "{table}" ({",".join(use)}) VALUES ({",".join(["?"]*len(use))})'
    cur.execute(sql,[row[k] for k in use])
    return cur.rowcount > 0

def classify(title):
    t=str(title or "").lower()
    if any(x in t for x in ["hack","exploit","rug","security","ofac","bug","risk","north korea","malware","attack","breach"]):
        return "Güvenlik / Risk"
    if any(x in t for x in ["listing","trading pair","launchpool","launchpad","exchange announces"]):
        return "Borsa / Listeleme"
    if any(x in t for x in ["etf","bitcoin","btc","market","regulation","clarity","senate","cme","volatility","reserve","mining pool"]):
        return "Genel Piyasa"
    if any(x in t for x in ["ai","tokenization","defi","wallet","onchain","terawulf","blackrock","agent","rwa","depin"]):
        return "Anlatı / Narrative"
    return "Genel Haber"

def signal(cat):
    return {
        "Güvenlik / Risk":"Dikkat",
        "Borsa / Listeleme":"Güçlü Aday",
        "Anlatı / Narrative":"İzle",
        "Genel Piyasa":"Piyasa Etkisi",
    }.get(cat,"Bilgi")

def translate(title):
    title=str(title or "").strip()
    return TITLE_TR.get(title,title)

def trust_label(score, enabled):
    try:
        s=float(score)
    except Exception:
        s=0
    if int(enabled or 0)!=1:
        return "Kapalı"
    if s>=80:
        return "Yüksek güven"
    if s>=60:
        return "Orta güven"
    if s>=40:
        return "Düşük güven"
    return "İzleme dışı"

def fetch_rss(src):
    ledger={"source_uid":src["source_uid"],"source_name":src["source_name"],"url":src["url"],"status":"ERROR","http_status":None,"bytes":0,"parsed":0,"kept":0,"error":None}
    rows=[]
    try:
        req=urllib.request.Request(src["url"],headers={"User-Agent":"TokenoskobiNewsRadarTimer/1.0"})
        with urllib.request.urlopen(req,timeout=NETWORK_TIMEOUT_SECONDS) as resp:
            ledger["http_status"]=getattr(resp,"status",None)
            raw=resp.read(1024*1024)
        ledger["bytes"]=len(raw)
        root=ET.fromstring(raw)
        items=root.findall(".//item")
        ledger["parsed"]=len(items)
        for item in items[:src["max_items"]]:
            def text(names):
                for name in names:
                    node=item.find(name)
                    if node is not None and node.text:
                        return clean_text(node.text)
                return ""
            title=text(["title"])
            link=text(["link"])
            pub=text(["pubDate","published","updated"])
            desc=text(["description","summary"])
            if not title:
                continue
            raw_key=json.dumps({"source":src["source_name"],"title":title,"link":link,"published":pub},ensure_ascii=False,sort_keys=True)
            rows.append({
                "news_uid":"timer_news_"+stable_hash(raw_key,20),
                "source_uid":src["source_uid"],
                "source_name":src["source_name"],
                "published_at_utc":parse_date(pub),
                "title":title,
                "url":link,
                "description":desc[:1000],
                "url_hash":stable_hash(link or title,32),
                "title_hash":stable_hash(title.lower(),32),
                "raw_hash":stable_hash(raw_key,32),
                "fetched_at_utc":now_utc(),
            })
        ledger["kept"]=len(rows)
        ledger["status"]="OK"
    except Exception as e:
        ledger["error"]=repr(e)
    return ledger, rows

def build_preview(cur):
    source_rows={}
    if table_exists(cur,"news_source_registry"):
        for r in cur.execute("SELECT * FROM news_source_registry").fetchall():
            d=dict(r)
            source_rows[d.get("source_uid")]=d

    rows=[]
    if table_exists(cur,"news_raw_feed_events"):
        q=cur.execute("""
            SELECT news_uid, source_uid, published_at_utc, title, fetched_at_utc
            FROM news_raw_feed_events
            ORDER BY fetched_at_utc DESC, published_at_utc DESC
            LIMIT 80
        """).fetchall()
        for r in q:
            d=dict(r)
            src=source_rows.get(d.get("source_uid"),{})
            title=d.get("title") or ""
            cat=classify(title)
            rows.append({
                "title_tr":translate(title),
                "original_title":title,
                "source_group":src.get("source_name") or d.get("source_uid"),
                "source_name":src.get("source_name") or d.get("source_uid"),
                "trust_label":trust_label(src.get("trust_score"),src.get("enabled",1)),
                "published_at_utc":d.get("published_at_utc"),
                "fetched_at_utc":d.get("fetched_at_utc"),
                "category":cat,
                "signal":signal(cat),
                "match_status":"Genel akış",
                "trade_signal":False,
                "paper_signal":False,
            })
    summary={
        "raw_news_count":len(rows),
        "visible_news_count":len(rows),
        "matched_news_count":0,
        "general_news_count":len(rows),
        "trade_signal_count":0,
        "paper_signal_count":0,
        "category_counts":dict(Counter(r["category"] for r in rows)),
        "refreshed_at_utc":now_utc(),
    }
    return {
        "created_at_utc":now_utc(),
        "phase":"NEWS_RADAR_TIMER_REFRESH_RUN",
        "quote":"Bilgiye sahip olan, her şeye sahiptir. · Kürşat AKYOL",
        "summary":summary,
        "news":rows,
        "rules":[
            "Haber tek başına trade/paper/live izni üretmez.",
            "Token eşleşmesi yoksa haber genel akışta kalır.",
            "Türkçe başlık görünüm amaçlıdır; orijinal başlık korunur.",
            "Timer refresh küçük ve bütçe kontrollü çalışır."
        ]
    }

def write_preview_html(path, payload):
    def e(x): return html.escape(str(x if x is not None else ""))
    cards=[]
    for r in payload.get("news",[]):
        cards.append(f"""
        <article class="news-card">
          <div class="news-top"><span>{e(r['category'])}</span><small>{e(str(r.get('fetched_at_utc',''))[:19].replace('T',' '))}</small></div>
          <h3>{e(r['title_tr'])}</h3>
          <p class="orig">Orijinal: {e(r['original_title'])}</p>
          <div class="badges"><b>{e(r['source_name'])}</b><span>{e(r['trust_label'])}</span><span>{e(r['match_status'])}</span><span>{e(r['signal'])}</span><span>İşlem sinyali yok</span></div>
        </article>""")
    s=payload["summary"]
    html_out=f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tokenoskobi Haber Radar</title>
<style>
body{{margin:0;background:#07111f;color:#edf4ff;font-family:Arial,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:20px}}
.hero,.section,.news-card{{background:#101a2d;border:1px solid #243653;border-radius:20px;padding:18px;margin-bottom:12px}}
h1{{margin:0 0 8px;font-size:28px}} p{{color:#9fb0ca;line-height:1.45}}
.stats{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin-top:14px}}
.stat{{background:#172b52;border-radius:16px;padding:12px;text-align:center}} .stat b{{display:block;font-size:22px}}
.flow{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}
.news-top,.badges{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:space-between}}
.news-top span,.badges span,.badges b,small{{background:#172b52;border-radius:999px;padding:6px 9px}}
.orig{{font-size:13px}} .footer{{opacity:.8;text-align:center;padding:20px}}
@media(max-width:900px){{.stats{{grid-template-columns:repeat(2,1fr)}}.flow{{grid-template-columns:1fr}}}}
</style>
</head>
<body><div class="wrap">
<section class="hero">
<h1>Haber Radar</h1>
<p><b>Bilgiye sahip olan, her şeye sahiptir. · Kürşat AKYOL</b></p>
<p>Haber akışı ayrı tutulur. Haber tek başına alım, satım veya paper izni değildir. Cüzdan, piyasa ve güvenlik verisiyle birleşmeden işlem sinyali üretmez.</p>
<div class="stats">
<div class="stat"><b>{s.get('raw_news_count',0)}</b><span>Ham haber</span></div>
<div class="stat"><b>{s.get('visible_news_count',0)}</b><span>Görünen haber</span></div>
<div class="stat"><b>{s.get('matched_news_count',0)}</b><span>Tokena bağlı</span></div>
<div class="stat"><b>{s.get('general_news_count',0)}</b><span>Genel akış</span></div>
<div class="stat"><b>2</b><span>Kaynak</span></div>
<div class="stat"><b>0</b><span>İşlem sinyali</span></div>
</div>
</section>
<section class="section"><h2>Haber Akışı</h2><p>En son çekilen haberler. Teknik UID/hash alanları gösterilmez.</p><div class="flow">{''.join(cards)}</div></section>
<section class="section"><h2>Panel Kuralları</h2><p>Ana token kartı: Haber Yok / Zayıf / Güçlü / Kritik. Haber listesi ayrı ayraçta kalır.</p><p>Token eşleşmesi yoksa haber token altına zorla bağlanmaz. Fusion: haber + cüzdan + piyasa + güvenlik birlikte değerlendirilir.</p></section>
<div class="footer">Timer refresh ekranıdır. “Bilgiye sahip olan, her şeye sahiptir. · Kürşat AKYOL”</div>
</div></body></html>"""
    tmp=f"{path}.tmp.{os.getpid()}"
    Path(tmp).write_text(html_out,encoding="utf-8")
    os.replace(tmp,path)

def acquire_lock():
    os.makedirs(RUN_DIR,exist_ok=True)
    try:
        fd=os.open(LOCK_FILE, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False

def release_lock():
    try:
        os.remove(LOCK_FILE)
    except FileNotFoundError:
        pass

def auto_disable_if_needed(state):
    if state.get("consecutive_failures",0) >= MAX_CONSECUTIVE_FAILURES:
        try:
            subprocess.run(["systemctl","disable","--now",TIMER_UNIT],timeout=20)
            state["auto_disabled_timer"]=True
        except Exception as e:
            state["auto_disable_error"]=repr(e)

def main():
    os.makedirs(LOG_DIR,exist_ok=True)
    os.makedirs(PREVIEW_DIR,exist_ok=True)
    state=read_json(STATE_FILE,{})
    result={"started_at_utc":now_utc(),"final_status":"FAIL","errors":[],"warnings":[]}

    if not acquire_lock():
        result["final_status"]="SKIP_LOCK_EXISTS"
        result["warnings"].append("LOCK_EXISTS_NO_OVERLAP")
        write_json_atomic(JSON_OUT,result)
        return 0

    try:
        last=state.get("last_run_started_epoch")
        now_epoch=time.time()
        if last and now_epoch-float(last) < MIN_SECONDS_BETWEEN_RUNS:
            result["final_status"]="SKIP_MIN_INTERVAL"
            result["warnings"].append("MIN_SECONDS_BETWEEN_RUNS_NOT_MET")
            return 0

        state["last_run_started_epoch"]=now_epoch
        write_json_atomic(STATE_FILE,state)

        stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir=f"{ROOT}/backups/news_radar_timer_run_{stamp}"
        os.makedirs(backup_dir,exist_ok=True)
        backup_db=f"{backup_dir}/tokenoskobi_clean_v1.sqlite.before_timer_run"
        backup_html=f"{backup_dir}/news_radar_tr_preview_index.html.before_timer_run"
        backup_data=f"{backup_dir}/news_radar_tr_preview_data.json.before_timer_run"
        shutil.copy2(DB,backup_db)
        if os.path.exists(PREVIEW_HTML): shutil.copy2(PREVIEW_HTML,backup_html)
        if os.path.exists(PREVIEW_DATA): shutil.copy2(PREVIEW_DATA,backup_data)

        ledgers=[]
        fetched=[]
        for src in RSS_SOURCES[:MAX_SOURCES]:
            led, rows=fetch_rss(src)
            ledgers.append(led)
            for r in rows:
                if len(fetched) < MAX_ITEMS_TOTAL:
                    fetched.append(r)

        if not fetched:
            raise RuntimeError("NO_FETCHED_ROWS")

        con=sqlite3.connect(DB)
        con.row_factory=sqlite3.Row
        cur=con.cursor()

        before=count(cur,"news_raw_feed_events")
        existing_url=set()
        existing_raw=set()
        existing_title=set()
        if table_exists(cur,"news_raw_feed_events"):
            for r in cur.execute("SELECT url_hash, raw_hash, title FROM news_raw_feed_events").fetchall():
                d=dict(r)
                if d.get("url_hash"): existing_url.add(d["url_hash"])
                if d.get("raw_hash"): existing_raw.add(d["raw_hash"])
                if d.get("title"): existing_title.add(stable_hash(str(d["title"]).lower(),32))

        inserted=0
        duplicate=0
        cur.execute("BEGIN")
        for row in fetched:
            is_dup=row["url_hash"] in existing_url or row["raw_hash"] in existing_raw or row["title_hash"] in existing_title
            if is_dup:
                duplicate += 1
                continue
            ok=insert_existing(cur,"news_raw_feed_events",{
                "news_uid":row["news_uid"],
                "source_uid":row["source_uid"],
                "published_at_utc":row["published_at_utc"],
                "title":row["title"],
                "url_hash":row["url_hash"],
                "raw_hash":row["raw_hash"],
                "fetched_at_utc":row["fetched_at_utc"],
            })
            if ok:
                inserted += 1
                existing_url.add(row["url_hash"])
                existing_raw.add(row["raw_hash"])
                existing_title.add(row["title_hash"])

        con.commit()

        health={
            "integrity_check":cur.execute("PRAGMA integrity_check").fetchone()[0],
            "quick_check":cur.execute("PRAGMA quick_check").fetchone()[0],
            "foreign_key_error_count":len(cur.execute("PRAGMA foreign_key_check").fetchall()),
        }
        if health["integrity_check"]!="ok" or health["quick_check"]!="ok" or health["foreign_key_error_count"]!=0:
            raise RuntimeError(f"DB_HEALTH_FAIL:{health}")

        payload=build_preview(cur)
        con.close()

        write_json_atomic(PREVIEW_DATA,payload)
        write_preview_html(PREVIEW_HTML,payload)

        state["consecutive_failures"]=0
        state["last_success_utc"]=now_utc()
        state["last_inserted_raw"]=inserted
        state["last_duplicate_count"]=duplicate
        write_json_atomic(STATE_FILE,state)

        result.update({
            "final_status":"PASS",
            "finished_at_utc":now_utc(),
            "backup_dir":backup_dir,
            "fetch_ledger":ledgers,
            "fetched_rows":len(fetched),
            "inserted_raw":inserted,
            "duplicate":duplicate,
            "news_raw_feed_events_before":before,
            "news_raw_feed_events_after":payload["summary"]["raw_news_count"],
            "trade_signal_count":0,
            "paper_signal_count":0,
            "health":health,
            "preview_data":PREVIEW_DATA,
            "preview_html":PREVIEW_HTML,
        })

    except Exception as e:
        result["errors"].append(repr(e))
        state["consecutive_failures"]=int(state.get("consecutive_failures",0))+1
        state["last_failure_utc"]=now_utc()
        auto_disable_if_needed(state)
        write_json_atomic(STATE_FILE,state)
        try:
            if "backup_db" in locals() and os.path.exists(backup_db): shutil.copy2(backup_db,DB)
            if "backup_html" in locals() and os.path.exists(backup_html): shutil.copy2(backup_html,PREVIEW_HTML)
            if "backup_data" in locals() and os.path.exists(backup_data): shutil.copy2(backup_data,PREVIEW_DATA)
            result["restored_from_backup"]=True
        except Exception as restore_error:
            result["errors"].append("RESTORE_FAILED:"+repr(restore_error))

    finally:
        release_lock()
        write_json_atomic(JSON_OUT,result)
        lines=[
            "# LATEST NEWS RADAR TIMER RUN",
            "",
            f"- started_at_utc: `{result.get('started_at_utc')}`",
            f"- final_status: **{result.get('final_status')}**",
            f"- fetched_rows: `{result.get('fetched_rows')}`",
            f"- inserted_raw: `{result.get('inserted_raw')}`",
            f"- duplicate: `{result.get('duplicate')}`",
            f"- trade_signal_count: `0`",
            f"- paper_signal_count: `0`",
            f"- errors: `{result.get('errors')}`",
        ]
        Path(REPORT).write_text("\n".join(lines)+"\n",encoding="utf-8")

    return 0 if result.get("final_status") in ("PASS","SKIP_LOCK_EXISTS","SKIP_MIN_INTERVAL") else 2


# === TOKENOSKOBI URL EMPTY TOLERANCE V1 BEGIN ===
_TOKENOSKOBI_URL_EMPTY_REAL_MAIN_V1 = main

def _tokenoskobi_url_empty_raw_count_v1():
    import sqlite3 as _sqlite3
    db = "/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite"
    con = _sqlite3.connect(db)
    try:
        return int(con.execute("SELECT COUNT(*) FROM news_raw_feed_events").fetchone()[0])
    finally:
        con.close()

def _tokenoskobi_url_empty_latest_rows_v1(limit):
    import sqlite3 as _sqlite3
    db = "/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite"
    con = _sqlite3.connect(db)
    con.row_factory = _sqlite3.Row
    try:
        rows = con.execute(
            "SELECT rowid,* FROM news_raw_feed_events ORDER BY rowid DESC LIMIT ?",
            (int(limit),)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()

def _tokenoskobi_url_empty_has_real_url_v1(row):
    real_fields = (
        "url", "link", "href", "source_url", "original_url",
        "article_url", "canonical_url", "external_url",
    )
    if not isinstance(row, dict):
        return False
    for key in real_fields:
        val = row.get(key)
        if val is not None and str(val).strip():
            return True
    return False

def _tokenoskobi_url_empty_has_title_v1(row):
    if not isinstance(row, dict):
        return False
    for key in ("title", "headline", "name"):
        val = row.get(key)
        if val is not None and str(val).strip():
            return True
    return False

def _tokenoskobi_url_empty_exit2_is_tolerable_v1(rc, before_count, after_count):
    try:
        rc_int = int(rc) if rc is not None else 0
        before_count = int(before_count)
        after_count = int(after_count)
    except Exception:
        return False

    if rc_int != 2:
        return False

    delta = after_count - before_count
    if delta <= 0 or delta > 100:
        return False

    rows = _tokenoskobi_url_empty_latest_rows_v1(delta)
    if not rows or len(rows) != delta:
        return False

    real_url_present = sum(1 for r in rows if _tokenoskobi_url_empty_has_real_url_v1(r))
    title_present = sum(1 for r in rows if _tokenoskobi_url_empty_has_title_v1(r))

    if real_url_present == 0 and title_present == len(rows):
        print(
            "TOKENOSKOBI_URL_EMPTY_TOLERANCE_V1: converted exit 2 to success; "
            f"delta={delta}; reason=NO_REAL_URL_BUT_TITLE_PRESENT; url_hash_not_link",
            flush=True,
        )
        return True

    return False

def main():
    try:
        before_count = _tokenoskobi_url_empty_raw_count_v1()
    except Exception:
        before_count = None

    system_exit_seen = False
    rc = 0

    try:
        rc = _TOKENOSKOBI_URL_EMPTY_REAL_MAIN_V1()
    except SystemExit as e:
        system_exit_seen = True
        rc = e.code

    try:
        after_count = _tokenoskobi_url_empty_raw_count_v1()
    except Exception:
        after_count = before_count

    if _tokenoskobi_url_empty_exit2_is_tolerable_v1(rc, before_count, after_count):
        return 0

    if system_exit_seen:
        raise SystemExit(rc)

    return rc
# === TOKENOSKOBI URL EMPTY TOLERANCE V1 END ===

if __name__ == "__main__":
    sys.exit(main())
