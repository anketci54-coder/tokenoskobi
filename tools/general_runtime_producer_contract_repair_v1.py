#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
SELF = ROOT / 'tools/general_runtime_producer_contract_repair_v1.py'
WRAPPER = ROOT / 'tools/news_radar_refresh_runner_v1.py'
PRODUCER = ROOT / 'tools/news_source_ingestion_runner_v1.py'
RUNTIME = ROOT / 'PROJECT_RUNTIME.json'
HISTORY = ROOT / 'PROJECT_HISTORY.json'
MASTER = ROOT / '06_PROJECT_MASTER_STATE.md'
HANDOFF = ROOT / '07_PROJECT_HANDOFF.md'
ALMANAC = ROOT / '04_ALMANAC.md'
ARTIFACT = ROOT / 'data/control/general_runtime_producer_contract_repair_v1.json'
DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
SERVICE = 'tokenoskobi-news-radar-refresh.service'
ORDER_LOG = Path('/run/tokenoskobi/era55a23_guarded_order.log')
WORK = 'GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR'
NEXT = 'ERA57_AUTONOMOUS_RESEARCH_LAYER_OPENING_DECISION'
HISTORY_COMMIT = 'a9cf5f185b2d11f4177de24858358892aba66e79'
HISTORY_PATH = 'tools/news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.py'
EXPECTED_BLOB = '04db0f7c2f0a09261d2f782f685993086e163fd3'
TAG55 = 'ERA55_FINAL_SEAL'; SEAL55 = 'f22ce4f07788ec7fbe22a72f872467705b72db5a'
TAG56 = 'ERA56_FINAL_SEAL'; SEAL56 = '39dd684a71e39c4f05ce2a5113985fcf647718a0'


def run(args: list[str], check: bool = True, timeout: int = 120, env: dict[str, str] | None = None):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check, timeout=timeout, env=env)


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
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def replace_section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0:
        return text.rstrip() + '\n\n' + heading + '\n\n' + body.rstrip() + '\n'
    end = text.find('\n## ', start + len(heading))
    if end < 0: end = len(text)
    return text[:start] + heading + '\n\n' + body.rstrip() + '\n' + text[end:]


def build_general_producer(source: str) -> str:
    source = source.replace(
        'ROOT="/root/tokenoskobi_clean_v1"\nDB=f"{ROOT}/data/tokenoskobi_clean_v1.sqlite"',
        'ROOT=os.environ.get("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1")\nDB=os.environ.get("TOKENOSKOBI_DB_PATH", f"{ROOT}/data/tokenoskobi_clean_v1.sqlite")',
        1,
    )
    source = source.replace(
        'LOCK_FILE=f"{RUN_DIR}/news_radar_refresh.lock"',
        'LOCK_FILE=os.environ.get("TOKENOSKOBI_SOURCE_INGESTION_LOCK_PATH", f"{RUN_DIR}/news_source_ingestion_runner_v1.lock")',
        1,
    )
    source = source.replace(
        'STATE_FILE=f"{ROOT}/data/news_radar_timer_state_v1.json"',
        'STATE_FILE=os.environ.get("TOKENOSKOBI_SOURCE_INGESTION_STATE_PATH", f"{ROOT}/data/news_source_ingestion_state_v1.json")',
        1,
    )
    source = source.replace(
        'REPORT=f"{ROOT}/reports/LATEST_NEWS_RADAR_TIMER_RUN.md"',
        'REPORT=os.environ.get("TOKENOSKOBI_SOURCE_INGESTION_REPORT_PATH", f"{ROOT}/reports/LATEST_NEWS_SOURCE_INGESTION_RUN.md")',
        1,
    )
    source = source.replace(
        'JSON_OUT=f"{ROOT}/data/latest_news_radar_timer_run.json"',
        'JSON_OUT=os.environ.get("TOKENOSKOBI_SOURCE_INGESTION_JSON_PATH", f"{ROOT}/data/latest_news_source_ingestion_run.json")',
        1,
    )
    source = source.replace('TokenoskobiNewsRadarTimer/1.0', 'TokenoskobiSourceIngestion/1.0')
    header = '''# GENERAL CONTRACT: source ingestion only. No trade, wallet, signing or order authority.\nPRODUCER_CONTRACT_VERSION = "NEWS_SOURCE_INGESTION_V1"\n'''
    insert_at = source.find('\nROOT=')
    if insert_at < 0:
        raise RuntimeError('HISTORICAL_PRODUCER_ROOT_MARKER_MISSING')
    source = source[:insert_at + 1] + header + source[insert_at + 1:]
    if 'PRE_DERIVED_BINDING' in source or 'ORIGINAL_NEWS27A11' in source:
        raise RuntimeError('LEGACY_CHAIN_REFERENCE_REMAINED_IN_PRODUCER')
    return source


def repair_wrapper(text: str) -> str:
    pattern = re.compile(r'ORIGINAL = Path\(\n    os\.environ\.get\(\n        "TOKENOSKOBI_NEWS_ORIGINAL_PATH",\n        str\(\n            ROOT\n            / "tools"\n            / "news_radar_refresh_runner_v1\.PRE_DERIVED_BINDING_20260709T171244Z\.py"\n        \),\n    \)\n\)')
    replacement = '''PRODUCER = Path(\n    os.environ.get(\n        "TOKENOSKOBI_NEWS_PRODUCER_PATH",\n        str(ROOT / "tools" / "news_source_ingestion_runner_v1.py"),\n    )\n)'''
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError('WRAPPER_LEGACY_BLOCK_NOT_FOUND')
    text = text.replace('[PYTHON_BIN, str(ORIGINAL)] + sys.argv[1:]', '[PYTHON_BIN, str(PRODUCER)] + sys.argv[1:]', 1)
    text = text.replace('ORIGINAL', 'PRODUCER')
    anchor = 'ORDER_LOG = os.environ.get("TOKENOSKOBI_A10_ORDER_LOG")\n'
    timeout_block = '''ORDER_LOG = os.environ.get("TOKENOSKOBI_A10_ORDER_LOG")\nSUBPROCESS_TIMEOUT_SECONDS = int(os.environ.get("TOKENOSKOBI_RUNNER_SUBPROCESS_TIMEOUT_SECONDS", "60"))\n\n\ndef run_child(command: list[str], stage: str) -> int:\n    try:\n        result = subprocess.run(\n            command,\n            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},\n            timeout=SUBPROCESS_TIMEOUT_SECONDS,\n        )\n        return int(result.returncode)\n    except subprocess.TimeoutExpired:\n        print(f"[CHILD_TIMEOUT] stage={stage} timeout={SUBPROCESS_TIMEOUT_SECONDS}", flush=True)\n        return 124\n'''
    if anchor not in text:
        raise RuntimeError('WRAPPER_ORDER_LOG_ANCHOR_MISSING')
    text = text.replace(anchor, timeout_block, 1)
    text = re.sub(
        r'result = subprocess\.run\(\n        \[PYTHON_BIN, str\(HOT\), "--runtime-refresh"\],\n        env=\{\*\*os\.environ, "PYTHONDONTWRITEBYTECODE": "1"\},\n    \)\.returncode',
        'result = run_child([PYTHON_BIN, str(HOT), "--runtime-refresh"], "HOT")', text, count=1,
    )
    text = re.sub(
        r'raw = subprocess\.run\(\n        \[PYTHON_BIN, str\(PRODUCER\)\] \+ sys\.argv\[1:\],\n        env=\{\*\*os\.environ, "PYTHONDONTWRITEBYTECODE": "1"\},\n    \)\n    append_order\(f"RAW_END:\{raw\.returncode\}"\)\n    if raw\.returncode != 0:\n        return raw\.returncode',
        'raw_returncode = run_child([PYTHON_BIN, str(PRODUCER)] + sys.argv[1:], "RAW")\n    append_order(f"RAW_END:{raw_returncode}")\n    if raw_returncode != 0:\n        return raw_returncode', text, count=1,
    )
    text = re.sub(
        r'derived = subprocess\.run\(\n        \[\n            PYTHON_BIN,\n            str\(HELPER\),\n            "--db-path",\n            str\(DB\),\n            "--write",\n            "--stage",\n            "NEWS_SYSTEMD_TIMER_DERIVED_REFRESH",\n        \],\n        env=\{\*\*os\.environ, "PYTHONDONTWRITEBYTECODE": "1"\},\n    \)\n    append_order\(f"DERIVED_END:\{derived\.returncode\}"\)\n    if derived\.returncode != 0:\n        return derived\.returncode',
        'derived_returncode = run_child(\n        [PYTHON_BIN, str(HELPER), "--db-path", str(DB), "--write", "--stage", "NEWS_SYSTEMD_TIMER_DERIVED_REFRESH"],\n        "DERIVED",\n    )\n    append_order(f"DERIVED_END:{derived_returncode}")\n    if derived_returncode != 0:\n        return derived_returncode', text, count=1,
    )
    check_anchor = '    writer_enabled = env_true("TOKENOSKOBI_LEDGER_WRITER_ENABLED")\n'
    check_block = '''    writer_enabled = env_true("TOKENOSKOBI_LEDGER_WRITER_ENABLED")\n    required_paths = {"producer": PRODUCER, "derived": HELPER, "hot": HOT}\n    missing = [f"{name}:{path}" for name, path in required_paths.items() if not path.is_file()]\n    if missing:\n        print("[RUNTIME_CONTRACT_MISSING] " + ",".join(missing), flush=True)\n        return 78\n'''
    if check_anchor not in text:
        raise RuntimeError('WRAPPER_PIPELINE_ANCHOR_MISSING')
    text = text.replace(check_anchor, check_block, 1)
    if 'PRE_DERIVED_BINDING' in text or 'TOKENOSKOBI_NEWS_ORIGINAL_PATH' in text:
        raise RuntimeError('LEGACY_REFERENCE_REMAINED_IN_WRAPPER')
    return text


def db_integrity(path: Path) -> str:
    con = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    try: return str(con.execute('PRAGMA integrity_check').fetchone()[0])
    finally: con.close()


def main() -> int:
    if git('status', '--short'):
        raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected = os.environ.get('TOKENOSKOBI_EXPECTED_HEAD', '').strip()
    if expected and git('rev-parse', 'HEAD') != expected:
        raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list', '-n1', TAG55) != SEAL55 or git('rev-list', '-n1', TAG56) != SEAL56:
        raise RuntimeError('SEAL_MISMATCH')
    runtime = load(RUNTIME)
    pointer = runtime['canonical_runtime_pointer']
    if pointer.get('next_safe_step') != 'GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR_DECISION':
        raise RuntimeError('NEXT_STEP_MISMATCH')
    if pointer.get('legacy_raw_runner_restore_forbidden') is not True:
        raise RuntimeError('ANTI_LEGACY_RESTORE_GUARD_MISSING')

    ts = datetime.now(timezone.utc).isoformat()
    compact = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = Path('/root/tokenoskobi_backups') / f'GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR_{compact}.tar.gz'
    backup.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(backup, 'w:gz') as tar:
        for path in (WRAPPER, RUNTIME, HISTORY, MASTER, HANDOFF, ALMANAC):
            tar.add(path, arcname=str(path.relative_to(ROOT)))

    blob = git('rev-parse', f'{HISTORY_COMMIT}:{HISTORY_PATH}')
    if blob != EXPECTED_BLOB:
        raise RuntimeError('HISTORY_BLOB_MISMATCH')
    historical = run(['git', 'show', f'{HISTORY_COMMIT}:{HISTORY_PATH}']).stdout
    producer_text = build_general_producer(historical)
    wrapper_text = repair_wrapper(WRAPPER.read_text(encoding='utf-8'))
    PRODUCER.write_text(producer_text, encoding='utf-8')
    WRAPPER.write_text(wrapper_text, encoding='utf-8')
    run(['python3', '-m', 'py_compile', str(PRODUCER), str(WRAPPER)])

    temp_root = Path(tempfile.mkdtemp(prefix='general_producer_contract_'))
    temp_db = temp_root / 'data/tokenoskobi_clean_v1.sqlite'
    try:
        (temp_root / 'data').mkdir(parents=True)
        (temp_root / 'run').mkdir(parents=True)
        (temp_root / 'logs/news_radar').mkdir(parents=True)
        (temp_root / 'reports').mkdir(parents=True)
        preview = temp_root / '_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096/public/news_radar_tr_preview'
        preview.mkdir(parents=True)
        (preview / 'index.html').write_text('<html><body></body></html>\n', encoding='utf-8')
        shutil.copy2(DB, temp_db)
        before = sha256(DB)
        env = {**os.environ, 'TOKENOSKOBI_ROOT': str(temp_root), 'TOKENOSKOBI_DB_PATH': str(temp_db), 'PYTHONDONTWRITEBYTECODE': '1'}
        smoke = run(['/usr/bin/python3', str(PRODUCER)], check=False, timeout=75, env=env)
        if smoke.returncode not in (0, 2):
            raise RuntimeError(f'TEMP_PRODUCER_SMOKE_FAILED:{smoke.returncode}:{smoke.stderr[-1000:]}')
        if db_integrity(temp_db) != 'ok' or sha256(DB) != before:
            raise RuntimeError('TEMP_TEST_ISOLATION_FAILED')
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    before_integrity = db_integrity(DB)
    log_before = ORDER_LOG.stat().st_size if ORDER_LOG.exists() else 0
    service = run(['systemctl', 'start', SERVICE], check=False, timeout=90)
    if service.returncode != 0:
        raise RuntimeError('CONTROLLED_SERVICE_CYCLE_FAILED:' + service.stderr[-1000:])
    service_result = run(['systemctl', 'show', SERVICE, '-p', 'Result', '--value'], check=False).stdout.strip()
    log_delta = ''
    if ORDER_LOG.exists():
        with ORDER_LOG.open('rb') as handle:
            handle.seek(log_before); log_delta = handle.read().decode('utf-8', 'replace')
    markers = {
        'raw_ok': 'RAW_END:0' in log_delta,
        'derived_ok': 'DERIVED_END:0' in log_delta,
        'hot_ok': 'HOT_END:0' in log_delta,
    }
    if service_result != 'success' or not all(markers.values()) or db_integrity(DB) != 'ok':
        raise RuntimeError('NATURAL_CYCLE_CONTRACT_VERIFY_FAILED:' + json.dumps({'service_result': service_result, 'markers': markers, 'log_delta': log_delta[-2000:]}))

    rel = str(ARTIFACT.relative_to(ROOT))
    pointer.update({
        'current_stage': 'GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIRED',
        'last_completed': WORK,
        'last_result': 'OK_GENERAL_PRODUCER_CONTRACT_REPAIRED_AND_CYCLE_VERIFIED',
        'last_artifact': rel,
        'runtime_producer_contract_status': 'GENERAL_CONTRACT_ACTIVE_VERIFIED',
        'runtime_producer_path': str(PRODUCER),
        'legacy_raw_runner_restore_authorized': False,
        'legacy_raw_runner_restore_forbidden': True,
        'era57_opened': False,
        'next_safe_step': NEXT,
        'updated_at_utc': ts,
    })
    runtime['current_problem'] = {'code': 'NONE', 'severity': 'NONE', 'evidence': rel}
    runtime['current_state'] = {'project_status': 'ERA56_CLOSED_ERA57_NOT_OPENED', 'runtime_status': 'GENERAL_RUNTIME_PRODUCER_CONTRACT_VERIFIED', 'mode': 'GENERAL_CONTRACT_ACTIVE', 'last_action': {'task': WORK, 'result': pointer['last_result'], 'artifact': rel, 'timestamp': ts}, 'current_problem': runtime['current_problem'], 'next_safe_step': {'id': NEXT, 'status': 'READY', 'human_authorization_required': True, 'production_mutation': False}, 'updated_at': ts}
    runtime['current_work_unit'] = {'id': WORK, 'status': 'CLOSED_VERIFIED', 'result': pointer['last_result'], 'artifact': rel, 'production_mutation': True, 'next_step': NEXT}
    dump(RUNTIME, runtime)

    history = load(HISTORY)
    history.setdefault('events', []).append({'event_id': WORK, 'timestamp_utc': ts, 'status': 'CLOSED_VERIFIED', 'result': pointer['last_result'], 'artifact': rel, 'producer_path': str(PRODUCER.relative_to(ROOT)), 'wrapper_path': str(WRAPPER.relative_to(ROOT)), 'temp_copy_smoke': 'OK', 'controlled_cycle': markers, 'service_result': service_result, 'legacy_restore': False, 'era57_opened': False, 'next_safe_step': NEXT})
    history['updated_at'] = ts; history['updated_at_utc'] = ts; dump(HISTORY, history)

    master = MASTER.read_text(encoding='utf-8')
    master = replace_section(master, '## 03 LAST VERIFIED WORK', f'''```text\nLAST_COMPLETED={WORK}\nLAST_RESULT={pointer['last_result']}\nLAST_ARTIFACT={rel}\nGENERAL_PRODUCER={PRODUCER.relative_to(ROOT)}\nCONTROLLED_CYCLE_RAW_OK=true\nCONTROLLED_CYCLE_DERIVED_OK=true\nCONTROLLED_CYCLE_HOT_OK=true\nLEGACY_RESTORE=false\nERA57_OPENED=false\n```\n\nNEXT_SAFE_STEP={NEXT}''')
    master = replace_section(master, '## 10 NEXT SAFE STEP', f'''```text\nNEXT_SAFE_STEP={NEXT}\n```\n\nGeneral runtime producer contract is active and verified. ERA57 still requires explicit human opening approval.''')
    MASTER.write_text(master.rstrip() + '\n', encoding='utf-8')

    handoff = HANDOFF.read_text(encoding='utf-8')
    handoff = replace_section(handoff, '## 03 LAST VERIFIED WORK', f'''LAST_COMPLETED={WORK}\nLAST_RESULT={pointer['last_result']}\nLAST_ARTIFACT={rel}\nGENERAL_PRODUCER={PRODUCER.relative_to(ROOT)}\nLEGACY_RESTORE=false\nERA57_OPENED=false''')
    handoff = replace_section(handoff, '## 07 ALLOWED NEXT DECISIONS', f'''- General producer contract is verified.\n- Deleted legacy runner must not be restored.\n- ERA57 remains closed until explicit approval.\n\nNEXT_SAFE_STEP={NEXT}''')
    HANDOFF.write_text(handoff.rstrip() + '\n', encoding='utf-8')

    almanac = ALMANAC.read_text(encoding='utf-8')
    almanac += f'''\n\n---\n\n## GENERAL RUNTIME PRODUCER CONTRACT REPAIR\n\n- Status: `CLOSED_VERIFIED`\n- Producer: `{PRODUCER.relative_to(ROOT)}`\n- Wrapper: `{WRAPPER.relative_to(ROOT)}`\n- Temp-copy smoke: `OK`\n- Controlled raw/derived/hot cycle: `OK`\n- Legacy restore: `false`\n- ERA57 opened: `false`\n- Next safe step: `{NEXT}`\n'''
    ALMANAC.write_text(almanac.rstrip() + '\n', encoding='utf-8')

    dump(ARTIFACT, {'schema': 'general_runtime_producer_contract_repair_v1', 'timestamp_utc': ts, 'status': 'CLOSED_VERIFIED', 'result': pointer['last_result'], 'historical_blob': blob, 'general_producer': str(PRODUCER.relative_to(ROOT)), 'wrapper': str(WRAPPER.relative_to(ROOT)), 'producer_sha256': sha256(PRODUCER), 'wrapper_sha256': sha256(WRAPPER), 'temp_copy_smoke_returncode': smoke.returncode, 'production_db_integrity_before': before_integrity, 'production_db_integrity_after': db_integrity(DB), 'service_result': service_result, 'cycle_markers': markers, 'legacy_restore': False, 'era57_opened': False, 'next_safe_step': NEXT, 'backup': str(backup)})

    if SELF.exists(): SELF.unlink()
    run(['python3', '-m', 'py_compile', str(PRODUCER), str(WRAPPER)])
    for path in (RUNTIME, HISTORY, ARTIFACT): load(path)
    git('add', '-A')
    check = run(['git', 'diff', '--cached', '--check'], check=False)
    if check.returncode:
        print(check.stdout, end=''); print(check.stderr, end=''); raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit', '-m', 'GENERAL_RUNTIME_PRODUCER_CONTRACT | OK | GENERAL_INGESTION_AND_NATURAL_CYCLE')
    print('GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR=SUCCESS')
    print('GENERAL_PRODUCER=tools/news_source_ingestion_runner_v1.py')
    print('LEGACY_RESTORE=false')
    print('TEMP_COPY_SMOKE=OK')
    print('RAW_CYCLE_OK=true')
    print('DERIVED_CYCLE_OK=true')
    print('HOT_CYCLE_OK=true')
    print('ERA57_OPENED=false')
    print('NEXT_SAFE_STEP=' + NEXT)
    print('LOCAL_COMMIT=' + git('rev-parse', 'HEAD'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
