def prioritize(f):
 r,s,p,perf,stats=[f.get(k,0) for k in ("reliability","security","probability","performance","statistics")]
 gain=(r+s+p)/3; utility=gain-max(0,100-perf)-max(0,100-stats)
 risks=[f.get(k,0) for k in ("sybil_risk","mev_risk","insider_risk","attribution_risk")]
 high=sum(x>=70 for x in risks); epistemic=f.get("epistemic_status","UNKNOWN")
 if f.get("privacy_break"): tier="QUARANTINED"
 elif high>=2 or (f.get("contradiction_risk",0)>=70 and epistemic=="CONTESTED"): tier="QUARANTINED"
 elif high==1 or f.get("concept_drift",0)>=60 or f.get("attribution_confidence",100)<50: tier="HUMAN_REVIEW"
 elif not f.get("liquidity_actionable"): tier="WATCH_LOW"
 elif utility>=95 and f.get("performance_status")=="REPEATABLE_EDGE" and epistemic in ("CONFIRMED","SUPPORTED"): tier="WATCH_HIGH"
 elif utility>=70: tier="WATCH_MEDIUM"
 else: tier="WATCH_LOW"
 return {"watch_priority":tier,"net_utility":round(utility,4),"accept_baseline":utility>=95,
 "risk_components":dict(zip(("sybil","mev","insider","attribution"),risks)),
 "primary_hypothesis":f.get("primary_hypothesis","UNRESOLVED"),
 "strongest_alternative_hypothesis":f.get("strongest_alternative_hypothesis","UNOBSERVED_EXPLANATION"),
 "automatic_action":False,"human_final_authority":True}
