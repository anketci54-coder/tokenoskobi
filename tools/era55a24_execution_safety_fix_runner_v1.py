#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path("/root/tokenoskobi_clean_v1")
TARGET = ROOT / "tools/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.py"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"A24_FIX_REPLACEMENT_COUNT_INVALID:{label}:{count}")
    return source.replace(old, new, 1)


def transform(source: str) -> str:
    source = replace_once(
        source,
        '''    since = moment.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
''',
        '''    since = moment.astimezone(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S.%f UTC"
    )
''',
        "MICROSECOND_JOURNAL_BOUNDARY",
    )

    source = replace_once(
        source,
        '''    def restore_timer() -> None:
        nonlocal timer_restored
        if timer_initial["active"] == "active":
            run(["systemctl", "start", TIMER], check=False, timeout=30)
        timer_restored = True
''',
        '''    def restore_timer() -> None:
        nonlocal timer_restored
        if timer_initial["active"] == "active":
            run(["systemctl", "start", TIMER], check=True, timeout=30)
        else:
            run(["systemctl", "stop", TIMER], check=True, timeout=30)
        timer_restored = True
''',
        "STRICT_TIMER_RESTORE",
    )

    source = replace_once(
        source,
        '''    def cleanup() -> None:
        if repo_backups:
            try:
                restore_repo_state(repo_backups)
            except Exception:
                pass
        if not timer_restored:
            restore_timer()
        if repo_backup_root is not None:
            shutil.rmtree(repo_backup_root, ignore_errors=True)
''',
        '''    def cleanup() -> None:
        if repo_backups:
            try:
                restore_repo_state(repo_backups)
                run(
                    ["git", "reset", "--mixed", EXPECTED_HEAD],
                    check=False,
                    timeout=30,
                )
            except Exception:
                pass
        if not timer_restored:
            try:
                restore_timer()
            except Exception:
                pass
        if repo_backup_root is not None:
            shutil.rmtree(repo_backup_root, ignore_errors=True)
''',
        "REPO_INDEX_AND_TIMER_CLEANUP",
    )

    source = replace_once(
        source,
        '''    if not git("diff", "--cached", "--name-only"):
        raise RuntimeError("A24_NO_STAGED_CHANGES")
    git("commit", "-m", SUBJECT)

    repo_backups = {}
    restore_timer()
    timer_after = systemctl_state(TIMER)
    if timer_after["active"] != timer_initial["active"]:
        raise RuntimeError("A24_TIMER_ACTIVE_STATE_NOT_RESTORED")
    if timer_after["enabled"] != timer_initial["enabled"]:
        raise RuntimeError("A24_TIMER_ENABLED_STATE_CHANGED")
    verify_persistent_runtime(a23)

    atexit.unregister(cleanup)
''',
        '''    if not git("diff", "--cached", "--name-only"):
        raise RuntimeError("A24_NO_STAGED_CHANGES")

    restore_timer()
    timer_after = systemctl_state(TIMER)
    if timer_after["active"] != timer_initial["active"]:
        raise RuntimeError("A24_TIMER_ACTIVE_STATE_NOT_RESTORED")
    if timer_after["enabled"] != timer_initial["enabled"]:
        raise RuntimeError("A24_TIMER_ENABLED_STATE_CHANGED")
    verify_persistent_runtime(a23)

    git("commit", "-m", SUBJECT)
    repo_backups = {}
    atexit.unregister(cleanup)
''',
        "RESTORE_TIMER_BEFORE_COMMIT",
    )

    return source


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    transformed = transform(source)
    code = compile(transformed, str(Path(__file__).resolve()), "exec")
    namespace = {
        "__name__": "__main__",
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
    }
    exec(code, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
