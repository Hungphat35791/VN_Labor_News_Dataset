# P4.06 Human Gold Annotation Protocol

**Status:** Preparation only — `WAITING_FOR_HUMAN_REVIEW`
**Taxonomy:** `config/relevance_taxonomy.md`, version `1.0.0`
**Scope:** Independent human annotation of the 620 existing audit-sample articles.

## 1. What is prepared

- `p406_reviewer_1_sheet.csv` and `p406_reviewer_2_sheet.csv` contain the same
  620 article IDs, order, titles, and full content as
  `data/interim/relevance_review_sample.csv`.
- Both sheets contain only P4.06 annotation fields; automatic predictions and
  legacy A–L labels are not included.
- All response fields are blank and `annotation_status` is `PENDING`.
- The existing 620-row sample, Batch 01–03, Pilot 10, and canonical CSV remain
  unchanged.

Reviewers should receive only the calibration exercises and their own calibration
sheet until independent calibration work is completed and locked. The coordinator-
only answer key must not be distributed beforehand. After calibration, send each
reviewer only their own P4.06 sheet and this protocol.

## 2. P4.06 relevance and topic decisions

Use the P4.06 taxonomy directly, reread the full available title and article body,
and decide independently:

- `RELEVANT`: labor or employment with a direct Vietnam connection is a substantive
  subject. Assign one or more supported P4.06 topics.
- `IRRELEVANT`: labor is absent, incidental, or outside the defined scope. Topic
  set must be empty.
- `REVIEW_REQUIRED`: available text is insufficient, truncated, contradictory,
  too vague, or context-dependent to decide reliably. Topic set must be empty; give
  the missing or conflicting evidence in the reason.

The permitted P4.06 topics are `EMPLOYMENT`, `UNEMPLOYMENT`, `WAGES`,
`SOCIAL_INSURANCE`, `UNEMPLOYMENT_INSURANCE`, `LABOR_RIGHTS`, `LABOR_CONTRACT`,
`LABOR_DISPUTE`, `OCCUPATIONAL_SAFETY`, and `LABOR_POLICY`. A relevant article may
receive multiple labels, but each must be supported by substantive article content.
Enter `gold_topic_labels_p406` as a JSON string array, for example
`["WAGES","LABOR_DISPUTE"]`; use `[]` for non-RELEVANT statuses.

The older `labeling_guideline.md` uses `Relevant`, `Borderline`, `Not relevant`,
`Uncertain`, and a single A–L topic. These are a separate annotation system:

- Do not copy or convert its labels or topics into P4.06.
- Do not use `BORDERLINE` or `UNCERTAIN` in the P4.06 response field. Reassess
  under P4.06; use `REVIEW_REQUIRED` when its stated abstention criteria apply.
- If an old A–L record is encountered, keep it in its own artifact and do not treat
  it as P4.06 gold.

## 3. Reviewer fields and completion

The P4.06 sheet columns are:

`article_id,title,content,gold_relevance_status,gold_topic_labels_p406,review_reason,reviewer_id,review_date,annotation_status`

- `review_reason`: a concrete evidence-based explanation from the article, or the
  specific missing/conflicting evidence for `REVIEW_REQUIRED`.
- `reviewer_id`: the reviewer’s real, group-confirmed identifier.
- `review_date`: actual completion date in `YYYY-MM-DD`.
- `annotation_status`: keep `PENDING` until the row is complete; set to
  `COMPLETED` only after all required values and topic/status consistency checks
  pass. Use `NEEDS_ADJUDICATION` when the reviewer cannot resolve a policy or
  evidence issue; do not manufacture a label to complete the row.

Do not use the other reviewer’s sheet, AI proposals, `relevance_status`,
`topic_labels`, or classifier output to decide. Do not edit article text or IDs.
Do not enter answers into the 620-item legacy A–L sample.

## 4. Agreement, adjudication, and final P4.09 gold

After both submissions are received and locked, compare by `article_id`:

1. Compare relevance status.
2. Compare topic sets without converting to one topic.
3. Treat any status or topic-set difference as an item for discussion/adjudication;
   preserve both original reviewer decisions.
4. An authorized adjudicator records the final decision, actual adjudicator ID,
   actual decision date, evidence-based reason, and a resolved/unresolved status.
   The assistant must not decide the outcome.
5. Unresolved rows remain explicitly unresolved and are excluded by P4.09 with
   an exclusion count; they are not silently dropped or mapped to another label.

`evaluate.py` requires these final gold CSV columns (additional provenance columns
are allowed):

`article_id,gold_relevance_status,gold_topic_labels_p406,annotation_status,adjudication_status,annotation_method,reviewer_id,review_date,review_reason,contributing_reviewer_ids,adjudicator_id,adjudication_date`

For eligible rows, use `annotation_status=COMPLETED`,
`adjudication_status=NOT_REQUIRED` for resolved agreement or `ADJUDICATED` for a
resolved adjudication, and `annotation_method=human` or `human_adjudicated`.
`contributing_reviewer_ids` must preserve two distinct actual reviewer IDs.
Adjudicated rows must include the actual adjudicator ID/date; consensus rows must
not claim an adjudicator. Keep reviewer/adjudicator identifiers and dates real.

P4.09 preserves `BORDERLINE` and `UNCERTAIN` if encountered in an eligible legacy
gold file but excludes them from its three-class and topic metrics; it never
coerces them. P4.06’s `REVIEW_REQUIRED` is a distinct abstention class. No metric
is valid until the gold rows are complete, resolved, and validated.

## 5. Sampling and evaluation limitation

The 620 articles were sampled in strata based on P4.07 predicted statuses (200
`RELEVANT`, 220 `IRRELEVANT`, 200 `REVIEW_REQUIRED`; seed 42). Predictions are not
present in the reviewer sheets, but this design is not a representative sample of
the corpus distribution. Any P4.09 metrics from this sample must be reported as
sample-specific and must not be presented as unbiased corpus-wide performance.
The rule-based classifiers do not train a train/test model. If a later evaluation
does split data, keep every candidate duplicate group within one split and record
the split policy and seed.

The repository already has a separate temporal modeling split (8,213 train,
2,562 validation, 2,009 test). Its leakage audit reports 32 near-title candidate
pairs crossing splits and two metadata duplicate clusters crossing splits;
65 related records are in `splits/modeling_eligibility_manifest.csv` as
`review_hold`. One P4.04 content-candidate group, `DUP-GROUP-000058`, spans
validation and test; its four members are already held out in the eligibility
manifest. These candidates are not human-confirmed duplicates. P4.09's current
rule-based comparison does not use this split; if a future learned-model
evaluation uses it, apply the duplicate-group leakage check and keep held or
candidate groups quarantined until reviewed.
