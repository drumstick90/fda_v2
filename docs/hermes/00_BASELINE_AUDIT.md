# Hermes prompt 00 — baseline and behaviour audit

Execute Stage 00 of the FDA portfolio refactor.

Read `docs/PRD_PORTFOLIO_REFACTOR.md`, `docs/hermes/SHARED_CONTRACT.md` and `docs/hermes/RUN_STATUS.md` first.

## Outcome

Create an evidence-based baseline that a later refactor can preserve. This is an audit stage, not an architectural implementation stage.

## Required work

- Inspect the complete backend, frontend API client, Docker configuration, dependencies and existing documentation.
- Inventory every FastAPI endpoint, method, request shape, response shape, important status code and SSE event shape consumed by the frontend.
- Map the major behaviours currently embedded in `backend/main.py`, including OpenFDA querying, label selection, indication extraction, history analysis, batch/export behaviour and provider fallback behaviour.
- Identify live-network or paid-model dependencies and the seams needed to test them offline.
- Run every existing non-destructive validation command that can be run safely. Record commands, results and environmental blockers exactly.
- Inspect for committed secrets, unsafe `.env` handling, unused infrastructure/dependencies, dead files and misleading claims. Report findings; do not perform broad cleanup yet.
- Create `docs/refactor/BASELINE.md` containing the endpoint contract, behaviour inventory, current validation baseline, prioritized regression risks and recommended characterization-test matrix.

## Constraints

- Do not change application behaviour, architecture, prompts, dependencies or UI.
- Apart from `docs/refactor/BASELINE.md` and factual run-status updates, do not edit product files.
- Do not make live LLM calls.
- A live OpenFDA smoke request is optional only if network access already exists and no credentials or cost are involved; the audit must remain useful without it.

## Success criteria

- A reviewer can determine what must remain compatible during Stages 01–04.
- All frontend-consumed contracts and SSE events are represented.
- Risks are ranked by likelihood and impact, with clinical-semantic regressions clearly identified.
- Current failures are documented rather than repaired or hidden.

Complete the standard handoff from `SHARED_CONTRACT.md` and stop. Do not start Stage 01.
