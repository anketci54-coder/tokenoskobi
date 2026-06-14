#!/usr/bin/env python3
"""Design-safe runtime path resolver for Phase41.

This module is intentionally inert until imported by a future approved
migration. It performs no writes, no DB access, no network calls, no secret
access, no panel access, and no runtime side effects.
"""

import json
import os
from pathlib import Path


SCHEMA_VERSION = "runtime_paths_v1"

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "runtime_paths_v1.json"
)

REQUIRED_PATH_KEYS = {
    "repo_root",
    "runtime_root",
    "data_dir",
    "sqlite_db",
    "active_panel_dir",
    "active_panel_data",
    "panel_assets_dir",
    "secrets_dir",
    "backups_dir",
    "temp_dir",
    "status_dir",
    "tools_dir",
}

REQUIRED_HOT_PATH_KEYS = {
    "sqlite_db",
    "active_panel_dir",
    "active_panel_data",
    "secrets_dir",
}

REQUIRED_WRITE_CLASSES = {
    "read_only",
    "temp_output",
    "status_output",
    "preview_output",
    "backup_output",
    "secret_output",
    "active_hot_path_output",
}


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _decision(
    ok,
    path_key="",
    path="",
    write_class="",
    reason_codes=None,
    required_controls=None,
    matched_path=None,
    audit=None,
):
    return {
        "ok": bool(ok),
        "decision": "ALLOW" if ok else "DENY",
        "engine": SCHEMA_VERSION,
        "path_key": str(path_key or ""),
        "path": str(path or ""),
        "write_class": str(write_class or ""),
        "reason_codes": list(reason_codes or []),
        "required_controls": list(required_controls or []),
        "matched_path": dict(matched_path or {}),
        "audit": dict(audit or {}),
    }


def load_runtime_paths(path=None):
    """Load runtime_paths_v1.json.

    Missing, unreadable, or invalid JSON config returns a fail-closed object
    instead of raising.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    try:
        with config_path.open("r", encoding="utf-8") as f:
            registry = json.load(f)
    except FileNotFoundError:
        return {
            "ok": False,
            "registry": None,
            "error": "RUNTIME_PATHS_CONFIG_MISSING",
            "path": str(config_path),
        }
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "registry": None,
            "error": "RUNTIME_PATHS_CONFIG_INVALID_JSON",
            "detail": str(exc),
            "path": str(config_path),
        }
    except Exception as exc:
        return {
            "ok": False,
            "registry": None,
            "error": "RUNTIME_PATHS_CONFIG_LOAD_FAILED",
            "detail": str(exc),
            "path": str(config_path),
        }

    return {
        "ok": True,
        "registry": registry,
        "error": "",
        "path": str(config_path),
    }


def validate_runtime_paths(registry):
    """Validate the minimal runtime_paths_v1 contract."""
    errors = []
    warnings = []

    if not isinstance(registry, dict):
        return {
            "ok": False,
            "errors": ["RUNTIME_PATHS_REGISTRY_NOT_OBJECT"],
            "warnings": warnings,
        }

    if registry.get("schema_version") != SCHEMA_VERSION:
        errors.append("RUNTIME_PATHS_SCHEMA_VERSION_MISMATCH")

    for key in ("root_policy", "paths", "write_classes"):
        if not isinstance(registry.get(key), dict):
            errors.append(f"RUNTIME_PATHS_MISSING_{key.upper()}")

    paths = _as_dict(registry.get("paths"))
    for key in REQUIRED_PATH_KEYS:
        if not isinstance(paths.get(key), dict):
            errors.append(f"RUNTIME_PATH_KEY_MISSING:{key}")

    write_classes = _as_dict(registry.get("write_classes"))
    for key in REQUIRED_WRITE_CLASSES:
        if not isinstance(write_classes.get(key), dict):
            errors.append(f"RUNTIME_WRITE_CLASS_MISSING:{key}")

    for key in REQUIRED_HOT_PATH_KEYS:
        entry = _as_dict(paths.get(key))
        if entry.get("hot_path") is not True:
            warnings.append(f"RUNTIME_HOT_PATH_FLAG_MISSING:{key}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _env_value(env, key):
    if env is None:
        return os.environ.get(key)
    if isinstance(env, dict):
        return env.get(key)
    return None


def _normalize_path(value):
    text = str(value or "").strip()
    if not text:
        return ""
    if "\x00" in text:
        return ""
    try:
        return str(Path(text))
    except Exception:
        return ""


def _absolute_path(value):
    text = _normalize_path(value)
    if not text:
        return ""
    try:
        p = Path(text)
    except Exception:
        return ""
    if not p.is_absolute():
        return ""
    return str(p)


def _runtime_root(registry, env=None):
    root_policy = _as_dict(registry.get("root_policy"))
    override = _env_value(env, "TOKENOSKOBI_ROOT")
    if override:
        override_path = _absolute_path(override)
        if not override_path:
            return {
                "ok": False,
                "root": "",
                "used_environment_override": True,
                "error": "TOKENOSKOBI_ROOT_MALFORMED",
            }
        return {
            "ok": True,
            "root": override_path,
            "used_environment_override": True,
            "error": "",
        }

    legacy_root = _absolute_path(root_policy.get("legacy_root"))
    if not legacy_root:
        return {
            "ok": False,
            "root": "",
            "used_environment_override": False,
            "error": "LEGACY_RUNTIME_ROOT_MALFORMED",
        }

    return {
        "ok": True,
        "root": legacy_root,
        "used_environment_override": False,
        "error": "",
    }


def _expand_template(template, resolved):
    text = str(template or "")
    previous = None
    current = text
    for _ in range(20):
        if current == previous:
            break
        previous = current
        for key, value in resolved.items():
            current = current.replace("{" + key + "}", str(value))
    if "{" in current or "}" in current:
        return ""
    return _normalize_path(current)


def _resolve_all_paths(registry, env=None):
    paths = _as_dict(registry.get("paths"))
    root = _runtime_root(registry, env)
    if not root.get("ok"):
        return {
            "ok": False,
            "paths": {},
            "used_environment_override": root.get("used_environment_override", False),
            "error": root.get("error"),
        }

    resolved = {
        "runtime_root": root.get("root"),
    }

    repo_default = _as_dict(paths.get("repo_root")).get("default", ".")
    resolved["repo_root"] = _normalize_path(repo_default)

    order = [
        "data_dir",
        "sqlite_db",
        "public_dir",
        "active_panel_dir",
        "active_panel_data",
        "panel_assets_dir",
        "panel_icons_final_dir",
        "panel_icons_dir",
        "secrets_dir",
        "backups_dir",
        "temp_dir",
        "status_dir",
        "tools_dir",
    ]

    for key in order:
        entry = _as_dict(paths.get(key))
        if not entry:
            continue
        expanded = _expand_template(entry.get("default"), resolved)
        if not expanded:
            return {
                "ok": False,
                "paths": resolved,
                "used_environment_override": root.get("used_environment_override", False),
                "error": f"RUNTIME_PATH_TEMPLATE_UNRESOLVED:{key}",
            }
        resolved[key] = expanded

    return {
        "ok": True,
        "paths": resolved,
        "used_environment_override": root.get("used_environment_override", False),
        "error": "",
    }


def resolve_path(path_key, registry=None, env=None):
    """Resolve a logical path key to its configured path."""
    if registry is None:
        loaded = load_runtime_paths()
        if not loaded.get("ok"):
            return _decision(
                False,
                path_key=path_key,
                reason_codes=[loaded.get("error") or "RUNTIME_PATHS_CONFIG_LOAD_FAILED"],
                required_controls=["valid_runtime_paths_config"],
                audit={"config_path": loaded.get("path", "")},
            )
        registry = loaded.get("registry")

    validation = validate_runtime_paths(registry)
    if not validation.get("ok"):
        return _decision(
            False,
            path_key=path_key,
            reason_codes=validation.get("errors"),
            required_controls=["valid_runtime_paths_config"],
            audit={"warnings": validation.get("warnings", [])},
        )

    key = str(path_key or "").strip()
    paths = _as_dict(registry.get("paths"))
    if key not in paths:
        return _decision(
            False,
            path_key=key,
            reason_codes=[f"RUNTIME_PATH_KEY_UNKNOWN:{key}"],
            required_controls=["known_path_key"],
            audit={"fail_closed": True},
        )

    resolved = _resolve_all_paths(registry, env)
    if not resolved.get("ok"):
        return _decision(
            False,
            path_key=key,
            reason_codes=[resolved.get("error") or "RUNTIME_PATH_RESOLUTION_FAILED"],
            required_controls=["resolvable_runtime_paths"],
            audit={"used_environment_override": resolved.get("used_environment_override", False)},
        )

    path_value = resolved.get("paths", {}).get(key)
    if not path_value:
        return _decision(
            False,
            path_key=key,
            reason_codes=[f"RUNTIME_PATH_NOT_RESOLVED:{key}"],
            required_controls=["resolvable_path_key"],
            audit={"used_environment_override": resolved.get("used_environment_override", False)},
        )

    entry = _as_dict(paths.get(key))
    return _decision(
        True,
        path_key=key,
        path=path_value,
        matched_path={
            "kind": entry.get("kind"),
            "hot_path": bool(entry.get("hot_path")),
            "tracked_in_git": entry.get("tracked_in_git"),
        },
        audit={
            "schema_version": registry.get("schema_version"),
            "used_environment_override": resolved.get("used_environment_override", False),
        },
    )


def _is_same_or_under(path, parent):
    try:
        p = Path(path).resolve(strict=False)
        base = Path(parent).resolve(strict=False)
        return p == base or base in p.parents
    except Exception:
        return False


def classify_path(path, registry=None, env=None):
    """Classify a concrete path without granting write permission."""
    if registry is None:
        loaded = load_runtime_paths()
        if not loaded.get("ok"):
            return _decision(
                False,
                path=path,
                reason_codes=[loaded.get("error") or "RUNTIME_PATHS_CONFIG_LOAD_FAILED"],
                required_controls=["valid_runtime_paths_config"],
            )
        registry = loaded.get("registry")

    validation = validate_runtime_paths(registry)
    if not validation.get("ok"):
        return _decision(
            False,
            path=path,
            reason_codes=validation.get("errors"),
            required_controls=["valid_runtime_paths_config"],
            audit={"warnings": validation.get("warnings", [])},
        )

    target = _normalize_path(path)
    if not target:
        return _decision(
            False,
            path=path,
            reason_codes=["RUNTIME_PATH_MALFORMED"],
            required_controls=["valid_path"],
        )

    resolved = _resolve_all_paths(registry, env)
    if not resolved.get("ok"):
        return _decision(
            False,
            path=target,
            reason_codes=[resolved.get("error") or "RUNTIME_PATH_RESOLUTION_FAILED"],
            required_controls=["resolvable_runtime_paths"],
        )

    resolved_paths = resolved.get("paths", {})
    hot = False
    hot_reason = ""
    matched_key = ""

    for key in REQUIRED_HOT_PATH_KEYS:
        hot_path = resolved_paths.get(key)
        if not hot_path:
            continue
        if target == hot_path:
            hot = True
            hot_reason = f"MATCH:{key}"
            matched_key = key
            break

    if not hot:
        active_panel_dir = resolved_paths.get("active_panel_dir")
        secrets_dir = resolved_paths.get("secrets_dir")
        if active_panel_dir and _is_same_or_under(target, active_panel_dir):
            hot = True
            hot_reason = "UNDER_ACTIVE_PANEL_DIR"
            matched_key = "active_panel_dir"
        elif secrets_dir and _is_same_or_under(target, secrets_dir):
            hot = True
            hot_reason = "UNDER_SECRETS_DIR"
            matched_key = "secrets_dir"

    return _decision(
        True,
        path_key=matched_key,
        path=target,
        matched_path={
            "hot_path": hot,
            "hot_path_reason": hot_reason,
        },
        audit={
            "schema_version": registry.get("schema_version"),
            "used_environment_override": resolved.get("used_environment_override", False),
        },
    )


def is_hot_path(path, registry=None, env=None):
    """Return True when a path is classified as a hot path."""
    classified = classify_path(path, registry=registry, env=env)
    if not classified.get("ok"):
        return True
    return bool(_as_dict(classified.get("matched_path")).get("hot_path"))


def _authority_allows(authority_decision):
    if authority_decision is None:
        return False
    if not isinstance(authority_decision, dict):
        return False
    return authority_decision.get("ok") is True and authority_decision.get("decision") == "ALLOW"


def _policy_allows(policy_decision):
    if policy_decision is None:
        return False
    if not isinstance(policy_decision, dict):
        return False
    return policy_decision.get("ok") is True and policy_decision.get("decision") == "ALLOW"


def validate_write_target(
    path_key=None,
    path=None,
    write_class="read_only",
    authority_decision=None,
    policy_decision=None,
    registry=None,
    env=None,
):
    """Validate a write target class without performing any write."""
    if registry is None:
        loaded = load_runtime_paths()
        if not loaded.get("ok"):
            return _decision(
                False,
                path_key=path_key,
                path=path,
                write_class=write_class,
                reason_codes=[loaded.get("error") or "RUNTIME_PATHS_CONFIG_LOAD_FAILED"],
                required_controls=["valid_runtime_paths_config"],
            )
        registry = loaded.get("registry")

    validation = validate_runtime_paths(registry)
    if not validation.get("ok"):
        return _decision(
            False,
            path_key=path_key,
            path=path,
            write_class=write_class,
            reason_codes=validation.get("errors"),
            required_controls=["valid_runtime_paths_config"],
        )

    write_classes = _as_dict(registry.get("write_classes"))
    cls = str(write_class or "").strip()
    if cls not in write_classes:
        return _decision(
            False,
            path_key=path_key,
            path=path,
            write_class=cls,
            reason_codes=[f"RUNTIME_WRITE_CLASS_UNKNOWN:{cls}"],
            required_controls=["known_write_class"],
        )

    if path_key:
        resolved = resolve_path(path_key, registry=registry, env=env)
        if not resolved.get("ok"):
            resolved["write_class"] = cls
            return resolved
        target_path = resolved.get("path")
        key = str(path_key)
    else:
        target_path = _normalize_path(path)
        key = ""
        if not target_path:
            return _decision(
                False,
                path_key=key,
                path=path,
                write_class=cls,
                reason_codes=["RUNTIME_WRITE_TARGET_MALFORMED"],
                required_controls=["valid_write_target"],
            )

    classified = classify_path(target_path, registry=registry, env=env)
    if not classified.get("ok"):
        classified["write_class"] = cls
        return classified

    hot = bool(_as_dict(classified.get("matched_path")).get("hot_path"))
    class_policy = _as_dict(write_classes.get(cls))
    matched = {
        "write_class": cls,
        "allowed_by_default": class_policy.get("allowed_by_default"),
        "requires_hot_path_check": class_policy.get("requires_hot_path_check"),
        "requires_authority": class_policy.get("requires_authority"),
        "requires_approval": class_policy.get("requires_approval"),
        "requires_rollback": class_policy.get("requires_rollback"),
        "hot_path": hot,
        "hot_path_reason": _as_dict(classified.get("matched_path")).get("hot_path_reason"),
    }

    reasons = []
    required = []

    if cls == "read_only":
        return _decision(
            True,
            path_key=key,
            path=target_path,
            write_class=cls,
            matched_path=matched,
            audit={"schema_version": registry.get("schema_version")},
        )

    if hot and cls != "backup_output":
        reasons.append("HOT_PATH_MUTATION_DENIED")
        required.extend(["authority_allow", "policy_allow", "approval_allow"])

    if cls == "backup_output":
        resolved = _resolve_all_paths(registry, env)
        backups_dir = resolved.get("paths", {}).get("backups_dir") if resolved.get("ok") else ""
        if not backups_dir or not _is_same_or_under(target_path, backups_dir):
            reasons.append("BACKUP_OUTPUT_OUTSIDE_BACKUPS_DIR_DENIED")
            required.append("backups_dir_target")

    if cls in {"secret_output", "active_hot_path_output"}:
        if not _authority_allows(authority_decision):
            reasons.append("AUTHORITY_DECISION_DENIED_OR_MISSING")
            required.append("authority_allow")
        if not _policy_allows(policy_decision):
            reasons.append("POLICY_DECISION_DENIED_OR_MISSING")
            required.append("policy_allow")
        if class_policy.get("requires_approval") is True:
            required.append("approval_allow")
        if class_policy.get("requires_rollback") is True:
            required.append("rollback_plan")

    if class_policy.get("allowed_by_default") is not True and cls not in {"secret_output", "active_hot_path_output"}:
        reasons.append(f"WRITE_CLASS_DENIED_BY_DEFAULT:{cls}")

    if reasons:
        return _decision(
            False,
            path_key=key,
            path=target_path,
            write_class=cls,
            reason_codes=sorted(set(reasons)),
            required_controls=sorted(set(required)),
            matched_path=matched,
            audit={"schema_version": registry.get("schema_version"), "fail_closed": True},
        )

    return _decision(
        True,
        path_key=key,
        path=target_path,
        write_class=cls,
        matched_path=matched,
        audit={"schema_version": registry.get("schema_version"), "fail_closed": True},
    )


def explain_path_decision(decision):
    """Return a short human-readable explanation for a path decision."""
    if not isinstance(decision, dict):
        return "DENY: malformed path decision"

    status = str(decision.get("decision") or "DENY")
    path_key = str(decision.get("path_key") or "")
    path = str(decision.get("path") or "")
    write_class = str(decision.get("write_class") or "")
    reasons = decision.get("reason_codes") or []

    label = path_key or path or "unknown_path"
    if write_class:
        label = f"{label} [{write_class}]"

    if status == "ALLOW":
        return f"ALLOW: path policy permits {label}"
    if reasons:
        return f"DENY: {label} blocked by " + ", ".join(str(r) for r in reasons)
    return f"DENY: {label} blocked by fail-closed path policy"
