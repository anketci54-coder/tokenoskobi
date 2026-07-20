from era58_mev_sniper_insider_classifier_v1 import classify
cases=[({"drift_score":.8},"RE_EVALUATION_PENDING"),({"team_or_deployer_link":1},"TEAM_OR_DEPLOYER_LINKED"),({"mev_pattern":1},"NON_COPYABLE_MEV"),({"first_blocks_entry":1,"liquidity_event_proximity":1,"ultra_short_hold":1},"SNIPER"),({"pre_news_positioning":1,"repeat_early_entry":1,"independent_evidence_count":2},"INSIDER_SUSPECTED"),({"realized_trades":12,"consistency":.8,"liquidity_actionable":1,"mev_risk":.1,"team_risk":.1,"sybil_risk":.1},"COPYABLE_SMART_MONEY"),({"profit_positive":1,"liquidity_actionable":0},"NON_COPYABLE_PROFIT"),({"realized_trades":1,"x_return":20},"LUCKY_ONE_OFF"),({},"UNRESOLVED")]
for f,w in cases:
    r=classify(f); assert r["classification"]==w and r["strongest_alternative_hypothesis"] and r["confidence_cap"]<=.95
print("ERA58D3_SYNTHETIC_TESTS=9/9_PASS")
