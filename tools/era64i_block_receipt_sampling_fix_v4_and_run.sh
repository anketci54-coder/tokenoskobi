#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

TARGET="tools/era64i_bounded_historical_wallet_event_backfill.sh"
BACKUP="/root/era64i_runner_before_block_receipt_fix_$(date -u +%Y%m%dT%H%M%SZ).sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
cp "$TARGET" "$BACKUP"

python3 <<'PY'
from pathlib import Path

path=Path('tools/era64i_bounded_historical_wallet_event_backfill.sh')
text=path.read_text(encoding='utf-8')

simple_replacements=[
('''    "eth_getLogs",\n    "eth_getBlockByNumber"\n''','''    "eth_getTransactionReceipt",\n    "eth_getBlockByNumber"\n'''),
("""    if set(methods or [])!={'eth_chainId','eth_blockNumber','eth_getLogs','eth_getBlockByNumber'}:\n""","""    if set(methods or [])!={'eth_chainId','eth_blockNumber','eth_getTransactionReceipt','eth_getBlockByNumber'}:\n"""),
('''    "historical_block_span": 4096,\n    "log_chunk_size": 16,\n    "maximum_sampled_blocks_per_chunk": 1,\n    "maximum_wallet_scope": 16,\n    "log_query_sampling_mode": "WALLET_TOPIC_FILTER_WITH_ADAPTIVE_RANGE_SPLIT",\n    "maximum_logs_per_sampled_block": 6,\n''','''    "historical_block_span": 2048,\n    "log_chunk_size": 64,\n    "maximum_sampled_blocks_per_chunk": 1,\n    "maximum_wallet_scope": 16,\n    "maximum_receipts_per_sampled_block": 16,\n    "log_query_sampling_mode": "FULL_BLOCK_TRANSACTION_RECEIPT_SAMPLING_PROVIDER_SAFE",\n    "maximum_logs_per_sampled_block": 8,\n'''),
("""    bounded_int(limits.get('maximum_wallet_scope'),'maximum_wallet_scope',1,32)\n    bounded_int(limits.get('maximum_logs_per_sampled_block'),'maximum_logs_per_sampled_block',1,16)\n""","""    bounded_int(limits.get('maximum_wallet_scope'),'maximum_wallet_scope',1,32)\n    bounded_int(limits.get('maximum_receipts_per_sampled_block'),'maximum_receipts_per_sampled_block',1,24)\n    bounded_int(limits.get('maximum_logs_per_sampled_block'),'maximum_logs_per_sampled_block',1,16)\n"""),
("""                    self.endpoint_index=(self.endpoint_index+offset)%count\n""","""                    self.endpoint_index=(self.endpoint_index+offset+1)%count\n"""),
("""                    if method=='eth_getLogs' and ('limit exceeded' in str(exc).lower() or '-32005' in str(exc)):\n                        raise Era64IError('RPC_LOG_LIMIT_EXCEEDED') from exc\n""","""""),
("""    max_blocks_per_chunk=int(config['limits']['maximum_sampled_blocks_per_chunk'])\n    max_logs_per_block=int(config['limits']['maximum_logs_per_sampled_block'])\n""","""    max_blocks_per_chunk=int(config['limits']['maximum_sampled_blocks_per_chunk'])\n    max_receipts_per_block=int(config['limits']['maximum_receipts_per_sampled_block'])\n    max_logs_per_block=int(config['limits']['maximum_logs_per_sampled_block'])\n"""),
("""        logs,host,filter_mode=fetch_logs_for_chunk(client,tokens,wallet_scope,chunk_start,chunk_end)\n""","""        logs,host,filter_mode=fetch_logs_for_chunk(client,tokens,wallet_scope,chunk_start,chunk_end,max_receipts_per_block)\n"""),
("""ERA64I performs a bounded historical BSC scan using allowlisted read-only RPC methods. It samples ERC-20 Transfer logs for canonical BSC base and quote assets across a 2,048-block historical range and writes only to a dedicated ERA64I staging SQLite database.\n""","""ERA64I performs a bounded historical BSC scan using allowlisted read-only RPC methods. It deterministically samples full blocks and transaction receipts, extracts canonical BSC base and quote ERC-20 Transfer logs across a 2,048-block historical range, and writes only to a dedicated ERA64I staging SQLite database.\n"""),
]
for old,new in simple_replacements:
    count=text.count(old)
    if count!=1:
        raise SystemExit(f'ERA64I_BLOCK_RECEIPT_SIMPLE_PATTERN_COUNT_INVALID:{count}:{old[:90]!r}')
    text=text.replace(old,new,1)

start_marker='def wallet_topic(address: str) -> str:\n'
end_marker='def log_sort_key(item: dict[str,Any]) -> tuple[Any,...]:\n'
start=text.find(start_marker)
end=text.find(end_marker,start)
if start<0 or end<0 or end<=start:
    raise SystemExit(f'ERA64I_BLOCK_RECEIPT_FUNCTION_BOUNDARY_INVALID:{start}:{end}')
new_block='''def transaction_hash(item: Any) -> str | None:\n    if isinstance(item,dict):\n        return normalize_hash(item.get('hash'))\n    return normalize_hash(item)\n\ndef transaction_wallet_priority(item: Any,wallets: set[str]) -> tuple[int,str]:\n    tx_hash=transaction_hash(item) or '0x'+'f'*64\n    if not isinstance(item,dict):\n        return (1,tx_hash)\n    src=normalize_address(item.get('from'))\n    dst=normalize_address(item.get('to'))\n    return (0 if src in wallets or dst in wallets else 1,tx_hash)\n\ndef fetch_logs_for_chunk(\n    client: RpcClient,\n    tokens: list[str],\n    wallets: list[str],\n    start: int,\n    end: int,\n    maximum_receipts: int,\n) -> tuple[list[dict[str,Any]],str|None,str]:\n    if not wallets:\n        raise Era64IError('WALLET_SCOPE_EMPTY')\n    sampled_block=start+(end-start)//2\n    block=client.call('eth_getBlockByNumber',[hex(sampled_block),True])\n    if not isinstance(block,dict):\n        raise Era64IError('SAMPLED_BLOCK_NOT_OBJECT')\n    if as_hex_int(block.get('number'),'sampled_block.number')!=sampled_block:\n        raise Era64IError('SAMPLED_BLOCK_NUMBER_MISMATCH')\n    transactions=block.get('transactions')\n    if not isinstance(transactions,list):\n        raise Era64IError('SAMPLED_BLOCK_TRANSACTIONS_NOT_LIST')\n    wallet_set={item for item in wallets if normalize_address(item) is not None}\n    ordered=sorted(transactions,key=lambda item:transaction_wallet_priority(item,wallet_set))\n    prioritized=[item for item in ordered if transaction_wallet_priority(item,wallet_set)[0]==0]\n    remainder=[item for item in ordered if transaction_wallet_priority(item,wallet_set)[0]!=0]\n    chosen=prioritized[:maximum_receipts]\n    remaining=maximum_receipts-len(chosen)\n    if remaining>0:\n        chosen.extend(evenly_select(remainder,remaining))\n    token_set=set(tokens)\n    merged=[]\n    for transaction in chosen:\n        tx_hash=transaction_hash(transaction)\n        if tx_hash is None:\n            continue\n        receipt=client.call('eth_getTransactionReceipt',[tx_hash])\n        if not isinstance(receipt,dict):\n            raise Era64IError('TRANSACTION_RECEIPT_NOT_OBJECT')\n        logs=receipt.get('logs')\n        if not isinstance(logs,list):\n            raise Era64IError('TRANSACTION_RECEIPT_LOGS_NOT_LIST')\n        for item in logs:\n            if not isinstance(item,dict):\n                continue\n            token=normalize_address(item.get('address'))\n            topics=item.get('topics')\n            if token not in token_set:\n                continue\n            if not isinstance(topics,list) or len(topics)<3 or str(topics[0]).lower()!=TRANSFER_TOPIC:\n                continue\n            merged.append(item)\n    unique={}\n    for item in merged:\n        key=(\n          str(item.get('blockHash') or '').lower(),\n          str(item.get('transactionHash') or '').lower(),\n          str(item.get('logIndex') or '').lower(),\n          str(item.get('address') or '').lower(),\n        )\n        unique.setdefault(key,item)\n    return sorted(unique.values(),key=log_sort_key),client.last_endpoint_host,'FULL_BLOCK_TRANSACTION_RECEIPT_SAMPLING'\n\n'''
text=text[:start]+new_block+text[end:]

path.write_text(text,encoding='utf-8')
print('ERA64I_BLOCK_RECEIPT_SAMPLING_FIX_V4=APPLIED')
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
Path('/tmp/era64i_block_receipt_compile_check.py').write_text(text[start:end],encoding='utf-8')
print('ERA64I_BLOCK_RECEIPT_PATCH_VERIFY=VERIFIED')
PY_VERIFY
python3 -m py_compile /tmp/era64i_block_receipt_compile_check.py
rm -f /tmp/era64i_block_receipt_compile_check.py

git add "$TARGET"
git commit -m "ERA64: replace historical log queries with receipt sampling"
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
rm -f "$BACKUP"

echo "ERA64I_BLOCK_RECEIPT_SAMPLING_FIX_V4=VERIFIED"
bash tools/era64i_bounded_historical_wallet_event_backfill.sh
