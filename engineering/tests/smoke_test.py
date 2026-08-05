from pathlib import Path

ROOT = Path.cwd()

FILES = [
    "tokenoskobi_kernel.py",
    "tools/tokenoskobi_product_slice_02_server.py",
    "tools/tokenoskobi_product_slice_03_server.py",
    "core/platform/file_lock.py",
]

print("=" * 60)
print("TOKENOSKOBI SMOKE TEST")
print("=" * 60)

failed = False

for item in FILES:

    path = ROOT / item

    ok = path.exists()

    print(f"{item:<55} {'PASS' if ok else 'FAIL'}")

    if not ok:
        failed = True

print("=" * 60)

if failed:
    raise SystemExit(1)

print("SMOKE TEST PASSED")
