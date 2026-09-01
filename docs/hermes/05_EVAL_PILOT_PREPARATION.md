# Hermes prompt 05 — evaluation pilot preparation

Execute Stage 05 of the FDA portfolio refactor.

Read the governing PRD, shared contract, run status and accepted AI contract. Confirm Stages 00–04 are accepted before editing.

## Outcome

Prepare a source-grounded ten-case evaluation pilot and a clinician-review workflow. This stage ends before any case becomes gold standard.

## Required work

- Create the planned `backend/evals/` structure with clear separation between draft cases, frozen datasets, schemas, scorers, runners and reports.
- Define a versioned case schema covering case ID, drug, frozen source metadata, source text, difficulty class, clinician-authored expected fields, review state and notes.
- Define a clinician rubric for factuality, completeness, unsupported claims, population fidelity, therapeutic-context fidelity, source/version fidelity, schema compliance and failure severity.
- Include concrete rubric anchors for pass, minor error, major error and clinically important failure, while marking the rubric as requiring clinician approval.
- Select ten candidate cases across the PRD strata, with an intentional psychiatry emphasis and meaningful variety rather than ten easy labels.
- Retrieve/freeze the relevant authoritative OpenFDA label source sections and metadata reproducibly. Preserve `set_id`, effective time, source URL/query details and retrieval timestamp where available.
- Keep candidate cases in a clearly labelled draft/review location. Leave clinician-only gold fields empty or explicitly unresolved.
- Create a concise clinician review guide and worksheet describing how to author expected indications, qualifiers and limitations from the frozen text and how to record uncertainty.
- Add schema and provenance validation tests that do not require network access.

## Hard clinical gate

You must not:

- write or infer the gold answers;
- label model-generated content as clinician-authored;
- mark a case reviewed or approved;
- move unresolved cases into the frozen benchmark;
- score provider quality.

## Success criteria

- Ten varied candidate cases contain frozen, traceable source material.
- The schema and rubric are versioned, testable and ready for clinician completion.
- Draft versus frozen status is impossible to confuse in code or documentation.
- The clinician has a practical review workflow that does not require editing application code.

End with gate verdict `BLOCKED — CLINICIAN REVIEW REQUIRED` even when all engineering work succeeds. State exactly which files and fields the clinician must complete. Do not start Stage 06 automatically.
