from era58_entity_resolution_engine_v1 import resolve
from era58_mev_sniper_insider_classifier_v1 import classify
from era58_smart_money_performance_engine_v1 import evaluate
from era58_watch_priority_engine_v1 import prioritize
from era58_news_wallet_counter_intelligence_v1 import correlate
def replay(c):
 e=resolve(c.get("entity",{})); b=classify(c.get("behavior",{}))
 p=evaluate(*c["performance"]); n=correlate(c.get("news",{}))
 q=dict(c.get("priority",{})); q.update(performance_status=p["status"],primary_hypothesis=b["classification"],strongest_alternative_hypothesis=b["strongest_alternative_hypothesis"])
 w=prioritize(q); conflicts=[]
 if b["classification"]=="COPYABLE_SMART_MONEY" and p["status"]!="REPEATABLE_EDGE": conflicts.append("BEHAVIOR_PERFORMANCE_CONFLICT")
 if n["classification"]=="DISTRIBUTION_OR_EXIT_LIQUIDITY_RISK": conflicts.append("NEWS_FLOW_DISTRIBUTION_RISK")
 if n["news_flow_conflict"]: conflicts.append("NEWS_FLOW_CONFLICT")
 quarantine=e["quarantine"] or b["quarantine"] or w["watch_priority"]=="QUARANTINED"
 status="QUARANTINED" if quarantine else "HUMAN_REVIEW" if conflicts or w["watch_priority"]=="HUMAN_REVIEW" else w["watch_priority"]
 alt=n["strongest_alternative_hypothesis"] if conflicts else b["strongest_alternative_hypothesis"]
 return {"decision_status":status,"entity":e,"behavior":b,"performance":p,"news":n,"priority":w,
 "primary_hypothesis":b["classification"],"strongest_alternative_hypothesis":alt,
 "unresolved_conflicts":conflicts,"automatic_action":False,"human_final_authority":True}
