from pathlib import Path
import re

ROOT = Path.cwd()

CORE_FILES = [
    "tokenoskobi_kernel.py",
    "research_evidence_ledger.py",
    "runtime_policy_authority_gate.py",
    "tokenoskobi_product_slice_02_server.py",
    "tokenoskobi_product_slice_03_server.py",
    "tokenoskobi_product_slice_03_runtime.py",
]

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z0-9_\.]+)", re.MULTILINE)

print("=" * 70)
print("TOKENOSKOBI CORE DEPENDENCY MAP")
print("=" * 70)

for file in ROOT.rglob("*.py"):
    if file.name not in CORE_FILES:
        continue

    print(f"\n[{file.relative_to(ROOT)}]")

    try:
        text = file.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print("  READ ERROR:", e)
        continue

    imports = sorted(set(IMPORT_RE.findall(text)))

    for imp in imports:
        print("  ->", imp)