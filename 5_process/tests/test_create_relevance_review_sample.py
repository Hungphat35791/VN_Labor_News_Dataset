"""Tests for the P4.07 stratified manual-audit sample."""
import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "create_relevance_review_sample.py"
SPEC = importlib.util.spec_from_file_location("create_relevance_review_sample", SRC)
sample_creator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sample_creator
SPEC.loader.exec_module(sample_creator)


def _source_row(article_id):
    return {
        "article_id": article_id,
        "title": f"Title {article_id}",
        "content": f"Original article body {article_id}",
        "relevance_status": "relevant_auto",
    }


def _prediction_row(article_id, status):
    return {
        "article_id": article_id,
        "relevance_status": status,
        "topic_labels": "DO_NOT_COPY",
        "matched_keywords": "prediction-only",
    }


def _records(counts):
    source_rows = []
    prediction_rows = []
    number = 1
    for status in sample_creator.STATUSES:
        for _ in range(counts.get(status, 0)):
            article_id = f"A{number:04d}"
            number += 1
            source_rows.append(_source_row(article_id))
            prediction_rows.append(_prediction_row(article_id, status))
    return source_rows, prediction_rows


class TestCreateSample(unittest.TestCase):
    def test_selects_requested_counts_per_status(self):
        source, predictions = _records(
            {
                sample_creator.RELEVANT: 250,
                sample_creator.IRRELEVANT: 220,
                sample_creator.REVIEW_REQUIRED: 240,
            }
        )
        rows, report = sample_creator.create_sample(source, predictions, random_seed=42)
        self.assertEqual(len(rows), 620)
        self.assertEqual(
            report["sampled_count_by_status"],
            {
                sample_creator.RELEVANT: 200,
                sample_creator.IRRELEVANT: 220,
                sample_creator.REVIEW_REQUIRED: 200,
            },
        )

    def test_all_irrelevant_rows_are_sampled(self):
        source, predictions = _records(
            {
                sample_creator.RELEVANT: 205,
                sample_creator.IRRELEVANT: 3,
                sample_creator.REVIEW_REQUIRED: 205,
            }
        )
        rows, report = sample_creator.create_sample(source, predictions)
        irrelevant_ids = {
            row["article_id"]
            for row, prediction in zip(source, predictions)
            if prediction["relevance_status"] == sample_creator.IRRELEVANT
        }
        selected_ids = {row["article_id"] for row in rows}
        self.assertTrue(irrelevant_ids.issubset(selected_ids))
        self.assertEqual(report["sampled_count_by_status"][sample_creator.IRRELEVANT], 3)

    def test_sampling_is_reproducible_with_same_seed(self):
        source, predictions = _records(
            {
                sample_creator.RELEVANT: 230,
                sample_creator.IRRELEVANT: 220,
                sample_creator.REVIEW_REQUIRED: 230,
            }
        )
        first, _ = sample_creator.create_sample(source, predictions, random_seed=42)
        second, _ = sample_creator.create_sample(source, predictions, random_seed=42)
        self.assertEqual(first, second)

    def test_no_article_id_is_duplicated(self):
        source, predictions = _records(
            {
                sample_creator.RELEVANT: 205,
                sample_creator.IRRELEVANT: 220,
                sample_creator.REVIEW_REQUIRED: 205,
            }
        )
        rows, report = sample_creator.create_sample(source, predictions)
        ids = [row["article_id"] for row in rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(report["unique_article_id_count"], len(ids))

    def test_manual_fields_are_blank_and_predictions_are_not_exported(self):
        source, predictions = _records(
            {
                sample_creator.RELEVANT: 1,
                sample_creator.IRRELEVANT: 1,
                sample_creator.REVIEW_REQUIRED: 1,
            }
        )
        rows, _ = sample_creator.create_sample(
            source,
            predictions,
            requested_counts={status: 1 for status in sample_creator.STATUSES},
        )
        self.assertEqual(
            set(rows[0]),
            set(sample_creator.OUTPUT_COLUMNS),
        )
        self.assertEqual(
            sample_creator.OUTPUT_COLUMNS,
            (
                "article_id",
                "title",
                "content",
                "relevance_manual",
                "topic_manual",
                "review_reason",
                "reviewer_id",
                "review_date",
                "review_status",
            ),
        )
        for row in rows:
            self.assertTrue(
                all(row[field] == "" for field in sample_creator.ANNOTATION_COLUMNS)
            )
            self.assertEqual(row["review_status"], sample_creator.INITIAL_REVIEW_STATUS)
            self.assertNotIn("relevance_status", row)
            self.assertNotIn("topic_labels", row)
            self.assertNotIn("matched_keywords", row)
        self.assertNotIn("DO_NOT_COPY", json.dumps(rows))

    def test_source_fields_are_joined_by_article_id(self):
        source = [_source_row("ID-B"), _source_row("ID-A")]
        predictions = [
            _prediction_row("ID-A", sample_creator.RELEVANT),
            _prediction_row("ID-B", sample_creator.IRRELEVANT),
        ]
        rows, _ = sample_creator.create_sample(
            source,
            predictions,
            requested_counts={
                sample_creator.RELEVANT: 1,
                sample_creator.IRRELEVANT: 1,
                sample_creator.REVIEW_REQUIRED: 0,
            },
        )
        rows_by_id = {row["article_id"]: row for row in rows}
        self.assertEqual(rows_by_id["ID-A"]["title"], "Title ID-A")
        self.assertEqual(rows_by_id["ID-B"]["content"], "Original article body ID-B")

    def test_missing_group_or_quota_shortfall_is_explicit(self):
        source, predictions = _records(
            {
                sample_creator.RELEVANT: 4,
                sample_creator.IRRELEVANT: 0,
                sample_creator.REVIEW_REQUIRED: 3,
            }
        )
        rows, report = sample_creator.create_sample(source, predictions)
        self.assertEqual(len(rows), 7)
        self.assertFalse(report["complete"])
        self.assertEqual(report["available_count_by_status"][sample_creator.IRRELEVANT], 0)
        self.assertEqual(report["sampled_count_by_status"][sample_creator.IRRELEVANT], 0)
        self.assertEqual(report["shortfall_by_status"][sample_creator.RELEVANT], 196)
        self.assertEqual(report["shortfall_by_status"][sample_creator.IRRELEVANT], 220)
        self.assertEqual(report["shortfall_by_status"][sample_creator.REVIEW_REQUIRED], 197)

    def test_duplicate_or_blank_ids_and_invalid_status_fail(self):
        with self.assertRaisesRegex(ValueError, "duplicate article_id"):
            sample_creator.create_sample(
                [_source_row("A"), _source_row("A")],
                [
                    _prediction_row("A", sample_creator.RELEVANT),
                    _prediction_row("A", sample_creator.IRRELEVANT),
                ],
            )
        with self.assertRaisesRegex(ValueError, "must not be blank"):
            sample_creator.create_sample(
                [_source_row("")],
                [_prediction_row("", sample_creator.RELEVANT)],
            )
        with self.assertRaisesRegex(ValueError, "invalid relevance_status"):
            sample_creator.create_sample(
                [_source_row("A")], [_prediction_row("A", "UNKNOWN")]
            )

    def test_result_ids_must_match_source_ids(self):
        with self.assertRaisesRegex(ValueError, "is absent from the source"):
            # Extra prediction IDs are rejected before sampling rather than dropped silently.
            sample_creator.create_sample(
                [_source_row("SOURCE")],
                [_prediction_row("PREDICTION", sample_creator.RELEVANT)],
            )

    def test_sample_order_is_mixed_across_statuses(self):
        source, predictions = _records(
            {
                sample_creator.RELEVANT: 10,
                sample_creator.IRRELEVANT: 10,
                sample_creator.REVIEW_REQUIRED: 10,
            }
        )
        rows, _ = sample_creator.create_sample(
            source,
            predictions,
            random_seed=42,
            requested_counts={status: 5 for status in sample_creator.STATUSES},
        )
        status_by_id = {row["article_id"]: pred["relevance_status"] for row, pred in zip(source, predictions)}
        sampled_statuses = [status_by_id[row["article_id"]] for row in rows]
        self.assertGreater(len(set(sampled_statuses)), 1)
        self.assertNotEqual(sampled_statuses, sorted(sampled_statuses))


class TestCreateReviewSampleFiles(unittest.TestCase):
    @staticmethod
    def _write_csv(path, rows, fields):
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(
                {field: row.get(field, "") for field in fields}
                for row in rows
            )

    def test_source_is_unchanged_and_csv_report_match(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "source.csv"
            results_path = root / "predictions.csv"
            output_path = root / "review.csv"
            report_path = root / "report.json"
            source_rows, prediction_rows = _records(
                {
                    sample_creator.RELEVANT: 2,
                    sample_creator.IRRELEVANT: 1,
                    sample_creator.REVIEW_REQUIRED: 2,
                }
            )
            self._write_csv(source_path, source_rows, ["article_id", "title", "content", "relevance_status"])
            self._write_csv(results_path, prediction_rows, ["article_id", "relevance_status", "topic_labels", "matched_keywords"])
            before = hashlib.sha256(source_path.read_bytes()).hexdigest()

            report = sample_creator.create_review_sample(
                source_path, results_path, output_path, report_path, random_seed=42
            )

            with output_path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)
                self.assertEqual(reader.fieldnames, list(sample_creator.OUTPUT_COLUMNS))
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 5)
            self.assertEqual(report["total_sample_size"], len(rows))
            self.assertEqual(
                len({row["article_id"] for row in rows}),
                report["unique_article_id_count"],
            )
            self.assertEqual(saved_report["sampled_count_by_status"], report["sampled_count_by_status"])
            self.assertEqual(before, hashlib.sha256(source_path.read_bytes()).hexdigest())
            self.assertTrue(
                all(
                    not row[field]
                    for row in rows
                    for field in sample_creator.ANNOTATION_COLUMNS
                )
            )
            self.assertTrue(all(row["review_status"] == "PENDING" for row in rows))

    def test_existing_human_annotations_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "source.csv"
            results_path = root / "predictions.csv"
            output_path = root / "review.csv"
            report_path = root / "report.json"
            source_rows, prediction_rows = _records(
                {
                    sample_creator.RELEVANT: 1,
                    sample_creator.IRRELEVANT: 1,
                    sample_creator.REVIEW_REQUIRED: 1,
                }
            )
            self._write_csv(source_path, source_rows, ["article_id", "title", "content"])
            self._write_csv(results_path, prediction_rows, ["article_id", "relevance_status"])
            sample_creator.create_review_sample(
                source_path, results_path, output_path, report_path, random_seed=42
            )

            with output_path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)
                fields = reader.fieldnames
            rows[0]["relevance_manual"] = "Relevant"
            with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            before = hashlib.sha256(output_path.read_bytes()).hexdigest()

            with self.assertRaisesRegex(ValueError, "human annotations"):
                sample_creator.create_review_sample(
                    source_path, results_path, output_path, report_path, random_seed=42
                )
            self.assertEqual(before, hashlib.sha256(output_path.read_bytes()).hexdigest())

    def test_existing_sample_with_only_pending_status_can_be_regenerated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "source.csv"
            results_path = root / "predictions.csv"
            output_path = root / "review.csv"
            report_path = root / "report.json"
            source_rows, prediction_rows = _records(
                {
                    sample_creator.RELEVANT: 1,
                    sample_creator.IRRELEVANT: 1,
                    sample_creator.REVIEW_REQUIRED: 1,
                }
            )
            self._write_csv(source_path, source_rows, ["article_id", "title", "content"])
            self._write_csv(results_path, prediction_rows, ["article_id", "relevance_status"])
            sample_creator.create_review_sample(
                source_path, results_path, output_path, report_path, random_seed=42
            )
            report = sample_creator.create_review_sample(
                source_path, results_path, output_path, report_path, random_seed=42
            )
            self.assertEqual(report["total_sample_size"], 3)

    def test_source_and_p402_to_p407_artifacts_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "source.csv"
            results_path = root / "predictions.csv"
            self._write_csv(source_path, [_source_row("A")], ["article_id", "title", "content"])
            self._write_csv(
                results_path,
                [_prediction_row("A", sample_creator.RELEVANT)],
                ["article_id", "relevance_status"],
            )
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                sample_creator.create_review_sample(
                    source_path, results_path, source_path, root / "report.json"
                )
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                sample_creator.create_review_sample(
                    source_path,
                    results_path,
                    sample_creator.PROTECTED_ARTIFACTS[1],
                    root / "report.json",
                )

    def test_results_csv_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "source.csv"
            results_path = root / "predictions.csv"
            self._write_csv(source_path, [_source_row("A")], ["article_id", "title", "content"])
            self._write_csv(
                results_path,
                [_prediction_row("A", sample_creator.RELEVANT)],
                ["article_id", "relevance_status"],
            )
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                sample_creator.create_review_sample(
                    source_path, results_path, results_path, root / "report.json"
                )


if __name__ == "__main__":
    unittest.main()
