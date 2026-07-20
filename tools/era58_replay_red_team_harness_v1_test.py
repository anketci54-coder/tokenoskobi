from era58_replay_red_team_harness_v1 import replay
good=[.10,.08,-.03,.12,.05,-.02,.09,.07,.04,-.01]; perf=(good,[x-.005 for x in good],.9)
base={"reliability":100,"security":100,"probability":100,"performance":100,"statistics":100,"liquidity_actionable":1,"epistemic_status":"SUPPORTED","attribution_confidence":90}
smart={"realized_trades":12,"consistency":.8,"liquidity_actionable":1,"mev_risk":.1,"team_risk":.1,"sybil_risk":.1}
clean={"entity":{"official_attribution":1},"behavior":smart,"performance":perf,"news":{"source_reliability":80,"claim_credibility":80,"flow_consistency":80},"priority":base}
assert replay(clean)["decision_status"]=="WATCH_HIGH"
assert replay(clean|{"behavior":{"mev_pattern":1},"priority":base|{"mev_risk":80}})["decision_status"]=="HUMAN_REVIEW"
assert replay(clean|{"entity":{"sybil_risk":.9},"priority":base|{"sybil_risk":80}})["decision_status"]=="QUARANTINED"
assert replay(clean|{"news":{"source_reliability":80,"claim_credibility":80,"flow_consistency":20,"positive_news":1,"net_selling":1}})["decision_status"]=="HUMAN_REVIEW"
fragile=[.7,-.6,.2,-.4,.1,.1,.1,.1,.1,.1]
assert replay(clean|{"performance":(fragile,fragile,.9)})["decision_status"]=="HUMAN_REVIEW"
assert replay(clean|{"entity":{"privacy_break":1}})["decision_status"]=="QUARANTINED"
u=replay({"entity":{},"behavior":{},"performance":perf,"news":{},"priority":base|{"reliability":50,"security":50,"probability":50,"performance":50,"statistics":50}})
assert u["decision_status"]=="WATCH_LOW" and u["strongest_alternative_hypothesis"] and u["automatic_action"] is False
print("ERA58D7_SYNTHETIC_REPLAYS=7/7_PASS")
