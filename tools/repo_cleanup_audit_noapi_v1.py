#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import hashlib
import fnmatch

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "REPO_CLEANUP_AUDIT_NOAPI_AFTER_NEWS_F"

OUT_JSON = ROOT / "data/control/repo_cleanup_audit_noapi_after_news_f_v1.json"
OUT_MD = ROOT / "reports/LATEST_REPO_CLEANUP_AUDIT_NOAPI_AFTER_NEWS_F.md"

PROTECTED_EXACT = {
    "PROJECT_BOOT.json",
    "PROJECT_RUNTIME.json",
    "PROJECT_MASTER_STATE.md",
    "PROJECT_HANDOFF.md",
    "docs/CENGIZHAN_INTELLIGENCE_DOCTRINE.md",
    "data/tokenoskobi_clean_v1.sqlite",
    "data/control/news_f_final_operational_seal_with_known_warnings_v1.json",
    "tools/news_f_final_operational_seal_with_known_warnings_v1.py",
}

PROTECTED_PREFIXES = [
    ".git/",
    "docs/canonical/",
    "docs/CANONICAL",
    "data/control/news_",
    "reports/LATEST_NEWS_",
    "tools/news_",
]

ARCHIVE_CANDIDATE_PREFIXES = [
    "_phase",
    "phase",
    "tmp",
    "temp",
    "scratch",
    "old",
    "backup",
    "backups",
]

SAFE_DELETE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".DS_Store",
    "*.tmp",
    "*.temp",
    "*.swp",
    "*.swo",
    "*~",
]

REVIEW_PATTERNS = [
    "*.bak",
    "*.backup",
    "*.old",
    "*.orig",
    "*.rej",
    "*.log",
    "*.out",
    "*.err",
    "*.sqlite-wal",
    "*.sqlite-shm",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def run_cmd(args, timeout=40):
    try:
        p = subprocess.run(args, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"cmd": args, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as e:
        return {"cmd": args, "rc": None, "stdout": "", "stderr": type(e).__name__ + ":" + str(e)[:300]}


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
            "exists": True,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "size_bytes": st.st_size if path.is_file() else None,
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
            "sha256": sha256_file(path) if path.is_file() else None,
        }
    except Exception as e:
        return {"path": rel(path), "exists": False, "error": type(e).__name__ + ":" + str(e)[:200]}


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


def split_lines(s):
    return [x for x in (s or "").splitlines() if x.strip()]


def parse_git_status_porcelain(text):
    rows = []
    for line in split_lines(text):
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            old, new = path.split(" -> ", 1)
            path = new
        rows.append({"status": status, "path": path})
    return rows


def is_protected(path):
    if path in PROTECTED_EXACT:
        return True
    for p in PROTECTED_PREFIXES:
        if path.startswith(p):
            return True
    return False


def match_any(path, patterns):
    base = path.split("/")[-1]
    parts = path.split("/")
    for pat in patterns:
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(base, pat) or pat in parts:
            return pat
    return None


def top_segment(path):
    return path.split("/", 1)[0]


def classify_path(path, git_state, exists=True, is_dir=False):
    if is_protected(path):
        return {
            "class": "KEEP_PROTECTED",
            "reason": "protected current project/news seal artifact",
            "recommended_action": "KEEP",
        }

    safe_pat = match_any(path, SAFE_DELETE_PATTERNS)
    if safe_pat:
        return {
            "class": "SAFE_DELETE_CANDIDATE",
            "reason": "matches safe generated/cache pattern: " + safe_pat,
            "recommended_action": "DELETE_AFTER_APPROVAL",
        }

    review_pat = match_any(path, REVIEW_PATTERNS)
    if review_pat:
        return {
            "class": "REVIEW_CANDIDATE",
            "reason": "matches review pattern: " + review_pat,
            "recommended_action": "REVIEW_THEN_ARCHIVE_OR_DELETE",
        }

    top = top_segment(path).lower()
    if any(top.startswith(x) for x in ARCHIVE_CANDIDATE_PREFIXES):
        return {
            "class": "ARCHIVE_CANDIDATE",
            "reason": "top-level temporary/phase/backup style directory or file",
            "recommended_action": "ARCHIVE_AFTER_APPROVAL",
        }

    if git_state == "untracked" and path.startswith("_"):
        return {
            "class": "ARCHIVE_CANDIDATE",
            "reason": "untracked underscore-prefixed working artifact",
            "recommended_action": "ARCHIVE_AFTER_APPROVAL",
        }

    if git_state == "modified":
        return {
            "class": "REVIEW_CANDIDATE",
            "reason": "tracked file modified in working tree",
            "recommended_action": "REVIEW_BEFORE_KEEP_OR_RESTORE",
        }

    if git_state == "untracked":
        return {
            "class": "REVIEW_CANDIDATE",
            "reason": "untracked file/directory not automatically safe",
            "recommended_action": "REVIEW_BEFORE_ARCHIVE",
        }

    return {
        "class": "KEEP_OR_UNKNOWN",
        "reason": "no cleanup rule matched",
        "recommended_action": "KEEP",
    }


def list_top_level_dirs():
    out = []
    for p in sorted(ROOT.iterdir(), key=lambda x: x.name.lower()):
        if p.name == ".git":
            continue
        if p.is_dir():
            info = file_info(p)
            info["child_count"] = sum(1 for _ in p.iterdir()) if p.exists() else None
            cls = classify_path(rel(p), "tracked_or_unknown", is_dir=True)
            info.update(cls)
            out.append(info)
    return out


def collect_cache_files():
    out = []
    for p in ROOT.rglob("*"):
        rp = rel(p)
        if rp.startswith(".git/"):
            continue
        if match_any(rp, SAFE_DELETE_PATTERNS) or match_any(rp, REVIEW_PATTERNS):
            info = file_info(p)
            cls = classify_path(rp, "tracked_or_unknown", exists=p.exists(), is_dir=p.is_dir())
            info.update(cls)
            out.append(info)
    return out[:500]


def du_summary():
    r = run_cmd(["bash", "-lc", "du -sh ./* 2>/dev/null | sort -h | tail -80"], timeout=60)
    rows = []
    for line in split_lines(r.get("stdout")):
        parts = line.split(None, 1)
        if len(parts) == 2:
            rows.append({"size": parts[0], "path": parts[1].replace("./", "", 1)})
    return {"cmd": r, "top": rows}


def build_report(result):
    lines = []
    lines.append("# Repo Cleanup Audit NOAPI After NEWS-F")
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
    lines.append("## Git Dirty Items")
    lines.append("")
    lines.append("| State | Path | Class | Recommendation |")
    lines.append("|---|---|---|---|")
    for item in result["git_dirty_classified"]:
        lines.append(f"| {item.get('git_state')} | {item.get('path')} | {item.get('class')} | {item.get('recommended_action')} |")
    lines.append("")
    lines.append("## Safe Delete Candidates")
    lines.append("")
    for item in result["safe_delete_candidates"][:100]:
        lines.append(f"- `{item.get('path')}` — {item.get('reason')}")
    lines.append("")
    lines.append("## Archive Candidates")
    lines.append("")
    for item in result["archive_candidates"][:100]:
        lines.append(f"- `{item.get('path')}` — {item.get('reason')}")
    lines.append("")
    lines.append("## Review Candidates")
    lines.append("")
    for item in result["review_candidates"][:150]:
        lines.append(f"- `{item.get('path')}` — {item.get('reason')} — {item.get('recommended_action')}")
    lines.append("")
    lines.append("## Top-Level Directories")
    lines.append("")
    lines.append("| Path | Class | Children | Recommendation |")
    lines.append("|---|---|---:|---|")
    for item in result["top_level_dirs"]:
        lines.append(f"| {item.get('path')} | {item.get('class')} | {item.get('child_count')} | {item.get('recommended_action')} |")
    lines.append("")
    lines.append("## Disk Usage Top")
    lines.append("")
    lines.append("```text")
    for item in result["du_summary"].get("top", []):
        lines.append(f"{item.get('size')}\t{item.get('path')}")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    git_head = run_cmd(["git", "rev-parse", "HEAD"]).get("stdout")
    git_branch = run_cmd(["git", "branch", "--show-current"]).get("stdout")
    status_raw = run_cmd(["git", "status", "--porcelain=v1"])
    untracked_raw = run_cmd(["git", "ls-files", "--others", "--exclude-standard"])
    modified_raw = run_cmd(["git", "ls-files", "--modified"])
    deleted_raw = run_cmd(["git", "ls-files", "--deleted"])

    status_rows = parse_git_status_porcelain(status_raw.get("stdout"))
    untracked = set(split_lines(untracked_raw.get("stdout")))
    modified = set(split_lines(modified_raw.get("stdout")))
    deleted = set(split_lines(deleted_raw.get("stdout")))

    dirty_classified = []

    status_paths = set()
    for row in status_rows:
        p = row["path"]
        status_paths.add(p)
        if p in untracked or row["status"].strip() == "??":
            state = "untracked"
        elif p in modified:
            state = "modified"
        elif p in deleted:
            state = "deleted"
        else:
            state = "dirty"
        path_obj = ROOT / p
        info = file_info(path_obj) if path_obj.exists() else {"path": p, "exists": False}
        cls = classify_path(p, state, exists=path_obj.exists(), is_dir=path_obj.is_dir())
        item = {"git_status": row["status"], "git_state": state}
        item.update(info)
        item.update(cls)
        dirty_classified.append(item)

    top_dirs = list_top_level_dirs()
    cache_candidates = collect_cache_files()

    combined = dirty_classified + cache_candidates + top_dirs

    seen = set()
    deduped = []
    for item in combined:
        p = item.get("path")
        key = (p, item.get("class"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    safe_delete = [x for x in deduped if x.get("class") == "SAFE_DELETE_CANDIDATE"]
    archive = [x for x in deduped if x.get("class") == "ARCHIVE_CANDIDATE"]
    review = [x for x in deduped if x.get("class") == "REVIEW_CANDIDATE"]
    protected = [x for x in deduped if x.get("class") == "KEEP_PROTECTED"]

    fail_count = 0
    warn_count = 0

    if dirty_classified:
        warn_count += 1
        decision = "WARN_REPO_CLEANUP_CANDIDATES_FOUND_REVIEW_REQUIRED"
        next_step = "REPO_CLEANUP_ARCHIVE_APPLY_REQUIRES_APPROVAL"
    elif safe_delete or archive or review:
        warn_count += 1
        decision = "WARN_REPO_CLEANUP_CANDIDATES_FOUND_REVIEW_REQUIRED"
        next_step = "REPO_CLEANUP_ARCHIVE_APPLY_REQUIRES_APPROVAL"
    else:
        decision = "OK_REPO_CLEANUP_AUDIT_NO_CANDIDATES"
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
            "db_write": False,
            "systemd_change": False,
            "repo_artifact_write": True,
        },
        "git": {
            "head": git_head,
            "branch": git_branch,
            "status_raw": status_raw,
            "untracked_raw": untracked_raw,
            "modified_raw": modified_raw,
            "deleted_raw": deleted_raw,
        },
        "git_dirty_classified": dirty_classified,
        "safe_delete_candidates": safe_delete,
        "archive_candidates": archive,
        "review_candidates": review,
        "protected_items_seen": protected,
        "top_level_dirs": top_dirs,
        "cache_and_review_pattern_files": cache_candidates,
        "du_summary": du_summary(),
        "summary": {
            "dirty_item_count": len(dirty_classified),
            "safe_delete_candidate_count": len(safe_delete),
            "archive_candidate_count": len(archive),
            "review_candidate_count": len(review),
            "protected_seen_count": len(protected),
            "top_level_dir_count": len(top_dirs),
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_report(result))

    print("OK_REPO_CLEANUP_AUDIT_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + rel(OUT_JSON))
    print("REPORT=" + rel(OUT_MD))
    print("DIRTY_ITEM_COUNT=" + str(result["summary"]["dirty_item_count"]))
    print("SAFE_DELETE_CANDIDATE_COUNT=" + str(result["summary"]["safe_delete_candidate_count"]))
    print("ARCHIVE_CANDIDATE_COUNT=" + str(result["summary"]["archive_candidate_count"]))
    print("REVIEW_CANDIDATE_COUNT=" + str(result["summary"]["review_candidate_count"]))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
