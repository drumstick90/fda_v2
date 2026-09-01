# Hermes prompt 08 — calibration packet generation

Execute Stage 08 of the FDA portfolio refactor.

Read the governing PRD, shared contract, run status, frozen benchmark manifest, clinician rubric and accepted eval engine. Do not proceed unless every benchmark case is clinician-approved and the full-benchmark human gate is recorded in `RUN_STATUS.md`.

## Outcome

Generate and freeze a blinded 15–20-output packet that the clinician can score manually before any automated judge is calibrated or benchmark result is published.

## Required work

- Verify dataset immutability/version, clinician-review records, source provenance and eligibility of all cases.
- Define a reproducible stratified sampling plan across difficulty classes and failure-sensitive categories.
- With explicit user authorisation for credentials and cost, generate 15–20 candidate outputs using the Stage 04 summary contract and recorded provider/model/settings. Prefer a mix likely to exercise the rubric rather than selecting only easy cases.
- Preserve raw requests, structured responses, errors, prompt/dataset versions and source references in an append-only experiment directory.
- Create a blinded clinician scoring worksheet. Hide provider/model identity and automated scores from the review surface while retaining a private mapping for later analysis.
- Include every rubric dimension, severity, rationale and uncertainty field required for calibration.
- Validate that each worksheet item maps exactly to one immutable output and one approved source case.
- Document how the clinician completes, signs and returns the packet without changing raw model output.

## Constraints

- Do not make paid or credentialed calls without explicit authorisation.
- Do not run or reveal the LLM judge before the clinician ratings are locked.
- Do not edit, repair, regenerate selectively or discard weak model outputs after seeing their quality.
- Do not score the outputs on the clinician's behalf.
- Do not publish model-performance claims from this packet.

## Success criteria

- The packet contains 15–20 traceable, immutable and blinded outputs.
- The review worksheet covers the complete clinician rubric and cannot be confused with automated scoring.
- Generation errors and malformed outputs remain part of the evidence.
- A private mapping permits later provider/model analysis without unblinding the clinician review.

End with gate verdict `BLOCKED — CLINICIAN CALIBRATION SCORING REQUIRED`. State exactly how the clinician records completion. Do not start Stage 09.
