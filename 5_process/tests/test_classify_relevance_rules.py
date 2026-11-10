"""Unit tests for the conservative P4.07 rule-based classifier."""
import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "classify_relevance_rules.py"
SPEC = importlib.util.spec_from_file_location("classify_relevance_rules", SRC)
classifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = classifier
SPEC.loader.exec_module(classifier)


def _record(title, content="", article_id="A1", **extra):
    return {
        "article_id": article_id,
        "title": title,
        "content": content,
        **extra,
    }


class TestNormalizeAndClassify(unittest.TestCase):
    def test_normalization_is_accent_and_case_insensitive(self):
        self.assertEqual(
            classifier.normalize_text("  BẢO HIỂM   Xã Hội  "),
            "bao hiem xa hoi",
        )
        self.assertEqual(classifier.normalize_text("Đình công!"), "dinh cong")

    def test_employment_recruitment_is_relevant(self):
        result = classifier.classify_article(
            _record("Doanh nghiệp tuyển dụng lao động tại Đồng Nai", "Nhiều vị trí đang tuyển.")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("EMPLOYMENT", result["topic_labels"])

    def test_unemployment_is_relevant(self):
        result = classifier.classify_article(
            _record("Công nhân mất việc sau khi nhà máy đóng cửa", "Nhiều lao động mất việc.")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("UNEMPLOYMENT", result["topic_labels"])

    def test_wages_are_relevant(self):
        result = classifier.classify_article(
            _record("Đề xuất tăng lương tối thiểu vùng cho người lao động", "...")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("WAGES", result["topic_labels"])
        self.assertIn("LABOR_POLICY", result["topic_labels"].split(";"))

    def test_social_insurance_abbreviation_is_relevant(self):
        result = classifier.classify_article(
            _record("Công nhân được hưởng BHXH một lần", "...")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("SOCIAL_INSURANCE", result["topic_labels"])

    def test_unemployment_insurance_is_not_mislabeled_as_general_unemployment(self):
        result = classifier.classify_article(
            _record("Trợ cấp bảo hiểm thất nghiệp tăng", "Hồ sơ BHTN được giải quyết.")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("UNEMPLOYMENT_INSURANCE", result["topic_labels"])
        self.assertNotIn("UNEMPLOYMENT", result["topic_labels"].split(";"))

    def test_labor_rights_are_relevant(self):
        result = classifier.classify_article(
            _record("Bảo vệ quyền lợi người lao động khi doanh nghiệp nợ lương", "...")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("LABOR_RIGHTS", result["topic_labels"])

    def test_labor_contract_is_relevant(self):
        result = classifier.classify_article(
            _record("Quy định về hợp đồng lao động có thời hạn", "...")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("LABOR_CONTRACT", result["topic_labels"])

    def test_labor_dispute_is_relevant(self):
        result = classifier.classify_article(
            _record("Công nhân đình công để đòi quyền lợi", "...")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("LABOR_DISPUTE", result["topic_labels"])

    def test_occupational_safety_is_relevant(self):
        result = classifier.classify_article(
            _record("Tai nạn lao động tại công trường khiến nhiều người bị thương", "...")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("OCCUPATIONAL_SAFETY", result["topic_labels"])

    def test_labor_policy_is_relevant(self):
        result = classifier.classify_article(
            _record("Sửa đổi Bộ luật Lao động để bảo vệ người làm công", "...")
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("LABOR_POLICY", result["topic_labels"])

    def test_one_article_can_receive_multiple_supported_topics(self):
        result = classifier.classify_article(
            _record(
                "Đình công vì doanh nghiệp chậm trả lương",
                "Tranh chấp tiền lương khiến công nhân ngừng việc.",
            )
        )
        labels = set(result["topic_labels"].split(";"))
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("LABOR_DISPUTE", labels)
        self.assertIn("WAGES", labels)

    def test_worker_word_alone_requires_review(self):
        result = classifier.classify_article(
            _record("Công nhân phát huy sáng kiến", "Bài viết chỉ nhắc đến công nhân.")
        )
        self.assertEqual(result["relevance_status"], "REVIEW_REQUIRED")
        self.assertEqual(result["review_status"], "REVIEW_REQUIRED")
        self.assertEqual(result["topic_labels"], "")

    def test_keyword_with_nonlabor_sports_context_is_irrelevant(self):
        result = classifier.classify_article(
            _record("Monaco sa thải huấn luyện viên giữa kỳ nghỉ đông", "Câu lạc bộ xác nhận.")
        )
        self.assertEqual(result["relevance_status"], "IRRELEVANT")
        self.assertEqual(result["topic_labels"], "")

    def test_generic_insurance_or_pay_mention_requires_review(self):
        result = classifier.classify_article(
            _record("Người dân lo lắng về bảo hiểm và mức lương", "Thông tin rất ngắn.")
        )
        self.assertEqual(result["relevance_status"], "REVIEW_REQUIRED")

    def test_pension_money_is_not_mislabeled_as_wages(self):
        result = classifier.classify_article(
            _record(
                "Vợ chồng cụ ông 92 tuổi ủng hộ lương hưu cho quỹ từ thiện",
                "Khoản tiền lương hưu được gia đình dành dụm.",
            )
        )
        self.assertEqual(result["relevance_status"], "REVIEW_REQUIRED")
        self.assertNotIn("WAGES", result["topic_labels"].split(";"))

    def test_insurance_article_does_not_get_incidental_safety_topic(self):
        result = classifier.classify_article(
            _record(
                "Quỹ bảo hiểm thất nghiệp hỗ trợ người dân",
                "BHXH điều chỉnh mức đóng vào quỹ bảo hiểm tai nạn lao động - bệnh nghề nghiệp.",
            )
        )
        self.assertEqual(result["relevance_status"], "RELEVANT")
        self.assertIn("UNEMPLOYMENT_INSURANCE", result["topic_labels"].split(";"))
        self.assertNotIn("OCCUPATIONAL_SAFETY", result["topic_labels"].split(";"))

    def test_incidental_job_phrase_requires_context(self):
        result = classifier.classify_article(
            _record("Chính sách an sinh mới", "Bài viết có nhắc đến việc làm.")
        )
        self.assertEqual(result["relevance_status"], "REVIEW_REQUIRED")
        self.assertNotIn("EMPLOYMENT", result["topic_labels"].split(";"))

    def test_unrelated_article_without_labor_cues_is_irrelevant(self):
        result = classifier.classify_article(
            _record("Đội tuyển giành chiến thắng", "Trận đấu diễn ra tối qua.")
        )
        self.assertEqual(result["relevance_status"], "IRRELEVANT")

    def test_empty_content_requires_review_even_with_title_match(self):
        result = classifier.classify_article(_record("Tuyển dụng lao động", "   "))
        self.assertEqual(result["relevance_status"], "REVIEW_REQUIRED")
        self.assertEqual(result["topic_labels"], "")

    def test_missing_body_and_title_requires_review(self):
        result = classifier.classify_article(_record("", ""))
        self.assertEqual(result["relevance_status"], "REVIEW_REQUIRED")

    def test_existing_relevance_status_is_ignored(self):
        relevant = classifier.classify_article(
            _record(
                "Doanh nghiệp tuyển dụng lao động",
                "Thông báo nhiều vị trí việc làm.",
                relevance_status="irrelevant",
            )
        )
        irrelevant = classifier.classify_article(
            _record("Tin bóng đá", "Trận đấu kết thúc.", relevance_status="relevant_auto")
        )
        self.assertEqual(relevant["relevance_status"], "RELEVANT")
        self.assertEqual(irrelevant["relevance_status"], "IRRELEVANT")

    def test_match_evidence_method_and_versions_are_present(self):
        result = classifier.classify_article(
            _record("Đóng BHXH cho người lao động", "Doanh nghiệp nợ đóng BHXH.")
        )
        self.assertEqual(result["method"], "rule_based")
        self.assertEqual(result["classifier_version"], classifier.CLASSIFIER_VERSION)
        self.assertEqual(result["taxonomy_version"], classifier.TAXONOMY_VERSION)
        self.assertTrue(json.loads(result["matched_keywords"]))
        self.assertTrue(json.loads(result["matched_rules"]))
        self.assertTrue(result["reason"])


class TestInputOutput(unittest.TestCase):
    def test_blank_or_duplicate_article_ids_raise_clear_errors(self):
        with self.assertRaisesRegex(ValueError, "article_id must not be blank"):
            classifier.classify_records([_record("Tiêu đề", "Nội dung", article_id=" ")])
        with self.assertRaisesRegex(ValueError, "duplicate article_id"):
            classifier.classify_records(
                [_record("Một", "Nội dung", "A1"), _record("Hai", "Nội dung", " A1 ")]
            )

    def test_every_valid_id_is_written_once(self):
        records = [
            _record("Tuyển dụng lao động", "Vị trí việc làm.", "A1"),
            _record("Tin thể thao", "Trận đấu.", "A2"),
        ]
        results, stats = classifier.classify_records(records)
        self.assertEqual([row["article_id"] for row in results], ["A1", "A2"])
        self.assertEqual(len({row["article_id"] for row in results}), 2)
        self.assertEqual(stats["total_articles_checked"], 2)

    def test_topics_are_limited_to_taxonomy(self):
        results, _ = classifier.classify_records(
            [_record("Tuyển dụng lao động và BHXH", "Thông tin việc làm.", "A1")]
        )
        valid = set(classifier.TOPIC_ORDER)
        self.assertTrue(set(results[0]["topic_labels"].split(";")).issubset(valid))

    def test_source_csv_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.csv"
            source.write_text("article_id,title,content\nA1,Tin,Noi dung\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                classifier.detect_from_csv(source, source, Path(temp_dir) / "report.json")

    def test_p402_through_p406_artifacts_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.csv"
            source.write_text("article_id,title,content\nA1,Tin,Noi dung\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not overwrite P4.02-P4.06"):
                classifier.detect_from_csv(
                    source,
                    classifier.PROTECTED_ARTIFACTS[-1],
                    Path(temp_dir) / "report.json",
                )

    def test_csv_and_json_report_statistics_match_results(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "input.csv"
            output = root / "results.csv"
            report_path = root / "report.json"
            with source.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=["article_id", "title", "content", "relevance_status"]
                )
                writer.writeheader()
                writer.writerow(
                    _record("Đình công do chậm trả lương", "Tranh chấp tiền lương.", "A1",
                            relevance_status="irrelevant")
                )
                writer.writerow(_record("Bóng đá", "Trận đấu.", "A2"))
                writer.writerow(_record("Công nhân", "", "A3"))

            input_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            report = classifier.detect_from_csv(source, output, report_path)
            with output.open(encoding="utf-8-sig", newline="") as stream:
                results = list(csv.DictReader(stream))
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(len(results), 3)
            self.assertEqual(
                sum(row["relevance_status"] == "RELEVANT" for row in results),
                report["relevant_count"],
            )
            self.assertEqual(
                sum(row["relevance_status"] == "IRRELEVANT" for row in results),
                report["irrelevant_count"],
            )
            self.assertEqual(
                sum(row["relevance_status"] == "REVIEW_REQUIRED" for row in results),
                report["review_required_count"],
            )
            self.assertEqual(sum(saved_report["topic_distribution"].values()), 2)
            self.assertEqual(saved_report["input_sha256"], input_hash)
            self.assertEqual(saved_report["total_articles_checked"], len(results))

    def test_repeated_classification_is_deterministic(self):
        record = _record("Tăng lương tối thiểu cho công nhân", "Doanh nghiệp điều chỉnh.")
        self.assertEqual(
            classifier.classify_article(record), classifier.classify_article(record)
        )


if __name__ == "__main__":
    unittest.main()
