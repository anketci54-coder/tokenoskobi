# V2_36 Human Approval Integrity To Execution Boundary Binding Plan

STAMP_UTC=2026-06-26T12:41:18.531334+00:00  
MODE=PLAN_ONLY_NOAPI

## Purpose

V2_35 locked human approval integrity and anti-manipulation doctrine. V2_36 binds that doctrine to the execution boundary so that a human approval can never become a shortcut around execution safety.

## Safety Scope

DB_WRITE=false  
PANEL_WRITE=false  
API_RPC=false  
RUNTIME_APPLY=false  
SERVICE_RESTART=false  
TIMER_CHANGE=false  
LIVE_DECISION=false  
LIVE_TRADE=false  
WALLET_ACCESS=false  
PRIVATE_KEY_ACCESS=false  

## Binding Doctrine

HUMAN_APPROVAL_INTEGRITY_REQUIRED=true  
ANTI_MANIPULATION_REQUIRED=true  
EXECUTION_BOUNDARY_LOCK_REQUIRED=true  
APPROVAL_CONTEXT_HASH_REQUIRED=true  
REPLAY_TIMEOUT_REQUIRED=true  
RISK_DELTA_REQUIRED=true  
UI_REQUIRED_WARNINGS_REQUIRED=true  
HIGH_RISK_TWO_STEP_REQUIRED=true  
SOCIAL_ENGINEERING_RESISTANCE_REQUIRED=true  
APPROVAL_NOT_BYPASS_EXECUTION=true  
WALLET_PRIVATE_KEY_BLOCKED=true  
LIVE_TRADE_BLOCKED=true  

## Contract Rules

1. APPROVAL_TO_EXECUTION_BOUNDARY_LOCK  
   Human approval may authorize only an execution request envelope, never direct wallet/live execution.

2. APPROVAL_CONTEXT_HASH_REQUIRED  
   Every approval must bind request_hash, risk_snapshot_hash, decision_context_hash, operator_id_hash, timestamp_utc, and expiry_utc.

3. REPLAY_TIMEOUT_REQUIRED  
   Expired, reused, mismatched, or stale approval tokens must fail closed before execution boundary.

4. RISK_DELTA_RECHECK_REQUIRED  
   If risk, liquidity, slippage, tax, route, or security context changes after approval, approval becomes invalid.

5. HIGH_RISK_TWO_STEP_CONFIRMATION_REQUIRED  
   High-risk classes require second independent confirmation and cannot downgrade to single approval.

6. UI_REQUIRED_WARNINGS_REQUIRED  
   Approval UI must show blocking warnings before approval creation; hidden warnings invalidate approval.

7. SOCIAL_ENGINEERING_RESISTANCE_REQUIRED  
   Approval text must be structured, explicit, non-ambiguous, and resistant to prompt/social pressure.

8. APPROVAL_NOT_BYPASS_EXECUTION  
   Human approval never bypasses Engine2 execution gates, wallet locks, paper/live progression, kill switches, or budget limits.

9. WALLET_PRIVATE_KEY_BLOCKED  
   No approval contract may request, expose, store, infer, or transmit private key, seed, or wallet secret material.

10. LIVE_TRADE_BLOCKED  
    This V2_36 phase is plan-only; live trading, wallet signing, runtime execution, RPC/API calls are forbidden.

## Required Next Audit

NEXT=V2_36_HUMAN_APPROVAL_INTEGRITY_TO_EXECUTION_BOUNDARY_BINDING_POST_PLAN_AUDIT_NOAPI
