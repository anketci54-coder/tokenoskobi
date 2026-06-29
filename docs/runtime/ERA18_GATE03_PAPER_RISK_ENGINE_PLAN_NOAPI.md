# ERA18_GATE03_PAPER_RISK_ENGINE_PLAN_NOAPI

STATUS=PLAN_ONLY_NOAPI

RISK LIMITS
- Position Limit
- Daily Loss Limit
- Drawdown Limit
- Token Risk Cap
- Liquidity Cap
- Exposure Cap
- Correlation Cap

KILL SWITCH
Risk breach -> PAPER_OBSERVE_ONLY
Critical breach -> PAPER_FAIL_CLOSED
Silent failure forbidden
Audit event required

RECOVERY
Manual review required
Auto resume forbidden
New audit required after fail closed

BOUNDARY
Paper risk cannot enable live execution.
Wallet/signing/real order remain disabled.

4G
Speed=ASYNC_RISK_EVAL_HOT_PATH_UNCHANGED
Security=RISK_LIMITS_AND_KILL_SWITCH_REQUIRED
Power=PAPER_DECISIONS_RISK_CERTIFIED
Economy=MINIMUM_RISK_STATE

NEXT
ERA18_GATE03B_PAPER_RISK_ENGINE_DRYRUN_NOAPI
