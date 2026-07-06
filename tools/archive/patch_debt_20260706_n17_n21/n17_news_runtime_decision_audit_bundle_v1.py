#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
PROBE = ROOT / 'data/control/n17a_news_runtime_probe_readonly_result_v1.json'
OUT = ROOT / 'data/control/n17_news_runtime_decision_audit_bundle_v1.json'
ROWS = ROOT / 'data/control/n17_news_runtime_decision_audit_bundle_v1_rows.jsonl'
PANEL_TARGET = ROOT / 'active_panel_8096/current/data/news_center_live_readmodel_v1.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n17_news_decision_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        read_json(Path(tmp))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def count_for(table_counts, name):
    for item in table_counts:
        if item.get('table') == name:
            return item.get('count') or 0
    return 0


def check_for(checks, name):
    for item in checks:
        if item.get('name') == name:
            return bool(item.get('ok'))
    return False


def main():
    if not PROBE.exists():
        raise SystemExit('FAIL: missing N17A probe result: ' + str(PROBE))
    probe = read_json(PROBE)
    checks = probe.get('checks', [])
    table_counts = probe.get('table_counts', [])
    unit_status = probe.get('unit_status', {})

    raw_count = count_for(table_counts, 'news_raw_feed_events')
    token_match_count = count_for(table_counts, 'news_token_match_events')
    signal_count = count_for(table_counts, 'news_signal_events')
    score_count = count_for(table_counts, 'news_score_events_v1')
    timer_active = unit_status.get('tokenoskobi-news-radar-refresh.timer') == 'active'
    service_known = bool(unit_status.get('tokenoskobi-news-radar-refresh.service'))
    runner_exists = check_for(checks, 'runner_exists')
    db_selected = check_for(checks, 'db_selected')
    raw_nonzero = raw_count > 0
    downstream_zero = token_match_count == 0 and signal_count == 0 and score_count == 0

    audit_rows = [
        {'gate': 'service_known', 'ok': service_known, 'value': unit_status.get('tokenoskobi-news-radar-refresh.service')},
        {'gate': 'timer_active', 'ok': timer_active, 'value': unit_status.get('tokenoskobi-news-radar-refresh.timer')},
        {'gate': 'runner_exists', 'ok': runner_exists, 'value': runner_exists},
        {'gate': 'db_selected', 'ok': db_selected, 'value': probe.get('selected_db')},
        {'gate': 'raw_feed_nonzero', 'ok': raw_nonzero, 'value': raw_count},
        {'gate': 'token_match_nonzero', 'ok': token_match_count > 0, 'value': token_match_count},
        {'gate': 'signal_nonzero', 'ok': signal_count > 0, 'value': signal_count},
        {'gate': 'score_nonzero', 'ok': score_count > 0, 'value': score_count}
    ]

    if raw_nonzero and downstream_zero:
        diagnosis = 'RAW_NEWS_PRESENT_BUT_MATCH_SIGNAL_SCORE_CHAIN_EMPTY'
        next_action = 'REPAIR_MATCHER_AND_DOWNSTREAM_CHAIN_READONLY_FIRST'
        panel_decision = 'NEWS_CENTER_RAW_PRESENT_DOWNSTREAM_EMPTY'
    elif raw_nonzero and token_match_count > 0 and signal_count == 0:
        diagnosis = 'MATCHES_PRESENT_BUT_SIGNAL_CHAIN_EMPTY'
        next_action = 'REPAIR_SIGNAL_CHAIN_READONLY_FIRST'
        panel_decision = 'NEWS_CENTER_MATCH_PRESENT_SIGNAL_EMPTY'
    elif raw_nonzero and token_match_count > 0 and signal_count > 0 and score_count == 0:
        diagnosis = 'SIGNALS_PRESENT_BUT_SCORE_CHAIN_EMPTY'
        next_action = 'REPAIR_SCORE_CHAIN_READONLY_FIRST'
        panel_decision = 'NEWS_CENTER_SIGNAL_PRESENT_SCORE_EMPTY'
    elif timer_active and raw_nonzero:
        diagnosis = 'NEWS_RUNTIME_PARTIAL_LIVE_OR_RECENT_REQUIRES_FRESHNESS_AUDIT'
        next_action = 'ADD_FRESHNESS_AUDIT_BEFORE_LIVE_CLAIM'
        panel_decision = 'NEWS_CENTER_PARTIAL_NEEDS_FRESHNESS_AUDIT'
    elif not timer_active and raw_nonzero:
        diagnosis = 'HISTORICAL_RAW_NEWS_PRESENT_TIMER_INACTIVE'
        next_action = 'DECIDE_TIMER_REENABLE_AFTER_RUNNER_STATIC_AUDIT'
        panel_decision = 'NEWS_CENTER_HISTORICAL_RAW_TIMER_INACTIVE'
    else:
        diagnosis = 'NEWS_RUNTIME_NOT_PROVEN'
        next_action = 'KEEP_SEALED_INACTIVE_AND_AUDIT_SOURCES'
        panel_decision = 'NEWS_CENTER_SEALED_INACTIVE'

    result = {
        'stage': 'N17_NEWS_RUNTIME_DECISION_AUDIT_BUNDLE',
        'generated_at_utc': now(),
        'producer': 'tools/n17_news_runtime_decision_audit_bundle_v1.py',
        'input_probe': str(PROBE.relative_to(ROOT)),
        'decision': diagnosis,
        'next_action': next_action,
        'panel_decision': panel_decision,
        'counts': {
            'news_raw_feed_events': raw_count,
            'news_token_match_events': token_match_count,
            'news_signal_events': signal_count,
            'news_score_events_v1': score_count
        },
        'audit_rows': audit_rows,
        'safe_repair_sequence': [
            'N17A1 runner static audit: inspect ORIGINAL_RUNNER, postprocess reachability, matcher import/path, preview writes.',
            'N17A2 tempdb or dryrun-only matcher probe: do not start timer, do not call API unless explicitly approved.',
            'N17A3 if chain is proven, run one controlled oneshot locally and compare table deltas.',
            'N17A4 update news_center_live_readmodel_v1.json only with observed counts and freshness evidence.',
            'N17A5 only then consider timer re-enable.'
        ],
        'authority': {
            'readonly': True,
            'systemd_start': False,
            'systemd_stop': False,
            'api_calls': 0,
            'provider_call': False,
            'wallet': False,
            'signing': False,
            'live_trade': False,
            'db_write': False,
            'core_change': False
        }
    }

    panel_model = {
        'stage': 'N17_NEWS_CENTER_DECISION_VIEW',
        'generated_at_utc': now(),
        'producer': 'tools/n17_news_runtime_decision_audit_bundle_v1.py',
        'decision': panel_decision,
        'data_freshness_sec': 0,
        'authority': {
            'trade': False,
            'wallet_signing': False,
            'provider_call_from_browser': False,
            'policy_apply': False,
            'paper_trade_write': False
        },
        'source_count': 1 if PROBE.exists() else 0,
        'items': [{
            'key': 'news_center',
            'label': 'Haber Akış Merkezi',
            'status': panel_decision,
            'diagnosis': diagnosis,
            'next_action': next_action,
            'counts': result['counts'],
            'live_news_claim': False,
            'note': 'This is a decision view from readonly probe evidence. It does not claim live news until producer chain and freshness are proven.'
        }]
    }

    atomic_write(OUT, result)
    atomic_write(PANEL_TARGET, panel_model)
    ROWS.parent.mkdir(parents=True, exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in audit_rows) + '\n', encoding='utf-8')
    print('FINAL_GATE=PASS_N17_NEWS_RUNTIME_DECISION_AUDIT_BUNDLE')
    print('DECISION=' + diagnosis)
    print('NEXT_ACTION=' + next_action)
    print('PANEL_DECISION=' + panel_decision)
    print('JSON=' + str(OUT.relative_to(ROOT)))
    print('PANEL=' + str(PANEL_TARGET.relative_to(ROOT)))


if __name__ == '__main__':
    main()
