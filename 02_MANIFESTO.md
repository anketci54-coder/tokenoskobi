# 02 MANIFESTO

<!-- CANONICAL_WORKFLOW_RULES_LOCK_START -->
## CANONICAL GENERAL WORKFLOW RULES LOCK

Updated UTC: `2026-07-08T10:48:50.680029Z`

These rules are mandatory for every new ChatGPT window.

### Startup

Read in this order:

1. `PROJECT_RUNTIME.json`
2. `PROJECT_BOOT.json`
3. `06_PROJECT_MASTER_STATE.md`
4. `07_PROJECT_HANDOFF.md`
5. `02_MANIFESTO.md`
6. `03_ROADMAP.md`

### General Main Line Rule

- A main line is a real software/module milestone, major repair line, or major architecture line.
- A main line must contain related work only.
- Whatever the main line is called, do not create micro main lines for plan, apply, test, audit, review, risk decision, Go/No-Go, seal, documentation cleanup, state normalization, minor fix, or minor addition.
- Internal work must stay under the same main line unless the split rule below applies.

### Split Rule

- Prefer one main line.
- If one related topic is too large for one controlled closure, it may be split into 2-3 sibling main lines.
- Splitting is allowed only with explicit reason, such as:
  - scope is too large,
  - risk profile is materially different,
  - runtime/database/panel/service/integration impact areas are different,
  - testing and audit must be independent,
  - one main line would slow delivery instead of helping it.
- More than 3 sibling main lines requires consolidation review before continuing.
- If unsure whether to split, keep the work in the same main line and use A/B/C/D or A_1/A_2 first.

### A/B/C/D Rule

Use A/B/C/D/E/F under the same main line:

- `A` = plan or scope
- `B` = apply or build
- `C` = test or dry-run
- `D` = audit or review
- `E` = external review if needed
- `F` = GitHub seal or closure

Examples:

- `ERA52A_PLAN`
- `ERA52B_APPLY`
- `ERA52C_TEST`
- `ERA52D_AUDIT`
- `PHASE61A_PLAN`
- `PHASE61B_APPLY`
- `REPAIR_LINE_A_SCOPE`
- `REPAIR_LINE_B_FIX`

### Nested Number Rule

Use numbering only inside the same letter when that exact sub-area needs smaller parts:

- `ERA52B_1_FILE_LAYOUT`
- `ERA52B_2_READONLY_CONTRACT`
- `ERA52B_3_DRYRUN_WIRING`

If numbering grows beyond `_3`, stop and consolidate before continuing.

### Fix / Addition Rule

Fixes stay under the relevant letter:

- `ERA52B_FIX_1_READONLY_GUARD`
- `ERA52C_FIX_1_TEST_EXPECTATION`

Additions stay under the relevant letter:

- `ERA52B_ADD_1_CONTRACT_FIELD`
- `ERA52D_ADD_1_AUDIT_CHECK`

A fix or addition becomes a new main line only if it is genuinely a new major module.

### Deadline Rule

- Prefer small working code over repeated decision documents.
- Reduce documents.
- Reduce labels.
- Avoid repeated gate chains.

### Safety Rule

- `PROJECT_RUNTIME.json` is source of truth.
- Human approval required.
- AI trade authority is zero.
- Live trade locked.
- Paper trade locked until explicit phase.
- No Runtime, DB, panel, service, timer, deploy mutation unless explicitly in scope.
<!-- CANONICAL_WORKFLOW_RULES_LOCK_END -->

Bu belge projenin kalıcı anayasal kurallarıdır.
Bu belge proje tarihi, tamamlanan fazlar, roadmap, mimari detaylar, runtime durumu veya geçici kararlar içermez.

## PROJECT PHILOSOPHY

<!-- TOKENOSKOBI_MOTTO_OPPORTUNITY_COST_DOCTRINE_START -->
## TOKENOSKOBI MOTTO AND OPPORTUNITY COST DOCTRINE

STATUS: PERMANENT CONSTITUTIONAL RULE  
UPDATED_UTC: 2026-07-08T16:34:38.515049+00:00

Core motto:

- Şimşek kadar hızlı.
- Balyoz kadar güçlü.
- Kale kadar güvenli.
- Karınca kadar tutumlu.

This motto is not slogan text. It is a mandatory decision gate.

Any idea, module, red-team suggestion, AI recommendation, architecture change, documentation change, runtime change, or optimization may enter Tokenoskobi only if it passes this doctrine:

1. SPEED must not decrease unless explicitly measured and accepted.
2. POWER must not decrease unless explicitly measured and accepted.
3. SECURITY must not decrease unless explicitly measured and accepted.
4. ECONOMY / COST-EFFICIENCY must not decrease unless explicitly measured and accepted.
5. If at least one of SPEED, POWER, SECURITY, or ECONOMY increases and none decreases, the idea may continue.
6. If one decreases but others increase, opportunity cost calculation is mandatory before acceptance.
7. If the opportunity cost is negative, unclear, unmeasured, or creates bloat, the idea is rejected or deferred.
8. External red-team outputs, Gemini, Claude, Codex, Copilot, or any AI output are advisory only. They are never binding unless they pass this doctrine and receive user approval.
9. The system must never become heavy, bloated, slow, expensive, or over-documented merely because an external reviewer suggested more work.
10. Minimal safe path wins unless measured evidence proves a heavier path improves the motto balance.

Short form for every new window:

`SPEED ↑ / POWER ↑ / SECURITY ↑ / ECONOMY ↑ or OPPORTUNITY_COST_POSITIVE. Otherwise reject/defer.`

<!-- TOKENOSKOBI_MOTTO_OPPORTUNITY_COST_DOCTRINE_END -->

<!-- TOKENOSKOBI_MOTTO_OPPORTUNITY_COST_FORMULA_BINDING_START -->
## TOKENOSKOBI MOTTO OPPORTUNITY COST FORMULA BINDING

STATUS: PERMANENT_CONSTITUTIONAL_FORMULA_BINDING
UPDATED_UTC: 2026-07-08T16:48:01.474705+00:00

Existing formula source:
- tools/ede_opportunity_cost_baseline_v1.py
- data/era24f_ede_opportunity_cost_baseline_v1.json

ERA24F formula:
- expected_gain = (reliability + security + probability) / 3
- cost_penalty = max(0, 100 - performance)
- uncertainty_penalty = max(0, 100 - statistics)
- net_utility = expected_gain - cost_penalty - uncertainty_penalty
- accept_baseline = net_utility >= 95

Motto mapping:
- SPEED = performance
- POWER = average(reliability, probability)
- SECURITY = security
- ECONOMY = inverse cost, bloat, and maintenance burden

Decision:
- No regression and at least one dimension improves: continue.
- One dimension decreases but others improve: run opportunity cost.
- net_utility >= 95 plus explicit user approval: continue.
- net_utility < 95, unclear cost, bloat, missing evidence, or no user approval: reject or defer.
- External AI output is advisory only.

Short rule:
MOTTO_GATE = SPEED / POWER / SECURITY / ECONOMY.
OPPORTUNITY_COST_BASE = ERA24F_EDE.
ACCEPT = NO_REGRESSION OR NET_UTILITY_GE_95_WITH_USER_APPROVAL.
<!-- TOKENOSKOBI_MOTTO_OPPORTUNITY_COST_FORMULA_BINDING_END -->


Şimşek kadar hızlı.
Balyoz kadar güçlü.
Kale kadar güvenli.
Karınca kadar tutumlu.
Veriye göre konuş.
Veri yoksa konuşma.
Kanıt yoksa güven yok.
Risk skordan üstündür.
Önce hayatta kal.
Disiplin tahminden üstündür.
Genel çözüm özel yamadan üstündür.
Shadow canlıdan önce gelir.

## CONSTITUTIONAL PRINCIPLES

Kalıcı kural geçici karardan üstündür.
Kanıt varsayımdan üstündür.
Güvenlik hızdan taviz vermez.
Risk kabulü açık onay gerektirir.
Onaysız kapsam genişletme yasaktır.
Hiçbir iş canonical senkron olmadan tamamlanmış sayılmaz.

## AI BEHAVIOR RULES

AI is assistant.
AI is never authority.
AI never guesses.
AI never fabricates.
AI never invents architecture.
AI never invents roadmap.
AI never invents phases.
AI never invents passes.
AI never invents engines.
AI always requests approval before implementation.

## HUMAN AUTHORITY

Nihai otorite kullanıcıdır.
Açık kullanıcı onayı olmadan uygulama yapılmaz.
Belirsizlik varsa durulur, raporlanır ve kullanıcı beklenir.
AI hiçbir zaman kullanıcı adına karar vermez.

## DOCUMENTATION CONSTITUTION

One document.
One responsibility.

Rule changes
→ Manifesto

Roadmap
→ Roadmap

Completed work
→ Almanac

Architecture
→ Atlas

Current state
→ Project Master State

Continuation
→ Project Handoff

Navigation
→ Index

Bootstrap
→ PROJECT_RUNTIME.json and PROJECT_BOOT.json

Duplicate canonical documents are forbidden.
Her onaylı değişiklik etkilenen canonical belgeye işlenir.
Dokümantasyon etki analizi yapılmadan canonical değişiklik yapılmaz.

## CODE GENERATION CONSTITUTION

Unless explicitly requested:

Never generate code.

When code is requested:

- single block
- paste-and-run
- reusable
- generic
- minimal
- compact
- production-safe

Never require nano.
Never require vim.
Never require interactive editors.

## SERVER OPERATION CONSTITUTION

All server commands must:

start with

cd /root/tokenoskobi_clean_v1

Commands must:

- be safe
- be idempotent
- be SSH-safe
- be mobile-safe
- be 4G-safe

Never risk disconnecting the user.
Never terminate SSH.
Never require manual recovery without approval.

## GITHUB CONSTITUTION

Nothing is complete before:

git status clean

tests successful

post audit completed

GitHub synchronized

canonical documents synchronized

## SECURITY CONSTITUTION

Güvenlik varsayılan durumdur.
Yetki en az ayrıcalık ilkesine göre ele alınır.
Onaysız risk artıran işlem yapılamaz.
İnteraktif, geri dönüşü zor veya kullanıcıyı düşürebilecek adımlar açık onay ister.

## RISK CONSTITUTION

Risk skordan üstündür.
Belirsizlik rahatlatıcı yorumla kapatılamaz.
Bilinmeyen risk varsa güvenli varsayılan uygulanır.
Risk görünürlüğü, performans baskısından üstündür.

## CHANGE MANAGEMENT CONSTITUTION

Every approved change must include:

impact analysis

documentation update

verification

post audit

GitHub synchronization

## AMENDMENT PROCESS

Manifesto changes are constitutional amendments.
They require explicit user approval.

<!-- ERA23_GOVERNING_DOCTRINE_ADDENDUM_BEGIN -->

## ERA23 GOVERNING DOCTRINE ADDENDUM

STATUS: ACTIVE

This manifesto is the highest governing document of Tokenoskobi OS. If roadmap, implementation, AI recommendation or documentation conflicts with this document, this document prevails.

CORE RULES:
1. Evidence First
2. Capability Before Implementation
3. Concept Freeze
4. Concept Budget
5. Architectural Budget
6. Opportunity Cost
7. One Capability Per ERA
8. ERA Purity
9. One Purpose = One Canonical File
10. Canonical Source of Truth
11. Recovery Before Mutation
12. Measure Before Optimize
13. Local Before Push
14. Simulation Before Capital
15. Capital Preservation First
16. Evolution Through Evidence

DOCTRINE LIBRARY RULE:
War, nature, economics, game theory and technology doctrines are not copied as stories. They are converted into measurable decision principles. No doctrine enters the system because a famous commander, animal model or technology trend suggests it. It must pass mathematical verification, simulation advantage, paper-trade advantage, real-data statistical significance and positive opportunity cost.

CONCEPT LIFECYCLE:
IDEA -> HYPOTHESIS -> EXPERIMENT -> EVIDENCE -> CAPABILITY -> CORE

CONCEPT FREEZE:
During an active ERA, new engines, memory types, states and metaphors do not enter the core. They wait in backlog unless they are required for the current ERA capability.
<!-- ERA23_GOVERNING_DOCTRINE_ADDENDUM_END -->

## DISCIPLINE DOCTRINE SYNC — 2026-07-08T09:33:39.212698Z

- Risk is minimized, never zero.
- Runtime fail-silent, closure fail-safe.
- Opportunity Cost blocks non-critical bloat.
- Runtime never imports Lab.
- Lab remains read-only, NOAPI, and outside hot runtime path.

## MANIFESTO RULE INSERTION AND REPLACEMENT CONSTITUTION

Yeni onaylı bir kural mevcut manifesto kuralıyla çakışıyorsa, mevcut kural kendi yerinde yeni kuralla değiştirilir.
Değiştirilen eski kural manifesto içinde ikinci bir kopya olarak tutulmaz.
Yeni onaylı kural manifestoda mevcut değilse ve hiçbir mevcut kuralla çakışmıyorsa, manifestonun en sonuna eklenir.
Manifestonun mevcut yazım şekli, başlık düzeni, boşluk yapısı, yazı tipi ve biçimlendirmesi açık kullanıcı onayı olmadan değiştirilmez.

<!-- RISK_DRIVEN_PLAYBOOK_DOCTRINE_START -->
## RISK-DRIVEN PLAYBOOK AND COMPLEXITY DOCTRINE

STATUS: PERMANENT CONSTITUTIONAL RULE
UPDATED_UTC: 2026-07-13T10:21:10.001914+00:00

1. Constitution is invariant. It defines mandatory authority, evidence, canonical synchronization, commit, push, remote verification and closure rules.
2. Playbook is risk-driven. Read-only, temp-copy, shadow runtime, canary, benchmark, stress, chaos and external review are selected only when the work's risk justifies them.
3. No playbook may bypass or replace the Constitution.
4. Complexity must pay for itself through measured SPEED, POWER, SECURITY, ECONOMY or ADAPTABILITY value. Otherwise it is rejected or deferred.
5. Evidence never disappears. Reproducible temporary tools may be removed after their evidence and decision remain canonical.
6. Current state has one owner: `PROJECT_RUNTIME.json`. Other documents reference or summarize it and may not create competing current-state authority.
7. Prefer the smallest safe playbook that satisfies the risk class and evidence requirement.
<!-- RISK_DRIVEN_PLAYBOOK_DOCTRINE_END -->
