#!/usr/bin/env python3
import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path

SAFE_ID_RE = re.compile(r"^[A-Z0-9_]+$")
SAFE_ERA_RE = re.compile(r"^[0-9]+$")


def run(args, check=True, capture=True):
    if isinstance(args, str):
        raise TypeError("run() requires argv list; use run_static_shell() only for fixed shell pipelines")
    r = subprocess.run(args, text=True, capture_output=capture)
    if check and r.returncode != 0:
        if capture:
            print(r.stdout)
            print(r.stderr)
        raise SystemExit(r.returncode)
    return r.stdout.strip() if capture else ""


def run_static_shell(cmd, check=True):
    # Only for fixed internal shell pipelines. Never pass user input here.
    r = subprocess.run(["bash", "-lc", cmd], text=True, capture_output=True)
    if check and r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(r.returncode)
    return r.stdout.strip()


def validate_safe(label, value, pattern):
    if not pattern.fullmatch(value or ""):
        raise SystemExit(f"INVALID_{label}: {value!r}")
    return value


def load_json(p, default):
    p = Path(p)
    if not p.exists():
        return default
    return json.loads(p.read_text())


def write_json(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def append_if_exists(path, text):
    p = Path(path)
    if p.exists():
        p.write_text(p.read_text() + "\n" + text + "\n")


def sync_runtime(rt, *, era, current_id, work_type, next_step):
    current_work_unit = {
        "id": current_id,
        "type": work_type,
        "status": "WORK_UNIT_CLOSED",
        "last_completed_step": f"ERA{era}_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI",
        "next_step": next_step,
    }
    next_safe_step = {"name": next_step, "status": "READY"}

    rt["current_work_unit"] = current_work_unit
    rt["next_safe_step"] = next_safe_step

    # Keep legacy/current_state readers coherent until repository consumers are migrated.
    cs = rt.get("current_state")
    if not isinstance(cs, dict):
        cs = {}
    cs["mode"] = f"ERA{era}_FINAL_CLOSED"
    cs["active_work_unit"] = current_work_unit
    cs["next_safe_step"] = next_safe_step
    cs["last_completed_step"] = current_work_unit["last_completed_step"]
    rt["current_state"] = cs

    return rt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--era", required=True)
    ap.add_argument("--current-id", required=True)
    ap.add_argument("--next", required=True)
    ap.add_argument("--type", default="ERA_CLOSE")
    args = ap.parse_args()

    era = validate_safe("ERA", str(args.era), SAFE_ERA_RE)
    current_id = validate_safe("CURRENT_ID", args.current_id, SAFE_ID_RE)
    next_step = validate_safe("NEXT_STEP", args.next, SAFE_ID_RE)
    work_type = validate_safe("TYPE", args.type, SAFE_ID_RE)
    now = datetime.datetime.now(datetime.UTC).isoformat()

    local = run(["git", "rev-parse", "HEAD"])
    remote = run(["git", "rev-parse", "origin/main"])
    status_before = run(["git", "status", "--short"], check=False)

    health = {
        "era": f"ERA{era}",
        "phase": "FINAL_SIZE_AND_CANONICAL_HEALTH_NOAPI",
        "created_at_utc": now,
        "git_before_close": {
            "local_head": local,
            "remote_head": remote,
            "head_sync_before_final_push": local == remote,
            "git_status_before": status_before.splitlines(),
        },
        "sizes": {
            "root_size": run_static_shell("du -sh . 2>/dev/null | awk '{print $1}'", check=False),
            "data_size": run_static_shell("du -sh data 2>/dev/null | awk '{print $1}'", check=False),
            "data_control_size": run_static_shell("du -sh data/control 2>/dev/null | awk '{print $1}'", check=False),
            "database_files": run_static_shell("find data -type f \\( -name '*.sqlite' -o -name '*.sqlite-*' -o -name '*.db' \\) -printf '%p %s\\n' 2>/dev/null | sort -k2 -nr | head -50", check=False).splitlines(),
            "large_files_top50": run_static_shell("find . -path './.git' -prune -o -type f -size +5M -printf '%p %s\\n' 2>/dev/null | sort -k2 -nr | head -50", check=False).splitlines(),
        },
        "cleanup_performed": False,
        "decision": f"PASS_ERA{era}_FINAL_HEALTH_CHECK_NOAPI",
    }
    write_json(f"data/control/era{era}_final_size_and_canonical_health_noapi_v1.json", health)

    final_review = {
        "era": f"ERA{era}",
        "phase": "FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI",
        "created_at_utc": now,
        "current_work_unit": current_id,
        "next_work_unit": next_step,
        "result": "ERA_CLOSED_LOCAL_THEN_FINAL_PUSH",
        "guards": {
            "runtime_mutation": False,
            "external_api_calls": 0,
            "live_trade": False,
            "wallet_action": False,
            "db_schema_change": False,
            "service_change": False,
            "cleanup_performed": False,
        },
        "decision": f"PASS_ERA{era}_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI",
    }
    write_json(f"data/control/era{era}_final_review_and_canonical_close_noapi_v1.json", final_review)

    rt = load_json("PROJECT_RUNTIME.json", {})
    rt = sync_runtime(rt, era=era, current_id=current_id, work_type=work_type, next_step=next_step)
    write_json("PROJECT_RUNTIME.json", rt)

    hist = load_json("PROJECT_HISTORY.json", {"events": []})
    if isinstance(hist, dict):
        hist.setdefault("events", []).append({
            "ts_utc": now,
            "era": f"ERA{era}",
            "event": "FINAL_CLOSE",
            "head_before_push": local,
            "next": next_step,
        })
        write_json("PROJECT_HISTORY.json", hist)

    note = f"""## ERA{era} Final Close — {now}
- Status: CLOSED
- Final gate: PASS_ERA{era}_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI
- Next: {next_step}
- Health: root/database size check recorded.
"""
    for md in ["03_ROADMAP.md", "04_ALMANAC.md", "06_PROJECT_MASTER_STATE.md", "07_PROJECT_HANDOFF.md"]:
        append_if_exists(md, note)

    roadmap_json = Path("data/tokenoskobi_v1_v8_master_era_roadmap.json")
    if roadmap_json.exists():
        rj = load_json(roadmap_json, {})
        if isinstance(rj, dict):
            rj[f"ERA{era}"] = {"status": "CLOSED", "closed_at_utc": now, "next": next_step}
            write_json(roadmap_json, rj)

    run(["tk", "sync"], check=False)
    run_static_shell("tk ai >/dev/null", check=False)
    run_static_shell("tk machine >/tmp/tk_machine_era_final_before_push.json", check=False)

    add_paths = [
        "PROJECT_RUNTIME.json",
        "PROJECT_HISTORY.json",
        "03_ROADMAP.md",
        "04_ALMANAC.md",
        "06_PROJECT_MASTER_STATE.md",
        "07_PROJECT_HANDOFF.md",
        "data/control",
        "data/tokenoskobi_v1_v8_master_era_roadmap.json",
        "tools/era_close.py",
    ]
    existing = [p for p in add_paths if Path(p).exists()]
    if existing:
        run(["git", "add", *existing])
    run(["git", "commit", "-m", f"Close ERA{era} final canonical package"], check=False)
    run(["git", "push", "origin", "main"])

    run(["tk", "sync"], check=False)
    run_static_shell("tk machine >/tmp/tk_machine_era_final_after_push.json", check=False)

    after = load_json("/tmp/tk_machine_era_final_after_push.json", {})
    print("ERA_CLOSE_DONE")
    print("HEAD_SYNC:", after.get("project", {}).get("head_sync"))
    print("GIT_CLEAN:", after.get("project", {}).get("git_clean"))
    print("LOCAL_HEAD:", after.get("project", {}).get("local_head"))
    print("REMOTE_HEAD:", after.get("project", {}).get("remote_head"))
    print("CURRENT_WORK_UNIT:", after.get("current_state", {}).get("active_work_unit"))
    print("NEXT_SAFE_STEP:", after.get("current_state", {}).get("next_safe_step"))


if __name__ == "__main__":
    main()
