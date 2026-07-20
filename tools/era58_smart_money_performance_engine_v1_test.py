from era58_smart_money_performance_engine_v1 import evaluate
good=[.10,.08,-.03,.12,.05,-.02,.09,.07,.04,-.01]
assert evaluate(good,[x-.005 for x in good],.9)["status"]=="REPEATABLE_EDGE"
assert evaluate(good[:3],good[:3],.9)["status"]=="INSUFFICIENT_SAMPLE"
assert evaluate(good,[-.01]*10,.2)["status"]=="NON_ACTIONABLE_CAPACITY"
assert evaluate([.7,-.6,.2,-.4,.1,.1,.1,.1,.1,.1],[.7,-.6,.2,-.4,.1,.1,.1,.1,.1,.1],.9)["status"]=="FRAGILE_EDGE"
assert evaluate([.02,-.015]*5,[.015,-.01]*5,.8)["status"]=="UNPROVEN_EDGE"
print("ERA58D4_SYNTHETIC_TESTS=5/5_PASS")
