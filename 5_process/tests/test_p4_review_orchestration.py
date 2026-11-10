from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
SPEC = importlib.util.spec_from_file_location(
    "p4_review_orchestration", SRC / "run_p4_review_workflow.py"
)
workflow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = workflow
SPEC.loader.exec_module(workflow)


class TestP4ReviewOrchestration(unittest.TestCase):
    def test_evaluator_non_json_summary_is_parsed_as_a_status(self):
        completed = SimpleNamespace(
            returncode=0,
            stdout="P4.09 status=WAITING_FOR_GOLD_LABELS; JSON: report.json",
            stderr="",
        )
        with patch.object(workflow.subprocess, "run", return_value=completed):
            step = workflow._run("evaluation", ["evaluate.py"])
        self.assertEqual(step["status"], "SUCCEEDED")
        self.assertEqual(step["result"]["status"], "WAITING_FOR_GOLD_LABELS")

    def test_csv_data_detection_distinguishes_header_only_from_submissions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sheet.csv"
            path.write_text("article_id,label\n", encoding="utf-8")
            self.assertFalse(workflow._csv_has_data(path))
            path.write_text("article_id,label\nA1,Relevant\n", encoding="utf-8")
            self.assertTrue(workflow._csv_has_data(path))

    def test_finish_blocks_if_a_protected_input_changed_during_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reviewer_sheet = root / "reviewer.csv"
            reviewer_sheet.write_text("original", encoding="utf-8")
            report_path = root / "status.json"
            with (
                patch.object(workflow, "REVIEWER_INPUTS", {"reviewer": reviewer_sheet}),
                patch.object(workflow, "REPORTS", root),
                patch.object(workflow, "STATUS_REPORT", report_path),
                patch.object(workflow, "GOLD", root / "gold.csv"),
            ):
                result = workflow._finish(
                    [],
                    {"reviewer": "0" * 64},
                    {},
                    "WAITING_FOR_GOLD_LABELS",
                )
            saved = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("reviewer", saved["protected_inputs_changed_during_run"])

    def test_finish_records_new_reviewer_input_and_refresh_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reviewer_sheet = root / "reviewer.csv"
            reviewer_sheet.write_text("article_id,label\nA1,Relevant\n", encoding="utf-8")
            report_path = root / "status.json"
            with (
                patch.object(workflow, "REVIEWER_INPUTS", {"reviewer": reviewer_sheet}),
                patch.object(workflow, "REPORTS", root),
                patch.object(workflow, "STATUS_REPORT", report_path),
                patch.object(workflow, "GOLD", root / "gold.csv"),
            ):
                result = workflow._finish(
                    [],
                    {"reviewer": workflow._sha256(reviewer_sheet)},
                    {"reviewer": "0" * 64},
                    "WAITING_FOR_GOLD_LABELS",
                )
            saved = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "WAITING_FOR_GOLD_LABELS")
        self.assertTrue(saved["changed_since_previous_run"]["reviewer"])
        self.assertEqual(saved["protected_inputs_changed_during_run"], {})


if __name__ == "__main__":
    unittest.main()
