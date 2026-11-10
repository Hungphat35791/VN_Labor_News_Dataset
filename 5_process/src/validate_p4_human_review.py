"""Validate real P4 human submissions and write non-destructive status reports."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
PROCESS = REPO / "5_process"
REPORTS = PROCESS / "reports"
CALIBRATION_1 = PROCESS / "data" / "interim" / "reviewer_1_calibration_sheet.csv"
CALIBRATION_2 = PROCESS / "data" / "interim" / "reviewer_2_calibration_sheet.csv"
ANSWER_KEY = REPORTS / "reviewer_calibration_answer_key.md"
CALIBRATION_LOCK = REPORTS / "reviewer_calibration_lock.json"
P406_1 = PROCESS / "relevance_evaluation" / "p406_reviewer_1_sheet.csv"
P406_2 = PROCESS / "relevance_evaluation" / "p406_reviewer_2_sheet.csv"
CANONICAL = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
DUPLICATE_1 = PROCESS / "data" / "interim" / "duplicate_review_reviewer_1_sheet.csv"
DUPLICATE_2 = PROCESS / "data" / "interim" / "duplicate_review_reviewer_2_sheet.csv"
NEAR_CANDIDATES = PROCESS / "data" / "interim" / "near_duplicate_candidates.csv"
DUPLICATE_GROUPS = PROCESS / "data" / "interim" / "duplicate_groups.csv"
SPLIT_MANIFEST = PROCESS / "splits" / "split_manifest.csv"
ELIGIBILITY_MANIFEST = PROCESS / "splits" / "modeling_eligibility_manifest.csv"

CALIBRATION_COLUMNS = (
    "scenario_id",
    "reviewer_id",
    "relevance_manual",
    "topic_manual",
    "review_reason",
    "review_date",
)
P406_COLUMNS = (
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
P406_STATUSES = {"RELEVANT", "IRRELEVANT", "REVIEW_REQUIRED"}
P406_TOPICS = {
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
}
P406_ANNOTATION_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED", "NEEDS_ADJUDICATION"}
DUPLICATE_COLUMNS = (
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
DUPLICATE_DECISIONS = {
    "CONFIRMED_DUPLICATE",
    "RELATED_BUT_DISTINCT",
    "NOT_DUPLICATE",
    "UNCERTAIN",
    "NEEDS_ADJUDICATION",
}
DUPLICATE_TYPES = {
    "URL_DUPLICATE",
    "EXACT_CONTENT_DUPLICATE",
    "NEAR_DUPLICATE",
    "VERSION_DUPLICATE",
}

CALIBRATION_REPORT = REPORTS / "reviewer_calibration_results.json"
CALIBRATION_FEEDBACK = REPORTS / "reviewer_calibration_feedback.md"
CALIBRATION_REVIEWER_REPORTS = {
    "reviewer_1": REPORTS / "reviewer_calibration_reviewer_1_report.json",
    "reviewer_2": REPORTS / "reviewer_calibration_reviewer_2_report.json",
}
P406_VALIDATION_REPORT = REPORTS / "p406_annotation_validation_report.json"
P406_MISSING = REPORTS / "p406_missing_annotations.csv"
P406_AGREEMENT = REPORTS / "p406_reviewer_agreement_report.json"
P406_QUEUE = REPORTS / "p406_adjudication_queue.csv"
DUPLICATE_VALIDATION = REPORTS / "duplicate_review_validation_report.json"
DUPLICATE_AGREEMENT = REPORTS / "duplicate_reviewer_agreement_report.json"
DUPLICATE_QUEUE = REPORTS / "duplicate_adjudication_queue.csv"
VERSION_REVIEW = REPORTS / "duplicate_version_lineage_review.csv"

P406_QUEUE_COLUMNS = (
    "article_id",
    "reviewer_1_relevance",
    "reviewer_1_topics",
    "reviewer_1_reason",
    "reviewer_1_id",
    "reviewer_1_date",
    "reviewer_2_relevance",
    "reviewer_2_topics",
    "reviewer_2_reason",
    "reviewer_2_id",
    "reviewer_2_date",
    "disagreement_type",
    "adjudication_status",
    "final_relevance_status",
    "final_topic_labels_p406",
    "adjudication_reason",
    "adjudicator_id",
    "adjudication_date",
)
DUPLICATE_QUEUE_COLUMNS = (
    "group_id",
    "article_id_1",
    "article_id_2",
    "reviewer_1_decision",
    "reviewer_1_relationship_type",
    "reviewer_1_version_evidence",
    "reviewer_1_reason",
    "reviewer_1_id",
    "reviewer_1_date",
    "reviewer_2_decision",
    "reviewer_2_relationship_type",
    "reviewer_2_version_evidence",
    "reviewer_2_reason",
    "reviewer_2_id",
    "reviewer_2_date",
    "disagreement_type",
    "adjudication_status",
    "final_decision",
    "final_relationship_type",
    "version_lineage_evidence",
    "adjudication_reason",
    "adjudicator_id",
    "adjudication_date",
)
VERSION_REVIEW_COLUMNS = (
    "group_id",
    "article_id_1",
    "article_id_2",
    "candidate_type",
    "similarity_score",
    "same_source",
    "publish_date_1",
    "publish_date_2",
    "source_url_1",
    "source_url_2",
    "reviewer_1_decision",
    "reviewer_2_decision",
    "confirmed_relationship_type",
    "version_lineage_evidence",
    "review_status",
    "cross_split_candidate",
    "modeling_quarantine",
)


def _read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"{path}: CSV must have a header.")
        missing = sorted(set(required) - set(reader.fieldnames))
        if missing:
            raise ValueError(f"{path}: missing required columns {missing}.")
        return list(reader)


def _validate_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        return False


def _load_key(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    pattern = re.compile(
        r"^\|\s*(CAL-\d{2})\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*"
        r"(SUPPORTED_BY_GUIDELINE|NEEDS_CLARIFICATION|NEEDS_ADJUDICATION)\s*\|$"
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            scenario_id, relevance, topic, status = match.groups()
            rows[scenario_id] = {
                "relevance": relevance.strip(),
                "topic": topic.strip(),
                "status": status,
            }
    if len(rows) != 12:
        raise ValueError(f"{path}: expected 12 answer-key scenarios, parsed {len(rows)}.")
    return rows


def _normalize_manual_relevance(value: str) -> str:
    return {
        "relevant": "Relevant",
        "borderline": "Borderline",
        "not relevant": "Not relevant",
        "uncertain": "Uncertain",
    }.get(value.strip().casefold(), "")


def _manual_topic_code(value: str) -> str:
    match = re.match(r"^\s*([A-L])(?:\s*[-—:]|\s*$)", value, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _read_calibration(path: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows = _read_csv(path, CALIBRATION_COLUMNS)
    seen: set[str] = set()
    errors: list[str] = []
    completed = 0
    for row_number, row in enumerate(rows, start=2):
        scenario_id = (row.get("scenario_id") or "").strip()
        if scenario_id in seen:
            errors.append(f"row {row_number}: duplicate scenario_id {scenario_id!r}")
        seen.add(scenario_id)
        response_fields = {
            field: row.get(field, "").strip()
            for field in CALIBRATION_COLUMNS[1:]
        }
        relevance = _normalize_manual_relevance(response_fields["relevance_manual"])
        required_fields = (
            response_fields["reviewer_id"],
            response_fields["relevance_manual"],
            response_fields["review_reason"],
            response_fields["review_date"],
        )
        response_complete = all(required_fields) and (
            relevance not in {"Relevant", "Borderline"}
            or bool(response_fields["topic_manual"])
        )
        if response_complete:
            completed += 1
            if not relevance:
                errors.append(f"row {row_number}: invalid relevance_manual")
            topic_code = _manual_topic_code(row["topic_manual"])
            if row["topic_manual"].strip() and not topic_code:
                errors.append(f"row {row_number}: invalid topic_manual (expected A-L or blank)")
            if relevance in {"Relevant", "Borderline"} and not topic_code:
                errors.append(f"row {row_number}: Relevant/Borderline requires an A-L topic")
            if relevance in {"Not relevant", "Uncertain"} and row["topic_manual"].strip():
                errors.append(f"row {row_number}: Not relevant/Uncertain requires blank topic")
            if not _validate_date(row["review_date"]):
                errors.append(f"row {row_number}: review_date must be YYYY-MM-DD")
        elif any(response_fields.values()):
            errors.append(f"row {row_number}: partial calibration response")
    reviewer_ids = {
        row["reviewer_id"].strip()
        for row in rows
        if row.get("reviewer_id", "").strip()
    }
    if len(reviewer_ids) > 1:
        errors.append("calibration sheet contains multiple reviewer_id values")
    return rows, {
        "row_count": len(rows),
        "unique_scenario_count": len(seen),
        "completed_response_count": completed,
        "pending_response_count": len(rows) - completed,
        "reviewer_ids": sorted(
            {
                row["reviewer_id"].strip()
                for row in rows
                if row.get("reviewer_id", "").strip()
            }
        ),
        "validation_errors": errors,
    }


def _score_calibration(
    reviewer_rows: list[dict[str, str]], answer_key: dict[str, dict[str, str]]
) -> dict[str, Any]:
    scored: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    for row in reviewer_rows:
        scenario_id = row["scenario_id"].strip()
        key = answer_key.get(scenario_id)
        if key is None:
            counts["INVALID_SCENARIO"] += 1
            scored.append({"scenario_id": scenario_id, "assessment": "INVALID_SCENARIO"})
            continue
        if key["status"] == "NEEDS_CLARIFICATION":
            assessment = "NEEDS_CLARIFICATION"
        elif key["status"] == "NEEDS_ADJUDICATION":
            assessment = "NEEDS_ADJUDICATION"
        else:
            relevance_ok = (
                _normalize_manual_relevance(row["relevance_manual"])
                == key["relevance"]
            )
            expected_topic = _manual_topic_code(key["topic"])
            actual_topic = _manual_topic_code(row["topic_manual"])
            if not relevance_ok:
                assessment = "INCORRECT_LABEL"
            elif expected_topic != actual_topic:
                assessment = "INCORRECT_TOPIC"
            else:
                assessment = "CORRECT"
        counts[assessment] += 1
        scored.append({"scenario_id": scenario_id, "assessment": assessment})
    return {
        "scenario_count": len(scored),
        "assessment_counts": dict(sorted(counts.items())),
        "scenario_results": scored,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_calibration_lock(
    lock_path: Path,
    reviewer_files: dict[str, Path],
    reviewer_ids: dict[str, str],
) -> dict[str, Any]:
    if not lock_path.is_file():
        return {
            "valid": False,
            "file_exists": False,
            "errors": ["CALIBRATION_LOCK_MANIFEST_MISSING"],
        }
    try:
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "valid": False,
            "file_exists": True,
            "errors": [f"CALIBRATION_LOCK_MANIFEST_INVALID:{exc}"],
        }
    reviewers = lock_data.get("reviewers")
    if not isinstance(reviewers, dict):
        return {
            "valid": False,
            "file_exists": True,
            "errors": ["CALIBRATION_LOCK_REVIEWERS_OBJECT_REQUIRED"],
        }
    errors: list[str] = []
    locked_hashes: dict[str, str] = {}
    for reviewer, path in reviewer_files.items():
        entry = reviewers.get(reviewer)
        if not isinstance(entry, dict):
            errors.append(f"{reviewer}:LOCK_ENTRY_MISSING")
            continue
        if entry.get("locked") is not True:
            errors.append(f"{reviewer}:NOT_LOCKED")
        locked_by = entry.get("locked_by")
        if not isinstance(locked_by, str) or not locked_by.strip():
            errors.append(f"{reviewer}:LOCKED_BY_REQUIRED")
        locked_at = entry.get("locked_at", "")
        if not isinstance(locked_at, str):
            locked_at = ""
        try:
            datetime.fromisoformat(locked_at)
        except (TypeError, ValueError):
            errors.append(f"{reviewer}:INVALID_LOCKED_AT")
        claimed_reviewer_id = entry.get("reviewer_id")
        if (
            not isinstance(claimed_reviewer_id, str)
            or claimed_reviewer_id.strip() != reviewer_ids.get(reviewer, "")
        ):
            errors.append(f"{reviewer}:REVIEWER_ID_MISMATCH")
        actual_hash = _file_sha256(path)
        claimed_hash = entry.get("sheet_sha256", "")
        if not isinstance(claimed_hash, str):
            claimed_hash = ""
        if claimed_hash != actual_hash:
            errors.append(f"{reviewer}:SHEET_HASH_MISMATCH")
        else:
            locked_hashes[reviewer] = actual_hash
    return {
        "valid": not errors,
        "file_exists": True,
        "errors": errors,
        "locked_sheet_sha256": locked_hashes,
    }


def _validate_p406_sheet(
    path: Path,
    sample_ids: list[str],
    sample_articles: dict[str, dict[str, str]] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any], dict[str, dict[str, str]]]:
    rows = _read_csv(path, P406_COLUMNS)
    indexed: dict[str, dict[str, str]] = {}
    row_errors: dict[str, list[str]] = defaultdict(list)
    for row_number, row in enumerate(rows, start=2):
        article_id = (row.get("article_id") or "").strip()
        if not article_id:
            row_errors[f"ROW-{row_number}"].append("MISSING_ARTICLE_ID")
            continue
        if article_id in indexed:
            row_errors[article_id].append("DUPLICATE_ARTICLE_ID")
        indexed[article_id] = row
        if sample_articles is not None and article_id in sample_articles:
            for field in ("title", "content"):
                if row.get(field, "") != sample_articles[article_id].get(field, ""):
                    row_errors[article_id].append(f"CHANGED_{field.upper()}")
        status = (row.get("annotation_status") or "").strip()
        relevance = (row.get("gold_relevance_status") or "").strip()
        reason = (row.get("review_reason") or "").strip()
        reviewer = (row.get("reviewer_id") or "").strip()
        review_date = (row.get("review_date") or "").strip()
        raw_topics = (row.get("gold_topic_labels_p406") or "").strip()
        if status not in P406_ANNOTATION_STATUSES:
            row_errors[article_id].append("INVALID_ANNOTATION_STATUS")
        if status in {"COMPLETED", "NEEDS_ADJUDICATION"}:
            if relevance not in P406_STATUSES:
                row_errors[article_id].append("INVALID_OR_MISSING_RELEVANCE")
            topics: list[str] | None = None
            try:
                parsed = json.loads(raw_topics)
                if (
                    not isinstance(parsed, list)
                    or any(not isinstance(topic, str) for topic in parsed)
                    or len(parsed) != len(set(parsed))
                ):
                    raise ValueError
                topics = parsed
            except (json.JSONDecodeError, ValueError):
                row_errors[article_id].append("INVALID_OR_MISSING_TOPIC_JSON")
            if topics is not None:
                if set(topics) - P406_TOPICS:
                    row_errors[article_id].append("TOPIC_OUTSIDE_P406_TAXONOMY")
                if relevance == "RELEVANT" and not topics:
                    row_errors[article_id].append("RELEVANT_REQUIRES_TOPIC")
                if relevance in {"IRRELEVANT", "REVIEW_REQUIRED"} and topics:
                    row_errors[article_id].append("NONRELEVANT_STATUS_REQUIRES_EMPTY_TOPICS")
            if not reason:
                row_errors[article_id].append("MISSING_REVIEW_REASON")
            if not reviewer:
                row_errors[article_id].append("MISSING_REVIEWER_ID")
            if not _validate_date(review_date):
                row_errors[article_id].append("INVALID_OR_MISSING_REVIEW_DATE")
        elif any((relevance, raw_topics, reason, reviewer, review_date)):
            row_errors[article_id].append("INCOMPLETE_NONCOMPLETED_ANNOTATION")
        if status == "PENDING":
            row_errors[article_id].append("PENDING_HUMAN_REVIEW")
        elif status == "IN_PROGRESS":
            row_errors[article_id].append("IN_PROGRESS_HUMAN_REVIEW")

    expected = set(sample_ids)
    actual = set(indexed)
    missing_ids = sorted(expected - actual)
    unexpected_ids = sorted(actual - expected)
    if missing_ids:
        for article_id in missing_ids:
            row_errors[article_id].append("MISSING_REVIEWER_ROW")
    if unexpected_ids:
        for article_id in unexpected_ids:
            row_errors[article_id].append("UNEXPECTED_ARTICLE_ID")
    if [row.get("article_id", "").strip() for row in rows] != sample_ids:
        row_errors["__ORDER__"].append("ID_ORDER_DIFFERS_FROM_MASTER_SAMPLE")
    reviewer_ids = {
        row.get("reviewer_id", "").strip()
        for row in rows
        if row.get("reviewer_id", "").strip()
    }
    if len(reviewer_ids) > 1:
        row_errors["__REVIEWER_ID__"].append("MULTIPLE_REVIEWER_IDS_IN_ONE_SHEET")

    completed_valid = [
        article_id
        for article_id, row in indexed.items()
        if row.get("annotation_status") == "COMPLETED"
        and article_id not in row_errors
        and "__REVIEWER_ID__" not in row_errors
    ]
    counts = Counter(row.get("annotation_status", "") for row in rows)
    return rows, {
        "file": str(path),
        "row_count": len(rows),
        "unique_article_id_count": len(indexed),
        "reviewer_ids": sorted(reviewer_ids),
        "annotation_status_counts": dict(counts),
        "valid_completed_count": len(completed_valid),
        "completion_percent": round(len(completed_valid) * 100 / 620, 2),
        "pending_count": counts["PENDING"],
        "in_progress_count": counts["IN_PROGRESS"],
        "awaiting_adjudication_count": counts["NEEDS_ADJUDICATION"],
        "missing_article_id_count": len(missing_ids),
        "unexpected_article_id_count": len(unexpected_ids),
        "validation_error_count": sum(len(errors) for errors in row_errors.values()),
        "validation_errors_by_article_id": dict(sorted(row_errors.items())),
    }, indexed


def _topic_signature(value: str) -> tuple[str, ...] | None:
    try:
        labels = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(labels, list) or any(not isinstance(label, str) for label in labels):
        return None
    return tuple(sorted(labels))


def _build_p406_agreement(
    one: dict[str, dict[str, str]],
    two: dict[str, dict[str, str]],
    validation_one: dict[str, Any],
    validation_two: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    keys = sorted(set(one) | set(two))
    counts: Counter[str] = Counter()
    queue: list[dict[str, str]] = []
    evaluated = 0
    relevance_agreements = 0
    topic_comparable = 0
    topic_agreements = 0
    for article_id in keys:
        first = one.get(article_id)
        second = two.get(article_id)
        if first is None or second is None:
            counts["MISSING_REVIEWER_ROW"] += 1
            continue
        valid_source_rows = (
            first.get("annotation_status") in {"COMPLETED", "NEEDS_ADJUDICATION"}
            and second.get("annotation_status") in {"COMPLETED", "NEEDS_ADJUDICATION"}
            and article_id not in validation_one["validation_errors_by_article_id"]
            and article_id not in validation_two["validation_errors_by_article_id"]
            and "__REVIEWER_ID__" not in validation_one["validation_errors_by_article_id"]
            and "__REVIEWER_ID__" not in validation_two["validation_errors_by_article_id"]
            and first.get("reviewer_id", "").strip()
            and second.get("reviewer_id", "").strip()
            and first.get("reviewer_id", "").strip()
            != second.get("reviewer_id", "").strip()
        )
        if not valid_source_rows:
            counts["NOT_BOTH_VALID_COMPLETED"] += 1
            continue
        reviewer_requested = (
            first.get("annotation_status") == "NEEDS_ADJUDICATION"
            or second.get("annotation_status") == "NEEDS_ADJUDICATION"
        )
        if reviewer_requested:
            counts["REVIEWER_REQUESTED_ADJUDICATION"] += 1
            queue.append(
                {
                    "article_id": article_id,
                    "reviewer_1_relevance": first.get("gold_relevance_status", ""),
                    "reviewer_1_topics": first.get("gold_topic_labels_p406", ""),
                    "reviewer_1_reason": first.get("review_reason", ""),
                    "reviewer_1_id": first.get("reviewer_id", ""),
                    "reviewer_1_date": first.get("review_date", ""),
                    "reviewer_2_relevance": second.get("gold_relevance_status", ""),
                    "reviewer_2_topics": second.get("gold_topic_labels_p406", ""),
                    "reviewer_2_reason": second.get("review_reason", ""),
                    "reviewer_2_id": second.get("reviewer_id", ""),
                    "reviewer_2_date": second.get("review_date", ""),
                    "disagreement_type": "REVIEWER_REQUESTED_ADJUDICATION",
                    "adjudication_status": "PENDING",
                    "final_relevance_status": "",
                    "final_topic_labels_p406": "",
                    "adjudication_reason": "",
                    "adjudicator_id": "",
                    "adjudication_date": "",
                }
            )
            continue
        if (
            first.get("annotation_status") != "COMPLETED"
            or second.get("annotation_status") != "COMPLETED"
        ):
            counts["NOT_BOTH_VALID_COMPLETED"] += 1
            continue
        evaluated += 1
        relevance_diff = first["gold_relevance_status"] != second["gold_relevance_status"]
        topics_one = _topic_signature(first["gold_topic_labels_p406"])
        topics_two = _topic_signature(second["gold_topic_labels_p406"])
        topic_diff = topics_one != topics_two
        relevance_agreements += int(not relevance_diff)
        if (
            first["gold_relevance_status"] == "RELEVANT"
            and second["gold_relevance_status"] == "RELEVANT"
        ):
            topic_comparable += 1
            topic_agreements += int(not topic_diff)
        if relevance_diff and topic_diff:
            kind = "RELEVANCE_AND_TOPIC_DISAGREEMENT"
        elif relevance_diff:
            kind = "RELEVANCE_DISAGREEMENT"
        elif topic_diff:
            kind = "TOPIC_DISAGREEMENT"
        else:
            kind = "AGREEMENT"
        counts[kind] += 1
        if kind != "AGREEMENT":
            queue.append(
                {
                    "article_id": article_id,
                    "reviewer_1_relevance": first["gold_relevance_status"],
                    "reviewer_1_topics": first["gold_topic_labels_p406"],
                    "reviewer_1_reason": first["review_reason"],
                    "reviewer_1_id": first["reviewer_id"],
                    "reviewer_1_date": first["review_date"],
                    "reviewer_2_relevance": second["gold_relevance_status"],
                    "reviewer_2_topics": second["gold_topic_labels_p406"],
                    "reviewer_2_reason": second["review_reason"],
                    "reviewer_2_id": second["reviewer_id"],
                    "reviewer_2_date": second["review_date"],
                    "disagreement_type": kind,
                    "adjudication_status": "PENDING",
                    "final_relevance_status": "",
                    "final_topic_labels_p406": "",
                    "adjudication_reason": "",
                    "adjudicator_id": "",
                    "adjudication_date": "",
                }
            )
    total_expected = 620
    return (
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": (
                "WAITING_FOR_ADJUDICATION"
                if counts["REVIEWER_REQUESTED_ADJUDICATION"]
                or counts["RELEVANCE_DISAGREEMENT"]
                    + counts["TOPIC_DISAGREEMENT"]
                    + counts["RELEVANCE_AND_TOPIC_DISAGREEMENT"]
                else "WAITING_FOR_REVIEWERS"
                if evaluated == 0
                else "PARTIALLY_COMPLETED"
            ),
            "expected_sample_size": total_expected,
            "valid_completed_by_both": evaluated,
            "agreement_count": counts["AGREEMENT"],
            "relevance_disagreement_count": counts["RELEVANCE_DISAGREEMENT"],
            "topic_disagreement_count": counts["TOPIC_DISAGREEMENT"],
            "relevance_and_topic_disagreement_count": counts[
                "RELEVANCE_AND_TOPIC_DISAGREEMENT"
            ],
            "not_comparable_or_missing_count": total_expected - evaluated,
            "adjudication_queue_count": len(queue),
            "agreement_metrics": {
                "relevance": {
                    "agreement_count": relevance_agreements,
                    "comparable_count": evaluated,
                    "raw_agreement": (
                        round(relevance_agreements / evaluated, 4)
                        if evaluated
                        else None
                    ),
                },
                "topics_among_both_relevant": {
                    "agreement_count": topic_agreements,
                    "comparable_count": topic_comparable,
                    "raw_agreement": (
                        round(topic_agreements / topic_comparable, 4)
                        if topic_comparable
                        else None
                    ),
                },
            },
            "note": (
                "Raw agreement is reported only for records with two valid independent "
                "completed reviews. No chance-corrected coefficient is calculated."
            ),
        },
        queue,
    )


def _validate_duplicate_sheet(
    path: Path,
    expected_pairs: list[tuple[str, str]],
    candidate_context: dict[tuple[str, str], dict[str, str]] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any], dict[tuple[str, str], dict[str, str]]]:
    rows = _read_csv(path, DUPLICATE_COLUMNS)
    indexed: dict[tuple[str, str], dict[str, str]] = {}
    errors: dict[str, list[str]] = defaultdict(list)
    for row_number, row in enumerate(rows, start=2):
        first = (row.get("article_id_1") or "").strip()
        second = (row.get("article_id_2") or "").strip()
        pair = tuple(sorted((first, second)))
        key = "|".join(pair)
        if not first or not second or first == second:
            errors[f"ROW-{row_number}"].append("INVALID_PAIR")
            continue
        if pair in indexed:
            errors[key].append("DUPLICATE_PAIR")
        indexed[pair] = row
        expected = (candidate_context or {}).get(pair)
        if expected is not None:
            fields = {
                "group_id": "group_id",
                "article_id_1": "article_id_1",
                "article_id_2": "article_id_2",
                "title_1": "title_1",
                "title_2": "title_2",
                "content_1": "content_1",
                "content_2": "content_2",
                "source_name_1": "source_name_1",
                "source_name_2": "source_name_2",
                "publish_date_1": "publish_date_1",
                "publish_date_2": "publish_date_2",
                "source_url_1": "source_url_1",
                "source_url_2": "source_url_2",
                "similarity_score": "similarity_score",
                "candidate_type": "candidate_type",
            }
            for field, context_key in fields.items():
                if row.get(field, "") != expected.get(context_key, ""):
                    errors[key].append(f"CHANGED_OR_MISMATCHED_{field.upper()}")
        status = (row.get("review_status") or "").strip()
        decision = (row.get("review_decision") or "").strip()
        relationship = (row.get("confirmed_relationship_type") or "").strip()
        evidence = (row.get("version_lineage_evidence") or "").strip()
        if status not in {"PENDING", "IN_PROGRESS", "COMPLETED", "NEEDS_ADJUDICATION"}:
            errors[key].append("INVALID_REVIEW_STATUS")
        if decision:
            if decision not in DUPLICATE_DECISIONS:
                errors[key].append("INVALID_REVIEW_DECISION")
            if not (row.get("reviewer_id") or "").strip():
                errors[key].append("MISSING_REVIEWER_ID")
            if not (row.get("review_reason") or "").strip():
                errors[key].append("MISSING_REVIEW_REASON")
            if not _validate_date((row.get("review_date") or "").strip()):
                errors[key].append("INVALID_OR_MISSING_REVIEW_DATE")
            if decision == "CONFIRMED_DUPLICATE":
                if relationship not in DUPLICATE_TYPES:
                    errors[key].append("INVALID_OR_MISSING_CONFIRMED_RELATIONSHIP_TYPE")
                if relationship == "VERSION_DUPLICATE" and not evidence:
                    errors[key].append("VERSION_DUPLICATE_REQUIRES_LINEAGE_EVIDENCE")
            elif relationship or evidence:
                errors[key].append("RELATIONSHIP_EVIDENCE_REQUIRES_CONFIRMED_DUPLICATE")
            if decision == "NEEDS_ADJUDICATION" and status != "NEEDS_ADJUDICATION":
                errors[key].append("ADJUDICATION_DECISION_STATUS_MISMATCH")
            if decision != "NEEDS_ADJUDICATION" and status != "COMPLETED":
                errors[key].append("DECIDED_PAIR_MUST_BE_COMPLETED")
        elif any(
            (row.get(field) or "").strip()
            for field in (
                "reviewer_id",
                "review_reason",
                "review_date",
                "confirmed_relationship_type",
                "version_lineage_evidence",
            )
        ):
            errors[key].append("PARTIAL_REVIEW_RESPONSE")

    actual_pairs = set(indexed)
    expected_set = set(expected_pairs)
    missing = expected_set - actual_pairs
    unexpected = actual_pairs - expected_set
    if missing:
        errors["__MISSING_PAIRS__"].append(f"{len(missing)} expected candidate pairs missing")
    if unexpected:
        errors["__UNEXPECTED_PAIRS__"].append(f"{len(unexpected)} non-candidate pairs found")
    if list(indexed) != expected_pairs:
        errors["__ORDER__"].append("PAIR_ORDER_DIFFERS_FROM_CANDIDATE_INPUT")
    reviewer_ids = {
        row.get("reviewer_id", "").strip()
        for row in rows
        if row.get("reviewer_id", "").strip()
    }
    if len(reviewer_ids) > 1:
        errors["__REVIEWER_ID__"].append("MULTIPLE_REVIEWER_IDS_IN_ONE_SHEET")

    decisions = Counter(
        row["review_decision"].strip()
        for row in rows
        if (row.get("review_decision") or "").strip()
    )
    complete_decisions = 0
    if len(reviewer_ids) <= 1:
        for pair, row in indexed.items():
            pair_key = "|".join(pair)
            decision = (row.get("review_decision") or "").strip()
            status = row.get("review_status")
            if (
                decision
                and status in {"COMPLETED", "NEEDS_ADJUDICATION"}
                and pair_key not in errors
            ):
                complete_decisions += 1
    return rows, {
        "file": str(path),
        "row_count": len(rows),
        "unique_pair_count": len(indexed),
        "reviewer_ids": sorted(reviewer_ids),
        "completed_or_escalated_decision_count": complete_decisions,
        "pending_pair_count": len(expected_pairs) - complete_decisions,
        "decision_counts": dict(decisions),
        "validation_error_count": sum(len(v) for v in errors.values()),
        "validation_errors_by_pair": dict(sorted(errors.items())),
    }, indexed


def _build_duplicate_agreement(
    one: dict[tuple[str, str], dict[str, str]],
    two: dict[tuple[str, str], dict[str, str]],
    validation_one: dict[str, Any],
    validation_two: dict[str, Any],
    pair_rows: dict[tuple[str, str], dict[str, str]],
) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    pairs = sorted(set(one) | set(two))
    counts: Counter[str] = Counter()
    queue: list[dict[str, str]] = []
    version_rows: list[dict[str, str]] = []
    comparable = 0
    decision_agreements = 0
    relationship_comparable = 0
    relationship_agreements = 0
    reviewer_consensus_duplicates = 0
    reviewer_consensus_version_lineages = 0
    errors_one = validation_one["validation_errors_by_pair"]
    errors_two = validation_two["validation_errors_by_pair"]
    for pair in pairs:
        first, second = one.get(pair), two.get(pair)
        key = "|".join(pair)
        valid_pair_reviews = bool(
            first is not None
            and second is not None
            and key not in errors_one
            and key not in errors_two
            and "__REVIEWER_ID__" not in errors_one
            and "__REVIEWER_ID__" not in errors_two
            and first.get("review_decision", "").strip()
            and second.get("review_decision", "").strip()
            and first.get("reviewer_id", "").strip()
            and second.get("reviewer_id", "").strip()
            and first.get("reviewer_id", "").strip()
            != second.get("reviewer_id", "").strip()
        )
        if not valid_pair_reviews:
            counts["NOT_BOTH_VALID_REVIEWED"] += 1
            continue
        if (
            first.get("review_decision") == "NEEDS_ADJUDICATION"
            or second.get("review_decision") == "NEEDS_ADJUDICATION"
        ):
            base = pair_rows.get(pair, {})
            counts["REVIEWER_REQUESTED_ADJUDICATION"] += 1
            queue.append(
                {
                    "group_id": base.get("group_id", ""),
                    "article_id_1": (pair_rows.get(pair) or {}).get("article_id_1", pair[0]),
                    "article_id_2": (pair_rows.get(pair) or {}).get("article_id_2", pair[1]),
                    "reviewer_1_decision": (first or {}).get("review_decision", ""),
                    "reviewer_1_relationship_type": (first or {}).get(
                        "confirmed_relationship_type", ""
                    ),
                    "reviewer_1_version_evidence": (first or {}).get(
                        "version_lineage_evidence", ""
                    ),
                    "reviewer_1_reason": (first or {}).get("review_reason", ""),
                    "reviewer_1_id": (first or {}).get("reviewer_id", ""),
                    "reviewer_1_date": (first or {}).get("review_date", ""),
                    "reviewer_2_decision": (second or {}).get("review_decision", ""),
                    "reviewer_2_relationship_type": (second or {}).get(
                        "confirmed_relationship_type", ""
                    ),
                    "reviewer_2_version_evidence": (second or {}).get(
                        "version_lineage_evidence", ""
                    ),
                    "reviewer_2_reason": (second or {}).get("review_reason", ""),
                    "reviewer_2_id": (second or {}).get("reviewer_id", ""),
                    "reviewer_2_date": (second or {}).get("review_date", ""),
                    "disagreement_type": "REVIEWER_REQUESTED_ADJUDICATION",
                    "adjudication_status": "PENDING",
                    "final_decision": "",
                    "final_relationship_type": "",
                    "version_lineage_evidence": "",
                    "adjudication_reason": "",
                    "adjudicator_id": "",
                    "adjudication_date": "",
                }
            )
            continue
        comparable += 1
        decision_one = first["review_decision"].strip()
        decision_two = second["review_decision"].strip()
        relationship_one = first["confirmed_relationship_type"].strip()
        relationship_two = second["confirmed_relationship_type"].strip()
        evidence_one = first["version_lineage_evidence"].strip()
        evidence_two = second["version_lineage_evidence"].strip()
        decision_agreements += int(decision_one == decision_two)
        if (
            decision_one == "CONFIRMED_DUPLICATE"
            and decision_two == "CONFIRMED_DUPLICATE"
        ):
            relationship_comparable += 1
            relationship_agreements += int(relationship_one == relationship_two)
            if relationship_one == relationship_two:
                reviewer_consensus_duplicates += 1
                if (
                    relationship_one == "VERSION_DUPLICATE"
                    and evidence_one
                    and evidence_two
                ):
                    reviewer_consensus_version_lineages += 1
        if decision_one == decision_two and relationship_one == relationship_two:
            kind = "AGREEMENT"
        elif decision_one == decision_two:
            kind = "RELATIONSHIP_TYPE_DISAGREEMENT"
        else:
            kind = "DECISION_DISAGREEMENT"
        counts[kind] += 1
        if kind != "AGREEMENT":
            base = pair_rows.get(pair, {})
            queue.append(
                {
                    "group_id": base.get("group_id", ""),
                    "article_id_1": base.get("article_id_1", pair[0]),
                    "article_id_2": base.get("article_id_2", pair[1]),
                    "reviewer_1_decision": decision_one,
                    "reviewer_1_relationship_type": relationship_one,
                    "reviewer_1_version_evidence": evidence_one,
                    "reviewer_1_reason": first["review_reason"],
                    "reviewer_1_id": first["reviewer_id"],
                    "reviewer_1_date": first["review_date"],
                    "reviewer_2_decision": decision_two,
                    "reviewer_2_relationship_type": relationship_two,
                    "reviewer_2_version_evidence": evidence_two,
                    "reviewer_2_reason": second["review_reason"],
                    "reviewer_2_id": second["reviewer_id"],
                    "reviewer_2_date": second["review_date"],
                    "disagreement_type": kind,
                    "adjudication_status": "PENDING",
                    "final_decision": "",
                    "final_relationship_type": "",
                    "version_lineage_evidence": "",
                    "adjudication_reason": "",
                    "adjudicator_id": "",
                    "adjudication_date": "",
                }
            )
        base = pair_rows.get(pair, {})
    for pair in pairs:
        first, second = one.get(pair, {}), two.get(pair, {})
        base = pair_rows.get(pair, {})
        relationship_one = first.get("confirmed_relationship_type", "").strip()
        relationship_two = second.get("confirmed_relationship_type", "").strip()
        evidence_one = first.get("version_lineage_evidence", "").strip()
        evidence_two = second.get("version_lineage_evidence", "").strip()
        has_lineage_submission = bool(
            relationship_one == "VERSION_DUPLICATE"
            or relationship_two == "VERSION_DUPLICATE"
            or evidence_one
            or evidence_two
        )
        decisions_complete = bool(
            first.get("review_decision", "").strip()
            and second.get("review_decision", "").strip()
        )
        version_rows.append(
            {
                "group_id": base.get("group_id", ""),
                "article_id_1": pair[0],
                "article_id_2": pair[1],
                "candidate_type": base.get("candidate_type", ""),
                "similarity_score": base.get("similarity_score", ""),
                "same_source": str(
                    base.get("source_name_1", "") == base.get("source_name_2", "")
                ).lower(),
                "publish_date_1": base.get("publish_date_1", ""),
                "publish_date_2": base.get("publish_date_2", ""),
                "source_url_1": base.get("source_url_1", ""),
                "source_url_2": base.get("source_url_2", ""),
                "reviewer_1_decision": first.get("review_decision", "").strip(),
                "reviewer_2_decision": second.get("review_decision", "").strip(),
                "confirmed_relationship_type": (
                    relationship_one if relationship_one == relationship_two else ""
                ),
                "version_lineage_evidence": json.dumps(
                    {"reviewer_1": evidence_one, "reviewer_2": evidence_two},
                    ensure_ascii=False,
                )
                if has_lineage_submission
                else "",
                "review_status": (
                    "NEEDS_ADJUDICATION"
                    if decisions_complete
                    and (
                        first.get("review_decision") != second.get("review_decision")
                        or relationship_one != relationship_two
                    )
                    else "REVIEWED"
                    if decisions_complete
                    else "PENDING"
                ),
                "cross_split_candidate": base.get("cross_split_candidate", "false"),
                "modeling_quarantine": base.get("modeling_quarantine", "false"),
            }
        )
    return (
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": (
                "WAITING_FOR_ADJUDICATION"
                if counts["REVIEWER_REQUESTED_ADJUDICATION"]
                or counts["DECISION_DISAGREEMENT"]
                or counts["RELATIONSHIP_TYPE_DISAGREEMENT"]
                else "WAITING_FOR_DUPLICATE_REVIEW"
                if comparable == 0
                else "PARTIALLY_COMPLETED"
            ),
            "candidate_pair_count": len(pairs),
            "valid_reviewed_by_both_count": comparable,
            "agreement_count": counts["AGREEMENT"],
            "decision_disagreement_count": counts["DECISION_DISAGREEMENT"],
            "relationship_type_disagreement_count": counts[
                "RELATIONSHIP_TYPE_DISAGREEMENT"
            ],
            "not_comparable_or_pending_count": len(pairs) - comparable,
            "adjudication_queue_count": len(queue),
            "confirmed_duplicate_count": reviewer_consensus_duplicates,
            "confirmed_version_lineage_count": reviewer_consensus_version_lineages,
            "confirmation_basis": (
                "Two independent reviewers agree on CONFIRMED_DUPLICATE and the same "
                "relationship type; version lineage additionally requires evidence from both."
            ),
            "agreement_metrics": {
                "decision": {
                    "agreement_count": decision_agreements,
                    "comparable_count": comparable,
                    "raw_agreement": (
                        round(decision_agreements / comparable, 4)
                        if comparable
                        else None
                    ),
                },
                "relationship_type_among_both_confirmed": {
                    "agreement_count": relationship_agreements,
                    "comparable_count": relationship_comparable,
                    "raw_agreement": (
                        round(relationship_agreements / relationship_comparable, 4)
                        if relationship_comparable
                        else None
                    ),
                },
            },
        },
        queue,
        version_rows,
    )


def _parse_answer_key_and_calibration() -> tuple[
    dict[str, Any], str, dict[str, dict[str, Any]]
]:
    expected = _load_key(ANSWER_KEY)
    one, stats_one = _read_calibration(CALIBRATION_1)
    two, stats_two = _read_calibration(CALIBRATION_2)
    expected_ids = list(expected)
    structure_ok = (
        [row["scenario_id"].strip() for row in one] == expected_ids
        and [row["scenario_id"].strip() for row in two] == expected_ids
    )
    reviewers_are_distinct = (
        len(stats_one["reviewer_ids"]) == 1
        and len(stats_two["reviewer_ids"]) == 1
        and stats_one["reviewer_ids"][0] != stats_two["reviewer_ids"][0]
    )
    both_complete = (
        stats_one["completed_response_count"] == 12
        and stats_two["completed_response_count"] == 12
        and not stats_one["validation_errors"]
        and not stats_two["validation_errors"]
        and structure_ok
        and reviewers_are_distinct
    )
    lock_report = _validate_calibration_lock(
        CALIBRATION_LOCK,
        {"reviewer_1": CALIBRATION_1, "reviewer_2": CALIBRATION_2},
        {
            "reviewer_1": stats_one["reviewer_ids"][0]
            if len(stats_one["reviewer_ids"]) == 1
            else "",
            "reviewer_2": stats_two["reviewer_ids"][0]
            if len(stats_two["reviewer_ids"]) == 1
            else "",
        },
    )
    ready_to_score = both_complete and lock_report["valid"]
    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "WAITING_FOR_REVIEWERS"
            if not both_complete
            else "WAITING_FOR_REVIEWER_LOCK"
            if not lock_report["valid"]
            else "COMPLETED"
        ),
        "answer_key_version": "1.0.0",
        "calibration_scenario_count": 12,
        "reviewers": {
            "reviewer_1": stats_one,
            "reviewer_2": stats_two,
        },
        "both_reviewers_complete": both_complete,
        "reviewer_independence_verified": reviewers_are_distinct,
        "reviewer_lock_validation": lock_report,
        "both_reviewers_locked": lock_report["valid"],
        "reviewer_comparison": None,
        "scoring_policy": (
            "Answer key is consulted only after both independent sheets contain 12 "
            "complete, valid responses in the expected scenario order and a coordinator "
            "lock manifest matches both exact sheet hashes."
        ),
    }
    feedback = [
        "# Reviewer Calibration Feedback",
        "",
        f"**Status:** `{report['status']}`",
        "",
        "- Reviewer 1 completed responses: "
        f"{stats_one['completed_response_count']}/12",
        "- Reviewer 2 completed responses: "
        f"{stats_two['completed_response_count']}/12",
        (
            "- The answer key has not been applied because both submissions are not "
            "complete and valid."
            if not both_complete
            else "- The answer key has not been applied because the coordinator lock "
            "manifest is missing, invalid, or stale."
            if not lock_report["valid"]
            else "- The answer key was applied after both submissions were complete, "
            "valid, and locked by matching SHA-256."
        ),
        "- No reviewer answers were created, changed, or inferred.",
    ]
    reviewer_reports: dict[str, dict[str, Any]] = {
        "reviewer_1": {
            "status": "WAITING_FOR_REVIEWERS",
            "reviewer_validation": stats_one,
            "scoring": None,
        },
        "reviewer_2": {
            "status": "WAITING_FOR_REVIEWERS",
            "reviewer_validation": stats_two,
            "scoring": None,
        },
    }
    if ready_to_score:
        score_one = _score_calibration(one, expected)
        score_two = _score_calibration(two, expected)
        disagreements = []
        by_scenario_one = {row["scenario_id"]: row for row in score_one["scenario_results"]}
        by_scenario_two = {row["scenario_id"]: row for row in score_two["scenario_results"]}
        reviewer_rows_one = {row["scenario_id"]: row for row in one}
        reviewer_rows_two = {row["scenario_id"]: row for row in two}
        response_disagreements = []
        for scenario_id in expected_ids:
            if by_scenario_one[scenario_id]["assessment"] != by_scenario_two[scenario_id]["assessment"]:
                disagreements.append(scenario_id)
            response_one = reviewer_rows_one[scenario_id]
            response_two = reviewer_rows_two[scenario_id]
            if (
                _normalize_manual_relevance(response_one["relevance_manual"])
                != _normalize_manual_relevance(response_two["relevance_manual"])
                or _manual_topic_code(response_one["topic_manual"])
                != _manual_topic_code(response_two["topic_manual"])
            ):
                response_disagreements.append(scenario_id)
        report["status"] = "COMPLETED"
        report["reviewer_comparison"] = {
            "reviewer_1": score_one,
            "reviewer_2": score_two,
            "assessment_disagreement_scenario_ids": disagreements,
            "response_disagreement_scenario_ids": response_disagreements,
        }
        for reviewer, result, stats in (
            ("reviewer_1", score_one, stats_one),
            ("reviewer_2", score_two, stats_two),
        ):
            errors = [
                row["scenario_id"]
                for row in result["scenario_results"]
                if row["assessment"] in {"INCORRECT_LABEL", "INCORRECT_TOPIC"}
            ]
            reviewer_reports[reviewer] = {
                "status": "COMPLETED",
                "reviewer_validation": stats,
                "scoring": result,
                "incorrect_or_misclassified_scenario_ids": errors,
                "retraining_recommendation": (
                    "Revisit the relevant A-L boundary and provide evidence-based "
                    "rationale for scenarios assessed incorrectly."
                    if errors
                    else "No supported-key label/topic errors detected; retain "
                    "clarification and adjudication scenarios as unresolved policy cases."
                ),
            }
        feedback = [
            "# Reviewer Calibration Feedback",
            "",
            "**Status:** `COMPLETED`",
            "",
            "Reference scoring was run only after both complete submissions were found.",
            "",
        ]
        for reviewer, result in (("Reviewer 1", score_one), ("Reviewer 2", score_two)):
            feedback.append(f"## {reviewer}")
            feedback.append("")
            for status, count in sorted(result["assessment_counts"].items()):
                feedback.append(f"- {status}: {count}")
            feedback.append("")
        feedback.extend(
            [
                "## Policy-dependent scenarios",
                "",
                "- CAL-03 remains `NEEDS_CLARIFICATION` regardless of the key's "
                "supported relevance label; no primary-topic tie-break is invented.",
                "- CAL-09 remains `NEEDS_ADJUDICATION`; the answer key does not force "
                "a gold label or topic.",
                "",
                "Calibration is not production annotation and does not create gold labels.",
            ]
        )
    report["individual_reviewer_report_paths"] = {
        reviewer: str(path)
        for reviewer, path in CALIBRATION_REVIEWER_REPORTS.items()
    }
    return report, "\n".join(feedback) + "\n", reviewer_reports


def _build_duplicate_context() -> tuple[list[dict[str, str]], list[tuple[str, str]], dict[tuple[str, str], dict[str, str]]]:
    canonical = _read_csv(
        CANONICAL,
        ("article_id", "title", "content", "source_name", "publish_date", "source_url"),
    )
    article_index = {row["article_id"]: row for row in canonical}
    groups = _read_csv(DUPLICATE_GROUPS, ("duplicate_group_id", "article_id"))
    group_index: dict[str, str] = {}
    for row in groups:
        article_id = row["article_id"]
        group_id = row["duplicate_group_id"]
        if article_id in group_index and group_index[article_id] != group_id:
            raise ValueError(f"Article {article_id} occurs in multiple duplicate groups.")
        group_index[article_id] = group_id
    candidates = _read_csv(NEAR_CANDIDATES, ("article_id_1", "article_id_2", "similarity_score", "duplicate_type"))

    split_index = {}
    if SPLIT_MANIFEST.exists():
        split_index = {
            row["article_id"]: row["split"]
            for row in _read_csv(SPLIT_MANIFEST, ("article_id", "split"))
        }
    held_ids: set[str] = set()
    if ELIGIBILITY_MANIFEST.exists():
        held_ids = {
            row["article_id"]
            for row in _read_csv(
                ELIGIBILITY_MANIFEST, ("article_id", "modeling_split", "hold_reason")
            )
            if row["modeling_split"] == "review_hold"
        }

    pair_rows: list[dict[str, str]] = []
    expected_pairs: list[tuple[str, str]] = []
    pair_map: dict[tuple[str, str], dict[str, str]] = {}
    for row in candidates:
        first, second = row["article_id_1"].strip(), row["article_id_2"].strip()
        pair = tuple(sorted((first, second)))
        if pair in pair_map:
            raise ValueError(f"Duplicate candidate pair {pair}.")
        if first not in article_index or second not in article_index:
            raise ValueError(f"Candidate pair {pair} contains an ID absent from canonical CSV.")
        if group_index.get(first) != group_index.get(second):
            raise ValueError(f"Candidate pair {pair} does not share one candidate group.")
        left, right = article_index[first], article_index[second]
        split_pair = {split_index.get(first, ""), split_index.get(second, "")}
        cross = len(split_pair - {""}) > 1
        context = {
            "group_id": group_index[first],
            "article_id_1": first,
            "article_id_2": second,
            "title_1": left["title"],
            "title_2": right["title"],
            "content_1": left.get("content", ""),
            "content_2": right.get("content", ""),
            "candidate_type": row["duplicate_type"],
            "similarity_score": row["similarity_score"],
            "source_name_1": left["source_name"],
            "source_name_2": right["source_name"],
            "publish_date_1": left["publish_date"],
            "publish_date_2": right["publish_date"],
            "source_url_1": left["source_url"],
            "source_url_2": right["source_url"],
            "cross_split_candidate": str(cross).lower(),
            "modeling_quarantine": str(first in held_ids or second in held_ids).lower(),
        }
        expected_pairs.append(pair)
        pair_map[pair] = context
        pair_rows.append(context)
    if len(expected_pairs) != 70 or len({r["group_id"] for r in pair_rows}) != 61:
        raise ValueError("Expected 70 candidate pairs in 61 groups.")
    return pair_rows, expected_pairs, pair_map


def validate_all(overwrite_reports: bool = False) -> dict[str, Any]:
    targets = (
        CALIBRATION_REPORT,
        CALIBRATION_FEEDBACK,
        *CALIBRATION_REVIEWER_REPORTS.values(),
        P406_VALIDATION_REPORT,
        P406_MISSING,
        P406_AGREEMENT,
        P406_QUEUE,
        DUPLICATE_VALIDATION,
        DUPLICATE_AGREEMENT,
        DUPLICATE_QUEUE,
        VERSION_REVIEW,
    )
    existing = [str(path) for path in targets if path.exists()]
    if existing and not overwrite_reports:
        raise FileExistsError("Refusing to overwrite reports: " + ", ".join(existing))

    calibration, feedback, calibration_reviewer_reports = (
        _parse_answer_key_and_calibration()
    )
    sample_rows = _read_csv(
        PROCESS / "data" / "interim" / "relevance_review_sample.csv",
        ("article_id", "title", "content"),
    )
    sample_ids = [row["article_id"].strip() for row in sample_rows]
    if len(sample_ids) != 620 or len(set(sample_ids)) != 620:
        raise ValueError("P4.06 source sample must have 620 unique article IDs.")
    sample_articles = {row["article_id"].strip(): row for row in sample_rows}
    _, p406_stats_1, p406_index_1 = _validate_p406_sheet(
        P406_1, sample_ids, sample_articles
    )
    _, p406_stats_2, p406_index_2 = _validate_p406_sheet(
        P406_2, sample_ids, sample_articles
    )
    p406_agreement, p406_queue = _build_p406_agreement(
        p406_index_1, p406_index_2, p406_stats_1, p406_stats_2
    )
    missing_rows: list[dict[str, str]] = []
    for reviewer, stats in (("reviewer_1", p406_stats_1), ("reviewer_2", p406_stats_2)):
        for article_id, errors in stats["validation_errors_by_article_id"].items():
            reviewer_index = p406_index_1 if reviewer == "reviewer_1" else p406_index_2
            row = reviewer_index.get(article_id, {})
            missing_rows.append(
                {
                    "reviewer": reviewer,
                    "article_id": article_id,
                    "annotation_status": row.get("annotation_status", ""),
                    "missing_or_invalid_fields": ";".join(errors),
                }
            )
    p406_validation = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "WAITING_FOR_ADJUDICATION"
            if p406_agreement["adjudication_queue_count"]
            else "WAITING_FOR_REVIEWERS"
            if p406_stats_1["valid_completed_count"] == 0
            and p406_stats_2["valid_completed_count"] == 0
            else "PARTIALLY_COMPLETED"
        ),
        "master_sample_count": len(sample_rows),
        "reviewer_1": p406_stats_1,
        "reviewer_2": p406_stats_2,
        "taxonomy_note": (
            "This validator accepts only P4.06 statuses/topics. Legacy A-L manual "
            "values are not converted or accepted as P4.06 labels."
        ),
    }
    duplicate_rows, expected_pairs, pair_map = _build_duplicate_context()
    _, duplicate_stats_1, duplicate_index_1 = _validate_duplicate_sheet(
        DUPLICATE_1, expected_pairs, pair_map
    )
    _, duplicate_stats_2, duplicate_index_2 = _validate_duplicate_sheet(
        DUPLICATE_2, expected_pairs, pair_map
    )
    duplicate_agreement, duplicate_queue, version_rows = _build_duplicate_agreement(
        duplicate_index_1,
        duplicate_index_2,
        duplicate_stats_1,
        duplicate_stats_2,
        pair_map,
    )
    duplicate_validation = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "WAITING_FOR_DUPLICATE_REVIEW"
            if duplicate_stats_1["completed_or_escalated_decision_count"] == 0
            and duplicate_stats_2["completed_or_escalated_decision_count"] == 0
            else "PARTIALLY_COMPLETED"
        ),
        "candidate_pair_count": len(expected_pairs),
        "candidate_group_count": len({row["group_id"] for row in duplicate_rows}),
        "canonical_article_count": len(
            _read_csv(
                CANONICAL,
                ("article_id", "title", "content", "source_name", "publish_date", "source_url"),
            )
        ),
        "pairs_with_missing_canonical_articles": 0,
        "reviewer_1": duplicate_stats_1,
        "reviewer_2": duplicate_stats_2,
        "cross_split_candidate_pair_count": sum(
            row["cross_split_candidate"] == "true" for row in duplicate_rows
        ),
        "cross_split_candidate_group_ids": sorted(
            {
                row["group_id"]
                for row in duplicate_rows
                if row["cross_split_candidate"] == "true"
            }
        ),
        "cross_split_candidate_group_count": len(
            {
                row["group_id"]
                for row in duplicate_rows
                if row["cross_split_candidate"] == "true"
            }
        ),
        "candidate_pairs_with_modeling_quarantine_count": sum(
            row["modeling_quarantine"] == "true" for row in duplicate_rows
        ),
        "cross_split_pairs_without_existing_modeling_quarantine_count": sum(
            row["cross_split_candidate"] == "true"
            and row["modeling_quarantine"] != "true"
            for row in duplicate_rows
        ),
        "version_lineage_review_candidate_count": len(version_rows),
        "version_lineage_verification_count": sum(
        row["confirmed_relationship_type"] == "VERSION_DUPLICATE"
        and bool(row["version_lineage_evidence"])
        for row in version_rows
        ),
        "version_lineage_note": (
            "Version lineage requires explicit reviewer evidence; similarity and "
            "publication dates alone are not sufficient."
        ),
    }

    outputs = [
        (CALIBRATION_REPORT, json.dumps(calibration, ensure_ascii=False, indent=2) + "\n"),
        (CALIBRATION_FEEDBACK, feedback),
        (P406_VALIDATION_REPORT, json.dumps(p406_validation, ensure_ascii=False, indent=2) + "\n"),
        (P406_AGREEMENT, json.dumps(p406_agreement, ensure_ascii=False, indent=2) + "\n"),
        (DUPLICATE_VALIDATION, json.dumps(duplicate_validation, ensure_ascii=False, indent=2) + "\n"),
        (DUPLICATE_AGREEMENT, json.dumps(duplicate_agreement, ensure_ascii=False, indent=2) + "\n"),
    ]
    outputs.extend(
        (
            path,
            json.dumps(
                calibration_reviewer_reports[reviewer],
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )
        for reviewer, path in CALIBRATION_REVIEWER_REPORTS.items()
    )
    for path, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w" if overwrite_reports else "x", encoding="utf-8") as stream:
            stream.write(content)
    _write_csv(
        P406_MISSING,
        ("reviewer", "article_id", "annotation_status", "missing_or_invalid_fields"),
        missing_rows,
        overwrite=overwrite_reports,
    )
    _write_csv(P406_QUEUE, P406_QUEUE_COLUMNS, p406_queue, overwrite=overwrite_reports)
    _write_csv(
        DUPLICATE_QUEUE,
        DUPLICATE_QUEUE_COLUMNS,
        duplicate_queue,
        overwrite=overwrite_reports,
    )
    _write_csv(
        VERSION_REVIEW,
        VERSION_REVIEW_COLUMNS,
        version_rows,
        overwrite=overwrite_reports,
    )
    return {
        "calibration_status": calibration["status"],
        "p406_status": p406_validation["status"],
        "p406_agreement_status": p406_agreement["status"],
        "duplicate_status": duplicate_validation["status"],
        "duplicate_agreement_status": duplicate_agreement["status"],
    }


def _write_csv(
    path: Path,
    columns: tuple[str, ...],
    rows: list[dict[str, str]],
    overwrite: bool = False,
) -> None:
    with path.open("w" if overwrite else "x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite-reports",
        action="store_true",
        help="Refresh only validator-generated reports and queues, never reviewer inputs.",
    )
    args = parser.parse_args(argv)
    try:
        statuses = validate_all(overwrite_reports=args.overwrite_reports)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"P4 human-review validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(statuses, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
