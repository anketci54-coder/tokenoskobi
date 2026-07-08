# HOT Intelligence Ingress Gateway Plan NOAPI

- stage: `HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI`
- generated_at_utc: `2026-07-08T13:27:34.282990+00:00`
- decision: `OK_HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI_DOCUMENTED`
- next_step: `HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_NOAPI`

## Red Team Locked Rules
- `ONCHAIN_SOURCE_OF_TRUTH`: Onchain evidence outranks social/news claims when conflict exists.
- `CONFLICT_RESOLVER_BLOCKER`: HOT Gateway cannot go live without conflict resolver policy.
- `CRITICAL_REQUIRES_EVIDENCE`: CRITICAL event cannot become outbound alarm without Evidence/Prosecutor confirmation.
- `UNKNOWN_MONITOR`: Unknown anomaly is not automatically dangerous; classify as UNKNOWN_MONITOR unless severity evidence exists.
- `FUZZY_DUPLICATE_REQUIRED`: Exact hash is not enough; content similarity/fuzzy duplicate threshold must be planned.
- `DYNAMIC_TRUST_SCORE`: Source trust score must decay dynamically; recent major false signal has strong negative impact.
- `RATE_LIMIT_INGRESS`: Source-level rate limiting is mandatory against spam wave attacks.
- `ATOMIC_DATA_ONLY`: Do not copy every API parameter; keep only minimum decision-relevant fields.
- `SOURCE_REGISTRY_DEFER_DETAIL`: Deep source registry details are deferred; only minimum source identity/trust fields now.
- `NO_TOKENS_NO_KEYS`: No Telegram token, Discord bot, X API, live API key, wallet, signing, trade, or paper trade in this stage.

## Cold / Hot Boundary
- cold_news_refresh: `20min timer, fallback/backfill only`
- hot_gateway: `primary war intelligence ingress plan`
- forbidden_claim: `20min timer is real-time intelligence`
- current_stage: `plan and contract only`

## Atomic Ingress Event Contract
```json
{
  "canonical_content_hash": "sha256 normalized text",
  "chain": "optional string",
  "conflict_state": "NONE|SOCIAL_ONLY|ONCHAIN_CONFLICT|MULTI_SOURCE_CONFIRMED|QUARANTINE",
  "contract_address": "optional string",
  "event_type": "exploit|lp_pull|deployer_move|whale_move|bridge_risk|social_rumor|spam|unknown_monitor",
  "event_uid": "deterministic string",
  "fuzzy_duplicate_key": "planned similarity bucket",
  "raw_text_hash": "sha256",
  "raw_url_hash": "optional sha256",
  "received_at_utc": "ISO-8601",
  "routing_status": "DROP|INFO|WATCH|CRITICAL_CANDIDATE|QUARANTINE",
  "severity_guess": "INFO|WATCH|CRITICAL_CANDIDATE|QUARANTINE",
  "source_trust_score": "0-100 planned",
  "source_type": "telegram|discord|x|news|rss|onchain|dex|mempool|manual_synthetic",
  "source_uid": "string",
  "token_address": "optional string",
  "token_symbol": "optional string",
  "wallet_address": "optional string"
}
```

## Filter / Routing Policy
- `DROP`: price-only comment, generic shill, no token/chain/wallet/contract/actionable entity
- `INFO`: relevant but low severity, no immediate risk
- `WATCH`: single-source suspicious event or unknown_monitor without evidence
- `QUARANTINE`: conflicting evidence, spam wave, low-trust source, possible manipulation
- `CRITICAL_CANDIDATE`: high-severity event with entity extraction and at least preliminary evidence
- `CRITICAL_ALARM`: not produced by Gateway alone; requires Evidence/Prosecutor confirmation

## Conflict Resolver Policy
- `SOCIAL_VS_ONCHAIN`: If social says exploit but onchain has no anomaly, route WATCH or QUARANTINE, not CRITICAL_ALARM.
- `ONCHAIN_CONFIRMED`: If onchain confirms abnormal LP/deployer/bridge/wallet behavior, raise severity.
- `MULTI_SOCIAL_DUPLICATE`: Many social posts with same content are not multi-source confirmation unless independent source trust differs.
- `FAST_BUT_FAKE_GUARD`: Speed cannot bypass source trust, duplicate filtering, and evidence requirement.

## Safety Boundary
- plan_only: `True`
- noapi: `True`
- real_db_write: `False`
- db_schema_write: `False`
- runtime_change: `False`
- systemd_change: `False`
- telegram_token_use: `False`
- discord_bot_use: `False`
- x_api_use: `False`
- wallet: `False`
- signing: `False`
- live_trade: `False`
- paper_trade: `False`
- ai_trade_authority: `False`
- repo_artifact_write: `True`
