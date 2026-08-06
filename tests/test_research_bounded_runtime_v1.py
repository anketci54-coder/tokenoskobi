
import base64
import copy
import hashlib
import json
import os
import secrets
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

import runtime.core.runtime_research_bounded_v1 as runtime_module

from core.research_content_quarantine import (
    DISABLED_CAPABILITIES,
    quarantine,
)
from core.research_execution_firewall import (
    RESEARCH_SCHEMA,
)
from runtime.core.runtime_research_bounded_v1 import (
    AUDIT_STORE_PATH,
    BoundedResearchRuntime,
    CAPABILITY_AUDIENCE,
    CAPABILITY_SCHEMA,
    MANIFEST_SCHEMA,
    REQUEST_SCHEMA,
    SIGNED_MANIFEST_PATH,
    SIGNED_MANIFEST_SIGNATURE_PATH,
    run_bounded_research,
)

PRIVATE_KEY_PATH = Path(
    "/root/.tokenoskobi/trust/"
    "era57f5_authority_private_ed25519.pem"
)

def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

def private_key():
    value = (
        serialization.load_pem_private_key(
            PRIVATE_KEY_PATH.read_bytes(),
            password=None,
        )
    )

    if not isinstance(
        value,
        Ed25519PrivateKey,
    ):
        raise RuntimeError(
            "TEST_PRIVATE_KEY_NOT_ED25519"
        )

    return value

def runtime():
    return BoundedResearchRuntime()

def issue_capability(
    item,
    task_class="SECURITY_AUDIT",
    nonce=None,
    issued_at=None,
    expires_at=None,
    manifest_sequence=None,
    audience=CAPABILITY_AUDIENCE,
):
    now = int(time.time())

    payload = {
        "schema": CAPABILITY_SCHEMA,
        "audience": audience,
        "boot_id": item.boot_id,
        "manifest_sequence": (
            item.manifest_sequence
            if manifest_sequence is None
            else manifest_sequence
        ),
        "task_class": task_class,
        "nonce": (
            secrets.token_hex(32)
            if nonce is None
            else nonce
        ),
        "issued_at_epoch": (
            now - 1
            if issued_at is None
            else issued_at
        ),
        "expires_at_epoch": (
            now + 60
            if expires_at is None
            else expires_at
        ),
    }

    payload_bytes = canonical(payload)
    signature = private_key().sign(
        payload_bytes
    )

    return json.dumps(
        {
            "payload":
                base64.b64encode(
                    payload_bytes
                ).decode("ascii"),
            "signature":
                base64.b64encode(
                    signature
                ).decode("ascii"),
        },
        sort_keys=True,
    )

def claim(
    claim_id="c1",
    claim_text="The observed claim is supported",
    claim_version=1,
):
    return {
        "claim_id": claim_id,
        "claim_text": claim_text,
        "claim_version": claim_version,
    }

def request(
    item,
    session,
    source_id,
    sequence,
    report_id="report-main",
    question="Is the observed claim supported?",
    claim_id="c1",
    claim_text="The observed claim is supported",
    report_sources=None,
    raw=None,
    claim_count=1,
    evidence_count=1,
):
    registry = item.registry_snapshot()
    uri = registry[source_id][
        "source_uri"
    ]

    if raw is None:
        raw = (
            "verified evidence from "
            + source_id
        ).encode("utf-8")

    claims = []

    for index in range(claim_count):
        current_id = (
            claim_id
            if claim_count == 1
            else "claim-" + str(index)
        )
        current_text = (
            claim_text
            if claim_count == 1
            else "Claim text " + str(index)
        )

        claims.append(
            claim(
                current_id,
                current_text,
                1,
            )
        )

    quarantined = quarantine(
        raw,
        "text/plain",
        uri,
    )
    content = quarantined["content"]

    evidence_items = []

    for index in range(evidence_count):
        current_claim = claims[
            index % len(claims)
        ]

        evidence_items.append({
            "claim_id":
                current_claim["claim_id"],
            "claim_text":
                current_claim["claim_text"],
            "claim_version":
                current_claim[
                    "claim_version"
                ],
            "source_id": source_id,
            "source_uri": uri,
            "raw_sha256":
                content["raw_sha256"],
            "normalized_sha256":
                content[
                    "normalized_sha256"
                ],
            "supports": True,
            "contradicts": False,
        })

    return {
        "schema": REQUEST_SCHEMA,
        "session_id":
            session["session_id"],
        "session_sequence": sequence,
        "raw": raw,
        "mime": "text/plain",
        "source_id": source_id,
        "source_uri": uri,
        "source_observed_at":
            "2026-07-18T12:00:00Z",
        "now_utc":
            "2026-07-18T12:01:00Z",
        "declared_as_of":
            "2026-07-18T12:00:00Z",
        "report": {
            "schema": RESEARCH_SCHEMA,
            "report_id": report_id,
            "report_version": 1,
            "research_question":
                question,
            "scope": {},
            "status":
                "COMPLETED_VERIFIED",
            "executive_summary":
                "research only",
            "claims": claims,
            "unknowns": [],
            "contradictions": [],
            "sources": list(
                report_sources
                if report_sources is not None
                else ["source-a", "source-b"]
            ),
            "confidence": {
                "overall": 1.0,
            },
            "limitations": [],
            "human_review_required": True,
            "executable": False,
            "actionable": False,
            "decision_eligible": False,
            "created_at":
                "2026-07-18T12:00:00Z",
        },
        "model_outputs": [],
        "evidence_items": evidence_items,
        "capabilities": {
            key: False
            for key in
            DISABLED_CAPABILITIES
        },
    }

def read_audit_records():
    records = []

    if not AUDIT_STORE_PATH.exists():
        return records

    for line in (
        AUDIT_STORE_PATH
        .read_text(encoding="utf-8")
        .splitlines()
    ):
        if line.strip():
            records.append(
                json.loads(line)
            )

    return records

def validate_audit_chain(records):
    previous_hash = "0" * 64

    for sequence, record in enumerate(
        records
    ):
        if record["sequence"] != sequence:
            return False

        if record[
            "previous_hash"
        ] != previous_hash:
            return False

        body = {
            "sequence": sequence,
            "previous_hash":
                previous_hash,
            "event": record["event"],
        }

        expected = hashlib.sha256(
            canonical(body)
        ).hexdigest()

        if record[
            "entry_hash"
        ] != expected:
            return False

        previous_hash = expected

    return True

def internal_event(correlation_id):
    for record in reversed(
        read_audit_records()
    ):
        event = record.get("event") or {}

        if event.get(
            "correlation_id"
        ) == correlation_id:
            return event

    return None

class Tests(unittest.TestCase):
    def test_signed_manifest_boot(self):
        item = runtime()

        self.assertEqual(
            item.manifest_sequence,
            1,
        )
        self.assertRegex(
            item.public_key_fingerprint,
            r"^[0-9a-f]{64}$",
        )

    def test_constructor_override_denied(self):
        with self.assertRaises(
            TypeError
        ):
            BoundedResearchRuntime({})

    def test_private_internal_opener_removed(self):
        item = runtime()

        self.assertFalse(
            hasattr(
                item,
                "_open_internal_session",
            )
        )

    def test_invalid_critical_capability_denied(self):
        item = runtime()

        result = item.open_critical_session(
            "not-a-capability"
        )

        self.assertFalse(result["ok"])
        self.assertEqual(
            result["stage"],
            "REQUEST_REJECTED",
        )

    def test_valid_critical_capability(self):
        item = runtime()
        token = issue_capability(item)

        session = item.open_critical_session(
            token
        )

        self.assertTrue(session["ok"])
        self.assertTrue(
            session["critical_session"]
        )
        self.assertEqual(
            session["task_class"],
            "SECURITY_AUDIT",
        )

    def test_critical_capability_replay_denied(self):
        item = runtime()
        token = issue_capability(item)

        first = item.open_critical_session(
            token
        )
        second = item.open_critical_session(
            token
        )

        self.assertTrue(first["ok"])
        self.assertFalse(second["ok"])

    def test_expired_capability_denied(self):
        item = runtime()
        now = int(time.time())

        token = issue_capability(
            item,
            issued_at=now - 100,
            expires_at=now - 1,
        )

        result = item.open_critical_session(
            token
        )

        self.assertFalse(result["ok"])

    def test_wrong_boot_capability_denied(self):
        first = runtime()
        second = runtime()

        token = issue_capability(first)

        result = second.open_critical_session(
            token
        )

        self.assertFalse(result["ok"])

    def test_reserved_critical_session_slots(self):
        item = runtime()

        normal = [
            item.open_session()
            for _ in range(29)
        ]

        self.assertTrue(
            all(
                value["ok"]
                for value in normal[:28]
            )
        )
        self.assertFalse(normal[28]["ok"])

        critical = [
            item.open_critical_session(
                issue_capability(item)
            )
            for _ in range(5)
        ]

        self.assertTrue(
            all(
                value["ok"]
                for value in critical[:4]
            )
        )
        self.assertFalse(
            critical[4]["ok"]
        )

        snapshot = item.global_snapshot()

        self.assertEqual(
            snapshot["normal_sessions"],
            28,
        )
        self.assertEqual(
            snapshot["critical_sessions"],
            4,
        )

    def test_task_class_mutation_denied(self):
        item = runtime()
        session = item.open_session()
        session_id = session["session_id"]

        item._sessions[
            session_id
        ]["task_class"] = "SECURITY_AUDIT"

        result = item.run(
            request(
                item,
                session,
                "source-a",
                0,
                report_sources=[
                    "source-a"
                ],
            )
        )

        self.assertFalse(result["ok"])

        event = internal_event(
            result["correlation_id"]
        )

        self.assertIn(
            "TASK_CLASS_BINDING_MISMATCH",
            event[
                "internal_reason_codes"
            ],
        )

    def test_two_source_quality_flow(self):
        item = runtime()
        session = item.open_session()

        first = item.run(
            request(
                item,
                session,
                "source-a",
                0,
            )
        )
        second = item.run(
            request(
                item,
                session,
                "source-b",
                1,
            )
        )

        self.assertTrue(first["ok"])
        self.assertFalse(
            first[
                "research_quality_gate_passed"
            ]
        )
        self.assertTrue(second["ok"])
        self.assertTrue(
            second[
                "research_quality_gate_passed"
            ]
        )
        self.assertFalse(
            second["actionable"]
        )

    def test_semantic_contamination_blocked(self):
        item = runtime()
        session = item.open_session()

        first = item.run(
            request(
                item,
                session,
                "source-a",
                0,
                report_id="report-a",
                question="Token is safe",
                claim_id="shared",
                claim_text="Token is safe",
            )
        )
        second = item.run(
            request(
                item,
                session,
                "source-b",
                1,
                report_id="report-b",
                question="Token is compromised",
                claim_id="shared",
                claim_text="Token is compromised",
            )
        )

        self.assertTrue(first["ok"])
        self.assertTrue(second["ok"])
        self.assertFalse(
            second[
                "research_quality_gate_passed"
            ]
        )
        self.assertNotEqual(
            first[
                "report_context_hash"
            ],
            second[
                "report_context_hash"
            ],
        )

    def test_session_resource_isolation(self):
        item = runtime()
        attacker = item.open_session()
        victim = item.open_session()

        for sequence in range(8):
            source_id = (
                "source-a"
                if sequence % 2 == 0
                else "source-b"
            )

            result = item.run(
                request(
                    item,
                    attacker,
                    source_id,
                    sequence,
                    report_sources=[
                        source_id
                    ],
                )
            )
            self.assertTrue(result["ok"])

        exhausted = item.run(
            request(
                item,
                attacker,
                "source-a",
                8,
                report_sources=[
                    "source-a"
                ],
            )
        )

        victim_result = item.run(
            request(
                item,
                victim,
                "source-a",
                0,
                report_sources=[
                    "source-a"
                ],
            )
        )

        self.assertFalse(exhausted["ok"])
        self.assertTrue(victim_result["ok"])

    def test_external_rejection_masking(self):
        item = runtime()
        session = item.open_session()

        invalid = request(
            item,
            session,
            "source-a",
            0,
        )
        invalid["critical"] = True

        capability = request(
            item,
            session,
            "source-a",
            0,
        )
        capability["capabilities"][
            "socket_access"
        ] = True

        first = item.run(invalid)
        second = item.run(capability)

        self.assertEqual(
            first["stage"],
            second["stage"],
        )
        self.assertEqual(
            first["reason_codes"],
            second["reason_codes"],
        )

    def test_runtime_audit_reader_removed(self):
        item = runtime()

        self.assertFalse(
            hasattr(
                item,
                "internal_audit_snapshot",
            )
        )
        self.assertFalse(
            hasattr(
                item._audit_store,
                "clear",
            )
        )

    def test_audit_flood_does_not_evict(self):
        item = runtime()
        session = item.open_session()

        first_id = None

        for index in range(128):
            invalid = request(
                item,
                session,
                "source-a",
                0,
            )
            invalid[
                "invalid-" + str(index)
            ] = True

            result = item.run(invalid)

            if first_id is None:
                first_id = result[
                    "correlation_id"
                ]

        records = read_audit_records()

        self.assertTrue(
            validate_audit_chain(records)
        )
        self.assertIsNotNone(
            internal_event(first_id)
        )

    def test_secret_not_logged(self):
        item = runtime()
        session = item.open_session()

        value = request(
            item,
            session,
            "source-a",
            0,
            raw=b"PRIVATE_SECRET_PAYLOAD_ERA57F5",
        )
        value["capabilities"][
            "socket_access"
        ] = True

        result = item.run(value)

        rendered = json.dumps(
            {
                "external": result,
                "audit":
                    read_audit_records(),
            },
            ensure_ascii=False,
        )

        self.assertNotIn(
            "PRIVATE_SECRET_PAYLOAD_ERA57F5",
            rendered,
        )

    def test_global_lock_convoy_removed(self):
        item = runtime()
        first = item.open_session()
        second = item.open_session()

        entered = threading.Event()
        release = threading.Event()

        original = (
            runtime_module.quarantine
        )

        def slow_quarantine(
            raw,
            mime,
            uri,
            max_bytes=1048576,
        ):
            if raw.startswith(
                b"SLOW_F5_FIXTURE"
            ):
                entered.set()
                release.wait(timeout=1.5)

            return original(
                raw,
                mime,
                uri,
                max_bytes,
            )

        runtime_module.quarantine = (
            slow_quarantine
        )

        try:
            with ThreadPoolExecutor(
                max_workers=2
            ) as pool:
                slow_future = pool.submit(
                    item.run,
                    request(
                        item,
                        first,
                        "source-a",
                        0,
                        raw=(
                            b"SLOW_F5_FIXTURE "
                            b"verified evidence"
                        ),
                        report_sources=[
                            "source-a"
                        ],
                    ),
                )

                self.assertTrue(
                    entered.wait(timeout=1)
                )

                fast_future = pool.submit(
                    item.run,
                    request(
                        item,
                        second,
                        "source-b",
                        0,
                        report_sources=[
                            "source-b"
                        ],
                    ),
                )

                fast_result = (
                    fast_future.result(
                        timeout=0.5
                    )
                )

                self.assertTrue(
                    fast_result["ok"]
                )

                release.set()

                self.assertTrue(
                    slow_future.result(
                        timeout=1
                    )["ok"]
                )
        finally:
            release.set()
            runtime_module.quarantine = (
                original
            )

    def test_parallel_same_session_one_wins(self):
        item = runtime()
        session = item.open_session()
        value = request(
            item,
            session,
            "source-a",
            0,
            report_sources=[
                "source-a"
            ],
        )

        with ThreadPoolExecutor(
            max_workers=2
        ) as pool:
            results = list(
                pool.map(
                    item.run,
                    [
                        copy.deepcopy(value),
                        copy.deepcopy(value),
                    ],
                )
            )

        self.assertEqual(
            sum(
                result["ok"]
                for result in results
            ),
            1,
        )

    def test_source_content_rebind_denied(self):
        item = runtime()
        session = item.open_session()

        first = item.run(
            request(
                item,
                session,
                "source-a",
                0,
                report_sources=[
                    "source-a"
                ],
            )
        )
        second = item.run(
            request(
                item,
                session,
                "source-a",
                1,
                raw=b"changed source content",
                report_sources=[
                    "source-a"
                ],
            )
        )

        self.assertTrue(first["ok"])
        self.assertFalse(second["ok"])

    def test_restart_old_session_denied(self):
        first = runtime()
        session = first.open_session()
        second = runtime()

        result = second.run(
            request(
                second,
                session,
                "source-a",
                0,
            )
        )

        self.assertFalse(result["ok"])

    def test_input_not_mutated(self):
        item = runtime()
        session = item.open_session()
        value = request(
            item,
            session,
            "source-a",
            0,
        )
        original = copy.deepcopy(value)

        item.run(value)

        self.assertEqual(value, original)

    def test_stateless_wrapper_denied(self):
        result = run_bounded_research({})

        self.assertFalse(result["ok"])
        self.assertEqual(
            result["stage"],
            "REQUEST_REJECTED",
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)
