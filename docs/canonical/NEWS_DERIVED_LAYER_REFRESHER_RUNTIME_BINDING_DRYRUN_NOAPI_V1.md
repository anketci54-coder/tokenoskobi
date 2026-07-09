# NEWS Derived Layer Refresher Runtime Binding Dryrun NOAPI V1

Generated UTC: 2026-07-09T17:05:33.150633+00:00

Decision: OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_NOAPI

Helper:
tools/news_derived_layer_refresher_v1.py

TempDB delta:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 1,
  "news_signal_events": 1,
  "news_token_match_events": 1
}

Real DB delta:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}

Runner binding preview:
{
  "backup_runner": "tools/news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T170532Z.py",
  "helper": "tools/news_derived_layer_refresher_v1.py",
  "preview_contains_helper": true,
  "preview_contains_original": true,
  "preview_line_count": 20,
  "preview_sha256": "a3f76ba2f8389a8d6037e48f29968046929a9735879564895c21b77d3a89fbaf",
  "preview_text_sample": "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n\nROOT = Path('/root/tokenoskobi_clean_v1')\nORIGINAL = ROOT / 'tools' / 'news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T170532Z.py'\nHELPER = ROOT / 'tools' / 'news_derived_layer_refresher_v1.py'\nDB = ROOT / 'data' / 'tokenoskobi_clean_v1.sqlite'\n\ndef main():\n    raw = subprocess.run([sys.executable, str(ORIGINAL)])\n    if raw.returncode != 0:\n        return raw.returncode\n    derived = subprocess.run([sys.executable, str(HELPER), '--db-path', str(DB), '--write', '--stage', 'NEWS_SYSTEMD_TIMER_DERIVED_REFRESH'])\n    return derived.returncode\n\nif __name__ == '__main__':\n    raise SystemExit(main())\n",
  "target_runner": "tools/news_radar_refresh_runner_v1.py"
}

Tests:
- test_count: 7
- ok_count: 7
- fail_count: 0

Next:
NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP
