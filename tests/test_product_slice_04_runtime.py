import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if "fcntl" not in sys.modules:
    fcntl = types.ModuleType("fcntl")
    fcntl.LOCK_SH, fcntl.LOCK_EX, fcntl.LOCK_UN = 1, 2, 8
    fcntl.flock = lambda *_args: None
    sys.modules["fcntl"] = fcntl
os.environ["TOKENOSKOBI_ROOT"] = str(REPO)
os.environ["TOKENOSKOBI_SLICE03_RUNTIME_PATH"] = str(REPO / "tools/tokenoskobi_product_slice_03_runtime.py")
os.environ["TOKENOSKOBI_SLICE03_CORE_PATH"] = str(REPO / "tools/tokenoskobi_product_slice_03_server.py")
os.environ["TOKENOSKOBI_SLICE02_SERVER_PATH"] = str(REPO / "tools/tokenoskobi_product_slice_02_server.py")
os.environ["TOKENOSKOBI_SLICE04_CHECKPOINT_PATH"] = str(REPO / "data/control/product_slice_04_closed_loop_checkpoint_v1.json")
os.environ.setdefault("TOKENOSKOBI_SLICE03_STATE_DIR", tempfile.mkdtemp())
os.environ.setdefault("TOKENOSKOBI_GT_RATE_DIR", tempfile.mkdtemp())
SPEC = importlib.util.spec_from_file_location("slice04", REPO / "tools/tokenoskobi_product_slice_04_runtime.py")
assert SPEC and SPEC.loader
S04 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S04)


class Slice04RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        S04.GRAPH_PATH = Path(self.temp.name) / "graph.json"

    def tearDown(self):
        self.temp.cleanup()

    def test_graph_is_deterministic_persisted_and_evidence_linked(self):
        first = S04.persist_graph()
        second = S04.persist_graph()
        self.assertEqual(first, second)
        self.assertEqual(json.loads(S04.GRAPH_PATH.read_text()), first)
        self.assertEqual(first["graph_hash"], S04.digest({k: v for k, v in first.items() if k != "graph_hash"}))
        node_ids = {node["id"] for node in first["nodes"]}
        for edge in first["edges"]:
            self.assertIn(edge["from"], node_ids)
            self.assertIn(edge["to"], node_ids)
            if "evidence" in edge:
                self.assertIn(edge["evidence"], node_ids)

    def test_graph_read_endpoint_requires_existing_persistence(self):
        self.assertFalse(S04.GRAPH_PATH.exists())
        with self.assertRaisesRegex(S04.CORE.HistoryCorruption, "EVIDENCE_GRAPH_MISSING"):
            S04.read_graph()
        self.assertFalse(S04.GRAPH_PATH.exists())
        persisted = S04.persist_graph()
        self.assertEqual(S04.read_graph(), persisted)

    def test_existing_graph_mutation_fails_closed(self):
        S04.persist_graph()
        altered = json.loads(S04.GRAPH_PATH.read_text())
        altered["nodes"][0]["label"] = "tampered"
        S04.GRAPH_PATH.write_text(json.dumps(altered), encoding="utf-8")
        with self.assertRaisesRegex(S04.CORE.HistoryCorruption, "IMMUTABILITY"):
            S04.persist_graph()

    def test_authority_remains_zero_and_mobile_panel_is_bound(self):
        self.assertTrue(all(S04.AUTHORITY[key] is False for key in ("paper", "live", "wallet", "signing", "order", "broadcast")))
        self.assertIn("/api/v1/evidence-graph", S04.GRAPH_PANEL)
        self.assertIn("@media(max-width:700px)", S04.HTML)
        self.assertIn("Kanıt Grafiği", S04.HTML)


    def test_panel_loader_is_self_contained_and_dom_ready(self):
        source = (REPO / "tools/tokenoskobi_product_slice_04_runtime.py").read_text(encoding="utf-8")
        self.assertIn("return self.send_json(200, read_graph())", source)
        self.assertIn("DOMContentLoaded", S04.GRAPH_PANEL)
        self.assertIn("fetch('/api/v1/evidence-graph'", S04.GRAPH_PANEL)
        self.assertIn("slice04Esc", S04.GRAPH_PANEL)
        self.assertNotIn("await api('/api/v1/evidence-graph')", S04.GRAPH_PANEL)
        self.assertNotIn("esc(n.kind)", S04.GRAPH_PANEL)

    def test_systemd_draft_binds_slice04_runtime_without_losing_slice03_state(self):
        unit = (REPO / "systemd_drafts/tokenoskobi-product-slice-02.service").read_text(encoding="utf-8")
        self.assertIn("ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_04_runtime.py", unit)
        self.assertIn("StateDirectory=tokenoskobi-product-slice-03 tokenoskobi-product-slice-04", unit)
        self.assertIn("TOKENOSKOBI_SLICE03_STATE_DIR=/var/lib/tokenoskobi-product-slice-03", unit)
        self.assertIn("TOKENOSKOBI_SLICE04_GRAPH_PATH=/var/lib/tokenoskobi-product-slice-04/evidence_graph_v1.json", unit)
        self.assertIn("ReadOnlyPaths=/root/tokenoskobi_clean_v1", unit)
        self.assertIn("ProtectSystem=strict", unit)


if __name__ == "__main__":
    unittest.main()
