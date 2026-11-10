# Reviewer Calibration Guide — VN Labor News Dataset

**Guide version:** `1.0.0`
**Policy basis:** `5_process/config/labeling_guideline.md` as currently written
**Status:** Reviewer aid only. This guide does not amend the official guideline, approve proposed policy changes, create labels, or authorize changes to source data.

Use the official guideline if this guide and the guideline appear to differ. The examples below are synthetic training scenarios, not ground-truth labels for any dataset record.

## 1. Purpose and scope

This guide helps reviewers apply the current four-value `relevance_manual` field and the single-primary-topic A–L `topic_manual` field consistently to news articles about labor and employment in Vietnam. Reviewers must base decisions on the article's title and full available content, not on keyword matches or automated suggestions.

The current manual guideline is not the P4.06 multi-label taxonomy. Do not copy or convert P4.06 statuses or topic labels into the manual-review fields. The 620-article sample is an audit sample, not a representative sample of the dataset's natural class distribution.

## 1.1 Submission lock and coordinator scoring

The coordinator must not score calibration answers until both sheets are complete,
valid, independently submitted, and locked. The lock is recorded separately in the
coordinator-only `reports/reviewer_calibration_lock.json`; it is never included in
reviewer packets. The manifest contains a `reviewers` object with `reviewer_1` and
`reviewer_2` entries. Each entry must include `locked: true`, the actual
`reviewer_id`, `locked_by`, ISO-8601 `locked_at`, and the exact submitted
`sheet_sha256`. The validator compares the manifest hashes to the current files.
Any subsequent edit makes the lock stale and prevents answer-key scoring until the
coordinator confirms and records a new lock. Do not create the manifest until both
independent submissions are actually received and frozen.

## 2. Review one article

1. Read the full title and available article content. Identify the article's central subject, the people affected, the employment or labor connection, and the Vietnam context.
2. Decide whether labor or employment is a substantive subject. Do not decide from a keyword, an automatic field, or a proposed label.
3. Select exactly one `relevance_manual` value from Section 3.
4. For `Relevant` or `Borderline`, select one primary topic A–L from Section 4. For `Not relevant` or `Uncertain`, leave `topic_manual` blank.
5. Write an evidence-based `review_reason`, including the article detail that supports the relevance and topic decision. If another topic competes for the primary position, name it and explain the choice.
6. Enter the actual reviewer ID and the actual date the review was completed. Do not invent either value.
7. Check the record against Section 10. Do not mark a record complete while required fields are missing or invalid.

Make the relevance decision from the article before consulting any allowed supplemental material. Never treat AI proposals, automatic labels, audit suggestions, or another reviewer's result as the answer. Where a workflow permits a later comparison, it must not replace the reviewer's own evidence-based decision.

## 3. Relevance labels

| `relevance_manual` | Apply when | Do not use it to mean |
|---|---|---|
| `Relevant` | The article's main focus directly concerns jobs, the labor market, workers, labor relations, working conditions or rights, or labor policy in Vietnam. | A match to a labor keyword without substantive labor content. |
| `Borderline` | The article has a meaningful but indirect or secondary connection to labor or employment. The guideline's example is a project or industrial park said to potentially create jobs without concrete hiring or actual workforce information. | Any article that merely mentions a worker, employer, salary, or workplace. |
| `Not relevant` | There is enough information to determine that the article does not substantially concern labor or employment in the project scope; a labor-related word may be incidental or used in another sense. | A conclusion based only on missing or truncated article content. |
| `Uncertain` | Available information is insufficient or contradictory for deciding whether the article is in scope. State what evidence is missing or conflicting in `review_reason`. | A confidence score, a way to avoid a difficult decision, or an automatic substitute for a difficult topic choice. The official guideline also contains a conflicting instruction about topic uncertainty; see Section 8. |

Use the article's subject and evidence, not the presence of a topic keyword. Do not infer legal wrongdoing from an allegation or infer sentiment from a relevance/topic decision.

## 4. Single primary topic A–L

The manual guideline requires one primary topic for `Relevant` and `Borderline` articles. It is not a multi-label task. If several topics have meaningful evidence, select the one that best reflects the article's central subject and explain a competing topic in `review_reason`. The guideline does not provide a quantitative tie-breaker; unresolved ties are flagged in Section 8 rather than settled by an invented rule.

| Code and official name | In scope / recognition cues | Common confusion and distinction | Primary-topic principle | Synthetic illustration |
|---|---|---|---|---|
| **A — Thị trường lao động Việt Nam** | Labor supply or demand, recruitment, labor shortages, job creation, job placement, or worker mobility. | Distinguish from **B** when the core issue is unemployment/job loss, and **H** when an employment policy or training program is the focus. | Choose A when hiring, workforce supply/demand, or movement between jobs is the main subject. | A report centers on employers' unfilled vacancies and recruitment demand in several provinces. |
| **B — Thất nghiệp, mất việc, cắt giảm nhân sự** | Unemployment, involuntary job loss, reduced work hours, or workforce cuts. | Distinguish from **D**: voluntary resignation, job change, contract termination, or retirement in an employment relationship is D; involuntary job loss or layoffs are B. | Choose B when loss of work or workforce reduction is the central event. | A factory closure leaves a group of workers without jobs. |
| **C — Tiền lương, bảo hiểm, quyền lợi** | Wages, bonuses, social/health/unemployment insurance, employment-linked rights, benefits, or allowances. | Distinguish from **H** when the subject is a broader employment/social-support policy, and from **D** when contract termination is central. A one-off gift unrelated to an employment entitlement is not automatically C. | Choose C when pay, insurance, or an employment-linked entitlement is the article's main subject. | Workers seek payment of overdue wages and the article focuses on the unpaid amounts. |
| **D — Hợp đồng lao động, nghỉ việc, sa thải** | Employment contracts, ending employment, resignation, dismissal, discipline, or retirement within an employment relationship. | Distinguish from **B** by whether the core event is voluntary/individual termination or involuntary unemployment/downsizing. | Choose D when the contract or termination relationship itself is central, rather than a broader labor-market outcome. | An article examines a dispute about the terms for ending an employment contract. |
| **E — Điều kiện làm việc, an toàn lao động** | Working hours, overtime, safety, workplace accidents, work environment, or facilities tied to work. | Do not infer E just because a crime victim has a worker's occupation. The guideline calls for a direct, significant work/task connection; a single incident without discussion of safety conditions or measures is generally at most Borderline. | Choose E when conditions or occupational safety are the main labor issue. | A report focuses on hazards and safety inspections at an active construction site. |
| **F — Công đoàn, đình công, tranh chấp lao động** | Union representation, collective bargaining, strikes, or labor disputes. | A person's union title or a passing union quotation is not enough; the representation, negotiation, strike, or dispute must be substantive. | Choose F when the actual labor dispute or representation activity is the central subject. | Workers stop work while their union negotiates with management over a workplace issue. |
| **G — Nhóm lao động dễ bị ảnh hưởng** | A specific worker group and its distinctive labor-related hardship or circumstances are the focus. | Do not assign G merely because an affected person belongs to a worker group; establish that the group and labor-related circumstances are substantive. | Choose G when the group's distinct labor vulnerability or circumstances are more central than a specific wage, safety, or policy topic. | An article centers on barriers faced by workers with disabilities in retaining employment. |
| **H — Chính sách việc làm, đào tạo nghề, an sinh xã hội** | Employment policy, vocational training, reskilling, worker support, or social protection policy. | Distinguish from **C** when a specific wage/insurance entitlement is central. A one-off community donation is not automatically a policy or employment benefit. | Choose H when a program, policy, training, or social-protection measure is the central subject. | A report explains a government vocational retraining program for displaced workers. |
| **I — Lừa đảo tuyển dụng, bóc lột lao động** | Recruitment fraud, forced/coerced labor, exploitation, or trafficking connected with labor. | A scam that impersonates a worker to defraud customers is not necessarily recruitment fraud against workers. | Choose I when deception or exploitation in obtaining or compelling labor is central. | People are deceived by job offers and then forced to work under coercive conditions. |
| **J — Kinh tế và yếu tố tác động đến việc làm** | Economic, industry, business, or technology factors that materially affect employment or labor. | A general business/economic report is not enough if labor effects are only incidental; distinguish from A when actual hiring/supply-demand is central. | Choose J when an economic or industry change and its employment effects are the main focus. | A report examines how factory automation is changing staffing needs in an industry. |
| **K — Pháp luật lao động và thực thi** | Labor-law rules, labor inspection, enforcement, penalties, or litigation concerning labor law. | A criminal prosecution or a rule in another legal domain is not K solely because workers are involved. | Choose K when labor law or its enforcement is the central subject. | An article examines enforcement proceedings over an employer's alleged violation of labor regulations. |
| **L — Tâm lý người lao động, chất lượng việc làm** | Workers' mental health, experience, satisfaction, burnout, or job quality. | Distinguish from **E** when physical conditions/safety are central, or **C** when pay/benefits are central. | Choose L when worker experience or psychological/job-quality outcomes are the main subject. | A report centers on workers' accounts of burnout and work-life strain. |

These illustrations explain the current categories; they do not establish additional thresholds or policy. When the main topic cannot be selected from the current wording, record the competing topics and request clarification/adjudication instead of inventing a ranking rule.

## 5. Writing `review_reason`

For each article, write a concise explanation in the reviewer's own words:

- Identify the concrete fact, event, or statement in the article that supports the relevance decision.
- Explain why the article is directly relevant, meaningfully but indirectly related, outside scope, or unresolved.
- For a relevant/borderline article, explain why the selected primary topic best represents the focus; mention a competing topic when material.
- For `Uncertain`, identify the missing or contradictory information that prevents a scope decision.
- Attribute allegations to the source when describing them. Do not turn a reported allegation into a finding of fact or legal conclusion.
- Do not copy an AI proposal, an automatic label, or a headline in place of reasoning; do not write a generic reason such as “related to labor.”

## 6. `reviewer_id` and `review_date`

- `reviewer_id` must identify the real person who made the decision, using the group's actual agreed identifier. Never use an AI/account/device name or invent a code.
- The current guideline does not specify a naming format or an authoritative reviewer registry. If the team has not agreed on a code or cannot verify that it belongs to the reviewer, mark the record as requiring confirmation and ask the coordinator; do not create a convention in this guide.
- `review_date` is the actual date the reviewer completed that article's review, in `YYYY-MM-DD` format. Do not substitute the system date, file timestamp, start date, or script execution date.
- These values must not be prefilled or inferred.

## 7. `review_status` is not a relevance label

`review_status` records workflow progress; `relevance_manual` records the reviewer's substantive decision. They answer different questions and must not be substituted for one another.

| `review_status` | Current guideline meaning |
|---|---|
| `PENDING` | Review has not started. |
| `IN_PROGRESS` | Review is underway. |
| `COMPLETED` | Review is finished and required fields have been checked. |
| `NEEDS_ADJUDICATION` | The case needs adjudication because of disagreement or an unresolved case. |

Do not set `COMPLETED` merely because a relevance value was chosen. Check the required fields and the topic rule first. Do not use `Uncertain` as a workflow state or `NEEDS_ADJUDICATION` as a relevance label.

## 8. Difficult, incomplete, or unresolved cases

1. Re-read the full available title/content and identify the specific evidence and the unresolved question. Do not use keywords or automated labels to fill a gap.
2. If the text is missing, truncated, or contradictory in a way that prevents deciding whether the article is in scope, use `Uncertain`, leave the topic blank, and explain the missing/conflicting evidence.
3. If relevance is clear but multiple topics compete, the guideline says to choose the primary topic and mention the competing topic in the reason. If the primary topic cannot be distinguished, the guideline also says to use `Uncertain`, while its definition says not to use `Uncertain` merely because topic classification is difficult. This is an unresolved conflict in the official guideline: mark **`NEEDS_CLARIFICATION`** in the review note/reason and request a responsible human decision. Do not resolve the conflict by treating this guide or an unapproved proposal as policy.
4. The guideline does not define a quantitative rule for deciding which of two equally central A–L topics is primary. If the article and current distinctions do not resolve it, record the evidence and both candidate topics and request adjudication/clarification.
5. Preserve the reviewer's own decision and reason. Do not force agreement, revise another reviewer's choice, or convert an AI/audit proposal into an answer.
6. Use `review_status=NEEDS_ADJUDICATION` only when the workflow calls for a human adjudication of an actual disagreement or unresolved case. If the issue is a policy interpretation not resolved by the guideline, keep it explicit and ask the responsible project owner; do not mark it as resolved.

### Known guideline questions for the project owner

- **Uncertain vs. difficult topic:** The article procedure says to choose `Uncertain` if the primary topic cannot be distinguished, but the label definition says not to use `Uncertain` only because topic classification is difficult.
- **Borderline threshold:** “Meaningful but indirect” is not quantified; the guideline gives examples and cautions against incidental mentions but no universal threshold.
- **Primary-topic tie-break:** The reviewer must choose one primary topic but no formal hierarchy or tie-break rule is defined when topics are equally central.
- **Reviewer ID convention:** The identifier must be real, but the guideline does not specify a team registry or format.

These items are **NEEDS_CLARIFICATION**, not approved changes. The policy discussion/voting documents are not themselves the official guideline, and an unfilled ballot is not approval.

## 9. Common reviewer errors

- Deciding from a keyword, title alone, automatic field, or proposed label instead of reading the article.
- Treating any mention of a worker, company, salary, dismissal, or workplace as sufficient for relevance.
- Treating two articles about the same event as equivalent evidence or copying another reviewer's decision.
- Confusing involuntary unemployment/layoffs (**B**) with voluntary resignation or employment termination (**D**).
- Treating a worker's occupation or the place where a crime happened as sufficient evidence for occupational safety (**E**).
- Selecting a topic because it appears in the article rather than because it is the main subject.
- Filling multiple topics in a field that requires one primary A–L topic.
- Filling a topic for `Not relevant` or `Uncertain`, or omitting the topic for `Relevant`/`Borderline`.
- Using `Uncertain` to avoid a hard topic choice without noting the guideline conflict.
- Leaving out article-specific evidence, making an unsupported legal conclusion, or copying AI text into `review_reason`.
- Inventing reviewer identity/date, using the current date without confirmation, or marking `COMPLETED` before required fields are valid.

## 10. Before completing a record

- [ ] I read the full available title and content.
- [ ] I selected exactly one allowed relevance label based on article evidence.
- [ ] I selected one primary A–L topic only if the relevance is `Relevant` or `Borderline`; otherwise the topic is blank.
- [ ] I considered the main subject and relevant topic boundaries, not just keywords.
- [ ] My `review_reason` cites specific article evidence and explains the decision.
- [ ] I recorded a real, group-recognized `reviewer_id`; I did not invent or infer it.
- [ ] I recorded the actual completion date in `YYYY-MM-DD`; I did not infer it from metadata.
- [ ] I documented any missing evidence, competing topic, guideline conflict, or adjudication need without resolving it by assumption.
- [ ] I did not use an AI proposal, automatic label, another reviewer's result, or unapproved policy proposal as ground truth.
- [ ] I checked that `review_status` reflects workflow state and is not being used as a relevance label.
- [ ] I will mark `COMPLETED` only after all required values and label/topic conditions are valid.

## 11. Calibration exercise access

The 12 synthetic practice prompts are provided separately in `reviewer_calibration_exercises.md`. Reviewers should receive only that exercise document and their own blank calibration sheet. Reference outcomes are kept in a separate coordinator-only file and must not be shared until both reviewers have submitted and locked independent responses. The exercises are not part of the 620-article sample and must not be copied into production annotation data.

## 12. Sources and authority boundaries

- **Authoritative manual policy:** `5_process/config/labeling_guideline.md`.
- **Workflow context:** `5_process/data/interim/pilot_10/pilot_10_protocol.md`, `5_process/reports/pilot_10_reviewer_distribution_guide.md`, `5_process/reports/pilot_10_completion_checklist.md`, and `5_process/reports/pilot_10_agreement_workflow_design.md`. These support independent review, provenance, and preservation of disagreements; they do not amend the label definitions.
- **Different taxonomy:** `5_process/config/relevance_taxonomy.md` is a P4.06 taxonomy with different statuses and multi-label topics. It explicitly says it is not interchangeable with the current four manual relevance labels and single-primary A–L scheme; do not use it to decide these fields.
- **Unrelated taxonomy:** `5_process/config/duplicate_taxonomy.md` concerns duplicate relationships and does not define relevance or A–L topics.
- **Unapproved policy material:** `labeling_policy_clarification_proposal.md` and `labeling_policy_review_assessment.md` are proposals/analysis, not approved policy. The group-voting record is a blank form, not evidence of approval.
