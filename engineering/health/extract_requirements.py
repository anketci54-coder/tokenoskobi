from pathlib import Path
import re
import sys

ROOT = Path.cwd()

IMPORT_FILE = ROOT / "engineering" / "reports" / "all_imports.txt"

if not IMPORT_FILE.exists():
    print("Import report not found.")
    sys.exit(1)

STANDARD = {
    "__future__",
    "abc",
    "argparse",
    "asyncio",
    "base64",
    "collections",
    "concurrent",
    "contextlib",
    "csv",
    "datetime",
    "functools",
    "glob",
    "gzip",
    "hashlib",
    "heapq",
    "html",
    "http",
    "importlib",
    "io",
    "itertools",
    "json",
    "logging",
    "math",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "platform",
    "queue",
    "random",
    "re",
    "secrets",
    "shutil",
    "signal",
    "sqlite3",
    "statistics",
    "string",
    "subprocess",
    "sys",
    "tempfile",
    "threading",
    "time",
    "traceback",
    "typing",
    "types",
    "urllib",
    "uuid",
    "warnings",
    "xml",
    "zipfile",
    "fcntl"
}

imports = set()

pattern = re.compile(r"(?:import|from)\s+([A-Za-z0-9_.]+)")

for line in IMPORT_FILE.read_text(
        encoding="utf8",
        errors="ignore").splitlines():

    m = pattern.search(line)

    if not m:
        continue

    pkg = m.group(1).split(".")[0]

    if pkg in STANDARD:
        continue

    if pkg.startswith("core"):
        continue

    if pkg.startswith("tools"):
        continue

    if pkg.startswith("tests"):
        continue

    imports.add(pkg)

print("=" * 60)
print("THIRD PARTY PACKAGES")
print("=" * 60)

for pkg in sorted(imports):
    print(pkg)