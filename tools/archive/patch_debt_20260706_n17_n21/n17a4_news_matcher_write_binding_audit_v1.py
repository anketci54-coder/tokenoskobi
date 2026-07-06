#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import ast, json, os, re, sqlite3, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
OUT = ROOT / 'data/control/n17a4_news_matcher_write_binding_audit_v1.json'
ROWS = ROOT / 'data/control/n17a4_news_matcher_write_binding_audit_v1_rows.jsonl'

PATTERNS = [
    'match_many',
    'match_raw_news_to_tokens',
    'score_token_against_raw',
    'news_token_matcher_v1',
    'news_token_match_events',
    'INSERT INTO news_token_match_events',
    'news_raw_feed_events',
    'token_uid',
    'pair_uid',
]
SKIP_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.local_archive', 'archive'}
SCAN_SUFFIXES = {'.py', '.sh', '.md', '.json', '.service', '.timer'}

def now(): return datetime.now(timezone.utc).isoformat()

def read_json(path):
    with open(path, encoding='utf-8') as f: return json.load(f)

def awrite(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n17a4_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def should_scan(path):
    parts=set(path.parts)
    if parts & SKIP_DIRS: return False
    return path.is_file() and (path.suffix in SCAN_SUFFIXES or path.name.endswith(('.service','.timer')))

def grep_repo():
    hits=[]
    for p in ROOT.rglob('*'):
        if not should_scan(p): continue
        try: txt=p.read_text(encoding='utf-8', errors='replace')
        except Exception: continue
        found=[]
        for pat in PATTERNS:
            if pat in txt: found.append(pat)
        if found:
            lines=[]
            for i,line in enumerate(txt.splitlines(),1):
                if any(pat in line for pat in found):
                    lines.append({'line':i,'text':line.strip()[:240]})
                    if len(lines)>=20: break
            hits.append({'path':str(p.relative_to(ROOT)),'patterns':found,'lines':lines})
    return hits

def py_ast_calls(path):
    out={'path':str(path.relative_to(ROOT)),'parse_ok':False,'imports':[],'calls':[],'db_insert_strings':[]}
    try:
        src=path.read_text(encoding='utf-8', errors='replace')
        tree=ast.parse(src); out['parse_ok']=True
    except Exception as e:
        out['error']=type(e).__name__+':'+str(e)[:160]; return out
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import, ast.ImportFrom)):
            out['imports'].append(ast.unparse(n) if hasattr(ast,'unparse') else str(type(n)))
        if isinstance(n,ast.Call):
            fn=n.func
            name=getattr(fn,'id',None) or getattr(fn,'attr',None)
            if name in {'match_many','match_raw_news_to_tokens','score_token_against_raw','execute','executemany'}:
                out['calls'].append({'name':name,'lineno':getattr(n,'lineno',None)})
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            s=n.value
            if 'news_token_match_events' in s or 'INSERT' in s.upper() and 'news_' in s:
                out['db_insert_strings'].append(s[:300])
    return out

def db_schema():
    if not DB.exists(): return {'db_exists':False,'tables':[]}
    con=sqlite3.connect(str(DB)); cur=con.cursor()
    tables=[]
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for (name,) in cur.fetchall():
        if 'news' in name or 'token' in name or 'pair' in name:
            cur.execute(f'PRAGMA table_info({name})')
            cols=[r[1] for r in cur.fetchall()]
            try:
                cur.execute(f'SELECT COUNT(*) FROM {name}')
                cnt=int(cur.fetchone()[0])
            except Exception:
                cnt=None
            tables.append({'table':name,'count':cnt,'columns':cols})
    con.close(); return {'db_exists':True,'tables':tables}

def main():
    hits=grep_repo()
    py_infos=[py_ast_calls(ROOT/h['path']) for h in hits if h['path'].endswith('.py')]
    schema=db_schema()
    matcher_callers=[h for h in hits if any(p in h['patterns'] for p in ['match_many','match_raw_news_to_tokens','news_token_matcher_v1']) and h['path']!='tools/news_token_matcher_v1.py']
    match_table_writers=[h for h in hits if 'INSERT INTO news_token_match_events' in h['patterns'] or any('news_token_match_events' in (ln.get('text') or '') and 'INSERT' in (ln.get('text') or '').upper() for ln in h.get('lines',[]))]
    token_source_tables=[t for t in schema.get('tables',[]) if any(c in t.get('columns',[]) for c in ['token_uid','pair_uid','symbol','token_address','address'])]

    checks=[
        {'gate':'matcher_library_exists', 'ok':(ROOT/'tools/news_token_matcher_v1.py').exists()},
        {'gate':'external_matcher_caller_found', 'ok':bool(matcher_callers), 'value':[x['path'] for x in matcher_callers[:10]]},
        {'gate':'match_table_writer_found', 'ok':bool(match_table_writers), 'value':[x['path'] for x in match_table_writers[:10]]},
        {'gate':'token_source_table_candidate_found', 'ok':bool(token_source_tables), 'value':[{'table':t['table'],'count':t['count'],'columns':t['columns'][:12]} for t in token_source_tables[:10]]},
        {'gate':'news_raw_table_present', 'ok':any(t['table']=='news_raw_feed_events' and (t.get('count') or 0)>0 for t in schema.get('tables',[]))},
        {'gate':'news_match_table_present', 'ok':any(t['table']=='news_token_match_events' for t in schema.get('tables',[]))},
    ]

    if not checks[1]['ok'] and not checks[2]['ok']:
        decision='MATCHER_LIBRARY_EXISTS_BUT_NO_CALLER_OR_DB_WRITER_FOUND'
        next_action='BUILD_NEWS_MATCHER_BINDING_RUNNER_TEMPDB_FIRST'
    elif checks[1]['ok'] and not checks[2]['ok']:
        decision='MATCHER_CALLER_EXISTS_BUT_NO_MATCH_TABLE_WRITER_FOUND'
        next_action='PATCH_CALLER_TO_WRITE_MATCH_TABLE_TEMPDB_FIRST'
    elif not checks[3]['ok']:
        decision='NO_TOKEN_SOURCE_TABLE_CANDIDATE_FOUND'
        next_action='BUILD_TOKEN_DICTIONARY_OR_SOURCE_BINDING'
    else:
        decision='MATCHER_WRITE_BINDING_COMPONENTS_PARTIAL_PRESENT'
        next_action='TRACE_EXISTING_CALLER_AND_DB_WRITER_ON_TEMPDB'

    result={
        'stage':'N17A4_NEWS_MATCHER_WRITE_BINDING_AUDIT',
        'generated_at_utc':now(),
        'producer':'tools/n17a4_news_matcher_write_binding_audit_v1.py',
        'decision':decision,
        'next_action':next_action,
        'checks':checks,
        'matcher_callers':matcher_callers,
        'match_table_writers':match_table_writers,
        'token_source_tables':token_source_tables,
        'repo_hits':hits[:200],
        'py_ast_infos':py_infos[:80],
        'db_schema':schema,
        'authority':{'readonly':True,'real_db_write':False,'tempdb_write':False,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}
    }
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N17A4_NEWS_MATCHER_WRITE_BINDING_AUDIT')
    print('DECISION='+decision)
    print('NEXT_ACTION='+next_action)
    print('JSON='+str(OUT.relative_to(ROOT)))

if __name__=='__main__': main()
