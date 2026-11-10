"""Generate near-duplicate article candidates for human review."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[2]
INPUT_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
OUTPUT_DEFAULT = REPO / "5_process" / "data" / "interim" / "near_duplicate_candidates.csv"
REPORT_DEFAULT = REPO / "5_process" / "reports" / "near_duplicate_report.json"
METADATA_DETECTOR = REPO / "5_process" / "src" / "03_clean_metadata.py"
URL_CANDIDATES = REPO / "5_process" / "data" / "interim" / "url_duplicate_candidates.csv"
EXACT_CANDIDATES = REPO / "5_process" / "data" / "interim" / "exact_duplicate_candidates.csv"
EXACT_REPORT = REPO / "5_process" / "reports" / "exact_duplicate_report.json"

DETECTOR_VERSION = "1.0.0"
DEFAULT_THRESHOLD = 0.85
METHOD = "TF-IDF word-unigram+bigram cosine similarity (sparse candidate pairs)"
DUPLICATE_TYPE = "NEAR_DUPLICATE"
REVIEW_STATUS = "REVIEW_REQUIRED"
REQUIRED_COLUMNS = ("article_id", "content")
OUTPUT_COLUMNS = (
    "article_id_1",
    "article_id_2",
    "similarity_score",
    "duplicate_type",
    "method",
    "threshold",
    "reason",
    "detector_version",
    "review_status",
)

_PAIR_FINDER: Callable | None = None


def _load_existing_pair_finder() -> Callable:
    """Load the TF-IDF implementation already used by the metadata audit."""
    global _PAIR_FINDER
    if _PAIR_FINDER is not None:
        return _PAIR_FINDER

    module_name = "process_metadata_near_duplicate_helper"
    spec = importlib.util.spec_from_file_location(module_name, METADATA_DETECTOR)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load existing detector from {METADATA_DETECTOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    _PAIR_FINDER = module.near_duplicate_pairs
    return _PAIR_FINDER


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_threshold(threshold: float) -> None:
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be greater than 0 and at most 1.")


def find_candidates(
    records: list[dict[str, str]],
    threshold: float = DEFAULT_THRESHOLD,
    pair_finder: Callable | None = None,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Find unique near-duplicate pairs, excluding exact raw-content matches."""
    _validate_threshold(threshold)
    seen_article_ids: set[str] = set()
    valid_records: list[dict[str, str]] = []
    empty_content_count = 0

    for row_number, record in enumerate(records, start=2):
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
        valid_records.append({"article_id": article_id, "content": content})

    compare_pairs = pair_finder or _load_existing_pair_finder()
    contents = [record["content"] for record in valid_records]
    unique_pairs: dict[tuple[str, str], float] = {}
    for left_index, right_index, similarity in compare_pairs(contents, threshold):
        left = valid_records[left_index]
        right = valid_records[right_index]
        if left["content"] == right["content"]:
            continue
        article_id_1, article_id_2 = sorted((left["article_id"], right["article_id"]))
        pair = (article_id_1, article_id_2)
        bounded_similarity = min(1.0, max(0.0, float(similarity)))
        if bounded_similarity < threshold:
            continue
        unique_pairs[pair] = max(unique_pairs.get(pair, 0.0), bounded_similarity)

    candidates = []
    for (article_id_1, article_id_2), similarity in sorted(unique_pairs.items()):
        candidates.append(
            {
                "article_id_1": article_id_1,
                "article_id_2": article_id_2,
                "similarity_score": round(similarity, 6),
                "duplicate_type": DUPLICATE_TYPE,
                "method": METHOD,
                "threshold": threshold,
                "reason": (
                    f"TF-IDF word unigram/bigram cosine similarity {similarity:.4f} "
                    f">= threshold {threshold:.4f}; candidate only, requires human review "
                    "to distinguish republication from independent coverage of the same event."
                ),
                "detector_version": DETECTOR_VERSION,
                "review_status": REVIEW_STATUS,
            }
        )

    stats = {
        "total_articles_checked": len(records),
        "empty_content_count": empty_content_count,
        "candidate_pair_count": len(candidates),
        "unique_articles_in_candidates": len(
            {article_id for pair in unique_pairs for article_id in pair}
        ),
    }
    return candidates, stats


def detect_from_csv(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    threshold: float = DEFAULT_THRESHOLD,
    pair_finder: Callable | None = None,
) -> dict[str, int | float]:
    """Read the input CSV and write only the P4.04 candidate and report files."""
    _validate_threshold(threshold)
    resolved_input = input_path.resolve()
    resolved_output = output_path.resolve()
    resolved_report = report_path.resolve()
    protected_outputs = {
        resolved_input,
        URL_CANDIDATES.resolve(),
        EXACT_CANDIDATES.resolve(),
        EXACT_REPORT.resolve(),
    }
    if resolved_output in protected_outputs or resolved_report in protected_outputs:
        raise ValueError("P4.04 output/report paths must not overwrite source or P4.02/P4.03 artifacts.")
    if resolved_output == resolved_report:
        raise ValueError("Candidate CSV and JSON report must use different paths.")

    started_at = time.perf_counter()
    input_sha256 = _file_sha256(input_path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = sorted(set(REQUIRED_COLUMNS) - set(reader.fieldnames or ()))
        if missing:
            raise ValueError(f"Input CSV is missing required columns: {missing}")
        records = list(reader)
    if input_sha256 != _file_sha256(input_path):
        raise ValueError("Input CSV changed while being read; no outputs were written.")

    candidates, stats = find_candidates(
        records,
        threshold=threshold,
        pair_finder=pair_finder,
    )
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
        "threshold": threshold,
        **stats,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(candidates)
    report["execution_time_seconds"] = round(time.perf_counter() - started_at, 6)
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
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="cosine similarity threshold in (0, 1] (default: 0.85)",
    )
    args = parser.parse_args(argv)

    try:
        report = detect_from_csv(args.input, args.output, args.report, args.threshold)
    except (OSError, UnicodeError, csv.Error, ValueError, ImportError) as exc:
        print(f"Near duplicate detection failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Checked {report['total_articles_checked']} articles; "
        f"{report['candidate_pair_count']} candidate pairs at threshold {args.threshold:.4f}. "
        f"CSV: {args.output}; JSON: {args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
