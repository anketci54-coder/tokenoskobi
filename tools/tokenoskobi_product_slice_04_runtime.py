#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(os.getenv("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1"))
SLICE03_PATH = Path(os.getenv("TOKENOSKOBI_SLICE03_RUNTIME_PATH", ROOT / "tools/tokenoskobi_product_slice_03_runtime.py"))
CHECKPOINT_PATH = Path(os.getenv("TOKENOSKOBI_SLICE04_CHECKPOINT_PATH", ROOT / "data/control/product_slice_04_closed_loop_checkpoint_v1.json"))
GRAPH_PATH = Path(os.getenv("TOKENOSKOBI_SLICE04_GRAPH_PATH", "/var/lib/tokenoskobi-product-slice-04/evidence_graph_v1.json"))

SPEC = importlib.util.spec_from_file_location("tokenoskobi_product_slice_03_runtime", SLICE03_PATH)
if not SPEC or not SPEC.loader:
    raise RuntimeError("PRODUCT_SLICE_03_RUNTIME_IMPORT_FAILED")
SLICE03 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SLICE03)
CORE = SLICE03.CORE


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_checkpoint() -> dict[str, Any]:
    value = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    required = (
        value.get("schema") == "tokenoskobi.product_slice_04.closed_loop_checkpoint.v1",
        value.get("closed_loop_confirmed") is True,
        value.get("transaction_success") is True,
        value.get("product_slice_04_closed") is False,
    )
    if not all(required):
        raise CORE.HistoryCorruption("SLICE04_CHECKPOINT_INVALID")
    return value


def build_graph(checkpoint: dict[str, Any]) -> dict[str, Any]:
    flow = checkpoint["economic_flow"]
    tx = checkpoint["transaction_hash"].lower()
    nodes = [
        {"id": "wallet:user", "kind": "WALLET", "label": "User wallet", "identity_claim": "UNATTRIBUTED"},
        {"id": f"tx:{tx}", "kind": "TRANSACTION", "label": tx[:12] + "...", "success": True},
        {"id": "router:relay", "kind": "ROUTER", "label": "Relay router", "net_delta": flow["relay_router_net_delta"]},
        {"id": "pool:verified", "kind": "POOL", "label": "Verified swap pool"},
        {"id": "token:usdc", "kind": "TOKEN", "label": "USDC"},
        {"id": "token:usdt", "kind": "TOKEN", "label": "USDT"},
        {"id": "evidence:checkpoint", "kind": "EVIDENCE", "label": "Closed-loop checkpoint", "result_hash": checkpoint["result_hash"]},
    ]
    edges = [
        {"from": "wallet:user", "to": f"tx:{tx}", "relation": "SUBMITTED", "evidence": "evidence:checkpoint"},
        {"from": f"tx:{tx}", "to": "router:relay", "relation": "ROUTED_BY", "evidence": "evidence:checkpoint"},
        {"from": "token:usdc", "to": "router:relay", "relation": "INPUT", "amount": flow["swap_input"]["amount"], "evidence": "evidence:checkpoint"},
        {"from": "router:relay", "to": "pool:verified", "relation": "SWAP", "evidence": "evidence:checkpoint"},
        {"from": "pool:verified", "to": "token:usdt", "relation": "OUTPUT", "amount": flow["user_output"]["amount"], "evidence": "evidence:checkpoint"},
        {"from": "evidence:checkpoint", "to": f"tx:{tx}", "relation": "PROVES"},
    ]
    graph = {
        "schema": "tokenoskobi.product_slice_04.evidence_graph.v1",
        "source_checkpoint_hash": checkpoint["result_hash"],
        "transaction_hash": tx,
        "nodes": nodes,
        "edges": edges,
        "uncertainty": ["WALLET_IDENTITY_UNATTRIBUTED", "CEX_ENTITY_NOT_ASSERTED_FOR_THIS_TRANSACTION"],
        "authority": {"paper": False, "live": False, "wallet": False, "signing": False, "order": False, "broadcast": False},
    }
    graph["graph_hash"] = digest(graph)
    return graph


def persist_graph() -> dict[str, Any]:
    graph = build_graph(load_checkpoint())
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if GRAPH_PATH.exists():
        existing = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
        if existing != graph:
            raise CORE.HistoryCorruption("EVIDENCE_GRAPH_IMMUTABILITY_VIOLATION")
        return existing
    descriptor, temporary = tempfile.mkstemp(prefix=".evidence_graph_", dir=GRAPH_PATH.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes(graph) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, GRAPH_PATH)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return graph


def read_graph() -> dict[str, Any]:
    if not GRAPH_PATH.is_file():
        raise CORE.HistoryCorruption("EVIDENCE_GRAPH_MISSING")
    try:
        existing = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CORE.HistoryCorruption("EVIDENCE_GRAPH_INVALID") from exc
    expected = build_graph(load_checkpoint())
    if existing != expected:
        raise CORE.HistoryCorruption("EVIDENCE_GRAPH_IMMUTABILITY_VIOLATION")
    return existing


GRAPH_PANEL = """<section class=\"box\"><div class=\"row\"><h3>Kanıt Grafiği</h3><button onclick=\"loadGraph()\">Yenile</button></div><p class=\"muted\">Gerçek closed-loop işleminden, değişmez checkpoint kanıtıyla üretilir. Kimlik iddiası yapılmaz.</p><div id=\"evidenceGraph\" class=\"graph\">Yükleniyor…</div></section><style>.graph{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px}.node{border:1px solid #486681;border-radius:999px;padding:14px;text-align:center;background:#0b131c}.edge{font-size:12px;color:#9fc8ed;padding:4px;word-break:break-word}@media(max-width:700px){.graph{grid-template-columns:1fr}.node{border-radius:14px}}</style><script>function slice04Esc(value){return String(value==null?'':value).replace(/[&<>\"']/g,function(char){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[char]})}async function loadGraph(){let el=document.getElementById('evidenceGraph');if(!el)return;try{let response=await fetch('/api/v1/evidence-graph',{cache:'no-store'}),d=await response.json();if(!response.ok)throw new Error(d.error||'EVIDENCE_GRAPH_LOAD_FAILED');let nodes=d.nodes||[],edges=d.edges||[];el.innerHTML=nodes.map(n=>'<div class=\"node\"><b>'+slice04Esc(n.kind)+'</b><br>'+slice04Esc(n.label)+'</div>').join('')+'<div style=\"grid-column:1/-1\">'+edges.map(e=>'<div class=\"edge\">'+slice04Esc(e.from)+' → '+slice04Esc(e.relation)+' → '+slice04Esc(e.to)+(e.amount?' · '+slice04Esc(e.amount):'')+'</div>').join('')+'</div>'}catch(e){el.textContent=e.message||'EVIDENCE_GRAPH_LOAD_FAILED'}}if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',loadGraph,{once:true})}else{loadGraph()}</script>"""
HTML = CORE.HTML.replace("</main><script>", GRAPH_PANEL + "</main><script>")


class Handler(SLICE03.Handler):
    def do_GET(self) -> None:
        path = CORE.urllib.parse.urlsplit(self.path).path
        try:
            if path == "/api/v1/evidence-graph":
                return self.send_json(200, read_graph())
            if path in ("/", "/panel", "/panel/", "/panel/panel_v2", "/panel/panel_v2/"):
                return self.send_json(200, HTML, "text/html; charset=utf-8")
            return super().do_GET()
        except Exception as exc:
            self.handle_error(exc)


AUTHORITY = SLICE03.AUTHORITY
if __name__ == "__main__":
    assert CORE.CFG["host"] == "127.0.0.1"
    assert all(AUTHORITY[key] is False for key in ("paper", "live", "wallet", "signing", "order", "broadcast"))
    persist_graph()
    ThreadingHTTPServer((CORE.CFG["host"], CORE.CFG["port"]), Handler).serve_forever()
