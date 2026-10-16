"""Bounded loopback smoke test of both product entry points, without live APIs."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def running_product(module: str, root: Path, arguments=()):
    """Start an isolated subprocess and always reap it, including on failure."""
    with (root / "server.log").open("w+") as log:
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        env = {key: value for key, value in os.environ.items()
               if not key.startswith("TOKENOSKOBI_")}
        env.update({
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT),
            "TOKENOSKOBI_PRODUCT_SLICE_02_PORT": str(port),
            "TOKENOSKOBI_SLICE03_STATE_DIR": str(root / "state"),
            "TOKENOSKOBI_GT_RATE_DIR": str(root / "rate"),
        })
        base = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        process = subprocess.Popen([sys.executable, "-B", "-m", module, *arguments],
                                   cwd=root, env=env, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 10
            while True:
                if process.poll() is not None:
                    log.seek(0)
                    raise AssertionError(f"Startup failed: {log.read()}")
                try:
                    with opener.open(base + "/healthz", timeout=0.5) as response:
                        health = json.load(response)
                    break
                except (urllib.error.URLError, TimeoutError):
                    if time.monotonic() >= deadline:
                        raise AssertionError("Readiness timeout")
                    time.sleep(0.05)
            assert health["ok"] is True, health
            yield base, opener
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def smoke(module: str) -> None:
    with tempfile.TemporaryDirectory(prefix="tokenoskobi_runtime_smoke_") as directory:
        with running_product(module, Path(directory)) as (base, opener):
            with opener.open(base + "/", timeout=2) as response:
                assert response.status == 200
                assert "TOKENOSKOB" in response.read().decode().upper()
            request = urllib.request.Request(
                base + "/api/v1/analyze", method="POST",
                data=json.dumps({"token_address": "invalid"}).encode(),
                headers={"Content-Type": "application/json"},
            )
            try:
                opener.open(request, timeout=2)
                raise AssertionError("Invalid address was accepted")
            except urllib.error.HTTPError as error:
                with error:
                    payload = json.load(error)
                assert error.code == 400, (error.code, payload)
                assert "INVALID" in payload["error"], payload
            if module.endswith("slice_03_runtime"):
                with opener.open(base + "/healthz", timeout=2) as response:
                    assert json.load(response)["event_count"] == 0
            print(f"{module}: health, panel, invalid-input rejection PASS")


if __name__ == "__main__":
    for target in ("services.market.tokenoskobi_product_slice_02_server",
                   "services.market.tokenoskobi_product_slice_03_runtime"):
        smoke(target)
