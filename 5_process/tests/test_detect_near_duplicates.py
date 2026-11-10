"""Unit tests for P4.04 near-duplicate candidate generation."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "detect_near_duplicates.py"
SPEC = importlib.util.spec_from_file_location("detect_near_duplicates", SRC)
detector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(detector)


def _row(article_id: str, content: str) -> dict[str, str]:
    return {"article_id": article_id, "content": content}


def _similarity_pairs(contents: list[str], threshold: float) -> list[tuple[int, int, float]]:
    """Small deterministic stand-in for the shared TF-IDF implementation."""
    pairs = []
    for left in range(len(contents)):
        for right in range(left + 1, len(contents)):
            if contents[left] == contents[right]:
                score = 1.0
            elif "shared article wording" in contents[left] and "shared article wording" in contents[right]:
                score = 0.91
            else:
                score = 0.1
            if score >= threshold:
                pairs.append((left, right, score))
    return pairs


class TestFindCandidates(unittest.TestCase):
    def test_similar_articles_at_or_above_threshold_are_candidates(self):
        candidates, _ = detector.find_candidates(
            [
                _row("A1", "shared article wording and original details one"),
                _row("A2", "shared article wording and revised details two"),
            ],
            threshold=0.85,
            pair_finder=_similarity_pairs,
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["similarity_score"], 0.91)

    def test_different_articles_are_not_candidates(self):
        candidates, _ = detector.find_candidates(
            [_row("A1", "first unrelated article"), _row("A2", "second unrelated text")],
            pair_finder=_similarity_pairs,
        )

        self.assertEqual(candidates, [])

    def test_exact_content_matches_are_excluded_consistent_with_p403(self):
        content = "An exact article body with enough distinct words to compare."
        candidates, _ = detector.find_candidates(
            [_row("A1", content), _row("A2", content)],
            pair_finder=_similarity_pairs,
        )

        self.assertEqual(candidates, [])

    def test_existing_tfidf_implementation_detects_similar_text(self):
        shared = " ".join(
            [
                "nguoi lao dong",
                "tien luong",
                "bao hiem xa hoi",
                "doanh nghiep",
                "hop dong lao dong",
                "quyen loi",
                "thoi gian lam viec",
                "chinh sach viec lam",
                "cong doan",
                "viec lam",
                "thi truong lao dong",
                "ho tro nguoi lao dong",
                "bao hiem that nghiep",
                "an toan lao dong",
                "nghi viec",
                "nguon nhan luc",
            ]
        )
        pair_finder = detector._load_existing_pair_finder()
        candidates, _ = detector.find_candidates(
            [
                _row("A1", f"{shared} noi dung rieng thu nhat"),
                _row("A2", f"{shared} noi dung rieng thu hai"),
            ],
            threshold=0.85,
            pair_finder=pair_finder,
        )

        self.assertEqual(len(candidates), 1)
        self.assertGreaterEqual(candidates[0]["similarity_score"], 0.85)

    def test_empty_and_whitespace_only_content_are_skipped(self):
        candidates, stats = detector.find_candidates(
            [_row("A1", ""), _row("A2", "  \t\n"), _row("A3", "valid text")],
            pair_finder=_similarity_pairs,
        )

        self.assertEqual(candidates, [])
        self.assertEqual(stats["empty_content_count"], 2)

    def test_blank_or_duplicate_article_ids_raise_clear_errors(self):
        with self.assertRaisesRegex(ValueError, "article_id must not be blank"):
            detector.find_candidates([_row("", "valid text")], pair_finder=_similarity_pairs)
        with self.assertRaisesRegex(ValueError, "duplicate article_id"):
            detector.find_candidates(
                [_row("A1", "first text"), _row("A1", "second text")],
                pair_finder=_similarity_pairs,
            )

    def test_pairs_are_sorted_and_emitted_once(self):
        def duplicate_pairs(contents, _threshold):
            return [(0, 1, 0.91), (1, 0, 0.92), (0, 1, 0.91)]

        candidates, _ = detector.find_candidates(
            [_row("B2", "first"), _row("A1", "second")],
            pair_finder=duplicate_pairs,
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual((candidates[0]["article_id_1"], candidates[0]["article_id_2"]), ("A1", "B2"))
        self.assertEqual(candidates[0]["similarity_score"], 0.92)

    def test_similarity_scores_are_bounded(self):
        candidates, _ = detector.find_candidates(
            [_row("A1", "first"), _row("A2", "second")],
            pair_finder=lambda _contents, _threshold: [(0, 1, 1.0001)],
        )

        self.assertEqual(candidates[0]["similarity_score"], 1.0)
        self.assertGreaterEqual(candidates[0]["similarity_score"], 0.0)
        self.assertLessEqual(candidates[0]["similarity_score"], 1.0)

    def test_all_required_csv_fields_and_review_status_are_written(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path, output_path, report_path = self._run_csv(
                temp_dir,
                "A1,shared article wording one\nA2,shared article wording two\n",
                pair_finder=_similarity_pairs,
            )

            with output_path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, list(detector.OUTPUT_COLUMNS))
                rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["duplicate_type"], "NEAR_DUPLICATE")
            self.assertEqual(rows[0]["review_status"], "REVIEW_REQUIRED")
            self.assertTrue(report_path.is_file())

    def test_source_csv_and_p402_p403_artifacts_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path, output_path, report_path = self._paths(temp_dir)
            input_path.write_text("article_id,content\nA1,text\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                detector.detect_from_csv(input_path, input_path, report_path)
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                detector.detect_from_csv(input_path, detector.EXACT_CANDIDATES, report_path)

    def test_no_candidates_writes_header_only_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, output_path, _ = self._run_csv(
                temp_dir,
                "A1,unrelated first article\nA2,unrelated second article\n",
                pair_finder=_similarity_pairs,
            )

            with output_path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, list(detector.OUTPUT_COLUMNS))
                self.assertEqual(list(reader), [])

    def test_threshold_out_of_range_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "greater than 0"):
            detector.find_candidates([], threshold=0.0, pair_finder=_similarity_pairs)
        with self.assertRaisesRegex(ValueError, "greater than 0"):
            detector.find_candidates([], threshold=1.1, pair_finder=_similarity_pairs)

    @staticmethod
    def _paths(temp_dir: str) -> tuple[Path, Path, Path]:
        root = Path(temp_dir)
        return (
            root / "source.csv",
            root / "near_duplicate_candidates.csv",
            root / "near_duplicate_report.json",
        )

    @classmethod
    def _run_csv(cls, temp_dir: str, data_rows: str, pair_finder):
        input_path, output_path, report_path = cls._paths(temp_dir)
        input_path.write_text("article_id,content\n" + data_rows, encoding="utf-8")
        detector.detect_from_csv(
            input_path,
            output_path,
            report_path,
            threshold=0.85,
            pair_finder=pair_finder,
        )
        return input_path, output_path, report_path


if __name__ == "__main__":
    unittest.main()
