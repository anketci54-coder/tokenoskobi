#!/usr/bin/env python3
import json, re, shutil, hashlib, datetime, os
from pathlib import Path

ROOT=Path.cwd()
NOW=datetime.datetime.now(datetime.UTC).isoformat()
TS=datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")

TARGETS=[ROOT/"public", ROOT/"active_panel_8096/current/data"]
BACKUP=Path(f"/root/tokenoskobi_era44_public_exposure_backup_{TS}")
REPORT=ROOT/"data/control/era44_public_exposure_boundary_fix_noapi_v1.json"
MD=ROOT/"reports/LATEST_ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI.md"

FORBIDDEN_KEY_RE=re.compile(r"(secret|private|debug|internal|wallet_seed|seed_phrase|mnemonic|provider_url|rpc_url|raw_payload|source_path|absolute_path|recommended_action|action_hint|operator_note)", re.I)
FORBIDDEN_STR_RE=[
    re.compile(r"/root/tokenoskobi_clean_v1"),
    re.compile(r"sk-or-v1-[A-Za-z0-9_\-]+"),
    re.compile(r"(api[_-]?key|secret|private[_-]?key|mnemonic|seed phrase)\s*[:=]\s*[^,\s\"']+", re.I),
]

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def sanitize(obj, path=""):
    changed=[]
    if isinstance(obj, dict):
        out={}
        for k,v in obj.items():
            kp=f"{path}.{k}" if path else str(k)
            if FORBIDDEN_KEY_RE.search(str(k)):
                out[k]="[REDACTED_PUBLIC_BOUNDARY]"
                changed.append(kp)
            else:
                nv,ch=sanitize(v,kp)
                out[k]=nv
                changed.extend(ch)
        return out,changed
    if isinstance(obj, list):
        arr=[]
        for i,v in enumerate(obj):
            nv,ch=sanitize(v,f"{path}[{i}]")
            arr.append(nv); changed.extend(ch)
        return arr,changed
    if isinstance(obj, str):
        s=obj
        for rx in FORBIDDEN_STR_RE:
            s=rx.sub("[REDACTED_PUBLIC_BOUNDARY]",s)
        if s!=obj:
            return s,[path]
    return obj,[]

records=[]
BACKUP.mkdir(parents=True,exist_ok=True)

for base in TARGETS:
    if not base.exists():
        records.append({"target":str(base.relative_to(ROOT)) if base.is_relative_to(ROOT) else str(base),"exists":False})
        continue

    for p in sorted(base.rglob("*")):
        if p.is_symlink():
            target=os.readlink(p)
            exists=p.exists()
            if not exists:
                rel=p.relative_to(ROOT)
                backup_path=BACKUP/rel
                backup_path.parent.mkdir(parents=True,exist_ok=True)
                backup_path.write_text(target+"\n")
                p.unlink()
                records.append({"path":str(rel),"type":"broken_symlink_removed","target":target})
            else:
                records.append({"path":str(p.relative_to(ROOT)),"type":"symlink_recorded","target":target})
            continue

        if not p.is_file():
            continue

        rel=p.relative_to(ROOT)

        if p.suffix.lower() != ".json":
            continue

        before_hash=sha(p)
        raw=p.read_text(errors="replace")
        try:
            data=json.loads(raw)
        except Exception as e:
            records.append({"path":str(rel),"type":"json_parse_failed","error":str(e),"sha256":before_hash})
            continue

        new_data,changes=sanitize(data)
        if not changes:
            records.append({"path":str(rel),"type":"json_checked_no_change","sha256":before_hash})
            continue

        backup_path=BACKUP/rel
        backup_path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,backup_path)

        p.write_text(json.dumps(new_data,indent=2,ensure_ascii=False)+"\n")
        after_hash=sha(p)

        records.append({
            "path":str(rel),
            "type":"json_sanitized",
            "changed_paths":changes[:200],
            "changed_count":len(changes),
            "before_sha256":before_hash,
            "after_sha256":after_hash,
            "backup_path":str(backup_path)
        })

changed=[r for r in records if r.get("type") in ("json_sanitized","broken_symlink_removed")]
decision="PASS_ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI" if changed else "PASS_ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NO_CHANGES_REQUIRED_NOAPI"

out={
  "era":"ERA44",
  "phase":"PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI",
  "created_at_utc":NOW,
  "targets":[str(t.relative_to(ROOT)) if t.is_relative_to(ROOT) else str(t) for t in TARGETS],
  "backup_dir":str(BACKUP),
  "records":records,
  "changed_count":len(changed),
  "decision":decision,
  "next_step":"ERA44_PUBLIC_EXPOSURE_BOUNDARY_POST_FIX_AUDIT_NOAPI",
  "guards":{
    "external_api_calls":0,
    "live_trade":False,
    "wallet_action":False,
    "db_schema_change":False,
    "service_change":False,
    "nginx_change":False,
    "cleanup_performed":False,
    "public_json_sanitization_only":True
  }
}
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")

MD.parent.mkdir(parents=True,exist_ok=True)
MD.write_text(
"# ERA44 PUBLIC EXPOSURE BOUNDARY FIX NOAPI\n\n"
f"- Created UTC: {NOW}\n"
f"- Decision: `{decision}`\n"
f"- Changed public-facing items: {len(changed)}\n"
f"- Backup dir: `{BACKUP}`\n"
"- Scope: public JSON/symlink boundary only. No DB/schema/service/nginx/wallet/trade mutation.\n\n"
"## Changed Items\n" +
("\n".join([f"- `{r.get('path')}` — `{r.get('type')}` — changes: {r.get('changed_count',1)}" for r in changed]) if changed else "- No changes required.") + "\n"
)

rtp=ROOT/"PROJECT_RUNTIME.json"
rt=json.loads(rtp.read_text())
wu={
 "id":"ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI",
 "type":"PUBLIC_EXPOSURE_BOUNDARY_FIX",
 "status":"WORK_UNIT_OPEN",
 "last_completed_step":"ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI",
 "next_step":"ERA44_PUBLIC_EXPOSURE_BOUNDARY_POST_FIX_AUDIT_NOAPI"
}
ns={"name":"ERA44_PUBLIC_EXPOSURE_BOUNDARY_POST_FIX_AUDIT_NOAPI","status":"READY"}
rt["current_work_unit"]=wu
rt["next_safe_step"]=ns
cs=rt.get("current_state") if isinstance(rt.get("current_state"),dict) else {}
cs["active_work_unit"]=wu
cs["next_safe_step"]=ns
cs["runtime_status"]="WORK_UNIT_OPEN"
cs["updated_at"]=NOW
rt["current_state"]=cs
rt["last_completed"]="ERA44_PUBLIC_EXPOSURE_BOUNDARY_FIX_NOAPI"
rt["status"]="WORK_UNIT_OPEN"
rtp.write_text(json.dumps(rt,indent=2,ensure_ascii=False)+"\n")

print("DECISION:",decision)
print("CHANGED:",len(changed))
print("BACKUP:",BACKUP)
print("NEXT_STEP:",ns["name"])
