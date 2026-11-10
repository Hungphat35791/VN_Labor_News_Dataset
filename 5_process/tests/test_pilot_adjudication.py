from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
SPEC = importlib.util.spec_from_file_location(
    "pilot_adjudication", SRC / "prepare_pilot_adjudication.py"
)
pilot_adjudication = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pilot_adjudication
SPEC.loader.exec_module(pilot_adjudication)


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=pilot_adjudication.FORM_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _case() -> dict[str, str]:
    return {
        "article_id": "A1",
        "title": "Article",
        "reviewer_1_relevance": "Relevant",
        "reviewer_1_topic": "A — Thị trường lao động Việt Nam",
        "reviewer_1_reason": "Evidence from the article.",
        "reviewer_1_id": "R1",
        "reviewer_1_date": "2026-03-01",
        "reviewer_2_relevance": "Borderline",
        "reviewer_2_topic": "A — Thị trường lao động Việt Nam",
        "reviewer_2_reason": "Independent evidence.",
        "reviewer_2_id": "R2",
        "reviewer_2_date": "2026-03-02",
        "disagreement_type": "RELEVANCE_DISAGREEMENT",
        "adjudication_status": "PENDING",
        "final_relevance": "",
        "final_topic": "",
        "adjudication_reason": "",
        "adjudicator_id": "",
        "adjudication_date": "",
    }


class TestPilotAdjudication(unittest.TestCase):
    def test_prepare_and_validate_empty_queue_creates_no_decision(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queue, form = root / "queue.csv", root / "form.csv"
            reviewer_1, reviewer_2 = root / "r1.csv", root / "r2.csv"
            report = root / "report.json"
            _write(queue, [])
            reviewer_1.write_text("reviewer 1", encoding="utf-8")
            reviewer_2.write_text("reviewer 2", encoding="utf-8")
            (root / "reviewer_1_sheet.csv").write_text("r1", encoding="utf-8")
            (root / "reviewer_2_sheet.csv").write_text("r2", encoding="utf-8")
            with (
                patch.object(pilot_adjudication, "QUEUE", queue),
                patch.object(pilot_adjudication, "FORM", form),
                patch.object(pilot_adjudication, "REPORT", report),
                patch.object(pilot_adjudication, "PILOT_DIR", root),
            ):
                pilot_adjudication.prepare_form()
                result = pilot_adjudication.validate_form()
            self.assertEqual(result["queue_case_count"], 0)
            self.assertFalse(any(form.read_text(encoding="utf-8-sig").splitlines()[1:]))

    def test_final_decision_requires_valid_provenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queue, form = root / "queue.csv", root / "form.csv"
            row = _case()
            _write(queue, [row])
            row.update(
                {
                    "adjudication_status": "ADJUDICATED",
                    "final_relevance": "Relevant",
                    "final_topic": "A — Thị trường lao động Việt Nam",
                    "adjudication_reason": "Final rationale.",
                    "adjudicator_id": "",
                    "adjudication_date": "2026-03-03",
                }
            )
            _write(form, [row])
            with (
                patch.object(pilot_adjudication, "QUEUE", queue),
                patch.object(pilot_adjudication, "FORM", form),
                patch.object(pilot_adjudication, "PILOT_DIR", root),
            ):
                with self.assertRaisesRegex(ValueError, "requires reason, adjudicator ID and date"):
                    pilot_adjudication.validate_form()

    def test_only_queued_cases_and_immutable_reviews_are_accepted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queue, form = root / "queue.csv", root / "form.csv"
            source = _case()
            changed = dict(source)
            changed["reviewer_1_relevance"] = "Not relevant"
            _write(queue, [source])
            _write(form, [changed])
            with (
                patch.object(pilot_adjudication, "QUEUE", queue),
                patch.object(pilot_adjudication, "FORM", form),
            ):
                with self.assertRaisesRegex(ValueError, "immutable reviewer/source field"):
                    pilot_adjudication.validate_form()

    def test_relevant_case_requires_a_valid_topic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queue, form = root / "queue.csv", root / "form.csv"
            source = _case()
            _write(queue, [source])
            source.update(
                {
                    "adjudication_status": "ADJUDICATED",
                    "final_relevance": "Relevant",
                    "final_topic": "P4.06: WAGES",
                    "adjudication_reason": "Final rationale.",
                    "adjudicator_id": "ADJ1",
                    "adjudication_date": "2026-03-03",
                }
            )
            _write(form, [source])
            with (
                patch.object(pilot_adjudication, "QUEUE", queue),
                patch.object(pilot_adjudication, "FORM", form),
                patch.object(pilot_adjudication, "PILOT_DIR", root),
            ):
                with self.assertRaisesRegex(ValueError, "valid A-L topic"):
                    pilot_adjudication.validate_form()


if __name__ == "__main__":
    unittest.main()
