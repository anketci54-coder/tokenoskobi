#!/usr/bin/env python3
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
from pathlib import Path

ROOT = Path("/root/tokenoskobi_clean_v1")
WRAPPER = ROOT / "tools/era55a15_p0_pre_gateway_queue_semantic_parity_repair_and_temp_copy_test_v1.py"
EXPECTED_SOURCE_SHA256 = "e528eee230c4379af1c8db418b10bafb6c0e4a6b5a011bdeedfd51b882f9c2b2"


def extract_payload(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Name)
            and target.id == "_PAYLOAD"
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise RuntimeError("A15_PAYLOAD_NOT_FOUND")


def main() -> int:
    payload = extract_payload(WRAPPER)
    padded = payload + ("=" * (-len(payload) % 4))
    compressed = base64.b64decode(padded, validate=True)
    source = gzip.decompress(compressed)
    actual_sha = hashlib.sha256(source).hexdigest()
    if actual_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            "A15_SOURCE_SHA256_MISMATCH expected="
            + EXPECTED_SOURCE_SHA256
            + " actual="
            + actual_sha
        )
    text = source.decode("utf-8")
    compile(text, str(WRAPPER), "exec")
    print("A15_PAYLOAD_PADDING_REPAIRED=true")
    print("A15_SOURCE_SHA256=" + actual_sha)
    namespace = {
        "__name__": "__main__",
        "__file__": str(WRAPPER),
        "__package__": None,
        "__cached__": None,
    }
    exec(compile(text, str(WRAPPER), "exec"), namespace, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
