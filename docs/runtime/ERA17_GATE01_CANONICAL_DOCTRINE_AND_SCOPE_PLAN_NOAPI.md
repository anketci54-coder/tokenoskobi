# ERA17_GATE01_CANONICAL_DOCTRINE_AND_SCOPE_PLAN_NOAPI

STATUS=PLAN_ONLY_NOAPI

MISSION
READ_ONLY_CONSTITUTIONAL_RUNTIME_CERTIFICATION

TERMINOLOGY
PASS=LEGACY_FROZEN
ERA17_PLUS_UNIT=GATE
NEW_PHASE_IDENTIFIERS=false
NEW_PASS_IDENTIFIERS=false

READ_ONLY_ISOLATION
- wallet_absent
- signing_absent
- private_keys_absent
- transaction_encoder_absent
- abi_encoder_absent
- rpc_write_client_absent
- raw_tx_builder_absent
- order_creator_absent

CONSTITUTIONAL_INVARIANCE
Runtime does not self-recalibrate.
Runtime does not change thresholds.
Audit learns.
Human approval and new seal are required.

THRESHOLD_MODEL
- Constitutional Threshold = IMMUTABLE
- Operational Threshold = AUDIT_SEALED_ONLY
- Adaptive Threshold = ADVISORY_ONLY

CHAIN
Evidence -> Ledger -> ReadModel -> Decision -> Guardian -> Output

SUCCESS
Wrong ALLOW is critical failure.
FAIL_CLOSED is valid success.

NEXT
ERA17_GATE02_RUNTIME_KERNEL_AND_ISOLATION_DRYRUN_NOAPI
