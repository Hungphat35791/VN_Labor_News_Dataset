# Duplicate Taxonomy — P4.01

**Taxonomy version:** `1.0.0`  
**Status:** Specification for review; does not change or execute any detector.  
**Scope:** Classify duplicate relationships and define metadata for review candidates and groups.  
**Data policy:** The authoritative Collecting CSV and existing Process artifacts are read-only.

## 1. Purpose and decision principles

This taxonomy is for recording evidence and guiding human review. A detector produces a
candidate, not a deletion decision. No process using this taxonomy may automatically
delete, edit, overwrite, or merge an article.

Apply these principles:

1. Compare article identity and content evidence, not just shared topic, keywords, entities,
   source, or event.
2. Keep the original article fields and URLs unchanged. Store comparison keys, hashes,
   scores, decisions, and lineage as separate derived metadata.
3. Keep the duplicate type and detection method with every candidate. A similarity score
   alone is not a duplicate verdict.
4. Do not infer a version relationship from event similarity or publication dates alone.
5. Keep candidate pairs distinct from confirmed relationships. Do not form a confirmed
   group by transitively chaining unreviewed or weak candidate pairs.

## 2. Duplicate types

### 2.1 URL Duplicate

**Definition:** Two records point to the same article resource, or to URL variants that
resolve to the same article resource under an explicitly documented normalization rule.

**Identification conditions:**

- The original `source_url` values are retained.
- A comparison key may normalize URL scheme/host casing, known host aliases, default
  ports, fragments, trailing slashes, and explicitly recognized tracking parameters.
- A URL-key match is a candidate. Confirm identity using available evidence such as final
  redirect URL, canonical URL, source, title, and content. Do not treat a shared domain,
  path prefix, or query parameter alone as proof.
- Do not remove query parameters unless their semantics are known to be tracking-only.

**Example:** The same article URL appears once with `www` and a tracking parameter and
once without them; both resolve to the same article and have matching article content.

**Not a duplicate:** Two different article paths on the same publisher domain; two URLs
that happen to share a slug but identify separately published articles; or two articles
with similar titles and the same event but different content.

**Detection method:** Parse and validate the URL, derive a versioned comparison key, and
compare candidate keys. Where available, corroborate with redirect/canonical URL evidence.
Record the normalization method and key; never replace the source URL.

**Proposed handling:** Mark as `URL_DUPLICATE_CANDIDATE` and review. If confirmed, retain
both source records and record their relationship. Do not remove a record solely because
its normalized URL matches another.

### 2.2 Exact Content Duplicate

**Definition:** Two records contain the same complete article text, apart from explicitly
documented, non-semantic canonicalization used for comparison. This is stronger evidence
than a matching title, URL, or event.

**Identification conditions:**

- Compare the complete available `content`, not a short excerpt, title, or selected
  paragraph.
- Preserve a hash of the unmodified source text. If a comparison form is used, document
  its normalization (at minimum Unicode NFC and consistent line endings); do not silently
  remove sentences, boilerplate, numbers, or punctuation.
- A hash match is a candidate and should be verified by comparing the corresponding
  comparison text to guard against implementation errors or hash collisions.
- Store whether equality was raw-text equality or equality after the named canonicalization.

**Example:** Two publisher records contain the same full article body, with only line
ending differences after CSV decoding.

**Not a duplicate:** The same headline with different article bodies; a shared quotation,
press release excerpt, or boilerplate paragraph; or two reports of the same event that
contain independently written material.

**Detection method:** Calculate a cryptographic digest (for example SHA-256) over the
complete source text and, if needed, over a separately named canonical comparison text.
Use exact equality verification after matching digests.

**Proposed handling:** Mark as `EXACT_CONTENT_CANDIDATE` and review source, date, and
context. Retain all records and their provenance even when exact equality is confirmed.

### 2.3 Near Duplicate

**Definition:** Two records have substantial article-level textual overlap but are not
exact content duplicates. This category is for candidate review, not automatic
deduplication.

**Identification conditions:**

- Similarity must be based on substantial portions of the article text, not only title,
  common phrases, shared quotations, or a generic boilerplate block.
- The candidate should have enough usable text for a meaningful comparison. Very short,
  truncated, or mostly boilerplate records should be flagged as insufficient evidence.
- Record the compared text fields, preprocessing, algorithm, score, threshold, and relevant
  evidence. Thresholds must be empirically reviewed; no score alone confirms duplication.
- Similarity must be assessed against the possibility of independently written coverage
  of the same event.

**Example:** A publisher republishes most of another article with light sentence edits,
while the two full texts are not equal.

**Not a duplicate:** Two articles cover the same strike, policy announcement, or workplace
incident but have different reporting, interviews, facts, analysis, or structure. A
matching headline or shared facts alone is insufficient.

**Detection method:** Candidate generation may use TF-IDF with cosine similarity,
token/shingle Jaccard or MinHash, SimHash, or fuzzy matching. Use title similarity only
as a screening signal unless corroborated by article-body evidence. Human review confirms
or rejects the relationship.

**Proposed handling:** Mark as `NEAR_DUPLICATE_CANDIDATE`; prioritize for human review.
If confirmed, retain the articles and record the reason and relationship. Do not select a
“winner” or remove either article automatically.

### 2.4 Version Duplicate

**Definition:** Multiple records represent versions or snapshots of the same underlying
article/document, where one version was updated, corrected, or expanded. The relationship
is version lineage, not merely textual similarity.

**Identification conditions:**

- Require direct lineage evidence, such as a stable source document identifier, explicit
  “updated/corrected” metadata, a documented revision history, or a reliable canonical
  article identity with version timestamps.
- Content may differ between versions. Record the observed version ordering and evidence.
- A shared URL or high text similarity may support the finding but does not, by itself,
  establish a version relationship.
- The current dataset schema does not expose a dedicated document-version identifier;
  where direct lineage evidence is unavailable, use `REVIEW_REQUIRED` rather than infer
  versioning.

**Example:** The publisher updates one article at the same canonical article identity,
and two captured snapshots have distinct update timestamps and differing text.

**Not a duplicate:** Two publishers independently report the same event; a later article
that adds new reporting; or two similar articles without evidence that one is a revision
of the other.

**Detection method:** Prefer source-provided document/version identifiers, revision
history, canonical identity, and update timestamps. Compare text and timestamps as
supporting evidence, not as sole proof.

**Proposed handling:** Record a version family and each version's lineage/order. Preserve
all snapshots and their timestamps. A downstream consumer may choose a version for a
specific analysis only through an explicit, documented, reversible selection; this
taxonomy does not authorize deletion or replacement.

## 3. Distinctions for difficult cases

| Case | Classification |
|---|---|
| Complete content is identical (or identical after the documented non-semantic text canonicalization) | Exact content duplicate candidate |
| Article bodies substantially overlap but contain meaningful edits or omissions | Near duplicate candidate |
| Articles describe the same event but have distinct reporting or independently written content | Not a duplicate on event evidence alone; retain both |
| A single publisher article has multiple captured revisions with direct lineage evidence | Version duplicate relationship; preserve every version |
| Same URL key but no corroborating evidence that it is the same resource | URL duplicate candidate; review required |
| Similar titles only, or a shared boilerplate/quotation only | Insufficient evidence; do not confirm as duplicate |

Duplicate type is not an article relevance or quality label. Confirming a duplicate
relationship does not imply that either article is irrelevant, invalid, or safe to remove.

## 4. Candidate metadata

Represent each candidate as one relationship between two article records. The following
logical fields are recommended; implementations may map them to a table or CSV after the
integration contract is approved.

| Field | Requirement | Meaning |
|---|---|---|
| `candidate_id` | Required | Stable identifier for this candidate relationship |
| `article_id_1`, `article_id_2` | Required | Source record identifiers in stable sorted order |
| `duplicate_type` | Required | `URL_DUPLICATE`, `EXACT_CONTENT_DUPLICATE`, `NEAR_DUPLICATE`, or `VERSION_DUPLICATE` |
| `candidate_status` | Required | `CANDIDATE`, `REVIEW_REQUIRED`, `CONFIRMED_DUPLICATE`, `CONFIRMED_NOT_DUPLICATE`, or `VERSION_RELATION_CONFIRMED` |
| `evidence` | Required | Concise, content-free description of evidence; do not copy article text |
| `method` | Required | Detector/verification method identifier |
| `method_version` | Required | Version of the detector or comparison procedure |
| `taxonomy_version` | Required | Taxonomy version applied; initially `1.0.0` |
| `score` | Conditional | Similarity score, if the method produces one |
| `threshold` | Conditional | Threshold/configuration used to generate a scored candidate |
| `comparison_fields` | Required | Fields compared, such as `source_url`, `title`, or `content` |
| `normalization` | Conditional | Named normalization and version, when comparison uses a transformed value |
| `reviewer_id`, `reviewed_at` | Required for a human decision | Human reviewer and decision timestamp |
| `decision_reason` | Required for a human decision | Rationale, especially for same-event or version decisions |
| `proposed_action` | Required | Recommendation only; must not trigger mutation |
| `created_at` | Required | Candidate creation timestamp |
| `input_fingerprint` | Recommended | Input snapshot/checksum used for reproducibility |

Candidate records should not embed article full text, title, or URL unless a separate,
approved access-controlled review artifact requires them. Use `article_id` to retrieve
source fields.

## 5. Duplicate group metadata

A group is a set of related records for review and lineage. It is not a command to collapse
records. A group may contain only one confirmed relationship class; do not mix exact,
near, URL, and version relationships under one undifferentiated label.

| Field | Requirement | Meaning |
|---|---|---|
| `duplicate_group_id` | Required | Stable group identifier |
| `group_type` | Required | One of the four taxonomy types, or an explicitly named `MIXED_REVIEW_GROUP` when distinct edges are retained separately |
| `group_status` | Required | `CANDIDATE_GROUP`, `REVIEW_REQUIRED`, `CONFIRMED_GROUP`, or `REJECTED_GROUP` |
| `member_article_ids` | Required | Stable list of member `article_id` values |
| `candidate_ids` | Required | Candidate relationships supporting membership |
| `group_evidence` | Required | Short, content-free summary of why the records are grouped |
| `method`, `method_version` | Required | Provenance of candidate generation/group construction |
| `taxonomy_version` | Required | Taxonomy version applied |
| `reviewer_id`, `reviewed_at`, `decision_reason` | Required for a human decision | Review provenance and rationale |
| `proposed_action` | Required | Recommendation only; no record mutation |
| `created_at` | Required | Group creation timestamp |

For version groups, implementations should additionally preserve `document_family_id`,
version identifiers when available, and an explicit version order or timestamp per member.
Do not infer order from group membership order.

Group construction must avoid unsupported transitive conclusions: if A is a candidate
with B and B is a candidate with C, do not mark A, B, and C as one confirmed duplicate
group unless evidence supports each relationship or review confirms the group.

## 6. Review outcomes and handling

Use the candidate/group status to distinguish machine-generated hypotheses from human
decisions. `CONFIRMED_NOT_DUPLICATE` records a reviewed false positive and should remain
available for audit. `VERSION_RELATION_CONFIRMED` confirms lineage, not that any version
can be discarded.

Recommended actions are advisory labels such as `REVIEW`, `KEEP_BOTH`, `PRESERVE_VERSIONS`,
or `NO_CHANGE`. Any future proposal to exclude an article from a specific analytical
view must be separate, reversible, attributable to a human decision, and must preserve
the authoritative source and lineage. No action in this taxonomy authorizes deletion,
editing, or merging.

## 7. Relationship to existing Process outputs

The existing metadata audit already creates normalized URL/title keys, content hashes,
TF-IDF near-content candidates, and `dup_cluster_id` values in derived metadata. Those
outputs are audit evidence, not confirmed duplicate decisions. Existing split leakage
checks also produce title-based candidates, not duplicate verdicts. This taxonomy does
not modify those detectors, their outputs, the Collecting CSV, or any existing Process
artifact.

Before a future detector or integration task uses these fields, the project should agree
on the data contract, URL normalization semantics, exact-content normalization, similarity
threshold calibration, group ID strategy, and human decision authority.
