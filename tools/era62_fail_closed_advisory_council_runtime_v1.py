#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from core.authority import (
    evaluate_authority,
    load_authority_state,
    validate_authority_state,
)

ROOT_DEFAULT = Path(__file__).resolve().parents[1]
SCHEMA_ID = "tokenoskobi.era62.advisory_council_result.v1"

TASK_KEYS = {
    "request_id",
    "task_type",
    "target",
    "declared_effects",
    "evidence_pointers",
    "risk_class",
    "required_specialists",
    "human_approval_requirement",
}

TARGET_KEYS = {
    "resource",
    "path",
    "hot_path",
}

EVIDENCE_KEYS = {
    "evidence_id",
    "path",
    "sha256",
    "claims",
}

PACKET_KEYS = {
    "specialist_id",
    "verdict",
    "confidence",
    "evidence_used",
    "assumptions",
    "risks",
    "objections",
    "recommended_action",
    "forbidden_actions",
}

ISSUE_KEYS = {
    "issue_id",
    "category",
    "severity",
    "description",
    "blocking",
}

ACTION_KEYS = {
    "action",
    "reason",
    "execution_allowed",
    "requires_human_approval",
}


class CouncilBlock(ValueError):
    pass


def block(code: str) -> None:
    raise CouncilBlock(str(code))


def exact_object(
    value: Any,
    keys: set[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        block(f"{label}_OBJECT_REQUIRED")

    actual = set(value)
    missing = sorted(keys - actual)
    extra = sorted(actual - keys)

    if missing:
        block(f"{label}_MISSING_KEYS:{','.join(missing)}")

    if extra:
        block(f"{label}_UNKNOWN_KEYS:{','.join(extra)}")

    return value


def text(
    value: Any,
    label: str,
    maximum: int = 4096,
) -> str:
    if not isinstance(value, str):
        block(f"{label}_STRING_REQUIRED")

    if not value or len(value) > maximum:
        block(f"{label}_INVALID_LENGTH")

    if "\x00" in value:
        block(f"{label}_NULL_BYTE")

    return value


def text_list(
    value: Any,
    label: str,
    maximum_items: int = 64,
    unique: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        block(f"{label}_ARRAY_REQUIRED")

    if len(value) > maximum_items:
        block(f"{label}_TOO_MANY_ITEMS")

    result = [
        text(item, f"{label}_{index}")
        for index, item in enumerate(value)
    ]

    if unique and len(result) != len(set(result)):
        block(f"{label}_DUPLICATE_ITEM")

    return result


def strict_json_loads(
    raw: str,
    label: str,
    maximum_bytes: int = 262144,
) -> dict[str, Any]:
    if not isinstance(raw, str):
        block(f"{label}_RAW_STRING_REQUIRED")

    if len(raw.encode("utf-8")) > maximum_bytes:
        block(f"{label}_TOO_LARGE")

    def object_hook(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for key, value in pairs:
            if key in result:
                block(f"{label}_DUPLICATE_KEY:{key}")

            result[key] = value

        return result

    def reject_constant(value: str) -> None:
        block(f"{label}_NONFINITE_NUMBER:{value}")

    try:
        parsed = json.loads(
            raw,
            object_pairs_hook=object_hook,
            parse_constant=reject_constant,
        )
    except CouncilBlock:
        raise
    except json.JSONDecodeError as exc:
        block(f"{label}_INVALID_JSON:{exc.msg}")

    if not isinstance(parsed, dict):
        block(f"{label}_OBJECT_REQUIRED")

    return parsed


def load_config(root: Path) -> dict[str, Any]:
    path = root / "config/era62_advisory_council_runtime_v1.json"

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        block(f"CONFIG_LOAD_FAILED:{type(exc).__name__}")

    if not isinstance(config, dict):
        block("CONFIG_OBJECT_REQUIRED")

    if config.get("schema") != (
        "tokenoskobi.era62.advisory_council_runtime.v1"
    ):
        block("CONFIG_SCHEMA_MISMATCH")

    disabled = (
        "provider_dispatch_active",
        "external_model_binding",
        "network",
        "live_data",
        "database_write",
        "panel_mutation",
        "service_mutation",
        "timer_mutation",
        "production_runtime_binding",
        "automatic_action",
        "execution",
    )

    for key in disabled:
        if config.get(key) is not False:
            block(f"DISABLED_SURFACE_ENABLED:{key}")

    authority = config.get("authority") or {}

    for key in (
        "ai",
        "trade",
        "wallet",
        "signing",
        "order_create",
    ):
        if authority.get(key) != 0:
            block(f"AUTHORITY_REGRESSION:{key}")

    return config


def inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def safe_path(
    root: Path,
    relative: Any,
    allowed_roots: list[str],
    *,
    must_exist: bool,
    regular_file: bool,
) -> tuple[Path, str]:
    value = text(relative, "PATH", 512)

    if value.startswith("/") or "\\" in value:
        block("PATH_ABSOLUTE_OR_BACKSLASH_DENIED")

    parts = value.split("/")

    if any(part in ("", ".", "..") for part in parts):
        block("PATH_TRAVERSAL_OR_EMPTY_COMPONENT_DENIED")

    pure = PurePosixPath(value)

    if pure.is_absolute():
        block("PATH_ABSOLUTE_DENIED")

    normalized = pure.as_posix()

    allowed = any(
        normalized == prefix.rstrip("/")
        or normalized.startswith(prefix.rstrip("/") + "/")
        for prefix in allowed_roots
    )

    if not allowed:
        block("PATH_OUTSIDE_ALLOWED_ROOTS")

    current = root

    for part in parts:
        current = current / part

        if current.exists() and current.is_symlink():
            block("PATH_SYMLINK_ESCAPE_DENIED")

    try:
        resolved = (root / normalized).resolve(strict=must_exist)
    except FileNotFoundError:
        block("PATH_MISSING")

    root_resolved = root.resolve()

    if not inside(root_resolved, resolved):
        block("PATH_OUTSIDE_REPOSITORY")

    if regular_file and not resolved.is_file():
        block("PATH_REGULAR_FILE_REQUIRED")

    return resolved, normalized


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def validate_evidence(
    value: Any,
    root: Path,
    config: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    if not isinstance(value, list) or not value:
        block("EVIDENCE_POINTERS_NONEMPTY_ARRAY_REQUIRED")

    if len(value) > config["limits"]["max_evidence_pointers"]:
        block("EVIDENCE_POINTERS_TOO_MANY")

    verified: list[dict[str, Any]] = []
    index: dict[str, dict[str, Any]] = {}

    for position, raw in enumerate(value):
        item = exact_object(
            raw,
            EVIDENCE_KEYS,
            f"EVIDENCE_{position}",
        )

        evidence_id = text(
            item["evidence_id"],
            f"EVIDENCE_ID_{position}",
            128,
        )

        if evidence_id in index:
            block(f"EVIDENCE_ID_DUPLICATE:{evidence_id}")

        checksum = text(
            item["sha256"],
            f"EVIDENCE_SHA256_{position}",
            64,
        )

        if (
            len(checksum) != 64
            or any(
                character not in "0123456789abcdef"
                for character in checksum
            )
        ):
            block(f"EVIDENCE_SHA256_INVALID:{evidence_id}")

        claims = text_list(
            item["claims"],
            f"EVIDENCE_CLAIMS_{position}",
            32,
            True,
        )

        if not claims:
            block(f"EVIDENCE_CLAIMS_EMPTY:{evidence_id}")

        path, normalized = safe_path(
            root,
            item["path"],
            config["allowed_evidence_roots"],
            must_exist=True,
            regular_file=True,
        )

        actual = sha256(path)

        if actual != checksum:
            block(f"EVIDENCE_CHECKSUM_MISMATCH:{evidence_id}")

        record = {
            "evidence_id": evidence_id,
            "path": normalized,
            "sha256": actual,
            "claims": claims,
            "verified": True,
        }

        verified.append(record)
        index[evidence_id] = record

    return verified, index


def validate_issues(
    value: Any,
    label: str,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        block(f"{label}_ARRAY_REQUIRED")

    if len(value) > config["limits"]["max_issue_items"]:
        block(f"{label}_TOO_MANY_ITEMS")

    result: list[dict[str, Any]] = []

    for position, raw in enumerate(value):
        item = exact_object(
            raw,
            ISSUE_KEYS,
            f"{label}_{position}",
        )

        category = text(
            item["category"],
            f"{label}_{position}_CATEGORY",
            64,
        )

        severity = text(
            item["severity"],
            f"{label}_{position}_SEVERITY",
            16,
        )

        if category not in config["allowed_issue_categories"]:
            block(f"{label}_{position}_CATEGORY_DENIED:{category}")

        if severity not in config["allowed_severities"]:
            block(f"{label}_{position}_SEVERITY_DENIED:{severity}")

        if not isinstance(item["blocking"], bool):
            block(f"{label}_{position}_BLOCKING_BOOLEAN_REQUIRED")

        result.append(
            {
                "issue_id": text(
                    item["issue_id"],
                    f"{label}_{position}_ID",
                    128,
                ),
                "category": category,
                "severity": severity,
                "description": text(
                    item["description"],
                    f"{label}_{position}_DESCRIPTION",
                    4096,
                ),
                "blocking": item["blocking"],
            }
        )

    return result


def blocked_result(
    request_id: str,
    blockers: list[str],
    authority_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    unique = sorted(set(str(item) for item in blockers if item))

    return {
        "schema_id": SCHEMA_ID,
        "request_id": request_id or "UNKNOWN",
        "status": "BLOCK",
        "decision_summary": {
            "result": "BLOCK",
            "advisory_only": True,
            "reason_count": len(unique),
        },
        "supported_facts": [],
        "unsupported_claims": [],
        "specialist_verdicts": [],
        "agreements": [],
        "conflicts": [],
        "critical_dissent": [],
        "risk_engine_result": {
            "decision": "NOT_INVOKED",
            "boundary": "NOT_BYPASSED",
            "final_risk_authority": "RISK_ENGINE",
            "execution_allowed": False,
        },
        "authority_gate_result": authority_result or {
            "decision": "DENY",
            "reason_codes": ["PREVALIDATION_BLOCK"],
        },
        "recommended_options": [
            {"action": "REQUEST_MORE_EVIDENCE"}
        ],
        "rejected_options": [],
        "required_human_decision": {
            "required": True,
            "decision": "REVIEW_BLOCKERS",
        },
        "blockers": unique,
        "missing_specialists": [],
        "model_agreement_is_evidence": False,
        "model_vote_authority": 0,
        "majority_vote_allowed": False,
        "execution_allowed": False,
        "authority": 0,
        "human_approval_required": True,
    }


def evaluate_council(
    task_raw: str,
    specialist_raw_by_id: Mapping[str, str],
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    root_path = Path(root or ROOT_DEFAULT).resolve()
    request_id = "UNKNOWN"
    authority_result: dict[str, Any] | None = None

    try:
        config = load_config(root_path)

        task = exact_object(
            strict_json_loads(
                task_raw,
                "TASK",
                config["limits"]["max_json_bytes"],
            ),
            TASK_KEYS,
            "TASK",
        )

        request_id = text(task["request_id"], "REQUEST_ID", 128)
        task_type = text(task["task_type"], "TASK_TYPE", 64)
        risk_class = text(task["risk_class"], "RISK_CLASS", 64)

        if task_type not in config["routes"]:
            block(f"TASK_TYPE_DENIED:{task_type}")

        if risk_class not in config["allowed_risk_classes"]:
            block(f"RISK_CLASS_DENIED:{risk_class}")

        if task["human_approval_requirement"] is not True:
            block("HUMAN_APPROVAL_REQUIREMENT_MUST_BE_TRUE")

        required_specialists = text_list(
            task["required_specialists"],
            "REQUIRED_SPECIALISTS",
            8,
            True,
        )

        expected_specialists = list(config["routes"][task_type])

        if required_specialists != expected_specialists:
            block("REQUIRED_SPECIALIST_ROUTE_MISMATCH")

        target = exact_object(
            task["target"],
            TARGET_KEYS,
            "TARGET",
        )

        resource = text(
            target["resource"],
            "TARGET_RESOURCE",
            128,
        )

        if resource not in config["allowed_target_resources"]:
            block(f"TARGET_RESOURCE_DENIED:{resource}")

        if target["hot_path"] is not False:
            block("TARGET_HOT_PATH_DENIED")

        target_path = target["path"]

        if target_path is not None:
            safe_path(
                root_path,
                target_path,
                config["allowed_target_roots"],
                must_exist=False,
                regular_file=False,
            )

        effects = task["declared_effects"]

        if not isinstance(effects, dict):
            block("DECLARED_EFFECTS_OBJECT_REQUIRED")

        unknown_effects = sorted(
            set(effects) - set(config["known_effects"])
        )

        if unknown_effects:
            block(
                "UNKNOWN_DECLARED_EFFECTS:"
                + ",".join(unknown_effects)
            )

        normalized_effects: dict[str, bool] = {}

        for key, value in effects.items():
            if not isinstance(value, bool):
                block(f"DECLARED_EFFECT_BOOLEAN_REQUIRED:{key}")

            normalized_effects[key] = value

        verified_evidence, evidence_index = validate_evidence(
            task["evidence_pointers"],
            root_path,
            config,
        )

        loaded = load_authority_state(
            root_path / "config/authority_state_v1.json"
        )

        if not loaded.get("ok"):
            block(
                str(
                    loaded.get("error")
                    or "AUTHORITY_CONFIG_LOAD_FAILED"
                )
            )

        validation = validate_authority_state(loaded["state"])

        if not validation.get("ok"):
            block("AUTHORITY_CONFIG_VALIDATION_FAILED")

        authority_result = evaluate_authority(
            {
                "operation_id": f"era62:{request_id}",
                "operation_type": "read_only",
                "effects": normalized_effects,
                "target": {
                    "resource": resource,
                    "path": target_path,
                    "hot_path": False,
                },
            },
            state=loaded["state"],
        )

        critical = (
            task_type in config["critical_task_types"]
            or risk_class in config["critical_risk_classes"]
            or any(normalized_effects.values())
        )

        if not isinstance(specialist_raw_by_id, Mapping):
            block("SPECIALIST_OUTPUT_MAP_REQUIRED")

        supplied_ids = set(specialist_raw_by_id)
        canonical_ids = set(config["canonical_specialists"])

        unknown_ids = sorted(supplied_ids - canonical_ids)

        if unknown_ids:
            block(
                "UNKNOWN_SUPPLIED_SPECIALISTS:"
                + ",".join(unknown_ids)
            )

        missing = sorted(set(expected_specialists) - supplied_ids)

        blockers: list[str] = []
        degraded = False

        if authority_result.get("decision") != "ALLOW":
            blockers.append("AUTHORITY_GATE_DENIED")
            blockers.extend(authority_result.get("reason_codes") or [])

        if missing:
            if critical:
                blockers.append(
                    "MISSING_REQUIRED_SPECIALIST:"
                    + ",".join(missing)
                )
            else:
                degraded = True

        packets: list[dict[str, Any]] = []

        for assigned_id in expected_specialists:
            if assigned_id not in specialist_raw_by_id:
                continue

            packet = exact_object(
                strict_json_loads(
                    specialist_raw_by_id[assigned_id],
                    f"SPECIALIST_{assigned_id}",
                    config["limits"]["max_json_bytes"],
                ),
                PACKET_KEYS,
                f"SPECIALIST_PACKET_{assigned_id}",
            )

            packet_id = text(
                packet["specialist_id"],
                "SPECIALIST_ID",
                128,
            )

            if packet_id != assigned_id:
                block(
                    f"SPECIALIST_ID_MISMATCH:{assigned_id}:{packet_id}"
                )

            verdict = text(
                packet["verdict"],
                "SPECIALIST_VERDICT",
                64,
            )

            if verdict not in config["allowed_verdicts"]:
                block(f"SPECIALIST_VERDICT_DENIED:{verdict}")

            confidence = packet["confidence"]

            if (
                not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not math.isfinite(float(confidence))
                or not 0 <= float(confidence) <= 100
            ):
                block("SPECIALIST_CONFIDENCE_INVALID")

            evidence_used = text_list(
                packet["evidence_used"],
                "SPECIALIST_EVIDENCE_USED",
                64,
                True,
            )

            unknown_evidence = sorted(
                set(evidence_used) - set(evidence_index)
            )

            if unknown_evidence:
                block(
                    "SPECIALIST_UNKNOWN_EVIDENCE:"
                    + ",".join(unknown_evidence)
                )

            assumptions = text_list(
                packet["assumptions"],
                "SPECIALIST_ASSUMPTIONS",
                64,
                False,
            )

            risks = validate_issues(
                packet["risks"],
                "SPECIALIST_RISK",
                config,
            )

            objections = validate_issues(
                packet["objections"],
                "SPECIALIST_OBJECTION",
                config,
            )

            action = exact_object(
                packet["recommended_action"],
                ACTION_KEYS,
                "RECOMMENDED_ACTION",
            )

            action_name = text(
                action["action"],
                "RECOMMENDED_ACTION_NAME",
                64,
            )

            if action_name not in config["allowed_actions"]:
                block(f"RECOMMENDED_ACTION_DENIED:{action_name}")

            if action["execution_allowed"] is not False:
                block("RECOMMENDED_ACTION_EXECUTION_MUST_BE_FALSE")

            if action["requires_human_approval"] is not True:
                block(
                    "RECOMMENDED_ACTION_HUMAN_APPROVAL_MUST_BE_TRUE"
                )

            forbidden_actions = text_list(
                packet["forbidden_actions"],
                "FORBIDDEN_ACTIONS",
                64,
                True,
            )

            missing_forbidden = sorted(
                set(config["mandatory_forbidden_actions"])
                - set(forbidden_actions)
            )

            if missing_forbidden:
                block(
                    "MANDATORY_FORBIDDEN_ACTIONS_MISSING:"
                    + ",".join(missing_forbidden)
                )

            packets.append(
                {
                    "specialist_id": assigned_id,
                    "verdict": verdict,
                    "confidence": float(confidence),
                    "evidence_used": evidence_used,
                    "assumptions": assumptions,
                    "risks": risks,
                    "objections": objections,
                    "recommended_action": {
                        "action": action_name,
                        "reason": text(
                            action["reason"],
                            "RECOMMENDED_ACTION_REASON",
                            4096,
                        ),
                        "execution_allowed": False,
                        "requires_human_approval": True,
                    },
                    "forbidden_actions": forbidden_actions,
                }
            )

        conflicts: list[dict[str, Any]] = []
        critical_dissent: list[dict[str, Any]] = []

        verdicts = sorted({packet["verdict"] for packet in packets})
        actions = sorted(
            {
                packet["recommended_action"]["action"]
                for packet in packets
            }
        )

        if len(verdicts) > 1:
            conflicts.append(
                {
                    "class": "VERDICT_CONFLICT",
                    "values": verdicts,
                    "resolved": False,
                }
            )

        if len(actions) > 1:
            conflicts.append(
                {
                    "class": "ACTION_CONFLICT",
                    "values": actions,
                    "resolved": False,
                }
            )

        critical_categories = set(
            config["critical_dissent_categories"]
        )

        for packet in packets:
            specialist_id = packet["specialist_id"]

            if packet["verdict"] in (
                "BLOCK",
                "INSUFFICIENT_EVIDENCE",
            ):
                blockers.append(
                    f"{specialist_id}:VERDICT_{packet['verdict']}"
                )

            for issue in packet["risks"]:
                if issue["blocking"]:
                    blockers.append(
                        f"{specialist_id}:BLOCKING_RISK:{issue['issue_id']}"
                    )
                    critical_dissent.append(
                        {
                            "specialist_id": specialist_id,
                            "source": "RISK",
                            **issue,
                        }
                    )

            for issue in packet["objections"]:
                is_critical = (
                    issue["blocking"]
                    or (
                        issue["category"] in critical_categories
                        and issue["severity"] in ("HIGH", "CRITICAL")
                    )
                )

                if is_critical:
                    blockers.append(
                        f"{specialist_id}:CRITICAL_DISSENT:{issue['issue_id']}"
                    )
                    critical_dissent.append(
                        {
                            "specialist_id": specialist_id,
                            "source": "OBJECTION",
                            **issue,
                        }
                    )

        if blockers:
            status = "BLOCK"
        elif degraded:
            status = "DEGRADED_HUMAN_REVIEW_ONLY"
        else:
            status = "READY_FOR_HUMAN_REVIEW"

        agreements: list[dict[str, Any]] = []

        if packets and len(verdicts) == 1 and len(actions) == 1:
            agreements.append(
                {
                    "type": "UNANIMOUS_REPORTED_POSITION",
                    "verdict": verdicts[0],
                    "action": actions[0],
                    "evidence_weight": 0,
                    "authority": 0,
                }
            )

        action_support: dict[str, list[str]] = {}

        for packet in packets:
            action_name = packet["recommended_action"]["action"]

            action_support.setdefault(action_name, []).append(
                packet["specialist_id"]
            )

        recommended_options = [
            {
                "action": action_name,
                "reported_by": sorted(agent_ids),
                "vote_weight": 0,
                "execution_allowed": False,
            }
            for action_name, agent_ids in sorted(action_support.items())
        ]

        if not recommended_options:
            recommended_options = [
                {"action": "REQUEST_MORE_EVIDENCE"}
            ]

        return {
            "schema_id": SCHEMA_ID,
            "request_id": request_id,
            "status": status,
            "decision_summary": {
                "result": status,
                "advisory_only": True,
                "specialist_required": len(expected_specialists),
                "specialist_received": len(packets),
                "blocker_count": len(set(blockers)),
                "conflict_count": len(conflicts),
                "critical_dissent_count": len(critical_dissent),
            },
            "supported_facts": verified_evidence,
            "unsupported_claims": [],
            "specialist_verdicts": packets,
            "agreements": agreements,
            "conflicts": conflicts,
            "critical_dissent": critical_dissent,
            "risk_engine_result": {
                "decision": "NOT_INVOKED",
                "boundary": "NOT_BYPASSED",
                "final_risk_authority": "RISK_ENGINE",
                "execution_allowed": False,
            },
            "authority_gate_result": authority_result,
            "recommended_options": recommended_options,
            "rejected_options": [
                {
                    "action": action_name,
                    "reason": "EXECUTION_AND_AUTHORITY_ACTIONS_FORBIDDEN",
                }
                for action_name in config["mandatory_forbidden_actions"]
            ],
            "required_human_decision": {
                "required": True,
                "decision": (
                    "REVIEW_BLOCKERS"
                    if status == "BLOCK"
                    else (
                        "REVIEW_DEGRADED_PACKET"
                        if status == "DEGRADED_HUMAN_REVIEW_ONLY"
                        else "HUMAN_REVIEW"
                    )
                ),
            },
            "blockers": sorted(set(blockers)),
            "missing_specialists": missing,
            "model_agreement_is_evidence": False,
            "model_vote_authority": 0,
            "majority_vote_allowed": False,
            "execution_allowed": False,
            "authority": 0,
            "human_approval_required": True,
        }

    except CouncilBlock as exc:
        return blocked_result(
            request_id,
            [str(exc)],
            authority_result,
        )
    except Exception as exc:
        return blocked_result(
            request_id,
            [f"INTERNAL_FAIL_CLOSED:{type(exc).__name__}"],
            authority_result,
        )


__all__ = [
    "CouncilBlock",
    "evaluate_council",
    "strict_json_loads",
]
