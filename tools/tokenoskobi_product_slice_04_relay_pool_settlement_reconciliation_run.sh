#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/tokenoskobi_clean_v1"
SOURCE="/var/lib/tokenoskobi-product-slice-04/relay_settlement_fifo_reconstruction_v1.json"
ALLOWLIST="${ROOT}/config/product_slice_04_factory_allowlist_v1.json"
OUTPUT="/var/lib/tokenoskobi-product-slice-04/relay_pool_settlement_reconciliation_v1.json"

cd "$ROOT"
exec python3 tools/tokenoskobi_product_slice_04_relay_pool_settlement_reconciliation.py \
  --source "$SOURCE" --allowlist "$ALLOWLIST" --output "$OUTPUT"
