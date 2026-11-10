# Person 4 Handover Report

**Date:** 2026-11-09
**Repository:** `VN_Labor_News_Dataset_Clone`
**Overall status:** `PARTIALLY_COMPLETED`

## Summary

The technical validation, evaluation, and human-review preparation tools are
implemented and tested. Human calibration, Pilot 10, 620-article annotation,
duplicate review, and adjudication are still awaiting real submissions. No gold
labels or human decisions were generated. P4.09 remains
`WAITING_FOR_GOLD_LABELS`; no official evaluation metrics are available.

Latest status refresh after the supplied Pilot 10 reviewer-sheet snapshot:
calibration `WAITING_FOR_REVIEWERS`; Pilot 10 `WAITING_FOR_HUMAN_REVIEW` (0/10
per reviewer); P4.06 `WAITING_FOR_REVIEWERS` (0/620 per reviewer); duplicate
review `WAITING_FOR_DUPLICATE_REVIEW` (0/70 per reviewer); adjudication queues
empty; gold builder `WAITING_FOR_GOLD_LABELS` (620 records excluded, no gold file
created); P4.09 `WAITING_FOR_GOLD_LABELS`, with metrics suppressed.

The latest rerunnable workflow completed all eight stages successfully. The URL
detector report also records 0 candidates and 0 invalid URLs. Reviewer and source
input SHA-256 values were unchanged during execution and match the recorded
baselines; no gold file exists.

## P4.01–P4.09 status

| Task | Status | Current evidence / remaining dependency |
|---|---|---|
| P4.01 Duplicate taxonomy | `COMPLETED` | Taxonomy defines URL, exact-content, near, and version duplicate types. |
| P4.02 URL detection | `COMPLETED` | Detector ran on 12,784 articles; 0 candidates and 0 invalid URLs. `reports/url_duplicate_report.json` records the run. |
| P4.03 Exact-content detection | `COMPLETED` | No exact-content groups found in 12,784 articles. |
| P4.04 Near-duplicate detection | `WAITING_FOR_DUPLICATE_REVIEW` | 70 candidate pairs await independent human decisions. |
| P4.05 Duplicate grouping | `WAITING_FOR_DUPLICATE_REVIEW` | 61 candidate groups cover 127 articles; no group is confirmed. |
| P4.06 Human relevance/topic annotation | `WAITING_FOR_REVIEWERS` | Both 620-row sheets have 0 valid completed annotations. Consequently no gold is eligible. |
| P4.07 Relevance classification | `WAITING_FOR_HUMAN_REVIEW` | Rule-based predictions exist for 12,784 articles; human validation remains outstanding. |
| P4.08 Topic classification | `COMPLETED` | Multi-label topic candidates generated for 12,784 articles and tested. Predictions are not gold. |
| P4.09 Evaluation | `WAITING_FOR_GOLD_LABELS` | Evaluator is ready; no gold file or official metrics exist. |

## Work completed and verified technically

- Calibration validation preserves CAL-01–CAL-12, does not score until both valid
  independent submissions are present, and writes separate coordinator-side
  reviewer reports. A coordinator-only lock manifest must bind the exact sheet
  hashes before answer-key comparison. No valid lock or submissions exist; current
  state is 0/12 for each reviewer, `WAITING_FOR_REVIEWERS`.
- Pilot 10 A–L validation checks reviewer sheets, content/ID order, labels,
  provenance, progress, agreement, and disagreement queue. Current state: 0/10
  for each reviewer, `WAITING_FOR_HUMAN_REVIEW`. Pilot annotations are not P4.06
  gold and need project-owner approval.
- P4.06 validation checks all 620 article IDs, order, schema, permitted labels,
  topics, reviewer metadata, agreement, and missing records. Both sheets are
  pending, with 1,240 missing reviewer annotations total and no adjudication cases.
- Duplicate validation checks all 70 pairs and 61 groups against canonical article
  IDs, reviewer sheet consistency, split coverage, agreement, and version-lineage
  evidence. Both reviewers have submitted 0/70 decisions; no pair is confirmed and
  no lineage is verified.
- Adjudication tools use separate P4.06 and duplicate queues/forms, require
  queue membership and completed decision/reason/adjudicator/date fields, and
  protect reviewer opinions. No final decision can be inferred automatically.
- P4.09 validates gold IDs, statuses, P4.06 topics, reviewer provenance, and
  adjudication metadata. It supports relevance accuracy, precision/recall/F1,
  confusion matrix and class reports, plus multi-label micro/macro/per-topic scores,
  weighted F1, Hamming loss, subset accuracy, and Jaccard. `BORDERLINE` and
  `UNCERTAIN` are not coerced into another class.
- Full test suite: **229 passed**. `git diff --check`: **passed**.
- Python compilation (`py_compile`) of the workflow/evaluator scripts and focused
  tests: **passed**.
- Guarded workflow orchestration: all eight stages succeeded and final status is
  `WAITING_FOR_GOLD_LABELS`; no reviewer input changed and no gold file was built.
- URL duplicate report: 0 candidates, 0 invalid URLs,
  `NO_CANDIDATES_FOUND`.

## Current reviewer and adjudicator dependencies

| Workstream | Current status | Human action required |
|---|---|---|
| Calibration | `WAITING_FOR_REVIEWERS` | Each reviewer independently completes all 12 calibration scenarios. Keep the answer key coordinator-only until both are complete and valid. |
| Pilot 10 | `WAITING_FOR_HUMAN_REVIEW` | Review the 10 A–L pilot articles independently; resolve any queued disagreements, then obtain project-owner approval. Do not copy pilot answers into P4.06. |
| P4.06 (620 articles) | `WAITING_FOR_REVIEWERS` | Both reviewers complete the 620-row P4.06 sheets with actual reviewer ID, date, topics, and reasons. |
| Duplicate review | `WAITING_FOR_DUPLICATE_REVIEW` | Both reviewers decide all 70 pairs using the taxonomy and provide evidence for version-lineage decisions. Similarity scores or same-event coverage alone are not confirmation. |
| Adjudication | `WAITING_FOR_ADJUDICATION` when disagreements exist; currently no cases | A designated adjudicator resolves only queued disagreements and records an actual decision, reason, ID, and date in the corresponding form. |
| Gold and P4.09 | `WAITING_FOR_GOLD_LABELS` | After independent reviews and required adjudication, run the gold builder and then evaluation. Do not use classifier predictions or legacy A–L labels as gold. |

## Outputs and next-step commands

Generated coordinator reports and forms include:

- Calibration: `reports/reviewer_calibration_results.json`,
  `reports/reviewer_calibration_feedback.md`,
  `reports/reviewer_calibration_reviewer_1_report.json`,
  `reports/reviewer_calibration_reviewer_2_report.json`.
- Pilot 10: `reports/pilot_10_validation_report.json`,
  `reports/pilot_10_agreement_report.json`,
  `reports/pilot_10_adjudication_queue.csv`.
- P4.06: `reports/p406_annotation_validation_report.json`,
  `reports/p406_missing_annotations.csv`,
  `reports/p406_reviewer_agreement_report.json`,
  `reports/p406_adjudication_queue.csv`.
- Duplicate review: `reports/duplicate_review_validation_report.json`,
  `reports/duplicate_reviewer_agreement_report.json`,
  `reports/duplicate_adjudication_queue.csv`,
  `reports/duplicate_version_lineage_review.csv`.
- URL detection: `reports/url_duplicate_report.json`.
- Run-wide status and protected-input hashes:
  `reports/p4_review_workflow_status.json`.
- Pilot adjudication: `data/interim/pilot_10_adjudication_form.csv` and
  `reports/pilot_10_adjudication_validation_report.json` (no cases; Pilot remains outside P4.06 gold).
- Adjudication: `relevance_evaluation/p406_adjudication_form.csv`,
  `data/interim/duplicate_adjudication_form.csv`,
  `reports/adjudication_validation_report.json`.
- P4.09: `relevance_evaluation/relevance_report.json`,
  `relevance_evaluation/relevance_report.md`,
  `relevance_evaluation/topic_report.json`.

After submissions are provided, the coordinator should rerun the validators and
refresh generated reports without overwriting human inputs:

```powershell
python 5_process/src/validate_p4_human_review.py --overwrite-reports
python 5_process/src/validate_pilot_10.py --overwrite-reports
python 5_process/src/prepare_human_adjudication.py --refresh-empty-forms
python 5_process/src/prepare_human_adjudication.py --validate
```

Refresh adjudication forms only when they are still empty; if a form contains
adjudicator input, preserve it and resolve any stale-queue condition explicitly.
Build and evaluate gold only after the eligibility checks pass:

```powershell
python 5_process/src/prepare_human_adjudication.py --build-gold
python 5_process/relevance_evaluation/evaluate.py
```

The 620-article sample was stratified by P4.07 predicted status (200 relevant,
220 irrelevant, 200 review-required). Even after annotation, its metrics are not a
direct estimate of the natural full-dataset distribution.

## Leakage and data protection

Three candidate pairs in `DUP-GROUP-000058` cross validation/test. All four group
members already have modeling `review_hold` coverage. These are unconfirmed
candidates, not confirmed duplicates; retain the quarantine until human review
resolves them.

Protected file SHA-256 checks matched the recorded baselines:

| Protected input | SHA-256 |
|---|---|
| Canonical CSV | `90a1c4a4e6cd70f27df2ec15e58b4183990a398ed2a2730de2c0302bdedf6f41` |
| 620-item master sample | `8e09acffaaee6c5e6883634a3ecc32d075fc45ea3d24f7c5aa6c66ecd889e85c` |
| Batch 01 | `cdc485ef53ac6f13023243c30cb21ac9a2157b10a6d8c7d7dd4e393634a192df` |
| Batch 02 | `8120022d2aa665de5ea5a5da8cb51d92697eb7bf04c2b8849b47df7924f1dbc3` |
| Batch 03 | `81541d8e12510aa1d4558062de386af996575ad370ee4b306c9d2faac806ec9d` |
| Pilot 10 reviewer sheets (each) | `29f3f18da8b51a57477b76b7924144000a2e0e3869180511d9e0f772c7cb1e69` |
| Calibration reviewer sheets (each) | `909677c1171d1779708b5e61735a47c6fdf682755a0d2d837559c6d2a34ff45a` |
| Labeling guideline | `49983c55f820cc092652ff33c7642717f3e2cd309745a0007969e97b6398a849` |

No canonical article, reviewer response, adjudicator decision, or gold label was
created, changed, or inferred. No article was deleted, edited, or merged. No Git
commit or push was made.

## Final gap audit — 2026-11-09

Source assignment: [`Phan_cong_Process_6_nguoi.md`](../../Phan_cong_Process_6_nguoi.md),
section “Người 4 — Kiểm định nhãn và mức liên quan”. Statuses distinguish technical
evidence from human review and gold-label readiness.

| Mã nhiệm vụ | Deliverable bắt buộc | File bằng chứng | Trạng thái | Thiếu sót còn lại |
|---|---|---|---|---|
| GỐC-P4-A | Hướng dẫn nhãn liên quan và 12 nhóm A–L | [`config/labeling_guideline.md`](../config/labeling_guideline.md), [`reports/label_quality.md`](./label_quality.md) | `COMPLETED` về hướng dẫn; review chờ người | Chưa có submission hợp lệ trong sample hiện hành. |
| GỐC-P4-B | `data/processed/manual_label_sample.csv` có nguồn gốc rõ ràng | Đường dẫn yêu cầu hiện vắng; sample đang có: [`data/interim/relevance_review_sample.csv`](../data/interim/relevance_review_sample.csv), 620 ID, `PENDING`; batches 01–03 đều `PENDING` | `PARTIALLY_COMPLETED` | Không tự tạo alias/nhãn. Cần xác nhận đúng artifact/path và reviewer hoàn tất thủ công. |
| GỐC-P4-C | Báo cáo chất lượng nhãn, mẫu lấy, bất đồng, giới hạn | [`reports/label_quality.md`](./label_quality.md), [`reports/relevance_review_sample_report.json`](./relevance_review_sample_report.json) | `PARTIALLY_COMPLETED` | Báo cáo hiện ghi rõ file lịch sử 57-row vắng; chưa có kết quả review hiện hành để tính chất lượng/đồng thuận. |
| P4.01 | Duplicate taxonomy (URL, exact, near, version) | [`config/duplicate_taxonomy.md`](../config/duplicate_taxonomy.md) | `COMPLETED` | Không còn thiếu sót tài liệu kỹ thuật đã xác định. |
| P4.02 | URL duplicate detector, candidates, run evidence, tests | [`src/detect_url_duplicates.py`](../src/detect_url_duplicates.py), [`data/interim/url_duplicate_candidates.csv`](../data/interim/url_duplicate_candidates.csv), [`reports/url_duplicate_report.json`](./url_duplicate_report.json), [`tests/test_detect_url_duplicates.py`](../tests/test_detect_url_duplicates.py), [`README_PROCESS.md`](../README_PROCESS.md) | `COMPLETED` | Evidence: raw input 12,784 bài, input/output SHA-256, detector `1.0.0` / `url_normalization_v1`, 0 candidate pairs, 0 invalid URLs; 13 detector tests pass. Zero candidates là kết quả chạy, không phải thiếu output. |
| P4.03 | Exact-content duplicate detection | [`src/detect_exact_duplicates.py`](../src/detect_exact_duplicates.py), [`data/interim/exact_duplicate_candidates.csv`](../data/interim/exact_duplicate_candidates.csv), [`reports/exact_duplicate_report.json`](./exact_duplicate_report.json), [`tests/test_detect_exact_duplicates.py`](../tests/test_detect_exact_duplicates.py), [`README_PROCESS.md`](../README_PROCESS.md) | `COMPLETED` | Không phát hiện exact group trong 12,784 bài; không suy diễn human confirmation. |
| P4.04 | Near-duplicate candidates, review protocol, independent sheets | [`src/detect_near_duplicates.py`](../src/detect_near_duplicates.py), [`data/interim/near_duplicate_candidates.csv`](../data/interim/near_duplicate_candidates.csv), [`reports/near_duplicate_report.json`](./near_duplicate_report.json), [`reports/duplicate_review_protocol.md`](./duplicate_review_protocol.md), [`tests/test_detect_near_duplicates.py`](../tests/test_detect_near_duplicates.py) | `WAITING_FOR_DUPLICATE_REVIEW` | Công cụ và 70 candidate pairs đã có; hai reviewer sheets đều 0/70 quyết định. |
| P4.05 | Candidate groups và evidence giữ nguyên quan hệ cặp | [`src/group_duplicate_candidates.py`](../src/group_duplicate_candidates.py), [`data/interim/duplicate_groups.csv`](../data/interim/duplicate_groups.csv), [`reports/duplicate_grouping_report.json`](./duplicate_grouping_report.json), [`tests/test_duplicate_grouping.py`](../tests/test_duplicate_grouping.py), [`reports/duplicate_version_lineage_review.csv`](./duplicate_version_lineage_review.csv) | `WAITING_FOR_DUPLICATE_REVIEW` | 61 candidate groups/127 articles; không có group hoặc version lineage nào được người xác nhận. |
| P4.06 | Hai reviewer sheets 620 ID, validator, agreement/adjudication queue, protocol | [`relevance_evaluation/p406_reviewer_1_sheet.csv`](../relevance_evaluation/p406_reviewer_1_sheet.csv), [`relevance_evaluation/p406_reviewer_2_sheet.csv`](../relevance_evaluation/p406_reviewer_2_sheet.csv), [`src/validate_p4_human_review.py`](../src/validate_p4_human_review.py), [`src/prepare_human_adjudication.py`](../src/prepare_human_adjudication.py), [`relevance_evaluation/p406_gold_review_protocol.md`](../relevance_evaluation/p406_gold_review_protocol.md) | `WAITING_FOR_REVIEWERS` | 0/620 each; no agreements/disagreements to adjudicate and no eligible gold. |
| P4.07 | Rule-based relevance classifier with traceable output and human audit | [`src/classify_relevance_rules.py`](../src/classify_relevance_rules.py), [`data/interim/relevance_results.csv`](../data/interim/relevance_results.csv), [`reports/relevance_rule_report.json`](./relevance_rule_report.json), [`tests/test_classify_relevance_rules.py`](../tests/test_classify_relevance_rules.py), [`README_PROCESS.md`](../README_PROCESS.md) | `WAITING_FOR_HUMAN_REVIEW` | 12,784 predictions exist; 2,324 are `REVIEW_REQUIRED`. Predictions are not labels. A–L master/batches have no completed reviewer submissions. |
| P4.08 | Multi-label topic candidates, separate from manual A–L and Gold | [`topic_classification/classify_topics.py`](../topic_classification/classify_topics.py), [`topic_classification/topic_labels.csv`](../topic_classification/topic_labels.csv), [`reports/topic_classification_report.json`](./topic_classification_report.json), [`topic_classification/README.md`](../topic_classification/README.md), [`tests/test_topic_classification.py`](../tests/test_topic_classification.py) | `COMPLETED` kỹ thuật | Output/report explicitly identify automatic candidates, not gold; human validation remains outstanding. |
| P4.09 | Gold-gated relevance and multi-label evaluation with metrics/leakage checks | [`relevance_evaluation/evaluate.py`](../relevance_evaluation/evaluate.py), [`relevance_evaluation/README.md`](../relevance_evaluation/README.md), [`relevance_evaluation/p406_gold_review_protocol.md`](../relevance_evaluation/p406_gold_review_protocol.md), [`tests/test_relevance_evaluation.py`](../tests/test_relevance_evaluation.py), [`relevance_evaluation/relevance_report.json`](../relevance_evaluation/relevance_report.json), [`relevance_evaluation/topic_report.json`](../relevance_evaluation/topic_report.json) | `WAITING_FOR_GOLD_LABELS` | Evaluator accepts validated human/human-adjudicated gold and supports evaluation when supplied; currently no gold file or official metrics. |
| P4-WF | Detect changed reviewer inputs and refresh reports safely | [`src/run_p4_review_workflow.py`](../src/run_p4_review_workflow.py), [`reports/p4_review_workflow_status.json`](./p4_review_workflow_status.json), [`tests/test_p4_review_orchestration.py`](../tests/test_p4_review_orchestration.py) | `COMPLETED` as rerunnable workflow | Not a background watcher: coordinator must rerun it after submissions. Latest run completed all 8 stages, recorded input hashes, protected forms, and ended `WAITING_FOR_GOLD_LABELS`. |

### Final audit conclusion

`PERSON_4_TECHNICAL_WORK_COMPLETED` is **not** claimed. The pipeline, validators,
protocols, and evaluation path are implemented and tested, but the original named
manual sample artifact is absent, current review packages have no human submissions,
and P4.06/P4.09 cannot be completed without reviewers/adjudicator. Overall status is
`PARTIALLY_COMPLETED`, not a test-count-based completion claim.

Final verification: full suite **229 passed**; Python compilation passed;
P4.02 detector and guarded workflow completed successfully (8/8 workflow stages);
`git diff --check` passed. SHA-256 values matched for canonical input, master 620,
batches 01–03, Pilot 10 sheets, calibration sheets, P4.06 sheets, duplicate
reviewer sheets, and labeling guideline. No gold file exists, and no reviewer
submission changed during the audit.
