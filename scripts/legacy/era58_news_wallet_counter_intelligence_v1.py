def correlate(f):
 sr=f.get("source_reliability",50); cc=f.get("claim_credibility",50)
 flow=f.get("flow_consistency",50); mr=f.get("manipulation_risk",0)
 independent=f.get("independence_score",1)>=.5
 adjusted=min(cc,60) if not independent else cc
 conflict=bool(f.get("news_flow_conflict")) or abs(adjusted-flow)>=40
 if sr<30 and adjusted<30: primary="LOW_CREDIBILITY_CLAIM"
 elif f.get("positive_news") and f.get("net_selling"): primary="DISTRIBUTION_OR_EXIT_LIQUIDITY_RISK"; mr=max(mr,70)
 elif f.get("negative_news") and f.get("net_buying"): primary="CONTRARIAN_ACCUMULATION"
 elif adjusted>=65 and flow>=65 and not conflict: primary="CONFIRMING_FLOW"
 else: primary="MIXED_EVIDENCE"
 alternatives={"DISTRIBUTION_OR_EXIT_LIQUIDITY_RISK":"PROFIT_TAKING_HEDGING_OR_MARKET_MAKING",
 "CONTRARIAN_ACCUMULATION":"UNRELATED_REBALANCING_OR_SHORT_COVERING",
 "CONFIRMING_FLOW":"CORRELATED_PUBLIC_INFORMATION_RESPONSE",
 "LOW_CREDIBILITY_CLAIM":"TRUE_CLAIM_FROM_WEAK_SOURCE",
 "MIXED_EVIDENCE":"TIMING_MISMATCH_OR_UNOBSERVED_ACTOR"}
 return {"classification":primary,"source_reliability":sr,"claim_credibility":adjusted,
 "flow_consistency":flow,"manipulation_risk":mr,"news_flow_conflict":conflict,
 "primary_hypothesis":primary,"strongest_alternative_hypothesis":alternatives[primary],
 "automatic_action":False,"human_final_authority":True}
