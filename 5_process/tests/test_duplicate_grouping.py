"""Unit tests for duplicate candidate grouping."""
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "group_duplicate_candidates.py"
SPEC = importlib.util.spec_from_file_location("group_duplicate_candidates", SRC)
grouping = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(grouping)


def _write_candidates(root: Path, url_rows=None, exact_rows=None, near_rows=None):
    sources = (
        (root / "url_duplicate_candidates.csv", url_rows or []),
        (root / "exact_duplicate_candidates.csv", exact_rows or []),
        (root / "near_duplicate_candidates.csv", near_rows or []),
    )
    for path, rows in sources:
        if path.name.startswith("exact"):
            headers = [
                "duplicate_group_id",
                "article_id",
                "content_hash",
                "duplicate_type",
                "method",
                "reason",
                "detector_version",
                "review_status",
            ]
        elif path.name.startswith("url"):
            headers = [
                "article_id_1",
                "article_id_2",
                "original_url_1",
                "original_url_2",
                "normalized_url",
                "duplicate_type",
                "method",
                "reason",
                "detector_version",
                "review_status",
                "version_evidence",
            ]
        else:
            headers = [
                "article_id_1",
                "article_id_2",
                "similarity_score",
                "duplicate_type",
                "method",
                "threshold",
                "reason",
                "detector_version",
                "review_status",
                "version_evidence",
            ]
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
    return tuple(path for path, _ in sources)


def _edge(left, right, duplicate_type="NEAR_DUPLICATE", method="tfidf", **extra):
    return {
        "article_id_1": left,
        "article_id_2": right,
        "duplicate_type": duplicate_type,
        "method": method,
        "reason": "candidate evidence",
        **extra,
    }


def _exact(group_id, article_id, content_hash="hash-a"):
    return {
        "duplicate_group_id": group_id,
        "article_id": article_id,
        "content_hash": content_hash,
        "duplicate_type": "EXACT_CONTENT_DUPLICATE",
        "method": "sha256",
        "reason": "raw content hash and text equal",
    }


class TestDuplicateGrouping(unittest.TestCase):
    def _build(self, url_rows=None, exact_rows=None, near_rows=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = _write_candidates(
                Path(temp_dir), url_rows=url_rows, exact_rows=exact_rows, near_rows=near_rows
            )
            return grouping.build_groups(paths)

    def test_pair_forms_group_of_two(self):
        rows, report = self._build(near_rows=[_edge("A", "B")])
        self.assertEqual(report["total_groups"], 1)
        self.assertEqual(report["total_articles_in_groups"], 2)
        self.assertEqual({row["article_id"] for row in rows}, {"A", "B"})

    def test_exact_candidates_form_group_of_three(self):
        rows, report = self._build(
            exact_rows=[_exact("E1", "A"), _exact("E1", "B"), _exact("E1", "C")]
        )
        self.assertEqual(report["total_groups"], 1)
        self.assertEqual({row["group_size"] for row in rows}, {3})
        self.assertEqual(report["total_candidate_pairs"], 3)

    def test_transitive_a_b_and_b_c_form_one_group(self):
        rows, report = self._build(
            near_rows=[_edge("A", "B"), _edge("B", "C")]
        )
        self.assertEqual(report["total_groups"], 1)
        self.assertEqual({row["article_id"] for row in rows}, {"A", "B", "C"})
        self.assertEqual({row["group_size"] for row in rows}, {3})

    def test_article_linked_across_types_joins_same_group_and_keeps_types(self):
        rows, report = self._build(
            url_rows=[_edge("A", "B", "URL_DUPLICATE", "url_norm")],
            near_rows=[_edge("B", "C", "NEAR_DUPLICATE", "tfidf")],
        )
        self.assertEqual(report["total_groups"], 1)
        self.assertEqual(
            {row["duplicate_types"] for row in rows},
            {"NEAR_DUPLICATE; URL_DUPLICATE"},
        )
        self.assertEqual(
            {row["detection_methods"] for row in rows},
            {"tfidf; url_norm"},
        )

    def test_no_candidates_produces_no_groups(self):
        rows, report = self._build()
        self.assertEqual(rows, [])
        self.assertEqual(report["total_groups"], 0)
        self.assertEqual(report["total_articles_in_groups"], 0)

    def test_blank_article_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be blank"):
            self._build(near_rows=[_edge("", "B")])

    def test_duplicate_article_id_in_exact_group_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate article_id within exact"):
            self._build(exact_rows=[_exact("E1", "A"), _exact("E1", "A")])

    def test_non_candidate_article_never_enters_group(self):
        rows, _ = self._build(near_rows=[_edge("A", "B")])
        self.assertNotIn("C", {row["article_id"] for row in rows})

    def test_output_schema_and_reports_are_written(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _write_candidates(root, near_rows=[_edge("A", "B")])
            output = root / "duplicate_groups.csv"
            report_path = root / "duplicate_grouping_report.json"
            report = grouping.group_from_files(sources, output, report_path)

            with output.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, list(grouping.OUTPUT_COLUMNS))
                self.assertEqual(len(list(reader)), 2)
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_report["total_groups"], report["total_groups"])

    def test_no_candidates_writes_csv_header_and_empty_group_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _write_candidates(root)
            output = root / "duplicate_groups.csv"
            report_path = root / "duplicate_grouping_report.json"
            grouping.group_from_files(sources, output, report_path)

            with output.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, list(grouping.OUTPUT_COLUMNS))
                self.assertEqual(list(reader), [])

    def test_group_ids_are_deterministic_for_same_candidates(self):
        first_rows, _ = self._build(near_rows=[_edge("C", "D"), _edge("A", "B")])
        second_rows, _ = self._build(near_rows=[_edge("A", "B"), _edge("C", "D")])
        self.assertEqual(
            [(row["article_id"], row["duplicate_group_id"]) for row in first_rows],
            [(row["article_id"], row["duplicate_group_id"]) for row in second_rows],
        )

    def test_candidate_edges_and_reasons_are_preserved(self):
        rows, _ = self._build(
            near_rows=[_edge("A", "B", similarity_score="0.91", threshold="0.85")]
        )
        details = json.loads(rows[0]["candidate_pairs_json"])
        self.assertEqual(details[0]["similarity_score"], "0.91")
        self.assertEqual(details[0]["threshold"], "0.85")
        self.assertEqual(details[0]["reason"], "candidate evidence")
        self.assertEqual(details[0]["source_file"], "near_duplicate_candidates.csv")

    def test_version_duplicate_requires_explicit_lineage_evidence(self):
        with self.assertRaisesRegex(ValueError, "requires explicit version_evidence"):
            self._build(
                near_rows=[
                    _edge("A", "B", "VERSION_DUPLICATE", version_evidence="")
                ]
            )

    def test_version_duplicate_with_evidence_is_preserved(self):
        rows, report = self._build(
            near_rows=[
                _edge(
                    "A",
                    "B",
                    "VERSION_DUPLICATE",
                    "source_revision_history",
                    version_evidence="same canonical document; revisions timestamped",
                )
            ]
        )
        self.assertTrue(report["version_duplicate_evidence_available"])
        self.assertIn("VERSION_DUPLICATE", rows[0]["duplicate_types"])
        self.assertIn("version_evidence", rows[0]["candidate_pairs_json"])

    def test_output_path_cannot_overwrite_candidate_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sources = _write_candidates(root, near_rows=[_edge("A", "B")])
            rows, report = grouping.build_groups(sources)
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                grouping.group_from_files(sources, sources[0], root / "report.json")

    def test_duplicate_pair_rows_are_deduplicated_without_losing_distinct_evidence(self):
        rows, report = self._build(
            near_rows=[
                _edge("A", "B", reason="one"),
                _edge("B", "A", reason="one"),
                _edge("A", "B", reason="second method", method="other"),
            ]
        )
        self.assertEqual(report["total_candidate_pairs"], 1)
        self.assertEqual(report["total_groups"], 1)
        evidence = json.loads(rows[0]["candidate_pairs_json"])
        self.assertEqual(len(evidence), 2)
        self.assertEqual(rows[0]["candidate_pair_count"], 1)


if __name__ == "__main__":
    unittest.main()
