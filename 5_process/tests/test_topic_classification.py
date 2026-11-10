"""Tests for the isolated P4.08 topic-candidate output."""
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
    / "topic_classification"
    / "classify_topics.py"
)
SPEC = importlib.util.spec_from_file_location("p4_topic_classification", SCRIPT)
topic_classifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = topic_classifier
SPEC.loader.exec_module(topic_classifier)


def _record(article_id="A1", title="", content="", **extra):
    return {
        "article_id": article_id,
        "title": title,
        "content": content,
        **extra,
    }


class TestClassifyArticle(unittest.TestCase):
    def test_multiple_topics_have_scores_and_topic_specific_reasons(self):
        result = topic_classifier.classify_article(
            _record(
                title="Công nhân đình công vì doanh nghiệp chậm trả lương",
                content="Tranh chấp tiền lương khiến công nhân ngừng việc.",
                topic_manual="A - Must not be written or read as a label",
            )
        )
        labels = json.loads(result["topic_labels"])
        scores = json.loads(result["topic_scores"])
        reasons = json.loads(result["topic_reasons"])
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("WAGES", labels)
        self.assertIn("LABOR_DISPUTE", labels)
        self.assertGreater(scores["WAGES"], 0)
        self.assertTrue(reasons["WAGES"]["matched_rules"])
        self.assertTrue(reasons["WAGES"]["evidence"])
        self.assertTrue(reasons["LABOR_DISPUTE"]["evidence"])
        self.assertNotIn("topic_manual", result)

    def test_weak_only_evidence_requires_review_and_emits_no_topic(self):
        result = topic_classifier.classify_article(
            _record(title="Công nhân có mặt tại sự kiện", content="Bài chỉ nhắc công nhân.")
        )
        self.assertEqual(result["relevance_status"], "REVIEW_REQUIRED")
        self.assertEqual(json.loads(result["topic_labels"]), [])
        self.assertEqual(json.loads(result["topic_scores"]), {})
        self.assertEqual(json.loads(result["topic_reasons"]), {})
        self.assertEqual(result["review_status"], "REVIEW_REQUIRED")

    def test_empty_content_cannot_be_classified_from_title_only(self):
        result = topic_classifier.classify_article(
            _record(title="Tuyển dụng lao động", content=" ")
        )
        self.assertEqual(result["relevance_status"], "REVIEW_REQUIRED")
        self.assertEqual(json.loads(result["topic_labels"]), [])

    def test_unrelated_article_has_no_topic_labels(self):
        result = topic_classifier.classify_article(
            _record(title="Đội tuyển giành chiến thắng", content="Trận đấu kết thúc.")
        )
        self.assertEqual(result["relevance_status"], "IRRELEVANT")
        self.assertEqual(json.loads(result["topic_labels"]), [])

    def test_blank_or_duplicate_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "article_id must not be blank"):
            topic_classifier.classify_records([_record(article_id=" ")])
        with self.assertRaisesRegex(ValueError, "duplicate article_id"):
            topic_classifier.classify_records(
                [_record(article_id="A1"), _record(article_id=" A1 ")]
            )

    def test_nontext_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "title must be present as text"):
            topic_classifier.classify_records([_record(title=None)])

    def test_result_has_versions_and_score_semantics(self):
        result = topic_classifier.classify_article(
            _record(
                title="Công nhân được hưởng BHXH",
                content="Quyền lợi bảo hiểm xã hội của người lao động.",
            )
        )
        self.assertEqual(result["classifier_version"], topic_classifier.CLASSIFIER_VERSION)
        self.assertEqual(
            result["source_relevance_classifier_version"],
            topic_classifier.RELEVANCE_CLASSIFIER.CLASSIFIER_VERSION,
        )
        self.assertEqual(result["taxonomy_version"], "1.0.0")


class TestTopicClassificationFiles(unittest.TestCase):
    def _write_input(self, path: Path, rows: list[dict[str, str]]) -> str:
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["article_id", "title", "content"])
            writer.writeheader()
            writer.writerows(rows)
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_csv_report_schema_stats_and_source_immutability(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "input.csv"
            output = root / "topics.csv"
            report_path = root / "report.json"
            source_hash = self._write_input(
                source,
                [
                    _record("A1", "Tuyển dụng lao động", "Doanh nghiệp có nhiều vị trí tuyển dụng."),
                    _record("A2", "Tin ngắn", ""),
                ],
            )
            report = topic_classifier.classify_from_csv(source, output, report_path)
            with output.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, list(topic_classifier.OUTPUT_COLUMNS))
                rows = list(reader)
            saved = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 2)
            self.assertEqual(saved, report)
            self.assertEqual(report["total_articles_checked"], 2)
            self.assertFalse(report["manual_annotation_fields_written"])
            self.assertEqual(
                hashlib.sha256(source.read_bytes()).hexdigest(),
                source_hash,
            )

    def test_missing_columns_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "input.csv"
            source.write_text("article_id,title\nA1,Tin\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing required columns"):
                topic_classifier.classify_from_csv(
                    source, root / "topics.csv", root / "report.json"
                )

    def test_outputs_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "input.csv"
            self._write_input(source, [_record()])
            output = root / "topics.csv"
            report_path = root / "report.json"
            output.write_text("existing", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                topic_classifier.classify_from_csv(source, output, report_path)

    def test_protected_manual_file_cannot_be_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "input.csv"
            self._write_input(source, [_record()])
            with self.assertRaisesRegex(ValueError, "protected source or review artifacts"):
                topic_classifier.classify_from_csv(
                    source,
                    topic_classifier.PROTECTED_PATHS[-1],
                    root / "report.json",
                )


if __name__ == "__main__":
    unittest.main()
