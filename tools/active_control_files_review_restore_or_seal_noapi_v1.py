#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "ACTIVE_CONTROL_FILES_REVIEW_RESTORE_OR_SEAL_NOAPI"

OUT_JSON = ROOT / "data/control/active_control_files_review_restore_or_seal_noapi_v1.json"
OUT_MD = ROOT / "reports/LATEST_ACTIVE_CONTROL_FILES_REVIEW_RESTORE_OR_SEAL_NOAPI.md"

TARGETS = [
    "data/control/ACTIVE_CORE_RANKING.json",
    "data/control/ACTIVE_EXECUTION_GRAPH.json",
    "data/control/MINIMAL_ACTIVE_CORE_MANIFEST.json",
    "data/control/USED_BY_RUNTIME_INDEX.json",
]

POST_AUDIT = ROOT / "data/control/repo_cleanup_post_apply_audit_noapi_after_safe_1_v1.json"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


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


def read_json_file(path):
    try:
        txt = path.read_text(encoding="utf-8")
        return json.loads(txt), txt, None
    except Exception as e:
        return None, "", type(e).__name__ + ":" + str(e)[:400]


def read_head_file(path_str):
    r = run_cmd(["git", "show", "HEAD:" + path_str])
    if r["rc"] != 0:
        return None, "", r["stderr"] or "git show failed"
    txt = r["stdout"]
    try:
        return json.loads(txt), txt, None
    except Exception as e:
        return None, txt, type(e).__name__ + ":" + str(e)[:400]


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


def summarize_obj(obj):
    if not isinstance(obj, dict):
        return {"type": type(obj).__name__}
    out = {
        "type": "dict",
        "top_keys": sorted(list(obj.keys())),
        "top_key_count": len(obj.keys()),
    }
    for k, v in obj.items():
        if isinstance(v, list):
            out[k + "_len"] = len(v)
        elif isinstance(v, dict):
            out[k + "_keys"] = sorted(list(v.keys()))[:80]
            out[k + "_key_count"] = len(v.keys())
        elif isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
    return out


def compare_summary(a, b):
    if not isinstance(a, dict) or not isinstance(b, dict):
        return {"kind": "non_dict_or_parse_error"}
    ak = set(a.keys())
    bk = set(b.keys())
    changed_scalars = {}
    common = sorted(ak & bk)
    for k in common:
        av = a.get(k)
        bv = b.get(k)
        if isinstance(av, (str, int, float, bool, type(None))) and isinstance(bv, (str, int, float, bool, type(None))) and av != bv:
            changed_scalars[k] = {"head": av, "working": bv}
    len_changes = {}
    for k in common:
        av = a.get(k)
        bv = b.get(k)
        if isinstance(av, list) and isinstance(bv, list) and len(av) != len(bv):
            len_changes[k] = {"head_len": len(av), "working_len": len(bv)}
        if isinstance(av, dict) and isinstance(bv, dict) and len(av.keys()) != len(bv.keys()):
            len_changes[k] = {"head_key_count": len(av.keys()), "working_key_count": len(bv.keys())}
    return {
        "added_top_keys": sorted(bk - ak),
        "removed_top_keys": sorted(ak - bk),
        "changed_scalar_top_keys": changed_scalars,
        "changed_container_lengths": len_changes,
    }


def diff_stat(path_str):
    return {
        "numstat": run_cmd(["git", "diff", "--numstat", "--", path_str]),
        "stat": run_cmd(["git", "diff", "--stat", "--", path_str]),
        "name_status": run_cmd(["git", "diff", "--name-status", "--", path_str]),
        "patch_head_120": run_cmd(["bash", "-lc", "git diff -- '" + path_str.replace("'", "'\"'\"'") + "' | sed -n '1,160p'"]),
    }


def classify_file(review):
    if review["working_sha256"] == review["head_sha256"]:
        return "NO_CHANGE", "HEAD ile aynı."

    if review["parse_errors"]["head"] or review["parse_errors"]["working"]:
        return "REVIEW_REQUIRED", "JSON parse hatası veya HEAD okuma hatası var."

    cmp = review["semantic_compare"]
    changed_scalars = set((cmp.get("changed_scalar_top_keys") or {}).keys())
    added = set(cmp.get("added_top_keys") or [])
    removed = set(cmp.get("removed_top_keys") or [])
    len_changes = cmp.get("changed_container_lengths") or {}

    harmless = {"generated_at_utc", "updated_at_utc", "created_at_utc", "head", "commit", "current_head", "timestamp", "mtime_utc"}

    if not added and not removed and not len_changes and changed_scalars and changed_scalars.issubset(harmless):
        return "RESTORE_CANDIDATE_TIMESTAMP_ONLY", "Sadece timestamp/head benzeri alanlar değişmiş görünüyor."

    return "MEANINGFUL_CHANGE_REVIEW", "Top-level key/container veya anlamlı alan değişikliği var; restore/commit kararı gerekiyor."


def build_md(result):
    lines = []
    lines.append("# Active Control Files Review Restore or Seal NOAPI")
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
    lines.append("## File Reviews")
    lines.append("")
    for r in result["file_reviews"]:
        lines.append(f"### {r['path']}")
        lines.append("")
        lines.append(f"- classification: `{r['classification']}`")
        lines.append(f"- reason: {r['classification_reason']}")
        lines.append(f"- head_sha256: `{r['head_sha256']}`")
        lines.append(f"- working_sha256: `{r['working_sha256']}`")
        lines.append(f"- parse_head_error: `{r['parse_errors']['head']}`")
        lines.append(f"- parse_working_error: `{r['parse_errors']['working']}`")
        lines.append("")
        lines.append("Top-level semantic compare:")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(r["semantic_compare"], ensure_ascii=False, indent=2, sort_keys=True)[:4000])
        lines.append("```")
        lines.append("")
        lines.append("Diff stat:")
        lines.append("")
        lines.append("```text")
        lines.append((r["diff"]["stat"].get("stdout") or "")[:2000])
        lines.append("```")
        lines.append("")
    lines.append("## Git Status")
    lines.append("")
    lines.append("```text")
    lines.append(result["git_status"].get("stdout", ""))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    git_head = run_cmd(["git", "rev-parse", "HEAD"]).get("stdout")
    git_status = run_cmd(["git", "status", "--short"])

    post_obj, _, post_err = read_json_file(POST_AUDIT)

    file_reviews = []
    for path_str in TARGETS:
        path = ROOT / path_str
        working_obj, working_txt, working_err = read_json_file(path)
        head_obj, head_txt, head_err = read_head_file(path_str)

        review = {
            "path": path_str,
            "exists_working": path.exists(),
            "head_sha256": sha256_text(head_txt) if head_txt else None,
            "working_sha256": sha256_file(path),
            "parse_errors": {
                "head": head_err,
                "working": working_err,
            },
            "head_summary": summarize_obj(head_obj),
            "working_summary": summarize_obj(working_obj),
            "semantic_compare": compare_summary(head_obj, working_obj),
            "diff": diff_stat(path_str),
        }
        cls, reason = classify_file(review)
        review["classification"] = cls
        review["classification_reason"] = reason
        file_reviews.append(review)

    meaningful = [r for r in file_reviews if r["classification"] == "MEANINGFUL_CHANGE_REVIEW"]
    timestamp_only = [r for r in file_reviews if r["classification"] == "RESTORE_CANDIDATE_TIMESTAMP_ONLY"]
    parse_bad = [r for r in file_reviews if r["classification"] == "REVIEW_REQUIRED"]
    no_change = [r for r in file_reviews if r["classification"] == "NO_CHANGE"]

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    if post_err:
        add("WARN", "POST_APPLY_AUDIT_REF_NOT_READ", f"Post apply audit ref okunamadı: {post_err}")
    else:
        add("OK", "POST_APPLY_AUDIT_REF_READ", "Cleanup post-apply audit referansı okundu.")

    if parse_bad:
        add("FAIL", "ACTIVE_CONTROL_PARSE_OR_HEAD_READ_ERROR", f"Parse/head error count: {len(parse_bad)}")
    else:
        add("OK", "ACTIVE_CONTROL_JSON_PARSE_OK", "4 ACTIVE control JSON parse OK.")

    if meaningful:
        add("WARN", "MEANINGFUL_ACTIVE_CONTROL_CHANGES_FOUND", f"Meaningful review count: {len(meaningful)}")
    else:
        add("OK", "NO_MEANINGFUL_ACTIVE_CONTROL_CHANGES", "Meaningful ACTIVE control change görünmedi.")

    if timestamp_only:
        add("WARN", "TIMESTAMP_ONLY_RESTORE_CANDIDATES_FOUND", f"Timestamp-only restore candidate count: {len(timestamp_only)}")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if fail_count:
        decision = "FAIL_ACTIVE_CONTROL_FILES_REVIEW_BLOCKED"
        next_step = "REVIEW_ACTIVE_CONTROL_PARSE_FAILURE"
    elif meaningful:
        decision = "WARN_ACTIVE_CONTROL_FILES_MEANINGFUL_CHANGE_REVIEW_REQUIRED"
        next_step = "ACTIVE_CONTROL_FILES_SEAL_OR_RESTORE_DECISION_REQUIRED"
    elif timestamp_only:
        decision = "WARN_ACTIVE_CONTROL_FILES_RESTORE_CANDIDATE"
        next_step = "ACTIVE_CONTROL_FILES_RESTORE_APPLY_REQUIRES_APPROVAL"
    else:
        decision = "OK_ACTIVE_CONTROL_FILES_NO_RESTORE_NEEDED"
        next_step = "HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI"

    result = {
        "stage": STAGE,
        "generated_at_utc": now_iso(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "readonly_review": True,
            "restore_files": False,
            "commit_active_files": False,
            "delete_files": False,
            "move_files": False,
            "db_write": False,
            "systemd_change": False,
            "repo_artifact_write": True,
        },
        "git_head": git_head,
        "git_status": git_status,
        "post_apply_audit_ref": {
            "path": str(POST_AUDIT),
            "read_error": post_err,
            "decision": post_obj.get("decision") if isinstance(post_obj, dict) else None,
            "next_step": post_obj.get("next_step") if isinstance(post_obj, dict) else None,
        },
        "file_reviews": file_reviews,
        "findings": findings,
        "summary": {
            "target_count": len(TARGETS),
            "meaningful_change_count": len(meaningful),
            "timestamp_only_count": len(timestamp_only),
            "parse_bad_count": len(parse_bad),
            "no_change_count": len(no_change),
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
    }

    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_md(result))

    print("OK_ACTIVE_CONTROL_FILES_REVIEW_RESTORE_OR_SEAL_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + rel(OUT_JSON))
    print("REPORT=" + rel(OUT_MD))
    print("MEANINGFUL_CHANGE_COUNT=" + str(len(meaningful)))
    print("TIMESTAMP_ONLY_COUNT=" + str(len(timestamp_only)))
    print("PARSE_BAD_COUNT=" + str(len(parse_bad)))
    print("NO_CHANGE_COUNT=" + str(len(no_change)))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
