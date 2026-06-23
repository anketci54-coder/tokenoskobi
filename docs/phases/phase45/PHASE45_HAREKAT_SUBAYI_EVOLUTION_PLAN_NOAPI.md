# PHASE45_HAREKAT_SUBAYI_EVOLUTION_PLAN_NOAPI

## STATUS
PLAN_ONLY

## CONSTITUTIONAL_GATE_V1
SPEED_NEVER_DOWN=true
SECURITY_NEVER_DOWN=true
POWER_NEVER_DOWN=true
speed_degrades=false
security_degrades=false
power_degrades=false
hot_path_waits=false
risk_gate_weakens=false
ai_blocks_decision_chain=false
learning_blocks_execution=false

## HARD LOCKS
V1_SCOPE=true
MODE=PLAN_ONLY
DB_WRITE=false
RUNTIME_CHANGE=false
API_CALL=false
PANEL_WRITE=false
SERVICE_RESTART=false
GIT_PUSH=false
TRADE_AUTHORITY=false
AI_AUTHORITY=false
WALLET_AUTHORITY=false
AUTO_APPLY=false

## PURPOSE
Evolve the existing Harekât Subayı role into a hybrid AI operations officer inside the panel.

It explains, diagnoses, teaches, proposes repairs, and prepares training/export plans.

It does not execute changes by itself.

## CORE DOCTRINE
Harekât Subayı observes.
Harekât Subayı explains.
Harekât Subayı diagnoses.
Harekât Subayı proposes.
Human approves.
System applies only through approved phases.
Post-audit verifies.

## HYBRID AI DESIGN
### Local Small AI
- Runs on server
- Low or near-zero marginal cost
- Summarizes logs
- Classifies system issues
- Answers simple panel chat questions
- Never blocks HOT PATH
- Never makes final trade decisions

### API Fallback AI
- Used only when local model is insufficient
- Token budget controlled
- Cost guard required
- Used for deep diagnosis, repair planning, and code suggestion
- No auto-apply authority

## PANEL CHAT ROLE
The panel chat should answer:

- Why did the system reject this token?
- Why is this token watch-only?
- Why is News missing?
- Why did a runtime fail?
- What is the root cause?
- What repair plan is safest?
- What post-audit should run after repair?
- What should be sent to training?

## TRAINING EXPORT BUTTON LINK
Future panel button:

EĞİTİME GÖNDER

Planned modes:
- last_24h
- last_7d
- last_30d
- only_errors
- only_missed_opportunities
- only_scam_rug_honeypot_cases
- only_paper_outcomes

## SECURITY RULES
- No secrets in training export
- No wallet data in training export
- No auth file in training export
- No API keys in training export
- No raw live DB export to GPU server
- Only sanitized training bundles

## COST RULES
- Local first
- Small API model second
- Large API model only when explicitly needed
- Token budget required
- Daily cost ceiling required
- Per-question token ceiling required

## NON-GOALS
- No live AI integration
- No model install
- No API call
- No panel write
- No DB write
- No runtime change
- No service restart
- No git push
- No trade authority
- No wallet authority
- No auto repair

## NEXT_SAFE_STEP
PHASE45B_HAREKAT_SUBAYI_SCHEMA_PLAN_NOAPI

## FINAL_GATE
PASS_PHASE45_HAREKAT_SUBAYI_EVOLUTION_PLAN_NOAPI
