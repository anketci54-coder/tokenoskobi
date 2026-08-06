
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
import argparse, json, sqlite3
from typing import Any, Callable, Dict, List, Optional

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
POLICY_JSON = ROOT / "runtime/policies/news_runtime_policy_lock_v1.json"
DEFAULT_RECENT_LIMIT = 500
TABLES = ["news_raw_feed_events","news_token_match_events","news_signal_events","news_score_events_v1"]

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _q(x: str) -> str:
    return '"' + x.replace('"','""') + '"'

def _load_policy() -> Dict[str, Any]:
    return json.loads(POLICY_JSON.read_text(encoding="utf-8"))

def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", [table]).fetchone() is not None

def _cols(con: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in con.execute("PRAGMA table_info(" + _q(table) + ")").fetchall()]

def _counts(con: sqlite3.Connection) -> Dict[str, int]:
    return {t: con.execute("SELECT COUNT(*) FROM " + _q(t)).fetchone()[0] for t in TABLES}

def _bad_flags(con: sqlite3.Connection) -> int:
    return con.execute("""
        SELECT COUNT(*) FROM news_token_match_events
        WHERE COALESCE(write_allowed,0)!=0
           OR COALESCE(trade_signal,0)!=0
           OR COALESCE(paper_signal,0)!=0
    """).fetchone()[0]

def _recent_raw_uids(con: sqlite3.Connection, limit: int) -> List[str]:
    cols = _cols(con, "news_raw_feed_events")
    order_col = "fetched_at_utc" if "fetched_at_utc" in cols else "published_at_utc" if "published_at_utc" in cols else "news_uid"
    rows = con.execute("SELECT news_uid FROM news_raw_feed_events ORDER BY " + _q(order_col) + " DESC LIMIT ?", [limit]).fetchall()
    return [r[0] for r in rows]

def _recent_derived_counts(con: sqlite3.Connection, uids: List[str]) -> Dict[str, int]:
    if not uids:
        return {"news_token_match_events": 0, "news_signal_events": 0, "news_score_events_v1": 0}
    marks = ",".join(["?"] * len(uids))
    return {t: con.execute("SELECT COUNT(*) FROM " + _q(t) + " WHERE news_uid IN (" + marks + ")", uids).fetchone()[0] for t in ["news_token_match_events","news_signal_events","news_score_events_v1"]}

def _orphan_recent(con: sqlite3.Connection, table: str, uids: List[str]) -> List[Dict[str, Any]]:
    if not uids:
        return []
    marks = ",".join(["?"] * len(uids))
    rows = con.execute("""
        SELECT d.news_uid, COUNT(*) c
        FROM """ + _q(table) + """ d
        LEFT JOIN news_raw_feed_events r ON r.news_uid=d.news_uid
        WHERE d.news_uid IN (""" + marks + """)
          AND r.news_uid IS NULL
        GROUP BY d.news_uid
        LIMIT 50
    """, uids).fetchall()
    return [{"news_uid": r[0], "count": r[1]} for r in rows]

def _uid_policy_violations(uids: List[str], allowed_prefixes: List[str]) -> List[Dict[str, Any]]:
    bad = []
    for uid in uids:
        matches = [p for p in allowed_prefixes if uid.startswith(p)]
        if len(matches) != 1:
            bad.append({"news_uid": uid, "matched_prefixes": matches})
    return bad[:50]

def _duplicate_values(values: List[str]) -> List[str]:
    seen = set()
    dup = []
    for v in values:
        if v in seen and v not in dup:
            dup.append(v)
        seen.add(v)
    return dup[:50]

def verify_news_runtime_policy(db_path: str = str(DB), recent_limit: int = DEFAULT_RECENT_LIMIT, prior_observation_path: Optional[str] = None) -> Dict[str, Any]:
    policy = _load_policy()
    failures: List[str] = []
    warnings: List[str] = []

    prior = None
    if prior_observation_path:
        p = Path(prior_observation_path)
        if p.exists():
            prior = json.loads(p.read_text(encoding="utf-8"))
            if prior.get("decision") != "OK_NEWS_CONTINUOUS_PRODUCER_OBSERVATION_WINDOW_NOAPI":
                failures.append("prior_observation_not_ok")
        else:
            failures.append("prior_observation_missing")

    con = sqlite3.connect("file:" + str(db_path) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        missing = [t for t in TABLES if not _table_exists(con, t)]
        if missing:
            failures.append("missing_tables:" + ",".join(missing))
            return {"stage":"NEWS_RUNTIME_POLICY_VERIFIER_V1","generated_at_utc":_now(),"decision":"FAIL_NEWS_RUNTIME_POLICY_VERIFIER_V1","failures":failures,"warnings":warnings}

        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        counts = _counts(con)
        bad_flags = _bad_flags(con)
        recent_uids = _recent_raw_uids(con, recent_limit)
        uid_violations = _uid_policy_violations(recent_uids, policy["uid_policy"]["allowed_prefixes"])
        recent_duplicates = _duplicate_values(recent_uids)
        recent_orphans = {t: _orphan_recent(con, t, recent_uids) for t in ["news_token_match_events","news_signal_events","news_score_events_v1"]}
        derived_recent_counts = _recent_derived_counts(con, recent_uids)

        if integrity != "ok":
            failures.append("sqlite_integrity_not_ok")
        if bad_flags != 0:
            failures.append("bad_trade_flags_nonzero")
        if uid_violations:
            failures.append("uid_policy_violation")
        if recent_duplicates:
            failures.append("recent_uid_duplicate")
        if any(recent_orphans[t] for t in recent_orphans):
            failures.append("recent_orphan_derived_rows")

        if prior:
            delta = prior.get("delta", {})
            raw_delta = int(delta.get("news_raw_feed_events", 0))
            match_delta = int(delta.get("news_token_match_events", 0))
            signal_delta = int(delta.get("news_signal_events", 0))
            score_delta = int(delta.get("news_score_events_v1", 0))
            if min(raw_delta, match_delta, signal_delta, score_delta) < 0:
                failures.append("negative_delta_policy_violation")
            if not (raw_delta >= match_delta == signal_delta == score_delta >= 0):
                failures.append("downstream_delta_policy_violation")
            if raw_delta > int(policy["volume_policy"]["max_single_cycle_raw_delta_hard"]):
                failures.append("hard_volume_policy_violation")
            elif raw_delta > int(policy["volume_policy"]["max_single_cycle_raw_delta_soft"]):
                warnings.append("soft_volume_policy_observe")

        route = "HOLD" if failures else "OK"

        return {
            "stage": "NEWS_RUNTIME_POLICY_VERIFIER_V1",
            "generated_at_utc": _now(),
            "decision": "OK_NEWS_RUNTIME_POLICY_VERIFIER_V1" if not failures else "FAIL_NEWS_RUNTIME_POLICY_VERIFIER_V1",
            "policy_id": policy["policy_id"],
            "repair_id": policy.get("repair_id"),
            "bounded_window_only": True,
            "recent_limit": recent_limit,
            "counts": counts,
            "integrity": integrity,
            "bad_flags": bad_flags,
            "recent_raw_uid_count": len(recent_uids),
            "derived_recent_counts": derived_recent_counts,
            "uid_policy_violations": uid_violations,
            "recent_duplicates": recent_duplicates,
            "recent_orphans": recent_orphans,
            "routing": {"route": route, "hold_required": bool(failures), "quarantine_required": False},
            "authority": policy["authority"],
            "failures": failures,
            "warnings": warnings
        }
    finally:
        con.close()

def verify_policy(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        before = verify_news_runtime_policy()
        if before["decision"] != "OK_NEWS_RUNTIME_POLICY_VERIFIER_V1":
            return {"decision":"BLOCKED_BY_NEWS_RUNTIME_POLICY_VERIFIER_V1","policy_result":before}
        result = func(*args, **kwargs)
        after = verify_news_runtime_policy()
        if after["decision"] != "OK_NEWS_RUNTIME_POLICY_VERIFIER_V1":
            return {"decision":"POST_RUN_BLOCKED_BY_NEWS_RUNTIME_POLICY_VERIFIER_V1","function_result":result,"policy_result":after}
        return result
    return wrapper

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=str(DB))
    ap.add_argument("--recent-limit", type=int, default=DEFAULT_RECENT_LIMIT)
    ap.add_argument("--prior-observation", default=str(ROOT / "data/control/news_continuous_producer_observation_window_noapi_v1.json"))
    args = ap.parse_args()
    print(json.dumps(verify_news_runtime_policy(args.db_path, args.recent_limit, args.prior_observation), ensure_ascii=False, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
