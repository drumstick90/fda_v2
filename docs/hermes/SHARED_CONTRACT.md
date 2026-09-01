# Shared Hermes contract

This contract governs every prompt in this directory.

## Governing sources

Read before changing code:

1. `docs/PRD_PORTFOLIO_REFACTOR.md`
2. this contract;
3. `docs/hermes/RUN_STATUS.md`;
4. the current stage prompt;
5. relevant implementation, tests and documentation.

When they conflict, preserve clinical safety and existing externally observable behaviour, then report the conflict rather than guessing.

## Autonomy

You are authorised to inspect and edit files in this repository, run non-destructive local validation, and make the in-scope changes required by the current stage.

Stop and request a decision before:

- destructive or irreversible operations;
- external deployment, purchases or paid model runs not explicitly required by the stage;
- changing public API or streaming-event contracts;
- changing clinical interpretation heuristics without characterization tests;
- adding a new framework, service or material product feature;
- expanding beyond the current stage.

## Invariants

- OpenFDA label content is the authoritative source; generated content is not.
- Preserve traceability from generated output to source label identifiers and effective dates.
- Keep deterministic processing deterministic wherever practical.
- Do not fabricate benchmark inputs, gold answers, calibration scores, model results, screenshots, badges or deployment claims.
- Do not call AI-generated material clinician-authored, clinically validated, FDA-compliant, safe for clinical use or regulatory-compliant.
- Do not create patient-specific advice, diagnosis, prescribing guidance or clinical decision support.
- Never commit secrets, `.env` contents, API keys or sensitive logs.
- Do not add databases, Redis, vector search, RAG frameworks, authentication, Kubernetes, microservices or autonomous-agent product features unless a later approved PRD explicitly changes scope.
- Do not rewrite the application from scratch.

## Engineering standard

- Inspect before editing and preserve unrelated user changes.
- Prefer the smallest conventional design that solves the concrete problem.
- Add or update tests for changed behaviour.
- Mock external APIs in normal tests; routine CI must not require network access or paid LLM calls.
- Preserve endpoint paths, status codes, response fields and SSE event shapes unless the stage explicitly authorises a versioned change.
- Keep commits small and reviewable.
- Do not hide failures by weakening assertions, catching all exceptions, returning plausible fallback clinical content or excluding failing cases.

## Required validation

After changes, run the most relevant available checks:

- targeted tests for changed behaviour;
- complete backend tests;
- Python lint/type checks configured by the repository;
- frontend lint, typecheck and build when affected;
- a minimal application or container smoke test when feasible.

If a check cannot run, state why and give the next-best verification. Never report a check as passing unless it was actually run successfully.

## Required handoff

End every stage with:

1. outcome summary;
2. files and behaviours changed;
3. exact validation commands and results;
4. compatibility or clinical-safety evidence;
5. known risks and deferred work;
6. commits created;
7. gate verdict: `PASS`, `PASS WITH EXPLICIT CAVEATS`, or `BLOCKED`;
8. the precise precondition for the next stage.

Update `docs/hermes/RUN_STATUS.md` with factual status only. Do not mark later stages complete.
