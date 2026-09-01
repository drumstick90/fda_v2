# Hermes prompt 12 — release-readiness audit

Execute Stage 12 of the FDA portfolio refactor.

Execute the final acceptance audit for the FDA portfolio refactor.

Read the complete PRD, shared contract, run status, all accepted stage outputs and the current repository. This is an evidence-first audit. Fix only small, unambiguous release blockers; report larger defects for a dedicated repair stage.

## Outcome

Determine whether the repository genuinely satisfies the PRD's must-have definition of done and supports its intended portfolio narrative.

## Required work

- Start from a clean checkout/environment where feasible and follow the documented quick start exactly.
- Run backend tests/lint/type checks, frontend lint/typecheck/build, Compose/application smoke checks and offline eval tests.
- Inspect every public endpoint and the principal user journeys: drug search, batch search, label history, indication search, export and AI summary/provenance.
- Verify CI status if available, but do not substitute a badge for local evidence.
- Audit the PRD Definition of Done and Priority Rules item by item. For each item, record `PASS`, `PARTIAL`, `FAIL` or `NOT APPLICABLE` with file/test/report evidence.
- Verify the frozen dataset size, clinician-review records, source provenance, deterministic scorers, judge calibration, compared models, raw results and report reproducibility.
- Confirm source text and AI output remain conceptually/visually separate and that external-service failures cannot masquerade as valid clinical information.
- Scan for secrets, stale backups, dead configuration, unused infrastructure, broken links, unsupported claims and generated artifacts.
- Test the five-minute reviewer journey and the 45–60 second demo sequence.
- Create `docs/RELEASE_READINESS.md` with findings ordered by release impact and an explicit ship/no-ship verdict.

## Constraints

- Do not mark a checklist item complete based on intention, a prompt, or documentation alone.
- Do not weaken tests, alter benchmark data or edit reports to obtain a passing verdict.
- Do not manufacture evidence for missing screenshots, demos, results, clinical review or CI.
- Do not perform external deployment or repository-setting changes without explicit authorisation.

## Ship threshold

Return `SHIP` only when:

- every PRD must-have item passes;
- both clinician gates are evidenced;
- all reproducible local quality gates pass;
- no open issue could mislead a reviewer about clinical safety, model performance or provenance.

Otherwise return `NO-SHIP`, name the smallest ordered set of repair stages, and stop. Complete the standard handoff and update only Stage 12 in `RUN_STATUS.md`.
