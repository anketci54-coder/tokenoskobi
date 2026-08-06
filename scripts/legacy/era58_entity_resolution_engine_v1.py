def resolve(f):
    alt="SHARED_INFRASTRUCTURE_OR_COINCIDENCE"
    if f.get("privacy_break"): return {"relation":"UNKNOWN_PRIVACY_BROKEN","confidence_cap":0.25,"quarantine":True,"strongest_alternative_hypothesis":alt}
    if f.get("known_infrastructure") and not f.get("direct_control_proof"): return {"relation":"INFRASTRUCTURE_ONLY_NO_CONTROL_INFERENCE","confidence_cap":0.20,"quarantine":False,"strongest_alternative_hypothesis":alt}
    if max(f.get("sybil_risk",0),f.get("graph_pollution_risk",0))>=0.70: return {"relation":"QUARANTINED_HYPOTHESIS","confidence_cap":0.35,"quarantine":True,"strongest_alternative_hypothesis":"SYBIL_OR_GRAPH_POLLUTION"}
    if f.get("official_attribution") or f.get("direct_control_proof"): return {"relation":"CONFIRMED_LINK","confidence_cap":0.95,"quarantine":False,"strongest_alternative_hypothesis":"STALE_OR_COMPROMISED_ATTRIBUTION"}
    score=sum(bool(f.get(k)) for k in ("common_gas_funder","temporal_sync","route_similarity","profit_destination_match"))+int(f.get("independent_evidence_count",0))
    relation="PROBABLE_SAME_CONTROLLER" if score>=5 else "POSSIBLE_COORDINATION" if score>=3 else "INSUFFICIENT_EVIDENCE"
    cap={"PROBABLE_SAME_CONTROLLER":0.80,"POSSIBLE_COORDINATION":0.60,"INSUFFICIENT_EVIDENCE":0.30}[relation]
    return {"relation":relation,"confidence_cap":cap,"quarantine":False,"strongest_alternative_hypothesis":alt}
