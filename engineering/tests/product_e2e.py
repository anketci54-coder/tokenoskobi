"""HTTP lifecycle test with synthetic provider responses and real disk persistence.

Only the external provider transport is replaced. Analysis, evidence validation,
HTTP routing, packet hashing, locking and history storage run production code.
No live market/API availability is established by this test.
"""
import json
import os
import sqlite3
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from engineering.tests.product_runtime_smoke import running_product

TOKEN = "0x" + "a" * 40
QUOTE = "0x" + "b" * 40
POOL = "0x" + "c" * 40


def serve_fixture(root: Path):
    from services.market import tokenoskobi_product_slice_03_runtime as runtime

    market = runtime.CORE.SLICE02
    market.ROOT = root
    market.DBS = [root / "news.sqlite"]
    market.CFG["rpc"] = ["fixture://public"]
    os.environ["BSC_ALCHEMY_URL"] = "fixture://alchemy"

    def provider_response(url, body=None):
        price = float((root / "price").read_text())
        if body is not None and url in ("fixture://public", "fixture://alchemy"):
            values = {"eth_chainId": "0x38", "eth_blockNumber": "0x100000",
                      "eth_getCode": "0x6000"}
            if body["method"] == "eth_call":
                metadata = {market.SEL["name"]: "0x" + b"Fixture Token".ljust(32, b"\0").hex(),
                            market.SEL["symbol"]: "0x" + b"FIX".ljust(32, b"\0").hex(),
                            market.SEL["decimals"]: hex(18),
                            market.SEL["supply"]: hex(1_000_000 * 10**18),
                            market.SEL["owner"]: "0x" + "0" * 64}
                return {"result": metadata[body["params"][0]["data"]]}
            return {"result": values[body["method"]]}
        parsed = urllib.parse.urlsplit(url)
        assert parsed.netloc == "api.geckoterminal.com", url
        if parsed.path.endswith(f"/tokens/{TOKEN}"):
            return {"data": {"attributes": {"name": "Fixture Token", "symbol": "FIX",
                                            "price_usd": str(price)}}}
        if parsed.path.endswith(f"/tokens/{TOKEN}/pools"):
            return {"data": [{
                "attributes": {"address": POOL, "reserve_in_usd": "100000",
                               "base_token_price_usd": str(price), "quote_token_price_usd": "1"},
                "relationships": {
                    "base_token": {"data": {"id": f"bsc_{TOKEN}"}},
                    "quote_token": {"data": {"id": f"bsc_{QUOTE}"}},
                },
            }]}
        if f"/pools/{POOL}/ohlcv/" in parsed.path:
            assert urllib.parse.parse_qs(parsed.query)["token"] == [TOKEN]
            stamp = 1000 if (root / "stale").exists() else int(time.time()) - 10
            return {"meta": {"base": {"address": TOKEN}, "quote": {"address": QUOTE}},
                    "data": {"attributes": {"ohlcv_list": [
                        [stamp - i * 60, price, price, price, price, 100] for i in range(10)
                    ]}}}
        raise AssertionError(f"Unexpected provider request: {url}")

    market.request = provider_response
    runtime.CORE.ensure_state()
    runtime.verify_event_chain_locked()
    with runtime.ThreadingHTTPServer(("127.0.0.1", runtime.CORE.CFG["port"]),
                                     runtime.Handler) as server:
        server.serve_forever()


def check_lifecycle():
    with tempfile.TemporaryDirectory(prefix="tokenoskobi_e2e_") as directory:
        root = Path(directory)
        (root / "price").write_text("100")
        with sqlite3.connect(root / "news.sqlite") as connection:
            connection.execute("CREATE TABLE news_raw_feed_events (title TEXT, published_at_utc TEXT)")
            connection.execute("INSERT INTO news_raw_feed_events VALUES (?, ?)",
                               (TOKEN, datetime.now(timezone.utc).isoformat()))

        def call(path, payload=None, status=200):
            request = urllib.request.Request(
                base + path, data=None if payload is None else json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "X-Authenticated-User": "e2e-user"},
            )
            try:
                response = opener.open(request, timeout=5)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                result = json.load(response)
                assert response.code == status, (response.code, result)
                return result

        module = "engineering.tests.product_e2e"
        with running_product(module, root, ("--serve", directory)) as (base, opener):
            analysis = call("/api/v1/analyze", {"token_address": TOKEN})
            assert analysis["decision"]["decision"] == "ALLOW", analysis["decision"]
            assert analysis["decision"]["data_quality"] == "SUFFICIENT"
            assert analysis["news"]["fresh"] is True
            assert all(analysis["authority"][key] is False
                       for key in ("paper", "live", "wallet", "signing", "order", "broadcast"))
            packet_id = analysis["history"]["packet_id"]
            body = {"packet_id": packet_id}
            rejected = call("/api/v1/outcomes/observe", body, 400)
            assert rejected["error"] == "HUMAN_DECISION_REQUIRED_BEFORE_OUTCOME"
            assert call("/healthz")["event_count"] == 1

            human = call("/api/v1/decisions", {**body, "action": "ACCEPT", "note": "fixture only"}, 201)
            assert human["authority"] == "NO_TRADE_EXECUTION"
            assert human["event"]["payload"]["actor"] == "e2e-user"
            (root / "price").write_text("110")
            outcome = call("/api/v1/outcomes/observe", body, 201)
            assert outcome["authority"] == "OBSERVATION_ONLY_NO_EXECUTION"
            assert outcome["event"]["payload"]["change_pct"] == 10
            assert outcome["event"]["payload"]["human_decision_event_hash"] == human["event"]["event_hash"]
            packet = call(f"/api/v1/packets/{packet_id}")
            assert packet["integrity"] == "VERIFIED"
            assert packet["packet"]["analysis"]["market"]["token"]["price_usd"] == 100
            assert len(packet["events"]) == 3
            history = call("/api/v1/history")

        # A new OS process must reconstruct the same packet and event chain from disk.
        with running_product(module, root, ("--serve", directory)) as (base, opener):
            assert call("/healthz")["event_count"] == 3
            assert call("/api/v1/history") == history
            assert call(f"/api/v1/packets/{packet_id}") == packet
            (root / "stale").touch()
            degraded = call("/api/v1/analyze", {"token_address": TOKEN})
            assert degraded["decision"]["data_quality"] == "VERI_YETERSIZ"
            assert degraded["decision"]["decision"] == "REVIEW"
            assert call("/healthz")["event_count"] == 4
        print("HTTP E2E: analysis, human decision, outcome, restart persistence, stale-data rejection PASS")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--serve":
        serve_fixture(Path(sys.argv[2]))
    else:
        check_lifecycle()
