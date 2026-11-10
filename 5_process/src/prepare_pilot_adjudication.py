"""Prepare and validate the separate, non-gold Pilot 10 adjudication form."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROCESS = Path(__file__).resolve().parents[1]
PILOT_DIR = PROCESS / "data" / "interim" / "pilot_10"
REPORTS = PROCESS / "reports"
QUEUE = REPORTS / "pilot_10_adjudication_queue.csv"
FORM = PROCESS / "data" / "interim" / "pilot_10_adjudication_form.csv"
REPORT = REPORTS / "pilot_10_adjudication_validation_report.json"
FORM_COLUMNS = (
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
FINAL_FIELDS = (
    "final_relevance",
    "final_topic",
    "adjudication_reason",
    "adjudicator_id",
    "adjudication_date",
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


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"{path}: missing CSV header")
        return list(reader.fieldnames), list(reader)


def _write_form(rows: list[dict[str, str]], overwrite: bool = False) -> None:
    FORM.parent.mkdir(parents=True, exist_ok=True)
    with FORM.open("w" if overwrite else "x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FORM_COLUMNS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        return False


def _topic_code(value: str) -> str:
    for code, name in TOPIC_NAMES.items():
        if value.strip() in {f"{code} — {name}", f"{code} - {name}", f"{code}: {name}"}:
            return code
    return ""


def prepare_form(refresh_empty: bool = False) -> dict[str, int]:
    queue_columns, queue_rows = _read_csv(QUEUE)
    if tuple(queue_columns) != FORM_COLUMNS:
        raise ValueError(f"{QUEUE}: schema does not match the Pilot 10 adjudication form.")
    if FORM.exists():
        if not refresh_empty:
            raise FileExistsError(f"Refusing to overwrite {FORM}.")
        existing_columns, existing_rows = _read_csv(FORM)
        if existing_rows:
            raise FileExistsError(
                f"Refusing to refresh {FORM}; it contains adjudicator-entered rows."
            )
        if tuple(existing_columns) != FORM_COLUMNS:
            raise ValueError(f"{FORM}: schema differs from the current Pilot 10 form.")
    _write_form(queue_rows, overwrite=FORM.exists())
    return {"pilot_10_adjudication_cases": len(queue_rows)}


def validate_form() -> dict[str, Any]:
    queue_columns, queue_rows = _read_csv(QUEUE)
    form_columns, form_rows = _read_csv(FORM)
    if tuple(queue_columns) != FORM_COLUMNS or tuple(form_columns) != FORM_COLUMNS:
        raise ValueError("Pilot 10 adjudication form/queue schema mismatch.")
    queue_by_id: dict[str, dict[str, str]] = {}
    for row in queue_rows:
        article_id = row["article_id"].strip()
        if not article_id or article_id in queue_by_id:
            raise ValueError(f"Pilot 10 queue has a blank or duplicate article_id: {article_id!r}")
        queue_by_id[article_id] = row

    immutable = tuple(column for column in FORM_COLUMNS if column not in FINAL_FIELDS and column != "adjudication_status")
    seen: set[str] = set()
    counts = {"PENDING": 0, "ADJUDICATED": 0, "NEEDS_ADJUDICATION": 0}
    for row_number, row in enumerate(form_rows, start=2):
        article_id = row["article_id"].strip()
        if not article_id or article_id in seen:
            raise ValueError(f"Pilot 10 adjudication form row {row_number}: blank or duplicate article_id")
        seen.add(article_id)
        source = queue_by_id.get(article_id)
        if source is None:
            raise ValueError(f"{article_id}: not present in the current Pilot 10 queue")
        for field in immutable:
            if row.get(field, "") != source.get(field, ""):
                raise ValueError(f"{article_id}: immutable reviewer/source field {field!r} changed")

        status = row["adjudication_status"].strip()
        if status not in counts:
            raise ValueError(f"{article_id}: invalid adjudication_status {status!r}")
        values = [row[field].strip() for field in FINAL_FIELDS]
        if status == "PENDING":
            if any(values):
                raise ValueError(f"{article_id}: pending case must have blank final fields")
        elif status == "NEEDS_ADJUDICATION":
            if values[0] or values[1]:
                raise ValueError(f"{article_id}: unresolved case cannot contain final labels")
            if not all(values[2:4]) or not _valid_date(values[4]):
                raise ValueError(f"{article_id}: unresolved case needs reason, adjudicator ID and date")
        else:
            relevance, topic, reason, adjudicator, adjudication_date = values
            if relevance not in RELEVANCE:
                raise ValueError(f"{article_id}: invalid final relevance label")
            code = _topic_code(topic)
            if relevance in {"Relevant", "Borderline"} and not code:
                raise ValueError(f"{article_id}: Relevant/Borderline requires one valid A-L topic")
            if relevance in {"Not relevant", "Uncertain"} and topic:
                raise ValueError(f"{article_id}: Not relevant/Uncertain requires a blank topic")
            if not reason or not adjudicator or not _valid_date(adjudication_date):
                raise ValueError(f"{article_id}: resolved case requires reason, adjudicator ID and date")
        counts[status] += 1

    missing = set(queue_by_id) - seen
    if missing:
        raise ValueError(f"Pilot 10 adjudication form is missing queued cases: {sorted(missing)[:10]}")
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "NO_ADJUDICATION_CASES"
            if not form_rows
            else "WAITING_FOR_ADJUDICATION"
            if counts["PENDING"] or counts["NEEDS_ADJUDICATION"]
            else "VALIDATED"
        ),
        "queue_case_count": len(queue_rows),
        "form_case_count": len(form_rows),
        "status_counts": counts,
        "reviewer_1_sheet_sha256": _sha256(PILOT_DIR / "reviewer_1_sheet.csv"),
        "reviewer_2_sheet_sha256": _sha256(PILOT_DIR / "reviewer_2_sheet.csv"),
        "queue_sha256": _sha256(QUEUE),
        "form_sha256": _sha256(FORM),
        "note": "Pilot 10 adjudication is separate from P4.06 and never creates P4.09 gold.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--refresh-empty-form", action="store_true")
    mode.add_argument("--validate", action="store_true")
    parser.add_argument("--overwrite-report", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.prepare or args.refresh_empty_form:
            result = prepare_form(refresh_empty=args.refresh_empty_form)
        else:
            result = validate_form()
            if REPORT.exists() and not args.overwrite_report:
                raise FileExistsError(f"Refusing to overwrite {REPORT}; use --overwrite-report.")
            REPORT.parent.mkdir(parents=True, exist_ok=True)
            REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Pilot 10 adjudication validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
