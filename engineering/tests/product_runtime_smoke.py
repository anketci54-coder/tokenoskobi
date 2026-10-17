"""Bounded loopback smoke test of both product entry points, without live APIs."""
import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def running_product(module: str, root: Path, arguments=(), environment=None):
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
        env.update(environment or {})
        base = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        command = ([str(ROOT / "start.sh"), *arguments] if module == "start.sh" else
                   [sys.executable, "-B", "-m", module, *arguments])
        process = subprocess.Popen(command,
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
            if module == "start.sh":
                assert process.returncode == 0, "Launcher did not shut down cleanly"


def raw_http(base, method, path, headers, payload=None):
    connection = http.client.HTTPConnection("127.0.0.1", urllib.parse.urlsplit(base).port, timeout=3)
    try:
        connection.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for name, value in headers:
            connection.putheader(name, value)
        body = None if payload is None else json.dumps(payload).encode()
        if body is not None:
            connection.putheader("Content-Type", "application/json")
            connection.putheader("Content-Length", str(len(body)))
        connection.endheaders(body)
        response = connection.getresponse()
        body = response.read()
        if response.getheader("Content-Type", "").startswith("application/json"):
            body = json.loads(body)
        return response.status, body
    finally:
        connection.close()


def check_request_trust(base):
    host = urllib.parse.urlsplit(base).netloc
    for headers in ([("Host", host)], [("Host", host), ("Origin", f"http://{host}")]):
        assert raw_http(base, "GET", "/healthz", headers)[0] == 200
    cases = (
        ([("Host", "attacker.example")], "UNTRUSTED_HOST"),
        ([("Host", "attacker.example"), ("Origin", "http://attacker.example")], "UNTRUSTED_HOST"),
        ([("Host", "attacker.example"), ("X-Forwarded-Host", host),
          ("X-Forwarded-Proto", "https")], "UNTRUSTED_HOST"),
        ([], "UNTRUSTED_HOST"),
        ([("Host", host), ("Host", host)], "DUPLICATE_SECURITY_HEADER"),
        ([("Host", host), ("Origin", f"http://{host}"),
          ("Origin", f"http://{host}")], "DUPLICATE_SECURITY_HEADER"),
        ([("Host", host), ("Origin", "null")], "CROSS_ORIGIN_REQUEST_REJECTED"),
        ([("Host", host), ("Origin", f"https://{host}")], "CROSS_ORIGIN_REQUEST_REJECTED"),
        ([("Host", host), ("Origin", f"http://{host}/path")], "CROSS_ORIGIN_REQUEST_REJECTED"),
    )
    for method, paths in (("GET", ("/", "/healthz", "/api/v1/history", "/api/v1/packets/" + "a" * 64)),
                          ("POST", ("/api/v1/analyze", "/api/v1/decisions", "/api/v1/outcomes/observe"))):
        for path in paths:
            for headers, error in cases:
                status, body = raw_http(base, method, path, headers,
                                        {"token_address": "invalid"} if method == "POST" else None)
                assert status == 400, (method, path, headers, status)
                assert body.get("error") == error, (method, path, headers, body)


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
            for raw in (b'[]', b'null', b'{', b'\xff', b'{"token_address": 2}'):
                request = urllib.request.Request(base + "/api/v1/analyze", method="POST",
                    data=raw, headers={"Content-Type": "application/json"})
                try:
                    opener.open(request, timeout=2)
                    raise AssertionError("Malformed request was accepted")
                except urllib.error.HTTPError as error:
                    with error:
                        assert error.code == 400, (raw, error.code, error.read())
            for headers in ({"Content-Type": "text/plain"},
                            {"Content-Type": "application/json", "Origin": "https://unrelated.example"}):
                request = urllib.request.Request(base + "/api/v1/analyze", method="POST",
                    data=b'{"token_address":"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}', headers=headers)
                try:
                    opener.open(request, timeout=2)
                    raise AssertionError("Foreign-origin or form submission accepted")
                except urllib.error.HTTPError as error:
                    with error:
                        assert error.code == 400, (headers, error.code, error.read())
            if module.endswith("slice_03_runtime") or module == "start.sh":
                with opener.open(base + "/healthz", timeout=2) as response:
                    assert json.load(response)["event_count"] == 0
            check_request_trust(base)
            print(f"{module}: health, panel, invalid input, 63 Host/Origin rejection probes PASS")


def proxy_smoke():
    with tempfile.TemporaryDirectory(prefix="tokenoskobi_proxy_smoke_") as directory:
        root = Path(directory)
        (root / "config").mkdir()
        config = json.loads((ROOT / "config/product_slice_02_v1.json").read_text())
        config["trusted_origins"] = ["https://panel.example", "https://second.example"]
        (root / "config/product_slice_02_v1.json").write_text(json.dumps(config))
        with running_product("start.sh", root, environment={"TOKENOSKOBI_ROOT": directory}) as (base, _):
            headers = [("Host", "panel.example"), ("Origin", "https://panel.example")]
            assert raw_http(base, "GET", "/healthz", headers)[0] == 200
            status, body = raw_http(base, "POST", "/api/v1/analyze", headers, {"token_address": "invalid"})
            assert (status, body["error"]) == (400, "INVALID_BSC_TOKEN_ADDRESS"), body
            for origin in ("http://panel.example", "https://second.example"):
                for method in ("GET", "POST"):
                    status, body = raw_http(base, method, "/healthz", [("Host", "panel.example"), ("Origin", origin)], {})
                    assert (status, body["error"]) == (400, "CROSS_ORIGIN_REQUEST_REJECTED"), body
            assert raw_http(base, "GET", "/healthz", [("Host", "panel.example")])[0] == 200
        print("start.sh: explicitly trusted HTTPS proxy origin, scheme/authority mismatch rejection PASS")


if __name__ == "__main__":
    for target in ("services.market.tokenoskobi_product_slice_02_server",
                   "services.market.tokenoskobi_product_slice_03_server",
                   "services.market.tokenoskobi_product_slice_03_runtime", "start.sh"):
        smoke(target)
    proxy_smoke()
