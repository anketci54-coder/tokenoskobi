
import hashlib
import json
import re
from typing import Any

ZERO_HASH="0"*64

def canonical_bytes(value:Any)->bytes:
    return json.dumps(
        value,ensure_ascii=False,sort_keys=True,
        separators=(",",":")
    ).encode("utf-8")

def sha256(value:bytes)->str:
    return hashlib.sha256(value).hexdigest()

def capacity_decision(
    current_bytes:int,
    incoming_bytes:int,
    entry_count:int,
    quota_bytes:int,
    max_entries:int,
    warning_ratio:float=0.80,
    critical_ratio:float=0.95,
):
    reasons=[]
    projected=current_bytes+incoming_bytes

    if min(current_bytes,incoming_bytes,entry_count,quota_bytes,max_entries)<0:
        reasons.append("NEGATIVE_CAPACITY_VALUE")
    if not 0<warning_ratio<critical_ratio<=1:
        reasons.append("WATERMARK_CONFIG_INVALID")
    if quota_bytes<=0 or max_entries<=0:
        reasons.append("QUOTA_CONFIG_INVALID")

    if reasons:
        return {
            "ok":False,"decision":"FAIL_CLOSED",
            "reason_codes":sorted(reasons),"watermark":"INVALID"
        }

    ratio=projected/quota_bytes

    if entry_count+1>max_entries:
        return {
            "ok":False,"decision":"FAIL_CLOSED",
            "reason_codes":["ENTRY_QUOTA_EXCEEDED"],
            "watermark":"CRITICAL"
        }

    if projected>quota_bytes or ratio>=critical_ratio:
        return {
            "ok":False,"decision":"FAIL_CLOSED",
            "reason_codes":["CRITICAL_WATERMARK"],
            "watermark":"CRITICAL"
        }

    if ratio>=warning_ratio:
        return {
            "ok":True,"decision":"ALLOW_WITH_BACKPRESSURE",
            "reason_codes":["WARNING_WATERMARK"],
            "watermark":"WARNING"
        }

    return {
        "ok":True,"decision":"ALLOW",
        "reason_codes":[],"watermark":"NORMAL"
    }

def build_entry(
    evidence:dict,
    sequence_number:int,
    previous_entry_hash:str=ZERO_HASH,
):
    if not isinstance(evidence,dict):
        raise ValueError("EVIDENCE_OBJECT_REQUIRED")
    if sequence_number<1:
        raise ValueError("SEQUENCE_NUMBER_INVALID")
    if (
        not isinstance(previous_entry_hash,str)
        or re.fullmatch(
            r"[0-9a-f]{64}",
            previous_entry_hash
        ) is None
    ):
        raise ValueError("PREVIOUS_HASH_INVALID")

    payload_hash=sha256(canonical_bytes(evidence))
    unsigned={
        "schema":"era57_evidence_ledger_entry_v1",
        "sequence_number":sequence_number,
        "previous_entry_hash":previous_entry_hash,
        "payload_sha256":payload_hash,
        "evidence":evidence,
    }
    entry=dict(unsigned)
    entry["entry_hash"]=sha256(canonical_bytes(unsigned))
    return entry

def verify_chain(entries:list[dict]):
    previous=ZERO_HASH

    for expected,entry in enumerate(entries,start=1):
        if not isinstance(entry,dict):
            return {"ok":False,"reason":"ENTRY_OBJECT_REQUIRED"}

        if entry.get("sequence_number")!=expected:
            return {"ok":False,"reason":"SEQUENCE_MISMATCH"}

        if entry.get("previous_entry_hash")!=previous:
            return {"ok":False,"reason":"PREVIOUS_HASH_MISMATCH"}

        evidence=entry.get("evidence")
        if not isinstance(evidence,dict):
            return {"ok":False,"reason":"EVIDENCE_OBJECT_REQUIRED"}

        if entry.get("payload_sha256")!=sha256(canonical_bytes(evidence)):
            return {"ok":False,"reason":"PAYLOAD_HASH_MISMATCH"}

        unsigned={k:v for k,v in entry.items() if k!="entry_hash"}
        if entry.get("entry_hash")!=sha256(canonical_bytes(unsigned)):
            return {"ok":False,"reason":"ENTRY_HASH_MISMATCH"}

        previous=entry["entry_hash"]

    return {
        "ok":True,
        "entry_count":len(entries),
        "root_hash":previous
    }

def append_evidence(
    entries:list[dict],
    evidence:dict,
    current_bytes:int,
    quota_bytes:int,
    max_entries:int,
):
    if not isinstance(entries,list):
        return {
            "ok":False,
            "decision":"FAIL_CLOSED",
            "reason_codes":["ENTRY_LIST_REQUIRED"],
            "capacity":None,
            "entry":None,
            "auto_delete":False,
            "partial_output_actionable":False
        }

    existing=verify_chain(entries)

    if not existing["ok"]:
        return {
            "ok":False,
            "decision":"FAIL_CLOSED",
            "reason_codes":[
                "EXISTING_CHAIN_INVALID:"+
                str(existing.get("reason"))
            ],
            "capacity":None,
            "entry":None,
            "auto_delete":False,
            "partial_output_actionable":False
        }

    previous=(
        entries[-1]["entry_hash"]
        if entries else ZERO_HASH
    )
    candidate=build_entry(
        evidence,
        len(entries)+1,
        previous
    )
    incoming=len(canonical_bytes(candidate))

    capacity=capacity_decision(
        current_bytes,incoming,len(entries),
        quota_bytes,max_entries
    )

    if not capacity["ok"]:
        return {
            "ok":False,
            "decision":"FAIL_CLOSED",
            "capacity":capacity,
            "entry":None,
            "auto_delete":False,
            "partial_output_actionable":False
        }

    return {
        "ok":True,
        "decision":capacity["decision"],
        "capacity":capacity,
        "entry":candidate,
        "auto_delete":False,
        "partial_output_actionable":False
    }

