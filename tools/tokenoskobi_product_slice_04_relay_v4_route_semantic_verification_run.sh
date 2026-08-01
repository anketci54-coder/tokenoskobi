#!/usr/bin/env bash
set -euo pipefail

cd /root/tokenoskobi_clean_v1

exec python3 tools/tokenoskobi_product_slice_04_relay_v4_route_semantic_verification.py
