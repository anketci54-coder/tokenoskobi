#!/usr/bin/env python3
# NEWS27A11 runner wrapper: original runner + persistent Haber Radar panel mapping
import os, sys, json, tempfile, subprocess
from collections import Counter

ORIGINAL_RUNNER = '/root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.py'
PREVIEW_DATA = '/root/tokenoskobi_clean_v1/_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096/public/news_radar_tr_preview/news_radar_tr_preview_data.json'
PREVIEW_HTML = '/root/tokenoskobi_clean_v1/_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096/public/news_radar_tr_preview/index.html'

def _find_news_key(d):
    if isinstance(d, list):
        return None, d
    if not isinstance(d, dict):
        return None, []
    for k in ["news","news_rows","items","rows","visible_news","preview_news","data"]:
        if isinstance(d.get(k), list):
            return k, d[k]
    for k, v in d.items():
        if isinstance(v, list) and (not v or isinstance(v[0], dict)):
            return k, v
    return None, []

def _classify(row):
    title = str(row.get("title") or row.get("original_title") or row.get("headline") or "")
    cat = str(row.get("category") or row.get("news_type") or row.get("type") or "")
    txt = (title + " " + cat).lower()
    critical = ["north korea","hack","exploit","rug","scam","stolen","ofac","attack","nobitex"]
    watch = ["risk","bug","quantum","concern","warning","loss","bearish","inflation","security","güvenlik"]
    if any(k in txt for k in critical):
        return "risk_top", "Kritik Risk", 100
    if any(k in txt for k in watch):
        return "risk_watch", "Risk İzle", 75
    return "general_info", "Bilgi", 20

def _atomic_write_json(path, data):
    folder = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix="news27a11_", suffix=".json", dir=folder)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(tmp, encoding="utf-8") as f:
        json.load(f)
    os.replace(tmp, path)

def _atomic_write_text(path, text):
    folder = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix="news27a11_", suffix=".html", dir=folder)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)

def _apply_panel_mapping_data():
    with open(PREVIEW_DATA, encoding="utf-8") as f:
        data = json.load(f)
    key, rows = _find_news_key(data)
    mapped = []
    for row in rows:
        lane, label, priority = _classify(row)
        item = dict(row)
        item["panel_lane"] = lane
        item["panel_display_label"] = label
        item["panel_priority"] = priority
        item["token_card_behavior"] = "NO_MATCH_GENERAL_ONLY"
        item["trade_signal"] = 0
        item["paper_signal"] = 0
        mapped.append(item)
    mapped = sorted(mapped, key=lambda x: int(x.get("panel_priority") or 0), reverse=True)
    if isinstance(data, dict):
        out = dict(data)
        out[key or "news"] = mapped
    else:
        out = {"news": mapped}
    out["_news27_runner_panel_mapping"] = {
        "active": True,
        "source": "NEWS27A11_RUNNER_WRAPPER",
        "lane_counts": dict(Counter(x.get("panel_lane") for x in mapped)),
        "display_counts": dict(Counter(x.get("panel_display_label") for x in mapped)),
        "token_card_linked": 0,
        "trade_signal": 0,
        "paper_signal": 0
    }
    _atomic_write_json(PREVIEW_DATA, out)
    return mapped

def _apply_panel_mapping_html(mapped):
    if not os.path.exists(PREVIEW_HTML):
        return
    with open(PREVIEW_HTML, encoding="utf-8", errors="replace") as f:
        html = f.read()
    c = Counter(x.get("panel_display_label") for x in mapped)
    marker_begin = "<!-- NEWS27_RUNNER_PANEL_MAPPING_BEGIN -->"
    marker_end = "<!-- NEWS27_RUNNER_PANEL_MAPPING_END -->"
    block = f"""{marker_begin}
<style>
.news27-runner-box{margin:14px 0;padding:12px;border:1px solid rgba(148,163,184,.35);border-radius:14px;background:rgba(15,23,42,.72)}
.news27-runner-badge{display:inline-block;margin:3px 6px 3px 0;padding:4px 9px;border-radius:999px;font-size:12px;border:1px solid rgba(148,163,184,.35)}
.news27-runner-critical{background:rgba(127,29,29,.35)}
.news27-runner-watch{background:rgba(113,63,18,.35)}
.news27-runner-info{background:rgba(30,41,59,.5)}
</style>
<script>
window.__TOKENOSKOBI_NEWS_PANEL_MAPPING_ACTIVE__=true;
</script>
<div class="news27-runner-box">
<strong>Haber görünürlük özeti</strong>
<span class="news27-runner-badge news27-runner-critical">Kritik Risk: {c.get("Kritik Risk",0)}</span>
<span class="news27-runner-badge news27-runner-watch">Risk İzle: {c.get("Risk İzle",0)}</span>
<span class="news27-runner-badge news27-runner-info">Bilgi: {c.get("Bilgi",0)}</span>
<span class="news27-runner-badge news27-runner-info">Token kartı bağlantısı: 0</span>
</div>
{marker_end}"""
    if marker_begin in html and marker_end in html:
        s = html.index(marker_begin)
        e = html.index(marker_end) + len(marker_end)
        html = html[:s] + block + html[e:]
    elif "</body>" in html:
        html = html.replace("</body>", block + "\n</body>", 1)
    else:
        html = html + "\n" + block + "\n"
    _atomic_write_text(PREVIEW_HTML, html)

def _postprocess():
    mapped = _apply_panel_mapping_data()
    _apply_panel_mapping_html(mapped)


# === TOKENOSKOBI WRAPPER URL EMPTY TOLERANCE V1 BEGIN ===
def _tok_wrap_raw_count_v1():
    import sqlite3
    con = sqlite3.connect("/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite")
    try:
        return int(con.execute("SELECT COUNT(*) FROM news_raw_feed_events").fetchone()[0])
    finally:
        con.close()

def _tok_wrap_latest_rows_v1(limit):
    import sqlite3
    con = sqlite3.connect("/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite")
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT rowid,* FROM news_raw_feed_events ORDER BY rowid DESC LIMIT ?",
            (int(limit),)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()

def _tok_wrap_has_real_url_v1(row):
    fields = ("url","link","href","source_url","original_url","article_url","canonical_url","external_url")
    for k in fields:
        v = row.get(k) if isinstance(row, dict) else None
        if v is not None and str(v).strip():
            return True
    return False

def _tok_wrap_has_title_v1(row):
    fields = ("title","headline","name")
    for k in fields:
        v = row.get(k) if isinstance(row, dict) else None
        if v is not None and str(v).strip():
            return True
    return False

def _tok_wrap_url_empty_tol_v1(rc, before_count, after_count):
    try:
        rc = int(rc)
        before_count = int(before_count)
        after_count = int(after_count)
    except Exception:
        return False

    if rc != 2:
        return False

    delta = after_count - before_count
    if delta <= 0 or delta > 100:
        return False

    rows = _tok_wrap_latest_rows_v1(delta)
    if len(rows) != delta:
        return False

    real_url_present = sum(1 for r in rows if _tok_wrap_has_real_url_v1(r))
    title_present = sum(1 for r in rows if _tok_wrap_has_title_v1(r))

    if real_url_present == 0 and title_present == len(rows):
        print(
            "TOKENOSKOBI_WRAPPER_URL_EMPTY_TOLERANCE_V1: converted rc2 to success; "
            f"delta={delta}; reason=NO_REAL_URL_BUT_TITLE_PRESENT; url_hash_not_link",
            flush=True,
        )
        return True

    return False
# === TOKENOSKOBI WRAPPER URL EMPTY TOLERANCE V1 END ===


# === TOKENOSKOBI WRAPPER TRACE V1 BEGIN ===
def _tok_wrap_trace_v1(label, extra=""):
    try:
        print(
            "TOKENOSKOBI_WRAPPER_TRACE_V1: "
            + str(label)
            + ((" | " + str(extra)) if extra else ""),
            flush=True,
        )
    except Exception:
        pass
# === TOKENOSKOBI WRAPPER TRACE V1 END ===

# === TOKENOSKOBI WRAPPER RC2 RAW DELTA TOLERANCE V1 BEGIN ===
def _tok_wrap_rc2_raw_delta_url_empty_ok_v1(before_count, after_count):
    try:
        import sqlite3
        db_path = "/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite"
        before = int(before_count or 0)
        after = int(after_count or 0)
        delta = after - before
        if delta <= 0 or delta > 100:
            return False

        con = sqlite3.connect("file:" + db_path + "?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        cols = [x[1] for x in con.execute("PRAGMA table_info(news_raw_feed_events)").fetchall()]

        real_url_cols = []
        for c in cols:
            cl = c.lower()
            if "hash" in cl:
                continue
            if c in ("url", "link", "href", "source_url", "original_url", "article_url", "canonical_url", "external_url"):
                real_url_cols.append(c)
            elif cl.endswith("_url") or cl.endswith("_link") or cl.endswith("_href"):
                real_url_cols.append(c)

        rows = [dict(x) for x in con.execute(
            "SELECT * FROM news_raw_feed_events ORDER BY rowid DESC LIMIT ?",
            (delta,)
        ).fetchall()]
        con.close()

        if len(rows) != delta:
            return False

        ok = 0
        for row in rows:
            title = str(row.get("title") or "").strip()
            url_hash = str(row.get("url_hash") or "").strip()
            real_url = ""
            for c in real_url_cols:
                real_url = str(row.get(c) or "").strip()
                if real_url:
                    break
            if title and url_hash and not real_url:
                ok += 1

        return ok == delta

    except Exception as e:
        try:
            _tok_wrap_trace_v1("rc2_raw_delta_tolerance_error", repr(e))
        except Exception:
            pass
        return False
# === TOKENOSKOBI WRAPPER RC2 RAW DELTA TOLERANCE V1 END ===


def main():
    _tok_wrap_trace_v1('main_enter')
    _tok_wrap_trace_v1('before_count_start')
    before_count = _tok_wrap_raw_count_v1()
    _tok_wrap_trace_v1('before_count_done', before_count)
    _tok_wrap_trace_v1('subprocess_start')
    rc = subprocess.run([sys.executable, ORIGINAL_RUNNER] + sys.argv[1:]).returncode
    after_count = _tok_wrap_raw_count_v1()
    _tok_wrap_trace_v1('after_count_done', after_count)
    # === TOKENOSKOBI WRAPPER RC2 RAW DELTA TOLERANCE V1 CALL ===
    if int(rc) == 2:
        after_count = _tok_wrap_raw_count_v1()
        _tok_wrap_trace_v1('after_count_done', after_count)
        _tok_wrap_trace_v1('rc2_raw_delta_tolerance_check', 'before='+str(before_count)+' after='+str(after_count))
        if _tok_wrap_rc2_raw_delta_url_empty_ok_v1(before_count, after_count):
            _tok_wrap_trace_v1('rc2_raw_delta_tolerance_convert', 'rc=2->0 raw_delta_url_empty_ok')
            return 0
    if rc != 0:
        _tok_wrap_trace_v1('tolerance_check', 'rc='+str(rc))
        if _tok_wrap_url_empty_tol_v1(rc, before_count, after_count):
            rc = 0
        else:
            _tok_wrap_trace_v1('return_rc', rc)
            return rc
    try:
        _tok_wrap_trace_v1('postprocess_point')
        # === TOKENOSKOBI WRAPPER POSTPROCESS RC2 RAW DELTA TOLERANCE V1 CALL ===
        try:
            _tok_wrap_trace_v1('postprocess_rc2_tolerance_check', f'rc={rc} before={before_count} after={after_count}')
            if int(rc) != 0:
                if _tok_wrap_rc2_raw_delta_url_empty_ok_v1(before_count, after_count):
                    _tok_wrap_trace_v1('postprocess_rc2_tolerance_convert', f'rc={rc}->0 before={before_count} after={after_count}')
                    rc = 0
        except Exception as e:
            _tok_wrap_trace_v1('postprocess_rc2_tolerance_error', repr(e))
        # === TOKENOSKOBI WRAPPER FINAL RETURN AFTER POSTPROCESS TOLERANCE V1 ===
        _tok_wrap_trace_v1('final_return_after_postprocess', str(rc))
        _tok_wrap_trace_v1('return_rc', str(rc))
        return rc
        _postprocess()
    except Exception as e:
        print("NEWS27A11_PANEL_MAPPING_POSTPROCESS_FAIL:", repr(e), file=sys.stderr)
        return 2
    return 0


# === TOKENOSKOBI WIRE ADAPTER V2 BEGIN ===
def tokenoskobi_news_source_adapter_bridge_dryrun_v2(rows, known_sources=None, existing_hashes=None):
    """
    Safe bridge for news source ingestion adapter.
    This function:
    - does not fetch
    - does not call API
    - does not write DB
    - does not touch timer/systemd
    - does not open paper/live trade
    """
    from pathlib import Path
    import sys

    base = Path("/root/tokenoskobi_clean_v1")
    tools = base / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))

    from news_source_ingestion_runner_adapter_v1 import simulate_adapter_batch

    return simulate_adapter_batch(
        rows,
        known_sources=known_sources or set(),
        existing_hashes=existing_hashes or set(),
    )
# === TOKENOSKOBI WIRE ADAPTER V2 END ===

if __name__ == "__main__":
    raise SystemExit(main())
