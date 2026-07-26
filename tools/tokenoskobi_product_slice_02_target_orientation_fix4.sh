#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE_HEAD=${PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD:-}
BRANCH=agent/product-slice-02-target-orientation-fix1
BASE_PATH=tools/tokenoskobi_product_slice_02_target_orientation_fix3.sh
TEMP=/root/tokenoskobi_product_slice_02_target_orientation_fix4_patched.sh

fail(){ printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
[[ "$SOURCE_HEAD" =~ ^[0-9a-f]{40}$ ]] || fail SOURCE_HEAD_MISSING_OR_INVALID
[[ "$(git rev-parse "origin/$BRANCH")" == "$SOURCE_HEAD" ]] || fail SOURCE_HEAD_NOT_CURRENT_BRANCH_HEAD
[[ "$(git merge-base d1d5078a7fb9bab7108755bf63806cb27f697007 "$SOURCE_HEAD")" == d1d5078a7fb9bab7108755bf63806cb27f697007 ]] || fail SOURCE_HEAD_BASE_INVALID

git show "$SOURCE_HEAD:$BASE_PATH" > "$TEMP"

TEMP="$TEMP" python3 - <<'PY'
from pathlib import Path
import os

p=Path(os.environ['TEMP'])
s=p.read_text(encoding='utf-8')

old_start='''    set +e
    RESULT="$PRODUCTION_RESULT" WBNB="$WBNB" python3 - <<'PYPROD' > "$PRODUCTION_VALIDATION" 2>&1
'''
new_start='''    trap - ERR
    set +e
    RESULT="$PRODUCTION_RESULT" WBNB="$WBNB" python3 - <<'PYPROD' > "$PRODUCTION_VALIDATION" 2>&1
'''
old_end='''    VALIDATE_RC=$?
    set -e
    cat "$PRODUCTION_VALIDATION"
'''
new_end='''    VALIDATE_RC=$?
    set -e
    trap rollback ERR INT TERM
    cat "$PRODUCTION_VALIDATION"
'''

if s.count(old_start)!=1:
    raise SystemExit('BLOCKED=FIX4_PATCH_ANCHOR_VALIDATION_START')
if s.count(old_end)!=1:
    raise SystemExit('BLOCKED=FIX4_PATCH_ANCHOR_VALIDATION_END')

s=s.replace(old_start,new_start,1)
s=s.replace(old_end,new_end,1)
p.write_text(s,encoding='utf-8')
PY

chmod 0700 "$TEMP"
bash -n "$TEMP"

set +e
PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD="$SOURCE_HEAD" \
bash "$TEMP"
RC=$?
set -e
rm -f "$TEMP"

if [[ "$RC" -ne 0 ]]; then
  printf 'TARGET_ORIENTATION_FIX4_RESULT=FAILED\n'
  printf 'INNER_RC=%s\n' "$RC"
  exit "$RC"
fi

printf 'TARGET_ORIENTATION_FIX4_RESULT=SUCCESS\n'
