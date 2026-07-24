#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SOURCE="tools/era64g_bounded_staging_database_backfill.sh"
TARGET="/tmp/era64g_bounded_staging_database_backfill_zero_address_fixed.sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -f "$SOURCE" ]]

python3 - "$SOURCE" "$TARGET" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
text = source.read_text(encoding='utf-8')

old_sql = """        distinct_wallets=int(conn.execute('''
          SELECT COUNT(*) FROM (
            SELECT from_address AS wallet FROM era64g_wallet_event_staging_v1
            UNION
            SELECT to_address AS wallet FROM era64g_wallet_event_staging_v1
          )
        ''').fetchone()[0])"""
new_sql = """        distinct_wallets=int(conn.execute('''
          SELECT COUNT(*) FROM (
            SELECT from_address AS wallet
              FROM era64g_wallet_event_staging_v1
             WHERE from_address != '0x0000000000000000000000000000000000000000'
            UNION
            SELECT to_address AS wallet
              FROM era64g_wallet_event_staging_v1
             WHERE to_address != '0x0000000000000000000000000000000000000000'
          )
        ''').fetchone()[0])"""

old_test = "self.assertEqual(self.control['distinct_wallet_count'],150)"
new_test = "self.assertEqual(self.control['distinct_wallet_count'],self.source['distinct_wallet_count'])"

if text.count(old_sql) != 1:
    raise RuntimeError(f'ERA64G_DISTINCT_WALLET_SQL_PATTERN_COUNT={text.count(old_sql)}')
if text.count(old_test) != 1:
    raise RuntimeError(f'ERA64G_DISTINCT_WALLET_TEST_PATTERN_COUNT={text.count(old_test)}')

text = text.replace(old_sql, new_sql, 1)
text = text.replace(old_test, new_test, 1)

target.write_text(text, encoding='utf-8')
target.chmod(0o700)
print('ERA64G_ZERO_ADDRESS_WALLET_COUNT_FIX=VERIFIED')
PY

exec bash "$TARGET"
