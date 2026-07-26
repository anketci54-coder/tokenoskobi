#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE_HEAD=${PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD:-}
BRANCH=agent/product-slice-02-target-orientation-fix1
BASE_PATH=tools/tokenoskobi_product_slice_02_target_orientation_fix2.sh
TEMP=/root/tokenoskobi_product_slice_02_target_orientation_fix5_patched.sh
COOLDOWN_SEC=75

fail(){ printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
[[ "$SOURCE_HEAD" =~ ^[0-9a-f]{40}$ ]] || fail SOURCE_HEAD_MISSING_OR_INVALID
[[ "$(git rev-parse "origin/$BRANCH")" == "$SOURCE_HEAD" ]] || fail SOURCE_HEAD_NOT_CURRENT_BRANCH_HEAD
[[ "$(git merge-base d1d5078a7fb9bab7108755bf63806cb27f697007 "$SOURCE_HEAD")" == d1d5078a7fb9bab7108755bf63806cb27f697007 ]] || fail SOURCE_HEAD_BASE_INVALID

git show "$SOURCE_HEAD:$BASE_PATH" > "$TEMP"

TEMP="$TEMP" COOLDOWN_SEC="$COOLDOWN_SEC" python3 - <<'PY'
from pathlib import Path
import os

p=Path(os.environ['TEMP'])
s=p.read_text(encoding='utf-8')
cooldown=os.environ['COOLDOWN_SEC']
anchor="p.write_text(s,encoding='utf-8')"
if s.count(anchor)!=1:
    raise SystemExit('BLOCKED=FIX5_PATCH_ANCHOR_WRITE')

injection="""
rep(
 'cleanup_shadow\\n\\nOLD_PID=$(systemctl show \"$SERVICE\" -p MainPID --value)',
 'cleanup_shadow\\n\\nprintf \'GECKOTERMINAL_PRE_PRODUCTION_COOLDOWN_SEC=%s\\\\n\' ' + cooldown + '\\nsleep ' + cooldown + '\\n\\nOLD_PID=$(systemctl show \"$SERVICE\" -p MainPID --value)',
 'PRE_PRODUCTION_COOLDOWN',
)
rep(
 "\\nEXPECTED_STATUS=$' M tests/test_product_slice_02.py\\\\n M tools/tokenoskobi_product_slice_02_server.py'",
 "\\nprintf 'GECKOTERMINAL_PRE_PHONE_RETEST_COOLDOWN_SEC=%s\\\\n' " + cooldown + "\\nsleep " + cooldown + "\\n\\nEXPECTED_STATUS=$' M tests/test_product_slice_02.py\\\\n M tools/tokenoskobi_product_slice_02_server.py'",
 'PRE_PHONE_RETEST_COOLDOWN',
)
"""
s=s.replace(anchor,injection+anchor,1)
p.write_text(s,encoding='utf-8')
PY

chmod 0700 "$TEMP"
bash -n "$TEMP"

printf 'GECKOTERMINAL_PRE_SHADOW_COOLDOWN_SEC=%s\n' "$COOLDOWN_SEC"
sleep "$COOLDOWN_SEC"

set +e
PRODUCT_SLICE_02_ORIENTATION_SOURCE_HEAD="$SOURCE_HEAD" \
PRODUCT_SLICE_02_ORIENTATION_CONFIRM=YES \
bash "$TEMP"
RC=$?
set -e
rm -f "$TEMP"

if [[ "$RC" -ne 0 ]]; then
  printf 'TARGET_ORIENTATION_FIX5_RESULT=FAILED\n'
  printf 'INNER_RC=%s\n' "$RC"
  exit "$RC"
fi

printf 'TARGET_ORIENTATION_FIX5_RESULT=SUCCESS\n'
printf 'GECKOTERMINAL_COOLDOWN_POLICY=75_SECONDS_BETWEEN_BURSTS\n'
