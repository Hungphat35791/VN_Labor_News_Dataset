"""Create a numbered working batch from the manual-review master CSV."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
MASTER_DEFAULT = REPO / "5_process" / "data" / "interim" / "relevance_review_sample.csv"
BATCH_DEFAULT = REPO / "5_process" / "data" / "interim" / "relevance_review_batch_01.csv"
REPORT_DEFAULT = REPO / "5_process" / "reports" / "relevance_review_batch_01_report.json"
BATCH_NUMBER = 1
BATCH_SIZE = 50
OUTPUT_COLUMNS = (
    "article_id",
    "title",
    "content",
    "relevance_manual",
    "topic_manual",
    "review_reason",
    "reviewer_id",
    "review_date",
    "review_status",
)
ANNOTATION_COLUMNS = (
    "relevance_manual",
    "topic_manual",
    "review_reason",
    "reviewer_id",
    "review_date",
)
SOURCE_COLUMNS = ("article_id", "title", "content")
WORKFLOW_COLUMN = "review_status"
PROTECTED_PATHS = (
    REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv",
    MASTER_DEFAULT,
    REPO / "5_process" / "data" / "interim" / "relevance_results.csv",
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
    REPO / "5_process" / "src" / "detect_url_duplicates.py",
    REPO / "5_process" / "src" / "detect_exact_duplicates.py",
    REPO / "5_process" / "src" / "detect_near_duplicates.py",
    REPO / "5_process" / "src" / "group_duplicate_candidates.py",
    REPO / "5_process" / "src" / "classify_relevance_rules.py",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_master(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(OUTPUT_COLUMNS):
            raise ValueError(
                f"Master CSV schema must exactly match {list(OUTPUT_COLUMNS)}; "
                f"got {reader.fieldnames}."
            )
        rows = list(reader)

    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        article_id = row["article_id"].strip()
        if not article_id:
            raise ValueError(f"Master CSV row {row_number}: article_id must not be blank.")
        if article_id in seen_ids:
            raise ValueError(f"Master CSV row {row_number}: duplicate article_id {article_id!r}.")
        seen_ids.add(article_id)
    if len(rows) < BATCH_SIZE:
        raise ValueError(
            f"Master CSV has {len(rows)} rows; at least {BATCH_SIZE} are required."
        )
    return rows


def _validate_unreviewed(rows: list[dict[str, str]], source_name: str) -> None:
    for row_number, row in enumerate(rows, start=2):
        if any((row[field] or "").strip() for field in ANNOTATION_COLUMNS):
            raise ValueError(
                f"{source_name} row {row_number} contains manual annotations; "
                "refusing to create or overwrite an unannotated batch."
            )
        if row[WORKFLOW_COLUMN] != "PENDING":
            raise ValueError(
                f"{source_name} row {row_number} is not PENDING; "
                "refusing to create or overwrite the batch."
            )


def _validate_existing_batch(
    batch_path: Path,
    expected_rows: list[dict[str, str]],
) -> None:
    if not batch_path.exists():
        return
    with batch_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(OUTPUT_COLUMNS):
            raise ValueError(
                "Existing batch has a different schema; refusing to overwrite it."
            )
        existing_rows = list(reader)

    _validate_unreviewed(existing_rows, batch_path.name)
    if len(existing_rows) != len(expected_rows):
        raise ValueError("Existing batch row count differs; refusing to overwrite it.")
    for row_number, (existing, expected) in enumerate(
        zip(existing_rows, expected_rows), start=2
    ):
        if existing != expected:
            raise ValueError(
                f"Existing batch differs from the requested sample rows at row "
                f"{row_number}; refusing to overwrite it."
            )


def create_batch(
    master_path: Path = MASTER_DEFAULT,
    batch_path: Path | None = None,
    report_path: Path | None = None,
    created_at_utc: str | None = None,
    batch_number: int = BATCH_NUMBER,
) -> dict[str, Any]:
    """Write one 50-row master slice and a JSON provenance report."""
    if batch_number < 1:
        raise ValueError("Batch number must be a positive integer.")
    batch_path = batch_path or (
        MASTER_DEFAULT.parent / f"relevance_review_batch_{batch_number:02d}.csv"
    )
    report_path = report_path or (
        REPO / "5_process" / "reports"
        / f"relevance_review_batch_{batch_number:02d}_report.json"
    )
    master_resolved = master_path.resolve()
    batch_resolved = batch_path.resolve()
    report_resolved = report_path.resolve()
    protected_resolved = {path.resolve() for path in PROTECTED_PATHS}
    protected_resolved.add(master_resolved)
    if batch_resolved in protected_resolved or report_resolved in protected_resolved:
        raise ValueError(
            "Batch and report outputs must not overwrite the source or P4.02-P4.07 artifacts."
        )
    if batch_resolved == report_resolved:
        raise ValueError("Batch CSV and JSON report must use different paths.")

    master_hash_before = _sha256_file(master_path)
    master_rows = _read_master(master_path)
    start_index = (batch_number - 1) * BATCH_SIZE
    end_index = start_index + BATCH_SIZE
    if len(master_rows) < end_index:
        raise ValueError(
            f"Master CSV has {len(master_rows)} rows; batch {batch_number} "
            f"requires at least {end_index}."
        )
    batch_rows = master_rows[start_index:end_index]
    _validate_unreviewed(batch_rows, master_path.name)
    _validate_existing_batch(batch_path, batch_rows)
    if batch_path.exists():
        raise FileExistsError(
            f"Batch output already exists at {batch_path}; refusing to overwrite it."
        )
    if report_path.exists():
        raise FileExistsError(
            f"Batch report already exists at {report_path}; refusing to overwrite it."
        )
    if master_hash_before != _sha256_file(master_path):
        raise ValueError("Master sample changed while being read; no outputs were written.")

    report = {
        "batch_number": batch_number,
        "row_count": len(batch_rows),
        "article_ids": [row["article_id"] for row in batch_rows],
        "source_sample_sha256": master_hash_before,
        "source_sample": str(master_path.resolve().relative_to(REPO.resolve()))
        if master_path.resolve().is_relative_to(REPO.resolve())
        else master_path.name,
        "created_at_utc": created_at_utc or datetime.now(timezone.utc).isoformat(),
    }

    batch_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with batch_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(batch_rows)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, default=MASTER_DEFAULT)
    parser.add_argument("--batch-number", type=int, default=BATCH_NUMBER)
    parser.add_argument("--batch", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        report = create_batch(
            args.master,
            args.batch,
            args.report,
            batch_number=args.batch_number,
        )
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Creating manual review batch failed: {exc}", file=sys.stderr)
        return 1
    batch_path = args.batch or (
        MASTER_DEFAULT.parent
        / f"relevance_review_batch_{report['batch_number']:02d}.csv"
    )
    report_path = args.report or (
        REPO / "5_process" / "reports"
        / f"relevance_review_batch_{report['batch_number']:02d}_report.json"
    )
    print(
        f"Created Batch {report['batch_number']:02d} with {report['row_count']} rows "
        f"at {batch_path}; report: {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
