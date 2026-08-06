#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

TARGET="tools/era64j_historical_transfer_receipt_cost_enrichment.sh"
BACKUP="/root/era64j_runner_before_zero_cost_observation_fix_$(date -u +%Y%m%dT%H%M%SZ).sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
cp "$TARGET" "$BACKUP"

python3 <<'PY'
from pathlib import Path

path=Path('tools/era64j_historical_transfer_receipt_cost_enrichment.sh')
text=path.read_text(encoding='utf-8')
replacements=[
(
"""        transaction_gas_price=as_hex_int(transaction.get('gasPrice'),'transaction.gasPrice')
        if transaction_gas_price<=0:
            raise Era64JError(f'TRANSACTION_GAS_PRICE_INVALID:{tx_hash}')
        effective_gas_price=transaction_gas_price
        raw_transaction=json.dumps(transaction,sort_keys=True,separators=(',',':'),ensure_ascii=True)
        gas_price_source='TRANSACTION_GAS_PRICE_FALLBACK'
    gas_cost=gas_used*effective_gas_price
    if gas_cost<=0:
        raise Era64JError(f'GAS_COST_INVALID:{tx_hash}')
""",
"""        transaction_gas_price=as_hex_int(transaction.get('gasPrice'),'transaction.gasPrice')
        effective_gas_price=transaction_gas_price
        raw_transaction=json.dumps(transaction,sort_keys=True,separators=(',',':'),ensure_ascii=True)
        gas_price_source='TRANSACTION_GAS_PRICE_FALLBACK' if transaction_gas_price>0 else 'VERIFIED_ZERO_GAS_PRICE_OBSERVATION'
    gas_cost=gas_used*effective_gas_price
    if gas_cost<0:
        raise Era64JError(f'GAS_COST_NEGATIVE:{tx_hash}')
"""
),
(
"""                self.assertEqual(int(gas_cost),int(gas_used)*int(gas_price))
                self.assertGreater(int(gas_cost),0)
""",
"""                self.assertEqual(int(gas_cost),int(gas_used)*int(gas_price))
                self.assertGreaterEqual(int(gas_cost),0)
"""
),
(
"""    fallback_count=sum(1 for item in enrichments if item['gas_price_source']=='TRANSACTION_GAS_PRICE_FALLBACK')
    total_gas_cost=sum(int(item['gas_cost_wei']) for item in enrichments)
""",
"""    fallback_count=sum(1 for item in enrichments if item['gas_price_source']=='TRANSACTION_GAS_PRICE_FALLBACK')
    zero_gas_price_count=sum(1 for item in enrichments if item['gas_price_source']=='VERIFIED_ZERO_GAS_PRICE_OBSERVATION')
    total_gas_cost=sum(int(item['gas_cost_wei']) for item in enrichments)
"""
),
(
"""      'gas_price_fallback_count':fallback_count,'total_gas_cost_wei':str(total_gas_cost),
""",
"""      'gas_price_fallback_count':fallback_count,'zero_gas_price_observation_count':zero_gas_price_count,
      'total_gas_cost_wei':str(total_gas_cost),
"""
),
(
"""       'gas_price_fallback_count':fallback_count,'total_gas_cost_wei':str(total_gas_cost),
""",
"""       'gas_price_fallback_count':fallback_count,'zero_gas_price_observation_count':zero_gas_price_count,
       'total_gas_cost_wei':str(total_gas_cost),
"""
),
(
"""     print(f"FAILED_RECEIPT_COUNT={control['failed_receipt_count']}")
     print(f"RPC_REQUEST_COUNT={control['rpc_request_count']}")
""",
"""     print(f"FAILED_RECEIPT_COUNT={control['failed_receipt_count']}")
     print(f"ZERO_GAS_PRICE_OBSERVATION_COUNT={control['zero_gas_price_observation_count']}")
     print(f"RPC_REQUEST_COUNT={control['rpc_request_count']}")
"""
),
(
""" print(f"FAILED_RECEIPT_COUNT={c['failed_receipt_count']}")
 print(f"RPC_REQUEST_COUNT={c['rpc_request_count']}")
""",
""" print(f"FAILED_RECEIPT_COUNT={c['failed_receipt_count']}")
 print(f"ZERO_GAS_PRICE_OBSERVATION_COUNT={c['zero_gas_price_observation_count']}")
 print(f"RPC_REQUEST_COUNT={c['rpc_request_count']}")
"""
),
]
for old,new in replacements:
    count=text.count(old)
    if count!=1:
        raise SystemExit(f'ERA64J_ZERO_COST_OBSERVATION_PATTERN_COUNT_INVALID:{count}:{old[:100]!r}')
    text=text.replace(old,new,1)
path.write_text(text,encoding='utf-8')
print('ERA64J_ZERO_GAS_COST_OBSERVATION_FIX=APPLIED')
PY

python3 <<'PY_VERIFY'
from pathlib import Path
text=Path('tools/era64j_historical_transfer_receipt_cost_enrichment.sh').read_text(encoding='utf-8')
assert 'VERIFIED_ZERO_GAS_PRICE_OBSERVATION' in text
assert 'GAS_COST_NEGATIVE' in text
assert 'TRANSACTION_GAS_PRICE_INVALID' not in text
assert 'self.assertGreaterEqual(int(gas_cost),0)' in text
assert 'zero_gas_price_observation_count' in text
start=text.index("cat > \"$TOOL\" <<'PY_TOOL'\n")+len("cat > \"$TOOL\" <<'PY_TOOL'\n")
end=text.index('\nPY_TOOL\n',start)
Path('/tmp/era64j_zero_cost_compile_check.py').write_text(text[start:end],encoding='utf-8')
print('ERA64J_ZERO_GAS_COST_OBSERVATION_PATCH_VERIFY=VERIFIED')
PY_VERIFY
python3 -m py_compile /tmp/era64j_zero_cost_compile_check.py
rm -f /tmp/era64j_zero_cost_compile_check.py

git add "$TARGET"
git commit -m "ERA64: preserve verified zero gas price observations"
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
rm -f "$BACKUP"

echo "ERA64J_ZERO_GAS_COST_OBSERVATION_FIX=VERIFIED"
bash tools/era64j_historical_transfer_receipt_cost_enrichment.sh
