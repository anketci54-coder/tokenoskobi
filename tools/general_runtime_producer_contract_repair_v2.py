#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
SELF = ROOT / 'tools/general_runtime_producer_contract_repair_v2.py'
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
TAG55 = 'ERA55_FINAL_SEAL'; SEAL55 = 'f22ce4f07788ec7fbe22a72f872467705b72db5a'
TAG56 = 'ERA56_FINAL_SEAL'; SEAL56 = '39dd684a71e39c4f05ce2a5113985fcf647718a0'

PRODUCER_TEXT = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sqlite3
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

CONTRACT_VERSION = "NEWS_SOURCE_INGESTION_V1_1"
ROOT = Path(os.environ.get("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1"))
DB = Path(os.environ.get("TOKENOSKOBI_DB_PATH", str(ROOT / "data/tokenoskobi_clean_v1.sqlite")))
STATE = Path(os.environ.get("TOKENOSKOBI_SOURCE_INGESTION_STATE_PATH", str(ROOT / "runtime/state/news_source_ingestion_state_v1.json")))
TIMEOUT = int(os.environ.get("TOKENOSKOBI_SOURCE_HTTP_TIMEOUT_SECONDS", "10"))
MAX_SOURCES = int(os.environ.get("TOKENOSKOBI_SOURCE_MAX_SOURCES", "4"))
MAX_ITEMS = int(os.environ.get("TOKENOSKOBI_SOURCE_MAX_ITEMS_PER_SOURCE", "25"))
USER_AGENT = os.environ.get("TOKENOSKOBI_SOURCE_USER_AGENT", "TokenoskobiSourceIngestion/1.0")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable(*parts: object, size: int = 32) -> str:
    raw = "||".join("" if x is None else str(x).strip().lower() for x in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:size]


def clean(value: object) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_date(value: object) -> str:
    text = clean(value)
    if not text:
        return now()
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return now()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)


def columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [str(row[1]) for row in con.execute(f'PRAGMA table_info("{table}")').fetchall()]


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def pick(mapping: dict, names: tuple[str, ...], default: object = None):
    for name in names:
        if name in mapping and mapping[name] not in (None, ""):
            return mapping[name]
    return default


def registry_sources(con: sqlite3.Connection) -> list[dict]:
    table = "news_source_registry_v1"

    if not table_exists(con, table):
        raise RuntimeError("NEWS_SOURCE_REGISTRY_V1_MISSING")

    cols = columns(con, table)

    required = {
        "source_uid",
        "source_name",
        "source_url",
        "fetch_method",
        "status",
    }
    missing = sorted(required - set(cols))
    if missing:
        raise RuntimeError(
            "NEWS_SOURCE_REGISTRY_V1_CONTRACT_MISSING:"
            + ",".join(missing)
        )

    rows = [
        dict(zip(cols, row))
        for row in con.execute(
            """
            SELECT *
            FROM news_source_registry_v1
            ORDER BY
                COALESCE(priority, 0) DESC,
                source_uid ASC
            """
        ).fetchall()
    ]

    blocked_statuses = {
        "DISABLED",
        "INACTIVE",
        "BLOCKED",
        "REJECTED",
        "DEPRECATED",
        "ARCHIVED",
        "DENIED",
    }

    supported_methods = {
        "RSS",
        "ATOM",
        "FEED",
        "HTTP",
        "HTTPS",
        "GET",
        "XML",
    }

    out = []

    for row in rows:
        status = str(row.get("status") or "").strip().upper()
        if status in blocked_statuses:
            continue

        url = str(row.get("source_url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue

        fetch_method = str(
            row.get("fetch_method") or "RSS"
        ).strip().upper()

        if fetch_method not in supported_methods:
            continue

        source_class = str(
            row.get("source_class") or ""
        ).strip().lower()

        if source_class and not any(
            marker in source_class
            for marker in (
                "rss",
                "atom",
                "feed",
                "news",
                "media",
                "official",
            )
        ):
            continue

        out.append(
            {
                "source_uid": str(row["source_uid"]),
                "source_name": str(row["source_name"]),
                "url": url,
                "fetch_method": fetch_method,
                "priority": int(row.get("priority") or 0),
                "trust_level": row.get("trust_level"),
                "source_domain": row.get("source_domain"),
            }
        )

    if not out:
        raise RuntimeError(
            "NO_ENABLED_SUPPORTED_SOURCES_IN_NEWS_SOURCE_REGISTRY_V1"
        )

    return out[:MAX_SOURCES]


def fetch(source: dict) -> tuple[dict, list[dict]]:
    ledger = {"source_uid": source["source_uid"], "source_name": source["source_name"], "status": "ERROR", "parsed": 0, "kept": 0, "error": None}
    rows: list[dict] = []
    try:
        request = urllib.request.Request(source["url"], headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            payload = response.read(2 * 1024 * 1024)
        root = ET.fromstring(payload)
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        ledger["parsed"] = len(items)
        for item in items[:MAX_ITEMS]:
            def text(*names: str) -> str:
                for name in names:
                    node = item.find(name)
                    if node is not None:
                        if node.text:
                            return clean(node.text)
                        href = node.attrib.get("href")
                        if href:
                            return clean(href)
                return ""
            title = text("title", "{http://www.w3.org/2005/Atom}title")
            if not title:
                continue
            link = text("link", "{http://www.w3.org/2005/Atom}link")
            published = text("pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated")
            description = text("description", "summary", "{http://www.w3.org/2005/Atom}summary")
            uid = "news_" + stable(source["source_uid"], title, link, published, size=24)
            rows.append({
                "news_uid": uid,
                "source_uid": source["source_uid"],
                "source_name": source["source_name"],
                "published_at_utc": parse_date(published),
                "title": title,
                "url": link,
                "description": description[:4000],
                "url_hash": stable(link or title),
                "title_hash": stable(title),
                "raw_hash": stable(source["source_uid"], title, link, published, description),
                "fetched_at_utc": now(),
            })
        ledger["kept"] = len(rows)
        ledger["status"] = "OK"
    except Exception as exc:
        ledger["error"] = repr(exc)
    return ledger, rows


def insert_rows(con: sqlite3.Connection, rows: list[dict]) -> int:
    if not table_exists(con, "news_raw_feed_events"):
        raise RuntimeError("NEWS_RAW_FEED_EVENTS_MISSING")
    cols = columns(con, "news_raw_feed_events")
    inserted = 0
    for row in rows:
        use = [name for name in row if name in cols]
        if not use:
            continue
        sql = f'INSERT OR IGNORE INTO "news_raw_feed_events" ({",".join(use)}) VALUES ({",".join("?" for _ in use)})'
        cur = con.execute(sql, [row[name] for name in use])
        inserted += max(0, int(cur.rowcount or 0))
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    con = sqlite3.connect(DB, timeout=30)
    try:
        con.row_factory = sqlite3.Row
        sources = registry_sources(con)
        if not sources:
            raise RuntimeError("NO_ENABLED_INGESTION_SOURCES")
        if args.validate_only:
            print(json.dumps({"contract": CONTRACT_VERSION, "status": "OK", "source_count": len(sources), "db": str(DB)}, sort_keys=True))
            return 0
        ledgers = []
        all_rows: list[dict] = []
        for source in sources:
            ledger, rows = fetch(source)
            ledgers.append(ledger); all_rows.extend(rows)
        successful = sum(1 for item in ledgers if item["status"] == "OK")
        if successful == 0:
            atomic_json(STATE, {"contract": CONTRACT_VERSION, "status": "ERROR_NO_SOURCE_SUCCEEDED", "timestamp_utc": now(), "sources": ledgers})
            return 69
        con.execute("BEGIN IMMEDIATE")
        inserted = insert_rows(con, all_rows)
        con.commit()
        state = {"contract": CONTRACT_VERSION, "status": "OK", "timestamp_utc": now(), "source_count": len(sources), "successful_sources": successful, "candidate_rows": len(all_rows), "inserted_rows": inserted, "sources": ledgers}
        atomic_json(STATE, state)
        print(json.dumps(state, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
'''


def run(args: list[str], check: bool = True, timeout: int = 120, env: dict[str, str] | None = None):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check, timeout=timeout, env=env)


def git(*args: str) -> str:
    return run(['git', *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict): raise RuntimeError(f'JSON_OBJECT_REQUIRED:{path}')
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)


def section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0: return text.rstrip() + '\n\n' + heading + '\n\n' + body.rstrip() + '\n'
    end = text.find('\n## ', start + len(heading)); end = len(text) if end < 0 else end
    return text[:start] + heading + '\n\n' + body.rstrip() + '\n' + text[end:]


def integrity(path: Path) -> str:
    con = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    try: return str(con.execute('PRAGMA integrity_check').fetchone()[0])
    finally: con.close()


def repair_wrapper(text: str) -> str:
    start = text.index('ORIGINAL = Path(')
    end = text.index('\nHELPER = Path(', start)
    producer_block = '''PRODUCER = Path(\n    os.environ.get(\n        "TOKENOSKOBI_NEWS_PRODUCER_PATH",\n        str(ROOT / "tools" / "news_source_ingestion_runner_v1.py"),\n    )\n)\n'''
    text = text[:start] + producer_block + text[end + 1:]
    text = text.replace('[PYTHON_BIN, str(ORIGINAL)] + sys.argv[1:]', '[PYTHON_BIN, str(PRODUCER)] + sys.argv[1:]', 1)
    anchor = 'ORDER_LOG = os.environ.get("TOKENOSKOBI_A10_ORDER_LOG")\n'
    helper = '''ORDER_LOG = os.environ.get("TOKENOSKOBI_A10_ORDER_LOG")\nSUBPROCESS_TIMEOUT_SECONDS = int(os.environ.get("TOKENOSKOBI_RUNNER_SUBPROCESS_TIMEOUT_SECONDS", "75"))\n\n\ndef run_child(command: list[str], stage: str) -> int:\n    try:\n        return int(subprocess.run(command, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, timeout=SUBPROCESS_TIMEOUT_SECONDS).returncode)\n    except subprocess.TimeoutExpired:\n        print(f"[CHILD_TIMEOUT] stage={stage} timeout={SUBPROCESS_TIMEOUT_SECONDS}", flush=True)\n        return 124\n'''
    if anchor not in text: raise RuntimeError('ORDER_LOG_ANCHOR_MISSING')
    text = text.replace(anchor, helper, 1)
    text = text.replace('''    result = subprocess.run(\n        [PYTHON_BIN, str(HOT), "--runtime-refresh"],\n        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},\n    ).returncode''', '    result = run_child([PYTHON_BIN, str(HOT), "--runtime-refresh"], "HOT")', 1)
    text = text.replace('''    raw = subprocess.run(\n        [PYTHON_BIN, str(PRODUCER)] + sys.argv[1:],\n        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},\n    )\n    append_order(f"RAW_END:{raw.returncode}")\n    if raw.returncode != 0:\n        return raw.returncode''', '''    raw_returncode = run_child([PYTHON_BIN, str(PRODUCER)] + sys.argv[1:], "RAW")\n    append_order(f"RAW_END:{raw_returncode}")\n    if raw_returncode != 0:\n        return raw_returncode''', 1)
    text = text.replace('''    derived = subprocess.run(\n        [\n            PYTHON_BIN,\n            str(HELPER),\n            "--db-path",\n            str(DB),\n            "--write",\n            "--stage",\n            "NEWS_SYSTEMD_TIMER_DERIVED_REFRESH",\n        ],\n        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},\n    )\n    append_order(f"DERIVED_END:{derived.returncode}")\n    if derived.returncode != 0:\n        return derived.returncode''', '''    derived_returncode = run_child([PYTHON_BIN, str(HELPER), "--db-path", str(DB), "--write", "--stage", "NEWS_SYSTEMD_TIMER_DERIVED_REFRESH"], "DERIVED")\n    append_order(f"DERIVED_END:{derived_returncode}")\n    if derived_returncode != 0:\n        return derived_returncode''', 1)
    pipeline_anchor = '    writer_enabled = env_true("TOKENOSKOBI_LEDGER_WRITER_ENABLED")\n'
    check = '''    writer_enabled = env_true("TOKENOSKOBI_LEDGER_WRITER_ENABLED")\n    required = {"producer": PRODUCER, "derived": HELPER, "hot": HOT}\n    missing = [f"{name}:{path}" for name, path in required.items() if not path.is_file()]\n    if missing:\n        print("[RUNTIME_CONTRACT_MISSING] " + ",".join(missing), flush=True)\n        return 78\n'''
    if pipeline_anchor not in text: raise RuntimeError('PIPELINE_ANCHOR_MISSING')
    text = text.replace(pipeline_anchor, check, 1)
    if 'PRE_DERIVED_BINDING' in text or 'TOKENOSKOBI_NEWS_ORIGINAL_PATH' in text or 'str(ORIGINAL)' in text:
        raise RuntimeError('LEGACY_REFERENCE_REMAINED')
    return text


def main() -> int:
    if git('status', '--short'): raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected = os.environ.get('TOKENOSKOBI_EXPECTED_HEAD', '').strip()
    if expected and git('rev-parse', 'HEAD') != expected: raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list', '-n1', TAG55) != SEAL55 or git('rev-list', '-n1', TAG56) != SEAL56: raise RuntimeError('SEAL_MISMATCH')
    runtime = load(RUNTIME); pointer = runtime['canonical_runtime_pointer']
    if pointer.get('next_safe_step') != 'GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR_DECISION': raise RuntimeError('NEXT_STEP_MISMATCH')
    if pointer.get('legacy_raw_runner_restore_forbidden') is not True: raise RuntimeError('ANTI_PATCH_GUARD_MISSING')

    ts = datetime.now(timezone.utc).isoformat(); compact = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_dir = Path('/root/tokenoskobi_backups'); backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f'GENERAL_RUNTIME_PRODUCER_CONTRACT_{compact}.tar.gz'
    db_backup = backup_dir / f'GENERAL_RUNTIME_PRODUCER_CONTRACT_DB_{compact}.sqlite'
    shutil.copy2(DB, db_backup)
    with tarfile.open(backup, 'w:gz') as tar:
        for path in (WRAPPER, RUNTIME, HISTORY, MASTER, HANDOFF, ALMANAC): tar.add(path, arcname=str(path.relative_to(ROOT)))

    original_wrapper = WRAPPER.read_text(encoding='utf-8')
    try:
        PRODUCER.write_text(PRODUCER_TEXT, encoding='utf-8')
        WRAPPER.write_text(repair_wrapper(original_wrapper), encoding='utf-8')
        run(['python3', '-m', 'py_compile', str(PRODUCER), str(WRAPPER)])

        temp_root = Path(tempfile.mkdtemp(prefix='general_ingestion_contract_'))
        try:
            temp_db = temp_root / 'data/tokenoskobi_clean_v1.sqlite'; temp_db.parent.mkdir(parents=True)
            shutil.copy2(DB, temp_db)
            env = {**os.environ, 'TOKENOSKOBI_ROOT': str(temp_root), 'TOKENOSKOBI_DB_PATH': str(temp_db), 'PYTHONDONTWRITEBYTECODE': '1'}
            validate = run(['/usr/bin/python3', str(PRODUCER), '--validate-only'], check=False, timeout=30, env=env)
            if validate.returncode != 0 or integrity(temp_db) != 'ok':
                raise RuntimeError('TEMP_CONTRACT_VALIDATION_FAILED:' + validate.stderr[-1000:])
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)

        log_before = ORDER_LOG.stat().st_size if ORDER_LOG.exists() else 0
        cycle = run(['systemctl', 'start', SERVICE], check=False, timeout=120)
        result = run(['systemctl', 'show', SERVICE, '-p', 'Result', '--value'], check=False).stdout.strip()
        delta = ''
        if ORDER_LOG.exists():
            with ORDER_LOG.open('rb') as handle: handle.seek(log_before); delta = handle.read().decode('utf-8', 'replace')
        markers = {'raw_ok': 'RAW_END:0' in delta, 'derived_ok': 'DERIVED_END:0' in delta, 'hot_ok': 'HOT_END:0' in delta}
        if cycle.returncode != 0 or result != 'success' or not all(markers.values()) or integrity(DB) != 'ok':
            raise RuntimeError('CONTROLLED_CYCLE_FAILED:' + json.dumps({'cycle_rc': cycle.returncode, 'result': result, 'markers': markers, 'log': delta[-2000:]}))
    except Exception:
        WRAPPER.write_text(original_wrapper, encoding='utf-8')
        if PRODUCER.exists(): PRODUCER.unlink()
        shutil.copy2(db_backup, DB)
        raise

    rel = str(ARTIFACT.relative_to(ROOT)); final_result = 'OK_GENERAL_REGISTRY_DRIVEN_PRODUCER_CONTRACT_VERIFIED'
    pointer.update({'current_stage': 'GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIRED', 'last_completed': WORK, 'last_result': final_result, 'last_artifact': rel, 'runtime_producer_contract_status': 'GENERAL_REGISTRY_DRIVEN_ACTIVE_VERIFIED', 'runtime_producer_path': str(PRODUCER), 'legacy_raw_runner_restore_authorized': False, 'legacy_raw_runner_restore_forbidden': True, 'era57_opened': False, 'next_safe_step': NEXT, 'updated_at_utc': ts})
    runtime['current_problem'] = {'code': 'NONE', 'severity': 'NONE', 'evidence': rel}
    runtime['current_state'] = {'project_status': 'ERA56_CLOSED_ERA57_NOT_OPENED', 'runtime_status': 'GENERAL_RUNTIME_PRODUCER_CONTRACT_VERIFIED', 'mode': 'GENERAL_REGISTRY_DRIVEN_CONTRACT', 'last_action': {'task': WORK, 'result': final_result, 'artifact': rel, 'timestamp': ts}, 'current_problem': runtime['current_problem'], 'next_safe_step': {'id': NEXT, 'status': 'READY', 'human_authorization_required': True, 'production_mutation': False}, 'updated_at': ts}
    runtime['current_work_unit'] = {'id': WORK, 'status': 'CLOSED_VERIFIED', 'result': final_result, 'artifact': rel, 'production_mutation': True, 'next_step': NEXT}; dump(RUNTIME, runtime)

    history = load(HISTORY); history.setdefault('events', []).append({'event_id': WORK, 'timestamp_utc': ts, 'status': 'CLOSED_VERIFIED', 'result': final_result, 'artifact': rel, 'producer': str(PRODUCER.relative_to(ROOT)), 'registry_driven': True, 'temp_validation': True, 'controlled_cycle': markers, 'legacy_restore': False, 'era57_opened': False, 'next_safe_step': NEXT}); history['updated_at'] = ts; history['updated_at_utc'] = ts; dump(HISTORY, history)
    master = MASTER.read_text(encoding='utf-8'); master = section(master, '## 03 LAST VERIFIED WORK', f'''```text\nLAST_COMPLETED={WORK}\nLAST_RESULT={final_result}\nLAST_ARTIFACT={rel}\nGENERAL_PRODUCER={PRODUCER.relative_to(ROOT)}\nREGISTRY_DRIVEN=true\nRAW_CYCLE_OK=true\nDERIVED_CYCLE_OK=true\nHOT_CYCLE_OK=true\nLEGACY_RESTORE=false\nERA57_OPENED=false\n```\n\nNEXT_SAFE_STEP={NEXT}'''); master = section(master, '## 10 NEXT SAFE STEP', f'''```text\nNEXT_SAFE_STEP={NEXT}\n```\n\nGeneral registry-driven producer contract is verified. ERA57 still requires explicit approval.'''); MASTER.write_text(master.rstrip() + '\n', encoding='utf-8')
    handoff = HANDOFF.read_text(encoding='utf-8'); handoff = section(handoff, '## 03 LAST VERIFIED WORK', f'''LAST_COMPLETED={WORK}\nLAST_RESULT={final_result}\nLAST_ARTIFACT={rel}\nGENERAL_PRODUCER={PRODUCER.relative_to(ROOT)}\nREGISTRY_DRIVEN=true\nLEGACY_RESTORE=false\nERA57_OPENED=false'''); handoff = section(handoff, '## 07 ALLOWED NEXT DECISIONS', f'''- General registry-driven producer contract is verified.\n- Legacy runner restore remains forbidden.\n- ERA57 remains closed until explicit approval.\n\nNEXT_SAFE_STEP={NEXT}'''); HANDOFF.write_text(handoff.rstrip() + '\n', encoding='utf-8')
    almanac = ALMANAC.read_text(encoding='utf-8') + f'''\n\n---\n\n## GENERAL RUNTIME PRODUCER CONTRACT REPAIR\n\n- Status: `CLOSED_VERIFIED`\n- Producer: `{PRODUCER.relative_to(ROOT)}`\n- Source ownership: `news_source_registry`\n- Temp validation: `OK`\n- Controlled raw/derived/hot cycle: `OK`\n- Legacy restore: `false`\n- ERA57 opened: `false`\n- Next safe step: `{NEXT}`\n'''; ALMANAC.write_text(almanac.rstrip() + '\n', encoding='utf-8')
    dump(ARTIFACT, {'schema': 'general_runtime_producer_contract_repair_v1', 'timestamp_utc': ts, 'status': 'CLOSED_VERIFIED', 'result': final_result, 'producer': str(PRODUCER.relative_to(ROOT)), 'wrapper': str(WRAPPER.relative_to(ROOT)), 'registry_driven': True, 'temp_validation': True, 'controlled_cycle': markers, 'service_result': result, 'legacy_restore': False, 'era57_opened': False, 'next_safe_step': NEXT, 'backup': str(backup), 'db_backup': str(db_backup)})

    if SELF.exists(): SELF.unlink()
    run(['python3', '-m', 'py_compile', str(PRODUCER), str(WRAPPER)])
    git('add', '-A'); check = run(['git', 'diff', '--cached', '--check'], check=False)
    if check.returncode: print(check.stdout, end=''); print(check.stderr, end=''); raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit', '-m', 'GENERAL_RUNTIME_PRODUCER_CONTRACT | OK | REGISTRY_DRIVEN_INGESTION')
    print('GENERAL_RUNTIME_PRODUCER_CONTRACT_REPAIR=SUCCESS')
    print('GENERAL_PRODUCER=tools/news_source_ingestion_runner_v1.py')
    print('REGISTRY_DRIVEN=true')
    print('LEGACY_RESTORE=false')
    print('TEMP_VALIDATION=OK')
    print('RAW_CYCLE_OK=true')
    print('DERIVED_CYCLE_OK=true')
    print('HOT_CYCLE_OK=true')
    print('ERA57_OPENED=false')
    print('NEXT_SAFE_STEP=' + NEXT)
    print('LOCAL_COMMIT=' + git('rev-parse', 'HEAD'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
