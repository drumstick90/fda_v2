# PRD-to-prompt traceability

This map prevents requirements from disappearing between the governing PRD and the staged Hermes assignments. The PRD remains authoritative; this file identifies the primary implementation owner and expected evidence.

| PRD section | Primary stage(s) | Expected evidence |
|---|---|---|
| 1–5 — Thesis, users, principles, non-goals | Shared contract; 00; 12 | Baseline scope, invariant checks, final audit |
| 6–7 — Target architecture and backend refactor | 01–02 | Characterization tests, modular backend, architecture map |
| 8 — Infrastructure simplification | 03 | Two-service Compose, removed unused dependencies, smoke evidence |
| 9–10 — AI redesign and provider architecture | 04 | Typed common contract, versioned prompt, provenance, provider tests |
| 11–12 — Eval lab and dataset | 05; 07 | Versioned schema, ten-case pilot, balanced 30–50-case candidate pool, clinician gates |
| 13–14 — Dimensions and scorers | 05–06 | Clinician rubric, deterministic scorers, structured judge adapter |
| 15 — Judge calibration | 08–09 | Blinded output packet, clinician ratings, agreement analysis |
| 16–17 — Model comparison and regression | 09 | Reproducible experiments, category breakdowns, regression thresholds |
| 18 — Automated testing | 01–04; 06 | Offline unit/integration/contract/smoke tests |
| 19 — Continuous integration | 03 | Focused GitHub Actions workflow and matching local commands |
| 20 — Observability and failure behaviour | 03–04 | Typed/configured failures, safe logging, provider/upstream error tests |
| 21 — Safety positioning | 04; 10 | Source/generated UI distinction and `docs/SAFETY.md` |
| 22 — Architecture decisions | 10 | Four focused ADRs tied to implemented code |
| 23–24 — README and architecture diagram | 11 | Reviewer-first README and current architecture visual |
| 25 — Demo | 11–12 | Tested storyboard and genuine screenshot/GIF/video evidence |
| 26 — Optional eval UI | 11 only if justified | Small useful UI or explicit decision not to build it |
| 27 — Repository hygiene | 00; 03; 11–12 | Secret/dependency/dead-file audits and clean final tree |
| 28–31 — Metrics, definition of done, order and priorities | README sequence; 12 | Itemized evidence matrix and ship/no-ship verdict |
| 32 — Agent anti-goals | Shared contract; every stage | Scope discipline and stage handoffs |
| 33–34 — Portfolio narrative and strategic outcome | 11–12 | Claims supported by committed implementation and results |

## Human-authored evidence

The following requirements cannot be accepted from agent output alone:

- clinician gold answers for every benchmark case;
- clinician approval of the rubric and its severity anchors;
- manual ratings for the calibration packet;
- final clinical review of safety and limitation language.

Their gates are recorded in `RUN_STATUS.md` and rechecked in Stage 12.
