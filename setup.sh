#!/usr/bin/env bash
set -euo pipefail
repository_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$repository_dir"
python3 -c 'import os,sys; sys.exit(0 if os.name == "posix" and sys.version_info >= (3,11) else "Python 3.11+ ve Linux/POSIX gerekir.")'
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -B tokenoskobi.py check
printf '\nKurulum tamamlandı. Başlat: ./start.sh\nTestler: .venv/bin/python -B tokenoskobi.py test\n'
