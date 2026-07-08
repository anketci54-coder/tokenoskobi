#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "NEWS_E_REVIEW_PROMPT_AND_SEAL_PREP_NOAPI"

OUT_JSON = ROOT / "data/control/news_e_review_prompt_and_seal_prep_noapi_v1.json"
OUT_MD = ROOT / "reports/LATEST_NEWS_E_REVIEW_PROMPT_AND_SEAL_PREP_NOAPI.md"
OUT_CODEX = ROOT / "reports/NEWS_E_CODEX_REVIEW_PROMPT.md"
OUT_GEMINI = ROOT / "reports/NEWS_E_GEMINI_RED_TEAM_PROMPT.md"

REFS = {
    "news_a": ROOT / "data/control/news_a_final_pre_replay_truth_snapshot_noapi_v1.json",
    "news_b": ROOT / "data/control/news_b_runner_timer_journal_argv_audit_noapi_v1.json",
    "news_b_fix1": ROOT / "data/control/news_b_fix_1_systemd_stdout_stderr_path_targeted_apply_v1.json",
    "news_b_fix1_post": ROOT / "data/control/news_b_fix_1_post_apply_audit_noapi_v1.json",
    "news_b_fix2": ROOT / "data/control/news_b_fix_2_timer_activation_targeted_apply_v1.json",
    "news_b_fix2_post": ROOT / "data/control/news_b_fix_2_post_activation_audit_noapi_v1.json",
    "news_c": ROOT / "data/control/news_c_downstream_checksum_fingerprint_noapi_v1.json",
    "news_d": ROOT / "data/control/news_d_panel_readmodel_freshness_noapi_v1.json",
}

EXPECTED_SEQUENCE = [
    "NEWS_A_FINAL_PRE_REPLAY_TRUTH_SNAPSHOT_NOAPI",
    "NEWS_B_RUNNER_TIMER_JOURNAL_ARGV_AUDIT_NOAPI",
    "NEWS_B_FIX_1_SYSTEMD_STDOUT_STDERR_PATH_TARGETED_APPLY",
    "NEWS_B_FIX_1_POST_APPLY_AUDIT_NOAPI",
    "NEWS_B_FIX_2_TIMER_ACTIVATION_TARGETED_APPLY",
    "NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_NOAPI",
    "NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_NOAPI",
    "NEWS_D_PANEL_READMODEL_FRESHNESS_NOAPI",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def run_cmd(args, timeout=25):
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
            "stderr": type(e).__name__ + ":" + str(e)[:300],
        }


def read_json(path):
    if not path.exists():
        return None, "MISSING"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:400]


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


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compact_ref(name, path):
    obj, err = read_json(path)
    summary = {
        "name": name,
        "path": str(path),
        "read_error": err,
        "stage": obj.get("stage") if isinstance(obj, dict) else None,
        "decision": obj.get("decision") if isinstance(obj, dict) else None,
        "next_step": obj.get("next_step") if isinstance(obj, dict) else None,
        "generated_at_utc": obj.get("generated_at_utc") if isinstance(obj, dict) else None,
        "summary": obj.get("summary") if isinstance(obj, dict) else None,
        "findings": obj.get("findings") if isinstance(obj, dict) else None,
        "authority": obj.get("authority") if isinstance(obj, dict) else None,
    }
    return summary, obj


def get_count(summary, key):
    if not isinstance(summary, dict):
        return None
    return summary.get(key)


def decision_level(decision):
    s = str(decision or "")
    if s.startswith("FAIL_"):
        return "FAIL"
    if s.startswith("WARN_"):
        return "WARN"
    if s.startswith("OK_"):
        return "OK"
    return "UNKNOWN"


def build_known_warnings(refs):
    warnings = []
    d = refs.get("news_d", {})
    dsum = d.get("summary") or {}
    dfind = d.get("findings") or []
    for f in dfind:
        if f.get("level") == "WARN":
            warnings.append({
                "source": "NEWS-D",
                "code": f.get("code"),
                "message": f.get("message"),
            })
    if dsum.get("raw_newer_than_downstream") is True:
        warnings.append({
            "source": "NEWS-D",
            "code": "RAW_NEWER_THAN_DOWNSTREAM_CONFIRMED",
            "message": "Raw producer yeni haber alıyor; downstream 47/47/47 zinciri yeni raw haberleri henüz işlemiyor.",
        })
    if dsum.get("strong_panel_readmodel_count_matches") == 0:
        warnings.append({
            "source": "NEWS-D",
            "code": "PANEL_READMODEL_STRONG_COUNT_MATCH_ZERO",
            "message": "DB sayılarıyla güçlü panel/readmodel JSON count eşleşmesi bulunmadı.",
        })
    return warnings


def build_seal_matrix(refs):
    a = refs.get("news_a", {})
    b = refs.get("news_b", {})
    b1 = refs.get("news_b_fix1", {})
    b1p = refs.get("news_b_fix1_post", {})
    b2 = refs.get("news_b_fix2", {})
    b2p = refs.get("news_b_fix2_post", {})
    c = refs.get("news_c", {})
    d = refs.get("news_d", {})

    csum = c.get("summary") or {}
    dsum = d.get("summary") or {}

    return {
        "producer_resurrected": {
            "status": "OK" if decision_level(b2.get("decision")) == "OK" and decision_level(b2p.get("decision")) == "OK" else "REVIEW",
            "evidence": [
                b2.get("decision"),
                b2p.get("decision"),
                "timer_active=" + str(dsum.get("timer_active")),
                "timer_enabled=" + str(dsum.get("timer_enabled")),
            ],
        },
        "stdout_209_root_cause_closed": {
            "status": "OK" if decision_level(b1.get("decision")) == "OK" and decision_level(b1p.get("decision")) == "OK" else "REVIEW",
            "evidence": [
                "NEWS-B root cause: " + str(b.get("decision")),
                "Fix1: " + str(b1.get("decision")),
                "Fix1 post: " + str(b1p.get("decision")),
            ],
        },
        "downstream_47_chain_verified": {
            "status": "OK" if decision_level(c.get("decision")) == "OK" else "REVIEW",
            "evidence": [
                "raw=" + str(csum.get("raw_count")),
                "match=" + str(csum.get("match_count")),
                "signal=" + str(csum.get("signal_count")),
                "score=" + str(csum.get("score_count")),
                "match_signal_mismatch_total=" + str(csum.get("match_signal_mismatch_total")),
                "signal_score_mismatch_total=" + str(csum.get("signal_score_mismatch_total")),
                "raw_link_missing_total=" + str(csum.get("raw_link_missing_total")),
                "full_duplicate_group_total=" + str(csum.get("full_duplicate_group_total")),
                "canonical_duplicate_group_total=" + str(csum.get("canonical_duplicate_group_total")),
            ],
        },
        "trade_authority_absent": {
            "status": "OK" if csum.get("trade_signal_nonzero") == 0 and csum.get("paper_signal_nonzero") == 0 else "REVIEW",
            "evidence": [
                "trade_signal_nonzero=" + str(csum.get("trade_signal_nonzero")),
                "paper_signal_nonzero=" + str(csum.get("paper_signal_nonzero")),
            ],
        },
        "freshness_and_panel_known_issue": {
            "status": "WARN",
            "evidence": [
                d.get("decision"),
                "raw_count=" + str(dsum.get("raw_count")),
                "match_count=" + str(dsum.get("match_count")),
                "signal_count=" + str(dsum.get("signal_count")),
                "score_count=" + str(dsum.get("score_count")),
                "raw_newer_than_downstream=" + str(dsum.get("raw_newer_than_downstream")),
                "strong_panel_readmodel_count_matches=" + str(dsum.get("strong_panel_readmodel_count_matches")),
                "freshness_max_ts=" + str(dsum.get("freshness_max_ts")),
                "raw_max_ts=" + str(dsum.get("raw_max_ts")),
            ],
        },
        "cold_hot_doctrine_split": {
            "status": "OK",
            "evidence": [
                "20min timer is cold backfill/fallback only.",
                "HOT_INTELLIGENCE_INGRESS_GATEWAY is deferred until after NEWS-F seal.",
                "CENGIZHAN_INTELLIGENCE_DOCTRINE must be preserved as future architecture doctrine.",
            ],
        },
    }


def build_codex_prompt(result):
    lines = []
    lines.append("# Codex Review Prompt — NEWS Operational Seal Prep")
    lines.append("")
    lines.append("You are reviewing the Tokenoskobi NEWS recovery sequence. Do not propose a rewrite. Verify whether the current artifacts support an operational seal with known warnings.")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- Repository path: `/root/tokenoskobi_clean_v1`")
    lines.append("- Current stage: `NEWS_E_REVIEW_PROMPT_AND_SEAL_PREP_NOAPI`")
    lines.append("- Next intended stage: `NEWS_F_FINAL_OPERATIONAL_SEAL_WITH_KNOWN_WARNINGS`")
    lines.append("- Do not recommend live trading, paper trading, wallet/signing, or API expansion.")
    lines.append("- Do not convert the 20-minute timer into the final intelligence architecture.")
    lines.append("")
    lines.append("## Artifact Chain")
    lines.append("")
    for k, v in result["references"].items():
        lines.append(f"- `{k}`: `{v.get('decision')}` — `{v.get('path')}`")
    lines.append("")
    lines.append("## Seal Matrix")
    lines.append("")
    for k, v in result["seal_matrix"].items():
        lines.append(f"- `{k}`: `{v.get('status')}`")
        for e in v.get("evidence", []):
            lines.append(f"  - {e}")
    lines.append("")
    lines.append("## Known Warnings")
    lines.append("")
    for w in result["known_warnings"]:
        lines.append(f"- `{w.get('code')}`: {w.get('message')}")
    lines.append("")
    lines.append("## Review Questions")
    lines.append("")
    lines.append("1. Is the 209/STDOUT root cause adequately identified and closed?")
    lines.append("2. Is the timer active/enabled evidence sufficient for COLD NEWS producer operational status?")
    lines.append("3. Is the 47/47/47 downstream chain verified without broken references or duplicate rows?")
    lines.append("4. Are the NEWS-D warnings correctly classified as known issues rather than hidden failures?")
    lines.append("5. Is it safe to create NEWS-F as an operational seal with known warnings, without claiming panel/freshness fully clean?")
    lines.append("6. Confirm that HOT_INTELLIGENCE_INGRESS_GATEWAY should remain a post-NEWS-F architecture plan, not part of this seal.")
    lines.append("")
    lines.append("## Expected Output")
    lines.append("")
    lines.append("Return one of:")
    lines.append("")
    lines.append("- `OK_FOR_NEWS_F_SEAL_WITH_KNOWN_WARNINGS`")
    lines.append("- `WARN_REVIEW_BEFORE_NEWS_F`")
    lines.append("- `BLOCK_NEWS_F_SEAL`")
    lines.append("")
    lines.append("Include concrete artifact references and exact reasons.")
    lines.append("")
    return "\n".join(lines)


def build_gemini_prompt(result):
    lines = []
    lines.append("# Gemini Red Team Prompt — NEWS Seal + Cengizhan Doctrine Boundary")
    lines.append("")
    lines.append("Red Team task: evaluate whether Tokenoskobi can seal the current COLD NEWS recovery while explicitly preserving the Cengizhan/HOT intelligence doctrine for the next architecture stage.")
    lines.append("")
    lines.append("## Core Doctrine")
    lines.append("")
    lines.append("`COLD NEWS REFRESH` is not the final war intelligence system. It is the fallback/backfill patrol.")
    lines.append("")
    lines.append("`HOT_INTELLIGENCE_INGRESS_GATEWAY` is the future Cengizhan model:")
    lines.append("")
    lines.append("- Always-on or near-real-time intelligence ingress.")
    lines.append("- Telegram / Discord / X / crypto news / onchain watcher.")
    lines.append("- Ingress relevance filter.")
    lines.append("- Source trust scoring.")
    lines.append("- Adversarial tactic classifier.")
    lines.append("- Conflict resolution: onchain vs social vs news disagreement.")
    lines.append("- Priority router: CRITICAL / WATCH / INFO / DROP.")
    lines.append("- Hunter / Prosecutor / Risk / Panel / Telegram alarm integration.")
    lines.append("")
    lines.append("## Current Recovery Evidence")
    lines.append("")
    for k, v in result["seal_matrix"].items():
        lines.append(f"- `{k}` = `{v.get('status')}`")
        for e in v.get("evidence", []):
            lines.append(f"  - {e}")
    lines.append("")
    lines.append("## Known Warnings")
    lines.append("")
    for w in result["known_warnings"]:
        lines.append(f"- `{w.get('code')}`: {w.get('message')}")
    lines.append("")
    lines.append("## Red Team Questions")
    lines.append("")
    lines.append("1. Are we incorrectly presenting a 20-minute timer as final intelligence? If yes, block seal wording.")
    lines.append("2. Are the NEWS-D warnings acceptable as known issues for a cold producer seal?")
    lines.append("3. Is any claim stronger than evidence supports?")
    lines.append("4. Should NEWS-F wording say `COLD NEWS PRODUCER OPERATIONAL` rather than `NEWS FULLY COMPLETE`?")
    lines.append("5. Should HOT Gateway be opened only after NEWS-F, with CENGIZHAN_INTELLIGENCE_DOCTRINE as doctrine input?")
    lines.append("")
    lines.append("## Expected Output")
    lines.append("")
    lines.append("Return one of:")
    lines.append("")
    lines.append("- `OK_SEAL_COLD_NEWS_WITH_WARNINGS_THEN_OPEN_HOT_GATEWAY_PLAN`")
    lines.append("- `WARN_FIX_SEAL_WORDING_BEFORE_GITHUB_SEAL`")
    lines.append("- `BLOCK_SEAL_DUE_TO_HIDDEN_FAILURE`")
    lines.append("")
    lines.append("No praise. Give direct risk verdict.")
    lines.append("")
    return "\n".join(lines)


def build_report(result):
    lines = []
    lines.append("# NEWS-E Review Prompt and Seal Prep NOAPI")
    lines.append("")
    lines.append(f"- stage: `{STAGE}`")
    lines.append(f"- generated_at_utc: `{result['generated_at_utc']}`")
    lines.append(f"- decision: `{result['decision']}`")
    lines.append(f"- next_step: `{result['next_step']}`")
    lines.append("")
    lines.append("## Authority")
    lines.append("")
    for k, v in result["authority"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## References")
    lines.append("")
    for k, v in result["references"].items():
        lines.append(f"- `{k}`: decision=`{v.get('decision')}`, path=`{v.get('path')}`")
    lines.append("")
    lines.append("## Seal Matrix")
    lines.append("")
    for k, v in result["seal_matrix"].items():
        lines.append(f"### {k}")
        lines.append("")
        lines.append(f"- status: `{v.get('status')}`")
        for e in v.get("evidence", []):
            lines.append(f"- evidence: `{e}`")
        lines.append("")
    lines.append("## Known Warnings")
    lines.append("")
    for w in result["known_warnings"]:
        lines.append(f"- `{w.get('source')}` `{w.get('code')}`: {w.get('message')}")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for f in result["findings"]:
        lines.append(f"- `{f['level']}` {f['code']}: {f['message']}")
    lines.append("")
    lines.append("## Review Prompt Files")
    lines.append("")
    for k, v in result["review_prompts"].items():
        lines.append(f"- {k}: `{v.get('path')}`, sha256=`{v.get('sha256')}`")
    lines.append("")
    return "\n".join(lines)


def main():
    refs = {}
    full_objs = {}
    for name, path in REFS.items():
        compact, obj = compact_ref(name, path)
        refs[name] = compact
        full_objs[name] = obj

    known_warnings = build_known_warnings(refs)
    seal_matrix = build_seal_matrix(refs)

    findings = []

    def add(level, code, message):
        findings.append({"level": level, "code": code, "message": message})

    missing = [k for k, v in refs.items() if v.get("read_error")]
    if missing:
        add("FAIL", "REFERENCE_ARTIFACTS_MISSING_OR_UNREADABLE", "Okunamayan referanslar: " + ",".join(missing))
    else:
        add("OK", "REFERENCE_ARTIFACTS_READ", "NEWS-A/B/C/D referans artifact zinciri okundu.")

    if refs.get("news_b_fix2_post", {}).get("decision") == "OK_NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_CLEAN":
        add("OK", "COLD_PRODUCER_TIMER_OPERATIONAL_REFERENCE_OK", "Timer post-activation audit clean.")
    else:
        add("FAIL", "COLD_PRODUCER_TIMER_REFERENCE_NOT_CLEAN", "Timer post-activation audit clean değil.")

    if refs.get("news_c", {}).get("decision") == "OK_NEWS_C_DOWNSTREAM_CHECKSUM_FINGERPRINT_CLEAN":
        add("OK", "DOWNSTREAM_CHAIN_REFERENCE_OK", "NEWS-C downstream checksum clean.")
    else:
        add("FAIL", "DOWNSTREAM_CHAIN_REFERENCE_NOT_CLEAN", "NEWS-C downstream checksum clean değil.")

    if refs.get("news_d", {}).get("decision") == "WARN_NEWS_D_PANEL_READMODEL_FRESHNESS_REVIEW_REQUIRED":
        add("OK", "NEWS_D_WARNINGS_EXPLICITLY_CAPTURED", "NEWS-D warnings açıkça yakalandı; gizlenmedi.")
    elif refs.get("news_d", {}).get("decision") == "OK_NEWS_D_PANEL_READMODEL_FRESHNESS_CLEAN":
        add("OK", "NEWS_D_CLEAN", "NEWS-D clean.")
    else:
        add("FAIL", "NEWS_D_REFERENCE_BLOCKED_OR_UNKNOWN", "NEWS-D karar durumu beklenen değil.")

    if known_warnings:
        add("WARN", "KNOWN_WARNINGS_EXIST_FOR_NEWS_F", "NEWS-F seal known warnings ile yapılmalı; full-clean iddiası yasak.")
    else:
        add("OK", "NO_KNOWN_WARNINGS", "Known warning yok.")

    cold_hot = seal_matrix.get("cold_hot_doctrine_split", {})
    if cold_hot.get("status") == "OK":
        add("OK", "COLD_HOT_DOCTRINE_SPLIT_CAPTURED", "20dk timer fallback; HOT Gateway post-seal olarak ayrıldı.")
    else:
        add("FAIL", "COLD_HOT_DOCTRINE_SPLIT_MISSING", "Cold/Hot ayrımı eksik.")

    matrix_bad = [k for k, v in seal_matrix.items() if v.get("status") not in {"OK", "WARN"}]
    if matrix_bad:
        add("FAIL", "SEAL_MATRIX_HAS_BLOCKING_ITEMS", "Seal matrix blokajları: " + ",".join(matrix_bad))
    else:
        add("OK", "SEAL_MATRIX_NO_BLOCKING_ITEMS", "Seal matrix içinde blokaj yok; WARN maddeler açık.")

    fail_count = sum(1 for x in findings if x["level"] == "FAIL")
    warn_count = sum(1 for x in findings if x["level"] == "WARN")

    if fail_count:
        decision = "FAIL_NEWS_E_REVIEW_PROMPT_AND_SEAL_PREP_BLOCKED"
        next_step = "REVIEW_NEWS_E_BLOCKERS"
    else:
        decision = "WARN_NEWS_E_READY_FOR_REVIEW_AND_NEWS_F_SEAL_WITH_KNOWN_WARNINGS"
        next_step = "NEWS_F_FINAL_OPERATIONAL_SEAL_WITH_KNOWN_WARNINGS"

    result = {
        "stage": STAGE,
        "generated_at_utc": now_iso(),
        "decision": decision,
        "next_step": next_step,
        "authority": {
            "readonly_artifact_review": True,
            "real_db_write": False,
            "db_schema_write": False,
            "panel_write": False,
            "readmodel_write": False,
            "runner_code_change": False,
            "matcher_code_change": False,
            "systemd_change": False,
            "timer_change": False,
            "service_change": False,
            "boot_update": False,
            "runtime_update": False,
            "external_api_call": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "repo_artifact_write": True,
        },
        "references": refs,
        "expected_sequence": EXPECTED_SEQUENCE,
        "seal_matrix": seal_matrix,
        "known_warnings": known_warnings,
        "seal_wording_policy": {
            "allowed": [
                "COLD NEWS PRODUCER OPERATIONAL",
                "DOWNSTREAM 47/47/47 CHAIN VERIFIED",
                "FINAL SEAL WITH KNOWN WARNINGS",
                "20MIN TIMER IS FALLBACK/COLD BACKFILL",
                "HOT_INTELLIGENCE_INGRESS_GATEWAY DEFERRED AFTER NEWS-F",
            ],
            "forbidden": [
                "NEWS FULLY CLEAN",
                "PANEL FULLY VERIFIED",
                "FRESHNESS FULLY CURRENT",
                "HOT INTELLIGENCE IMPLEMENTED",
                "REAL-TIME INTELLIGENCE COMPLETE",
                "TRADE OR PAPER AUTHORITY ENABLED",
            ],
        },
        "findings": findings,
        "summary": {
            "fail_count": fail_count,
            "warn_count": warn_count,
            "known_warning_count": len(known_warnings),
            "seal_matrix_ok_count": sum(1 for v in seal_matrix.values() if v.get("status") == "OK"),
            "seal_matrix_warn_count": sum(1 for v in seal_matrix.values() if v.get("status") == "WARN"),
            "next_stage": next_step,
        },
    }

    codex_prompt = build_codex_prompt(result)
    gemini_prompt = build_gemini_prompt(result)

    result["review_prompts"] = {
        "codex": {
            "path": str(OUT_CODEX),
            "sha256": sha256_text(codex_prompt),
        },
        "gemini_red_team": {
            "path": str(OUT_GEMINI),
            "sha256": sha256_text(gemini_prompt),
        },
    }

    safe_write_text(OUT_CODEX, codex_prompt)
    safe_write_text(OUT_GEMINI, gemini_prompt)
    safe_write_json(OUT_JSON, result)
    safe_write_text(OUT_MD, build_report(result))

    print("OK_NEWS_E_REVIEW_PROMPT_AND_SEAL_PREP_NOAPI_WRITTEN")
    print("DECISION=" + decision)
    print("JSON=" + rel(OUT_JSON))
    print("REPORT=" + rel(OUT_MD))
    print("CODEX_PROMPT=" + rel(OUT_CODEX))
    print("GEMINI_PROMPT=" + rel(OUT_GEMINI))
    print("KNOWN_WARNING_COUNT=" + str(len(known_warnings)))
    print("SEAL_MATRIX_OK_COUNT=" + str(result["summary"]["seal_matrix_ok_count"]))
    print("SEAL_MATRIX_WARN_COUNT=" + str(result["summary"]["seal_matrix_warn_count"]))
    print("WARN_COUNT=" + str(warn_count))
    print("FAIL_COUNT=" + str(fail_count))
    print("NEXT_STEP=" + next_step)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
