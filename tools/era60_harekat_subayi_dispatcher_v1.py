import json

AGENTS=("chatgpt-planner","claude-reviewer","codex-builder","gemini-red-team")
ROUTES={
 "PLANNING":("chatgpt-planner","claude-reviewer","gemini-red-team"),
 "CODE_CHANGE":AGENTS,
 "REVIEW_ONLY":("claude-reviewer","gemini-red-team"),
 "RED_TEAM":("gemini-red-team","claude-reviewer")}
RAW_KEYS={"raw_issue_body","raw_web_content","raw_vendor_content",
          "system_prompt_override","instructions_from_source"}

def dispatch(task):
    if task.get("sanitized") is not True or RAW_KEYS.intersection(task):
        raise ValueError("SANITIZATION_GATE_BLOCK")
    kind=task.get("task_type")
    if kind not in ROUTES or not task.get("task_id"):
        raise ValueError("INVALID_TASK")
    return {"task_id":task["task_id"],"required_agents":list(ROUTES[kind]),
            "provider_dispatch_active":False,"authority":0,
            "human_approval_required":True}

def _check_packet(p):
    required={"schema_id","task_id","agent_id","model_binding","status","evidence",
      "evidence_dependency_graph","uncertainty","alternative_hypotheses",
      "engine_coverage","utility_assessment","risk_assessment",
      "proposed_action","authority","human_approval_required"}
    if set(p)!=required or p["agent_id"] not in AGENTS:
        raise ValueError("PACKET_SCHEMA_BLOCK")
    if p["authority"]!=0 or p["human_approval_required"] is not True:
        raise ValueError("AUTHORITY_BLOCK")
    mb=p["model_binding"]
    if mb["exact_version_pinned"] is not True or mb["model_id"]=="UNBOUND_FAIL_CLOSED":
        raise ValueError("MODEL_BINDING_BLOCK")
    pa=p["proposed_action"]
    if pa["execution_allowed"] is not False or pa["requires_human_approval"] is not True:
        raise ValueError("EXECUTION_AUTHORITY_BLOCK")
    u=p["utility_assessment"]
    eg=(u["reliability"]+u["security"]+u["probability"])/3
    cp=max(0,100-u["performance"]); up=max(0,100-u["statistics"])
    nu=eg-cp-up
    if any(abs(u[k]-v)>1e-9 for k,v in
      (("expected_gain",eg),("cost_penalty",cp),
       ("uncertainty_penalty",up),("net_utility",nu))):
        raise ValueError("CANONICAL_FORMULA_DRIFT")
    if u["accept_baseline"]!=(nu>=95):
        raise ValueError("ACCEPT_BASELINE_DRIFT")

def aggregate(task,packets):
    route=dispatch(task)
    if len({p.get("agent_id") for p in packets})!=len(packets):
        raise ValueError("DUPLICATE_AGENT_PACKET")
    indexed={p["agent_id"]:p for p in packets}
    blockers=[]
    missing=sorted(set(route["required_agents"])-set(indexed))
    if missing: blockers.append("MISSING_REQUIRED_AGENTS:"+",".join(missing))
    for aid in sorted(indexed):
        p=indexed[aid]; _check_packet(p)
        if p["status"] in ("BLOCK","ERROR","INSUFFICIENT_EVIDENCE"):
            blockers.append(aid+":NON_PASS_STATUS")
        if p["uncertainty"]["blocking_unknowns"]:
            blockers.append(aid+":BLOCKING_UNKNOWNS")
        if p["engine_coverage"]["missing_engines"]:
            blockers.append(aid+":MISSING_ENGINE")
        if p["risk_assessment"]["blocking_risk_present"]:
            blockers.append(aid+":BLOCKING_RISK")
        if any(x["material"] and x["status"]=="OPEN"
               for x in p["alternative_hypotheses"]):
            blockers.append(aid+":MATERIAL_ALTERNATIVE_HYPOTHESIS")
        graph=p["evidence_dependency_graph"]
        node_ids={x["evidence_id"] for x in graph["nodes"]}
        if any(x["canonical_evidence"] and (x["synthetic"] or x["red_team_score"])
               for x in graph["nodes"]):
            blockers.append(aid+":INVALID_CANONICAL_EVIDENCE")
        degraded=False
        for g in graph["dependency_groups"]:
            if not set(g["evidence_ids"]).issubset(node_ids):
                blockers.append(aid+":UNKNOWN_DEPENDENCY_EVIDENCE")
            if len(set(g["agents_using"]))>1 and not g["shared_across_agents"]:
                blockers.append(aid+":UNEXPOSED_SHARED_DEPENDENCY")
            if g["independence_impact"] in ("DEGRADED","BLOCKED"):
                degraded=True
            if g["independence_impact"]=="BLOCKED":
                blockers.append(aid+":DEPENDENCY_INDEPENDENCE_BLOCKED")
        if graph["independence_degraded"]!=degraded:
            blockers.append(aid+":INDEPENDENCE_FLAG_MISMATCH")
    actions=sorted({p["proposed_action"]["action"] for p in packets})
    return {"task_id":task["task_id"],
      "status":"BLOCK" if blockers else "READY_FOR_HUMAN_REVIEW",
      "required_agents":route["required_agents"],"received_agents":sorted(indexed),
      "blockers":sorted(set(blockers)),"reported_actions":actions,
      "model_agreement_is_evidence":False,"model_vote_authority":0,
      "war_room_output_type":"INDICTMENT_NOT_ORDER",
      "recommended_next_step":"REQUEST_MORE_EVIDENCE" if blockers else "HUMAN_REVIEW",
      "execution_allowed":False,"authority":0,"human_approval_required":True}
