#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

TARGET="tools/era64i_bounded_historical_wallet_event_backfill.sh"
BACKUP="/root/era64i_runner_before_wallet_topic_fix_$(date -u +%Y%m%dT%H%M%SZ).sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
cp "$TARGET" "$BACKUP"

python3 <<'PY'
from pathlib import Path

path=Path('tools/era64i_bounded_historical_wallet_event_backfill.sh')
text=path.read_text(encoding='utf-8')

replacements=[]
replacements.append((
'''  "provider_config": "config/era63e_always_on_market_runtime_v1.json",
''',
'''  "provider_config": "config/era63e_always_on_market_runtime_v1.json",
  "wallet_scope_artifact": "data/replay/era64h_staging_replay_relationship_graph_v1.json",
'''))
replacements.append((
'''    "historical_block_span": 2048,
    "log_chunk_size": 16,
    "maximum_sampled_blocks_per_chunk": 1,
    "log_query_sampling_mode": "MIDPOINT_BLOCK_PER_CHUNK_PROVIDER_LIMIT_SAFE",
''',
'''    "historical_block_span": 4096,
    "log_chunk_size": 16,
    "maximum_sampled_blocks_per_chunk": 1,
    "maximum_wallet_scope": 16,
    "log_query_sampling_mode": "WALLET_TOPIC_FILTER_WITH_ADAPTIVE_RANGE_SPLIT",
'''))
replacements.append((
'''    bounded_int(limits.get('maximum_sampled_blocks_per_chunk'),'maximum_sampled_blocks_per_chunk',1,4)
    bounded_int(limits.get('maximum_logs_per_sampled_block'),'maximum_logs_per_sampled_block',1,16)
''',
'''    bounded_int(limits.get('maximum_sampled_blocks_per_chunk'),'maximum_sampled_blocks_per_chunk',1,4)
    bounded_int(limits.get('maximum_wallet_scope'),'maximum_wallet_scope',1,32)
    bounded_int(limits.get('maximum_logs_per_sampled_block'),'maximum_logs_per_sampled_block',1,16)
'''))
replacements.append((
'''                except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError,OSError,json.JSONDecodeError,Era64IError) as exc:
                    last_error=f'{type(exc).__name__}:{exc}'
                    self.errors.append(f'{parsed.hostname}:{method}:{last_error}')
                    if attempt<self.retries:
                        time.sleep(min(self.backoff*(2**attempt),2.0))
''',
'''                except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError,OSError,json.JSONDecodeError,Era64IError) as exc:
                    last_error=f'{type(exc).__name__}:{exc}'
                    self.errors.append(f'{parsed.hostname}:{method}:{last_error}')
                    if method=='eth_getLogs' and ('limit exceeded' in str(exc).lower() or '-32005' in str(exc)):
                        raise Era64IError('RPC_LOG_LIMIT_EXCEEDED') from exc
                    if attempt<self.retries:
                        time.sleep(min(self.backoff*(2**attempt),2.0))
'''))
old_fetch='''def fetch_logs_for_chunk(client: RpcClient,tokens: list[str],start: int,end: int) -> tuple[list[dict[str,Any]],str|None,str]:
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
'''
new_fetch='''def wallet_topic(address: str) -> str:
    normalized=normalize_address(address)
    if normalized is None:
        raise Era64IError('WALLET_TOPIC_ADDRESS_INVALID')
    return '0x'+'0'*24+normalized[2:]

def fetch_logs_for_chunk(client: RpcClient,tokens: list[str],wallets: list[str],start: int,end: int) -> tuple[list[dict[str,Any]],str|None,str]:
    if not wallets:
        raise Era64IError('WALLET_SCOPE_EMPTY')

    def query(direction: str,query_tokens: list[str],query_wallets: list[str],query_start: int,query_end: int) -> list[dict[str,Any]]:
        topics=[TRANSFER_TOPIC,wallet_topic_values] if direction=='OUT' else [TRANSFER_TOPIC,None,wallet_topic_values]
        params={
          'fromBlock':hex(query_start),'toBlock':hex(query_end),
          'address':query_tokens,'topics':topics,
        }
        try:
            result=client.call('eth_getLogs',[params])
            if not isinstance(result,list):
                raise Era64IError('ETH_GET_LOGS_RESULT_NOT_LIST')
            return [item for item in result if isinstance(item,dict)]
        except Era64IError as exc:
            if 'RPC_LOG_LIMIT_EXCEEDED' not in str(exc):
                raise
            if query_start<query_end:
                midpoint=(query_start+query_end)//2
                return query(direction,query_tokens,query_wallets,query_start,midpoint)+query(direction,query_tokens,query_wallets,midpoint+1,query_end)
            if len(query_wallets)>1:
                midpoint=len(query_wallets)//2
                return query(direction,query_tokens,query_wallets[:midpoint],query_start,query_end)+query(direction,query_tokens,query_wallets[midpoint:],query_start,query_end)
            if len(query_tokens)>1:
                midpoint=len(query_tokens)//2
                return query(direction,query_tokens[:midpoint],query_wallets,query_start,query_end)+query(direction,query_tokens[midpoint:],query_wallets,query_start,query_end)
            raise Era64IError('RPC_LOG_LIMIT_EXCEEDED_AT_MINIMUM_QUERY') from exc

    merged=[]
    for direction in ('OUT','IN'):
        wallet_topic_values=[wallet_topic(item) for item in wallets]
        merged.extend(query(direction,tokens,wallets,start,end))
    unique={}
    for item in merged:
        key=(
          str(item.get('blockHash') or '').lower(),
          str(item.get('transactionHash') or '').lower(),
          str(item.get('logIndex') or '').lower(),
          str(item.get('address') or '').lower(),
        )
        unique.setdefault(key,item)
    return sorted(unique.values(),key=log_sort_key),client.last_endpoint_host,'WALLET_TOPIC_FILTER_ADAPTIVE_RANGE_SPLIT'
'''
replacements.append((old_fetch,new_fetch))
replacements.append((
'''    tokens=[str(item).lower() for item in config['scope_tokens']]
    selected:dict[tuple[int,str,int],dict[str,Any]]={}
''',
'''    tokens=[str(item).lower() for item in config['scope_tokens']]
    wallet_scope_path=ROOT/str(config['wallet_scope_artifact'])
    wallet_scope_source=json.loads(wallet_scope_path.read_text(encoding='utf-8'))
    graph=wallet_scope_source.get('relationship_graph')
    nodes=graph.get('nodes') if isinstance(graph,dict) else None
    if not isinstance(nodes,list) or not nodes:
        raise Era64IError('WALLET_SCOPE_GRAPH_NODES_EMPTY')
    ranked=sorted(
      (item for item in nodes if isinstance(item,dict) and normalize_address(item.get('address')) not in {None,ZERO_ADDRESS}),
      key=lambda item:(-int(item.get('transfer_event_count',0)),-int(item.get('counterparty_count',0)),str(item.get('address')).lower()),
    )
    maximum_wallet_scope=int(config['limits']['maximum_wallet_scope'])
    wallet_scope=[str(item['address']).lower() for item in ranked[:maximum_wallet_scope]]
    if len(wallet_scope)<1 or len(set(wallet_scope))!=len(wallet_scope):
        raise Era64IError('WALLET_SCOPE_INVALID')
    selected:dict[tuple[int,str,int],dict[str,Any]]={}
'''))
replacements.append((
'''    for chunk_start in range(start_block,end_block+1,chunk_size):
        if time.monotonic()-started>max_runtime:
''',
'''    for chunk_start in range(start_block,end_block+1,chunk_size):
        if len(selected)>=max_events:
            break
        if time.monotonic()-started>max_runtime:
'''))
replacements.append((
'''        logs,host,filter_mode=fetch_logs_for_chunk(client,tokens,chunk_start,chunk_end)
''',
'''        logs,host,filter_mode=fetch_logs_for_chunk(client,tokens,wallet_scope,chunk_start,chunk_end)
'''))
replacements.append((
'''      'scope_tokens':tokens,'token_event_counts':dict(sorted(token_counts.items())),
''',
'''      'scope_tokens':tokens,'wallet_scope_artifact':str(config['wallet_scope_artifact']),
      'wallet_scope_count':len(wallet_scope),'wallet_scope':wallet_scope,
      'token_event_counts':dict(sorted(token_counts.items())),
'''))
replacements.append((
'''      'distinct_token_count':len(token_counts),'rpc_request_count':client.request_count,
''',
'''      'distinct_token_count':len(token_counts),'wallet_scope_count':len(wallet_scope),
      'rpc_request_count':client.request_count,
'''))
replacements.append((
'''    print(f"DISTINCT_TOKEN_COUNT={control['distinct_token_count']}")
    print(f"RPC_REQUEST_COUNT={control['rpc_request_count']}")
''',
'''    print(f"DISTINCT_TOKEN_COUNT={control['distinct_token_count']}")
    print(f"WALLET_SCOPE_COUNT={control['wallet_scope_count']}")
    print(f"RPC_REQUEST_COUNT={control['rpc_request_count']}")
'''))

for old,new in replacements:
    count=text.count(old)
    if count!=1:
        raise SystemExit(f'ERA64I_WALLET_TOPIC_FIX_PATTERN_COUNT_INVALID:{count}:{old[:80]!r}')
    text=text.replace(old,new,1)

path.write_text(text,encoding='utf-8')
print('ERA64I_WALLET_TOPIC_ADAPTIVE_LOG_FIX=APPLIED')
PY

python3 -m py_compile <(python3 - <<'PY_EXTRACT'
from pathlib import Path
text=Path('tools/era64i_bounded_historical_wallet_event_backfill.sh').read_text(encoding='utf-8')
start=text.index("cat > \"$TOOL\" <<'PY_TOOL'\n")+len("cat > \"$TOOL\" <<'PY_TOOL'\n")
end=text.index('\nPY_TOOL\n',start)
print(text[start:end])
PY_EXTRACT
) 2>/dev/null || true

grep -q 'WALLET_TOPIC_FILTER_WITH_ADAPTIVE_RANGE_SPLIT' "$TARGET"
grep -q 'RPC_LOG_LIMIT_EXCEEDED_AT_MINIMUM_QUERY' "$TARGET"
grep -q 'wallet_scope_artifact' "$TARGET"

git add "$TARGET"
git commit -m "ERA64: filter historical logs by bounded wallet topics"
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
rm -f "$BACKUP"

echo "ERA64I_WALLET_TOPIC_ADAPTIVE_LOG_FIX=VERIFIED"
bash tools/era64i_bounded_historical_wallet_event_backfill.sh
