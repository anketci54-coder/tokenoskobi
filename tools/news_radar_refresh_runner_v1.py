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



# === TOKENOSKOBI NEWS DOWNSTREAM HOOK V1 BEGIN ===
def _tok_wrap_news_now_v1():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def _tok_wrap_news_stable_hash_v1(*parts):
    import hashlib
    s = "||".join("" if x is None else str(x).strip().lower() for x in parts)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _tok_wrap_news_table_exists_v1(con, table):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone() is not None

def _tok_wrap_news_pick_v1(row, *names):
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return ""

def _tok_wrap_news_load_tokens_v1(con):
    cur = con.cursor()
    out = []
    if not _tok_wrap_news_table_exists_v1(con, "token_score_100_events"):
        return out

    rows = cur.execute(
        "SELECT * FROM token_score_100_events ORDER BY score_total DESC LIMIT 5000"
    ).fetchall()

    for r in rows:
        d = dict(r)
        token_uid = _tok_wrap_news_pick_v1(d, "token_uid")
        pair_uid = _tok_wrap_news_pick_v1(d, "pair_uid")
        chain = _tok_wrap_news_pick_v1(d, "chain")
        symbol = ""
        name = ""
        token_address = ""
        pair_address = ""

        if token_uid and _tok_wrap_news_table_exists_v1(con, "tokens"):
            tr = cur.execute("SELECT * FROM tokens WHERE token_uid=? LIMIT 1", (token_uid,)).fetchone()
            if tr:
                td = dict(tr)
                symbol = _tok_wrap_news_pick_v1(td, "symbol", "token_symbol", "ticker", "name")
                name = _tok_wrap_news_pick_v1(td, "name", "token_name", "display_name") or symbol
                token_address = _tok_wrap_news_pick_v1(td, "token_address", "address", "contract_address")
                chain = chain or _tok_wrap_news_pick_v1(td, "chain", "network")

        if pair_uid and _tok_wrap_news_table_exists_v1(con, "pairs"):
            pr = cur.execute("SELECT * FROM pairs WHERE pair_uid=? LIMIT 1", (pair_uid,)).fetchone()
            if pr:
                pd = dict(pr)
                symbol = symbol or _tok_wrap_news_pick_v1(pd, "symbol", "base_symbol", "token_symbol", "name")
                name = name or _tok_wrap_news_pick_v1(pd, "name", "pair_name", "token_name") or symbol
                pair_address = _tok_wrap_news_pick_v1(pd, "pair_address", "address", "pool_address")
                chain = chain or _tok_wrap_news_pick_v1(pd, "chain", "network")

        if token_uid or pair_uid or symbol:
            out.append({
                "token_uid": token_uid,
                "pair_uid": pair_uid,
                "symbol": symbol,
                "name": name,
                "chain": chain,
                "token_address": token_address,
                "pair_address": pair_address,
            })
    return out

def _tok_wrap_news_tracker_paths_v1():
    base = "/root/tokenoskobi_clean_v1/runtime/state"
    return (
        os.path.join(base, "news_processed_tracker_v1.json"),
        os.path.join(base, "news_processed_tracker_v1.lock"),
    )

def _tok_wrap_news_acquire_lock_v1(lock_path, stale_seconds=300):
    import time
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    try:
        if os.path.exists(lock_path):
            age = time.time() - os.path.getmtime(lock_path)
            if age > stale_seconds:
                os.unlink(lock_path)
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        return True
    except FileExistsError:
        return False

def _tok_wrap_news_release_lock_v1(lock_path):
    try:
        if os.path.exists(lock_path):
            os.unlink(lock_path)
    except Exception:
        pass

def _tok_wrap_news_empty_tracker_v1():
    return {
        "schema_version": "1.0",
        "created_at_utc": _tok_wrap_news_now_v1(),
        "updated_at_utc": _tok_wrap_news_now_v1(),
        "source": "NEWS_RUNNER_DOWNSTREAM_HOOK",
        "processed_news_uids": [],
        "processed_hashes": [],
        "last_raw_count_seen": 0,
        "last_match_count_seen": 0,
        "last_signal_count_seen": 0,
        "last_score_count_seen": 0,
        "last_success_batch": {
            "started_at_utc": None,
            "finished_at_utc": None,
            "input_raw": 0,
            "new_processed": 0,
            "matches_inserted": 0,
            "signals_inserted": 0,
            "scores_inserted": 0
        }
    }

def _tok_wrap_news_load_tracker_v1(path):
    if not os.path.exists(path):
        return _tok_wrap_news_empty_tracker_v1()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data.get("processed_news_uids"), list):
        data["processed_news_uids"] = []
    if not isinstance(data.get("processed_hashes"), list):
        data["processed_hashes"] = []
    return data

def _tok_wrap_news_atomic_write_json_v1(path, data):
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".news_processed_tracker_v1.", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        with open(tmp, encoding="utf-8") as f:
            json.load(f)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def _tok_wrap_news_count_v1(con, table):
    if not _tok_wrap_news_table_exists_v1(con, table):
        return 0
    return int(con.execute("SELECT COUNT(*) FROM " + table).fetchone()[0])

def _tok_wrap_news_existing_news_uids_v1(con):
    if not _tok_wrap_news_table_exists_v1(con, "news_token_match_events"):
        return set()
    return {
        str(x[0])
        for x in con.execute(
            "SELECT DISTINCT news_uid FROM news_token_match_events WHERE news_uid IS NOT NULL"
        ).fetchall()
    }

def _tok_wrap_news_uid_exists_v1(con, table, col, value):
    if not _tok_wrap_news_table_exists_v1(con, table):
        return False
    row = con.execute(
        "SELECT 1 FROM " + table + " WHERE " + col + "=? LIMIT 1",
        (value,)
    ).fetchone()
    return row is not None

def _tok_wrap_news_select_candidates_v1(con, tracker, max_batch=100):
    if not _tok_wrap_news_table_exists_v1(con, "news_raw_feed_events"):
        return []
    existing = _tok_wrap_news_existing_news_uids_v1(con)
    tracker_uids = set(str(x) for x in tracker.get("processed_news_uids", []))
    tracker_hashes = set(str(x) for x in tracker.get("processed_hashes", []))

    rows = con.execute(
        """
        SELECT news_uid, source_uid, published_at_utc, title, url_hash, raw_hash, fetched_at_utc
        FROM news_raw_feed_events
        ORDER BY fetched_at_utc DESC
        LIMIT 300
        """
    ).fetchall()

    out = []
    seen = set()
    for r in rows:
        d = dict(r)
        news_uid = str(d.get("news_uid") or "").strip()
        raw_hash = str(d.get("raw_hash") or "").strip()
        fallback = _tok_wrap_news_stable_hash_v1(
            d.get("source_uid"), d.get("title"), d.get("published_at_utc"), raw_hash, d.get("url_hash")
        )
        if not news_uid:
            news_uid = "fallback_" + fallback[:20]
            d["news_uid"] = news_uid
        if news_uid in seen or news_uid in existing or news_uid in tracker_uids:
            continue
        if raw_hash and raw_hash in tracker_hashes:
            continue
        out.append(d)
        seen.add(news_uid)
        if len(out) >= int(max_batch):
            break

    return list(reversed(out))

def _tok_wrap_news_insert_downstream_v1(con, matches):
    now = _tok_wrap_news_now_v1()
    inserted_match = 0
    inserted_signal = 0
    inserted_score = 0

    for m in matches:
        if not bool(m.get("write_allowed")):
            continue
        match_uid = str(m.get("match_uid") or "").strip()
        news_uid = str(m.get("news_uid") or "").strip()
        if not match_uid or not news_uid:
            continue
        if _tok_wrap_news_uid_exists_v1(con, "news_token_match_events", "match_uid", match_uid):
            continue
        if _tok_wrap_news_uid_exists_v1(con, "news_token_match_events", "news_uid", news_uid):
            continue

        suffix = match_uid.split("match_", 1)[1] if match_uid.startswith("match_") else _tok_wrap_news_stable_hash_v1(match_uid)[:20]
        signal_uid = "signal_" + suffix
        score_uid = "score_" + suffix

        con.execute(
            """
            INSERT INTO news_token_match_events
            (match_uid, news_uid, source_uid, token_uid, pair_uid, symbol, chain,
             match_type, match_confidence, match_score, match_reasons_json,
             evidence_text, is_duplicate, write_allowed, trade_signal, paper_signal, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                match_uid,
                news_uid,
                m.get("source_uid"),
                m.get("token_uid"),
                m.get("pair_uid"),
                m.get("symbol"),
                m.get("chain"),
                m.get("match_type"),
                m.get("match_confidence"),
                int(m.get("match_score") or 0),
                json.dumps(m.get("match_reasons") or [], ensure_ascii=False),
                m.get("evidence_text"),
                1 if m.get("is_duplicate") else 0,
                1 if m.get("write_allowed") else 0,
                0,
                0,
                now,
            )
        )
        inserted_match += 1

        if not _tok_wrap_news_uid_exists_v1(con, "news_signal_events", "signal_uid", signal_uid):
            strength = int(m.get("match_score") or 0)
            label = "HIGH" if strength >= 70 else "MEDIUM" if strength >= 45 else "LOW"
            con.execute(
                """
                INSERT INTO news_signal_events
                (signal_uid, news_uid, token_uid, pair_uid, symbol, chain,
                 signal_type, signal_strength, signal_label, source_match_uid, evidence_text, created_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal_uid,
                    news_uid,
                    m.get("token_uid"),
                    m.get("pair_uid"),
                    m.get("symbol"),
                    m.get("chain"),
                    "TOKEN_NEWS_MATCH",
                    strength,
                    label,
                    match_uid,
                    m.get("evidence_text"),
                    now,
                )
            )
            inserted_signal += 1

        if not _tok_wrap_news_uid_exists_v1(con, "news_score_events_v1", "score_uid", score_uid):
            score = int(m.get("match_score") or 0)
            importance = "HIGH" if score >= 70 else "MEDIUM" if score >= 45 else "LOW"
            con.execute(
                """
                INSERT INTO news_score_events_v1
                (score_uid, news_uid, token_uid, pair_uid, symbol, chain,
                 news_token_relevance_score_100, news_risk_score_100, news_fusion_score_100,
                 importance_label, risk_label, fusion_label, explanation, created_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    score_uid,
                    news_uid,
                    m.get("token_uid"),
                    m.get("pair_uid"),
                    m.get("symbol"),
                    m.get("chain"),
                    score,
                    10,
                    score,
                    importance,
                    "LOW",
                    "NEWS_TOKEN_RELEVANT",
                    "Runtime downstream hook from NEWS runner",
                    now,
                )
            )
            inserted_score += 1

    return inserted_match, inserted_signal, inserted_score

def _tok_wrap_news_update_freshness_v1(con):
    if not _tok_wrap_news_table_exists_v1(con, "news_runtime_freshness_v1"):
        return
    now = _tok_wrap_news_now_v1()
    raw_count = _tok_wrap_news_count_v1(con, "news_raw_feed_events")
    match_count = _tok_wrap_news_count_v1(con, "news_token_match_events")
    signal_count = _tok_wrap_news_count_v1(con, "news_signal_events")
    score_count = _tok_wrap_news_count_v1(con, "news_score_events_v1")
    uid = "fresh_news_runner_hook_v1"

    exists = con.execute(
        "SELECT 1 FROM news_runtime_freshness_v1 WHERE freshness_uid=? LIMIT 1",
        (uid,)
    ).fetchone()

    if exists:
        con.execute(
            """
            UPDATE news_runtime_freshness_v1
            SET component=?, last_observed_at_utc=?, raw_count=?, match_count=?,
                signal_count=?, score_count=?, heartbeat_status=?, created_at_utc=?
            WHERE freshness_uid=?
            """,
            (
                "news_runner_downstream_hook",
                now,
                raw_count,
                match_count,
                signal_count,
                score_count,
                "GREEN",
                now,
                uid,
            )
        )
    else:
        con.execute(
            """
            INSERT INTO news_runtime_freshness_v1
            (freshness_uid, component, last_observed_at_utc, raw_count, match_count,
             signal_count, score_count, heartbeat_status, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uid,
                "news_runner_downstream_hook",
                now,
                raw_count,
                match_count,
                signal_count,
                score_count,
                "GREEN",
                now,
            )
        )

def _tok_wrap_news_downstream_hook_v1(before_count, after_count, rc):
    try:
        before_count = int(before_count or 0)
        after_count = int(after_count or 0)
        raw_delta = after_count - before_count
        if raw_delta <= 0:
            _tok_wrap_trace_v1("news_downstream_hook_skip", "raw_delta<=0")
            return 0

        tracker_path, lock_path = _tok_wrap_news_tracker_paths_v1()
        if not _tok_wrap_news_acquire_lock_v1(lock_path):
            _tok_wrap_trace_v1("news_downstream_hook_skip", "tracker_lock_busy")
            return 0

        try:
            db_path = "/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite"
            tracker = _tok_wrap_news_load_tracker_v1(tracker_path)

            base = "/root/tokenoskobi_clean_v1/tools"
            if base not in sys.path:
                sys.path.insert(0, base)
            from news_token_matcher_v1 import match_many

            con = sqlite3.connect(db_path, timeout=10)
            con.row_factory = sqlite3.Row
            tokens = _tok_wrap_news_load_tokens_v1(con)
            candidates = _tok_wrap_news_select_candidates_v1(con, tracker, max_batch=100)

            if not candidates or not tokens:
                tracker["updated_at_utc"] = _tok_wrap_news_now_v1()
                tracker["last_raw_count_seen"] = _tok_wrap_news_count_v1(con, "news_raw_feed_events")
                tracker["last_match_count_seen"] = _tok_wrap_news_count_v1(con, "news_token_match_events")
                tracker["last_signal_count_seen"] = _tok_wrap_news_count_v1(con, "news_signal_events")
                tracker["last_score_count_seen"] = _tok_wrap_news_count_v1(con, "news_score_events_v1")
                _tok_wrap_news_atomic_write_json_v1(tracker_path, tracker)
                con.close()
                _tok_wrap_trace_v1("news_downstream_hook_noop", "candidates="+str(len(candidates))+" tokens="+str(len(tokens)))
                return 0

            started = _tok_wrap_news_now_v1()
            matches = match_many(candidates, tokens)

            con.execute("BEGIN IMMEDIATE")
            inserted_match, inserted_signal, inserted_score = _tok_wrap_news_insert_downstream_v1(con, matches)
            _tok_wrap_news_update_freshness_v1(con)
            con.commit()

            processed_uids = list(tracker.get("processed_news_uids") or [])
            processed_hashes = list(tracker.get("processed_hashes") or [])
            uid_set = set(str(x) for x in processed_uids)
            hash_set = set(str(x) for x in processed_hashes)

            new_processed = 0
            for row in candidates:
                uid = str(row.get("news_uid") or "").strip()
                rh = str(row.get("raw_hash") or "").strip()
                if uid and uid not in uid_set:
                    processed_uids.append(uid)
                    uid_set.add(uid)
                    new_processed += 1
                if rh and rh not in hash_set:
                    processed_hashes.append(rh)
                    hash_set.add(rh)

            processed_uids = processed_uids[-5000:]
            processed_hashes = processed_hashes[-5000:]

            tracker["updated_at_utc"] = _tok_wrap_news_now_v1()
            tracker["processed_news_uids"] = processed_uids
            tracker["processed_hashes"] = processed_hashes
            tracker["last_raw_count_seen"] = _tok_wrap_news_count_v1(con, "news_raw_feed_events")
            tracker["last_match_count_seen"] = _tok_wrap_news_count_v1(con, "news_token_match_events")
            tracker["last_signal_count_seen"] = _tok_wrap_news_count_v1(con, "news_signal_events")
            tracker["last_score_count_seen"] = _tok_wrap_news_count_v1(con, "news_score_events_v1")
            tracker["last_success_batch"] = {
                "started_at_utc": started,
                "finished_at_utc": _tok_wrap_news_now_v1(),
                "input_raw": len(candidates),
                "new_processed": new_processed,
                "matches_inserted": inserted_match,
                "signals_inserted": inserted_signal,
                "scores_inserted": inserted_score
            }

            _tok_wrap_news_atomic_write_json_v1(tracker_path, tracker)
            con.close()

            _tok_wrap_trace_v1(
                "news_downstream_hook_done",
                "raw_delta="+str(raw_delta)
                +" candidates="+str(len(candidates))
                +" matches="+str(inserted_match)
                +" signals="+str(inserted_signal)
                +" scores="+str(inserted_score)
            )
            return 0

        finally:
            _tok_wrap_news_release_lock_v1(lock_path)

    except Exception as e:
        try:
            _tok_wrap_trace_v1("news_downstream_hook_error", repr(e))
        except Exception:
            pass
        return 2
# === TOKENOSKOBI NEWS DOWNSTREAM HOOK V1 END ===


def main():
    _tok_wrap_trace_v1('main_enter')
    _tok_wrap_trace_v1('before_count_start')
    before_count = _tok_wrap_raw_count_v1()
    _tok_wrap_trace_v1('before_count_done', before_count)
    _tok_wrap_trace_v1('subprocess_start')
    rc = subprocess.run([sys.executable, ORIGINAL_RUNNER] + sys.argv[1:]).returncode
    after_count = _tok_wrap_raw_count_v1()
    _tok_wrap_trace_v1('after_count_done', after_count)

    if int(rc) == 2:
        after_count = _tok_wrap_raw_count_v1()
        _tok_wrap_trace_v1('after_count_done', after_count)
        _tok_wrap_trace_v1('rc2_raw_delta_tolerance_check', 'before='+str(before_count)+' after='+str(after_count))
        if _tok_wrap_rc2_raw_delta_url_empty_ok_v1(before_count, after_count):
            _tok_wrap_trace_v1('rc2_raw_delta_tolerance_convert', 'rc=2->0 raw_delta_url_empty_ok')
            rc = 0

    if rc != 0:
        _tok_wrap_trace_v1('tolerance_check', 'rc='+str(rc))
        if _tok_wrap_url_empty_tol_v1(rc, before_count, after_count):
            rc = 0
        else:
            _tok_wrap_trace_v1('return_rc', rc)
            return rc

    hook_rc = _tok_wrap_news_downstream_hook_v1(before_count, after_count, rc)
    if int(hook_rc or 0) != 0:
        _tok_wrap_trace_v1('return_hook_rc', hook_rc)
        return int(hook_rc)

    _tok_wrap_trace_v1('final_return_after_downstream_hook', str(rc))
    _tok_wrap_trace_v1('return_rc', str(rc))
    return rc

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
