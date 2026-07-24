#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

TARGET="tools/era64i_bounded_historical_wallet_event_backfill.sh"
BACKUP="/root/era64i_runner_before_block_receipt_fix_v6_$(date -u +%Y%m%dT%H%M%SZ).sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
cp "$TARGET" "$BACKUP"

python3 <<'PY'
from pathlib import Path
import re

path=Path('tools/era64i_bounded_historical_wallet_event_backfill.sh')
text=path.read_text(encoding='utf-8')


def sub_once(pattern,replacement,label,flags=0):
    global text
    text,new_count=re.subn(pattern,replacement,text,count=1,flags=flags)
    if new_count!=1:
        raise SystemExit(f'ERA64I_V6_PATTERN_INVALID:{label}:{new_count}')

sub_once(r'"eth_getLogs",\n\s*"eth_getBlockByNumber"','"eth_getTransactionReceipt",\n    "eth_getBlockByNumber"','rpc_allowlist_json')
sub_once(
    r"if set\(methods or \[\]\)!=\{'eth_chainId','eth_blockNumber','eth_getLogs','eth_getBlockByNumber'\}:",
    "if set(methods or [])!={'eth_chainId','eth_blockNumber','eth_getTransactionReceipt','eth_getBlockByNumber'}:",
    'rpc_allowlist_validation',
)
sub_once(r'("historical_block_span"\s*:\s*)\d+',r'\g<1>2048','historical_span')
sub_once(r'("log_chunk_size"\s*:\s*)\d+',r'\g<1>64','chunk_size')
sub_once(r'("maximum_logs_per_sampled_block"\s*:\s*)\d+',r'\g<1>12','max_logs')
sub_once(
    r'("log_query_sampling_mode"\s*:\s*)"[^"]+"',
    r'\g<1>"FULL_BLOCK_TRANSACTION_RECEIPT_SAMPLING_PROVIDER_SAFE"',
    'sampling_mode',
)

if '"maximum_receipts_per_sampled_block"' not in text:
    sub_once(
        r'(^\s*"maximum_wallet_scope"\s*:\s*\d+,\n)',
        r'\g<1>    "maximum_receipts_per_sampled_block": 24,\n',
        'insert_receipt_limit',
        flags=re.M,
    )

if "bounded_int(limits.get('maximum_receipts_per_sampled_block')" not in text:
    sub_once(
        r"(^\s*bounded_int\(limits\.get\('maximum_wallet_scope'\),'maximum_wallet_scope',1,32\)\n)",
        r"\g<1>    bounded_int(limits.get('maximum_receipts_per_sampled_block'),'maximum_receipts_per_sampled_block',1,24)\n",
        'insert_receipt_validation',
        flags=re.M,
    )

sub_once(
    r'self\.endpoint_index=\(self\.endpoint_index\+offset\)%count',
    'self.endpoint_index=(self.endpoint_index+offset+1)%count',
    'provider_rotation',
)

text,count=re.subn(
    r"\n\s*if method=='eth_getLogs' and \('limit exceeded' in str\(exc\)\.lower\(\) or '-32005' in str\(exc\)\):\n\s*raise Era64IError\('RPC_LOG_LIMIT_EXCEEDED'\) from exc",
    '',
    text,
    count=1,
)
if count not in (0,1):
    raise SystemExit(f'ERA64I_V6_LOG_LIMIT_REMOVAL_INVALID:{count}')

start_marker='def wallet_topic(address: str) -> str:\n'
end_marker='def log_sort_key(item: dict[str,Any]) -> tuple[Any,...]:\n'
start=text.find(start_marker)
end=text.find(end_marker,start)
if start<0 or end<0 or end<=start:
    raise SystemExit(f'ERA64I_V6_FUNCTION_BOUNDARY_INVALID:{start}:{end}')

new_block=r"""def transaction_hash(item: Any) -> str | None:
    if isinstance(item,dict):
        return normalize_hash(item.get('hash'))
    return normalize_hash(item)

def transaction_wallet_priority(item: Any,wallets: set[str]) -> tuple[int,str]:
    tx_hash=transaction_hash(item) or '0x'+'f'*64
    if not isinstance(item,dict):
        return (1,tx_hash)
    src=normalize_address(item.get('from'))
    dst=normalize_address(item.get('to'))
    return (0 if src in wallets or dst in wallets else 1,tx_hash)

def fetch_logs_for_chunk(
    client: RpcClient,
    tokens: list[str],
    wallets: list[str],
    start: int,
    end: int,
    maximum_receipts: int,
) -> tuple[list[dict[str,Any]],str|None,str]:
    if not wallets:
        raise Era64IError('WALLET_SCOPE_EMPTY')
    sampled_block=start+(end-start)//2
    block=client.call('eth_getBlockByNumber',[hex(sampled_block),True])
    if not isinstance(block,dict):
        raise Era64IError('SAMPLED_BLOCK_NOT_OBJECT')
    if as_hex_int(block.get('number'),'sampled_block.number')!=sampled_block:
        raise Era64IError('SAMPLED_BLOCK_NUMBER_MISMATCH')
    transactions=block.get('transactions')
    if not isinstance(transactions,list):
        raise Era64IError('SAMPLED_BLOCK_TRANSACTIONS_NOT_LIST')
    wallet_set={item for item in wallets if normalize_address(item) is not None}
    ordered=sorted(transactions,key=lambda item:transaction_wallet_priority(item,wallet_set))
    prioritized=[item for item in ordered if transaction_wallet_priority(item,wallet_set)[0]==0]
    remainder=[item for item in ordered if transaction_wallet_priority(item,wallet_set)[0]!=0]
    chosen=prioritized[:maximum_receipts]
    remaining=maximum_receipts-len(chosen)
    if remaining>0:
        chosen.extend(evenly_select(remainder,remaining))
    token_set=set(tokens)
    merged=[]
    for transaction in chosen:
        tx_hash=transaction_hash(transaction)
        if tx_hash is None:
            continue
        receipt=client.call('eth_getTransactionReceipt',[tx_hash])
        if not isinstance(receipt,dict):
            raise Era64IError('TRANSACTION_RECEIPT_NOT_OBJECT')
        logs=receipt.get('logs')
        if not isinstance(logs,list):
            raise Era64IError('TRANSACTION_RECEIPT_LOGS_NOT_LIST')
        for item in logs:
            if not isinstance(item,dict):
                continue
            token=normalize_address(item.get('address'))
            topics=item.get('topics')
            if token not in token_set:
                continue
            if not isinstance(topics,list) or len(topics)<3 or str(topics[0]).lower()!=TRANSFER_TOPIC:
                continue
            merged.append(item)
    unique={}
    for item in merged:
        key=(
          str(item.get('blockHash') or '').lower(),
          str(item.get('transactionHash') or '').lower(),
          str(item.get('logIndex') or '').lower(),
          str(item.get('address') or '').lower(),
        )
        unique.setdefault(key,item)
    return sorted(unique.values(),key=log_sort_key),client.last_endpoint_host,'FULL_BLOCK_TRANSACTION_RECEIPT_SAMPLING'

"""
text=text[:start]+new_block+text[end:]

if "max_receipts_per_block=int(config['limits']['maximum_receipts_per_sampled_block'])" not in text:
    sub_once(
        r"(^\s*max_blocks_per_chunk=int\(config\['limits'\]\['maximum_sampled_blocks_per_chunk'\]\)\n)",
        r"\g<1>    max_receipts_per_block=int(config['limits']['maximum_receipts_per_sampled_block'])\n",
        'insert_runtime_receipt_limit',
        flags=re.M,
    )

sub_once(
    r'fetch_logs_for_chunk\(client,tokens,wallet_scope,chunk_start,chunk_end\)',
    'fetch_logs_for_chunk(client,tokens,wallet_scope,chunk_start,chunk_end,max_receipts_per_block)',
    'fetch_call',
)

text=text.replace(
    'It samples ERC-20 Transfer logs for canonical BSC base and quote assets across a 2,048-block historical range',
    'It deterministically samples full blocks and transaction receipts for canonical BSC base and quote assets across a 2,048-block historical range',
    1,
)

path.write_text(text,encoding='utf-8')
print('ERA64I_BLOCK_RECEIPT_SAMPLING_FIX_V6=APPLIED')
PY

python3 <<'PY_VERIFY'
from pathlib import Path
text=Path('tools/era64i_bounded_historical_wallet_event_backfill.sh').read_text(encoding='utf-8')
assert 'FULL_BLOCK_TRANSACTION_RECEIPT_SAMPLING_PROVIDER_SAFE' in text
assert 'eth_getTransactionReceipt' in text
assert 'maximum_receipts_per_sampled_block' in text
assert 'RPC_LOG_LIMIT_EXCEEDED_AT_MINIMUM_QUERY' not in text
assert 'fetch_logs_for_chunk(client,tokens,wallet_scope,chunk_start,chunk_end,max_receipts_per_block)' in text
start=text.index("cat > \"$TOOL\" <<'PY_TOOL'\n")+len("cat > \"$TOOL\" <<'PY_TOOL'\n")
end=text.index('\nPY_TOOL\n',start)
Path('/tmp/era64i_block_receipt_compile_check_v6.py').write_text(text[start:end],encoding='utf-8')
print('ERA64I_BLOCK_RECEIPT_PATCH_VERIFY_V6=VERIFIED')
PY_VERIFY
python3 -m py_compile /tmp/era64i_block_receipt_compile_check_v6.py
rm -f /tmp/era64i_block_receipt_compile_check_v6.py

git add "$TARGET"
git commit -m "ERA64: repair historical backfill with receipt sampling"
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
rm -f "$BACKUP"

echo "ERA64I_BLOCK_RECEIPT_SAMPLING_FIX_V6=VERIFIED"
bash tools/era64i_bounded_historical_wallet_event_backfill.sh
