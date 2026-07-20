from era58_entity_resolution_engine_v1 import resolve
assert resolve({"known_infrastructure":True})["relation"]=="INFRASTRUCTURE_ONLY_NO_CONTROL_INFERENCE"
assert resolve({"sybil_risk":.9})["quarantine"] is True
assert resolve({"privacy_break":True})["confidence_cap"]==.25
assert resolve({"official_attribution":True})["relation"]=="CONFIRMED_LINK"
x={"common_gas_funder":1,"temporal_sync":1,"route_similarity":1,"profit_destination_match":1,"independent_evidence_count":2}
assert resolve(x)["relation"]=="PROBABLE_SAME_CONTROLLER"
print("ERA58D2_SYNTHETIC_TESTS=5/5_PASS")
