# P4 Duplicate Candidate Review Protocol

**Status:** Preparation only — `WAITING_FOR_DUPLICATE_REVIEW`
**Candidate method:** TF-IDF word unigram/bigram cosine similarity, threshold `0.85`
**Scope:** 70 P4.04 near-duplicate candidate pairs in 61 candidate groups.

## 1. Review files and current state

- `data/interim/duplicate_review_sheet.csv` is the neutral 70-pair template.
- `data/interim/duplicate_review_reviewer_1_sheet.csv` and
  `data/interim/duplicate_review_reviewer_2_sheet.csv` are independent copies.
- Each row includes both full article titles and bodies, source/date/URL metadata,
  the candidate score/method, group ID, and blank review fields.
- All decisions are blank and `review_status` is `PENDING`.
- `data/interim/duplicate_review.csv` is a pre-existing, different 71-row legacy
  review artifact. It was inspected, not overwritten, and must not be mixed with
  the 70 P4.04 near-duplicate pairs.
- Existing split audit: one P4.04 candidate group (`DUP-GROUP-000058`, four
  articles) spans validation and test. All four IDs are already assigned to
  `review_hold` in `splits/modeling_eligibility_manifest.csv` because of a
  cross-split metadata cluster. This is a leakage precaution, not a human
  confirmation that these four articles are duplicates.

Distribute one reviewer-specific file to each reviewer. Reviewers must work
independently and return their own file without seeing the other reviewer's
decisions. Do not edit the neutral template.

## 2. Review one candidate pair

1. Read both full article bodies and titles before considering the score.
2. Compare article-level overlap, distinctive facts, quotations, wording,
   structure, source/date/URL evidence, and whether each article contains
   independent reporting.
3. Treat the similarity score and connected-component `group_id` as candidate
   navigation only. Neither proves a duplicate.
4. Record exactly one `review_decision`:
   - `CONFIRMED_DUPLICATE`: evidence supports the same article/content being
     duplicated or republished.
   - `RELATED_BUT_DISTINCT`: same event/topic or source material, but each article
     has meaningful independent reporting or distinct content.
   - `NOT_DUPLICATE`: the pair is not an article-level duplicate.
   - `UNCERTAIN`: available evidence is insufficient to decide.
   - `NEEDS_ADJUDICATION`: reviewer identifies an unresolved policy/evidence issue
     or the two reviewers disagree.
5. Enter the actual reviewer ID, completion date (`YYYY-MM-DD`), and a reason
   citing specific text/metadata. Leave unresolved decisions unresolved.
6. Set `review_status=COMPLETED` only when the decision and required evidence are
   complete; use `NEEDS_ADJUDICATION` for cases requiring a final human decision.

Never confirm a duplicate based only on title, common keywords, source, event, or
similarity score. Two independently written reports of the same event are
`RELATED_BUT_DISTINCT` when that is what the evidence supports.

## 3. Relationship type and version lineage

`candidate_type` records the detector's original `NEAR_DUPLICATE` candidate and
must not be silently changed. If a duplicate is confirmed, record its supported
relationship in `confirmed_relationship_type` (`URL_DUPLICATE`,
`EXACT_CONTENT_DUPLICATE`, `NEAR_DUPLICATE`, or `VERSION_DUPLICATE`) and explain
the evidence.

Use `VERSION_DUPLICATE` only with direct lineage evidence, such as a stable
document ID, explicit update/correction metadata, revision history, or reliable
canonical identity plus version timestamps. Record that evidence in
`version_lineage_evidence`. Similarity, same event, or publication dates alone are
not sufficient. If the evidence is absent, leave version lineage unconfirmed.

## 4. Group-level handling and adjudication

`group_id` is a connected component of candidate edges, not a confirmed duplicate
cluster. Review every pair independently. Do not promote the entire group by
transitive inference from one confirmed pair; do not delete, edit, merge, or
reassign article IDs.

The existing temporal split has 32 separate near-title candidate pairs crossing
splits and two metadata duplicate clusters crossing splits; 65 related records
are marked `review_hold` in the modeling eligibility manifest. P4.09 currently
does not train or test a fitted model and has no split input. Before a future
train/validation/test evaluation, use the eligibility manifest and keep every
candidate group within one split or quarantined; do not remove the review hold
without human review.

After both independent files are returned and locked, compare decisions by the
ordered article pair. Preserve both originals. Any conflicting decision or
relationship type goes to an authorized human adjudicator, who records an actual
ID, date, evidence-based reason, and final outcome in a separate adjudication
record. Do not overwrite either reviewer sheet or infer a decision for an
unreviewed pair.

## 5. Status accounting

`duplicate_review_summary.json` records candidate counts and starts with
`reviewed_pair_count=0`, `pending_pair_count=70`,
`status=WAITING_FOR_DUPLICATE_REVIEW`. No reviewer decisions have been received
at preparation time. Update the summary only from submitted review files and
report counts by decision, unresolved items, reviewer completion, and adjudication
separately. A missing decision is pending, not a negative duplicate finding.

No canonical article or candidate-generation artifact is modified by this review
workflow.
