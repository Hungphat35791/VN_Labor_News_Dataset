"""Unit tests for exact-content duplicate candidate generation."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "detect_exact_duplicates.py"
SPEC = importlib.util.spec_from_file_location("detect_exact_duplicates", SRC)
detector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(detector)


def _row(article_id: str, content: str) -> dict[str, str]:
    return {"article_id": article_id, "content": content}


class TestFindCandidates(unittest.TestCase):
    def test_two_identical_contents_are_detected(self):
        candidates, stats = detector.find_candidates(
            [_row("A1", "Bài viết nguyên bản."), _row("A2", "Bài viết nguyên bản.")]
        )

        self.assertEqual(len(candidates), 2)
        self.assertEqual(stats["exact_duplicate_group_count"], 1)
        self.assertEqual(candidates[0]["duplicate_group_id"], candidates[1]["duplicate_group_id"])
        self.assertEqual(candidates[0]["content_hash"], detector.sha256_content("Bài viết nguyên bản."))

    def test_three_identical_contents_form_one_group(self):
        candidates, stats = detector.find_candidates(
            [_row("A1", "Nội dung."), _row("A2", "Nội dung."), _row("A3", "Nội dung.")]
        )

        self.assertEqual(len(candidates), 3)
        self.assertEqual(stats["exact_duplicate_group_count"], 1)
        self.assertEqual(len({row["duplicate_group_id"] for row in candidates}), 1)

    def test_different_contents_are_not_duplicates(self):
        candidates, stats = detector.find_candidates(
            [_row("A1", "Bài về cùng sự kiện."), _row("A2", "Bài viết khác về sự kiện.")]
        )

        self.assertEqual(candidates, [])
        self.assertEqual(stats["exact_duplicate_group_count"], 0)

    def test_whitespace_difference_is_not_exact_duplicate(self):
        candidates, _ = detector.find_candidates(
            [_row("A1", "Bài viết có khoảng trắng."), _row("A2", "Bài viết  có khoảng trắng.")]
        )

        self.assertEqual(candidates, [])

    def test_punctuation_difference_is_not_exact_duplicate(self):
        candidates, _ = detector.find_candidates(
            [_row("A1", "Bài viết có dấu chấm."), _row("A2", "Bài viết có dấu chấm!")]
        )

        self.assertEqual(candidates, [])

    def test_empty_content_is_excluded(self):
        candidates, stats = detector.find_candidates(
            [_row("A1", ""), _row("A2", ""), _row("A3", "   ")]
        )

        self.assertEqual(candidates, [])
        self.assertEqual(stats["empty_content_count"], 3)

    def test_blank_or_duplicate_article_ids_raise_clear_errors(self):
        with self.assertRaisesRegex(ValueError, "article_id must not be blank"):
            detector.find_candidates([_row(" ", "Text")])
        with self.assertRaisesRegex(ValueError, "duplicate article_id"):
            detector.find_candidates([_row("A1", "First"), _row("A1", "Second")])

    def test_hash_collision_does_not_confirm_different_contents(self):
        candidates, stats = detector.find_candidates(
            [_row("A1", "First text"), _row("A2", "Second text")],
            hash_function=lambda _content: "forced-collision",
        )

        self.assertEqual(candidates, [])
        self.assertEqual(stats["hash_collision_buckets_detected"], 1)

    def test_csv_has_all_required_output_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._run_csv(temp_dir, "A1,One text\nA2,One text\n")

            with paths["output"].open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, list(detector.OUTPUT_COLUMNS))
                rows = list(reader)
            self.assertEqual(len(rows), 2)

    def test_source_csv_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._run_csv(temp_dir, "A1,One text\n", run=False)

            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                detector.detect_from_csv(paths["input"], paths["input"], paths["report"])

    def test_no_duplicates_writes_header_only_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._run_csv(temp_dir, "A1,First text\nA2,Second text\n")

            with paths["output"].open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, list(detector.OUTPUT_COLUMNS))
                self.assertEqual(list(reader), [])

            self.assertTrue(paths["report"].is_file())

    def test_report_contains_requested_counts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._run_csv(temp_dir, "A1,Same\nA2,Same\nA3,\n")
            import json

            report = json.loads(paths["report"].read_text(encoding="utf-8"))
            self.assertEqual(report["total_articles_checked"], 3)
            self.assertEqual(report["empty_content_count"], 1)
            self.assertEqual(report["exact_duplicate_group_count"], 1)
            self.assertEqual(report["articles_in_groups"], 2)
            self.assertEqual(report["candidates_requiring_review"], 1)
            self.assertEqual(report["candidate_article_rows_requiring_review"], 2)

    @staticmethod
    def _run_csv(temp_dir: str, data_rows: str, run: bool = True) -> dict[str, Path]:
        root = Path(temp_dir)
        input_path = root / "source.csv"
        output_path = root / "exact_duplicate_candidates.csv"
        report_path = root / "exact_duplicate_report.json"
        input_path.write_text(
            "article_id,content\n" + data_rows,
            encoding="utf-8",
        )
        if run:
            detector.detect_from_csv(input_path, output_path, report_path)
        return {"input": input_path, "output": output_path, "report": report_path}


if __name__ == "__main__":
    unittest.main()
