import unittest
from unittest.mock import patch

import tokenoskobi_kernel as kernel


class KernelStateTests(unittest.TestCase):
    def test_current_owner_overrides_historical_work_unit(self):
        runtime = {
            "current_work_unit": {"id": "OLD"},
            "next_safe_step": "OLD_STEP",
            "canonical_current_state_v4": {
                "active_work_unit": "CURRENT", "active_work_stage": "REVIEW",
                "next_safe_step": "CURRENT_STEP", "last_completed": "CHECKPOINT",
            },
        }
        with patch.object(kernel, "load_json", return_value=runtime), \
                patch.object(kernel, "sh", return_value="test"):
            state = kernel.collect()["current_state"]
        self.assertEqual(state["active_work_unit"]["id"], "CURRENT")
        self.assertEqual(state["next_safe_step"], "CURRENT_STEP")

    def test_machine_inspection_does_not_generate_files(self):
        with patch.object(kernel, "ensure_kernel_graph_files") as generate, \
                patch.object(kernel, "load_json", return_value={}), \
                patch.object(kernel, "sh", return_value="test"), \
                patch.object(kernel, "inventory_summary", return_value={}):
            kernel.collect(full=True)
        generate.assert_not_called()
