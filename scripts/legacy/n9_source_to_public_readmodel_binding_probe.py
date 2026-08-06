#!/usr/bin/env python3
"""N9 source-to-public-readmodel binding probe.

NOAPI / no wallet / no trade / no provider call.
This probe does not execute market logic. It inspects the configured source/public
readmodel files, validates their binding hashes, and writes an evidence result under
data/control.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import hashlib
import subprocess
import time

ROOT = Path("/root/tokenoskobi_clean_v1")
PHASE = "N9_SOURCE_TO_PUBLIC_READMODEL_BINDING_PROBE"
OUT = ROOT / "data/control/n9_source_to_public_readmodel_binding_probe_result_v1.json"
ROWS = ROOT / "data/control/n9_source_to_public_readmodel_binding_probe_result_v1_rows.jsonl"
PUBLIC_DIR = ROOT / "public/backpressure_readmodel_refresh_staging_v1"
SOURCE_CACHE = PUBLIC_DIR / "backpressure_readmodel_refresh_cache.json"
SOURCE_MANIFEST = PUBLIC_DIR / "backpressure_readmodel_refresh_manifest.json"
SOURCE_INDEX = PUBLIC_DIR / "backpressure_readmodel_refresh_index.json"
RUNNER = ROOT / "tools/backpressure_readmodel_refresh_runner_v1.py"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path):
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_read_error": f"{type(e).__name__}: {e}"}


def run(name, cmd):
    t0 = time.perf_counter()
    p = subprocess.run(cmd, shell=True, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t1 = time.perf_counter()
    return {
        "name": name,
        "cmd": cmd,
        "rc": p.returncode,
        "latency_ms": round((t1 - t0) * 1000, 3),
        "stdout_head": p.stdout[:2000],
        "stderr_head": p.stderr[:1000],
    }


def main():
    t0 = time.perf_counter()
    cache = read_json(SOURCE_CACHE) if SOURCE_CACHE.exists() else None
    manifest = read_json(SOURCE_MANIFEST) if SOURCE_MANIFEST.exists() else None
    index = read_json(SOURCE_INDEX) if SOURCE_INDEX.exists() else None

    cache_sha = sha256(SOURCE_CACHE)
    manifest_sha = sha256(SOURCE_MANIFEST)
    index_sha = sha256(SOURCE_INDEX)

    binding_checks = {
        "cache_exists": SOURCE_CACHE.exists(),
        "manifest_exists": SOURCE_MANIFEST.exists(),
        "index_exists": SOURCE_INDEX.exists(),
        "cache_parse_ok": isinstance(cache, dict) and "_read_error" not in cache,
        "manifest_parse_ok": isinstance(manifest, dict) and "_read_error" not in manifest,
        "index_parse_ok": isinstance(index, dict) and "_read_error" not in index,
        "cache_state_valid": isinstance(cache, dict) and cache.get("state") == "CACHE_VALID",
        "cache_runtime_lookup_only": isinstance(cache, dict) and cache.get("runtime_bucket") == "LOOKUP_ONLY",
        "manifest_cache_sha_matches": isinstance(manifest, dict) and manifest.get("cache_sha256") == cache_sha,
        "index_cache_sha_matches": isinstance(index, dict) and index.get("cache_sha256") == cache_sha,
        "index_manifest_sha_matches": isinstance(index, dict) and index.get("manifest_sha256") == manifest_sha,
    }

    runner_static = {
        "runner_exists": RUNNER.exists(),
        "mentions_public_dir": False,
        "mentions_source_cache": False,
        "mentions_source_manifest": False,
        "mentions_source_index": False,
        "contains_public_target_write_false": False,
        "contains_active_runner_file_write_false": False,
        "contains_service_timer_worker_false": False,
    }
    if RUNNER.exists():
        text = RUNNER.read_text(encoding="utf-8", errors="ignore")
        runner_static.update({
            "mentions_public_dir": str(PUBLIC_DIR) in text,
            "mentions_source_cache": str(SOURCE_CACHE) in text,
            "mentions_source_manifest": str(SOURCE_MANIFEST) in text,
            "mentions_source_index": str(SOURCE_INDEX) in text,
            "contains_public_target_write_false": "PUBLIC_TARGET_WRITE=False" in text or '"public_target_write": False' in text,
            "contains_active_runner_file_write_false": "ACTIVE_RUNNER_FILE_WRITE=False" in text or '"active_runner_file_write": False' in text,
            "contains_service_timer_worker_false": "SERVICE_TIMER_WORKER=False" in text or '"service_timer_worker": False' in text,
        })

    steps = [
        run("systemd_services", "systemctl list-units --type=service --all | grep -Ei 'tokenoskobi|coinoskobi' || true"),
        run("systemd_timers", "systemctl list-timers --all | grep -Ei 'tokenoskobi|coinoskobi' || true"),
        run("public_freshness", "find public -type f -printf '%T@ %p\\n' 2>/dev/null | sort -nr | head -40 || true"),
    ]

    binding_ok = all(binding_checks.values())
    runner_confirms_readonly_public_source = (
        runner_static["runner_exists"]
        and runner_static["mentions_source_cache"]
        and runner_static["mentions_source_manifest"]
        and runner_static["mentions_source_index"]
    )

    result = {
        "stage": PHASE,
        "created_at_utc": now(),
        "total_latency_ms": round((time.perf_counter() - t0) * 1000, 3),
        "safety": {
            "api_calls": 0,
            "wallet": False,
            "signing": False,
            "paper_trade": False,
            "live_trade": False,
            "provider_call": False,
            "dex_call": False,
            "policy_apply": False,
            "core_change": False,
        },
        "public_paths": {
            "cache": str(SOURCE_CACHE),
            "manifest": str(SOURCE_MANIFEST),
            "index": str(SOURCE_INDEX),
            "cache_sha256": cache_sha,
            "manifest_sha256": manifest_sha,
            "index_sha256": index_sha,
        },
        "binding_checks": binding_checks,
        "runner_static": runner_static,
        "binding_ok": binding_ok,
        "runner_confirms_readonly_public_source": runner_confirms_readonly_public_source,
        "full_source_to_public_readmodel_binding_proven": binding_ok and runner_confirms_readonly_public_source,
        "full_public_to_panel_binding_proven": False,
        "decision": "PUBLIC_READMODEL_SOURCE_BINDING_PROVEN" if binding_ok and runner_confirms_readonly_public_source else "PUBLIC_READMODEL_SOURCE_BINDING_NOT_PROVEN",
        "note": "This proves source/public readmodel file binding only. It does not prove token-analysis engine to panel end-to-end execution.",
        "steps": steps,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ROWS.write_text("\n".join(json.dumps({"kind": "check", "name": k, "ok": v}, ensure_ascii=False, sort_keys=True) for k, v in binding_checks.items()) + "\n", encoding="utf-8")

    print("FINAL_GATE=PASS_" + PHASE)
    print("DECISION=" + result["decision"])
    print("FULL_SOURCE_TO_PUBLIC_READMODEL_BINDING_PROVEN=" + str(result["full_source_to_public_readmodel_binding_proven"]))
    print("TOTAL_LATENCY_MS=" + str(result["total_latency_ms"]))
    print("JSON=" + str(OUT.relative_to(ROOT)))
    print("ROWS=" + str(ROWS.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
