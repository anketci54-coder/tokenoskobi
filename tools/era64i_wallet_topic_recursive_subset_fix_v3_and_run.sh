#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

TARGET="tools/era64i_bounded_historical_wallet_event_backfill.sh"
BACKUP="/root/era64i_runner_before_recursive_topic_subset_fix_$(date -u +%Y%m%dT%H%M%SZ).sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
cp "$TARGET" "$BACKUP"

python3 <<'PY'
from pathlib import Path

path=Path('tools/era64i_bounded_historical_wallet_event_backfill.sh')
text=path.read_text(encoding='utf-8')
old="""    def query(direction: str,query_tokens: list[str],query_wallets: list[str],query_start: int,query_end: int) -> list[dict[str,Any]]:
        topics=[TRANSFER_TOPIC,wallet_topic_values] if direction=='OUT' else [TRANSFER_TOPIC,None,wallet_topic_values]
"""
new="""    def query(direction: str,query_tokens: list[str],query_wallets: list[str],query_start: int,query_end: int) -> list[dict[str,Any]]:
        if not query_tokens or not query_wallets:
            return []
        wallet_topic_values=[wallet_topic(item) for item in query_wallets]
        topics=[TRANSFER_TOPIC,wallet_topic_values] if direction=='OUT' else [TRANSFER_TOPIC,None,wallet_topic_values]
"""
if text.count(old)!=1:
    raise SystemExit(f'ERA64I_RECURSIVE_TOPIC_QUERY_PATTERN_COUNT_INVALID:{text.count(old)}')
text=text.replace(old,new,1)
old_loop="""    for direction in ('OUT','IN'):
        wallet_topic_values=[wallet_topic(item) for item in wallets]
        merged.extend(query(direction,tokens,wallets,start,end))
"""
new_loop="""    for direction in ('OUT','IN'):
        merged.extend(query(direction,tokens,wallets,start,end))
"""
if text.count(old_loop)!=1:
    raise SystemExit(f'ERA64I_RECURSIVE_TOPIC_LOOP_PATTERN_COUNT_INVALID:{text.count(old_loop)}')
text=text.replace(old_loop,new_loop,1)
marker="    \"log_query_sampling_mode\": \"WALLET_TOPIC_FILTER_WITH_ADAPTIVE_RANGE_SPLIT\",\n"
replacement="    \"log_query_sampling_mode\": \"WALLET_TOPIC_FILTER_WITH_RECURSIVE_SUBSET_AND_ADAPTIVE_RANGE_SPLIT\",\n"
if text.count(marker)!=1:
    raise SystemExit(f'ERA64I_SAMPLING_MODE_PATTERN_COUNT_INVALID:{text.count(marker)}')
text=text.replace(marker,replacement,1)
path.write_text(text,encoding='utf-8')
print('ERA64I_RECURSIVE_WALLET_TOPIC_SUBSET_FIX=APPLIED')
PY

grep -q 'wallet_topic_values=\[wallet_topic(item) for item in query_wallets\]' "$TARGET"
grep -q 'WALLET_TOPIC_FILTER_WITH_RECURSIVE_SUBSET_AND_ADAPTIVE_RANGE_SPLIT' "$TARGET"
if grep -q 'wallet_topic_values=\[wallet_topic(item) for item in wallets\]' "$TARGET"; then
  echo "STALE_FULL_WALLET_TOPIC_SCOPE=FOUND"
  cp "$BACKUP" "$TARGET"
  exit 1
fi

git add "$TARGET"
git commit -m "ERA64: bind recursive log queries to wallet subsets"
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
rm -f "$BACKUP"

echo "ERA64I_RECURSIVE_WALLET_TOPIC_SUBSET_FIX=VERIFIED"
bash tools/era64i_bounded_historical_wallet_event_backfill.sh
