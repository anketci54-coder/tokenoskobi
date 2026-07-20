from era58_watch_priority_engine_v1 import prioritize
base={"reliability":100,"security":100,"probability":100,"performance":100,"statistics":100,
"liquidity_actionable":1,"performance_status":"REPEATABLE_EDGE","epistemic_status":"SUPPORTED",
"primary_hypothesis":"SMART_MONEY","strongest_alternative_hypothesis":"SURVIVORSHIP_BIAS"}
assert prioritize(base)["watch_priority"]=="WATCH_HIGH"
assert prioritize(base|{"mev_risk":80})["watch_priority"]=="HUMAN_REVIEW"
assert prioritize(base|{"mev_risk":80,"sybil_risk":80})["watch_priority"]=="QUARANTINED"
assert prioritize(base|{"liquidity_actionable":0})["watch_priority"]=="WATCH_LOW"
assert prioritize(base|{"reliability":90,"security":90,"probability":90})["watch_priority"]=="WATCH_MEDIUM"
assert prioritize(base|{"privacy_break":1})["watch_priority"]=="QUARANTINED"
print("ERA58D5_SYNTHETIC_TESTS=6/6_PASS")
