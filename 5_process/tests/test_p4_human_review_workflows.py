from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SRC / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load("p4_human_review_validator", "validate_p4_human_review.py")
adjudication = _load("p4_human_adjudication", "prepare_human_adjudication.py")
pilot = _load("pilot_10_validator", "validate_pilot_10.py")


def _write_csv(path: Path, columns: tuple[str, ...] | list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _p406_row(article_id: str, reviewer: str, status: str = "COMPLETED") -> dict[str, str]:
    return {
        "article_id": article_id,
        "title": f"Title {article_id}",
        "content": f"Content {article_id}",
        "gold_relevance_status": "RELEVANT",
        "gold_topic_labels_p406": json.dumps(["WAGES"]),
        "review_reason": f"Human evidence from {reviewer}.",
        "reviewer_id": reviewer,
        "review_date": "2026-03-01",
        "annotation_status": status,
    }


def _p406_queue_row(article_id: str, **updates: str) -> dict[str, str]:
    row = {column: "" for column in validator.P406_QUEUE_COLUMNS}
    row.update(
        {
            "article_id": article_id,
            "adjudication_status": "PENDING",
        }
    )
    row.update(updates)
    return row


def _duplicate_queue_row() -> dict[str, str]:
    row = {column: "" for column in validator.DUPLICATE_QUEUE_COLUMNS}
    row.update(
        {
            "group_id": "G1",
            "article_id_1": "A1",
            "article_id_2": "A2",
            "adjudication_status": "PENDING",
        }
    )
    return row


class TestCalibrationValidation(unittest.TestCase):
    def test_policy_cases_are_not_forced_into_correct_or_incorrect(self):
        key = {
            "CAL-03": {
                "relevance": "Relevant",
                "topic": "No single primary topic specified; B and C compete",
                "status": "NEEDS_CLARIFICATION",
            },
            "CAL-09": {
                "relevance": "No final reference label",
                "topic": "No final topic",
                "status": "NEEDS_ADJUDICATION",
            },
        }
        rows = [
            {"scenario_id": "CAL-03", "relevance_manual": "Relevant", "topic_manual": "B"},
            {"scenario_id": "CAL-09", "relevance_manual": "Uncertain", "topic_manual": ""},
        ]
        result = validator._score_calibration(rows, key)
        self.assertEqual(
            [row["assessment"] for row in result["scenario_results"]],
            ["NEEDS_CLARIFICATION", "NEEDS_ADJUDICATION"],
        )

    def test_not_relevant_and_uncertain_can_have_blank_topics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "calibration.csv"
            rows = []
            for index in range(1, 13):
                relevance = "Not relevant" if index == 10 else "Uncertain" if index == 12 else "Relevant"
                topic = "" if relevance in {"Not relevant", "Uncertain"} else "A - Thị trường lao động Việt Nam"
                rows.append(
                    {
                        "scenario_id": f"CAL-{index:02}",
                        "reviewer_id": "R1",
                        "relevance_manual": relevance,
                        "topic_manual": topic,
                        "review_reason": "Evidence from the scenario.",
                        "review_date": "2026-03-01",
                    }
                )
            _write_csv(path, validator.CALIBRATION_COLUMNS, rows)
            _, report = validator._read_calibration(path)
            self.assertEqual(report["completed_response_count"], 12)
            self.assertEqual(report["validation_errors"], [])

    def test_calibration_lock_requires_exact_sheet_hash_and_coordinator_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sheet_1, sheet_2 = root / "r1.csv", root / "r2.csv"
            lock = root / "lock.json"
            sheet_1.write_text("review 1", encoding="utf-8")
            sheet_2.write_text("review 2", encoding="utf-8")
            manifest = {
                "reviewers": {
                    "reviewer_1": {
                        "locked": True,
                        "reviewer_id": "R1",
                        "locked_by": "COORD",
                        "locked_at": "2026-03-01T10:00:00+00:00",
                        "sheet_sha256": validator._file_sha256(sheet_1),
                    },
                    "reviewer_2": {
                        "locked": True,
                        "reviewer_id": "R2",
                        "locked_by": "COORD",
                        "locked_at": "2026-03-01T10:00:00+00:00",
                        "sheet_sha256": validator._file_sha256(sheet_2),
                    },
                }
            }
            lock.write_text(json.dumps(manifest), encoding="utf-8")
            result = validator._validate_calibration_lock(
                lock,
                {"reviewer_1": sheet_1, "reviewer_2": sheet_2},
                {"reviewer_1": "R1", "reviewer_2": "R2"},
            )
            self.assertTrue(result["valid"])
            sheet_2.write_text("changed", encoding="utf-8")
            result = validator._validate_calibration_lock(
                lock,
                {"reviewer_1": sheet_1, "reviewer_2": sheet_2},
                {"reviewer_1": "R1", "reviewer_2": "R2"},
            )
            self.assertFalse(result["valid"])
            self.assertIn("reviewer_2:SHEET_HASH_MISMATCH", result["errors"])


class TestP406Validation(unittest.TestCase):
    def test_pending_rows_are_counted_as_waiting_human_annotations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "p406.csv"
            row = {
                column: ""
                for column in validator.P406_COLUMNS
            }
            row.update(
                {
                    "article_id": "A1",
                    "title": "Title",
                    "content": "Content",
                    "annotation_status": "PENDING",
                }
            )
            _write_csv(path, validator.P406_COLUMNS, [row])
            _, report, _ = validator._validate_p406_sheet(path, ["A1"])
            self.assertEqual(report["valid_completed_count"], 0)
            self.assertIn(
                "PENDING_HUMAN_REVIEW",
                report["validation_errors_by_article_id"]["A1"],
            )

    def test_reviewer_disagreement_is_preserved_in_adjudication_queue(self):
        first = {
            "A1": _p406_row("A1", "R1"),
        }
        second_row = _p406_row("A1", "R2")
        second_row["gold_relevance_status"] = "IRRELEVANT"
        second_row["gold_topic_labels_p406"] = "[]"
        second = {"A1": second_row}
        clean = {"validation_errors_by_article_id": {}}
        report, queue = validator._build_p406_agreement(first, second, clean, clean)
        self.assertEqual(report["status"], "WAITING_FOR_ADJUDICATION")
        self.assertEqual(report["relevance_and_topic_disagreement_count"], 1)
        self.assertEqual(queue[0]["reviewer_1_relevance"], "RELEVANT")
        self.assertEqual(queue[0]["reviewer_2_relevance"], "IRRELEVANT")
        self.assertEqual(queue[0]["final_relevance_status"], "")
        self.assertEqual(report["agreement_metrics"]["relevance"]["raw_agreement"], 0.0)
        self.assertIsNone(
            report["agreement_metrics"]["topics_among_both_relevant"]["raw_agreement"]
        )

    def test_p406_only_valid_independent_disagreements_are_queued(self):
        first = {"A1": _p406_row("A1", "R1", "NEEDS_ADJUDICATION")}
        second = {"A1": _p406_row("A1", "R2", "PENDING")}
        errors_first = {"validation_errors_by_article_id": {}}
        errors_second = {
            "validation_errors_by_article_id": {"A1": ["PENDING_HUMAN_REVIEW"]}
        }
        report, queue = validator._build_p406_agreement(
            first, second, errors_first, errors_second
        )
        self.assertEqual(queue, [])
        self.assertEqual(report["adjudication_queue_count"], 0)

    def test_topic_taxonomy_rejects_legacy_a_to_l_label(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "p406.csv"
            row = _p406_row("A1", "R1")
            row["gold_topic_labels_p406"] = '["A"]'
            _write_csv(path, validator.P406_COLUMNS, [row])
            _, report, _ = validator._validate_p406_sheet(path, ["A1"])
            self.assertIn(
                "TOPIC_OUTSIDE_P406_TAXONOMY",
                report["validation_errors_by_article_id"]["A1"],
            )

    def test_duplicate_article_ids_and_missing_provenance_are_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "p406.csv"
            row = _p406_row("A1", "")
            row["reviewer_id"] = ""
            row["review_date"] = ""
            _write_csv(path, validator.P406_COLUMNS, [row, row])
            _, report, _ = validator._validate_p406_sheet(path, ["A1"])
            errors = report["validation_errors_by_article_id"]["A1"]
            self.assertIn("DUPLICATE_ARTICLE_ID", errors)
            self.assertIn("MISSING_REVIEWER_ID", errors)
            self.assertIn("INVALID_OR_MISSING_REVIEW_DATE", errors)

    def test_same_reviewer_cannot_be_counted_as_independent_agreement(self):
        first = {"A1": _p406_row("A1", "SAME")}
        second = {"A1": _p406_row("A1", "SAME")}
        clean = {"validation_errors_by_article_id": {}}
        report, queue = validator._build_p406_agreement(first, second, clean, clean)
        self.assertEqual(report["valid_completed_by_both"], 0)
        self.assertEqual(report["agreement_count"], 0)
        self.assertEqual(queue, [])


class TestDuplicateValidation(unittest.TestCase):
    def test_pending_candidate_is_not_confirmed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "duplicate.csv"
            row = {column: "" for column in validator.DUPLICATE_COLUMNS}
            row.update(
                {
                    "group_id": "G1",
                    "article_id_1": "A1",
                    "article_id_2": "A2",
                    "candidate_type": "NEAR_DUPLICATE",
                    "review_status": "PENDING",
                }
            )
            _write_csv(path, validator.DUPLICATE_COLUMNS, [row])
            _, report, _ = validator._validate_duplicate_sheet(path, [("A1", "A2")])
            self.assertEqual(report["completed_or_escalated_decision_count"], 0)
            self.assertEqual(report["pending_pair_count"], 1)
            self.assertEqual(report["decision_counts"], {})

    def test_confirmed_duplicates_require_two_reviewers_and_version_evidence(self):
        pair = ("A1", "A2")
        base = {
            "group_id": "G1",
            "article_id_1": "A1",
            "article_id_2": "A2",
            "candidate_type": "NEAR_DUPLICATE",
        }
        first = {
            "review_decision": "CONFIRMED_DUPLICATE",
            "confirmed_relationship_type": "VERSION_DUPLICATE",
            "version_lineage_evidence": "Explicit revision history.",
            "review_reason": "Same article, updated text.",
            "reviewer_id": "R1",
            "review_date": "2026-03-01",
        }
        second = {**first, "reviewer_id": "R2"}
        clean = {"validation_errors_by_pair": {}}
        report, queue, version_rows = validator._build_duplicate_agreement(
            {pair: first},
            {pair: second},
            clean,
            clean,
            {pair: base},
        )
        self.assertEqual(report["confirmed_duplicate_count"], 1)
        self.assertEqual(report["confirmed_version_lineage_count"], 1)
        self.assertEqual(report["agreement_metrics"]["decision"]["raw_agreement"], 1.0)
        self.assertEqual(queue, [])
        self.assertEqual(version_rows[0]["review_status"], "REVIEWED")


class TestPilot10Validation(unittest.TestCase):
    def test_blank_reviewer_sheets_remain_waiting(self):
        master = [
            {"article_id": f"A{index}", "title": f"Title {index}", "content": "Body"}
            for index in range(10)
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reviewer.csv"
            rows = [
                {
                    "article_id": row["article_id"],
                    "title": row["title"],
                    "content": row["content"],
                    "relevance_manual": "",
                    "topic_manual": "",
                    "review_reason": "",
                    "reviewer_id": "",
                    "review_date": "",
                    "review_status": "PENDING",
                }
                for row in master
            ]
            _write_csv(path, pilot.REVIEW_COLUMNS, rows)
            report, indexed = pilot._validate_reviewer_sheet(path, master)
            agreement, queue = pilot._compare_reviewers(
                indexed, indexed, report, report
            )
        self.assertEqual(report["valid_completed_count"], 0)
        self.assertEqual(agreement["status"], "WAITING_FOR_HUMAN_REVIEW")
        self.assertEqual(queue, [])
        self.assertEqual(agreement["gold_eligible_count"], 0)

    def test_manual_a_to_l_disagreement_is_queued_not_resolved(self):
        master_row = {
            "article_id": "A1",
            "title": "Title",
            "content": "Body",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            first_path = Path(temp_dir) / "reviewer1.csv"
            second_path = Path(temp_dir) / "reviewer2.csv"
            base = {
                **master_row,
                "relevance_manual": "Relevant",
                "topic_manual": f"A — {pilot.TOPIC_NAMES['A']}",
                "review_reason": "Human rationale.",
                "reviewer_id": "R1",
                "review_date": "2026-03-01",
                "review_status": "COMPLETED",
            }
            second = dict(base)
            second.update(
                {
                    "topic_manual": f"D — {pilot.TOPIC_NAMES['D']}",
                    "reviewer_id": "R2",
                }
            )
            _write_csv(first_path, pilot.REVIEW_COLUMNS, [base])
            _write_csv(second_path, pilot.REVIEW_COLUMNS, [second])
            first_report, first_index = pilot._validate_reviewer_sheet(
                first_path, [master_row]
            )
            second_report, second_index = pilot._validate_reviewer_sheet(
                second_path, [master_row]
            )
            agreement, queue = pilot._compare_reviewers(
                first_index, second_index, first_report, second_report
            )
        self.assertEqual(agreement["topic_disagreement_count"], 1)
        self.assertEqual(queue[0]["reviewer_1_topic"], base["topic_manual"])
        self.assertEqual(queue[0]["reviewer_2_topic"], second["topic_manual"])
        self.assertEqual(queue[0]["final_topic"], "")
        self.assertEqual(agreement["gold_eligible_count"], 0)
        self.assertEqual(agreement["agreement_metrics"]["relevance"]["raw_agreement"], 1.0)
        self.assertEqual(
            agreement["agreement_metrics"][
                "topics_among_both_relevant_or_borderline"
            ]["raw_agreement"],
            0.0,
        )

    def test_pilot_invalid_or_missing_second_review_is_not_adjudicated(self):
        first = {
            "A1": {
                "article_id": "A1",
                "relevance_manual": "Relevant",
                "topic_manual": f"A — {pilot.TOPIC_NAMES['A']}",
                "review_reason": "Human rationale.",
                "reviewer_id": "R1",
                "review_date": "2026-03-01",
                "review_status": "NEEDS_ADJUDICATION",
            }
        }
        second = {
            "A1": {
                "article_id": "A1",
                "relevance_manual": "",
                "topic_manual": "",
                "review_reason": "",
                "reviewer_id": "",
                "review_date": "",
                "review_status": "PENDING",
            }
        }
        report_one = {"validation_errors_by_article_id": {}}
        report_two = {
            "validation_errors_by_article_id": {"A1": ["PENDING_REVIEW"]}
        }
        agreement, queue = pilot._compare_reviewers(
            first, second, report_one, report_two
        )
        self.assertEqual(queue, [])
        self.assertEqual(agreement["adjudication_queue_count"], 0)

    def test_pilot_agreement_uses_expected_master_size_when_rows_are_missing(self):
        empty_report = {"validation_errors_by_article_id": {}}
        agreement, queue = pilot._compare_reviewers(
            {}, {}, empty_report, empty_report, expected_count=10
        )
        self.assertEqual(agreement["pilot_article_count"], 10)
        self.assertEqual(agreement["not_comparable_or_missing_count"], 10)
        self.assertEqual(queue, [])


class TestAdjudicationWorkflow(unittest.TestCase):
    def test_pending_forms_validate_without_deciding_cases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            p406_form = root / "p406.csv"
            duplicate_form = root / "duplicate.csv"
            _write_csv(p406_form, list(validator.P406_QUEUE_COLUMNS), [])
            _write_csv(
                duplicate_form,
                list(validator.DUPLICATE_QUEUE_COLUMNS),
                [],
            )
            with (
                patch.object(adjudication, "P406_FORM", p406_form),
                patch.object(adjudication, "DUPLICATE_FORM", duplicate_form),
            ):
                report = adjudication.validate_forms()
            self.assertEqual(report["p406_resolved_count"], 0)
            self.assertEqual(report["duplicate_resolved_count"], 0)

    def test_invalid_final_topic_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            p406_form = root / "p406.csv"
            duplicate_form = root / "duplicate.csv"
            _write_csv(
                p406_form,
                list(validator.P406_QUEUE_COLUMNS),
                [
                    _p406_queue_row(
                        "A1",
                        adjudication_status="ADJUDICATED",
                        final_relevance_status="RELEVANT",
                        final_topic_labels_p406='["A"]',
                        adjudication_reason="Resolved using article evidence.",
                        adjudicator_id="ADJ1",
                        adjudication_date="2026-03-01",
                    )
                ],
            )
            _write_csv(duplicate_form, list(validator.DUPLICATE_QUEUE_COLUMNS), [])
            p406_queue = root / "p406_queue.csv"
            queue_row = _p406_queue_row(
                "A1",
                reviewer_1_relevance="RELEVANT",
                reviewer_1_topics='["WAGES"]',
                reviewer_1_reason="R1 reason",
                reviewer_1_id="R1",
                reviewer_1_date="2026-03-01",
                reviewer_2_relevance="IRRELEVANT",
                reviewer_2_topics="[]",
                reviewer_2_reason="R2 reason",
                reviewer_2_id="R2",
                reviewer_2_date="2026-03-01",
                disagreement_type="RELEVANCE_AND_TOPIC_DISAGREEMENT",
            )
            _write_csv(p406_queue, list(validator.P406_QUEUE_COLUMNS), [queue_row])
            with (
                patch.object(adjudication, "P406_FORM", p406_form),
                patch.object(adjudication, "DUPLICATE_FORM", duplicate_form),
                patch.object(adjudication, "P406_QUEUE", p406_queue),
            ):
                with self.assertRaises(ValueError):
                    adjudication.validate_forms()

    def test_adjudication_form_cannot_change_reviewer_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            p406_form = root / "p406.csv"
            duplicate_form = root / "duplicate.csv"
            p406_queue = root / "p406_queue.csv"
            queue_row = _p406_queue_row(
                "A1",
                reviewer_1_relevance="RELEVANT",
                reviewer_1_topics='["WAGES"]',
                reviewer_1_reason="R1 reason",
                reviewer_1_id="R1",
                reviewer_1_date="2026-03-01",
                reviewer_2_relevance="IRRELEVANT",
                reviewer_2_topics="[]",
                reviewer_2_reason="R2 reason",
                reviewer_2_id="R2",
                reviewer_2_date="2026-03-01",
                disagreement_type="RELEVANCE_AND_TOPIC_DISAGREEMENT",
            )
            edited_form_row = dict(queue_row)
            edited_form_row["reviewer_1_relevance"] = "IRRELEVANT"
            _write_csv(p406_queue, list(validator.P406_QUEUE_COLUMNS), [queue_row])
            _write_csv(p406_form, list(validator.P406_QUEUE_COLUMNS), [edited_form_row])
            _write_csv(duplicate_form, list(validator.DUPLICATE_QUEUE_COLUMNS), [])
            with (
                patch.object(adjudication, "P406_FORM", p406_form),
                patch.object(adjudication, "DUPLICATE_FORM", duplicate_form),
                patch.object(adjudication, "P406_QUEUE", p406_queue),
            ):
                with self.assertRaisesRegex(ValueError, "source field.*was changed"):
                    adjudication.validate_forms()

    def test_adjudicated_form_requires_adjudicator_id_and_date(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            p406_form = root / "p406.csv"
            duplicate_form = root / "duplicate.csv"
            p406_queue = root / "p406_queue.csv"
            queue_row = _p406_queue_row(
                "A1",
                reviewer_1_relevance="RELEVANT",
                reviewer_1_topics='["WAGES"]',
                reviewer_1_reason="R1 reason",
                reviewer_1_id="R1",
                reviewer_1_date="2026-03-01",
                reviewer_2_relevance="IRRELEVANT",
                reviewer_2_topics="[]",
                reviewer_2_reason="R2 reason",
                reviewer_2_id="R2",
                reviewer_2_date="2026-03-01",
                disagreement_type="RELEVANCE_AND_TOPIC_DISAGREEMENT",
            )
            form_row = dict(queue_row)
            form_row.update(
                {
                    "adjudication_status": "ADJUDICATED",
                    "final_relevance_status": "RELEVANT",
                    "final_topic_labels_p406": '["WAGES"]',
                    "adjudication_reason": "Resolved based on the article.",
                    "adjudicator_id": "",
                    "adjudication_date": "",
                }
            )
            _write_csv(p406_queue, list(validator.P406_QUEUE_COLUMNS), [queue_row])
            _write_csv(p406_form, list(validator.P406_QUEUE_COLUMNS), [form_row])
            _write_csv(duplicate_form, list(validator.DUPLICATE_QUEUE_COLUMNS), [])
            with (
                patch.object(adjudication, "P406_FORM", p406_form),
                patch.object(adjudication, "DUPLICATE_FORM", duplicate_form),
                patch.object(adjudication, "P406_QUEUE", p406_queue),
            ):
                with self.assertRaisesRegex(ValueError, "resolved case needs reason"):
                    adjudication.validate_forms()

    def test_gold_is_built_only_from_two_valid_consensus_reviews(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reviewer_1 = root / "r1.csv"
            reviewer_2 = root / "r2.csv"
            p406_form = root / "p406_adjudication.csv"
            duplicate_form = root / "duplicate_adjudication.csv"
            gold = root / "gold.csv"
            sample_rows = []
            rows_1 = []
            rows_2 = []
            for index in range(620):
                article_id = f"A{index}"
                sample_rows.append(
                    {
                        "article_id": article_id,
                        "title": f"Title {article_id}",
                        "content": f"Content {article_id}",
                    }
                )
                if index == 0:
                    rows_1.append(_p406_row(article_id, "R1"))
                    rows_2.append(_p406_row(article_id, "R2"))
                else:
                    pending_1 = _p406_row(article_id, "R1", "PENDING")
                    pending_2 = _p406_row(article_id, "R2", "PENDING")
                    for row in (pending_1, pending_2):
                        row.update(
                            {
                                "gold_relevance_status": "",
                                "gold_topic_labels_p406": "",
                                "review_reason": "",
                                "reviewer_id": "",
                                "review_date": "",
                            }
                        )
                    rows_1.append(pending_1)
                    rows_2.append(pending_2)
            _write_csv(reviewer_1, list(rows_1[0]), rows_1)
            _write_csv(reviewer_2, list(rows_2[0]), rows_2)
            master = root / "sample.csv"
            _write_csv(master, ("article_id", "title", "content"), sample_rows)
            patch_path = root / "data" / "interim" / "relevance_review_sample.csv"
            patch_path.parent.mkdir(parents=True)
            patch_path.write_bytes(master.read_bytes())
            _write_csv(p406_form, list(validator.P406_QUEUE_COLUMNS), [])
            _write_csv(duplicate_form, list(validator.DUPLICATE_QUEUE_COLUMNS), [])
            with (
                patch.object(adjudication, "P406_REVIEWER_1", reviewer_1),
                patch.object(adjudication, "P406_REVIEWER_2", reviewer_2),
                patch.object(adjudication, "PROCESS", root),
                patch.object(adjudication, "P406_FORM", p406_form),
                patch.object(adjudication, "DUPLICATE_FORM", duplicate_form),
                patch.object(adjudication, "GOLD_OUTPUT", gold),
                patch.object(adjudication, "GOLD_BUILD_REPORT", root / "gold_report.json"),
                patch.object(adjudication, "GOLD_BUILD_HISTORY", root / "gold_history.jsonl"),
            ):
                result = adjudication.build_gold()
            self.assertEqual(result["eligible_gold_count"], 1)
            self.assertEqual(result["provenance"]["gold_file_sha256"], adjudication._sha256(gold))
            with gold.open("r", encoding="utf-8-sig", newline="") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row["adjudication_status"], "NOT_REQUIRED")
            self.assertEqual(row["annotation_method"], "human")
            self.assertEqual(row["contributing_reviewer_ids"], "R1|R2")


if __name__ == "__main__":
    unittest.main()
