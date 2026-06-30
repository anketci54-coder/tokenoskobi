# SYSTEM_MAP.md

**Tokenoskobi System Architecture & Component Mapping**

**Version:** 1.0  
**Status:** ACTIVE  
**Classification:** Enterprise Architecture - System Design  
**Created:** 2026-06-30  
**Last Updated:** 2026-06-30  
**Owner:** Architecture Team  
**Related Documents:** 01_INDEX.md, 02_MANIFESTO.md, 05_ATLAS.md, AI_SPECIALISTS.md, OPERATION_PLAYBOOK.md

---

## SECTION 1: SYSTEM OVERVIEW

### Purpose

SYSTEM_MAP.md defines the logical architecture of Tokenoskobi—the relationships between components, the data flows, the authority boundaries, and the operational constraints.

This is NOT implementation. This is the architectural specification that guides implementation.

### Core Principle

```
Everything important has a role.
Everything with a role has authority boundaries.
Everything with authority has accountability.
Accountability is permanent.
```

---

## SECTION 2: SYSTEM COMPONENTS

### Primary Components

```
TOKENOSKOBI SYSTEM ARCHITECTURE
│
├─ AI ORCHESTRATION LAYER (Harekât Subayı)
│  ├─ Specialist Council (15 roles)
│  ├─ Guardian Enforcement (Constitutional rules)
│  ├─ Learning System (Confidence calibration)
│  ├─ Memory Systems (7 types)
│  └─ Decision Synthesis (Consensus mechanism)
│
├─ OPERATIONAL LAYER (Operators)
│  ├─ Analysis Initiation
│  ├─ Evidence Review
│  ├─ Decision Authority (Human approval)
│  ├─ Paper Trade Execution
│  └─ Crisis Management
│
├─ INTELLIGENCE LAYER (Knowledge Systems)
│  ├─ Case Library (Institutional memory)
│  ├─ Knowledge Graph (Entity relationships)
│  ├─ Lesson Storage (Learning outcomes)
│  ├─ Precedent Retrieval (Historical context)
│  └─ Outcome Tracking (Results recording)
│
├─ DATA LAYER (Evidence & Facts)
│  ├─ Onchain Data (RPC verified)
│  ├─ Risk Events (Detected threats)
│  ├─ Guardian Events (Blocks applied)
│  ├─ Runtime Events (System operations)
│  └─ News Events (External context)
│
├─ GOVERNANCE LAYER (Rules & Authority)
│  ├─ Constitutional Rules (240 immutable rules)
│  ├─ Guardian Authority (Hard enforcement)
│  ├─ Operator Authority (Decisions)
│  ├─ Amendment Procedures (Rule changes)
│  └─ Audit Trail (Permanent record)
│
└─ USER INTERFACE LAYER (Operator Interaction)
   ├─ Chat Experience (Natural language)
   ├─ Operational Boards (Status visibility)
   ├─ Evidence Cards (Data presentation)
   ├─ Decision Gates (Approval points)
   └─ Emergency Controls (KILL SWITCH)
```

---

## SECTION 3: AUTHORITY HIERARCHY

### Decision Authority

```
FINAL AUTHORITY HIERARCHY (Immutable)

LEVEL 1: GUARDIAN (Constitutional Enforcement)
├─ Authority: Absolute & immutable
├─ Can: Hard block any action
├─ Cannot: Be overridden (except via amendment)
├─ Governed by: Constitutional rules
└─ Updates: Via amendment procedure

LEVEL 2: RISK ENGINE (Risk Assessment)
├─ Authority: Risk verdict authority
├─ Can: Approve or reject based on risk
├─ Cannot: Override Guardian blocks
├─ Governed by: Risk framework
└─ Updates: Via specialist calibration

LEVEL 3: HAREKÂT SUBAYÍ (AI Orchestration)
├─ Authority: Recommendation synthesis
├─ Can: Synthesize specialist analysis
├─ Cannot: Override risk engine or Guardian
├─ Governed by: Orchestration rules
└─ Updates: Via specialist configuration

LEVEL 4: OPERATOR (Human Authority)
├─ Authority: Final decision approval
├─ Can: Approve or reject recommendations
├─ Cannot: Override Guardian or risk verdicts
├─ Governed by: Operational procedures
└─ Updates: Via training and policy

LEVEL 5: SYSTEM CONSTRAINTS
├─ Authority: Non-negotiable boundaries
├─ Hard constraints: 20 immutable principles
├─ Cannot be overridden: Ever
├─ Governed by: Constitutional framework
└─ Status: Permanent (cannot be changed)
```

---

## SECTION 4: DATA FLOWS

### Normal Operation Flow

```
OPERATOR INPUT
    ↓
HAREKÂT SUBAYÍ (Orchestration)
    ↓
[SPECIALIST COUNCIL - Parallel Processing]
├─ Evidence Specialist: Verify data
├─ Prosecutor Specialist: Assess deployer
├─ Risk Specialist: Evaluate risk
├─ Whale Specialist: Analyze positions
├─ Technical Specialist: Pattern analysis
├─ Memory Specialist: Historical comparison
├─ Guardian Specialist: Compliance check
└─ [8+ other specialists]
    ↓
[CONSENSUS & SYNTHESIS]
├─ Conflicts resolved
├─ Confidence calculated
├─ Recommendation formed
└─ Reasoning documented
    ↓
CASE CREATED (Immutable)
    ↓
OPERATOR DECISION GATE
├─ APPROVE → Paper Trade
├─ REJECT → Case archived
└─ INFO → More data
    ↓
OUTCOME TRACKING
├─ Entry recorded
├─ Exit recorded
├─ P&L calculated
└─ Result classified
    ↓
LEARNING INTEGRATION
├─ Case analyzed
├─ Lessons extracted
├─ Models updated
└─ Confidence adjusted
    ↓
CASE SEALED (Immutable)
    ↓
INSTITUTIONAL MEMORY UPDATED
```

### Emergency Flow

```
CRISIS DETECTED
    ↓
EMERGENCY AUTHORITY ACTIVATED
├─ Operator can invoke KILL SWITCH
├─ Operations halt immediately
├─ Guardian authority unchanged
└─ Human assessment required
    ↓
OPERATOR DECISION
├─ Assess threat
├─ Take corrective action
└─ Resume or escalate
    ↓
[NORMAL FLOW RESUMES or ESCALATION]
```

---

## SECTION 5: PERFORMANCE SPECIFICATIONS

### Response Time Targets

```
Operator Command Response:      < 2 seconds
├─ Chat input processing
├─ Initial routing
└─ First response indication

Evidence Collection:            < 5 seconds
├─ RPC queries
├─ Multi-source verification
└─ Consensus achievement

Specialist Analysis:            < 30 seconds
├─ All specialists complete
├─ Conflicts resolved
├─ Recommendation formed
└─ Confidence calculated

Operator Decision Gate:         < 1 minute
├─ Evidence presented
├─ Ready for approval
└─ Awaiting human decision

Paper Trade Execution:          Immediate
├─ Approved → executed
├─ Price snapshot taken
└─ Position opened

Case Retrieval:                 < 1 second
├─ Historical case lookup
├─ Similar case matching
└─ Precedent retrieval

Board Refresh:                  < 30 seconds
├─ Operational boards
├─ Status updates
├─ Alert aggregation
└─ Real-time data
```

### Scalability Targets

```
Concurrent Operators:           10-100+
├─ Single operator (baseline)
├─ Multiple simultaneous operators
├─ Coordination handled
└─ No cross-contamination

Active Cases:                   Thousands
├─ Search remains fast
├─ Knowledge Graph performs
└─ Learning system scales

Case Library Size:              50,000+ cases
├─ Years of institutional memory
├─ Historical retrieval fast
├─ Archive tiers (hot/warm/cold)
└─ No performance degradation

Knowledge Graph:                100,000+ nodes
├─ Entities and relationships
├─ Query performance maintained
├─ Traversal efficient
└─ Learning fast

Database:                       Years of data
├─ Evidence archived
├─ Cases preserved
├─ Learning models retained
└─ Audit trail complete
```

---

## SECTION 6: GOVERNANCE REQUIREMENTS

### Constitutional Binding

This document reflects the constitutional framework defined in MANIFESTO.md:
- 20 immutable operational principles
- 240+ immutable constitutional rules (across all documents)
- Guardian enforcement (absolute, non-overridable)
- Permanent immutability for all critical records

### Performance Compliance

All component implementations must:
1. Meet or exceed response time targets
2. Support scalability targets
3. Maintain immutability guarantees
4. Preserve audit trails
5. Enforce authority hierarchy

### Monitoring Requirements

System must continuously track:
- Response times (all operations)
- Search performance (cases, entities)
- Concurrent user handling
- Data consistency
- Authority enforcement

---

## SECTION 7: RELATED DOCUMENTS

**Upstream (Context):**
- 01_INDEX.md — Repository index
- 02_MANIFESTO.md — Constitutional principles
- 05_ATLAS.md — Architecture relations

**Peer (Components):**
- AI_SPECIALISTS.md — Specialist system specification
- OPERATION_PLAYBOOK.md — Operational procedures
- HAREKAT_KARARGAHI_UI_SPEC.md — User interface specification

**Downstream (Knowledge):**
- CASE_LIBRARY.md — Institutional memory
- KNOWLEDGE_GRAPH_ARCHITECTURE.md — Entity relationships
- PROJECT_MASTER_STATE.md — Current technical state

---

## SECTION 8: DOCUMENT METADATA

**Version History:**
- 1.0 (2026-06-30): Initial canonical specification

**Review Status:**
- ✓ Architecture review: APPROVED
- ✓ Governance review: APPROVED
- ✓ Constitutional alignment: VERIFIED
- Status: CANONICAL

**Authorization:**
- Owner: Architecture Team
- Authority: Başkomutan (final)
- Immutability: CONSTITUTIONAL

**Next Review:**
- Trigger: Major architecture change
- Process: Amendment procedure
- Timeline: As needed

---

## END OF SYSTEM_MAP.md

**Canonical Status:** ACTIVE  
**Immutability:** GUARANTEED  
**Authority:** CONSTITUTIONAL
