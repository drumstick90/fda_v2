# Hermes prompt 01 — characterization tests

Execute Stage 01 of the FDA portfolio refactor.

Read the governing PRD, `docs/hermes/SHARED_CONTRACT.md`, `docs/hermes/RUN_STATUS.md` and the accepted `docs/refactor/BASELINE.md`. Confirm Stage 00 is accepted before editing.

## Outcome

Build an offline regression safety net around the current application before modules are moved or behaviour is redesigned.

## Required work

- Introduce a conventional `pytest` test layout and only the test dependencies genuinely required.
- Extract or expose test seams with the smallest possible behaviour-preserving edits.
- Add representative frozen OpenFDA fixtures for successful, empty, malformed, incomplete, rate-limited and upstream-error responses.
- Characterize deterministic behaviour for indication extraction, query construction/escaping, label-date and version selection, formulation/status heuristics, grouping, batch accounting and CSV transformation.
- Add API contract tests for every endpoint used by the frontend, including error responses.
- Add SSE contract tests for both streaming endpoints, preserving event order, event keys and terminal/error behaviour.
- Mock OpenFDA and every LLM provider. Normal tests must run without network, API keys or paid calls.
- Add a minimal application-import/startup smoke test.
- Document exact local test commands.

## Constraints

- Characterization tests describe current externally observable behaviour, including awkward behaviour. Do not silently redesign it in this stage.
- Fix only defects that make reliable testing impossible and are demonstrably accidental; isolate each such fix and explain its compatibility impact.
- Do not modularise `backend/main.py` beyond minimal test seams.
- Do not change AI prompts or clinical interpretation rules.
- Do not chase an arbitrary coverage percentage. Cover the high-risk contracts identified in the baseline.

## Success criteria

- The suite detects changes to endpoint paths, response fields, SSE shapes and core deterministic clinical-data handling.
- The suite is deterministic and passes offline.
- Test failures produce actionable messages rather than snapshot noise.
- Existing functionality remains compatible with the frontend client.

Run the complete test suite twice to detect obvious order dependence. Complete the standard handoff and stop. Do not start Stage 02.
