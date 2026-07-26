#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE_HEAD=${PRODUCT_SLICE_02_MACHINE_SEAL_SOURCE_HEAD:-}
BRANCH=agent/product-slice-02-fix6-bounded-recovery
BASE_PATH=tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh
FIX1_PATH=tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix1.sh
FIX2_PATH=tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix2.sh
TEMP=/root/tokenoskobi_product_slice_02_machine_recovery_seal_fix2_patched.sh
NGINX_REPO=config/nginx/panel.coinoskobi.xyz.conf
SMOKE=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c

fail(){ printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
[[ "$SOURCE_HEAD" =~ ^[0-9a-f]{40}$ ]] || fail SOURCE_HEAD_MISSING_OR_INVALID
[[ "$(git rev-parse "origin/$BRANCH")" == "$SOURCE_HEAD" ]] || fail SOURCE_HEAD_NOT_CURRENT_BRANCH_HEAD
[[ "$(git merge-base e2c867d4fc14ed67af0ea096563a4f768e51c06e "$SOURCE_HEAD")" == e2c867d4fc14ed67af0ea096563a4f768e51c06e ]] || fail SOURCE_HEAD_BASE_INVALID
[[ -f "$NGINX_REPO" ]] || fail NGINX_REPO_FILE_MISSING

API_CODE="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 30 -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' https://panel.coinoskobi.xyz/api/v1/analyze 2>/dev/null || true)"
[[ "$API_CODE" == 401 ]] || fail EXTERNAL_API_NOT_401

git show "$SOURCE_HEAD:$BASE_PATH" > "$TEMP"

SOURCE_HEAD="$SOURCE_HEAD" TEMP="$TEMP" FIX1_PATH="$FIX1_PATH" FIX2_PATH="$FIX2_PATH" python3 - <<'PY'
from pathlib import Path
import os
p=Path(os.environ['TEMP'])
s=p.read_text(encoding='utf-8')
head=os.environ['SOURCE_HEAD']
fix1_path=os.environ['FIX1_PATH']
fix2_path=os.environ['FIX2_PATH']

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit('BLOCKED=PATCH_ANCHOR_MISSING_'+label)
    s=s.replace(old,new,1)

rep(
 'EXPECTED_FIX6_HEAD=bd7fa5ae6ddbedfc6f17f7f1d41aeda24720a33d',
 'EXPECTED_FIX6_HEAD='+head,
 'HEAD',
)
rep(
 'api_code(){ curl -sS -o "$1" -w \'%{http_code}\' --connect-timeout 5 --max-time 150 -H \'Content-Type: application/json\' --data \'{"token_address":"\'"$SMOKE"\'"}\' "$2" 2>/dev/null || true; }',
 'api_code(){ curl -sS -o "$1" -w \'%{http_code}\' --connect-timeout 5 --max-time 150 -H \'Content-Type: application/json\' --data \'{"token_address":"\'"$SMOKE"\'"}\' "$2" 2>/dev/null || true; }\napi_noauth_code(){ curl -sS -o /dev/null -w \'%{http_code}\' --connect-timeout 5 --max-time 30 -H \'Content-Type: application/json\' --data \'{"token_address":"\'"$SMOKE"\'"}\' "$1" 2>/dev/null || true; }',
 'API_FUNCTION',
)
rep(
 '    tar -xzf "$BACKUP/repo_before.tar.gz" -C "$ROOT"\n    git reset --quiet >/dev/null 2>&1 || true',
 '    rm -f \\\n      tools/tokenoskobi_product_slice_02_fix6_bounded_recovery.sh \\\n      tools/tokenoskobi_product_slice_02_fix6_helper.py \\\n      tools/tokenoskobi_product_slice_02_fix6_resume_nginx_recovery.sh \\\n      tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh \\\n      '+fix1_path+' \\\n      '+fix2_path+' \\\n      data/control/product_slice_02_single_token_decision_packet_v1.json \\\n      data/control/product_slice_02_smoke_analysis_v1.json \\\n      data/control/product_slice_02_nginx_route_recovery_v1.json \\\n      data/control/product_slice_02_machine_recovery_seal_v1.json \\\n      reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md\n    tar -xzf "$BACKUP/repo_before.tar.gz" -C "$ROOT"\n    git reset --quiet >/dev/null 2>&1 || true',
 'ROLLBACK',
)
rep(
 '[[ "$(http_code https://panel.coinoskobi.xyz/)" == 401 ]] || fail EXTERNAL_ROOT_NOT_401',
 '[[ "$(http_code https://panel.coinoskobi.xyz/)" == 401 ]] || fail EXTERNAL_ROOT_NOT_401\n[[ "$(api_noauth_code https://panel.coinoskobi.xyz/api/v1/analyze)" == 401 ]] || fail EXTERNAL_API_NOT_401',
 'EXTERNAL_API_GATE',
)
rep(
 '  tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh\ndo',
 '  tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh \\\n  '+fix1_path+' \\\n  '+fix2_path+'\ndo',
 'MATERIALIZE_LIST',
)
rep(
 '  git show "$EXPECTED_FIX6_HEAD:$rel" > "$rel"',
 '  if [[ "$rel" == tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh ]]; then\n    cp "$PRODUCT_SLICE_02_PATCHED_SELF" "$rel"\n  else\n    git show "$EXPECTED_FIX6_HEAD:$rel" > "$rel"\n  fi',
 'PATCHED_SELF_COPY',
)
rep(
 '  tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh\n\nSMOKE_JSON=',
 '  tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh \\\n  '+fix1_path+' \\\n  '+fix2_path+'\n\nSMOKE_JSON=',
 'CHMOD_LIST',
)
rep(
 "  'fix6_evidence_head':'bd7fa5ae6ddbedfc6f17f7f1d41aeda24720a33d',",
 "  'fix6_evidence_head':'"+head+"',",
 'EVIDENCE_HEAD',
)
rep(
 'git add \\\n  "$CONFIG" "$SERVER" "$TEST" "$UNIT" "$NGINX_REPO"',
 'python3 - <<\'PYWS\'\nfrom pathlib import Path\np=Path("config/nginx/panel.coinoskobi.xyz.conf")\ns=p.read_text(encoding="utf-8")\nlines=s.splitlines(keepends=True)\nout=[]\nchanged=0\nfor line in lines:\n    ending=""\n    body=line\n    if line.endswith("\\r\\n"):\n        body=line[:-2]; ending="\\r\\n"\n    elif line.endswith("\\n"):\n        body=line[:-1]; ending="\\n"\n    clean=body.rstrip(" \\t")\n    changed += int(clean != body)\n    out.append(clean+ending)\np.write_text("".join(out),encoding="utf-8")\nprint(f"NGINX_REPO_TRAILING_WHITESPACE_LINES_CLEANED={changed}")\nPYWS\nif grep -nE \'[[:blank:]]+$\' "$NGINX_REPO"; then fail NGINX_REPO_TRAILING_WHITESPACE_REMAINS; fi\n\ngit add \\\n  "$CONFIG" "$SERVER" "$TEST" "$UNIT" "$NGINX_REPO"',
 'WHITESPACE_NORMALIZATION',
)
rep(
 '  tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh \\\n  data/control/product_slice_02_single_token_decision_packet_v1.json',
 '  tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh \\\n  '+fix1_path+' \\\n  '+fix2_path+' \\\n  data/control/product_slice_02_single_token_decision_packet_v1.json',
 'GIT_ADD_LIST',
)
p.write_text(s,encoding='utf-8')
PY

chmod 0700 "$TEMP"
bash -n "$TEMP"

set +e
PRODUCT_SLICE_02_PATCHED_SELF="$TEMP" \
PRODUCT_SLICE_02_MACHINE_SEAL_CONFIRM=YES \
bash "$TEMP"
RC=$?
set -e

if [[ "$RC" -ne 0 ]]; then
  rm -f "$TEMP"
  printf 'MACHINE_SEAL_FIX2_RESULT=FAILED\n'
  printf 'INNER_RC=%s\n' "$RC"
  exit "$RC"
fi

rm -f "$TEMP"
printf 'MACHINE_SEAL_FIX2_RESULT=SUCCESS\n'
