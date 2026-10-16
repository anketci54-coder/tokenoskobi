"""Reject browser form submissions and cross-origin writes to the local panel."""
from urllib.parse import urlsplit


def validate_json_headers(headers):
    if headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise ValueError("JSON_CONTENT_TYPE_REQUIRED")
    if headers.get("Transfer-Encoding"):
        raise ValueError("TRANSFER_ENCODING_UNSUPPORTED")
    origin = headers.get("Origin")
    if origin is not None:
        parsed = urlsplit(origin)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or \
                parsed.netloc.lower() != headers.get("Host", "").lower():
            raise ValueError("CROSS_ORIGIN_REQUEST_REJECTED")
