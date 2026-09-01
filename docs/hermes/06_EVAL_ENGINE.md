# Hermes prompt 06 — evaluation engine

Execute Stage 06 of the FDA portfolio refactor only after the Stage 05 pilot pack exists. The clinician may review the pilot in parallel, but no unresolved draft case may be treated as gold.

Read the governing PRD, shared contract, run status, eval schema/rubric and accepted AI provider contract before editing.

## Outcome

Build a reproducible evaluation engine with deterministic scoring, a structured independent-judge adapter and experiment metadata, without publishing benchmark claims.

## Required work

- Implement dataset loading and strict version/schema validation. Reject unresolved draft cases from benchmark runs.
- Implement deterministic checks for JSON/schema compliance, required fields, preserved source identifiers, expected items, prohibited unsupported items and other rubric fields suitable for exact scoring.
- Normalize comparisons conservatively and expose mismatches; do not use fuzzy matching to conceal clinically meaningful distinctions.
- Implement a versioned LLM-judge prompt and structured judge response covering the PRD dimensions and severity rubric.
- Keep the judge provider independent/configurable and make clear in code and reports that its output is not ground truth.
- Implement a runner that records dataset version, case IDs, summary prompt version, provider/model, relevant generation settings, judge version, timestamp and per-dimension outputs.
- Add resumable output handling that never overwrites prior experiment evidence silently.
- Produce machine-readable raw results and a human-readable draft report containing case-level failures, not only aggregate scores.
- Add offline unit and integration tests with synthetic fixtures for pass, omission, unsupported claim, qualifier loss, treatment-mode confusion, wrong source and malformed output.
- Document separate commands for offline validation and explicitly authorised live generation/judging.

## Constraints

- Do not include unresolved Stage 05 draft cases in a frozen dataset.
- Do not make live or paid model calls unless the user explicitly authorises them for this run.
- Do not publish performance percentages before clinician gold data and judge calibration exist.
- Do not collapse all dimensions into a flattering composite that hides major failures.
- Do not use the same model output as both candidate answer and unqualified ground-truth judge.

## Success criteria

- Offline tests demonstrate that representative clinical failure classes are detected and retained in reports.
- Experiment records are reproducible, append-only or uniquely identified, and traceable to code/prompt/dataset versions.
- The engine refuses unreviewed data and incomplete provenance.
- No model-quality claim is emitted by default.

Complete the standard handoff and stop. Stage 07 requires the clinician-approved pilot gate to be recorded as accepted.
