#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from core.authority import (
    evaluate_authority,
    load_authority_state,
    validate_authority_state,
)
from core.policy import (
    evaluate_policy,
    load_policy_registry,
    validate_policy_registry,
)

GATE_SCHEMA = "runtime_policy_authority_gate_v1"
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


def _decision(
    ok: bool,
    stage: str,
    reasons: list[str] | None = None,
    matched: dict[str, Any] | None = None,
    baseline_authority: dict[str, Any] | None = None,
    baseline_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": GATE_SCHEMA,
        "ok": bool(ok),
        "decision": "ALLOW" if ok else "DENY",
        "stage": stage,
        "reason_codes": sorted(set(reasons or [])),
        "matched": matched or {},
        "baseline_authority": baseline_authority or {},
        "baseline_policy": baseline_policy or {},
        "fail_closed": True,
    }


def _baseline_engines(
    authority_state: dict[str, Any],
    policy_registry: dict[str, Any],
    stage: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    authority_decision = evaluate_authority(
        {
            "operation_id": f"runtime-gate:{stage}:authority-baseline",
            "operation_type": "read_only",
            "effects": {},
            "target": {"hot_path": False},
        },
        state=authority_state,
    )

    policy_decision = evaluate_policy(
        {
            "operation_id": f"runtime-gate:{stage}:policy-baseline",
            "operation_type": "logging_check",
            "domain": "logging_redaction",
            "mode": "read_only",
            "logging": {
                "prints_secret": False,
                "prints_full_url": False,
                "prints_large_payload": False,
                "fields": [],
            },
        },
        authority_decision=authority_decision,
        approval_decision={"ok": True, "decision": "ALLOW"},
        registry=policy_registry,
    )

    return authority_decision, policy_decision


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
    root_path = Path(
        root
        or os.environ.get("TOKENOSKOBI_ROOT")
        or "/root/tokenoskobi_clean_v1"
    ).resolve()
    env = dict(os.environ if environ is None else environ)
    reasons: list[str] = []
    matched: dict[str, Any] = {
        "root": str(root_path),
        "grant_id": grant_id,
        "service_name": service_name,
        "runner_path": runner_path,
    }

    try:
        authority_loaded = load_authority_state(
            root_path / "config" / "authority_state_v1.json"
        )
        policy_loaded = load_policy_registry(
            root_path / "config" / "project_policy_registry_v1.json"
        )

        if not authority_loaded.get("ok"):
            reasons.append(
                str(authority_loaded.get("error") or "AUTHORITY_CONFIG_LOAD_FAILED")
            )
            return _decision(False, stage, reasons, matched)
        if not policy_loaded.get("ok"):
            reasons.append(
                str(policy_loaded.get("error") or "POLICY_CONFIG_LOAD_FAILED")
            )
            return _decision(False, stage, reasons, matched)

        authority_state = authority_loaded["state"]
        policy_registry = policy_loaded["registry"]

        authority_validation = validate_authority_state(authority_state)
        policy_validation = validate_policy_registry(policy_registry)
        if not authority_validation.get("ok"):
            reasons.extend(authority_validation.get("errors") or [])
        if not policy_validation.get("ok"):
            reasons.extend(policy_validation.get("errors") or [])

        baseline_authority, baseline_policy = _baseline_engines(
            authority_state,
            policy_registry,
            stage,
        )
        if baseline_authority.get("decision") != "ALLOW":
            reasons.append("AUTHORITY_ENGINE_BASELINE_DENIED")
        if baseline_policy.get("decision") != "ALLOW":
            reasons.append("POLICY_ENGINE_BASELINE_DENIED")

        grant_registry = _load_json(
            root_path / "config" / "runtime_stage_grants_v1.json"
        )
        if grant_registry.get("schema_version") != "runtime_stage_grants_v1":
            reasons.append("RUNTIME_GRANT_SCHEMA_MISMATCH")
        if grant_registry.get("deny_unknown_grant") is not True:
            reasons.append("RUNTIME_GRANT_DENY_UNKNOWN_NOT_TRUE")
        if grant_registry.get("deny_unknown_stage") is not True:
            reasons.append("RUNTIME_STAGE_DENY_UNKNOWN_NOT_TRUE")
        if grant_registry.get("no_authority_expansion") is not True:
            reasons.append("RUNTIME_GRANT_AUTHORITY_EXPANSION_NOT_BLOCKED")

        grants = grant_registry.get("grants") or {}
        grant = grants.get(grant_id)
        if not isinstance(grant, dict):
            reasons.append("RUNTIME_GRANT_NOT_FOUND")
            return _decision(
                False,
                stage,
                reasons,
                matched,
                baseline_authority,
                baseline_policy,
            )

        if grant.get("enabled") is not True:
            reasons.append("RUNTIME_GRANT_DISABLED")
        if str(grant.get("service_name") or "") != service_name:
            reasons.append("RUNTIME_SERVICE_IDENTITY_MISMATCH")
        if str(grant.get("runner_path") or "") != runner_path:
            reasons.append("RUNTIME_RUNNER_IDENTITY_MISMATCH")

        stages = grant.get("stages") or {}
        stage_contract = stages.get(stage)
        if not isinstance(stage_contract, dict):
            reasons.append("RUNTIME_STAGE_NOT_GRANTED")
            return _decision(
                False,
                stage,
                reasons,
                matched,
                baseline_authority,
                baseline_policy,
            )

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
        try:
            artifact_path.relative_to(root_path)
        except ValueError:
            reasons.append("AUTHORIZATION_ARTIFACT_OUTSIDE_ROOT")
            artifact_path = root_path / "__invalid__"

        if not artifact_path.is_file():
            reasons.append("AUTHORIZATION_ARTIFACT_MISSING")
        else:
            artifact = _load_json(artifact_path)
            for dotted, expected in (
                grant.get("authorization_requirements") or {}
            ).items():
                try:
                    actual = _lookup(artifact, str(dotted))
                except KeyError:
                    reasons.append(
                        f"AUTHORIZATION_REQUIREMENT_MISSING:{dotted}"
                    )
                    continue
                matched[f"authorization:{dotted}"] = actual
                if actual != expected:
                    reasons.append(
                        f"AUTHORIZATION_REQUIREMENT_MISMATCH:{dotted}"
                    )

        required_env = stage_contract.get("required_environment") or {}
        for key, expected in required_env.items():
            actual = env.get(str(key))
            matched[f"environment:{key}"] = actual
            if actual != str(expected):
                reasons.append(f"RUNTIME_ENVIRONMENT_MISMATCH:{key}")

        matched["stage_mutating"] = bool(stage_contract.get("mutating"))
        matched["stage_effect"] = stage_contract.get("effect")
        matched["authority_engine"] = baseline_authority.get("engine")
        matched["policy_engine"] = baseline_policy.get("engine")

        return _decision(
            not reasons,
            stage,
            reasons,
            matched,
            baseline_authority,
            baseline_policy,
        )

    except Exception as exc:
        reasons.append(f"RUNTIME_GATE_ERROR:{type(exc).__name__}:{exc}")
        return _decision(False, stage, reasons, matched)


def enforce_runtime_stage(stage: str, **kwargs: Any) -> dict[str, Any]:
    return evaluate_runtime_stage(stage, **kwargs)
