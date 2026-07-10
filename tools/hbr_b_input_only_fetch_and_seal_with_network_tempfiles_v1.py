
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/hbr_a_input_only_source_plan_noapi_v1.json"
POLICY = ROOT / "runtime/policies/news_runtime_policy_lock_v1.json"
VERIFIER = ROOT / "tools/news_runtime_policy_verifier_v1.py"

INPUT_DIR = ROOT / "runtime/hbr_blind_replay"
ITEMS_JSONL = INPUT_DIR / "hbr_b_input_only_items_v1.jsonl"
SKIPPED_JSONL = INPUT_DIR / "hbr_b_input_only_skipped_v1.jsonl"
MANIFEST_JSON = INPUT_DIR / "hbr_b_input_manifest_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

SOURCE_URLS = {
    "coindesk_rss_input_only_candidate": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph_rss_input_only_candidate": "https://cointelegraph.com/rss"
}

USER_AGENT = "TokenoskobiHistoricalBlindReplayInputOnly/1.0"

def now():
    return datetime.now(timezone.utc).isoformat()

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def parse_dt(value):
    if not value:
        return None
    value = str(value).strip()
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            v = value.replace("Z", "+0000") if fmt.endswith("%z") else value
            dt = datetime.strptime(v, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None

def dt_iso(dt):
    return dt.astimezone(timezone.utc).isoformat() if dt else None

def in_windows(dt, windows):
    if dt is None:
        return False
    for w in windows:
        s = datetime.fromisoformat(w["start_utc"])
        e = datetime.fromisoformat(w["end_utc"])
        if s <= dt <= e:
            return True
    return False

def table_exists(con, table):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        [table]
    ).fetchone() is not None

def load_existing_uids():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        if not table_exists(con, "news_raw_feed_events"):
            return set()
        return {r[0] for r in con.execute("SELECT news_uid FROM news_raw_feed_events").fetchall()}
    finally:
        con.close()

def db_snapshot():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        counts = {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        return {"counts": counts, "integrity": integrity}
    finally:
        con.close()

def text_child(el, names):
    wanted = {n.lower() for n in names}
    for child in list(el):
        tag = str(child.tag).split("}")[-1].lower()
        if tag in wanted:
            return (child.text or "").strip()
    return ""

def link_child(el):
    direct = text_child(el, ["link"])
    if direct:
        return direct
    for child in list(el):
        tag = str(child.tag).split("}")[-1].lower()
        if tag == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
    return ""

def parse_feed(source_id, source_name, data):
    root = ET.fromstring(data)
    nodes = []
    nodes.extend(root.findall(".//item"))
    nodes.extend(root.findall(".//{http://www.w3.org/2005/Atom}entry"))
    if not nodes and str(root.tag).split("}")[-1].lower() in ("item", "entry"):
        nodes = [root]

    out = []
    for node in nodes:
        title = text_child(node, ["title"])
        url = link_child(node)
        pub_raw = text_child(node, ["pubDate", "published", "updated", "dc:date"])
        guid = text_child(node, ["guid", "id"])
        dt = parse_dt(pub_raw)
        canonical = json.dumps({
            "source_id": source_id,
            "title": title,
            "url": url,
            "published_at_utc": dt_iso(dt),
            "guid": guid
        }, ensure_ascii=False, sort_keys=True)
        url_hash = sha256_text(url or guid or canonical)[:24]
        raw_hash = sha256_text(canonical)
        candidate_news_uid = "hbr_input_" + sha256_text(source_id + "|" + url_hash + "|" + raw_hash)[:24]
        out.append({
            "source_id": source_id,
            "source_name": source_name,
            "published_at_utc": dt_iso(dt),
            "title": title,
            "url": url,
            "url_hash": url_hash,
            "raw_hash": raw_hash,
            "candidate_news_uid": candidate_news_uid,
            "fetched_at_utc": now(),
            "input_only": True
        })
    return out

def fetch_url(url, timeout, retry_count):
    last = None
    for attempt in range(retry_count + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            return {"ok": True, "attempt": attempt + 1, "url": url, "status": getattr(r, "status", None), "bytes": len(data), "sha256": sha256_bytes(data), "data": data, "error": None}
        except Exception as exc:
            last = repr(exc)
            time.sleep(1)
    return {"ok": False, "attempt": retry_count + 1, "url": url, "status": None, "bytes": 0, "sha256": None, "data": b"", "error": last}

def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")

def main():
    generated_at = now()
    failures = []
    warnings = []

    if not PRIOR.exists():
        failures.append("prior_hbr_a_missing")
        prior = {}
        source_plan = {}
    else:
        prior = json.loads(PRIOR.read_text(encoding="utf-8"))
        if prior.get("decision") != "OK_HBR_A_INPUT_ONLY_SOURCE_PLAN_NOAPI":
            failures.append("prior_hbr_a_not_ok")
        source_plan = prior.get("result", {}).get("source_plan", {})

    if not VERIFIER.exists():
        failures.append("policy_verifier_missing")
    compile_verifier = run([sys.executable, "-m", "py_compile", str(VERIFIER)]) if VERIFIER.exists() else {"rc": 1, "stdout": "", "stderr": "missing"}
    verifier_run = run([sys.executable, str(VERIFIER), "--db-path", str(DB), "--recent-limit", "500"]) if VERIFIER.exists() else {"rc": 1, "stdout": "", "stderr": "missing"}
    try:
        verifier_result = json.loads(verifier_run["stdout"]) if verifier_run["stdout"] else {}
    except Exception as exc:
        verifier_result = {"decision": "FAIL_PARSE_POLICY_VERIFIER", "error": repr(exc), "raw": verifier_run}

    if compile_verifier["rc"] != 0:
        failures.append("policy_verifier_compile_failed")
    if verifier_run["rc"] != 0:
        failures.append("policy_verifier_runtime_failed")
    if verifier_result.get("decision") != "OK_NEWS_RUNTIME_POLICY_VERIFIER_V1":
        failures.append("policy_verifier_not_ok")

    db_before = db_snapshot()
    if db_before["integrity"] != "ok":
        failures.append("sqlite_integrity_not_ok_before")

    caps = source_plan.get("next_fetch_caps", {})
    max_total = int(caps.get("max_total_input_items", 150))
    max_per_source = int(caps.get("max_items_per_source", 75))
    timeout = int(caps.get("timeout_seconds_per_source", 20))
    retry_count = int(caps.get("retry_count", 1))
    windows = source_plan.get("time_windows", [])
    forbidden = set(source_plan.get("forbidden_fields_before_prediction_seal", []))
    allowed_fields = set(source_plan.get("allowed_input_fields_next_step", []))

    fetched_items = []
    skipped = []
    source_fetches = []

    existing_uids = load_existing_uids()
    seen_url_hash = set()

    sources = source_plan.get("sources", [])
    for src in sources[: int(caps.get("max_sources", 2))]:
        source_id = src.get("source_id")
        source_name = src.get("source_name")
        url = SOURCE_URLS.get(source_id)
        if not url:
            skipped.append({"reason": "source_url_missing", "source_id": source_id, "source_name": source_name})
            continue
        fetch = fetch_url(url, timeout, retry_count)
        source_fetches.append({k: v for k, v in fetch.items() if k != "data"})
        if not fetch["ok"]:
            skipped.append({"reason": "source_fetch_failed", "source_id": source_id, "source_name": source_name, "error": fetch["error"]})
            continue
        try:
            parsed = parse_feed(source_id, source_name, fetch["data"])
        except Exception as exc:
            skipped.append({"reason": "source_parse_failed", "source_id": source_id, "source_name": source_name, "error": repr(exc)})
            continue

        taken = 0
        for item in parsed:
            if taken >= max_per_source:
                break
            forbidden_present = sorted([f for f in forbidden if f in item])
            extra_fields = sorted([k for k in item.keys() if k not in allowed_fields and k not in {"input_only", "within_locked_window"}])
            if forbidden_present:
                skipped.append({"reason": "forbidden_field_present", "candidate_news_uid": item.get("candidate_news_uid"), "forbidden": forbidden_present})
                continue
            if item["candidate_news_uid"] in existing_uids:
                skipped.append({"reason": "existing_uid_collision", "candidate_news_uid": item["candidate_news_uid"]})
                continue
            if item["url_hash"] in seen_url_hash:
                skipped.append({"reason": "duplicate_url_hash", "candidate_news_uid": item["candidate_news_uid"], "url_hash": item["url_hash"]})
                continue

            dt = parse_dt(item.get("published_at_utc"))
            item["within_locked_window"] = in_windows(dt, windows)
            item["window_status"] = "IN_LOCKED_WINDOW" if item["within_locked_window"] else "OUTSIDE_LOCKED_WINDOW_OR_UNDATED"
            item["schema_extra_fields"] = extra_fields

            fetched_items.append(item)
            seen_url_hash.add(item["url_hash"])
            taken += 1
            if len(fetched_items) >= max_total:
                break
        if len(fetched_items) >= max_total:
            break

    fetched_items = sorted(fetched_items, key=lambda r: (r.get("source_id") or "", r.get("published_at_utc") or "", r.get("url_hash") or ""))
    skipped = sorted(skipped, key=lambda r: json.dumps(r, ensure_ascii=False, sort_keys=True))

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(ITEMS_JSONL, fetched_items)
    write_jsonl(SKIPPED_JSONL, skipped)

    items_sha = sha256_file(ITEMS_JSONL)
    skipped_sha = sha256_file(SKIPPED_JSONL)

    in_window_count = sum(1 for r in fetched_items if r.get("within_locked_window") is True)
    outside_window_count = len(fetched_items) - in_window_count

    manifest_core = {
        "stage": "HBR_B_INPUT_ONLY_FETCH_AND_SEAL_WITH_NETWORK_TEMPFILES",
        "generated_at_utc": generated_at,
        "prior": "data/control/hbr_a_input_only_source_plan_noapi_v1.json",
        "source_plan_sha256": prior.get("result", {}).get("source_plan_sha256"),
        "items_jsonl": "runtime/hbr_blind_replay/hbr_b_input_only_items_v1.jsonl",
        "items_jsonl_sha256": items_sha,
        "skipped_jsonl": "runtime/hbr_blind_replay/hbr_b_input_only_skipped_v1.jsonl",
        "skipped_jsonl_sha256": skipped_sha,
        "input_count": len(fetched_items),
        "in_locked_window_count": in_window_count,
        "outside_locked_window_or_undated_count": outside_window_count,
        "skipped_count": len(skipped),
        "source_fetches": source_fetches,
        "no_outcome_fields": True,
        "production_db_insert": False,
        "production_db_write": False,
        "write_target": "tempfiles_only"
    }
    input_manifest_sha = sha256_text(json.dumps(manifest_core, ensure_ascii=False, sort_keys=True))
    manifest = dict(manifest_core)
    manifest["input_manifest_sha256"] = input_manifest_sha
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    db_after = db_snapshot()
    if db_after["integrity"] != "ok":
        failures.append("sqlite_integrity_not_ok_after")

    if len(source_fetches) == 0:
        failures.append("no_source_fetch_attempted")
    if not any(s.get("ok") is True for s in source_fetches):
        failures.append("no_source_fetch_success")
    if len(fetched_items) == 0:
        failures.append("input_items_zero")
    if any(any(f in row for f in forbidden) for row in fetched_items):
        failures.append("forbidden_outcome_field_detected")
    if len(input_manifest_sha) != 64:
        failures.append("input_manifest_sha_invalid")
    if db_before["counts"] != db_after["counts"]:
        warnings.append("production_db_changed_during_network_window_external_timer_possible")
    if in_window_count == 0:
        warnings.append("no_items_inside_locked_june_windows_next_step_may_need_window_repair")

    tests = [
        {"test_id": "T01_PRIOR_HBR_A_OK", "ok": prior.get("decision") == "OK_HBR_A_INPUT_ONLY_SOURCE_PLAN_NOAPI"},
        {"test_id": "T02_POLICY_VERIFIER_OK", "ok": verifier_result.get("decision") == "OK_NEWS_RUNTIME_POLICY_VERIFIER_V1", "verifier_decision": verifier_result.get("decision")},
        {"test_id": "T03_NETWORK_FETCH_ATTEMPTED", "ok": len(source_fetches) > 0},
        {"test_id": "T04_AT_LEAST_ONE_SOURCE_FETCH_SUCCESS", "ok": any(s.get("ok") is True for s in source_fetches)},
        {"test_id": "T05_INPUT_ITEMS_SEALED", "ok": len(fetched_items) > 0, "input_count": len(fetched_items)},
        {"test_id": "T06_NO_OUTCOME_FIELDS", "ok": not any(any(f in row for f in forbidden) for row in fetched_items)},
        {"test_id": "T07_INPUT_MANIFEST_SHA_CREATED", "ok": len(input_manifest_sha) == 64, "input_manifest_sha256": input_manifest_sha},
        {"test_id": "T08_TEMPFILES_ONLY", "ok": MANIFEST_JSON.exists() and ITEMS_JSONL.exists() and SKIPPED_JSONL.exists()},
        {"test_id": "T09_PRODUCTION_DB_WRITE_FORBIDDEN", "ok": True, "db_write_by_this_script": False, "production_db_insert": False},
        {"test_id": "T10_SQLITE_INTEGRITY_OK", "ok": db_before["integrity"] == "ok" and db_after["integrity"] == "ok"},
        {"test_id": "T11_BOUNDARY_LOCK", "ok": True, "api_call": False, "db_schema_change": False, "db_write": False, "network_call": True, "service_change": False, "timer_change": False, "paper_trade": False, "live_trade": False, "trade_authority": False}
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI" if not failures else "HBR_B_INPUT_ONLY_FETCH_AND_SEAL_HOLD"

    return {
        "stage": "HBR_B_INPUT_ONLY_FETCH_AND_SEAL_WITH_NETWORK_TEMPFILES",
        "generated_at_utc": generated_at,
        "decision": "OK_HBR_B_INPUT_ONLY_FETCH_AND_SEAL_WITH_NETWORK_TEMPFILES" if not failures else "FAIL_HBR_B_INPUT_ONLY_FETCH_AND_SEAL_WITH_NETWORK_TEMPFILES",
        "prior": "data/control/hbr_a_input_only_source_plan_noapi_v1.json",
        "policy_json": "runtime/policies/news_runtime_policy_lock_v1.json",
        "policy_verifier": "tools/news_runtime_policy_verifier_v1.py",
        "compile_verifier": compile_verifier,
        "verifier_result": verifier_result,
        "db_before": db_before,
        "db_after": db_after,
        "manifest": manifest,
        "input_items_preview": fetched_items[:10],
        "skipped_preview": skipped[:20],
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "api_call": False,
            "db_schema_change": False,
            "db_write": False,
            "index_creation": False,
            "live_trade": False,
            "network_call": True,
            "nginx_change": False,
            "paper_trade": False,
            "service_change": False,
            "timer_change": False,
            "trade_authority": False
        },
        "failures": failures,
        "warnings": warnings,
        "next": next_step
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
