import importlib.util
import unittest
from pathlib import Path

source = Path(__file__).with_name(
    "test_research_bounded_runtime_v1.py"
)
spec = importlib.util.spec_from_file_location(
    "_era57f7_fixture",
    source,
)
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class Tests(unittest.TestCase):
    def test_claim_text_change_blocks_reuse(self):
        def flow(second_text):
            runtime = fixture.runtime()
            session = runtime.open_session()

            first = runtime.run(
                fixture.request(
                    runtime, session, "source-a", 0,
                    claim_text="Original claim",
                )
            )
            second = runtime.run(
                fixture.request(
                    runtime, session, "source-b", 1,
                    claim_text=second_text,
                )
            )
            return first, second

        control = flow("Original claim")
        changed = flow("Changed claim meaning")

        self.assertTrue(control[0]["ok"])
        self.assertTrue(control[1]["ok"])
        self.assertTrue(changed[0]["ok"])
        self.assertTrue(changed[1]["ok"])

        self.assertTrue(
            control[1]["research_quality_gate_passed"]
        )
        self.assertFalse(
            changed[1]["research_quality_gate_passed"]
        )

    def test_downstream_reject_consumes_reserved_budget(self):
        def numeric_total(value):
            if isinstance(value, bool):
                return 0
            if isinstance(value, (int, float)):
                return value
            if isinstance(value, dict):
                return sum(
                    numeric_total(item)
                    for item in value.values()
                )
            if isinstance(value, (list, tuple)):
                return sum(
                    numeric_total(item)
                    for item in value
                )
            return 0

        runtime = fixture.runtime()
        session = runtime.open_session()
        session_id = session["session_id"]

        before = runtime.session_snapshot(session_id)

        rejected_request = fixture.request(
            runtime,
            session,
            "source-a",
            0,
            report_sources=["source-a"],
        )
        first_capability = next(
            iter(rejected_request["capabilities"])
        )
        rejected_request["capabilities"][
            first_capability
        ] = True

        rejected = runtime.run(rejected_request)
        after = runtime.session_snapshot(session_id)

        self.assertFalse(rejected["ok"])
        self.assertFalse(after["busy"])
        self.assertEqual(
            after["next_sequence"],
            before["next_sequence"] + 1,
        )
        self.assertEqual(
            after["ledger_entry_count"],
            before["ledger_entry_count"],
        )
        self.assertGreater(
            numeric_total(after["governor_state"]),
            numeric_total(before["governor_state"]),
        )

        stale = runtime.run(
            fixture.request(
                runtime,
                session,
                "source-b",
                0,
                report_sources=["source-b"],
            )
        )
        accepted = runtime.run(
            fixture.request(
                runtime,
                session,
                "source-b",
                1,
                report_sources=["source-b"],
            )
        )

        self.assertFalse(stale["ok"])
        self.assertTrue(accepted["ok"])

    def test_fingerprint_no_gain_session_locality(self):
        def no_gain_values(value):
            found = []

            if isinstance(value, dict):
                for key, item in value.items():
                    if (
                        "no_gain" in str(key).lower()
                        and isinstance(item, (int, float))
                        and not isinstance(item, bool)
                    ):
                        found.append(item)

                    found.extend(no_gain_values(item))

            elif isinstance(value, (list, tuple)):
                for item in value:
                    found.extend(no_gain_values(item))

            return found

        runtime = fixture.runtime()
        attacker = runtime.open_session()
        victim = runtime.open_session()

        attacker_before = runtime.session_snapshot(
            attacker["session_id"]
        )["governor_state"]
        victim_before = runtime.session_snapshot(
            victim["session_id"]
        )["governor_state"]

        for sequence in (0, 1):
            result = runtime.run(
                fixture.request(
                    runtime,
                    attacker,
                    "source-a",
                    sequence,
                    report_sources=["source-a"],
                )
            )
            self.assertTrue(result["ok"])

        attacker_after = runtime.session_snapshot(
            attacker["session_id"]
        )["governor_state"]
        victim_after = runtime.session_snapshot(
            victim["session_id"]
        )["governor_state"]

        self.assertEqual(victim_after, victim_before)
        self.assertNotEqual(attacker_after, attacker_before)

        counts = attacker_after["fingerprint_counts"]

        self.assertTrue(counts)
        self.assertGreaterEqual(max(counts.values()), 2)

        before_no_gain = no_gain_values(attacker_before)
        after_no_gain = no_gain_values(attacker_after)

        self.assertTrue(before_no_gain)
        self.assertTrue(after_no_gain)
        self.assertGreater(
            max(after_no_gain),
            max(before_no_gain),
        )

        victim_result = runtime.run(
            fixture.request(
                runtime,
                victim,
                "source-b",
                0,
                report_sources=["source-b"],
            )
        )

        self.assertTrue(victim_result["ok"])

    def test_global_canonical_evidence_reuse_disabled(self):
        runtime = fixture.runtime()

        producer = runtime.open_session()
        source_a_only = runtime.open_session()
        source_b_only = runtime.open_session()

        first = runtime.run(
            fixture.request(
                runtime,
                producer,
                "source-a",
                0,
                report_sources=["source-a"],
            )
        )
        complete = runtime.run(
            fixture.request(
                runtime,
                producer,
                "source-b",
                1,
                report_sources=["source-a", "source-b"],
            )
        )

        isolated_a = runtime.run(
            fixture.request(
                runtime,
                source_a_only,
                "source-a",
                0,
                report_sources=["source-a"],
            )
        )
        isolated_b = runtime.run(
            fixture.request(
                runtime,
                source_b_only,
                "source-b",
                0,
                report_sources=["source-b"],
            )
        )

        self.assertTrue(first["ok"])
        self.assertTrue(complete["ok"])
        self.assertTrue(
            complete["research_quality_gate_passed"]
        )

        for session, result in (
            (source_a_only, isolated_a),
            (source_b_only, isolated_b),
        ):
            self.assertTrue(result["ok"])
            self.assertFalse(
                result["research_quality_gate_passed"]
            )
            self.assertFalse(
                result["canonical_evidence_reuse"]
            )

            snapshot = runtime.session_snapshot(
                session["session_id"]
            )

            self.assertEqual(
                snapshot["source_count"],
                1,
            )
            self.assertEqual(
                snapshot["ledger_entry_count"],
                1,
            )
            self.assertEqual(
                snapshot["evidence_context_count"],
                1,
            )
            self.assertFalse(
                snapshot["canonical_evidence_reuse"]
            )
