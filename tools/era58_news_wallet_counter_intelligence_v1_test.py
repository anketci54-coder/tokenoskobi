from era58_news_wallet_counter_intelligence_v1 import correlate
assert correlate({"source_reliability":80,"claim_credibility":80,"flow_consistency":80})["classification"]=="CONFIRMING_FLOW"
assert correlate({"positive_news":1,"net_selling":1})["classification"]=="DISTRIBUTION_OR_EXIT_LIQUIDITY_RISK"
assert correlate({"negative_news":1,"net_buying":1})["classification"]=="CONTRARIAN_ACCUMULATION"
assert correlate({"source_reliability":20,"claim_credibility":20})["classification"]=="LOW_CREDIBILITY_CLAIM"
assert correlate({"claim_credibility":70,"flow_consistency":20})["classification"]=="MIXED_EVIDENCE"
r=correlate({"source_reliability":88,"positive_news":1,"net_selling":1,"independence_score":.2})
assert r["source_reliability"]==88 and r["claim_credibility"]<=60 and r["strongest_alternative_hypothesis"]
print("ERA58D6_SYNTHETIC_TESTS=6/6_PASS")
