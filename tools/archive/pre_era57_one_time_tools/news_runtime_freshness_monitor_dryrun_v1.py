
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PLAN = ROOT / "config/news_runtime_freshness_monitor_plan_v1.json"
FINAL_SEAL = ROOT / "data/control/news_ingress_chain_final_review_and_seal_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

def now_dt():
    return datetime.now(timezone.utc)

def now():
    return now_dt().isoformat()

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def q(name):
    return '"' + str(name).replace('"', '""') + '"'

def parse_ts(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        x = float(value)
        if x > 100000000000:
            x = x / 1000.0
        try:
            return datetime.fromtimestamp(x, timezone.utc)
        except Exception:
            return None
    s = str(value).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f"]:
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None

def table_columns(con, table):
    rows = con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()
    return [{"cid": r[0], "name": r[1], "type": r[2]} for r in rows]

def count_table(con, table):
    return con.execute("SELECT COUNT(*) FROM " + q(table)).fetchone()[0]

def timestamp_candidates(columns, configured):
    names = [c["name"] for c in columns]
    lower = {n.lower(): n for n in names}
    out = []
    for c in configured:
        if c.lower() in lower:
            out.append(lower[c.lower()])
    for n in names:
        ln = n.lower()
        if n not in out and any(x in ln for x in ["created", "observed", "generated", "timestamp", "datetime", "date", "time", "ts"]):
            out.append(n)
    return out

def latest_timestamp(con, table, candidates):
    best = None
    details = []
    for col in candidates:
        try:
            val = con.execute("SELECT MAX(" + q(col) + ") FROM " + q(table) + " WHERE " + q(col) + " IS NOT NULL").fetchone()[0]
            dt = parse_ts(val)
            details.append({"column": col, "raw_latest": val, "parsed_utc": dt.isoformat() if dt else None})
            if dt and (best is None or dt > best["dt"]):
                best = {"column": col, "raw_latest": val, "dt": dt}
        except Exception as e:
            details.append({"column": col, "error": str(e)})
    return best, details

def freshness(table, count, latest, plan):
    if count is None:
        return {"status": "MISSING_TABLE", "age_minutes": None, "severity": "FAIL"}
    if count == 0:
        return {"status": "EMPTY", "age_minutes": None, "severity": "WARN"}
    if latest is None:
        return {"status": "UNKNOWN_TIMESTAMP", "age_minutes": None, "severity": "WARN"}
    age = (now_dt() - latest["dt"]).total_seconds() / 60.0
    th = plan["threshold_policy_noapi_plan"]
    if table == "news_raw_feed_events":
        warn = th["raw_feed_warn_after_minutes"]
        fail = th["raw_feed_fail_after_minutes"]
    else:
        warn = th["derived_layer_warn_after_minutes"]
        fail = th["derived_layer_fail_after_minutes"]
    if age <= warn:
        return {"status": "FRESH", "age_minutes": round(age, 2), "severity": "OK", "warn_after_minutes": warn, "fail_after_minutes": fail}
    if age <= fail:
        return {"status": "STALE_WARN", "age_minutes": round(age, 2), "severity": "WARN", "warn_after_minutes": warn, "fail_after_minutes": fail}
    return {"status": "STALE_FAIL_WINDOW", "age_minutes": round(age, 2), "severity": "WARN", "warn_after_minutes": warn, "fail_after_minutes": fail}

def snapshot(plan):
    configured = {x["table"]: x.get("freshness_fields_candidates", []) for x in plan.get("monitored_tables", [])}
    out = {}
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        for table in TABLES:
            try:
                cols = table_columns(con, table)
                cnt = count_table(con, table)
                candidates = timestamp_candidates(cols, configured.get(table, []))
                latest, details = latest_timestamp(con, table, candidates)
                out[table] = {
                    "count": cnt,
                    "columns": cols,
                    "timestamp_candidates": candidates,
                    "candidate_details": details,
                    "selected_latest": {"column": latest["column"], "raw_latest": latest["raw_latest"], "parsed_utc": latest["dt"].isoformat()} if latest else None,
                    "freshness": freshness(table, cnt, latest, plan)
                }
            except Exception as e:
                out[table] = {"count": None, "error": str(e), "freshness": {"status": "MISSING_TABLE", "age_minutes": None, "severity": "FAIL"}}
    finally:
        con.close()
    return out

def counts():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    out = {}
    try:
        for t in TABLES:
            try:
                out[t] = count_table(con, t)
            except Exception:
                out[t] = None
    finally:
        con.close()
    return out

def main():
    plan = load(PLAN)
    final_seal = load(FINAL_SEAL)

    before = counts()
    timer_active = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    timer_enabled = run(["systemctl", "is-enabled", "tokenoskobi-news-radar-refresh.timer"])
    service_active = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])
    tables = snapshot(plan)
    after = counts()
    db_delta = {t: None if before[t] is None or after[t] is None else after[t] - before[t] for t in TABLES}

    failures = []
    warnings = []

    if final_seal.get("decision") != "OK_NEWS_INGRESS_CHAIN_FINAL_REVIEW_AND_SEAL_NOAPI":
        failures.append("prior_news_ingress_final_seal_not_ok")
    if timer_active.get("stdout") != "active":
        failures.append("producer_timer_not_active")
    if timer_enabled.get("stdout") != "enabled":
        failures.append("producer_timer_not_enabled")

    for table, item in tables.items():
        st = item.get("freshness", {}).get("status")
        if st == "MISSING_TABLE":
            failures.append("missing_table:" + table)
        elif st in ["EMPTY", "UNKNOWN_TIMESTAMP", "STALE_WARN", "STALE_FAIL_WINDOW"]:
            warnings.append("freshness_observation:" + table + ":" + str(st))

    if any(v not in (0, None) for v in db_delta.values()):
        failures.append("db_delta_not_zero")

    history = {
        "historical_access_next": plan["history_alignment"]["required_next_phase"],
        "index_strategy_required": plan["history_alignment"]["index_strategy_required"],
        "deduplication_policy_required": plan["history_alignment"]["deduplication_policy_required"],
        "index_creation_now": False,
        "backfill_now": False,
        "db_schema_change_now": False
    }

    if history["index_strategy_required"] is not True:
        failures.append("index_strategy_not_locked")
    if history["deduplication_policy_required"] is not True:
        failures.append("dedup_policy_not_locked")

    producer = {
        "timer_active": timer_active,
        "timer_enabled": timer_enabled,
        "service_active": service_active,
        "interpretation": "OK_TIMER_ACTIVE_ONESHOT_SERVICE_CAN_BE_INACTIVE" if timer_active.get("stdout") == "active" and timer_enabled.get("stdout") == "enabled" else "PRODUCER_TIMER_PROBLEM"
    }

    return {
        "stage": "NEWS_RUNTIME_FRESHNESS_MONITOR_DRYRUN_NOAPI",
        "generated_at_utc": now(),
        "decision": "OK_NEWS_RUNTIME_FRESHNESS_MONITOR_DRYRUN_INTERNAL" if not failures else "FAIL_NEWS_RUNTIME_FRESHNESS_MONITOR_DRYRUN_INTERNAL",
        "table_freshness": tables,
        "producer_status": producer,
        "panel_public_status_optional": {"checked": False, "reason": "NO_NETWORK_NOAPI_DRYRUN"},
        "history_alignment_status": history,
        "db_before": before,
        "db_after": after,
        "db_delta": db_delta,
        "authority": {
            "api_call": False,
            "network_call": False,
            "db_write": False,
            "db_schema_change": False,
            "index_creation": False,
            "service_change": False,
            "timer_change": False,
            "nginx_change": False,
            "paper_trade": False,
            "live_trade": False,
            "execution_authority": False
        },
        "failures": failures,
        "warnings": warnings,
        "next": "NEWS_HISTORICAL_ACCESS_LAYER_PLAN_NOAPI" if not failures else "NEWS_RUNTIME_FRESHNESS_MONITOR_DRYRUN_FIX_REQUIRED"
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
