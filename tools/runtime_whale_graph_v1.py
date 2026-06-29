
import dataclasses, hashlib, json, time, collections

CORE_WHALE_BTC_EQ = 50.0
SOFT_WHALE_RATIO = 0.90
WATCH_WHALE_RATIO = 0.70
SOFT_WHALE_BTC_EQ = CORE_WHALE_BTC_EQ * SOFT_WHALE_RATIO
WATCH_WHALE_BTC_EQ = CORE_WHALE_BTC_EQ * WATCH_WHALE_RATIO

MAX_GRAPH_DEPTH = 4
MAX_NODES = 64
MIN_VALUE_BTC_EQ = 0.05
MAX_GAS_TO_VALUE_RATIO = 0.10
EXCHANGE_INFLOW_WINDOW_SEC = 3600
NEWS_CORRELATION_WINDOW_SEC = 7200

KNOWN_WALLET_REGISTRY = {
    "0xcexbinance": "BINANCE_CEX",
    "0xcexcoinbase": "COINBASE_CEX",
    "0xjumpproxy": "JUMP_TRADING",
    "0xwintermute": "WINTERMUTE",
    "0xbridgehub": "BRIDGE",
    "0xmixerhub": "MIXER",
    "0xteamwallet": "TEAM_WALLET",
    "0xsniper": "SNIPER"
}

@dataclasses.dataclass(frozen=True, slots=True)
class WhaleTransfer:
    txid: str
    src: str
    dst: str
    btc_eq: float
    gas_btc_eq: float
    ts_mono_ns: int
    depth: int

def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def wallet_label(addr):
    return KNOWN_WALLET_REGISTRY.get(addr.lower(), "UNKNOWN")

def whale_tier(btc_eq, src_label="UNKNOWN", dst_label="UNKNOWN"):
    if btc_eq >= CORE_WHALE_BTC_EQ:
        return "CORE"
    if btc_eq >= SOFT_WHALE_BTC_EQ:
        return "SOFT"
    if btc_eq >= WATCH_WHALE_BTC_EQ:
        return "WATCH"
    if src_label != "UNKNOWN" or dst_label != "UNKNOWN":
        return "TRIGGER_KNOWN_WALLET"
    return "DROP"

def passes_dust_and_gas_filter(btc_eq, gas_btc_eq):
    if btc_eq < MIN_VALUE_BTC_EQ:
        return False
    if btc_eq <= 0:
        return False
    return (gas_btc_eq / btc_eq) <= MAX_GAS_TO_VALUE_RATIO

class WhaleGraphEngine:
    def __init__(self, max_depth=MAX_GRAPH_DEPTH, max_nodes=MAX_NODES):
        self.max_depth=max_depth
        self.max_nodes=max_nodes
        self.nodes=set()
        self.edges=[]
        self.dropped_dust=0
        self.dropped_depth=0
        self.dropped_nodes=0
        self.accepted=0
        self.exchange_inflows=[]
        self.raw_payload_stored=False
        self.trade_authority=False

    def add_transfer(self, txid, src, dst, btc_eq, gas_btc_eq, depth, ts_mono_ns=None):
        src=src.lower()
        dst=dst.lower()
        src_label=wallet_label(src)
        dst_label=wallet_label(dst)
        tier=whale_tier(float(btc_eq), src_label, dst_label)

        if tier == "DROP":
            self.dropped_dust += 1
            return {"accepted":False,"reason":"BELOW_THRESHOLD","tier":tier}

        if not passes_dust_and_gas_filter(float(btc_eq), float(gas_btc_eq)):
            self.dropped_dust += 1
            return {"accepted":False,"reason":"DUST_OR_GAS_RATIO_REJECTED","tier":tier}

        if depth > self.max_depth:
            self.dropped_depth += 1
            return {"accepted":False,"reason":"MAX_GRAPH_DEPTH_EXCEEDED","tier":tier}

        new_nodes={src,dst}
        if len(self.nodes | new_nodes) > self.max_nodes:
            self.dropped_nodes += 1
            return {"accepted":False,"reason":"MAX_NODES_EXCEEDED","tier":tier}

        ts = int(ts_mono_ns if ts_mono_ns is not None else time.perf_counter_ns())
        ev=WhaleTransfer(txid,src,dst,float(btc_eq),float(gas_btc_eq),ts,depth)
        self.nodes.update(new_nodes)
        self.edges.append(ev)
        self.accepted += 1

        if dst_label.endswith("_CEX") or "CEX" in dst_label:
            self.exchange_inflows.append(ev)

        return {
            "accepted":True,
            "tier":tier,
            "src_label":src_label,
            "dst_label":dst_label,
            "edge_hash":canonical_hash(dataclasses.asdict(ev))
        }

    def probability_score(self, news_hits=0, technical_confirmations=0):
        base=0.0
        if self.exchange_inflows:
            base += 0.35
        if any(e.btc_eq >= CORE_WHALE_BTC_EQ for e in self.edges):
            base += 0.25
        if len(self.edges) >= 3:
            base += 0.15
        base += min(news_hits,3) * 0.05
        base += min(technical_confirmations,3) * 0.05
        return min(round(base,4),0.99)

    def snapshot(self):
        return {
            "node_count":len(self.nodes),
            "edge_count":len(self.edges),
            "accepted":self.accepted,
            "dropped_dust":self.dropped_dust,
            "dropped_depth":self.dropped_depth,
            "dropped_nodes":self.dropped_nodes,
            "exchange_inflow_count":len(self.exchange_inflows),
            "max_depth":self.max_depth,
            "max_nodes":self.max_nodes,
            "raw_payload_stored":self.raw_payload_stored,
            "trade_authority":self.trade_authority
        }
