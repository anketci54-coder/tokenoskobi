
import dataclasses, hashlib, json, time

NOAPI = True
READ_ONLY = True
DB_WRITE = False
PACKET_EMIT = False
LIVE_TRADE = False
WALLET = False

ALLOWED_METHODS = {
    "eth_blockNumber",
    "eth_getLogs",
    "eth_getBlockByNumber",
    "eth_getTransactionReceipt"
}

FORBIDDEN_METHOD_PREFIXES = (
    "eth_send",
    "personal_",
    "wallet_",
    "debug_",
    "miner_",
    "admin_"
)

@dataclasses.dataclass(frozen=True, slots=True)
class RPCShadowRequest:
    provider: str
    chain: str
    method: str
    params_hash: str
    ts_mono_ns: int

@dataclasses.dataclass(frozen=True, slots=True)
class RPCShadowResult:
    accepted: bool
    reason: str
    provider: str
    chain: str
    method: str
    request_hash: str

def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def validate_method(method):
    if not isinstance(method,str):
        return False
    if method not in ALLOWED_METHODS:
        return False
    if any(method.startswith(p) for p in FORBIDDEN_METHOD_PREFIXES):
        return False
    return True

class ReadOnlyRPCShadowIntake:
    def __init__(self):
        self.accepted=0
        self.rejected=0
        self.api_call_count=0
        self.packet_emit_count=0
        self.db_write_count=0
        self.raw_payload_stored=False

    def prepare_request(self, provider, chain, method, params):
        if not validate_method(method):
            self.rejected += 1
            return RPCShadowResult(False,"METHOD_REJECTED",provider,chain,str(method),"")
        params_hash=canonical_hash(params)
        req=RPCShadowRequest(provider,chain,method,params_hash,time.perf_counter_ns())
        request_hash=canonical_hash(dataclasses.asdict(req))
        self.accepted += 1
        return RPCShadowResult(True,"READ_ONLY_SHADOW_ACCEPTED",provider,chain,method,request_hash)

    def snapshot(self):
        return {
            "accepted":self.accepted,
            "rejected":self.rejected,
            "api_call_count":self.api_call_count,
            "packet_emit_count":self.packet_emit_count,
            "db_write_count":self.db_write_count,
            "raw_payload_stored":self.raw_payload_stored
        }
