"""Evaluate P4.07/P4.08 candidates against human-confirmed P4.06 labels."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROCESS_DIR = Path(__file__).resolve().parents[1]
REPO = PROCESS_DIR.parent
EVALUATION_DIR = PROCESS_DIR / "relevance_evaluation"
GOLD_DEFAULT = EVALUATION_DIR / "gold_annotations.csv"
RELEVANCE_PREDICTIONS_DEFAULT = PROCESS_DIR / "data" / "interim" / "relevance_results.csv"
TOPIC_PREDICTIONS_DEFAULT = PROCESS_DIR / "topic_classification" / "topic_labels.csv"
P406_TAXONOMY_DEFAULT = PROCESS_DIR / "config" / "relevance_taxonomy.md"
GROUPS_DEFAULT = PROCESS_DIR / "data" / "interim" / "duplicate_groups.csv"
REPORT_JSON_DEFAULT = EVALUATION_DIR / "relevance_report.json"
REPORT_MD_DEFAULT = EVALUATION_DIR / "relevance_report.md"
PROTECTED_OUTPUT_PATHS = (
    REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv",
    EVALUATION_DIR / "gold_annotations.csv",
    EVALUATION_DIR / "p406_reviewer_1_sheet.csv",
    EVALUATION_DIR / "p406_reviewer_2_sheet.csv",
    EVALUATION_DIR / "p406_adjudication_form.csv",
    PROCESS_DIR / "data" / "interim" / "relevance_results.csv",
    PROCESS_DIR / "data" / "interim" / "relevance_review_sample.csv",
    PROCESS_DIR / "data" / "interim" / "relevance_review_batch_01.csv",
    PROCESS_DIR / "data" / "interim" / "relevance_review_batch_02.csv",
    PROCESS_DIR / "data" / "interim" / "relevance_review_batch_03.csv",
    PROCESS_DIR / "data" / "interim" / "pilot_10" / "reviewer_1_sheet.csv",
    PROCESS_DIR / "data" / "interim" / "pilot_10" / "reviewer_2_sheet.csv",
    PROCESS_DIR / "data" / "interim" / "reviewer_1_calibration_sheet.csv",
    PROCESS_DIR / "data" / "interim" / "reviewer_2_calibration_sheet.csv",
    PROCESS_DIR / "data" / "interim" / "duplicate_review_reviewer_1_sheet.csv",
    PROCESS_DIR / "data" / "interim" / "duplicate_review_reviewer_2_sheet.csv",
    PROCESS_DIR / "data" / "interim" / "duplicate_adjudication_form.csv",
    PROCESS_DIR / "data" / "processed" / "manual_label_sample.csv",
    PROCESS_DIR / "data" / "processed" / "legacy_borderline_manual_labels.csv",
    PROCESS_DIR / "config" / "labeling_guideline.md",
    PROCESS_DIR / "config" / "relevance_taxonomy.md",
)

GOLD_REQUIRED_COLUMNS = (
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
RELEVANCE_PREDICTION_COLUMNS = (
    "article_id",
    "relevance_status",
    "classifier_version",
    "taxonomy_version",
)
TOPIC_PREDICTION_COLUMNS = (
    "article_id",
    "relevance_status",
    "topic_labels",
    "classifier_version",
    "taxonomy_version",
)
SPLIT_COLUMNS = ("article_id", "split")
DUPLICATE_GROUP_COLUMNS = ("duplicate_group_id", "article_id")
RELEVANCE_CLASSES = ("RELEVANT", "IRRELEVANT", "REVIEW_REQUIRED")
GOLD_RELEVANCE_STATUSES = (
    *RELEVANCE_CLASSES,
    "BORDERLINE",
    "UNCERTAIN",
)
ANNOTATION_STATUSES = ("PENDING", "IN_PROGRESS", "COMPLETED", "NEEDS_ADJUDICATION")
ADJUDICATION_STATUSES = ("PENDING", "NOT_REQUIRED", "ADJUDICATED", "NEEDS_ADJUDICATION")
HUMAN_ANNOTATION_METHODS = ("human", "human_adjudicated")
TOPIC_LABELS = (
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
)
UNSCORED_GOLD_STATUSES = ("BORDERLINE", "UNCERTAIN")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _taxonomy_metadata(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^\*\*Taxonomy version:\*\*\s*`([^`]+)`", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"{path}: P4.06 taxonomy version is missing.")
    return {
        "name": "P4.06 relevance and topic taxonomy",
        "version": match.group(1),
        "file": str(path),
        "sha256": _sha256_file(path),
    }


def _read_csv(path: Path, required_columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"{path}: CSV must have a header.")
        missing = sorted(set(required_columns) - set(reader.fieldnames))
        if missing:
            raise ValueError(f"{path}: missing required columns: {missing}")
        return list(reader)


def _unique_id(record: dict[str, Any], row_number: int, source_name: str) -> str:
    value = record.get("article_id")
    article_id = value.strip() if isinstance(value, str) else ""
    if not article_id:
        raise ValueError(f"{source_name} row {row_number}: article_id must not be blank.")
    return article_id


def _parse_topic_list(value: Any, source_name: str, article_id: str) -> list[str]:
    if not isinstance(value, str):
        raise ValueError(f"{source_name} {article_id}: topic labels must be a JSON array.")
    try:
        labels = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{source_name} {article_id}: topic labels must be a JSON array."
        ) from exc
    if not isinstance(labels, list) or any(not isinstance(label, str) for label in labels):
        raise ValueError(f"{source_name} {article_id}: topic labels must be a JSON string array.")
    if len(labels) != len(set(labels)):
        raise ValueError(f"{source_name} {article_id}: duplicate topic labels are not allowed.")
    invalid = sorted(set(labels) - set(TOPIC_LABELS))
    if invalid:
        raise ValueError(f"{source_name} {article_id}: invalid P4.06 topic labels: {invalid}")
    return labels


def _validated_index(
    records: list[dict[str, Any]], source_name: str
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row_number, record in enumerate(records, start=2):
        article_id = _unique_id(record, row_number, source_name)
        if article_id in indexed:
            raise ValueError(
                f"{source_name} row {row_number}: duplicate article_id {article_id!r}."
            )
        indexed[article_id] = record
    return indexed


def _prediction_versions(
    records: list[dict[str, Any]], source_name: str
) -> dict[str, list[str]]:
    versions: dict[str, list[str]] = {}
    for field in ("classifier_version", "taxonomy_version"):
        if any(
            not isinstance(record.get(field), str) or not record[field].strip()
            for record in records
        ):
            raise ValueError(f"{source_name}: {field} must be present for every prediction.")
        values = {
            record.get(field, "").strip()
            for record in records
            if isinstance(record.get(field), str) and record[field].strip()
        }
        versions[field] = sorted(values)
    return versions


def _validate_predictions(
    relevance_predictions: list[dict[str, Any]],
    topic_predictions: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    relevance = _validated_index(relevance_predictions, "relevance predictions")
    topics = _validated_index(topic_predictions, "topic predictions")
    _prediction_versions(relevance_predictions, "relevance predictions")
    _prediction_versions(topic_predictions, "topic predictions")
    if set(relevance) != set(topics):
        missing_topics = sorted(set(relevance) - set(topics))
        missing_relevance = sorted(set(topics) - set(relevance))
        raise ValueError(
            "P4.07/P4.08 prediction IDs differ; "
            f"missing P4.08={missing_topics[:10]}, missing P4.07={missing_relevance[:10]}."
        )
    for article_id, row in relevance.items():
        status = row.get("relevance_status")
        if status not in RELEVANCE_CLASSES:
            raise ValueError(
                f"relevance predictions {article_id}: invalid relevance_status {status!r}."
            )
        topic_row = topics[article_id]
        topic_status = topic_row.get("relevance_status")
        if topic_status != status:
            raise ValueError(
                f"P4.07/P4.08 relevance status mismatch for {article_id}: "
                f"{status!r} != {topic_status!r}."
            )
        topic_labels = _parse_topic_list(
            topic_row.get("topic_labels"), "topic predictions", article_id
        )
        if status != "RELEVANT" and topic_labels:
            raise ValueError(
                f"topic predictions {article_id}: non-RELEVANT rows must have no final topics."
            )
    return relevance, topics


def _validate_gold_record(record: dict[str, Any], article_id: str) -> dict[str, Any]:
    annotation_status = record.get("annotation_status", "")
    adjudication_status = record.get("adjudication_status", "")
    method = record.get("annotation_method", "")
    if annotation_status not in ANNOTATION_STATUSES:
        raise ValueError(
            f"gold annotations {article_id}: invalid annotation_status {annotation_status!r}."
        )
    if adjudication_status not in ADJUDICATION_STATUSES:
        raise ValueError(
            f"gold annotations {article_id}: invalid adjudication_status "
            f"{adjudication_status!r}."
        )

    gold_status = record.get("gold_relevance_status", "")
    raw_topics = record.get("gold_topic_labels_p406", "")
    if annotation_status != "COMPLETED" or adjudication_status in {
        "PENDING",
        "NEEDS_ADJUDICATION",
    }:
        if gold_status and gold_status not in GOLD_RELEVANCE_STATUSES:
            raise ValueError(
                f"gold annotations {article_id}: invalid gold_relevance_status {gold_status!r}."
            )
        if raw_topics:
            _parse_topic_list(raw_topics, "gold annotations", article_id)
        return {"eligible": False, "exclusion": "not_completed_or_adjudicated"}

    if method not in HUMAN_ANNOTATION_METHODS:
        raise ValueError(
            f"gold annotations {article_id}: annotation_method must be human or "
            "human_adjudicated."
        )
    contributor_value = record.get("contributing_reviewer_ids")
    if not isinstance(contributor_value, str) or not contributor_value.strip():
        raise ValueError(
            f"gold annotations {article_id}: contributing_reviewer_ids must identify "
            "both independent reviewers."
        )
    contributor_ids = [
        reviewer_id.strip()
        for reviewer_id in contributor_value.split("|")
        if reviewer_id.strip()
    ]
    if len(contributor_ids) < 2 or len(set(contributor_ids)) != len(contributor_ids):
        raise ValueError(
            f"gold annotations {article_id}: at least two distinct contributing "
            "reviewer IDs are required."
        )
    adjudicator_id = record.get("adjudicator_id", "")
    adjudication_date = record.get("adjudication_date", "")
    if adjudication_status == "ADJUDICATED":
        if method != "human_adjudicated":
            raise ValueError(
                f"gold annotations {article_id}: ADJUDICATED requires "
                "annotation_method=human_adjudicated."
            )
        if not isinstance(adjudicator_id, str) or not adjudicator_id.strip():
            raise ValueError(
                f"gold annotations {article_id}: adjudicator_id must not be blank."
            )
        if not isinstance(adjudication_date, str):
            raise ValueError(
                f"gold annotations {article_id}: adjudication_date must be YYYY-MM-DD."
            )
        try:
            parsed_adjudication_date = date.fromisoformat(adjudication_date)
        except ValueError as exc:
            raise ValueError(
                f"gold annotations {article_id}: adjudication_date must be YYYY-MM-DD."
            ) from exc
        if parsed_adjudication_date.isoformat() != adjudication_date:
            raise ValueError(
                f"gold annotations {article_id}: adjudication_date must be YYYY-MM-DD."
            )
    elif adjudication_status == "NOT_REQUIRED":
        if method != "human":
            raise ValueError(
                f"gold annotations {article_id}: NOT_REQUIRED requires "
                "annotation_method=human."
            )
        if adjudicator_id or adjudication_date:
            raise ValueError(
                f"gold annotations {article_id}: non-adjudicated consensus must not "
                "contain adjudicator metadata."
            )
    if gold_status not in GOLD_RELEVANCE_STATUSES:
        raise ValueError(
            f"gold annotations {article_id}: invalid gold_relevance_status {gold_status!r}."
        )
    for field in ("reviewer_id", "review_reason"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"gold annotations {article_id}: {field} must not be blank.")
    review_date = record.get("review_date")
    if not isinstance(review_date, str):
        raise ValueError(f"gold annotations {article_id}: review_date must be YYYY-MM-DD.")
    try:
        parsed_date = date.fromisoformat(review_date)
    except ValueError as exc:
        raise ValueError(
            f"gold annotations {article_id}: review_date must be YYYY-MM-DD."
        ) from exc
    if parsed_date.isoformat() != review_date:
        raise ValueError(
            f"gold annotations {article_id}: review_date must be YYYY-MM-DD."
        )

    topic_labels = _parse_topic_list(
        raw_topics, "gold annotations", article_id
    )
    if gold_status == "RELEVANT" and not topic_labels:
        raise ValueError(
            f"gold annotations {article_id}: RELEVANT requires at least one P4.06 topic."
        )
    if gold_status != "RELEVANT" and topic_labels:
        raise ValueError(
            f"gold annotations {article_id}: non-RELEVANT statuses require an empty topic list."
        )
    return {
        "eligible": True,
        "gold_relevance_status": gold_status,
        "gold_topic_labels_p406": topic_labels,
    }


def _classification_metrics(
    actual: list[str], predicted: list[str], labels: tuple[str, ...]
) -> dict[str, Any]:
    confusion = {
        label: {prediction: 0 for prediction in labels}
        for label in labels
    }
    for actual_label, predicted_label in zip(actual, predicted):
        confusion[actual_label][predicted_label] += 1
    per_class: dict[str, dict[str, float | int]] = {}
    for label in labels:
        true_positive = confusion[label][label]
        false_positive = sum(
            confusion[other][label] for other in labels if other != label
        )
        false_negative = sum(
            confusion[label][other] for other in labels if other != label
        )
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        per_class[label] = {
            "support": sum(confusion[label].values()),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    count = len(actual)
    correct = sum(
        confusion[label][label]
        for label in labels
    )
    return {
        "sample_count": count,
        "accuracy": correct / count if count else None,
        "macro_precision": (
            sum(values["precision"] for values in per_class.values()) / len(labels)
            if labels
            else None
        ),
        "macro_recall": (
            sum(values["recall"] for values in per_class.values()) / len(labels)
            if labels
            else None
        ),
        "macro_f1": (
            sum(values["f1"] for values in per_class.values()) / len(labels)
            if labels
            else None
        ),
        "weighted_precision": (
            sum(values["precision"] * values["support"] for values in per_class.values())
            / count
            if count
            else None
        ),
        "weighted_recall": (
            sum(values["recall"] * values["support"] for values in per_class.values())
            / count
            if count
            else None
        ),
        "weighted_f1": (
            sum(values["f1"] * values["support"] for values in per_class.values())
            / count
            if count
            else None
        ),
        "per_class": per_class,
        "confusion_matrix": confusion,
        "zero_division": 0,
    }


def _multilabel_metrics(
    actual_sets: list[set[str]],
    predicted_sets: list[set[str]],
) -> dict[str, Any]:
    per_label: dict[str, dict[str, float | int]] = {}
    totals = {"tp": 0, "fp": 0, "fn": 0}
    for label in TOPIC_LABELS:
        tp = sum(label in actual and label in predicted for actual, predicted in zip(actual_sets, predicted_sets))
        fp = sum(label not in actual and label in predicted for actual, predicted in zip(actual_sets, predicted_sets))
        fn = sum(label in actual and label not in predicted for actual, predicted in zip(actual_sets, predicted_sets))
        totals["tp"] += tp
        totals["fp"] += fp
        totals["fn"] += fn
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label[label] = {
            "support": tp + fn,
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    micro_precision = (
        totals["tp"] / (totals["tp"] + totals["fp"])
        if totals["tp"] + totals["fp"]
        else 0.0
    )
    micro_recall = (
        totals["tp"] / (totals["tp"] + totals["fn"])
        if totals["tp"] + totals["fn"]
        else 0.0
    )
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if micro_precision + micro_recall
        else 0.0
    )
    jaccard_values = []
    hamming_errors = 0
    for actual, predicted in zip(actual_sets, predicted_sets):
        union = actual | predicted
        jaccard_values.append(len(actual & predicted) / len(union) if union else 1.0)
        hamming_errors += len(actual ^ predicted)
    sample_count = len(actual_sets)
    subset_accuracy = (
        sum(actual == predicted for actual, predicted in zip(actual_sets, predicted_sets))
        / sample_count
        if sample_count
        else None
    )
    total_support = sum(item["support"] for item in per_label.values())
    return {
        "sample_count": sample_count,
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "macro_precision": (
            sum(item["precision"] for item in per_label.values()) / len(TOPIC_LABELS)
        ),
        "macro_recall": (
            sum(item["recall"] for item in per_label.values()) / len(TOPIC_LABELS)
        ),
        "macro_f1": sum(item["f1"] for item in per_label.values()) / len(TOPIC_LABELS),
        "weighted_f1": (
            sum(item["f1"] * item["support"] for item in per_label.values())
            / total_support
            if total_support
            else 0.0
        ),
        "subset_accuracy": subset_accuracy,
        "hamming_loss": (
            hamming_errors / (sample_count * len(TOPIC_LABELS))
            if sample_count
            else None
        ),
        "mean_jaccard_score": (
            sum(jaccard_values) / sample_count if sample_count else None
        ),
        "per_label": per_label,
        "zero_division": 0,
    }


def _topic_report(report: dict[str, Any]) -> dict[str, Any]:
    topic_metrics = report.get("multilabel_topic_metrics")
    topic_status = report.get("status")
    topic_suppression_reason = report.get("metrics_suppressed_reason")
    if topic_metrics is None and topic_status == "COMPLETED":
        topic_status = "WAITING_FOR_GOLD_LABELS"
        topic_suppression_reason = (
            "No resolved RELEVANT P4.06 gold rows are available for multi-label topic scoring."
        )
    return {
        "generated_at_utc": report.get("generated_at_utc"),
        "status": topic_status,
        "evaluation_method": report.get("evaluation_method"),
        "gold_annotation_count": report.get("gold_annotation_count", 0),
        "completed_human_gold_count": report.get(
            "completed_adjudicated_or_not_required_count", 0
        ),
        "topic_metric_sample_count": report.get("topic_metric_sample_count", 0),
        "gold_source": report.get("inputs", {}).get("gold_file"),
        "gold_source_sha256": report.get("inputs", {}).get("gold_file_sha256"),
        "gold_taxonomy": report.get("gold_taxonomy"),
        "classifier": report.get("prediction_metadata", {}).get("topics"),
        "prediction_count": report.get("prediction_sample_counts", {}).get("topics", 0),
        "scope_and_limitations": (
            "The 620-article human-review sample is stratified by P4.07 predicted "
            "status and is not representative of the natural corpus distribution. "
            "Topic scores describe only eligible human-labeled RELEVANT records."
        ),
        "metrics": topic_metrics,
        "metrics_suppressed_reason": topic_suppression_reason,
        "duplicate_group_leakage_check": report.get("duplicate_group_leakage_check"),
    }


def _group_leakage(
    split_records: list[dict[str, Any]],
    duplicate_group_records: list[dict[str, Any]],
) -> dict[str, Any]:
    splits: dict[str, str] = {}
    for row_number, record in enumerate(split_records, start=2):
        article_id = _unique_id(record, row_number, "split file")
        if article_id in splits:
            raise ValueError(f"split file row {row_number}: duplicate article_id {article_id!r}.")
        split = record.get("split")
        if not isinstance(split, str) or not split.strip():
            raise ValueError(f"split file row {row_number}: split must not be blank.")
        splits[article_id] = split.strip()

    groups: dict[str, set[str]] = {}
    seen_members: set[tuple[str, str]] = set()
    missing_split_members: set[str] = set()
    for row_number, record in enumerate(duplicate_group_records, start=2):
        group_id = record.get("duplicate_group_id")
        if not isinstance(group_id, str) or not group_id.strip():
            raise ValueError(
                f"duplicate groups row {row_number}: duplicate_group_id must not be blank."
            )
        article_id = _unique_id(record, row_number, "duplicate groups")
        pair = (group_id.strip(), article_id)
        if pair in seen_members:
            raise ValueError(
                f"duplicate groups row {row_number}: repeated group member {pair!r}."
            )
        seen_members.add(pair)
        groups.setdefault(group_id.strip(), set()).add(article_id)
        if article_id not in splits:
            missing_split_members.add(article_id)

    cross_split_groups = {}
    for group_id, article_ids in groups.items():
        present_splits = {splits[article_id] for article_id in article_ids if article_id in splits}
        if len(present_splits) > 1:
            cross_split_groups[group_id] = sorted(
                (article_id, splits[article_id])
                for article_id in article_ids
                if article_id in splits
            )

    if missing_split_members:
        status = "INCOMPLETE_SPLIT_COVERAGE"
    elif cross_split_groups:
        status = "BLOCKED_LEAKAGE"
    else:
        status = "PASS"
    return {
        "status": status,
        "group_count": len(groups),
        "cross_split_group_count": len(cross_split_groups),
        "cross_split_groups": cross_split_groups,
        "missing_split_member_count": len(missing_split_members),
        "missing_split_member_ids": sorted(missing_split_members),
        "split_value_count": len(set(splits.values())),
    }


def evaluate_records(
    gold_records: list[dict[str, Any]],
    relevance_prediction_records: list[dict[str, Any]],
    topic_prediction_records: list[dict[str, Any]],
    split_records: list[dict[str, Any]] | None = None,
    duplicate_group_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    relevance_predictions, topic_predictions = _validate_predictions(
        relevance_prediction_records, topic_prediction_records
    )
    gold_index = _validated_index(gold_records, "gold annotations")
    completed: dict[str, dict[str, Any]] = {}
    exclusions: Counter[str] = Counter()
    for article_id, record in gold_index.items():
        validated = _validate_gold_record(record, article_id)
        if not validated["eligible"]:
            exclusions[validated["exclusion"]] += 1
            continue
        completed[article_id] = validated

    missing_predictions = sorted(set(completed) - set(relevance_predictions))
    if missing_predictions:
        raise ValueError(
            f"Completed gold annotations are missing predictions for IDs: {missing_predictions[:10]}."
        )

    eligible_for_relevance = [
        article_id
        for article_id, record in completed.items()
        if record["gold_relevance_status"] in RELEVANCE_CLASSES
    ]
    for article_id, record in completed.items():
        if record["gold_relevance_status"] in UNSCORED_GOLD_STATUSES:
            exclusions[f"gold_{record['gold_relevance_status'].lower()}"] += 1

    split_check: dict[str, Any]
    if split_records is None and duplicate_group_records is None:
        split_check = {
            "status": "NOT_APPLICABLE_NO_TRAIN_TEST_SPLIT",
            "group_count": None,
            "cross_split_group_count": None,
            "cross_split_groups": {},
            "missing_split_member_count": None,
            "missing_split_member_ids": [],
            "split_value_count": None,
            "note": "The evaluated rule-based classifiers do not fit a train/test model.",
        }
    elif split_records is None or duplicate_group_records is None:
        raise ValueError("Provide both split records and duplicate-group records, or neither.")
    else:
        split_check = _group_leakage(split_records, duplicate_group_records)

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_method": "comparison_with_completed_human_gold",
        "status": "COMPLETED",
        "gold_annotation_count": len(gold_records),
        "completed_adjudicated_or_not_required_count": len(completed),
        "relevance_metric_sample_count": len(eligible_for_relevance),
        "topic_metric_sample_count": sum(
            record["gold_relevance_status"] == "RELEVANT"
            for record in completed.values()
        ),
        "excluded_record_counts": dict(sorted(exclusions.items())),
        "relevance_metrics": None,
        "multilabel_topic_metrics": None,
        "duplicate_group_leakage_check": split_check,
        "prediction_metadata": {
            "relevance": {
                "method": "rule_based",
                **_prediction_versions(
                    list(relevance_predictions.values()), "relevance predictions"
                ),
            },
            "topics": {
                "method": "p4.07_rule_reuse_with_per_topic_evidence",
                **_prediction_versions(
                    list(topic_predictions.values()), "topic predictions"
                ),
            },
        },
        "prediction_sample_counts": {
            "relevance": len(relevance_predictions),
            "topics": len(topic_predictions),
        },
        "metric_policy": {
            "relevance": (
                "Exact three-class P4.06 comparison among RELEVANT, IRRELEVANT, and "
                "REVIEW_REQUIRED; no status is merged with another."
            ),
            "borderline_uncertain": (
                "BORDERLINE and UNCERTAIN are preserved and counted as excluded; neither "
                "is mapped to RELEVANT, IRRELEVANT, or REVIEW_REQUIRED."
            ),
            "topics": (
                "Multi-label P4.06 sets are compared only for completed, resolved gold "
                "records labelled RELEVANT. A-L manual topics are not converted."
            ),
            "adjudication": (
                "Rows not COMPLETED, PENDING adjudication, or NEEDS_ADJUDICATION are "
                "excluded; only human or human_adjudicated annotation methods are accepted."
            ),
        },
    }

    if split_check["status"] in {"BLOCKED_LEAKAGE", "INCOMPLETE_SPLIT_COVERAGE"}:
        report["status"] = split_check["status"]
        report["metrics_suppressed_reason"] = (
            "Duplicate-group leakage check did not pass; no evaluation metrics are reported."
        )
        return report

    if eligible_for_relevance:
        report["relevance_metrics"] = _classification_metrics(
            [
                completed[article_id]["gold_relevance_status"]
                for article_id in eligible_for_relevance
            ],
            [
                relevance_predictions[article_id]["relevance_status"]
                for article_id in eligible_for_relevance
            ],
            RELEVANCE_CLASSES,
        )

    topic_ids = [
        article_id
        for article_id, record in completed.items()
        if record["gold_relevance_status"] == "RELEVANT"
    ]
    if topic_ids:
        actual_topic_sets = [
            set(completed[article_id]["gold_topic_labels_p406"])
            for article_id in topic_ids
        ]
        predicted_topic_sets = [
            set(
                _parse_topic_list(
                    topic_predictions[article_id]["topic_labels"],
                    "topic predictions",
                    article_id,
                )
            )
            for article_id in topic_ids
        ]
        report["multilabel_topic_metrics"] = _multilabel_metrics(
            actual_topic_sets, predicted_topic_sets
        )

    if not eligible_for_relevance and not topic_ids:
        report["status"] = "WAITING_FOR_GOLD_LABELS"
        report["metrics_suppressed_reason"] = (
            "No completed, resolved human P4.06 relevance labels are available."
        )
    return report


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# P4.09 Relevance and Topic Evaluation",
        "",
        f"**Status:** `{report['status']}`",
        "",
        "## Evaluation metadata",
        "",
        f"- Evaluated at (UTC): {report.get('generated_at_utc', 'unknown')}",
        f"- Evaluation method: `{report.get('evaluation_method', 'unknown')}`",
        "",
        "## Data readiness",
        "",
        f"- Gold rows supplied: {report.get('gold_annotation_count', 0)}",
        f"- Prediction sample counts: "
        f"`{json.dumps(report.get('prediction_sample_counts', {}), sort_keys=True)}`",
        f"- Prediction classifiers/methods: "
        f"`{json.dumps(report.get('prediction_metadata', {}), sort_keys=True)}`",
        "- Only completed human or human-adjudicated records are eligible.",
        "- P4.06 statuses and topics are evaluated separately from A–L manual labels.",
        "- `BORDERLINE` and `UNCERTAIN` are never merged into another class.",
        "",
    ]
    if report.get("metrics_suppressed_reason"):
        lines.extend(
            [
                "## Metrics",
                "",
                f"No metrics reported: {report['metrics_suppressed_reason']}",
                "",
            ]
        )
    else:
        relevance = report.get("relevance_metrics")
        if relevance:
            lines.extend(
                [
                    "## Relevance classifier",
                    "",
                    f"- Sample count: {relevance['sample_count']}",
                    f"- Accuracy: {relevance['accuracy']:.6f}",
                    f"- Macro precision: {relevance['macro_precision']:.6f}",
                    f"- Macro recall: {relevance['macro_recall']:.6f}",
                    f"- Macro F1: {relevance['macro_f1']:.6f}",
                    f"- Weighted precision/recall/F1: "
                    f"{relevance['weighted_precision']:.6f} / "
                    f"{relevance['weighted_recall']:.6f} / "
                    f"{relevance['weighted_f1']:.6f}",
                    "- Confusion matrix (rows = human reference, columns = classifier):",
                    "",
                    "```json",
                    json.dumps(relevance["confusion_matrix"], ensure_ascii=False, indent=2),
                    "```",
                    "",
                ]
            )
        topics = report.get("multilabel_topic_metrics")
        if topics:
            lines.extend(
                [
                    "## Multi-label topic classifier",
                    "",
                    f"- Sample count: {topics['sample_count']}",
                    f"- Micro precision/recall/F1: {topics['micro_precision']:.6f} / "
                    f"{topics['micro_recall']:.6f} / {topics['micro_f1']:.6f}",
                    f"- Macro precision/recall/F1: {topics['macro_precision']:.6f} / "
                    f"{topics['macro_recall']:.6f} / {topics['macro_f1']:.6f}",
                    f"- Weighted F1: {topics['weighted_f1']:.6f}",
                    f"- Subset accuracy: {topics['subset_accuracy']:.6f}",
                    f"- Hamming loss: {topics['hamming_loss']:.6f}",
                    f"- Mean Jaccard score: {topics['mean_jaccard_score']:.6f}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Exclusions and limitations",
            "",
            "```json",
            json.dumps(report.get("excluded_record_counts", {}), ensure_ascii=False, indent=2),
            "```",
            "",
            "Metrics are valid only for the supplied resolved human gold subset. They do not "
            "represent corpus-wide performance without an appropriate sampling design.",
            "",
        ]
    )
    return "\n".join(lines)


def run_evaluation(
    gold_path: Path = GOLD_DEFAULT,
    relevance_predictions_path: Path = RELEVANCE_PREDICTIONS_DEFAULT,
    topic_predictions_path: Path = TOPIC_PREDICTIONS_DEFAULT,
    report_json_path: Path = REPORT_JSON_DEFAULT,
    report_md_path: Path = REPORT_MD_DEFAULT,
    split_path: Path | None = None,
    duplicate_groups_path: Path | None = None,
    overwrite_reports: bool = False,
    topic_report_json_path: Path | None = None,
) -> dict[str, Any]:
    if topic_report_json_path is None:
        topic_report_json_path = report_json_path.with_name("topic_report.json")
    input_paths = [
        relevance_predictions_path.resolve(),
        topic_predictions_path.resolve(),
    ]
    if gold_path.exists():
        input_paths.append(gold_path.resolve())
    if split_path is not None:
        input_paths.append(split_path.resolve())
    if duplicate_groups_path is not None:
        input_paths.append(duplicate_groups_path.resolve())
    report_json_resolved = report_json_path.resolve()
    report_md_resolved = report_md_path.resolve()
    topic_report_resolved = topic_report_json_path.resolve()
    report_paths = (report_json_resolved, report_md_resolved, topic_report_resolved)
    if any(path in input_paths for path in report_paths) or gold_path.resolve() in report_paths:
        raise ValueError("Evaluation reports must not overwrite an input file.")
    protected = {path.resolve() for path in PROTECTED_OUTPUT_PATHS}
    if any(path in protected for path in report_paths):
        raise ValueError("Evaluation reports must not overwrite protected source or review data.")
    if len(set(report_paths)) != len(report_paths):
        raise ValueError("Evaluation report paths must be different.")
    if not overwrite_reports and any(path.exists() for path in (
        report_json_path,
        report_md_path,
        topic_report_json_path,
    )):
        raise FileExistsError("Evaluation report already exists; refusing to overwrite it.")

    relevance_predictions = _read_csv(
        relevance_predictions_path, RELEVANCE_PREDICTION_COLUMNS
    )
    topic_predictions = _read_csv(
        topic_predictions_path, TOPIC_PREDICTION_COLUMNS
    )
    relevance_index, _ = _validate_predictions(
        relevance_predictions, topic_predictions
    )

    if gold_path.exists():
        gold_records = _read_csv(gold_path, GOLD_REQUIRED_COLUMNS)
        split_records = (
            _read_csv(split_path, SPLIT_COLUMNS) if split_path is not None else None
        )
        duplicate_group_records = (
            _read_csv(duplicate_groups_path, DUPLICATE_GROUP_COLUMNS)
            if duplicate_groups_path is not None
            else None
        )
        report = evaluate_records(
            gold_records,
            relevance_predictions,
            topic_predictions,
            split_records=split_records,
            duplicate_group_records=duplicate_group_records,
        )
    else:
        if split_path is not None or duplicate_groups_path is not None:
            if split_path is None or duplicate_groups_path is None:
                raise ValueError(
                    "Provide both --splits and --duplicate-groups, or neither."
                )
            split_records = _read_csv(split_path, SPLIT_COLUMNS)
            duplicate_group_records = _read_csv(
                duplicate_groups_path, DUPLICATE_GROUP_COLUMNS
            )
            leakage = _group_leakage(split_records, duplicate_group_records)
        else:
            leakage = {
                "status": "NOT_APPLICABLE_NO_TRAIN_TEST_SPLIT",
                "group_count": None,
                "cross_split_group_count": None,
                "cross_split_groups": {},
                "missing_split_member_count": None,
                "missing_split_member_ids": [],
                "split_value_count": None,
                "note": "The evaluated rule-based classifiers do not fit a train/test model.",
            }
        report = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "evaluation_method": "comparison_with_completed_human_gold",
            "status": "WAITING_FOR_GOLD_LABELS",
            "gold_annotation_count": 0,
            "completed_adjudicated_or_not_required_count": 0,
            "relevance_metric_sample_count": 0,
            "topic_metric_sample_count": 0,
            "excluded_record_counts": {},
            "relevance_metrics": None,
            "multilabel_topic_metrics": None,
            "duplicate_group_leakage_check": leakage,
            "prediction_metadata": {
                "relevance": {
                    "method": "rule_based",
                    **_prediction_versions(
                        relevance_predictions, "relevance predictions"
                    ),
                },
                "topics": {
                    "method": "p4.07_rule_reuse_with_per_topic_evidence",
                    **_prediction_versions(topic_predictions, "topic predictions"),
                },
            },
            "prediction_sample_counts": {
                "relevance": len(relevance_index),
                "topics": len(topic_predictions),
            },
            "metrics_suppressed_reason": (
                "Gold annotation file is absent. No accuracy, precision, recall, F1, "
                "confusion matrix, or multi-label score was calculated."
            ),
        }

    report["inputs"] = {
        "gold_file": str(gold_path),
        "gold_file_exists": gold_path.exists(),
        "relevance_predictions_file": str(relevance_predictions_path),
        "relevance_predictions_sha256": _sha256_file(relevance_predictions_path),
        "relevance_prediction_count": len(relevance_index),
        "topic_predictions_file": str(topic_predictions_path),
        "topic_predictions_sha256": _sha256_file(topic_predictions_path),
        "topic_prediction_count": len(topic_predictions),
        "gold_file_sha256": _sha256_file(gold_path) if gold_path.exists() else None,
        "p406_taxonomy_file": str(P406_TAXONOMY_DEFAULT),
        "p406_taxonomy_sha256": _sha256_file(P406_TAXONOMY_DEFAULT),
        "split_file": str(split_path) if split_path is not None else None,
        "duplicate_groups_file": (
            str(duplicate_groups_path) if duplicate_groups_path is not None else None
        ),
    }
    report["gold_taxonomy"] = _taxonomy_metadata(P406_TAXONOMY_DEFAULT)

    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    report_mode = "w" if overwrite_reports else "x"
    with report_json_path.open(report_mode, encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    with report_md_path.open(report_mode, encoding="utf-8") as stream:
        stream.write(_markdown_report(report))
    with topic_report_json_path.open(report_mode, encoding="utf-8") as stream:
        json.dump(_topic_report(report), stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=GOLD_DEFAULT)
    parser.add_argument(
        "--relevance-predictions",
        type=Path,
        default=RELEVANCE_PREDICTIONS_DEFAULT,
    )
    parser.add_argument(
        "--topic-predictions",
        type=Path,
        default=TOPIC_PREDICTIONS_DEFAULT,
    )
    parser.add_argument("--splits", type=Path)
    parser.add_argument("--duplicate-groups", type=Path)
    parser.add_argument("--report-json", type=Path, default=REPORT_JSON_DEFAULT)
    parser.add_argument("--report-md", type=Path, default=REPORT_MD_DEFAULT)
    parser.add_argument("--topic-report-json", type=Path)
    parser.add_argument(
        "--overwrite-reports",
        action="store_true",
        help="Replace only the selected evaluation JSON/Markdown report files.",
    )
    args = parser.parse_args(argv)
    try:
        report = run_evaluation(
            args.gold,
            args.relevance_predictions,
            args.topic_predictions,
            args.report_json,
            args.report_md,
            args.splits,
            args.duplicate_groups,
            args.overwrite_reports,
            args.topic_report_json,
        )
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"P4.09 evaluation failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"P4.09 status={report['status']}; "
        f"JSON: {args.report_json}; Markdown: {args.report_md}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
