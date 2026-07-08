#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "REPO_CLEANUP_POST_APPLY_AUDIT_NOAPI_AFTER_SAFE_1"

APPLY_JSON = ROOT / "data/control/repo_cleanup_apply_safe_1_after_news_f_v1.json"
OUT_JSON = ROOT / "data/control/repo_cleanup_post_apply_audit_noapi_after_safe_1_v1.json"
OUT_MD = ROOT / "reports/LATEST_REPO_CLEANUP_POST_APPLY_AUDIT_NOAPI_AFTER_SAFE_1.md"

EXPECTED_DIRTY_REVIEW = {
    "data/control/ACTIVE_CORE_RANKING.json",
    "data/control/ACTIVE_EXECUTION_GRAPH.json",
    "data/control/MINIMAL_ACTIVE_CORE_MANIFEST.json",
    "data/control/USED_BY_RUNTIME_INDEX.json",
}

EXPECTED_SELF_OUTPUTS = {
    "tools/repo_cleanup_post_apply_audit_noapi_v1.py",
    "data/control/repo_cleanup_post_apply_audit_noapi_after_safe_1_v1.json",
    "reports/LATEST_REPO_CLEANUP_POST_APPLY_AUDIT_NOAPI_AFTER_SAFE_1.md",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def run_cmd(args, timeout=45):
    try:
        p = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "cmd": args,
            "rc": p.returncode,
            "stdout": p.stdout.strip(),
            "stderr": p.stderr.strip(),
        }
    except Exception as e:
        return {
            "cmd": args,
            "rc": None,
            "stdout": "",
            "stderr": type(e).__name__ + ":" + str(e)[:400],
        }


def read_json(path):
    if not path.exists():
        return None, "MISSING"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:400]


def sha256_file(path, max_bytes=5_000_000):
    try:
        if path.is_file() and path.stat().st_size > max_bytes:
            return "SKIPPED_LARGE"
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def safe_write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    with open(tmp, encoding="utf-8") as f:
        json.load(f)
    os.replace(tmp, path)


def safe_write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def parse_git_status(text):
    rows = []
    for line in (text or "").splitlines():
        if not line.strip() or len(line) < 4:
            continue
        rows.append({"status": line[:2], "path": line[3:]})
    return rows


def collect_cache_leftovers():
    leftovers = []
    for p in ROOT.rglob("*"):
        if ".git" in p.parts:
            continue
        if p.name == "__pycache__" or p.suffix in {".pyc", ".pyo"}:
            leftovers.append(rel(p))
    return sorted(leftovers)


def file_state(path_str):
    p = ROOT / path_str
    try:
        st = p.stat()
        return {
            "path": path_str,
            "exists": True,
            "is_file": p.is_file(),
            "is_dir": p.is_dir(),
            "size_bytes": st.st_size if p.is_file() else None,
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
            "sha256": sha256_file(p) if p.is_file() else None,
        }
    except Exception as e:
        return {"path": path_str, "exists": False, "error": type(e).__name__ + ":" + str(e)[:200]}


def build_md(result):
    lines = []
    lines.append("# Repo Cleanup Post Apply Audit NOAPI After Safe-1")
    lines.append("")
    lines.append(f"- stage: `{STAGE}`")
    lines.append(f"- generated_at_utc: `{result['generated_at_utc']}`")
    lines.append(f"- decision: `{result['decision']}`")
    lines.append(f"- next_step: `{result['next_step']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for k, v in result["summary"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for f in result["findings"]:
        lines.append(f"- `{f['level']}` {f['code']}: {f['message']}")
    lines.append("")
    lines.append("## Remaining Dirty Review Files")
    lines.append("")
    for item in result["remaining_dirty_review_files"]:
        lines.append(f"- `{item.get('path')}` status=`{item.get('status')}`")
    lines.append("")
    lines.append("## Cache Leftovers")
    lines.append("")
    if result["cache_leftovers"]:
        for p in result["cache_leftovers"][:200]:
            lines.append(f"- `{p}`")
    else:
        lines.append("- NONE")
    lines.append("")
    lines.append("## Git Status")
    lines.append("")
    lines.append("```text")
    lines.append(result["git_status"].get("stdout", ""))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    apply_obj, apply_err = read_json(APPLY_JSON)

    git_head = run_cmd(["git", "rev-parse", "HEAD"]).get("stdout")
    git_status = run_cmd(["git", "status", "--short"])
    status_rows = parse_git_status(git_status.get("stdout"))

    cache_leftovers = collect_cache_leftovers()

    archive_target = None
    archive_target_exists = False
    phase_source_exists = (ROOT / "_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096").exists()

    if isinstance(apply_obj, dict):
        archive_target = ((apply_obj.get("archive_action") or {}).get("target"))
        if archive_target:
            archive_target_exists = Path(archive_target).exists()

    dirty_non_self = []
    dirty_review = []
    dirty_unexpected = []

    for row in status_rows:
        p = row["path"]
        if p in EXPECTED_SELF_OUTPUTS:
            continue
        if p in EXPECTED_DIRTY_REVIEW:
            dirty_review.append(row)
        else:
            dirty_unexpected.append(row)
        dirty_non_self.append(row)

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    if apply_err:
        add("FAIL", "APPLY_ARTIFACT_NOT_READ", f"Apply artifact okunamadı: {apply_err}")
    else:
        add("OK", "APPLY_ARTIFACT_READ", "Safe-1 apply artifact okundu.")

    if isinstance(apply_obj, dict) and apply_obj.get("decision") == "OK_REPO_CLEANUP_APPLY_SAFE_1_DONE":
        add("OK", "APPLY_DECISION_OK", "Safe-1 apply decision OK.")
    else:
        add("FAIL", "APPLY_DECISION_NOT_OK", "Safe-1 apply decision OK değil.")

    if not cache_leftovers:
        add("OK", "CACHE_LEFTOVERS_ABSENT", "__pycache__ / *.pyc leftover yok.")
    else:
        add("FAIL", "CACHE_LEFTOVERS_FOUND", f"Cache leftover count: {len(cache_leftovers)}")

    if not phase_source_exists and archive_target_exists:
        add("OK", "PHASE_DIR_ARCHIVED_EXTERNAL", "Phase temp dir repo dışı arşive taşındı ve kaynak repo içinde yok.")
    else:
        add("FAIL", "PHASE_DIR_ARCHIVE_NOT_CONFIRMED", f"source_exists={phase_source_exists}, target_exists={archive_target_exists}")

    if len(dirty_unexpected) == 0:
        add("OK", "NO_UNEXPECTED_DIRTY_FILES", "Beklenmeyen dirty dosya yok.")
    else:
        add("WARN", "UNEXPECTED_DIRTY_FILES_PRESENT", f"Beklenmeyen dirty count: {len(dirty_unexpected)}")

    if dirty_review:
        add("WARN", "ACTIVE_CONTROL_FILES_STILL_MODIFIED", "4 ACTIVE_* control dosyası hâlâ modified; restore mı commit mi kararı gerekiyor.")
    else:
        add("OK", "ACTIVE_CONTROL_FILES_NOT_DIRTY", "ACTIVE_* control dosyaları dirty değil.")

    fail_count = sum(1 for f in findings if f["level"] == "FAIL")
    warn_count = sum(1 for f in findings if f["level"] == "WARN")

    if fail_count:
        decision = "FAIL_REPO_CLEANUP_POST_APPLY_AUDIT_BLOCKED"
        next_step = "REVIEW_REPO_CLEANUP_POST_APPLY_FAILURE"
    elif warn_count:
        decision = "WARN_REPO_CLEANUP_SAFE_1_DONE_ACTIVE_CONTROL_REVIEW_REQUIRED"
        next_step = "ACTIVE_CONTROL_FILES_REVIEW_RESTORE_OR_SEAL"
    else:
        decision = "OK_REPO_CLEANUP_SAFE_1_POST_APPLY_CLEAN"
        next_step = "HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": now_iso(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "readonly_audit": True,
            "delete_files": False,
            "move_files": False,
            "archive_files": False,
            "restore_files": False,
            "commit_files": False,
            "db_write": False,
            "systemd_change": False,
            "repo_artifact_write": True,
        },
        "apply_artifact": {
            "path": str(APPLY_JSON),
            "read_error": apply_err,
            "decision": apply_obj.get("decision") if isinstance(apply_obj, dict) else None,
            "archive_target": archive_target,
        },
        "git_head": git_head,
        "git_status": git_status,
        "cache_leftovers": cache_leftovers,
        "phase_source_exists": phase_source_exists,
        "archive_target_exists": archive_target_exists,
        "remaining_dirty_review_files": dirty_review,
        "unexpected_dirty_files": dirty_unexpected,
        "active_control_file_states": [file_state(p) for p in sorted(EXPECTED_DIRTY_REVIEW)],
        "findings": findings,
        "summary": {
            "cache_leftover_count": len(cache_leftovers),
            "phase_source_exists": phase_source_exists,
            "archive_target_exists": archive_target_exists,
            "remaining_dirty_review_count": len(dirty_review),
            "unexpected_dirty_count": len(dirty_unexpected),
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_md(result))

    print("OK_REPO_CLEANUP_POST_APPLY_AUDIT_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + rel(OUT_JSON))
    print("REPORT=" + rel(OUT_MD))
    print("CACHE_LEFTOVER_COUNT=" + str(len(cache_leftovers)))
    print("PHASE_SOURCE_EXISTS=" + str(phase_source_exists))
    print("ARCHIVE_TARGET_EXISTS=" + str(archive_target_exists))
    print("REMAINING_DIRTY_REVIEW_COUNT=" + str(len(dirty_review)))
    print("UNEXPECTED_DIRTY_COUNT=" + str(len(dirty_unexpected)))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
