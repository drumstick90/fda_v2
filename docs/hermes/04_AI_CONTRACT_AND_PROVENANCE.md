# Hermes prompt 04 — AI contract, prompt versioning and provenance

Execute Stage 04 of the FDA portfolio refactor.

Read the governing PRD, shared contract, run status, architecture document and accepted tests. Confirm Stages 00–03 are accepted and all local gates are green before editing.

## Outcome

Turn the existing multi-provider summary feature into an explicit, testable and source-traceable component while retaining the FDA label as the source of truth.

## Required work

- Define a small async provider interface and adapters for the providers the current application genuinely supports: OpenAI, Gemini and DeepSeek.
- Define typed `SummaryRequest`, `SummaryContent` and `SummaryResponse` boundaries. Include at minimum summary text, approved indications, population qualifiers, limitations, source label identifier, source effective time, provider, model and prompt version.
- Version the summary prompt in a dedicated, reviewable location and record its identifier with every output.
- Ensure the model receives only the relevant supplied label content and explicit source-grounding instructions.
- Implement strict structured-output parsing, validation and explicit failure behaviour. Do not convert malformed provider output into apparently authoritative clinical content.
- Make provider selection/fallback behaviour explicit, configurable and observable. Preserve user-visible availability unless a change is justified and documented.
- Update API schemas and frontend presentation coherently. Clearly distinguish FDA-authored source text from generated interpretation and expose provenance near the generated content.
- Add provider contract tests using fakes for successful, empty, malformed, timeout, rate-limit and unavailable-provider cases.
- Add regression tests proving source identifiers, dates, provider/model and prompt version cannot be silently dropped.
- Document the AI data flow, fallback policy and failure semantics.

## Constraints

- Do not run a model comparison or claim one provider is better.
- Do not add RAG, vector search, autonomous agents, fine-tuning or unrelated summary features.
- Do not expose chain-of-thought or hidden provider reasoning.
- Do not display an AI interpretation as FDA-authored text.
- Do not retain the old unstructured response solely to avoid updating a clear internal boundary; preserve compatibility deliberately through an explicit adapter/version if required.

## Success criteria

- All providers implement the same tested contract.
- Structured responses reject unsupported/malformed content safely.
- Every accepted generated response is traceable to source, model, provider and prompt version.
- The frontend makes the source/generated distinction obvious.
- Normal validation uses no paid calls and all established gates pass.

Complete the standard handoff and stop. Do not start Stage 05.
