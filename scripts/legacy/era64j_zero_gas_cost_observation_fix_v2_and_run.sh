#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

TARGET="tools/era64j_historical_transfer_receipt_cost_enrichment.sh"
BACKUP="/root/era64j_runner_before_zero_cost_observation_fix_v2_$(date -u +%Y%m%dT%H%M%SZ).sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
cp "$TARGET" "$BACKUP"

python3 <<'PY'
from pathlib import Path

path=Path('tools/era64j_historical_transfer_receipt_cost_enrichment.sh')
text=path.read_text(encoding='utf-8')

old_gas="""        transaction_gas_price=as_hex_int(transaction.get('gasPrice'),'transaction.gasPrice')
        if transaction_gas_price<=0:
            raise Era64JError(f'TRANSACTION_GAS_PRICE_INVALID:{tx_hash}')
        effective_gas_price=transaction_gas_price
        raw_transaction=json.dumps(transaction,sort_keys=True,separators=(',',':'),ensure_ascii=True)
        gas_price_source='TRANSACTION_GAS_PRICE_FALLBACK'
    gas_cost=gas_used*effective_gas_price
    if gas_cost<=0:
        raise Era64JError(f'GAS_COST_INVALID:{tx_hash}')
"""
new_gas="""        transaction_gas_price=as_hex_int(transaction.get('gasPrice'),'transaction.gasPrice')
        effective_gas_price=transaction_gas_price
        raw_transaction=json.dumps(transaction,sort_keys=True,separators=(',',':'),ensure_ascii=True)
        gas_price_source='TRANSACTION_GAS_PRICE_FALLBACK' if transaction_gas_price>0 else 'VERIFIED_ZERO_GAS_PRICE_OBSERVATION'
    gas_cost=gas_used*effective_gas_price
    if gas_cost<0:
        raise Era64JError(f'GAS_COST_NEGATIVE:{tx_hash}')
"""
if text.count(old_gas)!=1:
    raise SystemExit(f'ERA64J_ZERO_COST_GAS_BLOCK_COUNT_INVALID:{text.count(old_gas)}')
text=text.replace(old_gas,new_gas,1)

old_test="""                self.assertEqual(int(gas_cost),int(gas_used)*int(gas_price))
                self.assertGreater(int(gas_cost),0)
"""
new_test="""                self.assertEqual(int(gas_cost),int(gas_used)*int(gas_price))
                self.assertGreaterEqual(int(gas_cost),0)
"""
if text.count(old_test)!=1:
    raise SystemExit(f'ERA64J_ZERO_COST_TEST_BLOCK_COUNT_INVALID:{text.count(old_test)}')
text=text.replace(old_test,new_test,1)

old_counter="""    fallback_count=sum(1 for item in enrichments if item['gas_price_source']=='TRANSACTION_GAS_PRICE_FALLBACK')
    total_gas_cost=sum(int(item['gas_cost_wei']) for item in enrichments)
"""
new_counter="""    fallback_count=sum(1 for item in enrichments if item['gas_price_source']=='TRANSACTION_GAS_PRICE_FALLBACK')
    zero_gas_price_count=sum(1 for item in enrichments if item['gas_price_source']=='VERIFIED_ZERO_GAS_PRICE_OBSERVATION')
    total_gas_cost=sum(int(item['gas_cost_wei']) for item in enrichments)
"""
if text.count(old_counter)!=1:
    raise SystemExit(f'ERA64J_ZERO_COST_COUNTER_BLOCK_COUNT_INVALID:{text.count(old_counter)}')
text=text.replace(old_counter,new_counter,1)

old_field="'gas_price_fallback_count':fallback_count,'total_gas_cost_wei':str(total_gas_cost),"
new_field="'gas_price_fallback_count':fallback_count,'zero_gas_price_observation_count':zero_gas_price_count,'total_gas_cost_wei':str(total_gas_cost),"
field_count=text.count(old_field)
if field_count!=2:
    raise SystemExit(f'ERA64J_ZERO_COST_FIELD_COUNT_INVALID:{field_count}')
text=text.replace(old_field,new_field)

old_main="""    print(f"FAILED_RECEIPT_COUNT={control['failed_receipt_count']}")
    print(f"RPC_REQUEST_COUNT={control['rpc_request_count']}")
"""
new_main="""    print(f"FAILED_RECEIPT_COUNT={control['failed_receipt_count']}")
    print(f"ZERO_GAS_PRICE_OBSERVATION_COUNT={control['zero_gas_price_observation_count']}")
    print(f"RPC_REQUEST_COUNT={control['rpc_request_count']}")
"""
if text.count(old_main)!=1:
    raise SystemExit(f'ERA64J_ZERO_COST_MAIN_PRINT_COUNT_INVALID:{text.count(old_main)}')
text=text.replace(old_main,new_main,1)

old_final="""print(f"FAILED_RECEIPT_COUNT={c['failed_receipt_count']}")
print(f"RPC_REQUEST_COUNT={c['rpc_request_count']}")
"""
new_final="""print(f"FAILED_RECEIPT_COUNT={c['failed_receipt_count']}")
print(f"ZERO_GAS_PRICE_OBSERVATION_COUNT={c['zero_gas_price_observation_count']}")
print(f"RPC_REQUEST_COUNT={c['rpc_request_count']}")
"""
if text.count(old_final)!=1:
    raise SystemExit(f'ERA64J_ZERO_COST_FINAL_PRINT_COUNT_INVALID:{text.count(old_final)}')
text=text.replace(old_final,new_final,1)

path.write_text(text,encoding='utf-8')
print('ERA64J_ZERO_GAS_COST_OBSERVATION_FIX_V2=APPLIED')
PY

python3 <<'PY_VERIFY'
from pathlib import Path
text=Path('tools/era64j_historical_transfer_receipt_cost_enrichment.sh').read_text(encoding='utf-8')
assert text.count('VERIFIED_ZERO_GAS_PRICE_OBSERVATION')>=2
assert 'GAS_COST_NEGATIVE' in text
assert 'TRANSACTION_GAS_PRICE_INVALID' not in text
assert 'GAS_COST_INVALID' not in text
assert 'self.assertGreaterEqual(int(gas_cost),0)' in text
assert text.count('zero_gas_price_observation_count')>=2
assert text.count('ZERO_GAS_PRICE_OBSERVATION_COUNT=')==2
start=text.index("cat > \"$TOOL\" <<'PY_TOOL'\n")+len("cat > \"$TOOL\" <<'PY_TOOL'\n")
end=text.index('\nPY_TOOL\n',start)
Path('/tmp/era64j_zero_cost_compile_check_v2.py').write_text(text[start:end],encoding='utf-8')
print('ERA64J_ZERO_GAS_COST_OBSERVATION_PATCH_VERIFY_V2=VERIFIED')
PY_VERIFY
python3 -m py_compile /tmp/era64j_zero_cost_compile_check_v2.py
rm -f /tmp/era64j_zero_cost_compile_check_v2.py

git add "$TARGET"
git commit -m "ERA64: preserve verified zero gas cost observations"
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
rm -f "$BACKUP"

echo "ERA64J_ZERO_GAS_COST_OBSERVATION_FIX_V2=VERIFIED"
bash tools/era64j_historical_transfer_receipt_cost_enrichment.sh
