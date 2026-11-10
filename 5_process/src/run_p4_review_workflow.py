"""Refresh P4 human-review states and continue only through validated inputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROCESS = Path(__file__).resolve().parents[1]
REPO = PROCESS.parent
SRC = PROCESS / "src"
REPORTS = PROCESS / "reports"
STATUS_REPORT = REPORTS / "p4_review_workflow_status.json"
GOLD = PROCESS / "relevance_evaluation" / "gold_annotations.csv"
REVIEWER_INPUTS = {
    "canonical": REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv",
    "master_620": PROCESS / "data" / "interim" / "relevance_review_sample.csv",
    "batch_01": PROCESS / "data" / "interim" / "relevance_review_batch_01.csv",
    "batch_02": PROCESS / "data" / "interim" / "relevance_review_batch_02.csv",
    "batch_03": PROCESS / "data" / "interim" / "relevance_review_batch_03.csv",
    "pilot_reviewer_1": PROCESS / "data" / "interim" / "pilot_10" / "reviewer_1_sheet.csv",
    "pilot_reviewer_2": PROCESS / "data" / "interim" / "pilot_10" / "reviewer_2_sheet.csv",
    "calibration_reviewer_1": PROCESS / "data" / "interim" / "reviewer_1_calibration_sheet.csv",
    "calibration_reviewer_2": PROCESS / "data" / "interim" / "reviewer_2_calibration_sheet.csv",
    "calibration_lock_manifest": PROCESS / "reports" / "reviewer_calibration_lock.json",
    "p406_reviewer_1": PROCESS / "relevance_evaluation" / "p406_reviewer_1_sheet.csv",
    "p406_reviewer_2": PROCESS / "relevance_evaluation" / "p406_reviewer_2_sheet.csv",
    "duplicate_reviewer_1": PROCESS / "data" / "interim" / "duplicate_review_reviewer_1_sheet.csv",
    "duplicate_reviewer_2": PROCESS / "data" / "interim" / "duplicate_review_reviewer_2_sheet.csv",
    "labeling_guideline": PROCESS / "config" / "labeling_guideline.md",
    "p406_taxonomy": PROCESS / "config" / "relevance_taxonomy.md",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _csv_has_data(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        next(reader, None)
        return next(reader, None) is not None


def _run(name: str, args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    result: dict[str, Any] = {
        "name": name,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "status": "SUCCEEDED" if completed.returncode == 0 else "FAILED",
    }
    if completed.returncode == 0 and completed.stdout.strip():
        try:
            result["result"] = json.loads(completed.stdout.strip().splitlines()[-1])
        except json.JSONDecodeError:
            output = completed.stdout.strip()
            if output.startswith("P4.09 status="):
                result["result"] = {
                    "status": output.split("P4.09 status=", 1)[1].split(";", 1)[0]
                }
            else:
                result["status"] = "FAILED"
                result["stderr"] = "Command did not return valid JSON output."
    return result


def _load_previous_hashes() -> dict[str, str]:
    if not STATUS_REPORT.exists():
        return {}
    try:
        previous = json.loads(STATUS_REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    hashes = previous.get("input_sha256", {})
    return hashes if isinstance(hashes, dict) else {}


def run_workflow() -> dict[str, Any]:
    previous_hashes = _load_previous_hashes()
    hashes_before = {
        name: _sha256(path)
        for name, path in REVIEWER_INPUTS.items()
        if path.is_file()
    }
    steps: list[dict[str, Any]] = []

    def run_step(name: str, args: list[str]) -> bool:
        result = _run(name, args)
        steps.append(result)
        return result["status"] == "SUCCEEDED"

    if not run_step(
        "calibration_p406_duplicate_validation",
        [str(SRC / "validate_p4_human_review.py"), "--overwrite-reports"],
    ):
        return _finish(steps, hashes_before, previous_hashes, "BLOCKED")
    if not run_step(
        "pilot_10_validation",
        [str(SRC / "validate_pilot_10.py"), "--overwrite-reports"],
    ):
        return _finish(steps, hashes_before, previous_hashes, "BLOCKED")

    pilot_form = PROCESS / "data" / "interim" / "pilot_10_adjudication_form.csv"
    if not pilot_form.exists():
        form_args = [str(SRC / "prepare_pilot_adjudication.py"), "--prepare"]
    elif not _csv_has_data(pilot_form):
        form_args = [
            str(SRC / "prepare_pilot_adjudication.py"),
            "--refresh-empty-form",
        ]
    else:
        form_args = []
    if form_args and not run_step("pilot_adjudication_form_refresh", form_args):
        return _finish(steps, hashes_before, previous_hashes, "BLOCKED")

    p406_form = PROCESS / "relevance_evaluation" / "p406_adjudication_form.csv"
    duplicate_form = PROCESS / "data" / "interim" / "duplicate_adjudication_form.csv"
    if not p406_form.exists() and not duplicate_form.exists():
        if not run_step(
            "p406_duplicate_adjudication_form_prepare",
            [str(SRC / "prepare_human_adjudication.py"), "--prepare"],
        ):
            return _finish(steps, hashes_before, previous_hashes, "BLOCKED")
    elif p406_form.exists() and duplicate_form.exists():
        if not _csv_has_data(p406_form) and not _csv_has_data(duplicate_form):
            if not run_step(
                "p406_duplicate_adjudication_empty_form_refresh",
                [
                    str(SRC / "prepare_human_adjudication.py"),
                    "--refresh-empty-forms",
                ],
            ):
                return _finish(steps, hashes_before, previous_hashes, "BLOCKED")

    if not run_step(
        "p406_duplicate_adjudication_validation",
        [
            str(SRC / "prepare_human_adjudication.py"),
            "--validate",
            "--overwrite-validation-report",
        ],
    ):
        return _finish(steps, hashes_before, previous_hashes, "BLOCKED")
    if not run_step(
        "pilot_adjudication_validation",
        [
            str(SRC / "prepare_pilot_adjudication.py"),
            "--validate",
            "--overwrite-report",
        ],
    ):
        return _finish(steps, hashes_before, previous_hashes, "BLOCKED")

    if not GOLD.exists():
        if not run_step(
            "human_gold_eligibility",
            [str(SRC / "prepare_human_adjudication.py"), "--build-gold"],
        ):
            return _finish(steps, hashes_before, previous_hashes, "BLOCKED")
    if not run_step(
        "p409_evaluation",
        [
            str(PROCESS / "relevance_evaluation" / "evaluate.py"),
            "--overwrite-reports",
        ],
    ):
        return _finish(steps, hashes_before, previous_hashes, "BLOCKED")

    evaluation = steps[-1].get("result", {})
    workflow_status = (
        "WAITING_FOR_GOLD_LABELS"
        if evaluation.get("status") == "WAITING_FOR_GOLD_LABELS"
        else "METRICS_COMPLETED"
        if evaluation.get("status") == "COMPLETED"
        else "BLOCKED"
    )
    return _finish(steps, hashes_before, previous_hashes, workflow_status)


def _finish(
    steps: list[dict[str, Any]],
    hashes_before: dict[str, str],
    previous_hashes: dict[str, str],
    status: str,
) -> dict[str, Any]:
    hashes_after = {
        name: _sha256(path)
        for name, path in REVIEWER_INPUTS.items()
        if path.is_file()
    }
    changed_during_run = {
        name: {"before": hashes_before.get(name), "after": hashes_after.get(name)}
        for name in set(hashes_before) | set(hashes_after)
        if hashes_before.get(name) != hashes_after.get(name)
    }
    if changed_during_run:
        status = "BLOCKED"
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "steps": steps,
        "input_sha256": hashes_after,
        "changed_since_previous_run": {
            name: previous_hashes.get(name) != digest
            for name, digest in hashes_after.items()
        },
        "protected_inputs_changed_during_run": changed_during_run,
        "gold_file_exists": GOLD.exists(),
        "gold_file_sha256": _sha256(GOLD) if GOLD.is_file() else None,
        "gold_build_report": (
            json.loads((REPORTS / "gold_build_report.json").read_text(encoding="utf-8"))
            if (REPORTS / "gold_build_report.json").is_file()
            else None
        ),
        "note": (
            "This command refreshes state when run; it does not watch files continuously "
            "and never creates reviewer or adjudicator decisions."
        ),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    STATUS_REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    del argv
    try:
        result = run_workflow()
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"P4 workflow orchestration failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] != "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
