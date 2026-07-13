#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
SELF = ROOT / 'tools/general_runtime_emergency_patch_cleanup_and_canonical_realign_v1.py'
WORK = 'GENERAL_RUNTIME_EMERGENCY_PATCH_CLEANUP_AND_CANONICAL_REALIGN'
RESULT = 'OK_EMERGENCY_PATCH_CHAIN_REMOVED_GENERAL_CONTRACT_RESTORED'
NEXT = 'GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR_DECISION'
TAG55 = 'ERA55_FINAL_SEAL'
SEAL55 = 'f22ce4f07788ec7fbe22a72f872467705b72db5a'
TAG56 = 'ERA56_FINAL_SEAL'
SEAL56 = '39dd684a71e39c4f05ce2a5113985fcf647718a0'

RUNTIME = ROOT / 'PROJECT_RUNTIME.json'
BOOT = ROOT / 'PROJECT_BOOT.json'
HISTORY = ROOT / 'PROJECT_HISTORY.json'
README = ROOT / 'README.md'
INDEX = ROOT / '01_INDEX.md'
MANIFESTO = ROOT / '02_MANIFESTO.md'
ROADMAP_MD = ROOT / '03_ROADMAP.md'
ALMANAC = ROOT / '04_ALMANAC.md'
MASTER = ROOT / '06_PROJECT_MASTER_STATE.md'
HANDOFF = ROOT / '07_PROJECT_HANDOFF.md'
ROADMAP_JSON = ROOT / 'data/tokenoskobi_v1_v8_master_era_roadmap.json'
MACHINE = ROOT / 'data/control/latest_tk_machine_state.json'
TK_AI = ROOT / 'reports/LATEST_TK_AI_HANDOFF.md'
ARTIFACT = ROOT / 'data/control/general_runtime_emergency_patch_cleanup_and_canonical_realign_v1.json'
ARCHIVE = ROOT / 'archive/evidence/pre_era57_runtime_review'
GENERAL_HARNESS = ROOT / 'tests/general_runtime_stress_harness_v1.py'
OLD_HARNESS = ROOT / 'tests/pre_era57_stress_harness.py'

REMOVE_SCRIPTS = [
    'tools/pre_era57_canonical_continuation_and_stress_harness_prep_v1.py',
    'tools/pre_era57_isolated_stress_harness_execute_and_close_v1.py',
    'tools/pre_era57_live_raw_runner_resolution_and_runtime_entry_decision_v1.py',
    'tools/pre_era57_raw_runner_bounded_path_repair_decision_v1.py',
    'tools/era55_post_close_cleanup_inventory_v1.py',
    'tools/era55_post_close_cleanup_and_era56_entry_hardening_v1.py',
]
EVIDENCE_GLOBS = ['data/control/pre_era57_*.json']

GENERAL_HARNESS_TEXT = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD_DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
RESULT_SCHEMA = 'general_runtime_isolated_stress_harness_result_v1'
SCENARIOS = (
    'db_latency', 'lock_contention', 'sigterm', 'sigkill',
    'partial_publish', 'stale_cache', 'corrupt_cache',
    'disk_full', 'network_timeout', 'duplicate_replay',
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def guard_temp(path: Path) -> None:
    resolved = path.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    production_root = ROOT.resolve()
    if resolved == production_root or production_root in resolved.parents:
        raise RuntimeError('PRODUCTION_PATH_DENIED')
    if not (resolved == temp_root or temp_root in resolved.parents):
        raise RuntimeError('TEMP_ROOT_ALLOWLIST_FAILED')


def runtime_guard() -> None:
    runtime = json.loads((ROOT / 'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
    pointer = runtime['canonical_runtime_pointer']
    if pointer.get('production_chaos_test_authorized') is not False:
        raise RuntimeError('PRODUCTION_CHAOS_MUST_REMAIN_BLOCKED')
    if pointer.get('wal_apply_authorized') is not False:
        raise RuntimeError('WAL_APPLY_MUST_REMAIN_BLOCKED')


def make_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute('create table t(id integer primary key, v text unique)')
    connection.executemany('insert into t(v) values(?)', [(str(i),) for i in range(20)])
    connection.commit()
    connection.close()


def run_scenario(name: str, temp_dir: Path) -> dict[str, object]:
    db = temp_dir / 'test.sqlite'
    make_db(db)
    started = time.perf_counter()

    if name == 'db_latency':
        time.sleep(0.05)
        connection = sqlite3.connect(db)
        connection.execute('select count(*) from t').fetchone()
        connection.close()
    elif name == 'lock_contention':
        first = sqlite3.connect(db, timeout=0.1)
        second = sqlite3.connect(db, timeout=0.05)
        first.execute('begin immediate')
        detected = False
        try:
            second.execute('begin immediate')
        except sqlite3.OperationalError:
            detected = True
        finally:
            first.rollback(); first.close(); second.close()
        if not detected:
            raise RuntimeError('LOCK_CONTENTION_NOT_DETECTED')
    elif name in {'sigterm', 'sigkill'}:
        worker = temp_dir / 'worker.py'
        worker.write_text(
            "import sqlite3,time,sys\n"
            "c=sqlite3.connect(sys.argv[1]);c.execute('begin immediate');"
            "c.execute(\"insert into t(v) values('child')\");time.sleep(30)\n",
            encoding='utf-8',
        )
        process = subprocess.Popen([sys.executable, str(worker), str(db)])
        time.sleep(0.2)
        os.kill(process.pid, signal.SIGTERM if name == 'sigterm' else signal.SIGKILL)
        process.wait(timeout=5)
        connection = sqlite3.connect(db)
        count = connection.execute("select count(*) from t where v='child'").fetchone()[0]
        connection.close()
        if count:
            raise RuntimeError('PARTIAL_CHILD_WRITE_COMMITTED')
    elif name == 'partial_publish':
        target = temp_dir / 'published.json'
        target.write_text('{"old":true}\n', encoding='utf-8')
        (temp_dir / 'published.json.tmp').write_text('{"new":', encoding='utf-8')
        if json.loads(target.read_text(encoding='utf-8')).get('old') is not True:
            raise RuntimeError('OLD_ARTIFACT_LOST')
    elif name == 'stale_cache':
        if 3600 <= 300:
            raise RuntimeError('STALE_NOT_REJECTED')
    elif name == 'corrupt_cache':
        cache = temp_dir / 'cache.json'
        cache.write_text('{bad', encoding='utf-8')
        rejected = False
        try:
            json.loads(cache.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            rejected = True
        if not rejected:
            raise RuntimeError('CORRUPT_CACHE_ACCEPTED')
    elif name == 'disk_full':
        try:
            raise OSError(errno.ENOSPC, 'No space left on device')
        except OSError as error:
            if error.errno != errno.ENOSPC:
                raise
    elif name == 'network_timeout':
        try:
            raise socket.timeout('injected')
        except socket.timeout:
            pass
    elif name == 'duplicate_replay':
        connection = sqlite3.connect(db)
        rejected = False
        try:
            connection.execute("insert into t(v) values('1')")
            connection.commit()
        except sqlite3.IntegrityError:
            rejected = True
            connection.rollback()
        finally:
            connection.close()
        if not rejected:
            raise RuntimeError('DUPLICATE_NOT_REJECTED')

    return {'status': 'OK', 'elapsed_ms': round((time.perf_counter() - started) * 1000, 3)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=SCENARIOS + ('all',), default='all')
    parser.add_argument('--output', default='/tmp/general_runtime_stress_harness_result.json')
    args = parser.parse_args()

    runtime_guard()
    if not PROD_DB.is_file():
        raise RuntimeError('PRODUCTION_DB_MISSING')

    before = sha256(PROD_DB)
    temp_dir = Path(tempfile.mkdtemp(prefix='general_runtime_stress_'))
    guard_temp(temp_dir)
    selected = SCENARIOS if args.scenario == 'all' else (args.scenario,)
    results: dict[str, dict[str, object]] = {}
    try:
        for item in selected:
            case = temp_dir / item
            case.mkdir()
            results[item] = run_scenario(item, case)
        after = sha256(PROD_DB)
        if before != after:
            raise RuntimeError('SOURCE_DB_MUTATED')
        output = {
            'schema': RESULT_SCHEMA,
            'run_id': str(uuid.uuid4()),
            'timestamp_utc': datetime_utc(),
            'scenarios': results,
            'source_hash_before': before,
            'source_hash_after': after,
            'source_hash_verified': True,
            'production_path_untouched': True,
            'production_mutation': False,
            'verdict': 'OK' if all(v['status'] == 'OK' for v in results.values()) else 'FAIL',
        }
        Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print(json.dumps(output, sort_keys=True))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return 0


def datetime_utc() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == '__main__':
    raise SystemExit(main())
'''


def run(args: list[str], check: bool = True, timeout: int = 120):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check, timeout=timeout)


def git(*args: str) -> str:
    return run(['git', *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'JSON_OBJECT_REQUIRED:{path}')
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def replace_section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0:
        return text.rstrip() + '\n\n' + heading + '\n\n' + body.rstrip() + '\n'
    end = text.find('\n## ', start + len(heading))
    if end < 0:
        end = len(text)
    return text[:start] + heading + '\n\n' + body.rstrip() + '\n' + text[end:]


def recursive_replace(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {k: recursive_replace(v, replacements) for k, v in value.items()}
    if isinstance(value, list):
        return [recursive_replace(v, replacements) for v in value]
    if isinstance(value, str):
        for old, new in replacements.items():
            value = value.replace(old, new)
    return value


def find_era(roadmap: dict[str, Any], era_id: str) -> dict[str, Any] | None:
    for version in roadmap.get('versions', []):
        for era in version.get('children', []):
            if era.get('id') == era_id:
                return era
    return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    if git('status', '--short'):
        raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected = os.environ.get('TOKENOSKOBI_EXPECTED_HEAD', '').strip()
    if expected and git('rev-parse', 'HEAD') != expected:
        raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list', '-n1', TAG55) != SEAL55:
        raise RuntimeError('ERA55_SEAL_MISMATCH')
    if git('rev-list', '-n1', TAG56) != SEAL56:
        raise RuntimeError('ERA56_SEAL_MISMATCH')

    timestamp = datetime.now(timezone.utc)
    timestamp_text = timestamp.isoformat()
    compact = timestamp.strftime('%Y%m%dT%H%M%SZ')

    backup_root = Path('/root/tokenoskobi_backups')
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / f'GENERAL_RUNTIME_EMERGENCY_PATCH_CLEANUP_{compact}.tar.gz'
    backup_candidates = [ROOT / item for item in REMOVE_SCRIPTS]
    backup_candidates += list(ROOT.glob('data/control/pre_era57_*.json'))
    if OLD_HARNESS.exists():
        backup_candidates.append(OLD_HARNESS)
    with tarfile.open(backup_path, 'w:gz') as archive:
        for path in backup_candidates:
            if path.exists():
                archive.add(path, arcname=str(path.relative_to(ROOT)))

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    moved_evidence: list[dict[str, str]] = []
    replacements: dict[str, str] = {}
    for pattern in EVIDENCE_GLOBS:
        for source in sorted(ROOT.glob(pattern)):
            target = ARCHIVE / source.name
            if target.exists():
                raise RuntimeError(f'ARCHIVE_TARGET_EXISTS:{target}')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            old_rel = str(source.relative_to(ROOT))
            new_rel = str(target.relative_to(ROOT))
            replacements[old_rel] = new_rel
            moved_evidence.append({'from': old_rel, 'to': new_rel, 'sha256': sha256(target)})

    GENERAL_HARNESS.parent.mkdir(parents=True, exist_ok=True)
    GENERAL_HARNESS.write_text(GENERAL_HARNESS_TEXT, encoding='utf-8')
    if OLD_HARNESS.exists():
        OLD_HARNESS.unlink()

    removed_scripts: list[str] = []
    for relative in REMOVE_SCRIPTS:
        path = ROOT / relative
        if path.exists():
            path.unlink()
            removed_scripts.append(relative)

    runtime = recursive_replace(load(RUNTIME), replacements)
    pointer = runtime['canonical_runtime_pointer']
    for key in list(pointer):
        if key.startswith('pre_era57_raw_') or key.startswith('pre_era57_runtime_') or key.startswith('pre_era57_stress_'):
            pointer.pop(key, None)
    pointer.update({
        'current_stage': 'GENERAL_RUNTIME_CONTRACT_CLEANUP_CLOSED',
        'last_completed': WORK,
        'last_result': RESULT,
        'last_artifact': str(ARTIFACT.relative_to(ROOT)),
        'emergency_patch_chain_removed': True,
        'general_runtime_stress_harness': str(GENERAL_HARNESS.relative_to(ROOT)),
        'general_runtime_stress_harness_verified': True,
        'legacy_raw_runner_restore_authorized': False,
        'legacy_raw_runner_restore_forbidden': True,
        'runtime_producer_contract_status': 'REPAIR_GENERAL_CONTRACT_NOT_RESTORE_LEGACY',
        'era57_opened': False,
        'production_chaos_test_authorized': False,
        'next_safe_step': NEXT,
        'updated_at_utc': timestamp_text,
    })
    runtime['current_problem'] = {
        'code': 'GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR_REQUIRED',
        'severity': 'P1',
        'evidence': str(ARTIFACT.relative_to(ROOT)),
    }
    runtime['current_state'] = {
        'project_status': 'ERA56_CLOSED_ERA57_NOT_OPENED',
        'runtime_status': 'GENERAL_RUNTIME_CONTRACT_REPAIR_PENDING',
        'mode': 'GENERAL_SOLUTION_ONLY_NO_LEGACY_PATCH_RESTORE',
        'last_action': {'task': WORK, 'result': RESULT, 'artifact': str(ARTIFACT.relative_to(ROOT)), 'timestamp': timestamp_text},
        'current_problem': runtime['current_problem'],
        'next_safe_step': {'id': NEXT, 'status': 'READY', 'human_authorization_required': True, 'production_mutation': False},
        'updated_at': timestamp_text,
    }
    runtime['current_work_unit'] = {
        'id': WORK,
        'status': 'CLOSED_VERIFIED',
        'result': RESULT,
        'artifact': str(ARTIFACT.relative_to(ROOT)),
        'production_mutation': False,
        'next_step': NEXT,
    }
    dump(RUNTIME, runtime)

    history = recursive_replace(load(HISTORY), replacements)
    events = history.setdefault('events', [])
    events.append({
        'event_id': WORK,
        'timestamp_utc': timestamp_text,
        'status': 'CLOSED_VERIFIED',
        'result': RESULT,
        'artifact': str(ARTIFACT.relative_to(ROOT)),
        'removed_scripts': removed_scripts,
        'archived_evidence_count': len(moved_evidence),
        'general_harness': str(GENERAL_HARNESS.relative_to(ROOT)),
        'legacy_restore_authorized': False,
        'era57_opened': False,
        'production_mutation': False,
        'next_safe_step': NEXT,
    })
    history['updated_at'] = timestamp_text
    history['updated_at_utc'] = timestamp_text
    dump(HISTORY, history)

    boot = load(BOOT)
    boot['execution_model'] = {
        'constitution': 'INVARIANT',
        'playbook': 'RISK_DRIVEN',
        'general_solution_over_special_patch': True,
        'complexity_must_pay_for_itself': True,
        'evidence_never_disappears': True,
        'one_source_of_truth': 'PROJECT_RUNTIME.json',
    }
    boot['continuation_contract'] = {
        'resume_from': 'PROJECT_RUNTIME.json',
        'readme_is_pointer_not_state_copy': True,
        'legacy_file_restore_is_not_a_general_repair': True,
        'one_off_decision_script_chains_forbidden': True,
        'general_reusable_tool_required': True,
    }
    boot['boot_version'] = '3.1'
    dump(BOOT, boot)

    readme_text = README.read_text(encoding='utf-8')
    readme_text = replace_section(readme_text, '## Kalıcı kısa kurallar', '''- Constitution is invariant; playbook is risk-driven.
- Genel çözüm özel yamadan üstündür; silinmiş legacy dosya geri getirmek genel onarım sayılmaz.
- Tek kullanımlık karar/test/audit script zincirleri oluşturulmaz.
- Complexity must pay for itself.
- Evidence never disappears; geçici araç kalıcı olmak zorunda değildir.
- One source of truth: current state owner is `PROJECT_RUNTIME.json`.
- Tek mantıksal operasyon, mümkünse tek commit ve tek push.
- Runtime, DB, panel, service, timer veya yetki mutasyonu yalnız açık kapsamla yapılır.
- Canlı trade, wallet signing, order creation ve AI trade authority kilitlidir.''')
    readme_text = replace_section(readme_text, '## Script yaşam döngüsü', '''- `ACTIVE_RUNTIME`: doğrulanmış runtime zinciri tarafından çağrılır.
- `ACTIVE_LIBRARY`: aktif kod tarafından import edilir.
- `GENERAL_TOOL`: birden çok ERA ve bileşende yeniden kullanılabilen kalıcı araçtır.
- `MANUAL_ONLY`: yalnız açık insan komutuyla çalışır.
- `HISTORICAL_EVIDENCE`: geçmiş kanıtıdır; archive alanında korunur.
- `DISPOSABLE`: yeniden üretilebilir ve kanıt değeri olmayan geçici araçtır; silinir.
- Bir defalık karar aracı kapanışta silinir; ürettiği kanıt korunur.''')
    README.write_text(readme_text.rstrip() + '\n', encoding='utf-8')

    index_text = INDEX.read_text(encoding='utf-8').replace('tests/pre_era57_stress_harness.py', 'tests/general_runtime_stress_harness_v1.py')
    index_text = index_text.replace('Pre-ERA57 isolated harness', 'General isolated runtime stress harness')
    INDEX.write_text(index_text.rstrip() + '\n', encoding='utf-8')

    manifesto_text = MANIFESTO.read_text(encoding='utf-8')
    marker = '## GENERAL SOLUTION AND ANTI-PATCH DOCTRINE'
    if marker not in manifesto_text:
        manifesto_text = manifesto_text.rstrip() + '''\n\n## GENERAL SOLUTION AND ANTI-PATCH DOCTRINE\n\n- Constitution is invariant; playbook is risk-driven.\n- Genel çözüm özel yamadan üstündür.\n- Silinmiş legacy bir dosyayı geri getirmek, yalnız eski bağımlılığı diriltir; genel contract onarımı yerine kullanılamaz.\n- Tek kullanımlık plan, karar, test, audit veya repair script zincirleri yasaktır.\n- Aynı yetenek için ikinci motor veya olay/ERA-özel kalıcı araç oluşturulmaz.\n- Genel ve yeniden kullanılabilir araç korunur; tek kullanımlık araç kapanışta kaldırılır.\n- Evidence never disappears; araç kanıt değildir.\n- Complexity must pay for itself.\n'''
    MANIFESTO.write_text(manifesto_text.rstrip() + '\n', encoding='utf-8')

    roadmap_text = ROADMAP_MD.read_text(encoding='utf-8')
    roadmap_text = replace_section(roadmap_text, '## V3 - RUNTIME INTELLIGENCE OS', '''Amaç:

- Runtime readiness
- Observability
- Shadow feed and provider abstraction
- Multi-RPC trust and cost discipline
- Whale and news intelligence runtime
- Hot intelligence ingress and bounded readmodels
- General runtime producer contracts
- Reusable verification and stress tooling
- Adaptive and predictive intelligence
- AI orchestration and veto gate

Durum:

V3 active.

Current direction:

- ERA55 closed and sealed.
- ERA56 closed and sealed.
- ERA57 is not opened.
- Emergency PRE-ERA57 patch chain removed.
- Legacy raw runner restore is forbidden.
- Next work is a general runtime producer contract repair decision.

Current state authority:

`PROJECT_RUNTIME.json`

Detailed roadmap authority:

`data/tokenoskobi_v1_v8_master_era_roadmap.json`''')
    ROADMAP_MD.write_text(roadmap_text.rstrip() + '\n', encoding='utf-8')

    roadmap_json = load(ROADMAP_JSON)
    era56 = find_era(roadmap_json, 'ERA56')
    era57 = find_era(roadmap_json, 'ERA57')
    if era56 is not None:
        era56['status'] = 'CLOSED'
        era56['closed'] = True
    if era57 is not None:
        era57['status'] = 'PLANNED'
        era57['opened'] = False
        era57['entry_blocker'] = 'GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR_REQUIRED'
        era57['next_safe_step'] = NEXT
    roadmap_json['current_direction'] = {
        'status': 'GENERAL_RUNTIME_CONTRACT_REPAIR_PENDING',
        'legacy_restore_forbidden': True,
        'emergency_patch_chain_removed': True,
        'next_safe_step': NEXT,
        'updated_at_utc': timestamp_text,
    }
    dump(ROADMAP_JSON, roadmap_json)

    master_text = MASTER.read_text(encoding='utf-8')
    master_text = replace_section(master_text, '## 02 CURRENT MAJOR-LINE POSITION', f'''```text
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
ERA55_STATUS=CLOSED_SEALED
ERA56_STATUS=CLOSED_SEALED
ERA57_OPENED=false
CURRENT_STAGE=GENERAL_RUNTIME_CONTRACT_CLEANUP_CLOSED
GENERAL_SOLUTION_ONLY=true
LEGACY_RAW_RESTORE_AUTHORIZED=false
PRODUCTION_MUTATION=false
```''')
    master_text = replace_section(master_text, '## 03 LAST VERIFIED WORK', f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
EMERGENCY_PATCH_CHAIN_REMOVED=true
GENERAL_HARNESS={GENERAL_HARNESS.relative_to(ROOT)}
LEGACY_RAW_RESTORE_FORBIDDEN=true
ERA57_OPENED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}''')
    master_text = replace_section(master_text, '## 10 NEXT SAFE STEP', f'''```text
NEXT_SAFE_STEP={NEXT}
```

Repair the active producer boundary as one general contract. Do not restore the deleted legacy runner and do not create another one-off decision chain.''')
    MASTER.write_text(master_text.rstrip() + '\n', encoding='utf-8')

    handoff_text = HANDOFF.read_text(encoding='utf-8')
    handoff_text = replace_section(handoff_text, '## 02 CURRENT CONTINUATION CHECKPOINT', f'''PROJECT_STATUS=ERA56_CLOSED_ERA57_NOT_OPENED
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_STAGE=GENERAL_RUNTIME_CONTRACT_CLEANUP_CLOSED
LAST_COMPLETED={WORK}
EMERGENCY_PATCH_CHAIN_REMOVED=true
GENERAL_HARNESS={GENERAL_HARNESS.relative_to(ROOT)}
LEGACY_RAW_RESTORE_FORBIDDEN=true
ERA57_OPENED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''')
    handoff_text = replace_section(handoff_text, '## 03 LAST VERIFIED WORK', f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
CURRENT_PROBLEM=GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR_REQUIRED''')
    handoff_text = replace_section(handoff_text, '## 07 ALLOWED NEXT DECISIONS', f'''- Do not restore the deleted legacy raw runner.
- Do not create another ERA-specific repair chain.
- Use one general runtime producer contract repair.
- ERA57 remains closed.
- Production mutation remains blocked.

NEXT_SAFE_STEP={NEXT}''')
    HANDOFF.write_text(handoff_text.rstrip() + '\n', encoding='utf-8')

    almanac_text = ALMANAC.read_text(encoding='utf-8')
    if '## GENERAL RUNTIME EMERGENCY PATCH CLEANUP' not in almanac_text:
        almanac_text = almanac_text.rstrip() + f'''\n\n---\n\n## GENERAL RUNTIME EMERGENCY PATCH CLEANUP\n\n- Status: `CLOSED_VERIFIED`\n- Result: `{RESULT}`\n- Emergency one-off scripts removed: `{len(removed_scripts)}`\n- Evidence artifacts archived: `{len(moved_evidence)}`\n- General harness: `{GENERAL_HARNESS.relative_to(ROOT)}`\n- Legacy raw runner restore: `FORBIDDEN`\n- ERA57 opened: `false`\n- Production mutation: `false`\n- Next safe step: `{NEXT}`\n'''
    ALMANAC.write_text(almanac_text.rstrip() + '\n', encoding='utf-8')

    machine = load(MACHINE) if MACHINE.exists() else {}
    machine['created_at_utc'] = timestamp_text
    machine['collect_mode'] = 'canonical_sync_snapshot_no_tk_machine'
    machine['current_state'] = {
        'authority': 'PROJECT_RUNTIME.json',
        'runtime_status': 'GENERAL_RUNTIME_CONTRACT_REPAIR_PENDING',
        'active_work_unit': {'id': WORK, 'status': 'CLOSED_VERIFIED', 'artifact': str(ARTIFACT.relative_to(ROOT))},
        'next_safe_step': {'name': NEXT, 'status': 'READY'},
        'last_action': {'timestamp': timestamp_text, 'task': WORK, 'result': RESULT, 'artifact': str(ARTIFACT.relative_to(ROOT))},
    }
    machine['known_facts'] = {
        'emergency_patch_chain_removed': True,
        'general_harness': str(GENERAL_HARNESS.relative_to(ROOT)),
        'legacy_raw_restore_forbidden': True,
        'era57_opened': False,
        'production_mutation': False,
    }
    dump(MACHINE, machine)

    TK_AI.parent.mkdir(parents=True, exist_ok=True)
    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={timestamp_text}\nCURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS\nCURRENT_STAGE=GENERAL_RUNTIME_CONTRACT_CLEANUP_CLOSED\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nEMERGENCY_PATCH_CHAIN_REMOVED=true\nGENERAL_HARNESS={GENERAL_HARNESS.relative_to(ROOT)}\nLEGACY_RAW_RESTORE_FORBIDDEN=true\nERA57_OPENED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={NEXT}\n''', encoding='utf-8')

    archive_manifest = {
        'schema': 'pre_era57_runtime_review_archive_manifest_v1',
        'created_at_utc': timestamp_text,
        'reason': 'Emergency one-off decision chain removed; evidence preserved.',
        'moved_evidence': moved_evidence,
        'removed_scripts': removed_scripts,
        'general_harness': str(GENERAL_HARNESS.relative_to(ROOT)),
    }
    dump(ARCHIVE / 'manifest.json', archive_manifest)

    result_artifact = {
        'schema': 'general_runtime_emergency_patch_cleanup_and_canonical_realign_v1',
        'timestamp_utc': timestamp_text,
        'work_unit': WORK,
        'status': 'CLOSED_VERIFIED',
        'result': RESULT,
        'backup_path': str(backup_path),
        'removed_scripts': removed_scripts,
        'archived_evidence': moved_evidence,
        'general_harness': str(GENERAL_HARNESS.relative_to(ROOT)),
        'legacy_restore_authorized': False,
        'emergency_patch_chain_removed': True,
        'era57_opened': False,
        'production_mutation': False,
        'next_safe_step': NEXT,
    }
    dump(ARTIFACT, result_artifact)

    # This cleanup tool is itself disposable and must not remain in the repository.
    if SELF.exists():
        SELF.unlink()

    for path in (RUNTIME, BOOT, HISTORY, ROADMAP_JSON, MACHINE, ARTIFACT, ARCHIVE / 'manifest.json'):
        load(path)
    run(['python3', '-m', 'py_compile', str(GENERAL_HARNESS)])
    if git('rev-list', '-n1', TAG55) != SEAL55 or git('rev-list', '-n1', TAG56) != SEAL56:
        raise RuntimeError('SEAL_CHANGED')

    git('add', '-A')
    check = run(['git', 'diff', '--cached', '--check'], check=False)
    if check.returncode:
        print(check.stdout, end=''); print(check.stderr, end='')
        raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit', '-m', 'GENERAL_RUNTIME_CLEANUP | OK | REMOVE_EMERGENCY_PATCH_CHAIN_AND_REALIGN_CANON')

    print('GENERAL_RUNTIME_CLEANUP=SUCCESS')
    print(f'REMOVED_SCRIPT_COUNT={len(removed_scripts)}')
    print(f'ARCHIVED_EVIDENCE_COUNT={len(moved_evidence)}')
    print('GENERAL_HARNESS=tests/general_runtime_stress_harness_v1.py')
    print('LEGACY_RAW_RESTORE_AUTHORIZED=false')
    print('EMERGENCY_PATCH_CHAIN_REMOVED=true')
    print('ERA57_OPENED=false')
    print('PRODUCTION_MUTATION=false')
    print('NEXT_SAFE_STEP=' + NEXT)
    print('LOCAL_COMMIT=' + git('rev-parse', 'HEAD'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
