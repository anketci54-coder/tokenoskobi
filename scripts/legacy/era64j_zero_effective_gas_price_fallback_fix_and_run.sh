#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

TARGET="tools/era64j_historical_transfer_receipt_cost_enrichment.sh"
BACKUP="/root/era64j_runner_before_zero_gas_price_fix_$(date -u +%Y%m%dT%H%M%SZ).sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
cp "$TARGET" "$BACKUP"

python3 <<'PY'
from pathlib import Path

path=Path('tools/era64j_historical_transfer_receipt_cost_enrichment.sh')
text=path.read_text(encoding='utf-8')
old="""    effective_value=receipt.get('effectiveGasPrice')
    raw_transaction=''
    gas_price_source='RECEIPT_EFFECTIVE_GAS_PRICE'
    if effective_value in (None,''):
        transaction=client.call('eth_getTransactionByHash',[tx_hash])
        if not isinstance(transaction,dict):
            raise Era64JError(f'TRANSACTION_NOT_OBJECT:{tx_hash}')
        if normalize_hash(transaction.get('hash'))!=tx_hash:
            raise Era64JError(f'TRANSACTION_HASH_MISMATCH:{tx_hash}')
        effective_value=transaction.get('gasPrice')
        raw_transaction=json.dumps(transaction,sort_keys=True,separators=(',',':'),ensure_ascii=True)
        gas_price_source='TRANSACTION_GAS_PRICE_FALLBACK'
    effective_gas_price=as_hex_int(effective_value,'effectiveGasPrice')
    if effective_gas_price<=0:
        raise Era64JError(f'EFFECTIVE_GAS_PRICE_INVALID:{tx_hash}')
"""
new="""    effective_value=receipt.get('effectiveGasPrice')
    raw_transaction=''
    gas_price_source='RECEIPT_EFFECTIVE_GAS_PRICE'
    receipt_effective_gas_price=0
    if effective_value not in (None,''):
        receipt_effective_gas_price=as_hex_int(effective_value,'receipt.effectiveGasPrice')
    if receipt_effective_gas_price>0:
        effective_gas_price=receipt_effective_gas_price
    else:
        transaction=client.call('eth_getTransactionByHash',[tx_hash])
        if not isinstance(transaction,dict):
            raise Era64JError(f'TRANSACTION_NOT_OBJECT:{tx_hash}')
        if normalize_hash(transaction.get('hash'))!=tx_hash:
            raise Era64JError(f'TRANSACTION_HASH_MISMATCH:{tx_hash}')
        transaction_gas_price=as_hex_int(transaction.get('gasPrice'),'transaction.gasPrice')
        if transaction_gas_price<=0:
            raise Era64JError(f'TRANSACTION_GAS_PRICE_INVALID:{tx_hash}')
        effective_gas_price=transaction_gas_price
        raw_transaction=json.dumps(transaction,sort_keys=True,separators=(',',':'),ensure_ascii=True)
        gas_price_source='TRANSACTION_GAS_PRICE_FALLBACK'
"""
count=text.count(old)
if count!=1:
    raise SystemExit(f'ERA64J_ZERO_EFFECTIVE_GAS_PRICE_PATTERN_COUNT_INVALID:{count}')
text=text.replace(old,new,1)
path.write_text(text,encoding='utf-8')
print('ERA64J_ZERO_EFFECTIVE_GAS_PRICE_FALLBACK_FIX=APPLIED')
PY

python3 <<'PY_VERIFY'
from pathlib import Path
text=Path('tools/era64j_historical_transfer_receipt_cost_enrichment.sh').read_text(encoding='utf-8')
assert "receipt_effective_gas_price=0" in text
assert "transaction_gas_price=as_hex_int(transaction.get('gasPrice'),'transaction.gasPrice')" in text
assert "TRANSACTION_GAS_PRICE_INVALID" in text
assert "EFFECTIVE_GAS_PRICE_INVALID" not in text
start=text.index("cat > \"$TOOL\" <<'PY_TOOL'\n")+len("cat > \"$TOOL\" <<'PY_TOOL'\n")
end=text.index('\nPY_TOOL\n',start)
Path('/tmp/era64j_zero_gas_price_compile_check.py').write_text(text[start:end],encoding='utf-8')
print('ERA64J_ZERO_EFFECTIVE_GAS_PRICE_PATCH_VERIFY=VERIFIED')
PY_VERIFY
python3 -m py_compile /tmp/era64j_zero_gas_price_compile_check.py
rm -f /tmp/era64j_zero_gas_price_compile_check.py

git add "$TARGET"
git commit -m "ERA64: fallback when receipt effective gas price is zero"
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
rm -f "$BACKUP"

echo "ERA64J_ZERO_EFFECTIVE_GAS_PRICE_FALLBACK_FIX=VERIFIED"
bash tools/era64j_historical_transfer_receipt_cost_enrichment.sh
