
import base64
import copy
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)

from core.research_consensus_policy import (
    assess_claim,
    assess_report,
)
from core.research_content_quarantine import (
    quarantine,
    synthesis_envelope,
    validate_capabilities,
)
from core.research_evidence_ledger import (
    append_evidence,
    canonical_bytes,
)
from core.research_execution_firewall import (
    validate_execution_input,
    validate_research_report,
)
from core.research_safety_governor import (
    DEFAULT_POLICY,
    evaluate_iteration,
    validate_adversarial_context,
)

REQUEST_SCHEMA = "era57_deep_isolation_runtime_request_v3"
RESULT_SCHEMA = "era57_deep_isolation_runtime_result_v3"

LOCK_PROTOCOL = (
    "GLOBAL_RESERVE_RELEASE__"
    "SESSION_RESERVE_RELEASE__"
    "BOUNDED_PROCESS_NO_GLOBAL_LOCK__"
    "SESSION_COMMIT_RELEASE__"
    "GLOBAL_RECONCILE_RELEASE"
)

CANONICAL_EVIDENCE_REUSE = False
SIGNED_REGISTRY_MANIFEST_REQUIRED_BEFORE_EXTERNAL_BINDING = True
CURRENT_REGISTRY_AUTHENTICATION = "HASH_PIN_ONLY"
PRODUCTION_TRUST_ROOT_VERIFIED = False

TRUST_ROOT_DIRECTORY = Path(
    "/root/.tokenoskobi/trust"
)
PUBLIC_KEY_PATH = (
    TRUST_ROOT_DIRECTORY
    / "era57f5_authority_public_ed25519.pem"
)
PUBLIC_KEY_FINGERPRINT_PATH = (
    TRUST_ROOT_DIRECTORY
    / "era57f5_authority_public_fingerprint.sha256"
)
SIGNED_MANIFEST_PATH = Path(
    "/root/tokenoskobi_clean_v1/config/"
    "research_runtime_signed_manifest_v1.json"
)
SIGNED_MANIFEST_SIGNATURE_PATH = Path(
    "/root/tokenoskobi_clean_v1/config/"
    "research_runtime_signed_manifest_v1.sig"
)
AUDIT_STORE_PATH = Path(
    "/root/.tokenoskobi/audit/"
    "era57_research_security_audit_chain_v1.jsonl"
)

MANIFEST_SCHEMA = (
    "tokenoskobi_era57_signed_runtime_manifest_v1"
)
CAPABILITY_SCHEMA = (
    "tokenoskobi_era57_critical_capability_v1"
)
CAPABILITY_AUDIENCE = (
    "TOKENOSKOBI_ERA57_RUNTIME"
)
MINIMUM_MANIFEST_SEQUENCE = 1
CAPABILITY_MAX_LIFETIME_SECONDS = 300
CAPABILITY_CLOCK_SKEW_SECONDS = 10

SIGNED_REGISTRY_MANIFEST = True
CRITICAL_CAPABILITY_REQUIRED = True
AUDIT_STORE_APPEND_ONLY = True
AUDIT_STORE_HASH_CHAINED = True
AUDIT_PUBLIC_READER_EXPOSED = False
AUDIT_PUBLIC_CLEAR_EXPOSED = False

SAME_PROCESS_ARBITRARY_CODE_ISOLATION = False
ROOT_TAMPER_RESISTANCE_VERIFIED = False
OS_PROCESS_ISOLATION_VERIFIED = False


class _AuditIntegrityError(RuntimeError):
    pass


class _AppendOnlyAuditStore:
    def __init__(
        self,
        path,
        max_bytes,
    ):
        self._path = Path(path)
        self._max_bytes = int(max_bytes)
        self._lock = threading.RLock()
        self._sequence = 0
        self._last_hash = "0" * 64
        self._expected_size = 0
        self._fd = None

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
            mode=0o700,
        )

        if not self._path.exists():
            self._path.touch(mode=0o600)

        os.chmod(self._path, 0o600)
        self._verify_existing()

        self._fd = os.open(
            str(self._path),
            os.O_APPEND
            | os.O_WRONLY
            | os.O_CLOEXEC,
        )

    def __del__(self):
        descriptor = getattr(
            self,
            "_fd",
            None,
        )

        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass

            self._fd = None

    def _verify_existing(self):
        previous_hash = "0" * 64
        sequence = 0

        data = self._path.read_bytes()

        for raw_line in data.splitlines():
            if not raw_line.strip():
                continue

            record = json.loads(
                raw_line.decode("utf-8")
            )

            if not isinstance(record, dict):
                raise _AuditIntegrityError(
                    "AUDIT_RECORD_NOT_OBJECT"
                )

            if record.get("sequence") != sequence:
                raise _AuditIntegrityError(
                    "AUDIT_SEQUENCE_INVALID"
                )

            if record.get(
                "previous_hash"
            ) != previous_hash:
                raise _AuditIntegrityError(
                    "AUDIT_PREVIOUS_HASH_INVALID"
                )

            event = record.get("event")

            body = {
                "sequence": sequence,
                "previous_hash":
                    previous_hash,
                "event": event,
            }

            expected_hash = _sha256(
                _canonical(body)
            )

            if record.get(
                "entry_hash"
            ) != expected_hash:
                raise _AuditIntegrityError(
                    "AUDIT_ENTRY_HASH_INVALID"
                )

            previous_hash = expected_hash
            sequence += 1

        self._sequence = sequence
        self._last_hash = previous_hash
        self._expected_size = len(data)

    def healthy(self):
        with self._lock:
            if self._fd is None:
                return False

            try:
                stat = os.fstat(self._fd)
            except OSError:
                return False

            return (
                stat.st_nlink > 0
                and stat.st_size
                == self._expected_size
            )

    def append(self, event):
        with self._lock:
            if not self.healthy():
                raise _AuditIntegrityError(
                    "AUDIT_STORE_HEALTH_FAILURE"
                )

            body = {
                "sequence":
                    self._sequence,
                "previous_hash":
                    self._last_hash,
                "event":
                    copy.deepcopy(event),
            }

            entry_hash = _sha256(
                _canonical(body)
            )

            record = dict(body)
            record["entry_hash"] = (
                entry_hash
            )

            line = (
                _canonical(record)
                + b"\n"
            )

            if (
                self._expected_size
                + len(line)
                > self._max_bytes
            ):
                raise _AuditIntegrityError(
                    "AUDIT_STORE_QUOTA_EXCEEDED"
                )

            written = os.write(
                self._fd,
                line,
            )

            if written != len(line):
                raise _AuditIntegrityError(
                    "AUDIT_PARTIAL_WRITE"
                )

            os.fsync(self._fd)

            self._expected_size += len(line)
            self._sequence += 1
            self._last_hash = entry_hash

            return {
                "sequence":
                    self._sequence - 1,
                "entry_hash":
                    entry_hash,
            }


def _decode_base64(value):
    if not isinstance(value, str):
        raise ValueError(
            "BASE64_STRING_REQUIRED"
        )

    return base64.b64decode(
        value.encode("ascii"),
        validate=True,
    )


def _load_manifest_bundle():
    public_pem = PUBLIC_KEY_PATH.read_bytes()
    public_key = (
        serialization.load_pem_public_key(
            public_pem
        )
    )

    if not isinstance(
        public_key,
        Ed25519PublicKey,
    ):
        raise RuntimeError(
            "TRUST_ANCHOR_NOT_ED25519"
        )

    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=(
            serialization.PublicFormat
            .SubjectPublicKeyInfo
        ),
    )

    fingerprint = _sha256(public_der)
    expected_fingerprint = (
        PUBLIC_KEY_FINGERPRINT_PATH
        .read_text(encoding="utf-8")
        .strip()
    )

    if fingerprint != expected_fingerprint:
        raise RuntimeError(
            "PUBLIC_KEY_FINGERPRINT_MISMATCH"
        )

    manifest = json.loads(
        SIGNED_MANIFEST_PATH
        .read_text(encoding="utf-8")
    )

    signature = _decode_base64(
        SIGNED_MANIFEST_SIGNATURE_PATH
        .read_text(encoding="utf-8")
        .strip()
    )

    public_key.verify(
        signature,
        _canonical(manifest),
    )

    now = int(time.time())

    required = {
        "schema",
        "sequence",
        "issued_at_epoch",
        "expires_at_epoch",
        "audience",
        "registry_sha256",
        "runtime_policy_sha256",
        "task_policy_sha256",
        "public_key_fingerprint_sha256",
    }

    if set(manifest) != required:
        raise RuntimeError(
            "SIGNED_MANIFEST_SCHEMA_FIELDS_INVALID"
        )

    if manifest["schema"] != MANIFEST_SCHEMA:
        raise RuntimeError(
            "SIGNED_MANIFEST_SCHEMA_INVALID"
        )

    sequence = manifest["sequence"]

    if (
        isinstance(sequence, bool)
        or not isinstance(sequence, int)
        or sequence
        < MINIMUM_MANIFEST_SEQUENCE
    ):
        raise RuntimeError(
            "SIGNED_MANIFEST_ROLLBACK_SEQUENCE"
        )

    issued_at = manifest[
        "issued_at_epoch"
    ]
    expires_at = manifest[
        "expires_at_epoch"
    ]

    if (
        isinstance(issued_at, bool)
        or isinstance(expires_at, bool)
        or not isinstance(issued_at, int)
        or not isinstance(expires_at, int)
        or issued_at
        > now + CAPABILITY_CLOCK_SKEW_SECONDS
        or expires_at <= now
        or expires_at <= issued_at
    ):
        raise RuntimeError(
            "SIGNED_MANIFEST_TIME_INVALID"
        )

    if manifest["audience"] != (
        CAPABILITY_AUDIENCE
    ):
        raise RuntimeError(
            "SIGNED_MANIFEST_AUDIENCE_INVALID"
        )

    if manifest[
        "registry_sha256"
    ] != _PINNED_REGISTRY_SHA256:
        raise RuntimeError(
            "SIGNED_MANIFEST_REGISTRY_HASH_MISMATCH"
        )

    if manifest[
        "runtime_policy_sha256"
    ] != _PINNED_POLICY_SHA256:
        raise RuntimeError(
            "SIGNED_MANIFEST_POLICY_HASH_MISMATCH"
        )

    if manifest[
        "task_policy_sha256"
    ] != _PINNED_TASK_POLICY_SHA256:
        raise RuntimeError(
            "SIGNED_MANIFEST_TASK_POLICY_HASH_MISMATCH"
        )

    if manifest[
        "public_key_fingerprint_sha256"
    ] != fingerprint:
        raise RuntimeError(
            "SIGNED_MANIFEST_KEY_FINGERPRINT_MISMATCH"
        )

    return public_key, manifest, fingerprint

def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

PINNED_TRUSTED_SOURCE_REGISTRY = {
    "source-a": {
        "active": True,
        "verified_independent": True,
        "independence_group": "group-a",
        "source_uri": "https://example.com/source-a",
    },
    "source-b": {
        "active": True,
        "verified_independent": True,
        "independence_group": "group-b",
        "source_uri": "https://example.com/source-b",
    },
}

PINNED_RUNTIME_POLICY = {
    "max_sessions": 32,
    "max_normal_sessions": 28,
    "max_critical_sessions": 4,
    "max_raw_bytes": 1048576,
    "max_claims": 32,
    "max_unknowns": 32,
    "max_contradictions": 32,
    "max_report_sources": 100,
    "max_model_outputs": 100,
    "max_evidence_items": 100,
    "max_nested_depth": 12,
    "max_total_nodes": 5000,
    "max_total_string_bytes": 1500000,
    "ledger_quota_bytes": 1000000,
    "ledger_max_entries": 100,

    "session_max_iterations": 8,
    "session_max_tokens": 250000,
    "session_max_cost_units": 5000,
    "session_max_wall_seconds": 3600,
    "session_max_sources": 64,
    "session_max_duplicate_fingerprint": 16,
    "session_max_no_gain_streak": 16,

    "normal_global_max_iterations": 32,
    "normal_global_max_tokens": 2000000,
    "normal_global_max_cost_units": 50000,
    "normal_global_max_wall_seconds": 7200,
    "normal_global_max_sources": 1000,

    "critical_reserved_max_iterations": 8,
    "critical_reserved_max_tokens": 500000,
    "critical_reserved_max_cost_units": 10000,
    "critical_reserved_max_wall_seconds": 1800,
    "critical_reserved_max_sources": 200,

    "audit_store_max_bytes": 67108864,
}

TRUSTED_TASK_CLASSES = frozenset({
    "SYSTEM_MAINTENANCE",
    "EMERGENCY_RECOVERY",
    "SECURITY_AUDIT",
    "CANONICAL_HEALTH_CHECK",
})

_PINNED_REGISTRY_JSON = _canonical(
    PINNED_TRUSTED_SOURCE_REGISTRY
)
_PINNED_REGISTRY_SHA256 = _sha256(
    _PINNED_REGISTRY_JSON
)

_PINNED_POLICY_JSON = _canonical(
    PINNED_RUNTIME_POLICY
)
_PINNED_POLICY_SHA256 = _sha256(
    _PINNED_POLICY_JSON
)

_PINNED_TASK_POLICY_JSON = _canonical(
    sorted(TRUSTED_TASK_CLASSES)
)
_PINNED_TASK_POLICY_SHA256 = _sha256(
    _PINNED_TASK_POLICY_JSON
)

REQUIRED_FIELDS = frozenset({
    "schema",
    "session_id",
    "session_sequence",
    "raw",
    "mime",
    "source_id",
    "source_uri",
    "source_observed_at",
    "now_utc",
    "report",
    "model_outputs",
    "evidence_items",
    "capabilities",
})

ALLOWED_FIELDS = REQUIRED_FIELDS | {
    "declared_as_of",
}

CLAIM_FIELDS = frozenset({
    "claim_id",
    "claim_text",
    "claim_version",
})

EVIDENCE_FIELDS = frozenset({
    "claim_id",
    "claim_text",
    "claim_version",
    "source_id",
    "source_uri",
    "raw_sha256",
    "normalized_sha256",
    "supports",
    "contradicts",
})

def _base(
    ok,
    decision,
    stage,
    reasons,
):
    return {
        "schema": RESULT_SCHEMA,
        "ok": bool(ok),
        "decision": decision,
        "stage": stage,
        "reason_codes": sorted(set(reasons)),
        "runtime_binding":
            "LOCAL_IN_MEMORY_DEEP_ISOLATION_READ_ONLY",
        "network_access": False,
        "database_mutation": False,
        "file_mutation": False,
        "production_access": False,
        "external_runtime_binding": False,
        "actionable": False,
        "decision_eligible": False,
        "execution_eligible": False,
        "trade_eligible": False,
        "wallet_eligible": False,
        "signing_eligible": False,
        "order_create_eligible": False,
        "human_review_required": True,
        "audit_payload_redacted": True,
        "fail_closed": True,
    }

def _generic_reject(
    correlation_id=None,
):
    value = _base(
        False,
        "FAIL_CLOSED",
        "REQUEST_REJECTED",
        ["REQUEST_REJECTED"],
    )
    value["correlation_id"] = (
        correlation_id
        if correlation_id is not None
        else secrets.token_hex(16)
    )
    return value

def _metrics(value):
    stack = [(value, 1)]
    nodes = 0
    depth = 0
    string_bytes = 0

    while stack:
        current, current_depth = stack.pop()
        nodes += 1
        depth = max(depth, current_depth)

        if isinstance(current, str):
            string_bytes += len(
                current.encode("utf-8")
            )

        elif isinstance(current, dict):
            for key, item in current.items():
                string_bytes += len(
                    str(key).encode("utf-8")
                )
                stack.append(
                    (item, current_depth + 1)
                )

        elif isinstance(current, list):
            for item in current:
                stack.append(
                    (item, current_depth + 1)
                )

    return {
        "nodes": nodes,
        "depth": depth,
        "string_bytes": string_bytes,
    }

class BoundedResearchRuntime:
    def __init__(self):
        if _sha256(_PINNED_REGISTRY_JSON) != \
                _PINNED_REGISTRY_SHA256:
            raise RuntimeError(
                "PINNED_REGISTRY_INTEGRITY_FAILURE"
            )

        if _sha256(_PINNED_POLICY_JSON) != \
                _PINNED_POLICY_SHA256:
            raise RuntimeError(
                "PINNED_RUNTIME_POLICY_INTEGRITY_FAILURE"
            )

        if _sha256(_PINNED_TASK_POLICY_JSON) != \
                _PINNED_TASK_POLICY_SHA256:
            raise RuntimeError(
                "PINNED_TASK_POLICY_INTEGRITY_FAILURE"
            )

        (
            self._public_key,
            self._signed_manifest,
            self._public_key_fingerprint,
        ) = _load_manifest_bundle()

        self._manifest_sequence = (
            self._signed_manifest[
                "sequence"
            ]
        )

        self._registry_json = bytes(
            _PINNED_REGISTRY_JSON
        )
        self._registry_hash = (
            _PINNED_REGISTRY_SHA256
        )

        self._runtime_policy_json = bytes(
            _PINNED_POLICY_JSON
        )
        self._runtime_policy_hash = (
            _PINNED_POLICY_SHA256
        )

        self._task_policy_json = bytes(
            _PINNED_TASK_POLICY_JSON
        )
        self._task_policy_hash = (
            _PINNED_TASK_POLICY_SHA256
        )

        self._boot_id = secrets.token_hex(32)
        self._session_binding_key = (
            secrets.token_bytes(32)
        )

        self._global_lock = threading.RLock()

        self._sessions = {}
        self._closed_sessions = set()
        self._used_capability_nonces = set()
        self._audit_failed = False

        self._audit_store = (
            _AppendOnlyAuditStore(
                AUDIT_STORE_PATH,
                self._runtime_policy()[
                    "audit_store_max_bytes"
                ],
            )
        )

        self._global_usage = {
            "normal": {
                "iterations": 0,
                "tokens": 0,
                "cost_units": 0,
                "wall_seconds": 0,
                "sources": 0,
            },
            "critical": {
                "iterations": 0,
                "tokens": 0,
                "cost_units": 0,
                "wall_seconds": 0,
                "sources": 0,
            },
        }

    @property
    def boot_id(self):
        return self._boot_id

    @property
    def registry_hash(self):
        return self._registry_hash

    @property
    def policy_hash(self):
        return self._runtime_policy_hash

    @property
    def task_policy_hash(self):
        return self._task_policy_hash

    @property
    def manifest_sequence(self):
        return self._manifest_sequence

    @property
    def public_key_fingerprint(self):
        return self._public_key_fingerprint

    def _runtime_policy(self):
        return json.loads(
            self._runtime_policy_json
        )

    def _registry(self):
        return json.loads(
            self._registry_json
        )

    def registry_snapshot(self):
        return self._registry()

    def global_snapshot(self):
        with self._global_lock:
            normal_sessions = sum(
                session["task_class"]
                == "NORMAL_RESEARCH"
                for session in
                self._sessions.values()
            )
            critical_sessions = (
                len(self._sessions)
                - normal_sessions
            )

            return {
                "normal": copy.deepcopy(
                    self._global_usage["normal"]
                ),
                "critical": copy.deepcopy(
                    self._global_usage["critical"]
                ),
                "active_sessions":
                    len(self._sessions),
                "normal_sessions":
                    normal_sessions,
                "critical_sessions":
                    critical_sessions,
                "normal_session_limit":
                    self._runtime_policy()[
                        "max_normal_sessions"
                    ],
                "critical_session_limit":
                    self._runtime_policy()[
                        "max_critical_sessions"
                    ],
                "absolute_session_limit":
                    self._runtime_policy()[
                        "max_sessions"
                    ],
                "fingerprint_counts_global":
                    False,
                "no_gain_streak_global":
                    False,
                "critical_reserved_capacity":
                    True,
                "signed_manifest":
                    True,
                "manifest_sequence":
                    self._manifest_sequence,
                "public_audit_reader":
                    False,
                "public_audit_clear":
                    False,
            }

    def _request_digest(self, request):
        if not isinstance(request, dict):
            return _sha256(
                b"NON_OBJECT_REQUEST"
            )

        raw = request.get("raw")
        raw_hash = (
            _sha256(raw)
            if isinstance(raw, bytes)
            else None
        )

        report = request.get("report")
        report_id = (
            report.get("report_id")
            if isinstance(report, dict)
            else None
        )

        metadata = {
            "schema": request.get("schema"),
            "source_id_hash": _sha256(
                str(
                    request.get("source_id", "")
                ).encode("utf-8")
            ),
            "source_uri_hash": _sha256(
                str(
                    request.get("source_uri", "")
                ).encode("utf-8")
            ),
            "report_id_hash": _sha256(
                str(report_id).encode("utf-8")
            ),
            "raw_sha256": raw_hash,
        }

        return _sha256(_canonical(metadata))

    def _record_reject(
        self,
        internal_stage,
        internal_reasons,
        request=None,
        session=None,
    ):
        correlation_id = secrets.token_hex(16)

        session_id = (
            session.get("session_id")
            if isinstance(session, dict)
            else None
        )

        session_pseudonym = (
            _sha256(
                session_id.encode("utf-8")
            )[:16]
            if isinstance(session_id, str)
            else None
        )

        event = {
            "correlation_id": correlation_id,
            "internal_stage":
                str(internal_stage),
            "internal_reason_codes": sorted({
                str(item)
                for item in internal_reasons
            }),
            "request_digest":
                self._request_digest(request),
            "session_pseudonym":
                session_pseudonym,
            "manifest_sequence":
                self._manifest_sequence,
            "policy_hash":
                self._runtime_policy_hash,
            "registry_hash":
                self._registry_hash,
            "task_policy_hash":
                self._task_policy_hash,
            "timestamp_ns":
                time.time_ns(),
            "raw_payload_logged": False,
            "secret_payload_logged": False,
        }

        try:
            self._audit_store.append(event)
        except Exception:
            self._audit_failed = True

        return correlation_id

    def _reject(
        self,
        internal_stage,
        internal_reasons,
        request=None,
        session=None,
    ):
        correlation_id = self._record_reject(
            internal_stage,
            internal_reasons,
            request=request,
            session=session,
        )
        return _generic_reject(correlation_id)

    def _new_governor_state(self):
        return {
            "iterations": 0,
            "total_tokens": 0,
            "total_cost_units": 0,
            "wall_seconds": 0,
            "source_count": 0,
            "fingerprint_counts": {},
            "no_gain_streak": 0,
        }

    def _session_governor_policy(
        self,
        task_class,
    ):
        runtime_policy = self._runtime_policy()
        policy = dict(DEFAULT_POLICY)

        if task_class == "NORMAL_RESEARCH":
            prefix = "session"
        else:
            prefix = "session"

        policy.update({
            "max_iterations":
                runtime_policy[
                    prefix + "_max_iterations"
                ],
            "max_total_tokens":
                runtime_policy[
                    prefix + "_max_tokens"
                ],
            "max_total_cost_units":
                runtime_policy[
                    prefix + "_max_cost_units"
                ],
            "max_wall_seconds":
                runtime_policy[
                    prefix + "_max_wall_seconds"
                ],
            "max_sources":
                runtime_policy[
                    prefix + "_max_sources"
                ],
            "max_duplicate_fingerprint":
                runtime_policy[
                    prefix +
                    "_max_duplicate_fingerprint"
                ],
            "max_no_gain_streak":
                runtime_policy[
                    prefix +
                    "_max_no_gain_streak"
                ],
        })

        return policy

    def _task_class_binding(
        self,
        session_id,
        task_class,
    ):
        payload = _canonical({
            "session_id": session_id,
            "task_class": task_class,
            "boot_id": self._boot_id,
            "manifest_sequence":
                self._manifest_sequence,
        })

        return hmac.new(
            self._session_binding_key,
            payload,
            hashlib.sha256,
        ).hexdigest()

    def _decode_critical_capability(
        self,
        token,
    ):
        if not isinstance(token, str):
            raise ValueError(
                "CAPABILITY_TOKEN_STRING_REQUIRED"
            )

        envelope = json.loads(token)

        if (
            not isinstance(envelope, dict)
            or set(envelope)
            != {"payload", "signature"}
        ):
            raise ValueError(
                "CAPABILITY_ENVELOPE_INVALID"
            )

        payload_bytes = _decode_base64(
            envelope["payload"]
        )
        signature = _decode_base64(
            envelope["signature"]
        )

        self._public_key.verify(
            signature,
            payload_bytes,
        )

        payload = json.loads(
            payload_bytes.decode("utf-8")
        )

        required = {
            "schema",
            "audience",
            "boot_id",
            "manifest_sequence",
            "task_class",
            "nonce",
            "issued_at_epoch",
            "expires_at_epoch",
        }

        if set(payload) != required:
            raise ValueError(
                "CAPABILITY_FIELDS_INVALID"
            )

        if payload["schema"] != (
            CAPABILITY_SCHEMA
        ):
            raise ValueError(
                "CAPABILITY_SCHEMA_INVALID"
            )

        if payload["audience"] != (
            CAPABILITY_AUDIENCE
        ):
            raise ValueError(
                "CAPABILITY_AUDIENCE_INVALID"
            )

        if payload["boot_id"] != (
            self._boot_id
        ):
            raise ValueError(
                "CAPABILITY_BOOT_EPOCH_MISMATCH"
            )

        if payload[
            "manifest_sequence"
        ] != self._manifest_sequence:
            raise ValueError(
                "CAPABILITY_MANIFEST_SEQUENCE_MISMATCH"
            )

        task_class = payload[
            "task_class"
        ]

        if task_class not in (
            TRUSTED_TASK_CLASSES
        ):
            raise ValueError(
                "CAPABILITY_TASK_CLASS_INVALID"
            )

        nonce = payload["nonce"]

        if (
            not isinstance(nonce, str)
            or len(nonce) != 64
            or any(
                character not in
                "0123456789abcdef"
                for character in nonce
            )
        ):
            raise ValueError(
                "CAPABILITY_NONCE_INVALID"
            )

        issued_at = payload[
            "issued_at_epoch"
        ]
        expires_at = payload[
            "expires_at_epoch"
        ]
        now = int(time.time())

        if (
            isinstance(issued_at, bool)
            or isinstance(expires_at, bool)
            or not isinstance(issued_at, int)
            or not isinstance(expires_at, int)
            or issued_at
            > now
            + CAPABILITY_CLOCK_SKEW_SECONDS
            or expires_at < now
            or expires_at <= issued_at
            or expires_at - issued_at
            > CAPABILITY_MAX_LIFETIME_SECONDS
        ):
            raise ValueError(
                "CAPABILITY_TIME_INVALID"
            )

        return payload

    def open_session(self):
        return self._open_session(
            "NORMAL_RESEARCH",
            capability_nonce=None,
        )

    def open_critical_session(
        self,
        capability_token,
    ):
        try:
            payload = (
                self._decode_critical_capability(
                    capability_token
                )
            )
        except (
            ValueError,
            TypeError,
            json.JSONDecodeError,
            InvalidSignature,
        ) as exc:
            return self._reject(
                "CRITICAL_CAPABILITY_GATE",
                [
                    "CRITICAL_CAPABILITY_REJECTED:"
                    + type(exc).__name__
                ],
            )

        return self._open_session(
            payload["task_class"],
            capability_nonce=payload[
                "nonce"
            ],
        )

    def _open_session(
        self,
        task_class,
        capability_nonce,
    ):
        with self._global_lock:
            policy = self._runtime_policy()

            normal_sessions = sum(
                session["task_class"]
                == "NORMAL_RESEARCH"
                for session in
                self._sessions.values()
            )
            critical_sessions = (
                len(self._sessions)
                - normal_sessions
            )

            if len(self._sessions) >= (
                policy["max_sessions"]
            ):
                return self._reject(
                    "SESSION_OPEN",
                    [
                        "ABSOLUTE_SESSION_LIMIT_REACHED"
                    ],
                )

            if task_class == (
                "NORMAL_RESEARCH"
            ):
                if normal_sessions >= (
                    policy[
                        "max_normal_sessions"
                    ]
                ):
                    return self._reject(
                        "SESSION_OPEN",
                        [
                            "NORMAL_SESSION_LIMIT_REACHED"
                        ],
                    )
            else:
                if capability_nonce is None:
                    return self._reject(
                        "SESSION_OPEN",
                        [
                            "CRITICAL_CAPABILITY_REQUIRED"
                        ],
                    )

                if capability_nonce in (
                    self._used_capability_nonces
                ):
                    return self._reject(
                        "SESSION_OPEN",
                        [
                            "CRITICAL_CAPABILITY_REPLAYED"
                        ],
                    )

                if critical_sessions >= (
                    policy[
                        "max_critical_sessions"
                    ]
                ):
                    return self._reject(
                        "SESSION_OPEN",
                        [
                            "CRITICAL_SESSION_LIMIT_REACHED"
                        ],
                    )

            session_id = secrets.token_hex(32)

            task_binding = (
                self._task_class_binding(
                    session_id,
                    task_class,
                )
            )

            session = {
                "session_id": session_id,
                "boot_id": self._boot_id,
                "sequence": 0,
                "task_class": task_class,
                "task_class_binding":
                    task_binding,
                "task_policy_hash":
                    self._task_policy_hash,
                "policy_hash":
                    self._runtime_policy_hash,
                "registry_hash":
                    self._registry_hash,
                "manifest_sequence":
                    self._manifest_sequence,
                "governor_state":
                    self._new_governor_state(),
                "ledger_entries": [],
                "ledger_bytes": 0,
                "evidence_by_context": {},
                "report_sources": {},
                "source_fingerprints": {},
                "busy": False,
                "global_inflight": 0,
                "closed": False,
                "lock": threading.RLock(),
            }

            if capability_nonce is not None:
                self._used_capability_nonces.add(
                    capability_nonce
                )

            self._sessions[session_id] = session

        value = _base(
            True,
            "SESSION_OPENED",
            "SESSION_OPEN",
            [],
        )
        value.update({
            "session_id": session_id,
            "boot_id": self._boot_id,
            "next_sequence": 0,
            "task_class": task_class,
            "critical_session":
                task_class
                != "NORMAL_RESEARCH",
            "registry_hash":
                self._registry_hash,
            "policy_hash":
                self._runtime_policy_hash,
            "task_policy_hash":
                self._task_policy_hash,
            "manifest_sequence":
                self._manifest_sequence,
            "signed_manifest": True,
            "a30_persistent_recovery":
                False,
        })
        return value

    def close_session(
        self,
        session_id,
    ):
        with self._global_lock:
            session = self._sessions.get(
                session_id
            )

            if session is None:
                return self._reject(
                    "SESSION_CLOSE",
                    ["SESSION_NOT_FOUND"],
                )

            if session["global_inflight"] > 0:
                return self._reject(
                    "SESSION_CLOSE",
                    ["SESSION_BUSY"],
                    session=session,
                )

            self._sessions.pop(
                session_id,
                None,
            )
            self._closed_sessions.add(
                session_id
            )

            if len(self._closed_sessions) > 1024:
                self._closed_sessions.pop()

        with session["lock"]:
            session["closed"] = True
            session["busy"] = False
            session["ledger_entries"].clear()
            session["evidence_by_context"].clear()
            session["report_sources"].clear()
            session["source_fingerprints"].clear()

        value = _base(
            True,
            "SESSION_CLOSED",
            "SESSION_CLOSE",
            [],
        )
        value["session_id"] = session_id
        return value

    def session_snapshot(
        self,
        session_id,
    ):
        with self._global_lock:
            session = self._sessions.get(
                session_id
            )

        if session is None:
            return self._reject(
                "SESSION_SNAPSHOT",
                ["SESSION_NOT_FOUND"],
            )

        with session["lock"]:
            root_hash = (
                session["ledger_entries"][-1][
                    "entry_hash"
                ]
                if session["ledger_entries"]
                else "0" * 64
            )

            value = _base(
                True,
                "SESSION_SNAPSHOT",
                "SESSION_SNAPSHOT",
                [],
            )
            value.update({
                "session_id": session_id,
                "boot_id": session["boot_id"],
                "task_class":
                    session["task_class"],
                "next_sequence":
                    session["sequence"],
                "busy": session["busy"],
                "ledger_entry_count":
                    len(
                        session[
                            "ledger_entries"
                        ]
                    ),
                "ledger_bytes":
                    session["ledger_bytes"],
                "ledger_root_hash":
                    root_hash,
                "evidence_context_count":
                    len(
                        session[
                            "evidence_by_context"
                        ]
                    ),
                "report_context_count":
                    len(
                        session[
                            "report_sources"
                        ]
                    ),
                "source_count":
                    len(
                        session[
                            "source_fingerprints"
                        ]
                    ),
                "governor_state":
                    copy.deepcopy(
                        session[
                            "governor_state"
                        ]
                    ),
                "raw_content_retained": False,
                "canonical_evidence_reuse":
                    False,
            })
            return value

    def _shape_reasons(
        self,
        request,
    ):
        if not isinstance(request, dict):
            return ["REQUEST_OBJECT_REQUIRED"]

        reasons = []

        reasons.extend(
            "MISSING_FIELD:" + key
            for key in sorted(
                REQUIRED_FIELDS - set(request)
            )
        )
        reasons.extend(
            "UNEXPECTED_FIELD:" + key
            for key in sorted(
                set(request) - ALLOWED_FIELDS
            )
        )

        if request.get("schema") != \
                REQUEST_SCHEMA:
            reasons.append(
                "REQUEST_SCHEMA_MISMATCH"
            )

        session_id = request.get(
            "session_id"
        )

        if (
            not isinstance(session_id, str)
            or len(session_id) != 64
            or any(
                character not in
                "0123456789abcdef"
                for character in session_id
            )
        ):
            reasons.append(
                "SESSION_ID_INVALID"
            )

        sequence = request.get(
            "session_sequence"
        )

        if (
            isinstance(sequence, bool)
            or not isinstance(sequence, int)
            or sequence < 0
        ):
            reasons.append(
                "SESSION_SEQUENCE_INVALID"
            )

        policy = self._runtime_policy()
        raw = request.get("raw")

        if not isinstance(raw, bytes):
            reasons.append(
                "RAW_BYTES_REQUIRED"
            )
        elif len(raw) > \
                policy["max_raw_bytes"]:
            reasons.append(
                "RAW_BYTE_LIMIT_EXCEEDED"
            )

        for key in (
            "mime",
            "source_id",
            "source_uri",
            "source_observed_at",
            "now_utc",
        ):
            value = request.get(key)

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                reasons.append(
                    "NONEMPTY_STRING_REQUIRED:" +
                    key
                )

        declared = request.get(
            "declared_as_of"
        )

        if declared is not None and (
            not isinstance(declared, str)
            or not declared.strip()
        ):
            reasons.append(
                "DECLARED_AS_OF_INVALID"
            )

        report = request.get("report")

        if not isinstance(report, dict):
            reasons.append(
                "REPORT_OBJECT_REQUIRED"
            )
            report = {}

        for key in (
            "report_id",
            "research_question",
        ):
            value = report.get(key)

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                reasons.append(
                    "REPORT_STRING_REQUIRED:" +
                    key
                )

        report_version = report.get(
            "report_version"
        )

        if (
            isinstance(report_version, bool)
            or not isinstance(
                report_version,
                int,
            )
            or report_version < 1
        ):
            reasons.append(
                "REPORT_VERSION_INVALID"
            )

        collection_limits = {
            "claims":
                policy["max_claims"],
            "unknowns":
                policy["max_unknowns"],
            "contradictions":
                policy[
                    "max_contradictions"
                ],
            "sources":
                policy[
                    "max_report_sources"
                ],
        }

        for key, limit in \
                collection_limits.items():
            value = report.get(key)

            if not isinstance(value, list):
                reasons.append(
                    "REPORT_LIST_REQUIRED:" +
                    key
                )
            elif len(value) > limit:
                reasons.append(
                    "REPORT_COLLECTION_LIMIT_EXCEEDED:" +
                    key
                )

        claims = report.get("claims")

        if isinstance(claims, list):
            if not claims:
                reasons.append(
                    "CLAIMS_REQUIRED"
                )

            claim_ids = []

            for index, claim in enumerate(
                claims
            ):
                if not isinstance(claim, dict):
                    reasons.append(
                        "CLAIM_OBJECT_REQUIRED:" +
                        str(index)
                    )
                    continue

                unexpected = (
                    set(claim) -
                    CLAIM_FIELDS
                )

                if unexpected:
                    reasons.extend(
                        "UNEXPECTED_CLAIM_FIELD:" +
                        key
                        for key in sorted(
                            unexpected
                        )
                    )

                claim_id = claim.get(
                    "claim_id"
                )
                claim_text = claim.get(
                    "claim_text"
                )
                claim_version = claim.get(
                    "claim_version"
                )

                if (
                    not isinstance(
                        claim_id,
                        str,
                    )
                    or not claim_id.strip()
                ):
                    reasons.append(
                        "CLAIM_ID_INVALID"
                    )
                else:
                    claim_ids.append(
                        claim_id.strip()
                    )

                if (
                    not isinstance(
                        claim_text,
                        str,
                    )
                    or not claim_text.strip()
                ):
                    reasons.append(
                        "CLAIM_TEXT_INVALID"
                    )

                if (
                    isinstance(
                        claim_version,
                        bool,
                    )
                    or not isinstance(
                        claim_version,
                        int,
                    )
                    or claim_version < 1
                ):
                    reasons.append(
                        "CLAIM_VERSION_INVALID"
                    )

            if len(claim_ids) != \
                    len(set(claim_ids)):
                reasons.append(
                    "DUPLICATE_CLAIM_ID"
                )

        model_outputs = request.get(
            "model_outputs"
        )

        if not isinstance(
            model_outputs,
            list,
        ):
            reasons.append(
                "MODEL_OUTPUT_LIST_REQUIRED"
            )
        elif len(model_outputs) > \
                policy[
                    "max_model_outputs"
                ]:
            reasons.append(
                "MODEL_OUTPUT_LIMIT_EXCEEDED"
            )

        evidence_items = request.get(
            "evidence_items"
        )

        if not isinstance(
            evidence_items,
            list,
        ):
            reasons.append(
                "EVIDENCE_ITEM_LIST_REQUIRED"
            )
        elif len(evidence_items) > \
                policy[
                    "max_evidence_items"
                ]:
            reasons.append(
                "EVIDENCE_ITEM_LIMIT_EXCEEDED"
            )
        else:
            for index, item in enumerate(
                evidence_items
            ):
                if not isinstance(item, dict):
                    reasons.append(
                        "EVIDENCE_ITEM_OBJECT_REQUIRED:" +
                        str(index)
                    )
                    continue

                unexpected = (
                    set(item) -
                    EVIDENCE_FIELDS
                )

                if unexpected:
                    reasons.extend(
                        "UNEXPECTED_EVIDENCE_FIELD:" +
                        key
                        for key in sorted(
                            unexpected
                        )
                    )

        if not isinstance(
            request.get("capabilities"),
            dict,
        ):
            reasons.append(
                "CAPABILITY_OBJECT_REQUIRED"
            )

        metrics = _metrics(request)

        if metrics["depth"] > \
                policy["max_nested_depth"]:
            reasons.append(
                "MAX_NESTED_DEPTH_EXCEEDED"
            )

        if metrics["nodes"] > \
                policy["max_total_nodes"]:
            reasons.append(
                "MAX_TOTAL_NODES_EXCEEDED"
            )

        if metrics["string_bytes"] > \
                policy[
                    "max_total_string_bytes"
                ]:
            reasons.append(
                "MAX_TOTAL_STRING_BYTES_EXCEEDED"
            )

        return sorted(set(reasons))

    def _semantic_context(
        self,
        report,
    ):
        report_id = report[
            "report_id"
        ].strip()
        report_version = report[
            "report_version"
        ]
        question = report[
            "research_question"
        ].strip()

        question_hash = _sha256(
            question.encode("utf-8")
        )

        claims = []
        claims_by_id = {}

        for claim in report["claims"]:
            claim_id = claim[
                "claim_id"
            ].strip()
            claim_text = claim[
                "claim_text"
            ].strip()
            claim_version = claim[
                "claim_version"
            ]

            claim_text_hash = _sha256(
                claim_text.encode("utf-8")
            )

            context_payload = {
                "report_id": report_id,
                "report_version":
                    report_version,
                "research_question_hash":
                    question_hash,
                "claim_id": claim_id,
                "claim_text_hash":
                    claim_text_hash,
                "claim_version":
                    claim_version,
            }

            context_hash = _sha256(
                _canonical(context_payload)
            )

            value = {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "claim_text_hash":
                    claim_text_hash,
                "claim_version":
                    claim_version,
                "claim_context_hash":
                    context_hash,
            }

            claims.append(value)
            claims_by_id[claim_id] = value

        report_context_hash = _sha256(
            _canonical({
                "report_id": report_id,
                "report_version":
                    report_version,
                "research_question_hash":
                    question_hash,
                "claim_context_hashes": [
                    item[
                        "claim_context_hash"
                    ]
                    for item in claims
                ],
            })
        )

        return {
            "report_id": report_id,
            "report_version":
                report_version,
            "research_question_hash":
                question_hash,
            "report_context_hash":
                report_context_hash,
            "claims": claims,
            "claims_by_id":
                claims_by_id,
        }

    def _estimate_resources(
        self,
        request,
        semantic,
    ):
        claims = semantic["claims"]
        model_outputs = request[
            "model_outputs"
        ]
        evidence_items = request[
            "evidence_items"
        ]

        return {
            "iterations": 1,
            "tokens": max(
                1,
                (len(request["raw"]) + 3)
                // 4
                + len(claims) * 24
                + len(model_outputs) * 20
                + len(evidence_items) * 40,
            ),
            "cost_units": max(
                1,
                len(claims)
                + len(model_outputs)
                + len(evidence_items),
            ),
            "wall_seconds": 1,
            "sources": 1,
        }

    def _global_limits(
        self,
        task_class,
    ):
        policy = self._runtime_policy()

        if task_class == \
                "NORMAL_RESEARCH":
            prefix = "normal_global"
            bucket = "normal"
        else:
            prefix = "critical_reserved"
            bucket = "critical"

        return bucket, {
            "iterations":
                policy[
                    prefix +
                    "_max_iterations"
                ],
            "tokens":
                policy[
                    prefix +
                    "_max_tokens"
                ],
            "cost_units":
                policy[
                    prefix +
                    "_max_cost_units"
                ],
            "wall_seconds":
                policy[
                    prefix +
                    "_max_wall_seconds"
                ],
            "sources":
                policy[
                    prefix +
                    "_max_sources"
                ],
        }

    def _reserve_global(
        self,
        session,
        estimate,
    ):
        with self._global_lock:
            current = self._sessions.get(
                session["session_id"]
            )

            if (
                current is not session
                or session["closed"]
            ):
                return None, [
                    "SESSION_NOT_FOUND_OR_CLOSED"
                ]

            bucket, limits = (
                self._global_limits(
                    session["task_class"]
                )
            )
            usage = self._global_usage[
                bucket
            ]

            reasons = []

            for key, value in \
                    estimate.items():
                if usage[key] + value > \
                        limits[key]:
                    reasons.append(
                        "GLOBAL_" +
                        key.upper() +
                        "_LIMIT_EXCEEDED"
                    )

            if reasons:
                return None, reasons

            for key, value in \
                    estimate.items():
                usage[key] += value

            session["global_inflight"] += 1

            return {
                "bucket": bucket,
                "estimate":
                    dict(estimate),
            }, []

    def _rollback_global(
        self,
        session,
        reservation,
    ):
        with self._global_lock:
            usage = self._global_usage[
                reservation["bucket"]
            ]

            for key, value in \
                    reservation[
                        "estimate"
                    ].items():
                usage[key] = max(
                    0,
                    usage[key] - value,
                )

            session["global_inflight"] = max(
                0,
                session[
                    "global_inflight"
                ] - 1,
            )

    def _finish_global(
        self,
        session,
    ):
        with self._global_lock:
            session["global_inflight"] = max(
                0,
                session[
                    "global_inflight"
                ] - 1,
            )

    def _reserve_session(
        self,
        session,
        request,
        work_fingerprint,
        source_binding_fingerprint,
        estimate,
    ):
        with session["lock"]:
            reasons = []

            if session["closed"]:
                reasons.append(
                    "SESSION_CLOSED"
                )

            if session["busy"]:
                reasons.append(
                    "SESSION_BUSY"
                )

            if session["boot_id"] != \
                    self._boot_id:
                reasons.append(
                    "BOOT_EPOCH_MISMATCH"
                )

            if session["policy_hash"] != \
                    self._runtime_policy_hash:
                reasons.append(
                    "RUNTIME_POLICY_HASH_MISMATCH"
                )

            if session["registry_hash"] != \
                    self._registry_hash:
                reasons.append(
                    "REGISTRY_HASH_MISMATCH"
                )

            if session["task_policy_hash"] != \
                    self._task_policy_hash:
                reasons.append(
                    "TASK_POLICY_HASH_MISMATCH"
                )

            if session.get(
                "manifest_sequence"
            ) != self._manifest_sequence:
                reasons.append(
                    "MANIFEST_SEQUENCE_MISMATCH"
                )

            expected_task_binding = (
                self._task_class_binding(
                    session["session_id"],
                    session["task_class"],
                )
            )

            actual_task_binding = (
                session.get(
                    "task_class_binding",
                    "",
                )
            )

            if not hmac.compare_digest(
                str(actual_task_binding),
                expected_task_binding,
            ):
                reasons.append(
                    "TASK_CLASS_BINDING_MISMATCH"
                )

            if request[
                "session_sequence"
            ] != session["sequence"]:
                reasons.append(
                    "STALE_OR_REPLAYED_SESSION_SEQUENCE"
                )

            previous_binding = (
                session[
                    "source_fingerprints"
                ].get(
                    request["source_id"]
                )
            )

            if (
                previous_binding is not None
                and previous_binding !=
                source_binding_fingerprint
            ):
                reasons.append(
                    "SOURCE_ID_CONTENT_REBIND_REJECTED"
                )

            if reasons:
                return False, reasons

            governor_request = {
                "estimated_tokens":
                    estimate["tokens"],
                "estimated_cost_units":
                    estimate["cost_units"],
                "wall_seconds_delta":
                    estimate["wall_seconds"],
                "new_sources": (
                    0
                    if request["source_id"]
                    in session[
                        "source_fingerprints"
                    ]
                    else 1
                ),
                "fingerprint":
                    work_fingerprint,
                "expected_gain_delta": (
                    0
                    if work_fingerprint
                    in session[
                        "governor_state"
                    ]["fingerprint_counts"]
                    else 1
                ),
                "paid_api_requested":
                    False,
            }

            governed = evaluate_iteration(
                session["governor_state"],
                governor_request,
                self._session_governor_policy(
                    session["task_class"]
                ),
            )

            if governed.get("ok") is not True:
                return False, (
                    governed.get(
                        "reason_codes",
                        [
                            "SESSION_GOVERNOR_REJECTED"
                        ],
                    )
                )

            session["governor_state"] = (
                governed["updated_state"]
            )
            session["sequence"] += 1
            session["busy"] = True

            return True, []

    def _finish_session(
        self,
        session,
    ):
        with session["lock"]:
            session["busy"] = False

    def run(
        self,
        request,
    ):
        session = None
        reservation = None
        global_reserved = False
        session_reserved = False

        try:
            if (
                self._audit_failed
                or not self._audit_store.healthy()
            ):
                return _generic_reject()

            reasons = self._shape_reasons(
                request
            )

            if reasons:
                return self._reject(
                    "REQUEST_VALIDATION",
                    reasons,
                    request=request,
                )

            session_id = request[
                "session_id"
            ]

            with self._global_lock:
                session = self._sessions.get(
                    session_id
                )

            if session is None:
                return self._reject(
                    "SESSION_GATE",
                    [
                        "SESSION_NOT_FOUND_OR_RESTARTED"
                    ],
                    request=request,
                )

            registry = self._registry()
            source_id = request[
                "source_id"
            ]
            source_meta = registry.get(
                source_id
            )

            if (
                not isinstance(
                    source_meta,
                    dict,
                )
                or source_meta.get(
                    "active"
                ) is not True
                or source_meta.get(
                    "verified_independent"
                ) is not True
            ):
                return self._reject(
                    "TRUSTED_SOURCE_GATE",
                    ["TRUSTED_SOURCE_NOT_FOUND"],
                    request=request,
                    session=session,
                )

            canonical_uri = str(
                source_meta.get(
                    "source_uri"
                ) or ""
            )

            if request["source_uri"] != \
                    canonical_uri:
                return self._reject(
                    "TRUSTED_SOURCE_GATE",
                    [
                        "SOURCE_URI_REGISTRY_MISMATCH"
                    ],
                    request=request,
                    session=session,
                )

            semantic = self._semantic_context(
                request["report"]
            )

            raw_sha256 = _sha256(
                request["raw"]
            )

            source_binding_fingerprint = (
                _sha256(
                    _canonical({
                        "source_id": source_id,
                        "raw_sha256":
                            raw_sha256,
                    })
                )
            )

            work_fingerprint = _sha256(
                _canonical({
                    "source_id": source_id,
                    "raw_sha256":
                        raw_sha256,
                    "report_context_hash":
                        semantic[
                            "report_context_hash"
                        ],
                })
            )

            estimate = self._estimate_resources(
                request,
                semantic,
            )

            reservation, global_reasons = (
                self._reserve_global(
                    session,
                    estimate,
                )
            )

            if reservation is None:
                return self._reject(
                    "GLOBAL_RESOURCE_GOVERNOR",
                    global_reasons,
                    request=request,
                    session=session,
                )

            global_reserved = True

            reserved, session_reasons = (
                self._reserve_session(
                    session,
                    request,
                    work_fingerprint,
                    source_binding_fingerprint,
                    estimate,
                )
            )

            if not reserved:
                self._rollback_global(
                    session,
                    reservation,
                )
                global_reserved = False

                return self._reject(
                    "SESSION_RESOURCE_GOVERNOR",
                    session_reasons,
                    request=request,
                    session=session,
                )

            session_reserved = True

            def reserved_reject(
                stage,
                internal_reasons,
            ):
                nonlocal global_reserved
                nonlocal session_reserved

                if session_reserved:
                    self._finish_session(
                        session
                    )
                    session_reserved = False

                if global_reserved:
                    self._finish_global(
                        session
                    )
                    global_reserved = False

                return self._reject(
                    stage,
                    internal_reasons,
                    request=request,
                    session=session,
                )

            capability = validate_capabilities(
                request["capabilities"]
            )

            if capability.get("ok") is not True:
                return reserved_reject(
                    "CAPABILITY_GATE",
                    capability.get(
                        "reason_codes",
                        [
                            "CAPABILITY_GATE_FAILED"
                        ],
                    ),
                )

            quarantined = quarantine(
                request["raw"],
                request["mime"],
                request["source_uri"],
            )

            if quarantined.get("ok") is not True:
                return reserved_reject(
                    "CONTENT_QUARANTINE",
                    quarantined.get(
                        "reason_codes",
                        [
                            "CONTENT_QUARANTINE_FAILED"
                        ],
                    ),
                )

            synthesis = synthesis_envelope(
                quarantined,
                request["capabilities"],
            )

            if synthesis.get("ok") is not True:
                return reserved_reject(
                    "SYNTHESIS_ENVELOPE",
                    synthesis.get(
                        "reason_codes",
                        [
                            "SYNTHESIS_ENVELOPE_FAILED"
                        ],
                    ),
                )

            context = validate_adversarial_context(
                synthesis["content"],
                request[
                    "source_observed_at"
                ],
                request["now_utc"],
                request.get(
                    "declared_as_of"
                ),
            )

            if context.get("ok") is not True:
                return reserved_reject(
                    "ADVERSARIAL_CONTEXT",
                    context.get(
                        "reason_codes",
                        [
                            "ADVERSARIAL_CONTEXT_FAILED"
                        ],
                    ),
                )

            firewall_report = copy.deepcopy(
                request["report"]
            )
            firewall_report.pop(
                "report_version",
                None,
            )
            firewall_report["claims"] = [
                item[
                    "claim_context_hash"
                ]
                for item in semantic[
                    "claims"
                ]
            ]

            report_validation = (
                validate_research_report(
                    firewall_report
                )
            )

            if report_validation.get(
                "ok"
            ) is not True:
                return reserved_reject(
                    "RESEARCH_REPORT_SCHEMA",
                    report_validation.get(
                        "reason_codes",
                        [
                            "REPORT_SCHEMA_FAILED"
                        ],
                    ),
                )

            execution = validate_execution_input(
                firewall_report
            )

            if execution.get("ok") is True:
                return reserved_reject(
                    "EXECUTION_FIREWALL",
                    [
                        "EXECUTION_FIREWALL_BYPASS"
                    ],
                )

            quarantine_content = (
                quarantined["content"]
            )
            normalized_sha256 = (
                quarantine_content[
                    "normalized_sha256"
                ]
            )

            trusted_evidence = []

            for item in request[
                "evidence_items"
            ]:
                claim_id = item.get(
                    "claim_id"
                )
                claim_meta = semantic[
                    "claims_by_id"
                ].get(claim_id)

                if claim_meta is None:
                    return reserved_reject(
                        "EVIDENCE_BINDING",
                        [
                            "EVIDENCE_CLAIM_NOT_FOUND"
                        ],
                    )

                binding_ok = (
                    item.get("claim_text")
                        == claim_meta[
                            "claim_text"
                        ]
                    and item.get(
                        "claim_version"
                    ) == claim_meta[
                        "claim_version"
                    ]
                    and item.get(
                        "source_id"
                    ) == source_id
                    and item.get(
                        "source_uri"
                    ) == request[
                        "source_uri"
                    ]
                    and item.get(
                        "raw_sha256"
                    ) == quarantine_content[
                        "raw_sha256"
                    ]
                    and item.get(
                        "normalized_sha256"
                    ) == normalized_sha256
                )

                if not binding_ok:
                    return reserved_reject(
                        "EVIDENCE_BINDING",
                        [
                            "EVIDENCE_SOURCE_OR_SEMANTIC_BINDING_MISMATCH"
                        ],
                    )

                supports = (
                    item.get("supports")
                    is True
                )
                contradicts = (
                    item.get("contradicts")
                    is True
                )

                if supports == contradicts:
                    return reserved_reject(
                        "EVIDENCE_BINDING",
                        [
                            "EVIDENCE_STANCE_INVALID"
                        ],
                    )

                trusted_evidence.append({
                    "claim_id":
                        claim_meta[
                            "claim_context_hash"
                        ],
                    "original_claim_id":
                        claim_meta[
                            "claim_id"
                        ],
                    "claim_text_hash":
                        claim_meta[
                            "claim_text_hash"
                        ],
                    "claim_version":
                        claim_meta[
                            "claim_version"
                        ],
                    "report_context_hash":
                        semantic[
                            "report_context_hash"
                        ],
                    "independence_key":
                        source_id,
                    "verified": True,
                    "supports": supports,
                    "contradicts":
                        contradicts,
                    "source_id": source_id,
                    "source_uri":
                        request["source_uri"],
                    "raw_sha256":
                        quarantine_content[
                            "raw_sha256"
                        ],
                    "normalized_sha256":
                        normalized_sha256,
                    "content_fingerprint":
                        context[
                            "content_fingerprint"
                        ],
                    "registry_hash":
                        self._registry_hash,
                })

            with session["lock"]:
                evidence_snapshot = (
                    copy.deepcopy(
                        session[
                            "evidence_by_context"
                        ]
                    )
                )
                report_source_snapshot = (
                    copy.deepcopy(
                        session[
                            "report_sources"
                        ]
                    )
                )
                ledger_snapshot = (
                    copy.deepcopy(
                        session[
                            "ledger_entries"
                        ]
                    )
                )
                ledger_bytes_snapshot = (
                    session["ledger_bytes"]
                )

            accumulated_by_context = {}

            for claim in semantic["claims"]:
                context_hash = claim[
                    "claim_context_hash"
                ]

                accumulated = list(
                    evidence_snapshot.get(
                        context_hash,
                        [],
                    )
                )

                existing_keys = {
                    (
                        evidence.get(
                            "source_id"
                        ),
                        evidence.get(
                            "raw_sha256"
                        ),
                        evidence.get(
                            "supports"
                        ),
                        evidence.get(
                            "contradicts"
                        ),
                    )
                    for evidence in accumulated
                }

                for evidence in \
                        trusted_evidence:
                    if evidence[
                        "claim_id"
                    ] != context_hash:
                        continue

                    key = (
                        evidence.get(
                            "source_id"
                        ),
                        evidence.get(
                            "raw_sha256"
                        ),
                        evidence.get(
                            "supports"
                        ),
                        evidence.get(
                            "contradicts"
                        ),
                    )

                    if key not in existing_keys:
                        accumulated.append(
                            evidence
                        )
                        existing_keys.add(key)

                accumulated_by_context[
                    context_hash
                ] = accumulated

            claim_assessments = []

            for claim in semantic["claims"]:
                context_hash = claim[
                    "claim_context_hash"
                ]

                assessment = assess_claim(
                    context_hash,
                    request[
                        "model_outputs"
                    ],
                    accumulated_by_context[
                        context_hash
                    ],
                    source_registry=registry,
                )

                if assessment.get("ok") is not True:
                    return reserved_reject(
                        "CLAIM_ASSESSMENT",
                        assessment.get(
                            "reason_codes",
                            [
                                "CLAIM_ASSESSMENT_FAILED"
                            ],
                        ),
                    )

                claim_assessments.append(
                    assessment
                )

            report_context_hash = semantic[
                "report_context_hash"
            ]

            current_report_sources = set(
                report_source_snapshot.get(
                    report_context_hash,
                    [],
                )
            )
            current_report_sources.add(
                source_id
            )

            report_sources = request[
                "report"
            ].get("sources", [])

            sources_bound = all(
                isinstance(item, str)
                and item in
                current_report_sources
                for item in report_sources
            )

            all_claims_supported = (
                bool(semantic["claims"])
                and len(claim_assessments)
                == len(semantic["claims"])
                and all(
                    item.get(
                        "evidence_consensus"
                    ) is True
                    for item in
                    claim_assessments
                )
            )

            derived_complete = (
                request["report"].get(
                    "status"
                ) in {
                    "COMPLETED_VERIFIED",
                    "COMPLETED_WITH_LIMITATIONS",
                }
                and request["report"].get(
                    "unknowns"
                ) == []
                and request["report"].get(
                    "contradictions"
                ) == []
                and sources_bound
                and all_claims_supported
                and not context.get(
                    "adversarial_indicators",
                    [],
                )
            )

            report_assessment = assess_report(
                {
                    "status":
                        request["report"][
                            "status"
                        ],
                    "complete":
                        derived_complete,
                    "claims": [
                        item[
                            "claim_context_hash"
                        ]
                        for item in
                        semantic["claims"]
                    ],
                    "contradictions":
                        request["report"].get(
                            "contradictions",
                            [],
                        ),
                },
                claim_assessments,
            )

            evidence_payload = {
                "schema":
                    "era57_deep_isolation_evidence_v3",
                "boot_id":
                    self._boot_id,
                "session_id":
                    session_id,
                "session_sequence":
                    request[
                        "session_sequence"
                    ],
                "task_class":
                    session[
                        "task_class"
                    ],
                "report_id":
                    semantic["report_id"],
                "report_version":
                    semantic[
                        "report_version"
                    ],
                "report_context_hash":
                    report_context_hash,
                "research_question_hash":
                    semantic[
                        "research_question_hash"
                    ],
                "claim_context_hashes": [
                    item[
                        "claim_context_hash"
                    ]
                    for item in
                    semantic["claims"]
                ],
                "source_id":
                    source_id,
                "source_uri":
                    request["source_uri"],
                "source_observed_at":
                    request[
                        "source_observed_at"
                    ],
                "raw_sha256":
                    quarantine_content[
                        "raw_sha256"
                    ],
                "normalized_sha256":
                    normalized_sha256,
                "content_fingerprint":
                    context[
                        "content_fingerprint"
                    ],
                "registry_hash":
                    self._registry_hash,
                "runtime_policy_hash":
                    self._runtime_policy_hash,
                "task_policy_hash":
                    self._task_policy_hash,
                "derived_report_complete":
                    derived_complete,
                "claim_assessments":
                    claim_assessments,
                "report_assessment":
                    report_assessment,
                "canonical_evidence_reuse":
                    False,
                "actionable": False,
                "execution_eligible": False,
                "human_review_required": True,
            }

            policy = self._runtime_policy()

            ledger = append_evidence(
                ledger_snapshot,
                evidence_payload,
                ledger_bytes_snapshot,
                policy[
                    "ledger_quota_bytes"
                ],
                policy[
                    "ledger_max_entries"
                ],
            )

            if ledger.get("ok") is not True:
                capacity = (
                    ledger.get("capacity")
                    or {}
                )
                ledger_reasons = (
                    ledger.get(
                        "reason_codes"
                    )
                    or capacity.get(
                        "reason_codes",
                        [
                            "EVIDENCE_LEDGER_FAILED"
                        ],
                    )
                )

                return reserved_reject(
                    "EVIDENCE_LEDGER",
                    ledger_reasons,
                )

            new_entries = (
                ledger_snapshot +
                [ledger["entry"]]
            )

            actual_ledger_bytes = sum(
                len(canonical_bytes(item))
                for item in new_entries
            )

            if actual_ledger_bytes > \
                    policy[
                        "ledger_quota_bytes"
                    ]:
                return reserved_reject(
                    "EVIDENCE_LEDGER",
                    [
                        "ACTUAL_LEDGER_BYTE_QUOTA_EXCEEDED"
                    ],
                )

            with session["lock"]:
                for context_hash, values in \
                        accumulated_by_context.items():
                    session[
                        "evidence_by_context"
                    ][context_hash] = values

                session[
                    "report_sources"
                ][report_context_hash] = sorted(
                    current_report_sources
                )

                session[
                    "source_fingerprints"
                ][source_id] = (
                    source_binding_fingerprint
                )

                session[
                    "ledger_entries"
                ] = new_entries
                session[
                    "ledger_bytes"
                ] = actual_ledger_bytes
                session["busy"] = False

            session_reserved = False

            self._finish_global(session)
            global_reserved = False

            quality_passed = (
                report_assessment.get(
                    "research_quality_gate_passed"
                ) is True
                and derived_complete
            )

            value = _base(
                True,
                (
                    "RESEARCH_QUALITY_PASS_NON_ACTIONABLE"
                    if quality_passed
                    else "RESEARCH_NON_ACTIONABLE"
                ),
                "COMPLETE",
                [],
            )

            value.update({
                "session_id":
                    session_id,
                "boot_id":
                    self._boot_id,
                "next_sequence":
                    session["sequence"],
                "task_class":
                    session["task_class"],
                "critical_session":
                    session["task_class"]
                    != "NORMAL_RESEARCH",
                "research_quality_gate_passed":
                    quality_passed,
                "derived_report_complete":
                    derived_complete,
                "report_context_hash":
                    report_context_hash,
                "claim_context_hashes": [
                    item[
                        "claim_context_hash"
                    ]
                    for item in
                    semantic["claims"]
                ],
                "canonical_evidence_reuse":
                    False,
                "truthfulness_guaranteed":
                    False,
                "instruction_authority":
                    False,
                "adversarial_indicators":
                    context.get(
                        "adversarial_indicators",
                        [],
                    ),
                "execution_firewall_rejected":
                    execution.get("ok")
                    is False,
                "ledger_sequence":
                    ledger["entry"][
                        "sequence_number"
                    ],
                "ledger_root_hash":
                    ledger["entry"][
                        "entry_hash"
                    ],
                "ledger_bytes":
                    actual_ledger_bytes,
                "ledger_persisted":
                    False,
                "state_persisted":
                    False,
                "registry_authentication":
                    "ED25519_SIGNED_MANIFEST",
                "signed_registry_manifest":
                    True,
                "manifest_sequence":
                    self._manifest_sequence,
                "public_key_fingerprint":
                    self._public_key_fingerprint,
                "a30_persistent_recovery":
                    False,
                "fail_closed_after_restart":
                    True,
                "lock_protocol":
                    LOCK_PROTOCOL,
            })

            return value

        except Exception as exc:
            if session_reserved and \
                    session is not None:
                self._finish_session(session)
                session_reserved = False

            if global_reserved and \
                    session is not None:
                self._finish_global(session)
                global_reserved = False

            return self._reject(
                "UNHANDLED_EXCEPTION",
                [
                    "FAIL_CLOSED_EXCEPTION:" +
                    type(exc).__name__
                ],
                request=request,
                session=session,
            )

def run_bounded_research(request):
    return _generic_reject()
