# Hermes execution runbook

This directory converts [`docs/PRD_PORTFOLIO_REFACTOR.md`](../PRD_PORTFOLIO_REFACTOR.md) into a sequence of bounded, reviewable Hermes assignments.

Run the prompts in order. Give Hermes one prompt at a time, on a clean branch created from the latest accepted stage. Do not paste the whole sequence into one run.

## Operating model

1. Read and accept the output from the current stage.
2. Review the diff and the validation evidence.
3. Merge or otherwise establish that stage as the new baseline.
4. Update [`RUN_STATUS.md`](RUN_STATUS.md).
5. Start the next stage from that accepted baseline.

The shared constraints in [`SHARED_CONTRACT.md`](SHARED_CONTRACT.md) apply to every stage. Each prompt adds only the constraints specific to that stage.

[`PRD_TRACEABILITY.md`](PRD_TRACEABILITY.md) maps every implementation-oriented PRD section to its owning stage and acceptance evidence.

## Sequence

| Stage | Prompt | Outcome | Gate before continuing |
|---:|---|---|---|
| 00 | [`00_BASELINE_AUDIT.md`](00_BASELINE_AUDIT.md) | Behaviour and risk baseline | Audit is accurate and no product behaviour changed |
| 01 | [`01_CHARACTERIZATION_TESTS.md`](01_CHARACTERIZATION_TESTS.md) | Regression safety net | Tests pass without live OpenFDA or paid LLM calls |
| 02 | [`02_BACKEND_MODULARISATION.md`](02_BACKEND_MODULARISATION.md) | Thin FastAPI entry point and modular backend | API/SSE contracts remain compatible |
| 03 | [`03_INFRASTRUCTURE_AND_CI.md`](03_INFRASTRUCTURE_AND_CI.md) | Clean Docker/config/dependencies and CI | Local checks and CI-equivalent commands pass |
| 04 | [`04_AI_CONTRACT_AND_PROVENANCE.md`](04_AI_CONTRACT_AND_PROVENANCE.md) | Provider interface, structured AI output and provenance | All providers use the same tested contract |
| 05 | [`05_EVAL_PILOT_PREPARATION.md`](05_EVAL_PILOT_PREPARATION.md) | Ten-case source-grounded pilot pack | **Clinician completes and signs off gold answers** |
| 06 | [`06_EVAL_ENGINE.md`](06_EVAL_ENGINE.md) | Deterministic scorers, judge adapter and reproducible runner | Offline tests pass; no quality claims made yet |
| 07 | [`07_BENCHMARK_EXPANSION.md`](07_BENCHMARK_EXPANSION.md) | Candidate 30–50-case benchmark | **Clinician verifies every included gold answer** |
| 08 | [`08_CALIBRATION_PACKET.md`](08_CALIBRATION_PACKET.md) | Blinded 15–20-output calibration packet | **Clinician manually scores and locks the packet** |
| 09 | [`09_CALIBRATION_AND_MODEL_COMPARISON.md`](09_CALIBRATION_AND_MODEL_COMPARISON.md) | Calibrated judge and model comparison | Results are reproducible and failures remain visible |
| 10 | [`10_SAFETY_AND_ARCHITECTURE_DOCS.md`](10_SAFETY_AND_ARCHITECTURE_DOCS.md) | Safety document and focused ADRs | Claims match implemented evidence |
| 11 | [`11_PORTFOLIO_POLISH.md`](11_PORTFOLIO_POLISH.md) | Reviewer-first README and demo assets | Five-minute reviewer journey works |
| 12 | [`12_RELEASE_READINESS_AUDIT.md`](12_RELEASE_READINESS_AUDIT.md) | Final evidence-based acceptance audit | All must-have PRD items pass or are explicitly open |

## Human clinical gates

Hermes may retrieve and freeze authoritative source text, validate schemas, identify missing fields and prepare review worksheets. Hermes must not create, silently complete or approve clinician gold answers.

The clinician must personally review:

- the first ten pilot cases after Stage 05;
- every case admitted to the frozen 30–50-case benchmark after Stage 07;
- the blinded calibration packet after Stage 08 and before Stage 09 calculates judge agreement;
- wording of clinical-safety and limitation claims before release.

## Branch and commit convention

Suggested branches:

```text
codex/fda-stage-00-baseline
codex/fda-stage-01-tests
...
codex/fda-stage-12-release-audit
```

Prefer small commits whose messages describe one completed outcome. Never combine an unreviewed stage with the next stage merely to obtain a green build.

## If a stage fails

Keep the stage branch intact. Record the failing command, error, attempted fixes and smallest unresolved blocker in `RUN_STATUS.md`. Repair or rerun that stage; do not route around a failed gate by weakening tests, changing clinical semantics or deleting evidence.
