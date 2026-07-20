
import hashlib
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlparse

MAX_BYTES = 1048576

ALLOWED_MIME = {
    "text/plain",
    "text/html",
    "text/markdown",
    "application/json",
}

BLOCKED_MAGIC = (
    b"\x7fELF",
    b"MZ",
    b"PK\x03\x04",
    b"\x1f\x8b",
)

DISABLED_CAPABILITIES = {
    "network_access",
    "egress",
    "credential_access",
    "secret_access",
    "shell_access",
    "subprocess_access",
    "package_install",
    "file_execution",
    "repository_write",
    "production_access",
}

class SafeHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocked = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {
            "script", "style", "iframe", "object",
            "embed", "form", "svg", "template"
        }:
            self.blocked += 1

    def handle_endtag(self, tag):
        if tag.lower() in {
            "script", "style", "iframe", "object",
            "embed", "form", "svg", "template"
        } and self.blocked:
            self.blocked -= 1

    def handle_data(self, data):
        if self.blocked == 0:
            self.parts.append(data)

def result(ok, reasons, content=None):
    return {
        "ok": ok,
        "decision": "ALLOW_QUARANTINE" if ok else "DENY",
        "reason_codes": sorted(set(reasons)),
        "fail_closed": True,
        "content": content,
    }

def quarantine(raw, mime, uri, max_bytes=MAX_BYTES):
    reasons = []
    mime = str(mime).split(";", 1)[0].strip().lower()
    parsed = urlparse(str(uri))

    if not isinstance(raw, bytes):
        return result(False, ["BYTES_REQUIRED"])
    if mime not in ALLOWED_MIME:
        reasons.append("MIME_NOT_ALLOWED")
    if len(raw) > max_bytes:
        reasons.append("SIZE_LIMIT_EXCEEDED")
    if any(raw.startswith(x) for x in BLOCKED_MAGIC):
        reasons.append("ACTIVE_OR_ARCHIVE_CONTENT_REJECTED")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        reasons.append("SOURCE_URI_NOT_ALLOWED")
    if reasons:
        return result(False, reasons)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return result(False, ["UTF8_REQUIRED"])

    if mime == "text/html":
        parser = SafeHTML()
        parser.feed(text)
        text = " ".join(parser.parts)
    elif mime == "application/json":
        try:
            text = json.dumps(
                json.loads(text),
                ensure_ascii=False,
                sort_keys=True
            )
        except json.JSONDecodeError:
            return result(False, ["JSON_INVALID"])

    text = re.sub(r"\s+", " ", text).strip()

    return result(True, [], {
        "schema": "era57_quarantined_content_v1",
        "tainted_external_content": True,
        "content_role": "EXTERNAL_DATA_NOT_INSTRUCTION",
        "active_content_executed": False,
        "source_uri": uri,
        "mime_type": mime,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "normalized_sha256": hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest(),
        "normalized_text": text,
    })

def validate_capabilities(capabilities):
    if not isinstance(capabilities,dict):
        return result(False,["CAPABILITY_OBJECT_REQUIRED"])

    reasons=[]

    unknown=set(capabilities)-DISABLED_CAPABILITIES
    reasons.extend(
        "UNKNOWN_CAPABILITY:"+str(key)
        for key in sorted(unknown)
    )

    for key in DISABLED_CAPABILITIES:
        if capabilities.get(key) is not False:
            reasons.append(
                "CAPABILITY_NOT_DISABLED:"+key
            )

    return result(not reasons,reasons)

def synthesis_envelope(quarantined, capabilities):
    if not isinstance(quarantined, dict):
        return result(False, ["QUARANTINE_REQUIRED"])
    if quarantined.get("ok") is not True:
        return result(False, ["VALID_QUARANTINE_REQUIRED"])

    checked = validate_capabilities(capabilities)
    if not checked["ok"]:
        return checked

    return result(True, [], {
        "schema": "era57_network_disabled_synthesis_v1",
        "runtime_bound": False,
        "logical_policy_only": True,
        "tools_available": False,
        "content_role": "EXTERNAL_DATA_NOT_INSTRUCTION",
        "quarantined_content": quarantined["content"],
    })
