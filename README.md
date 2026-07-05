# TOKENOSKOBI / COINOSKOBI

This README is only a boot pointer. Canonical live state is not stored here.

Use the kernel bootstrap:

```bash
cd /root/tokenoskobi_clean_v1 || exit 1
git pull --ff-only origin main
tk ai
tk sync
git status --short
```

New ChatGPT windows should read only:

1. `NEXT_CHAT_HANDOFF.md`
2. `PROJECT_RUNTIME.json`
3. `TOKENOSKOBI_OS_REGISTRY.json`
4. `PROJECT_HISTORY.json`

Current direction:

- Keep root small.
- Keep active code separate from archive/history.
- Archive sealed or inert branches instead of deleting evidence.
- Do not treat `docs/archive/*`, `data/archive/*`, or `archive/*` as active state.
- Prefer GitHub-side inspection first; use server only for runtime/process/local generated evidence.

Safety rules:

- Repository/server state is source of truth.
- Do not open a new ERA unless explicitly requested.
- Do not repeat closed audits unless drift is detected.
- Prefer one complete operation, one verification set, one commit, one push.
- CORE changes require explicit `CORE_UPGRADE`.
- New work should be plugin-based.
- No live trade, wallet signing, paid/API calls, or policy apply unless explicitly approved.
