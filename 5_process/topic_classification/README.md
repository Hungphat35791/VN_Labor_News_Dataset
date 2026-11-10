# P4.08 Topic Classification

This module reuses the explicit Vietnamese phrase rules and relevance gating in
`5_process/src/classify_relevance_rules.py` (P4.07). It emits multi-label P4.06
topic candidates in a separate derived CSV. It never writes `topic_manual` or any
other annotation field.

## Run

```powershell
python 5_process/topic_classification/classify_topics.py
```

Optional paths:

```powershell
python 5_process/topic_classification/classify_topics.py `
  --input 1_du_lieu_chinh/vn_labor_news_dataset.csv `
  --output 5_process/topic_classification/topic_labels.csv `
  --report 5_process/reports/topic_classification_report.json
```

Existing outputs are never overwritten. Remove or select new output paths only
after a human has checked that the existing artifacts are safe to replace; this
module itself refuses to overwrite any existing output.

## Input and output

Required input columns: `article_id`, `title`, `content`. IDs must be nonblank and
unique; title/content are read as text. Source text is never modified.

Output columns:

- `article_id`
- `relevance_status` — P4.07 gate (`RELEVANT`, `IRRELEVANT`, or `REVIEW_REQUIRED`)
- `topic_labels` — JSON array of zero or more P4.06 topic codes
- `topic_scores` — JSON object mapping each candidate topic to the integer count of
  matched strong P4.07 rules
- `topic_reasons` — JSON object with matched rule IDs and matched title/content phrases
  for each candidate topic
- `classifier_version`, `source_relevance_classifier_version`, `taxonomy_version`
- `review_status` — `REVIEW_REQUIRED` if P4.07 abstained; otherwise `AUTO_CLASSIFIED`

The score is an evidence count, not a probability or calibrated confidence. When
P4.07 returns `REVIEW_REQUIRED` or `IRRELEVANT`, final topic labels/scores/reasons
are empty; weak cues are not promoted to labels. All outputs are automatic candidates,
not gold labels.

P4.06's 10-topic multi-label taxonomy is not interchangeable with the 12-topic
A-L human-review taxonomy in `labeling_guideline.md`.
