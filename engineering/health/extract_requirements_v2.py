from pathlib import Path
import ast

ROOT = Path.cwd()

third_party = set()

STDLIB = {
    "__future__","abc","argparse","ast","asyncio","base64","collections",
    "contextlib","csv","datetime","functools","glob","gzip","hashlib",
    "heapq","html","http","importlib","io","itertools","json","logging",
    "math","multiprocessing","os","pathlib","pickle","platform","queue",
    "random","re","secrets","shutil","signal","sqlite3","statistics",
    "string","subprocess","sys","tempfile","threading","time","traceback",
    "typing","types","urllib","uuid","warnings","xml","zipfile","unittest",
    "socket","errno","fnmatch","email","hmac","dataclasses","copy"
}

for py in ROOT.rglob("*.py"):

    try:
        tree = ast.parse(py.read_text(encoding="utf8",errors="ignore"))
    except Exception:
        continue

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for n in node.names:

                pkg=n.name.split(".")[0]

                if pkg not in STDLIB and pkg not in ("core","tools","tests"):
                    third_party.add(pkg)

        elif isinstance(node, ast.ImportFrom):

            if node.module:

                pkg=node.module.split(".")[0]

                if pkg not in STDLIB and pkg not in ("core","tools","tests"):
                    third_party.add(pkg)

print("="*60)
print("REAL THIRD PARTY PACKAGES")
print("="*60)

for p in sorted(third_party):
    print(p)
