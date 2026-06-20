# Tokenoskobi / Coinoskobi Panel Implementation Gates v1

Phase: `UI_CONTRACT5_PANEL_IMPLEMENTATION_GATES_NOAPI`  
Timestamp: `20260517_191437`

## 1. Core rule

Panel implementation starts only after these gates are defined and testable:

1. TECH_PASS
2. DATA_PASS
3. FIT_PASS
4. TRUTH_PASS
5. PRODUCT_PASS

Technical PASS is never automatically Product PASS.

## 2. Implementation gate order

1. PLAN_GATE
2. DATA_CONTRACT_GATE
3. VIEW_MODEL_GATE
4. MOTION_TRUTH_GATE
5. FIT_GATE
6. PREVIEW_GATE
7. USER_PRODUCT_REVIEW_GATE
8. BASELINE_CANDIDATE_GATE
9. APPLY_PLAN_GATE
10. EXPLICIT_APPROVAL_GATE
11. REAL_APPLY_GATE
12. POST_AUDIT_GATE

## 3. PASS matrix

### TECH_PASS

- code runs
- syntax ok
- expected files created
- no failed checks
- no service/timer crash

### DATA_PASS

- all displayed fields map to canonical layer
- no duplicate calculation
- no hardcoded production metric
- no stale source used as live
- empty/missing data renders explicit empty_state

### FIT_PASS

- body vertical scroll absent on primary screen
- laptop fit profile passes
- desktop fit profile passes
- critical controls visible
- sidebar visible
- detail surfaces use local scroll only

### TRUTH_PASS

- every motion has source_layer
- every motion has source_uid
- every motion has reason
- every motion has freshness and expiry
- no fake/demo/mock motion
- no panel-invented motion

### PRODUCT_PASS

- user visually accepts
- premium feeling
- not toy-like
- not distracting
- clear information hierarchy
- icons/text/motion balanced

## 4. Hard fail rules

The following immediately fail implementation:

- body scroll on primary screen
- fake pulse/glow/radar without source_uid
- duplicated canonical data
- hardcoded production metric
- panel calculating risk/news/lifecycle directly
- motion state created inside panel
- active 8096 write without explicit approval
- DB/API/fetch/paper/live mutation without explicit approval
- preview accepted as baseline without user visual approval
- TECH_PASS marked as PRODUCT_PASS automatically
- source freshness ignored
- stale data shown as active
- buy/sell encouragement while hard_block exists
- long raw table/log dump on primary screen
- new product-specific hack/yama script

## 5. Preview rules

Preview must:

- state source baseline
- state view_model source
- state no active panel mutation
- expose PASS matrix
- not be promoted automatically

Protected:

- active 8096
- Haber final 8101
- Token Yaşam final 8102

## 6. Baseline rules

Candidate requires:

- TECH_PASS
- DATA_PASS
- FIT_PASS
- TRUTH_PASS
- user visual approval

Baseline requires:

- PRODUCT_PASS
- post-audit
- rollback path
- accepted_baselines copy
- latest symlink update only after approval

Active apply requires:

- separate apply plan
- explicit approval sentence
- backup
- real apply
- post-audit
- active panel health check

## 7. No-yama policy

- No blind regex patches to active panel.
- No product-specific one-off hack.
- No repeated preview clutter without cleanup/archive plan.
- Reusable architecture first: data contract, view model, motion state, fit rules.
- If visual source is bad, stop coding and return to asset/design source.

## 8. Implementation ready definition

Panel code can start only if:

- UI_CONTRACT1 exists
- UI_CONTRACT2 exists
- UI_CONTRACT3 exists
- UI_CONTRACT4 exists
- UI_CONTRACT5 exists
- target screen has view_model schema
- target screen has fit rules
- target screen has motion truth rules
- target screen has preview acceptance plan

## 9. Next phase

`UI_BUILD1_LIVING_PANEL_FOUNDATION_PLAN_NOAPI`
