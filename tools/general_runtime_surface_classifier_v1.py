#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

WORK = "GENERAL_RUNTIME_HARDENING_B_ACTIVE_SURFACE_CLASSIFICATION"
NEXT = "GENERAL_RUNTIME_HARDENING_C_GENERAL_RUNNER_CONTRACT"
LINE = "GENERAL_RUNTIME_HARDENING"
TOKEN = re.compile(
    r"(?:/root/tokenoskobi_clean_v1/)?"
    r"(?:tools|core|plugins|tests|config|data|runtime|reports|archive|active_panel_8096)"
    r"/[A-Za-z0-9_.@%+=:,/\-]+"
)
EVIDENCE = ("archive/", "reports/", "data/control/", "data/shadow_runtime_lab/")


def cmd(args, root=None, check=True):
    return subprocess.run(
        args,
        cwd=str(root) if root else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
        timeout=60,
    )


def load(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def section(text, heading, body):
    start = text.find(heading)
    if start < 0:
        return text.rstrip() + "\n\n" + heading + "\n\n" + body.rstrip() + "\n"
    end = text.find("\n## ", start + len(heading))
    if end < 0:
        end = len(text)
    return text[:start] + heading + "\n\n" + body.rstrip() + "\n" + text[end:]


def tracked(root):
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
    return sorted(x.decode("utf-8") for x in raw.split(b"\0") if x)


def norm(root, value):
    value = value.strip(" \t\r\n'\"`()[]{}<>,;").rstrip(":")
    prefix = str(root) + "/"
    if value.startswith(prefix):
        value = value[len(prefix):]
    value = value.lstrip("./")
    if not value:
        return None
    try:
        (root / value).resolve().relative_to(root.resolve())
    except (ValueError, OSError):
        return None
    return value


def paths(root, text):
    return {
        item
        for item in (norm(root, m.group(0)) for m in TOKEN.finditer(text))
        if item
    }


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def units(root):
    listing = cmd(
        [
            "systemctl", "list-unit-files",
            "--type=service", "--type=timer",
            "--no-legend", "--no-pager",
        ],
        check=False,
    )
    names = sorted({
        line.split()[0]
        for line in listing.stdout.splitlines()
        if line.split()
        and any(x in line.split()[0].lower() for x in ("tokenoskobi", "coinoskobi"))
    })
    records, seeds = [], set()
    for name in names:
        result = cmd(
            [
                "systemctl", "show", name, "--no-pager",
                "-p", "ActiveState", "-p", "SubState",
                "-p", "UnitFileState", "-p", "FragmentPath",
                "-p", "DropInPaths", "-p", "ExecStart",
                "-p", "Environment", "-p", "EnvironmentFiles",
            ],
            check=False,
        )
        props = dict(
            line.split("=", 1)
            for line in result.stdout.splitlines()
            if "=" in line
        )
        repo_paths = sorted(paths(root, "\n".join(props.values())))
        seeds.update(x for x in repo_paths if (root / x).exists())
        fragment = props.get("FragmentPath", "")
        records.append({
            "unit": name,
            "active": props.get("ActiveState"),
            "sub": props.get("SubState"),
            "enabled": props.get("UnitFileState"),
            "fragment": fragment or None,
            "fragment_sha256": (
                sha(Path(fragment))
                if fragment and Path(fragment).is_file()
                else None
            ),
            "dropins": props.get("DropInPaths") or None,
            "exec_start": props.get("ExecStart") or None,
            "environment": props.get("Environment") or None,
            "environment_files": props.get("EnvironmentFiles") or None,
            "repo_paths": repo_paths,
        })
    return records, seeds


def module_map(files):
    result = {}
    for path in files:
        if not path.endswith(".py"):
            continue
        parts = path[:-3].split("/")
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            name = ".".join(parts)
            result[name] = path
            result.setdefault(parts[-1], path)
    return result


def graph(root, files):
    file_set = set(files)
    modules = module_map(files)
    edges = defaultdict(set)
    parse_errors = []
    for path in files:
        if not path.endswith(".py"):
            continue
        text = (root / path).read_text(encoding="utf-8", errors="replace")
        edges[path].update(x for x in paths(root, text) if x in file_set or (root / x).exists())
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError as exc:
            parse_errors.append(f"{path}:{exc.lineno}:{exc.msg}")
            continue
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [x.name for x in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name in modules:
                    edges[path].add(modules[name])
                elif name.split(".")[-1] in modules:
                    edges[path].add(modules[name.split(".")[-1]])
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                edges[path].update(paths(root, node.value))
    return edges, parse_errors


def walk(seeds, edges):
    seen, queue = set(), deque(sorted(seeds))
    while queue:
        item = queue.popleft()
        if item in seen:
            continue
        seen.add(item)
        queue.extend(x for x in edges.get(item, ()) if x not in seen)
    return seen


def root_stats(root, files):
    rows = []
    total = 0
    for rel in files:
        full = root / rel
        if not full.is_file():
            continue
        size = full.stat().st_size
        total += size
        rows.append((size, rel))
    rows.sort(reverse=True)
    return {
        "file_count": len(rows),
        "total_bytes": total,
        "largest": [{"path": p, "bytes": s} for s, p in rows[:20]],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.getenv("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--artifact",
        default="data/control/general_runtime_hardening_b_active_surface_classification_v1.json",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()

    runtime_path = root / "PROJECT_RUNTIME.json"
    history_path = root / "PROJECT_HISTORY.json"
    master_path = root / "06_PROJECT_MASTER_STATE.md"
    handoff_path = root / "07_PROJECT_HANDOFF.md"
    artifact_path = root / args.artifact

    runtime = load(runtime_path)
    pointer = runtime["canonical_runtime_pointer"]
    if pointer.get("next_safe_step") != WORK:
        raise SystemExit("UNEXPECTED_NEXT_SAFE_STEP=" + str(pointer.get("next_safe_step")))
    if pointer.get("era57_opened") is not False:
        raise SystemExit("ERA57_MUST_REMAIN_CLOSED")
    if pointer.get("live_source_fetch_authorized") is not False:
        raise SystemExit("LIVE_FETCH_MUST_REMAIN_DISABLED")
    if pointer.get("production_mutation") is not False:
        raise SystemExit("PRODUCTION_MUTATION_MUST_REMAIN_FALSE")

    files = tracked(root)
    file_set = set(files)
    unit_rows, seeds = units(root)
    if not unit_rows:
        raise SystemExit("NO_TOKENOSKOBI_SYSTEMD_UNITS_FOUND")
    if not seeds:
        raise SystemExit("NO_REPOSITORY_ENTRYPOINT_FOUND_IN_SYSTEMD")

    edges, parse_errors = graph(root, files)
    reachable = walk(seeds, edges)

    active_runtime = sorted(
        x for x in reachable
        if x in file_set
        and x.endswith(".py")
        and x.startswith(("tools/", "active_panel_8096/"))
    )
    active_library = sorted(
        x for x in reachable
        if x in file_set
        and x.endswith(".py")
        and x not in active_runtime
    )
    active_data = sorted(
        x for x in reachable
        if x in file_set and not x.endswith(".py")
    )
    general = sorted(
        x for x in files
        if (x.startswith("tests/") or x.startswith("tools/general_"))
        and x not in reachable
    )
    manual = sorted(
        x for x in files
        if x.startswith("tools/") and x.endswith(".py")
        and x not in reachable and x not in general
    )
    historical = sorted(
        x for x in files
        if x.startswith(EVIDENCE) and x not in reachable
    )

    scope = {
        x for x in files
        if x.startswith(("tools/", "core/", "plugins/", "tests/", "data/", "runtime/state/", "reports/", "archive/"))
    }
    classified = set(active_runtime + active_library + active_data + general + manual + historical)
    unclassified = sorted(scope - classified)

    missing = []
    for source in sorted(reachable):
        if not source.endswith(".py") or not (root / source).is_file():
            continue
        text = (root / source).read_text(encoding="utf-8", errors="replace")
        for target in sorted(paths(root, text)):
            if not (root / target).exists():
                missing.append({"source": source, "target": target})
    missing = [dict(t) for t in {tuple(sorted(x.items())) for x in missing}]

    disposable = []
    for base_name in ("tools", "tests", "runtime", "data", "reports"):
        base = root / base_name
        if not base.exists():
            continue
        for full in base.rglob("*"):
            if not full.is_file():
                continue
            if (
                "__pycache__" in full.parts
                or full.suffix.lower() in {".pyc", ".pyo", ".tmp", ".swp", ".bak", ".orig"}
            ):
                rel = str(full.relative_to(root))
                if rel not in file_set:
                    disposable.append(rel)
    disposable = sorted(set(disposable))

    evidence_stats = {}
    for prefix in EVIDENCE:
        evidence_stats[prefix.rstrip("/")] = root_stats(
            root,
            [x for x in historical if x.startswith(prefix)],
        )

    result = "WARN_ACTIVE_REFERENCE_GAPS_FOUND" if missing else "OK_ACTIVE_SURFACE_CLASSIFIED"
    now = datetime.now(timezone.utc).isoformat()
    artifact = {
        "schema": "general_runtime_surface_classifier_v1",
        "timestamp_utc": now,
        "work_unit": WORK,
        "status": "CLOSED_VERIFIED",
        "result": result,
        "method": {
            "live_systemd": True,
            "git_inventory": True,
            "python_ast_import_graph": True,
            "literal_path_graph": True,
            "filename_only_delete_decision": False,
        },
        "systemd_units": unit_rows,
        "entrypoints": sorted(seeds),
        "classification": {
            "ACTIVE_RUNTIME": active_runtime,
            "ACTIVE_LIBRARY": active_library,
            "ACTIVE_RUNTIME_DATA": active_data,
            "GENERAL_TOOL": general,
            "MANUAL_ONLY": manual,
            "HISTORICAL_EVIDENCE_ROOTS": evidence_stats,
            "HISTORICAL_EVIDENCE_FILE_COUNT": len(historical),
            "DISPOSABLE": disposable,
            "UNCLASSIFIED": unclassified,
        },
        "counts": {
            "tracked": len(files),
            "active_runtime": len(active_runtime),
            "active_library": len(active_library),
            "active_runtime_data": len(active_data),
            "general_tool": len(general),
            "manual_only": len(manual),
            "historical_evidence": len(historical),
            "disposable": len(disposable),
            "unclassified": len(unclassified),
            "parse_errors": len(parse_errors),
            "missing_active_references": len(missing),
        },
        "parse_errors": parse_errors,
        "missing_active_references": missing,
        "decision": {
            "move": False,
            "delete": False,
            "archive": False,
            "wrapper_change": False,
            "database_change": False,
            "service_timer_change": False,
            "panel_change": False,
            "live_fetch_change": False,
            "production_mutation": False,
        },
        "next_safe_step": NEXT,
    }

    if not args.apply:
        print(json.dumps(artifact, ensure_ascii=False, indent=2))
        return 0

    save(artifact_path, artifact)

    hardening = pointer.get("general_runtime_hardening", {})
    substeps = hardening.get("substeps", {}) if isinstance(hardening, dict) else {}
    substeps.update({
        "A_CANONICAL_SYNC": "CLOSED_VERIFIED",
        "B_ACTIVE_SURFACE_CLASSIFICATION": "CLOSED_VERIFIED",
        "C_GENERAL_RUNNER_CONTRACT": "READY",
        "D_POLICY_AUTHORITY_REACHABILITY": "PENDING",
        "E_FINAL_STRESS_GATE": "PENDING",
    })
    hardening = {
        "id": LINE,
        "status": "OPEN",
        "substeps": substeps,
        "surface_classification_result": result,
        "surface_classification_artifact": args.artifact,
        "missing_active_reference_count": len(missing),
        "era57_opened": False,
        "production_mutation": False,
        "next_safe_step": NEXT,
        "updated_at_utc": now,
    }

    pointer.update({
        "current_stage": "GENERAL_RUNTIME_HARDENING_B_ACTIVE_SURFACE_CLASSIFICATION_CLOSED",
        "last_completed": WORK,
        "last_result": result,
        "last_artifact": args.artifact,
        "general_runtime_hardening": hardening,
        "era57_opened": False,
        "live_source_fetch_authorized": False,
        "production_mutation": False,
        "next_safe_step": NEXT,
        "updated_at_utc": now,
    })
    runtime.update({
        "last_completed": WORK,
        "last_result": result,
        "last_artifact": args.artifact,
        "next_safe_step": NEXT,
        "general_runtime_hardening": hardening,
        "updated_at": now,
        "updated_at_utc": now,
        "current_problem": {
            "code": (
                "ACTIVE_RUNTIME_REFERENCE_GAPS_REQUIRE_RUNNER_CONTRACT"
                if missing else "GENERAL_RUNNER_CONTRACT_REVIEW_REQUIRED"
            ),
            "severity": "P0" if missing else "P1",
            "evidence": args.artifact,
        },
        "current_work_unit": {
            "id": WORK,
            "main_line": LINE,
            "substep": "B_ACTIVE_SURFACE_CLASSIFICATION",
            "status": "CLOSED_VERIFIED",
            "result": result,
            "artifact": args.artifact,
            "production_mutation": False,
            "next_step": NEXT,
        },
    })
    runtime["current_state"] = {
        "project_status": "ERA56_CLOSED_PRE_ERA57_GENERAL_RUNTIME_HARDENING",
        "runtime_status": "ACTIVE_SURFACE_CLASSIFIED_RUNNER_CONTRACT_READY",
        "mode": "PRE_ERA57_GENERAL_RUNTIME_HARDENING",
        "last_action": {
            "task": WORK, "result": result,
            "artifact": args.artifact, "timestamp": now,
        },
        "current_problem": runtime["current_problem"],
        "next_safe_step": {
            "id": NEXT, "status": "READY",
            "human_authorization_required": True,
            "production_mutation": False,
        },
        "updated_at": now,
    }
    save(runtime_path, runtime)

    history = load(history_path)
    events = history.setdefault("events", [])
    if not any(isinstance(x, dict) and x.get("event_id") == WORK for x in events):
        events.append({
            "event_id": WORK,
            "timestamp_utc": now,
            "status": "CLOSED_VERIFIED",
            "result": result,
            "artifact": args.artifact,
            "counts": artifact["counts"],
            "file_move": False,
            "file_delete": False,
            "production_mutation": False,
            "next_safe_step": NEXT,
        })
    history["updated_at"] = now
    history["updated_at_utc"] = now
    save(history_path, history)

    master = master_path.read_text(encoding="utf-8")
    master = section(master, "## 02 CURRENT MAJOR-LINE POSITION", """```text
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
ERA55_STATUS=CLOSED_SEALED
ERA56_STATUS=CLOSED_SEALED
ERA57_OPENED=false
CURRENT_MAIN_LINE=GENERAL_RUNTIME_HARDENING
CURRENT_STAGE=GENERAL_RUNTIME_HARDENING_B_ACTIVE_SURFACE_CLASSIFICATION_CLOSED
LIVE_FETCH_AUTHORIZED=false
PRODUCTION_MUTATION=false
```""")
    master = section(master, "## 03 LAST VERIFIED WORK", f"""```text
LAST_COMPLETED={WORK}
LAST_RESULT={result}
LAST_ARTIFACT={args.artifact}
ACTIVE_RUNTIME_COUNT={len(active_runtime)}
ACTIVE_LIBRARY_COUNT={len(active_library)}
GENERAL_TOOL_COUNT={len(general)}
MANUAL_ONLY_COUNT={len(manual)}
HISTORICAL_EVIDENCE_COUNT={len(historical)}
DISPOSABLE_COUNT={len(disposable)}
MISSING_ACTIVE_REFERENCE_COUNT={len(missing)}
FILE_MOVE=false
FILE_DELETE=false
ERA57_OPENED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}""")
    master = section(master, "## 10 NEXT SAFE STEP", f"""```text
NEXT_SAFE_STEP={NEXT}
```

Resolve the active wrapper and raw-stage target from the classified live
surface. Do not restore timestamped legacy runners. Keep live fetch disabled.""")
    master_path.write_text(master.rstrip() + "\n", encoding="utf-8")

    handoff = handoff_path.read_text(encoding="utf-8")
    handoff = section(handoff, "## 02 CURRENT CONTINUATION CHECKPOINT", f"""PROJECT_STATUS=ERA56_CLOSED_PRE_ERA57_GENERAL_RUNTIME_HARDENING
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_MAIN_LINE={LINE}
CURRENT_STAGE=GENERAL_RUNTIME_HARDENING_B_ACTIVE_SURFACE_CLASSIFICATION_CLOSED
LAST_COMPLETED={WORK}
LAST_RESULT={result}
LAST_ARTIFACT={args.artifact}
FILE_MOVE=false
FILE_DELETE=false
LIVE_FETCH_AUTHORIZED=false
ERA57_OPENED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""")
    handoff = section(handoff, "## 07 ALLOWED NEXT DECISIONS", f"""- Use the classification artifact as runtime-surface evidence.
- Repair the general runner contract without restoring PRE_DERIVED files.
- Do not enable live source fetch.
- Do not delete or move evidence in the runner-contract step.
- ERA57 remains closed.

NEXT_SAFE_STEP={NEXT}""")
    handoff_path.write_text(handoff.rstrip() + "\n", encoding="utf-8")

    for line in (
        "GENERAL_RUNTIME_HARDENING_B_STATUS=CLOSED_VERIFIED",
        f"RESULT={result}",
        f"ACTIVE_RUNTIME_COUNT={len(active_runtime)}",
        f"ACTIVE_LIBRARY_COUNT={len(active_library)}",
        f"GENERAL_TOOL_COUNT={len(general)}",
        f"MANUAL_ONLY_COUNT={len(manual)}",
        f"HISTORICAL_EVIDENCE_COUNT={len(historical)}",
        f"DISPOSABLE_COUNT={len(disposable)}",
        f"MISSING_ACTIVE_REFERENCE_COUNT={len(missing)}",
        "FILE_MOVE=false",
        "FILE_DELETE=false",
        "LIVE_FETCH_AUTHORIZED=false",
        "ERA57_OPENED=false",
        "PRODUCTION_MUTATION=false",
        f"NEXT_SAFE_STEP={NEXT}",
    ):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
