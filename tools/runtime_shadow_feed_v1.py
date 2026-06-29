
import collections, dataclasses, hashlib, json, time

MAX_RAW_BYTES = 4096
MAX_JSON_DEPTH = 16

@dataclasses.dataclass(frozen=True, slots=True)
class ShadowFeedEvent:
    event_id: str
    source: str
    chain: str
    token_address: str
    payload_hash: str
    raw_size_bytes: int
    received_mono_ns: int

class ShadowFeedRejected(Exception):
    pass

def _json_depth_raw(s: str) -> int:
    depth = 0
    max_depth = 0
    in_string = False
    escape = False
    for ch in s:
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "{[":
            depth += 1
            if depth > max_depth:
                max_depth = depth
        elif ch in "}]":
            depth -= 1
            if depth < 0:
                raise ShadowFeedRejected("INVALID_JSON_DEPTH")
    return max_depth

def canonical_hash(obj) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(b).hexdigest()

class ShadowFeedQueue:
    def __init__(self, maxlen=128):
        self.queue = collections.deque(maxlen=maxlen)
        self.accepted = 0
        self.rejected = 0
        self.dropped = 0
        self.raw_payload_stored = False
    def ingest_raw(self, raw: str):
        if not isinstance(raw, str):
            self.rejected += 1
            raise ShadowFeedRejected("RAW_NOT_STRING")
        raw_size = len(raw.encode("utf-8"))
        if raw_size > MAX_RAW_BYTES:
            self.rejected += 1
            raise ShadowFeedRejected("RAW_TOO_LARGE")
        if _json_depth_raw(raw) > MAX_JSON_DEPTH:
            self.rejected += 1
            raise ShadowFeedRejected("RAW_TOO_DEEP")
        try:
            obj = json.loads(raw)
        except Exception as e:
            self.rejected += 1
            raise ShadowFeedRejected("RAW_JSON_INVALID") from e
        for key in ("source","chain","token_address"):
            if key not in obj or not isinstance(obj[key], str):
                self.rejected += 1
                raise ShadowFeedRejected("REQUIRED_FIELD_INVALID")
        payload_hash = canonical_hash(obj)
        event_id = hashlib.sha256(("shadow:"+payload_hash).encode()).hexdigest()
        event = ShadowFeedEvent(
            event_id=event_id,
            source=obj["source"],
            chain=obj["chain"],
            token_address=obj["token_address"].lower(),
            payload_hash=payload_hash,
            raw_size_bytes=raw_size,
            received_mono_ns=time.perf_counter_ns()
        )
        before_len=len(self.queue)
        self.queue.append(event)
        if len(self.queue) == before_len and before_len == self.queue.maxlen:
            self.dropped += 1
        self.accepted += 1
        return event
    def depth(self):
        return len(self.queue)
    def maxlen(self):
        return self.queue.maxlen
    def snapshot(self):
        return {
            "queue_depth": len(self.queue),
            "queue_maxlen": self.queue.maxlen,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "dropped": self.dropped,
            "raw_payload_stored": self.raw_payload_stored
        }
