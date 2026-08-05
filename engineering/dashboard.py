from pathlib import Path
import subprocess
import sys
import json

ROOT = Path(__file__).resolve().parent.parent

TOOLS = [
    ("Repository Validator", "engineering/health/repository_validator.py"),
    ("Health Check", "tools/tokenoskobi_healthcheck.py"),
    ("Repository Inventory", "engineering/health/repository_inventory.py"),
    ("Repository Intelligence", "engineering/health/repository_intelligence.py"),
]


def show_repository_summary():
    report = ROOT / "engineering" / "reports" / "repository_intelligence.json"

    if not report.exists():
        print("\nRepository summary not found.")
        return

    data = json.loads(report.read_text(encoding="utf-8"))

    print()
    print("=" * 72)
    print("REPOSITORY SUMMARY")
    print("=" * 72)

    for key, value in sorted(data["summary"].items()):
        print(f"{key:20} {value:5}")

    print("=" * 72)


print("=" * 72)
print("TOKENOSKOBI ENGINEERING DASHBOARD")
print("=" * 72)

for name, script in TOOLS:

    print()
    print(f">>> {name}")

    result = subprocess.run(
        [sys.executable, str(ROOT / script)],
        cwd=ROOT
    )

    if result.returncode == 0:
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name}")

show_repository_summary()

print()
print("=" * 72)
print("ENGINEERING DASHBOARD FINISHED")
print("=" * 72)