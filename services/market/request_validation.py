"""Validate request authority against configuration, never against client claims."""
import re
from urllib.parse import urlsplit


def parse_origin(value):
    """Accept a serialized HTTP(S) origin, without userinfo or URL components."""
    if not isinstance(value, str) or not re.fullmatch(
        r"https?://[A-Za-z0-9.-]+(?::[0-9]{1,5})?", value
    ):
        raise ValueError("INVALID_ORIGIN")
    parsed = urlsplit(value)
    if not parsed.hostname or parsed.port == 0:
        raise ValueError("INVALID_ORIGIN")
    return parsed.scheme, parsed.hostname.lower(), parsed.port or (443 if parsed.scheme == "https" else 80)


def single_header(headers, name):
    values = headers.get_all(name, []) if hasattr(headers, "get_all") else (
        [headers[name]] if name in headers else []
    )
    if len(values) > 1:
        raise ValueError("DUPLICATE_SECURITY_HEADER")
    return values[0] if values else None


def validate_request_headers(headers, config):
    origins = [parse_origin(f"http://{host}:{config['port']}")
               for host in (config["host"], "localhost")]
    origins.extend(parse_origin(value) for value in config.get("trusted_origins", []))
    # Host has no scheme: compare it to each independently trusted authority.
    authorities = set()
    for scheme, host, port in origins:
        authorities.add(f"{host}:{port}")
        if port == (443 if scheme == "https" else 80):
            authorities.add(host)
    host = single_header(headers, "Host")
    if not isinstance(host, str) or host.lower() not in authorities:
        raise ValueError("UNTRUSTED_HOST")
    origin = single_header(headers, "Origin")
    if origin is not None:
        try:
            parsed = parse_origin(origin)
            same_host = parse_origin(f"{parsed[0]}://{host}")[1:] == parsed[1:]
        except ValueError as exc:
            raise ValueError("CROSS_ORIGIN_REQUEST_REJECTED") from exc
        if parsed not in origins or not same_host:
            raise ValueError("CROSS_ORIGIN_REQUEST_REJECTED")


def validate_json_headers(headers, config):
    validate_request_headers(headers, config)
    if headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise ValueError("JSON_CONTENT_TYPE_REQUIRED")
    if headers.get("Transfer-Encoding"):
        raise ValueError("TRANSFER_ENCODING_UNSUPPORTED")
