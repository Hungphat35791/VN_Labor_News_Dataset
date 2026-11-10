# P4 Module Completion Report

**Scope:** P4.01–P4.09 — Deduplication & Relevance Classification

**Generated:** 2026-11-09
**Overall status:** `PARTIALLY_COMPLETED` — technical artifacts exist, but human
review and eligible gold labels are still outstanding.

## 1. Executive summary

P4.08 multi-label topic-candidate classification is implemented, tested, and run
against the canonical dataset. P4.09 evaluation is implemented and tested, but
correctly reports `WAITING_FOR_GOLD_LABELS`: no eligible P4.06 human gold file is
available. No accuracy, precision, recall, F1, confusion matrix, or topic score is
claimed.

The duplicate detectors and grouping pipeline produced candidates only. They did
not modify, delete, or merge articles. URL and exact-content detection found no
candidates; 70 near-duplicate pairs in 61 groups are prepared for independent
human review. Reviewer calibration and P4.06 review sheets are blank; no
adjudication or human duplicate decisions have been received.

## 1.1 Human-review readiness (checked 2026-11-09)

| Workstream | Observed state | What remains |
|---|---|---|
| Calibration | Both sheets contain 12 scenarios and no responses. Status `WAITING_FOR_REVIEWERS`; coordinator-only scoring is not performed. | Two reviewers must independently complete and lock their sheets before answer-key comparison. Individual reviewer result files are prepared. |
| Existing 620-item sample | 620 unique rows, expected 9-column A–L manual schema; all 620 are `PENDING`, with relevance/topic/reason/reviewer/date fields blank. | Not a P4.06 gold set. Do not copy its A–L labels or P4.07 predictions into P4.06. |
| Original Person 4 assignment output path | `data/processed/manual_label_sample.csv` is absent from the current repository. | `data/interim/relevance_review_sample.csv` is a distinct 620-row pending sample, not evidence of completed manual annotation. `reports/label_quality.md` now marks the older 57-row claim as historical and not verifiable from the absent file. |
| P4.06 reviewer packets | Two newly prepared sheets, 620 rows each, same IDs/order/title/content; response fields blank and `annotation_status=PENDING`. | Reviewers must complete independently after calibration, using the P4.06 protocol and actual reviewer IDs/dates. |
| Existing Batch 01–03 | 50 rows each; all 150 remain `PENDING` and their manual label/reason/reviewer/date fields are blank. | No completed batch review is available. These A–L sheets are separate from the new P4.06 packets. |
| Existing Pilot 10 | Both reviewer sheets contain the same 10 articles; all are `PENDING` and manual answer fields are blank. Validation reports `WAITING_FOR_HUMAN_REVIEW`. | Reviewers complete independent A-L judgments; any disagreement is queued. Pilot remains non-gold and awaits project-owner approval. |
| Legacy manual labels | `legacy_borderline_manual_labels.csv` has 56 completed A–L records for a separate, non-authoritative pool. | Not compatible with P4.06 and excluded from gold. |
| P4.04 duplicate candidates | 70 near-duplicate pairs across 61 candidate groups; all source candidates remain `REVIEW_REQUIRED`. | Two reviewers must review pairwise; no pair has a submitted decision or adjudication. |
| Existing `duplicate_review.csv` | 71 legacy review entries, all decision/review-note fields blank; contents do not correspond to the 70 P4.04 pairs. | Kept separate and unchanged; do not treat as P4.04 review. |
| Existing modeling split/leakage audit | Temporal split has 8,213 train, 2,562 validation, 2,009 test; audit reports 32 near-title candidate pairs and 2 metadata duplicate clusters crossing splits, with 65 rows on `review_hold`. P4.04 candidate group `DUP-GROUP-000058` (4 articles) crosses validation/test; all 4 are held in `modeling_eligibility_manifest.csv`. | Candidate similarity is not duplicate confirmation. Keep the four held rows out of modeling unless human review resolves the concern. |
| P4.09 gold | `gold_annotations.csv` is absent; relevance and topic reports both say `WAITING_FOR_GOLD_LABELS` with null metrics. | Requires valid two-reviewer consensus or fully adjudicated P4.06 annotations with provenance. |

No human agreement, Cohen's Kappa, duplicate-confirmation rate, or gold-based
classifier metric is available.

## 2. P4.01–P4.09 status

| Task | Status | Evidence and remaining work |
|---|---|---|
| P4.01 Duplicate taxonomy | `COMPLETED` | `config/duplicate_taxonomy.md` defines URL, exact-content, near, and version duplicates, with review-only handling. |
| P4.02 URL duplicate detection | `COMPLETED` | `src/detect_url_duplicates.py` ran on 12,784 articles; `reports/url_duplicate_report.json` records input/output SHA-256, input row count, detector version/method, 0 candidates and 0 invalid URLs; unit tests cover normalization, source preservation, report hashes, and input-change rejection. |
| P4.03 Exact-content detection | `COMPLETED` | `src/detect_exact_duplicates.py`; 0 exact groups among 12,784 articles. |
| P4.04 Near-duplicate detection | `WAITING_FOR_DUPLICATE_REVIEW` | `src/detect_near_duplicates.py` produced 70 candidate pairs; independent human review is required to distinguish duplicates from independent coverage. |
| P4.05 Duplicate grouping | `WAITING_FOR_DUPLICATE_REVIEW` | `src/group_duplicate_candidates.py` produced 61 candidate groups covering 127 articles. All remain `REVIEW_REQUIRED`; no automatic merge. |
| P4.06 Human relevance/topic annotation | `WAITING_FOR_GOLD_LABELS` | Taxonomy and review tooling are implemented, but both 620-row P4.06 sheets remain `PENDING`; no valid gold exists. |
| P4.07 Rule-based relevance classification | `WAITING_FOR_HUMAN_REVIEW` | `src/classify_relevance_rules.py` ran on 12,784 articles and has passing tests. Human confirmation and P4.09 performance validation await independent review and resolved gold. |
| P4.08 Topic classification | `COMPLETED` | New isolated P4.06 multi-label output generated for 12,784 articles; tests pass. Labels are automatic candidates, not gold. |
| P4.09 Relevance/topic evaluation | `WAITING_FOR_GOLD_LABELS` | Evaluator and tests are ready. The gold input is absent, so the report contains no performance metrics. |

No task is marked `BLOCKED`; P4.09 is explicitly waiting on human annotations,
not reporting a successful evaluation.

## 3. Implemented and reused artifacts

### Existing P4.01–P4.07 artifacts

- Taxonomies: `config/duplicate_taxonomy.md`,
  `config/relevance_taxonomy.md`.
- Detectors/grouping/classifier: `src/detect_url_duplicates.py`,
  `src/detect_exact_duplicates.py`, `src/detect_near_duplicates.py`,
  `src/group_duplicate_candidates.py`, `src/classify_relevance_rules.py`.
- Reports: `reports/exact_duplicate_report.json`,
  `reports/near_duplicate_report.json`,
  `reports/duplicate_grouping_report.json`,
  `reports/relevance_rule_report.json`.
- Candidate data: `data/interim/url_duplicate_candidates.csv`,
  `data/interim/exact_duplicate_candidates.csv`,
  `data/interim/near_duplicate_candidates.csv`,
  `data/interim/duplicate_groups.csv`,
  `data/interim/relevance_results.csv`.
- Existing tests: `tests/test_detect_url_duplicates.py`,
  `tests/test_detect_exact_duplicates.py`, `tests/test_detect_near_duplicates.py`,
  `tests/test_duplicate_grouping.py`, `tests/test_classify_relevance_rules.py`.
- `src/prepare_p4_human_review.py` and
  `tests/test_prepare_p4_human_review.py` create validated, blank independent
  reviewer packets without modifying the existing 620-item sample.
- `relevance_evaluation/p406_gold_review_protocol.md` documents the P4.06
  reviewer contract, P4.09 schema, and separation from manual A–L labels.
- `relevance_evaluation/README.md` documents `--overwrite-reports`, an explicit
  future-only option to refresh P4.09 outputs once new annotations are provided.
- `reports/duplicate_review_protocol.md` defines independent pair review,
  decisions, adjudication, and version-lineage evidence.
- `data/interim/duplicate_review_sheet.csv` is a neutral template;
  `duplicate_review_reviewer_1_sheet.csv` and
  `duplicate_review_reviewer_2_sheet.csv` are separate 70-pair reviewer copies.
- `reports/duplicate_review_summary.json` records
  `WAITING_FOR_DUPLICATE_REVIEW`, 0 reviewed pairs, and 70 pending pairs.
- `relevance_evaluation/p406_reviewer_1_sheet.csv` and
  `p406_reviewer_2_sheet.csv` contain 620 blank P4.06 annotation rows each.
- `src/validate_p4_human_review.py` validates calibration, P4.06, and duplicate
  submissions without changing reviewer data. It writes calibration results/feedback,
  P4.06 missing/validation/agreement reports, duplicate validation/agreement reports,
  adjudication queues, and a 70-pair version-lineage review sheet. Calibration is
  compared with the coordinator-only key only after both complete submissions exist.
- Calibration results are split into
  `reports/reviewer_calibration_reviewer_1_report.json` and
  `reports/reviewer_calibration_reviewer_2_report.json`. Both currently report
  `WAITING_FOR_REVIEWERS`; blank topic is accepted for `Not relevant` and `Uncertain`.
- `src/validate_pilot_10.py` validates the manual A-L Pilot 10 sheets, progress,
  agreement, disagreements, and adjudication queue without treating pilot labels as
  P4.06 gold. Its validation/agreement reports currently show 0/10 reviewed per
  reviewer, no comparable decisions, an empty queue, and `WAITING_FOR_HUMAN_REVIEW`.
- `src/prepare_human_adjudication.py` creates separate P4.06 and duplicate
  adjudication forms; it rejects cases not in the current queue or changed reviewer
  evidence, validates actual adjudicator IDs/dates/reasons, and builds P4.09 gold only
  from valid two-reviewer consensus or resolved adjudication. It writes no gold file
  when no eligible record exists. Validation snapshots include source hashes in
  `reports/adjudication_validation_report.json`; distinct snapshots are preserved in
  append-only `reports/adjudication_validation_history.jsonl`.
- Calibration results and feedback report `WAITING_FOR_REVIEWERS` (0/12 complete
  for each reviewer); files are `reports/reviewer_calibration_results.json` and
  `reports/reviewer_calibration_feedback.md`. No answer-key scoring was performed.
- Calibration answer-key comparison is now protected by
  `reports/reviewer_calibration_lock.json`, a coordinator-created manifest binding
  both reviewer IDs and exact sheet hashes. No valid lock exists, so comparison
  remains disabled and no answer key was disclosed in reviewer-facing files.
- P4.06 files are `reports/p406_annotation_validation_report.json`,
  `reports/p406_missing_annotations.csv`,
  `reports/p406_reviewer_agreement_report.json`, and
  `reports/p406_adjudication_queue.csv`. They record 620 pending rows per reviewer,
  zero valid completed annotations, zero comparable agreements/disagreements, and
  no adjudication cases.
- Duplicate files are `reports/duplicate_review_validation_report.json`,
  `reports/duplicate_reviewer_agreement_report.json`,
  `reports/duplicate_adjudication_queue.csv`, and
  `reports/duplicate_version_lineage_review.csv`. They record 70 valid candidate
  rows per reviewer, all pending; zero reviewed by both, zero confirmations, and
  zero verified version lineages. The version-lineage sheet contains all 70
  candidates with pending status.
- Separate coordinator forms are
  `relevance_evaluation/p406_adjudication_form.csv` and
  `data/interim/duplicate_adjudication_form.csv`; both currently have headers only.
- `data/interim/pilot_10_adjudication_form.csv` is a separate A–L pilot form;
  its validation reports `NO_ADJUDICATION_CASES`. Pilot decisions remain separate
  from P4.06 gold.
- `src/run_p4_review_workflow.py` safely refreshes validation/evaluation outputs
  without writing reviewer decisions. Latest run completed all steps and reports
  `WAITING_FOR_GOLD_LABELS`; no gold file was created.
- `reports/split_and_leakage_checks.json` and `splits/modeling_eligibility_manifest.csv`
  show existing temporal/modeling split checks. A P4.04 candidate group crosses
  validation/test, but all four members are already on `review_hold`.

### P4.08

- `topic_classification/classify_topics.py`
- `topic_classification/README.md`
- `topic_classification/topic_labels.csv`
- `reports/topic_classification_report.json`
- `tests/test_topic_classification.py`

P4.08 reuses the explicit P4.07 topic rules and relevance gate. Output uses JSON
arrays/objects for labels, integer rule-match scores, and per-topic rule/evidence
reasons. Scores are evidence counts, not calibrated confidence. No manual annotation
field is read or written. P4.06's 10 machine topics are not mapped to the 12 manual
A–L topics.

### P4.09

- `relevance_evaluation/evaluate.py`
- `relevance_evaluation/README.md`
- `relevance_evaluation/relevance_report.json`
- `relevance_evaluation/relevance_report.md`
- `relevance_evaluation/topic_report.json`
- `tests/test_relevance_evaluation.py`

The report records the evaluation method/time, classifier and taxonomy versions,
prediction methods and sample counts, input hashes, exclusions, and leakage-check
status. It only accepts completed human or human-adjudicated P4.06 gold. `BORDERLINE`,
`UNCERTAIN`, pending annotations, and unresolved adjudications are not collapsed into
another class. With valid gold, relevance reporting includes accuracy, macro- and
support-weighted precision/recall/F1, per-class scores, and a three-class confusion
matrix. The separate `topic_report.json` supports micro/macro/per-topic scores,
support-weighted F1, Hamming loss, subset accuracy, and Jaccard. Current outputs are
`WAITING_FOR_GOLD_LABELS` with null metrics; these capabilities do not imply an
evaluation result.

## 4. Observed results

### P4.02–P4.05 duplicate results

- Articles checked: 12,784.
- URL duplicate candidate pairs: 0.
- Exact-content duplicate groups: 0; articles in groups: 0.
- Near-duplicate candidate pairs: 70.
- Candidate groups: 61, covering 127 articles (58 groups of 2, 1 group of 3,
  and 2 groups of 4).
- Group status: `REVIEW_REQUIRED`.
- Version duplicate evidence: unavailable; no version lineage was inferred.
- Human-reviewed pairs: 0/70. Confirmed duplicates: 0. No reviewer agreement or
  adjudication result exists.
- Split audit over candidates: 3 candidate pairs in 1 group
  (`DUP-GROUP-000058`) cross validation/test. All crossing candidate pairs have
  existing modeling quarantine coverage; none are human-confirmed duplicates.

### P4.07 relevance results

Classifier/taxonomy version: `1.0.0` / `1.0.0`; method: rule-based.

| P4.06 status | Articles |
|---|---:|
| `RELEVANT` | 10,240 |
| `IRRELEVANT` | 220 |
| `REVIEW_REQUIRED` | 2,324 |

These are rule-based outputs, not human-confirmed labels or performance metrics.

### P4.08 topic results

Classifier/taxonomy version: `1.0.0` / `1.0.0`; method:
`p4.07_rule_reuse_with_per_topic_evidence`.

- Articles processed: 12,784.
- `RELEVANT` articles with one or more topic labels: 10,240.
- Multi-label `RELEVANT` articles: 6,317.
- `IRRELEVANT` and `REVIEW_REQUIRED` articles have no final topic labels.

| P4.06 topic | Candidate article count |
|---|---:|
| `EMPLOYMENT` | 5,891 |
| `UNEMPLOYMENT` | 1,501 |
| `WAGES` | 4,182 |
| `SOCIAL_INSURANCE` | 3,857 |
| `UNEMPLOYMENT_INSURANCE` | 1,616 |
| `LABOR_RIGHTS` | 628 |
| `LABOR_CONTRACT` | 1,346 |
| `LABOR_DISPUTE` | 1,009 |
| `OCCUPATIONAL_SAFETY` | 563 |
| `LABOR_POLICY` | 2,591 |

Counts are multi-label and therefore may sum to more than the number of articles.

### P4.09 evaluation results

- Status: `WAITING_FOR_GOLD_LABELS`.
- Eligible P4.06 gold annotations: 0.
- The gold builder returned `WAITING_FOR_GOLD_LABELS` and did not create
  `gold_annotations.csv`; no synthetic data or automatic predictions were used.
- P4.07 prediction rows: 12,784; P4.08 prediction rows: 12,784.
- Classifier versions: P4.07 `1.0.0`; P4.08 `1.0.0`; taxonomy version `1.0.0`.
- Relevance and multi-label metrics: not calculated.
- Leakage check: `NOT_APPLICABLE_NO_TRAIN_TEST_SPLIT`; these rule-based classifiers
  do not fit a train/test model. This applies only to the current P4.09 run; the
  separate temporal modeling split has known candidate leakage described above.

The existing legacy sidecar contains 56 A–L manual records for a separate, non-
authoritative pool and lacks the P4.06 gold contract. It was not used. A historical
`reports/label_quality.md` references a separate 57-row manual file that is not
present at the stated path and includes conflicting readiness statements; those
claims were not treated as P4.06 gold. No automatic mapping between the manual A–L
labels and P4.06 topics was attempted.

## 5. Validation

- Focused P4.08 tests: 11 passed.
- Focused P4.09 tests: 17 passed, including explicit report refresh after a
  simulated human-gold input in an isolated temporary test directory.
- Human-review packet tests: 5 passed.
- Human-review workflow tests: 15 passed, using synthetic fixtures only.
- Full `5_process` suite: 229 passed (latest final-gap-audit run).
- URL detector report: `reports/url_duplicate_report.json`, status
  `NO_CANDIDATES_FOUND`, 0 invalid URLs.
- Workflow orchestration: all 8 stages succeeded; final status
  `WAITING_FOR_GOLD_LABELS`; protected inputs did not change during the run.
- P4.08 output: 12,784 unique article IDs; all topic labels are valid P4.06 codes;
  score/reason keys match labels; no manual annotation columns are present.
- P4.09 output: `WAITING_FOR_GOLD_LABELS`; metrics are null and the suppression
  reason is recorded.
- Canonical input SHA-256 recorded by both P4.07 and P4.08:
  `90a1c4a4e6cd70f27df2ec15e58b4183990a398ed2a2730de2c0302bdedf6f41`.
- `git diff --check`: passed.

### Current human-review and data-integrity audit (2026-11-09)

| Check | Result |
|---|---|
| Calibration | Reviewer 1: 0/12 complete; Reviewer 2: 0/12 complete; status `WAITING_FOR_REVIEWERS`; no answer-key comparison. |
| Pilot 10 | Reviewer 1: 0/10 complete; Reviewer 2: 0/10 complete; `WAITING_FOR_HUMAN_REVIEW`; 0 comparable decisions, 0 disagreements, empty adjudication queue. |
| P4.06 sheets | 620 unique IDs each, same master order and unchanged title/content; all 1,240 rows are `PENDING`. |
| P4.06 outcomes | 0 valid completed annotations; 0 comparable agreements/disagreements; 0 adjudication cases. |
| Duplicate review | 70 pairs / 61 groups; all 70 pending for each reviewer; 0 decisions compared by both, 0 confirmations, 0 verified lineages. |
| Leakage candidates | 3 candidate pairs across splits in `DUP-GROUP-000058`; all three crossing pairs have existing modeling quarantine coverage; none is human-confirmed. |
| Adjudication forms | Separate forms exist with headers and 0 cases; validation passed; no human decision or adjudicator metadata was entered. |
| Gold/P4.09 | Gold builder returned `WAITING_FOR_GOLD_LABELS`, 0 eligible rows, and created no gold file. No metrics were calculated. |
| Generated CSV rows | Pilot 10 queue: 0; P4.06 missing report: 1,240 and queue: 0; duplicate queue: 0; version-lineage review: 70; adjudication forms: 0 cases each. |
| Protected data | SHA-256 baselines matched for the canonical CSV, 620 master sample, Batch 01–03, both Pilot 10 sheets, both calibration sheets, labeling guideline, both P4.06 sheets, and both duplicate reviewer sheets. |

## 6. Risks, limitations, and human actions

1. Review the 70 near-duplicate pairs and 61 groups manually. Same-event coverage is
   not sufficient evidence of duplication; do not delete or merge from candidate
   output alone.
   The existing temporal split has one P4.04 candidate group spanning
   validation/test; keep its four already-held members quarantined until reviewers
   resolve the pairwise evidence.
2. Provide resolved, completed P4.06 human annotations with the P4.09 gold schema
   before measuring classifier performance. Keep A–L manual labels separate unless
   the project formally defines and approves a mapping.
3. Review the 2,324 P4.07 `REVIEW_REQUIRED` articles and classifier false positives/
   false negatives through a properly controlled human sample.
4. Topic scores count matched strong rules; they are not probabilities, calibrated
   confidence values, or validated estimates of correctness.
5. Near-duplicate and rule-based classifiers may miss paraphrases or flag incidental
   phrasing; results are candidates for review.

The canonical CSV, reviewer sheets, master sample, batches, and existing manual
artifacts were not used as writable outputs. The two P4.06 review sheets were
derived only from the already-reviewed-as-pending sample's article IDs/title/body;
no predictions or legacy annotations were copied. The P4.04 sheets were derived
from current candidate pairs and canonical article text; all decision/provenance
fields remain blank. No source article was modified, deleted, or merged. No commit
or push was made.

The person-specific implementation and reviewer/adjudicator handoff is documented
in `reports/P4_PERSON_4_HANDOVER_REPORT.md`.
