# TOKENOSKOBI NEXT CHAT HANDOFF

Start in new window:

```bash
cd /root/tokenoskobi_clean_v1 || exit 1
git pull --ff-only origin main
tk ai
tk sync
git status --short
```

Source of truth: server workspace + GitHub `main` mirror.

Rules:

- Do not open a new ERA unless explicitly requested.
- Prefer GitHub inspection before asking for terminal output.
- Prefer one complete operation, one verification set, one commit, one push.
- CORE changes require explicit `CORE_UPGRADE`.
- New work should be plugin-based.
- No live trade, wallet signing, paid/API calls, or policy apply unless explicitly approved.

Current technical truth:

- Registry/kernel dirty-loop fixed and verified: second `tk registry` returns `UNCHANGED`.
- N7 water-drop probe completed: local visibility/search probe around `536.39 ms`; this is not full token-analysis latency.
- N8 trace completed: active system is partially flowing, but full token-analysis source→runtime→public readmodel→panel path was not proven at that point.
- N9 completed: source/public readmodel cache+manifest+index hash binding proven.
- N14 completed: public readmodel bridge created; active panel data now includes bridge JSON files and 8096 serves them.
- N14B completed: active panel UI was bound to bridge data and pushed.
- Phase9 draft service/timer archived as inert.
- News branch marked sealed inactive; service path preserved.
- Server provider corrected to Netcup.

N15 domain publish state:

- Target staging domain assumption: `panel.coinoskobi.xyz`.
- Nginx template exists: `deploy/nginx/coinoskobi_panel_8096_proxy.conf.template`.
- Apply script exists: `deploy/nginx/apply_panel_coinoskobi_xyz.sh`.
- Verify script exists: `deploy/nginx/verify_panel_domain.sh`.
- Rollback script exists: `deploy/nginx/rollback_panel_domain.sh`.
- GitHub side is ready; server-side DNS/Nginx/SSL apply still required.

Next safest work:

1. Pull latest GitHub commits to server.
2. Confirm DNS for `panel.coinoskobi.xyz` points to the Netcup server.
3. Run N15 apply script.
4. If HTTP returns 200 for `/` and `/data/backpressure_readmodel_refresh_cache.json`, issue SSL with certbot.
5. Run verify script and commit result JSON.
