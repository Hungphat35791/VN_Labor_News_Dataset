"""Generate exact-content duplicate candidates without modifying source records."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[2]
INPUT_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
OUTPUT_DEFAULT = REPO / "5_process" / "data" / "interim" / "exact_duplicate_candidates.csv"
REPORT_DEFAULT = REPO / "5_process" / "reports" / "exact_duplicate_report.json"

DETECTOR_VERSION = "1.0.0"
METHOD = "sha256_raw_content_with_exact_text_verification"
DUPLICATE_TYPE = "EXACT_CONTENT_DUPLICATE"
REVIEW_STATUS = "REVIEW_REQUIRED"
REQUIRED_COLUMNS = ("article_id", "content")
OUTPUT_COLUMNS = (
    "duplicate_group_id",
    "article_id",
    "content_hash",
    "duplicate_type",
    "method",
    "reason",
    "detector_version",
    "review_status",
)


def sha256_content(content: str) -> str:
    """Hash the unmodified decoded CSV content as UTF-8 bytes."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def find_candidates(
    records: list[dict[str, str]],
    hash_function: Callable[[str], str] = sha256_content,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Group identical nonblank content after hash bucketing and exact verification."""
    seen_article_ids: set[str] = set()
    hash_buckets: dict[str, list[tuple[str, str]]] = defaultdict(list)
    total_articles = 0
    empty_content_count = 0

    for row_number, record in enumerate(records, start=2):
        total_articles += 1
        raw_article_id = record.get("article_id")
        if not isinstance(raw_article_id, str) or not raw_article_id.strip():
            raise ValueError(f"CSV row {row_number}: article_id must not be blank.")
        article_id = raw_article_id.strip()
        if article_id in seen_article_ids:
            raise ValueError(f"CSV row {row_number}: duplicate article_id {article_id!r}.")
        seen_article_ids.add(article_id)

        content = record.get("content")
        if not isinstance(content, str):
            raise ValueError(f"CSV row {row_number}: content must be present as text.")
        if not content.strip():
            empty_content_count += 1
            continue
        hash_buckets[hash_function(content)].append((article_id, content))

    exact_groups: list[tuple[str, list[str]]] = []
    hash_collision_buckets = 0
    for content_hash, bucket in sorted(hash_buckets.items()):
        by_exact_content: dict[str, list[str]] = defaultdict(list)
        for article_id, content in bucket:
            by_exact_content[content].append(article_id)
        if len(by_exact_content) > 1:
            hash_collision_buckets += 1
        for article_ids in by_exact_content.values():
            if len(article_ids) > 1:
                exact_groups.append((content_hash, sorted(article_ids)))

    exact_groups.sort(key=lambda group: (group[0], group[1]))
    candidates: list[dict[str, str]] = []
    for group_number, (content_hash, article_ids) in enumerate(exact_groups, start=1):
        group_id = f"EXACT-{group_number:06d}"
        for article_id in article_ids:
            candidates.append(
                {
                    "duplicate_group_id": group_id,
                    "article_id": article_id,
                    "content_hash": content_hash,
                    "duplicate_type": DUPLICATE_TYPE,
                    "method": METHOD,
                    "reason": (
                        "SHA-256 of the unmodified content matches and the complete "
                        "decoded content strings are exactly equal; human review required."
                    ),
                    "detector_version": DETECTOR_VERSION,
                    "review_status": REVIEW_STATUS,
                }
            )

    stats = {
        "total_articles_checked": total_articles,
        "empty_content_count": empty_content_count,
        "exact_duplicate_group_count": len(exact_groups),
        "articles_in_groups": len(candidates),
        "candidates_requiring_review": len(exact_groups),
        "candidate_article_rows_requiring_review": len(candidates),
        "hash_collision_buckets_detected": hash_collision_buckets,
    }
    return candidates, stats


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_from_csv(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    hash_function: Callable[[str], str] = sha256_content,
) -> dict[str, int]:
    """Read the input CSV and write only derived candidate and summary files."""
    resolved_input = input_path.resolve()
    resolved_output = output_path.resolve()
    resolved_report = report_path.resolve()
    if resolved_input in {resolved_output, resolved_report}:
        raise ValueError("Output and report paths must not overwrite the input CSV.")
    if resolved_output == resolved_report:
        raise ValueError("Candidate CSV and JSON report must use different paths.")

    input_sha256 = _file_sha256(input_path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = sorted(set(REQUIRED_COLUMNS) - set(reader.fieldnames or ()))
        if missing:
            raise ValueError(f"Input CSV is missing required columns: {missing}")
        records = list(reader)
    if input_sha256 != _file_sha256(input_path):
        raise ValueError("Input CSV changed while being read; no outputs were written.")

    candidates, stats = find_candidates(records, hash_function=hash_function)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(candidates)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": (
            str(input_path.resolve().relative_to(REPO.resolve()))
            if input_path.resolve().is_relative_to(REPO.resolve())
            else input_path.name
        ),
        "input_sha256": input_sha256,
        "detector_version": DETECTOR_VERSION,
        "method": METHOD,
        **stats,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args(argv)

    try:
        stats = detect_from_csv(args.input, args.output, args.report)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Exact duplicate detection failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Checked {stats['total_articles_checked']} articles; "
        f"{stats['exact_duplicate_group_count']} exact duplicate groups, "
        f"{stats['articles_in_groups']} articles require review; "
        f"{stats['empty_content_count']} empty contents. "
        f"CSV: {args.output}; JSON: {args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
