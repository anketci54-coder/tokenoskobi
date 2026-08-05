#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import os
import sqlite3
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_F_FINAL_OPERATIONAL_SEAL_WITH_KNOWN_WARNINGS"

OUT_JSON = ROOT / "data/control/news_f_final_operational_seal_with_known_warnings_v1.json"
OUT_REPORT = ROOT / "reports/LATEST_NEWS_F_FINAL_OPERATIONAL_SEAL_WITH_KNOWN_WARNINGS.md"
OUT_SUMMARY = ROOT / "reports/NEWS_F_OPERATIONAL_SEAL_SUMMARY.md"
OUT_DOCTRINE = ROOT / "docs/CENGIZHAN_INTELLIGENCE_DOCTRINE.md"

PROJECT_RUNTIME = ROOT / "PROJECT_RUNTIME.json"
PROJECT_BOOT = ROOT / "PROJECT_BOOT.json"
PROJECT_MASTER = ROOT / "PROJECT_MASTER_STATE.md"
PROJECT_HANDOFF = ROOT / "PROJECT_HANDOFF.md"

DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

REFS = {
    "news_a": ROOT / "data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json",
    "news_b": ROOT / "data/control/news_b_runner_timer_journal_argv_audit_noapi_v1.json",
    "news_b_fix1": ROOT / "data/control/news_b_fix_1_systemd_stdout_stderr_path_targeted_apply_v1.json",
    "news_b_fix1_post": ROOT / "data/control/news_b_fix_1_post_apply_audit_noapi_v1.json",
    "news_b_fix2": ROOT / "data/control/news_b_fix_2_timer_activation_targeted_apply_v1.json",
    "news_b_fix2_post": ROOT / "data/control/news_b_fix_2_post_activation_audit_noapi_v1.json",
    "news_c": ROOT / "data/control/news_c_downstream_checksum_fingerprint_noapi_v1.json",
    "news_d": ROOT / "data/control/news_d_panel_readmodel_freshness_noapi_v1.json",
    "news_e": ROOT / "data/control/news_e_review_prompt_and_seal_prep_noapi_v1.json",
}

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1",
    "news_runtime_freshness_v1",
]


def now():
    return datetime.now(timezone.utc)


def iso_now():
    return now().isoformat()


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def run_cmd(args, timeout=35):
    try:
        p = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {"cmd": args, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as e:
        return {"cmd": args, "rc": None, "stdout": "", "stderr": type(e).__name__ + ":" + str(e)[:400]}


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def read_json(path):
    if not path.exists():
        return None, "MISSING"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:400]


def safe_write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def safe_write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    with open(tmp, encoding="utf-8") as f:
        json.load(f)
    os.replace(tmp, path)


def open_db_ro():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True, timeout=8)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    return con


def db_snapshot():
    out = {"error": None, "tables": {}}
    if not DB.exists():
        out["error"] = "DB_NOT_FOUND"
        return out
    try:
        con = open_db_ro()
        cur = con.cursor()
        for table in TABLES:
            item = {"exists": False, "count": None, "timestamp_col": None, "min_ts": None, "max_ts": None, "sample_last": None, "error": None}
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cur.fetchone() is None:
                out["tables"][table] = item
                continue
            item["exists"] = True
            cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
            item["count"] = int(cur.fetchone()["c"])
            cols = [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
            ts_col = None
            for c in ["created_at_utc", "fetched_at_utc", "generated_at_utc", "updated_at_utc", "last_observed_at_utc", "published_at_utc"]:
                if c in cols:
                    ts_col = c
                    break
            item["timestamp_col"] = ts_col
            if ts_col:
                cur.execute(f"SELECT MIN({ts_col}) AS mn, MAX({ts_col}) AS mx FROM {table}")
                r = cur.fetchone()
                item["min_ts"] = r["mn"]
                item["max_ts"] = r["mx"]
                cur.execute(f"SELECT * FROM {table} ORDER BY {ts_col} DESC LIMIT 1")
                rr = cur.fetchone()
                item["sample_last"] = dict(rr) if rr else None
            out["tables"][table] = item
        con.close()
    except Exception as e:
        out["error"] = type(e).__name__ + ":" + str(e)[:400]
    return out


def db_counts(snap):
    t = snap.get("tables", {})
    return {
        "raw": t.get("news_raw_feed_events", {}).get("count"),
        "match": t.get("news_token_match_events", {}).get("count"),
        "signal": t.get("news_signal_events", {}).get("count"),
        "score": t.get("news_score_events_v1", {}).get("count"),
        "freshness": t.get("news_runtime_freshness_v1", {}).get("count"),
    }


def systemd_snapshot():
    return {
        "timer_active": run_cmd(["systemctl", "is-active", TIMER]),
        "timer_enabled": run_cmd(["systemctl", "is-enabled", TIMER]),
        "timer_show": run_cmd(["systemctl", "show", TIMER, "-p", "ActiveState", "-p", "SubState", "-p", "Result", "-p", "Triggers", "-p", "UnitFileState", "-p", "LastTriggerUSec", "-p", "NextElapseUSecRealtime"]),
        "timer_status": run_cmd(["systemctl", "status", TIMER, "--no-pager", "-l"]),
        "list_timers": run_cmd(["systemctl", "list-timers", "--all", TIMER, "--no-pager"]),
        "service_active": run_cmd(["systemctl", "is-active", SERVICE]),
        "service_enabled": run_cmd(["systemctl", "is-enabled", SERVICE]),
        "service_show": run_cmd(["systemctl", "show", SERVICE, "-p", "ActiveState", "-p", "SubState", "-p", "Result", "-p", "ExecMainStatus", "-p", "ExecStart", "-p", "TriggeredBy", "-p", "UnitFileState"]),
    }


def journal_recent():
    since = (now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S UTC")
    r = run_cmd(["journalctl", "-u", SERVICE, "-u", TIMER, "--since", since, "--no-pager", "--output=short-iso"], timeout=45)
    text = (r.get("stdout") or "") + "\n" + (r.get("stderr") or "")
    low = text.lower()
    return {
        "cmd_rc": r.get("rc"),
        "line_count": len([x for x in text.splitlines() if x.strip()]),
        "status_209_stdout_count": low.count("status=209/stdout"),
        "failed_set_up_stdout_count": low.count("failed to set up standard output"),
        "invalidargument_count": low.count("invalidargument"),
        "rc2_count": low.count("rc=2") + low.count("status=2"),
        "traceback_count": low.count("traceback"),
        "failed_count": low.count("failed"),
        "started_timer_count": low.count("started tokenoskobi-news-radar-refresh.timer"),
        "started_service_count": low.count("starting tokenoskobi-news-radar-refresh.service") + low.count("started tokenoskobi-news-radar-refresh.service"),
        "finished_service_count": low.count("finished tokenoskobi-news-radar-refresh.service"),
        "tail": "\n".join(text.splitlines()[-80:]),
    }


def compact_ref(name, path):
    obj, err = read_json(path)
    return {
        "name": name,
        "path": str(path),
        "read_error": err,
        "stage": obj.get("stage") if isinstance(obj, dict) else None,
        "decision": obj.get("decision") if isinstance(obj, dict) else None,
        "next_step": obj.get("next_step") if isinstance(obj, dict) else None,
        "generated_at_utc": obj.get("generated_at_utc") if isinstance(obj, dict) else None,
        "summary": obj.get("summary") if isinstance(obj, dict) else None,
        "known_warnings": obj.get("known_warnings") if isinstance(obj, dict) else None,
        "seal_wording_policy": obj.get("seal_wording_policy") if isinstance(obj, dict) else None,
        "seal_matrix": obj.get("seal_matrix") if isinstance(obj, dict) else None,
    }


def write_json_state(path, updater):
    before = {"path": rel(path), "exists": path.exists(), "sha256_before": sha256_file(path), "updated": False, "error": None}
    if not path.exists():
        before["error"] = "MISSING"
        return before
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        updated = updater(obj)
        safe_write_json(path, updated)
        before["updated"] = True
        before["sha256_after"] = sha256_file(path)
        return before
    except Exception as e:
        before["error"] = type(e).__name__ + ":" + str(e)[:400]
        return before


def update_runtime_obj(obj, result):
    obj["updated_at_utc"] = result["generated_at_utc"]
    obj["mode"] = "NEWS_F_COLD_NEWS_OPERATIONAL_SEAL_WITH_KNOWN_WARNINGS"
    obj["last_completed"] = STAGE
    obj["next_safe_step"] = "HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI"
    obj["news_operational_state"] = {
        "status": "COLD_NEWS_PRODUCER_OPERATIONAL_WITH_KNOWN_WARNINGS",
        "seal_head": result["git"]["head"],
        "seal_stage": STAGE,
        "timer_role": "COLD_BACKFILL_FALLBACK_ONLY",
        "timer_active": result["summary"]["timer_active"],
        "timer_enabled": result["summary"]["timer_enabled"],
        "raw_count": result["summary"]["raw_count"],
        "match_count": result["summary"]["match_count"],
        "signal_count": result["summary"]["signal_count"],
        "score_count": result["summary"]["score_count"],
        "known_warnings": result["known_warnings"],
        "hot_gateway_deferred": True,
        "hot_gateway_next": "HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI",
    }
    obj["hard_rules"] = obj.get("hard_rules", {})
    obj["hard_rules"]["live_trade"] = "LOCKED"
    obj["hard_rules"]["paper_trade"] = "LOCKED"
    obj["hard_rules"]["ai_trade_authority"] = "ZERO"
    obj["hard_rules"]["human_approval_required"] = True
    return obj


def update_boot_obj(obj, result):
    obj["boot_version"] = obj.get("boot_version", "1.3")
    obj["updated_at_utc"] = result["generated_at_utc"]
    if isinstance(obj.get("project"), dict):
        obj["project"]["status"] = "NEWS_F_COLD_NEWS_OPERATIONAL_SEAL_WITH_KNOWN_WARNINGS"
        obj["project"]["mode"] = "COLD_NEWS_SEALED_HOT_GATEWAY_DEFERRED"
    obj["startup_priority"] = [
        "PROJECT_RUNTIME.json",
        "PROJECT_MASTER_STATE.md",
        "PROJECT_HANDOFF.md",
        "data/control/news_f_final_operational_seal_with_known_warnings_v1.json",
    ]
    obj["news_current_truth"] = {
        "status": "COLD_NEWS_PRODUCER_OPERATIONAL_WITH_KNOWN_WARNINGS",
        "seal_head": result["git"]["head"],
        "raw_count": result["summary"]["raw_count"],
        "match_count": result["summary"]["match_count"],
        "signal_count": result["summary"]["signal_count"],
        "score_count": result["summary"]["score_count"],
        "timer_active": result["summary"]["timer_active"],
        "timer_enabled": result["summary"]["timer_enabled"],
        "known_warnings": result["known_warnings"],
        "do_not_claim": [
            "NEWS_FULLY_CLEAN",
            "PANEL_FULLY_VERIFIED",
            "FRESHNESS_FULLY_CURRENT",
            "HOT_INTELLIGENCE_IMPLEMENTED",
            "REAL_TIME_INTELLIGENCE_COMPLETE",
            "TRADE_OR_PAPER_AUTHORITY_ENABLED",
        ],
        "next_safe_step": "HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI",
    }
    return obj


def update_markdown_with_block(path, title, block):
    before = {"path": rel(path), "exists": path.exists(), "sha256_before": sha256_file(path), "updated": False, "error": None}
    start = f"<!-- {title}:START -->"
    end = f"<!-- {title}:END -->"
    wrapped = start + "\n" + block.strip() + "\n" + end + "\n\n"
    try:
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        if start in old and end in old:
            pre = old.split(start, 1)[0]
            rest = old.split(start, 1)[1].split(end, 1)[1]
            new = pre + wrapped + rest.lstrip("\n")
        else:
            new = wrapped + old
        safe_write_text(path, new)
        before["updated"] = True
        before["sha256_after"] = sha256_file(path)
        return before
    except Exception as e:
        before["error"] = type(e).__name__ + ":" + str(e)[:400]
        return before


def doctrine_text(result):
    return f"""# CENGIZHAN INTELLIGENCE DOCTRINE

- generated_at_utc: `{result['generated_at_utc']}`
- source_stage: `{STAGE}`
- current_news_seal: `COLD_NEWS_PRODUCER_OPERATIONAL_WITH_KNOWN_WARNINGS`
- hot_gateway_status: `DEFERRED_AFTER_NEWS_F`

## Doctrine

1. Ordu uyumaz.
2. Haber beklenmez; haber avlanır.
3. Her haber komutaya gitmez.
4. Alakasız haber kapıda öldürülür.
5. Kritik haber hızlı ulakla taşınır.
6. Psikolojik harp ayrı risk sınıfıdır.
7. Tuzak, sahte panik, manipülasyon ve aldatma erken sezilir.
8. Lojistik yoksa istihbarat yoktur.
9. Teknoloji, hız ve disiplin aynı zincirde çalışır.
10. 20 dakikalık timer sadece cold backfill/fallback hattıdır; ana istihbarat mimarisi değildir.

## Cold / Hot Split

### COLD NEWS REFRESH

- Current state: `OPERATIONAL_WITH_KNOWN_WARNINGS`
- Purpose: missed-news backfill, audit trail, low-cost periodic scan.
- Timer: `20min`
- Not final war intelligence.

### HOT_INTELLIGENCE_INGRESS_GATEWAY

- Status: `NEXT_SAFE_STEP_AFTER_NEWS_F`
- Sources: Telegram, Discord, X, fast crypto news, onchain watcher, wallet watcher, mempool/DEX signals.
- Gate: relevance filter, source trust, duplicate filter, adversarial tactic classifier.
- Router: CRITICAL / WATCH / INFO / DROP.
- Conflict layer: onchain vs social vs news conflict resolution.
- Consumers: Hunter, Prosecutor, Risk, Whale, Panel, Telegram alarm.

## Forbidden Claims

- NEWS fully clean
- panel fully verified
- freshness fully current
- real-time intelligence implemented
- hot intelligence gateway implemented
- trade or paper authority enabled
"""


def state_block(result):
    warnings = "\n".join([f"- `{w.get('code')}`: {w.get('message')}" for w in result["known_warnings"]])
    return f"""# NEWS-F Current State

- generated_at_utc: `{result['generated_at_utc']}`
- head: `{result['git']['head']}`
- decision: `{result['decision']}`
- status: `COLD_NEWS_PRODUCER_OPERATIONAL_WITH_KNOWN_WARNINGS`
- next_safe_step: `HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI`

## Counts

- raw: `{result['summary']['raw_count']}`
- match: `{result['summary']['match_count']}`
- signal: `{result['summary']['signal_count']}`
- score: `{result['summary']['score_count']}`
- freshness: `{result['summary']['freshness_count']}`

## Timer

- active: `{result['summary']['timer_active']}`
- enabled: `{result['summary']['timer_enabled']}`
- role: `COLD_BACKFILL_FALLBACK_ONLY`

## Known Warnings

{warnings}

## Do Not Claim

- `NEWS_FULLY_CLEAN`
- `PANEL_FULLY_VERIFIED`
- `FRESHNESS_FULLY_CURRENT`
- `HOT_INTELLIGENCE_IMPLEMENTED`
- `REAL_TIME_INTELLIGENCE_COMPLETE`
- `TRADE_OR_PAPER_AUTHORITY_ENABLED`

## Doctrine

- `CENGIZHAN_INTELLIGENCE_DOCTRINE` is preserved.
- `HOT_INTELLIGENCE_INGRESS_GATEWAY` opens after this seal as a separate plan.
"""


def report_text(result):
    lines = []
    lines.append("# NEWS-F Final Operational Seal With Known Warnings")
    lines.append("")
    lines.append(f"- stage: `{STAGE}`")
    lines.append(f"- generated_at_utc: `{result['generated_at_utc']}`")
    lines.append(f"- decision: `{result['decision']}`")
    lines.append(f"- next_step: `{result['next_step']}`")
    lines.append(f"- head: `{result['git']['head']}`")
    lines.append("")
    lines.append("## Seal Statement")
    lines.append("")
    lines.append("`COLD NEWS PRODUCER OPERATIONAL WITH KNOWN WARNINGS`")
    lines.append("")
    lines.append("This is not a full-clean NEWS seal. This is not a HOT intelligence implementation. The 20-minute timer is a cold backfill/fallback patrol.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    for k in ["raw_count", "match_count", "signal_count", "score_count", "freshness_count"]:
        lines.append(f"- {k}: `{result['summary'][k]}`")
    lines.append("")
    lines.append("## Timer")
    lines.append("")
    lines.append(f"- active: `{result['summary']['timer_active']}`")
    lines.append(f"- enabled: `{result['summary']['timer_enabled']}`")
    lines.append("")
    lines.append("## Known Warnings")
    lines.append("")
    for w in result["known_warnings"]:
        lines.append(f"- `{w.get('code')}`: {w.get('message')}")
    lines.append("")
    lines.append("## Seal Matrix")
    lines.append("")
    for k, v in result["seal_matrix"].items():
        lines.append(f"- `{k}`: `{v.get('status')}`")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for f in result["findings"]:
        lines.append(f"- `{f['level']}` {f['code']}: {f['message']}")
    lines.append("")
    lines.append("## State Updates")
    lines.append("")
    for k, v in result["state_updates"].items():
        lines.append(f"- `{k}`: updated=`{v.get('updated')}` error=`{v.get('error')}`")
    lines.append("")
    return "\n".join(lines)


def main():
    git_head = run_cmd(["git", "rev-parse", "HEAD"]).get("stdout")
    git_branch = run_cmd(["git", "branch", "--show-current"]).get("stdout")
    git_status_before = run_cmd(["git", "status", "--short"]).get("stdout")

    refs = {name: compact_ref(name, path) for name, path in REFS.items()}
    db = db_snapshot()
    counts = db_counts(db)
    sysd = systemd_snapshot()
    journal = journal_recent()

    news_e = refs.get("news_e", {})
    known_warnings = news_e.get("known_warnings") or []
    seal_matrix = news_e.get("seal_matrix") or {}
    wording_policy = news_e.get("seal_wording_policy") or {}

    summary = {
        "raw_count": counts.get("raw"),
        "match_count": counts.get("match"),
        "signal_count": counts.get("signal"),
        "score_count": counts.get("score"),
        "freshness_count": counts.get("freshness"),
        "timer_active": (sysd.get("timer_active", {}).get("stdout") or "").strip(),
        "timer_enabled": (sysd.get("timer_enabled", {}).get("stdout") or "").strip(),
        "journal_status_209_stdout_count": journal.get("status_209_stdout_count"),
        "journal_failed_set_up_stdout_count": journal.get("failed_set_up_stdout_count"),
        "journal_invalidargument_count": journal.get("invalidargument_count"),
        "journal_rc2_count": journal.get("rc2_count"),
        "known_warning_count": len(known_warnings),
    }

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    missing_refs = [k for k, v in refs.items() if v.get("read_error")]
    if missing_refs:
        add("FAIL", "REFERENCE_CHAIN_INCOMPLETE", "Eksik/okunamayan artifact: " + ",".join(missing_refs))
    else:
        add("OK", "REFERENCE_CHAIN_READ", "NEWS-A through NEWS-E artifact chain okundu.")

    if news_e.get("decision") == "WARN_NEWS_E_READY_FOR_REVIEW_AND_NEWS_F_SEAL_WITH_KNOWN_WARNINGS":
        add("OK", "NEWS_E_READY_REFERENCE_OK", "NEWS-E seal prep ready with known warnings.")
    else:
        add("FAIL", "NEWS_E_NOT_READY", "NEWS-E decision beklenen değil: " + str(news_e.get("decision")))

    if summary["timer_active"] == "active" and summary["timer_enabled"] == "enabled":
        add("OK", "COLD_NEWS_TIMER_ACTIVE_ENABLED", "NEWS timer active/enabled.")
    else:
        add("FAIL", "COLD_NEWS_TIMER_NOT_ACTIVE_ENABLED", "NEWS timer active/enabled değil.")

    if counts.get("match") == 47 and counts.get("signal") == 47 and counts.get("score") == 47:
        add("OK", "DOWNSTREAM_47_CHAIN_STILL_PRESENT", "match/signal/score = 47/47/47.")
    else:
        add("FAIL", "DOWNSTREAM_47_CHAIN_NOT_PRESENT", "match/signal/score beklenen değil.")

    if isinstance(counts.get("raw"), int) and counts.get("raw") >= 270:
        add("OK", "RAW_PRODUCER_RUNNING", "Raw producer count 270 veya üstünde.")
    else:
        add("WARN", "RAW_PRODUCER_COUNT_REVIEW", "Raw count 270 altı veya bilinmiyor.")

    if journal.get("status_209_stdout_count") == 0 and journal.get("failed_set_up_stdout_count") == 0:
        add("OK", "STDOUT_209_NOT_PRESENT_RECENT", "Son journal penceresinde 209/STDOUT yok.")
    else:
        add("FAIL", "STDOUT_209_PRESENT_RECENT", "Son journal penceresinde 209/STDOUT görüldü.")

    if journal.get("invalidargument_count") == 0 and journal.get("rc2_count") == 0:
        add("OK", "INVALIDARGUMENT_RC2_NOT_PRESENT_RECENT", "Son journal penceresinde INVALIDARGUMENT/rc2 yok.")
    else:
        add("WARN", "INVALIDARGUMENT_OR_RC2_REVIEW", "Son journal penceresinde INVALIDARGUMENT/rc2 review gerekir.")

    if known_warnings:
        add("WARN", "SEAL_WITH_KNOWN_WARNINGS", "Known warnings mevcut; seal wording full-clean olamaz.")
    else:
        add("OK", "NO_KNOWN_WARNINGS", "Known warning yok.")

    if "HOT_INTELLIGENCE_INGRESS_GATEWAY DEFERRED AFTER NEWS-F" in wording_policy.get("allowed", []):
        add("OK", "HOT_GATEWAY_DEFERRED_POLICY_PRESENT", "HOT Gateway post-seal olarak ayrıldı.")
    else:
        add("FAIL", "HOT_GATEWAY_DEFERRED_POLICY_MISSING", "HOT Gateway deferred policy eksik.")

    fail_count = sum(1 for f in findings if f["level"] == "FAIL")
    warn_count = sum(1 for f in findings if f["level"] == "WARN")

    if fail_count:
        decision = "FAIL_NEWS_F_FINAL_OPERATIONAL_SEAL_BLOCKED"
        next_step = "REVIEW_NEWS_F_BLOCKERS"
    else:
        decision = "WARN_NEWS_F_FINAL_OPERATIONAL_SEAL_CLOSED_WITH_KNOWN_WARNINGS"
        next_step = "HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": iso_now(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "final_seal_artifact_write": True,
            "project_runtime_update": True,
            "project_boot_update": True,
            "project_master_state_update": True,
            "project_handoff_update": True,
            "doctrine_doc_write": True,
            "real_db_write": False,
            "db_schema_write": False,
            "panel_write": False,
            "readmodel_write": False,
            "runner_code_change": False,
            "matcher_code_change": False,
            "systemd_change": False,
            "timer_change": False,
            "service_change": False,
            "external_api_call": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
        },
        "git": {
            "head": git_head,
            "branch": git_branch,
            "status_before": git_status_before,
        },
        "references": refs,
        "db_snapshot": db,
        "systemd_snapshot": sysd,
        "journal_recent": journal,
        "known_warnings": known_warnings,
        "seal_matrix": seal_matrix,
        "seal_wording_policy": wording_policy,
        "summary": summary,
        "findings": findings,
        "state_updates": {},
    }

    safe_write_text(OUT_DOCTRINE, doctrine_text(result))

    block = state_block(result)
    state_updates = {}
    state_updates["project_runtime"] = write_json_state(PROJECT_RUNTIME, lambda obj: update_runtime_obj(obj, result))
    state_updates["project_boot"] = write_json_state(PROJECT_BOOT, lambda obj: update_boot_obj(obj, result))
    state_updates["project_master_state"] = update_markdown_with_block(PROJECT_MASTER, "NEWS_F_CURRENT_STATE", block)
    state_updates["project_handoff"] = update_markdown_with_block(PROJECT_HANDOFF, "NEWS_F_CURRENT_HANDOFF", block)
    state_updates["cengizhan_doctrine"] = {
        "path": rel(OUT_DOCTRINE),
        "exists": OUT_DOCTRINE.exists(),
        "updated": True,
        "sha256_after": sha256_file(OUT_DOCTRINE),
        "error": None,
    }

    result["state_updates"] = state_updates
    state_errors = [k for k, v in state_updates.items() if v.get("error")]
    if state_errors:
        result["findings"].append({"level": "WARN", "code": "STATE_UPDATE_WARNINGS", "message": "State update warning: " + ",".join(state_errors)})
        result["summary"]["warn_count"] = warn_count + 1
    else:
        result["summary"]["warn_count"] = warn_count
    result["summary"]["fail_count"] = fail_count

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_REPORT, report_text(result))
    safe_write_text(OUT_SUMMARY, state_block(result))

    print("OK_NEWS_F_FINAL_OPERATIONAL_SEAL_WITH_KNOWN_WARNINGS_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + rel(OUT_JSON))
    print("REPORT=" + rel(OUT_REPORT))
    print("SUMMARY=" + rel(OUT_SUMMARY))
    print("DOCTRINE=" + rel(OUT_DOCTRINE))
    print("RAW=" + str(summary["raw_count"]))
    print("MATCH=" + str(summary["match_count"]))
    print("SIGNAL=" + str(summary["signal_count"]))
    print("SCORE=" + str(summary["score_count"]))
    print("TIMER_ACTIVE=" + str(summary["timer_active"]))
    print("TIMER_ENABLED=" + str(summary["timer_enabled"]))
    print("KNOWN_WARNING_COUNT=" + str(summary["known_warning_count"]))
    print("WARN_COUNT=" + str(result["summary"]["warn_count"]))
    print("FAIL_COUNT=" + str(result["summary"]["fail_count"]))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
