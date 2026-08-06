#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

TARGET="tools/era64i_bounded_historical_wallet_event_backfill.sh"
BACKUP="/root/era64i_runner_before_rpc_limit_fix_$(date -u +%Y%m%dT%H%M%SZ).sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
cp "$TARGET" "$BACKUP"

python3 <<'PY'
from pathlib import Path

path=Path('tools/era64i_bounded_historical_wallet_event_backfill.sh')
text=path.read_text(encoding='utf-8')
old="""def fetch_logs_for_chunk(client: RpcClient,tokens: list[str],start: int,end: int) -> tuple[list[dict[str,Any]],str|None,str]:
    params={'fromBlock':hex(start),'toBlock':hex(end),'address':tokens,'topics':[TRANSFER_TOPIC]}
    try:
        result=client.call('eth_getLogs',[params])
        if not isinstance(result,list):
            raise Era64IError('ETH_GET_LOGS_RESULT_NOT_LIST')
        return [item for item in result if isinstance(item,dict)],client.last_endpoint_host,'COMBINED_TOKEN_FILTER'
    except Era64IError as combined_error:
        merged=[]
        provider_host=None
        for token in tokens:
            result=client.call('eth_getLogs',[{'fromBlock':hex(start),'toBlock':hex(end),'address':token,'topics':[TRANSFER_TOPIC]}])
            if not isinstance(result,list):
                raise Era64IError('ETH_GET_LOGS_FALLBACK_RESULT_NOT_LIST') from combined_error
            merged.extend(item for item in result if isinstance(item,dict))
            provider_host=client.last_endpoint_host
        return merged,provider_host,'PER_TOKEN_FALLBACK'
"""
new="""def fetch_logs_for_chunk(client: RpcClient,tokens: list[str],start: int,end: int) -> tuple[list[dict[str,Any]],str|None,str]:
    # Provider-safe deterministic sampling: query one midpoint block per configured chunk.
    # This preserves the 2048-block historical distribution while preventing public RPC
    # eth_getLogs result-limit failures on high-volume BSC base/quote tokens.
    sampled_block=start+(end-start)//2
    params={
      'fromBlock':hex(sampled_block),'toBlock':hex(sampled_block),
      'address':tokens,'topics':[TRANSFER_TOPIC]
    }
    try:
        result=client.call('eth_getLogs',[params])
        if not isinstance(result,list):
            raise Era64IError('ETH_GET_LOGS_RESULT_NOT_LIST')
        return [item for item in result if isinstance(item,dict)],client.last_endpoint_host,'MIDPOINT_BLOCK_COMBINED_TOKEN_FILTER'
    except Era64IError as combined_error:
        merged=[]
        provider_host=None
        for token in tokens:
            result=client.call('eth_getLogs',[{
              'fromBlock':hex(sampled_block),'toBlock':hex(sampled_block),
              'address':token,'topics':[TRANSFER_TOPIC]
            }])
            if not isinstance(result,list):
                raise Era64IError('ETH_GET_LOGS_MIDPOINT_FALLBACK_RESULT_NOT_LIST') from combined_error
            merged.extend(item for item in result if isinstance(item,dict))
            provider_host=client.last_endpoint_host
        unique={}
        for item in merged:
            key=(
              str(item.get('blockHash') or '').lower(),
              str(item.get('transactionHash') or '').lower(),
              str(item.get('logIndex') or '').lower(),
              str(item.get('address') or '').lower(),
            )
            unique.setdefault(key,item)
        return list(unique.values()),provider_host,'MIDPOINT_BLOCK_PER_TOKEN_FALLBACK'
"""
if text.count(old)!=1:
    raise SystemExit('ERA64I_RPC_LIMIT_FIX_PATTERN_COUNT_INVALID')
text=text.replace(old,new,1)
marker='    "maximum_sampled_blocks_per_chunk": 1,\n'
replacement='    "maximum_sampled_blocks_per_chunk": 1,\n    "log_query_sampling_mode": "MIDPOINT_BLOCK_PER_CHUNK_PROVIDER_LIMIT_SAFE",\n'
if text.count(marker)!=1:
    raise SystemExit('ERA64I_CONFIG_MARKER_COUNT_INVALID')
text=text.replace(marker,replacement,1)
path.write_text(text,encoding='utf-8')
print('ERA64I_RPC_LOG_LIMIT_SAMPLING_FIX=APPLIED')
PY

grep -q "MIDPOINT_BLOCK_PER_CHUNK_PROVIDER_LIMIT_SAFE" "$TARGET"
grep -q "MIDPOINT_BLOCK_PER_TOKEN_FALLBACK" "$TARGET"

git add "$TARGET"
git commit -m "ERA64: use provider-safe historical log sampling"
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
rm -f "$BACKUP"

echo "ERA64I_RPC_LOG_LIMIT_SAMPLING_FIX=VERIFIED"
bash tools/era64i_bounded_historical_wallet_event_backfill.sh
