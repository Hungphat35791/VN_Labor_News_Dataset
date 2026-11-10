"""Classify labor relevance with conservative, reviewable Vietnamese keyword rules."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
INPUT_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
OUTPUT_DEFAULT = REPO / "5_process" / "data" / "interim" / "relevance_results.csv"
REPORT_DEFAULT = REPO / "5_process" / "reports" / "relevance_rule_report.json"

CLASSIFIER_VERSION = "1.0.0"
TAXONOMY_VERSION = "1.0.0"
METHOD = "rule_based"
RELEVANT = "RELEVANT"
IRRELEVANT = "IRRELEVANT"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
STATUSES = (RELEVANT, IRRELEVANT, REVIEW_REQUIRED)
AUTO_CLASSIFIED = "AUTO_CLASSIFIED"

TOPIC_ORDER = (
    "EMPLOYMENT",
    "UNEMPLOYMENT",
    "WAGES",
    "SOCIAL_INSURANCE",
    "UNEMPLOYMENT_INSURANCE",
    "LABOR_RIGHTS",
    "LABOR_CONTRACT",
    "LABOR_DISPUTE",
    "OCCUPATIONAL_SAFETY",
    "LABOR_POLICY",
)

REQUIRED_COLUMNS = ("article_id", "title", "content")
OUTPUT_COLUMNS = (
    "article_id",
    "relevance_status",
    "topic_labels",
    "matched_keywords",
    "matched_rules",
    "reason",
    "method",
    "classifier_version",
    "taxonomy_version",
    "review_status",
)

PROTECTED_ARTIFACTS = (
    REPO / "5_process" / "data" / "interim" / "url_duplicate_candidates.csv",
    REPO / "5_process" / "data" / "interim" / "exact_duplicate_candidates.csv",
    REPO / "5_process" / "data" / "interim" / "near_duplicate_candidates.csv",
    REPO / "5_process" / "data" / "interim" / "duplicate_groups.csv",
    REPO / "5_process" / "reports" / "exact_duplicate_report.json",
    REPO / "5_process" / "reports" / "near_duplicate_report.json",
    REPO / "5_process" / "reports" / "duplicate_grouping_report.json",
    REPO / "5_process" / "config" / "duplicate_taxonomy.md",
    REPO / "5_process" / "config" / "relevance_taxonomy.md",
)


@dataclass(frozen=True)
class TopicRule:
    rule_id: str
    topic: str
    phrases: tuple[str, ...]
    context_phrases: tuple[str, ...] = ()


TOPIC_RULES = (
    TopicRule(
        "EMPLOYMENT_RECRUITMENT",
        "EMPLOYMENT",
        (
            "tuyen dung lao dong",
            "tuyen dung cong nhan",
            "tuyen dung nhan vien",
            "tuyen dung",
            "nhu cau tuyen dung",
            "thi truong lao dong",
            "cung lao dong",
            "cau lao dong",
            "thieu hut lao dong",
            "nhu cau nhan luc",
            "tuyen cong nhan",
            "ngay hoi viec lam",
            "san giao dich viec lam",
            "gioi thieu viec lam",
            "co hoi viec lam",
            "tao viec lam",
            "giai quyet viec lam",
            "tim viec",
        ),
    ),
    TopicRule(
        "EMPLOYMENT_CONTEXTUAL_JOB_REFERENCE",
        "EMPLOYMENT",
        ("viec lam",),
        (
            "tuyen dung",
            "thi truong lao dong",
            "nhu cau nhan luc",
            "tao viec lam",
            "tim viec",
            "cong nhan",
            "nguoi lao dong",
            "nhan vien",
        ),
    ),
    TopicRule(
        "UNEMPLOYMENT_JOB_LOSS",
        "UNEMPLOYMENT",
        (
            "mat viec lam",
            "mat viec",
            "that nghiep gia tang",
            "ty le that nghiep",
            "nguoi that nghiep",
            "lao dong that nghiep",
            "cat giam lao dong",
            "cat giam nhan su",
            "sa thai hang loat",
            "giam gio lam",
            "giam thoi gian lam viec",
        ),
    ),
    TopicRule(
        "WAGES_PAY",
        "WAGES",
        (
            "luong toi thieu",
            "luong toi thieu vung",
            "dieu chinh tien luong",
            "no luong",
            "cham tra luong",
            "tra luong",
            "tien cong",
            "luong thang 13",
            "thuong tet cho nguoi lao dong",
            "thuong tet cong nhan",
        ),
    ),
    TopicRule(
        "WAGES_CONTEXTUAL_GENERAL_PAY",
        "WAGES",
        ("tien luong", "cai cach tien luong", "luong co so"),
        (
            "cong nhan",
            "nguoi lao dong",
            "lao dong",
            "nhan vien",
            "hop dong lao dong",
        ),
    ),
    TopicRule(
        "WAGES_CONTEXTUAL_BONUS",
        "WAGES",
        ("thuong tet", "muc thuong tet"),
        (
            "cong nhan",
            "nguoi lao dong",
            "nhan vien",
            "doanh nghiep",
            "cong ty",
            "nha may",
            "cong doan",
            "tien thuong",
            "luong",
        ),
    ),
    TopicRule(
        "SOCIAL_INSURANCE_BHXH",
        "SOCIAL_INSURANCE",
        (
            "bao hiem xa hoi",
            "bhxh",
            "b h x h",
            "dong bhxh",
            "no dong bhxh",
            "no bhxh",
            "truy dong bhxh",
            "huong bhxh",
            "rut bhxh mot lan",
            "che do bhxh",
            "quy bhxh",
            "che do huu tri",
            "huong luong huu",
            "dieu kien huong luong huu",
        ),
    ),
    TopicRule(
        "UNEMPLOYMENT_INSURANCE_BHTN",
        "UNEMPLOYMENT_INSURANCE",
        (
            "bao hiem that nghiep",
            "bhtn",
            "b h t n",
            "tro cap that nghiep",
            "quy bao hiem that nghiep",
            "quy bhtn",
            "che do bao hiem that nghiep",
        ),
    ),
    TopicRule(
        "LABOR_RIGHTS_ENTITLEMENTS",
        "LABOR_RIGHTS",
        (
            "quyen loi nguoi lao dong",
            "quyen loi cua nguoi lao dong",
            "quyen loi cong nhan",
            "quyen cua nguoi lao dong",
            "bao ve quyen loi nguoi lao dong",
            "cuong buc lao dong",
            "ep buoc lao dong",
            "boc lot lao dong",
            "phan biet doi xu voi nguoi lao dong",
            "doi xu bat cong voi cong nhan",
        ),
    ),
    TopicRule(
        "LABOR_CONTRACT_EMPLOYMENT",
        "LABOR_CONTRACT",
        (
            "hop dong lao dong",
            "hop dong lam viec",
            "cham dut hop dong lao dong",
            "don phuong cham dut hop dong",
            "gia han hop dong lao dong",
            "ky hop dong lao dong",
            "hop dong thu viec",
            "hop dong co thoi han",
            "hop dong khong xac dinh thoi han",
        ),
    ),
    TopicRule(
        "LABOR_DISPUTE_COLLECTIVE",
        "LABOR_DISPUTE",
        (
            "tranh chap lao dong",
            "tranh chap tien luong",
            "dinh cong",
            "ngung viec tap the",
            "ngung viec",
            "doi thoai tai noi lam viec",
            "thuong luong tap the",
            "khieu nai tien luong",
            "khieu kien tien luong",
        ),
    ),
    TopicRule(
        "OCCUPATIONAL_SAFETY_WORKPLACE",
        "OCCUPATIONAL_SAFETY",
        (
            "an toan lao dong",
            "tai nan lao dong",
            "benh nghe nghiep",
            "ve sinh lao dong",
            "bao ho lao dong",
            "huan luyen an toan lao dong",
            "kiem dinh an toan lao dong",
            "mat an toan tai noi lam viec",
        ),
        (
            "kiem tra an toan",
            "huan luyen an toan",
            "bao dam an toan",
            "vi pham quy dinh an toan",
            "tai nan tai nha may",
            "tai nan tai cong truong",
            "phong ngua tai nan",
            "an toan ve sinh lao dong",
        ),
    ),
    TopicRule(
        "LABOR_POLICY_LEGISLATION",
        "LABOR_POLICY",
        (
            "chinh sach lao dong",
            "chinh sach viec lam",
            "phap luat lao dong",
            "bo luat lao dong",
            "luat lao dong",
            "quy dinh ve nguoi lao dong",
            "quy dinh ve lao dong",
            "chinh sach cho nguoi lao dong",
            "ho tro viec lam",
            "dao tao nghe",
            "chuyen doi nghe",
            "luong toi thieu",
            "luong toi thieu vung",
        ),
    ),
)

WEAK_RULES = (
    ("WEAK_WORKER_MENTION", ("nguoi lao dong", "cong nhan", "lao dong")),
    ("WEAK_GENERIC_PAY", ("luong", "tien thuong", "thuong tet")),
    ("WEAK_GENERIC_INSURANCE", ("bao hiem", "bao hiem y te")),
    ("WEAK_GENERIC_EMPLOYMENT", ("nhan su", "viec lam")),
    ("WEAK_DISMISSAL_TERM", ("sa thai", "bi sa thai")),
    ("WEAK_EMPLOYMENT_CONTEXT", ("doanh nghiep", "nha may", "cong ty")),
)

SPORTS_DISMISSAL_CONTEXT = (
    "huan luyen vien",
    "cau lac bo",
    "doi bong",
    "bong da",
    "giai dau",
    "cau thu",
)


def normalize_text(value: str) -> str:
    """Create an accent-insensitive comparison form without changing source text."""
    normalized = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    without_marks = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


def _compile_phrase_matcher(phrases: set[str]) -> tuple[re.Pattern[str] | None, dict[str, str]]:
    canonical = {normalize_text(phrase): phrase for phrase in phrases}
    canonical = {key: value for key, value in canonical.items() if key}
    if not canonical:
        return None, {}
    alternatives = sorted(canonical, key=lambda value: (-len(value), value))
    pattern = re.compile(
        r"(?=(?<![a-z0-9])(?P<phrase>"
        + "|".join(re.escape(phrase) for phrase in alternatives)
        + r")(?![a-z0-9]))"
    )
    return pattern, canonical


_TOPIC_PHRASE_RULES: dict[str, set[str]] = {}
_CONTEXT_PHRASES: set[str] = set()
for _rule in TOPIC_RULES:
    for _phrase in _rule.phrases:
        _TOPIC_PHRASE_RULES.setdefault(normalize_text(_phrase), set()).add(_rule.rule_id)
    _CONTEXT_PHRASES.update(_rule.context_phrases)
_TOPIC_MATCHER, _TOPIC_CANONICAL = _compile_phrase_matcher(
    set(_TOPIC_PHRASE_RULES)
)
_WEAK_PHRASE_RULES = {
    normalize_text(phrase): rule_id
    for rule_id, phrases in WEAK_RULES
    for phrase in phrases
}
_WEAK_MATCHER, _WEAK_CANONICAL = _compile_phrase_matcher(
    set(_WEAK_PHRASE_RULES)
)
_CONTEXT_MATCHER, _CONTEXT_CANONICAL = _compile_phrase_matcher(
    {normalize_text(phrase) for phrase in _CONTEXT_PHRASES}
)


def _phrase_matches(
    text: str,
    matcher: re.Pattern[str] | None,
    canonical_phrases: dict[str, str],
) -> list[tuple[str, str]]:
    normalized = normalize_text(text)
    if matcher is None or not normalized:
        return []
    return [
        (canonical_phrases[match.group("phrase")], match.group("phrase"))
        for match in matcher.finditer(normalized)
    ]


def _get_article_matches(
    title: str, content: str
) -> tuple[dict[str, set[str]], list[dict[str, str]], set[str]]:
    text_by_field = (("title", title), ("content", content))
    topic_matches: dict[str, set[str]] = {}
    keyword_evidence: set[tuple[str, str]] = set()
    context_phrases: set[str] = set()

    for field, text in text_by_field:
        for original_phrase, normalized_phrase in _phrase_matches(
            text, _TOPIC_MATCHER, _TOPIC_CANONICAL
        ):
            keyword_evidence.add((field, original_phrase))
            for rule_id in _TOPIC_PHRASE_RULES[normalized_phrase]:
                topic_matches.setdefault(rule_id, set()).add(field)
        for original_phrase, _ in _phrase_matches(
            text, _CONTEXT_MATCHER, _CONTEXT_CANONICAL
        ):
            context_phrases.add(normalize_text(original_phrase))
            keyword_evidence.add((field, original_phrase))

    matched_rule_ids = set(topic_matches)
    for rule in TOPIC_RULES:
        if rule.context_phrases and rule.rule_id in matched_rule_ids:
            required_context = {normalize_text(value) for value in rule.context_phrases}
            title_has_rule_phrase = "title" in topic_matches[rule.rule_id]
            if not title_has_rule_phrase and not context_phrases.intersection(required_context):
                matched_rule_ids.remove(rule.rule_id)
                topic_matches.pop(rule.rule_id, None)

    weak_rule_ids: set[str] = set()
    for field, text in text_by_field:
        for original_phrase, normalized_phrase in _phrase_matches(
            text, _WEAK_MATCHER, _WEAK_CANONICAL
        ):
            keyword_evidence.add((field, original_phrase))
            weak_rule_ids.add(_WEAK_PHRASE_RULES[normalized_phrase])

    all_rules = matched_rule_ids | weak_rule_ids
    matched_keywords = [
        {"field": field, "keyword": phrase}
        for field, phrase in sorted(keyword_evidence, key=lambda item: (item[0], item[1]))
    ]
    return {rule_id: topic_matches[rule_id] for rule_id in sorted(matched_rule_ids)}, matched_keywords, all_rules


def classify_article(record: dict[str, Any]) -> dict[str, str]:
    """Classify a single article from title and content only."""
    article_id = record.get("article_id")
    if not isinstance(article_id, str) or not article_id.strip():
        raise ValueError("article_id must not be blank.")
    title_value = record.get("title", "")
    content_value = record.get("content", "")
    if not isinstance(title_value, str) or not isinstance(content_value, str):
        raise ValueError(f"{article_id}: title and content must be text values.")

    title = title_value.strip()
    content = content_value.strip()
    topic_matches, matched_keywords, rule_ids = _get_article_matches(title, content)
    strong_rule_ids = set(topic_matches)
    weak_rule_ids = rule_ids - strong_rule_ids
    labels = sorted(
        {rule.topic for rule in TOPIC_RULES if rule.rule_id in strong_rule_ids},
        key=TOPIC_ORDER.index,
    )
    title_body = normalize_text(f"{title} {content}")
    sports_dismissal = (
        "sa thai" in title_body
        and any(normalize_text(context) in title_body for context in SPORTS_DISMISSAL_CONTEXT)
    )

    if not content:
        status = REVIEW_REQUIRED
        labels = []
        reason = "Article content is empty; title-only evidence is insufficient for automatic classification."
    elif labels:
        status = RELEVANT
        reason = (
            "Matched labor-specific rule(s) for "
            + ", ".join(labels)
            + ": "
            + ", ".join(sorted(strong_rule_ids))
            + ". Topic labels are rule-based candidates and may need human review."
        )
    elif sports_dismissal:
        status = IRRELEVANT
        labels = []
        reason = (
            "The dismissal wording occurs in a sports/coach context and no labor-specific "
            "topic rule matched."
        )
    elif weak_rule_ids:
        status = REVIEW_REQUIRED
        labels = []
        reason = (
            "Only weak or context-dependent labor cues matched: "
            + ", ".join(sorted(weak_rule_ids))
            + "; one such cue is insufficient to establish relevance."
        )
    else:
        status = IRRELEVANT
        labels = []
        reason = "No labor-specific rule or contextual labor cue matched title or content."

    review_status = REVIEW_REQUIRED if status == REVIEW_REQUIRED else AUTO_CLASSIFIED
    return {
        "article_id": article_id.strip(),
        "relevance_status": status,
        "topic_labels": ";".join(labels),
        "matched_keywords": json.dumps(matched_keywords, ensure_ascii=True, separators=(",", ":")),
        "matched_rules": json.dumps(sorted(rule_ids), ensure_ascii=True, separators=(",", ":")),
        "reason": reason,
        "method": METHOD,
        "classifier_version": CLASSIFIER_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "review_status": review_status,
    }


def classify_records(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Classify records, rejecting blank or duplicate article identifiers."""
    seen_article_ids: set[str] = set()
    results: list[dict[str, str]] = []
    empty_content_count = 0
    for row_number, record in enumerate(records, start=2):
        article_id = record.get("article_id")
        if not isinstance(article_id, str) or not article_id.strip():
            raise ValueError(f"CSV row {row_number}: article_id must not be blank.")
        article_id = article_id.strip()
        if article_id in seen_article_ids:
            raise ValueError(
                f"CSV row {row_number}: duplicate article_id {article_id!r}."
            )
        seen_article_ids.add(article_id)
        if not isinstance(record.get("title", ""), str) or not isinstance(
            record.get("content", ""), str
        ):
            raise ValueError(f"CSV row {row_number}: title and content must be text values.")
        if not record.get("content", "").strip():
            empty_content_count += 1
        results.append(classify_article(record))

    status_counts = Counter(result["relevance_status"] for result in results)
    topic_counts: Counter[str] = Counter()
    matched_rule_counts: Counter[str] = Counter()
    for result in results:
        topic_counts.update(filter(None, result["topic_labels"].split(";")))
        matched_rule_counts.update(json.loads(result["matched_rules"]))

    stats: dict[str, Any] = {
        "total_articles_checked": len(results),
        "relevant_count": status_counts[RELEVANT],
        "irrelevant_count": status_counts[IRRELEVANT],
        "review_required_count": status_counts[REVIEW_REQUIRED],
        "topic_distribution": {topic: topic_counts[topic] for topic in TOPIC_ORDER},
        "matched_rule_distribution": dict(sorted(matched_rule_counts.items())),
        "empty_content_count": empty_content_count,
    }
    return results, stats


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_input_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve()))
    except ValueError:
        return path.name


def detect_from_csv(
    input_path: Path,
    output_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    """Read the input CSV and write only the P4.07 results and report."""
    started_at = time.perf_counter()
    resolved_input = input_path.resolve()
    resolved_output = output_path.resolve()
    resolved_report = report_path.resolve()
    protected_paths = {path.resolve() for path in PROTECTED_ARTIFACTS}
    if resolved_output == resolved_input or resolved_report == resolved_input:
        raise ValueError("Output and report paths must not overwrite the input CSV.")
    if resolved_output in protected_paths or resolved_report in protected_paths:
        raise ValueError("P4.07 outputs must not overwrite P4.02-P4.06 artifacts.")
    if resolved_output == resolved_report:
        raise ValueError("Results CSV and JSON report must use different paths.")

    input_sha256 = _file_sha256(input_path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = sorted(set(REQUIRED_COLUMNS) - set(reader.fieldnames or ()))
        if missing:
            raise ValueError(f"Input CSV is missing required columns: {missing}")
        records = list(reader)
    if input_sha256 != _file_sha256(input_path):
        raise ValueError("Input CSV changed while being read; no outputs were written.")

    results, stats = classify_records(records)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": _relative_input_path(input_path),
        "input_sha256": input_sha256,
        "classifier_version": CLASSIFIER_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "method": METHOD,
        **stats,
        "execution_time_seconds": round(time.perf_counter() - started_at, 6),
        "limitations": [
            "Rule-based outputs are candidate classifications, not gold labels.",
            "The keyword rules may miss implicit, novel, or paraphrased labor reporting.",
            "A phrase can be incidental or used in a non-labor sense despite contextual rules.",
            "No accuracy, precision, recall, or F1 is reported because there is no sufficiently reliable representative gold set.",
            "The existing relevance_status field was not used as a label or feature.",
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(results)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args(argv)
    try:
        report = detect_from_csv(args.input, args.output, args.report)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Rule-based relevance classification failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Checked {report['total_articles_checked']} articles: "
        f"{report['relevant_count']} relevant, {report['irrelevant_count']} irrelevant, "
        f"{report['review_required_count']} review required. "
        f"CSV: {args.output}; JSON: {args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
