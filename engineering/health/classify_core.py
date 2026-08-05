from pathlib import Path

ROOT = Path.cwd()

RULES = {
    "CORE": [
        "kernel",
        "product_slice",
        "runtime_policy",
        "research_evidence",
    ],
    "RUNTIME": [
        "runtime",
        "producer",
        "panel",
        "ledger",
    ],
    "ARCHIVE": [
        "archive",
        "dryrun",
        "plan",
        "post_audit",
        "backup",
        "fix",
        "repair",
    ],
}

groups = {
    "CORE": [],
    "RUNTIME": [],
    "ARCHIVE": [],
    "OTHER": [],
}

for f in ROOT.rglob("*.py"):

    text = str(f).lower()

    found = False

    for group, keys in RULES.items():

        if any(k in text for k in keys):

            groups[group].append(f)

            found = True

            break

    if not found:

        groups["OTHER"].append(f)

print("=" * 60)

for group in groups:

    print(group)

    print("-" * 60)

    print(len(groups[group]))

    for x in groups[group][:40]:

        print(x.relative_to(ROOT))

    print()