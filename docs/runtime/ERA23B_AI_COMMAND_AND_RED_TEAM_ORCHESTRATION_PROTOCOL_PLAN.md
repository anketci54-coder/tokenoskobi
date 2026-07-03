# ERA23B_AI_COMMAND_AND_RED_TEAM_ORCHESTRATION_PROTOCOL_PLAN

STATUS=PLAN_CREATED_NOT_APPLIED
WORK_UNIT=ERA23B_AI_COMMAND_AND_RED_TEAM_ORCHESTRATION_PROTOCOL_PLAN
CREATED_AT_UTC=2026-07-03T07:56:20Z
SCOPE=PLAN_ONLY_NO_RUNTIME_MUTATION
CANONICAL_FILE=docs/runtime/ERA23B_AI_COMMAND_AND_RED_TEAM_ORCHESTRATION_PROTOCOL_PLAN.md
PREVIOUS_CONFIRMED_HEAD=ae7468a018fa7006ab87764c65fe5b7f2998a56b
NEXT_REQUIRED_STAGE=APPROVAL

## Purpose

ERA23B defines the AI Command and Red Team Orchestration Protocol for Tokenoskobi OS.
The protocol lets multiple AI lanes support planning, review, red-team attack, repository reasoning, contradiction detection, and merge recommendation without gaining runtime, trade, credential, or canonical authority.

## Non-Negotiable Boundaries

- TRADE_AUTHORITY remains locked.
- AI systems do not receive secrets, private keys, passwords, seed phrases, wallet keys, htpasswd values, or unrestricted server control.
- AI systems cannot directly approve live execution.
- AI systems cannot directly mutate canonical state.
- Red-team output is evidence, not command authority.
- GitHub/local workspace remains source-control seal.
- Local server state overrides GitHub remote and AI memory when conflict exists.

## AI Lanes

CHATGPT_LANE=planning,paste_and_run_code,canonical_draft,test_audit_design,handoff_continuity,recommendation_only
GITHUB_CODEX_COPILOT_LANE=repo_reasoning,inline_support,diff_review,test_support,no_independent_merge_authority
CLAUDE_REVIEW_LANE=conservative_review,logic_consistency,bloat_check,safety_maintainability_review,block_by_evidence_only
GEMINI_RED_TEAM_LANE=adversarial_review,architecture_attack,threat_modeling,unknown_unknowns,failure_mode_generation,evidence_only
HAREKAT_SUBAYI_LANE=compare_outputs,score_risk,detect_conflict,detect_hallucination,recommend_merge_or_no_merge,final_authority_user_and_process

## Input Package Contract

Every AI lane must receive bounded input only:
- WORK_UNIT
- current HEAD
- current branch
- target file list
- forbidden mutation list
- allowed mutation list
- exact objective
- current stage
- required output format
- evidence level requested
- stop conditions

Forbidden inputs:
- secrets
- private keys
- server passwords
- wallet seed phrases
- unrestricted shell access
- unmasked paid API tokens

## Output Package Contract

Required normalized fields:
AI_LANE=
INPUT_DIGEST=
CLAIMS=
EVIDENCE=
RISKS=
CONFLICTS=
RECOMMENDED_ACTION=
BLOCKERS=
CONFIDENCE=

Claims without evidence must be marked UNVERIFIED.

## Evidence Levels

L0_NAME_REFERENCE=thing is named
L1_SCHEMA_REFERENCE=thing is described in schema or doctrine
L2_PHYSICAL_EXISTS=file, table, service, or path physically exists
L3_NONZERO_DATA_OR_CONTENT=relevant non-empty content exists
L4_PRODUCER_LOCATED=producer or generator is located
L5_RUNTIME_CHAIN_LOCATED=runtime path is located
L6_CONSUMER_CHAIN_LOCATED=downstream consumer path is located
L7_CLOSED_AND_SEALED=committed,pushed,remote_verified,github_sealed,runtime_updated,closed

## Conflict Resolution Rules

1. Local server evidence beats AI memory.
2. Git diff beats verbal claim.
3. Test output beats assumption.
4. Post-audit beats pre-audit.
5. Canonical file beats loose note.
6. User approval beats recommendation.
7. Safety block beats speed pressure.
8. Trade lock beats opportunity pressure.

Conflict classes:
- FACT_CONFLICT
- ARCHITECTURE_CONFLICT
- SECURITY_CONFLICT
- RUNTIME_CONFLICT
- DOCUMENTATION_CONFLICT
- COST_CONFLICT
- SCOPE_CONFLICT
- AUTHORITY_CONFLICT

Resolution choices:
- ACCEPT
- REJECT
- DEFER
- SPLIT_WORK_UNIT
- REQUIRE_MORE_EVIDENCE

## Red Team Attack Surface

- prompt injection into handoff or canonical docs
- fake evidence in generated reports
- stale source-of-truth claims
- hallucinated file paths
- accidental secret exposure
- workflow bypass pressure
- documentation bloat
- hidden runtime mutation
- test without audit
- audit without evidence
- commit without remote verification
- GitHub seal without local confirmation
- over-aggressive automation
- live trade authority leakage
- uncontrolled AI-to-AI amplification
- conflicting recommendations
- unbounded file growth
- copy-paste shell corruption
- heredoc interpolation errors
- hardcoded path drift
- old internal path reactivation
- API cost leak
- PAYG guard bypass

## Harekât Subayı Scorecard

SPEED_SCORE=0-100
SECURITY_SCORE=0-100
POWER_SCORE=0-100
THRIFT_SCORE=0-100
EVIDENCE_SCORE=0-100
CONFLICT_SCORE=0-100
MERGE_READINESS=PASS|FAIL|REVIEW_REQUIRED

Hard fail conditions:
- secrets exposed
- private keys requested
- live trade unlocked
- runtime mutation outside approval
- dirty git state before controlled write
- HEAD mismatch without explicit recovery
- canonical counterpart ignored
- untracked canonical artifact after closure
- unpushed closure commit
- remote verification missing
- GitHub seal missing

## Workflow Binding

PLAN -> APPROVAL -> APPLY -> TEST -> AUDIT -> POST_AUDIT -> COMMIT -> PUSH -> REMOTE_VERIFY -> GITHUB_SEAL -> RUNTIME_UPDATE -> WORK_UNIT_CLOSED

No AI lane may skip a stage.

## Zero Near-Zero Cost Doctrine

- prefer free web AI UIs where available
- use GitHub as source-control seal
- use GitHub Actions only when cost-safe
- use Telegram only for compact status alerts
- use local scripts for deterministic checks
- no paid inference dependency in core workflow
- no uncontrolled API loop
- no background paid model calls
- no unbounded crawler
- no paid execution without explicit user approval

## Minimal File Doctrine

This work unit creates exactly one canonical plan file.
No new database table.
No new service.
No new timer.
No new panel file.
No new runner.
No new preview.
No new workflow file.
No duplicate markdown.

## Test Plan For APPLY Stage

- target plan file exists
- title matches work unit
- no runtime files changed
- no database changed
- no panel changed
- no service, timer, or nginx changed
- git diff contains only approved canonical docs
- no duplicate ERA23B canonical file exists
- no secret-like pattern introduced
- next safe step is coherent

## Acceptance Criteria

- this file is the only ERA23B canonical plan
- current HEAD remains expected before approval
- no runtime mutation occurred
- no duplicate canonical counterpart exists
- user explicitly approves APPLY stage

## Planned Next Step

NEXT_SAFE_STEP=ERA23B_AI_COMMAND_AND_RED_TEAM_ORCHESTRATION_PROTOCOL_APPROVAL
NEXT_WORK_UNIT_AFTER_APPROVAL=ERA23B_AI_COMMAND_AND_RED_TEAM_ORCHESTRATION_PROTOCOL_APPLY_NOAPI

## Closure State

WORK_UNIT_STATUS=PLAN_CREATED_NOT_APPLIED
COMMIT_STATUS=NOT_COMMITTED
PUSH_STATUS=NOT_PUSHED
GITHUB_SEAL_STATUS=NOT_STARTED
RUNTIME_UPDATE_STATUS=NOT_STARTED
