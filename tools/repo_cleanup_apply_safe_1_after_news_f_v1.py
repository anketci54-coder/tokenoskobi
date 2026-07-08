#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import shutil
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "REPO_CLEANUP_APPLY_SAFE_1_AFTER_NEWS_F"

OUT_JSON = ROOT / "data/control/repo_cleanup_apply_safe_1_after_news_f_v1.json"
OUT_MD = ROOT / "reports/LATEST_REPO_CLEANUP_APPLY_SAFE_1_AFTER_NEWS_F.md"

EXTERNAL_ARCHIVE_ROOT = Path("/root/tokenoskobi_external_archive")
PHASE_DIR = ROOT / "_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096"

PROTECTED_PREFIXES = [
    ".git/",
    "data/tokenoskobi_clean_v1.sqlite",
    "PROJECT_BOOT.json",
    "PROJECT_RUNTIME.json",
    "PROJECT_MASTER_STATE.md",
    "PROJECT_HANDOFF.md",
    "docs/",
    "reports/",
    "data/control/",
    "tools/",
    "runtime/",
    "core/",
]

CACHE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CACHE_FILE_SUFFIXES = {".pyc", ".pyo"}
CACHE_FILE_NAMES = {".DS_Store"}


def now():
    return datetime.now(timezone.utc)


def iso_now():
    return now().isoformat()


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def run_cmd(args, timeout=60):
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


def sha256_file(path, max_bytes=2_000_000):
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


def file_info(path):
    try:
        st = path.stat()
        return {
            "path": rel(path),
            "absolute_path": str(path),
            "exists": True,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "size_bytes": st.st_size if path.is_file() else None,
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
            "sha256": sha256_file(path) if path.is_file() else None,
        }
    except Exception as e:
        return {
            "path": rel(path),
            "absolute_path": str(path),
            "exists": False,
            "error": type(e).__name__ + ":" + str(e)[:300],
        }


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


def is_under_git(path):
    try:
        path.relative_to(ROOT / ".git")
        return True
    except Exception:
        return False


def should_delete_cache_path(path):
    if is_under_git(path):
        return False
    name = path.name
    if path.is_dir() and name in CACHE_DIR_NAMES:
        return True
    if path.is_file() and name in CACHE_FILE_NAMES:
        return True
    if path.is_file() and path.suffix in CACHE_FILE_SUFFIXES:
        return True
    return False


def collect_cache_targets():
    targets = []
    for p in ROOT.rglob("*"):
        if should_delete_cache_path(p):
            targets.append(p)
    targets.sort(key=lambda x: len(x.parts), reverse=True)
    dedup = []
    seen = set()
    for p in targets:
        rp = str(p)
        if rp in seen:
            continue
        if any(str(p).startswith(str(parent) + "/") for parent in dedup if parent.is_dir()):
            continue
        seen.add(rp)
        dedup.append(p)
    return dedup


def remove_path(path):
    before = file_info(path)
    try:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
        return {"action": "DELETE_CACHE", "before": before, "after_exists": path.exists(), "ok": True, "error": None}
    except Exception as e:
        return {"action": "DELETE_CACHE", "before": before, "after_exists": path.exists(), "ok": False, "error": type(e).__name__ + ":" + str(e)[:400]}


def archive_untracked_phase_dir():
    if not PHASE_DIR.exists():
        return {
            "action": "ARCHIVE_EXTERNAL_PHASE_DIR",
            "source": str(PHASE_DIR),
            "ok": True,
            "skipped": True,
            "reason": "source_missing",
        }

    ts = now().strftime("%Y%m%dT%H%M%SZ")
    target_root = EXTERNAL_ARCHIVE_ROOT / ("repo_cleanup_after_news_f_" + ts)
    target_root.mkdir(parents=True, exist_ok=True)
    target = target_root / PHASE_DIR.name

    before = file_info(PHASE_DIR)

    try:
        shutil.move(str(PHASE_DIR), str(target))
        return {
            "action": "ARCHIVE_EXTERNAL_PHASE_DIR",
            "source": str(PHASE_DIR),
            "target": str(target),
            "before": before,
            "target_exists": target.exists(),
            "ok": True,
            "skipped": False,
            "error": None,
        }
    except Exception as e:
        return {
            "action": "ARCHIVE_EXTERNAL_PHASE_DIR",
            "source": str(PHASE_DIR),
            "target": str(target),
            "before": before,
            "target_exists": target.exists(),
            "ok": False,
            "skipped": False,
            "error": type(e).__name__ + ":" + str(e)[:400],
        }


def build_md(result):
    lines = []
    lines.append("# Repo Cleanup Apply Safe 1 After NEWS-F")
    lines.append("")
    lines.append(f"- stage: `{STAGE}`")
    lines.append(f"- generated_at_utc: `{result['generated_at_utc']}`")
    lines.append(f"- decision: `{result['decision']}`")
    lines.append(f"- next_step: `{result['next_step']}`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- delete: `__pycache__`, `*.pyc`, generated cache files")
    lines.append("- external archive: `_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096`")
    lines.append("- untouched: `backups`, `logs`, `*.bak`, `*.log`, DB, docs, runtime, systemd")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for k, v in result["summary"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Archived")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(result["archive_action"], ensure_ascii=False, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("## Deleted Cache Targets")
    lines.append("")
    for item in result["delete_actions"][:200]:
        lines.append(f"- `{item.get('before', {}).get('path')}` ok=`{item.get('ok')}` error=`{item.get('error')}`")
    lines.append("")
    lines.append("## Git Status After")
    lines.append("")
    lines.append("```text")
    lines.append(result["git_status_after"].get("stdout", ""))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    git_before = run_cmd(["git", "status", "--short"])
    head_before = run_cmd(["git", "rev-parse", "HEAD"]).get("stdout")

    cache_targets = collect_cache_targets()
    delete_actions = []
    for p in cache_targets:
        delete_actions.append(remove_path(p))

    archive_action = archive_untracked_phase_dir()

    git_after_cleanup = run_cmd(["git", "status", "--short"])

    failed_delete = [x for x in delete_actions if not x.get("ok")]
    archive_failed = not archive_action.get("ok")

    fail_count = len(failed_delete) + (1 if archive_failed else 0)
    warn_count = 0

    if fail_count:
        decision = "FAIL_REPO_CLEANUP_APPLY_SAFE_1_REVIEW_REQUIRED"
        next_step = "REVIEW_REPO_CLEANUP_SAFE_1_FAILURE"
    else:
        decision = "OK_REPO_CLEANUP_APPLY_SAFE_1_DONE"
        next_step = "REPO_CLEANUP_POST_APPLY_AUDIT_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": iso_now(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "delete_generated_cache_only": True,
            "archive_untracked_phase_dir_external": True,
            "touch_backups": False,
            "touch_logs": False,
            "touch_bak_files": False,
            "touch_db": False,
            "touch_runtime": False,
            "touch_systemd": False,
            "repo_artifact_write": True,
        },
        "head_before": head_before,
        "git_status_before": git_before,
        "delete_actions": delete_actions,
        "archive_action": archive_action,
        "git_status_after": git_after_cleanup,
        "summary": {
            "cache_target_count": len(cache_targets),
            "cache_deleted_ok_count": sum(1 for x in delete_actions if x.get("ok")),
            "cache_delete_fail_count": len(failed_delete),
            "phase_dir_archived": bool(archive_action.get("ok") and not archive_action.get("skipped")),
            "phase_dir_archive_target": archive_action.get("target"),
            "archive_failed": archive_failed,
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_md(result))

    print("OK_REPO_CLEANUP_APPLY_SAFE_1_AFTER_NEWS_F_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + rel(OUT_JSON))
    print("REPORT=" + rel(OUT_MD))
    print("CACHE_TARGET_COUNT=" + str(result["summary"]["cache_target_count"]))
    print("CACHE_DELETED_OK_COUNT=" + str(result["summary"]["cache_deleted_ok_count"]))
    print("PHASE_DIR_ARCHIVED=" + str(result["summary"]["phase_dir_archived"]))
    print("PHASE_DIR_ARCHIVE_TARGET=" + str(result["summary"]["phase_dir_archive_target"]))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)

    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
