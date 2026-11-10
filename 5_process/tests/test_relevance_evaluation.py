"""Tests for P4.09 human-gold-only evaluation and metric safeguards."""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "relevance_evaluation"
    / "evaluate.py"
)
SPEC = importlib.util.spec_from_file_location("p4_relevance_evaluation", SCRIPT)
evaluator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = evaluator
SPEC.loader.exec_module(evaluator)


def _gold(
    article_id,
    status="RELEVANT",
    topics=None,
    annotation_status="COMPLETED",
    adjudication_status="NOT_REQUIRED",
    method="human",
    review_date="2026-11-09",
    **extra,
):
    return {
        "article_id": article_id,
        "gold_relevance_status": status,
        "gold_topic_labels_p406": json.dumps(topics if topics is not None else ["WAGES"]),
        "annotation_status": annotation_status,
        "adjudication_status": adjudication_status,
        "annotation_method": method,
        "reviewer_id": "RV-REAL",
        "review_date": review_date,
        "review_reason": "Evidence recorded by a human reviewer.",
        "contributing_reviewer_ids": "RV-1|RV-2",
        "adjudicator_id": "",
        "adjudication_date": "",
        **extra,
    }


def _relevance_prediction(article_id, status):
    return {
        "article_id": article_id,
        "relevance_status": status,
        "classifier_version": "1.0.0",
        "taxonomy_version": "1.0.0",
    }


def _topic_prediction(article_id, status, labels):
    return {
        "article_id": article_id,
        "relevance_status": status,
        "topic_labels": json.dumps(labels),
        "classifier_version": "1.0.0",
        "taxonomy_version": "1.0.0",
    }


class TestEvaluateRecords(unittest.TestCase):
    def test_three_class_metrics_and_multilabel_metrics(self):
        gold = [
            _gold("A1", "RELEVANT", ["WAGES", "LABOR_DISPUTE"]),
            _gold("A2", "IRRELEVANT", []),
            _gold("A3", "REVIEW_REQUIRED", []),
        ]
        relevance = [
            _relevance_prediction("A1", "RELEVANT"),
            _relevance_prediction("A2", "IRRELEVANT"),
            _relevance_prediction("A3", "REVIEW_REQUIRED"),
        ]
        topics = [
            _topic_prediction("A1", "RELEVANT", ["WAGES", "LABOR_DISPUTE"]),
            _topic_prediction("A2", "IRRELEVANT", []),
            _topic_prediction("A3", "REVIEW_REQUIRED", []),
        ]
        report = evaluator.evaluate_records(gold, relevance, topics)
        self.assertEqual(report["status"], "COMPLETED")
        self.assertEqual(report["relevance_metrics"]["accuracy"], 1.0)
        self.assertEqual(report["relevance_metrics"]["sample_count"], 3)
        self.assertEqual(report["relevance_metrics"]["weighted_f1"], 1.0)
        self.assertEqual(report["multilabel_topic_metrics"]["micro_f1"], 1.0)
        self.assertEqual(report["multilabel_topic_metrics"]["weighted_f1"], 1.0)
        self.assertEqual(report["multilabel_topic_metrics"]["subset_accuracy"], 1.0)
        self.assertEqual(report["multilabel_topic_metrics"]["sample_count"], 1)
        self.assertEqual(
            report["prediction_metadata"]["relevance"]["classifier_version"],
            ["1.0.0"],
        )
        self.assertEqual(
            report["prediction_metadata"]["topics"]["taxonomy_version"],
            ["1.0.0"],
        )
        self.assertEqual(
            report["prediction_sample_counts"], {"relevance": 3, "topics": 3}
        )

    def test_borderline_uncertain_pending_and_adjudication_are_not_collapsed(self):
        gold = [
            _gold("A1", "BORDERLINE", []),
            _gold("A2", "UNCERTAIN", []),
            _gold(
                "A3",
                "RELEVANT",
                ["WAGES"],
                annotation_status="PENDING",
                adjudication_status="PENDING",
                method="",
                review_date="",
            ),
            _gold(
                "A4",
                "RELEVANT",
                ["WAGES"],
                adjudication_status="NEEDS_ADJUDICATION",
            ),
        ]
        relevance = [
            _relevance_prediction("A1", "REVIEW_REQUIRED"),
            _relevance_prediction("A2", "REVIEW_REQUIRED"),
            _relevance_prediction("A3", "RELEVANT"),
            _relevance_prediction("A4", "RELEVANT"),
        ]
        topics = [
            _topic_prediction("A1", "REVIEW_REQUIRED", []),
            _topic_prediction("A2", "REVIEW_REQUIRED", []),
            _topic_prediction("A3", "RELEVANT", ["WAGES"]),
            _topic_prediction("A4", "RELEVANT", ["WAGES"]),
        ]
        report = evaluator.evaluate_records(gold, relevance, topics)
        exclusions = report["excluded_record_counts"]
        self.assertEqual(exclusions["gold_borderline"], 1)
        self.assertEqual(exclusions["gold_uncertain"], 1)
        self.assertEqual(exclusions["not_completed_or_adjudicated"], 2)
        self.assertIsNone(report["relevance_metrics"])
        self.assertIsNone(report["multilabel_topic_metrics"])
        self.assertEqual(report["status"], "WAITING_FOR_GOLD_LABELS")

    def test_missing_or_duplicate_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "article_id must not be blank"):
            evaluator.evaluate_records(
                [_gold(" ")], [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )
        with self.assertRaisesRegex(ValueError, "duplicate article_id"):
            evaluator.evaluate_records(
                [_gold("A1"), _gold("A1")],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )

    def test_invalid_gold_status_or_topic_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid gold_relevance_status"):
            evaluator.evaluate_records(
                [_gold("A1", "relevant")],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )
        with self.assertRaisesRegex(ValueError, "invalid P4.06 topic labels"):
            evaluator.evaluate_records(
                [_gold("A1", "RELEVANT", ["A - Thị trường lao động Việt Nam"])],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )

    def test_manual_relevance_and_topic_taxonomies_are_not_coerced(self):
        with self.assertRaisesRegex(ValueError, "invalid gold_relevance_status"):
            evaluator.evaluate_records(
                [_gold("A1", "Relevant")],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )

    def test_missing_reason_reviewer_or_invalid_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "review_date must be YYYY-MM-DD"):
            evaluator.evaluate_records(
                [_gold("A1", review_date="2026-02-30")],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )
        with self.assertRaisesRegex(ValueError, "reviewer_id must not be blank"):
            evaluator.evaluate_records(
                [_gold("A1", reviewer_id=" ")],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )

    def test_ai_annotation_method_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "annotation_method must be human"):
            evaluator.evaluate_records(
                [_gold("A1", method="ai_proposal")],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )

    def test_completed_adjudication_requires_real_adjudicator_provenance(self):
        adjudicated = _gold(
            "A1",
            adjudication_status="ADJUDICATED",
            method="human_adjudicated",
            adjudicator_id="ADJ-01",
            adjudication_date="2026-03-01",
        )
        report = evaluator.evaluate_records(
            [adjudicated],
            [_relevance_prediction("A1", "RELEVANT")],
            [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
        )
        self.assertEqual(report["status"], "COMPLETED")

        adjudicated["adjudicator_id"] = ""
        with self.assertRaisesRegex(ValueError, "adjudicator_id must not be blank"):
            evaluator.evaluate_records(
                [adjudicated],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )

    def test_consensus_gold_requires_two_distinct_reviewer_ids(self):
        gold = _gold("A1", contributing_reviewer_ids="RV-1|RV-1")
        with self.assertRaisesRegex(ValueError, "at least two distinct"):
            evaluator.evaluate_records(
                [gold],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )

    def test_duplicate_group_crossing_splits_suppresses_metrics(self):
        report = evaluator.evaluate_records(
            [_gold("A1"), _gold("A2")],
            [
                _relevance_prediction("A1", "RELEVANT"),
                _relevance_prediction("A2", "RELEVANT"),
            ],
            [
                _topic_prediction("A1", "RELEVANT", ["WAGES"]),
                _topic_prediction("A2", "RELEVANT", ["WAGES"]),
            ],
            split_records=[
                {"article_id": "A1", "split": "train"},
                {"article_id": "A2", "split": "test"},
            ],
            duplicate_group_records=[
                {"duplicate_group_id": "G1", "article_id": "A1"},
                {"duplicate_group_id": "G1", "article_id": "A2"},
            ],
        )
        self.assertEqual(report["status"], "BLOCKED_LEAKAGE")
        self.assertIsNone(report["relevance_metrics"])
        self.assertEqual(
            report["duplicate_group_leakage_check"]["cross_split_group_count"], 1
        )

    def test_split_group_incomplete_coverage_suppresses_metrics(self):
        report = evaluator.evaluate_records(
            [_gold("A1")],
            [_relevance_prediction("A1", "RELEVANT")],
            [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            split_records=[{"article_id": "A1", "split": "test"}],
            duplicate_group_records=[
                {"duplicate_group_id": "G1", "article_id": "A1"},
                {"duplicate_group_id": "G1", "article_id": "A2"},
            ],
        )
        self.assertEqual(report["status"], "INCOMPLETE_SPLIT_COVERAGE")
        self.assertIsNone(report["relevance_metrics"])

    def test_prediction_id_and_status_mismatch_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "prediction IDs differ"):
            evaluator.evaluate_records(
                [_gold("A1")],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A2", "RELEVANT", ["WAGES"])],
            )
        with self.assertRaisesRegex(ValueError, "status mismatch"):
            evaluator.evaluate_records(
                [_gold("A1")],
                [_relevance_prediction("A1", "RELEVANT")],
                [_topic_prediction("A1", "IRRELEVANT", [])],
            )

    def test_missing_prediction_version_is_rejected(self):
        prediction = _relevance_prediction("A1", "RELEVANT")
        prediction["classifier_version"] = ""
        with self.assertRaisesRegex(ValueError, "classifier_version must be present"):
            evaluator.evaluate_records(
                [_gold("A1")],
                [prediction],
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )


class TestEvaluationFiles(unittest.TestCase):
    @staticmethod
    def _write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def test_missing_gold_writes_waiting_report_without_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relevance_path = root / "relevance.csv"
            topic_path = root / "topics.csv"
            self._write_csv(
                relevance_path,
                list(evaluator.RELEVANCE_PREDICTION_COLUMNS),
                [_relevance_prediction("A1", "RELEVANT")],
            )
            self._write_csv(
                topic_path,
                list(evaluator.TOPIC_PREDICTION_COLUMNS),
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )
            report = evaluator.run_evaluation(
                root / "missing_gold.csv",
                relevance_path,
                topic_path,
                root / "report.json",
                root / "report.md",
            )
            saved = json.loads((root / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "WAITING_FOR_GOLD_LABELS")
            self.assertEqual(saved, report)
            self.assertIsNone(report["relevance_metrics"])
            self.assertIsNone(report["multilabel_topic_metrics"])
            markdown = (root / "report.md").read_text(encoding="utf-8")
            self.assertIn("No accuracy", markdown)
            self.assertIn("classifier_version", markdown)
            self.assertIn("comparison_with_completed_human_gold", markdown)
            self.assertEqual(report["prediction_sample_counts"], {"relevance": 1, "topics": 1})
            self.assertTrue(report["generated_at_utc"])
            self.assertIn("relevance_predictions_sha256", report["inputs"])
            self.assertEqual(report["gold_taxonomy"]["version"], "1.0.0")
            self.assertEqual(
                report["gold_taxonomy"]["sha256"],
                report["inputs"]["p406_taxonomy_sha256"],
            )

    def test_invalid_prediction_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relevance_path = root / "relevance.csv"
            topic_path = root / "topics.csv"
            self._write_csv(relevance_path, ["article_id"], [{"article_id": "A1"}])
            self._write_csv(
                topic_path,
                list(evaluator.TOPIC_PREDICTION_COLUMNS),
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )
            with self.assertRaisesRegex(ValueError, "missing required columns"):
                evaluator.run_evaluation(
                    root / "missing_gold.csv",
                    relevance_path,
                    topic_path,
                    root / "report.json",
                    root / "report.md",
                )

    def test_output_reports_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relevance_path = root / "relevance.csv"
            topic_path = root / "topics.csv"
            self._write_csv(
                relevance_path,
                list(evaluator.RELEVANCE_PREDICTION_COLUMNS),
                [_relevance_prediction("A1", "RELEVANT")],
            )
            self._write_csv(
                topic_path,
                list(evaluator.TOPIC_PREDICTION_COLUMNS),
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )
            report_json = root / "report.json"
            report_md = root / "report.md"
            report_json.write_text("existing", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                evaluator.run_evaluation(
                    root / "missing_gold.csv",
                    relevance_path,
                    topic_path,
                    report_json,
                    report_md,
                )

    def test_explicit_report_refresh_replaces_only_evaluation_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relevance_path = root / "relevance.csv"
            topic_path = root / "topics.csv"
            gold_path = root / "gold.csv"
            report_json = root / "report.json"
            report_md = root / "report.md"
            self._write_csv(
                relevance_path,
                list(evaluator.RELEVANCE_PREDICTION_COLUMNS),
                [_relevance_prediction("A1", "RELEVANT")],
            )
            self._write_csv(
                topic_path,
                list(evaluator.TOPIC_PREDICTION_COLUMNS),
                [_topic_prediction("A1", "RELEVANT", ["WAGES"])],
            )
            waiting = evaluator.run_evaluation(
                gold_path,
                relevance_path,
                topic_path,
                report_json,
                report_md,
            )
            self.assertEqual(waiting["status"], "WAITING_FOR_GOLD_LABELS")
            topic_report_path = root / "topic_report.json"
            waiting_topic_report = json.loads(topic_report_path.read_text(encoding="utf-8"))
            self.assertEqual(waiting_topic_report["status"], "WAITING_FOR_GOLD_LABELS")
            self.assertIsNone(waiting_topic_report["metrics"])

            self._write_csv(
                gold_path,
                list(evaluator.GOLD_REQUIRED_COLUMNS),
                [_gold("A1", "RELEVANT", ["WAGES"])],
            )
            completed = evaluator.run_evaluation(
                gold_path,
                relevance_path,
                topic_path,
                report_json,
                report_md,
                overwrite_reports=True,
            )

            self.assertEqual(completed["status"], "COMPLETED")
            self.assertEqual(completed["relevance_metrics"]["sample_count"], 1)
            self.assertEqual(completed["multilabel_topic_metrics"]["sample_count"], 1)
            saved = json.loads(report_json.read_text(encoding="utf-8"))
            self.assertEqual(saved, completed)
            topic_report = json.loads(topic_report_path.read_text(encoding="utf-8"))
            self.assertEqual(topic_report["metrics"]["subset_accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
