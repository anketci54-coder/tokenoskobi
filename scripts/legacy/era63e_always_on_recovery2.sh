#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]

python3 <<'PY'
from pathlib import Path

source_path = Path('/root/tokenoskobi_clean_v1/tools/era63e_always_on_fix.sh')
target_path = Path('/tmp/era63e_always_on_fix_recovered2.sh')
text = source_path.read_text(encoding='utf-8')

old_test = """    def test_13_rpc_methods_are_read_only(self):
        source = ENGINE_PATH.read_text(encoding='utf-8')
        self.assertIn(\"'eth_chainId'\", source)
        self.assertIn(\"'eth_blockNumber'\", source)
        self.assertIn(\"'eth_getBlockByNumber'\", source)
        for forbidden in ('eth_sendTransaction', 'eth_sendRawTransaction', 'personal_', 'wallet_'):
            self.assertNotIn(forbidden, source)
"""
new_test = """    def test_13_rpc_methods_are_read_only(self):
        tree = ast.parse(ENGINE_PATH.read_text(encoding='utf-8'))
        methods = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != 'call' or not node.args:
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                methods.add(first.value)
        self.assertEqual(methods, {'eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber'})
"""
if old_test not in text:
    raise SystemExit('RECOVERY_TEST_PATCH_TARGET_NOT_FOUND')
text = text.replace(old_test, new_test, 1)

old_stage = """git add -- \"${FILES[@]}\"
git add -f reports/LATEST_ERA63E_ALWAYS_ON_MARKET_RUNTIME.md reports/LATEST_TK_AI_HANDOFF.md
"""
new_stage = """for file in \"${FILES[@]}\"; do
  case \"$file\" in
    reports/*) git add -f -- \"$file\" ;;
    *) git add -- \"$file\" ;;
  esac
done
"""
if old_stage not in text:
    raise SystemExit('RECOVERY_STAGE_PATCH_TARGET_NOT_FOUND')
text = text.replace(old_stage, new_stage, 1)

target_path.write_text(text, encoding='utf-8')
target_path.chmod(0o700)
print('RECOVERY_PATCH=RPC_AST_ALLOWLIST_AND_IGNORED_REPORT_STAGING')
PY

exec bash /tmp/era63e_always_on_fix_recovered2.sh
