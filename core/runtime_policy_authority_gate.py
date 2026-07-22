#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from core.authority import evaluate_authority, load_authority_state, validate_authority_state
from core.policy import evaluate_policy, load_policy_registry, validate_policy_registry

GATE_SCHEMA = "runtime_policy_authority_gate_v2"
DEFAULT_GRANT_ID = "news_radar_refresh_v1"
DEFAULT_SERVICE = "tokenoskobi-news-radar-refresh.service"
DEFAULT_RUNNER = "tools/news_radar_refresh_runner_v1.py"
EXIT_POLICY_AUTHORITY_DENIED = 76


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _lookup(value: Any, dotted: str) -> Any:
    current = value
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted)
        current = current[part]
    return current


def _inside_root(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _decision(ok: bool, stage: str, reasons=None, matched=None, authority=None, policy=None, approval=None) -> dict[str, Any]:
    return {
        "schema": GATE_SCHEMA,
        "ok": bool(ok),
        "decision": "ALLOW" if ok else "DENY",
        "stage": stage,
        "reason_codes": sorted(set(reasons or [])),
        "matched": matched or {},
        "authority": authority or {},
        "policy": policy or {},
        "approval": approval or {},
        "fail_closed": True,
    }


def evaluate_runtime_stage(
    stage: str,
    *,
    root: str | Path | None = None,
    grant_id: str = DEFAULT_GRANT_ID,
    service_name: str = DEFAULT_SERVICE,
    runner_path: str = DEFAULT_RUNNER,
    environ: dict[str, str] | None = None,
    runtime_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root_path = Path(root or os.environ.get("TOKENOSKOBI_ROOT") or "/root/tokenoskobi_clean_v1").resolve()
    env = dict(os.environ if environ is None else environ)
    reasons: list[str] = []
    matched: dict[str, Any] = {
        "root": str(root_path),
        "grant_id": grant_id,
        "service_name": service_name,
        "runner_path": runner_path,
    }
    authority_decision: dict[str, Any] = {}
    policy_decision: dict[str, Any] = {}
    approval_decision: dict[str, Any] = {"ok": False, "decision": "DENY"}

    try:
        if not root_path.is_absolute():
            reasons.append("RUNTIME_ROOT_NOT_ABSOLUTE")
            return _decision(False, stage, reasons, matched)

        runner_abs = (root_path / runner_path).resolve()
        if not _inside_root(root_path, runner_abs):
            reasons.append("RUNTIME_RUNNER_OUTSIDE_ROOT")

        authority_loaded = load_authority_state(root_path / "config/authority_state_v1.json")
        policy_loaded = load_policy_registry(root_path / "config/project_policy_registry_v1.json")
        if not authority_loaded.get("ok"):
            reasons.append(str(authority_loaded.get("error") or "AUTHORITY_CONFIG_LOAD_FAILED"))
            return _decision(False, stage, reasons, matched)
        if not policy_loaded.get("ok"):
            reasons.append(str(policy_loaded.get("error") or "POLICY_CONFIG_LOAD_FAILED"))
            return _decision(False, stage, reasons, matched)

        authority_state = authority_loaded["state"]
        policy_registry = policy_loaded["registry"]
        authority_validation = validate_authority_state(authority_state)
        policy_validation = validate_policy_registry(policy_registry)
        reasons.extend(authority_validation.get("errors") or [])
        reasons.extend(policy_validation.get("errors") or [])

        grant_registry = _load_json(root_path / "config/runtime_stage_grants_v1.json")
        if grant_registry.get("schema_version") != "runtime_stage_grants_v1":
            reasons.append("RUNTIME_GRANT_SCHEMA_MISMATCH")
        if grant_registry.get("deny_unknown_grant") is not True:
            reasons.append("RUNTIME_GRANT_DENY_UNKNOWN_NOT_TRUE")
        if grant_registry.get("deny_unknown_stage") is not True:
            reasons.append("RUNTIME_STAGE_DENY_UNKNOWN_NOT_TRUE")
        if grant_registry.get("no_authority_expansion") is not True:
            reasons.append("RUNTIME_GRANT_AUTHORITY_EXPANSION_NOT_BLOCKED")

        grant = (grant_registry.get("grants") or {}).get(grant_id)
        if not isinstance(grant, dict):
            reasons.append("RUNTIME_GRANT_NOT_FOUND")
            return _decision(False, stage, reasons, matched)
        if grant.get("enabled") is not True:
            reasons.append("RUNTIME_GRANT_DISABLED")
        if str(grant.get("service_name") or "") != service_name:
            reasons.append("RUNTIME_SERVICE_IDENTITY_MISMATCH")
        if str(grant.get("runner_path") or "") != runner_path:
            reasons.append("RUNTIME_RUNNER_IDENTITY_MISMATCH")

        stage_contract = (grant.get("stages") or {}).get(stage)
        if not isinstance(stage_contract, dict):
            reasons.append("RUNTIME_STAGE_NOT_GRANTED")
            return _decision(False, stage, reasons, matched)

        operation_type = str(stage_contract.get("operation_type") or "").strip()
        effects = stage_contract.get("effects")
        target = stage_contract.get("target")
        mutating = bool(stage_contract.get("mutating"))
        if not operation_type:
            reasons.append("RUNTIME_STAGE_OPERATION_TYPE_MISSING")
        if not isinstance(effects, dict):
            reasons.append("RUNTIME_STAGE_EFFECTS_MISSING")
            effects = {}
        if not isinstance(target, dict):
            reasons.append("RUNTIME_STAGE_TARGET_MISSING")
            target = {}
        if mutating and not any(bool(v) for v in effects.values()):
            reasons.append("RUNTIME_MUTATING_STAGE_EFFECTS_EMPTY")
        if not mutating and any(bool(v) for v in effects.values()):
            reasons.append("RUNTIME_READONLY_STAGE_HAS_EFFECTS")

        runtime = runtime_override or _load_json(root_path / "PROJECT_RUNTIME.json")
        for dotted, expected in (grant.get("canonical_requirements") or {}).items():
            try:
                actual = _lookup(runtime, str(dotted))
            except KeyError:
                reasons.append(f"CANONICAL_REQUIREMENT_MISSING:{dotted}")
                continue
            matched[f"canonical:{dotted}"] = actual
            if actual != expected:
                reasons.append(f"CANONICAL_REQUIREMENT_MISMATCH:{dotted}")

        artifact_rel = str(grant.get("authorization_artifact") or "")
        artifact_path = (root_path / artifact_rel).resolve()
        artifact_verified = True
        if not artifact_rel or not _inside_root(root_path, artifact_path):
            reasons.append("AUTHORIZATION_ARTIFACT_OUTSIDE_ROOT")
            artifact_verified = False
        elif not artifact_path.is_file():
            reasons.append("AUTHORIZATION_ARTIFACT_MISSING")
            artifact_verified = False
        else:
            artifact = _load_json(artifact_path)
            for dotted, expected in (grant.get("authorization_requirements") or {}).items():
                try:
                    actual = _lookup(artifact, str(dotted))
                except KeyError:
                    reasons.append(f"AUTHORIZATION_REQUIREMENT_MISSING:{dotted}")
                    artifact_verified = False
                    continue
                matched[f"authorization:{dotted}"] = actual
                if actual != expected:
                    reasons.append(f"AUTHORIZATION_REQUIREMENT_MISMATCH:{dotted}")
                    artifact_verified = False

        approval_required = bool(stage_contract.get("approval_required"))
        approval_ok = (not approval_required) or artifact_verified
        approval_decision = {
            "ok": approval_ok,
            "decision": "ALLOW" if approval_ok else "DENY",
            "source": str(artifact_path) if approval_required else "NOT_REQUIRED",
            "verified": artifact_verified if approval_required else True,
        }
        if not approval_ok:
            reasons.append("HUMAN_APPROVAL_NOT_VERIFIED")

        for key, expected in (stage_contract.get("required_environment") or {}).items():
            actual = env.get(str(key))
            matched[f"environment:{key}"] = actual
            if actual != str(expected):
                reasons.append(f"RUNTIME_ENVIRONMENT_MISMATCH:{key}")
            if str(key).endswith("_PATH") and actual:
                if not _inside_root(root_path, Path(actual)):
                    reasons.append(f"RUNTIME_PATH_OUTSIDE_ROOT:{key}")

        authority_decision = evaluate_authority(
            {
                "operation_id": f"runtime-gate:{stage}",
                "operation_type": operation_type,
                "effects": effects,
                "target": target,
            },
            state=authority_state,
        )
        if authority_decision.get("decision") != "ALLOW":
            reasons.append("AUTHORITY_ENGINE_DENIED_STAGE")
            reasons.extend(authority_decision.get("reason_codes") or [])

        policy_decision = evaluate_policy(
            {
                "operation_id": f"runtime-gate:{stage}:policy",
                "operation_type": operation_type,
                "domain": "runtime_mutation" if mutating else "logging_redaction",
                "mode": "mutating" if mutating else "read_only",
                "logging": {
                    "prints_secret": False,
                    "prints_full_url": False,
                    "prints_large_payload": False,
                    "fields": [],
                },
            },
            authority_decision=authority_decision,
            approval_decision=approval_decision,
            registry=policy_registry,
        )
        if policy_decision.get("decision") != "ALLOW":
            reasons.append("POLICY_ENGINE_DENIED_STAGE")
            reasons.extend(policy_decision.get("reason_codes") or [])

        matched.update({
            "stage_mutating": mutating,
            "operation_type": operation_type,
            "effects": effects,
            "target": target,
        })
        return _decision(not reasons, stage, reasons, matched, authority_decision, policy_decision, approval_decision)
    except Exception as exc:
        reasons.append(f"RUNTIME_GATE_ERROR:{type(exc).__name__}:{exc}")
        return _decision(False, stage, reasons, matched, authority_decision, policy_decision, approval_decision)


def enforce_runtime_stage(stage: str, **kwargs: Any) -> dict[str, Any]:
    return evaluate_runtime_stage(stage, **kwargs)
