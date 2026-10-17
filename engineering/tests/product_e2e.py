"""HTTP lifecycle test with synthetic provider responses and real disk persistence.

Only the external provider transport is replaced. Analysis, evidence validation,
HTTP routing, packet hashing, locking and history storage run production code.
No live market/API availability is established by this test.
"""
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from engineering.tests.product_runtime_smoke import running_product
from engineering.tests.pancakeswap_fixture import BscPoolFixture

TOKEN = "0x" + "a" * 40
QUOTE = "0x55d398326f99059ff775485246999027b3197955"
POOL = "0x" + "c" * 40


def serve_fixture(root: Path):
    from services.market import tokenoskobi_product_slice_03_runtime as runtime

    market = runtime.CORE.SLICE02
    market.ROOT = root
    market.DBS = [root / "news.sqlite"]
    market.CFG["rpc"] = ["fixture://public"]
    os.environ.pop("BSC_ALCHEMY_URL", None)
    pools = {POOL: {"version": "v2", "tokens": (TOKEN, QUOTE)}}
    pool_rpc = BscPoolFixture(pools)

    def provider_response(url, body=None):
        price = float((root / "price").read_text())
        if body is not None and url in ("fixture://public", "fixture://alchemy"):
            pools[POOL]["factory"] = "0x" + "d" * 40 if (root / "unverified").exists() else None
            values = {"eth_chainId": "0x38", "eth_blockNumber": "0x100000",
                      "eth_getCode": "0x6000"}
            if body["method"] == "eth_call":
                if body["params"][0]["to"] == POOL:
                    return {"result": pool_rpc(url, body["method"], body["params"])}
                if body["params"][0]["data"] not in market.SEL.values():
                    return {"result": pool_rpc(url, body["method"], body["params"])}
                metadata = {market.SEL["name"]: "0x" + b"Fixture Token".ljust(32, b"\0").hex(),
                            market.SEL["symbol"]: "0x" + b"FIX".ljust(32, b"\0").hex(),
                            market.SEL["decimals"]: hex(18),
                            market.SEL["supply"]: hex(1_000_000 * 10**18),
                            market.SEL["owner"]: "0x" + "0" * 64}
                return {"result": metadata[body["params"][0]["data"]]}
            return {"result": values[body["method"]]}
        parsed = urllib.parse.urlsplit(url)
        assert parsed.netloc == "api.geckoterminal.com", url
        if parsed.path.endswith((f"/tokens/{TOKEN}", f"/tokens/{QUOTE}")):
            return {"data": {"attributes": {"name": "Fixture Token", "symbol": "FIX",
                                            "price_usd": str(price)}}}
        if parsed.path.endswith((f"/tokens/{TOKEN}/pools", f"/tokens/{QUOTE}/pools")):
            return {"data": [{
                "attributes": {"address": POOL, "reserve_in_usd": "100000",
                               "base_token_price_usd": str(price), "quote_token_price_usd": "1"},
                "relationships": {
                    "base_token": {"data": {"id": f"bsc_{TOKEN}"}},
                    "quote_token": {"data": {"id": f"bsc_{QUOTE}"}},
                    "dex": {"data": {"id": "provider-label-is-not-proof"}},
                },
            }]}
        if f"/pools/{POOL}/ohlcv/" in parsed.path:
            assert urllib.parse.parse_qs(parsed.query)["token"][0] in (TOKEN, QUOTE)
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
        with closing(sqlite3.connect(root / "news.sqlite")) as connection, connection:
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
            selected = analysis["market"]["selected_pool"]
            assert selected["provenance"]["verified"] is True
            assert selected["provenance"]["version"] == "v2"
            assert selected["quote_token_address"] == QUOTE  # stable quote allowed
            assert analysis["market"]["token"]["price_source"] == "VERIFIED_PANCAKESWAP_POOL"
            assert analysis["news"]["fresh"] is True
            assert analysis["provider"]["alchemy_http_ok"] is False
            assert "ALCHEMY_HYBRID_NOT_READY" in analysis["decision"]["warnings"]
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
            for publication in ("2000-01-01T00:00:00+00:00", None):
                with closing(sqlite3.connect(root / "news.sqlite")) as connection, connection:
                    connection.execute("DELETE FROM news_raw_feed_events")
                    if publication is not None:
                        connection.execute("INSERT INTO news_raw_feed_events VALUES (?, ?)", (TOKEN, publication))
                degraded_news = call("/api/v1/analyze", {"token_address": TOKEN})
                assert degraded_news["news"]["fresh"] is False
                assert degraded_news["decision"]["decision"] == "REVIEW", degraded_news["decision"]
                assert degraded_news["decision"]["data_quality"] == "VERI_YETERSIZ"
            with closing(sqlite3.connect(root / "news.sqlite")) as connection, connection:
                connection.execute("INSERT INTO news_raw_feed_events VALUES (?, ?)",
                                   (TOKEN, datetime.now(timezone.utc).isoformat()))
            (root / "stale").touch()
            degraded = call("/api/v1/analyze", {"token_address": TOKEN})
            assert degraded["decision"]["data_quality"] == "VERI_YETERSIZ"
            assert degraded["decision"]["decision"] == "REVIEW"
            assert call("/healthz")["event_count"] == 6

        # Reopen the same ledger through the actual launcher with no provider
        # substitution. GETs and human records need no market/network access.
        state = root / "state"
        packet_file = state / "packets" / f"{packet_id}.json"
        packet_bytes = packet_file.read_bytes()
        event_file = state / "decision_history_v1.jsonl"
        event_prefix = event_file.read_bytes()
        wrong_state = root / "ignored-environment-state"
        arguments = ("--state-dir", str(state))
        for index in range(2):
            with running_product("start.sh", root, arguments,
                                 {"TOKENOSKOBI_SLICE03_STATE_DIR": str(wrong_state)}) as (base, opener):
                assert call("/healthz")["event_count"] == 6 + index
                if index == 0:
                    revision = call("/api/v1/decisions", {**body, "action": "WAIT"}, 201)
                    assert revision["event"]["seq"] == 7
                    assert revision["event"]["payload"]["previous_decision_event_hash"] == human["event"]["event_hash"]
                    assert revision["authority"] == "NO_TRADE_EXECUTION"
                    launcher_history = call("/api/v1/history")
                else:
                    assert call("/api/v1/history") == launcher_history
                    assert call(f"/api/v1/packets/{packet_id}")["packet"]["analysis"] == packet["packet"]["analysis"]
            assert packet_file.read_bytes() == packet_bytes
            assert event_file.read_bytes().startswith(event_prefix)
            assert not wrong_state.exists(), "CLI state-dir precedence failed"

        env = {key: value for key, value in os.environ.items() if not key.startswith("TOKENOSKOBI_")}
        env["XDG_STATE_HOME"] = str(root / "unused-xdg")
        launcher = Path(__file__).resolve().parents[2] / "start.sh"
        event_file.write_bytes(event_file.read_bytes() + b"corrupt\n")
        corrupt_bytes = event_file.read_bytes()
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            free_port = reservation.getsockname()[1]
        failed = subprocess.run([str(launcher), "--port", str(free_port), *arguments],
                                cwd=root, env=env, capture_output=True, text=True, timeout=10)
        assert failed.returncode == 1, (failed.stdout, failed.stderr)
        assert "EVENT_LOG_INVALID_JSON" in failed.stderr, failed.stderr
        assert event_file.read_bytes() == corrupt_bytes
        assert not (root / "unused-xdg").exists(), "Corruption caused silent fallback"

        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            unused_state = root / "port-conflict-state"
            conflict = subprocess.run([str(launcher), "--port", str(listener.getsockname()[1]),
                                       "--state-dir", str(unused_state)], cwd=root, env=env,
                                      capture_output=True, text=True, timeout=10)
            assert conflict.returncode == 1, (conflict.stdout, conflict.stderr)
            assert "Address already in use" in conflict.stderr, conflict.stderr
            assert not unused_state.exists(), "Occupied port caused ledger writes"
        print("HTTP E2E: optional Alchemy, required-news gate, immutable packets, human/outcome links, "
              "launcher restart/CLI precedence, corrupt-ledger refusal, port-conflict isolation PASS")


def check_policy_gate():
    """Actual handlers and verifier, with only external transport substituted."""
    with tempfile.TemporaryDirectory(prefix="tokenoskobi_policy_e2e_") as directory:
        root = Path(directory)
        (root / "price").write_text("100")
        with running_product("engineering.tests.product_e2e", root, ("--serve", directory)) as (base, opener):
            def call(path, payload=None, expected=200):
                request = urllib.request.Request(base + path,
                    data=None if payload is None else json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"})
                try:
                    response = opener.open(request, timeout=5)
                except urllib.error.HTTPError as exc:
                    response = exc
                with response:
                    data = json.load(response)
                    assert response.code == expected, data
                    return data
            # A historical packet remains readable when current provenance fails.
            original = call("/api/v1/analyze", {"token_address": TOKEN})
            packet_id = original["history"]["packet_id"]
            call("/api/v1/decisions", {"packet_id": packet_id, "action": "ACCEPT"}, 201)
            count = call("/healthz")["event_count"]
            (root / "unverified").touch()
            failure = call("/api/v1/outcomes/observe", {"packet_id": packet_id}, 400)
            assert failure["error"] == "CURRENT_POOL_PROVENANCE_UNVERIFIED", failure
            assert call("/healthz")["event_count"] == count
            rejected = call("/api/v1/analyze", {"token_address": TOKEN})
            assert rejected["decision"]["decision"] == "BLOCK", rejected["decision"]
            assert "POOL_PROVENANCE_UNVERIFIED" in rejected["decision"]["blockers"]
            assert rejected["market"]["selected_pool"] is None
            assert rejected["market"]["rejected_pools"][0]["provenance"]["verified"] is False
            assert all(row["status"] == "VERI_YETERSIZ" for row in rejected["technical_timeframes"].values())
            (root / "unverified").unlink()
            stable = call("/api/v1/analyze", {"token_address": QUOTE})
            assert stable["decision"]["decision"] == "BLOCK", stable["decision"]
            assert "STABLECOIN_TARGET_EXCLUDED" in stable["decision"]["blockers"]
            reopened = call(f"/api/v1/packets/{packet_id}")
            assert reopened["packet"]["analysis"]["market"] == original["market"]
            assert reopened["integrity"] == "VERIFIED"
        print("HTTP policy E2E: unverified pools BLOCK; failed provenance writes no outcome; "
              "stable target BLOCK, stable quote accepted, prior packet preserved PASS")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--serve":
        serve_fixture(Path(sys.argv[2]))
    else:
        check_lifecycle()
        check_policy_gate()
