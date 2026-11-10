"""Tests for preparing the first manual-review batch."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "create_relevance_review_batch.py"
)
SPEC = importlib.util.spec_from_file_location("create_relevance_review_batch", SCRIPT)
batch_creator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = batch_creator
SPEC.loader.exec_module(batch_creator)


def _row(number: int) -> dict[str, str]:
    return {
        "article_id": f"ARTICLE-{number:03d}",
        "title": f"Title {number}",
        "content": f"Article content {number}",
        "relevance_manual": "",
        "topic_manual": "",
        "review_reason": "",
        "reviewer_id": "",
        "review_date": "",
        "review_status": "PENDING",
    }


class TestCreateBatch(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.master = self.root / "master.csv"
        self.batch = self.root / "batch.csv"
        self.report = self.root / "report.json"
        self.batch_02 = self.root / "batch_02.csv"
        self.report_02 = self.root / "report_02.json"
        self.master_rows = [_row(number) for number in range(1, 111)]
        self._write_csv(self.master, self.master_rows)

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=batch_creator.OUTPUT_COLUMNS
            )
            writer.writeheader()
            writer.writerows(rows)

    def _read_batch(self) -> tuple[list[str], list[dict[str, str]]]:
        with self.batch.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            return reader.fieldnames or [], list(reader)

    def test_creates_exactly_50_rows(self):
        report = batch_creator.create_batch(
            self.master, self.batch, self.report, created_at_utc="2026-11-09T00:00:00+00:00"
        )
        _, rows = self._read_batch()
        self.assertEqual(len(rows), 50)
        self.assertEqual(report["row_count"], 50)

    def test_batch_has_50_unique_article_ids(self):
        batch_creator.create_batch(self.master, self.batch, self.report)
        _, rows = self._read_batch()
        ids = [row["article_id"] for row in rows]
        self.assertEqual(len(ids), 50)
        self.assertEqual(len(set(ids)), 50)

    def test_exact_schema_and_column_order(self):
        batch_creator.create_batch(self.master, self.batch, self.report)
        fields, _ = self._read_batch()
        self.assertEqual(fields, list(batch_creator.OUTPUT_COLUMNS))

    def test_preserves_first_50_rows_in_original_order(self):
        batch_creator.create_batch(self.master, self.batch, self.report)
        _, rows = self._read_batch()
        self.assertEqual(
            [row["article_id"] for row in rows],
            [row["article_id"] for row in self.master_rows[:50]],
        )

    def test_preserves_titles_and_contents(self):
        batch_creator.create_batch(self.master, self.batch, self.report)
        _, rows = self._read_batch()
        for actual, expected in zip(rows, self.master_rows[:50]):
            self.assertEqual(actual["title"], expected["title"])
            self.assertEqual(actual["content"], expected["content"])

    def test_batch_02_contains_rows_51_to_100_in_master_order(self):
        report = batch_creator.create_batch(
            self.master,
            self.batch_02,
            self.report_02,
            batch_number=2,
        )
        with self.batch_02.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames, list(batch_creator.OUTPUT_COLUMNS))
            rows = list(reader)
        expected = self.master_rows[50:100]
        self.assertEqual(len(rows), 50)
        self.assertEqual(rows, expected)
        self.assertEqual(
            [row["article_id"] for row in rows],
            [row["article_id"] for row in expected],
        )
        self.assertEqual(
            len({row["article_id"] for row in rows}),
            50,
        )
        self.assertTrue(
            set(row["article_id"] for row in rows).isdisjoint(
                row["article_id"] for row in self.master_rows[:50]
            )
        )
        self.assertEqual(report["batch_number"], 2)
        self.assertEqual(report["row_count"], 50)
        self.assertEqual(
            report["article_ids"],
            [row["article_id"] for row in expected],
        )

    def test_batch_02_manual_fields_are_blank_and_pending(self):
        batch_creator.create_batch(
            self.master,
            self.batch_02,
            self.report_02,
            batch_number=2,
        )
        with self.batch_02.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertTrue(
            all(
                not row[field]
                for row in rows
                for field in batch_creator.ANNOTATION_COLUMNS
            )
        )
        self.assertTrue(all(row["review_status"] == "PENDING" for row in rows))

    def test_manual_fields_are_blank_and_statuses_pending(self):
        batch_creator.create_batch(self.master, self.batch, self.report)
        _, rows = self._read_batch()
        self.assertTrue(
            all(
                not row[field]
                for row in rows
                for field in batch_creator.ANNOTATION_COLUMNS
            )
        )
        self.assertTrue(all(row["review_status"] == "PENDING" for row in rows))

    def test_report_records_batch_and_source_provenance(self):
        source_hash = hashlib.sha256(self.master.read_bytes()).hexdigest()
        report = batch_creator.create_batch(
            self.master,
            self.batch,
            self.report,
            created_at_utc="2026-11-09T00:00:00+00:00",
        )
        saved = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(saved, report)
        self.assertEqual(report["batch_number"], 1)
        self.assertEqual(report["row_count"], 50)
        self.assertEqual(
            report["article_ids"],
            [row["article_id"] for row in self.master_rows[:50]],
        )
        self.assertEqual(report["source_sample_sha256"], source_hash)
        self.assertEqual(report["created_at_utc"], "2026-11-09T00:00:00+00:00")

    def test_existing_human_annotations_are_not_overwritten(self):
        batch_creator.create_batch(self.master, self.batch, self.report)
        _, rows = self._read_batch()
        rows[0]["reviewer_id"] = "human-reviewer"
        self._write_csv(self.batch, rows)
        before = hashlib.sha256(self.batch.read_bytes()).hexdigest()

        with self.assertRaisesRegex(ValueError, "manual annotations"):
            batch_creator.create_batch(self.master, self.batch, self.report)
        self.assertEqual(
            hashlib.sha256(self.batch.read_bytes()).hexdigest(), before
        )

    def test_existing_unreviewed_batch_is_not_overwritten(self):
        batch_creator.create_batch(self.master, self.batch, self.report)
        before_batch = hashlib.sha256(self.batch.read_bytes()).hexdigest()
        before_report = hashlib.sha256(self.report.read_bytes()).hexdigest()
        with self.assertRaisesRegex(FileExistsError, "already exists"):
            batch_creator.create_batch(self.master, self.batch, self.report)
        self.assertEqual(
            hashlib.sha256(self.batch.read_bytes()).hexdigest(), before_batch
        )
        self.assertEqual(
            hashlib.sha256(self.report.read_bytes()).hexdigest(), before_report
        )

    def test_existing_workflow_progress_is_not_overwritten(self):
        batch_creator.create_batch(self.master, self.batch, self.report)
        _, rows = self._read_batch()
        rows[0]["review_status"] = "IN_PROGRESS"
        self._write_csv(self.batch, rows)
        with self.assertRaisesRegex(ValueError, "not PENDING"):
            batch_creator.create_batch(self.master, self.batch, self.report)

    def test_master_is_not_modified(self):
        before = hashlib.sha256(self.master.read_bytes()).hexdigest()
        batch_creator.create_batch(self.master, self.batch, self.report)
        self.assertEqual(hashlib.sha256(self.master.read_bytes()).hexdigest(), before)

    def test_output_path_collision_with_master_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "source or P4.02-P4.07 artifacts"):
            batch_creator.create_batch(self.master, self.master, self.report)

    def test_output_path_collision_with_p407_artifact_is_rejected(self):
        protected = batch_creator.PROTECTED_PATHS[2]
        with self.assertRaisesRegex(ValueError, "P4.02-P4.07 artifacts"):
            batch_creator.create_batch(self.master, protected, self.report)


if __name__ == "__main__":
    unittest.main()
