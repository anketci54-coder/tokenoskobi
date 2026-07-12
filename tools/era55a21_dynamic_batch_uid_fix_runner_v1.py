#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path("/root/tokenoskobi_clean_v1")
TARGET = ROOT / "tools/era55a21_p0_single_natural_cycle_post_remediation_canary_apply_and_post_audit_v1.py"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"A21_DYNAMIC_UID_PATCH_COUNT_INVALID:{label}:{count}")
    return source.replace(old, new, 1)


def transform(source: str) -> str:
    source = replace_once(
        source,
        '''    expected_baseline_uid = str(contract["existing_batch_uid_must_be_preserved"])
    expected_new_uid = str(contract["prospective_batch_uid"])
    expected_source_count = int(contract["expected_new_ledger_rows"])
''',
        '''    expected_baseline_uid = str(contract["existing_batch_uid_must_be_preserved"])
    authorized_snapshot_uid = str(contract["prospective_batch_uid"])
    expected_new_uid = authorized_snapshot_uid
    expected_source_count = int(contract["expected_new_ledger_rows"])
''',
        "ONE_SHOT_CONTRACT_BINDING",
    )

    source = replace_once(
        source,
        '''    if str(plan["batch_uid"]) != expected_new_uid:
        raise RuntimeError(
            "A21_AUTHORIZED_BATCH_UID_DRIFT:"
            + expected_new_uid
            + ":"
            + str(plan["batch_uid"])
        )
''',
        '''    actual_new_uid = str(plan["batch_uid"])
    if actual_new_uid == expected_baseline_uid:
        raise RuntimeError("A21_DYNAMIC_BATCH_UID_EQUALS_BASELINE")
    expected_new_uid = actual_new_uid
    batch_uid_contract_drift = actual_new_uid != authorized_snapshot_uid
''',
        "ONE_SHOT_DYNAMIC_UID_BINDING",
    )

    source = replace_once(
        source,
        '''        "baseline_batch_uid": expected_baseline_uid,
        "new_batch_uid": expected_new_uid,
        "new_batch_sequence": new_batch["batch_sequence"],
''',
        '''        "baseline_batch_uid": expected_baseline_uid,
        "authorized_snapshot_batch_uid": authorized_snapshot_uid,
        "new_batch_uid": expected_new_uid,
        "batch_uid_bound_at_execution": True,
        "batch_uid_contract_drift": batch_uid_contract_drift,
        "new_batch_sequence": new_batch["batch_sequence"],
''',
        "ONE_SHOT_RESULT_FIELDS",
    )

    source = replace_once(
        source,
        '''    expected_new_uid = str(contract["prospective_batch_uid"])
    expected_new_rows = int(contract["expected_new_ledger_rows"])
''',
        '''    authorized_snapshot_uid = str(contract["prospective_batch_uid"])
    expected_new_uid = authorized_snapshot_uid
    expected_new_rows = int(contract["expected_new_ledger_rows"])
''',
        "ORCHESTRATOR_CONTRACT_BINDING",
    )

    source = replace_once(
        source,
        '''        if one_shot.get("status") != "OK_A21_ONE_SHOT_HOT_WRAPPER_COMPLETED":
            raise RuntimeError("A21_ONE_SHOT_STATUS_NOT_OK")

        order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
''',
        '''        if one_shot.get("status") != "OK_A21_ONE_SHOT_HOT_WRAPPER_COMPLETED":
            raise RuntimeError("A21_ONE_SHOT_STATUS_NOT_OK")
        if one_shot.get("authorized_snapshot_batch_uid") != authorized_snapshot_uid:
            raise RuntimeError("A21_AUTHORIZED_SNAPSHOT_UID_MISMATCH")
        if one_shot.get("batch_uid_bound_at_execution") is not True:
            raise RuntimeError("A21_DYNAMIC_BATCH_UID_NOT_BOUND_AT_EXECUTION")
        expected_new_uid = str(one_shot.get("new_batch_uid", ""))
        if not expected_new_uid or expected_new_uid == baseline_uid:
            raise RuntimeError("A21_EXECUTION_BOUND_BATCH_UID_INVALID")

        order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
''',
        "ORCHESTRATOR_EXECUTION_UID_BINDING",
    )

    source = replace_once(
        source,
        '''            "one_shot_result": one_shot,
            "production_before": before_inventory,
''',
        '''            "one_shot_result": one_shot,
            "dynamic_batch_uid_authorization": {
                "authorized_snapshot_batch_uid": authorized_snapshot_uid,
                "execution_bound_batch_uid": expected_new_uid,
                "batch_uid_bound_at_execution": True,
                "batch_uid_contract_drift": one_shot["batch_uid_contract_drift"],
                "source_count_remained_authorized": (
                    one_shot["source_candidate_count"] == expected_new_rows
                ),
                "bounded_dynamic_uid_policy": (
                    "UID_BOUND_AFTER_NATURAL_REFRESH_WITH_EXACT_SOURCE_COUNT_"
                    "AND_COMPLETE_ACCOUNTING"
                ),
            },
            "production_before": before_inventory,
''',
        "ARTIFACT_DYNAMIC_UID_EVIDENCE",
    )

    source = source.replace(
        "A21_AUTHORIZED_BATCH_UID_DRIFT",
        "A21_AUTHORIZED_BATCH_UID_DRIFT_REMOVED_BY_DYNAMIC_BINDING",
    )
    return source


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    transformed = transform(source)
    compile(transformed, str(Path(__file__).resolve()), "exec")
    namespace = {
        "__name__": "__main__",
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
    }
    exec(compile(transformed, str(Path(__file__).resolve()), "exec"), namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
