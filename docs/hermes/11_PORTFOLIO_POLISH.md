# Hermes prompt 11 — portfolio presentation and reviewer journey

Execute Stage 11 of the FDA portfolio refactor.

Read the governing PRD, shared contract, run status, accepted safety/architecture documents and actual evaluation results. Confirm Stages 00–10 and all clinician gates are accepted before editing.

## Outcome

Make the repository communicate the implemented product, engineering judgment, evaluation methodology and clinical-safety thinking within a five-minute reviewer journey.

## Required work

- Rewrite the README as a truthful portfolio landing page: product thesis, why it exists, core capabilities, verified evaluation findings, architecture, safety/provenance, quick start, validation and links to deeper documentation.
- Put a concise clinician-builder narrative and the strongest verifiable evidence above the fold.
- Add a clear architecture diagram that matches the current code and shows React, FastAPI, OpenFDA, summary service/providers and evaluation layers without decorative complexity.
- Present actual benchmark results with dataset size/version, models/settings, calibration caveat and visible failure examples. Do not use empty or fabricated tables.
- Improve the generated-summary UI only where needed to make source provenance, generated status, limitations and failures immediately legible.
- Add or refresh representative screenshots/GIFs only from a running application with real or explicitly labelled fixture data. Optimize asset sizes and add useful alt text.
- Create a 45–60 second demo script/storyboard following `data → product → AI → evaluation → safety`; record a video only if the environment and user direction support it.
- Remove stale backup files, dead code, generated artifacts, unused dependencies and misleading documentation with evidence and tests.
- Verify repository description/topic recommendations and list any GitHub metadata changes requiring a separate external action.

## Constraints

- Do not let visual polish displace failing tests, missing evaluation evidence or unresolved safety gaps.
- Do not fabricate a live demo, green badge, screenshot, result or deployment URL.
- Do not add a dedicated eval dashboard unless the backend evaluation pipeline is complete and the UI is genuinely inexpensive and useful.
- Do not describe the author as a senior software engineer or overstate the repository's scope; emphasize the clinical-product-evaluation intersection supported by evidence.

## Success criteria

- A reviewer can verify the product, modular engineering, AI contract, evaluation evidence and safety position within five minutes.
- Quick-start and validation commands work from a clean checkout.
- Screenshots, diagrams and results match the current implementation.
- The README's portfolio claim is fully supportable by committed evidence.

Complete the standard handoff and stop. Do not start Stage 12.
