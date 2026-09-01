# Hermes prompt 02 — backend modularisation

Execute Stage 02 of the FDA portfolio refactor.

Read the governing PRD, shared contract, run status, accepted baseline and characterization tests. Confirm Stages 00 and 01 are accepted and the test suite is green before editing.

## Outcome

Refactor the monolithic FastAPI backend into a conventional, understandable module structure without materially changing product behaviour.

## Required work

- Establish `backend/app/` with a thin application entry point, routers, services, schemas, clients, core configuration/logging and narrowly scoped utilities.
- Move API routes into domain routers for drugs, indications, labels/analysis, AI and export as the current contract warrants.
- Move OpenFDA HTTP construction, timeout/retry handling, rate-limit handling, response decoding and upstream-error translation behind one injected client.
- Move drug search, label analysis, indication search, summarisation orchestration and export transformations into cohesive services.
- Move request/response boundaries into explicit Pydantic schemas while preserving serialized field names and compatible validation.
- Remove duplicated deterministic helper logic between streaming and non-streaming paths where doing so is behaviour-preserving.
- Keep the executable/import path used by Docker and local documentation working, using a small compatibility shim only if it has a clear removal plan.
- Update tests alongside each move; use the Stage 01 suite as the compatibility gate.
- Add `docs/refactor/ARCHITECTURE.md` with the resulting module map, dependency direction and concrete rationale for material deviations from the PRD's illustrative tree.

## Constraints

- Do not redesign AI output, prompts or provider selection; Stage 04 owns that work.
- Do not alter endpoint paths, status codes, response fields, SSE event contracts or clinical interpretation heuristics.
- Do not add generic repository/service abstractions where one direct module is clearer.
- Do not combine infrastructure cleanup or portfolio UI work into this stage.
- Avoid circular imports and hidden module-level clients.

## Success criteria

- The application entry point contains bootstrap, middleware, router registration and lifecycle setup rather than business logic.
- External OpenFDA access occurs through one explicit client boundary.
- Services can be tested with injected fakes/mocks.
- All Stage 01 tests and relevant frontend checks pass.
- A reviewer can locate each major behaviour quickly from the architecture document.

Complete the standard handoff and stop. Do not start Stage 03.
