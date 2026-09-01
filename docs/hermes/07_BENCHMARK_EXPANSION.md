# Hermes prompt 07 — benchmark expansion and freeze preparation

Execute Stage 07 of the FDA portfolio refactor.

Read the governing PRD, shared contract, run status, accepted ten-case pilot and eval-engine documentation. Do not proceed unless the clinician has completed and signed off every gold field in the pilot and that gate is recorded in `RUN_STATUS.md`.

## Outcome

Expand the source pack toward a balanced 30–50-case benchmark and prepare it for clinician verification without manufacturing gold data.

## Required work

- Analyze the approved pilot's coverage across simple indications, multiple indications, population qualifiers, adjunctive versus monotherapy, complex wording, historical-label/version risks and similar psychiatric drugs.
- Define a documented sampling plan that closes the largest gaps and avoids over-representing easy or near-duplicate cases.
- Retrieve and freeze enough additional authoritative source cases to reach a total candidate set of 30–50, preserving the same provenance standard as the pilot.
- Include adversarially useful cases involving age restrictions, acute versus maintenance treatment, adjunctive use, formulations, multiple current labels, changed wording and plausible prior-knowledge contamination where supported by source text.
- Deduplicate candidates by source/version and substantive indication pattern.
- Generate clinician review worksheets with unresolved gold fields and explicit difficulty/coverage tags.
- Add dataset-balance and provenance validation reporting.
- Admit only already clinician-approved cases to the frozen dataset. Keep every new candidate in draft status until human review is recorded.

## Hard clinical gate

- Do not author, autocomplete or infer gold answers for new cases.
- Do not mark candidates clinician-reviewed.
- Do not fill gaps by generating synthetic FDA label text.
- Do not benchmark models on draft cases or report draft results as evidence.

## Success criteria

- The candidate pool contains 30–50 traceable, non-duplicative and deliberately varied cases.
- Coverage and remaining gaps are visible quantitatively and by clinical category.
- The frozen dataset contains only clinician-approved cases.
- The next human-review task is explicit and efficient.

End with gate verdict `BLOCKED — FULL CLINICIAN REVIEW REQUIRED` until every case intended for the frozen benchmark is verified. Do not start Stage 08.
