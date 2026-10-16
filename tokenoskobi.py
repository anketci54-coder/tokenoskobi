#!/usr/bin/env python3
"""Tokenoskobi: start the panel or verify this checkout."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def serve(args) -> int:
    if args.port is not None:
        os.environ["TOKENOSKOBI_PRODUCT_SLICE_02_PORT"] = str(args.port)
    if args.state_dir is not None:
        os.environ["TOKENOSKOBI_SLICE03_STATE_DIR"] = str(args.state_dir.resolve())
    from services.market import tokenoskobi_product_slice_03_runtime as runtime

    cfg = runtime.CORE.CFG
    # Bind first: a conflicting process must not cause ledger writes.
    with runtime.ThreadingHTTPServer((cfg["host"], cfg["port"]), runtime.Handler) as server:
        runtime.CORE.ensure_state()
        runtime.verify_event_chain_locked()

        def stop(_signum, _frame):
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, stop)
        print(f"Tokenoskobi: http://{cfg['host']}:{cfg['port']}", flush=True)
        print(f"Karar geçmişi: {runtime.CORE.STATE_DIR}", flush=True)
        print("Durdurmak için Ctrl+C. Analiz, dış veri sağlayıcılarına erişir.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Tokenoskobi durduruldu.", flush=True)
    return 0


def verify() -> int:
    commands = [
        ["-m", "unittest", "discover", "-s", "tests", "-v"],
        ["scripts/legacy/a30_process_crash_recovery_policy_test.py"],
        ["scripts/engineering/tokenoskobi_healthcheck.py"],
        ["engineering/tests/smoke_test.py"],
        ["engineering/tests/product_runtime_smoke.py"],
        ["-m", "engineering.tests.product_e2e"],
    ]
    for command in commands:
        print("\n> " + " ".join([sys.executable, "-B", *command]), flush=True)
        result = subprocess.run([sys.executable, "-B", *command], cwd=ROOT)
        if result.returncode:
            return result.returncode
    print("Tüm yerel doğrulamalar geçti. Canlı sağlayıcı erişimi bu testlere dahil değildir.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    panel = commands.add_parser("serve", help="Paneli ve karar geçmişini başlat")
    panel.add_argument("--port", type=int, help="Yerel HTTP portu (varsayılan: 8096)")
    panel.add_argument("--state-dir", type=Path, help="Karar geçmişinin kalıcı dizini")
    commands.add_parser("check", help="Çevrimdışı kurulum ve yapılandırma kontrolü")
    commands.add_parser("test", help="Regresyonlar ve geçici portlarda HTTP yaşam döngüsü")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11) or os.name != "posix":
        parser.exit(1, "Python 3.11+ ve Linux/POSIX gerekir. Windows'ta WSL kullanın.\n")
    try:
        if args.command == "serve":
            return serve(args)
        if args.command == "check":
            from scripts.engineering.tokenoskobi_healthcheck import main as check
            return check([])
        return verify()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Tokenoskobi başlatılamadı: {exc}", file=sys.stderr)
        print("Port çakışıyorsa --port, kayıt izni gerekiyorsa --state-dir kullanın.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
