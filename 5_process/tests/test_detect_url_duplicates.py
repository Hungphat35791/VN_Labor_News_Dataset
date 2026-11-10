"""Unit tests for URL duplicate candidate generation."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "detect_url_duplicates.py"
SPEC = importlib.util.spec_from_file_location("detect_url_duplicates", SRC)
detector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(detector)


def _row(article_id: str, url: str) -> dict[str, str]:
    return {"article_id": article_id, "source_url": url}


class TestNormalizeUrl(unittest.TestCase):
    def test_equivalent_scheme_host_case_www_fragment_and_trailing_slash(self):
        self.assertEqual(
            detector.normalize_url("HTTP://WWW.Tuoitre.vn/Bai-viet/#phan-1"),
            detector.normalize_url("https://tuoitre.vn/Bai-viet"),
        )

    def test_tracking_parameters_are_removed(self):
        self.assertEqual(
            detector.normalize_url(
                "https://example.vn/story?id=12&utm_source=newsletter&fbclid=abc"
            ),
            detector.normalize_url("http://www.example.vn/story?id=12"),
        )

    def test_meaningful_query_parameters_are_retained(self):
        self.assertNotEqual(
            detector.normalize_url("https://example.vn/story?id=12"),
            detector.normalize_url("https://example.vn/story?id=13"),
        )
        self.assertNotEqual(
            detector.normalize_url("https://example.vn/story?ref=12"),
            detector.normalize_url("https://example.vn/story?ref=13"),
        )

    def test_query_parameter_order_is_preserved(self):
        self.assertNotEqual(
            detector.normalize_url("https://example.vn/story?item=1&item=2"),
            detector.normalize_url("https://example.vn/story?item=2&item=1"),
        )

    def test_different_hostnames_are_not_equivalent(self):
        self.assertNotEqual(
            detector.normalize_url("https://example.vn/story"),
            detector.normalize_url("https://other.example.vn/story"),
        )

    def test_invalid_urls_return_empty_comparison_key(self):
        for value in (
            "",
            "not a url",
            "ftp://example.vn/story",
            "https:///story",
            "https://example.vn:bad/story",
            "https://user@example.vn/story",
            "https://bad host.vn/story",
        ):
            with self.subTest(value=value):
                self.assertEqual(detector.normalize_url(value), "")


class TestFindCandidates(unittest.TestCase):
    def test_multiple_records_with_same_normalized_url_create_all_pairs(self):
        candidates, invalid_count = detector.find_candidates(
            [
                _row("A3", "https://www.example.vn/story?utm_source=x"),
                _row("A1", "http://example.vn/story/"),
                _row("A2", "https://example.vn/story#section"),
            ]
        )

        self.assertEqual(invalid_count, 0)
        self.assertEqual(len(candidates), 3)
        self.assertEqual(
            {(row["article_id_1"], row["article_id_2"]) for row in candidates},
            {("A1", "A2"), ("A1", "A3"), ("A2", "A3")},
        )
        self.assertTrue(all(row["review_status"] == "REVIEW_REQUIRED" for row in candidates))
        self.assertTrue(all(row["duplicate_type"] == "URL_DUPLICATE" for row in candidates))

    def test_invalid_url_is_counted_and_not_a_candidate(self):
        candidates, invalid_count = detector.find_candidates(
            [_row("A1", "https://example.vn/story"), _row("A2", "invalid")]
        )

        self.assertEqual(candidates, [])
        self.assertEqual(invalid_count, 1)

    def test_no_duplicate_urls_returns_empty_candidates(self):
        candidates, invalid_count = detector.find_candidates(
            [
                _row("A1", "https://example.vn/story?id=1"),
                _row("A2", "https://example.vn/story?id=2"),
                _row("A3", "https://other.example.vn/story?id=1"),
            ]
        )

        self.assertEqual(candidates, [])
        self.assertEqual(invalid_count, 0)

    def test_blank_or_duplicate_article_ids_fail_explicitly(self):
        with self.assertRaisesRegex(ValueError, "must not be blank"):
            detector.find_candidates([_row("", "https://example.vn/story")])
        with self.assertRaisesRegex(ValueError, "duplicate article_id"):
            detector.find_candidates(
                [
                    _row("A1", "https://example.vn/one"),
                    _row("A1", "https://example.vn/two"),
                ]
            )

    def test_csv_output_preserves_original_urls_and_rejects_input_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.csv"
            output = root / "derived" / "candidates.csv"
            source.write_text(
                "article_id,title,content,publish_date,source_name,source_url\n"
                "A1,t1,c1,2024-01-01,s1,https://www.example.vn/story?utm_source=x\n"
                "A2,t2,c2,2024-01-02,s2,http://example.vn/story/\n",
                encoding="utf-8",
            )

            count, invalid_count, input_count, input_hash = detector.detect_from_csv(
                source, output
            )

            self.assertEqual((count, invalid_count), (1, 0))
            self.assertEqual(input_count, 2)
            self.assertEqual(len(input_hash), 64)
            written = output.read_text(encoding="utf-8-sig")
            self.assertIn("https://www.example.vn/story?utm_source=x", written)
            self.assertIn("http://example.vn/story/", written)
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                detector.detect_from_csv(source, source)

    def test_url_report_records_source_candidate_hashes_and_waiting_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.csv"
            output = root / "candidates.csv"
            report = root / "url_report.json"
            source.write_text(
                "article_id,source_url\nA1,https://example.vn/a\nA2,https://example.vn/b\n",
                encoding="utf-8",
            )
            count, invalid, input_count, input_hash = detector.detect_from_csv(
                source, output
            )
            detector._write_report(
                source, output, report, invalid, count, input_count, input_hash
            )
            data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["candidate_pair_count"], 0)
        self.assertEqual(data["input_article_count"], 2)
        self.assertEqual(data["status"], "NO_CANDIDATES_FOUND")
        self.assertEqual(len(data["input_sha256"]), 64)
        self.assertEqual(len(data["candidate_sha256"]), 64)

    def test_report_is_not_written_if_input_changes_after_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.csv"
            output = root / "candidates.csv"
            report = root / "url_report.json"
            source.write_text(
                "article_id,source_url\nA1,https://example.vn/a\n",
                encoding="utf-8",
            )
            count, invalid, input_count, input_hash = detector.detect_from_csv(
                source, output
            )
            source.write_text(
                "article_id,source_url\nA1,https://example.vn/changed\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "changed after candidate generation"):
                detector._write_report(
                    source, output, report, invalid, count, input_count, input_hash
                )
            self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
