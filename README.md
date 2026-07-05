# TOKENOSKOBI / COINOSKOBI

Canonical live state is not stored in this README.

Use the kernel bootstrap:

```bash
cd /root/tokenoskobi_clean_v1 || exit 1
tk ai
tk sync
git status --short
```

New ChatGPT windows should read:

1. `NEXT_CHAT_HANDOFF.md`
2. `PROJECT_RUNTIME.json`
3. `TOKENOSKOBI_OS_REGISTRY.json`
4. `PROJECT_HISTORY.json`

Rules:

- Repository/server state is source of truth.
- Do not open a new ERA unless explicitly requested.
- Do not repeat closed audits unless drift is detected.
- Prefer one complete operation, one verification set, one commit, one push.
- CORE changes require explicit CORE_UPGRADE.
- New work should be plugin-based.
- No live trade, wallet signing, or paid/API calls unless explicitly approved.

Historical documentation remains under `docs/`, `data/`, and `archive/`.
