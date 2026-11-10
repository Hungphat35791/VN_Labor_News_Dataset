# Reviewer Calibration Package Validation Report

**Validation date:** 2026-11-09  
**Scope:** Review and packaging of 12 synthetic calibration scenarios. No production annotation was performed.

## Files created or updated

- Created `reviewer_calibration_exercises.md` — reviewer-facing prompts only, with neutral scenario IDs.
- Created `reviewer_calibration_answer_key.md` — separate coordinator-only reference, rationales, and support status for each scenario.
- Created `reviewer_1_calibration_sheet.csv` and `reviewer_2_calibration_sheet.csv` — blank response sheets with the requested six-column schema.
- Created this report.
- Updated `reviewer_calibration_guide.md` to remove its embedded answer-bearing scenarios and direct the coordinator to distribute only the exercise document and each reviewer's own sheet.

The CSV sheets contain scenario IDs and response fields only, using exactly:
`scenario_id,reviewer_id,relevance_manual,topic_manual,review_reason,review_date`.
Scenario text is maintained once in the shared exercise document and keyed by the same IDs in both sheets. The coordinator must provide the identical exercise document to both reviewers, but only each reviewer's own sheet.

## Scenario review

- Confirmed 12 unique scenario IDs, `CAL-01` through `CAL-12`, in the same order in the exercise document, answer key, and both reviewer sheets.
- The set covers recruitment/labor market, voluntary resignation, competing layoff/wage topics, involuntary job loss, workplace safety, union/dispute, recruitment fraud/exploitation, employment policy/training, a crime connected to a work task, a crime with occupation only incidental, possible future job creation, and incomplete/conflicting evidence.
- The scenarios are synthetic and are explicitly excluded from the 620-article master sample and production annotation.
- Answer-key statuses: **10 `SUPPORTED_BY_GUIDELINE`**, **1 `NEEDS_CLARIFICATION`** (CAL-03, no primary-topic tie-break), and **1 `NEEDS_ADJUDICATION`** (CAL-09, case-specific work nexus threshold).
- The existing general conflict in the official guideline about `Uncertain` versus difficulty choosing a primary topic remains unresolved; no new policy was approved.

## Reviewer-sheet and answer-leak checks

- Both sheets have exactly 12 rows and the same scenario IDs/order and byte-for-byte identical CSV content.
- Each sheet has exactly the six requested columns; all reviewer response fields are blank.
- The reviewer exercise contains no answer-key status, reference label/topic outcomes, or coordinator rationales.
- The previous answer-bearing scenarios were removed from `reviewer_calibration_guide.md`.
- The answer key is stored separately and marked coordinator-only. Repository file separation alone does not enforce access control; the coordinator must not distribute or expose the answer key until both independent submissions are received and locked.

## Protected-data verification

SHA-256 values before and after preparation matched:

| Protected file | SHA-256 |
|---|---|
| `5_process/config/labeling_guideline.md` | `49983C55F820CC092652FF33C7642717F3E2CD309745A0007969E97B6398A849` |
| `5_process/data/interim/relevance_review_sample.csv` | `8E09ACFFAAEE6C5E6883634A3ECC32D075FC45EA3D24F7C5AA6C66ECD889E85C` |
| `5_process/data/interim/relevance_review_batch_01.csv` | `CDC485EF53AC6F13023243C30CB21AC9A2157B10A6D8C7D7DD4E393634A192DF` |
| `5_process/data/interim/relevance_review_batch_02.csv` | `8120022D2AA665DE5EA5A5DA8CB51D92697EB7BF04C2B8849B47DF7924F1DBC3` |
| `5_process/data/interim/relevance_review_batch_03.csv` | `81541D8E12510AA1D4558062DE386AF996575AD370EE4B306C9D2FAAC806EC9D` |
| `5_process/data/interim/pilot_10/reviewer_1_sheet.csv` | `29F3F18DA8B51A57477B76B7924144000A2E0E3869180511D9E0F772C7CB1E69` |
| `5_process/data/interim/pilot_10/reviewer_2_sheet.csv` | `29F3F18DA8B51A57477B76B7924144000A2E0E3869180511D9E0F772C7CB1E69` |

No labels were added to the 620-item master sample, Batch 01–03, Pilot 10, or canonical data. The official guideline was not modified. No policy proposal was approved, and no commit or push was performed.

## Validation results

- Scenario count, uniqueness, and ordering: **PASS**
- Answer-key coverage and status counts: **PASS**
- Reviewer-sheet schema, blank response fields, and equality: **PASS**
- No answer-key content in reviewer-facing exercises: **PASS**
- Protected-file SHA-256 checks: **PASS**
- `git diff --check`: **PASS**

Reviewers should receive `reviewer_calibration_exercises.md` and only their own calibration sheet. Do not begin Batch 01 or enter any calibration response in production data as part of this package.
