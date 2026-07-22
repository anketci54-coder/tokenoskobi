#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]

SOURCE="tools/era63b_build.sh"
TEMP="$(mktemp /tmp/era63b_build_fixed.XXXXXX.sh)"
trap 'rm -f "$TEMP"' EXIT

python3 - "$SOURCE" "$TEMP" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
text = source.read_text(encoding="utf-8")
old = '''printf '%s\\n' "${ALL_FILES[@]}" |
while IFS= read -r file; do
  [[ -e "$file" ]] && printf '%s\\n' "$file"
done >/tmp/era63b_existing_files.txt
'''
new = '''printf '%s\\n' "${ALL_FILES[@]}" |
while IFS= read -r file; do
  if [[ -e "$file" ]]; then
    printf '%s\\n' "$file"
  fi
done >/tmp/era63b_existing_files.txt
'''
if text.count(old) != 1:
    raise SystemExit("ERA63B_PATCH_TARGET_NOT_FOUND")
target.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

chmod 700 "$TEMP"
bash "$TEMP"
