import hashlib, json

INVARIANTS=("schema_valid","authority_zero","sanitized_input",
 "evidence_dependencies_exposed","synthetic_not_production_proof",
 "red_team_not_canonical_evidence","material_alternative_hypothesis_gate",
 "unknown_not_safe","missing_engine_not_neutral",
 "human_cognitive_load_measured")

def canonical(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def seal(record,previous_hash):
    out=dict(record); out["previous_hash"]=previous_hash
    out["record_hash"]=hashlib.sha256(canonical(out)).hexdigest()
    return out

def evaluate(record):
    inv=record["invariants"]
    if set(inv)!=set(INVARIANTS):
        raise ValueError("INVARIANT_SET_BLOCK")
    blocks=sorted(k for k,v in inv.items() if v is not True)
    score=100*sum(v is True for v in inv.values())/len(INVARIANTS)
    eligible=(record["human_adjudicated"] is True
      and record["adjudication"] in ("PASS","FAIL")
      and record["synthetic"] is False and score==100)
    if record["training_eligible"] is not eligible:
        raise ValueError("TRAINING_ELIGIBILITY_BLOCK")
    if record["production_proof"] is not False or record["authority"]!=0:
        raise ValueError("AUTHORITY_OR_PRODUCTION_PROOF_BLOCK")
    load=record["human_cognitive_load"]
    if load["blocking_items"]<0 or load["estimated_review_minutes"]<0:
        raise ValueError("COGNITIVE_LOAD_BLOCK")
    return {"status":"PASS" if not blocks else "BLOCK",
            "score":score,"blockers":blocks,"training_eligible":eligible}

def verify_ledger(path):
    previous="GENESIS"; count=0
    for line in open(path,encoding="utf-8"):
        row=json.loads(line); claimed=row.pop("record_hash")
        if row["previous_hash"]!=previous:
            raise ValueError("HASH_CHAIN_BLOCK")
        if hashlib.sha256(canonical(row)).hexdigest()!=claimed:
            raise ValueError("RECORD_HASH_BLOCK")
        evaluate({**row,"record_hash":claimed})
        previous=claimed; count+=1
    return {"records":count,"last_hash":previous}
