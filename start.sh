#!/usr/bin/env bash
set -euo pipefail
repository_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="${TOKENOSKOBI_PYTHON:-python3}"
if [[ -z "${TOKENOSKOBI_PYTHON:-}" && -x "$repository_dir/.venv/bin/python" ]]; then
    python_bin="$repository_dir/.venv/bin/python"
fi
exec "$python_bin" -B "$repository_dir/tokenoskobi.py" serve "$@"
