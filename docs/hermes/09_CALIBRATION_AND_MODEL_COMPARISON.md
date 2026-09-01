# Hermes prompt 09 — judge calibration and model comparison

Execute Stage 09 of the FDA portfolio refactor.

Read the governing PRD, shared contract, run status, frozen dataset manifest, clinician rubric, eval-engine documentation and the clinician-scored calibration packet from Stage 08. Do not proceed unless every benchmark case is clinician-approved and every selected calibration output has a recorded clinician score.

## Outcome

Calibrate the automated judge against clinician review, then run a transparent and reproducible comparison of at least two supported models.

## Required work

- Validate that the frozen dataset is immutable/versioned, all included cases are approved and no draft case can enter the run.
- Select or verify a stratified calibration subset of approximately 15–20 outputs containing passes, minor errors, major errors and clinically important failures where available.
- Compare judge scores with clinician scores and report exact agreement, adjacent-score agreement and major-failure agreement by dimension and overall severity.
- Inspect disagreements case by case. Revise the judge prompt only for a documented rubric-interpretation defect, version every revision, and rerun calibration transparently.
- Establish a documented calibration threshold or candidly state that the judge is insufficiently reliable for a given dimension.
- With explicit user authorisation for credentials/cost, run the same frozen cases and generation settings across at least two supported models. Record model identifiers and all relevant settings exactly.
- Apply deterministic scorers and the calibrated judge without hiding failures or excluding inconvenient cases.
- Produce versioned machine-readable results and a concise report containing aggregate metrics, category breakdowns, unsupported-claim rates, clinically important failures, representative error analysis, calibration limitations and reproducibility commands.
- Add regression thresholds that prioritize clinically important failures and source/qualifier fidelity rather than only average score.

## Constraints

- Do not spend money or use provider credentials without explicit authorisation.
- Do not tune prompts on the test cases and then present the same cases as an untouched benchmark. Record any development/test split or contamination.
- Do not claim global model superiority from this small task-specific benchmark.
- Do not remove failed outputs, provider errors or judge disagreements from denominators without a visible reason.
- Do not replace clinician ratings with judge ratings when agreement is inadequate.

## Success criteria

- Judge calibration is measurable and limitations are explicit.
- Every reported score is traceable to dataset, source, prompt, model, settings and code versions.
- At least two models are compared on identical eligible cases.
- The report foregrounds clinically important failures and is reproducible from committed inputs plus authorised credentials.

If live calls are not authorised or the required clinician scores are missing, complete all safe validation and end `BLOCKED` with the exact missing input. Do not fabricate placeholder results. Otherwise complete the standard handoff and stop.
