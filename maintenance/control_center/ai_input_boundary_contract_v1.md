# AI Input Boundary Contract v1

Phase: PHASE32B_MAINTENANCE_STATE_READER_AND_BUNDLE_CONTRACT_NOAPI

## Allowed
- Phase names, final gates, failed check names
- State summaries and roadmap summaries
- Hashes and file paths that do not contain secrets
- Safe report snippets
- Proposed next-phase plan text

## Forbidden
- API keys
- Passwords
- Private keys
- Wallet seed/private key
- Bearer tokens
- Cookies/session tokens
- Raw auth headers
- Full .env contents
- SSH private keys
- Basic Auth password

## Authority
AI may only summarize, classify, propose, and draft dry-run plans.
AI may not apply changes, patch runner, write DB, restart services, change timers, open trades, connect wallet, or sign transactions.

## Speed rule
AI and maintenance bundle generation must remain outside Fast Path. Fast Path must not wait for AI.
