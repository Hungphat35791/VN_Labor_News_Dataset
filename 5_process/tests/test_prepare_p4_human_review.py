"""Tests for safe generation of independent human-review packets."""
from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "src" / "prepare_p4_human_review.py"
SPEC = importlib.util.spec_from_file_location("prepare_p4_human_review", SCRIPT)
packet_builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = packet_builder
SPEC.loader.exec_module(packet_builder)


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


class TestP406ReviewerPackets(unittest.TestCase):
    def test_csv_writer_refuses_to_overwrite_an_existing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "existing.csv"
            target.write_text("protected", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                packet_builder._write_csv(target, ("article_id",), [])
            self.assertEqual(target.read_text(encoding="utf-8"), "protected")

    def test_builds_p406_rows_without_legacy_or_automatic_labels(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sample = Path(temp_dir) / "sample.csv"
            rows = [
                {
                    "article_id": f"A{index}",
                    "title": f"Title {index}",
                    "content": f"Article content {index}",
                    "relevance_manual": "",
                    "topic_manual": "",
                    "review_reason": "",
                    "reviewer_id": "",
                    "review_date": "",
                    "review_status": "PENDING",
                }
                for index in range(620)
            ]
            _write_csv(sample, packet_builder.P406_INPUT_COLUMNS, rows)

            result = packet_builder.build_p406_reviewer_rows(sample)

            self.assertEqual(len(result), 620)
            self.assertEqual(result[0]["article_id"], "A0")
            self.assertEqual(result[0]["title"], "Title 0")
            self.assertEqual(result[0]["content"], "Article content 0")
            self.assertEqual(result[0]["gold_relevance_status"], "")
            self.assertEqual(result[0]["gold_topic_labels_p406"], "")
            self.assertEqual(result[0]["review_reason"], "")
            self.assertEqual(result[0]["reviewer_id"], "")
            self.assertEqual(result[0]["review_date"], "")
            self.assertEqual(result[0]["annotation_status"], "PENDING")
            self.assertNotIn("relevance_status", result[0])
            self.assertNotIn("topic_labels", result[0])

    def test_rejects_reviewed_master_and_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sample = Path(temp_dir) / "sample.csv"
            rows = [
                {
                    "article_id": f"A{index}",
                    "title": "Title",
                    "content": "Content",
                    "relevance_manual": "",
                    "topic_manual": "",
                    "review_reason": "",
                    "reviewer_id": "",
                    "review_date": "",
                    "review_status": "PENDING",
                }
                for index in range(620)
            ]
            rows[1]["article_id"] = rows[0]["article_id"]
            _write_csv(sample, packet_builder.P406_INPUT_COLUMNS, rows)
            with self.assertRaisesRegex(ValueError, "duplicate article_id"):
                packet_builder.build_p406_reviewer_rows(sample)

            rows[1]["article_id"] = "A1"
            rows[1]["review_status"] = "COMPLETED"
            _write_csv(sample, packet_builder.P406_INPUT_COLUMNS, rows)
            with self.assertRaisesRegex(ValueError, "not PENDING"):
                packet_builder.build_p406_reviewer_rows(sample)


class TestDuplicateReviewPackets(unittest.TestCase):
    def test_pair_rows_include_full_evidence_and_blank_decisions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            canonical = root / "canonical.csv"
            candidates = root / "near.csv"
            groups = root / "groups.csv"
            _write_csv(
                canonical,
                ("article_id", "title", "content", "source_name", "publish_date", "source_url"),
                [
                    {
                        "article_id": "A1",
                        "title": "First",
                        "content": "Full first body",
                        "source_name": "Source A",
                        "publish_date": "2025-01-01",
                        "source_url": "https://example.test/1",
                    },
                    {
                        "article_id": "A2",
                        "title": "Second",
                        "content": "Full second body",
                        "source_name": "Source B",
                        "publish_date": "2025-01-02",
                        "source_url": "https://example.test/2",
                    },
                ],
            )
            _write_csv(
                candidates,
                (
                    "article_id_1",
                    "article_id_2",
                    "similarity_score",
                    "duplicate_type",
                    "method",
                    "threshold",
                ),
                [
                    {
                        "article_id_1": "A1",
                        "article_id_2": "A2",
                        "similarity_score": "0.91",
                        "duplicate_type": "NEAR_DUPLICATE",
                        "method": "test",
                        "threshold": "0.85",
                    }
                ],
            )
            _write_csv(
                groups,
                ("duplicate_group_id", "article_id"),
                [
                    {"duplicate_group_id": "G1", "article_id": "A1"},
                    {"duplicate_group_id": "G1", "article_id": "A2"},
                ],
            )

            result = packet_builder.build_duplicate_review_rows(canonical, candidates, groups)

            self.assertEqual(len(result), 1)
            row = result[0]
            self.assertEqual(row["group_id"], "G1")
            self.assertEqual(row["content_1"], "Full first body")
            self.assertEqual(row["content_2"], "Full second body")
            self.assertEqual(row["similarity_score"], "0.91")
            self.assertEqual(row["candidate_type"], "NEAR_DUPLICATE")
            self.assertEqual(row["review_status"], "PENDING")
            for field in ("reviewer_id", "review_decision", "review_reason", "review_date"):
                self.assertEqual(row[field], "")

    def test_rejects_pair_without_a_shared_candidate_group(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            canonical = root / "canonical.csv"
            candidates = root / "near.csv"
            groups = root / "groups.csv"
            _write_csv(
                canonical,
                ("article_id", "title", "content", "source_name", "publish_date", "source_url"),
                [
                    {
                        "article_id": aid,
                        "title": aid,
                        "content": "body",
                        "source_name": "source",
                        "publish_date": "2025-01-01",
                        "source_url": f"https://example.test/{aid}",
                    }
                    for aid in ("A1", "A2")
                ],
            )
            _write_csv(
                candidates,
                ("article_id_1", "article_id_2", "similarity_score", "duplicate_type", "method", "threshold"),
                [
                    {
                        "article_id_1": "A1",
                        "article_id_2": "A2",
                        "similarity_score": "0.9",
                        "duplicate_type": "NEAR_DUPLICATE",
                        "method": "test",
                        "threshold": "0.85",
                    }
                ],
            )
            _write_csv(
                groups,
                ("duplicate_group_id", "article_id"),
                [
                    {"duplicate_group_id": "G1", "article_id": "A1"},
                    {"duplicate_group_id": "G2", "article_id": "A2"},
                ],
            )

            with self.assertRaisesRegex(ValueError, "shared candidate group"):
                packet_builder.build_duplicate_review_rows(canonical, candidates, groups)


if __name__ == "__main__":
    unittest.main()
