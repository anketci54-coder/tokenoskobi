"""Validate the product's configuration before accepting any requests."""
import math
from urllib.parse import urlsplit

from services.market.request_validation import parse_origin

FINANCIAL_AUTHORITIES = ("paper", "live", "wallet", "signing", "order", "broadcast")


def validate_config(value):
    if not isinstance(value, dict):
        raise ValueError("CONFIG_OBJECT_REQUIRED")
    if value.get("host") != "127.0.0.1":
        raise ValueError("CONFIG_HOST_MUST_BE_LOOPBACK")
    port = value.get("port")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("CONFIG_PORT_INVALID")
    if type(value.get("chain_id")) is not int or value["chain_id"] != 56:
        raise ValueError("CONFIG_CHAIN_MUST_BE_BSC")
    for key in ("timeout_sec", "news_stale_sec"):
        number = value.get(key)
        if type(number) not in (int, float) or not math.isfinite(number) or number <= 0:
            raise ValueError(f"CONFIG_{key.upper()}_INVALID")
    authority = value.get("authority")
    if not isinstance(authority, dict) or any(
        authority.get(key) is not False for key in FINANCIAL_AUTHORITIES
    ):
        raise ValueError("CONFIG_FINANCIAL_AUTHORITY_MUST_BE_DISABLED")
    rpc = value.get("rpc")
    if not isinstance(rpc, list) or not rpc:
        raise ValueError("CONFIG_RPC_REQUIRED")
    for endpoint in rpc:
        if not isinstance(endpoint, str):
            raise ValueError("CONFIG_RPC_URL_INVALID")
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("CONFIG_RPC_HTTPS_URL_REQUIRED")
    origins = value.get("trusted_origins", [])
    if not isinstance(origins, list):
        raise ValueError("CONFIG_TRUSTED_ORIGINS_INVALID")
    for origin in origins:
        try:
            parse_origin(origin)
        except ValueError as exc:
            raise ValueError("CONFIG_TRUSTED_ORIGINS_INVALID") from exc
    return value
