# Hermes prompt 10 — safety documentation and architecture decisions

Execute Stage 10 of the FDA portfolio refactor.

Read the governing PRD, shared contract, run status, implemented architecture, AI-contract documentation and accepted evaluation evidence before editing.

## Outcome

Document the system's intended use, limitations, safeguards and major architectural trade-offs with claims that match the implemented evidence.

## Required work

- Create `docs/SAFETY.md` covering intended research/exploration use; prohibited diagnosis, prescribing, patient-specific decisions, emergency use and replacement of official FDA documentation; AI limitations; data freshness; provenance; failure behaviour; and implemented mitigations.
- State clearly which safeguards are implemented, which are evaluated, and which remain limitations. Link to tests/evaluation reports rather than using assurance language unsupported by evidence.
- Create focused ADRs for: OpenFDA as source of truth; no database at current scope; multi-provider LLM interface; and evaluation before additional AI features.
- For each ADR, include context, decision, consequences, alternatives rejected and concrete implementation references.
- Reconcile earlier architecture documentation and diagrams with the code that actually shipped.
- Audit existing README/docs/UI language for claims such as FDA compliant, clinically validated, safe for clinical use or regulatory compliant. Replace unsupported claims with precise factual wording.
- Document the source/generated-content distinction and residual risks visible to users.

## Constraints

- Do not present the benchmark as clinical validation.
- Do not invent legal or regulatory conclusions.
- Do not add controls that exist only in documentation; if a required safety behaviour is missing, report it as an implementation gap.
- Keep ADRs short and decision-focused.

## Success criteria

- A reviewer can distinguish intended use, non-use, evidence, safeguards and residual risk.
- Every material assurance claim links to implemented code, tests or evaluation evidence.
- ADRs explain why the architecture is intentionally small rather than merely listing technologies.
- Documentation contains no stale diagrams or contradicted setup instructions.

Complete the standard handoff and stop. Do not start Stage 11.
