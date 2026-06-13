#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("/root/tokenoskobi_clean_v1")
DEFAULT_DB = BASE / "data/tokenoskobi_clean_v1.sqlite"

PHASE_TOOL = "news_social_launch_signal_writer_v1"
REAL_WRITE_CONFIRM = "NEWS_SOCIAL_WRITER_REAL_WRITE_LOCAL_INPUT_ONLY"

SOURCE_TRUST = {"low", "medium", "medium_high", "high"}
ONCHAIN_STATUS = {"NOT_CHECKED", "PENDING", "CONFIRMED", "REJECTED"}
RISK_STATUS = {"NOT_CHECKED", "WAIT_MORE_DATA", "PASS", "REJECT"}
REVIEW_STATUS = {"WAIT_MORE_DATA", "READY_FOR_ONCHAIN_CHECK", "READY_FOR_RISK_CHECK", "REJECTED", "ARCHIVED"}
EVIDENCE_TYPE = {"OFFICIAL_POST", "EXCHANGE_NEWS", "SOCIAL_BURST", "LAUNCHPAD_CLAIM", "KOL_MENTION", "COMMUNITY_BURST"}
MEMORY_ROLE = {"AUTOPSY_INPUT", "LEARNING_SUMMARY_INPUT", "RWD_CONTEXT_INPUT"}

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def stable_uid(prefix: str, *parts: object) -> str:
    raw = "|".join("" if p is None else str(p).strip().lower() for p in parts)
    return prefix + "_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

def clamp_score(value: object, field: str) -> float:
    try:
        v = float(value)
    except Exception as exc:
        raise ValueError(f"{field}_NOT_NUMERIC") from exc
    if v < 0 or v > 100:
        raise ValueError(f"{field}_OUT_OF_RANGE_0_100")
    return v

def load_payload(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("INPUT_JSON_MUST_BE_OBJECT")
    return data

def require_str(data: dict, key: str) -> str:
    val = data.get(key)
    if not isinstance(val, str) or not val.strip():
        raise ValueError(f"MISSING_OR_EMPTY_{key}")
    return val.strip()

def optional_str(data: dict, key: str):
    val = data.get(key)
    if val is None:
        return None
    if not isinstance(val, str):
        raise ValueError(f"{key}_MUST_BE_STRING_OR_NULL")
    return val.strip() or None

def route_review(onchain_status: str, risk_status: str, contract_claim, manipulation_risk: float, expected_loss: float) -> tuple[str, str]:
    if manipulation_risk >= 85 or expected_loss >= 85:
        return "REJECTED", "risk/loss too high; route blocked before deterministic promotion"
    if not contract_claim:
        return "READY_FOR_ONCHAIN_CHECK", "contract missing or unconfirmed; onchain check required"
    if onchain_status in {"NOT_CHECKED", "PENDING"}:
        return "READY_FOR_ONCHAIN_CHECK", "contract claim exists but onchain confirmation still required"
    if onchain_status == "REJECTED":
        return "REJECTED", "onchain confirmation rejected"
    if risk_status in {"NOT_CHECKED", "WAIT_MORE_DATA"}:
        return "READY_FOR_RISK_CHECK", "onchain confirmed path still needs risk/security gate"
    if risk_status == "REJECT":
        return "REJECTED", "risk/security gate rejected"
    return "WAIT_MORE_DATA", "signal captured; deterministic ledger still required before any action"

def risk_reward_label(upside: float, loss: float, manipulation: float, onchain_status: str, risk_status: str) -> str:
    if manipulation >= 85 or loss >= 85:
        return "REJECT_RISK_HIGH"
    if upside >= 65 and loss <= 55 and onchain_status in {"PENDING", "CONFIRMED"}:
        return "WATCH_EARLY"
    if onchain_status == "CONFIRMED" and risk_status in {"WAIT_MORE_DATA", "NOT_CHECKED"}:
        return "READY_FOR_DETERMINISTIC_CHECK"
    return "WAIT_MORE_DATA"

def normalize_candidate(data: dict) -> dict:
    source_class = require_str(data, "source_class")
    source_name = require_str(data, "source_name")
    source_trust_level = require_str(data, "source_trust_level")
    if source_trust_level not in SOURCE_TRUST:
        raise ValueError("BAD_source_trust_level")

    token_name_claim = require_str(data, "token_name_claim")
    chain_claim = require_str(data, "chain_claim")
    contract_address_claim = optional_str(data, "contract_address_claim")
    launch_time_claim = optional_str(data, "launch_time_claim")

    evidence_type = require_str(data, "evidence_type")
    if evidence_type not in EVIDENCE_TYPE:
        raise ValueError("BAD_evidence_type")
    evidence_hash = require_str(data, "evidence_hash")
    evidence_summary = require_str(data, "evidence_summary")

    officialness_score = clamp_score(data.get("officialness_score", 0), "officialness_score")
    social_burst_score = clamp_score(data.get("social_burst_score", 0), "social_burst_score")
    manipulation_risk_score = clamp_score(data.get("manipulation_risk_score", 0), "manipulation_risk_score")
    expected_upside_score = clamp_score(data.get("expected_upside_score", 0), "expected_upside_score")
    expected_loss_score = clamp_score(data.get("expected_loss_score", 0), "expected_loss_score")

    onchain_confirmation_status = str(data.get("onchain_confirmation_status", "NOT_CHECKED")).strip()
    risk_gate_status = str(data.get("risk_gate_status", "WAIT_MORE_DATA")).strip()
    if onchain_confirmation_status not in ONCHAIN_STATUS:
        raise ValueError("BAD_onchain_confirmation_status")
    if risk_gate_status not in RISK_STATUS:
        raise ValueError("BAD_risk_gate_status")

    confirms_contract = 1 if data.get("confirms_contract") is True else 0
    confirms_onchain = 1 if data.get("confirms_onchain") is True else 0
    confirms_risk = 1 if data.get("confirms_risk") is True else 0

    review_status, review_reason = route_review(
        onchain_confirmation_status,
        risk_gate_status,
        contract_address_claim,
        manipulation_risk_score,
        expected_loss_score,
    )

    rr_label = risk_reward_label(
        expected_upside_score,
        expected_loss_score,
        manipulation_risk_score,
        onchain_confirmation_status,
        risk_gate_status,
    )

    memory_role = str(data.get("memory_role", "AUTOPSY_INPUT")).strip()
    if memory_role not in MEMORY_ROLE:
        raise ValueError("BAD_memory_role")

    mistake_family = str(data.get("mistake_family", "news_social_signal_without_full_deterministic_confirmation")).strip()
    if not mistake_family:
        raise ValueError("MISSING_mistake_family")

    t = now_iso()

    source_uid = stable_uid("src", source_class, source_name)
    signal_uid = stable_uid("sig", source_class, source_name, token_name_claim, chain_claim, contract_address_claim, launch_time_claim)
    evidence_uid = stable_uid("ev", signal_uid, evidence_type, evidence_hash)
    review_uid = stable_uid("rev", signal_uid, review_status)
    memory_uid = stable_uid("mem", signal_uid, mistake_family)
    repeat_mistake_key = stable_uid("mistake", mistake_family, source_class, chain_claim, token_name_claim)

    expected_value_preview = {
        "expected_upside_score": expected_upside_score,
        "expected_loss_score": expected_loss_score,
        "manipulation_risk_score": manipulation_risk_score,
        "risk_reward_label": rr_label,
        "repeat_mistake_key": repeat_mistake_key,
        "trade_authority": False,
        "signal_truth_status": "NOT_TRUTH",
        "deterministic_gate_required": True,
    }

    return {
        "source": {
            "source_uid": source_uid,
            "source_class": source_class,
            "source_name": source_name,
            "source_trust_level": source_trust_level,
            "official_required_for_high_confidence": 1,
            "trade_authority": 0,
            "created_at": t,
        },
        "signal": {
            "signal_uid": signal_uid,
            "source_uid": source_uid,
            "token_name_claim": token_name_claim,
            "chain_claim": chain_claim,
            "contract_address_claim": contract_address_claim,
            "launch_time_claim": launch_time_claim,
            "officialness_score": officialness_score,
            "social_burst_score": social_burst_score,
            "manipulation_risk_score": manipulation_risk_score,
            "onchain_confirmation_status": onchain_confirmation_status,
            "risk_gate_status": risk_gate_status,
            "signal_truth_status": "NOT_TRUTH",
            "trade_authority": 0,
            "created_at": t,
        },
        "evidence": {
            "evidence_uid": evidence_uid,
            "signal_uid": signal_uid,
            "evidence_type": evidence_type,
            "evidence_hash": evidence_hash,
            "evidence_summary": evidence_summary + " | rr=" + json.dumps(expected_value_preview, sort_keys=True),
            "confirms_contract": confirms_contract,
            "confirms_onchain": confirms_onchain,
            "confirms_risk": confirms_risk,
            "trade_authority": 0,
            "created_at": t,
        },
        "review": {
            "review_uid": review_uid,
            "signal_uid": signal_uid,
            "review_status": review_status,
            "review_reason": review_reason + " | risk_reward_label=" + rr_label,
            "deterministic_gate_required": 1,
            "ai_opinion_required": 0,
            "trade_authority": 0,
            "created_at": t,
        },
        "memory": {
            "memory_uid": memory_uid,
            "signal_uid": signal_uid,
            "linked_false_negative_case_uid": None,
            "linked_rwd_case_uid": None,
            "memory_role": memory_role,
            "hot_loop_allowed": 0,
            "trade_authority": 0,
            "created_at": t,
        },
        "risk_reward_preview": expected_value_preview,
    }

def integrity_info(db_path: Path) -> dict:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = con.cursor()
    integrity = cur.execute("PRAGMA integrity_check").fetchone()[0]
    fk_error_count = len(cur.execute("PRAGMA foreign_key_check").fetchall())
    con.close()
    return {"integrity": integrity, "fk_error_count": fk_error_count}

def count_existing_signal(db_path: Path, signal_uid: str) -> int:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = con.cursor()
    cnt = cur.execute("SELECT COUNT(*) FROM news_social_launch_signals_v1 WHERE signal_uid=?", (signal_uid,)).fetchone()[0]
    con.close()
    return int(cnt)

def backup_db(db_path: Path) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = BASE / "backups" / f"news_social_writer_v1_real_write_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup_path = backup_dir / "tokenoskobi_clean_v1.sqlite.before_news_social_writer_v1"
    shutil.copy2(db_path, backup_path)
    rollback = backup_dir / "ROLLBACK_NEWS_SOCIAL_WRITER_V1_RESTORE_DB.sh"
    rollback.write_text(
        "#!/usr/bin/env bash\n"
        "set -Eeuo pipefail\n"
        f"cp -a {str(backup_path)!r} {str(db_path)!r}\n"
        f"echo RESTORED_DB_FROM={str(backup_path)!r}\n",
        encoding="utf-8",
    )
    rollback.chmod(0o700)
    return backup_path

def write_rows(db_path: Path, rows: dict) -> dict:
    backup_path = backup_db(db_path)
    con = sqlite3.connect(str(db_path))
    try:
        cur = con.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("BEGIN")

        s = rows["source"]
        cur.execute("""
            INSERT OR IGNORE INTO news_social_sources_v1
            (source_uid, source_class, source_name, source_trust_level, official_required_for_high_confidence, trade_authority, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (
            s["source_uid"], s["source_class"], s["source_name"], s["source_trust_level"],
            s["official_required_for_high_confidence"], s["created_at"]
        ))

        if count_existing_signal(db_path, rows["signal"]["signal_uid"]) > 0:
            con.rollback()
            return {"written": False, "reason": "DUPLICATE_SIGNAL_BLOCKED", "backup_db": str(backup_path)}

        sig = rows["signal"]
        cur.execute("""
            INSERT INTO news_social_launch_signals_v1
            (signal_uid, source_uid, token_name_claim, chain_claim, contract_address_claim, launch_time_claim,
             officialness_score, social_burst_score, manipulation_risk_score, onchain_confirmation_status,
             risk_gate_status, signal_truth_status, trade_authority, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NOT_TRUTH', 0, ?)
        """, (
            sig["signal_uid"], sig["source_uid"], sig["token_name_claim"], sig["chain_claim"],
            sig["contract_address_claim"], sig["launch_time_claim"], sig["officialness_score"],
            sig["social_burst_score"], sig["manipulation_risk_score"], sig["onchain_confirmation_status"],
            sig["risk_gate_status"], sig["created_at"]
        ))

        ev = rows["evidence"]
        cur.execute("""
            INSERT INTO news_social_signal_evidence_links_v1
            (evidence_uid, signal_uid, evidence_type, evidence_hash, evidence_summary, confirms_contract,
             confirms_onchain, confirms_risk, trade_authority, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """, (
            ev["evidence_uid"], ev["signal_uid"], ev["evidence_type"], ev["evidence_hash"],
            ev["evidence_summary"], ev["confirms_contract"], ev["confirms_onchain"], ev["confirms_risk"],
            ev["created_at"]
        ))

        rv = rows["review"]
        cur.execute("""
            INSERT INTO news_social_review_queue_v1
            (review_uid, signal_uid, review_status, review_reason, deterministic_gate_required,
             ai_opinion_required, trade_authority, created_at)
            VALUES (?, ?, ?, ?, 1, ?, 0, ?)
        """, (
            rv["review_uid"], rv["signal_uid"], rv["review_status"], rv["review_reason"],
            rv["ai_opinion_required"], rv["created_at"]
        ))

        mem = rows["memory"]
        cur.execute("""
            INSERT INTO news_social_false_negative_memory_links_v1
            (memory_uid, signal_uid, linked_false_negative_case_uid, linked_rwd_case_uid, memory_role,
             hot_loop_allowed, trade_authority, created_at)
            VALUES (?, ?, ?, ?, ?, 0, 0, ?)
        """, (
            mem["memory_uid"], mem["signal_uid"], mem["linked_false_negative_case_uid"],
            mem["linked_rwd_case_uid"], mem["memory_role"], mem["created_at"]
        ))

        con.commit()
        return {"written": True, "reason": "ROWS_WRITTEN", "backup_db": str(backup_path)}
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Local JSON input only")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--write", action="store_true", help="Actually write DB rows; default is dry-run")
    ap.add_argument("--confirm", default="", help="Required confirmation phrase for --write")
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    input_path = Path(args.input)
    db_path = Path(args.db)

    if not input_path.exists():
        raise SystemExit("INPUT_FILE_MISSING")
    if not db_path.exists():
        raise SystemExit("DB_MISSING")

    payload = load_payload(input_path)
    rows = normalize_candidate(payload)
    pre = integrity_info(db_path)
    dup_count = count_existing_signal(db_path, rows["signal"]["signal_uid"])

    real_write_allowed = args.write and args.confirm == REAL_WRITE_CONFIRM
    result = {
        "tool": PHASE_TOOL,
        "mode": "REAL_WRITE" if real_write_allowed else "DRY_RUN",
        "input": str(input_path),
        "db": str(db_path),
        "pre_integrity": pre,
        "duplicate_signal_count_before": dup_count,
        "would_write": rows,
        "risk_reward_preview": rows["risk_reward_preview"],
        "hard_locks": {
            "news_social_signal_is_not_truth": rows["signal"]["signal_truth_status"] == "NOT_TRUTH",
            "trade_authority_zero": rows["signal"]["trade_authority"] == 0 and rows["review"]["trade_authority"] == 0,
            "deterministic_gate_required": rows["review"]["deterministic_gate_required"] == 1,
            "false_negative_hot_loop_false": rows["memory"]["hot_loop_allowed"] == 0,
            "api_calls": False,
            "paper_trade": False,
            "live_trade": False,
        },
    }

    if args.write and args.confirm != REAL_WRITE_CONFIRM:
        result["write_result"] = {"written": False, "reason": "CONFIRMATION_PHRASE_REQUIRED"}
    elif real_write_allowed:
        if dup_count > 0:
            result["write_result"] = {"written": False, "reason": "DUPLICATE_SIGNAL_BLOCKED"}
        else:
            result["write_result"] = write_rows(db_path, rows)
            result["post_integrity"] = integrity_info(db_path)
    else:
        result["write_result"] = {"written": False, "reason": "DRY_RUN_DEFAULT"}

    text = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
