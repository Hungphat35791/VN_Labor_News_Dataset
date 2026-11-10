import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PILOT_DIR = ROOT / "5_process" / "data" / "interim" / "pilot_10"
SELECTION_REPORT = PILOT_DIR / "pilot_10_selection_report.json"
PILOT_ARTICLES = PILOT_DIR / "pilot_10_articles.csv"
REVIEWER_1 = PILOT_DIR / "reviewer_1_sheet.csv"
REVIEWER_2 = PILOT_DIR / "reviewer_2_sheet.csv"
PROTOCOL = PILOT_DIR / "pilot_10_protocol.md"
DISTRIBUTION_GUIDE = (
    ROOT / "5_process" / "reports" / "pilot_10_reviewer_distribution_guide.md"
)
COMPLETION_CHECKLIST = (
    ROOT / "5_process" / "reports" / "pilot_10_completion_checklist.md"
)
ARTICLE_COLUMNS = ["article_id", "title", "content"]
REVIEW_COLUMNS = ARTICLE_COLUMNS + [
    "relevance_manual",
    "topic_manual",
    "review_reason",
    "reviewer_id",
    "review_date",
    "review_status",
]
ANNOTATION_COLUMNS = [
    "relevance_manual",
    "topic_manual",
    "review_reason",
    "reviewer_id",
    "review_date",
]


def _read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestPilotAnnotationPreparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(SELECTION_REPORT.read_text(encoding="utf-8"))
        cls.article_fields, cls.articles = _read_csv(PILOT_ARTICLES)
        cls.reviewer_1_fields, cls.reviewer_1 = _read_csv(REVIEWER_1)
        cls.reviewer_2_fields, cls.reviewer_2 = _read_csv(REVIEWER_2)

    def test_exactly_ten_unique_articles_match_selection_report(self):
        ids = [row["article_id"] for row in self.articles]
        report_ids = [record["article_id"] for record in self.report["articles"]]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, report_ids)
        self.assertEqual(self.article_fields, ARTICLE_COLUMNS)

    def test_reviewer_sheets_have_identical_source_fields_and_ids(self):
        self.assertEqual(self.reviewer_1_fields, REVIEW_COLUMNS)
        self.assertEqual(self.reviewer_2_fields, REVIEW_COLUMNS)
        source_fields_1 = [
            {field: row[field] for field in ARTICLE_COLUMNS}
            for row in self.reviewer_1
        ]
        source_fields_2 = [
            {field: row[field] for field in ARTICLE_COLUMNS}
            for row in self.reviewer_2
        ]
        self.assertEqual(source_fields_1, source_fields_2)
        self.assertEqual(source_fields_1, self.articles)
        ids = [row["article_id"] for row in self.reviewer_1]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(ids), len(set(ids)))

    def test_pilot_articles_match_canonical_source(self):
        canonical_path = ROOT / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
        with canonical_path.open(encoding="utf-8-sig", newline="") as stream:
            canonical_rows = {
                row["article_id"]: row for row in csv.DictReader(stream)
            }
        expected = [
            {
                field: canonical_rows[record["article_id"]][field]
                for field in ARTICLE_COLUMNS
            }
            for record in self.report["articles"]
        ]
        self.assertEqual(self.articles, expected)

    def test_annotations_are_blank_and_all_rows_start_pending(self):
        for rows in (self.reviewer_1, self.reviewer_2):
            self.assertEqual(len(rows), 10)
            for row in rows:
                for field in ANNOTATION_COLUMNS:
                    self.assertEqual(row[field], "")
                self.assertEqual(row["review_status"], "PENDING")

    def test_reviewer_sheets_contain_no_prediction_fields(self):
        disallowed_columns = {
            "relevance_status",
            "topic_primary",
            "topic_secondary",
            "ai_suggested_relevance",
            "ai_suggested_topic",
            "ai_prediction",
            "prediction",
        }
        self.assertTrue(disallowed_columns.isdisjoint(self.reviewer_1_fields))
        self.assertTrue(disallowed_columns.isdisjoint(self.reviewer_2_fields))

    def test_protocol_and_distribution_guide_protect_independent_review(self):
        protocol = PROTOCOL.read_text(encoding="utf-8")
        distribution = DISTRIBUTION_GUIDE.read_text(encoding="utf-8")
        for required in (
            "reviewer_1_sheet.csv",
            "reviewer_2_sheet.csv",
            "AI proposal",
            "review_reason",
            "`Relevant`, `Borderline`, `Not relevant` hoặc `Uncertain`",
            "topic A–L",
            "để `topic_manual` trống",
            "không ép đồng thuận",
        ):
            self.assertIn(required, protocol)
        for required in (
            "Reviewer 1 chỉ nhận `reviewer_1_sheet.csv`",
            "reviewer 2 chỉ nhận `reviewer_2_sheet.csv`",
            "Không trao đổi nhãn",
            "Sao lưu",
            "Không tự sửa nhãn",
            "`reviewer_id`",
            "`review_date`",
        ):
            self.assertIn(required, distribution)

    def test_completion_checklist_exists_and_all_checkboxes_are_unchecked(self):
        checklist = COMPLETION_CHECKLIST.read_text(encoding="utf-8")
        self.assertIn("độ đồng thuận", checklist.lower())
        self.assertIn("adjudication", checklist.lower())
        self.assertIn("guideline", checklist.lower())
        self.assertNotIn("[x]", checklist.lower())
        self.assertNotIn("[X]", checklist)
        checked = [
            line for line in checklist.splitlines()
            if line.lstrip().startswith("- [") and not line.startswith("- [ ]")
        ]
        self.assertEqual(checked, [])

    def test_canonical_master_and_batches_match_recorded_hashes(self):
        for relative_path, expected_hash in self.report[
            "protected_input_sha256"
        ].items():
            path = ROOT / Path(relative_path)
            self.assertTrue(path.is_file(), relative_path)
            self.assertEqual(_sha256(path), expected_hash, relative_path)


if __name__ == "__main__":
    unittest.main()
