# Hermes prompt 03 — infrastructure, configuration and CI

Execute Stage 03 of the FDA portfolio refactor.

Read the governing PRD, shared contract, run status and accepted outputs of Stages 00–02. Confirm the modularised application and tests are green before editing.

## Outcome

Make the application reproducible with only the infrastructure it actually uses, and make the local quality gates executable in CI.

## Required work

- Prove whether PostgreSQL, Redis, SQLAlchemy, Alembic, asyncpg, authentication libraries and related settings are used by the application.
- Remove confirmed-unused database/Redis services, volumes, environment variables and Python dependencies from the default setup.
- Centralize runtime configuration with explicit defaults, typed parsing where useful and clear startup failures for genuinely required settings.
- Replace ad-hoc prints with proportionate logging where it materially improves external-service failure diagnosis; never log secrets or full sensitive payloads.
- Verify and sanitize `.env.example` and ignore rules. Document optional provider keys without including real values.
- Ensure `docker compose up` starts only the frontend and backend and that their health/startup behaviour is testable.
- Add a focused GitHub Actions workflow for backend tests/lint and frontend lint/typecheck/build. Use dependency caching only if simple and correct.
- Configure lightweight Python linting and, if the codebase supports it without a large detour, type checking. Do not manufacture a green check by excluding most code.
- Update quick-start and developer-validation commands affected by these changes.

## Constraints

- Do not add replacement infrastructure.
- Do not add deployment automation, cloud-specific dependencies or an elaborate CI matrix.
- Do not require real API keys for CI.
- Do not remove a dependency merely because its usage is difficult to find; provide evidence first.
- Do not make product or AI-contract changes.

## Success criteria

- Default Compose contains only working frontend and backend services.
- A new contributor can run the documented validation commands.
- CI-equivalent commands pass locally, or an external-only limitation is documented precisely.
- OpenFDA, provider and malformed-response failures remain distinguishable.
- No secret or misleading configuration remains in tracked files.

Complete the standard handoff and stop. Do not start Stage 04.
