# Relevance and Labor-Topic Taxonomy — P4.06

**Taxonomy version:** `1.0.0`  
**Status:** Specification for human annotation and future classifiers; not a deployed classifier.  
**Scope:** Classify whether an article is substantively relevant to labor and employment in the Vietnam news dataset, then assign zero or more supported labor-topic labels.  
**Data policy:** The authoritative CSV and all existing Process artifacts remain read-only. This taxonomy does not create gold labels or authorize edits to existing labels.

## 1. Purpose and relationship to existing labels

This taxonomy separates two questions:

1. **Relevance classification:** Is labor/employment in Vietnam a substantive subject of this article?
2. **Topic classification:** If it is relevant, which of the ten labor topics are substantively discussed?

Relevance is one mutually exclusive status: `RELEVANT`, `IRRELEVANT`, or `REVIEW_REQUIRED`. Topic classification is multi-label: a relevant article may receive multiple labels, but each label must be supported by meaningful article content. A mention, keyword match, or reference to a worker is not sufficient by itself.

The existing `labeling_guideline.md` uses `Relevant`, `Borderline`, `Not relevant`, and `Uncertain`, and asks reviewers to choose one primary A–L topic. Those labels and topic codes are not interchangeable with this taxonomy. For transition planning only:

| Existing manual value | P4.06 handling |
|---|---|
| `Relevant` | Re-evaluate the evidence under P4.06; do not copy automatically. |
| `Borderline` | Usually `REVIEW_REQUIRED` until direct relevance is established or rejected. |
| `Not relevant` | May map to `IRRELEVANT` only after checking against P4.06 scope. |
| `Uncertain` | `REVIEW_REQUIRED`. |

Existing A–L topics may provide context for a reviewer but must not be mechanically converted to the P4.06 multi-label set. The CSV's `relevance_status` value `relevant_auto` is an existing pipeline/schema convention, not a human-verified gold label; it must not be treated as evidence that an article is relevant. The schema validator currently expects this value for the main dataset, so P4.06 introduces no change to that field or validation rule.

## 2. Relevance statuses

| Status | Definition and decision rule | Example |
|---|---|---|
| `RELEVANT` | The article's main subject, or a substantial and clearly evidenced section, concerns employment, workers, working conditions, labor relations, or labor policy with a direct Vietnam connection. Assign one or more P4.06 topic labels. | A report on factory workers' unpaid wages in Bình Dương. |
| `IRRELEVANT` | Labor/employment is absent or incidental, or the apparent labor term has another meaning; the article does not materially concern the Vietnam labor domain. Return no final P4.06 topic labels. | A sports story says a football coach was “fired,” with no discussion of labor as a subject. |
| `REVIEW_REQUIRED` | The article is truncated, contradictory, too vague, context-dependent, or only indirectly related such that a reviewer cannot reliably decide relevance or topic from the available title/content. This is an abstention state, not a negative label. Do not present tentative topics as final labels. | A proposed industrial park is said to “bring opportunities” but the article gives no concrete hiring, workforce, or employment impact. |

Use the available title and article body as evidence. A Vietnamese location, source, or worker-related keyword alone does not establish relevance. For this dataset, a foreign labor story with no substantive connection to Vietnamese workers, employment, policy, or a clearly stated comparison relevant to Vietnam is normally `IRRELEVANT`; unclear cross-border impact requires `REVIEW_REQUIRED`.

Do not use `REVIEW_REQUIRED` merely because an article has several valid topics. Do not force a decision when the body is unavailable or evidence is insufficient. Never infer a legal violation from an allegation reported in the article.

## 3. Labor-topic labels

Apply labels to substantive topics, not isolated mentions. The examples below are illustrative scenarios, not claims about particular source articles.

| Label | Definition and include when | Exclude when | Illustrative Vietnam-news example |
|---|---|---|---|
| `EMPLOYMENT` | Hiring, job vacancies, labor supply/demand, job placement, workforce participation, job creation, or labor mobility is a material subject. | A passing reference to hiring with no actual employment information; unemployment or a specific policy is the only substantive subject (consider the more specific label). | A report compares seasonal recruitment demand and vacancies at industrial parks in Đồng Nai. |
| `UNEMPLOYMENT` | Unemployment, job loss, layoffs, reduced working hours causing loss of work/income, or return-to-work after job loss is substantively discussed. | A general job fair or hiring plan without unemployment or job-loss context; unemployment-benefit administration alone (use `UNEMPLOYMENT_INSURANCE`). | A factory closure leaves workers in Hải Phòng unemployed and the article reports their search for new work. |
| `WAGES` | Pay, minimum wage, wage arrears, salary scales, bonuses, overtime compensation, or other employment remuneration is a material subject. | General household income or prices without a labor-pay connection; an incidental salary figure. | Workers at a garment company seek payment of delayed wages and overtime. |
| `SOCIAL_INSURANCE` | Workers' social insurance (`BHXH`) participation, contributions, arrears, benefits, pension, maternity, sickness, or related worker coverage is discussed. Include health insurance only when the article materially addresses worker coverage or employment-linked benefits. | Public health insurance or healthcare with no worker/employment link; unemployment insurance as the only insurance subject (use `UNEMPLOYMENT_INSURANCE`). | A report explains workers' access to maternity benefits or employers' unpaid BHXH contributions. |
| `UNEMPLOYMENT_INSURANCE` | Unemployment insurance (`BHTN`) contributions, eligibility, benefits, claims, or administration is a material subject. | General unemployment without discussion of the insurance system (use `UNEMPLOYMENT`); unrelated insurance. | A provincial employment center reports BHTN claims and benefits for displaced workers. |
| `LABOR_RIGHTS` | A worker's rights, entitlements, representation, discrimination, coercion, or alleged/confirmed deprivation of rights is substantively examined. Preserve the article's distinction between allegation and established fact. | Do not add merely because any wage, contract, or safety article concerns workers: use this label only when rights/entitlement is itself a material framing or issue. | Workers allege retaliation for organizing; the article examines their rights and the response from relevant parties. |
| `LABOR_CONTRACT` | Employment contracts, contract terms, contract type, signing, renewal, termination, or disputes about the employment agreement are central. | Commercial/service contracts unrelated to employment; an employment relationship mentioned without contract substance. | A report discusses fixed-term employment contracts and conversion to indefinite-term contracts at a Vietnamese enterprise. |
| `LABOR_DISPUTE` | Collective or individual conflict between workers/representatives and an employer, including strikes, negotiations, grievances, or dispute resolution, is a material subject. | A report that only states a labor rule or worker condition without an actual conflict; a strike unrelated to employment. | Workers at a factory stop work over meal allowances and negotiations with management. |
| `OCCUPATIONAL_SAFETY` | Workplace hazards, occupational disease, workplace injury/death, safety procedures, or employer safety obligations are materially discussed. | General public safety or an incident outside work with no occupational connection. | A construction-site accident prompts reporting on worker protection and safety inspection. |
| `LABOR_POLICY` | A law, government program, regulation, public intervention, or policy proposal whose primary subject or substantial effect concerns labor/employment is analyzed. | A law or government announcement with no material labor dimension; routine reporting of an individual case where policy is not discussed. | A report explains a proposed Vietnamese minimum-wage adjustment or a national job-transition program. |

## 4. Multi-label rules and overlap

1. Assign every label independently against its definition. Multiple labels are appropriate only when each topic has meaningful evidence and is not merely implied by another label.
2. There is no required “primary” label in P4.06. Store the selected labels as a set; do not force a hierarchy.
3. Use specific labels for distinct substantive aspects. For example, an article about layoffs and BHTN claims may receive `UNEMPLOYMENT` and `UNEMPLOYMENT_INSURANCE`; an article about unpaid wages in a strike may receive `WAGES` and `LABOR_DISPUTE`.
4. Do not automatically add `LABOR_RIGHTS` to every article labeled `WAGES`, `LABOR_CONTRACT`, `SOCIAL_INSURANCE`, or `OCCUPATIONAL_SAFETY`. Add it only when rights or entitlements are themselves discussed.
5. Do not automatically add `LABOR_POLICY` because a government agency or law is mentioned. The policy must be a substantive object of the article.
6. Do not label two related concepts just because one is background context. If only one topic has material evidence, assign only that one. If it is unclear whether a secondary topic is material, send the case to review rather than over-label.
7. For `IRRELEVANT`, the final topic-label set is empty. For `REVIEW_REQUIRED`, final labels are withheld; any machine suggestions must be stored separately as unconfirmed candidates.

## 5. Mention of workers versus labor relevance

An article is not relevant merely because it:

- mentions a worker, employee, company, factory, salary, hiring, “sa thải,” or another labor-associated word once;
- quotes an official or worker without discussing labor, employment, or working conditions;
- reports a business, economic, sports, political, or public-safety story whose labor reference is incidental;
- shares a location, publisher, or keyword with labor news.

Consider the full context and the article's central question. A report on a factory fire may be `OCCUPATIONAL_SAFETY` if worker exposure and workplace safety are a substantial focus; it may be `IRRELEVANT` if it is solely about property damage and workers are only incidental. If the available text does not resolve that distinction, use `REVIEW_REQUIRED`.

## 6. Review workflow for ambiguous or incomplete articles

1. Read the title and enough of the article body to identify its subject, affected people, and Vietnam connection. Do not decide from keywords, current `topic_primary`, `topic_secondary`, `relevance_score`, or `relevance_status`.
2. Record `REVIEW_REQUIRED` when the body is missing/truncated, evidence conflicts, relevance is only speculative, or a label boundary cannot be resolved.
3. Record the precise uncertainty and the evidence needed (for example, full article text, whether a benefit is BHTN or BHXH, or whether the reported event occurred in a workplace).
4. A human reviewer may resolve the case to `RELEVANT` with one or more labels, or `IRRELEVANT`, and must record reviewer identity, review time, and reason. Preserve the initial machine result and review history; do not silently overwrite it.
5. Keep allegations attributed to their source. Classification is not a legal finding, a quality judgment, sentiment, or duplicate decision.

## 7. Result metadata contract

Each result should be traceable and reproducible. Recommended logical fields:

| Field | Requirement | Meaning |
|---|---|---|
| `article_id` | Required | Stable source record identifier. |
| `relevance_status` | Required | Exactly `RELEVANT`, `IRRELEVANT`, or `REVIEW_REQUIRED`. |
| `topic_labels` | Required | Set/list of zero or more of the ten labels; empty for `IRRELEVANT` and for unresolved `REVIEW_REQUIRED`. |
| `reason` | Required | Concise evidence-based rationale; for review, state the unresolved question. Do not copy full article text. |
| `method` | Required | Actual decision method, e.g. human annotation or a named rule/model workflow; do not claim a method that was not used. |
| `taxonomy_version` | Required | `1.0.0` for this specification. |
| `classifier_version` | Required | Version of the actual classifier, or an explicit value such as `NOT_APPLICABLE_HUMAN` for manual-only decisions. Never imply a classifier was run when it was not. |
| `review_status` | Required | Human-review state, e.g. `REVIEW_REQUIRED`, `REVIEWED`, or `NOT_REVIEWED`, kept distinct from relevance. |
| `reviewer_id`, `reviewed_at` | Required for a human decision | Reviewer identity and timestamp; do not invent these values. |
| `candidate_topic_labels` | Optional | Unconfirmed suggestions for `REVIEW_REQUIRED`; must not be represented as final `topic_labels`. |

This contract specifies provenance but does not implement a classifier, alter the source schema, or prescribe a particular storage artifact.

## 8. Existing manual-review evidence and limitations

`label_quality.md` reports a 57-article manual sample: 56 records stratified using automatic `topic_primary` plus one prioritized case. It reports 45 `Relevant`, 10 `Borderline`, and 2 `Not relevant`, reviewed by one reviewer. This sample is useful as a limited review artifact, not as gold labels for the full dataset:

- It is stratified and includes a priority case, not a random representative sample; do not extrapolate error rates or accuracy to all 12,784 articles.
- The reviewer count is one; independent multi-annotator agreement has not been measured.
- The sample uses the prior one-primary-topic A–L scheme and four relevance values, not the P4.06 multi-label taxonomy. Do not relabel or score P4.06 from those counts without a fresh, documented annotation protocol.
- `label_quality.md` also contains a limitations statement saying no reviewer confirmation is available, which conflicts with its earlier statement that 57/57 rows were reviewed and names a reviewer/date. Reconcile that report before using the sample for any evaluation claim.
- Existing `relevance_status = relevant_auto` is not a gold label. No accuracy, precision, recall, F-score, or inter-annotator agreement is asserted by this taxonomy.

To establish an evaluation set, define an independent annotation protocol, double-annotate an appropriate sample, adjudicate disagreements, and retain sampling and reviewer provenance. Until then, these labels are a policy specification only.
