"""Create explainable P4.08 multi-label topic candidates using P4.07 rules."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

PROCESS_DIR = Path(__file__).resolve().parents[1]
REPO = PROCESS_DIR.parent
SOURCE_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
OUTPUT_DEFAULT = PROCESS_DIR / "topic_classification" / "topic_labels.csv"
REPORT_DEFAULT = REPO / "5_process" / "reports" / "topic_classification_report.json"
RELEVANCE_CLASSIFIER_PATH = PROCESS_DIR / "src" / "classify_relevance_rules.py"

CLASSIFIER_VERSION = "1.0.0"
METHOD = "p4.07_rule_reuse_with_per_topic_evidence"
REQUIRED_COLUMNS = ("article_id", "title", "content")
OUTPUT_COLUMNS = (
    "article_id",
    "relevance_status",
    "topic_labels",
    "topic_scores",
    "topic_reasons",
    "classifier_version",
    "source_relevance_classifier_version",
    "taxonomy_version",
    "review_status",
)
PROTECTED_PATHS = (
    SOURCE_DEFAULT,
    PROCESS_DIR / "data" / "interim" / "relevance_results.csv",
    PROCESS_DIR / "data" / "interim" / "relevance_review_sample.csv",
    PROCESS_DIR / "data" / "interim" / "relevance_review_batch_01.csv",
    PROCESS_DIR / "data" / "interim" / "relevance_review_batch_02.csv",
    PROCESS_DIR / "data" / "interim" / "relevance_review_batch_03.csv",
    PROCESS_DIR / "data" / "interim" / "url_duplicate_candidates.csv",
    PROCESS_DIR / "data" / "interim" / "exact_duplicate_candidates.csv",
    PROCESS_DIR / "data" / "interim" / "near_duplicate_candidates.csv",
    PROCESS_DIR / "data" / "interim" / "duplicate_groups.csv",
    PROCESS_DIR / "data" / "processed" / "manual_label_sample.csv",
    PROCESS_DIR / "data" / "processed" / "legacy_borderline_manual_labels.csv",
    PROCESS_DIR / "data" / "interim" / "pilot_10" / "reviewer_1_sheet.csv",
    PROCESS_DIR / "data" / "interim" / "pilot_10" / "reviewer_2_sheet.csv",
    PROCESS_DIR / "data" / "interim" / "reviewer_1_calibration_sheet.csv",
    PROCESS_DIR / "data" / "interim" / "reviewer_2_calibration_sheet.csv",
    PROCESS_DIR / "reports" / "relevance_rule_report.json",
    PROCESS_DIR / "config" / "labeling_guideline.md",
)


def _load_relevance_classifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "p4_relevance_classifier_for_topics", RELEVANCE_CLASSIFIER_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load P4.07 classifier at {RELEVANCE_CLASSIFIER_PATH}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RELEVANCE_CLASSIFIER = _load_relevance_classifier()
TOPIC_ORDER = tuple(RELEVANCE_CLASSIFIER.TOPIC_ORDER)
TOPIC_RULES = tuple(RELEVANCE_CLASSIFIER.TOPIC_RULES)
TOPIC_RULES_BY_ID = {rule.rule_id: rule for rule in TOPIC_RULES}
NORMALIZED_RULE_PHRASES = {
    rule.rule_id: tuple(
        (
            phrase,
            RELEVANCE_CLASSIFIER.normalize_text(phrase),
        )
        for phrase in (*rule.phrases, *rule.context_phrases)
    )
    for rule in TOPIC_RULES
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_records(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"{path}: input CSV must have a header.")
        missing = sorted(set(REQUIRED_COLUMNS) - set(reader.fieldnames))
        if missing:
            raise ValueError(f"{path}: missing required columns: {missing}")
        return list(reader)


def _topic_evidence(
    rule_ids: set[str], title: str, content: str
) -> dict[str, dict[str, Any]]:
    normalized_fields = {
        "title": RELEVANCE_CLASSIFIER.normalize_text(title),
        "content": RELEVANCE_CLASSIFIER.normalize_text(content),
    }
    evidence_by_topic: dict[str, dict[str, Any]] = {}
    for topic in TOPIC_ORDER:
        matched_rules = sorted(
            rule_id
            for rule_id in rule_ids
            if rule_id in TOPIC_RULES_BY_ID
            and TOPIC_RULES_BY_ID[rule_id].topic == topic
        )
        if not matched_rules:
            continue

        evidence: set[tuple[str, str]] = set()
        for rule_id in matched_rules:
            for field, normalized_text in normalized_fields.items():
                for phrase, normalized_phrase in NORMALIZED_RULE_PHRASES[rule_id]:
                    if normalized_phrase and (
                        f" {normalized_phrase} " in f" {normalized_text} "
                    ):
                        evidence.add((field, phrase))

        evidence_by_topic[topic] = {
            "matched_rules": matched_rules,
            "evidence": [
                {"field": field, "phrase": phrase}
                for field, phrase in sorted(evidence)
            ],
        }
    return evidence_by_topic


def classify_article(record: dict[str, Any]) -> dict[str, str]:
    """Return isolated P4.08 outputs; no manual-label field is read or written."""
    relevance = RELEVANCE_CLASSIFIER.classify_article(record)
    article_id = relevance["article_id"]
    title = record.get("title", "")
    content = record.get("content", "")
    matched_rule_ids = set(json.loads(relevance["matched_rules"]))
    candidate_labels = (
        relevance["topic_labels"].split(";")
        if relevance["relevance_status"] == RELEVANCE_CLASSIFIER.RELEVANT
        else []
    )
    evidence_by_topic = _topic_evidence(matched_rule_ids, title, content)
    topic_labels = [
        topic
        for topic in TOPIC_ORDER
        if topic in candidate_labels and topic in evidence_by_topic
    ]
    topic_scores = {
        topic: len(evidence_by_topic[topic]["matched_rules"])
        for topic in topic_labels
    }
    topic_reasons = {
        topic: evidence_by_topic[topic]
        for topic in topic_labels
    }
    return {
        "article_id": article_id,
        "relevance_status": relevance["relevance_status"],
        "topic_labels": json.dumps(topic_labels, ensure_ascii=True, separators=(",", ":")),
        "topic_scores": json.dumps(topic_scores, ensure_ascii=True, separators=(",", ":")),
        "topic_reasons": json.dumps(topic_reasons, ensure_ascii=True, separators=(",", ":")),
        "classifier_version": CLASSIFIER_VERSION,
        "source_relevance_classifier_version": relevance["classifier_version"],
        "taxonomy_version": relevance["taxonomy_version"],
        "review_status": relevance["review_status"],
    }


def classify_records(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    seen_ids: set[str] = set()
    results: list[dict[str, str]] = []
    empty_content_count = 0

    for row_number, record in enumerate(records, start=2):
        article_id_value = record.get("article_id")
        article_id = article_id_value.strip() if isinstance(article_id_value, str) else ""
        if not article_id:
            raise ValueError(f"CSV row {row_number}: article_id must not be blank.")
        if article_id in seen_ids:
            raise ValueError(
                f"CSV row {row_number}: duplicate article_id {article_id!r}."
            )
        seen_ids.add(article_id)
        for field in ("title", "content"):
            if not isinstance(record.get(field, ""), str):
                raise ValueError(
                    f"CSV row {row_number}: {field} must be present as text."
                )
        if not record.get("content", "").strip():
            empty_content_count += 1
        results.append(classify_article(record))

    relevance_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    for result in results:
        relevance_counts[result["relevance_status"]] += 1
        topic_counts.update(json.loads(result["topic_labels"]))

    stats = {
        "total_articles_checked": len(results),
        "relevance_status_counts": dict(sorted(relevance_counts.items())),
        "topic_distribution": {topic: topic_counts[topic] for topic in TOPIC_ORDER},
        "empty_content_count": empty_content_count,
    }
    return results, stats


def _relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve()))
    except ValueError:
        return path.name


def classify_from_csv(
    input_path: Path = SOURCE_DEFAULT,
    output_path: Path = OUTPUT_DEFAULT,
    report_path: Path = REPORT_DEFAULT,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    resolved_input = input_path.resolve()
    resolved_output = output_path.resolve()
    resolved_report = report_path.resolve()
    protected = {path.resolve() for path in PROTECTED_PATHS}
    if resolved_output == resolved_input or resolved_report == resolved_input:
        raise ValueError("P4.08 outputs must not overwrite the input CSV.")
    if resolved_output == resolved_report:
        raise ValueError("P4.08 CSV and JSON outputs must use different paths.")
    if resolved_output in protected or resolved_report in protected:
        raise ValueError("P4.08 outputs must not overwrite protected source or review artifacts.")
    if output_path.exists() or report_path.exists():
        raise FileExistsError("P4.08 output already exists; refusing to overwrite it.")

    input_hash = _sha256_file(input_path)
    records = _read_records(input_path)
    results, stats = classify_records(records)
    if input_hash != _sha256_file(input_path):
        raise ValueError("Input CSV changed while being read; no outputs were written.")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": _relative_path(input_path),
        "input_sha256": input_hash,
        "classifier_version": CLASSIFIER_VERSION,
        "source_relevance_classifier_version": RELEVANCE_CLASSIFIER.CLASSIFIER_VERSION,
        "taxonomy_version": RELEVANCE_CLASSIFIER.TAXONOMY_VERSION,
        "method": METHOD,
        "topic_score_semantics": (
            "Integer count of matched strong P4.07 rules for a topic; not a probability "
            "or calibrated confidence."
        ),
        "manual_annotation_fields_written": False,
        **stats,
        "execution_time_seconds": round(time.perf_counter() - started_at, 6),
        "limitations": [
            "Topic assignments are automatic candidates, not human-confirmed labels or ground truth.",
            "A topic score is a count of matched strong rules, not a probability or calibrated confidence.",
            "P4.06 multi-label topics are separate from the A-L manual annotation taxonomy.",
            "Only explicit rules in P4.07 are reused; implicit topics and paraphrases may be missed.",
            "Context-dependent or insufficient evidence remains REVIEW_REQUIRED.",
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8-sig", newline="") as stream:
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
    parser.add_argument("--input", type=Path, default=SOURCE_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args(argv)
    try:
        report = classify_from_csv(args.input, args.output, args.report)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"P4.08 topic classification failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Classified {report['total_articles_checked']} articles for topic candidates; "
        f"CSV: {args.output}; JSON: {args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
