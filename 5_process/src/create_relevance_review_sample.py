"""Create a reproducible A-L manual-review sample stratified by P4.07 results."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SOURCE_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
RESULTS_DEFAULT = REPO / "5_process" / "data" / "interim" / "relevance_results.csv"
OUTPUT_DEFAULT = REPO / "5_process" / "data" / "interim" / "relevance_review_sample.csv"
REPORT_DEFAULT = REPO / "5_process" / "reports" / "relevance_review_sample_report.json"

RELEVANT = "RELEVANT"
IRRELEVANT = "IRRELEVANT"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
STATUSES = (RELEVANT, IRRELEVANT, REVIEW_REQUIRED)
DEFAULT_SAMPLE_SIZES = {
    RELEVANT: 200,
    IRRELEVANT: 220,
    REVIEW_REQUIRED: 200,
}
DEFAULT_RANDOM_SEED = 42
SOURCE_COLUMNS = ("article_id", "title", "content")
RESULT_COLUMNS = ("article_id", "relevance_status")
ANNOTATION_COLUMNS = (
    "relevance_manual",
    "topic_manual",
    "review_reason",
    "reviewer_id",
    "review_date",
)
WORKFLOW_COLUMN = "review_status"
OUTPUT_COLUMNS = (*SOURCE_COLUMNS, *ANNOTATION_COLUMNS, WORKFLOW_COLUMN)
INITIAL_REVIEW_STATUS = "PENDING"
LEGACY_ANNOTATION_COLUMNS = (
    "manual_relevance_status",
    "manual_topic_labels",
    "manual_evidence",
    "manual_notes",
    "reviewer",
    "reviewed_at",
)

PROTECTED_ARTIFACTS = (
    SOURCE_DEFAULT,
    RESULTS_DEFAULT,
    REPO / "5_process" / "reports" / "relevance_rule_report.json",
    REPO / "5_process" / "data" / "interim" / "url_duplicate_candidates.csv",
    REPO / "5_process" / "data" / "interim" / "exact_duplicate_candidates.csv",
    REPO / "5_process" / "data" / "interim" / "near_duplicate_candidates.csv",
    REPO / "5_process" / "data" / "interim" / "duplicate_groups.csv",
    REPO / "5_process" / "reports" / "exact_duplicate_report.json",
    REPO / "5_process" / "reports" / "near_duplicate_report.json",
    REPO / "5_process" / "reports" / "duplicate_grouping_report.json",
    REPO / "5_process" / "config" / "duplicate_taxonomy.md",
    REPO / "5_process" / "config" / "relevance_taxonomy.md",
    REPO / "5_process" / "config" / "labeling_guideline.md",
    REPO / "5_process" / "src" / "classify_relevance_rules.py",
    REPO / "5_process" / "tests" / "test_classify_relevance_rules.py",
    REPO / "5_process" / "README_PROCESS.md",
    Path(__file__).resolve(),
)


def _read_csv(path: Path, required_columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = sorted(set(required_columns) - set(reader.fieldnames or ()))
        if missing:
            raise ValueError(f"{path}: missing required columns: {missing}")
        return list(reader)


def _validated_id(
    row: dict[str, Any],
    path: Path,
    row_number: int,
    seen: set[str],
) -> str:
    value = row.get("article_id")
    article_id = value.strip() if isinstance(value, str) else ""
    if not article_id:
        raise ValueError(f"{path.name} row {row_number}: article_id must not be blank.")
    if article_id in seen:
        raise ValueError(f"{path.name} row {row_number}: duplicate article_id {article_id!r}.")
    seen.add(article_id)
    return article_id


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_existing_sample(output_path: Path, generated_rows: list[dict[str, str]]) -> None:
    if not output_path.exists():
        return
    with output_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        existing_rows = list(reader)
    if not existing_rows:
        raise ValueError(f"Existing review sample is empty and will not be overwritten: {output_path}")

    manual_fields = set(ANNOTATION_COLUMNS) | set(LEGACY_ANNOTATION_COLUMNS)
    for row_number, row in enumerate(existing_rows, start=2):
        annotations = {
            field: row.get(field, "").strip()
            for field in manual_fields
            if row.get(field, "").strip()
        }
        workflow = row.get(WORKFLOW_COLUMN, "").strip()
        if workflow not in ("", INITIAL_REVIEW_STATUS):
            annotations[WORKFLOW_COLUMN] = workflow
        if annotations:
            raise ValueError(
                f"Existing review sample has human annotations or workflow progress at "
                f"row {row_number}; refusing to overwrite it. Preserve and migrate the "
                "reviewed file manually."
            )

    expected_ids = [row["article_id"] for row in generated_rows]
    existing_ids = [row.get("article_id", "") for row in existing_rows]
    if existing_ids != expected_ids:
        raise ValueError(
            "Existing review sample article IDs/order differ from the deterministic "
            "seeded selection; refusing to overwrite it."
        )
    for row_number, (existing, generated) in enumerate(zip(existing_rows, generated_rows), start=2):
        if any(existing.get(field, "") != generated[field] for field in SOURCE_COLUMNS):
            raise ValueError(
                f"Existing review sample source fields differ at row {row_number}; "
                "refusing to overwrite it."
            )


def create_sample(
    source_rows: list[dict[str, str]],
    prediction_rows: list[dict[str, str]],
    random_seed: int = DEFAULT_RANDOM_SEED,
    requested_counts: dict[str, int] | None = None,
    generated_at_utc: str | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Stratify by P4.07 status, sample available rows, and hide predicted labels."""
    quotas = dict(requested_counts or DEFAULT_SAMPLE_SIZES)
    if set(quotas) != set(STATUSES):
        raise ValueError(f"requested_counts must define exactly: {list(STATUSES)}")
    if any(not isinstance(value, int) or value < 0 for value in quotas.values()):
        raise ValueError("requested sample counts must be non-negative integers.")

    source_by_id: dict[str, dict[str, str]] = {}
    seen_source_ids: set[str] = set()
    for row_number, row in enumerate(source_rows, start=2):
        article_id = _validated_id(row, SOURCE_DEFAULT, row_number, seen_source_ids)
        source_by_id[article_id] = row

    predictions_by_status: dict[str, list[str]] = {status: [] for status in STATUSES}
    seen_prediction_ids: set[str] = set()
    for row_number, row in enumerate(prediction_rows, start=2):
        article_id = _validated_id(row, RESULTS_DEFAULT, row_number, seen_prediction_ids)
        status = row.get("relevance_status", "")
        if status not in predictions_by_status:
            raise ValueError(
                f"{RESULTS_DEFAULT.name} row {row_number}: invalid relevance_status {status!r}."
            )
        if article_id not in source_by_id:
            raise ValueError(
                f"{RESULTS_DEFAULT.name} row {row_number}: article_id {article_id!r} "
                "is absent from the source CSV."
            )
        predictions_by_status[status].append(article_id)

    if seen_source_ids != seen_prediction_ids:
        missing_results = sorted(seen_source_ids - seen_prediction_ids)
        extra_results = sorted(seen_prediction_ids - seen_source_ids)
        raise ValueError(
            "Source and P4.07 result article_id sets differ; "
            f"missing results={missing_results[:5]}, extra results={extra_results[:5]}."
        )

    rng = random.Random(random_seed)
    selected_ids: list[str] = []
    selected_counts: dict[str, int] = {}
    available_counts = {
        status: len(predictions_by_status[status]) for status in STATUSES
    }
    for status in STATUSES:
        candidates = sorted(predictions_by_status[status])
        selected_count = min(quotas[status], len(candidates))
        selected_ids.extend(rng.sample(candidates, selected_count))
        selected_counts[status] = selected_count
    rng.shuffle(selected_ids)

    sample_rows: list[dict[str, str]] = []
    for article_id in selected_ids:
        source_row = source_by_id[article_id]
        row = {
            field: source_row.get(field, "")
            for field in SOURCE_COLUMNS
        }
        row.update({field: "" for field in ANNOTATION_COLUMNS})
        row[WORKFLOW_COLUMN] = INITIAL_REVIEW_STATUS
        sample_rows.append(row)

    shortfall_by_status = {
        status: quotas[status] - selected_counts[status]
        for status in STATUSES
        if selected_counts[status] < quotas[status]
    }
    report = {
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).isoformat(),
        "input_row_count": len(prediction_rows),
        "source_row_count": len(source_rows),
        "available_count_by_status": available_counts,
        "requested_sample_count_by_status": quotas,
        "sampled_count_by_status": selected_counts,
        "shortfall_by_status": shortfall_by_status,
        "total_sample_size": len(sample_rows),
        "random_seed": random_seed,
        "unique_article_id_count": len({row["article_id"] for row in sample_rows}),
        "review_schema": list(OUTPUT_COLUMNS),
        "manual_taxonomy": "A-L as defined in 5_process/config/labeling_guideline.md",
        "initial_review_status": INITIAL_REVIEW_STATUS,
        "sampling_rule": (
            "For each P4.07 relevance_status, select min(requested, available) distinct "
            "article IDs using random.Random(random_seed).sample, then shuffle the "
            "combined sample with the same seeded generator. Article title/content are "
            "joined from the authoritative source CSV by article_id. Predicted status "
            "and topic labels are not included in the reviewer CSV."
        ),
        "complete": not shortfall_by_status,
        "limitations": [
            "Sampling strata are based on P4.07 rule-based predictions, not gold labels.",
            "The review sample is an audit sample, not a representative sample of natural class distribution.",
            "This sample cannot establish corpus-wide prevalence or unbiased performance metrics without an appropriate sampling design and reliable reference labels.",
            "Do not calculate Accuracy, Precision, Recall, or F1 without a trustworthy adjudicated gold set.",
        ],
    }
    return sample_rows, report


def create_review_sample(
    source_path: Path = SOURCE_DEFAULT,
    results_path: Path = RESULTS_DEFAULT,
    output_path: Path = OUTPUT_DEFAULT,
    report_path: Path = REPORT_DEFAULT,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> dict[str, Any]:
    """Read source and predictions, then write the unlabeled review sample and report."""
    protected = {path.resolve() for path in PROTECTED_ARTIFACTS}
    protected.update({source_path.resolve(), results_path.resolve()})
    output_resolved = output_path.resolve()
    report_resolved = report_path.resolve()
    if output_resolved in protected or report_resolved in protected:
        raise ValueError("Review-sample outputs must not overwrite source or P4.02-P4.07 artifacts.")
    if output_resolved == source_path.resolve() or output_resolved == results_path.resolve():
        raise ValueError("Review-sample CSV output must not overwrite an input file.")
    if report_resolved == source_path.resolve() or report_resolved == results_path.resolve():
        raise ValueError("Review-sample report must not overwrite an input file.")
    if output_resolved == report_resolved:
        raise ValueError("Review-sample CSV and JSON report must use different paths.")

    source_hash_before = _sha256_file(source_path)
    results_hash_before = _sha256_file(results_path)
    source_rows = _read_csv(source_path, SOURCE_COLUMNS)
    prediction_rows = _read_csv(results_path, RESULT_COLUMNS)
    if source_hash_before != _sha256_file(source_path):
        raise ValueError("Source CSV changed while being read; no outputs were written.")
    if results_hash_before != _sha256_file(results_path):
        raise ValueError("P4.07 results changed while being read; no outputs were written.")

    sample_rows, report = create_sample(source_rows, prediction_rows, random_seed)
    _validate_existing_sample(output_path, sample_rows)
    report["source_file"] = str(source_path.resolve().relative_to(REPO.resolve())) if (
        source_path.resolve().is_relative_to(REPO.resolve())
    ) else source_path.name
    report["results_file"] = str(results_path.resolve().relative_to(REPO.resolve())) if (
        results_path.resolve().is_relative_to(REPO.resolve())
    ) else results_path.name
    report["source_sha256"] = source_hash_before
    report["results_sha256"] = results_hash_before

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(sample_rows)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_DEFAULT)
    parser.add_argument("--results", type=Path, default=RESULTS_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT)
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED)
    args = parser.parse_args(argv)
    try:
        report = create_review_sample(
            args.source, args.results, args.output, args.report, args.seed
        )
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Creating relevance review sample failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Created {report['total_sample_size']} review rows "
        f"(complete={report['complete']}) at {args.output}; report: {args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
