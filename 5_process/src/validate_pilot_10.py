"""Validate the independent A-L manual-label Pilot 10 submissions."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROCESS = Path(__file__).resolve().parents[1]
PILOT_DIR = PROCESS / "data" / "interim" / "pilot_10"
REPORTS = PROCESS / "reports"
MASTER = PILOT_DIR / "pilot_10_articles.csv"
REVIEWER_FILES = {
    "reviewer_1": PILOT_DIR / "reviewer_1_sheet.csv",
    "reviewer_2": PILOT_DIR / "reviewer_2_sheet.csv",
}
VALIDATION_REPORT = REPORTS / "pilot_10_validation_report.json"
AGREEMENT_REPORT = REPORTS / "pilot_10_agreement_report.json"
ADJUDICATION_QUEUE = REPORTS / "pilot_10_adjudication_queue.csv"

REVIEW_COLUMNS = (
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
RELEVANCE = {"Relevant", "Borderline", "Not relevant", "Uncertain"}
TOPIC_NAMES = {
    "A": "Thị trường lao động Việt Nam",
    "B": "Thất nghiệp, mất việc, cắt giảm nhân sự",
    "C": "Tiền lương, bảo hiểm, quyền lợi",
    "D": "Hợp đồng lao động, nghỉ việc, sa thải",
    "E": "Điều kiện làm việc, an toàn lao động",
    "F": "Công đoàn, đình công, tranh chấp lao động",
    "G": "Nhóm lao động dễ bị ảnh hưởng",
    "H": "Chính sách việc làm, đào tạo nghề, an sinh xã hội",
    "I": "Lừa đảo tuyển dụng, bóc lột lao động",
    "J": "Kinh tế và yếu tố tác động đến việc làm",
    "K": "Pháp luật lao động và thực thi",
    "L": "Tâm lý người lao động, chất lượng việc làm",
}
REVIEW_STATES = {"PENDING", "IN_PROGRESS", "COMPLETED", "NEEDS_ADJUDICATION"}
QUEUE_COLUMNS = (
    "article_id",
    "title",
    "reviewer_1_relevance",
    "reviewer_1_topic",
    "reviewer_1_reason",
    "reviewer_1_id",
    "reviewer_1_date",
    "reviewer_2_relevance",
    "reviewer_2_topic",
    "reviewer_2_reason",
    "reviewer_2_id",
    "reviewer_2_date",
    "disagreement_type",
    "adjudication_status",
    "final_relevance",
    "final_topic",
    "adjudication_reason",
    "adjudicator_id",
    "adjudication_date",
)


def _read_csv(
    path: Path,
    required_columns: tuple[str, ...] = REVIEW_COLUMNS,
) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"{path}: missing CSV header")
        missing = sorted(set(required_columns) - set(reader.fieldnames))
        if missing:
            raise ValueError(f"{path}: missing columns {missing}")
        return list(reader)


def _write_csv(
    path: Path,
    rows: list[dict[str, str]],
    overwrite: bool = False,
) -> None:
    with path.open("w" if overwrite else "x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=QUEUE_COLUMNS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _valid_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        return False


def _topic_code(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        return ""
    for code, topic_name in TOPIC_NAMES.items():
        if candidate in {
            f"{code} — {topic_name}",
            f"{code} - {topic_name}",
            f"{code}: {topic_name}",
        }:
            return code
    return ""


def _validate_reviewer_sheet(
    path: Path, master_rows: list[dict[str, str]]
) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    rows = _read_csv(path)
    master_ids = [row["article_id"].strip() for row in master_rows]
    master_index = {row["article_id"].strip(): row for row in master_rows}
    indexed: dict[str, dict[str, str]] = {}
    errors: dict[str, list[str]] = defaultdict(list)
    status_counts: Counter[str] = Counter()
    for row_number, row in enumerate(rows, start=2):
        article_id = row["article_id"].strip()
        if not article_id:
            errors[f"ROW-{row_number}"].append("MISSING_ARTICLE_ID")
            continue
        if article_id in indexed:
            errors[article_id].append("DUPLICATE_ARTICLE_ID")
        indexed[article_id] = row
        status = row["review_status"].strip()
        relevance = row["relevance_manual"].strip()
        topic = row["topic_manual"].strip()
        reason = row["review_reason"].strip()
        reviewer_id = row["reviewer_id"].strip()
        review_date = row["review_date"].strip()
        status_counts[status] += 1
        source = master_index.get(article_id)
        if source is None:
            errors[article_id].append("UNEXPECTED_ARTICLE_ID")
        else:
            for field in ("title", "content"):
                if row[field] != source.get(field, ""):
                    errors[article_id].append(f"CHANGED_{field.upper()}")
        if status not in REVIEW_STATES:
            errors[article_id].append("INVALID_REVIEW_STATUS")
        if status in {"COMPLETED", "NEEDS_ADJUDICATION"}:
            if relevance not in RELEVANCE:
                errors[article_id].append("INVALID_OR_MISSING_RELEVANCE")
            code = _topic_code(topic)
            if topic and not code:
                errors[article_id].append("INVALID_OR_UNRECOGNIZED_A_L_TOPIC")
            if relevance in {"Relevant", "Borderline"} and not code:
                errors[article_id].append("RELEVANT_OR_BORDERLINE_REQUIRES_TOPIC")
            if relevance in {"Not relevant", "Uncertain"} and topic:
                errors[article_id].append("NOT_RELEVANT_OR_UNCERTAIN_REQUIRES_BLANK_TOPIC")
            if not reason:
                errors[article_id].append("MISSING_REVIEW_REASON")
            if not reviewer_id:
                errors[article_id].append("MISSING_REVIEWER_ID")
            if not _valid_date(review_date):
                errors[article_id].append("INVALID_OR_MISSING_REVIEW_DATE")
        elif any((relevance, topic, reason, reviewer_id, review_date)):
            errors[article_id].append("PARTIAL_UNCOMPLETED_REVIEW")

    missing = sorted(set(master_ids) - set(indexed))
    unexpected = sorted(set(indexed) - set(master_ids))
    for article_id in missing:
        errors[article_id].append("MISSING_REVIEWER_ROW")
    for article_id in unexpected:
        if "UNEXPECTED_ARTICLE_ID" not in errors[article_id]:
            errors[article_id].append("UNEXPECTED_ARTICLE_ID")
    if [row["article_id"].strip() for row in rows] != master_ids:
        errors["__ORDER__"].append("ID_ORDER_DIFFERS_FROM_PILOT_MASTER")
    reviewer_ids = {
        row["reviewer_id"].strip()
        for row in rows
        if row.get("reviewer_id", "").strip()
    }
    if len(reviewer_ids) > 1:
        errors["__REVIEWER_ID__"].append("MULTIPLE_REVIEWER_IDS_IN_ONE_SHEET")

    completed_valid = sum(
        row.get("review_status") == "COMPLETED"
        and row["article_id"].strip() not in errors
        and "__REVIEWER_ID__" not in errors
        for row in rows
    )
    pending_count = status_counts["PENDING"]
    return (
        {
            "file": str(path),
            "row_count": len(rows),
            "unique_article_id_count": len(indexed),
            "reviewer_ids": sorted(reviewer_ids),
            "status_counts": dict(status_counts),
            "valid_completed_count": completed_valid,
            "pending_count": pending_count,
            "completion_percent": (
                round(completed_valid * 100 / len(master_rows), 2)
                if master_rows
                else 0.0
            ),
            "missing_article_id_count": len(missing),
            "unexpected_article_id_count": len(unexpected),
            "validation_errors_by_article_id": dict(sorted(errors.items())),
            "validation_error_count": sum(len(items) for items in errors.values()),
        },
        indexed,
    )


def _compare_reviewers(
    one: dict[str, dict[str, str]],
    two: dict[str, dict[str, str]],
    one_report: dict[str, Any],
    two_report: dict[str, Any],
    expected_count: int | None = None,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    comparable = 0
    counts: Counter[str] = Counter()
    queue: list[dict[str, str]] = []
    relevance_agreements = 0
    topic_comparable = 0
    topic_agreements = 0
    errors_one = one_report["validation_errors_by_article_id"]
    errors_two = two_report["validation_errors_by_article_id"]
    for article_id in sorted(set(one) | set(two)):
        first, second = one.get(article_id), two.get(article_id)
        if first is None or second is None:
            counts["MISSING_REVIEWER_ROW"] += 1
            continue
        valid_source_rows = (
            first.get("review_status") in {"COMPLETED", "NEEDS_ADJUDICATION"}
            and second.get("review_status") in {"COMPLETED", "NEEDS_ADJUDICATION"}
            and article_id not in errors_one
            and article_id not in errors_two
            and "__REVIEWER_ID__" not in errors_one
            and "__REVIEWER_ID__" not in errors_two
            and first.get("reviewer_id", "").strip()
            and second.get("reviewer_id", "").strip()
            and first.get("reviewer_id", "").strip()
            != second.get("reviewer_id", "").strip()
        )
        if not valid_source_rows:
            counts["NOT_BOTH_VALID_COMPLETED"] += 1
            continue
        if (
            first.get("review_status") == "NEEDS_ADJUDICATION"
            or second.get("review_status") == "NEEDS_ADJUDICATION"
        ):
            counts["REVIEWER_REQUESTED_ADJUDICATION"] += 1
            kind = "REVIEWER_REQUESTED_ADJUDICATION"
        elif (
            first.get("review_status") != "COMPLETED"
            or second.get("review_status") != "COMPLETED"
        ):
            counts["NOT_BOTH_VALID_COMPLETED"] += 1
            continue
        else:
            comparable += 1
            relevance_diff = first["relevance_manual"].strip() != second["relevance_manual"].strip()
            topic_diff = _topic_code(first["topic_manual"]) != _topic_code(second["topic_manual"])
            relevance_agreements += int(not relevance_diff)
            if (
                first["relevance_manual"] in {"Relevant", "Borderline"}
                and second["relevance_manual"] in {"Relevant", "Borderline"}
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
                    "title": first.get("title", ""),
                    "reviewer_1_relevance": first.get("relevance_manual", ""),
                    "reviewer_1_topic": first.get("topic_manual", ""),
                    "reviewer_1_reason": first.get("review_reason", ""),
                    "reviewer_1_id": first.get("reviewer_id", ""),
                    "reviewer_1_date": first.get("review_date", ""),
                    "reviewer_2_relevance": second.get("relevance_manual", ""),
                    "reviewer_2_topic": second.get("topic_manual", ""),
                    "reviewer_2_reason": second.get("review_reason", ""),
                    "reviewer_2_id": second.get("reviewer_id", ""),
                    "reviewer_2_date": second.get("review_date", ""),
                    "disagreement_type": kind,
                    "adjudication_status": "PENDING",
                    "final_relevance": "",
                    "final_topic": "",
                    "adjudication_reason": "",
                    "adjudicator_id": "",
                    "adjudication_date": "",
                }
            )
    total = expected_count if expected_count is not None else max(len(one), len(two))
    return (
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": (
                "WAITING_FOR_ADJUDICATION"
                if queue
                else "WAITING_FOR_HUMAN_REVIEW"
                if comparable == 0
                else "PILOT_REVIEW_COMPLETE_PENDING_PROJECT_APPROVAL"
            ),
            "pilot_article_count": total,
            "valid_completed_by_both_count": comparable,
            "agreement_count": counts["AGREEMENT"],
            "relevance_disagreement_count": counts["RELEVANCE_DISAGREEMENT"],
            "topic_disagreement_count": counts["TOPIC_DISAGREEMENT"],
            "relevance_and_topic_disagreement_count": counts[
                "RELEVANCE_AND_TOPIC_DISAGREEMENT"
            ],
            "reviewer_requested_adjudication_count": counts[
                "REVIEWER_REQUESTED_ADJUDICATION"
            ],
            "not_comparable_or_missing_count": total - comparable,
            "adjudication_queue_count": len(queue),
            "agreement_metrics": {
                "relevance": {
                    "agreement_count": relevance_agreements,
                    "comparable_count": comparable,
                    "raw_agreement": (
                        round(relevance_agreements / comparable, 4)
                        if comparable
                        else None
                    ),
                },
                "topics_among_both_relevant_or_borderline": {
                    "agreement_count": topic_agreements,
                    "comparable_count": topic_comparable,
                    "raw_agreement": (
                        round(topic_agreements / topic_comparable, 4)
                        if topic_comparable
                        else None
                    ),
                },
            },
            "gold_eligible_count": 0,
            "note": (
                "Pilot 10 uses the manual A-L taxonomy, is purposive and not "
                "statistically representative, and is never imported into P4.06 gold. "
                "Project approval is required after review."
            ),
        },
        queue,
    )


def validate(overwrite_reports: bool = False) -> dict[str, Any]:
    targets = (VALIDATION_REPORT, AGREEMENT_REPORT, ADJUDICATION_QUEUE)
    if not overwrite_reports and any(path.exists() for path in targets):
        raise FileExistsError(
            "Pilot reports already exist; use --overwrite-reports to refresh generated outputs."
        )
    master_rows = _read_csv(MASTER, ("article_id", "title", "content"))
    expected_ids = [row["article_id"].strip() for row in master_rows]
    if len(expected_ids) != 10 or len(set(expected_ids)) != 10:
        raise ValueError("Pilot master must contain exactly 10 unique article IDs.")
    reports: dict[str, Any] = {}
    indexed: dict[str, dict[str, dict[str, str]]] = {}
    for reviewer, path in REVIEWER_FILES.items():
        reports[reviewer], indexed[reviewer] = _validate_reviewer_sheet(path, master_rows)
    agreement, queue = _compare_reviewers(
        indexed["reviewer_1"],
        indexed["reviewer_2"],
        reports["reviewer_1"],
        reports["reviewer_2"],
        expected_count=len(master_rows),
    )
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": agreement["status"],
        "sample_size": len(master_rows),
        "sample_design": "purposive; not statistically representative",
        "taxonomy": "official manual A-L labeling guideline; not P4.06 taxonomy",
        "reviewers": reports,
        "gold_eligible_count": 0,
        "note": (
            "Pilot labels are not P4.06 gold and require project-owner approval "
            "before any broader workflow decision."
        ),
    }
    for path, content in (
        (VALIDATION_REPORT, json.dumps(report, ensure_ascii=False, indent=2) + "\n"),
        (AGREEMENT_REPORT, json.dumps(agreement, ensure_ascii=False, indent=2) + "\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.open("w" if overwrite_reports else "x", encoding="utf-8").write(content)
    _write_csv(ADJUDICATION_QUEUE, queue, overwrite=overwrite_reports)
    return {
        "status": report["status"],
        "reviewer_1_completed": reports["reviewer_1"]["valid_completed_count"],
        "reviewer_2_completed": reports["reviewer_2"]["valid_completed_count"],
        "adjudication_queue_count": len(queue),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite-reports", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate(args.overwrite_reports), ensure_ascii=False))
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Pilot 10 validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
