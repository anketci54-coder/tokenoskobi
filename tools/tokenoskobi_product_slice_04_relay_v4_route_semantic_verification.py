#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
DEFAULT_PROVIDER = ROOT / "config/era63e_always_on_market_runtime_v1.json"
DEFAULT_RECONCILIATION = Path("/var/lib/tokenoskobi-product-slice-04/relay_pool_settlement_reconciliation_v1.json")
DEFAULT_RECEIPT = Path("/var/lib/tokenoskobi-product-slice-04/relay_v4_target_receipt_v1.json")
DEFAULT_OUTPUT = Path("/var/lib/tokenoskobi-product-slice-04/relay_v4_route_semantic_verification_v1.json")

TARGET_TX = "0x3d516b2c6ccee0235ec7a81303de7e04cf667972639a881b4dc6fc602cd70f5a"
RELAY_V3_ROUTER = "0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f"
RELAY_SOLVER = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"
UNISWAP_V4_POOL_MANAGER = "0x28e2ea090877bf75740558f6bfb36a5ffee9e9df"
SETTLEMENT_CALLER = "0x011af51cc6614fec1de0e0ff6dc315a150f3851c"
POOL_ID = "0x8321c1f53959b14ece4b5400e60aeac59e7b6b8bac446f2f0a89b9e84e68a08a"
USDC = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"
USDT = "0x55d398326f99059ff775485246999027b3197955"
POOL_INPUT_RAW = 10_483_200_000_000_000_000
POOL_OUTPUT_RAW = 10_490_666_816_297_243_269

SOLVER_CALL_EXECUTED_TOPIC = "0x93485dcd31a905e3ffd7b012abe3438fa8fa77f98ddc9f50e879d3fa7ccdc324"
FUNDS_MOVEMENT_TOPIC = "0xafbab204e8271965231d37baed9b1abca8725b7409c70314455f68bc89142b91"
UNISWAP_V4_SWAP_TOPIC = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"

OFFICIAL_ALLOWLIST = {
    "relay_v3_router": {
        "address": RELAY_V3_ROUTER,
        "source": "https://docs.relay.link/references/api/api_resources/contract-addresses",
        "events": {
            SOLVER_CALL_EXECUTED_TOPIC: "SolverCallExecuted(address,bytes,uint256)",
            FUNDS_MOVEMENT_TOPIC: "FundsMovement(address,address,address,uint256,bytes)",
        },
    },
    "uniswap_v4_pool_manager": {
        "address": UNISWAP_V4_POOL_MANAGER,
        "source": "https://developers.uniswap.org/docs/protocols/v4/deployments",
        "interface_source": "https://github.com/Uniswap/v4-core/blob/main/src/interfaces/IPoolManager.sol",
        "events": {UNISWAP_V4_SWAP_TOPIC: "Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)"},
    },
}

AUTHORITY = {
    "network_access": True,
    "network_mode": "READ_ONLY_ALLOWLISTED_BSC_RPC_SINGLE_RECEIPT",
    "staging_file_write": True,
    "source_evidence_write": False,
    "repository_write": False,
    "production_database_write": False,
    "panel_mutation": False,
    "service_mutation": False,
    "timer_mutation": False,
    "paper_trade": False,
    "live_trade": False,
    "wallet": False,
    "signing": False,
    "order_create": False,
    "broadcast": False,
}

HEX_RE = re.compile(r"^0x[0-9a-f]*$")
ADDRESS_RE = re.compile(r"^0x[0-9a-f]{40}$")
HASH_RE = re.compile(r"^0x[0-9a-f]{64}$")


class SemanticVerificationError(RuntimeError):
    pass


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_object(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise SemanticVerificationError(f"{code}_MISSING")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticVerificationError(f"{code}_INVALID_JSON") from exc
    if not isinstance(value, dict):
        raise SemanticVerificationError(f"{code}_NOT_OBJECT")
    return value


def normalize_hex(value: Any, field: str, length: int | None = None) -> str:
    text = str(value or "").lower()
    if HEX_RE.fullmatch(text) is None or (length is not None and len(text) != length):
        raise SemanticVerificationError(f"{field}_INVALID_HEX")
    return text


def parse_quantity(value: Any, field: str) -> int:
    text = normalize_hex(value, field)
    try:
        return int(text, 16)
    except ValueError as exc:
        raise SemanticVerificationError(f"{field}_INVALID_QUANTITY") from exc


def word_bytes(data: str, field: str) -> list[bytes]:
    text = normalize_hex(data, field)[2:]
    if len(text) % 64 != 0:
        raise SemanticVerificationError(f"{field}_WORD_ALIGNMENT_INVALID")
    return [bytes.fromhex(text[index:index + 64]) for index in range(0, len(text), 64)]


def word_address(word: bytes, field: str) -> str:
    if len(word) != 32 or any(word[:12]):
        raise SemanticVerificationError(f"{field}_ADDRESS_PADDING_INVALID")
    result = "0x" + word[12:].hex()
    if ADDRESS_RE.fullmatch(result) is None:
        raise SemanticVerificationError(f"{field}_ADDRESS_INVALID")
    return result


def unsigned(word: bytes) -> int:
    return int.from_bytes(word, "big", signed=False)


def signed(word: bytes, bits: int, field: str) -> int:
    raw = unsigned(word)
    mask = (1 << bits) - 1
    value = raw & mask
    result = value - (1 << bits) if value & (1 << (bits - 1)) else value
    extension = raw >> bits
    expected = (1 << (256 - bits)) - 1 if result < 0 else 0
    if extension != expected:
        raise SemanticVerificationError(f"{field}_SIGN_EXTENSION_INVALID")
    return result


def dynamic_bytes(words: list[bytes], offset_word: int, field: str) -> str:
    if offset_word >= len(words):
        raise SemanticVerificationError(f"{field}_OFFSET_WORD_MISSING")
    offset = unsigned(words[offset_word])
    if offset % 32 != 0 or offset // 32 >= len(words):
        raise SemanticVerificationError(f"{field}_OFFSET_INVALID")
    start = offset // 32
    length = unsigned(words[start])
    raw = b"".join(words[start + 1:])
    if length > len(raw):
        raise SemanticVerificationError(f"{field}_LENGTH_INVALID")
    padding = raw[length:]
    if any(padding):
        raise SemanticVerificationError(f"{field}_PADDING_INVALID")
    return "0x" + raw[:length].hex()


def decode_solver_call(log: dict[str, Any]) -> dict[str, Any]:
    words = word_bytes(str(log.get("data") or ""), "SOLVER_CALL_DATA")
    if len(words) < 4:
        raise SemanticVerificationError("SOLVER_CALL_DATA_TOO_SHORT")
    return {
        "log_index": parse_quantity(log.get("logIndex"), "SOLVER_CALL_LOG_INDEX"),
        "to": word_address(words[0], "SOLVER_CALL_TO"),
        "call_data": dynamic_bytes(words, 1, "SOLVER_CALL_BYTES"),
        "native_amount_raw": str(unsigned(words[2])),
    }


def decode_funds_movement(log: dict[str, Any]) -> dict[str, Any]:
    words = word_bytes(str(log.get("data") or ""), "FUNDS_MOVEMENT_DATA")
    if len(words) < 6:
        raise SemanticVerificationError("FUNDS_MOVEMENT_DATA_TOO_SHORT")
    return {
        "log_index": parse_quantity(log.get("logIndex"), "FUNDS_MOVEMENT_LOG_INDEX"),
        "from": word_address(words[0], "FUNDS_MOVEMENT_FROM"),
        "to": word_address(words[1], "FUNDS_MOVEMENT_TO"),
        "currency": word_address(words[2], "FUNDS_MOVEMENT_CURRENCY"),
        "amount_raw": str(unsigned(words[3])),
        "metadata": dynamic_bytes(words, 4, "FUNDS_MOVEMENT_METADATA"),
    }


def decode_v4_swap(log: dict[str, Any]) -> dict[str, Any]:
    topics = log.get("topics")
    if not isinstance(topics, list) or len(topics) != 3:
        raise SemanticVerificationError("V4_SWAP_TOPICS_INVALID")
    words = word_bytes(str(log.get("data") or ""), "V4_SWAP_DATA")
    if len(words) != 6:
        raise SemanticVerificationError("V4_SWAP_DATA_WORD_COUNT_INVALID")
    sender_topic = normalize_hex(topics[2], "V4_SWAP_SENDER_TOPIC", 66)
    sender = word_address(bytes.fromhex(sender_topic[2:]), "V4_SWAP_SENDER")
    return {
        "log_index": parse_quantity(log.get("logIndex"), "V4_SWAP_LOG_INDEX"),
        "pool_id": normalize_hex(topics[1], "V4_SWAP_POOL_ID", 66),
        "sender": sender,
        "amount0_raw": str(signed(words[0], 128, "V4_SWAP_AMOUNT0")),
        "amount1_raw": str(signed(words[1], 128, "V4_SWAP_AMOUNT1")),
        "sqrt_price_x96": str(unsigned(words[2])),
        "liquidity": str(unsigned(words[3])),
        "tick": signed(words[4], 24, "V4_SWAP_TICK"),
        "fee": unsigned(words[5]),
    }


def validate_reconciliation(value: dict[str, Any]) -> None:
    if value.get("schema") != "tokenoskobi.product_slice_04.relay_pool_settlement_reconciliation.v1":
        raise SemanticVerificationError("RECONCILIATION_SCHEMA_INVALID")
    claims = value.get("canonical_claims")
    expected = {
        "settlement_transfer_ledger_reconciled": True,
        "route_verified": False,
        "cost_basis_complete": False,
        "pnl_complete": False,
        "closed_loop_confirmed": False,
        "successful_wallet_classification_ready": False,
    }
    if claims != expected:
        raise SemanticVerificationError("RECONCILIATION_CLAIMS_INVALID")
    transaction = value.get("reconciliation")
    if not isinstance(transaction, dict) or transaction.get("transaction_hash") != TARGET_TX:
        raise SemanticVerificationError("RECONCILIATION_TARGET_INVALID")


def validate_provider(value: dict[str, Any]) -> dict[str, Any]:
    rpc = value.get("rpc")
    if not isinstance(rpc, dict) or rpc.get("chain_id") != 56:
        raise SemanticVerificationError("PROVIDER_CHAIN_INVALID")
    allowed_hosts = set(rpc.get("allowed_hosts") or [])
    endpoints = []
    for item in rpc.get("endpoints") or []:
        parsed = urllib.parse.urlparse(str(item))
        if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() not in allowed_hosts:
            raise SemanticVerificationError("PROVIDER_ENDPOINT_NOT_ALLOWLISTED")
        endpoints.append(str(item).rstrip("/"))
    if not endpoints:
        raise SemanticVerificationError("PROVIDER_ENDPOINTS_EMPTY")
    return {"endpoints": endpoints, "allowed_hosts": allowed_hosts,
            "timeout": min(max(float(rpc.get("timeout_seconds", 12)), 2.0), 30.0)}


def rpc_call(provider: dict[str, Any], method: str, params: list[Any]) -> tuple[Any, str]:
    if method not in {"eth_chainId", "eth_getTransactionReceipt"}:
        raise SemanticVerificationError("RPC_METHOD_NOT_ALLOWLISTED")
    last_error = ""
    for endpoint in provider["endpoints"]:
        host = str(urllib.parse.urlparse(endpoint).hostname or "").lower()
        if host not in provider["allowed_hosts"]:
            continue
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
        request = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json",
            "User-Agent": "Tokenoskobi-Product-Slice-04/1.0 relay-v4-semantic-verification"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=provider["timeout"]) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict) or payload.get("error") is not None or "result" not in payload:
                raise SemanticVerificationError("RPC_RESPONSE_INVALID")
            return payload["result"], host
        except Exception as exc:  # endpoint failover is bounded and read-only
            last_error = type(exc).__name__
            time.sleep(0.05)
    raise SemanticVerificationError(f"RPC_ENDPOINTS_EXHAUSTED:{last_error}")


def fetch_receipt(provider_path: Path) -> tuple[dict[str, Any], str]:
    provider = validate_provider(read_object(provider_path, "PROVIDER"))
    chain_id, _ = rpc_call(provider, "eth_chainId", [])
    if parse_quantity(chain_id, "CHAIN_ID") != 56:
        raise SemanticVerificationError("RPC_CHAIN_ID_MISMATCH")
    receipt, host = rpc_call(provider, "eth_getTransactionReceipt", [TARGET_TX])
    if not isinstance(receipt, dict):
        raise SemanticVerificationError("TARGET_RECEIPT_NOT_OBJECT")
    return receipt, host


def validate_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    if normalize_hex(receipt.get("transactionHash"), "RECEIPT_TX", 66) != TARGET_TX:
        raise SemanticVerificationError("RECEIPT_TX_MISMATCH")
    if parse_quantity(receipt.get("status"), "RECEIPT_STATUS") != 1:
        raise SemanticVerificationError("RECEIPT_NOT_SUCCESSFUL")
    logs = receipt.get("logs")
    if not isinstance(logs, list) or not logs:
        raise SemanticVerificationError("RECEIPT_LOGS_INVALID")

    solver_calls: list[dict[str, Any]] = []
    funds: list[dict[str, Any]] = []
    swaps: list[dict[str, Any]] = []
    seen_indexes: set[int] = set()
    for item in logs:
        if not isinstance(item, dict):
            raise SemanticVerificationError("RECEIPT_LOG_NOT_OBJECT")
        index = parse_quantity(item.get("logIndex"), "LOG_INDEX")
        if index in seen_indexes:
            raise SemanticVerificationError("DUPLICATE_LOG_INDEX")
        seen_indexes.add(index)
        address = normalize_hex(item.get("address"), "LOG_ADDRESS", 42)
        topics = item.get("topics")
        if not isinstance(topics, list) or not topics:
            raise SemanticVerificationError("LOG_TOPICS_INVALID")
        topic0 = normalize_hex(topics[0], "LOG_TOPIC0", 66)
        if address == RELAY_V3_ROUTER and topic0 == SOLVER_CALL_EXECUTED_TOPIC:
            solver_calls.append(decode_solver_call(item))
        elif address == RELAY_V3_ROUTER and topic0 == FUNDS_MOVEMENT_TOPIC:
            funds.append(decode_funds_movement(item))
        elif address == UNISWAP_V4_POOL_MANAGER and topic0 == UNISWAP_V4_SWAP_TOPIC:
            swaps.append(decode_v4_swap(item))

    target_swaps = [row for row in swaps if row["pool_id"] == POOL_ID]
    if len(target_swaps) != 1:
        raise SemanticVerificationError(f"TARGET_V4_SWAP_COUNT_INVALID:{len(target_swaps)}")
    swap = target_swaps[0]
    if swap["sender"] != SETTLEMENT_CALLER:
        raise SemanticVerificationError("V4_SWAP_SENDER_MISMATCH")
    if int(swap["amount0_raw"]) != -POOL_OUTPUT_RAW or int(swap["amount1_raw"]) != POOL_INPUT_RAW:
        raise SemanticVerificationError("V4_SWAP_AMOUNTS_MISMATCH")
    if swap["sqrt_price_x96"] == "0" or swap["liquidity"] == "0":
        raise SemanticVerificationError("V4_SWAP_STATE_INVALID")

    caller_events = [row for row in solver_calls if row["to"] == SETTLEMENT_CALLER]
    if len(caller_events) != 1:
        raise SemanticVerificationError(f"SETTLEMENT_CALL_EVENT_COUNT_INVALID:{len(caller_events)}")
    if caller_events[0]["call_data"] == "0x":
        raise SemanticVerificationError("SETTLEMENT_CALL_DATA_EMPTY")

    expected_movements = {
        (RELAY_V3_ROUTER, SETTLEMENT_CALLER, USDC, str(POOL_INPUT_RAW)),
        (SETTLEMENT_CALLER, RELAY_V3_ROUTER, USDT, str(POOL_OUTPUT_RAW)),
    }
    actual_movements = {(row["from"], row["to"], row["currency"], row["amount_raw"]) for row in funds}
    missing = sorted(expected_movements - actual_movements)
    if missing:
        raise SemanticVerificationError("RELAY_FUNDS_MOVEMENT_LINK_MISSING")

    if not (swap["log_index"] < caller_events[0]["log_index"]):
        raise SemanticVerificationError("SOLVER_CALL_SWAP_CHRONOLOGY_INVALID")
    return {"solver_call": caller_events[0], "funds_movements": funds, "v4_swap": swap,
            "recognized_relay_event_count": len(solver_calls) + len(funds),
            "recognized_pool_manager_swap_count": len(swaps)}


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(temp, 0o600)
    json.loads(temp.read_text(encoding="utf-8"))
    temp.replace(path)
    os.chmod(path, 0o600)


def run(reconciliation_path: Path, provider_path: Path, receipt_path: Path,
        output_path: Path, *, fetch: bool) -> dict[str, Any]:
    reconciliation = read_object(reconciliation_path, "RECONCILIATION")
    validate_reconciliation(reconciliation)
    provider_host = "OFFLINE_RECEIPT"
    if fetch:
        receipt, provider_host = fetch_receipt(provider_path)
        atomic_write(receipt_path, receipt)
    else:
        receipt = read_object(receipt_path, "RECEIPT")
    decoded = validate_receipt(receipt)
    evidence = {
        "schema": "tokenoskobi.product_slice_04.relay_v4_route_semantic_verification.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "RELAY_ABI_AND_ALLOWLISTED_UNISWAP_V4_ROUTE_SEMANTICS_VERIFIED",
        "authority": dict(AUTHORITY),
        "target_transaction": TARGET_TX,
        "provider_host": provider_host,
        "receipt_hash": canonical_hash(receipt),
        "official_allowlist": OFFICIAL_ALLOWLIST,
        "decoded_evidence": decoded,
        "canonical_claims": {
            "settlement_transfer_ledger_reconciled": True,
            "relay_event_semantics_complete": True,
            "route_verified": True,
            "cost_basis_complete": False,
            "pnl_complete": False,
            "closed_loop_confirmed": False,
        },
        "next_safe_step": "PRODUCT_SLICE_04_COST_BASIS_PNL_AND_FIFO_CLOSED_LOOP_FINALIZATION",
    }
    basis = dict(evidence); basis.pop("generated_at_utc")
    evidence["result_hash"] = canonical_hash(basis)
    atomic_write(output_path, evidence)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reconciliation", type=Path, default=DEFAULT_RECONCILIATION)
    parser.add_argument("--provider", type=Path, default=DEFAULT_PROVIDER)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    try:
        result = run(args.reconciliation, args.provider, args.receipt, args.output, fetch=not args.offline)
    except SemanticVerificationError as exc:
        print(f"SEMANTIC_VERIFICATION=FAIL:{exc}")
        return 1
    print(f"OUTPUT={args.output}")
    print(f"RESULT_HASH={result['result_hash']}")
    for key, value in result["canonical_claims"].items():
        print(f"{key.upper()}={str(value).lower()}")
    print(f"NEXT_SAFE_STEP={result['next_safe_step']}")
    print("SEMANTIC_VERIFICATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
