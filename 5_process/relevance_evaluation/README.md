# P4.09 Relevance and Topic Evaluation

The evaluator uses only completed human or human-adjudicated gold annotations. It
does not use `relevant_auto`, P4.07 predictions, AI proposals, calibration scenarios,
or incomplete reviewer rows as gold labels.

## Gold input contract

Provide a separate UTF-8 CSV containing these fields (additional provenance columns
are allowed):

`article_id,gold_relevance_status,gold_topic_labels_p406,annotation_status,adjudication_status,annotation_method,reviewer_id,review_date,review_reason,contributing_reviewer_ids,adjudicator_id,adjudication_date`

- `gold_relevance_status`: `RELEVANT`, `IRRELEVANT`, `REVIEW_REQUIRED`, `BORDERLINE`, or `UNCERTAIN`.
- `gold_topic_labels_p406`: JSON array of zero or more P4.06 labels, for example
  `["WAGES","LABOR_DISPUTE"]`. `RELEVANT` requires at least one topic; all other statuses
  require `[]`.
- `annotation_status`: `PENDING`, `IN_PROGRESS`, `COMPLETED`, or `NEEDS_ADJUDICATION`.
- `adjudication_status`: `PENDING`, `NOT_REQUIRED`, `ADJUDICATED`, or `NEEDS_ADJUDICATION`.
- `annotation_method`: `human` or `human_adjudicated` for eligible completed rows.
- `reviewer_id`, `review_date` (actual `YYYY-MM-DD`), and `review_reason` are required for
  eligible completed rows.
- `contributing_reviewer_ids` must identify at least two distinct reviewers for every
  eligible row. `ADJUDICATED` rows must include the actual `adjudicator_id` and
  `adjudication_date`; `NOT_REQUIRED` consensus rows must not claim adjudicator metadata.

P4.06's `REVIEW_REQUIRED`, legacy manual `BORDERLINE`, and legacy manual `UNCERTAIN` are
not interchangeable. Borderline and Uncertain rows are counted as excluded from the
three-class P4.06 relevance metrics; they are never coerced into another class.
Legacy A-L `topic_manual` values must not be mapped to P4.06 multi-label topics.

Rows that are pending, incomplete, or awaiting adjudication are excluded. Invalid IDs,
duplicate IDs, invalid labels, missing provenance on completed rows, or schema errors
stop evaluation with an explicit error.

## Predictions and metrics

By default, P4.07 results are read from `data/interim/relevance_results.csv`, and P4.08
topic results from `topic_classification/topic_labels.csv`. Both prediction files must
cover the same article IDs. The evaluator writes
`relevance_evaluation/relevance_report.json` and `.md` and refuses to overwrite existing
reports by default. After a later gold submission, rerun with `--overwrite-reports` to
refresh only those two report files; input and reviewer data remain protected.

Relevance metrics: accuracy, macro and support-weighted precision/recall/F1, per-class
scores, and a three-class confusion matrix over the exact statuses `RELEVANT`, `IRRELEVANT`, and
`REVIEW_REQUIRED`. No status is merged. P4.07's review-required output is evaluated as
the explicit abstention class in P4.06.

Multi-label topic metrics: micro/macro and per-label precision/recall/F1, support-weighted
F1, Hamming loss, subset accuracy, and mean per-article Jaccard score. Topic evaluation uses completed resolved gold rows
with `gold_relevance_status=RELEVANT` and their human-authored P4.06 topic sets.

The evaluator writes `relevance_report.json`, `relevance_report.md`, and a separate
`topic_report.json`. Reports record evaluation method/time, classifier/taxonomy versions
and methods, prediction/gold sample counts, exclusions, zero-division policy, input
hashes, and limitations. Metrics are not corpus-wide estimates without an appropriate
sampling design.

## Leakage check

The current rule-based classifiers do not fit a train/test model, so a split check is not
applicable by default. If a data split is used, pass both `--splits` (`article_id,split`)
and `--duplicate-groups` (`duplicate_group_id,article_id`). Evaluation metrics are
suppressed if a duplicate group crosses splits or split coverage is incomplete.

## Run

```powershell
python 5_process/src/validate_p4_human_review.py
python 5_process/src/prepare_human_adjudication.py --prepare
python 5_process/src/prepare_human_adjudication.py --validate
```

The P4 human-review validator reads the calibration, P4.06, and duplicate reviewer
submissions without modifying them. It refuses to overwrite its reports by default;
use `--overwrite-reports` to refresh only those generated reports after submissions
change. It compares calibration submissions with the coordinator-only key only after
both are complete and the coordinator-only `reports/reviewer_calibration_lock.json`
matches both exact sheet hashes; it creates queues without choosing outcomes. The adjudication
command creates separate forms and validates human-entered decisions. If both forms
are still header-only, update them from new queues with
`python 5_process/src/prepare_human_adjudication.py --refresh-empty-forms`; this
refuses to replace a form containing human-entered data. Do not edit reviewer sheets
or adjudication forms with automatic predictions. Calibration feedback is
coordinator-only; do not share answer-key results until both reviewer sheets are
locked and valid.

The separate Pilot 10 A-L adjudication form is prepared and validated without
entering pilot decisions into P4.06 gold:

```powershell
python 5_process/src/prepare_pilot_adjudication.py --prepare
python 5_process/src/prepare_pilot_adjudication.py --validate
```

Use `--refresh-empty-form` only when the form has no rows. The validator rejects
cases outside the current pilot queue, changes to either reviewer opinion, invalid
A-L topics, and missing adjudicator provenance. A refreshed queue does not authorize
an automatic decision.

After reviewer submissions are updated, the coordinator can refresh the workflow in
one guarded pass:

```powershell
python 5_process/src/run_p4_review_workflow.py
```

This reruns calibration/P4.06/duplicate and Pilot 10 validators, safely refreshes
only header-only/empty adjudication forms, validates adjudication, attempts gold
generation only from eligible human records, and runs P4.09. It writes the current
step results and input SHA-256/change detection to
`5_process/reports/p4_review_workflow_status.json`. It is a rerunnable command, not
a background watcher. Any validation failure blocks downstream gold/evaluation;
reviewer sheets are never written by the workflow.

Validate the A-L manual Pilot 10 independently:

```powershell
python 5_process/src/validate_pilot_10.py
```

Its reports and queue are separate from P4.06 gold. Pilot labels remain purposive,
manual-taxonomy evidence pending project-owner approval, and are never converted to
P4.06 multi-label records.

Only after human review is complete and any disagreement is resolved can the gold
builder be run:

```powershell
python 5_process/src/prepare_human_adjudication.py --build-gold
python 5_process/relevance_evaluation/evaluate.py
```

The gold builder includes only valid two-reviewer consensus rows and valid resolved
adjudications. It writes no gold file when no eligible row exists, and it refuses to
overwrite an existing gold file. Inspect the evaluator report before describing an
evaluation as complete.

Without `gold_annotations.csv`, the command validates the prediction inputs and writes
`WAITING_FOR_GOLD_LABELS`; no performance metric is emitted. When the gold annotations
are ready, the report can be refreshed with:

```powershell
python 5_process/relevance_evaluation/evaluate.py --overwrite-reports
```
