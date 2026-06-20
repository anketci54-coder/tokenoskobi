# AI Proposal Lifecycle Contract v1

Phase: PHASE32C_AI_PROPOSAL_SCHEMA_AND_VALIDATOR_CONTRACT_NOAPI

## Lifecycle

1. Maintenance Bundle is generated outside Fast Path.
2. AI receives only redacted bundle content.
3. AI returns a structured proposal object.
4. Proposal Validator checks schema, forbidden flags, secrets, Fast Path impact, rollback and approval rules.
5. Validator emits one of: REJECT, REVIEW_REQUIRED, PLAN_ONLY_ALLOWED, DRYRUN_ALLOWED, APPROVAL_REQUIRED.
6. Real apply is never performed by AI.
7. Real apply requires separate guarded phase and explicit user approval.
8. Every real apply requires backup, rollback and post-audit.

## Hard boundaries

- AI cannot write live DB.
- AI cannot patch runner.
- AI cannot write active panel.
- AI cannot restart service or change timer.
- AI cannot install local AI or download model.
- AI cannot call external API by default.
- AI cannot open paper/live trade.
- AI cannot connect wallet or sign transaction.
- AI cannot weaken risk gate or hardblock.
- AI cannot override quarantine truth boundary.
- AI cannot request secrets.

## Speed rule

Fast Path must not wait for AI, proposal validation, bundle generation, report generation or external model calls.

## Next phase

PHASE32D_APPROVAL_QUEUE_AND_ROLLBACK_REGISTRY_PLAN_NOAPI
