"""Prepare blank independent P4.06 annotation and duplicate-review packets."""
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
PROCESS = REPO / "5_process"
SAMPLE_DEFAULT = PROCESS / "data" / "interim" / "relevance_review_sample.csv"
CANONICAL_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
NEAR_CANDIDATES_DEFAULT = PROCESS / "data" / "interim" / "near_duplicate_candidates.csv"
DUPLICATE_GROUPS_DEFAULT = PROCESS / "data" / "interim" / "duplicate_groups.csv"
URL_CANDIDATES_DEFAULT = PROCESS / "data" / "interim" / "url_duplicate_candidates.csv"
EXACT_CANDIDATES_DEFAULT = PROCESS / "data" / "interim" / "exact_duplicate_candidates.csv"

P406_INPUT_COLUMNS = (
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
P406_ANNOTATION_COLUMNS = (
    "relevance_manual",
    "topic_manual",
    "review_reason",
    "reviewer_id",
    "review_date",
)
P406_OUTPUT_COLUMNS = (
    "article_id",
    "title",
    "content",
    "gold_relevance_status",
    "gold_topic_labels_p406",
    "review_reason",
    "reviewer_id",
    "review_date",
    "annotation_status",
)

DUPLICATE_OUTPUT_COLUMNS = (
    "group_id",
    "article_id_1",
    "article_id_2",
    "title_1",
    "title_2",
    "content_1",
    "content_2",
    "source_name_1",
    "source_name_2",
    "publish_date_1",
    "publish_date_2",
    "source_url_1",
    "source_url_2",
    "similarity_score",
    "candidate_type",
    "method",
    "threshold",
    "confirmed_relationship_type",
    "version_lineage_evidence",
    "reviewer_id",
    "review_decision",
    "review_reason",
    "review_date",
    "review_status",
)
DUPLICATE_DECISIONS = (
    "CONFIRMED_DUPLICATE",
    "RELATED_BUT_DISTINCT",
    "NOT_DUPLICATE",
    "UNCERTAIN",
    "NEEDS_ADJUDICATION",
)

GOLD_REVIEWER_1 = PROCESS / "relevance_evaluation" / "p406_reviewer_1_sheet.csv"
GOLD_REVIEWER_2 = PROCESS / "relevance_evaluation" / "p406_reviewer_2_sheet.csv"
DUPLICATE_REVIEW_NEUTRAL = PROCESS / "data" / "interim" / "duplicate_review_sheet.csv"
DUPLICATE_REVIEWER_1 = PROCESS / "data" / "interim" / "duplicate_review_reviewer_1_sheet.csv"
DUPLICATE_REVIEWER_2 = PROCESS / "data" / "interim" / "duplicate_review_reviewer_2_sheet.csv"
DUPLICATE_SUMMARY = PROCESS / "reports" / "duplicate_review_summary.json"


def _read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"{path}: CSV must have a header.")
        missing = sorted(set(required) - set(reader.fieldnames))
        if missing:
            raise ValueError(f"{path}: missing required columns: {missing}.")
        return list(reader)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_index(
    rows: list[dict[str, str]], source_name: str
) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, start=2):
        article_id = (row.get("article_id") or "").strip()
        if not article_id:
            raise ValueError(f"{source_name} row {row_number}: article_id must not be blank.")
        if article_id in indexed:
            raise ValueError(
                f"{source_name} row {row_number}: duplicate article_id {article_id!r}."
            )
        indexed[article_id] = row
    return indexed


def build_p406_reviewer_rows(sample_path: Path) -> list[dict[str, str]]:
    """Build P4.06-only rows from the existing 620-item sample, without predictions."""
    with sample_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(P406_INPUT_COLUMNS):
            raise ValueError(
                f"{sample_path}: expected exact legacy sample schema "
                f"{list(P406_INPUT_COLUMNS)}, got {reader.fieldnames}."
            )
        source_rows = list(reader)

    if len(source_rows) != 620:
        raise ValueError(f"{sample_path}: expected 620 sample rows, got {len(source_rows)}.")
    _unique_index(source_rows, sample_path.name)

    output: list[dict[str, str]] = []
    for row_number, row in enumerate(source_rows, start=2):
        if row.get("review_status") != "PENDING":
            raise ValueError(
                f"{sample_path.name} row {row_number}: review_status is not PENDING."
            )
        if any((row.get(field) or "").strip() for field in P406_ANNOTATION_COLUMNS):
            raise ValueError(
                f"{sample_path.name} row {row_number}: existing manual annotation found."
            )
        output.append(
            {
                "article_id": row["article_id"],
                "title": row["title"],
                "content": row["content"],
                "gold_relevance_status": "",
                "gold_topic_labels_p406": "",
                "review_reason": "",
                "reviewer_id": "",
                "review_date": "",
                "annotation_status": "PENDING",
            }
        )
    return output


def build_duplicate_review_rows(
    canonical_path: Path,
    candidates_path: Path,
    groups_path: Path,
) -> list[dict[str, str]]:
    """Join candidate pairs to article text and candidate groups for independent review."""
    canonical_rows = _read_csv(
        canonical_path,
        ("article_id", "title", "content", "source_name", "publish_date", "source_url"),
    )
    articles = _unique_index(canonical_rows, canonical_path.name)
    group_rows = _read_csv(groups_path, ("duplicate_group_id", "article_id"))
    group_by_article = _unique_group_index(group_rows, groups_path.name)
    candidate_rows = _read_csv(
        candidates_path,
        (
            "article_id_1",
            "article_id_2",
            "similarity_score",
            "duplicate_type",
            "method",
            "threshold",
        ),
    )
    seen_pairs: set[tuple[str, str]] = set()
    output: list[dict[str, str]] = []
    for row_number, candidate in enumerate(candidate_rows, start=2):
        first = (candidate.get("article_id_1") or "").strip()
        second = (candidate.get("article_id_2") or "").strip()
        if not first or not second or first == second:
            raise ValueError(f"{candidates_path.name} row {row_number}: invalid article pair.")
        pair = tuple(sorted((first, second)))
        if pair in seen_pairs:
            raise ValueError(f"{candidates_path.name}: duplicate candidate pair {pair}.")
        seen_pairs.add(pair)
        if first not in articles or second not in articles:
            raise ValueError(
                f"{candidates_path.name} row {row_number}: article is absent from canonical CSV."
            )
        first_group = group_by_article.get(first)
        second_group = group_by_article.get(second)
        if not first_group or first_group != second_group:
            raise ValueError(
                f"{candidates_path.name} row {row_number}: pair lacks a shared candidate group."
            )
        left, right = articles[first], articles[second]
        output.append(
            {
                "group_id": first_group,
                "article_id_1": first,
                "article_id_2": second,
                "title_1": left["title"],
                "title_2": right["title"],
                "content_1": left["content"],
                "content_2": right["content"],
                "source_name_1": left["source_name"],
                "source_name_2": right["source_name"],
                "publish_date_1": left["publish_date"],
                "publish_date_2": right["publish_date"],
                "source_url_1": left["source_url"],
                "source_url_2": right["source_url"],
                "similarity_score": candidate["similarity_score"],
                "candidate_type": candidate["duplicate_type"],
                "method": candidate["method"],
                "threshold": candidate["threshold"],
                "reviewer_id": "",
                "review_decision": "",
                "review_reason": "",
                "review_date": "",
                "review_status": "PENDING",
            }
        )
    return output


def _unique_group_index(
    rows: list[dict[str, str]], source_name: str
) -> dict[str, str]:
    group_by_article: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=2):
        article_id = (row.get("article_id") or "").strip()
        group_id = (row.get("duplicate_group_id") or "").strip()
        if not article_id or not group_id:
            raise ValueError(
                f"{source_name} row {row_number}: group and article IDs must not be blank."
            )
        previous = group_by_article.get(article_id)
        if previous is not None and previous != group_id:
            raise ValueError(
                f"{source_name} row {row_number}: article belongs to multiple groups."
            )
        group_by_article[article_id] = group_id
    return group_by_article


def _write_csv(
    path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]
) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def prepare_packets() -> dict[str, Any]:
    """Validate all inputs and create blank, non-overwriting reviewer packets."""
    outputs = (
        GOLD_REVIEWER_1,
        GOLD_REVIEWER_2,
        DUPLICATE_REVIEW_NEUTRAL,
        DUPLICATE_REVIEWER_1,
        DUPLICATE_REVIEWER_2,
        DUPLICATE_SUMMARY,
    )
    existing = [str(path) for path in outputs if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing review artifacts: " + ", ".join(existing)
        )

    gold_rows = build_p406_reviewer_rows(SAMPLE_DEFAULT)
    duplicate_rows = build_duplicate_review_rows(
        CANONICAL_DEFAULT, NEAR_CANDIDATES_DEFAULT, DUPLICATE_GROUPS_DEFAULT
    )
    url_rows = _read_csv(
        URL_CANDIDATES_DEFAULT, ("article_id_1", "article_id_2", "duplicate_type")
    )
    exact_rows = _read_csv(
        EXACT_CANDIDATES_DEFAULT, ("duplicate_group_id", "article_id", "duplicate_type")
    )
    if len(duplicate_rows) != 70 or len({row["group_id"] for row in duplicate_rows}) != 61:
        raise ValueError("Current near-duplicate inputs differ from the expected 70 pairs/61 groups.")
    group_count = len({row["group_id"] for row in duplicate_rows})
    summary: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "WAITING_FOR_DUPLICATE_REVIEW",
        "candidate_pair_count": len(duplicate_rows),
        "candidate_group_count": group_count,
        "reviewed_pair_count": 0,
        "pending_pair_count": len(duplicate_rows),
        "confirmed_pair_count": None,
        "review_decision_counts": {decision: 0 for decision in DUPLICATE_DECISIONS},
        "candidate_review_counts_by_type": {
            "URL_DUPLICATE_PAIRS": len(url_rows),
            "EXACT_CONTENT_DUPLICATE_GROUPS": len(
                {row["duplicate_group_id"] for row in exact_rows}
            ),
            "NEAR_DUPLICATE_PAIRS": len(duplicate_rows),
        },
        "reviewer_sheet_rows": {
            "neutral_template": len(duplicate_rows),
            "reviewer_1": len(duplicate_rows),
            "reviewer_2": len(duplicate_rows),
        },
        "inputs": {
            "canonical_sha256": _sha256(CANONICAL_DEFAULT),
            "master_sample_sha256": _sha256(SAMPLE_DEFAULT),
            "near_duplicate_candidates_sha256": _sha256(NEAR_CANDIDATES_DEFAULT),
            "duplicate_groups_sha256": _sha256(DUPLICATE_GROUPS_DEFAULT),
            "url_duplicate_candidates_sha256": _sha256(URL_CANDIDATES_DEFAULT),
            "exact_duplicate_candidates_sha256": _sha256(EXACT_CANDIDATES_DEFAULT),
        },
        "policy": (
            "Candidate similarities and connected-component groups are not human "
            "duplicate decisions. No source article is modified or merged."
        ),
    }

    for path in (GOLD_REVIEWER_1, GOLD_REVIEWER_2):
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_csv(path, P406_OUTPUT_COLUMNS, gold_rows)
    for path in (
        DUPLICATE_REVIEW_NEUTRAL,
        DUPLICATE_REVIEWER_1,
        DUPLICATE_REVIEWER_2,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_csv(path, DUPLICATE_OUTPUT_COLUMNS, duplicate_rows)
    DUPLICATE_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with DUPLICATE_SUMMARY.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        summary = prepare_packets()
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Review packet preparation failed: {exc}", file=sys.stderr)
        return 1
    print(
        "Prepared 620 independent P4.06 rows per reviewer and "
        f"{summary['candidate_pair_count']} duplicate candidate pairs; "
        f"duplicate status={summary['status']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
