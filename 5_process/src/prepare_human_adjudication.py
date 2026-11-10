"""Prepare and validate blank human adjudication forms; optionally build eligible gold."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

PROCESS = Path(__file__).resolve().parents[1]
REPORTS = PROCESS / "reports"
P406_DIR = PROCESS / "relevance_evaluation"
INTERIM = PROCESS / "data" / "interim"
P406_QUEUE = REPORTS / "p406_adjudication_queue.csv"
DUPLICATE_QUEUE = REPORTS / "duplicate_adjudication_queue.csv"
P406_FORM = P406_DIR / "p406_adjudication_form.csv"
DUPLICATE_FORM = INTERIM / "duplicate_adjudication_form.csv"
P406_REVIEWER_1 = P406_DIR / "p406_reviewer_1_sheet.csv"
P406_REVIEWER_2 = P406_DIR / "p406_reviewer_2_sheet.csv"
GOLD_OUTPUT = P406_DIR / "gold_annotations.csv"
GOLD_COLUMNS = (
    "article_id",
    "gold_relevance_status",
    "gold_topic_labels_p406",
    "annotation_status",
    "adjudication_status",
    "annotation_method",
    "reviewer_id",
    "review_date",
    "review_reason",
    "contributing_reviewer_ids",
    "adjudicator_id",
    "adjudication_date",
)
RELEVANCE = {"RELEVANT", "IRRELEVANT", "REVIEW_REQUIRED"}
TOPICS = {
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
ADJUDICATION_VALIDATION_REPORT = REPORTS / "adjudication_validation_report.json"
ADJUDICATION_HISTORY = REPORTS / "adjudication_validation_history.jsonl"
GOLD_BUILD_REPORT = REPORTS / "gold_build_report.json"
GOLD_BUILD_HISTORY = REPORTS / "gold_build_history.jsonl"
P406_ADJUDICATION_STATUSES = {"PENDING", "ADJUDICATED", "NEEDS_ADJUDICATION"}
DUPLICATE_DECISIONS = {
    "CONFIRMED_DUPLICATE",
    "RELATED_BUT_DISTINCT",
    "NOT_DUPLICATE",
    "UNCERTAIN",
}
DUPLICATE_TYPES = {
    "URL_DUPLICATE",
    "EXACT_CONTENT_DUPLICATE",
    "NEAR_DUPLICATE",
    "VERSION_DUPLICATE",
}


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"{path}: missing CSV header")
        return list(reader.fieldnames), list(reader)


def _write_csv_new(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    overwrite: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w" if overwrite else "x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def prepare_forms(refresh_empty: bool = False) -> dict[str, int]:
    targets = (P406_FORM, DUPLICATE_FORM)
    existing = [str(path) for path in targets if path.exists()]
    if existing and not refresh_empty:
        raise FileExistsError("Refusing to overwrite adjudication forms: " + ", ".join(existing))
    p406_columns, p406_rows = _read_csv(P406_QUEUE)
    duplicate_columns, duplicate_rows = _read_csv(DUPLICATE_QUEUE)
    if existing:
        if len(existing) != len(targets):
            raise FileExistsError("Both adjudication forms must exist before refreshing empty forms.")
        for path in targets:
            columns, rows = _read_csv(path)
            if rows:
                raise FileExistsError(
                    f"Refusing to refresh {path}; it contains human-entered adjudication data."
                )
            expected_columns = p406_columns if path == P406_FORM else duplicate_columns
            if columns != expected_columns:
                raise ValueError(f"{path}: existing form schema differs from current queue.")
    _write_csv_new(P406_FORM, p406_columns, p406_rows, overwrite=bool(existing))
    _write_csv_new(
        DUPLICATE_FORM,
        duplicate_columns,
        duplicate_rows,
        overwrite=bool(existing),
    )
    return {
        "p406_adjudication_cases": len(p406_rows),
        "duplicate_adjudication_cases": len(duplicate_rows),
    }


def _valid_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _gold_build_provenance(gold_file_exists: bool) -> dict[str, Any]:
    sources = {
        "p406_reviewer_1": P406_REVIEWER_1,
        "p406_reviewer_2": P406_REVIEWER_2,
        "p406_queue": P406_QUEUE,
        "p406_adjudication_form": P406_FORM,
        "master_sample": PROCESS / "data" / "interim" / "relevance_review_sample.csv",
        "p406_taxonomy": PROCESS / "config" / "relevance_taxonomy.md",
        "p406_protocol": P406_DIR / "p406_gold_review_protocol.md",
    }
    source_hashes = {
        name: _sha256(path)
        for name, path in sources.items()
        if path.is_file()
    }
    taxonomy_path = sources["p406_taxonomy"]
    taxonomy_version = None
    if taxonomy_path.is_file():
        match = re.search(
            r"^\*\*Taxonomy version:\*\*\s*`([^`]+)`",
            taxonomy_path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        taxonomy_version = match.group(1) if match else None
    return {
        "source_sha256": source_hashes,
        "p406_taxonomy_version": taxonomy_version,
        "gold_file_sha256": _sha256(GOLD_OUTPUT) if gold_file_exists else None,
    }


def _record_gold_build_report(report: dict[str, Any]) -> None:
    GOLD_BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    GOLD_BUILD_REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    existing = (
        GOLD_BUILD_HISTORY.read_text(encoding="utf-8").splitlines()
        if GOLD_BUILD_HISTORY.exists()
        else []
    )
    previous_hashes = []
    for line in existing:
        try:
            previous_hashes.append(json.loads(line).get("source_sha256"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{GOLD_BUILD_HISTORY}: invalid JSONL history entry.") from exc
    if report["provenance"]["source_sha256"] not in previous_hashes:
        with GOLD_BUILD_HISTORY.open("a", encoding="utf-8") as stream:
            stream.write(serialized + "\n")


def _require_queue_membership(
    form_rows: list[dict[str, str]],
    queue_path: Path,
    key_fields: tuple[str, ...],
    immutable_fields: tuple[str, ...],
    form_name: str,
) -> None:
    _, queue_rows = _read_csv(queue_path)
    queue_index: dict[tuple[str, ...], dict[str, str]] = {}
    for row in queue_rows:
        key = tuple(row[field].strip() for field in key_fields)
        if key in queue_index:
            raise ValueError(f"{queue_path}: duplicate adjudication case {key}")
        queue_index[key] = row
    seen: set[tuple[str, ...]] = set()
    for row_number, row in enumerate(form_rows, start=2):
        key = tuple(row[field].strip() for field in key_fields)
        if key not in queue_index:
            raise ValueError(
                f"{form_name} row {row_number}: case {key} is not present in the "
                "current adjudication queue."
            )
        if key in seen:
            raise ValueError(f"{form_name}: duplicate adjudication case {key}")
        seen.add(key)
        queued = queue_index[key]
        for field in immutable_fields:
            if row.get(field, "") != queued.get(field, ""):
                raise ValueError(
                    f"{form_name} row {row_number}: source field {field!r} was changed."
                )
    if seen != set(queue_index):
        missing = sorted(set(queue_index) - seen)
        raise ValueError(f"{form_name}: missing queued cases {missing[:10]}")


def _topics(value: str, where: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{where}: topics must be a JSON array") from exc
    if (
        not isinstance(parsed, list)
        or any(not isinstance(topic, str) for topic in parsed)
        or len(parsed) != len(set(parsed))
        or set(parsed) - TOPICS
    ):
        raise ValueError(f"{where}: topic labels are invalid for P4.06")
    return parsed


def validate_forms() -> dict[str, Any]:
    p406_columns, p406_rows = _read_csv(P406_FORM)
    duplicate_columns, duplicate_rows = _read_csv(DUPLICATE_FORM)
    required_p406 = {
        "article_id",
        "adjudication_status",
        "final_relevance_status",
        "final_topic_labels_p406",
        "adjudication_reason",
        "adjudicator_id",
        "adjudication_date",
    }
    required_duplicate = {
        "group_id",
        "article_id_1",
        "article_id_2",
        "adjudication_status",
        "final_decision",
        "final_relationship_type",
        "version_lineage_evidence",
        "adjudication_reason",
        "adjudicator_id",
        "adjudication_date",
    }
    if required_p406 - set(p406_columns):
        raise ValueError(f"P4.06 adjudication form missing columns {sorted(required_p406-set(p406_columns))}")
    if required_duplicate - set(duplicate_columns):
        raise ValueError(
            "Duplicate adjudication form missing columns "
            f"{sorted(required_duplicate-set(duplicate_columns))}"
        )
    _require_queue_membership(
        p406_rows,
        P406_QUEUE,
        ("article_id",),
        (
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
        ),
        "P4.06 adjudication form",
    )
    _require_queue_membership(
        duplicate_rows,
        DUPLICATE_QUEUE,
        ("article_id_1", "article_id_2"),
        (
            "group_id",
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
        ),
        "Duplicate adjudication form",
    )
    p406_ids: set[str] = set()
    p406_resolved = 0
    p406_pending = 0
    for row_number, row in enumerate(p406_rows, start=2):
        article_id = row["article_id"].strip()
        if not article_id or article_id in p406_ids:
            raise ValueError(f"P4.06 adjudication form row {row_number}: blank or duplicate article_id")
        p406_ids.add(article_id)
        status = row["adjudication_status"].strip()
        if status not in P406_ADJUDICATION_STATUSES:
            raise ValueError(f"{article_id}: invalid adjudication_status {status!r}")
        values = (
            row["final_relevance_status"].strip(),
            row["final_topic_labels_p406"].strip(),
            row["adjudication_reason"].strip(),
            row["adjudicator_id"].strip(),
            row["adjudication_date"].strip(),
        )
        if status == "PENDING":
            if any(values):
                raise ValueError(f"{article_id}: pending adjudication must have blank final fields")
            p406_pending += 1
        elif status == "NEEDS_ADJUDICATION":
            if values[0] or values[1]:
                raise ValueError(f"{article_id}: unresolved adjudication must not have final labels")
            if not all(values[2:4]) or not _valid_date(values[4]):
                raise ValueError(f"{article_id}: unresolved case needs reason, adjudicator and date")
        else:
            relevance, raw_topics, reason, adjudicator, adjudication_date = values
            if relevance not in RELEVANCE:
                raise ValueError(f"{article_id}: invalid final P4.06 relevance")
            topics = _topics(raw_topics, article_id)
            if relevance == "RELEVANT" and not topics:
                raise ValueError(f"{article_id}: RELEVANT requires at least one topic")
            if relevance != "RELEVANT" and topics:
                raise ValueError(f"{article_id}: non-RELEVANT statuses require an empty topic list")
            if not reason or not adjudicator or not _valid_date(adjudication_date):
                raise ValueError(f"{article_id}: resolved case needs reason, adjudicator and date")
            p406_resolved += 1

    pair_keys: set[tuple[str, str]] = set()
    duplicate_resolved = 0
    duplicate_pending = 0
    for row_number, row in enumerate(duplicate_rows, start=2):
        first, second = row["article_id_1"].strip(), row["article_id_2"].strip()
        pair = tuple(sorted((first, second)))
        if not first or not second or first == second or pair in pair_keys:
            raise ValueError(f"Duplicate adjudication form row {row_number}: invalid or duplicate pair")
        pair_keys.add(pair)
        status = row["adjudication_status"].strip()
        decision = row["final_decision"].strip()
        relation = row["final_relationship_type"].strip()
        evidence = row["version_lineage_evidence"].strip()
        reason = row["adjudication_reason"].strip()
        adjudicator = row["adjudicator_id"].strip()
        adjudication_date = row["adjudication_date"].strip()
        if status not in {"PENDING", "ADJUDICATED", "NEEDS_ADJUDICATION"}:
            raise ValueError(f"{pair}: invalid adjudication_status {status!r}")
        if status == "PENDING":
            if any((decision, relation, evidence, reason, adjudicator, adjudication_date)):
                raise ValueError(f"{pair}: pending adjudication must have blank final fields")
            duplicate_pending += 1
        elif status == "NEEDS_ADJUDICATION":
            if decision or relation:
                raise ValueError(f"{pair}: unresolved case must not have a final decision/type")
            if not reason or not adjudicator or not _valid_date(adjudication_date):
                raise ValueError(f"{pair}: unresolved case needs reason, adjudicator and date")
        else:
            if decision not in DUPLICATE_DECISIONS:
                raise ValueError(f"{pair}: invalid final duplicate decision")
            if not reason or not adjudicator or not _valid_date(adjudication_date):
                raise ValueError(f"{pair}: resolved case needs reason, adjudicator and date")
            if decision == "CONFIRMED_DUPLICATE":
                if relation not in DUPLICATE_TYPES:
                    raise ValueError(f"{pair}: confirmed duplicate needs a valid relationship type")
                if relation == "VERSION_DUPLICATE" and not evidence:
                    raise ValueError(f"{pair}: version duplicate needs lineage evidence")
            elif relation or evidence:
                raise ValueError(f"{pair}: non-duplicate decision cannot claim relationship/evidence")
            duplicate_resolved += 1
    return {
        "generated_at_utc": datetime.now().astimezone().isoformat(),
        "p406_case_count": len(p406_rows),
        "p406_resolved_count": p406_resolved,
        "p406_pending_count": p406_pending,
        "duplicate_case_count": len(duplicate_rows),
        "duplicate_resolved_count": duplicate_resolved,
        "duplicate_pending_count": duplicate_pending,
        "source_sha256": {
            "p406_reviewer_1": _sha256(P406_REVIEWER_1),
            "p406_reviewer_2": _sha256(P406_REVIEWER_2),
            "p406_queue": _sha256(P406_QUEUE),
            "p406_form": _sha256(P406_FORM),
            "duplicate_reviewer_1": _sha256(
                INTERIM / "duplicate_review_reviewer_1_sheet.csv"
            ),
            "duplicate_reviewer_2": _sha256(
                INTERIM / "duplicate_review_reviewer_2_sheet.csv"
            ),
            "duplicate_queue": _sha256(DUPLICATE_QUEUE),
            "duplicate_form": _sha256(DUPLICATE_FORM),
        },
    }


def record_validation_history(report: dict[str, Any], overwrite_report: bool = False) -> None:
    report["generated_at_utc"] = datetime.now().astimezone().isoformat()
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if ADJUDICATION_VALIDATION_REPORT.exists() and not overwrite_report:
        raise FileExistsError(
            f"Refusing to overwrite {ADJUDICATION_VALIDATION_REPORT}; "
            "use --overwrite-validation-report."
        )
    ADJUDICATION_VALIDATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    ADJUDICATION_VALIDATION_REPORT.write_text(report_text, encoding="utf-8")

    snapshot = {
        "generated_at_utc": report["generated_at_utc"],
        "source_sha256": report["source_sha256"],
        "p406_case_count": report["p406_case_count"],
        "p406_resolved_count": report["p406_resolved_count"],
        "duplicate_case_count": report["duplicate_case_count"],
        "duplicate_resolved_count": report["duplicate_resolved_count"],
    }
    serialized = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    history_lines = (
        ADJUDICATION_HISTORY.read_text(encoding="utf-8").splitlines()
        if ADJUDICATION_HISTORY.exists()
        else []
    )
    for line in history_lines:
        try:
            previous = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError(f"{ADJUDICATION_HISTORY}: invalid JSONL history entry.")
        if previous.get("source_sha256") == report["source_sha256"]:
            return
    with ADJUDICATION_HISTORY.open("a", encoding="utf-8") as stream:
        stream.write(serialized + "\n")


def _annotation_is_valid(row: dict[str, str]) -> bool:
    if row.get("annotation_status") != "COMPLETED":
        return False
    if row.get("gold_relevance_status") not in RELEVANCE:
        return False
    if not row.get("review_reason", "").strip() or not row.get("reviewer_id", "").strip():
        return False
    if not _valid_date(row.get("review_date", "")):
        return False
    try:
        topics = _topics(row.get("gold_topic_labels_p406", ""), row.get("article_id", ""))
    except ValueError:
        return False
    return bool(topics) if row["gold_relevance_status"] == "RELEVANT" else not topics


def build_gold() -> dict[str, Any]:
    if GOLD_OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {GOLD_OUTPUT}")
    adjudication_report = validate_forms()
    _, first_rows = _read_csv(P406_REVIEWER_1)
    _, second_rows = _read_csv(P406_REVIEWER_2)
    _, master_rows = _read_csv(
        PROCESS / "data" / "interim" / "relevance_review_sample.csv"
    )
    _, adjudication_rows = _read_csv(P406_FORM)
    first = {row["article_id"].strip(): row for row in first_rows}
    second = {row["article_id"].strip(): row for row in second_rows}
    adjudications = {row["article_id"].strip(): row for row in adjudication_rows}
    if len(first) != len(first_rows) or len(second) != len(second_rows):
        raise ValueError("P4.06 reviewer sheets contain duplicate article_id values")
    reviewer_ids_one = {
        row.get("reviewer_id", "").strip()
        for row in first_rows
        if row.get("reviewer_id", "").strip()
    }
    reviewer_ids_two = {
        row.get("reviewer_id", "").strip()
        for row in second_rows
        if row.get("reviewer_id", "").strip()
    }
    if len(reviewer_ids_one) > 1 or len(reviewer_ids_two) > 1:
        raise ValueError("Each P4.06 reviewer sheet must contain at most one reviewer_id.")
    if list(first) != list(second):
        raise ValueError("P4.06 reviewer sheets do not have identical article_id ordering")
    master = {row["article_id"].strip(): row for row in master_rows}
    master_ids = [row["article_id"].strip() for row in master_rows]
    if len(master_ids) != 620 or len(set(master_ids)) != 620:
        raise ValueError("P4.06 master sample must contain 620 unique article IDs")
    if list(first) != master_ids:
        raise ValueError("P4.06 reviewer sheets do not match the master sample IDs/order")
    for article_id in master_ids:
        for reviewer_row in (first[article_id], second[article_id]):
            if (
                reviewer_row.get("title") != master[article_id].get("title")
                or reviewer_row.get("content") != master[article_id].get("content")
            ):
                raise ValueError(f"{article_id}: reviewer sheet title/content differs from master")

    gold_rows: list[dict[str, str]] = []
    excluded_reasons: Counter[str] = Counter()
    for article_id in first:
        one, two = first[article_id], second[article_id]
        if (
            not _annotation_is_valid(one)
            or not _annotation_is_valid(two)
            or one.get("reviewer_id", "").strip() == two.get("reviewer_id", "").strip()
        ):
            excluded_reasons["invalid_incomplete_or_nonindependent_reviews"] += 1
            continue
        topics_one = _topics(one["gold_topic_labels_p406"], article_id)
        topics_two = _topics(two["gold_topic_labels_p406"], article_id)
        agrees = (
            one["gold_relevance_status"] == two["gold_relevance_status"]
            and set(topics_one) == set(topics_two)
        )
        if agrees:
            gold_rows.append(
                {
                    "article_id": article_id,
                    "gold_relevance_status": one["gold_relevance_status"],
                    "gold_topic_labels_p406": json.dumps(sorted(topics_one)),
                    "annotation_status": "COMPLETED",
                    "adjudication_status": "NOT_REQUIRED",
                    "annotation_method": "human",
                    "reviewer_id": f"{one['reviewer_id']}|{two['reviewer_id']}",
                    "review_date": max(one["review_date"], two["review_date"]),
                    "review_reason": (
                        f"Reviewer 1: {one['review_reason']} | "
                        f"Reviewer 2: {two['review_reason']}"
                    ),
                    "contributing_reviewer_ids": f"{one['reviewer_id']}|{two['reviewer_id']}",
                    "adjudicator_id": "",
                    "adjudication_date": "",
                }
            )
            continue
        adjudication = adjudications.get(article_id)
        if not adjudication or adjudication["adjudication_status"] != "ADJUDICATED":
            excluded_reasons["unresolved_disagreement"] += 1
            continue
        gold_rows.append(
            {
                "article_id": article_id,
                "gold_relevance_status": adjudication["final_relevance_status"],
                "gold_topic_labels_p406": json.dumps(
                    sorted(_topics(adjudication["final_topic_labels_p406"], article_id))
                ),
                "annotation_status": "COMPLETED",
                "adjudication_status": "ADJUDICATED",
                "annotation_method": "human_adjudicated",
                "reviewer_id": f"{one['reviewer_id']}|{two['reviewer_id']}",
                "review_date": max(one["review_date"], two["review_date"]),
                "review_reason": adjudication["adjudication_reason"],
                "contributing_reviewer_ids": f"{one['reviewer_id']}|{two['reviewer_id']}",
                "adjudicator_id": adjudication["adjudicator_id"],
                "adjudication_date": adjudication["adjudication_date"],
            }
        )
    result = {
        "status": "GOLD_READY_FOR_P4_09_VALIDATION" if gold_rows else "WAITING_FOR_GOLD_LABELS",
        "eligible_gold_count": len(gold_rows),
        "records_excluded_or_unresolved": sum(excluded_reasons.values()),
        "excluded_reason_counts": dict(sorted(excluded_reasons.items())),
        "gold_file_created": bool(gold_rows),
        "adjudication_forms": adjudication_report,
        "provenance": _gold_build_provenance(False),
    }
    if not gold_rows:
        _record_gold_build_report(result)
        return result
    _write_csv_new(GOLD_OUTPUT, list(GOLD_COLUMNS), gold_rows)
    result["provenance"] = _gold_build_provenance(gold_file_exists=True)
    _record_gold_build_report(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare", action="store_true", help="Create blank adjudication forms.")
    mode.add_argument(
        "--refresh-empty-forms",
        action="store_true",
        help="Refresh forms only if both exist and contain no human-entered rows.",
    )
    mode.add_argument("--validate", action="store_true", help="Validate completed adjudication forms.")
    mode.add_argument("--build-gold", action="store_true", help="Build only resolved P4.06 human gold.")
    parser.add_argument(
        "--overwrite-validation-report",
        action="store_true",
        help="Replace the latest validation snapshot; the JSONL history remains append-only.",
    )
    args = parser.parse_args(argv)
    try:
        result = (
            prepare_forms()
            if args.prepare
            else prepare_forms(refresh_empty=True)
            if args.refresh_empty_forms
            else validate_forms()
            if args.validate
            else build_gold()
        )
        if args.validate:
            record_validation_history(
                result,
                overwrite_report=args.overwrite_validation_report,
            )
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Human adjudication workflow failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
